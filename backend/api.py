import json
import hashlib
import logging
from contextlib import asynccontextmanager
from datetime import date, datetime, time, timezone
from pathlib import Path
from uuid import uuid4

from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
import grpc
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pymongo.errors import PyMongoError
from starlette.datastructures import UploadFile

from backend.config import settings
from backend.database.mongodb import initialize_application_indexes, mongodb
from backend.database.raft_database import close_raft_connections, get_raft_database
from backend.models.event import Event
from backend.models.seat import Seat
from backend.models.user import User
from backend.services.auth_service import AuthError, AuthService
from backend.services.booking_lifecycle_service import (
    BookingLifecycleError,
    BookingLifecycleService,
)
from backend.services.booking_service import BookingError, BookingService
from backend.services.event_service import EventError, EventService
from backend.services.notification_service import NotificationError, NotificationService
from backend.services.payment_service import PaymentError, PaymentService
from backend.services.refund_service import RefundError
from backend.services.seat_reservation_service import (
    ReservationError,
    SeatReservationService,
)
from backend.utils.jwt_handler import decode_access_token
from backend.raft.http_gateway import RaftGatewayError, RaftHttpGateway
from llm import llm_service
from llm.proto import llm_pb2, llm_pb2_grpc


logger = logging.getLogger(__name__)
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "frontend" / "pictures" / "uploads"
bearer_scheme = HTTPBearer(auto_error=False)


def _json_safe(value):
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, dict):
        result = {key: _json_safe(item) for key, item in value.items()}
        if "_id" in value:
            result.setdefault("id", str(value["_id"]))
        return result
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _response(data):
    return {"success": True, "data": _json_safe(data)}


def _event_payload(data):
    payload = dict(data)
    if isinstance(payload.get("date"), str):
        try:
            parsed_date = date.fromisoformat(payload["date"])
        except ValueError as error:
            raise EventError("date must use YYYY-MM-DD format", 400) from error
        payload["date"] = datetime.combine(
            parsed_date,
            time.min,
            tzinfo=timezone.utc,
        )
    for field in ("totalSeats", "seatsPerRow"):
        if field in payload:
            try:
                payload[field] = int(payload[field])
            except (TypeError, ValueError) as error:
                raise EventError(f"{field} must be an integer", 400) from error
    if "price" in payload:
        try:
            payload["price"] = float(payload["price"])
        except (TypeError, ValueError) as error:
            raise EventError("price must be a number", 400) from error
    return payload


async def _read_event_request(request):
    if "application/json" in request.headers.get("content-type", ""):
        body = await request.json()
        if not isinstance(body, dict):
            raise EventError("Event data must be a JSON object", 400)
        return _event_payload(body), None

    form = await request.form()
    payload = {}
    poster = None
    for key, value in form.multi_items():
        if key == "poster" and isinstance(value, UploadFile):
            poster = value
        elif isinstance(value, str):
            payload[key] = value
    return _event_payload(payload), poster


def _save_poster(upload):
    if not upload:
        return None
    extension = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }.get(upload.content_type)
    if not extension:
        raise EventError("Poster must be a PNG, JPG, or WEBP image", 400)
    content = upload.file.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise EventError("Poster must be no larger than 5 MB", 400)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{extension}"
    (UPLOAD_DIR / filename).write_bytes(content)
    return f"/uploads/{filename}"


def _serialize_booking(database, booking, *, include_user=False):
    def mongo_id(value):
        return ObjectId(value) if isinstance(value, str) and ObjectId.is_valid(value) else value

    result = dict(booking)
    event = Event.find_by_id(database, booking["eventId"])
    result["eventId"] = event or booking["eventId"]
    result["event"] = event
    result["seats"] = list(
        database["seats"].find({"_id": {"$in": [
            mongo_id(seat_id) for seat_id in booking.get("seats", [])
        ]}})
    )
    payment_id = booking.get("paymentId")
    result["paymentId"] = (
        database["payments"].find_one({"_id": mongo_id(payment_id)}) if payment_id else None
    )
    refund_id = booking.get("refundId")
    result["refundId"] = (
        database["refunds"].find_one({"_id": mongo_id(refund_id)}) if refund_id else None
    )
    if include_user:
        user = User.find_by_id(database, booking["userId"])
        result["userId"] = AuthService.public_user(user) if user else None
    return _json_safe(result)


