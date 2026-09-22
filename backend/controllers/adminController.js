const Booking = require("../models/Booking");
const Event = require("../models/Event");
const Seat = require("../models/Seat");
const User = require("../models/User");
const eventController = require("./eventController");

async function listUsers(_req, res) {
  const users = await User.find().select("name email role createdAt").sort({ createdAt: -1 });
  return res.json({ success: true, data: users });
}

async function listBookings(_req, res) {
  const bookings = await Booking.find().populate("userId", "name email role").populate("eventId seats").sort({ createdAt: -1 });
  return res.json({ success: true, data: bookings });
}

async function listEvents(_req, res) {
  const events = await Event.find().sort({ date: 1, createdAt: -1 });
  return res.json({ success: true, data: events });
}

async function getStats(_req, res) {
  const [totalEvents, totalUsers, totalBookings, seatCounts] = await Promise.all([
    Event.countDocuments(),
    User.countDocuments(),
    Booking.countDocuments(),
    Seat.aggregate([{ $group: { _id: "$status", count: { $sum: 1 } } }]),
  ]);
  const counts = Object.fromEntries(seatCounts.map((item) => [item._id, item.count]));
  return res.json({
    success: true,
    data: {
      totalEvents,
      totalUsers,
      totalBookings,
      totalSeats: Object.values(counts).reduce((total, count) => total + count, 0),
      availableSeats: counts.available || 0,
      bookedSeats: counts.booked || 0,
      reservedSeats: counts.reserved || 0,
    },
  });
}

async function listSeats(req, res) {
  const seats = await Seat.find({ eventId: req.params.eventId }).populate("reservedBy", "name email").sort({ seatNumber: 1 });
  return res.json({ success: true, data: seats });
}

async function updateSeat(req, res) {
  const allowedStatuses = ["available", "reserved", "booked"];
  if (!allowedStatuses.includes(req.body.status)) {
    return res.status(400).json({ success: false, message: "Invalid seat status" });
  }
  const update = { status: req.body.status };
  if (req.body.status === "available") {
    update.reservedBy = null;
    update.reservedAt = null;
  }
  const seat = await Seat.findByIdAndUpdate(req.params.seatId, { $set: update }, { new: true, runValidators: true }).populate("reservedBy", "name email");
  if (!seat) return res.status(404).json({ success: false, message: "Seat not found" });
  return res.json({ success: true, data: seat });
}

module.exports = {
  listUsers,
  listBookings,
  listEvents,
  getStats,
  listSeats,
  updateSeat,
  createEvent: eventController.createEvent,
  updateEvent: eventController.updateEvent,
  deleteEvent: eventController.deleteEvent,
};