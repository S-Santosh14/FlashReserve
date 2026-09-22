import streamlit as st

from frontend.components.admin_nav import render_admin_nav
from frontend.components.poster import render_poster
from frontend.utils.api import APIError, get_admin_bookings
from frontend.utils.navigation import breadcrumb, page_header


def render():
    render_admin_nav("admin_bookings")
    page_header("RESERVATIONS", "Manage Bookings", "Review customer reservations from MongoDB.", "← Dashboard", "admin_dashboard", "🏠 Dashboard", "admin_dashboard")
    breadcrumb(["Admin", "Manage Bookings"])
    try:
        bookings = get_admin_bookings(st.session_state.auth_token)
    except APIError as error:
        st.error(error.message)
        return
    if not bookings:
        st.info("No bookings found.")
        return
    rows = []
    for booking in bookings:
        customer = booking.get("userId") or {}
        event = booking.get("eventId") or {}
        seats = booking.get("seats") or []
        rows.append({
            "Booking ID": booking.get("_id", ""),
            "Customer": customer.get("email", "-"),
            "Event": event.get("title", "-"),
            "Seats": ", ".join(seat.get("seatNumber", "") for seat in seats),
            "Amount": booking.get("totalAmount", 0),
            "Status": booking.get("status", ""),
            "Created At": str(booking.get("createdAt", ""))[:19],
        })
        with st.container(border=True):
            poster_col, info_col = st.columns([.35, 2.65])
            with poster_col:
                render_poster(event, key=f"admin-booking-{booking.get('_id', '')}")
            with info_col:
                st.markdown(f"**{event.get('title', '-')}** · {booking.get('status', '')}")
                st.caption(f"{customer.get('email', '-')} · Seats: {', '.join(seat.get('seatNumber', '') for seat in seats)} · ₹{booking.get('totalAmount', 0)}")
    st.dataframe(rows, use_container_width=True, hide_index=True)
