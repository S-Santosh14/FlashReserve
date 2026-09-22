import streamlit as st

from frontend.data.dummy_data import SOLD_SEATS


def render_seat_map():
    """Native buttons provide real, stateful seat controls without custom JS."""
    selected = st.session_state.selected_seats
    st.markdown("<div class='screen-label'>STAGE</div><div class='screen-line'></div>", unsafe_allow_html=True)
    for row in "ABCDE":
        seat_columns = st.columns([0.35, 1, 1, 1, 0.26, 1, 1, 1], gap="small")
        with seat_columns[0]:
            st.markdown(f"<div class='row-label'>{row}</div>", unsafe_allow_html=True)
        positions = [1, 2, 3, 5, 6, 7]
        for number, col_index in zip(range(1, 7), positions):
            seat = f"{row}{number}"
            with seat_columns[col_index]:
                sold = seat in SOLD_SEATS
                selected_now = seat in selected
                if st.button(
                    seat,
                    key=f"seat_{seat}",
                    disabled=sold,
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
        <span><i class="seat-swatch sold"></i>Sold</span></div>
        """,
        unsafe_allow_html=True,
    )
