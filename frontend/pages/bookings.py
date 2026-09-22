import streamlit as st

from frontend.components.booking_card import render_booking_card


def render():
    st.markdown("<div class='page-intro compact'><span class='eyebrow'>YOUR PLANS</span><h1>My bookings</h1><p>Everything you have reserved, in one place.</p></div>", unsafe_allow_html=True)
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
