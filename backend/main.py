"""Canonical ASGI entry point for the FlashReserve REST API."""

from backend.api import app
from backend.config import settings


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=False,
    )