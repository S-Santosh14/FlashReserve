from backend.config import settings


RAFT_NODES = settings.raft_nodes()


def get_node_addresses():

    return {
        node_id: (
            f"{config['host']}:{config['port']}"
        )
        for node_id, config in RAFT_NODES.items()
    }


def get_node_port(node_id):

    if node_id not in RAFT_NODES:
        raise ValueError("Unknown Raft node")

    return RAFT_NODES[node_id]["port"]


def get_node_mongo_uri(node_id):
    return settings.raft_mongo_uri(node_id)


def get_node_database_name(node_id):
    return settings.raft_database_name(node_id)