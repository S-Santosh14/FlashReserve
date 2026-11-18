"""FlashReserve customer-support gRPC service backed by Groq when configured."""

import json
import os
from concurrent import futures
from pathlib import Path
import sys
import time

import grpc
from dotenv import load_dotenv
from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    Groq,
    InternalServerError,
    RateLimitError,
)


PROTO_DIR = Path(__file__).parent / "proto"
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH)
if str(PROTO_DIR) not in sys.path:
    sys.path.insert(0, str(PROTO_DIR))

import llm_pb2  # noqa: E402
import llm_pb2_grpc  # noqa: E402


SYSTEM_PROMPT = """You are the FlashReserve Customer Support Assistant.

FlashReserve is a distributed ticket booking system with a Streamlit frontend,
Python REST and gRPC services, MongoDB/PyMongo persistence, JWT authentication,
bcrypt password hashing, atomic seat reservation, mock payments, and this
Python gRPC support service.

Explain registration, login, event discovery, event creation, seat selection,
seat availability, bookings, cancellation, mock payments, confirmation, and
admin capabilities clearly and concisely. The backend context is the source of
truth for current events, prices, seats, bookings, and statuses. Never invent
dynamic values, expose secrets, passwords, JWTs, internal IDs, or credentials.
If the supplied context does not contain an answer, say that the information
is unavailable and direct the customer to the relevant FlashReserve page.
Do not claim that an action was completed unless the backend confirms it.
Only confirmed bookings can be cancelled. Customers cancel from My Bookings,
and the backend processes a mock refund; do not promise a refund amount or
completion time unless supplied by trusted backend context.
Conversation history is for conversational continuity only. It is not a source
of current booking, payment, event, or seat facts; rely on trusted backend
context for those facts.
"""


def provider_status():
    return {
        "configured": bool(os.getenv("GROQ_API_KEY")),
        "model": os.getenv(
            "GROQ_MODEL",
            os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
        ),
    }


