import logging
import re
import smtplib
import threading
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr

from pymongo import ReturnDocument
from pymongo.errors import PyMongoError

from backend.config import settings


logger = logging.getLogger(__name__)


class NotificationError(Exception):
    pass


class NotificationService:
    POLL_SECONDS = 5
    LEASE_SECONDS = 600
    SMTP_TIMEOUT_SECONDS = 20

    def __init__(self, database):
        self.outbox = database["notificationoutbox"]
        self.stop_event = threading.Event()
        self.thread = None

    def enqueue(self, mode, kind, user, booking):
        if kind not in {"confirmation", "cancellation"}:
            raise NotificationError("Unsupported notification type.")
        expected_status = "confirmed" if kind == "confirmation" else "cancelled"
        if booking.get("status") != expected_status:
            raise NotificationError("Booking status does not match the notification.")
        email = user.get("email")
        if not isinstance(email, str) or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            raise NotificationError("The account does not have a valid email address.")
        event = booking.get("event")
        seats = booking.get("seats")
        if (
            not isinstance(event, dict)
            or not event.get("title")
            or not isinstance(seats, list)
            or not seats
            or any(not isinstance(seat, dict) or not seat.get("seatNumber") for seat in seats)
            or not booking.get("bookingReference")
            or not booking.get("id")
        ):
            raise NotificationError("Booking details are incomplete for email delivery.")

        notification_id = f"{mode}:{booking['id']}:{kind}"
        now = datetime.now(timezone.utc)
        document = {
            "_id": notification_id,
            "mode": mode,
            "kind": kind,
            "recipient": email,
            "customerName": user.get("name", "Customer"),
            "reference": booking["bookingReference"],
            "event": event["title"],
            "date": str(event.get("date", "")),
            "time": str(event.get("time", "")),
            "venue": str(event.get("venue", "")),
            "seats": [seat["seatNumber"] for seat in seats],
            "amount": booking.get("totalAmount"),
            "status": "pending",
            "attempts": 0,
            "nextAttemptAt": now,
            "createdAt": now,
        }
        self.outbox.update_one(
            {"_id": notification_id}, {"$setOnInsert": document}, upsert=True
        )

    def start(self):
        if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning("SMTP configuration is incomplete; queued notifications will be retried.")
        self.thread = threading.Thread(target=self._run, name="notification-worker", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread is not None:
            self.thread.join(timeout=self.SMTP_TIMEOUT_SECONDS + 5)
            if self.thread.is_alive():
                logger.error("Notification worker did not stop before the timeout.")

    def _run(self):
        while not self.stop_event.is_set():
            try:
                self.process_one()
            except PyMongoError as error:
                logger.error("Notification database operation failed (%s).", type(error).__name__)
            self.stop_event.wait(self.POLL_SECONDS)

    def process_one(self):
        now = datetime.now(timezone.utc)
        expired = self.outbox.update_many(
            {"status": "sending", "leaseUntil": {"$lte": now}},
            {"$set": {"status": "delivery_unknown", "updatedAt": now},
             "$unset": {"leaseUntil": ""}},
        )
        if expired.modified_count:
            logger.error(
                "%s notification delivery attempt(s) have an unknown outcome and need review.",
                expired.modified_count,
            )
        item = self.outbox.find_one_and_update(
            {"status": "pending", "nextAttemptAt": {"$lte": now}},
            {"$set": {"status": "sending", "leaseUntil": now + timedelta(seconds=self.LEASE_SECONDS)},
             "$inc": {"attempts": 1}},
            sort=[("createdAt", 1)],
            return_document=ReturnDocument.AFTER,
        )
        if not item:
            return False

        transmitting = False
        smtp = None
        try:
            if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
                raise NotificationError("SMTP settings are incomplete.")
            message = self._message(item)
            smtp = smtplib.SMTP(
                settings.SMTP_HOST, settings.SMTP_PORT, timeout=self.SMTP_TIMEOUT_SECONDS
            )
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            transmitting = True
            smtp.send_message(message)
        except (smtplib.SMTPResponseException, smtplib.SMTPRecipientsRefused) as error:
            self._record_failure(item, "pending", error)
        except (smtplib.SMTPException, OSError, NotificationError, ValueError) as error:
            self._record_failure(item, "delivery_unknown" if transmitting else "pending", error)
        else:
            self.outbox.update_one(
                {"_id": item["_id"], "status": "sending"},
                {"$set": {"status": "sent", "sentAt": datetime.now(timezone.utc)},
                 "$unset": {"leaseUntil": "", "lastError": ""}},
            )
            logger.info("Notification accepted by SMTP for booking %s.", item["reference"])
        finally:
            if smtp is not None:
                smtp.close()
        return True

    def _record_failure(self, item, status, error):
        now = datetime.now(timezone.utc)
        delay = min(3600, 30 * (2 ** min(item["attempts"] - 1, 7)))
        self.outbox.update_one(
            {"_id": item["_id"], "status": "sending"},
            {"$set": {
                "status": status,
                "lastError": type(error).__name__,
                "updatedAt": now,
                "nextAttemptAt": now + timedelta(seconds=delay),
            }, "$unset": {"leaseUntil": ""}},
        )
        logger.error(
            "Notification delivery %s for booking %s (%s).",
            status, item["reference"], type(error).__name__,
        )

    @staticmethod
    def _message(item):
        message = EmailMessage()
        message["From"] = formataddr((settings.SMTP_FROM_NAME, settings.SMTP_USER))
        message["To"] = item["recipient"]
        message["Subject"] = (
            "FlashReserve booking confirmed"
            if item["kind"] == "confirmation"
            else "FlashReserve booking cancelled"
        )
        message.set_content(
            f"Hello {item['customerName']},\n\n"
            f"Your booking is {'confirmed' if item['kind'] == 'confirmation' else 'cancelled'}.\n"
            f"Booking reference: {item['reference']}\n"
            f"Event: {item['event']}\n"
            f"Date: {item['date']} {item['time']}\n"
            f"Venue: {item['venue']}\n"
            f"Seats: {', '.join(item['seats'])}\n"
            f"Total amount: {item['amount']}\n\n"
            "FlashReserve"
        )
        return message
