import hashlib
import html
import logging
import uuid
from datetime import datetime

import streamlit as st

from frontend.utils.chat_tasks import discard_chat_task, get_chat_result, submit_chat
from frontend.utils.navigation import breadcrumb, page_header
from frontend.utils.session import currency, go


_logger = logging.getLogger(__name__)


SUGGESTIONS = [
    "Where can I find my booking?",
    "How do I cancel my booking?",
    "How does payment work?",
    "Which seats are available?",
]


def _owner_key():
    user = st.session_state.user or {}
    user_id = user.get("_id") or user.get("id")
    if user_id:
        return str(user_id)
    token = st.session_state.auth_token or ""
    return hashlib.sha256(token.encode()).hexdigest() if token else "signed-out"


def _history_before(messages, end_index=None):
    history = []
    for message in messages[:end_index]:
        if message.get("status") == "error" or not message.get("content"):
            continue
        if message.get("role") in ("user", "assistant"):
            history.append({"role": message["role"], "content": message["content"]})
    return history[-8:]


def _queue_question(question, user_index=None):
    if st.session_state.support_pending:
        return

    messages = st.session_state.support_messages
    if user_index is None:
        history = _history_before(messages)
        messages.append({
            "role": "user",
            "content": question,
            "timestamp": datetime.now().astimezone().isoformat(),
        })
        user_index = len(messages) - 1
        messages.append({
            "role": "assistant",
            "content": "",
            "timestamp": datetime.now().astimezone().isoformat(),
            "status": "pending",
        })
    else:
        history = _history_before(messages, user_index)
        assistant_index = user_index + 1
        messages[assistant_index].update({
            "content": "",
            "timestamp": datetime.now().astimezone().isoformat(),
            "status": "pending",
            "error": None,
            "data": None,
        })

    assistant_index = user_index + 1
    task_id = str(uuid.uuid4())
    st.session_state.support_pending = {
        "task_id": task_id,
        "assistant_index": assistant_index,
    }
    st.session_state.support_scroll_latest = True
    try:
        selected_event = st.session_state.selected_event
        event_id = selected_event.get("id") if isinstance(selected_event, dict) else selected_event
        submit_chat(
            task_id,
            question,
            st.session_state.auth_token,
            event_id,
            history,
        )
    except Exception as error:
        st.session_state.support_pending = None
        messages[assistant_index].update({
            "status": "error",
            "error": "Support could not start this request. Please try again.",
        })
        st.session_state.support_focus_input = True
        _logger.exception("Support request could not be queued (%s).", type(error).__name__)


def _complete_pending_request():
    pending = st.session_state.support_pending
    if not pending:
        return
    result = get_chat_result(pending["task_id"])
    if result is None:
        return

    assistant = st.session_state.support_messages[pending["assistant_index"]]
    st.session_state.support_pending = None
    st.session_state.support_focus_input = True
    st.session_state.support_scroll_latest = True
    if result.get("error"):
        assistant.update({"status": "error", "error": result["error"]})
        return True

    data = result.get("data")
    response = data.get("response") if isinstance(data, dict) else None
    if not isinstance(response, str) or not response.strip():
        assistant.update({
            "status": "error",
            "error": "Support returned an incomplete response. Please retry.",
        })
        return True
    assistant.update({"status": "complete", "content": response, "data": data})
    return True


def _render_booking_cards(bookings):
    for booking in bookings:
        if not isinstance(booking, dict):
            continue
        with st.container(border=True):
            event, status = st.columns([3, 1])
            with event:
                st.markdown(f"**{html.escape(str(booking.get('event') or 'Event'))}**")
            with status:
                st.caption(str(booking.get("status") or "Status unavailable").capitalize())
            st.caption(f"Reference: {booking.get('reference') or 'Unavailable'}")
            details = []
            if booking.get("date"):
                details.append(str(booking["date"])[:10])
            if booking.get("time"):
                details.append(str(booking["time"]))
            if booking.get("venue"):
                details.append(str(booking["venue"]))
            if details:
                st.caption(" · ".join(details))
            seats = booking.get("seats") or []
            st.write(f"Seats: {', '.join(str(seat) for seat in seats) if seats else 'Unavailable'}")
            amount = booking.get("amount")
            if isinstance(amount, (int, float)):
                st.write(f"**{currency(amount)}**")
            if booking.get("paymentStatus"):
                st.caption(f"Payment: {str(booking['paymentStatus']).capitalize()}")
            if booking.get("refundStatus"):
                st.caption(f"Refund: {str(booking['refundStatus']).capitalize()}")


def _render_seat_data(data):
    seats = data.get("seats") or []
    if not seats:
        return
    by_category = {}
    for seat in seats:
        if isinstance(seat, dict):
            by_category.setdefault(seat.get("category") or "Other", []).append(str(seat.get("number", "")))
    st.caption(f"{len(seats)} currently available")
    with st.expander("View available seats"):
        for category, numbers in by_category.items():
            st.markdown(f"**{html.escape(str(category))}** · {len(numbers)}")
            st.markdown(
                f"<div class='support-seat-list'>{html.escape(', '.join(numbers))}</div>",
                unsafe_allow_html=True,
            )


