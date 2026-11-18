import streamlit as st

from frontend.utils.session import go, logout


ADMIN_ITEMS = [
    ("Dashboard", "admin_dashboard", ":material/dashboard:"),
    ("Manage events", "admin_events", ":material/event:"),
    ("Manage seats", "admin_seats", ":material/event_seat:"),
    ("Manage bookings", "admin_bookings", ":material/confirmation_number:"),
    ("Manage users", "admin_users", ":material/group:"),
]


def render_admin_nav(active_page):
    with st.container(horizontal=True, wrap=True, vertical_alignment="center", key="admin-header"):
        st.markdown(
            "<div class='brand admin-brand'><span class='brand-mark'></span>FLASHRESERVE "
            "<small>ADMIN</small></div>",
            unsafe_allow_html=True,
        )
        if st.button("Log out", key="admin_top_logout", icon=":material/logout:"):
            logout()
    st.markdown("<div class='admin-rule'></div>", unsafe_allow_html=True)
    st.sidebar.markdown("## FlashReserve")
    st.sidebar.caption("Admin workspace")
    for label, page, icon in ADMIN_ITEMS:
        if st.sidebar.button(
            label,
            key=f"admin_nav_{page}",
            icon=icon,
            width="stretch",
            type="primary" if page == active_page else "secondary",
        ):
            go(page)
