import streamlit as st

from frontend.utils.session import go


NAV_ITEMS = [
    ("Explore", "home", ":material/explore:"),
    ("Events", "events", ":material/local_activity:"),
    ("My bookings", "bookings", ":material/confirmation_number:"),
    ("Support", "support", ":material/support_agent:"),
    ("Profile", "profile", ":material/person:"),
]


def render_navbar(active_page: str):
    with st.container(horizontal=True, wrap=True, vertical_alignment="center", key="main-navigation"):
        st.markdown(
            "<div class='brand'><span class='brand-mark'></span>FLASHRESERVE</div>",
            unsafe_allow_html=True,
        )
        for label, page, icon in NAV_ITEMS:
            if st.button(
                label,
                key=f"nav_{page}",
                icon=icon,
                type="primary" if active_page == page else "secondary",
            ):
                go(page)
