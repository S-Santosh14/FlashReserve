"""Streamlit session state for the REST-backed frontend."""

import copy
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
    "booking": None,
    "selected_booking_id": None,
    "payment_status": "idle",
    "bookings": [],
    "events": [],
    "support_messages": [],
    "event_category": "All",
}


def initialize_session():
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = copy.deepcopy(value)
    if st.session_state.logged_in and not st.session_state.auth_token:
        st.session_state.logged_in = False


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
