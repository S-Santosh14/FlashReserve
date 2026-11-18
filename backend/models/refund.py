from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from pymongo.errors import DuplicateKeyError

from backend.database.mongodb import get_database


class Refund:
    COLLECTION = "refunds"

    STATUSES = {"processing", "success", "failed"}

    @staticmethod
    def collection():
        db = get_database()
        return db[Refund.COLLECTION]

    @staticmethod
    def validate(data: dict) -> dict:
        required_fields = [
            "bookingId",
            "userId",
            "amount",
            "idempotencyKey",
            "transactionId",
        ]

        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValueError(f"{field} is required")

        if not ObjectId.is_valid(data["bookingId"]):
            raise ValueError("Invalid bookingId")

        if not ObjectId.is_valid(data["userId"]):
            raise ValueError("Invalid userId")

        try:
            amount = float(data["amount"])
        except (TypeError, ValueError):
            raise ValueError("amount must be a valid number")

        if amount < 0:
            raise ValueError("amount cannot be negative")

        idempotency_key = str(data["idempotencyKey"]).strip()
        transaction_id = str(data["transactionId"]).strip()

        if not idempotency_key:
            raise ValueError("idempotencyKey cannot be empty")

        if not transaction_id:
            raise ValueError("transactionId cannot be empty")

        status = data.get("status", "processing")

        if status not in Refund.STATUSES:
            raise ValueError(f"Invalid refund status: {status}")

        return {
            "bookingId": ObjectId(data["bookingId"]),
            "userId": ObjectId(data["userId"]),
            "amount": amount,
            "idempotencyKey": idempotency_key,
            "transactionId": transaction_id,
            "status": status,
        }

    @staticmethod
    def prepare(data: dict) -> dict:
        now = datetime.now(timezone.utc)

        refund = Refund.validate(data)

        refund["createdAt"] = now
        refund["updatedAt"] = now

        return refund

    @staticmethod
    def find_by_id(refund_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(refund_id):
            return None

        return Refund.collection().find_one(
            {"_id": ObjectId(refund_id)}
        )

    @staticmethod
    def find_by_booking(booking_id: str) -> Optional[dict]:
        if not ObjectId.is_valid(booking_id):
            return None

        return Refund.collection().find_one(
            {"bookingId": ObjectId(booking_id)}
        )

    @staticmethod
    def find_by_idempotency_key(key: str) -> Optional[dict]:
        return Refund.collection().find_one(
            {"idempotencyKey": key.strip()}
        )

    @staticmethod
    def find_by_transaction_id(transaction_id: str) -> Optional[dict]:
        return Refund.collection().find_one(
            {"transactionId": transaction_id.strip()}
        )

    @staticmethod
    def create(data: dict) -> dict:
        refund = Refund.prepare(data)

        try:
            result = Refund.collection().insert_one(refund)
            refund["_id"] = result.inserted_id
            return refund

        except DuplicateKeyError:
            raise ValueError(
                "A refund already exists for this booking, "
                "idempotency key, or transaction ID"
            )

    @staticmethod
    def update_status(refund_id: str, status: str) -> bool:
        if not ObjectId.is_valid(refund_id):
            return False

        if status not in Refund.STATUSES:
            raise ValueError(f"Invalid refund status: {status}")

        result = Refund.collection().update_one(
            {"_id": ObjectId(refund_id)},
            {
                "$set": {
                    "status": status,
                    "updatedAt": datetime.now(timezone.utc),
                }
            },
        )

        return result.modified_count > 0