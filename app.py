import streamlit as st

from frontend.components.footer import render_footer
from frontend.components.mode_selector import render_mode_selector
from frontend.components.navbar import render_navbar
from frontend.components.raft_monitor import render_raft_monitor
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
from frontend.styles import inject_premium_styles
from frontend.utils.api import APIError, get_mode_availability, login_user, register_user
from frontend.utils.session import go, initialize_session


st.set_page_config(
    page_title="FlashReserve",
    page_icon=":material/local_activity:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _selected_mode_is_available():
    availability = get_mode_availability()
    st.session_state.mode_availability = availability
    mode = st.session_state.operating_mode
    selected = availability[mode]
    if not selected["available"]:
        st.error(
            selected.get(
                "unavailable_message",
                "Selected operating mode is temporarily unavailable.",
            )
        )
        return False
    return True


def _password_strength(password):
    checks = (
        len(password) >= 8,
        any(character.islower() for character in password),
        any(character.isupper() for character in password),
        any(character.isdigit() for character in password),
        any(not character.isalnum() for character in password),
    )
    score = sum(checks)
    labels = ("Very weak", "Weak", "Fair", "Good", "Strong", "Very strong")
    return score, labels[score]


def login_screen():
    welcome, panel = st.columns([1.05, .95], gap="large", vertical_alignment="center")
    with welcome:
        st.markdown(
            """
            <section class="login-shell">
              <div class="login-brand"><span class="brand-mark"></span>FLASHRESERVE</div>
              <div class="eyebrow">MAKE ROOM FOR A GOOD NIGHT</div>
              <h1 class="login-title">The best nights<br>start with a seat.</h1>
              <p class="login-copy">
                Find your next live experience, choose the seats you love, and keep every plan
                together in one place.
              </p>
              <div class="login-points">
                <span>Live events</span><span>Clear seat availability</span><span>Secure booking</span>
              </div>
            </section>
            """,
            unsafe_allow_html=True,
        )
    with panel:
        with st.container(key="login-panel"):
            st.markdown("### Welcome back")
            st.caption("Sign in to pick up where your next experience begins.")
            render_mode_selector()
            availability = st.session_state.get("mode_availability", {})
            selected_available = availability.get(
                st.session_state.operating_mode, {}
            ).get("available", False)
            sign_in, register = st.tabs(["Sign in", "Create account"])
            with sign_in:
                
                with st.form("login_form"):
                    email = st.text_input(
                        "Email",
                        placeholder="you@example.com",
                        key="login_email",
                    )
                    password = st.text_input(
                        "Password",
                        type="password",
                        key="login_password",
                    )
                    submitted = st.form_submit_button(
                        "Sign in",
                        type="primary",
                        width="stretch",
                        disabled=not selected_available,
                    )
                if submitted:
                    if not email or not password:
                        st.error("Enter your email and password.")
                    elif _selected_mode_is_available():
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
                st.markdown(
                    "<div class='login-hint'>Your account stays connected to the selected operating mode.</div>",
                    unsafe_allow_html=True,
                )
            with register:
                name = st.text_input("Your name", placeholder="Full name", key="register_name")
                email = st.text_input(
                    "Email",
                    placeholder="you@example.com",
                    key="register_email",
                )
                new_password = st.text_input(
                    "Create password",
                    type="password",
                    key="register_password",
                )
                if new_password:
                    score, strength = _password_strength(new_password)
                    st.progress(score / 5, text=f"Password strength: {strength}")
                else:
                    st.caption("Use at least 8 characters and mix letter cases, numbers, and symbols.")
                confirm_password = st.text_input(
                    "Confirm password",
                    type="password",
                    key="register_confirm_password",
                )
                registered = st.button(
                    "Create account",
                    type="primary",
                    width="stretch",
                    disabled=not selected_available,
                    key="register_submit",
                )
                if registered:
                    if not name or not email or not new_password or not confirm_password:
                        st.error("Please complete all fields.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match.")
                    elif _selected_mode_is_available():
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

    render_raft_monitor()


def app():
    initialize_session()
    inject_premium_styles()
    if not st.session_state.logged_in:
        login_screen()
        return

    render_mode_selector()
    if st.session_state.role == "admin":
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