def _queue_notification(request, mode, kind, user, booking):
    try:
        request.app.state.notifications.enqueue(mode, kind, user, booking)
    except PyMongoError as error:
        logger.error("Notification queue write failed (%s).", type(error).__name__)
        raise NotificationError("Notification queue write failed.") from error


async def _current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication is required")
    try:
        claims = decode_access_token(credentials.credentials)
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    user = User.find_by_id(request.app.state.database, claims.get("id", ""))
    if not user:
        raise HTTPException(status_code=401, detail="Authentication is no longer valid")
    return user


async def _admin_user(user=Depends(_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Administrator access is required")
    return user


def _error_response(status_code, message):
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=status_code,
        content={"success": False, "message": message},
    )


def _support_answer(database, user, message, event_id, history):
    if not isinstance(message, str) or not message.strip():
        raise HTTPException(status_code=400, detail="A message is required.")

    context = {"events": [], "bookings": []}
    if event_id and ObjectId.is_valid(str(event_id)):
        event = Event.find_by_id(database, str(event_id))
        if event:
            seats = database["seats"].find(
                {"eventId": event["_id"], "status": "available"},
                {"seatNumber": 1},
            )
            context["available_seats"] = [seat["seatNumber"] for seat in seats]
    else:
        context["events"] = [
            {"title": event.get("title"), "venue": event.get("venue")}
            for event in EventService(database).get_all_events()
        ]

    bookings = BookingLifecycleService(database).get_user_bookings(str(user["_id"]))
    context["bookings"] = [
        {
            "title": (
                Event.find_by_id(database, booking["eventId"]) or {}
            ).get("title"),
            "status": booking.get("status"),
        }
        for booking in bookings[:20]
    ]

    safe_history = []
    if isinstance(history, list):
        safe_history = [
            {"role": item["role"], "content": item["content"][:1000]}
            for item in history[-8:]
            if isinstance(item, dict)
            and item.get("role") in {"user", "assistant"}
            and isinstance(item.get("content"), str)
        ]
    context["conversation"] = safe_history

    try:
        with grpc.insecure_channel(settings.LLM_GRPC_ADDRESS) as channel:
            response = llm_pb2_grpc.LLMServiceStub(channel).AskQuestion(
                llm_pb2.Question(
                    text=message.strip()[:2000],
                    context=json.dumps(context, ensure_ascii=True),
                ),
                timeout=35,
            )
        if response.success:
            return response.response, response.status
        logger.warning("Customer-support gRPC service returned an unsuccessful response.")
    except grpc.RpcError as error:
        logger.warning(
            "Customer-support gRPC service is unavailable (%s).",
            error.code().name,
        )

    return llm_service.answer_question(message, context), "fallback"


def _raft_applied_result(submission):
    applied = submission.get("result")
    if not isinstance(applied, dict) or not isinstance(applied.get("result"), dict):
        raise RaftGatewayError(
            "The committed command did not return an application result.",
            502,
            "RAFT_INVALID_RESULT",
        )
    return applied["result"]


def _raft_request_id(operation, *parts):
    identity = ":".join(str(part) for part in parts)
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return f"{operation}:{digest}"


def create_app(mongo_service=mongodb):
    @asynccontextmanager
    async def lifespan(application):
        if not settings.JWT_SECRET:
            raise RuntimeError("JWT_SECRET or SECRET_KEY is required to start the API.")
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        database = mongo_service.connect()
        initialize_application_indexes(database)
        application.state.database = database
        raft_gateway = RaftHttpGateway(get_raft_database)
        application.state.raft_gateway = raft_gateway
        notifications = NotificationService(database)
        application.state.notifications = notifications
        notifications.start()
        try:
            yield
        finally:
            notifications.stop()
            raft_gateway.close()
            close_raft_connections()
            mongo_service.close()

    application = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
    application.state.raft_gateway = None
    application.mount(
        "/uploads",
        StaticFiles(directory=str(UPLOAD_DIR), check_dir=False),
        name="uploads",
    )

    @application.exception_handler(AuthError)
    @application.exception_handler(EventError)
    @application.exception_handler(ReservationError)
    @application.exception_handler(BookingError)
    @application.exception_handler(BookingLifecycleError)
    @application.exception_handler(PaymentError)
    @application.exception_handler(RefundError)
    async def service_error_handler(request, error):
        return _error_response(
            getattr(error, "status_code", 400),
            getattr(error, "message", str(error)),
        )

    @application.exception_handler(PyMongoError)
    async def database_error_handler(request, error):
        logger.error("MongoDB request failed (%s).", type(error).__name__)
        return _error_response(503, "The database operation could not be completed.")

    @application.exception_handler(NotificationError)
    async def notification_error_handler(request, error):
        logger.error("Notification could not be queued: %s", error)
        return _error_response(
            503, "The booking operation completed, but its email could not be queued. Retry the request."
        )

    @application.exception_handler(RaftGatewayError)
    async def raft_gateway_error_handler(request, error):
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=error.status_code,
            content={
                "success": False,
                "message": error.message,
                "code": error.code,
            },
        )

    @application.exception_handler(HTTPException)
    async def http_error_handler(request, error):
        return _error_response(error.status_code, str(error.detail))

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(request, error):
        return _error_response(422, "Request validation failed.")

    @application.get("/api/health")
    def health(request: Request):
        database = request.app.state.database
        database.client.admin.command("ping")
        return _response({
            "status": "ok",
            "raftEnabled": False,
            "database": {"connected": True, "name": database.name},
        })

    @application.post("/api/auth/register")
    def register(body: dict, request: Request):
        return AuthService(request.app.state.database).register(body)

    @application.post("/api/auth/login")
    def login(body: dict, request: Request):
        return AuthService(request.app.state.database).login(body)

    @application.get("/api/events")
    def list_events(request: Request):
        return _response(EventService(request.app.state.database).get_all_events())

    @application.get("/api/events/{event_id}")
    def get_event(event_id: str, request: Request):
        return _response(EventService(request.app.state.database).get_event(event_id))

    @application.get("/api/events/{event_id}/seats")
    def get_seats(request: Request, event_id: str, user=Depends(_current_user)):
        database = request.app.state.database
        BookingLifecycleService(database).cleanup_expired_bookings(event_id=event_id)
        SeatReservationService(database).release_expired_locks(
            event_id=ObjectId(event_id)
        )
        seats = list(Seat.collection(database).find({"eventId": ObjectId(event_id)}))
        for seat in seats:
            reserved_by = seat.get("reservedBy")
            reserved_user = User.find_by_id(database, reserved_by) if reserved_by else None
            seat["reservedBy"] = (
                AuthService.public_user(reserved_user) if reserved_user else None
            )
        return _response(seats)

    @application.post("/api/events/{event_id}/seats/reserve")
    def reserve_seats(
        event_id: str,
        body: dict,
        request: Request,
        user=Depends(_current_user),
    ):
        result = SeatReservationService(request.app.state.database).reserve_seats(
            event_id=event_id,
            seat_numbers=body.get("seatNumbers"),
            user_id=str(user["_id"]),
            reservation_id=body.get("reservationId"),
        )
        return _response(result)

    @application.post("/api/bookings")
    def create_booking(body: dict, request: Request, user=Depends(_current_user)):
        database = request.app.state.database
        result = BookingService(database).create_booking(
            user_id=str(user["_id"]),
            event_id=body.get("eventId"),
            seat_numbers=body.get("seatNumbers"),
            total_amount=body.get("totalAmount"),
            reservation_id=body.get("reservationId"),
        )
        return _response(_serialize_booking(database, result["data"]))

    @application.get("/api/bookings")
    def list_bookings(request: Request, user=Depends(_current_user)):
        database = request.app.state.database
        lifecycle = BookingLifecycleService(database)
        lifecycle.cleanup_expired_bookings()
        return _response([
            _serialize_booking(database, booking)
            for booking in lifecycle.get_user_bookings(str(user["_id"]))
        ])

    @application.put("/api/bookings/{booking_id}/cancel")
    def cancel_booking(
        booking_id: str,
        request: Request,
        user=Depends(_current_user),
    ):
        database = request.app.state.database
        booking = BookingLifecycleService(database).cancel_booking(
            booking_id,
            str(user["_id"]),
        )
        serialized = _serialize_booking(database, booking)
        _queue_notification(request, "normal", "cancellation", user, serialized)
        return _response(serialized)

    @application.post("/api/payments/mock")
    def mock_payment(body: dict, request: Request, user=Depends(_current_user)):
        database = request.app.state.database
        result = PaymentService(database).process_mock_payment(
            booking_id=body.get("bookingId"),
            user_id=str(user["_id"]),
            amount=body.get("amount"),
            idempotency_key=body.get("idempotencyKey"),
            method=body.get("method", "UPI"),
            outcome=body.get("outcome", "success"),
        )
        if result.get("booking"):
            result["booking"] = _serialize_booking(database, result["booking"])
            if (
                result.get("payment", {}).get("status") == "success"
                and result["booking"].get("status") == "confirmed"
            ):
                _queue_notification(
                    request, "normal", "confirmation", user, result["booking"]
                )
        return _response(result)

    @application.post("/api/chat")
    def chat(body: dict, request: Request, user=Depends(_current_user)):
        answer, status = _support_answer(
            request.app.state.database,
            user,
            body.get("message"),
            body.get("eventId"),
            body.get("history"),
        )
        return _response({"answer": answer, "status": status})

    @application.get("/api/admin/stats")
    def admin_stats(request: Request, user=Depends(_admin_user)):
        database = request.app.state.database
        return _response({
            "totalEvents": database["events"].count_documents({}),
            "totalUsers": database["users"].count_documents({}),
            "totalBookings": database["bookings"].count_documents({}),
            "totalSeats": database["seats"].count_documents({}),
            "availableSeats": database["seats"].count_documents({"status": "available"}),
            "bookedSeats": database["seats"].count_documents({"status": "booked"}),
        })

    @application.get("/api/admin/users")
    def admin_users(request: Request, user=Depends(_admin_user)):
        users = list(
            request.app.state.database["users"]
            .find({}, {"password": 0})
            .sort("createdAt", -1)
        )
        return _response(users)

    @application.get("/api/admin/bookings")
    def admin_bookings(request: Request, user=Depends(_admin_user)):
        database = request.app.state.database
        bookings = list(database["bookings"].find().sort("createdAt", -1))
        return _response([
            _serialize_booking(database, booking, include_user=True)
            for booking in bookings
        ])

    @application.get("/api/admin/events")
    def admin_events(request: Request, user=Depends(_admin_user)):
        events = list(
            request.app.state.database["events"]
            .find()
            .sort([("date", 1), ("createdAt", -1)])
        )
        return _response(events)

    @application.post("/api/admin/events")
    async def create_event(request: Request, user=Depends(_admin_user)):
        database = request.app.state.database
        payload, poster = await _read_event_request(request)
        poster_url = _save_poster(poster)
        if poster_url:
            payload["posterUrl"] = poster_url
        result = EventService(database).create_event(payload)
        return _response(result["data"])

    @application.put("/api/admin/events/{event_id}")
    async def update_event(
        event_id: str,
        request: Request,
        user=Depends(_admin_user),
    ):
        database = request.app.state.database
        payload, poster = await _read_event_request(request)
        poster_url = _save_poster(poster)
        if poster_url:
            payload["posterUrl"] = poster_url
        result = EventService(database).update_event(event_id, payload)
        return _response(result["data"])

    @application.delete("/api/admin/events/{event_id}")
    def delete_event(
        event_id: str,
        request: Request,
        user=Depends(_admin_user),
    ):
        return _response(
            EventService(request.app.state.database).delete_event(event_id)
        )

    @application.get("/api/admin/events/{event_id}/seats")
    def admin_event_seats(
        event_id: str,
        request: Request,
        user=Depends(_admin_user),
    ):
        if not ObjectId.is_valid(event_id):
            raise EventError("Invalid event id", 400)
        database = request.app.state.database
        seats = list(database["seats"].find({"eventId": ObjectId(event_id)}))
        for seat in seats:
            reserved_by = seat.get("reservedBy")
            reserved_user = User.find_by_id(database, reserved_by) if reserved_by else None
            seat["reservedBy"] = (
                AuthService.public_user(reserved_user) if reserved_user else None
            )
        return _response(seats)

    @application.put("/api/admin/seats/{seat_id}")
    def release_seat(
        seat_id: str,
        body: dict,
        request: Request,
        user=Depends(_admin_user),
    ):
        if body.get("status") != "available":
            raise HTTPException(status_code=400, detail="Only seat release is supported.")
        if not ObjectId.is_valid(seat_id):
            raise HTTPException(status_code=400, detail="Invalid seat ID.")
        result = request.app.state.database["seats"].update_one(
            {
                "_id": ObjectId(seat_id),
                "status": "reserved",
                "bookingId": None,
            },
            {
                "$set": {
                    "status": "available",
                    "reservedBy": None,
                    "reservedAt": None,
                    "reservationId": None,
                    "lockExpiresAt": None,
                    "updatedAt": datetime.now(timezone.utc),
                }
            },
        )
        if result.modified_count != 1:
            raise HTTPException(
                status_code=409,
                detail="The seat is no longer an active reservation.",
            )
        return _response({"released": True})

    @application.get("/api/raft/status")
    def raft_status(request: Request):
        return _response(request.app.state.raft_gateway.get_cluster_status())

    @application.get("/api/raft/leader")
    def raft_leader(request: Request):
        return _response(request.app.state.raft_gateway.get_leader())

    @application.get("/api/raft/nodes")
    def raft_nodes(request: Request):
        return _response(
            request.app.state.raft_gateway.get_cluster_status()["nodes"]
        )

    @application.get("/api/raft/log-status")
    def raft_log_status(request: Request):
        cluster = request.app.state.raft_gateway.get_cluster_status()
        return _response([
            {
                "nodeId": node["nodeId"],
                "available": node["available"],
                "lastLogIndex": node.get("lastLogIndex"),
                "commitIndex": node.get("commitIndex"),
                "lastApplied": node.get("lastApplied"),
                "replicationLag": node.get("replicationLag"),
                "logSynchronized": node.get("logSynchronized", False),
                "recoveryStatus": (
                    "unavailable"
                    if not node["available"]
                    else "synchronized"
                    if node.get("logSynchronized")
                    else "catching_up"
                ),
            }
            for node in cluster["nodes"]
        ])

    @application.get("/api/raft/events")
    def raft_events(request: Request):
        database = request.app.state.raft_gateway.read_database()
        return _response(EventService(database).get_all_events())

    @application.get("/api/raft/events/{event_id}")
    def raft_event(event_id: str, request: Request):
        if not ObjectId.is_valid(event_id):
            raise EventError("Invalid event id", 400)
        database = request.app.state.raft_gateway.read_database()
        return _response(EventService(database).get_event(event_id))

    @application.get("/api/raft/events/{event_id}/seats")
    def raft_event_seats(
        event_id: str,
        request: Request,
        user=Depends(_current_user),
    ):
        if not ObjectId.is_valid(event_id):
            raise EventError("Invalid event id", 400)
        database = request.app.state.raft_gateway.read_database()
        EventService(database).get_event(event_id)
        seats = list(
            database["seats"].find({"eventId": ObjectId(event_id)})
        )
        now = datetime.now(timezone.utc)
        for seat in seats:
            expires_at = seat.get("lockExpiresAt")
            if (
                seat.get("status") == "reserved"
                and seat.get("bookingId") is None
                and (expires_at is None or expires_at <= now)
            ):
                seat["status"] = "available"
                seat["reservedBy"] = None
            elif seat.get("reservedBy") is not None:
                seat["reservedBy"] = str(seat["reservedBy"])
        return _response(seats)

    @application.post("/api/raft/events/{event_id}/seats/reserve")
    def raft_reserve_seats(
        event_id: str,
        body: dict,
        request: Request,
        user=Depends(_current_user),
    ):
        if not ObjectId.is_valid(event_id):
            raise ReservationError("Invalid event ID", 400)
        reservation_id = body.get("reservationId")
        if not isinstance(reservation_id, str) or not reservation_id:
            raise ReservationError(
                "A reservationId is required for Raft idempotency",
                400,
            )
        database = request.app.state.raft_gateway.read_database()
        EventService(database).get_event(event_id)
        user_id = str(user["_id"])
        request_id = _raft_request_id(
            "reserve",
            user_id,
            event_id,
            reservation_id,
        )
        submission = request.app.state.raft_gateway.submit_command(
            request_id,
            "RESERVE_SEATS",
            {
                "event_id": event_id,
                "seat_numbers": body.get("seatNumbers"),
                "user_id": user_id,
                "reservation_id": reservation_id,
            },
        )
        return _response(_raft_applied_result(submission))

    @application.post("/api/raft/bookings")
    def raft_create_booking(
        body: dict,
        request: Request,
        user=Depends(_current_user),
    ):
        event_id = body.get("eventId")
        reservation_id = body.get("reservationId")
        if not isinstance(reservation_id, str) or not reservation_id:
            raise BookingError(
                "A reservationId is required for Raft idempotency",
                400,
            )
        if not ObjectId.is_valid(str(event_id or "")):
            raise BookingError("Invalid event ID", 400)
        database = request.app.state.raft_gateway.read_database()
        EventService(database).get_event(event_id)
        user_id = str(user["_id"])
        request_id = BookingService.generate_request_id(
            user_id,
            reservation_id,
        )
        submission = request.app.state.raft_gateway.submit_command(
            request_id,
            "CREATE_BOOKING",
            {
                "user_id": user_id,
                "event_id": event_id,
                "seat_numbers": body.get("seatNumbers"),
                "total_amount": body.get("totalAmount"),
                "reservation_id": reservation_id,
            },
        )
        operation = _raft_applied_result(submission)
        booking = operation.get("data")
        if not isinstance(booking, dict):
            raise RaftGatewayError(
                "The committed booking operation returned no booking.",
                502,
                "RAFT_INVALID_RESULT",
            )
        database = request.app.state.raft_gateway.database_provider(
            submission["leaderId"]
        )
        return _response(_serialize_booking(database, booking))

    @application.get("/api/raft/bookings")
    def raft_bookings(request: Request, user=Depends(_current_user)):
        database = request.app.state.raft_gateway.read_database()
        bookings = BookingLifecycleService(database).get_user_bookings(
            str(user["_id"])
        )
        return _response([
            _serialize_booking(database, booking)
            for booking in bookings
        ])

    @application.get("/api/raft/bookings/{booking_id}")
    def raft_booking(
        booking_id: str,
        request: Request,
        user=Depends(_current_user),
    ):
        database = request.app.state.raft_gateway.read_database()
        booking = BookingLifecycleService(database).get_booking(
            booking_id,
            str(user["_id"]),
        )
        return _response(_serialize_booking(database, booking))

    @application.put("/api/raft/bookings/{booking_id}/cancel")
    def raft_cancel_booking(
        booking_id: str,
        request: Request,
        user=Depends(_current_user),
    ):
        user_id = str(user["_id"])
        if not ObjectId.is_valid(booking_id):
            raise BookingLifecycleError("Invalid booking ID", 400)
        request_id = _raft_request_id(
            "cancel",
            user_id,
            booking_id,
        )
        submission = request.app.state.raft_gateway.submit_command(
            request_id,
            "CANCEL_BOOKING",
            {
                "booking_id": booking_id,
                "user_id": user_id,
            },
        )
        booking = _raft_applied_result(submission).get("result")
        if not isinstance(booking, dict):
            raise RaftGatewayError(
                "The committed cancellation returned no booking.",
                502,
                "RAFT_INVALID_RESULT",
            )
        database = request.app.state.raft_gateway.database_provider(
            submission["leaderId"]
        )
        serialized = _serialize_booking(database, booking)
        _queue_notification(request, "raft", "cancellation", user, serialized)
        return _response(serialized)

    @application.post("/api/raft/payments/mock")
    def raft_mock_payment(
        body: dict,
        request: Request,
        user=Depends(_current_user),
    ):
        idempotency_key = body.get("idempotencyKey")
        if not isinstance(idempotency_key, str) or not idempotency_key:
            raise PaymentError("An idempotencyKey is required", 400)
        user_id = str(user["_id"])
        request_id = _raft_request_id(
            "payment",
            user_id,
            idempotency_key,
        )
        submission = request.app.state.raft_gateway.submit_command(
            request_id,
            "PROCESS_PAYMENT",
            {
                "booking_id": body.get("bookingId"),
                "user_id": user_id,
                "amount": body.get("amount"),
                "idempotency_key": idempotency_key,
                "method": body.get("method", "UPI"),
                "outcome": body.get("outcome", "success"),
            },
        )
        result = _raft_applied_result(submission)
        database = request.app.state.raft_gateway.database_provider(
            submission["leaderId"]
        )
        if isinstance(result.get("booking"), dict):
            result["booking"] = _serialize_booking(
                database,
                result["booking"],
            )
            if (
                result.get("payment", {}).get("status") == "success"
                and result["booking"].get("status") == "confirmed"
            ):
                _queue_notification(
                    request, "raft", "confirmation", user, result["booking"]
                )
        return _response(result)

    @application.post("/api/raft/chat")
    def raft_chat(
        body: dict,
        request: Request,
        user=Depends(_current_user),
    ):
        database = request.app.state.raft_gateway.read_database()
        answer, status = _support_answer(
            database,
            user,
            body.get("message"),
            body.get("eventId"),
            body.get("history"),
        )
        return _response({"answer": answer, "status": status})

    @application.get("/api/raft/admin/stats")
    def raft_admin_stats(request: Request, user=Depends(_admin_user)):
        database = request.app.state.raft_gateway.read_database()
        standalone = request.app.state.database
        return _response({
            "totalEvents": database["events"].count_documents({}),
            "totalUsers": standalone["users"].count_documents({}),
            "totalBookings": database["bookings"].count_documents({}),
            "totalSeats": database["seats"].count_documents({}),
            "availableSeats": database["seats"].count_documents({
                "status": "available",
            }),
            "bookedSeats": database["seats"].count_documents({
                "status": "booked",
            }),
        })

    @application.get("/api/raft/admin/users")
    def raft_admin_users(request: Request, user=Depends(_admin_user)):
        users = list(
            request.app.state.database["users"]
            .find({}, {"password": 0})
            .sort("createdAt", -1)
        )
        return _response(users)

    @application.get("/api/raft/admin/bookings")
    def raft_admin_bookings(request: Request, user=Depends(_admin_user)):
        database = request.app.state.raft_gateway.read_database()
        bookings = list(database["bookings"].find().sort("createdAt", -1))
        results = []
        for booking in bookings:
            serialized = _serialize_booking(database, booking)
            account = User.find_by_id(
                request.app.state.database,
                booking["userId"],
            )
            serialized["user"] = (
                AuthService.public_user(account) if account else None
            )
            results.append(serialized)
        return _response(results)

    @application.get("/api/raft/admin/events")
    def raft_admin_events(request: Request, user=Depends(_admin_user)):
        database = request.app.state.raft_gateway.read_database()
        return _response(
            list(database["events"].find().sort([("date", 1), ("createdAt", -1)]))
        )

    @application.post("/api/raft/admin/events")
    async def raft_create_event(request: Request, user=Depends(_admin_user)):
        payload, poster = await _read_event_request(request)
        poster_url = _save_poster(poster)
        if poster_url:
            payload["posterUrl"] = poster_url
        submission = request.app.state.raft_gateway.submit_command(
            f"create-event:{uuid4()}",
            "CREATE_EVENT",
            {"event": payload, "seats": []},
        )
        event = _raft_applied_result(submission).get("event")
        if not isinstance(event, dict):
            raise RaftGatewayError(
                "The committed event operation returned no event.",
                502,
                "RAFT_INVALID_RESULT",
            )
        return _response(event)

    @application.put("/api/raft/admin/events/{event_id}")
    async def raft_update_event(
        event_id: str,
        request: Request,
        user=Depends(_admin_user),
    ):
        if not ObjectId.is_valid(event_id):
            raise EventError("Invalid event id", 400)
        payload, poster = await _read_event_request(request)
        poster_url = _save_poster(poster)
        if poster_url:
            payload["posterUrl"] = poster_url
        database = request.app.state.raft_gateway.read_database()
        seats = [
            {"seatNumber": seat["seatNumber"], "category": seat.get("category")}
            for seat in database["seats"].find(
                {"eventId": ObjectId(event_id)},
                {"seatNumber": 1, "category": 1},
            ).sort("seatNumber", 1)
        ]
        submission = request.app.state.raft_gateway.submit_command(
            f"update-event:{uuid4()}",
            "UPDATE_EVENT",
            {
                "event_id": event_id,
                "event": payload,
                "seats": seats,
            },
        )
        event = _raft_applied_result(submission).get("event")
        if not isinstance(event, dict):
            raise RaftGatewayError(
                "The committed event update returned no event.",
                502,
                "RAFT_INVALID_RESULT",
            )
        return _response(event)

    @application.delete("/api/raft/admin/events/{event_id}")
    def raft_delete_event(
        event_id: str,
        request: Request,
        user=Depends(_admin_user),
    ):
        submission = request.app.state.raft_gateway.submit_command(
            f"delete-event:{uuid4()}",
            "DELETE_EVENT",
            {"event_id": event_id},
        )
        return _response(_raft_applied_result(submission))

    @application.get("/api/raft/admin/events/{event_id}/seats")
    def raft_admin_event_seats(
        event_id: str,
        request: Request,
        user=Depends(_admin_user),
    ):
        if not ObjectId.is_valid(event_id):
            raise EventError("Invalid event id", 400)
        database = request.app.state.raft_gateway.read_database()
        seats = list(
            database["seats"].find({"eventId": ObjectId(event_id)})
        )
        for seat in seats:
            if seat.get("reservedBy") is not None:
                seat["reservedBy"] = str(seat["reservedBy"])
        return _response(seats)

    @application.put("/api/raft/admin/seats/{seat_id}")
    def raft_admin_release_seat(
        seat_id: str,
        body: dict,
        request: Request,
        user=Depends(_admin_user),
    ):
        submission = request.app.state.raft_gateway.submit_command(
            f"release-seat:{uuid4()}",
            "UPDATE_SEAT",
            {"seat_id": seat_id, "status": body.get("status")},
        )
        return _response(_raft_applied_result(submission))

    return application


app = create_app()
