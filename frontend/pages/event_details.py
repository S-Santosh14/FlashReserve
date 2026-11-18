from html import escape

import streamlit as st

from frontend.utils.api import APIError, get_event
from frontend.components.poster import render_poster
from frontend.utils.navigation import breadcrumb, page_header
from frontend.utils.session import currency, go


def render():
    try:
        event = get_event(st.session_state.selected_event)
    except APIError as error:
        st.error(error.message)
        return
    page_header("EVENT DETAILS", event["title"], f"{event['category']} · {event['venue']}", "← Events", "events", "🏠 Home", "home")
    breadcrumb(["Home", "Events", event["title"]])
    eyebrow = escape(str(event.get("eyebrow") or event.get("category") or "Live event"))
    title = escape(str(event.get("title") or "Untitled event"))
    venue = escape(str(event.get("venue") or "Venue to be announced"))
    event_date = escape(str(event.get("date") or "Date to be announced"))
    event_time = escape(str(event.get("time") or "Time to be announced"))
    description = escape(str(event.get("description") or "Event details will be announced soon."))
    category = escape(str(event.get("category") or "Live event"))
    st.markdown("<div class='tiny-gap'></div>", unsafe_allow_html=True)
    image_col, info_col = st.columns([1.28, 1], gap="large")
    with image_col:
        render_poster(event, key=event["id"], variant="hero")
    with info_col:
        st.markdown(
            f"""
            <div class="detail-summary">
              <span class="event-category">{eyebrow}</span>
              <h2>{title}</h2>
              <p class="venue-line">{venue}</p>
              <div class="detail-rule"></div>
              <div class="detail-key"><span>WHEN</span><b>{event_date}<br>{event_time}</b></div>
              <div class="detail-key"><span>ENTRY FROM</span><b>{currency(event.get('price', 0))}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(
            "Choose your seats",
            key="select_seats",
            type="primary",
            icon=":material/event_seat:",
            width="stretch",
        ):
            go(
                "seats",
                selected_seats=[],
                reservation_id=None,
                lock_expires_at=None,
                booking=None,
                payment_idempotency_key=None,
                payment_attempt_signature=None,
            )
    description_col, info_col = st.columns([1.28, 1], gap="large")
    with description_col:
        st.markdown(f"<div class='content-section'><div class='section-kicker'>ABOUT THE EVENT</div><h2>Made for a memorable evening.</h2><p>{description}</p></div>", unsafe_allow_html=True)
    with info_col:
        st.markdown(
            f"""
            <div class="info-list"><div class="section-kicker">EVENT INFORMATION</div>
            <div><span>Category</span><b>{category}</b></div>
            <div><span>Date</span><b>{event_date}</b></div><div><span>Time</span><b>{event_time}</b></div>
            <div><span>Venue</span><b>{venue}</b></div><div><span>Price</span><b>From {currency(event.get('price', 0))}</b></div></div>
            """,
            unsafe_allow_html=True,
        )
