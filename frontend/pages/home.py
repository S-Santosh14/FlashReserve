import streamlit as st

from frontend.components.event_card import render_event_card
from frontend.data.dummy_data import CATEGORIES, EVENTS
from frontend.utils.session import go


def _category_strip(active):
    columns = st.columns(len(CATEGORIES), gap="small")
    for col, category in zip(columns, CATEGORIES):
        with col:
            if st.button(category, key=f"home_category_{category}", type="primary" if category == active else "secondary", use_container_width=True):
                st.session_state.event_category = category
                st.rerun()


def render():
    st.markdown(
        """
        <section class="hero">
          <div class="eyebrow">FIND A REASON TO GO OUT</div>
          <h1>Discover your next<br><em>experience.</em></h1>
          <p>Movies, concerts, sports, comedy and more — thoughtfully collected in one place.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    search = st.text_input("Search experiences", placeholder="Search events, artists, venues…", key="home_search", label_visibility="collapsed")
    location, shortcut, _ = st.columns([1.35, 1.05, 4.3])
    with location:
        st.markdown("<div class='location-pill'>● &nbsp; Hyderabad</div>", unsafe_allow_html=True)
    with shortcut:
        if st.button("Browse all events", key="browse_events", use_container_width=True):
            go("events")
    st.markdown("<div class='section-spacer'></div><div class='section-kicker'>BROWSE BY INTEREST</div>", unsafe_allow_html=True)
    _category_strip(st.session_state.event_category)
    active = st.session_state.event_category
    filtered = [event for event in EVENTS if active == "All" or event["category"] == active]
    if search:
        query = search.lower()
        filtered = [event for event in filtered if query in (event["title"] + event["venue"] + event["city"]).lower()]
    st.markdown("<div class='section-head'><h2>Recommended for you</h2><span>Handpicked in Hyderabad</span></div>", unsafe_allow_html=True)
    displayed = filtered[:4] if filtered else EVENTS[:4]
    for row_start in range(0, len(displayed), 4):
        cols = st.columns(4, gap="medium")
        for col, event in zip(cols, displayed[row_start : row_start + 4]):
            with col:
                render_event_card(event, key_prefix="home")
    st.markdown("<div class='editorial-note'><span>THIS WEEK</span><p>One tap to the moments you will remember.</p><small>Plans deserve a little less friction.</small></div>", unsafe_allow_html=True)
