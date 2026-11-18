from datetime import datetime, timezone

from pymongo.errors import DuplicateKeyError

from backend.database.raft_database import get_raft_database


class RaftLogEntry:

    COLLECTION = "raftlogentries"

    @staticmethod
    def collection(node_id):
        return get_raft_database(node_id)[RaftLogEntry.COLLECTION]

    @staticmethod
    def validate(data):
        required_fields = [
            "nodeId",
            "index",
            "term",
            "requestId",
            "command",
        ]

        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValueError(f"{field} is required")

        if not isinstance(data["nodeId"], str) or not data["nodeId"].strip():
            raise ValueError("nodeId must be a non-empty string")

        if not isinstance(data["index"], int) or data["index"] < 0:
            raise ValueError("index must be a non-negative integer")

        if not isinstance(data["term"], int) or data["term"] < 0:
            raise ValueError("term must be a non-negative integer")

        if not isinstance(data["requestId"], str) or not data["requestId"].strip():
            raise ValueError("requestId must be a non-empty string")

        return {
            "nodeId": data["nodeId"].strip(),
            "index": data["index"],
            "term": data["term"],
            "requestId": data["requestId"].strip(),
            "command": data["command"],
        }

    @staticmethod
    def create(node_id, data):
        entry = RaftLogEntry.validate(data)

        try:
            RaftLogEntry.collection(node_id).insert_one(entry)
            return entry
        except DuplicateKeyError:
            raise ValueError(
                "A Raft log entry already exists for this node and index"
            )

    @staticmethod
    def find_by_index(node_id, index):
        return RaftLogEntry.collection(node_id).find_one(
            {"nodeId": node_id, "index": index}
        )

    @staticmethod
    def find_from_index(node_id, start_index):
        return list(
            RaftLogEntry.collection(node_id)
            .find({
                "nodeId": node_id,
                "index": {"$gte": start_index},
            })
            .sort("index", 1)
        )

    @staticmethod
    def get_last_entry(node_id):
        return RaftLogEntry.collection(node_id).find_one(
            {"nodeId": node_id},
            sort=[("index", -1)],
        )

    @staticmethod
    def delete_from_index(node_id, start_index):
        return RaftLogEntry.collection(node_id).delete_many({
            "nodeId": node_id,
            "index": {"$gte": start_index},
        })