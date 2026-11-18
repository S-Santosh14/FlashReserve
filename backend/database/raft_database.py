import logging
import threading

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from backend.config import settings
from backend.database.mongodb import initialize_application_indexes


class RaftDatabaseManager:

    def __init__(self):
        self.clients = {}
        self.lock = threading.Lock()

    def get_database(self, node_id):
        uri = settings.raft_mongo_uri(node_id)
        database_name = settings.raft_database_name(node_id)

        with self.lock:
            client = self.clients.get(node_id)
            if client is None:
                client = MongoClient(
                    uri,
                    serverSelectionTimeoutMS=(
                        settings.RAFT_MONGO_SERVER_SELECTION_TIMEOUT_MS
                    ),
                    appname=f"FlashReserve-Raft-{node_id}",
                )
                try:
                    client.admin.command("ping")
                    database = client.get_database(database_name)
                    initialize_application_indexes(database)
                except PyMongoError:
                    client.close()
                    raise
                self.clients[node_id] = client

        return self.clients[node_id].get_database(database_name)

    def close(self):
        with self.lock:
            clients = tuple(self.clients.values())
            self.clients.clear()
        for client in clients:
            client.close()


raft_database_manager = RaftDatabaseManager()
logger = logging.getLogger(__name__)


def get_raft_database(node_id):
    try:
        return raft_database_manager.get_database(node_id)
    except PyMongoError:
        logger.error(
            "Unable to connect Raft node %s to its configured MongoDB.",
            node_id,
        )
        raise


def close_raft_connections():
    raft_database_manager.close()