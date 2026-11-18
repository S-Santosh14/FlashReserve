from html import escape

import streamlit as st

from frontend.components.poster import render_poster
from frontend.utils.navigation import breadcrumb, page_header
from frontend.utils.session import currency, go


def render():
    booking = st.session_state.booking
    if not booking:
        go("home")
        return
    event = booking.get("event") or {}
    title = escape(str(event.get("title") or "FlashReserve event"))
    reference = escape(str(booking.get("reference") or booking.get("id") or "Unavailable"))
    short_date = escape(str(event.get("short_date") or ""))
    event_time = escape(str(event.get("time") or ""))
    venue = escape(str(event.get("venue") or ""))
    seats = escape(" · ".join(str(seat) for seat in booking.get("seats", [])))
    transaction = escape(str(booking.get("transaction_id") or "Recorded by FlashReserve"))
    booked_on = escape(str(booking.get("booked_on") or "Unavailable"))
    page_header("RESERVATION COMPLETE", "Booking confirmed", "Your tickets have been successfully booked.", "← My bookings", "bookings", "🏠 Home", "home")
    breadcrumb(["Home", "My Bookings", "Confirmation"])
    with st.container(border=True, key="confirmation-ticket"):
        poster_col, details_col = st.columns([0.72, 1.8], gap="large", vertical_alignment="center")
        with poster_col:
            render_poster(event, key=f"confirmation-{booking['id']}", variant="compact")
        with details_col:
            st.markdown(
                f"""
                <div class="confirmation">
                  <div class="confirmation-check">✓</div><span class="eyebrow">RESERVATION COMPLETE</span>
                  <h2>Booking reference {reference}</h2><div class="confirmation-id">Keep this reference for your records.</div>
                  <div class="confirmation-id">Booked: {booked_on}</div>
                  <h2>{title}</h2><p>{short_date} · {event_time}<br>{venue}</p>
                  <div class="confirmation-grid"><div><span>SEATS</span><b>{seats}</b></div><div><span>TOTAL</span><b>{currency(booking.get('amount', 0))}</b></div></div>
                  <div class="confirmation-id">Transaction: {transaction}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    first, second, _ = st.columns([1.2, 1.2, 2.2])
    with first:
        if st.button("View booking", key="view_new_booking", type="primary", width="stretch"):
            if not any(item["id"] == booking["id"] for item in st.session_state.bookings):
                st.session_state.bookings.insert(0, booking)
            go("booking_details", selected_booking_id=booking["id"])
    with second:
        if st.button("Explore events", key="explore_again", width="stretch"):
            if not any(item["id"] == booking["id"] for item in st.session_state.bookings):
                st.session_state.bookings.insert(0, booking)
            go("events")
