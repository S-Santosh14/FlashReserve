import streamlit as st

from frontend.data.dummy_data import get_event
from frontend.utils.session import currency, go


def render():
    booking = next((item for item in st.session_state.bookings if item["id"] == st.session_state.selected_booking_id), None)
    if not booking:
        go("bookings")
    event = get_event(booking["event_id"])
    if st.button("← Back to my bookings", key="booking_back"):
        go("bookings")
    st.markdown("<div class='tiny-gap'></div>", unsafe_allow_html=True)
    top, image_col = st.columns([1.6, 0.8], gap="large")
    with top:
        st.markdown(
            f"""
            <span class="eyebrow">BOOKING {booking['id']}</span><h1>{event['title']}</h1>
            <span class="status {booking['status'].lower()}">{booking['status']}</span>
            <div class="ticket-detail"><span>WHEN</span><b>{event['date']}<br>{event['time']}</b></div>
            <div class="ticket-detail"><span>WHERE</span><b>{event['venue']}</b></div>
            """,
            unsafe_allow_html=True,
        )
    with image_col:
        st.image(event["image"], use_container_width=True)
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
                booking["status"] = "Cancelled"
                st.rerun()
