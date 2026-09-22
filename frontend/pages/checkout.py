import streamlit as st

from frontend.components.poster import render_poster
from frontend.utils.api import APIError, create_booking, get_event
from frontend.utils.navigation import breadcrumb, page_header
from frontend.utils.session import currency, go


def render():
    try:
        event = get_event(st.session_state.selected_event)
    except APIError as error:
        st.error(error.message)
        return
    seats = st.session_state.selected_seats
    ticket_total = event["price"] * len(seats)
    page_header("ALMOST THERE", "Booking summary", "Check the details before you continue.", "← Seats", "seats", "🏠 Home", "home")
    breadcrumb(["Home", "Events", event["title"], "Seats", "Checkout"])
    main, total_col = st.columns([1.35, 0.8], gap="large")
    with main:
        poster_col, event_col = st.columns([.28, 1.72], gap="medium")
        with poster_col:
            render_poster(event, key=f"checkout-{event['id']}")
        with event_col:
            st.markdown(f"### {event['title']}")
            st.caption(f"{event['date']} · {event['time']} · {event['venue']}")
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
            if st.session_state.booking and st.session_state.booking.get("status") == "Pending":
                go("payment")
            else:
                try:
                    booking = create_booking(event["id"], seats, ticket_total, st.session_state.auth_token)
                except APIError as error:
                    st.error(error.message)
                else:
                    st.session_state.booking = booking
                    go("payment")
        st.markdown("<p class='secure-note'>A mock checkout for the UI prototype. No payment details are stored.</p>", unsafe_allow_html=True)
