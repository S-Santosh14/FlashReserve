import streamlit as st

from frontend.components.event_card import render_event_card
from frontend.utils.api import APIError, get_events
from frontend.utils.navigation import breadcrumb, page_header


def render():
    try:
        events = get_events()
    except APIError as error:
        st.error(error.message)
        return
    st.session_state.events = events
    categories = ["All"] + sorted({event["category"] for event in events if event.get("category")})
    if st.session_state.event_category not in categories:
        st.session_state.event_category = "All"
    page_header("WHAT'S ON", "Explore events", "Good plans are closer than you think.", "← Home", "home", "🏠 Home", "home")
    breadcrumb(["Home", "Events"])
    search_col, _ = st.columns([3.2, 1.8])
    with search_col:
        query = st.text_input("Search events", placeholder="Search events, artists, venues…", key="events_search", label_visibility="collapsed")
    st.markdown("<div class='filter-label'>CATEGORY</div>", unsafe_allow_html=True)
    category_columns = st.columns(len(categories), gap="small")
    for col, category in zip(category_columns, categories):
        with col:
            if st.button(category, key=f"events_category_{category}", type="primary" if st.session_state.event_category == category else "secondary", use_container_width=True):
                st.session_state.event_category = category
                st.rerun()
    filters = st.columns(3)
    with filters[0]:
        st.selectbox("Date", ["Any date", "This week", "This month"], label_visibility="collapsed")
    with filters[1]:
        st.selectbox("Location", ["Hyderabad", "All locations", "Delhi", "Pilani"], label_visibility="collapsed")
    with filters[2]:
        st.selectbox("Price", ["Any price", "Under ₹500", "₹500 – ₹700"], label_visibility="collapsed")
    category = st.session_state.event_category
    matches = [item for item in events if category == "All" or item["category"] == category]
    if query:
        query = query.casefold()
        matches = [item for item in matches if query in f"{item['title']} {item['venue']} {item.get('city', '')}".casefold()]
    st.markdown(f"<div class='result-count'>{len(matches)} experiences available</div>", unsafe_allow_html=True)
    for index in range(0, len(matches), 3):
        columns = st.columns(3, gap="medium")
        for col, event in zip(columns, matches[index : index + 3]):
            with col:
                render_event_card(event, key_prefix="explore")
