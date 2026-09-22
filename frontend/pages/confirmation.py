import streamlit as st

from frontend.data.dummy_data import get_event
from frontend.utils.session import currency, go


def render():
    booking = st.session_state.booking
    if not booking:
        go("home")
    event = get_event(booking["event_id"])
    st.markdown(
        f"""
        <div class="confirmation">
          <div class="confirmation-check">✓</div><span class="eyebrow">RESERVATION COMPLETE</span>
          <h1>Booking confirmed</h1><div class="confirmation-id">{booking['id']}</div>
          <h2>{event['title']}</h2><p>{event['short_date']} · {event['time']}<br>{event['venue']}</p>
          <div class="confirmation-grid"><div><span>SEATS</span><b>{' · '.join(booking['seats'])}</b></div><div><span>TOTAL</span><b>{currency(booking['amount'])}</b></div></div>
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