def _render_message(message, index):
    role = message.get("role")
    is_user = role == "user"
    with st.chat_message("user" if is_user else "assistant", avatar=":material/person:" if is_user else ":material/support_agent:"):
        if is_user:
            st.write(message.get("content", ""))
        elif message.get("status") == "pending":
            st.markdown(":shimmer[FlashReserve is typing…]")
        else:
            if message.get("content"):
                st.write(message["content"])
            data = message.get("data") or {}
            if data.get("kind") == "bookings":
                _render_booking_cards(data.get("bookings") or [])
            elif data.get("kind") == "seats":
                _render_seat_data(data)
            if message.get("status") == "error":
                st.warning(message.get("error", "Support is temporarily unavailable."))
                if st.button("Retry", key=f"support_retry_{index}", icon=":material/replay:"):
                    _queue_question(st.session_state.support_messages[index - 1]["content"], index - 1)
                    st.rerun()

        timestamp = message.get("timestamp")
        if timestamp:
            try:
                time_label = datetime.fromisoformat(timestamp).astimezone().strftime("%I:%M %p")
            except (TypeError, ValueError):
                time_label = ""
            if time_label:
                st.caption(time_label)


def _render_conversation():
    for index, message in enumerate(st.session_state.support_messages):
        _render_message(message, index)
    st.markdown("<div id='support-chat-bottom'></div>", unsafe_allow_html=True)


@st.fragment(run_every=0.5)
def _poll_pending_request():
    if _complete_pending_request():
        st.rerun(scope="app")


def render():
    page_header(
        "WE'RE HERE TO HELP",
        "FlashReserve Support",
        "Real answers for bookings, payments, events, and seat availability.",
        "← Home",
        "home",
        "🏠 Home",
        "home",
    )
    breadcrumb(["Home", "Support"])

    owner = _owner_key()
    if st.session_state.support_owner != owner:
        pending = st.session_state.support_pending
        if pending:
            discard_chat_task(pending["task_id"])
        st.session_state.support_messages = []
        st.session_state.support_pending = None
        st.session_state.support_owner = owner

    action, clear = st.columns([1, 1])
    with action:
        if st.button("My bookings", icon=":material/confirmation_number:", width="stretch"):
            go("bookings")
    with clear:
        if st.button(
            "Clear chat",
            icon=":material/delete_sweep:",
            disabled=bool(st.session_state.support_pending),
            width="stretch",
        ):
            st.session_state.support_messages = []
            st.rerun()

    if not st.session_state.support_messages:
        st.markdown(
            "<div class='support-welcome'><span class='support-avatar'>FR</span><div><b>FlashReserve Support</b><p>Ask a question or choose a quick topic to get started.</p></div></div>",
            unsafe_allow_html=True,
        )
    else:
        if st.session_state.support_pending:
            _poll_pending_request()
        _render_conversation()

    if not st.session_state.support_messages:
        shortcut_columns = st.columns(2)
        for index, question in enumerate(SUGGESTIONS):
            with shortcut_columns[index % 2]:
                if st.button(
                    question,
                    key=f"support_suggestion_{index}",
                    disabled=bool(st.session_state.support_pending),
                    width="stretch",
                ):
                    _queue_question(question)
                    st.rerun()

    with st.container(key="support-composer"):
        with st.form("support_chat_form", clear_on_submit=True):
            input_col, button_col = st.columns([8, 1], vertical_alignment="center")

            with input_col:
                incoming = st.text_input(
                    "Message",
                    placeholder="Ask about a booking, event, payment, or seat...",
                    label_visibility="collapsed",
                    key="support_chat_draft",
                    disabled=bool(st.session_state.support_pending),
                )

            with button_col:
                submitted = st.form_submit_button(
                    "➤",
                    width="stretch",
                    disabled=bool(st.session_state.support_pending),
                )

    if submitted and incoming.strip():
        _queue_question(incoming.strip())
        st.rerun()

    should_focus = st.session_state.support_focus_input
    should_scroll = st.session_state.support_scroll_latest
    st.session_state.support_focus_input = False
    st.session_state.support_scroll_latest = False
    if should_focus or should_scroll:
        focus_value = "true" if should_focus else "false"
        st.html(
            f"""<script>
            requestAnimationFrame(() => {{
              document.getElementById("support-chat-bottom")?.scrollIntoView({{ behavior: "smooth", block: "end" }});
              if ({focus_value}) {{
                const input = document.querySelector(".st-key-support_chat_input textarea");
                if (input && !input.disabled) input.focus({{ preventScroll: true }});
              }}
            }});
            </script>""",
            unsafe_allow_javascript=True,
        )
