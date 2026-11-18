import streamlit as st

from frontend.components.admin_nav import render_admin_nav
from frontend.components.poster import render_poster
from frontend.utils.api import APIError, get_event_seats, get_events, update_admin_seat
from frontend.utils.navigation import breadcrumb, page_header


def render():
    render_admin_nav("admin_seats")
    page_header("INVENTORY", "Manage Seats", "Inspect live seat state and release seats through the backend.", "← Dashboard", "admin_dashboard", "🏠 Dashboard", "admin_dashboard")
    breadcrumb(["Admin", "Manage Seats"])
    try:
        events = get_events()
    except APIError as error:
        st.error(error.message)
        return
    if not events:
        st.info("No events found.")
        return

    labels = {f"{event['title']} · {event['venue']}": event for event in events}
    label_values = list(labels.values())
    selected_id = st.session_state.get("admin_selected_event")
    selected_index = next((index for index, event in enumerate(label_values) if event["id"] == selected_id), 0)
    selected = labels[st.selectbox("Select an event", list(labels), index=selected_index)]
    st.session_state.admin_selected_event = selected["id"]
    poster_col, details_col = st.columns([.8, 2.2])
    with poster_col:
        render_poster(selected, key=f"seat-event-{selected['id']}")
    with details_col:
        st.markdown(f"### {selected['title']}")
        st.caption(f"{selected['venue']} · {selected['date']} · {selected['totalSeats']} total seats")
    try:
        seats = get_event_seats(selected["id"], st.session_state.auth_token)
    except APIError as error:
        st.error(error.message)
        return

    statuses = st.multiselect("Show statuses", ["available", "reserved", "booked"], default=["available", "reserved", "booked"])
    visible = [seat for seat in seats if seat.get("status") in statuses]
    st.caption(f"Showing {len(visible)} of {len(seats)} seats")
    for seat in visible:
        reserved_by = seat.get("reservedBy") or {}
        left, middle, right, timestamp = st.columns([1.1, 1.1, 2.2, 1.8])
        left.write(f"**{seat.get('seatNumber', '')}**")
        middle.write(seat.get("status", ""))
        right.write(reserved_by.get("email", "-") if reserved_by else "-")
        timestamp.write(str(seat.get("reservedAt") or "-")[:19])
        if seat.get("status") == "reserved":
            if st.button("Release reservation", key=f"release_{seat['_id']}"):
                try:
                    update_admin_seat(seat["_id"], "available", st.session_state.auth_token)
                except APIError as error:
                    st.error(error.message)
                else:
                    st.rerun()
