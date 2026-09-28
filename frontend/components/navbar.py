import streamlit as st

from frontend.utils.session import go


NAV_ITEMS = [("Explore", "home"), ("Events", "events"), ("My bookings", "bookings"), ("Support", "support")]


def render_navbar(active_page: str):
    st.markdown("<div class='nav-rule'></div>", unsafe_allow_html=True)
    brand, *nav, profile, theme_col = st.columns(
        [2.0, 0.78, 0.78, 1.08, 0.9, 0.92, 0.92], gap="small"
    )
    with brand:
        st.markdown("<div class='brand'><span class='brand-mark'></span>FLASHRESERVE</div>", unsafe_allow_html=True)
    for column, (label, page) in zip(nav, NAV_ITEMS):
        with column:
            if st.button(
                label,
                key=f"nav_{page}",
                type="primary" if active_page == page else "secondary",
                use_container_width=True,
            ):
                go(page)
    with profile:
        if st.button(
            "Profile",
            key="nav_profile",
            type="primary" if active_page == "profile" else "secondary",
            use_container_width=True,
        ):
            go("profile")
    with theme_col:
        is_dark = st.session_state.get("theme", "light") == "dark"
        if st.button(
            "☀ Light" if is_dark else "☾ Dark",
            key="theme_toggle",
            use_container_width=True,
            help="Switch between light and dark theme",
        ):
            st.session_state.theme = "light" if is_dark else "dark"
            st.rerun()
    st.markdown("<div class='nav-space'></div>", unsafe_allow_html=True)
