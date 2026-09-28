import streamlit as st

from frontend.components.admin_nav import render_admin_nav
from frontend.utils.api import APIError, get_admin_stats
from frontend.utils.session import go
from frontend.utils.navigation import breadcrumb


def render():
    render_admin_nav("admin_dashboard")
    breadcrumb(["Admin", "Dashboard"])
    st.markdown("<div class='page-intro'><span class='eyebrow'>OPERATIONS</span><h1>Admin Dashboard</h1><p>Live activity from FlashReserve.</p></div>", unsafe_allow_html=True)
    try:
        stats = get_admin_stats(st.session_state.auth_token)
    except APIError as error:
        st.error(error.message)
        return

    first, second, third = st.columns(3)
    first.metric("Total Events", stats.get("totalEvents", 0))
    second.metric("Total Users", stats.get("totalUsers", 0))
    third.metric("Total Bookings", stats.get("totalBookings", 0))
    first, second, third = st.columns(3)
    first.metric("Total Seats", stats.get("totalSeats", 0))
    second.metric("Available Seats", stats.get("availableSeats", 0))
    third.metric("Booked Seats", stats.get("bookedSeats", 0))

    st.markdown("### Quick actions")
    events_col, seats_col, bookings_col, users_col = st.columns(4)
    with events_col:
        if st.button("Manage Events", use_container_width=True):
            go("admin_events")
    with seats_col:
        if st.button("Manage Seats", use_container_width=True):
            go("admin_seats")
    with bookings_col:
        if st.button("Manage Bookings", use_container_width=True):
            go("admin_bookings")
    with users_col:
        if st.button("Manage Users", use_container_width=True):
            go("admin_users")
