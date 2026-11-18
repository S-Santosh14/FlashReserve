import streamlit as st


import re


_SEAT_NUMBER = re.compile(r"^([A-Za-z]+)(\d+)$")


def _row_index(row):
    value = 0
    for character in row.upper():
        value = value * 26 + ord(character) - ord("A") + 1
    return value


def _seat_position(seat):
    seat_number = str(seat.get("seatNumber", ""))
    match = _SEAT_NUMBER.fullmatch(seat_number)
    if match:
        row = match.group(1).upper()
        return (0, _row_index(row), int(match.group(2)), seat_number)
    return (1, 0, 0, seat_number.lower())


def group_seats_by_row(seats):
    rows = {}
    for seat in seats:
        seat_number = str(seat.get("seatNumber", ""))
        match = _SEAT_NUMBER.fullmatch(seat_number)
        row = match.group(1).upper() if match else "Other"
        rows.setdefault(row, []).append(seat)
    return sorted(
        ((row, sorted(row_seats, key=_seat_position)) for row, row_seats in rows.items()),
        key=lambda item: (1, 0) if item[0] == "Other" else (0, _row_index(item[0])),
    )


def render_seat_map(seats, selected_seats=None, user_id="", reservation_id=None):
    """Render every API seat in its stored row, using atomic backend reservations."""
    selected = set(selected_seats or [])
    if not seats:
        st.info("No seats are configured for this event yet.")
        return

    st.markdown("<div class='screen-label'>STAGE / SCREEN</div><div class='screen-line'></div>", unsafe_allow_html=True)
    rows = group_seats_by_row(seats)
    for row, row_seats in rows:
        with st.container(horizontal=True, vertical_alignment="center", gap="small", key=f"seat-row-{row}"):
            st.markdown(f"<div class='row-label'>{row}</div>", unsafe_allow_html=True, width="content")
            aisle_after = len(row_seats) // 2
            for index, seat in enumerate(row_seats, start=1):
                if index == aisle_after + 1 and len(row_seats) > 2:
                    st.space("medium")

                seat_number = str(seat.get("seatNumber", ""))
                status = str(seat.get("status", "unavailable")).lower()
                seat_id = str(seat.get("_id") or seat_number)
                is_selected = seat_number in selected
                category = str(seat.get("category") or "Silver")
                is_owned_reservation = (
                    status == "reserved"
                    and str(seat.get("reservedBy") or "") == str(user_id)
                    and str(seat.get("reservationId") or "") == str(reservation_id or "")
                )
                disabled = status != "available" and not is_owned_reservation
                status_key = "booked" if status == "booked" else "reserved" if status == "reserved" else "available"
                help_text = f"{seat_number} · {category} · {status.replace('_', ' ').title()}"
                if is_owned_reservation:
                    help_text = f"{seat_number} · {category} · Held for you"
                if st.button(
                    seat_number,
                    key=f"seat-{status_key}-{seat_id}",
                    help=help_text,
                    disabled=disabled,
                    type="primary" if is_selected else "secondary",
                    width="content",
                ):
                    if seat_number in st.session_state.selected_seats:
                        st.session_state.selected_seats.remove(seat_number)
                    else:
                        st.session_state.selected_seats.append(seat_number)
                    st.rerun(scope="fragment")
    st.markdown(
        """
        <div class="seat-legend"><span><i class="seat-swatch available"></i>Available</span>
        <span><i class="seat-swatch selected"></i>Selected</span>
        <span><i class="seat-swatch reserved"></i>Reserved</span>
        <span><i class="seat-swatch sold"></i>Booked</span></div>
        """,
        unsafe_allow_html=True,
    )
