from datetime import datetime, timezone

from bson import ObjectId


class Booking:

    COLLECTION = "bookings"

    STATUSES = [
        "pending",
        "confirmed",
        "cancelled",
        "failed",
        "expired"
    ]

    @staticmethod
    def validate(data):

        # Required fields
        required_fields = [
            "userId",
            "eventId",
            "seats",
            "totalAmount",
            "bookingReference"
        ]

        for field in required_fields:

            if field not in data or data[field] is None:
                raise ValueError(f"{field} is required")

        # Validate ObjectIds
        object_id_fields = [
            "userId",
            "eventId",
            "paymentId",
            "refundId"
        ]

        for field in object_id_fields:

            value = data.get(field)

            if value is not None:

                if isinstance(value, str):

                    if not ObjectId.is_valid(value):
                        raise ValueError(
                            f"Invalid {field}"
                        )

                elif not isinstance(value, ObjectId):

                    raise ValueError(
                        f"{field} must be an ObjectId"
                    )

        # Validate seats
        if not isinstance(data["seats"], list):
            raise ValueError("seats must be a list")

        for seat_id in data["seats"]:

            if isinstance(seat_id, str):

                if not ObjectId.is_valid(seat_id):
                    raise ValueError("Invalid seat ObjectId")

            elif not isinstance(seat_id, ObjectId):

                raise ValueError(
                    "Every seat must contain an ObjectId"
                )

        # Validate total amount
        amount = data["totalAmount"]

        if isinstance(amount, bool) or not isinstance(
            amount, (int, float)
        ):
            raise ValueError(
                "totalAmount must be a number"
            )

        if amount < 0:
            raise ValueError(
                "totalAmount cannot be negative"
            )

        # Validate booking reference
        if not isinstance(data["bookingReference"], str):
            raise ValueError(
                "bookingReference must be a string"
            )

        if not data["bookingReference"].strip():
            raise ValueError(
                "bookingReference cannot be empty"
            )

        # Validate reservation ID
        reservation_id = data.get("reservationId")

        if reservation_id is not None:

            if not isinstance(reservation_id, str):
                raise ValueError(
                    "reservationId must be a string or null"
                )

        # Validate status
        status = data.get("status", "pending")

        if status not in Booking.STATUSES:
            raise ValueError(
                "Invalid booking status"
            )

        return True

    @staticmethod
    def prepare(data):

        Booking.validate(data)

        now = datetime.now(timezone.utc)

        def convert_object_id(value):

            if isinstance(value, str):
                return ObjectId(value)

            return value

        return {

            "userId": convert_object_id(
                data["userId"]
            ),

            "eventId": convert_object_id(
                data["eventId"]
            ),

            "seats": [
                convert_object_id(seat_id)
                for seat_id in data["seats"]
            ],

            "totalAmount": data["totalAmount"],

            "reservationId": data.get(
                "reservationId"
            ),

            "bookingReference": (
                data["bookingReference"].strip()
            ),

            "paymentId": convert_object_id(
                data.get("paymentId")
            ),

            "refundId": convert_object_id(
                data.get("refundId")
            ),

            "expiresAt": data.get("expiresAt"),

            "cleanupCompletedAt": data.get(
                "cleanupCompletedAt"
            ),

            "status": data.get(
                "status",
                "pending"
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

        return database[Booking.COLLECTION]

    @staticmethod
    def find_by_id(database, booking_id):

        if isinstance(booking_id, str):

            booking_id = ObjectId(booking_id)

        return Booking.collection(database).find_one({
            "_id": booking_id
        })

    @staticmethod
    def find_by_reference(database, reference):

        return Booking.collection(database).find_one({
            "bookingReference": reference
        })

    @staticmethod
    def find_by_user(database, user_id):

        if isinstance(user_id, str):

            user_id = ObjectId(user_id)

        return list(
            Booking.collection(database).find({
                "userId": user_id
            })
        )

    @staticmethod
    def find_by_event(database, event_id):

        if isinstance(event_id, str):

            event_id = ObjectId(event_id)

        return list(
            Booking.collection(database).find({
                "eventId": event_id
            })
        )

    @staticmethod
    def create(database, data):

        document = Booking.prepare(data)

        result = Booking.collection(database).insert_one(
            document
        )

        return result.inserted_id

    @staticmethod
    def update_status(database, booking_id, status):

        if status not in Booking.STATUSES:

            raise ValueError("Invalid booking status")

        if isinstance(booking_id, str):

            booking_id = ObjectId(booking_id)

        return Booking.collection(database).update_one(

            {"_id": booking_id},

            {
                "$set": {
                    "status": status,
                    "updatedAt": datetime.now(timezone.utc)
                }
            }
        )