from datetime import datetime, timezone

from bson import ObjectId


class Event:

    COLLECTION = "events"

    STATUSES = ["active", "archived"]

    @staticmethod
    def validate(data):

        required_fields = [
            "title",
            "category",
            "venue",
            "date",
            "time",
            "description",
            "totalSeats",
            "price"
        ]

        for field in required_fields:

            if field not in data or data[field] is None:
                raise ValueError(f"{field} is required")

        string_fields = [
            "title",
            "category",
            "venue",
            "time",
            "description"
        ]

        for field in string_fields:

            if not isinstance(data[field], str):
                raise ValueError(
                    f"{field} must be a string"
                )

            if not data[field].strip():
                raise ValueError(
                    f"{field} cannot be empty"
                )

        if not isinstance(data["date"], datetime):
            raise ValueError("date must be a datetime")

        if isinstance(data["totalSeats"], bool) or not isinstance(
            data["totalSeats"], (int, float)
        ):
            raise ValueError("totalSeats must be a number")

        if data["totalSeats"] < 0:
            raise ValueError(
                "totalSeats cannot be negative"
            )

        if isinstance(data["price"], bool) or not isinstance(
            data["price"], (int, float)
        ):
            raise ValueError("price must be a number")

        if data["price"] < 0:
            raise ValueError(
                "price cannot be negative"
            )

        seats_per_row = data.get("seatsPerRow", 10)

        if isinstance(seats_per_row, bool) or not isinstance(
            seats_per_row, (int, float)
        ):
            raise ValueError(
                "seatsPerRow must be a number"
            )

        if seats_per_row < 1:
            raise ValueError(
                "seatsPerRow must be at least 1"
            )

        status = data.get("status", "active")

        if status not in Event.STATUSES:
            raise ValueError("Invalid event status")

        poster_url = data.get("posterUrl", "")

        if not isinstance(poster_url, str):
            raise ValueError(
                "posterUrl must be a string"
            )

        return True

    @staticmethod
    def prepare(data):

        Event.validate(data)

        now = datetime.now(timezone.utc)

        return {
            "title": data["title"].strip(),

            "category": data["category"].strip(),

            "venue": data["venue"].strip(),

            "date": data["date"],

            "time": data["time"].strip(),

            "description": data["description"].strip(),

            "totalSeats": data["totalSeats"],

            "seatsPerRow": data.get("seatsPerRow", 10),

            "price": data["price"],

            "status": data.get("status", "active"),

            "posterUrl": data.get("posterUrl", ""),

            "createdAt": now,

            "updatedAt": now
        }

    @staticmethod
    def collection(database):

        return database[Event.COLLECTION]

    @staticmethod
    def find_by_id(database, event_id):

        if isinstance(event_id, str):
            event_id = ObjectId(event_id)

        return Event.collection(database).find_one({
            "_id": event_id
        })

    @staticmethod
    def find_all(database):

        return list(
            Event.collection(database).find()
        )

    @staticmethod
    def find_active(database):

        return list(
            Event.collection(database).find({
                "status": "active"
            })
        )

    @staticmethod
    def create(database, data):

        document = Event.prepare(data)

        result = Event.collection(database).insert_one(
            document
        )

        return result.inserted_id

    @staticmethod
    def update(database, event_id, data):

        if isinstance(event_id, str):
            event_id = ObjectId(event_id)

        Event.validate(data)

        updated_data = {
            key: value
            for key, value in Event.prepare(data).items()
            if key not in ["createdAt"]
        }

        updated_data["updatedAt"] = datetime.now(
            timezone.utc
        )

        return Event.collection(database).update_one(
            {"_id": event_id},
            {"$set": updated_data}
        )

    @staticmethod
    def delete(database, event_id):

        if isinstance(event_id, str):
            event_id = ObjectId(event_id)

        return Event.collection(database).delete_one({
            "_id": event_id
        })