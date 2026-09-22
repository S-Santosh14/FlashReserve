import streamlit as st

from frontend.components.poster import render_poster
from frontend.utils.api import APIError, get_event, get_seats, reserve_seats
from frontend.components.seat_map import render_seat_map
from frontend.utils.navigation import breadcrumb, page_header
from frontend.utils.session import currency, go


def render():
    try:
        event = get_event(st.session_state.selected_event)
        seats = get_seats(event["id"], st.session_state.auth_token)
    except APIError as error:
        st.error(error.message)
        return
    page_header("CHOOSE YOUR SPOT", "Select your seats", f"{event['title']} · {event['short_date']} · {event['time']}", "← Event details", "event_details", "🏠 Home", "home")
    breadcrumb(["Home", "Events", event["title"], "Seats"])
    poster_col, event_col = st.columns([.22, 1.78], gap="medium")
    with poster_col:
        render_poster(event, key=f"seats-{event['id']}")
    with event_col:
        st.markdown(f"### {event['title']}")
        st.caption(f"{event['short_date']} · {event['time']} · {event['venue']}")
    map_col, summary_col = st.columns([2.15, 0.85], gap="large")
    with map_col:
        st.markdown("<div class='seat-area'>", unsafe_allow_html=True)
        render_seat_map(seats)
        st.markdown("</div>", unsafe_allow_html=True)
    with summary_col:
        selected = st.session_state.selected_seats
        total = len(selected) * event["price"]
        seat_text = ", ".join(selected) if selected else "No seats yet"
        st.markdown(f"<div class='summary-card'><div class='section-kicker'>BOOKING SUMMARY</div><h3>{event['title']}</h3><div class='summary-line'><span>Selected seats</span><b>{seat_text}</b></div><div class='summary-line'><span>Tickets</span><b>{len(selected)}</b></div><div class='summary-total'><span>Total</span><strong>{currency(total)}</strong></div></div>", unsafe_allow_html=True)
        if st.button("Continue", key="seat_continue", type="primary", disabled=not selected, use_container_width=True):
            try:
                reserve_seats(event["id"], selected, st.session_state.auth_token)
            except APIError as error:
                st.error(error.message)
            else:
                go("checkout")
        if st.button("← Back to event", key="seat_back", use_container_width=True):
            go("event_details")
