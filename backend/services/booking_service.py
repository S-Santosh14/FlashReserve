import hashlib
import secrets

from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from backend.models.booking import Booking
from backend.models.event import Event
from backend.models.seat import Seat


class BookingError(Exception):

    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class BookingService:

    MAX_SEATS = 20

    def __init__(self, database):
        self.database = database

    @staticmethod
    def generate_reference():
        return "FR-" + secrets.token_hex(6).upper()

    @staticmethod
    def generate_request_id(user_id, reservation_id):
        identity = hashlib.sha256(
            f"{user_id}:{reservation_id}".encode()
        ).hexdigest()

        return f"booking:{identity}"

    @staticmethod
    def normalize_seats(seat_numbers):

        if not isinstance(seat_numbers, list) or not seat_numbers:
            raise BookingError(
                "Select at least one seat",
                400
            )

        if len(seat_numbers) > BookingService.MAX_SEATS:
            raise BookingError(
                "Provide up to 20 seats",
                400
            )

        if any(
            not isinstance(seat, str) or not seat.strip()
            for seat in seat_numbers
        ):
            raise BookingError(
                "Invalid seat numbers",
                400
            )

        seats = [seat.strip() for seat in seat_numbers]

        if len(set(seats)) != len(seats):
            raise BookingError(
                "Duplicate seat numbers are not allowed",
                400
            )

        return seats

    def matches_booking(self, booking, event_id, seat_numbers, amount):

        booked_seats = []
        seat_ids = []

        for seat in booking.get("seats", []):

            if isinstance(seat, dict):
                booked_seats.append(seat["seatNumber"])
            else:
                if not ObjectId.is_valid(str(seat)):
                    return False
                seat_ids.append(ObjectId(str(seat)))

        if seat_ids:
            if len(set(seat_ids)) != len(seat_ids):
                return False
            seats = list(Seat.collection(self.database).find({
                "_id": {"$in": seat_ids},
                "eventId": ObjectId(str(event_id)),
            }))
            if len(seats) != len(seat_ids):
                return False
            booked_seats.extend(seat["seatNumber"] for seat in seats)

        return (
            str(booking["eventId"]) == str(event_id)
            and booking["totalAmount"] == amount
            and sorted(booked_seats) == sorted(seat_numbers)
        )

    def create_booking(
        self,
        user_id,
        event_id,
        seat_numbers,
        total_amount,
        reservation_id=None,
        *,
        booking_id=None,
        booking_reference=None,
        operation_time=None,
    ):

        if not ObjectId.is_valid(user_id):
            raise BookingError("Invalid user ID", 400)

        if not ObjectId.is_valid(event_id):
            raise BookingError("Invalid event ID", 400)

        if (
            isinstance(total_amount, bool)
            or not isinstance(total_amount, (int, float))
            or total_amount < 0
        ):
            raise BookingError("Invalid total amount", 400)

        seat_numbers = self.normalize_seats(seat_numbers)

        user_id = ObjectId(user_id)
        event_id = ObjectId(event_id)

        if reservation_id is not None:

            if (
                not isinstance(reservation_id, str)
                or len(reservation_id) > 128
            ):
                raise BookingError(
                    "reservationId must be a string of at most 128 characters",
                    400
                )

            if not reservation_id:
                raise BookingError(
                    "Invalid reservation ID",
                    400
                )

        # ----------------------------------
        # CHECK EVENT
        # ----------------------------------

        event = Event.find_by_id(
            self.database,
            event_id
        )

        if not event:
            raise BookingError("Event not found", 404)

        booking_collection = Booking.collection(self.database)
        if reservation_id:
            existing = booking_collection.find_one({
                "userId": user_id,
                "reservationId": reservation_id,
            })
            if existing:
                if not self.matches_booking(
                    existing, event_id, seat_numbers, total_amount
                ):
                    raise BookingError(
                        "This reservation was already used for a different booking request",
                        409
                    )
                return {
                    "success": True,
                    "replayed": True,
                    "data": existing,
                }

        if event.get("status") == "archived":
            raise BookingError(
                "This event is archived and cannot receive bookings",
                409
            )

        expected_amount = event["price"] * len(seat_numbers)

        if total_amount != expected_amount:
            raise BookingError(
                "Booking amount does not match event price",
                400
            )

        now = operation_time or datetime.now(timezone.utc)

        # ----------------------------------
        # RELEASE EXPIRED SEAT LOCKS
        # ----------------------------------

        Seat.collection(self.database).update_many(
            {
                "eventId": event_id,
                "status": "reserved",
                "$or": [
                    {"lockExpiresAt": {"$lte": now}},
                    {"lockExpiresAt": None},
                ],
            },
            {
                "$set": {
                    "status": "available",
                    "reservedBy": None,
                    "reservedAt": None,
                    "reservationId": None,
                    "lockExpiresAt": None,
                    "bookingId": None,
                    "updatedAt": now,
                }
            }
        )

        # ----------------------------------
        # RESOLVE RESERVATION ID
        # ----------------------------------

        seat_collection = Seat.collection(self.database)

        if not reservation_id:

            active_reservations = seat_collection.distinct(
                "reservationId",
                {
                    "eventId": event_id,
                    "seatNumber": {"$in": seat_numbers},
                    "status": "reserved",
                    "reservedBy": user_id,
                    "bookingId": None,
                    "lockExpiresAt": {"$gt": now},
                }
            )

            if len(active_reservations) != 1:
                raise BookingError(
                    "Reserve all selected seats together before creating a booking",
                    409
                )

            reservation_id = active_reservations[0]

        # ----------------------------------
        # IDEMPOTENCY CHECK
        # ----------------------------------

        booking_collection = Booking.collection(self.database)

        existing = booking_collection.find_one({
            "userId": user_id,
            "reservationId": reservation_id,
        })

        if existing:

            if not self.matches_booking(
                existing,
                event_id,
                seat_numbers,
                total_amount
            ):
                raise BookingError(
                    "This reservation was already used for a different booking request",
                    409
                )

            return {
                "success": True,
                "replayed": True,
                "data": existing,
            }

        # ----------------------------------
        # VERIFY SEAT HOLDS
        # ----------------------------------

        held_seats = list(
            seat_collection.find({
                "eventId": event_id,
                "seatNumber": {"$in": seat_numbers},
                "status": "reserved",
                "reservedBy": user_id,
                "reservationId": reservation_id,
                "bookingId": None,
                "lockExpiresAt": {"$gt": now},
            })
        )

        if len(held_seats) != len(seat_numbers):
            raise BookingError(
                "All requested seats must be held by you before checkout",
                409
            )

        expires_at = min(
            seat["lockExpiresAt"]
            for seat in held_seats
        )

        if booking_id is None:
            booking_id = ObjectId()
        elif isinstance(booking_id, str):
            if not ObjectId.is_valid(booking_id):
                raise BookingError("Invalid deterministic booking ID", 400)
            booking_id = ObjectId(booking_id)

        booking_reference = booking_reference or self.generate_reference()

        booking_document = {
            "_id": booking_id,
            "userId": user_id,
            "eventId": event_id,
            "seats": [
                seat["_id"] for seat in held_seats
            ],
            "totalAmount": expected_amount,
            "reservationId": reservation_id,
            "bookingReference": booking_reference,
            "paymentId": None,
            "refundId": None,
            "expiresAt": expires_at,
            "cleanupCompletedAt": None,
            "status": "pending",
            "createdAt": now,
            "updatedAt": now,
        }

        # ----------------------------------
        # ATOMIC BOOKING CREATION
        # ----------------------------------

        client = self.database.client

        try:

            with client.start_session() as session:

                with session.start_transaction():

                    # Recheck holds inside the transaction.
                    valid_seats = list(
                        seat_collection.find(
                            {
                                "_id": {
                                    "$in": [
                                        seat["_id"]
                                        for seat in held_seats
                                    ]
                                },
                                "eventId": event_id,
                                "status": "reserved",
                                "reservedBy": user_id,
                                "reservationId": reservation_id,
                                "bookingId": None,
                                "lockExpiresAt": {"$gt": now},
                            },
                            session=session,
                        )
                    )

                    if len(valid_seats) != len(seat_numbers):
                        raise BookingError(
                            "Seat holds expired or changed. Please select your seats again",
                            409
                        )

                    booking_collection.insert_one(
                        booking_document,
                        session=session
                    )

                    claimed = seat_collection.update_many(
                        {
                            "_id": {
                                "$in": [
                                    seat["_id"]
                                    for seat in held_seats
                                ]
                            },
                            "status": "reserved",
                            "reservedBy": user_id,
                            "reservationId": reservation_id,
                            "bookingId": None,
                            "lockExpiresAt": {"$gt": now},
                        },
                        {
                            "$set": {
                                "bookingId": booking_id,
                                "updatedAt": now,
                            }
                        },
                        session=session,
                    )

                    if claimed.modified_count != len(seat_numbers):
                        raise BookingError(
                            "Seat holds expired or changed. Please select your seats again",
                            409
                        )

            return {
                "success": True,
                "replayed": False,
                "data": booking_document,
            }

        except DuplicateKeyError:

            duplicate = booking_collection.find_one({
                "userId": user_id,
                "reservationId": reservation_id,
            })

            if duplicate and self.matches_booking(
                duplicate,
                event_id,
                seat_numbers,
                total_amount
            ):
                return {
                    "success": True,
                    "replayed": True,
                    "data": duplicate,
                }

            raise BookingError(
                "Reservation has already been used",
                409
            )