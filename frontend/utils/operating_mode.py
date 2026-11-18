import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[2] / ".env")


NORMAL_MODE = "Normal Mode"
RAFT_MODE = "Raft Mode"
MODE_OPTIONS = (NORMAL_MODE, RAFT_MODE)
RAFT_CLUSTER_SIZE = int(
    os.environ.get(
        "RAFT_CLUSTER_SIZE",
        os.environ.get("FLASHRESERVE_RAFT_CLUSTER_SIZE", "7"),
    )
)


def configured_raft_nodes(cluster_size=RAFT_CLUSTER_SIZE, environ=None):
    environ = os.environ if environ is None else environ
    if cluster_size < 3 or cluster_size % 2 == 0:
        raise ValueError("RAFT_CLUSTER_SIZE must be an odd integer of at least 3.")
    return tuple(
        (
            f"node-{index}",
            environ.get(
                f"RAFT_NODE_{index}_API_URL",
                environ.get(
                    f"FLASHRESERVE_RAFT_NODE_{index}_URL",
                    f"http://127.0.0.1:{5000 + index}",
                ),
            ).rstrip("/"),
        )
        for index in range(1, cluster_size + 1)
    )


if RAFT_CLUSTER_SIZE < 3 or RAFT_CLUSTER_SIZE % 2 == 0:
    raise ValueError("RAFT_CLUSTER_SIZE must be an odd integer of at least 3.")
RAFT_NODES = configured_raft_nodes()
RAFT_ENTRY_URL = RAFT_NODES[0][1]


def api_base_url(mode, environ=None):
    environ = os.environ if environ is None else environ
    normal_url = (
        environ.get("API_BASE_URL")
        or environ.get("FLASHRESERVE_NORMAL_API_URL")
    )
    legacy_url = environ.get("FLASHRESERVE_API_URL")
    if legacy_url and legacy_url.rstrip("/") not in {url for _, url in RAFT_NODES}:
        normal_url = normal_url or legacy_url
    normal_url = (normal_url or "http://localhost:5000").rstrip("/")
    if mode == NORMAL_MODE:
        return normal_url
    if mode == RAFT_MODE:
        return (
            environ.get("RAFT_API_BASE_URL")
            or normal_url
        ).rstrip("/")
    raise ValueError(f"Unsupported FlashReserve operating mode: {mode}")


def switch_mode(session_state, selected_mode):
    if selected_mode not in MODE_OPTIONS:
        raise ValueError(f"Unsupported FlashReserve operating mode: {selected_mode}")

    previous_mode = session_state.get("operating_mode", NORMAL_MODE)
    if previous_mode == selected_mode:
        return False

    if session_state.get("logged_in"):
        session_state["mode_switch_notice"] = (
            "Operating mode is locked until you log out."
        )
        return False

    if session_state.get("booking_submit_in_progress"):
        session_state["mode_selector"] = previous_mode
        session_state["mode_selector_main"] = previous_mode
        session_state["mode_switch_notice"] = (
            "Mode cannot be changed while a booking request is in progress. "
            "Wait for the request to finish, then try again."
        )
        return False

    session_state["operating_mode"] = selected_mode
    session_state["mode_selector"] = selected_mode
    session_state["mode_selector_main"] = selected_mode
    session_state.pop("_flashreserve_read_cache", None)
    session_state.pop("_flashreserve_raft_status_cache", None)
    session_state.pop("raft_leader_url", None)
    session_state.pop("raft_last_observed_leader", None)
    has_booking_workflow = any(
        session_state.get(key)
        for key in ("reservation_id", "booking", "payment_idempotency_key", "selected_seats")
    )
    session_state["events"] = []
    session_state["bookings"] = []
    session_state["selected_event"] = None
    session_state["selected_seats"] = []
    session_state["reservation_id"] = None
    session_state["lock_expires_at"] = None
    session_state["booking"] = None
    session_state["payment_idempotency_key"] = None
    session_state["payment_attempt_signature"] = None
    session_state["payment_status"] = "idle"
    session_state["selected_booking_id"] = None
    session_state["booking_submit_in_progress"] = False
    session_state["booking_submit_mode"] = None
    if session_state.get("current_page") in {
        "event_details", "seats", "checkout", "payment", "confirmation", "booking_details",
    }:
        session_state["current_page"] = "bookings" if session_state.get("logged_in") else "home"
    if has_booking_workflow:
        session_state["mode_switch_notice"] = (
            "Mode changed. The previous mode's seat hold/checkout was cleared to avoid "
            "submitting that booking in a different database. Select seats again."
        )
    return True


