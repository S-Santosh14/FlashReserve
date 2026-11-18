import uuid

from datetime import datetime, timezone
from bson import ObjectId

from backend.services.payment_service import PaymentError


class RefundError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


class RefundService:

    STATUSES = ["processing", "success", "failed"]

    def __init__(self, database):

        self.database = database
        self.refunds = database["refunds"]
        self.bookings = database["bookings"]
        self.payments = database["payments"]

    # --------------------------------------------------
    # REQUEST VALIDATION
    # --------------------------------------------------

    def validate_request(self, booking_id, idempotency_key):

        if not ObjectId.is_valid(str(booking_id)):
            raise RefundError("Invalid booking ID")

        if not isinstance(idempotency_key, str):
            raise RefundError("Invalid idempotency key")

        idempotency_key = idempotency_key.strip()

        if not idempotency_key or len(idempotency_key) > 128:
            raise RefundError("Invalid idempotency key")

        return idempotency_key

    # --------------------------------------------------
    # CREATE REFUND
    # --------------------------------------------------

    def create_refund(
        self,
        booking_id,
        user_id,
        idempotency_key,
        outcome="success",
        *,
        refund_id=None,
        transaction_id=None,
        operation_time=None,
    ):

        if not ObjectId.is_valid(str(user_id)):
            raise RefundError("Invalid user ID")

        booking_id = ObjectId(str(booking_id))
        user_id = ObjectId(str(user_id))

        idempotency_key = self.validate_request(
            booking_id,
            idempotency_key
        )

        if outcome not in ["success", "failed"]:
            raise RefundError(
                "Refund outcome must be success or failed"
            )

        # 1. Check idempotency key.
        existing = self.refunds.find_one({
            "idempotencyKey": idempotency_key
        })

        if existing:

            if (
                existing["bookingId"] != booking_id
                or existing["userId"] != user_id
            ):
                raise RefundError(
                    "Idempotency key belongs to another refund",
                    409
                )

            return {
                "refund": existing,
                "replayed": True
            }

        # 2. Validate booking ownership.
        booking = self.bookings.find_one({
            "_id": booking_id,
            "userId": user_id
        })

        if not booking:
            raise RefundError("Booking not found", 404)

        if booking.get("status") != "cancelled":
            raise RefundError(
                "Only cancelled bookings can be refunded",
                409
            )

        # 3. Find successful payment.
        payment = self.payments.find_one({
            "bookingId": booking_id,
            "userId": user_id,
            "status": "success"
        })

        if not payment:
            raise RefundError(
                "No successful payment found for this booking",
                409
            )

        amount = payment["amount"]
        now = operation_time or datetime.now(timezone.utc)

        # 4. Create refund record.
        refund = {
            "_id": (
                ObjectId(refund_id)
                if isinstance(refund_id, str)
                else refund_id or ObjectId()
            ),
            "bookingId": booking_id,
            "userId": user_id,
            "amount": amount,
            "idempotencyKey": idempotency_key,
            "transactionId": transaction_id or (
                "REF-" + uuid.uuid4().hex.upper()
            ),
            "status": "processing",
            "createdAt": now,
            "updatedAt": now
        }

        try:
            self.refunds.insert_one(refund)

        except Exception as error:

            if getattr(error, "code", None) == 11000:

                existing = self.refunds.find_one({
                    "$or": [
                        {"bookingId": booking_id},
                        {"idempotencyKey": idempotency_key}
                    ]
                })

                if existing:
                    if (
                        existing["bookingId"] != booking_id
                        or existing["userId"] != user_id
                    ):
                        raise RefundError(
                            "A refund already exists for this booking",
                            409
                        )

                    return {
                        "refund": existing,
                        "replayed": True
                    }

            raise

        # 5. Simulate refund processing.
        final_status = outcome

        self.refunds.update_one(
            {
                "_id": refund["_id"],
                "status": "processing"
            },
            {
                "$set": {
                    "status": final_status,
                    "updatedAt": now
                }
            }
        )

        updated_refund = self.refunds.find_one({
            "_id": refund["_id"]
        })

        return {
            "refund": updated_refund,
            "replayed": False
        }

    # --------------------------------------------------
    # GET REFUND
    # --------------------------------------------------

    def get_refund(self, refund_id, user_id):

        if not ObjectId.is_valid(str(refund_id)):
            raise RefundError("Invalid refund ID")

        if not ObjectId.is_valid(str(user_id)):
            raise RefundError("Invalid user ID")

        refund = self.refunds.find_one({
            "_id": ObjectId(str(refund_id)),
            "userId": ObjectId(str(user_id))
        })

        if not refund:
            raise RefundError("Refund not found", 404)

        return refund

    # --------------------------------------------------
    # GET REFUND BY BOOKING
    # --------------------------------------------------

    def get_booking_refund(self, booking_id, user_id):

        if not ObjectId.is_valid(str(booking_id)):
            raise RefundError("Invalid booking ID")

        if not ObjectId.is_valid(str(user_id)):
            raise RefundError("Invalid user ID")

        refund = self.refunds.find_one({
            "bookingId": ObjectId(str(booking_id)),
            "userId": ObjectId(str(user_id))
        })

        if not refund:
            raise RefundError("Refund not found", 404)

        return refund