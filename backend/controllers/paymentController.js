const crypto = require("crypto");

const Booking = require("../models/Booking");
const Payment = require("../models/Payment");
const { isValidObjectId, requireFields } = require("../utils/validation");

async function mockPayment(req, res) {
  const missing = requireFields(req.body, ["bookingId", "amount"]);
  if (missing.length) return res.status(400).json({ success: false, message: `Missing required fields: ${missing.join(", ")}` });
  if (!isValidObjectId(req.body.bookingId) || typeof req.body.amount !== "number" || req.body.amount < 0) return res.status(400).json({ success: false, message: "Provide a valid bookingId and amount" });

  const booking = await Booking.findOne({ _id: req.body.bookingId, userId: req.user.id });
  if (!booking) return res.status(404).json({ success: false, message: "Booking not found" });
  if (booking.status !== "pending") return res.status(409).json({ success: false, message: "Booking is not awaiting payment" });
  if (req.body.amount !== booking.totalAmount) return res.status(400).json({ success: false, message: "Payment amount does not match booking total" });

  if (req.body.shouldFail !== undefined && typeof req.body.shouldFail !== "boolean") {
    return res.status(400).json({ success: false, message: "shouldFail must be boolean when provided" });
  }

  const paymentStatus = req.body.shouldFail ? "failed" : "success";
  const payment = await Payment.create({ bookingId: booking._id, userId: req.user.id, amount: req.body.amount, transactionId: `MOCK-${crypto.randomUUID()}`, status: paymentStatus });
  if (paymentStatus === "failed") {
    return res.status(402).json({ success: false, message: "Mock payment failed", data: { payment } });
  }

  booking.status = "confirmed";
  await booking.save();
  return res.status(201).json({ success: true, data: { payment, booking } });
}

module.exports = { mockPayment };