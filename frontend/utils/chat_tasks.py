"""Background customer-support requests for the Streamlit chat UI."""

from concurrent.futures import Future, ThreadPoolExecutor
import logging
import threading

from frontend.utils.api import APIError, ask_chat


_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="flashreserve-chat")
_tasks: dict[str, Future] = {}
_tasks_lock = threading.Lock()
_logger = logging.getLogger(__name__)


def _request_chat(message, token, event_id, history):
    try:
        return {"data": ask_chat(message, token, event_id, history)}
    except APIError as error:
        return {"error": error.message}
    except Exception:
        _logger.exception("Unexpected error while requesting customer support.")
        return {"error": "Support is temporarily unavailable. Please try again."}


def submit_chat(task_id, message, token, event_id, history):
    with _tasks_lock:
        if task_id in _tasks:
            raise ValueError("A chat task with this id already exists.")
        _tasks[task_id] = _executor.submit(_request_chat, message, token, event_id, history)


def get_chat_result(task_id):
    with _tasks_lock:
        future = _tasks.get(task_id)
    if future is None or not future.done():
        return None
    try:
        return future.result()
    finally:
        with _tasks_lock:
            _tasks.pop(task_id, None)


def discard_chat_task(task_id):
    with _tasks_lock:
        future = _tasks.pop(task_id, None)
    if future:
        future.cancel()
