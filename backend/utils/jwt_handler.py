from datetime import datetime, timedelta, timezone

import jwt

from backend.config import settings


def create_access_token(user):
    if not settings.JWT_SECRET:
        raise RuntimeError(
            "JWT configuration is unavailable"
        )

    now = datetime.now(timezone.utc)

    expiration = now + timedelta(
        minutes=settings.JWT_EXPIRATION_MINUTES
    )

    payload = {
        "id": str(user["_id"]),
        "role": user["role"],
        "email": user["email"],
        "iat": now,
        "exp": expiration,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token):
    if not settings.JWT_SECRET:
        raise RuntimeError(
            "JWT configuration is unavailable"
        )

    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )

    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")

    except jwt.InvalidTokenError:
        raise ValueError("Invalid authentication token")