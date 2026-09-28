"""Fictional content for the FlashReserve UI prototype.

Keep URLs here so local assets or service-provided media can replace them later.
"""

EVENTS = [
    {
        "id": "techfest",
        "title": "TechFest 2026",
        "category": "Technology",
        "venue": "BITS Pilani, Hyderabad Campus",
        "city": "Hyderabad",
        "date": "28 September 2026",
        "short_date": "28 Sep",
        "time": "7:00 PM",
        "price": 499,
        "image": "frontend/pictures/techfest.jpg",
        "eyebrow": "IDEAS / MAKERS / FUTURE",
        "description": "A one-night campus showcase where student builders, creative technologists and visiting founders share the prototypes shaping what comes next. Expect live demos, a founder conversation and an after-hours mixer.",
    },
    {
        "id": "campus-beats",
        "title": "Campus Beats",
        "category": "Concerts",
        "venue": "The Courtyard, Gachibowli",
        "city": "Hyderabad",
        "date": "30 September 2026",
        "short_date": "30 Sep",
        "time": "8:00 PM",
        "price": 699,
        "image": "frontend/pictures/concert.jpg",
        "eyebrow": "LIVE / OPEN AIR",
        "description": "An open-air night of independent music and unexpectedly good company. Three emerging acts, one luminous courtyard and a set list made for late September.",
    },
    {
        "id": "after-hours",
        "title": "Comedy After Hours",
        "category": "Comedy",
        "venue": "The Lantern Room",
        "city": "Delhi",
        "date": "02 October 2026",
        "short_date": "02 Oct",
        "time": "7:30 PM",
        "price": 599,
        "image": "frontend/pictures/comedy.jpg",
        "eyebrow": "LATE SET / GOOD HUMOUR",
        "description": "A sharp, smart and intimate stand-up set with comics who know how to keep a room leaning forward. Mature humour, no two drink minimum.",
    },
    {
        "id": "cricket-night",
        "title": "Cricket Night",
        "category": "Sports",
        "venue": "Pilani Sports Ground",
        "city": "Pilani",
        "date": "05 October 2026",
        "short_date": "05 Oct",
        "time": "6:30 PM",
        "price": 399,
        "image": "frontend/pictures/cricket.jpg",
        "eyebrow": "UNDER LIGHTS",
        "description": "A fast-paced campus rivalry under the lights. Bring your voice, pick a side and stay for the final over.",
    },
    {
        "id": "monsoon-repertoire",
        "title": "Monsoon Repertoire",
        "category": "Theatre",
        "venue": "Ravindra Mini Theatre",
        "city": "Hyderabad",
        "date": "11 October 2026",
        "short_date": "11 Oct",
        "time": "6:00 PM",
        "price": 549,
        "image": "frontend/pictures/theatre.jpg",
        "eyebrow": "A NEW STAGE PIECE",
        "description": "A tender, contemporary ensemble performance about cities, rain and the memories we carry home.",
    },
    {
        "id": "frame-by-frame",
        "title": "Frame by Frame",
        "category": "Movies",
        "venue": "Studio 4, Prism Cinemas",
        "city": "Hyderabad",
        "date": "18 October 2026",
        "short_date": "18 Oct",
        "time": "5:45 PM",
        "price": 429,
        "image": "frontend/pictures/movie.jpg",
        "eyebrow": "FILM / CONVERSATION",
        "description": "A curated premiere followed by an easygoing conversation with the director and cinematography team.",
    },
]

CATEGORIES = ["All", "Movies", "Concerts", "Sports", "Comedy", "Technology", "Theatre"]

SOLD_SEATS = {"A3", "A6", "B5", "C2", "C7", "D4", "E1", "E6"}

INITIAL_BOOKINGS = [
    {
        "id": "FR-2847391",
        "event_id": "techfest",
        "seats": ["A2", "B3"],
        "amount": 998,
        "status": "Confirmed",
        "booked_on": "12 September 2026",
    },
    {
        "id": "FR-1928410",
        "event_id": "frame-by-frame",
        "seats": ["C4"],
        "amount": 429,
        "status": "Completed",
        "booked_on": "28 August 2026",
    },
]

SUPPORT_ANSWERS = {
    "cancel": "You can cancel an eligible booking from My Bookings. Open the booking, choose Cancel booking, and confirm the change. This prototype updates the status only in this browser session.",
    "seats": "Available seats are shown in outline, your selected seats are blue, and sold seats are muted. Seat availability is intentionally local dummy state for this UI prototype.",
    "booking": "Your current and previous reservations are collected in My Bookings. Select View details to see seats, price and booking status.",
    "seat": "Seat changes are not available after mock payment in this prototype. You can select different seats any time before continuing from the seat map.",
}


def get_event(event_id: str):
    return next((event for event in EVENTS if event["id"] == event_id), EVENTS[0])
