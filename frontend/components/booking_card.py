import streamlit as st

from frontend.components.poster import render_poster
from frontend.utils.api import APIError, cancel_booking
from frontend.utils.session import currency, event_for_booking, go


def render_booking_card(booking, key_prefix="booking"):
    event = event_for_booking(booking)
    if not event:
        st.error("The event for this booking is no longer available.")
        return
    left, right = st.columns([1.15, 2.6], gap="medium")
    with left:
        render_poster(event, key=f"booking-card-{booking['id']}")
    with right:
        st.markdown(
            f"""
            <div class="booking-card-copy">
              <span class="status {booking['status'].lower()}">{booking['status']}</span>
              <div class="booking-event">{event['title']}</div>
              <div class="booking-meta">{event['date']} · {event['time']}<br>{event['venue']}<br>Seats: {', '.join(booking['seats'])} &nbsp;·&nbsp; {currency(booking['amount'])}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        action_col, cancel_col, _ = st.columns([1.3, 1.1, 1.3], gap="small")
        with action_col:
            if st.button("View details", key=f"{key_prefix}_view_{booking['id']}", use_container_width=True):
                go("booking_details", selected_booking_id=booking["id"])
        if booking["status"] == "Confirmed":
            with cancel_col:
                if st.button("Cancel", key=f"{key_prefix}_cancel_{booking['id']}", use_container_width=True):
                    try:
                        updated = cancel_booking(booking["id"], st.session_state.auth_token)
                    except APIError as error:
                        st.error(error.message)
                    else:
                        for index, item in enumerate(st.session_state.bookings):
                            if item["id"] == booking["id"]:
                                st.session_state.bookings[index] = updated
                        st.rerun()
