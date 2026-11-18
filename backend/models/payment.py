from datetime import datetime, timezone

from bson import ObjectId


class Payment:

    COLLECTION = "payments"

    METHODS = [
        "UPI",
        "CARD",
        "NET_BANKING",
        "WALLET"
    ]

    MOCK_OUTCOMES = [
        "success",
        "failed",
        "pending",
        "timeout"
    ]

    STATUSES = [
        "processing",
        "pending",
        "success",
        "failed",
        "timeout"
    ]

    @staticmethod
    def validate(data):

        required_fields = [
            "bookingId",
            "userId",
            "amount",
            "transactionId",
            "idempotencyKey",
            "method",
            "mockOutcome"
        ]

        for field in required_fields:

            if field not in data or data[field] is None:

                raise ValueError(
                    f"{field} is required"
                )

        # Validate ObjectIds
        for field in ["bookingId", "userId"]:

            value = data[field]

            if isinstance(value, str):

                if not ObjectId.is_valid(value):

                    raise ValueError(
                        f"Invalid {field}"
                    )

            elif not isinstance(value, ObjectId):

                raise ValueError(
                    f"{field} must be an ObjectId"
                )

        # Validate amount
        amount = data["amount"]

        if isinstance(amount, bool) or not isinstance(
            amount, (int, float)
        ):

            raise ValueError(
                "amount must be a number"
            )

        if amount < 0:

            raise ValueError(
                "amount cannot be negative"
            )

        # Validate transaction ID
        transaction_id = data["transactionId"]

        if not isinstance(transaction_id, str):

            raise ValueError(
                "transactionId must be a string"
            )

        if not transaction_id.strip():

            raise ValueError(
                "transactionId cannot be empty"
            )

        # Validate idempotency key
        idempotency_key = data["idempotencyKey"]

        if not isinstance(idempotency_key, str):

            raise ValueError(
                "idempotencyKey must be a string"
            )

        if not idempotency_key.strip():

            raise ValueError(
                "idempotencyKey cannot be empty"
            )

        # Validate payment method
        if data["method"] not in Payment.METHODS:

            raise ValueError(
                "Invalid payment method"
            )

        # Validate mock outcome
        if data["mockOutcome"] not in Payment.MOCK_OUTCOMES:

            raise ValueError(
                "Invalid mock payment outcome"
            )

        # Validate payment status
        status = data.get("status", "processing")

        if status not in Payment.STATUSES:

            raise ValueError(
                "Invalid payment status"
            )

        return True

    @staticmethod
    def prepare(data):

        Payment.validate(data)

        now = datetime.now(timezone.utc)

        def convert_object_id(value):

            if isinstance(value, str):

                return ObjectId(value)

            return value

        return {

            "bookingId": convert_object_id(
                data["bookingId"]
            ),

            "userId": convert_object_id(
                data["userId"]
            ),

            "amount": data["amount"],

            "transactionId": (
                data["transactionId"].strip()
            ),

            "idempotencyKey": (
                data["idempotencyKey"].strip()
            ),

            "method": data["method"],

            "mockOutcome": data["mockOutcome"],

            "status": data.get(
                "status",
                "processing"
            ),

            "processingLockUntil": data.get(
                "processingLockUntil"
            ),

            "createdAt": data.get(
                "createdAt",
                now
            ),

            "updatedAt": data.get(
                "updatedAt",
                now
            )
        }

    @staticmethod
    def collection(database):

        return database[Payment.COLLECTION]

    @staticmethod
    def find_by_id(database, payment_id):

        if isinstance(payment_id, str):

            payment_id = ObjectId(payment_id)

        return Payment.collection(database).find_one({
            "_id": payment_id
        })

    @staticmethod
    def find_by_transaction_id(database, transaction_id):

        return Payment.collection(database).find_one({
            "transactionId": transaction_id.strip()
        })

    @staticmethod
    def find_by_idempotency_key(database, idempotency_key):

        return Payment.collection(database).find_one({
            "idempotencyKey": idempotency_key.strip()
        })

    @staticmethod
    def find_by_booking(database, booking_id):

        if isinstance(booking_id, str):

            booking_id = ObjectId(booking_id)

        return list(
            Payment.collection(database).find({
                "bookingId": booking_id
            }).sort("createdAt", -1)
        )

    @staticmethod
    def find_by_user(database, user_id):

        if isinstance(user_id, str):

            user_id = ObjectId(user_id)

        return list(
            Payment.collection(database).find({
                "userId": user_id
            }).sort("createdAt", -1)
        )

    @staticmethod
    def create(database, data):

        document = Payment.prepare(data)

        result = Payment.collection(database).insert_one(
            document
        )

        return result.inserted_id

    @staticmethod
    def update_status(database, payment_id, status):

        if status not in Payment.STATUSES:

            raise ValueError(
                "Invalid payment status"
            )

        if isinstance(payment_id, str):

            payment_id = ObjectId(payment_id)

        return Payment.collection(database).update_one(

            {"_id": payment_id},

            {
                "$set": {
                    "status": status,
                    "updatedAt": datetime.now(timezone.utc)
                }
            }
        )