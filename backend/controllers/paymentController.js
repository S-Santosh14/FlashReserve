const crypto = require("crypto");

const Booking = require("../models/Booking");
const Payment = require("../models/Payment");
const Seat = require("../models/Seat");
const { isValidObjectId, requireFields } = require("../utils/validation");

async function mockPayment(req, res) {
  const missing = requireFields(req.body, ["bookingId", "amount"]);

  if (missing.length) {
    return res.status(400).json({
      success: false,
      message: `Missing required fields: ${missing.join(", ")}`,
    });
  }

  if (
    !isValidObjectId(req.body.bookingId) ||
    typeof req.body.amount !== "number" ||
    req.body.amount < 0
  ) {
    return res.status(400).json({
      success: false,
      message: "Provide a valid bookingId and amount",
    });
  }

  const booking = await Booking.findOne({
    _id: req.body.bookingId,
    userId: req.user.id,
  });

  if (!booking) {
    return res.status(404).json({
      success: false,
      message: "Booking not found",
    });
  }

  if (booking.status !== "pending") {
    return res.status(409).json({
      success: false,
      message: "Booking is not awaiting payment",
    });
  }

  if (req.body.amount !== booking.totalAmount) {
    return res.status(400).json({
      success: false,
      message: "Payment amount does not match booking total",
    });
  }

  if (
    req.body.shouldFail !== undefined &&
    typeof req.body.shouldFail !== "boolean"
  ) {
    return res.status(400).json({
      success: false,
      message: "shouldFail must be boolean when provided",
    });
  }

  // Make sure the seats are still reserved by this user
  // and their reservation has not expired.
  const seats = await Seat.find({
    _id: { $in: booking.seats },
    status: "reserved",
    reservedBy: req.user.id,
    reservationExpiresAt: { $gt: new Date() },
  });

  if (seats.length !== booking.seats.length) {
    booking.status = "cancelled";
    await booking.save();

    return res.status(409).json({
      success: false,
      message: "Seat reservation has expired. Please select the seats again.",
    });
  }

  const paymentStatus = req.body.shouldFail ? "failed" : "success";

  const payment = await Payment.create({
    bookingId: booking._id,
    userId: req.user.id,
    amount: req.body.amount,
    transactionId: `MOCK-${crypto.randomUUID()}`,
    status: paymentStatus,
  });

  // Payment failed → release seats.
  if (paymentStatus === "failed") {
    await Seat.updateMany(
      {
        _id: { $in: booking.seats },
        status: "reserved",
        reservedBy: req.user.id,
      },
      {
        $set: {
          status: "available",
          reservedBy: null,
          reservedAt: null,
          reservationExpiresAt: null,
        },
      },
    );

    return res.status(402).json({
      success: false,
      message: "Mock payment failed",
      data: { payment },
    });
  }

  // Payment succeeded → NOW make seats permanently booked.
  await Seat.updateMany(
    {
      _id: { $in: booking.seats },
      status: "reserved",
      reservedBy: req.user.id,
    },
    {
      $set: {
        status: "booked",
        reservedBy: null,
        reservedAt: null,
        reservationExpiresAt: null,
      },
    },
  );

  booking.status = "confirmed";
  await booking.save();

  return res.status(201).json({
    success: true,
    data: {
      payment,
      booking,
    },
  });
}

module.exports = { mockPayment };