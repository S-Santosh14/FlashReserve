from pathlib import Path
import streamlit as st

from frontend.components.footer import render_footer
from frontend.components.navbar import render_navbar
from frontend.pages import (
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


def inject_styles():
    css_path = Path(__file__).parent / "frontend" / "styles" / "main.css" 
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read() 
    st.markdown( f"<style>{css}</style>", unsafe_allow_html=True,)


def login_screen():
    _, center, _ = st.columns([1.1, 1.55, 1.1])
    with center:
        st.markdown("<div class='login-shell'><div class='login-brand'><span class='brand-mark'></span>FLASHRESERVE</div><h1 class='login-title'>Welcome back</h1><p class='login-copy'>Reserve your next experience.</p></div>", unsafe_allow_html=True)
        sign_in, register = st.tabs(["Sign in", "Register"])
        with sign_in:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="")
                password = st.text_input("Password", type="password", placeholder="")
                submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
            if submitted:
                if username == "santosh" and password == "1234":
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    go("home")
                else:
                    st.error("Try the demo account: santosh / 1234")
            st.markdown("<div class='login-hint'>Demo credentials: <b>santosh</b> / <b>1234</b></div>", unsafe_allow_html=True)
        with register:
            with st.form("register_form"):
                name = st.text_input("Your name", placeholder="Your name")
                email = st.text_input("Email", placeholder="you@example.com")
                new_password = st.text_input("Create password", type="password")
                registered = st.form_submit_button("Create account", type="primary", use_container_width=True)
            if registered:
                if name and email and new_password:
                    st.session_state.logged_in = True
                    st.session_state.username = name.split()[0].lower()
                    go("home")
                st.error("Please complete all fields.")


def app():
    initialize_session()
    inject_styles()
    if not st.session_state.logged_in:
        login_screen()
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
