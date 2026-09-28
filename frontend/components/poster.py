import streamlit as st


def render_poster(event, key="poster", height=None):
    image = event.get("image") or event.get("poster_url")
    if image:
        try:
            st.image(image, use_container_width=True, output_format="auto")
            return
        except Exception:
            pass
    category = str(event.get("category", "LIVE EVENT")).upper()
    title = event.get("title", "FlashReserve")
    st.markdown(
        f"<div class='poster-fallback' data-poster='{key}'><span>{category}</span><strong>{title}</strong><small>FLASHRESERVE / LIVE EXPERIENCES</small></div>",
        unsafe_allow_html=True,
    )