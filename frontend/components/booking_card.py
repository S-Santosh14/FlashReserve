from html import escape

import streamlit as st

from frontend.components.poster import render_poster
from frontend.utils.api import APIError, cancel_booking
from frontend.utils.session import currency, event_for_booking, go


def render_booking_card(booking, key_prefix="booking"):
    event = event_for_booking(booking)
    if not event:
        st.error("The event for this booking is no longer available.")
        return
    status = escape(str(booking.get("status") or "Unknown"))
    title = escape(str(event.get("title") or "FlashReserve event"))
    reference = escape(str(booking.get("reference") or booking.get("id") or "Unavailable"))
    event_date = escape(str(event.get("date") or "Date to be announced"))
    event_time = escape(str(event.get("time") or "Time to be announced"))
    venue = escape(str(event.get("venue") or "Venue to be announced"))
    seats = escape(", ".join(str(seat) for seat in booking.get("seats", [])))
    booked_on = escape(str(booking.get("booked_on") or "Unavailable"))
    left, right = st.columns([1.15, 2.6], gap="medium")
    with left:
        render_poster(event, key=f"booking-card-{booking['id']}")
    with right:
        st.markdown(
            f"""
            <div class="booking-card-copy">
              <span class="status {status.casefold()}">{status}</span>
              <div class="booking-event">{title}</div>
              <div class="booking-meta">Reference: {reference}<br>Booked: {booked_on}<br>{event_date} · {event_time}<br>{venue}<br>Seats: {seats} &nbsp;·&nbsp; {currency(booking.get('amount', 0))}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if booking.get("refund"):
            st.caption(f"Refund {booking['refund'].get('status', 'pending')} · {currency(booking['refund'].get('amount', 0))}")
        action_col, cancel_col, _ = st.columns([1.3, 1.1, 1.3], gap="small")
        with action_col:
            if st.button("View details", key=f"{key_prefix}_view_{booking['id']}", width="stretch"):
                go("booking_details", selected_booking_id=booking["id"])
        if booking["status"] == "Confirmed":
            with cancel_col:
                if st.button("Cancel", key=f"{key_prefix}_cancel_{booking['id']}", width="stretch"):
                    try:
                        updated = cancel_booking(booking["id"], st.session_state.auth_token)
                    except APIError as error:
                        st.error(error.message)
                    else:
                        for index, item in enumerate(st.session_state.bookings):
                            if item["id"] == booking["id"]:
                                st.session_state.bookings[index] = updated
                        st.rerun()
