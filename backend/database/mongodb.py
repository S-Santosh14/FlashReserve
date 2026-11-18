import logging

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from backend.config import settings


logger = logging.getLogger(__name__)


def initialize_application_indexes(database):
    database["users"].create_index("email", unique=True)
    database["seats"].create_index(
        [("eventId", 1), ("seatNumber", 1)],
        unique=True,
    )
    database["bookings"].create_index(
        [("userId", 1), ("reservationId", 1)],
        unique=True,
        partialFilterExpression={"reservationId": {"$type": "string"}},
    )
    database["payments"].create_index(
        "idempotencyKey",
        unique=True,
        partialFilterExpression={"idempotencyKey": {"$type": "string"}},
    )
    database["refunds"].create_index(
        "idempotencyKey",
        unique=True,
    )
    database["refunds"].create_index(
        "bookingId",
        unique=True,
    )


class MongoDB:

    def __init__(self):
        self.client = None
        self.database = None

    def connect(self):
        if not settings.MONGODB_URI:
            raise ValueError(
                "STANDALONE_MONGO_URI or MONGODB_URI is missing from .env."
            )

        try:
            client = MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5000,
                appname="FlashReserve-Python"
            )

            client.admin.command("ping")
            database = client.get_database(
                settings.DATABASE_NAME
            )
            initialize_application_indexes(database)
        except PyMongoError as error:
            logger.error(
                "Standalone MongoDB connection or index setup failed (%s).",
                type(error).__name__,
            )
            if "client" in locals():
                client.close()
            raise

        self.client = client
        self.database = database
        logger.info("Connected to standalone MongoDB database %s.", settings.DATABASE_NAME)
        return database

    def get_database(self):
        if self.database is None:
            raise RuntimeError(
                "MongoDB is not connected."
            )
        return self.database

    def close(self):
        if self.client:
            self.client.close()
            self.client = None
            self.database = None
            logger.info("Standalone MongoDB connection closed.")


mongodb = MongoDB()


def get_database():
    return mongodb.get_database()