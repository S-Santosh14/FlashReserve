const Booking = require("../models/Booking");
const Event = require("../models/Event");
const Payment = require("../models/Payment");
const Seat = require("../models/Seat");
const { askQuestion, checkReady, address } = require("../grpc/llmClient");

async function buildContext(req, message) {
  const [events, bookings] = await Promise.all([
    Event.find().select("title venue category date time price totalSeats").sort({ date: 1 }).lean(),
    req.user ? Booking.find({ userId: req.user.id }).populate("eventId", "title venue").select("status eventId").lean() : [],
  ]);

  const normalizedMessage = message.toLowerCase();
  const matchingEvent = events.find((event) => normalizedMessage.includes(event.title.toLowerCase()));
  const requestedEventId = req.body.eventId || matchingEvent?._id?.toString();
  let availableSeats;
  if (requestedEventId) {
    availableSeats = (await Seat.find({ eventId: requestedEventId, status: "available" }).select("seatNumber").sort({ seatNumber: 1 }).lean()).map((seat) => seat.seatNumber);
  }

  const payments = req.user ? await Payment.find({ userId: req.user.id }).select("bookingId amount status transactionId").lean() : [];

  return JSON.stringify({
    events: events.map((event) => ({ title: event.title, venue: event.venue, category: event.category, date: event.date, time: event.time, price: event.price, totalSeats: event.totalSeats })),
    bookings: bookings.map((booking) => ({ title: booking.eventId?.title || "Event", status: booking.status, bookingId: booking._id.toString() })),
    payments: payments.map((payment) => ({ bookingId: payment.bookingId.toString(), amount: payment.amount, status: payment.status })),
    ...(matchingEvent ? { requested_event: { title: matchingEvent.title, venue: matchingEvent.venue, price: matchingEvent.price } } : {}),
    ...(availableSeats ? { available_seats: availableSeats } : {}),
  });
}

async function chat(req, res) {
  const message = typeof req.body.message === "string" ? req.body.message.trim() : "";
  if (!message) return res.status(400).json({ success: false, message: "message is required" });

  let context;
  try {
    context = await buildContext(req, message);
  } catch (_error) {
    context = JSON.stringify({});
  }

  try {
    const answer = await askQuestion({ text: message, userId: req.user?.id || "", eventId: req.body.eventId || "", context });
    if (!answer.success) {
      console.error(`LLM response unavailable (status=${answer.status || "unknown"}).`);
      return res.status(answer.status === "model_unavailable" ? 502 : 503).json({ success: false, message: answer.response || "Support is temporarily unavailable. Please try again shortly." });
    }
    return res.json({ success: true, data: { response: answer.response, status: answer.status } });
  } catch (error) {
    console.error(`gRPC chatbot request failed (code=${error.code || "unknown"}).`);
    return res.status(503).json({ success: false, message: "Support chatbot is temporarily unavailable. Please try again later." });
  }
}

async function health(_req, res) {
  try {
    await checkReady();
    return res.json({ success: true, data: { grpc: "ready", address } });
  } catch (error) {
    console.error(`gRPC chatbot health failed (code=${error.code || "unknown"}).`);
    return res.status(503).json({ success: false, message: "Python chatbot service is unavailable." });
  }
}

module.exports = { chat, health };