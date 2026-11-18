import time

import streamlit as st

from frontend.utils.api import get_raft_cluster_status
from frontend.utils.operating_mode import RAFT_NODES, raft_cluster_availability


def render_raft_monitor():
    _render_cluster_status()


def _build_monitor_rows(statuses, now_ms):
    observed_statuses = {}
    for raw_status in statuses:
        if not isinstance(raw_status, dict):
            continue
        node_id = raw_status.get("nodeId") or raw_status.get("node_id")
        if node_id:
            observed_statuses[str(node_id)] = raw_status

    fresh_statuses = []
    rows = []
    for node_id, _ in RAFT_NODES:
        observed_status = observed_statuses.get(node_id)
        status = dict(observed_status or {
            "nodeId": node_id,
            "available": False,
            "rpcConnected": False,
            "database": {"connected": False},
            "observed_at": now_ms / 1000,
        })
        status.setdefault("nodeId", node_id)
        observed_at = status.get("observed_at")
        stale = (
            not isinstance(observed_at, (int, float))
            or now_ms - observed_at * 1000 > 15_000
        )
        if stale:
            status["available"] = False
        fresh_statuses.append(status)

        database = status.get("database")
        if not isinstance(database, dict):
            database = {}
        database_connected = database.get("connected") is True
        healthy = (
            status.get("available") is True
            and status.get("healthy") is True
            and status.get("topologyMatches") is True
            and database_connected
            and status.get("applicationStatus") != "failed"
        )
        role = str(status.get("role") or "unknown").upper()
        heartbeat_age = status.get("heartbeatAgeMs")
        if role == "LEADER" and isinstance(status.get("lastQuorumAt"), (int, float)):
            heartbeat_age = max(0, now_ms - status["lastQuorumAt"])
        heartbeat = (
            f"{int(heartbeat_age)} ms"
            if isinstance(heartbeat_age, (int, float))
            else "Unknown"
        )
        term = status.get("currentTerm")
        rows.append({
            "Node ID": node_id,
            "Role": role,
            "Term": str(term) if isinstance(term, (int, float)) else "—",
            "Reported Leader": str(status.get("leaderId") or "—"),
            "Status": (
                "STALE" if stale else "READY" if healthy else
                "UNAVAILABLE" if not status.get("available") else "DEGRADED"
            ),
            "RPC Connectivity": (
                "Connected" if status.get("rpcConnected") else "Unavailable"
            ),
            "Database Connectivity": (
                "Connected" if database_connected else "Unavailable"
            ),
            "Heartbeat": heartbeat,
            "Replication ACK": str(status.get("replicationAck") or "UNKNOWN"),
        })
    return fresh_statuses, rows


@st.fragment(run_every="5s")
def _render_cluster_status():
    statuses = get_raft_cluster_status(timeout=1.5, force_refresh=True)
    now_ms = time.time() * 1000
    expected_nodes = len(RAFT_NODES)
    majority = expected_nodes // 2 + 1
    fresh_statuses, rows = _build_monitor_rows(statuses, now_ms)

    valid_leader, reason, leader = raft_cluster_availability(
        fresh_statuses,
        now_ms=now_ms,
    )
    active_nodes = sum(row["Status"] == "READY" for row in rows)
    failed_nodes = expected_nodes - active_nodes
    reachable_nodes = sum(status.get("available") is True for status in fresh_statuses)
    quorum_available = reachable_nodes >= majority and active_nodes >= majority
    terms = [
        status["currentTerm"]
        for status in fresh_statuses
        if isinstance(status.get("currentTerm"), (int, float))
    ]
    current_term = (
        leader.get("currentTerm")
        if valid_leader and leader
        else max(terms, default="—")
    )
    leader_name = leader.get("nodeId") if valid_leader and leader else "Unconfirmed"

    st.subheader("Live Raft cluster monitoring")
    st.caption("Live node health and replication status reported by the Raft cluster.")
    with st.container(horizontal=True, wrap=True):
        st.metric("Total nodes", expected_nodes, border=True)
        st.metric("Active nodes", active_nodes, border=True)
        st.metric("Failed / degraded", failed_nodes, border=True)
        st.metric("Current leader", leader_name, border=True)
        st.metric("Current term", current_term, border=True)
        st.metric(
            "Quorum",
            "Available" if quorum_available else "Unavailable",
            f"{active_nodes}/{majority} healthy",
            border=True,
        )

    if not valid_leader:
        st.warning(
            reason or "No quorum-confirmed leader is currently available.",
            title="Raft cluster status",
        )

    with st.container(border=True):
        st.subheader("Seven-node status")
        st.dataframe(
            rows,
            column_order=[
                "Node ID",
                "Role",
                "Term",
                "Reported Leader",
                "Status",
                "RPC Connectivity",
                "Database Connectivity",
                "Heartbeat",
                "Replication ACK",
            ],
            column_config={
                "Node ID": st.column_config.TextColumn(width="small"),
                "Role": st.column_config.TextColumn(width="small"),
                "Term": st.column_config.TextColumn(width="small"),
                "Reported Leader": st.column_config.TextColumn(width="small"),
                "Status": st.column_config.TextColumn(width="small"),
                "RPC Connectivity": st.column_config.TextColumn(width="small"),
                "Database Connectivity": st.column_config.TextColumn(width="small"),
                "Heartbeat": st.column_config.TextColumn(width="small"),
                "Replication ACK": st.column_config.TextColumn(width="small"),
            },
            hide_index=True,
            height=300,
            width="stretch",
            alt="Live Raft node health, term, heartbeat, and replication status",
        )

    st.subheader("Node details")
    for status in fresh_statuses:
        node_id = status.get("nodeId", status.get("node_id", "unknown"))
        with st.expander(node_id):
            st.json({
                "role": status.get("role"),
                "currentTerm": status.get("currentTerm"),
                "leaderId": status.get("leaderId"),
                "available": status.get("available"),
                "healthy": status.get("healthy"),
                "rpcConnected": status.get("rpcConnected"),
                "database": status.get("database"),
                "heartbeatAgeMs": status.get("heartbeatAgeMs"),
                "lastLogIndex": status.get("lastLogIndex"),
                "commitIndex": status.get("commitIndex"),
                "lastApplied": status.get("lastApplied"),
                "replicationLag": status.get("replicationLag"),
                "logStatus": status.get("logStatus"),
                "replicationAck": status.get("replicationAck"),
                "replicationAckDetails": status.get("replicationAckDetails"),
                "applicationFailure": status.get("applicationFailure"),
            })
