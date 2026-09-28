import streamlit as st

from frontend.components.admin_nav import render_admin_nav
from frontend.utils.api import APIError, get_admin_users
from frontend.utils.navigation import breadcrumb, page_header


def render():
    render_admin_nav("admin_users")
    page_header("ACCOUNTS", "Manage Users", "Review customer and admin accounts without exposing credentials.", "← Dashboard", "admin_dashboard", "🏠 Dashboard", "admin_dashboard")
    breadcrumb(["Admin", "Manage Users"])
    try:
        users = get_admin_users(st.session_state.auth_token)
    except APIError as error:
        st.error(error.message)
        return
    rows = [
        {
            "Name": user.get("name", ""),
            "Email": user.get("email", ""),
            "Role": user.get("role", ""),
            "Created At": str(user.get("createdAt", ""))[:19],
        }
        for user in users
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)
