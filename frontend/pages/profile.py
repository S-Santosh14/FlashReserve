import streamlit as st

from frontend.utils.session import go


def render():
    upcoming = sum(item["status"] == "Confirmed" for item in st.session_state.bookings)
    complete = sum(item["status"] == "Completed" for item in st.session_state.bookings)
    st.markdown("<div class='page-intro compact'><span class='eyebrow'>YOUR ACCOUNT</span><h1>Profile</h1><p>Personal details and booking activity.</p></div>", unsafe_allow_html=True)
    profile, activity = st.columns([1, 1.1], gap="large")
    with profile:
        st.markdown("<div class='profile-card'><div class='avatar'>SS</div><h2>Santosh Siddamsetti</h2><p>santosh@example.com</p><div class='detail-rule'></div><span class='profile-label'>SIGNED IN AS</span><b>" + (st.session_state.username or "santosh") + "</b></div>", unsafe_allow_html=True)
    with activity:
        st.markdown(f"<div class='activity-card'><div class='section-kicker'>BOOKING ACTIVITY</div><div class='activity-grid'><div><b>{len(st.session_state.bookings)}</b><span>Total bookings</span></div><div><b>{upcoming}</b><span>Upcoming</span></div><div><b>{complete}</b><span>Completed</span></div></div></div>", unsafe_allow_html=True)
    st.markdown("<div class='tiny-gap'></div>", unsafe_allow_html=True)
    action, _ = st.columns([1.2, 3.8])
    with action:
        if st.button("Logout", key="profile_logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.current_page = "home"
            st.rerun()
