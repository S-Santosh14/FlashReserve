from datetime import datetime, timezone

from bson import ObjectId


class Seat:

    COLLECTION = "seats"

    CATEGORIES = [
        "Silver",
        "Gold",
        "Platinum",
        "VIP"
    ]

    STATUSES = [
        "available",
        "reserved",
        "booked"
    ]

    @staticmethod
    def validate(data):

        # Required fields
        if not data.get("eventId"):
            raise ValueError("eventId is required")

        if not data.get("seatNumber"):
            raise ValueError("seatNumber is required")

        # ObjectId validation
        for field in ["eventId", "reservedBy", "bookingId"]:

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

        # Seat number
        if not isinstance(data["seatNumber"], str):
            raise ValueError(
                "seatNumber must be a string"
            )

        if not data["seatNumber"].strip():
            raise ValueError(
                "seatNumber cannot be empty"
            )

        # Category
        category = data.get("category")

        if category is not None:

            if category not in Seat.CATEGORIES:
                raise ValueError(
                    "Invalid seat category"
                )

        # Status
        status = data.get("status", "available")

        if status not in Seat.STATUSES:
            raise ValueError(
                "Invalid seat status"
            )

        return True

    @staticmethod
    def prepare(data):

        Seat.validate(data)

        now = datetime.now(timezone.utc)

        def convert_object_id(value):

            if isinstance(value, str):
                return ObjectId(value)

            return value

        return {

            "eventId": convert_object_id(
                data["eventId"]
            ),

            "seatNumber": data["seatNumber"].strip(),

            "category": data.get("category"),

            "status": data.get(
                "status",
                "available"
            ),

            "reservedBy": convert_object_id(
                data.get("reservedBy")
            ),

            "reservedAt": data.get("reservedAt"),

            "reservationId": data.get(
                "reservationId"
            ),

            "lockExpiresAt": data.get(
                "lockExpiresAt"
            ),

            "bookingId": convert_object_id(
                data.get("bookingId")
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

        return database[Seat.COLLECTION]

    @staticmethod
    def find_by_id(database, seat_id):

        if isinstance(seat_id, str):
            seat_id = ObjectId(seat_id)

        return Seat.collection(database).find_one({
            "_id": seat_id
        })

    @staticmethod
    def find_by_event(database, event_id):

        if isinstance(event_id, str):
            event_id = ObjectId(event_id)

        return list(
            Seat.collection(database).find({
                "eventId": event_id
            })
        )

    @staticmethod
    def find_available(database, event_id):

        if isinstance(event_id, str):
            event_id = ObjectId(event_id)

        return list(
            Seat.collection(database).find({
                "eventId": event_id,
                "status": "available"
            })
        )

    @staticmethod
    def create(database, data):

        document = Seat.prepare(data)

        result = Seat.collection(database).insert_one(
            document
        )

        return result.inserted_id

    @staticmethod
    def update(database, seat_id, data):

        if isinstance(seat_id, str):
            seat_id = ObjectId(seat_id)

        Seat.validate(data)

        document = Seat.prepare(data)

        document.pop("createdAt", None)

        document["updatedAt"] = datetime.now(
            timezone.utc
        )

        return Seat.collection(database).update_one(
            {"_id": seat_id},
            {"$set": document}
        )