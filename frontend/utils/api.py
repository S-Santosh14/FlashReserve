"""Small REST client for the FlashReserve Node backend."""

from datetime import datetime
import os

import requests


BASE_URL = os.getenv("FLASHRESERVE_API_URL", "http://localhost:5000").rstrip("/")


class APIError(Exception):
    """User-facing error returned by the backend or caused by an unavailable backend."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _request(method, path, token=None, payload=None, files=None):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        request_kwargs = {"headers": headers, "timeout": 10}
        if files:
            request_kwargs["files"] = files
            request_kwargs["data"] = payload or {}
        else:
            request_kwargs["json"] = payload
        response = requests.request(method, f"{BASE_URL}{path}", **request_kwargs)
    except requests.RequestException as error:
        raise APIError("FlashReserve backend is unavailable. Please try again.") from error

    try:
        body = response.json()
    except ValueError as error:
        raise APIError("The backend returned an invalid response.", response.status_code) from error

    if not response.ok or body.get("success") is False:
        raise APIError(body.get("message", "The request could not be completed."), response.status_code)
    return body.get("data", body)


def _display_date(value, short=False):
    if not value:
        return "Date to be announced"
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.strftime("%d %b" if short else "%d %B %Y")
    except ValueError:
        return str(value)


def _normalize_event(raw):
    event = dict(raw)
    event["id"] = str(raw.get("id") or raw.get("_id"))
    event["raw_date"] = str(raw.get("date", ""))[:10]
    event["date"] = _display_date(raw.get("date"))
    event["short_date"] = _display_date(raw.get("date"), short=True)
    event["city"] = raw.get("city") or raw.get("venue", "")
    event["eyebrow"] = raw.get("eyebrow") or str(raw.get("category", "EVENT")).upper()
    event["price"] = int(raw.get("price") or 0)
    event["image"] = raw.get("image")
    event["poster_url"] = raw.get("posterUrl", "")
    if event["poster_url"] and event["poster_url"].startswith("/"):
        event["poster_url"] = f"{BASE_URL}{event['poster_url']}"
    event["image"] = event["poster_url"] or event["image"]
    return event


def _normalize_booking(raw):
    event_raw = raw.get("eventId") if isinstance(raw.get("eventId"), dict) else raw.get("event")
    event = _normalize_event(event_raw) if event_raw else None
    seats = raw.get("seats", [])
    seat_numbers = [seat.get("seatNumber", "") if isinstance(seat, dict) else str(seat) for seat in seats]
    booking = dict(raw)
    booking["id"] = str(raw.get("id") or raw.get("_id"))
    booking["event_id"] = event["id"] if event else str(raw.get("eventId", ""))
    booking["event"] = event
    booking["seats"] = seat_numbers
    booking["amount"] = raw.get("totalAmount", raw.get("amount", 0))
    booking["status"] = str(raw.get("status", "pending")).capitalize()
    booking["booked_on"] = _display_date(raw.get("createdAt"), short=False)
    return booking


def register_user(name, email, password):
    return _request("POST", "/api/auth/register", payload={"name": name, "email": email, "password": password})


def login_user(email, password):
    return _request("POST", "/api/auth/login", payload={"email": email, "password": password})


def get_events():
    return [_normalize_event(event) for event in _request("GET", "/api/events")]


def get_event(event_id):
    return _normalize_event(_request("GET", f"/api/events/{event_id}"))


def get_seats(event_id, token):
    return _request("GET", f"/api/events/{event_id}/seats", token=token)


def reserve_seats(event_id, seat_numbers, token):
    reserved = []
    for seat_number in seat_numbers:
        reserved.append(_request("POST", f"/api/events/{event_id}/seats/reserve", token=token, payload={"seatNumber": seat_number}))
    return reserved


def create_booking(event_id, seat_numbers, total_amount, token):
    booking = _request(
        "POST",
        "/api/bookings",
        token=token,
        payload={"eventId": event_id, "seatNumbers": seat_numbers, "totalAmount": total_amount},
    )
    return _normalize_booking(booking)


def get_bookings(token):
    return [_normalize_booking(booking) for booking in _request("GET", "/api/bookings", token=token)]


def cancel_booking(booking_id, token):
    return _normalize_booking(_request("PUT", f"/api/bookings/{booking_id}/cancel", token=token))


def make_mock_payment(booking_id, amount, token, should_fail=False):
    return _request(
        "POST",
        "/api/payments/mock",
        token=token,
        payload={"bookingId": booking_id, "amount": amount, "shouldFail": should_fail},
    )


def ask_chat(message, token, event_id=None):
    return _request(
        "POST",
        "/api/chat",
        token=token,
        payload={"message": message, **({"eventId": event_id} if event_id else {})},
    )


def get_admin_stats(token):
    return _request("GET", "/api/admin/stats", token=token)


def get_admin_users(token):
    return _request("GET", "/api/admin/users", token=token)


def get_admin_bookings(token):
    bookings = _request("GET", "/api/admin/bookings", token=token)
    for booking in bookings:
        event = booking.get("eventId")
        if isinstance(event, dict):
            booking["eventId"] = _normalize_event(event)
    return bookings


def get_event_seats(event_id, token):
    return _request("GET", f"/api/admin/events/{event_id}/seats", token=token)


def update_admin_seat(seat_id, status, token):
    return _request("PUT", f"/api/admin/seats/{seat_id}", token=token, payload={"status": status})


def create_event(event, token, poster=None):
    if poster:
        files = {"poster": (poster.name, poster.getvalue(), poster.type or "application/octet-stream")}
        return _normalize_event(_request("POST", "/api/admin/events", token=token, payload=event, files=files))
    return _normalize_event(_request("POST", "/api/admin/events", token=token, payload=event))


def update_event(event_id, event, token, poster=None):
    if poster:
        files = {"poster": (poster.name, poster.getvalue(), poster.type or "application/octet-stream")}
        return _normalize_event(_request("PUT", f"/api/admin/events/{event_id}", token=token, payload=event, files=files))
    return _normalize_event(_request("PUT", f"/api/admin/events/{event_id}", token=token, payload=event))


def delete_event(event_id, token):
    return _request("DELETE", f"/api/admin/events/{event_id}", token=token)