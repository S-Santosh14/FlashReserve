from html import escape

import streamlit as st

from frontend.components.event_card import render_event_card
from frontend.components.poster import render_poster
from frontend.utils.api import APIError, get_bookings, get_events
from frontend.utils.session import currency, go


def _category_strip(categories):
    st.pills(
        "Browse by interest",
        categories,
        selection_mode="single",
        key="event_category",
        label_visibility="collapsed",
    )


def render():
    user = st.session_state.get("user") or {}
    display_name = escape(
        str(user.get("name") or st.session_state.get("username") or "there").split()[0]
    )
    st.markdown(
        f"""
        <section class="hero home-hero">
          <div class="eyebrow">YOUR NEXT GREAT NIGHT STARTS HERE</div>
          <h1>Good evening, {display_name}.<br><em>Make it memorable.</em></h1>
          <p>Find live music, theatre, sport, comedy and more — then make the night yours.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    try:
        events = get_events()
    except APIError as error:
        st.error(error.message)
        return
    st.session_state.events = events

    try:
        bookings = get_bookings(st.session_state.auth_token)
        st.session_state.bookings = bookings
        bookings_available = True
    except APIError as error:
        bookings = []
        bookings_available = False
        booking_error = error.message
    else:
        booking_error = None

    spotlight = next(
        (
            event
            for event in events
            if event.get("featured") or event.get("isFeatured")
        ),
        events[0] if events else None,
    )
    if spotlight:
        with st.container(border=True, key="home-featured"):
            poster_col, details_col = st.columns(
                [1.15, 1],
                gap="large",
                vertical_alignment="center",
            )
            with poster_col:
                render_poster(
                    spotlight,
                    key=f"home-featured-{spotlight['id']}",
                    variant="hero",
                )
            with details_col:
                category = escape(str(spotlight.get("category") or "Live event"))
                title = escape(str(spotlight.get("title") or "Untitled event"))
                date_label = escape(str(spotlight.get("short_date") or "Date to be announced"))
                time_label = escape(str(spotlight.get("time") or "Time to be announced"))
                venue = escape(
                    str(spotlight.get("city") or spotlight.get("venue") or "Venue to be announced")
                )
                st.markdown(
                    f"""
                    <div class="home-featured-copy">
                      <div class="section-kicker">SPOTLIGHT FROM THE LIVE LINE-UP</div>
                      <div class="event-category">{category}</div>
                      <h2>{title}</h2>
                      <p>{date_label} · {time_label}<br>{venue}</p>
                      <div class="home-featured-price">Tickets from <strong>{currency(spotlight.get('price', 0))}</strong></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(
                    "Discover this event",
                    key="home_featured_event",
                    type="primary",
                    icon=":material/arrow_forward:",
                    width="stretch",
                ):
                    go(
                        "event_details",
                        selected_event=spotlight["id"],
                        selected_seats=[],
                    )
    else:
        st.markdown(
            "<div class='empty-state home-empty'>New experiences are on their way. Check back soon.</div>",
            unsafe_allow_html=True,
        )

    categories = ["All"] + sorted(
        {event["category"] for event in events if event.get("category")}
    )
    if st.session_state.event_category not in categories:
        st.session_state.event_category = "All"

    search_col, shortcut_col = st.columns(
        [2.4, 1],
        vertical_alignment="bottom",
        gap="medium",
    )
    with search_col:
        search = st.text_input(
            "Search experiences",
            placeholder="Search events, artists, venues…",
            key="home_search",
            label_visibility="collapsed",
        )
    with shortcut_col:
        if st.button(
            "Explore all events",
            key="browse_events",
            icon=":material/explore:",
            width="stretch",
        ):
            go("events")

    _category_strip(categories)
    active = st.session_state.event_category
    filtered = [
        event
        for event in events
        if active == "All" or event["category"] == active
    ]
    if search:
        query = search.casefold()
        filtered = [
            event
            for event in filtered
            if query
            in f"{event['title']} {event['venue']} {event.get('city', '')}".casefold()
        ]
    st.markdown(
        f"<div class='section-head'><h2>Find your next experience</h2>"
        f"<span>{len(filtered)} events match your interests</span></div>",
        unsafe_allow_html=True,
    )
    displayed = filtered[:6]
    if not displayed:
        st.markdown(
            "<div class='empty-state'>No events match your search.</div>",
            unsafe_allow_html=True,
        )
    for row_start in range(0, len(displayed), 3):
        cols = st.columns(3, gap="medium")
        for col, event in zip(cols, displayed[row_start : row_start + 3]):
            with col:
                render_event_card(event, key_prefix="home")

    confirmed = sum(booking.get("status") == "Confirmed" for booking in bookings)
    upcoming = sum(booking.get("status") == "Pending" for booking in bookings)
    metric_events, metric_bookings, metric_upcoming = st.columns(3)
    metric_events.metric("Events to explore", len(events))
    metric_bookings.metric(
        "Confirmed bookings",
        confirmed if bookings_available else "Unavailable",
    )
    metric_upcoming.metric(
        "Awaiting payment",
        upcoming if bookings_available else "Unavailable",
    )
    if booking_error:
        st.caption(f"Booking activity could not be refreshed: {booking_error}")

    if bookings:
        st.markdown(
            "<div class='section-head'><h2>Your recent plans</h2>"
            "<span>Bookings connected to your account</span></div>",
            unsafe_allow_html=True,
        )
        for booking in bookings[:2]:
            event = booking.get("event") or {}
            with st.container(border=True):
                title, status = st.columns([3, 1], vertical_alignment="center")
                with title:
                    st.markdown(
                        f"**{escape(str(event.get('title') or 'FlashReserve booking'))}**"
                    )
                    st.caption(
                        f"{escape(str(event.get('short_date') or event.get('date') or ''))} · "
                        f"{escape(str(event.get('venue') or ''))}"
                    )
                with status:
                    st.badge(str(booking.get("status", "Unknown")))
                if st.button(
                    "View booking",
                    key=f"home_booking_{booking.get('id', '')}",
                    icon=":material/confirmation_number:",
                ):
                    go("booking_details", selected_booking_id=booking["id"])
    st.markdown(
        "<div class='editorial-note'><span>MADE FOR THE MOMENT</span>"
        "<p>Choose your seats. Bring your people. Be there.</p>"
        "<small>Every good plan deserves a great start.</small></div>",
        unsafe_allow_html=True,
    )
