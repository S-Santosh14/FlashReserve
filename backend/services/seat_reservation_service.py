import uuid

from datetime import datetime, timedelta, timezone

from pymongo import ReturnDocument

from backend.models.seat import Seat
from backend.models.booking import Booking


class ReservationError(Exception):

    def __init__(self, message, status_code=409):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class SeatReservationService:

    LOCK_DURATION_MS = 5 * 60 * 1000

    def __init__(self, database):
        self.database = database

    @staticmethod
    def utc_now():
        return datetime.now(timezone.utc)

    # -----------------------------------------
    # RELEASE EXPIRED RESERVATIONS
    # -----------------------------------------

    def release_expired_locks(self, now=None, event_id=None):

        now = now or self.utc_now()

        query = {
            "status": "reserved",
            "$or": [
                {"lockExpiresAt": {"$lte": now}},
                {
                    "lockExpiresAt": None,
                    "reservedAt": {
                        "$lte": now - timedelta(
                            milliseconds=self.LOCK_DURATION_MS
                        )
                    }
                }
            ]
        }

        if event_id:
            query["eventId"] = event_id

        result = Seat.collection(
            self.database
        ).update_many(
            query,
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

        return result.modified_count

    # -----------------------------------------
    # RESERVATION VALIDATION
    # -----------------------------------------

    def validate_request(self, event_id, seat_numbers, user_id):

        from bson import ObjectId

        if not ObjectId.is_valid(event_id):
            raise ReservationError(
                "Invalid event ID",
                400
            )

        if not ObjectId.is_valid(user_id):
            raise ReservationError(
                "Invalid user ID",
                400
            )

        if not isinstance(seat_numbers, list) or not seat_numbers:
            raise ReservationError(
                "Select at least one seat",
                400
            )

        if len(seat_numbers) > 20:
            raise ReservationError(
                "You can reserve a maximum of 20 seats",
                400
            )

        if any(
            not isinstance(seat, str) or not seat.strip()
            for seat in seat_numbers
        ):
            raise ReservationError(
                "Invalid seat numbers",
                400
            )

        seat_numbers = [
            seat.strip()
            for seat in seat_numbers
        ]

        if len(set(seat_numbers)) != len(seat_numbers):
            raise ReservationError(
                "Duplicate seat numbers are not allowed",
                400
            )

        return seat_numbers

    # -----------------------------------------
    # RESERVE SEATS
    # -----------------------------------------

    def reserve_seats(
        self,
        event_id,
        seat_numbers,
        user_id,
        reservation_id=None,
        *,
        operation_time=None,
    ):

        from bson import ObjectId

        seat_numbers = self.validate_request(
            event_id,
            seat_numbers,
            user_id
        )

        event_id = ObjectId(event_id)
        user_id = ObjectId(user_id)

        now = operation_time or self.utc_now()

        expires_at = now + timedelta(
            milliseconds=self.LOCK_DURATION_MS
        )

        lock_id = reservation_id or str(uuid.uuid4())

        if not isinstance(lock_id, str) or not lock_id or len(lock_id) > 128:
            raise ReservationError(
                "Invalid reservation ID",
                400
            )

        # Release expired locks before processing.
        self.release_expired_locks(
            now,
            event_id
        )

        # A reservation already used for a booking cannot be reused.
        existing_booking = Booking.collection(
            self.database
        ).find_one({
            "userId": user_id,
            "reservationId": lock_id,
        })

        if existing_booking:
            raise ReservationError(
                "This reservation already has a booking. Start a new reservation.",
                409
            )

        seat_collection = Seat.collection(
            self.database
        )

        # Ensure every requested seat exists.
        current_seats = list(
            seat_collection.find({
                "eventId": event_id,
                "seatNumber": {
                    "$in": seat_numbers
                }
            })
        )

        if len(current_seats) != len(seat_numbers):
            raise ReservationError(
                "One or more selected seats do not exist",
                404
            )

        # Validate seat availability before claiming.
        for seat in current_seats:

            if seat.get("bookingId"):
                raise ReservationError(
                    f"Seat {seat['seatNumber']} is unavailable",
                    409
                )

            if seat["status"] == "available":
                continue

            lock_expires_at = seat.get("lockExpiresAt")
            if lock_expires_at is not None and lock_expires_at.tzinfo is None:
                lock_expires_at = lock_expires_at.replace(tzinfo=timezone.utc)

            same_owner = (
                seat["status"] == "reserved"
                and seat.get("reservationId") == lock_id
                and seat.get("reservedBy") == user_id
                and lock_expires_at
                and lock_expires_at > now
            )

            expired = (
                seat["status"] == "reserved"
                and (
                    lock_expires_at is None
                    or lock_expires_at <= now
                )
            )

            if not same_owner and not expired:
                raise ReservationError(
                    f"Seat {seat['seatNumber']} is already reserved or unavailable",
                    409
                )

        # Remove seats from an older selection using this reservation ID.
        seat_collection.update_many(
            {
                "eventId": event_id,
                "reservationId": lock_id,
                "reservedBy": user_id,
                "status": "reserved",
                "bookingId": None,
                "seatNumber": {
                    "$nin": seat_numbers
                }
            },
            {
                "$set": {
                    "status": "available",
                    "reservedBy": None,
                    "reservedAt": None,
                    "reservationId": None,
                    "lockExpiresAt": None,
                    "updatedAt": now,
                }
            }
        )

        claimed_seats = []

        try:

            # Each update is atomic at the individual document level.
            for seat_number in seat_numbers:

                claimed = seat_collection.find_one_and_update(
                    {
                        "eventId": event_id,
                        "seatNumber": seat_number,
                        "bookingId": None,
                        "$or": [
                            {
                                "status": "available"
                            },
                            {
                                "status": "reserved",
                                "lockExpiresAt": {
                                    "$lte": now
                                }
                            },
                            {
                                "status": "reserved",
                                "lockExpiresAt": None
                            },
                            {
                                "status": "reserved",
                                "reservationId": lock_id,
                                "reservedBy": user_id,
                                "lockExpiresAt": {
                                    "$gt": now
                                }
                            }
                        ]
                    },
                    {
                        "$set": {
                            "status": "reserved",
                            "reservedBy": user_id,
                            "reservedAt": now,
                            "reservationId": lock_id,
                            "lockExpiresAt": expires_at,
                            "updatedAt": now,
                        }
                    },
                    return_document=ReturnDocument.AFTER
                )

                if claimed is None:
                    raise ReservationError(
                        f"Seat {seat_number} could not be reserved. Please try again.",
                        409
                    )

                claimed_seats.append(claimed)

            # Verify the entire selection.
            final_seats = list(
                seat_collection.find({
                    "eventId": event_id,
                    "seatNumber": {
                        "$in": seat_numbers
                    },
                    "status": "reserved",
                    "reservedBy": user_id,
                    "reservationId": lock_id,
                    "bookingId": None,
                    "lockExpiresAt": {
                        "$gt": operation_time if operation_time is not None else self.utc_now()
                    }
                }).sort("seatNumber", 1)
            )

            if len(final_seats) != len(seat_numbers):
                raise ReservationError(
                    "The selected seats could not be reserved together",
                    409
                )

            return {
                "success": True,
                "reservationId": lock_id,
                "expiresAt": expires_at,
                "seats": final_seats,
                "message": "Seats reserved successfully"
            }

        except Exception:

            # Compensation: release only this user's claims.
            seat_collection.update_many(
                {
                    "eventId": event_id,
                    "reservationId": lock_id,
                    "reservedBy": user_id,
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
                        "updatedAt": operation_time if operation_time is not None else self.utc_now(),
                    }
                }
            )

            raise