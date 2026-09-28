import streamlit as st


def render_footer():
    st.markdown(
        """
        <footer class="site-footer">
          <div><div class="footer-brand">FLASHRESERVE</div><p>Reserve in seconds. Experience more.</p></div>
          <div class="footer-links"><span>Explore</span><span>Events</span><span>Support</span><span>My bookings</span></div>
          <div class="footer-copy">© 2026 FlashReserve</div>
        </footer>
        """,
        unsafe_allow_html=True,
    )
