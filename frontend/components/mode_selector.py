import streamlit as st

from frontend.utils.api import get_mode_availability
from frontend.utils.operating_mode import (
    NORMAL_MODE,
    RAFT_MODE,
    switch_mode,
)


def _select_mode(mode):
    switch_mode(st.session_state, mode)


def render_mode_selector():
    st.session_state.setdefault("operating_mode", NORMAL_MODE)
    st.session_state.setdefault("mode_selector_main", st.session_state.operating_mode)

    if st.session_state.get("logged_in"):
        return

    _render_login_mode_selector()


def _render_login_mode_selector():
    availability = get_mode_availability()
    st.session_state.mode_availability = availability
    normal = availability[NORMAL_MODE]
    raft = availability[RAFT_MODE]
    selected_mode = st.session_state.operating_mode
    raft_available = raft.get("available") is True

    with st.container(border=True, key="mode-selector"):
        st.markdown("#### Choose operating mode")
        status_column, refresh_column = st.columns(
            [3, 1],
            vertical_alignment="center",
        )
        if normal.get("available") is True:
            status_column.markdown(
                """
                <div class="backend-status backend-online">
                    <span class="status-indicator"></span>
                    <span>Backend connected</span>
                    <span class="status-detail">All systems operational</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            status_column.markdown(
                f"""
                <div class="backend-status backend-offline">
                    <span class="status-indicator"></span>
                    <span>Backend unavailable</span>
                    <span class="status-detail">Check server connection</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        refresh_column.button(
            "Refresh status",
            key="refresh_backend_status",
            icon=":material/refresh:",
            width="stretch",
        )
        normal_column, raft_column = st.columns(2)
        with normal_column:
            st.button(
                NORMAL_MODE,
                key="select_normal_mode",
                type="primary" if selected_mode == NORMAL_MODE else "secondary",
                width="stretch",
                on_click=_select_mode,
                args=(NORMAL_MODE,),
            )
        with raft_column:
            st.button(
                RAFT_MODE,
                key="select_raft_mode",
                type="primary" if selected_mode == RAFT_MODE else "secondary",
                width="stretch",
                disabled=not raft_available,
                on_click=_select_mode,
                args=(RAFT_MODE,),
            )

        if not raft_available:
            st.caption(
                raft.get(
                    "unavailable_message",
                    "Raft Mode is temporarily unavailable because the cluster has no valid leader or quorum.",
                )
            )
