import uuid
import hashlib

from datetime import datetime, timedelta, timezone

from bson import ObjectId
from pymongo import ReturnDocument

from backend.models.payment import Payment


class PaymentError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


class PaymentService:

    METHODS = [
        "UPI",
        "CARD",
        "NET_BANKING",
        "WALLET"
    ]

    OUTCOMES = [
        "success",
        "failed",
        "pending",
        "timeout"
    ]

    PROCESSING_LOCK_SECONDS = 60

    def __init__(self, database):

        self.database = database

        self.payments = database["payments"]
        self.bookings = database["bookings"]
        self.seats = database["seats"]

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    def validate_request(
        self,
        booking_id,
        amount,
        idempotency_key,
        method,
        outcome
    ):

        if not ObjectId.is_valid(str(booking_id)):
            raise PaymentError("Invalid booking ID")

        if (
            isinstance(amount, bool)
            or not isinstance(amount, (int, float))
            or amount < 0
        ):
            raise PaymentError("Invalid payment amount")

        if not isinstance(idempotency_key, str):
            raise PaymentError("Invalid idempotency key")

        idempotency_key = idempotency_key.strip()

        if not idempotency_key or len(idempotency_key) > 128:
            raise PaymentError(
                "A valid idempotency key of at most 128 characters is required"
            )

        if method not in self.METHODS:
            raise PaymentError(
                "Method must be UPI, CARD, NET_BANKING, or WALLET"
            )

        if outcome not in self.OUTCOMES:
            raise PaymentError(
                "Outcome must be success, failed, pending, or timeout"
            )

        return idempotency_key

    # --------------------------------------------------
    # IDEMPOTENCY
    # --------------------------------------------------

    def find_idempotent_payment(self, request):

        payment = self.payments.find_one({
            "idempotencyKey": request["idempotencyKey"]
        })

        if not payment:
            return None

        same_request = (
            payment["userId"] == request["userId"]
            and payment["bookingId"] == request["bookingId"]
            and payment["amount"] == request["amount"]
            and payment["method"] == request["method"]
            and payment["mockOutcome"] == request["outcome"]
        )

        if not same_request:
            raise PaymentError(
                "This idempotency key was already used for a different payment",
                409
            )

        booking = self.bookings.find_one({
            "_id": payment["bookingId"],
            "userId": request["userId"]
        })

        return {
            "payment": payment,
            "booking": booking,
            "replayed": True
        }

    # --------------------------------------------------
    # RELEASE BOOKING SEATS
    # --------------------------------------------------

    def release_booking_seats(self, booking_id, operation_time=None):

        now = operation_time or datetime.now(timezone.utc)

        self.seats.update_many(
            {
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

    # --------------------------------------------------
    # MOCK PAYMENT
    # --------------------------------------------------

    def process_mock_payment(
        self,
        booking_id,
        user_id,
        amount,
        idempotency_key,
        method="UPI",
        outcome="success",
        *,
        payment_id=None,
        transaction_id=None,
        operation_time=None,
    ):

        if not ObjectId.is_valid(str(user_id)):
            raise PaymentError("Invalid user ID")

        user_id = ObjectId(str(user_id))
        booking_id = ObjectId(str(booking_id))

        idempotency_key = self.validate_request(
            booking_id,
            amount,
            idempotency_key,
            method,
            outcome
        )

        request = {
            "bookingId": booking_id,
            "userId": user_id,
            "amount": amount,
            "idempotencyKey": idempotency_key,
            "method": method,
            "outcome": outcome
        }

        # 1. Check for an existing idempotent request.
        existing = self.find_idempotent_payment(request)

        if existing and existing["payment"]["status"] != "processing":
            return existing

        now = operation_time or datetime.now(timezone.utc)

        # 2. Validate booking ownership.
        booking = self.bookings.find_one({
            "_id": booking_id,
            "userId": user_id
        })

        if not booking:
            raise PaymentError("Booking not found", 404)

        if booking["totalAmount"] != amount:
            raise PaymentError(
                "Payment amount does not match booking total"
            )

        # 3. Create payment if one does not exist.
        payment = existing["payment"] if existing else None

        if not payment:

            payment = {
                "_id": (
                    ObjectId(payment_id)
                    if isinstance(payment_id, str)
                    else payment_id or ObjectId()
                ),
                "bookingId": booking_id,
                "userId": user_id,
                "amount": amount,
                "transactionId": transaction_id or f"MOCK-{uuid.uuid4().hex.upper()}",
                "idempotencyKey": idempotency_key,
                "method": method,
                "mockOutcome": outcome,
                "status": "processing",
                "processingLockUntil": None,
                "createdAt": now,
                "updatedAt": now
            }

            try:
                self.payments.insert_one(payment)

            except Exception as error:

                if getattr(error, "code", None) != 11000:
                    raise

                existing = self.find_idempotent_payment(request)

                if not existing:
                    raise

                if existing["payment"]["status"] != "processing":
                    return existing

                payment = existing["payment"]

        # 4. Acquire processing lock.
        lock_until = now + timedelta(
            seconds=self.PROCESSING_LOCK_SECONDS
        )

        locked_payment = self.payments.find_one_and_update(
            {
                "_id": payment["_id"],
                "status": "processing",
                "$or": [
                    {"processingLockUntil": None},
                    {"processingLockUntil": {"$lte": now}}
                ]
            },
            {
                "$set": {
                    "processingLockUntil": lock_until,
                    "updatedAt": now
                }
            },
            return_document=ReturnDocument.AFTER
        )

        if not locked_payment:

            return {
                "payment": self.payments.find_one({
                    "_id": payment["_id"]
                }),
                "booking": booking,
                "replayed": True
            }

        payment = locked_payment

        # 5. Link payment to pending booking.
        booking = self.bookings.find_one_and_update(
            {
                "_id": booking_id,
                "userId": user_id,
                "status": "pending",
                "paymentId": None,
                "expiresAt": {"$gt": now}
            },
            {
                "$set": {
                    "paymentId": payment["_id"],
                    "updatedAt": now
                }
            },
            return_document=ReturnDocument.AFTER
        )

        if not booking:

            booking = self.bookings.find_one({
                "_id": booking_id,
                "userId": user_id,
                "status": "pending",
                "paymentId": payment["_id"],
                "expiresAt": {"$gt": now}
            })

        if not booking:

            self.payments.update_one(
                {
                    "_id": payment["_id"],
                    "status": "processing"
                },
                {
                    "$set": {
                        "status": "failed",
                        "processingLockUntil": None,
                        "updatedAt": now
                    }
                }
            )

            raise PaymentError(
                "The booking is no longer available for payment",
                409
            )

        # 6. Pending outcome.
        if outcome == "pending":

            self.payments.update_one(
                {"_id": payment["_id"], "status": "processing"},
                {
                    "$set": {
                        "status": "pending",
                        "processingLockUntil": None,
                        "updatedAt": now
                    }
                }
            )

            return {
                "payment": self.payments.find_one({
                    "_id": payment["_id"]
                }),
                "booking": booking,
                "replayed": False
            }

        # 7. Failed or timeout outcome.
        if outcome in ["failed", "timeout"]:

            booking_status = (
                "expired" if outcome == "timeout" else "failed"
            )

            self.bookings.update_one(
                {
                    "_id": booking_id,
                    "status": "pending",
                    "paymentId": payment["_id"]
                },
                {
                    "$set": {
                        "status": booking_status,
                        "updatedAt": now
                    }
                }
            )

            self.release_booking_seats(booking_id, operation_time=now)

            self.payments.update_one(
                {
                    "_id": payment["_id"],
                    "status": "processing"
                },
                {
                    "$set": {
                        "status": outcome,
                        "processingLockUntil": None,
                        "updatedAt": now
                    }
                }
            )

            return {
                "payment": self.payments.find_one({
                    "_id": payment["_id"]
                }),
                "booking": self.bookings.find_one({
                    "_id": booking_id
                }),
                "replayed": False
            }

        # 8. Successful payment.
        return self._complete_successful_payment(
            booking,
            payment,
            now
        )

    # --------------------------------------------------
    # SUCCESSFUL PAYMENT
    # --------------------------------------------------

    def _complete_successful_payment(
        self,
        booking,
        payment,
        now
    ):

        booking_id = booking["_id"]
        payment_id = payment["_id"]

        seat_ids = booking.get("seats", [])

        try:

            with self.database.client.start_session() as session:

                with session.start_transaction():

                    # Confirm all reserved seats.
                    result = self.seats.update_many(
                        {
                            "_id": {"$in": seat_ids},
                            "bookingId": booking_id,
                            "status": "reserved",
                            "lockExpiresAt": {"$gt": now}
                        },
                        {
                            "$set": {
                                "status": "booked",
                                "reservedBy": None,
                                "reservedAt": None,
                                "reservationId": None,
                                "lockExpiresAt": None,
                                "updatedAt": now
                            }
                        },
                        session=session
                    )

                    if result.modified_count != len(seat_ids):
                        raise PaymentError(
                            "One or more reserved seats expired before payment completed",
                            409
                        )

                    # Confirm booking.
                    booking_result = self.bookings.update_one(
                        {
                            "_id": booking_id,
                            "status": "pending",
                            "paymentId": payment_id,
                            "expiresAt": {"$gt": now}
                        },
                        {
                            "$set": {
                                "status": "confirmed",
                                "updatedAt": now
                            }
                        },
                        session=session
                    )

                    if booking_result.modified_count != 1:
                        raise PaymentError(
                            "Booking expired before payment completed",
                            409
                        )

                    # Complete payment.
                    payment_result = self.payments.update_one(
                        {
                            "_id": payment_id,
                            "status": "processing"
                        },
                        {
                            "$set": {
                                "status": "success",
                                "processingLockUntil": None,
                                "updatedAt": now
                            }
                        },
                        session=session
                    )

                    if payment_result.modified_count != 1:
                        raise PaymentError(
                            "Payment status changed before confirmation",
                            409
                        )

        except PaymentError:
            raise

        except Exception:
            # Do not silently report success if the transaction fails.
            raise

        return {
            "payment": self.payments.find_one({
                "_id": payment_id
            }),
            "booking": self.bookings.find_one({
                "_id": booking_id
            }),
            "replayed": False
        }

    # --------------------------------------------------
    # PAYMENT RETRIEVAL
    # --------------------------------------------------

    def get_payment(self, payment_id, user_id):

        if not ObjectId.is_valid(str(payment_id)):
            raise PaymentError("Invalid payment ID")

        if not ObjectId.is_valid(str(user_id)):
            raise PaymentError("Invalid user ID")

        payment = self.payments.find_one({
            "_id": ObjectId(str(payment_id)),
            "userId": ObjectId(str(user_id))
        })

        if not payment:
            raise PaymentError("Payment not found", 404)

        return payment

    def get_booking_payments(self, booking_id, user_id):

        if not ObjectId.is_valid(str(booking_id)):
            raise PaymentError("Invalid booking ID")

        if not ObjectId.is_valid(str(user_id)):
            raise PaymentError("Invalid user ID")

        booking = self.bookings.find_one({
            "_id": ObjectId(str(booking_id)),
            "userId": ObjectId(str(user_id))
        })

        if not booking:
            raise PaymentError("Booking not found", 404)

        return list(
            self.payments.find({
                "bookingId": booking["_id"],
                "userId": booking["userId"]
            }).sort("createdAt", -1)
        )