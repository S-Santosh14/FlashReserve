# FlashReserve

Distributed Ticket Booking System

Milestone 1: Project Foundation, gRPC & LLM Integration
● Real-time seat reservation with concurrency control to prevent race conditions.
● Payment processing (mock/stub service acceptable).
● LLM Integration: Customer support chatbot for FAQs (e.g., "How to cancel a booking?", "What seats are available? Etc.").

## Run

```powershell
cd outputs\flashreserve
python -m pip install -r requirements.txt
streamlit run app.py
```

Use the demo sign-in: `santosh` / `1234`.

## Included demo flow

Sign in → discover/search → event details → native clickable seat map → summary → mock payment → confirmation → booking details/cancellation.


# FlashReserve

Distributed ticket booking system with a Streamlit customer UI, an Express/MongoDB backend, and a Python gRPC customer-support service.

## Project Tree

```text
FlashReserve/
├── app.py
├── requirements.txt
├── frontend/
│   ├── components/
│   ├── pages/
│   └── utils/
├── backend/
│   ├── server.js
│   ├── config/
│   ├── models/
│   ├── routes/
│   ├── controllers/
│   ├── middleware/
│   └── grpc/llm.proto
└── llm/
		├── llm_service.py
		├── llm_prototype.ipynb
		├── requirements.txt
		└── proto/
				└── llm.proto
```

## Services

1. MongoDB stores users, events, seats, bookings, and payments.
2. Node.js/Express exposes the REST API and owns authentication, authorization, booking, payment, and MongoDB access.
3. The Python LLM service listens on gRPC at `127.0.0.1:50051` by default.
4. Streamlit calls Node over HTTP. Node calls the Python chatbot over gRPC for support questions.

The chatbot is intentionally small for Milestone 1. FAQ answers are deterministic. Dynamic events, seats, and bookings are queried by Node and passed as request context; the Python service does not invent those values.

## Configuration

Keep the existing `backend/.env` file. It contains `PORT`, `MONGODB_URI`, and `JWT_SECRET`.

Optional values:

```text
FLASHRESERVE_API_URL=http://localhost:5000
LLM_GRPC_ADDRESS=127.0.0.1:50051
LLM_GRPC_HOST=127.0.0.1
LLM_GRPC_PORT=50051
```

Do not commit secrets or replace the existing environment file.

## Installation

Backend:

```powershell
cd backend
npm install
```

Streamlit and REST client:

```powershell
python -m pip install -r requirements.txt
```

Python gRPC service:

```powershell
python -m pip install -r llm/requirements.txt
```

## Start All Services

Start MongoDB using the local service or MongoDB Atlas configured by `MONGODB_URI`.

Terminal 1, Node backend:

```powershell
cd backend
npm start
```

Terminal 2, Python chatbot:

```powershell
python llm/llm_service.py
```

Terminal 3, Streamlit:

```powershell
python -m streamlit run app.py
```

Open `http://localhost:8501`.

## REST APIs

```text
GET    /api/health

POST   /api/auth/register
POST   /api/auth/login

GET    /api/events
GET    /api/events/:id
GET    /api/events/:eventId/seats
POST   /api/events/:eventId/seats/reserve

POST   /api/bookings
GET    /api/bookings
GET    /api/bookings/:id
PUT    /api/bookings/:id/cancel

POST   /api/payments/mock
POST   /api/chat

GET    /api/admin/users
GET    /api/admin/bookings
GET    /api/admin/events
POST   /api/admin/events
PUT    /api/admin/events/:id
DELETE /api/admin/events/:id
```

Protected endpoints use:

```text
Authorization: Bearer <JWT>
```

## Customer Flow

Register and login return a JWT. Streamlit stores the token and basic user information in `st.session_state`, never the password.

The customer flow is:

```text
Register
-> Login
-> Browse events
-> Event details
-> Select and reserve seats
-> Create booking
-> Mock payment
-> Confirmation and transaction ID
-> My Bookings
-> Cancellation
-> Support chatbot
```

Example chatbot request after login:

```powershell
curl -X POST http://localhost:5000/api/chat `
	-H "Authorization: Bearer YOUR_JWT" `
	-H "Content-Type: application/json" `
	-d '{"message":"How do I cancel my booking?"}'
```

The response is JSON containing `data.response` and `data.status`.

## Admin Flow

Seed three admin accounts intentionally:

```powershell
cd backend
npm run seed:admins
```

The script prompts for passwords and stores only bcrypt hashes. Admin JWTs can access user, booking, and event management APIs. There is no admin registration endpoint.

## Database Collections

- `users`: customer/admin accounts with bcrypt password hashes
- `events`: title, category, venue, date, time, description, price, and seat count
- `seats`: event seat number, availability, reservation owner, and reservation timestamp
- `bookings`: customer, event, seats, amount, and status
- `payments`: booking, customer, amount, mock transaction ID, and status

## Seat Concurrency

Reservation uses one atomic MongoDB `findOneAndUpdate` filtered by `status: "available"`. Only one concurrent request can transition a seat to `reserved`; competing requests receive HTTP `409`.

## Authentication

Customers register with an email and password. Passwords are hashed with bcrypt. Login verifies the hash and returns a JWT signed with `JWT_SECRET`. Authentication middleware verifies the JWT, and admin middleware requires `role: "admin"`. Passwords and secrets are never returned or logged.

## gRPC Architecture

The shared contract is `llm/proto/llm.proto`, mirrored at `backend/grpc/llm.proto`.

```text
Streamlit POST /api/chat
		-> Node chat controller
		-> MongoDB context lookup
		-> gRPC LLMService.AskQuestion
		-> Python answer_question()
		-> Node JSON response
		-> Streamlit chat message
```

If the Python service is unavailable, Node returns HTTP `503` with a user-safe message. The booking system remains available.

## Validation

The Stage 4 checks include:

```powershell
python -m compileall -q app.py frontend llm
cd backend
npm test
```

The Python gRPC service and Node client have also been tested with a real gRPC request and dynamic seat context.

## Remaining Scope

LLM provider integration, gRPC streaming, RAG, and production deployment are intentionally outside Milestone 1. The current support service is a deterministic FAQ service with live application context.

