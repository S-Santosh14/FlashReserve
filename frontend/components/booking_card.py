import streamlit as st

from frontend.utils.session import currency, event_for_booking, go


def render_booking_card(booking, key_prefix="booking"):
    event = event_for_booking(booking)
    left, right = st.columns([1.15, 2.6], gap="medium")
    with left:
        st.image(event["image"], use_container_width=True)
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
                    for item in st.session_state.bookings:
                        if item["id"] == booking["id"]:
                            item["status"] = "Cancelled"
                    st.rerun()
