import streamlit as st

from frontend.utils.session import go


ADMIN_ITEMS = [
    ("Dashboard", "admin_dashboard"),
    ("Manage Events", "admin_events"),
    ("Manage Seats", "admin_seats"),
    ("Manage Bookings", "admin_bookings"),
    ("Manage Users", "admin_users"),
]


def render_admin_nav(active_page):
    top = st.columns([2.3, 1, 1, 1, 1, 1, 1.2], gap="small")
    with top[0]:
        st.markdown("<div class='brand admin-brand'><span class='brand-mark'></span>FLASHRESERVE <small>ADMIN</small></div>", unsafe_allow_html=True)
    for column, (label, page) in zip(top[1:6], ADMIN_ITEMS):
        with column:
            if st.button(label, key=f"admin_top_{page}", use_container_width=True, type="primary" if page == active_page else "secondary"):
                go(page)
    with top[6]:
        if st.button("Logout", key="admin_top_logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.auth_token = ""
            st.session_state.user = None
            st.session_state.username = ""
            st.session_state.role = ""
            st.session_state.current_page = "home"
            st.rerun()
    st.markdown("<div class='admin-rule'></div>", unsafe_allow_html=True)
    st.sidebar.markdown("## FlashReserve Admin")
    st.sidebar.caption("Operations dashboard")
    for label, page in ADMIN_ITEMS:
        if st.sidebar.button(label, key=f"admin_nav_{page}", use_container_width=True, type="primary" if page == active_page else "secondary"):
            go(page)
    st.sidebar.divider()
    if st.sidebar.button("Logout", key="admin_logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.auth_token = ""
        st.session_state.user = None
        st.session_state.username = ""
        st.session_state.role = ""
        st.session_state.current_page = "home"
        st.rerun()
