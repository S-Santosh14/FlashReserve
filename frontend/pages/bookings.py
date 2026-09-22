import streamlit as st

from frontend.components.booking_card import render_booking_card
from frontend.utils.api import APIError, get_bookings
from frontend.utils.navigation import breadcrumb, page_header


def render():
    try:
        st.session_state.bookings = get_bookings(st.session_state.auth_token)
    except APIError as error:
        st.error(error.message)
        return
    page_header("YOUR PLANS", "My bookings", "Everything you have reserved, in one place.", "← Home", "home", "🏠 Home", "home")
    breadcrumb(["Home", "My Bookings"])
    tabs = st.tabs(["Upcoming", "Past", "Cancelled"])
    groups = [
        [item for item in st.session_state.bookings if item["status"] == "Confirmed"],
        [item for item in st.session_state.bookings if item["status"] == "Completed"],
        [item for item in st.session_state.bookings if item["status"] == "Cancelled"],
    ]
    labels = ["upcoming reservations", "past experiences", "cancelled reservations"]
    for tab, bookings, label in zip(tabs, groups, labels):
        with tab:
            if not bookings:
                st.markdown(f"<div class='empty-state'>No {label} yet.</div>", unsafe_allow_html=True)
            for booking in bookings:
                st.markdown("<div class='booking-card'>", unsafe_allow_html=True)
                render_booking_card(booking)
                st.markdown("</div>", unsafe_allow_html=True)
