import streamlit as st


def render_seat_map(seats):
    """Render all seats in a clean theatre-style layout."""

    selected = st.session_state.selected_seats

    st.markdown(
        "<div class='screen-label'>STAGE</div>"
        "<div class='screen-line'></div>",
        unsafe_allow_html=True,
    )

    seat_by_number = {
        seat["seatNumber"]: seat
        for seat in seats
    }
    def seat_number_key(seat_number):
        prefix = "".join(
            character for character in seat_number
            if not character.isdigit()
        )
        number = "".join(
            character for character in seat_number
            if character.isdigit()
        )
        return prefix, int(number or 0)

    sorted_seats = sorted(
        seat_by_number.keys(),
        key=seat_number_key,
    )

    seats_per_row = 8

    for row_index in range(0, len(sorted_seats), seats_per_row):

        row_seats = sorted_seats[
            row_index:row_index + seats_per_row
        ]

        row_number = row_index // seats_per_row
        row_label = chr(ord("A") + row_number)

        seat_columns = st.columns(
            [
                0.35,
                1,
                1,
                1,
                1,
                0.35,
                1,
                1,
                1,
                1,
            ],
            gap="small",
        )

        with seat_columns[0]:
            st.markdown(
                f"<div class='row-label'>{row_label}</div>",
                unsafe_allow_html=True,
            )

        positions = [1, 2, 3, 4, 6, 7, 8, 9]

        for seat, col_index in zip(row_seats, positions):

            with seat_columns[col_index]:

                seat_data = seat_by_number[seat]

                unavailable = (
                    seat_data["status"] != "available"
                )

                selected_now = seat in selected

                if st.button(
                    seat,
                    key=f"seat_{seat}",
                    disabled=unavailable,
                    type="primary"
                    if selected_now
                    else "secondary",
                    use_container_width=True,
                ):
                    if seat in st.session_state.selected_seats:
                        st.session_state.selected_seats.remove(seat)
                    else:
                        st.session_state.selected_seats.append(seat)

                    st.rerun()

    st.markdown(
        """
        <div class="seat-legend">
            <span>
                <i class="seat-swatch available"></i>
                Available
            </span>
            <span>
                <i class="seat-swatch selected"></i>
                Selected
            </span>
            <span>
                <i class="seat-swatch reserved"></i>
                Reserved
            </span>
            <span>
                <i class="seat-swatch sold"></i>
                Booked
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )