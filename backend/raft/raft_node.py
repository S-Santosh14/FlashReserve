import hashlib
import json
import logging
import random
import threading
import time

import grpc

from concurrent.futures import CancelledError
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

logger = logging.getLogger(__name__)


class RaftNode:

    FOLLOWER = "follower"
    CANDIDATE = "candidate"
    LEADER = "leader"

    HEARTBEAT_INTERVAL = 0.5

    ELECTION_TIMEOUT_MIN = 2.0
    ELECTION_TIMEOUT_MAX = 4.0

    def __init__(
        self,
        node_id,
        members,
        store,
        cluster_id="d864d183-36cd-4b41-80a0-8b68afc74105",
        topology_id=None,
        election_timeout_min=None,
        election_timeout_max=None,
    ):

        if node_id not in members:
            raise ValueError("Node must belong to the cluster")

        if len(members) < 3 or len(members) % 2 == 0:
            raise ValueError(
                "Raft cluster should have an odd number of nodes"
            )

        self.node_id = node_id
        self.members = list(members)
        self.cluster_id = cluster_id
        self.topology_id = topology_id or ""
        self.store = store
        self._random = random.SystemRandom()
        self.election_timeout_min = (
            self.ELECTION_TIMEOUT_MIN
            if election_timeout_min is None
            else election_timeout_min
        )
        self.election_timeout_max = (
            self.ELECTION_TIMEOUT_MAX
            if election_timeout_max is None
            else election_timeout_max
        )
        if (
            self.election_timeout_min <= 0
            or self.election_timeout_min >= self.election_timeout_max
        ):
            raise ValueError("Invalid Raft election timeout range")

        self.lock = threading.RLock()

        self.state = self.FOLLOWER

        self.current_term = 0
        self.voted_for = None

        self.log = []

        self.commit_index = 0
        self.last_applied = 0

        self.leader_id = None

        self.next_index = {}
        self.match_index = {}
        self._replication_locks = {
            peer_id: threading.Lock()
            for peer_id in self.members
            if peer_id != self.node_id
        }
        self.replication_status = {
            peer_id: {
                "ackStatus": "PENDING",
                "lastAttemptAt": None,
                "lastAcknowledgedAt": None,
                "lastError": None,
            }
            for peer_id in self._replication_locks
        }

        self.applied_results = []

        self.votes_received = set()

        self.running = False
        self.last_quorum_at = None
        self.last_quorum_acknowledgements = 0
        self.last_successful_sync_at = None
        self.last_application_error = None

        self.last_heartbeat = time.monotonic()
        self.election_timeout = self._random_timeout()

        self.heartbeat_thread = None
        self.election_executor = None
        self.last_leader_contact = None

        self._load_persistent_state()

    # ==========================================
    # INITIALIZATION
    # ==========================================

    def _random_timeout(self):
        seed = f"{self.cluster_id}:{self.current_term}"
        ordered_members = sorted(
            self.members,
            key=lambda member: hashlib.sha256(
                f"{seed}:{member}".encode("utf-8")
            ).digest(),
        )
        slot = ordered_members.index(self.node_id)
        slot_width = (
            self.election_timeout_max - self.election_timeout_min
        ) / len(ordered_members)
        lower = self.election_timeout_min + slot_width * (slot + 0.1)
        upper = self.election_timeout_min + slot_width * (slot + 0.9)
        return self._random.uniform(lower, upper)

    def _load_persistent_state(self):

        saved = self.store.load(self.node_id)

        if not saved:
            self._persist()
            return

        if saved.get("clusterId") not in (
            None,
            self.cluster_id
        ):
            raise ValueError(
                "Persisted cluster ID does not match configured cluster"
            )

        saved_configuration = saved.get("configuration") or {}

        saved_members = saved_configuration.get("oldMembers")

        if saved_members and set(saved_members) != set(self.members):
            raise ValueError(
                "Persisted Raft membership does not match configured membership"
            )

        self.current_term = saved["currentTerm"]

        self.voted_for = saved["votedFor"]

        self.log = saved["log"]

        self.commit_index = saved["commitIndex"]

        self.last_applied = saved["lastApplied"]

        self.applied_results = saved["appliedResults"]

        self.last_heartbeat = time.monotonic()
        self.election_timeout = self._random_timeout()

    def _configuration(self):

        return {
            "oldMembers": self.members,
            "newMembers": None,
            "index": 0
        }

    def _persistent_state(self):

        return {
            "clusterId": self.cluster_id,
            "clusterConfigVersion": 1,
            "configuration": self._configuration(),
            "currentTerm": self.current_term,
            "votedFor": self.voted_for,
            "log": self.log,
            "commitIndex": self.commit_index,
            "lastApplied": self.last_applied,
            "appliedResults": self.applied_results
        }

    def _persist(self):

        self.store.save(
            self.node_id,
            self._persistent_state()
        )

    # ==========================================
    # LOG HELPERS
    # ==========================================

    def _last_log_index(self):

        return len(self.log)

    def _last_log_term(self):

        if not self.log:
            return 0

        return self.log[-1]["term"]

    def _term_at(self, index):

        if index == 0:
            return 0

        if index > len(self.log):
            return None

        return self.log[index - 1]["term"]

    def _last_index_of_term(self, term):

        for index in range(len(self.log), 0, -1):

            if self.log[index - 1]["term"] == term:
                return index

        return 0

    def _reset_election_timer(self):

        self.last_heartbeat = time.monotonic()

        self.election_timeout = self._random_timeout()

    # ==========================================
    # REQUEST VOTE
    # ==========================================

    def request_vote(
        self,
        term,
        candidate_id,
        last_log_index,
        last_log_term
    ):

        with self.lock:

            if candidate_id not in self.members:
                return {
                    "term": self.current_term,
                    "vote_granted": False
                }

            if term < self.current_term:

                return {
                    "term": self.current_term,
                    "vote_granted": False
                }

            # A higher term forces this node to become a follower.
            if term > self.current_term:

                self.current_term = term

                self.voted_for = None

                self.state = self.FOLLOWER

                self.leader_id = None

                self._persist()

            local_last_index = self._last_log_index()

            local_last_term = self._last_log_term()

            candidate_log_is_up_to_date = (
                last_log_term > local_last_term
                or (
                    last_log_term == local_last_term
                    and last_log_index >= local_last_index
                )
            )

            vote_granted = (
                candidate_log_is_up_to_date
                and (
                    self.voted_for is None
                    or self.voted_for == candidate_id
                )
            )

            if vote_granted:

                self.voted_for = candidate_id

                self.state = self.FOLLOWER

                self._reset_election_timer()

                self._persist()

            return {
                "term": self.current_term,
                "vote_granted": vote_granted
            }

    # ==========================================
    # APPEND ENTRIES
    # ==========================================

    def append_entries(
        self,
        term,
        leader_id,
        prev_log_index,
        prev_log_term,
        entries,
        leader_commit
    ):

        with self.lock:

            if leader_id not in self.members:
                return {
                    "term": self.current_term,
                    "success": False,
                    "match_index": 0
                }

            if term < self.current_term:

                return {
                    "term": self.current_term,
                    "success": False,
                    "match_index": 0
                }

            # A higher term invalidates the previous leadership and vote.
            if term > self.current_term:
                self.current_term = term
                self.voted_for = None
                self.state = self.FOLLOWER
                self.leader_id = None
                self.last_quorum_at = None
                self.last_quorum_acknowledgements = 0
                self._persist()

            # Do not accept two different leaders in the same term.
            if (
                term == self.current_term
                and self.leader_id is not None
                and self.leader_id != leader_id
            ):
                return {
                    "term": self.current_term,
                    "success": False,
                    "match_index": 0,
                    "conflict_index": len(self.log) + 1,
                    "conflict_term": 0
                }

            self.state = self.FOLLOWER
            self.leader_id = leader_id

            self._reset_election_timer()
            self.last_leader_contact = time.monotonic()

            # Check the previous log entry.
            if prev_log_index > len(self.log):

                self._persist()

                return {
                    "term": self.current_term,
                    "success": False,
                    "match_index": len(self.log),
                    "conflict_index": len(self.log) + 1
                }

            if (
                prev_log_index > 0
                and self._term_at(prev_log_index) != prev_log_term
            ):

                conflict_term = self._term_at(prev_log_index)

                first_index = prev_log_index

                while (
                    first_index > 1
                    and self._term_at(first_index - 1) == conflict_term
                ):
                    first_index -= 1

                self._persist()

                return {
                    "term": self.current_term,
                    "success": False,
                    "match_index": 0,
                    "conflict_index": first_index,
                    "conflict_term": conflict_term
                }

            expected_index = prev_log_index + 1
            previous_entry_term = prev_log_term
            for entry in entries:
                if (
                    entry.get("index") != expected_index
                    or entry.get("term", term + 1) > term
                    or entry.get("term", 0) < previous_entry_term
                ):
                    return {
                        "term": self.current_term,
                        "success": False,
                        "match_index": 0,
                        "conflict_index": expected_index,
                        "conflict_term": 0,
                    }
                previous_entry_term = entry["term"]
                expected_index += 1

            # Validate and reconcile on a copy so a rejected request is atomic.
            reconciled_log = list(self.log)
            for entry in entries:

                index = entry["index"]

                if index <= len(reconciled_log):

                    existing = reconciled_log[index - 1]

                    if existing["term"] != entry["term"]:

                        if index <= self.commit_index:

                            raise RuntimeError(
                                "Attempted to overwrite a committed log entry"
                            )

                        reconciled_log = reconciled_log[:index - 1]

                        reconciled_log.append(entry)
                    elif (
                        existing.get("requestId") != entry.get("requestId")
                        or existing.get("command") != entry.get("command")
                    ):
                        return {
                            "term": self.current_term,
                            "success": False,
                            "match_index": max(0, index - 1),
                            "conflict_index": index,
                            "conflict_term": existing["term"],
                        }

                else:

                    if index != len(reconciled_log) + 1:

                        raise ValueError(
                            "Log entries must have contiguous indexes"
                        )

                    reconciled_log.append(entry)

            previous_log = self.log
            previous_commit_index = self.commit_index
            self.log = reconciled_log

            # Update commit index.
            if leader_commit > self.commit_index:

                self.commit_index = max(
                    self.commit_index,
                    min(leader_commit, prev_log_index + len(entries))
                )

            try:
                self._persist()
            except Exception:
                self.log = previous_log
                self.commit_index = previous_commit_index
                raise
            self.last_successful_sync_at = time.time() * 1000

            replicated_match_index = prev_log_index + len(entries)

            return {
                "term": self.current_term,
                "success": True,
                "match_index": replicated_match_index,
                "conflict_index": 0,
                "conflict_term": 0
            }

    # ==========================================
    # START ELECTION
    # ==========================================

    def start_election(self, request_vote_callback, require_timeout=False):

        with self.lock:

            if not self.running:
                return False

            if require_timeout and not self.check_election_timeout():
                return False

            election_term = self.current_term + 1
            candidate_state = self._persistent_state()
            candidate_state["currentTerm"] = election_term
            candidate_state["votedFor"] = self.node_id
            self.store.save(self.node_id, candidate_state)

            self.state = self.CANDIDATE

            self.current_term = election_term

            self.voted_for = self.node_id

            self.leader_id = None

            self.votes_received = {
                self.node_id
            }

            self._reset_election_timer()

            last_log_index = self._last_log_index()

            last_log_term = self._last_log_term()

            logger.info(
                "node=%s term=%s state=%s log_index=%s commit_index=%s applied_index=%s election started self_vote=1 voters=%s quorum=%s",
                self.node_id, election_term, self.state, last_log_index,
                self.commit_index, self.last_applied, len(self.members),
                len(self.members) // 2 + 1,
            )

        peers = [peer for peer in self.members if peer != self.node_id]
        completed = threading.Event()
        remaining = len(peers)

        def handle_response(future, peer_id):
            nonlocal remaining
            try:
                response = future.result()
                with self.lock:
                    if not self.running:
                        return
                    if response["term"] > self.current_term:
                        self.current_term = response["term"]
                        self.voted_for = None
                        self.state = self.FOLLOWER
                        self.leader_id = None
                        self.last_quorum_at = None
                        self.last_quorum_acknowledgements = 0
                        self._persist()
                        completed.set()
                    elif (
                        self.state == self.CANDIDATE
                        and self.current_term == election_term
                        and response["term"] == election_term
                    ):
                        if response["vote_granted"]:
                            self.votes_received.add(peer_id)
                        logger.info(
                            "node=%s term=%s state=%s peer=%s vote_granted=%s votes=%s/%s",
                            self.node_id, election_term, self.state, peer_id,
                            response["vote_granted"], len(self.votes_received),
                            len(self.members),
                        )
                        if self._has_majority():
                            self._become_leader()
                            completed.set()
            except CancelledError:
                pass
            except grpc.RpcError:
                # The transport logs the peer, gRPC status, and deadline.
                pass
            except Exception:
                logger.exception(
                    "node=%s election_term=%s peer=%s vote request or response handling failed",
                    self.node_id, election_term, peer_id,
                )
            finally:
                with self.lock:
                    remaining -= 1
                    if remaining == 0:
                        completed.set()

        for peer_id in peers:
            future = self.election_executor.submit(
                request_vote_callback, peer_id, election_term, self.node_id,
                last_log_index, last_log_term,
            )
            future.add_done_callback(
                lambda result, peer=peer_id: handle_response(result, peer)
            )

        while not completed.wait(0.1):
            with self.lock:
                if not self.running or self.current_term != election_term or self.state != self.CANDIDATE:
                    break

        with self.lock:
            elected = self.state == self.LEADER and self.current_term == election_term
            logger.info(
                "node=%s election_term=%s state=%s votes=%s/%s quorum=%s result=%s",
                self.node_id, election_term, self.state, len(self.votes_received),
                len(self.members), len(self.members) // 2 + 1,
                "ELECTED" if elected else "NO_MAJORITY_OR_SUPERSEDED",
            )
            return elected

    # ==========================================
    # MAJORITY CHECK
    # ==========================================

    def _has_majority(self):

        return (
            len(self.votes_received)
            >= (len(self.members) // 2) + 1
        )

    # ==========================================
    # BECOME LEADER
    # ==========================================

    def _become_leader(self):

        self.state = self.LEADER

        self.leader_id = self.node_id

        last_index = self._last_log_index()

        for peer_id in self.members:

            if peer_id == self.node_id:
                continue

            self.next_index[peer_id] = last_index + 1

            self.match_index[peer_id] = 0
            self.replication_status[peer_id] = {
                "ackStatus": "PENDING",
                "lastAttemptAt": None,
                "lastAcknowledgedAt": None,
                "lastError": None,
            }

        self.match_index[self.node_id] = last_index
        self.last_quorum_at = None
        self.last_quorum_acknowledgements = 1

        self._persist()

    # ==========================================
    # LEADER HEARTBEAT / REPLICATION
    # ==========================================

    def replicate_to_peer(
        self,
        peer_id,
        append_entries_callback
    ):
        if peer_id not in self._replication_locks:
            return False

        replication_lock = self._replication_locks[peer_id]
        if not replication_lock.acquire(blocking=False):
            return False
        try:
            return self._replicate_to_peer_locked(
                peer_id,
                append_entries_callback,
            )
        finally:
            replication_lock.release()

    def _replicate_to_peer_locked(
        self,
        peer_id,
        append_entries_callback,
    ):

        with self.lock:

            if self.state != self.LEADER:
                return False

            next_index = self.next_index.get(
                peer_id,
                self._last_log_index() + 1
            )

            prev_log_index = next_index - 1

            prev_log_term = self._term_at(
                prev_log_index
            )

            entries = [
                entry.copy()
                for entry in self.log[next_index - 1:]
            ]

            term = self.current_term

            commit_index = self.commit_index
            progress = self.replication_status[peer_id]
            progress["ackStatus"] = "PENDING"
            progress["lastAttemptAt"] = time.time() * 1000
            progress["lastError"] = None

        try:

            response = append_entries_callback(
                peer_id,
                term,
                self.node_id,
                prev_log_index,
                prev_log_term,
                entries,
                commit_index
            )

        except Exception as error:
            error_message = f"{type(error).__name__}: {error}"[:300]
            if isinstance(error, grpc.RpcError):
                status_code = error.code()
                ack_status = (
                    "UNREACHABLE"
                    if status_code in {
                        grpc.StatusCode.UNAVAILABLE,
                        grpc.StatusCode.DEADLINE_EXCEEDED,
                        grpc.StatusCode.CANCELLED,
                    }
                    else "FAILED"
                )
            else:
                ack_status = "FAILED"
            with self.lock:
                if self.state == self.LEADER and self.current_term == term:
                    progress = self.replication_status[peer_id]
                    progress["ackStatus"] = ack_status
                    progress["lastError"] = error_message
            return False

        with self.lock:

            if (
                not isinstance(response, dict)
                or not isinstance(response.get("term"), int)
                or not isinstance(response.get("success"), bool)
                or not isinstance(response.get("match_index"), int)
            ):
                if self.state == self.LEADER and self.current_term == term:
                    progress = self.replication_status[peer_id]
                    progress["ackStatus"] = "FAILED"
                    progress["lastError"] = "Invalid AppendEntries response"
                return False

            if response["term"] > self.current_term:

                self.current_term = response["term"]

                self.voted_for = None

                self.state = self.FOLLOWER

                self.leader_id = None
                self.last_quorum_at = None
                self.last_quorum_acknowledgements = 0
                progress = self.replication_status[peer_id]
                progress["ackStatus"] = "FAILED"
                progress["lastError"] = (
                    f"Peer reported higher term {response['term']}"
                )

                self._persist()

                return False

            if self.state != self.LEADER or self.current_term != term:
                return False

            if response["term"] < term:
                progress = self.replication_status[peer_id]
                progress["ackStatus"] = "FAILED"
                progress["lastError"] = (
                    f"Peer acknowledged stale term {response['term']}"
                )
                return False

            if response["success"]:

                match_index = response["match_index"]
                expected_match_index = prev_log_index + len(entries)
                if (
                    match_index < prev_log_index
                    or match_index > expected_match_index
                    or match_index > self._last_log_index()
                ):
                    progress = self.replication_status[peer_id]
                    progress["ackStatus"] = "FAILED"
                    progress["lastError"] = (
                        "AppendEntries acknowledgement index was out of range"
                    )
                    return False

                match_index = max(
                    self.match_index.get(peer_id, 0),
                    match_index,
                )
                self.match_index[peer_id] = match_index

                self.next_index[peer_id] = max(
                    self.next_index.get(peer_id, 1),
                    match_index + 1,
                )
                progress = self.replication_status[peer_id]
                progress["ackStatus"] = (
                    "ACKNOWLEDGED"
                    if match_index >= self._last_log_index()
                    else "CATCHING UP"
                )
                progress["lastAcknowledgedAt"] = time.time() * 1000
                progress["lastError"] = None
                self.last_successful_sync_at = time.time() * 1000

                self._advance_commit_index()

                if entries:
                    logger.info(
                        "node=%s term=%s state=%s peer=%s replicated_through=%s entries=%s",
                        self.node_id, self.current_term, self.state, peer_id,
                        match_index, len(entries),
                    )

                return True

            progress = self.replication_status[peer_id]
            progress["ackStatus"] = "CATCHING UP"
            conflict_index = response.get("conflict_index", 0)
            conflict_term = response.get("conflict_term", 0)

            if conflict_term:

                last_index = self._last_index_of_term(
                    conflict_term
                )

                if last_index > 0:

                    self.next_index[peer_id] = last_index + 1

                else:

                    self.next_index[peer_id] = max(
                        1,
                        conflict_index
                    )

            elif conflict_index:

                self.next_index[peer_id] = max(
                    1,
                    conflict_index
                )

            else:

                self.next_index[peer_id] = max(1, next_index - 1)

            self.next_index[peer_id] = max(
                self.match_index.get(peer_id, 0) + 1,
                min(self.next_index[peer_id], self._last_log_index() + 1),
            )
            progress["lastError"] = (
                "Follower rejected previous log index; retrying from "
                f"index {self.next_index[peer_id]}"
            )

            return False

    def record_replication_round(self, term, acknowledged_peers):
            with self.lock:
                if self.state != self.LEADER or self.current_term != term:
                    return

                acknowledgements = {
                    peer_id for peer_id in acknowledged_peers
                    if peer_id in self.members and peer_id != self.node_id
                }
                acknowledgements.add(self.node_id)
                self.last_quorum_acknowledgements = len(acknowledgements)

                if self._has_member_majority(acknowledgements):
                    self.last_quorum_at = time.time() * 1000

    def _has_member_majority(self, members):
            return len(members) >= (len(self.members) // 2) + 1

    # ==========================================
    # COMMIT INDEX
    # ==========================================

    def _advance_commit_index(self):

        for index in range(
            self._last_log_index(),
            self.commit_index,
            -1
        ):

            if self._term_at(index) != self.current_term:
                continue

            replicated = 1

            for peer_id in self.members:

                if peer_id == self.node_id:
                    continue

                if self.match_index.get(peer_id, 0) >= index:
                    replicated += 1

            if replicated >= (len(self.members) // 2) + 1:

                previous_commit_index = self.commit_index
                self.commit_index = index

                try:
                    self._persist()
                except Exception:
                    self.commit_index = previous_commit_index
                    raise

                logger.info(
                    "node=%s term=%s state=%s commit_index=%s replicated=%s/%s",
                    self.node_id, self.current_term, self.state, index,
                    replicated, len(self.members),
                )
                break

    # ==========================================
    # COMMITTED LOG APPLICATION
    # ==========================================

    def get_next_committed_entry(self):

        with self.lock:

            if self.last_applied >= self.commit_index:
                return None

            next_index = self.last_applied + 1

            if next_index > len(self.log):
                return None

            return self.log[next_index - 1].copy()

    def mark_applied(self, index, result=None):

        with self.lock:

            expected_index = self.last_applied + 1

            if index != expected_index:
                raise ValueError(
                    f"Expected applied index {expected_index}, "
                    f"received {index}"
                )

            if index > self.commit_index:
                raise ValueError(
                    "Cannot apply an uncommitted log entry"
                )

            self.last_applied = index

            self.applied_results.append({
                "index": index,
                "result": result
            })

            try:
                self._persist()
            except Exception:
                self.applied_results.pop()
                self.last_applied = expected_index - 1
                raise

    # ==========================================
    # CLIENT COMMAND SUBMISSION
    # ==========================================

    def submit_command(self, command_id, command_type, payload):

        if not command_id:
            raise ValueError("Command ID is required")

        if not command_type:
            raise ValueError("Command type is required")

        if not isinstance(payload, dict):
            raise ValueError("Command payload must be a dictionary")

        if any(
            key in payload
            for key in ("_raftTimestamp", "operationId", "operationType", "requestId")
        ):
            raise ValueError("Raft operation metadata is reserved")

        with self.lock:

            if self.state != self.LEADER:
                return {
                    "success": False,
                    "committed": False,
                    "leader_id": self.leader_id,
                    "message": "This node is not the leader"
                }

            # Prevent duplicate log entries for the same request.
            for entry in self.log:

                if entry["requestId"] == command_id:
                    existing_payload = json.loads(
                        entry["command"]["payload"]
                    )
                    for metadata_key in (
                        "_raftTimestamp",
                        "operationId",
                        "operationType",
                        "requestId",
                    ):
                        existing_payload.pop(metadata_key, None)
                    if (
                        entry["command"]["type"] != command_type
                        or existing_payload != payload
                    ):
                        raise ValueError(
                            "Request ID was reused with a different command"
                        )

                    return {
                        "success": True,
                        "committed": entry["index"] <= self.commit_index,
                        "index": entry["index"],
                        "leader_id": self.node_id,
                        "message": "Command already exists"
                    }

            index = self._last_log_index() + 1
            command_payload = dict(payload)
            command_timestamp = datetime.now(timezone.utc).isoformat()
            command_payload.update({
                "_raftTimestamp": command_timestamp,
                "operationId": str(
                    uuid5(NAMESPACE_URL, f"{self.cluster_id}:{command_id}")
                ),
                "operationType": command_type,
                "requestId": command_id,
            })

            entry = {
                "index": index,
                "term": self.current_term,
                "timestamp": command_timestamp,
                "requestId": command_id,
                "command": {
                    "type": command_type,
                    "payload": json.dumps(
                        command_payload,
                        sort_keys=True,
                        separators=(",", ":"),
                        default=str
                    )
                }
            }

            self.log.append(entry)

            self.match_index[self.node_id] = index

            try:
                self._persist()
            except Exception:
                self.log.pop()
                self.match_index[self.node_id] = index - 1
                raise

            print(
                f"[{self.node_id}] Command appended "
                f"at index {index}: {command_type}"
            )

            return {
                "success": True,
                "committed": False,
                "index": index,
                "leader_id": self.node_id,
                "message": "Command appended; awaiting majority"
            }

    # ==========================================
    # WAIT FOR MAJORITY COMMITMENT
    # ==========================================

    def wait_for_commit(self, index, timeout=10):

        import time

        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:

            with self.lock:

                if self.state != self.LEADER:
                    return False

                if self.commit_index >= index:
                    return True

            time.sleep(0.05)

        return False

    # ==========================================
    # WAIT FOR STATE MACHINE APPLICATION
    # ==========================================

    def wait_for_application(self, index, timeout=15):

        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:

            with self.lock:

                if self.last_applied >= index:
                    return True

            time.sleep(0.05)

        return False
    

    # ==========================================
    # NODE MONITORING
    # ==========================================

    def check_election_timeout(self):

        with self.lock:

            if not self.running:
                return False

            if self.state == self.LEADER:
                return False

            elapsed = (
                time.monotonic() - self.last_heartbeat
            )

            if elapsed < self.election_timeout:
                return False

        return True

    def get_status(self):

        with self.lock:

            return {
                "nodeId": self.node_id,
                "state": self.state,
                "currentTerm": self.current_term,
                "votedFor": self.voted_for,
                "leaderId": self.leader_id,
                "commitIndex": self.commit_index,
                "lastApplied": self.last_applied,
                "lastLogIndex": self._last_log_index(),
                "running": self.running,
                "lastQuorumAt": self.last_quorum_at,
                "lastQuorumAcknowledgements": self.last_quorum_acknowledgements,
                "lastSuccessfulSyncAt": self.last_successful_sync_at,
                "applicationFailure": self.last_application_error,
                "clusterId": self.cluster_id,
                "clusterConfigVersion": 1,
                "configuredMembers": list(self.members),
                "configuration": self._configuration(),
                "topologyId": self.topology_id,
                "replicationProgress": {
                    peer_id: {
                        "nextIndex": self.next_index.get(peer_id, 0),
                        "matchIndex": self.match_index.get(peer_id, 0),
                        **self.replication_status.get(peer_id, {}),
                    }
                    for peer_id in self.members
                    if peer_id != self.node_id and self.state == self.LEADER
                },
                "votesReceived": len(self.votes_received),
                "electionTimeoutMs": int(self.election_timeout * 1000),
            }

    # ==========================================
    # START / STOP
    # ==========================================

    def start(self):

        with self.lock:

            if self.running:
                return

            self.running = True
            self.election_executor = ThreadPoolExecutor(
                max_workers=len(self.members) - 1,
                thread_name_prefix=f"{self.node_id}-vote",
            )

            self._reset_election_timer()

            self.heartbeat_thread = threading.Thread(
                target=self._run_monitor,
                daemon=True
            )

            self.heartbeat_thread.start()

    def stop(self):

        with self.lock:
            self.running = False

        if self.heartbeat_thread:
            self.heartbeat_thread.join(timeout=2)
        if self.election_executor:
            self.election_executor.shutdown(wait=False, cancel_futures=True)

    def _run_monitor(self):

        while self.running:

            time.sleep(0.1)

            if self.check_election_timeout():

                # The gRPC transport will be connected
                # in the next implementation step.
                pass
