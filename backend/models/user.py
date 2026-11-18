from datetime import datetime, timezone

from bson import ObjectId


class User:

    COLLECTION = "users"

    ROLES = ["customer", "admin"]

    @staticmethod
    def validate(data):

        required_fields = [
            "name",
            "email",
            "password"
        ]

        for field in required_fields:

            if not data.get(field):
                raise ValueError(
                    f"{field} is required"
                )

        if not isinstance(data["name"], str):
            raise ValueError("Name must be a string")

        if not isinstance(data["email"], str):
            raise ValueError("Email must be a string")

        if not isinstance(data["password"], str):
            raise ValueError("Password must be a string")

        role = data.get("role", "customer")

        if role not in User.ROLES:
            raise ValueError("Invalid user role")

        return True

    @staticmethod
    def prepare(data):

        User.validate(data)

        now = datetime.now(timezone.utc)

        return {
            "name": data["name"].strip(),

            "email": data["email"].strip().lower(),

            "password": data["password"],

            "role": data.get("role", "customer"),

            "createdAt": now,

            "updatedAt": now
        }

    @staticmethod
    def collection(database):

        return database[User.COLLECTION]

    @staticmethod
    def find_by_email(database, email):

        return User.collection(database).find_one({
            "email": email.strip().lower()
        })

    @staticmethod
    def find_by_id(database, user_id):

        if isinstance(user_id, str):
            user_id = ObjectId(user_id)

        return User.collection(database).find_one({
            "_id": user_id
        })

    @staticmethod
    def create(database, data):

        document = User.prepare(data)

        result = User.collection(database).insert_one(
            document
        )

        return result.inserted_id