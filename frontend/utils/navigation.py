import streamlit as st

from frontend.utils.session import go


def page_header(kicker, title, subtitle="", back_label=None, back_page=None, home_label=None, home_page=None):
    actions = []
    if back_label and back_page:
        actions.append((back_label, back_page, "nav_back"))
    if home_label and home_page:
        actions.append((home_label, home_page, "nav_home"))
    if actions:
        columns = st.columns([1.2] * len(actions) + [4.5], gap="small")
        for column, (label, page, key_prefix) in zip(columns, actions):
            with column:
                if st.button(label, key=f"{key_prefix}_{title}", use_container_width=True):
                    go(page)
    st.markdown(
        f"<div class='page-intro'><span class='eyebrow'>{kicker}</span><h1>{title}</h1><p>{subtitle}</p></div>",
        unsafe_allow_html=True,
    )


def breadcrumb(items):
    st.markdown(
        "<div class='breadcrumb'>" + " <span>→</span> ".join(items) + "</div>",
        unsafe_allow_html=True,
    )
