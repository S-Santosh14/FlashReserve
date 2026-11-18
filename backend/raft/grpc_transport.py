import json
import logging
import threading
import time

import grpc

from concurrent import futures

from backend.grpc.proto import raft_pb2
from backend.grpc.proto import raft_pb2_grpc
from backend.config import settings

logger = logging.getLogger(__name__)


class RaftPortBindError(RuntimeError):
    pass


class RaftGrpcServicer(raft_pb2_grpc.RaftServiceServicer):

    def __init__(self, node, transport):
        self.node = node
        self.transport = transport

    # ==========================================
    # REQUEST VOTE
    # ==========================================

    def RequestVote(self, request, context):

        response = self.node.request_vote(
            term=request.term,
            candidate_id=request.candidate_id,
            last_log_index=request.last_log_index,
            last_log_term=request.last_log_term
        )

        return raft_pb2.RequestVoteResponse(
            term=response["term"],
            vote_granted=response["vote_granted"],
            voter_id=self.node.node_id
        )

    # ==========================================
    # APPEND ENTRIES / HEARTBEAT
    # ==========================================

    def AppendEntries(self, request, context):

        entries = []
        for entry in request.entries:
            command_payload = entry.command_payload.decode("utf-8")
            try:
                payload = json.loads(command_payload)
            except json.JSONDecodeError:
                payload = None
            timestamp = (
                payload.get("_raftTimestamp")
                if isinstance(payload, dict)
                else None
            )
            entries.append({
                "index": entry.index,
                "term": entry.term,
                "timestamp": timestamp,
                "requestId": entry.command_id,
                "command": {
                    "type": entry.command_type,
                    "payload": command_payload
                }
            })

        response = self.node.append_entries(
            term=request.term,
            leader_id=request.leader_id,
            prev_log_index=request.prev_log_index,
            prev_log_term=request.prev_log_term,
            entries=entries,
            leader_commit=request.leader_commit
        )

        return raft_pb2.AppendEntriesResponse(
            term=response["term"],
            success=response["success"],
            follower_id=self.node.node_id,
            match_index=response.get("match_index", 0),
            conflict_index=response.get("conflict_index", 0),
            conflict_term=response.get("conflict_term", 0)
        )

    # ==========================================
    # INSTALL SNAPSHOT
    # ==========================================

    def InstallSnapshot(self, request, context):
        with self.node.lock:
            if (
                request.leader_id in self.node.members
                and request.term >= self.node.current_term
            ):
                if request.term > self.node.current_term:
                    self.node.current_term = request.term
                    self.node.voted_for = None
                    self.node.state = self.node.FOLLOWER
                    self.node.leader_id = None
                    self.node.last_quorum_at = None
                    self.node.last_quorum_acknowledgements = 0
                    self.node._persist()

                if self.node.leader_id in (None, request.leader_id):
                    self.node.state = self.node.FOLLOWER
                    self.node.leader_id = request.leader_id
                    self.node._reset_election_timer()
                    self.node.last_leader_contact = time.monotonic()

            current_term = self.node.current_term

        return raft_pb2.InstallSnapshotResponse(
            term=current_term,
            follower_id=self.node.node_id,
            success=False
        )

    # ==========================================
    # CLIENT COMMAND
    # ==========================================

    def SubmitCommand(self, request, context):

        # Reject requests unless this node is currently the leader.
        with self.node.lock:
            if self.node.state != self.node.LEADER:
                return raft_pb2.SubmitCommandResponse(
                    success=False,
                    committed=False,
                    leader_id=self.node.leader_id or "",
                    message="This node is not the leader",
                    command_id=request.command_id
                )

        if not request.command_id or not request.command_type:
            return raft_pb2.SubmitCommandResponse(
                success=False,
                committed=False,
                leader_id=self.node.node_id,
                message="command_id and command_type are required",
                command_id=request.command_id
            )

        # Decode and validate the JSON command payload.
        try:
            import json
            payload = json.loads(request.command_payload.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("Command payload must be a JSON object")
        except (ValueError, UnicodeDecodeError) as error:
            return raft_pb2.SubmitCommandResponse(
                success=False,
                committed=False,
                leader_id=self.node.node_id,
                message=f"Invalid command payload: {error}",
                command_id=request.command_id
            )

        # Append the command to the leader's durable Raft log.
        try:
            submission = self.node.submit_command(
                command_id=request.command_id,
                command_type=request.command_type,
                payload=payload
            )
        except Exception as error:
            return raft_pb2.SubmitCommandResponse(
                success=False,
                committed=False,
                leader_id=self.node.node_id,
                message=f"Command append failed: {error}",
                command_id=request.command_id
            )

        if not submission.get("success"):
            return raft_pb2.SubmitCommandResponse(
                success=False,
                committed=False,
                leader_id=submission.get("leader_id") or "",
                message=submission.get("message", "Command rejected"),
                command_id=request.command_id
            )

        index = submission["index"]

        # Wait for a majority of the cluster to replicate the entry.
        if not self.node.wait_for_commit(index=index, timeout=10):
            return raft_pb2.SubmitCommandResponse(
                success=False,
                committed=False,
                leader_id=self.node.leader_id or "",
                message="Majority commitment timed out or leadership was lost",
                command_id=request.command_id
            )

        # The runtime applies committed entries to the shared application DB.
        if not self.node.wait_for_application(index=index, timeout=20):
            return raft_pb2.SubmitCommandResponse(
                success=False,
                committed=True,
                leader_id=self.node.leader_id or self.node.node_id,
                message=(
                    "Command was committed by a majority, but state-machine "
                    "application did not finish before the timeout"
                ),
                command_id=request.command_id
            )

        # Return the persisted state-machine result for this request.
        with self.node.lock:
            applied = next(
                (
                    item for item in reversed(self.node.applied_results)
                    if item.get("requestId") == request.command_id
                ),
                None
            )

        if applied is None:
            return raft_pb2.SubmitCommandResponse(
                success=False,
                committed=True,
                leader_id=self.node.node_id,
                message="Command applied, but its result record was not found",
                command_id=request.command_id
            )

        result = applied.get("result")

        if isinstance(result, dict):
            business_success = result.get("success", True)
            if business_success:
                message = "Command committed and applied successfully"
            else:
                message = (
                    "Command committed and applied; business operation failed: "
                    + str(result.get("error") or result.get("message") or result)
                )
        else:
            business_success = True
            message = "Command committed and applied successfully"

        return raft_pb2.SubmitCommandResponse(
            success=business_success,
            committed=True,
            leader_id=self.node.node_id,
            message=message,
            command_id=request.command_id,
            result_payload=json.dumps(
                result,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode("utf-8"),
        )

    # ==========================================
    # CLUSTER STATUS
    # ==========================================

    def GetClusterStatus(self, request, context):
        status = self.node.get_status()
        database_connected = False
        database_name = ""
        database = getattr(
            getattr(self.node, "store", None),
            "database",
            None,
        )
        if database is not None:
            database_name = getattr(database, "name", "")
            try:
                database_connected = bool(
                    database.client.topology_description.has_writable_server()
                )
            except (AttributeError, RuntimeError):
                database_connected = False

        heartbeat_age_ms = 0
        last_heartbeat = getattr(self.node, "last_heartbeat", None)
        if last_heartbeat is not None:
            heartbeat_age_ms = max(
                0,
                int((time.monotonic() - last_heartbeat) * 1000),
            )

        local_status = raft_pb2.NodeStatus(
            node_id=self.node.node_id,
            state=status["state"],
            current_term=status["currentTerm"],
            commit_index=status["commitIndex"],
            last_applied=status["lastApplied"],
            last_log_index=status["lastLogIndex"],
            reachable=True,
            leader_id=status.get("leaderId") or "",
            running=status.get("running", False),
            database_connected=database_connected,
            heartbeat_age_ms=heartbeat_age_ms,
            last_successful_sync_at_ms=int(
                status.get("lastSuccessfulSyncAt") or 0
            ),
            last_quorum_at_ms=int(status.get("lastQuorumAt") or 0),
            last_quorum_acknowledgements=status.get(
                "lastQuorumAcknowledgements",
                0,
            ),
            cluster_id=status.get("clusterId") or "",
            cluster_config_version=status.get("clusterConfigVersion", 0),
            configured_members=status.get("configuredMembers", []),
            topology_id=status.get("topologyId") or "",
            configuration_json=json.dumps(
                status.get("configuration") or {},
                sort_keys=True,
                separators=(",", ":"),
            ),
            replication_progress_json=json.dumps(
                status.get("replicationProgress") or {},
                sort_keys=True,
                separators=(",", ":"),
            ),
            application_failure=status.get("applicationFailure") or "",
            database_name=database_name,
            votes_received=status.get("votesReceived", 0),
        )

        return raft_pb2.GetClusterStatusResponse(
            leader_id=status.get("leaderId") or "",
            current_term=status["currentTerm"],
            nodes=[local_status],
            has_leader=bool(status.get("leaderId")),
        )


class RaftGrpcTransport:

    def __init__(self, node, addresses):

        self.node = node
        self.addresses = addresses

        self.channels = {}
        self.stubs = {}
        self.channel_states = {}
        self.channel_states_lock = threading.Lock()

        self.server = None

        self._create_peer_connections()

    # ==========================================
    # PEER CONNECTIONS
    # ==========================================

    def _create_peer_connections(self):

        for peer_id, address in self.addresses.items():

            if peer_id == self.node.node_id:
                continue

            channel = grpc.insecure_channel(address)

            self.channels[peer_id] = channel
            with self.channel_states_lock:
                self.channel_states[peer_id] = "UNKNOWN"

            def on_connectivity(state, peer=peer_id):
                with self.channel_states_lock:
                    self.channel_states[peer] = state.name

            channel.subscribe(on_connectivity, try_to_connect=True)

            self.stubs[peer_id] = (
                raft_pb2_grpc.RaftServiceStub(channel)
            )

    def channel_state(self, peer_id):
        with self.channel_states_lock:
            return self.channel_states.get(peer_id, "UNKNOWN")

    def _call(self, peer_id, method, request, term=None):
        try:
            return getattr(self.stubs[peer_id], method)(
                request, timeout=settings.RAFT_RPC_TIMEOUT
            )
        except grpc.RpcError as error:
            def diagnostic(name):
                accessor = getattr(error, name, None)
                if not callable(accessor):
                    return "unavailable"
                try:
                    value = accessor()
                except (AttributeError, NotImplementedError):
                    return "unavailable"
                return value if value is not None else "unavailable"

            code = diagnostic("code")
            with self.node.lock:
                current_term = self.node.current_term
                role = self.node.state
            logger.warning(
                "grpc failure local=%s peer=%s address=%s method=%s "
                "status=%s details=%r debug=%r timeout_seconds=%s "
                "channel=%s request_term=%s current_term=%s role=%s",
                self.node.node_id, peer_id, self.addresses[peer_id], method,
                getattr(code, "name", code), diagnostic("details"),
                diagnostic("debug_error_string"), settings.RAFT_RPC_TIMEOUT,
                self.channel_state(peer_id), term, current_term, role,
            )
            raise

    # ==========================================
    # START SERVER
    # ==========================================

    def start_server(self, host="0.0.0.0", port=50051):

        self.server = grpc.server(
            futures.ThreadPoolExecutor(max_workers=20),
            options=(("grpc.so_reuseport", 0),),
        )

        raft_pb2_grpc.add_RaftServiceServicer_to_server(
            RaftGrpcServicer(self.node, self),
            self.server
        )

        try:
            bound_port = self.server.add_insecure_port(f"{host}:{port}")
        except RuntimeError as error:
            raise RaftPortBindError(
                f"Node {self.node.node_id} could not bind port {port}; "
                "it may already be occupied. Inspect the listener before stopping it."
            ) from error
        if not bound_port:
            raise RaftPortBindError(
                f"Node {self.node.node_id} could not bind port {port}; "
                "it may already be occupied. Inspect the listener before stopping it."
            )

        self.server.start()

        return self.server

    # ==========================================
    # REQUEST VOTE FROM PEER
    # ==========================================

    def request_vote(
        self,
        peer_id,
        term,
        candidate_id,
        last_log_index,
        last_log_term
    ):

        response = self._call(
            peer_id, "RequestVote",
            raft_pb2.RequestVoteRequest(
                term=term,
                candidate_id=candidate_id,
                last_log_index=last_log_index,
                last_log_term=last_log_term
            ),
            term=term,
        )
        if response.voter_id != peer_id:
            raise ValueError(f"Unexpected voter identity from {peer_id}")

        return {
            "term": response.term,
            "vote_granted": response.vote_granted
        }

    # ==========================================
    # APPEND ENTRIES TO PEER
    # ==========================================

    def append_entries(
        self,
        peer_id,
        term,
        leader_id,
        prev_log_index,
        prev_log_term,
        entries,
        leader_commit
    ):

        grpc_entries = []

        for entry in entries:

            command = entry["command"]

            grpc_entries.append(
                raft_pb2.LogEntry(
                    index=entry["index"],
                    term=entry["term"],
                    command_type=command.get("type", ""),
                    command_payload=command.get(
                        "payload", ""
                    ).encode("utf-8"),
                    command_id=entry["requestId"]
                )
            )

        response = self._call(
            peer_id, "AppendEntries",
            raft_pb2.AppendEntriesRequest(
                term=term,
                leader_id=leader_id,
                prev_log_index=prev_log_index,
                prev_log_term=prev_log_term,
                entries=grpc_entries,
                leader_commit=leader_commit
            ),
            term=term,
        )
        if response.follower_id != peer_id:
            raise ValueError(f"Unexpected follower identity from {peer_id}")

        return {
            "term": response.term,
            "success": response.success,
            "match_index": response.match_index,
            "conflict_index": response.conflict_index,
            "conflict_term": response.conflict_term
        }

    # ==========================================
    # PEER STATUS
    # ==========================================

    def get_peer_status(self, peer_id):

        response = self._call(
            peer_id, "GetClusterStatus",
            raft_pb2.GetClusterStatusRequest(
                requester_id=self.node.node_id
            ),
        )

        for node_status in response.nodes:

            if node_status.node_id == peer_id:
                return node_status

        raise RuntimeError(
            f"Node {peer_id} was not found in cluster status"
        )

    # ==========================================
    # CLOSE CONNECTIONS
    # ==========================================

    def close(self):

        if self.server:
            self.server.stop(grace=2)

        for channel in self.channels.values():
            channel.close()