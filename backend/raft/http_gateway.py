import json
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import grpc

from backend.config import settings
from backend.grpc.proto import raft_pb2, raft_pb2_grpc


class RaftGatewayError(Exception):
    def __init__(self, message, status_code=503, code="RAFT_UNAVAILABLE"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class RaftHttpGateway:
    def __init__(self, database_provider, addresses=None, rpc_timeout=None):
        configured_nodes = settings.raft_nodes()
        self.members = list(configured_nodes)
        self.addresses = addresses or {
            node_id: f"{config['host']}:{config['port']}"
            for node_id, config in configured_nodes.items()
        }
        self.database_provider = database_provider
        self.rpc_timeout = rpc_timeout or settings.RAFT_RPC_TIMEOUT
        self.channels = {
            node_id: grpc.insecure_channel(address)
            for node_id, address in self.addresses.items()
        }
        self.stubs = {
            node_id: raft_pb2_grpc.RaftServiceStub(channel)
            for node_id, channel in self.channels.items()
        }

    def close(self):
        for channel in self.channels.values():
            channel.close()

    def _read_node_status(self, node_id):
        response = self.stubs[node_id].GetClusterStatus(
            raft_pb2.GetClusterStatusRequest(requester_id="http-gateway"),
            timeout=self.rpc_timeout,
        )
        if len(response.nodes) != 1 or response.nodes[0].node_id != node_id:
            raise RaftGatewayError(
                f"{node_id} returned an invalid local status response.",
                502,
                "RAFT_INVALID_STATUS",
            )
        return response.nodes[0]

    @staticmethod
    def _attach_replication_acknowledgements(statuses, leaders):
        leader = leaders[0] if len(leaders) == 1 else None
        leader_progress = leader.get("replicationProgress", {}) if leader else {}
        for status in statuses:
            node_id = status["nodeId"]
            if leader is None:
                status["replicationAck"] = "PENDING"
                status["replicationAckDetails"] = {}
            elif node_id == leader["nodeId"]:
                status["replicationAck"] = "ACKNOWLEDGED"
                status["replicationAckDetails"] = {
                    "matchIndex": leader.get("lastLogIndex", 0),
                    "source": "local durable leader log",
                }
            else:
                progress = leader_progress.get(node_id, {})
                status["replicationAck"] = progress.get(
                    "ackStatus",
                    "PENDING",
                )
                status["replicationAckDetails"] = dict(progress)

    def get_cluster_status(self):
        def fetch(node_id):
            try:
                status = self._read_node_status(node_id)
            except grpc.RpcError:
                return {
                    "nodeId": node_id,
                    "available": False,
                    "rpcConnected": False,
                    "database": {
                        "connected": False,
                        "name": settings.raft_database_name(node_id),
                    },
                    "topologyMatches": False,
                    "observedAt": time.time() * 1000,
                }
            except RaftGatewayError:
                return {
                    "nodeId": node_id,
                    "available": False,
                    "rpcConnected": True,
                    "database": {
                        "connected": False,
                        "name": settings.raft_database_name(node_id),
                    },
                    "topologyMatches": False,
                    "observedAt": time.time() * 1000,
                }

            try:
                configuration = json.loads(status.configuration_json or "{}")
                replication_progress = json.loads(
                    status.replication_progress_json or "{}"
                )
            except json.JSONDecodeError:
                configuration = {}
                replication_progress = {}

            database_name = status.database_name
            database_connected = status.database_connected
            expected_members = set(self.members)
            expected_database = settings.raft_database_name(node_id)
            expected_topology = settings.raft_topology_id()
            topology_matches = (
                status.node_id == node_id
                and set(status.configured_members) == expected_members
                and database_name == expected_database
                and status.topology_id == expected_topology
                and bool(status.cluster_id)
                and status.cluster_config_version == 1
            )
            application_failure = status.application_failure or None
            application_status = (
                "failed"
                if application_failure
                else (
                    "catching_up"
                    if status.last_applied < status.commit_index
                    else "ready"
                )
            )
            return {
                "nodeId": node_id,
                "node_id": node_id,
                "role": status.state,
                "state": status.state,
                "leaderId": status.leader_id or None,
                "currentTerm": status.current_term,
                "lastLogIndex": status.last_log_index,
                "commitIndex": status.commit_index,
                "lastApplied": status.last_applied,
                "available": True,
                "reachable": status.reachable,
                "rpcConnected": True,
                "running": status.running,
                "healthy": status.running and database_connected and not application_failure,
                "database": {
                    "connected": database_connected,
                    "name": database_name,
                },
                "databaseStatus": "DATABASE_CONNECTED" if database_connected else "DATABASE_UNAVAILABLE",
                "rpcStatus": "RPC_CONNECTED",
                "raftStatus": "RAFT_ACTIVE" if status.running else "RAFT_STOPPED",
                "applicationStatus": application_status,
                "applicationFailure": application_failure,
                "logSynchronized": False,
                "stateMachineCaughtUp": status.last_applied >= status.commit_index,
                "heartbeatAgeMs": status.heartbeat_age_ms,
                "lastSuccessfulSyncAt": status.last_successful_sync_at_ms or None,
                "lastQuorumAt": status.last_quorum_at_ms or None,
                "lastQuorumAcknowledgements": status.last_quorum_acknowledgements,
                "lastQuorumAcknowledgementsByConfiguration": {
                    "oldMembers": status.last_quorum_acknowledgements,
                    "newMembers": 0,
                },
                "votesReceived": status.votes_received,
                "clusterId": status.cluster_id,
                "clusterConfigVersion": status.cluster_config_version,
                "configuredMembers": list(status.configured_members),
                "topologyId": status.topology_id,
                "configuration": configuration,
                "replicationProgress": replication_progress,
                "electionTimeoutMs": int(
                    settings.RAFT_ELECTION_TIMEOUT_MAX * 1000
                ),
                "topologyMatches": topology_matches,
                "observedAt": time.time() * 1000,
            }

        with ThreadPoolExecutor(max_workers=len(self.members)) as executor:
            statuses = list(executor.map(fetch, self.members))

        reachable = [status for status in statuses if status["available"]]
        leaders = [
            status for status in reachable
            if status["role"] == "leader"
            and status["leaderId"] == status["nodeId"]
        ]
        self._attach_replication_acknowledgements(statuses, leaders)
        if len(leaders) == 1:
            leader = leaders[0]
            for status in reachable:
                status["replicationLag"] = max(
                    0,
                    leader["commitIndex"] - status["lastLogIndex"],
                )
                status["logSynchronized"] = (
                    status["lastLogIndex"] >= leader["commitIndex"]
                    and status["commitIndex"] == leader["commitIndex"]
                    and status["lastApplied"] == leader["lastApplied"]
                )
                status["logStatus"] = (
                    "LOG_SYNCHRONIZED"
                    if status["logSynchronized"]
                    else "LOG_CATCHING_UP"
                )
                status["stateMachineStatus"] = (
                    "STATE_MACHINE_CAUGHT_UP"
                    if status["stateMachineCaughtUp"]
                    else "STATE_MACHINE_CATCHING_UP"
                )
        else:
            for status in statuses:
                status.setdefault("replicationLag", None)
                status.setdefault("logStatus", "LOG_STATUS_UNKNOWN")
                status.setdefault("stateMachineStatus", "STATE_STATUS_UNKNOWN")

        return {
            "enabled": True,
            "clusterSize": len(self.members),
            "majorityRequired": len(self.members) // 2 + 1,
            "nodes": statuses,
            "leader": leaders[0] if len(leaders) == 1 else None,
        }

    def get_leader(self, *, require_quorum=True):
        cluster = self.get_cluster_status()
        statuses = cluster["nodes"]
        reachable = [
            status for status in statuses
            if status["available"]
            and status["healthy"]
            and status["topologyMatches"]
        ]
        majority = cluster["majorityRequired"]
        if require_quorum and len(reachable) < majority:
            raise RaftGatewayError(
                f"Raft voting quorum unavailable ({len(reachable)}/{majority} healthy nodes).",
                503,
                "RAFT_NO_QUORUM",
            )

        highest_term = max(
            (status["currentTerm"] for status in reachable),
            default=-1,
        )
        leaders = [
            status for status in reachable
            if status["role"] == "leader"
            and status["currentTerm"] == highest_term
        ]
        if len(leaders) > 1:
            raise RaftGatewayError(
                "Conflicting Raft leaders were reported in the same term.",
                503,
                "RAFT_CONFLICTING_LEADERS",
            )
        if not leaders:
            raise RaftGatewayError(
                "No healthy Raft leader is currently available.",
                503,
                "RAFT_LEADER_UNAVAILABLE",
            )

        leader = leaders[0]
        freshness_ms = max(
            3000,
            2 * leader["electionTimeoutMs"],
        )
        last_quorum_at = leader.get("lastQuorumAt")
        if (
            not isinstance(last_quorum_at, (int, float))
            or time.time() * 1000 - last_quorum_at > freshness_ms
            or leader["lastQuorumAcknowledgements"] < majority
        ):
            raise RaftGatewayError(
                "The leader has not recently confirmed a voting majority.",
                503,
                "RAFT_NO_QUORUM",
            )
        return leader

    def submit_command(self, command_id, command_type, payload):
        leader = self.get_leader()
        try:
            response = self.stubs[leader["nodeId"]].SubmitCommand(
                raft_pb2.SubmitCommandRequest(
                    command_id=command_id,
                    command_type=command_type,
                    command_payload=json.dumps(
                        payload,
                        sort_keys=True,
                        separators=(",", ":"),
                        default=str,
                    ).encode("utf-8"),
                    client_id="flashreserve-http",
                ),
                timeout=max(
                    self.rpc_timeout,
                    settings.RAFT_RPC_TIMEOUT + 25,
                ),
            )
        except grpc.RpcError as error:
            raise RaftGatewayError(
                "The Raft leader could not complete the command. Retry with the same request ID.",
                504,
                "RAFT_COMMAND_OUTCOME_UNKNOWN",
            ) from error

        if not response.committed:
            code = (
                "RAFT_NOT_LEADER"
                if response.leader_id and response.leader_id != leader["nodeId"]
                else "RAFT_NO_QUORUM"
            )
            raise RaftGatewayError(
                response.message or "The Raft command was not committed.",
                503,
                code,
            )

        try:
            result = json.loads(response.result_payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise RaftGatewayError(
                "The committed Raft command returned an invalid result.",
                502,
                "RAFT_INVALID_RESULT",
            ) from error

        if not response.success:
            failure = result if isinstance(result, dict) else {}
            error_result = failure.get("result")
            if isinstance(error_result, dict):
                failure = error_result
            raise RaftGatewayError(
                str(failure.get("error") or response.message),
                int(failure.get("status_code", 409)),
                "RAFT_COMMAND_REJECTED",
            )
        return {
            "leaderId": leader["nodeId"],
            "term": leader["currentTerm"],
            "commandId": command_id,
            "result": result,
        }

    def read_database(self):
        database, _leader_id = self.read_database_with_leader()
        return database

    def read_database_with_leader(self):
        command_id = f"read-barrier:{uuid4()}"
        committed = self.submit_command(command_id, "READ_BARRIER", {})
        return (
            self.database_provider(committed["leaderId"]),
            committed["leaderId"],
        )
