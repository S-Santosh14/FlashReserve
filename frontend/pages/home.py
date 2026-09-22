import streamlit as st

from frontend.components.event_card import render_event_card
from frontend.utils.api import APIError, get_events
from frontend.utils.session import go


def _category_strip(active, categories):
    columns = st.columns(len(categories), gap="small")
    for col, category in zip(columns, categories):
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
    try:
        events = get_events()
    except APIError as error:
        st.error(error.message)
        return
    st.session_state.events = events
    categories = ["All"] + sorted({event["category"] for event in events if event.get("category")})
    if st.session_state.event_category not in categories:
        st.session_state.event_category = "All"
    location, shortcut, _ = st.columns([1.35, 1.05, 4.3])
    with location:
        st.markdown("<div class='location-pill'>● &nbsp; Hyderabad</div>", unsafe_allow_html=True)
    with shortcut:
        if st.button("Browse all events", key="browse_events", use_container_width=True):
            go("events")
    st.markdown("<div class='section-spacer'></div><div class='section-kicker'>BROWSE BY INTEREST</div>", unsafe_allow_html=True)
    _category_strip(st.session_state.event_category, categories)
    active = st.session_state.event_category
    filtered = [event for event in events if active == "All" or event["category"] == active]
    if search:
        query = search.lower()
        filtered = [event for event in filtered if query in f"{event['title']} {event['venue']} {event.get('city', '')}".lower()]
    st.markdown("<div class='section-head'><h2>Recommended for you</h2><span>Handpicked in Hyderabad</span></div>", unsafe_allow_html=True)
    displayed = filtered[:4]
    if not displayed:
        st.markdown("<div class='empty-state'>No events match your search.</div>", unsafe_allow_html=True)
    for row_start in range(0, len(displayed), 4):
        cols = st.columns(4, gap="medium")
        for col, event in zip(cols, displayed[row_start : row_start + 4]):
            with col:
                render_event_card(event, key_prefix="home")
    st.markdown("<div class='editorial-note'><span>THIS WEEK</span><p>One tap to the moments you will remember.</p><small>Plans deserve a little less friction.</small></div>", unsafe_allow_html=True)
