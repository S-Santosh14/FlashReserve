import streamlit as st

from frontend.components.seat_map import render_seat_map
from frontend.data.dummy_data import get_event
from frontend.utils.session import currency, go


def render():
    event = get_event(st.session_state.selected_event)
    st.markdown(f"<div class='page-intro compact'><span class='eyebrow'>CHOOSE YOUR SPOT</span><h1>Select your seats</h1><p>{event['title']} &nbsp;·&nbsp; {event['short_date']} · {event['time']} &nbsp;·&nbsp; {event['city']}</p></div>", unsafe_allow_html=True)
    map_col, summary_col = st.columns([2.15, 0.85], gap="large")
    with map_col:
        st.markdown("<div class='seat-area'>", unsafe_allow_html=True)
        render_seat_map()
        st.markdown("</div>", unsafe_allow_html=True)
    with summary_col:
        selected = st.session_state.selected_seats
        total = len(selected) * event["price"]
        seat_text = ", ".join(selected) if selected else "No seats yet"
        st.markdown(f"<div class='summary-card'><div class='section-kicker'>BOOKING SUMMARY</div><h3>{event['title']}</h3><div class='summary-line'><span>Selected seats</span><b>{seat_text}</b></div><div class='summary-line'><span>Tickets</span><b>{len(selected)}</b></div><div class='summary-total'><span>Total</span><strong>{currency(total)}</strong></div></div>", unsafe_allow_html=True)
        if st.button("Continue", key="seat_continue", type="primary", disabled=not selected, use_container_width=True):
            go("checkout")
        if st.button("Back", key="seat_back", use_container_width=True):
            go("event_details")
