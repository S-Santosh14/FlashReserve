import json
import hashlib
import threading

from datetime import datetime, timedelta, timezone
from bson import ObjectId

from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from backend.services.booking_service import (
    BookingService,
    BookingError
)

from backend.services.booking_lifecycle_service import (
    BookingLifecycleService,
    BookingLifecycleError
)

from backend.services.payment_service import (
    PaymentService,
    PaymentError
)

from backend.services.refund_service import (
    RefundService,
    RefundError
)
from backend.models.event import Event
from backend.models.seat import Seat
from backend.services.event_service import EventService, EventError
from backend.services.seat_reservation_service import (
    ReservationError,
    SeatReservationService,
)


class StateMachineError(Exception):
    pass


class RaftStateMachine:

    COLLECTION = "raftcommandresults"

    LOCK_DURATION_SECONDS = 60

    def __init__(self, database):

        self.database = database

        self.commands = database[self.COLLECTION]

        self.booking_service = BookingService(database)

        self.lifecycle_service = BookingLifecycleService(database)

        self.payment_service = PaymentService(database)

        self.refund_service = RefundService(database)
        self.event_service = EventService(database)
        self.reservation_service = SeatReservationService(database)

        self.local_lock = threading.RLock()

        # Unique command IDs prevent duplicate ledger records.
        self.commands.create_index(
            "commandId",
            unique=True
        )

    # --------------------------------------------------
    # COMMAND NORMALIZATION
    # --------------------------------------------------

    @staticmethod
    def normalize_payload(payload):

        try:

            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")

            if isinstance(payload, str):
                payload = json.loads(payload)

        except (json.JSONDecodeError, UnicodeDecodeError) as error:

            raise StateMachineError(
                "Invalid JSON command payload"
            ) from error

        if not isinstance(payload, dict):
            raise StateMachineError(
                "Command payload must be a JSON object"
            )

        return payload

    # --------------------------------------------------
    # COMMAND CLAIM
    # --------------------------------------------------

    def claim_command(self, command_id, command_type, payload):

        now = datetime.now(timezone.utc)

        try:

            self.commands.update_one(
                {
                    "commandId": command_id
                },
                {
                    "$setOnInsert": {
                        "commandId": command_id,
                        "commandType": command_type,
                        "payload": payload,
                        "status": "pending",
                        "createdAt": now
                    }
                },
                upsert=True
            )

        except DuplicateKeyError:
            pass

        existing = self.commands.find_one({
            "commandId": command_id
        })

        if not existing:
            raise StateMachineError(
                "Unable to create command record"
            )

        if (
            existing["commandType"] != command_type
            or existing["payload"] != payload
        ):
            raise StateMachineError(
                "Command ID was reused with different data"
            )

        if existing["status"] == "completed":

            return {
                "claimed": False,
                "completed": True,
                "success": True,
                "result": existing.get("result")
            }

        if existing["status"] == "failed":

            return {
                "claimed": False,
                "completed": True,
                "success": False,
                "result": existing.get("result") or {
                    "error": existing.get("error", "Command failed"),
                    "status_code": existing.get("status_code", 400),
                }
            }

        lock_until = now + timedelta(
            seconds=self.LOCK_DURATION_SECONDS
        )

        claimed = self.commands.find_one_and_update(
            {
                "commandId": command_id,
                "$or": [
                    {"status": "pending"},
                    {
                        "status": "processing",
                        "lockUntil": {"$lte": now}
                    },
                    {
                        "status": "processing",
                        "lockUntil": None
                    }
                ]
            },
            {
                "$set": {
                    "status": "processing",
                    "lockUntil": lock_until,
                    "updatedAt": now
                }
            },
            return_document=ReturnDocument.AFTER
        )

        if not claimed:

            return {
                "claimed": False,
                "completed": False,
                "result": None
            }

        return {
            "claimed": True,
            "completed": False,
            "result": None
        }

    # --------------------------------------------------
    # BUSINESS COMMAND DISPATCHER
    # --------------------------------------------------

    def execute_business_command(
        self,
        command_type,
        payload,
        command_id="legacy",
    ):
        operation_time_value = payload.get("_raftTimestamp")
        if operation_time_value:
            try:
                operation_time = datetime.fromisoformat(
                    operation_time_value.replace("Z", "+00:00")
                )
            except (AttributeError, TypeError, ValueError) as error:
                raise StateMachineError("Invalid Raft operation timestamp") from error
            if operation_time.tzinfo is None:
                operation_time = operation_time.replace(tzinfo=timezone.utc)
        else:
            operation_time = datetime.now(timezone.utc)

        def deterministic_object_id(suffix):
            digest = hashlib.sha256(
                f"{command_id}:{suffix}".encode("utf-8")
            ).digest()
            return ObjectId(digest[:12])

        def parse_datetime(value, field):
            if isinstance(value, datetime):
                result = value
            elif isinstance(value, str):
                try:
                    result = datetime.fromisoformat(
                        value.replace("Z", "+00:00")
                    )
                except ValueError as error:
                    raise StateMachineError(
                        f"Invalid {field} timestamp"
                    ) from error
            else:
                raise StateMachineError(f"Invalid {field} timestamp")
            return result.replace(tzinfo=timezone.utc) if result.tzinfo is None else result

        def deterministic_seat_id(event_id, seat_number):
            digest = hashlib.sha256(
                f"{event_id}:{seat_number}".encode("utf-8")
            ).digest()
            return ObjectId(digest[:12])

        def upsert_event(event_id, event_data, seat_rows, *, source_updated_at=None):
            created_at_value = event_data.get("createdAt")
            event_data = {
                key: value
                for key, value in event_data.items()
                if key in EventService.EVENT_FIELDS
            }
            if "date" in event_data:
                event_data["date"] = parse_datetime(event_data["date"], "event date")
            try:
                Event.validate(event_data)
            except (TypeError, ValueError) as error:
                raise EventError(str(error), 400) from error

            total_seats = event_data.get("totalSeats")
            seats_per_row = event_data.get("seatsPerRow", 10)
            if (
                isinstance(total_seats, bool)
                or not isinstance(total_seats, int)
                or total_seats < 1
                or isinstance(seats_per_row, bool)
                or not isinstance(seats_per_row, int)
                or seats_per_row < 1
            ):
                raise EventError(
                    "totalSeats and seatsPerRow must be positive integers",
                    400,
                )

            now = source_updated_at or operation_time
            event_document = Event.prepare(event_data)
            event_document["_id"] = event_id
            event_document["updatedAt"] = now
            event_document["createdAt"] = (
                parse_datetime(created_at_value, "event creation")
                if created_at_value is not None
                else now
            )
            if source_updated_at is not None:
                event_document["_catalogSourceUpdatedAt"] = source_updated_at

            self.database["events"].update_one(
                {"_id": event_id},
                {
                    "$set": {
                        key: value
                        for key, value in event_document.items()
                        if key != "_id"
                    },
                    "$setOnInsert": {"_id": event_id},
                },
                upsert=True,
            )

            seat_by_number = {}
            for seat in seat_rows:
                if not isinstance(seat, dict):
                    raise StateMachineError("Invalid event seat catalog entry")
                seat_number = seat.get("seatNumber")
                if not isinstance(seat_number, str) or not seat_number.strip():
                    raise StateMachineError("Invalid seat number in event catalog")
                seat_by_number[seat_number.strip()] = seat.get("category")

            if not seat_by_number:
                seat_numbers = EventService.seat_numbers_to_add(
                    total_seats,
                    seats_per_row,
                )
                seat_by_number = {
                    seat_number: EventService.seat_category(
                        index,
                        total_seats,
                    )
                    for index, seat_number in enumerate(seat_numbers)
                }
            else:
                missing_seats = EventService.seat_numbers_to_add(
                    total_seats,
                    seats_per_row,
                    seat_by_number,
                )
                for seat_number in missing_seats:
                    seat_index = EventService.seat_index(
                        seat_number,
                        seats_per_row,
                    )
                    seat_by_number[seat_number] = EventService.seat_category(
                        seat_index,
                        total_seats,
                    )

            seat_collection = Seat.collection(self.database)
            for seat_number, category in seat_by_number.items():
                if category not in Seat.CATEGORIES:
                    category = "Silver"
                seat_document = {
                    "_id": deterministic_seat_id(event_id, seat_number),
                    "eventId": event_id,
                    "seatNumber": seat_number,
                    "category": category,
                    "status": "available",
                    "reservedBy": None,
                    "reservedAt": None,
                    "reservationId": None,
                    "lockExpiresAt": None,
                    "bookingId": None,
                    "createdAt": now,
                    "updatedAt": now,
                }
                seat_collection.update_one(
                    {"eventId": event_id, "seatNumber": seat_number},
                    {"$setOnInsert": seat_document},
                    upsert=True,
                )

            return Event.find_by_id(self.database, event_id)

        # CREATE BOOKING
        if command_type == "CREATE_BOOKING":
            reference = hashlib.sha256(
                f"{command_id}:booking-reference".encode("utf-8")
            ).hexdigest()[:12].upper()
            deterministic_fields = {}
            if command_id != "legacy":
                deterministic_fields = {
                    "booking_id": deterministic_object_id("booking"),
                    "booking_reference": f"FR-{reference}",
                    "operation_time": operation_time,
                }

            return self.booking_service.create_booking(
                user_id=payload["user_id"],
                event_id=payload["event_id"],
                seat_numbers=payload["seat_numbers"],
                total_amount=payload["total_amount"],
                reservation_id=payload["reservation_id"],
                **deterministic_fields,
            )

        if command_type == "RESERVE_SEATS":
            return self.reservation_service.reserve_seats(
                event_id=payload["event_id"],
                seat_numbers=payload["seat_numbers"],
                user_id=payload["user_id"],
                reservation_id=payload["reservation_id"],
                **(
                    {"operation_time": operation_time}
                    if command_id != "legacy"
                    else {}
                ),
            )

        if command_type == "RELEASE_SEAT":
            if not ObjectId.is_valid(str(payload.get("user_id", ""))):
                raise ReservationError("Invalid user ID", 400)
            if not ObjectId.is_valid(str(payload.get("event_id", ""))):
                raise ReservationError("Invalid event ID", 400)
            if (
                not isinstance(payload.get("reservation_id"), str)
                or not payload["reservation_id"]
            ):
                raise ReservationError("Invalid reservation ID", 400)
            if not isinstance(payload.get("seat_numbers"), list):
                raise ReservationError("Invalid seat numbers", 400)
            result = self.database["seats"].update_many(
                {
                    "eventId": ObjectId(payload["event_id"]),
                    "seatNumber": {"$in": payload["seat_numbers"]},
                    "status": "reserved",
                    "reservedBy": ObjectId(payload["user_id"]),
                    "reservationId": payload["reservation_id"],
                    "bookingId": None,
                },
                {
                    "$set": {
                        "status": "available",
                        "reservedBy": None,
                        "reservedAt": None,
                        "reservationId": None,
                        "lockExpiresAt": None,
                        "updatedAt": operation_time,
                    }
                },
            )
            return {"released": result.modified_count}

        if command_type == "READ_BARRIER":
            return {
                "success": True,
                "readIndex": payload.get("_raftIndex"),
            }

        if command_type == "SYNC_EVENT_CATALOG":
            event_data = payload.get("event")
            if not isinstance(event_data, dict):
                raise StateMachineError("Event catalog payload is required")
            event_id_value = payload.get("event_id") or event_data.get("_id")
            if not ObjectId.is_valid(str(event_id_value or "")):
                raise EventError("Invalid event ID", 400)
            event_id = ObjectId(str(event_id_value))
            source_updated_at = (
                parse_datetime(payload["source_updated_at"], "catalog")
                if payload.get("source_updated_at")
                else operation_time
            )
            return {
                "success": True,
                "event": upsert_event(
                    event_id,
                    event_data,
                    payload.get("seats", []),
                    source_updated_at=source_updated_at,
                ),
            }

        if command_type == "CREATE_EVENT":
            event_data = payload.get("event")
            if not isinstance(event_data, dict):
                raise EventError("Event data is required", 400)
            return {
                "success": True,
                "event": upsert_event(
                    deterministic_object_id("event"),
                    event_data,
                    payload.get("seats", []),
                ),
            }

        if command_type == "UPDATE_EVENT":
            event_id = payload.get("event_id")
            event_data = payload.get("event")
            if not ObjectId.is_valid(str(event_id or "")):
                raise EventError("Invalid event ID", 400)
            if not isinstance(event_data, dict):
                raise EventError("Event data is required", 400)
            event_id = ObjectId(str(event_id))
            current = Event.find_by_id(self.database, event_id)
            if not current:
                raise EventError("Event not found", 404)
            merged = {
                key: current[key]
                for key in EventService.EVENT_FIELDS
                if key in current
            }
            if current.get("createdAt") is not None:
                merged["createdAt"] = current["createdAt"]
            merged.update({
                key: value
                for key, value in event_data.items()
                if key in EventService.EVENT_FIELDS
            })
            seat_rows = payload.get("seats", [])
            if len(seat_rows) < self.database["seats"].count_documents(
                {"eventId": event_id}
            ):
                raise EventError(
                    "Event updates cannot remove existing seats",
                    409,
                )
            return {
                "success": True,
                "event": upsert_event(
                    event_id,
                    merged,
                    seat_rows,
                ),
            }

        if command_type == "DELETE_EVENT":
            event_id = payload.get("event_id")
            if not ObjectId.is_valid(str(event_id or "")):
                raise EventError("Invalid event ID", 400)
            event_id = ObjectId(str(event_id))
            event = Event.find_by_id(self.database, event_id)
            if not event:
                return {"success": True, "archived": False}
            has_booking_history = self.database["bookings"].find_one(
                {"eventId": event_id}
            ) is not None
            has_held_seats = self.database["seats"].find_one({
                "eventId": event_id,
                "status": {"$in": ["reserved", "booked"]},
            }) is not None
            if has_booking_history or has_held_seats:
                self.database["events"].update_one(
                    {"_id": event_id},
                    {"$set": {"status": "archived", "updatedAt": operation_time}},
                )
                return {"success": True, "archived": True}
            self.database["seats"].delete_many({"eventId": event_id})
            self.database["events"].delete_one({"_id": event_id})
            return {"success": True, "archived": False}

        if command_type == "UPDATE_SEAT":
            seat_id = payload.get("seat_id")
            if not ObjectId.is_valid(str(seat_id or "")):
                raise EventError("Invalid seat ID", 400)
            if payload.get("status") != "available":
                raise EventError("Only seat release is supported", 400)
            result = self.database["seats"].update_one(
                {
                    "_id": ObjectId(str(seat_id)),
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
                        "updatedAt": operation_time,
                    }
                },
            )
            if result.modified_count != 1:
                seat = self.database["seats"].find_one(
                    {"_id": ObjectId(str(seat_id))}
                )
                if not seat or seat.get("status") != "available":
                    raise EventError(
                        "The seat is no longer an active reservation",
                        409,
                    )
            return {"success": True, "released": True}

        # PROCESS PAYMENT
        if command_type == "PROCESS_PAYMENT":
            transaction_id = hashlib.sha256(
                f"{command_id}:payment-transaction".encode("utf-8")
            ).hexdigest()[:32].upper()
            deterministic_fields = {}
            if command_id != "legacy":
                deterministic_fields = {
                    "payment_id": deterministic_object_id("payment"),
                    "transaction_id": f"MOCK-{transaction_id}",
                    "operation_time": operation_time,
                }

            return self.payment_service.process_mock_payment(
                booking_id=payload["booking_id"],
                user_id=payload["user_id"],
                amount=payload["amount"],
                idempotency_key=payload["idempotency_key"],
                method=payload.get("method", "UPI"),
                outcome=payload.get("outcome", "success"),
                **deterministic_fields,
            )

        # CANCEL BOOKING

        if command_type == "CANCEL_BOOKING":

            return self.lifecycle_service.cancel_booking(
                booking_id=payload["booking_id"],
                user_id=payload["user_id"],
                **(
                    {"operation_time": operation_time}
                    if command_id != "legacy"
                    else {}
                ),
            )

        # PROCESS REFUND
        if command_type == "PROCESS_REFUND":
            transaction_id = hashlib.sha256(
                f"{command_id}:refund-transaction".encode("utf-8")
            ).hexdigest()[:32].upper()
            deterministic_fields = {}
            if command_id != "legacy":
                deterministic_fields = {
                    "refund_id": deterministic_object_id("refund"),
                    "transaction_id": f"REF-{transaction_id}",
                    "operation_time": operation_time,
                }

            return self.refund_service.create_refund(
                booking_id=payload["booking_id"],
                user_id=payload["user_id"],
                idempotency_key=payload["idempotency_key"],
                outcome=payload.get("outcome", "success"),
                **deterministic_fields,
            )

        raise StateMachineError(
            f"Unsupported command: {command_type}"
        )

    # --------------------------------------------------
    # COMMAND RESULT
    # --------------------------------------------------

    def complete_command(
        self,
        command_id,
        result
    ):

        now = datetime.now(timezone.utc)

        updated = self.commands.update_one(
            {
                "commandId": command_id,
                "status": "processing"
            },
            {
                "$set": {
                    "status": "completed",
                    "result": result,
                    "completedAt": now,
                    "updatedAt": now,
                    "lockUntil": None
                }
            }
        )

        if updated.modified_count != 1:

            raise StateMachineError(
                "Unable to persist command result"
            )

    def fail_command(
        self,
        command_id,
        failure
    ):

        now = datetime.now(timezone.utc)
        if not isinstance(failure, dict):
            failure = {
                "error": str(failure),
                "status_code": 400,
            }

        self.commands.update_one(
            {
                "commandId": command_id,
                "status": "processing"
            },
            {
                "$set": {
                    "status": "failed",
                    "error": failure["error"],
                    "status_code": failure["status_code"],
                    "result": failure,
                    "updatedAt": now,
                    "lockUntil": None
                }
            }
        )

    # --------------------------------------------------
    # APPLY COMMITTED COMMAND
    # --------------------------------------------------

    def apply_command(
        self,
        command_id,
        command_type,
        payload
    ):

        if not command_id:
            raise StateMachineError(
                "Command ID is required"
            )

        payload = self.normalize_payload(payload)

        with self.local_lock:

            claim = self.claim_command(
                command_id,
                command_type,
                payload
            )

            if claim["completed"]:

                return {
                    "success": claim.get("success", True),
                    "replayed": True,
                    "result": claim["result"]
                }

            if not claim["claimed"]:

                return {
                    "success": False,
                    "pending": True,
                    "message": "Command is being processed"
                }

            try:

                result = self.execute_business_command(
                    command_type,
                    payload,
                    command_id=command_id,
                )

                self.complete_command(
                    command_id,
                    result
                )

                return {
                    "success": True,
                    "replayed": False,
                    "result": result
                }

            except (
                BookingError,
                BookingLifecycleError,
                PaymentError,
                RefundError,
                StateMachineError,
                EventError,
                ReservationError,
            ) as error:

                failure = {
                    "error": str(error),
                    "status_code": getattr(error, "status_code", 400),
                }
                self.fail_command(command_id, failure)

                return {
                    "success": False,
                    "replayed": False,
                    **failure,
                }

            except Exception:
                # Unexpected infrastructure errors should
                # remain retryable after the processing lease expires.
                self.commands.update_one(
                    {
                        "commandId": command_id,
                        "status": "processing"
                    },
                    {
                        "$set": {
                            "lockUntil": datetime.now(
                                timezone.utc
                            ),
                            "updatedAt": datetime.now(
                                timezone.utc
                            )
                        }
                    }
                )

                raise
