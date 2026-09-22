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
    page_header("RESERVATION COMPLETE", "Booking confirmed", "Your tickets have been successfully booked.", "← My bookings", "bookings", "🏠 Home", "home")
    breadcrumb(["Home", "My Bookings", "Confirmation"])
    render_poster(event, key=f"confirmation-{booking['id']}")
    st.markdown(
        f"""
        <div class="confirmation">
          <div class="confirmation-check">✓</div><span class="eyebrow">RESERVATION COMPLETE</span>
              <h2>Booking ID {booking['id']}</h2><div class="confirmation-id">Keep this reference for your records.</div>
          <h2>{event.get('title', 'FlashReserve event')}</h2><p>{event.get('short_date', '')} · {event.get('time', '')}<br>{event.get('venue', '')}</p>
          <div class="confirmation-grid"><div><span>SEATS</span><b>{' · '.join(booking['seats'])}</b></div><div><span>TOTAL</span><b>{currency(booking['amount'])}</b></div></div>
          <div class="confirmation-id">Transaction: {booking.get('transaction_id', 'Recorded by FlashReserve')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    first, second, _ = st.columns([1.2, 1.2, 2.2])
    with first:
        if st.button("View booking", key="view_new_booking", type="primary", use_container_width=True):
            if not any(item["id"] == booking["id"] for item in st.session_state.bookings):
                st.session_state.bookings.insert(0, booking)
            go("booking_details", selected_booking_id=booking["id"])
    with second:
        if st.button("Explore events", key="explore_again", use_container_width=True):
            if not any(item["id"] == booking["id"] for item in st.session_state.bookings):
                st.session_state.bookings.insert(0, booking)
            go("events")
