from collections import Counter
import uuid

import streamlit as st

from frontend.components.poster import render_poster
from frontend.utils.api import APIError, get_event, get_seats, reserve_seats
from frontend.components.seat_map import render_seat_map
from frontend.utils.navigation import breadcrumb, page_header
from frontend.utils.session import currency, go


@st.fragment(run_every="5s")
def render():
    try:
        event = get_event(st.session_state.selected_event)
        seats = get_seats(event["id"], st.session_state.auth_token)
    except APIError as error:
        st.error(error.message)
        return
    page_header("CHOOSE YOUR SPOT", "Select your seats", f"{event['title']} · {event['short_date']} · {event['time']}", "← Event details", "event_details", "🏠 Home", "home")
    breadcrumb(["Home", "Events", event["title"], "Seats"])
    poster_col, event_col = st.columns([.32, 1.68], gap="medium")
    with poster_col:
        render_poster(event, key=f"seats-{event['id']}")
    with event_col:
        st.markdown(f"### {event['title']}")
        st.caption(f"{event['short_date']} · {event['time']} · {event['venue']}")
    map_col, summary_col = st.columns([2.15, 0.85], gap="large")
    with map_col:
        selected = st.session_state.selected_seats
        user_id = str((st.session_state.get("user") or {}).get("id") or "")
        seat_by_number = {str(seat.get("seatNumber", "")): seat for seat in seats}
        still_selectable = {
            seat_number
            for seat_number, seat in seat_by_number.items()
            if seat.get("status") == "available"
            or (seat.get("status") == "reserved" and str(seat.get("reservedBy") or "") == user_id)
        }
        stale_selection = [seat for seat in selected if seat not in still_selectable]
        if stale_selection:
            st.session_state.selected_seats = [seat for seat in selected if seat in still_selectable]
            st.warning("One or more selected seats are no longer available. The map has been refreshed.")
        with st.container(border=True, key="seat-map"):
            st.caption(f"{len(seats)} seats · {sum(seat.get('status') == 'available' for seat in seats)} available · Scroll horizontally for wider rows")
            categories = Counter(seat.get("category", "Silver") for seat in seats)
            st.caption(" · ".join(f"{category}: {categories.get(category, 0)}" for category in ["VIP", "Platinum", "Gold", "Silver"]))
            render_seat_map(
                seats,
                st.session_state.selected_seats,
                user_id,
                st.session_state.reservation_id,
            )
    with summary_col:
        selected = st.session_state.selected_seats
        total = len(selected) * event["price"]
        seat_text = ", ".join(selected) if selected else "No seats yet"
        with st.container(key="seat-summary"):
            st.markdown(f"<div class='summary-card'><div class='section-kicker'>BOOKING SUMMARY</div><h3>{event['title']}</h3><div class='summary-line'><span>Selected seats</span><b>{seat_text}</b></div><div class='summary-line'><span>Tickets · {currency(event['price'])} each</span><b>{len(selected)}</b></div><div class='summary-total'><span>Total</span><strong>{currency(total)}</strong></div></div>", unsafe_allow_html=True)
            if st.button("Continue", key="seat_continue", type="primary", disabled=not selected, width="stretch"):
                reservation_id = st.session_state.reservation_id or uuid.uuid4().hex
                st.session_state.reservation_id = reservation_id
                try:
                    reservation = reserve_seats(event["id"], selected, st.session_state.auth_token, reservation_id)
                except APIError as error:
                    st.error(error.message)
                    if error.status_code == 409:
                        st.rerun()
                else:
                    st.session_state.lock_expires_at = reservation["expiresAt"]
                    st.session_state.booking = None
                    st.session_state.payment_idempotency_key = None
                    st.session_state.payment_attempt_signature = None
                    go("checkout")
            if st.button("← Back to event", key="seat_back", width="stretch"):
                go("event_details")
