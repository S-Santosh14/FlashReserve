import streamlit as st

from frontend.utils.api import APIError, get_bookings
from frontend.utils.navigation import breadcrumb, page_header
from frontend.utils.session import go


def render():
    try:
        bookings = get_bookings(st.session_state.auth_token)
        st.session_state.bookings = bookings
    except APIError as error:
        st.error(error.message)
        return
    upcoming = sum(item["status"] == "Confirmed" for item in bookings)
    complete = sum(item["status"] == "Completed" for item in bookings)
    user = st.session_state.user or {}
    display_name = user.get("name", st.session_state.username or "FlashReserve customer")
    email = user.get("email", "")
    initials = "".join(part[0] for part in display_name.split()[:2]).upper() or "FR"
    page_header("YOUR ACCOUNT", "Profile", "Personal details and booking activity.", "← Home", "home", "🏠 Home", "home")
    breadcrumb(["Home", "Profile"])
    profile, activity = st.columns([1, 1.1], gap="large")
    with profile:
        st.markdown(f"<div class='profile-card'><div class='avatar'>{initials}</div><h2>{display_name}</h2><p>{email}</p><div class='detail-rule'></div><span class='profile-label'>SIGNED IN AS</span><b>{display_name}</b></div>", unsafe_allow_html=True)
    with activity:
        st.markdown(f"<div class='activity-card'><div class='section-kicker'>BOOKING ACTIVITY</div><div class='activity-grid'><div><b>{len(bookings)}</b><span>Total bookings</span></div><div><b>{upcoming}</b><span>Upcoming</span></div><div><b>{complete}</b><span>Completed</span></div></div></div>", unsafe_allow_html=True)
    st.markdown("<div class='tiny-gap'></div>", unsafe_allow_html=True)
    action, _ = st.columns([1.2, 3.8])
    with action:
        if st.button("Logout", key="profile_logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.auth_token = ""
            st.session_state.user = None
            st.session_state.username = ""
            st.session_state.role = ""
            st.session_state.current_page = "home"
            st.rerun()
