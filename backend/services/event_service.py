from datetime import datetime, timezone

from bson import ObjectId

from backend.models.event import Event
from backend.models.seat import Seat


class EventError(Exception):

    def __init__(self, message, status_code=400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class EventService:

    SEAT_CATEGORIES = ["VIP", "Platinum", "Gold", "Silver"]

    EVENT_FIELDS = [
        "title",
        "category",
        "venue",
        "date",
        "time",
        "description",
        "totalSeats",
        "seatsPerRow",
        "price",
        "status",
        "posterUrl",
    ]

    def __init__(self, database):
        self.database = database

    # -----------------------------------------
    # SEAT GENERATION HELPERS
    # -----------------------------------------

    @staticmethod
    def row_label(index):

        label = ""

        value = index + 1

        while value > 0:

            value -= 1

            label = chr(65 + value % 26) + label

            value //= 26

        return label

    @staticmethod
    def seat_numbers_to_add(
        total_seats,
        seats_per_row,
        existing_seat_numbers=None
    ):

        existing = set(existing_seat_numbers or [])

        seat_numbers = []

        remaining = max(
            0,
            total_seats - len(existing)
        )

        index = 0

        while len(seat_numbers) < remaining:

            row = EventService.row_label(
                index // seats_per_row
            )

            seat_number = (
                f"{row}{(index % seats_per_row) + 1}"
            )

            if seat_number not in existing:

                existing.add(seat_number)

                seat_numbers.append(seat_number)

            index += 1

        return seat_numbers

    @staticmethod
    def seat_category(index, total_seats):

        category_index = min(
            len(EventService.SEAT_CATEGORIES) - 1,
            (index * len(EventService.SEAT_CATEGORIES))
            // total_seats
        )

        return EventService.SEAT_CATEGORIES[
            category_index
        ]

    @staticmethod
    def seat_index(seat_number, seats_per_row):

        import re

        match = re.match(
            r"^([A-Z]+)(\d+)$",
            seat_number,
            re.IGNORECASE
        )

        if not match:
            return float("inf")

        row = match.group(1).upper()

        row_index = 0

        for character in row:

            row_index = (
                row_index * 26
                + ord(character) - 64
            )

        return (
            (row_index - 1) * seats_per_row
            + int(match.group(2)) - 1
        )

    def generate_seats(
        self,
        event_id,
        total_seats,
        seats_per_row,
        existing_seat_numbers=None
    ):

        seat_numbers = self.seat_numbers_to_add(
            total_seats,
            seats_per_row,
            existing_seat_numbers
        )

        now = datetime.now(timezone.utc)

        documents = []

        for index, seat_number in enumerate(seat_numbers):

            seat_position = self.seat_index(
                seat_number,
                seats_per_row
            )

            documents.append({
                "eventId": event_id,
                "seatNumber": seat_number,
                "category": self.seat_category(
                    seat_position,
                    total_seats
                ),
                "status": "available",
                "reservedBy": None,
                "reservedAt": None,
                "reservationId": None,
                "lockExpiresAt": None,
                "bookingId": None,
                "createdAt": now,
                "updatedAt": now,
            })

        if documents:

            Seat.collection(self.database).insert_many(
                documents,
                ordered=True
            )

        return len(documents)

    # -----------------------------------------
    # LIST EVENTS
    # -----------------------------------------

    def get_all_events(self):

        return list(
            Event.collection(self.database)
            .find({"status": {"$ne": "archived"}})
            .sort([
                ("date", 1),
                ("createdAt", -1)
            ])
        )

    # -----------------------------------------
    # GET EVENT
    # -----------------------------------------

    def get_event(self, event_id):

        if not ObjectId.is_valid(event_id):

            raise EventError(
                "Invalid event id",
                400
            )

        event = Event.collection(
            self.database
        ).find_one({
            "_id": ObjectId(event_id),
            "status": {"$ne": "archived"}
        })

        if not event:

            raise EventError(
                "Event not found",
                404
            )

        return event

    # -----------------------------------------
    # CREATE EVENT
    # -----------------------------------------

    def create_event(self, data):

        event_data = dict(data)

        try:

            Event.validate(event_data)

        except (ValueError, TypeError) as error:

            raise EventError(str(error), 400)

        total_seats = event_data["totalSeats"]

        seats_per_row = event_data.get(
            "seatsPerRow",
            10
        )

        if (
            isinstance(total_seats, bool)
            or not isinstance(total_seats, int)
            or total_seats < 1
        ):

            raise EventError(
                "totalSeats must be a positive integer",
                400
            )

        if (
            isinstance(seats_per_row, bool)
            or not isinstance(seats_per_row, int)
            or seats_per_row < 1
        ):

            raise EventError(
                "seatsPerRow must be a positive integer",
                400
            )

        event_data["seatsPerRow"] = seats_per_row

        event_id = ObjectId()

        document = Event.prepare(event_data)

        document["_id"] = event_id

        Event.collection(
            self.database
        ).insert_one(document)

        self.generate_seats(
            event_id,
            total_seats,
            seats_per_row
        )

        return {
            "success": True,
            "data": Event.find_by_id(
                self.database,
                event_id
            )
        }

    # -----------------------------------------
    # UPDATE EVENT
    # -----------------------------------------

    def update_event(self, event_id, data):

        if not ObjectId.is_valid(event_id):

            raise EventError(
                "Invalid event id",
                400
            )

        event_id = ObjectId(event_id)

        current_event = Event.collection(
            self.database
        ).find_one({"_id": event_id})

        if not current_event:

            raise EventError(
                "Event not found",
                404
            )

        allowed = {
            key: value
            for key, value in data.items()
            if key in self.EVENT_FIELDS
        }

        if not allowed:

            raise EventError(
                "No valid event fields provided",
                400
            )

        total_seats = allowed.get(
            "totalSeats",
            current_event["totalSeats"]
        )

        seats_per_row = allowed.get(
            "seatsPerRow",
            current_event.get("seatsPerRow", 10)
        )

        price = allowed.get(
            "price",
            current_event["price"]
        )

        if (
            isinstance(total_seats, bool)
            or not isinstance(total_seats, int)
            or total_seats < 1
        ):

            raise EventError(
                "totalSeats must be a positive integer",
                400
            )

        if (
            isinstance(seats_per_row, bool)
            or not isinstance(seats_per_row, int)
            or seats_per_row < 1
        ):

            raise EventError(
                "seatsPerRow must be a positive integer",
                400
            )

        if (
            isinstance(price, bool)
            or not isinstance(price, (int, float))
            or price < 0
        ):

            raise EventError(
                "price must be a non-negative number",
                400
            )

        if (
            "status" in allowed
            and allowed["status"] not in Event.STATUSES
        ):

            raise EventError(
                "status must be active or archived",
                400
            )

        existing_seats = list(
            Seat.collection(self.database).find(
                {"eventId": event_id},
                {"seatNumber": 1}
            )
        )

        existing_numbers = [
            seat["seatNumber"]
            for seat in existing_seats
        ]

        current_count = len(existing_numbers)

        if total_seats < current_count:

            raise EventError(
                "totalSeats cannot be below the existing seat count",
                400
            )

        now = datetime.now(timezone.utc)

        allowed["updatedAt"] = now

        result = Event.collection(
            self.database
        ).update_one(
            {"_id": event_id},
            {"$set": allowed}
        )

        if result.matched_count == 0:

            raise EventError(
                "Event not found",
                404
            )

        if total_seats > current_count:

            self.generate_seats(
                event_id,
                total_seats,
                seats_per_row,
                existing_numbers
            )

        return {
            "success": True,
            "data": Event.find_by_id(
                self.database,
                event_id
            )
        }

    # -----------------------------------------
    # DELETE OR ARCHIVE EVENT
    # -----------------------------------------

    def delete_event(self, event_id):

        if not ObjectId.is_valid(event_id):

            raise EventError(
                "Invalid event id",
                400
            )

        event_id = ObjectId(event_id)

        event = Event.find_by_id(
            self.database,
            event_id
        )

        if not event:

            raise EventError(
                "Event not found",
                404
            )

        has_booking_history = (
            self.database["bookings"].find_one({
                "eventId": event_id
            }) is not None
        )

        has_held_seats = (
            self.database["seats"].find_one({
                "eventId": event_id,
                "status": {
                    "$in": ["reserved", "booked"]
                }
            }) is not None
        )

        if has_booking_history or has_held_seats:

            Event.collection(
                self.database
            ).update_one(
                {"_id": event_id},
                {
                    "$set": {
                        "status": "archived",
                        "updatedAt": datetime.now(timezone.utc)
                    }
                }
            )

            return {
                "success": True,
                "message": (
                    "Event archived to preserve booking "
                    "history and seat records."
                ),
                "data": {
                    "archived": True
                }
            }

        Seat.collection(
            self.database
        ).delete_many({
            "eventId": event_id
        })

        Event.delete(
            self.database,
            event_id
        )

        return {
            "success": True,
            "message": "Event deleted",
            "data": {
                "archived": False
            }
        }