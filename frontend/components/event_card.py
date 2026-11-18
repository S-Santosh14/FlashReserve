from html import escape

import streamlit as st

from frontend.components.poster import render_poster
from frontend.utils.session import currency, go


def render_event_card(event, key_prefix="card"):
    event_id = str(event.get("id", ""))
    with st.container(key=f"event-card-{key_prefix}-{event_id}"):
        render_poster(event, key=event_id or key_prefix, variant="card")
        st.markdown(
            f"""
            <div class="event-card-copy">
              <div class="event-category">{escape(str(event.get('category') or 'Live event'))}</div>
              <div class="event-title">{escape(str(event.get('title') or 'Untitled event'))}</div>
              <div class="event-meta">{escape(str(event.get('city') or event.get('venue') or ''))}
                &nbsp;·&nbsp; {escape(str(event.get('short_date') or 'Date to be announced'))}
                · {escape(str(event.get('time') or 'Time to be announced'))}</div>
              <div class="event-card-bottom"><span>From <b>{currency(event.get('price', 0))}</b></span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(
            "View event",
            key=f"{key_prefix}_{event_id}",
            icon=":material/arrow_forward:",
            width="stretch",
        ):
            go("event_details", selected_event=event_id, selected_seats=[])