def raft_cluster_availability(statuses, now_ms, freshness_ms=3000):
    reachable = [status for status in statuses if status.get("available")]
    expected_members = {node_id for node_id, _ in RAFT_NODES}
    highest_term = max(
        (status.get("currentTerm", -1) for status in reachable),
        default=-1,
    )
    leaders = [
        status for status in reachable
        if status.get("role") == "leader"
        and status.get("currentTerm", -1) == highest_term
    ]
    leader = max(leaders, key=lambda status: status.get("currentTerm", 0), default=None)
    if leader and sum(
        status.get("currentTerm") == leader.get("currentTerm") for status in leaders
    ) > 1:
        return False, "Conflicting Raft leaders were reported in the same term.", None

    config_status = leader or max(
        reachable,
        key=lambda status: (status.get("configuration") or {}).get("index", -1),
        default={},
    )
    configuration = config_status.get("configuration")
    old_members = configuration.get("oldMembers") if isinstance(configuration, dict) else None
    new_members = configuration.get("newMembers") if isinstance(configuration, dict) else None
    if len(expected_members) == 7:
        expected = set(expected_members)
        expected_topology = config_status.get("topologyId")
        expected_cluster_id = config_status.get("clusterId")
        expected_config_version = config_status.get("clusterConfigVersion")
        for status in reachable:
            reported_members = status.get("configuredMembers")
            if (
                not expected_topology
                or not expected_cluster_id
                or status.get("clusterId") != expected_cluster_id
                or status.get("clusterConfigVersion") != expected_config_version
                or status.get("topologyId") != expected_topology
                or not isinstance(reported_members, list)
                or set(reported_members) != expected
            ):
                return (
                    False,
                    "Seven-node topology is not consistently reported by every reachable Raft process.",
                    leader,
                )
        if not isinstance(old_members, list) or not old_members:
            return (
                False,
                "Raft Mode is temporarily unavailable while cluster configuration is being finalized.",
                leader,
            )
        old_set = set(old_members)
        new_set = set(new_members or [])
        if new_members or old_set != expected:
            return (
                False,
                "Raft Mode is temporarily unavailable while cluster configuration is being finalized.",
                leader,
            )
        for status in reachable:
            reported = status.get("configuration")
            if (
                not isinstance(reported, dict)
                or set(reported.get("oldMembers") or []) != expected
                or reported.get("newMembers")
                or not isinstance(reported.get("index"), int)
                or reported.get("index", 0) > status.get("commitIndex", -1)
                or reported.get("index", 0) > status.get("lastApplied", -1)
            ):
                return (
                    False,
                    "Raft Mode is temporarily unavailable while cluster configuration is being finalized.",
                    leader,
                )
    elif not isinstance(old_members, list) or not old_members:
        return False, "The active Raft voter configuration could not be verified.", leader

    healthy_ids = {
        status.get("nodeId", status.get("node_id"))
        for status in reachable
        if (status.get("database") or {}).get("connected") is True
        and status.get("healthy") is True
        and status.get("applicationStatus") != "failed"
    }
    if isinstance(old_members, list) and old_members:
        old_count = len(set(old_members) & healthy_ids)
        old_majority = len(old_members) // 2 + 1
        new_count = len(set(new_members or []) & healthy_ids)
        new_majority = len(new_members) // 2 + 1 if new_members else None
        quorum_available = old_count >= old_majority and (
            new_majority is None or new_count >= new_majority
        )
        quorum_description = (
            f"old {old_count}/{old_majority}"
            + (f", new {new_count}/{new_majority}" if new_majority is not None else "")
        )
    else:
        fallback_majority = len(statuses) // 2 + 1
        quorum_available = len(reachable) >= fallback_majority
        quorum_description = f"{len(reachable)}/{fallback_majority}"

    if not quorum_available:
        return False, f"Raft voting quorum unavailable ({quorum_description}).", leader
    if leader is None:
        return False, (
            f"A healthy Raft quorum is available ({quorum_description}), "
            "but leader election is still in progress."
        ), None
    if leader.get("leaderId") != leader.get("nodeId", leader.get("node_id")):
        return False, "The reported leader does not identify itself as leader.", None
    if leader.get("healthy") is not True or leader.get("applicationStatus") == "failed":
        return False, "The Raft leader has a state-machine application failure.", leader
    if leader.get("database", {}).get("connected") is not True:
        return False, "The leader's MongoDB connection is not confirmed.", leader

    last_quorum_at = leader.get("lastQuorumAt")
    if not isinstance(last_quorum_at, (int, float)) or now_ms - last_quorum_at > freshness_ms:
        return False, "A Raft leader is visible, but recent majority confirmation is unavailable.", leader
    if last_quorum_at > now_ms:
        return False, "Raft quorum status is invalid or from the future.", leader
    required_votes = max(
        len(old_members) // 2 + 1,
        len(new_members) // 2 + 1 if new_members else 0,
    )
    if leader.get("lastQuorumAcknowledgements", 0) < required_votes:
        return False, "The leader has not reported enough recent acknowledgements for the active quorum.", leader
    acknowledgements = leader.get("lastQuorumAcknowledgementsByConfiguration")
    if not isinstance(acknowledgements, dict):
        return False, "The leader has not reported acknowledgements for the active voter configuration.", leader
    if acknowledgements.get("oldMembers", 0) < len(old_members) // 2 + 1:
        return False, "The leader has not confirmed the old voter majority.", leader
    if new_members and acknowledgements.get("newMembers", 0) < len(new_members) // 2 + 1:
        return False, "The leader has not confirmed the new voter majority.", leader
    return True, "Leader and majority confirmed.", leader
