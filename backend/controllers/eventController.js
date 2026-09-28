const Event = require("../models/Event");
const Seat = require("../models/Seat");
const { isValidObjectId, requireFields } = require("../utils/validation");

const eventFields = ["title", "category", "venue", "date", "time", "description", "totalSeats", "price"];

function seatNumbers(totalSeats) {
  return Array.from({ length: totalSeats }, (_value, index) => `A${index + 1}`);
}

async function listEvents(_req, res) {
  const events = await Event.find().sort({ date: 1, createdAt: -1 });
  return res.json({ success: true, data: events });
}

async function getEvent(req, res) {
  if (!isValidObjectId(req.params.id)) {
    return res.status(400).json({ success: false, message: "Invalid event id" });
  }
  const event = await Event.findById(req.params.id);
  if (!event) return res.status(404).json({ success: false, message: "Event not found" });
  return res.json({ success: true, data: event });
}

async function createEvent(req, res) {
  const missing = requireFields(req.body, eventFields);
  if (missing.length) return res.status(400).json({ success: false, message: `Missing required fields: ${missing.join(", ")}` });
  const totalSeats = Number(req.body.totalSeats);
  const price = Number(req.body.price);
  if (!Number.isInteger(totalSeats) || totalSeats < 1 || !Number.isFinite(price) || price < 0) {
    return res.status(400).json({ success: false, message: "totalSeats must be a positive integer and price must be a non-negative number" });
  }

  const event = await Event.create({ ...req.body, totalSeats, price, posterUrl: req.file ? `/uploads/events/${req.file.filename}` : req.body.posterUrl || "" });
  await Seat.insertMany(seatNumbers(event.totalSeats).map((seatNumber) => ({ eventId: event._id, seatNumber })), { ordered: true });
  return res.status(201).json({ success: true, data: event });
}

async function updateEvent(req, res) {
  if (!isValidObjectId(req.params.id)) return res.status(400).json({ success: false, message: "Invalid event id" });
  const allowed = Object.fromEntries(eventFields.filter((field) => req.body[field] !== undefined).map((field) => [field, req.body[field]]));
  if (allowed.totalSeats !== undefined) allowed.totalSeats = Number(allowed.totalSeats);
  if (allowed.price !== undefined) allowed.price = Number(allowed.price);
  if (allowed.totalSeats !== undefined && (!Number.isInteger(allowed.totalSeats) || allowed.totalSeats < 1)) {
    return res.status(400).json({ success: false, message: "totalSeats must be a positive integer" });
  }
  if (allowed.price !== undefined && (!Number.isFinite(allowed.price) || allowed.price < 0)) {
    return res.status(400).json({ success: false, message: "price must be a non-negative number" });
  }

  if (allowed.totalSeats !== undefined) {
    const currentCount = await Seat.countDocuments({ eventId: req.params.id });
    if (allowed.totalSeats < currentCount) return res.status(400).json({ success: false, message: "totalSeats cannot be below the existing seat count" });
  }

  if (req.file) allowed.posterUrl = `/uploads/events/${req.file.filename}`;
  const event = await Event.findByIdAndUpdate(req.params.id, allowed, { new: true, runValidators: true });
  if (!event) return res.status(404).json({ success: false, message: "Event not found" });
  if (allowed.totalSeats !== undefined) {
    const currentCount = await Seat.countDocuments({ eventId: event._id });
    if (allowed.totalSeats > currentCount) {
      await Seat.insertMany(seatNumbers(allowed.totalSeats).slice(currentCount).map((seatNumber) => ({ eventId: event._id, seatNumber })));
    }
  }
  return res.json({ success: true, data: event });
}

async function deleteEvent(req, res) {
  if (!isValidObjectId(req.params.id)) return res.status(400).json({ success: false, message: "Invalid event id" });
  const event = await Event.findByIdAndDelete(req.params.id);
  if (!event) return res.status(404).json({ success: false, message: "Event not found" });
  await Seat.deleteMany({ eventId: event._id });
  return res.json({ success: true, message: "Event deleted" });
}

module.exports = { listEvents, getEvent, createEvent, updateEvent, deleteEvent };