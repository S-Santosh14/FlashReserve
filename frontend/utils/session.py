"""Streamlit session state for the REST-backed frontend."""

import copy
from datetime import datetime, timezone
import streamlit as st


DEFAULTS = {
    "logged_in": False,
    "username": "",
    "user": None,
    "role": "",
    "auth_token": "",
    "current_page": "home",
    "selected_event": None,
    "selected_seats": [],
    "reservation_id": None,
    "lock_expires_at": None,
    "booking": None,
    "payment_idempotency_key": None,
    "payment_attempt_signature": None,
    "selected_booking_id": None,
    "payment_status": "idle",
    "bookings": [],
    "events": [],
    "support_messages": [],
    "support_pending": None,
    "support_owner": None,
    "support_focus_input": False,
    "support_scroll_latest": False,
    "event_category": "All",
    "operating_mode": "Normal Mode",
    "mode_selector_main": "Normal Mode",
    "mode_switch_notice": None,
    "mode_availability": None,
    "raft_status_last_successful_at": None,
    "booking_submit_in_progress": False,
    "booking_submit_mode": None,
}


def initialize_session():
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = copy.deepcopy(value)
    if st.session_state.logged_in and not st.session_state.auth_token:
        reset_session_state()


def reset_session_state():
    st.session_state.clear()
    for key, value in DEFAULTS.items():
        st.session_state[key] = copy.deepcopy(value)


def logout():
    reset_session_state()
    st.rerun()


def go(page: str, **values):
    for key, value in values.items():
        st.session_state[key] = value
    st.session_state.current_page = page
    st.rerun()


def currency(value) -> str:
    return f"₹{int(value or 0):,}"


def event_for_booking(booking):
    if booking.get("event"):
        return booking["event"]
    return next((event for event in st.session_state.events if event["id"] == booking.get("event_id")), None)


@st.fragment(run_every="1s")
def render_reservation_countdown(expires_at):
    if not expires_at:
        st.warning("Seat-hold expiry is unavailable. Return to the seat map and reserve again.")
        return
    try:
        expiry = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
    except ValueError:
        st.error("The reservation expiry returned by the backend is invalid.")
        return
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    remaining = max(0, int((expiry - datetime.now(timezone.utc)).total_seconds()))
    if remaining:
        st.warning(f"Your seat hold expires in {remaining // 60:02d}:{remaining % 60:02d}.")
    else:
        st.error("Your seat hold has expired. Choose the seats again to continue.")
