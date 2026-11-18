from backend.database.raft_database import get_raft_database


class RaftAppliedResult:

    COLLECTION = "raftappliedresults"

    @staticmethod
    def collection(node_id):
        return get_raft_database(node_id)[
            RaftAppliedResult.COLLECTION
        ]

    @staticmethod
    def validate(data):
        required_fields = [
            "nodeId",
            "index",
            "requestId",
        ]

        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValueError(f"{field} is required")

        if not isinstance(data["nodeId"], str) or not data["nodeId"].strip():
            raise ValueError("nodeId must be a non-empty string")

        if isinstance(data["index"], bool) or not isinstance(data["index"], (int, float)):
            raise ValueError("index must be a number")

        if not isinstance(data["requestId"], str) or not data["requestId"].strip():
            raise ValueError("requestId must be a non-empty string")

        return {
            "nodeId": data["nodeId"].strip(),
            "index": data["index"],
            "requestId": data["requestId"].strip(),
            "result": data.get("result"),
        }

    @staticmethod
    def create(node_id, data):
        document = RaftAppliedResult.validate(data)

        RaftAppliedResult.collection(node_id).insert_one(document)

        return document

    @staticmethod
    def find_by_request_id(node_id, request_id):
        return RaftAppliedResult.collection(node_id).find_one({
            "nodeId": node_id,
            "requestId": request_id,
        })

    @staticmethod
    def find_by_index(node_id, index):
        return RaftAppliedResult.collection(node_id).find_one({
            "nodeId": node_id,
            "index": index,
        })

    @staticmethod
    def update_result(node_id, request_id, result):
        return RaftAppliedResult.collection(node_id).update_one(
            {
                "nodeId": node_id,
                "requestId": request_id,
            },
            {
                "$set": {
                    "result": result,
                }
            },
        )