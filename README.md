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

