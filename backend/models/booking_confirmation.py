from datetime import datetime, timezone

from bson import ObjectId


class BookingConfirmation:

    COLLECTION = "bookingconfirmations"

    STATUSES = [
        "pending",
        "sending",
        "sent",
        "failed",
        "delivery_unknown"
    ]

    DELIVERY_OUTCOMES = [
        "claimed",
        "sending",
        "accepted",
        "rejected",
        "unknown",
        "not_sent"
    ]

    DELIVERY_REQUIRED = [
        "attemptId",
        "claimedAt",
        "outcome"
    ]

    RECOVERY_REQUIRED = [
        "recoveredAt",
        "previousAttempts",
        "previousError",
        "reason"
    ]

    REQUIRED_FIELDS = [
        "bookingId",
        "bookingReference",
        "messageId",
        "recipientEmail",
        "customerName",
        "eventName",
        "eventDate",
        "eventTime",
        "venue",
        "seats",
        "ticketQuantity",
        "ticketPrice",
        "totalAmount",
        "paymentStatus",
        "confirmedAt"
    ]

    @staticmethod
    def validate_delivery_attempt(attempt):

        for field in BookingConfirmation.DELIVERY_REQUIRED:

            if field not in attempt or attempt[field] is None:
                raise ValueError(
                    f"Delivery attempt: {field} is required"
                )

        if attempt["outcome"] not in (
            BookingConfirmation.DELIVERY_OUTCOMES
        ):
            raise ValueError("Invalid delivery outcome")

        if not isinstance(attempt["attemptId"], str):
            raise ValueError("attemptId must be a string")

        return True

    @staticmethod
    def validate_recovery_history(history):

        for field in BookingConfirmation.RECOVERY_REQUIRED:

            if field not in history or history[field] is None:
                raise ValueError(
                    f"Recovery history: {field} is required"
                )

        if isinstance(history["previousAttempts"], bool):
            raise ValueError("previousAttempts must be a number")

        if not isinstance(history["previousAttempts"], (int, float)):
            raise ValueError("previousAttempts must be a number")

        return True

    @staticmethod
    def validate_cancellation(cancellation):

        required_fields = [
            "messageId",
            "recipientEmail",
            "customerName",
            "eventName",
            "eventDate",
            "eventTime",
            "venue",
            "bookingReference",
            "seats",
            "ticketQuantity",
            "originalAmount",
            "cancelledAt",
            "cancellationStatus"
        ]

        for field in required_fields:

            if field not in cancellation or cancellation[field] is None:
                raise ValueError(
                    f"Cancellation: {field} is required"
                )

        for field in [
            "messageId",
            "recipientEmail",
            "customerName",
            "eventName",
            "eventDate",
            "eventTime",
            "venue",
            "bookingReference",
            "cancellationStatus"
        ]:

            if not isinstance(cancellation[field], str):
                raise ValueError(
                    f"Cancellation: {field} must be a string"
                )

        if not isinstance(cancellation["seats"], list):
            raise ValueError("Cancellation seats must be a list")

        if isinstance(cancellation["ticketQuantity"], bool):
            raise ValueError("ticketQuantity must be a number")

        if not isinstance(cancellation["ticketQuantity"], (int, float)):
            raise ValueError("ticketQuantity must be a number")

        if isinstance(cancellation["originalAmount"], bool):
            raise ValueError("originalAmount must be a number")

        if not isinstance(cancellation["originalAmount"], (int, float)):
            raise ValueError("originalAmount must be a number")

        return True

    @staticmethod
    def validate(data):

        for field in BookingConfirmation.REQUIRED_FIELDS:

            if field not in data or data[field] is None:
                raise ValueError(f"{field} is required")

        booking_id = data["bookingId"]

        if isinstance(booking_id, str):

            if not ObjectId.is_valid(booking_id):
                raise ValueError("Invalid bookingId")

        elif not isinstance(booking_id, ObjectId):

            raise ValueError("bookingId must be an ObjectId")

        string_fields = [
            "bookingReference",
            "messageId",
            "recipientEmail",
            "customerName",
            "eventName",
            "eventDate",
            "eventTime",
            "venue",
            "paymentStatus"
        ]

        for field in string_fields:

            if not isinstance(data[field], str):
                raise ValueError(f"{field} must be a string")

        if not isinstance(data["seats"], list):
            raise ValueError("seats must be a list")

        if any(not isinstance(seat, str) for seat in data["seats"]):
            raise ValueError("Every seat must be a string")

        numeric_fields = [
            "ticketQuantity",
            "ticketPrice",
            "totalAmount"
        ]

        for field in numeric_fields:

            if isinstance(data[field], bool):
                raise ValueError(f"{field} must be a number")

            if not isinstance(data[field], (int, float)):
                raise ValueError(f"{field} must be a number")

        if not isinstance(data["confirmedAt"], datetime):
            raise ValueError("confirmedAt must be a datetime")

        status = data.get("status", "pending")

        if status not in BookingConfirmation.STATUSES:
            raise ValueError("Invalid confirmation status")

        for attempt in data.get("deliveryAttempts", []):

            BookingConfirmation.validate_delivery_attempt(attempt)

        for history in data.get("recoveryHistory", []):

            BookingConfirmation.validate_recovery_history(history)

        cancellation = data.get("cancellation")

        if cancellation is not None:

            BookingConfirmation.validate_cancellation(cancellation)

        return True

    @staticmethod
    def prepare_delivery_attempt(attempt):

        BookingConfirmation.validate_delivery_attempt(attempt)

        return {
            "attemptId": attempt["attemptId"],
            "claimedAt": attempt["claimedAt"],
            "sendStartedAt": attempt.get("sendStartedAt"),
            "smtpAcceptedAt": attempt.get("smtpAcceptedAt"),
            "completedAt": attempt.get("completedAt"),
            "outcome": attempt["outcome"],
            "errorCode": attempt.get("errorCode")
        }

    @staticmethod
    def prepare_recovery_history(history):

        BookingConfirmation.validate_recovery_history(history)

        return {
            "recoveredAt": history["recoveredAt"],
            "previousAttempts": history["previousAttempts"],
            "previousError": history["previousError"],
            "reason": history["reason"]
        }

    @staticmethod
    def prepare_cancellation(cancellation):

        BookingConfirmation.validate_cancellation(cancellation)

        return {
            "messageId": cancellation["messageId"],
            "recipientEmail": cancellation["recipientEmail"],
            "customerName": cancellation["customerName"],
            "eventName": cancellation["eventName"],
            "eventDate": cancellation["eventDate"],
            "eventTime": cancellation["eventTime"],
            "venue": cancellation["venue"],
            "posterUrl": cancellation.get("posterUrl", ""),
            "bookingReference": cancellation["bookingReference"],
            "seats": cancellation["seats"],
            "ticketQuantity": cancellation["ticketQuantity"],
            "originalAmount": cancellation["originalAmount"],
            "cancelledAt": cancellation["cancelledAt"],
            "cancellationStatus": cancellation["cancellationStatus"],
            "refundAmount": cancellation.get("refundAmount"),
            "refundStatus": cancellation.get("refundStatus", "not_applicable"),
            "status": cancellation.get("status", "pending"),
            "attempts": cancellation.get("attempts", 0),
            "deliveryAttempts": [
                BookingConfirmation.prepare_delivery_attempt(a)
                for a in cancellation.get("deliveryAttempts", [])
            ],
            "activeAttemptId": cancellation.get("activeAttemptId"),
            "recoveryHistory": [
                BookingConfirmation.prepare_recovery_history(h)
                for h in cancellation.get("recoveryHistory", [])
            ],
            "nextAttemptAt": cancellation.get("nextAttemptAt", datetime.now(timezone.utc)),
            "lockUntil": cancellation.get("lockUntil"),
            "sentAt": cancellation.get("sentAt"),
            "lastError": cancellation.get("lastError")
        }

    @staticmethod
    def prepare(data):

        BookingConfirmation.validate(data)

        now = datetime.now(timezone.utc)

        document = {
            "bookingId": (
                ObjectId(data["bookingId"])
                if isinstance(data["bookingId"], str)
                else data["bookingId"]
            ),
            "bookingReference": data["bookingReference"],
            "messageId": data["messageId"],
            "recipientEmail": data["recipientEmail"],
            "customerName": data["customerName"],
            "eventName": data["eventName"],
            "eventDate": data["eventDate"],
            "eventTime": data["eventTime"],
            "venue": data["venue"],
            "seats": data["seats"],
            "ticketQuantity": data["ticketQuantity"],
            "ticketPrice": data["ticketPrice"],
            "totalAmount": data["totalAmount"],
            "paymentStatus": data["paymentStatus"],
            "confirmedAt": data["confirmedAt"],
            "posterUrl": data.get("posterUrl", ""),
            "status": data.get("status", "pending"),
            "attempts": data.get("attempts", 0),
            "deliveryAttempts": [
                BookingConfirmation.prepare_delivery_attempt(a)
                for a in data.get("deliveryAttempts", [])
            ],
            "activeAttemptId": data.get("activeAttemptId"),
            "recoveryHistory": [
                BookingConfirmation.prepare_recovery_history(h)
                for h in data.get("recoveryHistory", [])
            ],
            "nextAttemptAt": data.get("nextAttemptAt", now),
            "lockUntil": data.get("lockUntil"),
            "sentAt": data.get("sentAt"),
            "lastError": data.get("lastError"),
            "createdAt": data.get("createdAt", now),
            "updatedAt": data.get("updatedAt", now)
        }

        if data.get("cancellation") is not None:

            document["cancellation"] = (
                BookingConfirmation.prepare_cancellation(
                    data["cancellation"]
                )
            )

        return document

    @staticmethod
    def collection(database):

        return database[BookingConfirmation.COLLECTION]

    @staticmethod
    def find_by_booking_id(database, booking_id):

        if isinstance(booking_id, str):
            booking_id = ObjectId(booking_id)

        return BookingConfirmation.collection(database).find_one({
            "bookingId": booking_id
        })

    @staticmethod
    def find_by_message_id(database, message_id):

        return BookingConfirmation.collection(database).find_one({
            "messageId": message_id
        })

    @staticmethod
    def create(database, data):

        document = BookingConfirmation.prepare(data)

        result = BookingConfirmation.collection(database).insert_one(
            document
        )

        return result.inserted_id