def _context_data(raw_context):
    if not raw_context:
        return {}
    try:
        parsed = json.loads(raw_context)
    except (json.JSONDecodeError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _retryable_provider_error(error):
    if isinstance(error, (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError)):
        return True
    return isinstance(error, APIStatusError) and (
        error.status_code in (408, 409, 429) or error.status_code >= 500
    )


def _provider_attempts():
    try:
        retries = int(os.getenv("GROQ_MAX_RETRIES", "2"))
        timeout_ms = int(os.getenv("GROQ_TIMEOUT_MS", "8000"))
        backoff_ms = int(os.getenv("GROQ_RETRY_BACKOFF_MS", "250"))
    except ValueError as error:
        raise ValueError("Groq retry and timeout settings must be integers.") from error
    if not 0 <= retries <= 3:
        raise ValueError("GROQ_MAX_RETRIES must be between 0 and 3.")
    if timeout_ms <= 0 or backoff_ms < 0:
        raise ValueError("Groq timeout must be positive and retry backoff cannot be negative.")
    return retries, timeout_ms, backoff_ms


def answer_question(question, context=None):
    """Return an FAQ answer, using only supplied application context for dynamic facts."""
    text = question.strip().lower()
    data = context or {}

    asks_about_seats = any(word in text for word in ("seat", "seats"))
    asks_about_events = "event" in text or "events" in text
    if asks_about_seats:
        available = data.get("available_seats")
        if available is None:
            return "Seat availability is checked live when you select an event. Please open an event to view its current seats."
        if not available:
            return "There are no available seats for the selected event right now."
        return f"Available seats for the selected event: {', '.join(available)}."
    if "cancel" in text:
        return "Only confirmed bookings can be cancelled. Open My Bookings, select a confirmed booking, and choose Cancel booking. FlashReserve then processes a mock refund; check the booking details for its status."
    if any(word in text for word in ("book a ticket", "reserve a ticket", "reserve seats", "buy a ticket")):
        return "Open an event, choose available seats, continue to checkout, and complete the mock payment to confirm your booking."
    if "payment" in text or "pay" in text:
        return "FlashReserve uses a mock payment flow for this milestone. Your booking is confirmed after a successful mock payment."
    if asks_about_events:
        events = data.get("events", [])
        if events:
            return "Available events: " + "; ".join(f"{event.get('title', 'Event')} at {event.get('venue', 'the listed venue')}" for event in events) + "."
        return "Open Explore events to see the current event catalogue."
    if "booking" in text or "bookings" in text or "reservation" in text:
        bookings = data.get("bookings", [])
        if bookings:
            return "Your bookings: " + "; ".join(f"{booking.get('title', 'Event')} ({booking.get('status', 'pending')})" for booking in bookings) + "."
        return "Open My Bookings to view your reservations."
    return "I can help with booking tickets, seat availability, payments, events, bookings, and cancellation."


def _bounded_provider_timeout(timeout_ms, retries, backoff_ms):
    try:
        grpc_deadline_ms = int(os.getenv("LLM_GRPC_TIMEOUT_MS", "30000"))
    except ValueError as error:
        raise ValueError("LLM_GRPC_TIMEOUT_MS must be a positive integer.") from error
    if grpc_deadline_ms <= 0:
        raise ValueError("LLM_GRPC_TIMEOUT_MS must be a positive integer.")
    backoff_budget_ms = backoff_ms * ((2 ** retries) - 1)
    attempt_budget_ms = (grpc_deadline_ms - 1000 - backoff_budget_ms) // (retries + 1)
    if attempt_budget_ms <= 0:
        raise ValueError("The configured gRPC deadline is too short for the Groq retry policy.")
    return min(timeout_ms, attempt_budget_ms)


def generate_llm_response(question, context=None):
    status = provider_status()
    if not status["configured"]:
        raise RuntimeError("GROQ_API_KEY is missing from the project-root .env configuration.")

    retries, timeout_ms, backoff_ms = _provider_attempts()
    timeout_ms = _bounded_provider_timeout(timeout_ms, retries, backoff_ms)
    client = Groq(
        api_key=os.environ["GROQ_API_KEY"],
        timeout=timeout_ms / 1000,
        max_retries=0,
    )
    data = context if isinstance(context, dict) else {}
    conversation = data.get("conversation", [])
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if isinstance(conversation, list):
        messages.extend(
            {"role": item["role"], "content": item["content"][:1000]}
            for item in conversation[-8:]
            if isinstance(item, dict)
            and item.get("role") in ("user", "assistant")
            and isinstance(item.get("content"), str)
        )
    messages.append({
        "role": "user",
        "content": (
            f"Question: {question}\n\nTrusted backend context:\n"
            f"{json.dumps({key: value for key, value in data.items() if key != 'conversation'}, ensure_ascii=True)}"
        ),
    })

    for attempt in range(retries + 1):
        try:
            completion = client.chat.completions.create(
                model=status["model"],
                temperature=0.2,
                max_tokens=500,
                messages=messages,
            )
            response = completion.choices[0].message.content
            if not isinstance(response, str) or not response.strip():
                raise RuntimeError("The provider returned an empty response.")
            return response.strip()
        except Exception as error:
            if attempt >= retries or not _retryable_provider_error(error):
                raise
            time.sleep((backoff_ms / 1000) * (2 ** attempt))
    raise RuntimeError("The provider retry loop ended unexpectedly.")


def provider_error_status(error):
    status_code = getattr(error, "status_code", None)
    if status_code == 404 or getattr(error, "code", None) == "model_not_found":
        return "model_unavailable"
    if status_code in (401, 403):
        return "provider_authentication_failed"
    return "provider_unavailable"


def check_provider():
    status = provider_status()
    if not status["configured"]:
        raise RuntimeError("GROQ_API_KEY is missing from the project-root .env configuration.")
    _, timeout_ms, _ = _provider_attempts()
    client = Groq(
        api_key=os.environ["GROQ_API_KEY"],
        timeout=timeout_ms / 1000,
        max_retries=0,
    )
    return client.models.retrieve(status["model"])


class LLMService(llm_pb2_grpc.LLMServiceServicer):
    def AskQuestion(self, request, _context):
        try:
            response = generate_llm_response(request.text, _context_data(request.context))
        except (
            APIConnectionError,
            APIStatusError,
            APITimeoutError,
            RateLimitError,
            RuntimeError,
        ) as error:
            status = provider_error_status(error)
            print(f"LLM provider request failed (type={type(error).__name__}, status={getattr(error, 'status_code', 'unavailable')}, category={status}).")
            response = answer_question(request.text, _context_data(request.context))
            return llm_pb2.Answer(response=response, success=True, status="fallback")
        return llm_pb2.Answer(response=response, success=True, status="ok")


def serve():
    host = os.getenv("LLM_GRPC_HOST", "127.0.0.1")
    port = os.getenv("LLM_GRPC_PORT", "50060")
    status = provider_status()
    if status["configured"]:
        print(f"Groq provider configured; model: {status['model']}")
    else:
        print("GROQ_API_KEY is missing from the project-root .env configuration.")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    llm_pb2_grpc.add_LLMServiceServicer_to_server(LLMService(), server)
    if not server.add_insecure_port(f"{host}:{port}"):
        raise RuntimeError(f"Unable to bind the support gRPC service to {host}:{port}.")
    server.start()
    print(f"FlashReserve LLM gRPC service listening on {host}:{port}")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(grace=2)


if __name__ == "__main__":
    if sys.argv[1:] == ["--check-provider"]:
        try:
            model = check_provider()
        except Exception as error:
            category = provider_error_status(error)
            print(
                f"Groq provider check failed (type={type(error).__name__}, "
                f"status={getattr(error, 'status_code', 'unavailable')}, category={category})."
            )
            raise SystemExit(1) from None
        print(f"Groq credentials accepted; configured model is available ({model.id}).")
    else:
        serve()