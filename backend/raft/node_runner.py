import argparse
import logging
import signal
import time

from backend.config import settings
from backend.database.raft_database import (
    close_raft_connections,
    get_raft_database,
)

from backend.raft.state_machine import RaftStateMachine

from backend.raft.mongo_raft_store import MongoRaftStore
from backend.raft.raft_node import RaftNode
from backend.raft.grpc_transport import RaftGrpcTransport, RaftPortBindError
from backend.raft.raft_runtime import RaftRuntime

from backend.raft.cluster_config import (
    RAFT_NODES,
    get_node_addresses,
    get_node_port
)

logger = logging.getLogger(__name__)


def run_node(node_id):

    if node_id not in RAFT_NODES:
        raise ValueError("Invalid node ID")

    settings.validate_raft_timing()
    stopped = False
    runtime = None
    transport = None

    def shutdown(signum, frame):

        nonlocal stopped

        if stopped:
            return

        stopped = True

    try:
        logger.info("Starting Raft node %s.", node_id)
        node_database = get_raft_database(node_id)
        store = MongoRaftStore(node_database)
        state_machine = RaftStateMachine(node_database)
        members = list(RAFT_NODES)
        node = RaftNode(
            node_id=node_id,
            members=members,
            store=store,
            topology_id=settings.raft_topology_id(),
            election_timeout_min=settings.RAFT_ELECTION_TIMEOUT_MIN,
            election_timeout_max=settings.RAFT_ELECTION_TIMEOUT_MAX,
        )
        transport = RaftGrpcTransport(
            node=node,
            addresses=get_node_addresses(),
        )
        port = get_node_port(node_id)
        transport.start_server(host="0.0.0.0", port=port)
        runtime = RaftRuntime(
            node=node,
            transport=transport,
            state_machine=state_machine,
        )
        runtime.start()
        with node.lock:
            logger.info(
                "node=%s database=%s port=%s term=%s state=%s election_timeout_ms=%s log_index=%s commit_index=%s applied_index=%s",
                node_id,
                node_database.name,
                port,
                node.current_term,
                node.state,
                int(node.election_timeout * 1000),
                node._last_log_index(),
                node.commit_index,
                node.last_applied,
            )

        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

        while not stopped:
            time.sleep(1)

    finally:
        if runtime is not None:
            runtime.stop()
        if transport is not None:
            transport.close()
        close_raft_connections()


def main():

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    parser = argparse.ArgumentParser(
        description="Start a FlashReserve Raft node"
    )

    parser.add_argument(
        "--node",
        required=True,
        choices=list(RAFT_NODES.keys()),
        help="Raft node ID to start"
    )

    args = parser.parse_args()

    try:
        run_node(args.node)
    except RaftPortBindError as error:
        logger.error("%s", error)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()