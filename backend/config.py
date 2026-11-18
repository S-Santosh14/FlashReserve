import os
import hashlib
import json
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _integer(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except ValueError as error:
        raise ValueError(f"{name} must be an integer.") from error


def _integer_compat(primary_name, legacy_name, default):
    if os.getenv(primary_name) is not None:
        return _integer(primary_name, default)
    return _integer(legacy_name, default)


def _positive_float(name, default):
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError as error:
        raise ValueError(f"{name} must be a number.") from error
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero.")
    return value


class Settings:
    APP_NAME = os.getenv("APP_NAME", "FlashReserve")
    APP_ENV = os.getenv("APP_ENV", "development")
    APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT = _integer_compat("PORT", "APP_PORT", 5000)

    MONGODB_URI = (
        os.getenv("STANDALONE_MONGO_URI")
        or os.getenv("MONGODB_URI")
    )
    DATABASE_NAME = (
        os.getenv("STANDALONE_DB_NAME")
        or os.getenv("DATABASE_NAME", "flashreserve")
    )

    RAFT_NODE_ID = os.getenv("RAFT_NODE_ID", "node-1")
    RAFT_CLUSTER_SIZE = _integer(
        "RAFT_CLUSTER_SIZE",
        int(os.getenv("FLASHRESERVE_RAFT_CLUSTER_SIZE", "7")),
    )
    if RAFT_CLUSTER_SIZE < 3 or RAFT_CLUSTER_SIZE % 2 == 0:
        raise ValueError("RAFT_CLUSTER_SIZE must be an odd integer of at least 3.")

    RAFT_DATABASES = {
        f"node-{index}": os.getenv(
            f"RAFT_NODE_{index}_DATABASE_NAME",
            f"flashreserve_raft_node{index}",
        )
        for index in range(1, RAFT_CLUSTER_SIZE + 1)
    }

    JWT_SECRET = os.getenv("JWT_SECRET") or os.getenv("SECRET_KEY")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_MINUTES = _integer("JWT_EXPIRATION_MINUTES", 60)

    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = _integer("SMTP_PORT", 587)
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "FlashReserve")

    GRPC_HOST = os.getenv("GRPC_HOST", "127.0.0.1")
    GRPC_PORT = _integer("GRPC_PORT", 50051)
    LLM_GRPC_ADDRESS = os.getenv(
        "LLM_GRPC_ADDRESS",
        f"{os.getenv('LLM_GRPC_HOST', '127.0.0.1')}:"
        f"{_integer('LLM_GRPC_PORT', 50060)}",
    )

    RAFT_ELECTION_TIMEOUT_MIN = _positive_float(
        "RAFT_ELECTION_TIMEOUT_MIN",
        2.0,
    )
    RAFT_ELECTION_TIMEOUT_MAX = _positive_float(
        "RAFT_ELECTION_TIMEOUT_MAX",
        4.0,
    )
    RAFT_HEARTBEAT_INTERVAL = _positive_float(
        "RAFT_HEARTBEAT_INTERVAL",
        0.5,
    )
    RAFT_RPC_TIMEOUT = _positive_float("RAFT_RPC_TIMEOUT", 2.0)
    RAFT_MONGO_SERVER_SELECTION_TIMEOUT_MS = _integer(
        "RAFT_MONGO_SERVER_SELECTION_TIMEOUT_MS",
        max(100, int(min(1.0, RAFT_RPC_TIMEOUT / 2) * 1000)),
    )
    if (
        RAFT_MONGO_SERVER_SELECTION_TIMEOUT_MS <= 0
        or RAFT_MONGO_SERVER_SELECTION_TIMEOUT_MS
        >= RAFT_RPC_TIMEOUT * 1000
    ):
        raise ValueError(
            "RAFT_MONGO_SERVER_SELECTION_TIMEOUT_MS must be positive and "
            "shorter than RAFT_RPC_TIMEOUT."
        )
    RAFT_STATUS_INTERVAL = _positive_float("RAFT_STATUS_INTERVAL", 15.0)

    @classmethod
    def raft_nodes(cls):
        return {
            f"node-{index}": {
                "host": os.getenv(
                    f"RAFT_NODE_{index}_HOST",
                    "127.0.0.1",
                ),
                "port": _integer(
                    f"RAFT_NODE_{index}_PORT",
                    50050 + index,
                ),
            }
            for index in range(1, cls.RAFT_CLUSTER_SIZE + 1)
        }

    @classmethod
    def raft_mongo_uri(cls, node_id):
        try:
            node_number = int(node_id.rsplit("-", 1)[1])
        except (AttributeError, IndexError, ValueError) as error:
            raise ValueError(f"Invalid Raft node ID: {node_id}") from error

        if node_id != f"node-{node_number}" or not 1 <= node_number <= cls.RAFT_CLUSTER_SIZE:
            raise ValueError(f"Invalid Raft node ID: {node_id}")

        uri = os.getenv(f"RAFT_NODE_{node_number}_MONGO_URI")
        if not uri:
            raise ValueError(
                f"RAFT_NODE_{node_number}_MONGO_URI is required to start {node_id}; "
                "Raft nodes never fall back to the standalone MongoDB URI."
            )
        return uri

    @classmethod
    def raft_database_name(cls, node_id):
        try:
            return cls.RAFT_DATABASES[node_id]
        except KeyError as error:
            raise ValueError(f"Invalid Raft node ID: {node_id}") from error

    @classmethod
    def raft_topology_id(cls):
        topology = {
            "members": cls.raft_nodes(),
            "databases": cls.RAFT_DATABASES,
        }
        serialized = json.dumps(
            topology,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def validate_raft_timing(cls):
        if cls.RAFT_ELECTION_TIMEOUT_MIN >= cls.RAFT_ELECTION_TIMEOUT_MAX:
            raise ValueError(
                "RAFT_ELECTION_TIMEOUT_MIN must be less than "
                "RAFT_ELECTION_TIMEOUT_MAX."
            )
        if cls.RAFT_HEARTBEAT_INTERVAL >= cls.RAFT_ELECTION_TIMEOUT_MIN:
            raise ValueError(
                "RAFT_HEARTBEAT_INTERVAL must be less than "
                "RAFT_ELECTION_TIMEOUT_MIN."
            )


settings = Settings()
