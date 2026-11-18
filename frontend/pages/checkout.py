import streamlit as st

from frontend.components.poster import render_poster
from frontend.utils.api import APIError, create_booking, get_event
from frontend.utils.navigation import breadcrumb, page_header
from frontend.utils.session import currency, go, render_reservation_countdown


def render():
    try:
        event = get_event(st.session_state.selected_event)
    except APIError as error:
        st.error(error.message)
        return
    seats = st.session_state.selected_seats
    if not seats or not st.session_state.reservation_id:
        st.warning("Choose and reserve seats before checkout.")
        if st.button("Choose seats", key="checkout_choose_seats"):
            go("seats")
        return
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
        render_reservation_countdown(st.session_state.lock_expires_at)
        if st.button("Proceed to payment", key="to_payment", type="primary", width="stretch"):
            if st.session_state.booking_submit_in_progress:
                st.warning("Your booking request is already being submitted.")
            else:
                if st.session_state.booking and st.session_state.booking.get("status") == "Pending":
                    go("payment")
                else:
                    st.session_state.booking_submit_in_progress = True
                    st.session_state.booking_submit_mode = st.session_state.operating_mode
                    try:
                        with st.spinner("Confirming your seats…"):
                            booking = create_booking(
                                event["id"],
                                seats,
                                ticket_total,
                                st.session_state.auth_token,
                                st.session_state.reservation_id,
                            )
                    except APIError as error:
                        st.error(error.message)
                    else:
                        st.session_state.booking = booking
                        st.session_state.payment_idempotency_key = None
                        st.session_state.payment_attempt_signature = None
                        go("payment")
                    finally:
                        st.session_state.booking_submit_in_progress = False
                        st.session_state.booking_submit_mode = None
        if st.session_state.booking and st.session_state.booking.get("status") in {"Failed", "Expired"}:
            st.error("This payment attempt ended and its seats were released.")
            if st.button("Choose seats again", key="checkout_retry_seats"):
                go(
                    "seats",
                    booking=None,
                    reservation_id=None,
                    lock_expires_at=None,
                    payment_idempotency_key=None,
                    payment_attempt_signature=None,
                )
        st.markdown("<p class='secure-note'>A mock checkout for the UI prototype. No payment details are stored.</p>", unsafe_allow_html=True)
