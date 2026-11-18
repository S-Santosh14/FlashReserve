from datetime import date

import streamlit as st

from frontend.components.admin_nav import render_admin_nav
from frontend.components.poster import render_poster
from frontend.utils.api import (
    APIError,
    create_event,
    delete_event,
    get_admin_events,
    update_event,
)
from frontend.utils.navigation import breadcrumb, page_header
from frontend.utils.session import go


def _event_payload(
    title,
    category,
    venue,
    event_date,
    event_time,
    description,
    total_seats,
    seats_per_row,
    price,
    status,
):
    return {
        "title": title.strip(),
        "category": category.strip(),
        "venue": venue.strip(),
        "date": event_date.isoformat(),
        "time": event_time.strip(),
        "description": description.strip(),
        "totalSeats": int(total_seats),
        "seatsPerRow": int(seats_per_row),
        "price": float(price),
        "status": status,
    }


def _render_form(event=None):
    editing = event is not None
    if editing and not isinstance(event, dict):
        st.error("The selected event could not be loaded. Choose another event or create a new one.")
        return

    values = event if editing else {}
    event_id = values.get("id", "new")
    form_key = f"admin_event_{'edit' if editing else 'create'}_{event_id}"
    st.markdown("### Edit event" if editing else "### Create event")

    raw_date = values.get("raw_date") or str(values.get("date", ""))[:10]
    try:
        event_date = date.fromisoformat(raw_date) if raw_date else date.today()
    except (TypeError, ValueError):
        event_date = date.today()

    with st.form(form_key):
        title = st.text_input("Title", value=values.get("title", ""), key=f"{form_key}_title")
        category = st.text_input("Category", value=values.get("category", ""), key=f"{form_key}_category")
        venue = st.text_input("Venue", value=values.get("venue", ""), key=f"{form_key}_venue")
        selected_date = st.date_input("Date", value=event_date, key=f"{form_key}_date")
        event_time = st.text_input("Time", value=values.get("time", ""), key=f"{form_key}_time")
        description = st.text_area(
            "Description",
            value=values.get("description", ""),
            key=f"{form_key}_description",
        )
        poster = st.file_uploader(
            "Event Poster (PNG, JPG, JPEG, WEBP)",
            type=["png", "jpg", "jpeg", "webp"],
            key=f"{form_key}_poster",
        )
        if poster:
            st.image(poster, caption="Poster preview", width="stretch")
        total_seats = st.number_input(
            "Total seats",
            min_value=1,
            value=max(1, int(values.get("totalSeats") or 1)),
            step=1,
            key=f"{form_key}_total_seats",
        )
        seats_per_row = st.number_input(
            "Seats per row",
            min_value=1,
            value=max(1, int(values.get("seatsPerRow") or 10)),
            step=1,
            help="New seats are generated in numbered rows using this layout.",
            key=f"{form_key}_seats_per_row",
        )
        price = st.number_input(
            "Ticket price",
            min_value=0.0,
            value=float(values.get("price") or 0),
            step=1.0,
            key=f"{form_key}_price",
        )
        status = st.selectbox(
            "Event status",
            ("active", "archived"),
            index=0 if values.get("status", "active") != "archived" else 1,
            help="Archived events are hidden from customers and cannot receive new reservations.",
            key=f"{form_key}_status",
        )
        submitted = st.form_submit_button(
            "Update event" if editing else "Create event",
            type="primary",
            width="stretch",
        )

    if not submitted:
        return
    if not all((title.strip(), category.strip(), venue.strip(), event_time.strip(), description.strip())):
        st.error("Complete all event fields.")
        return

    payload = _event_payload(
        title,
        category,
        venue,
        selected_date,
        event_time,
        description,
        total_seats,
        seats_per_row,
        price,
        status,
    )
    try:
        if editing:
            update_event(event_id, payload, st.session_state.auth_token, poster=poster)
        else:
            create_event(payload, st.session_state.auth_token, poster=poster)
    except APIError as error:
        st.error(error.message)
    else:
        st.session_state.admin_notice = "Event saved successfully."
        st.rerun()


