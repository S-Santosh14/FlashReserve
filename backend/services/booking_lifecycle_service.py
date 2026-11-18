from datetime import datetime, timedelta, timezone

from bson import ObjectId
from pymongo import ReturnDocument

from backend.models.booking import Booking


class BookingLifecycleError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


class BookingLifecycleService:

    LOCK_DURATION_MS = 5 * 60 * 1000
    CLEANUP_BATCH_SIZE = 100

    def __init__(self, database):
        self.database = database
        self.bookings = database["bookings"]
        self.seats = database["seats"]
        self.payments = database["payments"]

    # --------------------------------------------------
    # 1. BOOKING RETRIEVAL
    # --------------------------------------------------

    def get_user_bookings(self, user_id):

        if not ObjectId.is_valid(str(user_id)):
            raise BookingLifecycleError("Invalid user ID")

        user_id = ObjectId(str(user_id))

        bookings = list(
            self.bookings.find({
                "userId": user_id
            }).sort("createdAt", -1)
        )

        return bookings

    def get_booking(self, booking_id, user_id):

        if not ObjectId.is_valid(str(booking_id)):
            raise BookingLifecycleError("Invalid booking ID")

        if not ObjectId.is_valid(str(user_id)):
            raise BookingLifecycleError("Invalid user ID")

        booking = self.bookings.find_one({
            "_id": ObjectId(str(booking_id)),
            "userId": ObjectId(str(user_id))
        })

        if not booking:
            raise BookingLifecycleError(
                "Booking not found",
                404
            )

        return booking

    def get_booking_by_reference(self, booking_reference, user_id):

        if not isinstance(booking_reference, str) or not booking_reference.strip():
            raise BookingLifecycleError("Invalid booking reference")

        if not ObjectId.is_valid(str(user_id)):
            raise BookingLifecycleError("Invalid user ID")

        booking = self.bookings.find_one({
            "bookingReference": booking_reference.strip(),
            "userId": ObjectId(str(user_id))
        })

        if not booking:
            raise BookingLifecycleError(
                "Booking not found",
                404
            )

        return booking

    # --------------------------------------------------
    # 2. BOOKING CANCELLATION
    # --------------------------------------------------

    def cancel_booking(self, booking_id, user_id, *, operation_time=None):

        if not ObjectId.is_valid(str(booking_id)):
            raise BookingLifecycleError("Invalid booking ID")

        if not ObjectId.is_valid(str(user_id)):
            raise BookingLifecycleError("Invalid user ID")

        booking_id = ObjectId(str(booking_id))
        user_id = ObjectId(str(user_id))

        booking = self.bookings.find_one({
            "_id": booking_id,
            "userId": user_id
        })

        if not booking:
            raise BookingLifecycleError(
                "Booking not found",
                404
            )

        if booking["status"] not in ["confirmed", "cancelled"]:
            raise BookingLifecycleError(
                "Only confirmed bookings can be cancelled",
                409
            )

        now = operation_time or datetime.now(timezone.utc)

        # Idempotent cancellation: a retry must not
        # create another cancellation operation.
        if booking["status"] == "confirmed":

            updated = self.bookings.find_one_and_update(
                {
                    "_id": booking_id,
                    "userId": user_id,
                    "status": "confirmed"
                },
                {
                    "$set": {
                        "status": "cancelled",
                        "updatedAt": now
                    }
                },
                return_document=ReturnDocument.AFTER
            )

            if not updated:
                latest = self.bookings.find_one({
                    "_id": booking_id,
                    "userId": user_id
                })

                if not latest or latest["status"] != "cancelled":
                    raise BookingLifecycleError(
                        "Booking status changed. Please refresh and try again.",
                        409
                    )

        # Release seats belonging to this booking.
        seat_ids = booking.get("seats", [])

        self.seats.update_many(
            {
                "_id": {"$in": seat_ids},
                "bookingId": booking_id,
                "status": {"$in": ["reserved", "booked"]}
            },
            {
                "$set": {
                    "status": "available",
                    "reservedBy": None,
                    "reservedAt": None,
                    "reservationId": None,
                    "lockExpiresAt": None,
                    "bookingId": None,
                    "updatedAt": now
                }
            }
        )

        return self.bookings.find_one({
            "_id": booking_id
        })

    # --------------------------------------------------
    # 3. EXPIRED BOOKING CLEANUP
    # --------------------------------------------------

    def cleanup_expired_bookings(self, now=None, event_id=None):

        now = now or datetime.now(timezone.utc)

        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        event_filter = {}

        if event_id is not None:

            if not ObjectId.is_valid(str(event_id)):
                raise BookingLifecycleError("Invalid event ID")

            event_filter["eventId"] = ObjectId(str(event_id))

        # Find pending bookings whose expiry has passed.
        expired_bookings = list(
            self.bookings.find({
                **event_filter,
                "status": "pending",
                "$or": [
                    {"expiresAt": {"$lte": now}},
                    {"expiresAt": None}
                ]
            })
            .sort("_id", 1)
            .limit(self.CLEANUP_BATCH_SIZE)
        )

        # Find failed/expired bookings awaiting cleanup.
        terminal_bookings = list(
            self.bookings.find({
                **event_filter,
                "status": {"$in": ["failed", "expired"]},
                "cleanupCompletedAt": None
            })
            .limit(self.CLEANUP_BATCH_SIZE)
        )

        expired_ids = [
            booking["_id"]
            for booking in expired_bookings
        ]

        terminal_ids = [
            booking["_id"]
            for booking in terminal_bookings
        ]

        all_booking_ids = expired_ids + terminal_ids

        expired_seat_ids = []

        for booking in expired_bookings + terminal_bookings:
            expired_seat_ids.extend(booking.get("seats", []))

        # Legacy bookings without expiresAt use the
        # original five-minute reservation duration.
        legacy_cutoff = now - timedelta(
            milliseconds=self.LOCK_DURATION_MS
        )

        legacy_seat_ids = []

        for booking in expired_bookings:

            if not booking.get("expiresAt"):
                legacy_seat_ids.extend(
                    booking.get("seats", [])
                )

        # Release expired reservation locks and seats
        # associated with expired/terminal bookings.
        self.seats.update_many(
            {
                "$or": [
                    {
                        **event_filter,
                        "status": "reserved",
                        "lockExpiresAt": {"$lte": now}
                    },
                    {
                        **event_filter,
                        "status": "reserved",
                        "lockExpiresAt": None,
                        "reservedAt": {"$lte": legacy_cutoff}
                    },
                    {
                        "_id": {"$in": expired_seat_ids},
                        "bookingId": {"$in": all_booking_ids},
                        "status": {"$in": ["reserved", "booked"]}
                    },
                    {
                        "_id": {"$in": legacy_seat_ids},
                        "status": "booked",
                        "bookingId": None
                    }
                ]
            },
            {
                "$set": {
                    "status": "available",
                    "reservedBy": None,
                    "reservedAt": None,
                    "reservationId": None,
                    "lockExpiresAt": None,
                    "bookingId": None,
                    "updatedAt": now
                }
            }
        )

        # Mark pending bookings as expired.
        if expired_ids:

            self.bookings.update_many(
                {
                    "_id": {"$in": expired_ids},
                    "status": "pending",
                    "$or": [
                        {"expiresAt": {"$lte": now}},
                        {"expiresAt": None}
                    ]
                },
                {
                    "$set": {
                        "status": "expired",
                        "updatedAt": now
                    }
                }
            )

            # Pending/processing payments become timeout.
            self.payments.update_many(
                {
                    "bookingId": {"$in": expired_ids},
                    "status": {"$in": ["pending", "processing"]}
                },
                {
                    "$set": {
                        "status": "timeout",
                        "processingLockUntil": None,
                        "updatedAt": now
                    }
                }
            )

        # Reconcile failed and previously expired bookings.
        failed_ids = [
            booking["_id"]
            for booking in terminal_bookings
            if booking["status"] == "failed"
        ]

        previously_expired_ids = [
            booking["_id"]
            for booking in terminal_bookings
            if booking["status"] == "expired"
        ]

        if failed_ids:

            self.payments.update_many(
                {
                    "bookingId": {"$in": failed_ids},
                    "status": {"$in": ["pending", "processing"]}
                },
                {
                    "$set": {
                        "status": "failed",
                        "processingLockUntil": None,
                        "updatedAt": now
                    }
                }
            )

        if previously_expired_ids:

            self.payments.update_many(
                {
                    "bookingId": {"$in": previously_expired_ids},
                    "status": {"$in": ["pending", "processing"]}
                },
                {
                    "$set": {
                        "status": "timeout",
                        "processingLockUntil": None,
                        "updatedAt": now
                    }
                }
            )

        # Mark cleanup as completed.
        if terminal_ids:

            self.bookings.update_many(
                {
                    "_id": {"$in": terminal_ids},
                    "status": {"$in": ["failed", "expired"]},
                    "cleanupCompletedAt": None
                },
                {
                    "$set": {
                        "cleanupCompletedAt": now,
                        "updatedAt": now
                    }
                }
            )

        return {
            "expiredBookings": len(expired_ids),
            "cleanedTerminalBookings": len(terminal_ids)
        }