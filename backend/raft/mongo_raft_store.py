import json

from pymongo import UpdateOne
from pymongo.write_concern import WriteConcern


class MongoRaftStore:

    def __init__(self, database):

        self.database = database

        self.states = database["raftstates"]
        self.logs = database["raftlogentries"]
        self.results = database["raftappliedresults"]
        self.logs.create_index(
            [("nodeId", 1), ("index", 1)],
            unique=True,
        )
        self.results.create_index(
            [("nodeId", 1), ("requestId", 1)],
            unique=True,
        )

        self.write_concern = WriteConcern(
            w="majority",
            j=True
        )

        self.states = self.states.with_options(
            write_concern=self.write_concern
        )

        self.logs = self.logs.with_options(
            write_concern=self.write_concern
        )

        self.results = self.results.with_options(
            write_concern=self.write_concern
        )

        self.persisted_logs = {}
        self.persisted_results = {}

    @staticmethod
    def _serialize(value):

        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str
        )

    # ------------------------------------------
    # LOAD PERSISTED STATE
    # ------------------------------------------

    def load(self, node_id):

        state = self.states.find_one({
            "_id": node_id
        })

        log_entries = list(
            self.logs.find({
                "nodeId": node_id
            }).sort("index", 1)
        )

        applied_results = list(
            self.results.find({
                "nodeId": node_id
            }).sort("index", 1)
        )

        self.persisted_logs = {
            entry["index"]: self._serialize({
                "nodeId": node_id,
                "index": entry["index"],
                "term": entry["term"],
                "timestamp": entry.get("timestamp"),
                "requestId": entry["requestId"],
                "command": entry["command"]
            })
            for entry in log_entries
        }

        durable_applied_index = (
            state.get("lastApplied", 0) if state else 0
        )

        durable_results = [
            item for item in applied_results
            if item["index"] <= durable_applied_index
        ]

        self.persisted_results = {
            item["requestId"]: self._serialize({
                "nodeId": node_id,
                "index": item["index"],
                "requestId": item["requestId"],
                "result": item.get("result")
            })
            for item in durable_results
        }

        if not state and not log_entries and not applied_results:
            return None

        configuration = (
            state.get("configuration") if state else None
        )

        result = {
            "clusterId": state.get("clusterId") if state else None,
            "clusterConfigVersion": (
                state.get("clusterConfigVersion", 1)
                if state else 1
            ),
            "currentTerm": state.get("currentTerm", 0) if state else 0,
            "votedFor": state.get("votedFor") if state else None,
            "log": [
                {
                    "index": entry["index"],
                    "term": entry["term"],
                    "timestamp": entry.get("timestamp"),
                    "requestId": entry["requestId"],
                    "command": entry["command"]
                }
                for entry in log_entries
            ],
            "commitIndex": (
                state.get("commitIndex", 0) if state else 0
            ),
            "lastApplied": (
                state.get("lastApplied", 0) if state else 0
            ),
            "appliedResults": [
                {
                    "index": item["index"],
                    "requestId": item["requestId"],
                    "result": item.get("result")
                }
                for item in durable_results
            ]
        }

        if configuration and configuration.get("oldMembers"):
            result["configuration"] = configuration

        return result

    # ------------------------------------------
    # SAVE PERSISTENT STATE
    # ------------------------------------------

    def save(self, node_id, state):

        log_operations = []

        for entry in state["log"]:

            document = {
                "nodeId": node_id,
                **entry
            }

            serialized = self._serialize(document)

            if self.persisted_logs.get(entry["index"]) == serialized:
                continue

            log_operations.append(
                UpdateOne(
                    {
                        "nodeId": node_id,
                        "index": entry["index"]
                    },
                    {
                        "$set": document
                    },
                    upsert=True
                )
            )

        if log_operations:

            self.logs.bulk_write(
                log_operations,
                ordered=True
            )

        # Remove entries that were overwritten by
        # a conflicting leader log.
        last_persisted_index = max(
            self.persisted_logs.keys(),
            default=0
        )

        if last_persisted_index > len(state["log"]):

            self.logs.delete_many({
                "nodeId": node_id,
                "index": {
                    "$gt": len(state["log"])
                }
            })

        # Persist applied command results.
        result_operations = []

        for item in state["appliedResults"]:

            document = {
                "nodeId": node_id,
                **item
            }

            serialized = self._serialize(document)

            if (
                self.persisted_results.get(item["requestId"])
                == serialized
            ):
                continue

            result_operations.append(
                UpdateOne(
                    {
                        "nodeId": node_id,
                        "requestId": item["requestId"]
                    },
                    {
                        "$set": document
                    },
                    upsert=True
                )
            )

        if result_operations:

            self.results.bulk_write(
                result_operations,
                ordered=True
            )

        # Persist Raft metadata.
        self.states.update_one(
            {
                "_id": node_id
            },
            {
                "$set": {
                    "clusterId": state["clusterId"],
                    "clusterConfigVersion": state[
                        "clusterConfigVersion"
                    ],
                    "configuration": state["configuration"],
                    "currentTerm": state["currentTerm"],
                    "votedFor": state["votedFor"],
                    "commitIndex": state["commitIndex"],
                    "lastApplied": state["lastApplied"]
                }
            },
            upsert=True
        )

        self.persisted_logs = {
            entry["index"]: self._serialize({
                "nodeId": node_id,
                **entry
            })
            for entry in state["log"]
        }

        self.persisted_results = {
            item["requestId"]: self._serialize({
                "nodeId": node_id,
                **item
            })
            for item in state["appliedResults"]
        }