import streamlit as st

from frontend.utils.api import APIError, ask_chat
from frontend.utils.navigation import breadcrumb, page_header


SUGGESTIONS = [
    ("How do I cancel my booking?", "cancel"),
    ("Which seats are available?", "seats"),
    ("Where can I find my booking?", "booking"),
    ("Can I change my seat?", "seat"),
]


def _append_exchange(message):
    try:
        result = ask_chat(message, st.session_state.auth_token, st.session_state.selected_event)
    except APIError as error:
        st.session_state.support_messages.extend([
            {"role": "user", "content": message},
            {"role": "assistant", "content": error.message},
        ])
    else:
        st.session_state.support_messages.extend([
            {"role": "user", "content": message},
            {"role": "assistant", "content": result["response"]},
        ])


def render():
    page_header("WE'RE HERE TO HELP", "FlashReserve Support", "Questions about your booking? Start with a quick answer below.", "← Home", "home", "🏠 Home", "home")
    breadcrumb(["Home", "Support"])
    #st.markdown("<div class='support-shell'>", unsafe_allow_html=True)
    if not st.session_state.support_messages:
        st.markdown("<div class='support-welcome'><span class='support-avatar'>FR</span><div><b>FlashReserve Support</b><p>We usually reply instantly in this prototype.</p></div></div>", unsafe_allow_html=True)
        for index, (label, _) in enumerate(SUGGESTIONS):
            if st.button(label, key=f"support_suggestion_{index}", use_container_width=True):
                _append_exchange(label)
                st.rerun()
    else:
        for message in st.session_state.support_messages:
            with st.chat_message("user" if message["role"] == "user" else "assistant"):
                st.write(message["content"])
    #st.markdown("</div>", unsafe_allow_html=True)
    incoming = st.chat_input("Write your question…")
    if incoming:
        _append_exchange(incoming)
        st.rerun()
