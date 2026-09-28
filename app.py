import streamlit as st

from frontend.components.footer import render_footer
from frontend.components.navbar import render_navbar
from frontend.utils.api import APIError, login_user, register_user
from frontend.styles import inject_admin_styles, inject_theme_styles
from frontend.pages import (
    admin_bookings,
    admin_dashboard,
    admin_events,
    admin_seats,
    admin_users,
    booking_details,
    bookings,
    checkout,
    confirmation,
    event_details,
    events,
    home,
    payment,
    profile,
    seats,
    support,
)
from frontend.utils.session import go, initialize_session


st.set_page_config(page_title="FlashReserve", page_icon="FR", layout="wide", initial_sidebar_state="collapsed")


def login_screen():
    _, theme_col = st.columns([5.5, 1.0])
    with theme_col:
        is_dark = st.session_state.get("theme", "light") == "dark"
        if st.button("☀ Light" if is_dark else "☾ Dark", key="login_theme_toggle", use_container_width=True):
            st.session_state.theme = "light" if is_dark else "dark"
            st.rerun()
    _, center, _ = st.columns([1.1, 1.55, 1.1])
    with center:
        st.markdown("<div class='login-shell'><div class='login-brand'><span class='brand-mark'></span>FLASHRESERVE</div><h1 class='login-title'>Your next night out starts here.</h1><p class='login-copy'>Discover live events, choose your seats, and reserve the moment.</p></div>", unsafe_allow_html=True)
        sign_in, register = st.tabs(["SIGN IN", "CREATE ACCOUNT"])
        with sign_in:
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="you@example.com")
                password = st.text_input("Password", type="password", placeholder="")
                submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
            if submitted:
                if not email or not password:
                    st.error("Enter your email and password.")
                else:
                    try:
                        result = login_user(email, password)
                    except APIError as error:
                        st.error(error.message)
                    else:
                        user = result["user"]
                        st.session_state.logged_in = True
                        st.session_state.auth_token = result["token"]
                        st.session_state.user = user
                        st.session_state.username = user["name"]
                        st.session_state.role = user.get("role", "customer")
                        go("admin_dashboard" if st.session_state.role == "admin" else "home")
            st.markdown("<div class='login-hint'>Sign in with your FlashReserve account.</div>", unsafe_allow_html=True)
        with register:
            with st.form("register_form"):
                name = st.text_input("Your name", placeholder="Your name")
                email = st.text_input("Email", placeholder="you@example.com")
                new_password = st.text_input("Create password", type="password")
                confirm_password = st.text_input("Confirm password", type="password")
                registered = st.form_submit_button("Create account", type="primary", use_container_width=True)
            if registered:
                if not name or not email or not new_password or not confirm_password:
                    st.error("Please complete all fields.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    try:
                        result = register_user(name, email, new_password)
                    except APIError as error:
                        st.error(error.message)
                    else:
                        user = result["user"]
                        st.session_state.logged_in = True
                        st.session_state.auth_token = result["token"]
                        st.session_state.user = user
                        st.session_state.username = user["name"]
                        st.session_state.role = user.get("role", "customer")
                        go("home")


def app():
    initialize_session()
    inject_theme_styles()
    if not st.session_state.logged_in:
        login_screen()
        return
    if st.session_state.role == "admin":
        inject_admin_styles()
        admin_routes = {
            "admin_dashboard": admin_dashboard.render,
            "admin_events": admin_events.render,
            "admin_seats": admin_seats.render,
            "admin_bookings": admin_bookings.render,
            "admin_users": admin_users.render,
        }
        admin_routes.get(st.session_state.current_page, admin_dashboard.render)()
        return
    page = st.session_state.current_page
    render_navbar(page)
    routes = {
        "home": home.render,
        "events": events.render,
        "event_details": event_details.render,
        "seats": seats.render,
        "checkout": checkout.render,
        "payment": payment.render,
        "confirmation": confirmation.render,
        "bookings": bookings.render,
        "booking_details": booking_details.render,
        "support": support.render,
        "profile": profile.render,
    }
    routes.get(page, home.render)()
    render_footer()


if __name__ == "__main__":
    app()
