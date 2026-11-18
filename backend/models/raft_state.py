from datetime import datetime, timezone

from backend.database.raft_database import get_raft_database


class RaftState:

    COLLECTION = "raftstates"

    @staticmethod
    def collection(node_id):
        db = get_raft_database(node_id)
        return db[RaftState.COLLECTION]

    @staticmethod
    def prepare(data):
        return {
            "_id": data["_id"],
            "clusterId": data.get("clusterId"),
            "clusterConfigVersion": data.get(
                "clusterConfigVersion", 1
            ),
            "configuration": data.get("configuration"),
            "currentTerm": data.get("currentTerm", 0),
            "votedFor": data.get("votedFor"),
            "commitIndex": data.get("commitIndex", 0),
            "lastApplied": data.get("lastApplied", 0),
        }

    @staticmethod
    def find(node_id, state_id):
        return RaftState.collection(node_id).find_one(
            {"_id": state_id}
        )

    @staticmethod
    def create(node_id, data):
        state = RaftState.prepare(data)

        RaftState.collection(node_id).insert_one(state)

        return state

    @staticmethod
    def update(node_id, state_id, updates):
        allowed_fields = {
            "clusterId",
            "clusterConfigVersion",
            "configuration",
            "currentTerm",
            "votedFor",
            "commitIndex",
            "lastApplied",
        }

        invalid_fields = set(updates) - allowed_fields

        if invalid_fields:
            raise ValueError(
                f"Invalid RaftState fields: {invalid_fields}"
            )

        return RaftState.collection(node_id).update_one(
            {"_id": state_id},
            {"$set": updates},
        )