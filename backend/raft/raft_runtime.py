import json
import logging
import threading
import time

import grpc
from pymongo.errors import PyMongoError

from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.config import settings

logger = logging.getLogger(__name__)


class RaftRuntime:

    HEARTBEAT_INTERVAL = settings.RAFT_HEARTBEAT_INTERVAL
    MONITOR_INTERVAL = 0.1
    APPLY_INTERVAL = 0.1

    def __init__(self, node, transport, state_machine=None):

        self.node = node
        self.transport = transport
        self.state_machine = state_machine

        self.running = False

        self.monitor_thread = None
        self.replication_thread = None
        self.apply_thread = None
        self.status_thread = None

        self.executor = ThreadPoolExecutor(
            max_workers=6,
            thread_name_prefix=f"{node.node_id}-peer"
        )
        self.status_executor = ThreadPoolExecutor(
            max_workers=len(node.members) - 1,
            thread_name_prefix=f"{node.node_id}-status",
        )

        self.stop_event = threading.Event()

    # ==========================================
    # START RUNTIME
    # ==========================================

    def start(self):

        if self.running:
            return

        self.running = True
        self.stop_event.clear()

        self.node.start()

        self.monitor_thread = threading.Thread(
            target=self._election_monitor,
            daemon=True
        )

        self.replication_thread = threading.Thread(
            target=self._heartbeat_monitor,
            daemon=True
        )

        self.apply_thread = threading.Thread(
            target=self._apply_monitor,
            daemon=True
        )
        self.status_thread = threading.Thread(
            target=self._status_monitor,
            daemon=True,
        )

        self.monitor_thread.start()
        self.replication_thread.start()
        self.apply_thread.start()
        self.status_thread.start()

        self._log("runtime started")

    def _log(self, message, *args, level=logging.INFO):
        with self.node.lock:
            node_id = self.node.node_id
            term = self.node.current_term
            state = self.node.state
            log_index = len(self.node.log)
            commit = self.node.commit_index
            applied = self.node.last_applied
        logger.log(
            level,
            "node=%s term=%s state=%s log_index=%s commit_index=%s applied_index=%s " + message,
            node_id, term, state, log_index, commit, applied, *args,
        )

    # ==========================================
    # ELECTION MONITOR
    # ==========================================

    def _election_monitor(self):

        while not self.stop_event.is_set():

            try:

                if self.node.check_election_timeout():

                    elected = self.node.start_election(
                        self.transport.request_vote,
                        require_timeout=True,
                    )

                    if elected:

                        self._log("elected leader votes=%s", len(self.node.votes_received))

            except PyMongoError as error:
                self._log(
                    "election aborted before requesting votes: "
                    "Raft term and self-vote could not be durably saved "
                    "error=%s",
                    type(error).__name__,
                    level=logging.ERROR,
                )
                self.stop_event.wait(
                    max(self.node.election_timeout, settings.RAFT_RPC_TIMEOUT)
                )
                continue

            except Exception as error:

                self._log("election failed error=%s", type(error).__name__, level=logging.ERROR)

            self.stop_event.wait(
                self.MONITOR_INTERVAL
            )

    # ==========================================
    # HEARTBEAT AND LOG REPLICATION
    # ==========================================

    def _heartbeat_monitor(self):

        while not self.stop_event.is_set():

            try:

                if self.node.state == self.node.LEADER:

                    self._replicate_to_followers()

            except Exception as error:

                self._log("replication round failed error=%s", type(error).__name__, level=logging.ERROR)

            self.stop_event.wait(
                self.HEARTBEAT_INTERVAL
            )

    def _replicate_to_followers(self):

        with self.node.lock:

            if self.node.state != self.node.LEADER:
                return

            followers = [
                peer_id
                for peer_id in self.node.members
                if peer_id != self.node.node_id
            ]

        futures = {}

        for peer_id in followers:

            future = self.executor.submit(
                self.node.replicate_to_peer,
                peer_id,
                self.transport.append_entries
            )

            futures[future] = peer_id

        with self.node.lock:
            replication_term = self.node.current_term

        acknowledged_peers = set()
        try:
            completed = as_completed(futures, timeout=3)
            for future in completed:
                peer_id = futures[future]
                try:
                    if future.result():
                        acknowledged_peers.add(peer_id)
                        self._log("append acknowledged peer=%s", peer_id, level=logging.DEBUG)
                except Exception as error:
                    self._log(
                        "communication failure peer=%s error=%s",
                        peer_id, type(error).__name__, level=logging.WARNING,
                    )
        except TimeoutError:
            self._log("replication round timed out", level=logging.WARNING)

        self.node.record_replication_round(
            replication_term,
            acknowledged_peers,
        )

    def _status_monitor(self):
        while not self.stop_event.is_set():
            try:
                self._report_status()
            except Exception:
                logger.exception("node=%s status monitor failed", self.node.node_id)
            self.stop_event.wait(settings.RAFT_STATUS_INTERVAL)

    def _report_status(self):
        if not hasattr(self.transport, "get_peer_status"):
            return
        with self.node.lock:
            local = self.node.get_status()
            contact = self.node.last_leader_contact
            timeout = self.node.election_timeout
        leader = None
        if local["state"] == self.node.LEADER:
            if local["lastQuorumAt"] and (
                time.time() * 1000 - local["lastQuorumAt"] < timeout * 1000
            ):
                leader = local["nodeId"]
        elif (
            local["state"] == self.node.FOLLOWER
            and contact is not None
            and time.monotonic() - contact < timeout
        ):
            leader = local["leaderId"]

        peers = [peer for peer in self.node.members if peer != self.node.node_id]
        futures = {
            self.status_executor.submit(self.transport.get_peer_status, peer): peer
            for peer in peers
        }
        observations = {}
        try:
            for future in as_completed(futures, timeout=settings.RAFT_RPC_TIMEOUT + 1):
                peer = futures[future]
                try:
                    observations[peer] = future.result()
                except grpc.RpcError:
                    observations[peer] = None
                except Exception:
                    logger.exception(
                        "node=%s invalid peer status peer=%s",
                        self.node.node_id, peer,
                    )
                    observations[peer] = None
        except TimeoutError:
            logger.warning("node=%s cluster status observation timed out", self.node.node_id)

        lines = [
            "cluster observation (peer status is sampled, not consensus)",
            f"local={local['nodeId']} role={local['state']} term={local['currentTerm']} "
            f"known_leader={leader or 'UNKNOWN'} quorum={len(self.node.members) // 2 + 1}/{len(self.node.members)}",
            "node role availability term log commit applied database",
            f"{local['nodeId']} {local['state']} LOCAL {local['currentTerm']} "
            f"{local['lastLogIndex']} {local['commitIndex']} {local['lastApplied']} local",
        ]
        for peer in peers:
            status = observations.get(peer)
            if status is None:
                lines.append(f"{peer} UNKNOWN UNAVAILABLE - - - - UNKNOWN")
            else:
                lines.append(
                    f"{peer} {status.state} AVAILABLE {status.current_term} "
                    f"{status.last_log_index} {status.commit_index} {status.last_applied} "
                    f"{'CONNECTED' if status.database_connected else 'UNAVAILABLE'}"
                )
        if local["state"] == self.node.LEADER:
            lines.append("leader local replication progress: peer next_index match_index")
            for peer, progress in local["replicationProgress"].items():
                lines.append(
                    f"{peer} {progress['nextIndex']} {progress['matchIndex']} "
                    f"{progress['ackStatus']} error={progress['lastError'] or '-'}"
                )
        if contact is not None:
            lines.append(f"last_leader_contact_age_seconds={time.monotonic() - contact:.1f}")
        logger.info("\n%s", "\n".join(lines))

    # ==========================================
    # COMMITTED COMMAND APPLICATION
    # ==========================================

    def _apply_monitor(self):

        while not self.stop_event.is_set():

            try:

                if self.state_machine is not None:

                    self._apply_committed_entries()

            except Exception as error:

                self._log("state machine error=%s", type(error).__name__, level=logging.ERROR)

            self.stop_event.wait(
                self.APPLY_INTERVAL
            )

    def _apply_committed_entries(self):

        while not self.stop_event.is_set():

            with self.node.lock:

                next_index = self.node.last_applied + 1

                if next_index > self.node.commit_index:
                    return

                entry = next(
                    (
                        item for item in self.node.log
                        if item["index"] == next_index
                    ),
                    None
                )

                if entry is None:
                    self._log("committed log entry missing index=%s", next_index, level=logging.ERROR)
                    return

                command_id = entry["requestId"]
                command_type = entry["command"]["type"]
                command_payload = entry["command"]["payload"]

            try:

                result = self.state_machine.apply_command(
                    command_id=command_id,
                    command_type=command_type,
                    payload=command_payload
                )

            except Exception as error:
                with self.node.lock:
                    self.node.last_application_error = str(error)

                self._log(
                    "application will retry index=%s error=%s",
                    next_index, type(error).__name__, level=logging.ERROR,
                )

                return

            # Another process may still own the command lease.
            # Do not advance lastApplied until it finishes.
            if result.get("pending"):

                return

            with self.node.lock:

                if self.node.last_applied + 1 != next_index:
                    return

                self.node.applied_results.append({
                    "index": next_index,
                    "requestId": command_id,
                    "result": result
                })

                self.node.last_applied = next_index
                self.node.last_application_error = None

                try:
                    self.node._persist()
                except Exception as error:
                    self.node.applied_results.pop()
                    self.node.last_applied = next_index - 1
                    self.node.last_application_error = str(error)
                    raise

            self._log("committed command applied type=%s index=%s", command_type, next_index)

    # ==========================================
    # STOP RUNTIME
    # ==========================================

    def stop(self):

        if not self.running:
            return

        self._log("stopping Raft runtime")

        self.running = False
        self.stop_event.set()

        self.node.stop()

        if self.monitor_thread:
            self.monitor_thread.join(timeout=3)

        if self.replication_thread:
            self.replication_thread.join(timeout=3)

        if self.apply_thread:
            self.apply_thread.join(timeout=3)
        if self.status_thread:
            self.status_thread.join(timeout=settings.RAFT_RPC_TIMEOUT + 2)

        self.executor.shutdown(
            wait=False,
            cancel_futures=True
        )
        self.status_executor.shutdown(wait=False, cancel_futures=True)

        self._log("Raft runtime stopped")