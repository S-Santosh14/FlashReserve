# FlashReserve

Distributed Ticket Booking System

FlashReserve is a distributed ticket booking system developed as an AOS project. It provides a simple interface for discovering events, selecting seats, booking tickets, making mock payments, managing bookings, and getting customer support through an LLM service.

## Features

* User registration and login
* Browse and search events
* Event details and posters
* Interactive seat selection
* Real-time seat reservation
* Concurrency control for simultaneous bookings
* 30-second reservation timeout
* Mock payment processing
* Booking history
* Booking cancellation
* Customer support chatbot
* Admin dashboard
* Admin user, event, booking and seat management
* MongoDB database
* REST API using Node.js and Express
* gRPC communication with the Python LLM service

## Technologies Used

* **Frontend:** Python, Streamlit
* **Backend:** Node.js, Express.js
* **Database:** MongoDB
* **Communication:** REST API, gRPC
* **LLM Service:** Python
* **Authentication:** JWT
* **Password Security:** bcrypt

## Project Structure

```text
FlashReserve/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── frontend/
│   ├── components/
│   │   ├── admin_nav.py
│   │   ├── booking_card.py
│   │   ├── event_card.py
│   │   ├── footer.py
│   │   ├── navbar.py
│   │   ├── poster.py
│   │   └── seat_map.py
│   │
│   ├── data/
│   │   └── dummy_data.py
│   │
│   ├── pages/
│   │   ├── home.py
│   │   ├── events.py
│   │   ├── event_details.py
│   │   ├── seats.py
│   │   ├── checkout.py
│   │   ├── payment.py
│   │   ├── confirmation.py
│   │   ├── bookings.py
│   │   ├── booking_details.py
│   │   ├── profile.py
│   │   ├── support.py
│   │   ├── admin_dashboard.py
│   │   ├── admin_users.py
│   │   ├── admin_events.py
│   │   ├── admin_seats.py
│   │   └── admin_bookings.py
│   │
│   ├── pictures/
│   ├── styles.py
│   │
│   └── utils/
│       ├── api.py
│       ├── navigation.py
│       └── session.py
│
├── backend/
│   ├── server.js
│   ├── package.json
│   ├── package-lock.json
│   ├── .env
│   │
│   ├── config/
│   │   └── db.js
│   │
│   ├── controllers/
│   │   ├── adminController.js
│   │   ├── authController.js
│   │   ├── bookingController.js
│   │   ├── chatController.js
│   │   ├── eventController.js
│   │   ├── paymentController.js
│   │   └── seatController.js
│   │
│   ├── grpc/
│   │   ├── llm.proto
│   │   └── llmClient.js
│   │
│   ├── middleware/
│   │   ├── adminMiddleware.js
│   │   └── authMiddleware.js
│   │
│   ├── models/
│   │   ├── Booking.js
│   │   ├── Event.js
│   │   ├── Payment.js
│   │   ├── Seat.js
│   │   └── User.js
│   │
│   ├── routes/
│   │   ├── adminRoutes.js
│   │   ├── authRoutes.js
│   │   ├── bookingRoutes.js
│   │   ├── chatRoutes.js
│   │   ├── eventRoutes.js
│   │   ├── paymentRoutes.js
│   │   └── seatRoutes.js
│   │
│   ├── uploads/
│   │
│   └── utils/
│       ├── asyncHandler.js
│       ├── seedAdmins.js
│       └── validation.js
│
└── llm/
    ├── llm_service.py
    ├── llm_prototype.ipynb
    ├── requirements.txt
    │
    └── proto/
        ├── llm.proto
        ├── llm_pb2.py
        └── llm_pb2_grpc.py
```

## Installation

Open the extracted `FlashReserve` folder in **VS Code**.

Make sure Python, Node.js and MongoDB are available on the system.

### Backend

Open a terminal in VS Code:

```powershell
cd backend
npm install
```

### Streamlit

Open another terminal in the main `FlashReserve` folder:

```powershell
python -m pip install -r requirements.txt
```

### LLM Service

Install the Python packages required by the LLM service:

```powershell
python -m pip install -r llm/requirements.txt
```

## Running the Project

The complete application uses three terminals.

### Terminal 1 – Frontend

From the main `FlashReserve` folder:

```powershell
streamlit run app.py
```

### Terminal 2 – Backend

```powershell
cd backend
npm start
```

The backend runs on port `5000`.

### Terminal 3 – LLM Service

```powershell
cd llm
python llm_service.py
```

The LLM service runs through gRPC on port `50051`.

Keep all three terminals running while using the application.

After Streamlit starts, open:

```text
http://localhost:8501
```

## Application Flow

```text
Register / Login
       ↓
Browse Events
       ↓
Search / Select Event
       ↓
Event Details
       ↓
Select Seats
       ↓
Reserve Seats
       ↓
Checkout
       ↓
Mock Payment
       ↓
Booking Confirmation
       ↓
My Bookings
       ↓
Cancellation
       ↓
Customer Support
```

## Admin Flow

The project also contains an admin dashboard for managing the system.

Admins can:

* View users
* View bookings
* View events
* Create events
* Update events
* Delete events
* View event seats
* Update seat status

Admin pages are available through the admin section of the application.

## Database

MongoDB is used to store the application data.

The main collections are:

```text
Users
Events
Seats
Bookings
Payments
```

The MongoDB connection is configured in the backend environment configuration.

## LLM and gRPC

FlashReserve contains a separate Python customer-support service.

The communication works as follows:

```text
Streamlit
    ↓
Node.js / Express Backend
    ↓
gRPC
    ↓
Python LLM Service
```

The chatbot can answer questions related to:

* Events
* Seat availability
* Ticket booking
* Bookings
* Cancellation
* Payments

The backend provides the current application information to the LLM service so that dynamic information such as events, seats and bookings can be handled using the application data.

## Seat Concurrency

FlashReserve includes concurrency control for ticket reservations.

When two users try to reserve the same seat at the same time, the backend uses an atomic database operation to make sure that the same seat cannot be successfully reserved by both users.

A seat reservation is held for **30 seconds**. If the booking process is not completed within this period, the reservation can expire and the seat becomes available again.

## Testing Concurrency

To demonstrate the concurrency handling:

1. Open **two separate terminals** for the Streamlit frontend.
2. Run the frontend in both terminals.
3. Open the two frontend instances in separate browser windows.
4. Login from both instances.
5. Select the **same event and the same seat**.
6. Try to reserve the seat from both windows at approximately the same time.

The system handles the simultaneous requests and prevents both users from reserving the same seat.

The competing reservation can remain blocked for **30 seconds** before the reservation timeout is reached.

This demonstrates how FlashReserve handles simultaneous booking requests and prevents race conditions.

## Mock Payment

The project includes a mock payment system for testing the complete booking flow.

The payment process is:

```text
Seat Reservation
      ↓
Create Booking
      ↓
Mock Payment
      ↓
Payment Success
      ↓
Booking Confirmation
```

No real money is involved in the payment process.

## Important

All three services should be running while testing the complete application:

```text
Streamlit Frontend
        ↓
Node.js Backend
        ↓
MongoDB

Node.js Backend
        ↓
Python gRPC LLM Service
```

If the backend is stopped, booking and other API-based features will not work.

If the Python LLM service is stopped, the customer-support chatbot will not work.

## Project Status

The current version includes the main ticket booking workflow, frontend and backend integration, MongoDB connectivity, authentication, seat reservation, concurrency handling, mock payments, admin functionality, and the customer-support LLM service.

## Team

**FlashReserve – AOS Project**

Developed as part of the **Advanced Operating Systems** course at **BITS Pilani**.
