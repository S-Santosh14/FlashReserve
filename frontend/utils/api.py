"""REST client for the FlashReserve Python backend."""

from datetime import datetime
import copy
import os
import re
import time

import requests
import streamlit as st

from frontend.utils.booking_time import format_booking_timestamp
from frontend.utils.operating_mode import (
    MODE_OPTIONS,
    NORMAL_MODE,
    RAFT_MODE,
    RAFT_NODES,
    api_base_url,
    raft_cluster_availability,
)

BASE_URL = api_base_url(NORMAL_MODE)
_READ_CACHE_KEY = "_flashreserve_read_cache"
_RAFT_STATUS_CACHE_KEY = "_flashreserve_raft_status_cache"
_PERFORMANCE_KEY = "_flashreserve_api_performance"
_RAFT_STATUS_TTL_SECONDS = 1.0
_EVENT_CACHE_TTL_SECONDS = 30.0
_SEAT_CACHE_TTL_SECONDS = 2.0


def get_api_base_url():
    return api_base_url(st.session_state.get("operating_mode", NORMAL_MODE))


class APIError(Exception):
    """User-facing error returned by the backend or caused by an unavailable backend."""

    def __init__(self, message, status_code=None, code=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


def _session_read_cache():
    cache = st.session_state.get(_READ_CACHE_KEY)
    if not isinstance(cache, dict):
        cache = {}
        st.session_state[_READ_CACHE_KEY] = cache
    return cache


def _cached_read(namespace, identity, ttl, loader):
    cache_key = (
        namespace,
        st.session_state.get("operating_mode", NORMAL_MODE),
        get_api_base_url(),
        str((st.session_state.get("user") or {}).get("id") or ""),
        str(identity),
    )
    now = time.monotonic()
    cached = _session_read_cache().get(cache_key)
    if cached and now - cached[0] < ttl:
        return copy.deepcopy(cached[1])
    value = loader()
    _session_read_cache()[cache_key] = (now, copy.deepcopy(value))
    return value


def clear_read_cache(namespace=None, identity=None):
    cache = st.session_state.get(_READ_CACHE_KEY)
    if not isinstance(cache, dict):
        return
    if namespace is None:
        cache.clear()
        return
    for key in list(cache):
        if key[0] == namespace and (identity is None or key[-1] == str(identity)):
            del cache[key]


def _invalidate_raft_status_cache():
    st.session_state.pop(_RAFT_STATUS_CACHE_KEY, None)


def _record_performance(operation, duration_ms, outcome):
    samples = st.session_state.get(_PERFORMANCE_KEY)
    if not isinstance(samples, list):
        samples = []
    samples.append({
        "operation": operation,
        "mode": st.session_state.get("operating_mode", NORMAL_MODE),
        "duration_ms": round(duration_ms, 2),
        "outcome": outcome,
        "recorded_at": time.time(),
    })
    st.session_state[_PERFORMANCE_KEY] = samples[-100:]


def get_api_performance_samples(limit=20):
    """Return recent per-session API and Raft discovery timings."""
    samples = st.session_state.get(_PERFORMANCE_KEY, [])
    limit = max(0, int(limit))
    return copy.deepcopy(samples[-limit:]) if limit else []


def _request_candidates(statuses):
    available, _reason, _leader = raft_cluster_availability(
        statuses,
        now_ms=time.time() * 1000,
    )
    return [api_base_url(RAFT_MODE)] if available else []


def _raft_request_path(path):
    if path.startswith("/api/auth/") or path.startswith("/api/raft/"):
        return path
    if path.startswith("/api/"):
        return f"/api/raft/{path[len('/api/'):]}"
    return path


def _retry_safe_raft_request(method, path, payload):
    method = method.upper()
    if method in {"GET", "HEAD", "OPTIONS"}:
        return True
    if method == "POST" and path == "/api/auth/login":
        return True
    if method == "POST" and path == "/api/bookings":
        return isinstance(payload, dict) and bool(payload.get("reservationId"))
    if method == "POST" and re.fullmatch(r"/api/events/[^/]+/seats/reserve", path):
        return isinstance(payload, dict) and bool(payload.get("reservationId"))
    if method == "POST" and path == "/api/payments/mock":
        return isinstance(payload, dict) and bool(payload.get("idempotencyKey"))
    return method == "PUT" and bool(re.fullmatch(r"/api/bookings/[^/]+/cancel", path))


def _perform_raft_request(method, path, token, payload, files, timeout, retry_safe):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request_kwargs = {"headers": headers}
    if files:
        request_kwargs["files"] = files
        request_kwargs["data"] = payload or {}
    else:
        request_kwargs["json"] = payload

    max_attempts = 2 if retry_safe else 1
    request_timeout = max(timeout, 35.0) if method in {"POST", "PUT", "DELETE"} else timeout
    deadline = time.monotonic() + (max(1.0, request_timeout) * max_attempts) + 1.0
    request_url = get_api_base_url()
    request_path = _raft_request_path(path)
    last_error = None
    for attempt in range(max_attempts):
        try:
            response = requests.request(
                method,
                f"{request_url}{request_path}",
                timeout=max(0.1, min(request_timeout, deadline - time.monotonic())),
                **request_kwargs,
            )
        except requests.RequestException as error:
            _invalidate_raft_status_cache()
            st.session_state.pop("raft_leader_url", None)
            last_error = APIError(
                "The Raft cluster could not be reached. "
                "No standalone fallback was attempted.",
                None,
            )
            if not retry_safe:
                raise last_error from error
        else:
            try:
                body = response.json()
            except ValueError as error:
                raise APIError(
                    "The backend returned an invalid response.",
                    response.status_code,
                ) from error
            if not isinstance(body, dict):
                raise APIError("The backend returned an invalid response.", response.status_code)
            if response.ok and body.get("success") is not False:
                return body.get("data", body)

            code = body.get("code")
            message = body.get("message", "The request could not be completed.")
            if code == "RAFT_NO_QUORUM":
                message = "Raft cannot accept this write because a voting majority is unavailable."
            elif code in {"RAFT_NOT_LEADER", "RAFT_LEADER_UNAVAILABLE"}:
                message = "The Raft leader is changing or unavailable. Please retry."
            elif code == "RAFT_APPLY_FAILED":
                message = "Raft committed the request but could not apply it to the leader database."
            last_error = APIError(message, response.status_code, code)
            if response.status_code not in (502, 503, 504):
                raise last_error
            _invalidate_raft_status_cache()
            st.session_state.pop("raft_leader_url", None)
        if not retry_safe or attempt + 1 >= max_attempts:
            raise last_error
        remaining = deadline - time.monotonic()
        if remaining <= 0.1:
            raise last_error
        statuses = get_raft_cluster_status(
            timeout=min(0.8, remaining),
            force_refresh=True,
        )
        candidates = _request_candidates(statuses)
        if candidates:
            request_url = candidates[0]
            st.session_state["raft_leader_url"] = request_url
        else:
            st.session_state.pop("raft_leader_url", None)
            raise APIError(
                "The Raft cluster has no reachable elected leader. "
                "No standalone fallback was attempted.",
                last_error.status_code,
                last_error.code,
            ) from last_error
        time.sleep(0.1)

    if last_error:
        raise last_error
    raise APIError("The Raft cluster is unavailable. No standalone fallback was attempted.")


def _request_impl(method, path, token=None, payload=None, files=None, timeout=10):
    if st.session_state.get("operating_mode", NORMAL_MODE) == RAFT_MODE:
        return _perform_raft_request(
            method,
            path,
            token,
            payload,
            files,
            timeout,
            _retry_safe_raft_request(method, path, payload),
        )

    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        request_kwargs = {"headers": headers, "timeout": timeout}
        if files:
            request_kwargs["files"] = files
            request_kwargs["data"] = payload or {}
        else:
            request_kwargs["json"] = payload
        response = requests.request(method, f"{get_api_base_url()}{path}", **request_kwargs)
    except requests.RequestException as error:
        if st.session_state.get("operating_mode", NORMAL_MODE) == RAFT_MODE:
            raise APIError("The Raft cluster is unavailable. No standalone fallback was attempted.") from error
        raise APIError("FlashReserve backend is unavailable. Please try again.") from error

    try:
        body = response.json()
    except ValueError as error:
        raise APIError("The backend returned an invalid response.", response.status_code) from error

    if not response.ok or body.get("success") is False:
        raise APIError(body.get("message", "The request could not be completed."), response.status_code)
    return body.get("data", body)


def _request(method, path, token=None, payload=None, files=None, timeout=10):
    started_at = time.perf_counter()
    outcome = "error"
    try:
        result = _request_impl(method, path, token, payload, files, timeout)
        outcome = "success"
        return result
    finally:
        _record_performance(
            f"{method.upper()} {path}",
            (time.perf_counter() - started_at) * 1000,
            outcome,
        )


def _display_date(value, short=False):
    if not value:
        return "Date to be announced"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.strftime("%d %b" if short else "%d %B %Y")
    except ValueError:
        return str(value)


def _normalize_event(raw):
    event = dict(raw)
    event["id"] = str(raw.get("id") or raw.get("_id"))
    event["raw_date"] = str(raw.get("date", ""))[:10]
    event["date"] = _display_date(raw.get("date"))
    event["short_date"] = _display_date(raw.get("date"), short=True)
    event["city"] = raw.get("city") or raw.get("venue", "")
    event["eyebrow"] = raw.get("eyebrow") or str(raw.get("category", "EVENT")).upper()
    event["price"] = int(raw.get("price") or 0)
    event["seatsPerRow"] = int(raw.get("seatsPerRow") or 10)
    event["status"] = raw.get("status") or "active"
    event["image"] = raw.get("image")
    event["poster_url"] = raw.get("posterUrl", "")
    if event["poster_url"] and event["poster_url"].startswith("/"):
        event["poster_url"] = f"{get_api_base_url()}{event['poster_url']}"
    event["image"] = event["poster_url"] or event["image"]
    return event


def _normalize_booking(raw):
    event_raw = raw.get("eventId") if isinstance(raw.get("eventId"), dict) else raw.get("event")
    event = _normalize_event(event_raw) if event_raw else None
    seats = raw.get("seats", [])
    seat_numbers = [seat.get("seatNumber", "") if isinstance(seat, dict) else str(seat) for seat in seats]
    booking = dict(raw)
    booking["id"] = str(raw.get("id") or raw.get("_id"))
    booking["event_id"] = event["id"] if event else str(raw.get("eventId", ""))
    booking["event"] = event
    booking["seats"] = seat_numbers
    booking["amount"] = raw.get("totalAmount", raw.get("amount", 0))
    booking["status"] = str(raw.get("status", "pending")).capitalize()
    booking["booked_on"] = format_booking_timestamp(raw.get("createdAt"))
    booking["reference"] = raw.get("bookingReference") or booking["id"]
    booking["expires_at"] = raw.get("expiresAt")
    booking["payment"] = raw.get("paymentId") if isinstance(raw.get("paymentId"), dict) else None
    booking["refund"] = raw.get("refundId") if isinstance(raw.get("refundId"), dict) else None
    return booking


def register_user(name, email, password):
    return _request("POST", "/api/auth/register", payload={"name": name, "email": email, "password": password})


def login_user(email, password):
    return _request("POST", "/api/auth/login", payload={"email": email, "password": password})


def get_events():
    return _cached_read(
        "events",
        "all",
        _EVENT_CACHE_TTL_SECONDS,
        lambda: [_normalize_event(event) for event in _request("GET", "/api/events")],
    )


def get_admin_events(token):
    return [
        _normalize_event(event)
        for event in _request("GET", "/api/admin/events", token=token)
    ]


def get_event(event_id):
    return _cached_read(
        "event",
        event_id,
        _EVENT_CACHE_TTL_SECONDS,
        lambda: _normalize_event(_request("GET", f"/api/events/{event_id}")),
    )


def get_seats(event_id, token):
    return _cached_read(
        "seats",
        event_id,
        _SEAT_CACHE_TTL_SECONDS,
        lambda: _request("GET", f"/api/events/{event_id}/seats", token=token),
    )


def reserve_seats(event_id, seat_numbers, token, reservation_id):
    try:
        return _request(
            "POST",
            f"/api/events/{event_id}/seats/reserve",
            token=token,
            payload={"seatNumbers": seat_numbers, "reservationId": reservation_id},
        )
    finally:
        clear_read_cache("seats", event_id)


def create_booking(event_id, seat_numbers, total_amount, token, reservation_id):
    try:
        booking = _request(
            "POST",
            "/api/bookings",
            token=token,
            payload={"eventId": event_id, "seatNumbers": seat_numbers, "totalAmount": total_amount, "reservationId": reservation_id},
        )
        return _normalize_booking(booking)
    finally:
        clear_read_cache("seats", event_id)
        clear_read_cache("bookings")


def get_bookings(token):
    return [_normalize_booking(booking) for booking in _request("GET", "/api/bookings", token=token)]


def cancel_booking(booking_id, token):
    try:
        return _normalize_booking(_request("PUT", f"/api/bookings/{booking_id}/cancel", token=token))
    finally:
        clear_read_cache("seats")
        clear_read_cache("bookings")


def make_mock_payment(booking_id, amount, token, method, outcome, idempotency_key):
    try:
        result = _request(
            "POST",
            "/api/payments/mock",
            token=token,
            payload={
                "bookingId": booking_id,
                "amount": amount,
                "method": method,
                "outcome": outcome,
                "idempotencyKey": idempotency_key,
            },
        )
        if isinstance(result.get("booking"), dict):
            result["booking"] = _normalize_booking(result["booking"])
        return result
    finally:
        clear_read_cache("seats")
        clear_read_cache("bookings")


def ask_chat(message, token, event_id=None, history=None):
    result = _request(
        "POST",
        "/api/chat",
        token=token,
        payload={
            "message": message,
            "history": history or [],
            **({"eventId": event_id} if event_id else {}),
        },
        timeout=35,
    )
    if (
        isinstance(result, dict)
        and "response" not in result
        and isinstance(result.get("answer"), str)
    ):
        return {**result, "response": result["answer"]}
    return result


def get_admin_stats(token):
    return _request("GET", "/api/admin/stats", token=token)


def get_admin_users(token):
    return _request("GET", "/api/admin/users", token=token)


def get_admin_bookings(token):
    bookings = _request("GET", "/api/admin/bookings", token=token)
    for booking in bookings:
        event = booking.get("eventId")
        if isinstance(event, dict):
            booking["eventId"] = _normalize_event(event)
    return bookings


def get_event_seats(event_id, token):
    return _request("GET", f"/api/admin/events/{event_id}/seats", token=token)


def update_admin_seat(seat_id, status, token):
    try:
        return _request("PUT", f"/api/admin/seats/{seat_id}", token=token, payload={"status": status})
    finally:
        clear_read_cache("seats")


def create_event(event, token, poster=None):
    try:
        if poster:
            files = {"poster": (poster.name, poster.getvalue(), poster.type or "application/octet-stream")}
            return _normalize_event(_request("POST", "/api/admin/events", token=token, payload=event, files=files))
        return _normalize_event(_request("POST", "/api/admin/events", token=token, payload=event))
    finally:
        clear_read_cache()


def update_event(event_id, event, token, poster=None):
    try:
        if poster:
            files = {"poster": (poster.name, poster.getvalue(), poster.type or "application/octet-stream")}
            return _normalize_event(_request("PUT", f"/api/admin/events/{event_id}", token=token, payload=event, files=files))
        return _normalize_event(_request("PUT", f"/api/admin/events/{event_id}", token=token, payload=event))
    finally:
        clear_read_cache()


def delete_event(event_id, token):
    try:
        return _request("DELETE", f"/api/admin/events/{event_id}", token=token)
    finally:
        clear_read_cache()


def get_raft_cluster_status(timeout=1.5, force_refresh=False):
    """Return actual gRPC-reported member status through the REST gateway."""
    now = time.monotonic()
    cached = st.session_state.get(_RAFT_STATUS_CACHE_KEY)
    if (
        not force_refresh
        and isinstance(cached, tuple)
        and now - cached[0] < _RAFT_STATUS_TTL_SECONDS
    ):
        return copy.deepcopy(cached[1])

    started_at = time.perf_counter()
    gateway_url = api_base_url(RAFT_MODE)
    try:
        response = requests.get(
            f"{gateway_url}/api/raft/status",
            timeout=timeout,
        )
        response.raise_for_status()
        body = response.json()
        data = body.get("data") if isinstance(body, dict) else None
        if (
            not isinstance(data, dict)
            or body.get("success") is not True
            or not isinstance(data.get("nodes"), list)
        ):
            raise ValueError("Invalid Raft status response")
        observed_at = time.time()
        statuses = []
        for item in data["nodes"]:
            if not isinstance(item, dict):
                raise ValueError("Invalid Raft node status")
            status = dict(item)
            status["node_id"] = status.get("nodeId")
            status["url"] = gateway_url
            status["observed_at"] = (
                status.get("observedAt", observed_at * 1000) / 1000
            )
            statuses.append(status)
    except (requests.RequestException, ValueError):
        observed_at = time.time()
        statuses = [
            {
                "nodeId": node_id,
                "node_id": node_id,
                "url": gateway_url,
                "available": False,
                "observed_at": observed_at,
                "database": {
                    "connected": False,
                    "name": os.environ.get(
                        f"RAFT_NODE_{node_id.rsplit('-', 1)[-1]}_DATABASE_NAME",
                        f"flashreserve_raft_node{node_id.rsplit('-', 1)[-1]}",
                    ),
                },
                "topologyMatches": False,
                "error": "Raft status gateway is unavailable.",
            }
            for node_id, _ in RAFT_NODES
        ]
    _record_performance(
        "Raft leader discovery",
        (time.perf_counter() - started_at) * 1000,
        "success" if any(status["available"] for status in statuses) else "unavailable",
    )
    st.session_state[_RAFT_STATUS_CACHE_KEY] = (time.monotonic(), copy.deepcopy(statuses))
    return statuses


def get_mode_availability(timeout=3.5):
    """Check standalone database health and Raft leader/majority evidence."""
    health_url = f"{api_base_url(NORMAL_MODE)}/api/health"
    normal = {
        "available": False,
        "reason": "Standalone backend is unavailable.",
        "unavailable_message": "Normal Mode is temporarily unavailable.",
    }
    try:
        response = requests.get(health_url, timeout=timeout)
        response.raise_for_status()
        body = response.json()
        data = body.get("data", body) if isinstance(body, dict) else None
        database = data.get("database") if isinstance(data, dict) else None
        if (
            isinstance(data, dict)
            and body.get("success") is True
            and data.get("status") == "ok"
            and data.get("raftEnabled") is not True
            and isinstance(database, dict)
            and database.get("connected") is True
        ):
            normal = {
                "available": True,
                "reason": f"Connected to standalone database ({database.get('name') or 'available'}).",
                "unavailable_message": None,
            }
        else:
            normal["reason"] = (
                "Standalone backend is Raft-enabled, uses an unexpected database, "
                "or MongoDB is not ready."
            )
    except requests.ConnectionError:
        normal["reason"] = f"Could not connect to backend at {health_url}."
    except requests.Timeout:
        normal["reason"] = f"Backend health check timed out at {health_url}."
    except requests.HTTPError as error:
        status_code = (
            error.response.status_code
            if error.response is not None
            else "unknown"
        )
        normal["reason"] = (
            f"Backend health endpoint returned HTTP {status_code}."
        )
    except requests.RequestException as error:
        normal["reason"] = (
            f"Backend health request failed ({type(error).__name__})."
        )
    except ValueError:
        normal["reason"] = "Standalone backend returned an invalid health response."

    raft_statuses = get_raft_cluster_status(timeout=timeout)
    raft_reachable = [status for status in raft_statuses if status.get("available")]
    highest_raft_term = max(
        (status.get("currentTerm", -1) for status in raft_reachable),
        default=-1,
    )
    leaders = [
        status for status in raft_reachable
        if status.get("role") == "leader"
        and status.get("currentTerm", -1) == highest_raft_term
    ]
    leader = max(leaders, key=lambda status: status.get("currentTerm", 0), default=None)
    freshness_ms = max(3000, 2 * leader.get("electionTimeoutMs", 0) if leader else 0)
    raft_available, raft_reason, leader = raft_cluster_availability(
        raft_statuses,
        now_ms=time.time() * 1000,
        freshness_ms=freshness_ms,
    )
    configuration_status = leader or max(
        raft_reachable,
        key=lambda status: (status.get("configuration") or {}).get("index", -1),
        default={},
    )
    configuration = configuration_status.get("configuration") or {}
    configured_members = {node_id for node_id, _ in RAFT_NODES}
    old_members = configuration.get("oldMembers")
    configuration_finalized = len(RAFT_NODES) != 7 or (
        isinstance(old_members, list)
        and set(old_members) == configured_members
        and not configuration.get("newMembers")
    )
    if leader and raft_available:
        unavailable = len(raft_statuses) - len(raft_reachable)
        if unavailable:
            unavailable_summary = (
                "One Raft node is unavailable"
                if unavailable == 1
                else f"{unavailable} Raft nodes are unavailable"
            )
            raft_reason = (
                f"{unavailable_summary}; leader {leader.get('nodeId')} confirms "
                "the configured voting quorum."
            )
        else:
            raft_reason = "All configured Raft nodes are available and the elected leader confirms its voting quorum."
    elif not raft_reachable:
        raft_reason = "Raft cluster unavailable: no configured nodes are reachable."
    raft = {
        "available": raft_available,
        "reason": raft_reason,
        "unavailable_message": (
            None
            if raft_available
            else (
                "Raft Mode is temporarily unavailable while cluster configuration is being finalized."
                if len(RAFT_NODES) == 7 and raft_reachable and not configuration_finalized
                else "Raft Mode is temporarily unavailable because the cluster has no valid leader or quorum."
            )
        ),
        "configuration_finalized": configuration_finalized,
        "leader": leader.get("nodeId") if leader else None,
        "term": leader.get("currentTerm") if leader else None,
        "cluster_size": len(RAFT_NODES),
        "majority_required": len(RAFT_NODES) // 2 + 1,
        "reachable_nodes": len(raft_reachable),
        "healthy_nodes": sum(
            (status.get("database") or {}).get("connected") is True
            for status in raft_reachable
        ),
        "leader_votes_received": leader.get("lastElectionVotesReceived") if leader else None,
        "leader_quorum_acknowledgements": leader.get("lastQuorumAcknowledgements") if leader else None,
        "valid_majority": raft_available,
        "cluster_status": (
            "Healthy" if raft_available
            else "No quorum" if "quorum unavailable" in raft_reason.lower()
            else "Recovering" if raft_reachable
            else "Unavailable"
        ),
        "nodes": raft_statuses,
    }
    return {
        NORMAL_MODE: normal,
        RAFT_MODE: raft,
        "available_modes": tuple(
            mode for mode in MODE_OPTIONS
            if (normal if mode == NORMAL_MODE else raft)["available"]
        ),
    }