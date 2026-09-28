from datetime import date

import streamlit as st

from frontend.components.admin_nav import render_admin_nav
from frontend.components.poster import render_poster
from frontend.components.poster import render_poster
from frontend.utils.api import APIError, create_event, delete_event, get_events, update_event
from frontend.utils.navigation import breadcrumb, page_header
from frontend.utils.session import go



def _event_payload(title, category, venue, event_date, event_time, description, total_seats, price):
    return {
        "title": title.strip(),
        "category": category.strip(),
        "venue": venue.strip(),
        "date": event_date.isoformat(),
        "time": event_time.strip(),
        "description": description.strip(),
        "totalSeats": int(total_seats),
        "price": float(price),
    }


def _render_form(event=None):
    editing = event is not None
    prefix = "edit" if editing else "create"
    st.markdown("### Edit event" if editing else "### Create event")
    raw_date = event.get("raw_date") if editing else date.today().isoformat()
    try:
        event_date = date.fromisoformat(raw_date)
    except ValueError:
        event_date = date.today()
    with st.form(f"admin_event_{prefix}"):
        title = st.text_input("Title", value=event.get("title", "") if editing else "")
        category = st.text_input("Category", value=event.get("category", "") if editing else "")
        venue = st.text_input("Venue", value=event.get("venue", "") if editing else "")
        selected_date = st.date_input("Date", value=event_date)
        event_time = st.text_input("Time", value=event.get("time", "") if editing else "")
        description = st.text_area("Description", value=event.get("description", "") if editing else "")
        poster = st.file_uploader("Event Poster (PNG, JPG, JPEG, WEBP)", type=["png", "jpg", "jpeg", "webp"], key=f"poster_{prefix}_{event.get('id', 'new') if editing else 'new'}")
        if poster:
            st.image(poster, caption="Poster preview", use_container_width=True)
        total_seats = st.number_input("Total Seats", min_value=1, value=int(event.get("totalSeats", 1)) if editing else 1, step=1)
        price = st.number_input("Ticket Price", min_value=0.0, value=float(event.get("price", 0)) if editing else 0.0, step=1.0)
        submitted = st.form_submit_button("Update Event" if editing else "Create Event", type="primary")
    if not submitted:
        return
    if not all([title.strip(), category.strip(), venue.strip(), event_time.strip(), description.strip()]):
        st.error("Complete all event fields.")
        return
    payload = _event_payload(title, category, venue, selected_date, event_time, description, total_seats, price)
    try:
        if editing:
            update_event(event["id"], payload, st.session_state.auth_token, poster=poster)
        else:
            create_event(payload, st.session_state.auth_token, poster=poster)
    except APIError as error:
        st.error(error.message)
    else:
        st.session_state.admin_notice = "Event saved successfully."
        st.rerun()


def render():
    render_admin_nav("admin_events")
    page_header("CATALOGUE", "Manage Events", "Create and maintain events stored in MongoDB.", "← Dashboard", "admin_dashboard", "🏠 Dashboard", "admin_dashboard")
    breadcrumb(["Admin", "Manage Events"])
    if st.session_state.get("admin_notice"):
        st.success(st.session_state.pop("admin_notice"))
    try:
        events = get_events()
    except APIError as error:
        st.error(error.message)
        return

    create_tab, manage_tab = st.tabs(["Create Event", "Existing Events"])
    with create_tab:
        _render_form()
    with manage_tab:
        if not events:
            st.info("No events found.")
            return
        st.markdown("### Event catalogue")
        for row_start in range(0, len(events), 2):
            columns = st.columns(2, gap="medium")
            for column, event in zip(columns, events[row_start : row_start + 2]):
                with column:
                    with st.container(border=True):
                        render_poster(event, key=f"admin-{event['id']}")
                        st.markdown(f"**{event['title']}**")
                        st.caption(f"{event['category']}  ·  {event['venue']}")
                        st.write(f"{event['short_date']}  ·  {event['time']}  ·  {event['totalSeats']} seats")
                        edit_col, seats_col = st.columns(2)
                        with edit_col:
                            if st.button("Edit", key=f"card_edit_{event['id']}", use_container_width=True):
                                st.session_state.admin_selected_event = event["id"]
                                st.rerun()
                        with seats_col:
                            if st.button("Manage seats", key=f"card_seats_{event['id']}", use_container_width=True):
                                st.session_state.admin_selected_event = event["id"]
                                go("admin_seats")
        labels = {f"{event['title']} · {event['venue']}": event for event in events}
        selected_id = st.session_state.get("admin_selected_event")
        label_values = list(labels.values())
        selected_index = next((index for index, event in enumerate(label_values) if event["id"] == selected_id), 0)
        selected_label = st.selectbox("Select an event to edit", list(labels), index=selected_index)
        selected = labels[selected_label]
        st.session_state.admin_selected_event = selected["id"]
        if selected.get("poster_url"):
            st.markdown("**Current poster**")
            render_poster(selected, key=f"current-{selected['id']}")
        _render_form(selected)
        st.divider()
        st.markdown("### Delete event")
        confirm = st.checkbox(f"I understand that {selected['title']} and its seats will be deleted.", key=f"confirm_delete_{selected['id']}")
        if st.button("Delete Event", type="secondary", disabled=not confirm, key=f"delete_{selected['id']}"):
            try:
                delete_event(selected["id"], st.session_state.auth_token)
            except APIError as error:
                st.error(error.message)
            else:
                st.success("Event deleted.")
                st.rerun()
