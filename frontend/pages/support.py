import streamlit as st

from frontend.data.dummy_data import SUPPORT_ANSWERS


SUGGESTIONS = [
    ("How do I cancel my booking?", "cancel"),
    ("Which seats are available?", "seats"),
    ("Where can I find my booking?", "booking"),
    ("Can I change my seat?", "seat"),
]


def _reply_for(text):
    lowered = text.lower()
    if "cancel" in lowered:
        return SUPPORT_ANSWERS["cancel"]
    if "seat" in lowered or "available" in lowered:
        return SUPPORT_ANSWERS["seats"] if "available" in lowered else SUPPORT_ANSWERS["seat"]
    if "booking" in lowered or "find" in lowered:
        return SUPPORT_ANSWERS["booking"]
    return "I can help with bookings, seating and cancellation. Try one of the suggested questions, or ask about your reservation."


def _append_exchange(message):
    st.session_state.support_messages.extend([
        {"role": "user", "content": message},
        {"role": "assistant", "content": _reply_for(message)},
    ])


def render():
    st.markdown("<div class='page-intro compact'><span class='eyebrow'>WE'RE HERE TO HELP</span><h1>FlashReserve Support</h1><p>Questions about your booking? Start with a quick answer below.</p></div>", unsafe_allow_html=True)
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
