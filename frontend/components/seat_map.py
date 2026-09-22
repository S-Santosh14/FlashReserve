import streamlit as st


def render_seat_map(seats):
    """Native buttons provide real, stateful seat controls without custom JS."""
    selected = st.session_state.selected_seats
    st.markdown("<div class='screen-label'>STAGE</div><div class='screen-line'></div>", unsafe_allow_html=True)
    seat_by_number = {seat["seatNumber"]: seat for seat in seats}
    rows = sorted({seat_number.rstrip("0123456789") or "A" for seat_number in seat_by_number})
    for row in rows:
        seat_columns = st.columns([0.35, 1, 1, 1, 0.26, 1, 1, 1], gap="small")
        with seat_columns[0]:
            st.markdown(f"<div class='row-label'>{row}</div>", unsafe_allow_html=True)
        positions = [1, 2, 3, 5, 6, 7]
        row_seats = sorted((seat for seat in seat_by_number if seat.startswith(row)), key=lambda value: int(value[len(row):] or 0))
        for seat, col_index in zip(row_seats, positions):
            with seat_columns[col_index]:
                unavailable = seat_by_number[seat]["status"] != "available"
                selected_now = seat in selected
                if st.button(
                    seat,
                    key=f"seat_{seat}",
                    disabled=unavailable,
                    type="primary" if selected_now else "secondary",
                    use_container_width=True,
                ):
                    if seat in st.session_state.selected_seats:
                        st.session_state.selected_seats.remove(seat)
                    else:
                        st.session_state.selected_seats.append(seat)
                    st.rerun()
    st.markdown(
        """
        <div class="seat-legend"><span><i class="seat-swatch available"></i>Available</span>
        <span><i class="seat-swatch selected"></i>Selected</span>
        <span><i class="seat-swatch reserved"></i>Reserved</span>
        <span><i class="seat-swatch sold"></i>Booked</span></div>
        """,
        unsafe_allow_html=True,
    )
