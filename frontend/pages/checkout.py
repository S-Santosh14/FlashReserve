import streamlit as st

from frontend.data.dummy_data import get_event
from frontend.utils.session import currency, go


def render():
    event = get_event(st.session_state.selected_event)
    seats = st.session_state.selected_seats
    ticket_total = event["price"] * len(seats)
    st.markdown("<div class='page-intro compact'><span class='eyebrow'>ALMOST THERE</span><h1>Booking summary</h1><p>Check the details before you continue.</p></div>", unsafe_allow_html=True)
    main, total_col = st.columns([1.35, 0.8], gap="large")
    with main:
        st.markdown(
            f"""
            <div class="checkout-event"><span class="event-category">{event['category']}</span><h2>{event['title']}</h2>
            <p>{event['date']} · {event['time']}<br>{event['venue']}</p>
            <div class="detail-rule"></div><div class="checkout-seats"><span>YOUR SEATS</span><b>{' · '.join(seats)}</b></div></div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("← Change seats", key="change_seats"):
            go("seats")
    with total_col:
        st.markdown(f"<div class='summary-card total-card'><div class='section-kicker'>PRICE DETAILS</div><div class='summary-line'><span>{len(seats)} × ticket</span><b>{currency(ticket_total)}</b></div><div class='summary-line'><span>Convenience fee</span><b>₹0</b></div><div class='summary-total'><span>TOTAL</span><strong>{currency(ticket_total)}</strong></div></div>", unsafe_allow_html=True)
        if st.button("Proceed to payment", key="to_payment", type="primary", use_container_width=True):
            go("payment")
        st.markdown("<p class='secure-note'>A mock checkout for the UI prototype. No payment details are stored.</p>", unsafe_allow_html=True)
