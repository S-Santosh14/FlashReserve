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
    st.markdown("<div class='tiny-gap'></div>", unsafe_allow_html=True)
    image_col, info_col = st.columns([1.28, 1], gap="large")
    with image_col:
        render_poster(event, key=event["id"])
    with info_col:
        st.markdown(
            f"""
            <div class="detail-summary">
              <span class="event-category">{event['eyebrow']}</span>
              <h2>{event['title']}</h2>
              <p class="venue-line">{event['venue']}</p>
              <div class="detail-rule"></div>
              <div class="detail-key"><span>WHEN</span><b>{event['date']}<br>{event['time']}</b></div>
              <div class="detail-key"><span>ENTRY FROM</span><b>{currency(event.get('price', 0))}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Select seats", key="select_seats", type="primary", use_container_width=True):
            go("seats", selected_seats=[])
    description_col, info_col = st.columns([1.28, 1], gap="large")
    with description_col:
        st.markdown(f"<div class='content-section'><div class='section-kicker'>ABOUT THE EVENT</div><h2>Made for a memorable evening.</h2><p>{event['description']}</p></div>", unsafe_allow_html=True)
    with info_col:
        st.markdown(
            f"""
            <div class="info-list"><div class="section-kicker">EVENT INFORMATION</div>
            <div><span>Date</span><b>{event['date']}</b></div><div><span>Time</span><b>{event['time']}</b></div>
            <div><span>Venue</span><b>{event['venue']}</b></div><div><span>Price</span><b>From {currency(event.get('price', 0))}</b></div></div>
            """,
            unsafe_allow_html=True,
        )
