import streamlit as st

from frontend.data.dummy_data import get_event
from frontend.utils.session import currency, go


def render():
    event = get_event(st.session_state.selected_event)
    if st.button("← Back to events", key="back_from_detail"):
        go("events")
    st.markdown("<div class='tiny-gap'></div>", unsafe_allow_html=True)
    image_col, info_col = st.columns([1.28, 1], gap="large")
    with image_col:
        st.image(event["image"], use_container_width=True)
    with info_col:
        st.markdown(
            f"""
            <div class="detail-summary">
              <span class="event-category">{event['eyebrow']}</span>
              <h1>{event['title']}</h1>
              <p class="venue-line">{event['venue']}</p>
              <div class="detail-rule"></div>
              <div class="detail-key"><span>WHEN</span><b>{event['date']}<br>{event['time']}</b></div>
              <div class="detail-key"><span>ENTRY FROM</span><b>{currency(event['price'])}</b></div>
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
            <div><span>Venue</span><b>{event['venue']}</b></div><div><span>Price</span><b>From {currency(event['price'])}</b></div></div>
            """,
            unsafe_allow_html=True,
        )
