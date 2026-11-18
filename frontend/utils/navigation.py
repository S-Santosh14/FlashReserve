from html import escape

import streamlit as st

from frontend.utils.session import go


def page_header(kicker, title, subtitle="", back_label=None, back_page=None, home_label=None, home_page=None):
    actions = []
    if back_label and back_page:
        actions.append((back_label, back_page, "nav_back"))
    if home_label and home_page:
        actions.append((home_label, home_page, "nav_home"))
    if actions:
        with st.container(horizontal=True, wrap=True, vertical_alignment="center"):
            for label, page, key_prefix in actions:
                icon = ":material/home:" if label.startswith("🏠") else None
                if label.startswith("🏠"):
                    label = label[1:].strip()
                if st.button(
                    label,
                    key=f"{key_prefix}_{title}",
                    icon=icon,
                ):
                    go(page)
    st.markdown(
        f"<div class='page-intro'><span class='eyebrow'>{escape(str(kicker))}</span>"
        f"<h1>{escape(str(title))}</h1><p>{escape(str(subtitle))}</p></div>",
        unsafe_allow_html=True,
    )


def breadcrumb(items):
    st.markdown(
        "<div class='breadcrumb'>"
        + " <span>→</span> ".join(escape(str(item)) for item in items)
        + "</div>",
        unsafe_allow_html=True,
    )
