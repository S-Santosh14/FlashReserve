"""A deliberately small state layer; replace local writes with gRPC calls later."""

import copy
import streamlit as st

from frontend.data.dummy_data import INITIAL_BOOKINGS


DEFAULTS = {
    "logged_in": False,
    "username": "",
    "current_page": "home",
    "selected_event": "techfest",
    "selected_seats": [],
    "booking": None,
    "selected_booking_id": "FR-2847391",
    "payment_status": "idle",
    "bookings": copy.deepcopy(INITIAL_BOOKINGS),
    "support_messages": [],
    "event_category": "All",
}


def initialize_session():
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = copy.deepcopy(value)


def go(page: str, **values):
    for key, value in values.items():
        st.session_state[key] = value
    st.session_state.current_page = page
    st.rerun()


def currency(value: int) -> str:
    return f"₹{value:,}"


def event_for_booking(booking):
    from frontend.data.dummy_data import get_event
    return get_event(booking["event_id"])
