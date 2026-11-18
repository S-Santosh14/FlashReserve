from datetime import date, datetime, timedelta

import streamlit as st

from frontend.components.event_card import render_event_card
from frontend.utils.api import APIError, get_events
from frontend.utils.navigation import breadcrumb, page_header


def _event_date(event):
    value = str(event.get("raw_date") or event.get("date") or "").strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        try:
            return datetime.strptime(value, "%d %B %Y").date()
        except ValueError:
            return None


def _filter_events(
    events,
    query="",
    category="All",
    location="All locations",
    price="Any price",
    date_filter="Any date",
    sort_by="Soonest",
    today=None,
):
    today = today or date.today()
    filtered = []
    for event in events:
        if category != "All" and event.get("category") != category:
            continue
        city = str(event.get("city") or event.get("venue") or "")
        if location != "All locations" and city != location:
            continue
        event_price = float(event.get("price") or 0)
        if price == "Under ₹500" and event_price >= 500:
            continue
        if price == "₹500 – ₹700" and not 500 <= event_price <= 700:
            continue
        if price == "Over ₹700" and event_price <= 700:
            continue
        event_date = _event_date(event)
        if date_filter != "Any date":
            if event_date is None:
                continue
            if date_filter == "This week":
                week_start = today - timedelta(days=today.weekday())
                week_end = week_start + timedelta(days=6)
                if not week_start <= event_date <= week_end:
                    continue
            elif date_filter == "This month":
                if (event_date.year, event_date.month) != (today.year, today.month):
                    continue
        searchable = " ".join(
            str(event.get(field) or "")
            for field in ("title", "category", "venue", "city", "description")
        ).casefold()
        if query and query.casefold() not in searchable:
            continue
        filtered.append((event, event_date))

    if sort_by == "Soonest":
        filtered.sort(key=lambda item: (item[1] is None, item[1] or date.max))
    elif sort_by == "Latest":
        with_date = [item for item in filtered if item[1] is not None]
        without_date = [item for item in filtered if item[1] is None]
        filtered = sorted(with_date, key=lambda item: item[1], reverse=True) + without_date
    elif sort_by == "Price: low to high":
        filtered.sort(key=lambda item: float(item[0].get("price") or 0))
    elif sort_by == "Price: high to low":
        filtered.sort(key=lambda item: float(item[0].get("price") or 0), reverse=True)
    return [event for event, _event_day in filtered]


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

    page_header(
        "THE CITY IS YOURS",
        "Explore events",
        "Find the live moments, new voices, and nights worth getting out for.",
        "← Home",
        "home",
        ":material/home: Home",
        "home",
    )
    breadcrumb(["Home", "Events"])

    query_col, date_col = st.columns([2.2, 1], vertical_alignment="bottom")
    with query_col:
        query = st.text_input(
            "Search events",
            placeholder="Search events, artists, venues…",
            key="events_search",
        )
    with date_col:
        date_filter = st.selectbox("When", ["Any date", "This week", "This month"])

    category = st.pills(
        "Category",
        categories,
        selection_mode="single",
        key="event_category",
        label_visibility="collapsed",
    )
    locations = ["All locations"] + sorted({
        str(event.get("city") or event.get("venue"))
        for event in events
        if event.get("city") or event.get("venue")
    })
    filters = st.columns(3)
    with filters[0]:
        location = st.selectbox("Location", locations)
    with filters[1]:
        price = st.selectbox(
            "Price",
            ["Any price", "Under ₹500", "₹500 – ₹700", "Over ₹700"],
        )
    with filters[2]:
        sort_by = st.selectbox(
            "Sort by",
            ["Soonest", "Latest", "Price: low to high", "Price: high to low"],
        )

    matches = _filter_events(
        events,
        query=query.strip(),
        category=category or "All",
        location=location,
        price=price,
        date_filter=date_filter,
        sort_by=sort_by,
    )
    st.markdown(
        f"<div class='result-count'>{len(matches)} "
        f"{'experience' if len(matches) == 1 else 'experiences'} to discover</div>",
        unsafe_allow_html=True,
    )
    if not matches:
        st.markdown(
            "<div class='empty-state'>No events match these filters. Try widening your search.</div>",
            unsafe_allow_html=True,
        )
        return
    for index in range(0, len(matches), 3):
        columns = st.columns(3, gap="medium")
        for column, event in zip(columns, matches[index : index + 3]):
            with column:
                render_event_card(event, key_prefix="explore")
