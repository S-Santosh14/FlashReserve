import re

import bcrypt

from pymongo.errors import DuplicateKeyError

from backend.models.user import User
from backend.utils.jwt_handler import create_access_token


class AuthError(Exception):

    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code

        super().__init__(message)


class AuthService:

    def __init__(self, database):
        self.database = database

    @staticmethod
    def public_user(user):

        return {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "createdAt": user.get("createdAt"),
        }

    @staticmethod
    def validate_email(email):

        pattern = r"^\S+@\S+\.\S+$"

        return bool(re.match(pattern, email))

    @staticmethod
    def hash_password(password):

        salt = bcrypt.gensalt(rounds=12)

        hashed = bcrypt.hashpw(
            password.encode("utf-8"),
            salt
        )

        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password, hashed_password):

        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )

    def register(self, data):

        name = data.get("name")
        email = data.get("email")
        password = data.get("password")

        missing = [
            field
            for field, value in {
                "name": name,
                "email": email,
                "password": password,
            }.items()
            if not value
        ]

        if missing:
            raise AuthError(
                f"Missing required fields: {', '.join(missing)}",
                400
            )

        if not isinstance(name, str):
            raise AuthError("Name must be a string", 400)

        if not isinstance(email, str):
            raise AuthError("Email must be a string", 400)

        if not isinstance(password, str):
            raise AuthError("Password must be a string", 400)

        name = name.strip()
        email = email.strip().lower()

        if not name:
            raise AuthError("Name cannot be empty", 400)

        if not self.validate_email(email) or len(password) < 8:
            raise AuthError(
                "Provide a valid email and a password of at least 8 characters",
                400
            )

        existing_user = User.find_by_email(
            self.database,
            email
        )

        if existing_user:
            raise AuthError(
                "Email is already registered",
                409
            )

        user_data = {
            "name": name,
            "email": email,
            "password": self.hash_password(password),

            # Public registration cannot assign admin privileges.
            "role": "customer",
        }

        try:

            user_id = User.create(
                self.database,
                user_data
            )

        except DuplicateKeyError:

            raise AuthError(
                "Email is already registered",
                409
            )

        user = User.find_by_id(
            self.database,
            user_id
        )

        if not user:
            raise RuntimeError(
                "User registration succeeded but user could not be retrieved"
            )

        token = create_access_token(user)

        return {
            "success": True,
            "data": {
                "user": self.public_user(user),
                "token": token,
            }
        }

    def login(self, data):

        email = data.get("email")
        password = data.get("password")

        missing = [
            field
            for field, value in {
                "email": email,
                "password": password,
            }.items()
            if not value
        ]

        if missing:
            raise AuthError(
                f"Missing required fields: {', '.join(missing)}",
                400
            )

        if not isinstance(email, str) or not isinstance(password, str):
            raise AuthError(
                "Invalid email or password",
                401
            )

        email = email.strip().lower()

        user = User.find_by_email(
            self.database,
            email
        )

        if not user or not self.verify_password(
            password,
            user["password"]
        ):

            raise AuthError(
                "Invalid email or password",
                401
            )

        token = create_access_token(user)

        return {
            "success": True,
            "data": {
                "user": self.public_user(user),
                "token": token,
            }
        }