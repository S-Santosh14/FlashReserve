const Booking = require("../models/Booking");
const Event = require("../models/Event");
const Seat = require("../models/Seat");
const { isValidObjectId, requireFields } = require("../utils/validation");

async function createBooking(req, res) {
  const missing = requireFields(req.body, ["eventId", "seatNumbers", "totalAmount"]);
  if (missing.length) return res.status(400).json({ success: false, message: `Missing required fields: ${missing.join(", ")}` });
  if (!isValidObjectId(req.body.eventId) || !Array.isArray(req.body.seatNumbers) || !req.body.seatNumbers.length || typeof req.body.totalAmount !== "number" || req.body.totalAmount < 0) {
    return res.status(400).json({ success: false, message: "Provide a valid eventId, seatNumbers array, and totalAmount" });
  }

  const event = await Event.findById(req.body.eventId);
  if (!event) return res.status(404).json({ success: false, message: "Event not found" });
  const uniqueSeatNumbers = [...new Set(req.body.seatNumbers.map((seat) => String(seat).trim()))];
  const seats = await Seat.find({ eventId: event._id, seatNumber: { $in: uniqueSeatNumbers }, status: "reserved", reservedBy: req.user.id });
  if (seats.length !== uniqueSeatNumbers.length) return res.status(409).json({ success: false, message: "All requested seats must be reserved by you before booking" });
  const expectedAmount = event.price * uniqueSeatNumbers.length;
  if (req.body.totalAmount !== expectedAmount) return res.status(400).json({ success: false, message: "Booking amount does not match event price" });

  const booking = await Booking.create({ userId: req.user.id, eventId: event._id, seats: seats.map((seat) => seat._id), totalAmount: req.body.totalAmount, status: "pending" });
  await Seat.updateMany({ _id: { $in: seats.map((seat) => seat._id) }, status: "reserved", reservedBy: req.user.id }, { $set: { status: "booked" } });
  return res.status(201).json({ success: true, data: await booking.populate(["eventId", "seats"]) });
}

async function listBookings(req, res) {
  const bookings = await Booking.find({ userId: req.user.id }).populate("eventId seats").sort({ createdAt: -1 });
  return res.json({ success: true, data: bookings });
}

async function getBooking(req, res) {
  if (!isValidObjectId(req.params.id)) return res.status(400).json({ success: false, message: "Invalid booking id" });
  const booking = await Booking.findOne({ _id: req.params.id, userId: req.user.id }).populate("eventId seats");
  if (!booking) return res.status(404).json({ success: false, message: "Booking not found" });
  return res.json({ success: true, data: booking });
}

async function cancelBooking(req, res) {
  if (!isValidObjectId(req.params.id)) return res.status(400).json({ success: false, message: "Invalid booking id" });
  const booking = await Booking.findOneAndUpdate({ _id: req.params.id, userId: req.user.id, status: { $in: ["pending", "confirmed"] } }, { $set: { status: "cancelled" } }, { new: true });
  if (!booking) return res.status(404).json({ success: false, message: "Booking not found or cannot be cancelled" });
  await Seat.updateMany({ _id: { $in: booking.seats } }, { $set: { status: "available", reservedBy: null, reservedAt: null } });
  return res.json({ success: true, data: booking });
}

module.exports = { createBooking, listBookings, getBooking, cancelBooking };