def _render_event_catalogue(events):
    search = st.text_input("Search events", placeholder="Search title, category, or venue")
    query = search.strip().casefold()
    filtered_events = [
        event for event in events
        if not query or query in " ".join(
            str(event.get(field, ""))
            for field in ("title", "category", "venue", "status")
        ).casefold()
    ]
    if not filtered_events:
        st.info("No events match your search." if events else "No events found.")
        return

    st.markdown("### Event catalogue")
    for row_start in range(0, len(filtered_events), 2):
        columns = st.columns(2, gap="medium")
        for column, event in zip(columns, filtered_events[row_start : row_start + 2]):
            with column:
                with st.container(border=True):
                    render_poster(event, key=f"admin-{event['id']}")
                    st.markdown(f"**{event.get('title', 'Untitled event')}**")
                    st.caption(
                        f"{event.get('category', 'Uncategorized')} · "
                        f"{event.get('venue', 'Venue not set')} · "
                        f"{str(event.get('status', 'active')).capitalize()}"
                    )
                    st.write(
                        f"{event.get('short_date', 'Date not set')} · "
                        f"{event.get('time', 'Time not set')} · "
                        f"{event.get('totalSeats', 0)} seats"
                    )
                    edit_col, seats_col = st.columns(2)
                    with edit_col:
                        if st.button(
                            "Edit",
                            key=f"card_edit_{event['id']}",
                            width="stretch",
                        ):
                            st.session_state.admin_selected_event = event["id"]
                            st.rerun()
                    with seats_col:
                        if st.button(
                            "Manage seats",
                            key=f"card_seats_{event['id']}",
                            width="stretch",
                        ):
                            st.session_state.admin_selected_event = event["id"]
                            go("admin_seats")


def render():
    render_admin_nav("admin_events")
    page_header(
        "CATALOGUE",
        "Manage Events",
        "Create and maintain events stored in the selected database.",
        "← Dashboard",
        "admin_dashboard",
        "🏠 Dashboard",
        "admin_dashboard",
    )
    breadcrumb(["Admin", "Manage Events"])
    notice = st.session_state.pop("admin_notice", None)
    if notice:
        st.success(notice)

    try:
        events = get_admin_events(st.session_state.auth_token)
    except APIError as error:
        st.error(error.message)
        return

    create_tab, manage_tab = st.tabs(["Create event", "Existing events"])
    with create_tab:
        _render_form()
    with manage_tab:
        _render_event_catalogue(events)
        if not events:
            return

        event_ids = [event["id"] for event in events]
        selected_id = st.session_state.get("admin_selected_event")
        if selected_id not in event_ids:
            if selected_id is not None:
                st.warning("The previously selected event no longer exists. Select an available event.")
            selected_id = event_ids[0]
            st.session_state.admin_selected_event = selected_id
        selected_id = st.selectbox(
            "Select an event to edit",
            event_ids,
            index=event_ids.index(selected_id),
            format_func=lambda event_id: next(
                f"{event.get('title', 'Untitled event')} · {event.get('venue', 'No venue')}"
                for event in events if event["id"] == event_id
            ),
            key="admin_event_selection",
        )
        st.session_state.admin_selected_event = selected_id
        selected = next((event for event in events if event["id"] == selected_id), None)
        if selected is None:
            st.error("The selected event no longer exists. Refresh the event list and select another event.")
            return

        if selected.get("poster_url"):
            st.markdown("**Current poster**")
            render_poster(selected, key=f"current-{selected['id']}")
        _render_form(selected)

        st.divider()
        st.markdown("### Delete event")
        st.caption(
            "If booking history or held seats exist, this action archives the event instead "
            "of deleting its bookings, payments, or customer records."
        )
        confirm = st.checkbox(
            f"Confirm deletion of {selected.get('title', 'this event')} (or archive it if records must be preserved).",
            key=f"confirm_delete_{selected['id']}",
        )
        if st.button(
            "Delete event",
            type="secondary",
            disabled=not confirm,
            key=f"delete_{selected['id']}",
        ):
            try:
                result = delete_event(selected["id"], st.session_state.auth_token)
            except APIError as error:
                st.error(error.message)
            else:
                st.session_state.admin_selected_event = None
                st.session_state.admin_notice = (
                    "Event archived to preserve booking and seat records."
                    if result.get("archived")
                    else "Event deleted."
                )
                st.rerun()
