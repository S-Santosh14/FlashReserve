"""FlashReserve customer-support gRPC service backed by Groq when configured."""

import json
import os
from concurrent import futures
from pathlib import Path
import sys

import grpc
from dotenv import load_dotenv
from groq import Groq


PROTO_DIR = Path(__file__).parent / "proto"
ENV_PATH = Path(__file__).resolve().parent.parent / "backend" / ".env"
load_dotenv(dotenv_path=ENV_PATH)
if str(PROTO_DIR) not in sys.path:
    sys.path.insert(0, str(PROTO_DIR))

import llm_pb2  # noqa: E402
import llm_pb2_grpc  # noqa: E402


SYSTEM_PROMPT = """You are the FlashReserve Customer Support Assistant.

FlashReserve is a distributed ticket booking system with a Streamlit frontend,
Node.js and Express backend, MongoDB/Mongoose persistence, JWT authentication,
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
"""


def provider_status():
    return {
        "configured": bool(os.getenv("GROQ_API_KEY")),
        "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        "env_path": str(ENV_PATH),
    }


def _context_data(raw_context):
    if not raw_context:
        return {}
    try:
        return json.loads(raw_context)
    except json.JSONDecodeError:
        return {}


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
        return "Open My Bookings, select a booking, and choose Cancel booking. Cancellation is processed by FlashReserve."
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


def generate_llm_response(question, context=None):
    status = provider_status()
    if not status["configured"]:
        raise RuntimeError("GROQ_API_KEY is missing from the existing backend/.env configuration.")

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    completion = client.chat.completions.create(
        model=status["model"],
        temperature=0.2,
        max_tokens=500,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {question}\n\nTrusted backend context:\n{json.dumps(context or {}, ensure_ascii=True)}"},
        ],
    )
    return completion.choices[0].message.content.strip()


def provider_error_status(error):
    if getattr(error, "status_code", None) == 404 or getattr(error, "code", None) == "model_not_found":
        return "model_unavailable"
    return "provider_unavailable"


class LLMService(llm_pb2_grpc.LLMServiceServicer):
    def AskQuestion(self, request, _context):
        try:
            response = generate_llm_response(request.text, _context_data(request.context))
        except Exception as error:
            status = provider_error_status(error)
            print(f"LLM provider request failed (type={type(error).__name__}, status={getattr(error, 'status_code', 'unavailable')}, category={status}).")
            if status == "model_unavailable":
                message = "The configured support model is unavailable. Please configure a supported GROQ_MODEL."
            elif not provider_status()["configured"]:
                message = "GROQ_API_KEY is missing from the existing backend/.env configuration."
            else:
                message = "Support is temporarily unavailable. Please try again shortly."
            return llm_pb2.Answer(response=message, success=False, status=status)
        return llm_pb2.Answer(response=response, success=True, status="ok")


def serve():
    host = os.getenv("LLM_GRPC_HOST", "127.0.0.1")
    port = os.getenv("LLM_GRPC_PORT", "50051")
    status = provider_status()
    if status["configured"]:
        print(f"Groq provider configured; model: {status['model']}")
    else:
        print("GROQ_API_KEY is missing from the existing backend/.env configuration.")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    llm_pb2_grpc.add_LLMServiceServicer_to_server(LLMService(), server)
    server.add_insecure_port(f"{host}:{port}")
    server.start()
    print(f"FlashReserve LLM gRPC service listening on {host}:{port}")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(grace=2)


if __name__ == "__main__":
    serve()