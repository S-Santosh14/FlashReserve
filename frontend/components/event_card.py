import streamlit as st

from frontend.components.poster import render_poster
from frontend.utils.session import currency, go


def render_event_card(event, key_prefix="card"):
    st.markdown("<div class='event-card'>", unsafe_allow_html=True)
    render_poster(event, key=event.get("id", key_prefix))
    st.markdown(
        f"""
        <div class="event-card-copy">
          <div class="event-category">{event['category']}</div>
          <div class="event-title">{event['title']}</div>
          <div class="event-meta">{event['city']} &nbsp;·&nbsp; {event['short_date']} · {event['time']}</div>
          <div class="event-card-bottom"><span>From <b>{currency(event.get('price', 0))}</b></span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("View event  →", key=f"{key_prefix}_{event['id']}", use_container_width=True):
        go("event_details", selected_event=event["id"], selected_seats=[])
    st.markdown("</div>", unsafe_allow_html=True)
