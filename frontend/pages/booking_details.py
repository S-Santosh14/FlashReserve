import streamlit as st

from frontend.components.poster import render_poster
from frontend.utils.api import APIError, cancel_booking, get_bookings
from frontend.utils.navigation import breadcrumb, page_header
from frontend.utils.session import currency, go


def render():
    try:
        st.session_state.bookings = get_bookings(st.session_state.auth_token)
    except APIError as error:
        st.error(error.message)
        return
    booking = next((item for item in st.session_state.bookings if item["id"] == st.session_state.selected_booking_id), None)
    if not booking:
        go("bookings")
        return
    event = booking.get("event")
    if not event:
        st.error("The event for this booking is no longer available.")
        return
    page_header("BOOKING DETAILS", event["title"], f"{event.get('category', '')} · {event.get('venue', '')}", "← My bookings", "bookings", "🏠 Home", "home")
    breadcrumb(["Home", "My Bookings", "Booking Details"])
    st.markdown("<div class='tiny-gap'></div>", unsafe_allow_html=True)
    top, image_col = st.columns([1.6, 0.8], gap="large")
    with top:
        st.markdown(
            f"""
            <span class="eyebrow">BOOKING {booking['id']}</span><h2>{event['title']}</h2>
            <div class="ticket-detail"><span>WHEN</span><b>{event['date']}<br>{event['time']}</b></div>
            <div class="ticket-detail"><span>WHERE</span><b>{event['venue']}</b></div>
            """,
            unsafe_allow_html=True,
        )
    with image_col:
        render_poster(event, key=f"booking-{booking['id']}")
    st.markdown("<div class='ticket-divider'></div>", unsafe_allow_html=True)
    first, second, third = st.columns(3)
    with first:
        st.markdown(f"<div class='ticket-metric'><span>SEATS</span><b>{' · '.join(booking['seats'])}</b></div>", unsafe_allow_html=True)
    with second:
        st.markdown(f"<div class='ticket-metric'><span>AMOUNT</span><b>{currency(booking['amount'])}</b></div>", unsafe_allow_html=True)
    with third:
        st.markdown(f"<div class='ticket-metric'><span>BOOKED ON</span><b>{booking['booked_on']}</b></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    if booking["status"] == "Confirmed":
        action, _ = st.columns([1.2, 3.8])
        with action:
            if st.button("Cancel booking", key="detail_cancel", use_container_width=True):
                try:
                    updated = cancel_booking(booking["id"], st.session_state.auth_token)
                except APIError as error:
                    st.error(error.message)
                else:
                    st.session_state.booking = updated
                    st.rerun()
