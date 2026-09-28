const Event = require("../models/Event");
const Seat = require("../models/Seat");
const { isValidObjectId, requireFields } = require("../utils/validation");

const RESERVATION_TIMEOUT_SECONDS =
  Number(process.env.RESERVATION_TIMEOUT_SECONDS) || 30;

async function releaseExpiredReservations(eventId) {
  await Seat.updateMany(
    {
      eventId,
      status: "reserved",
      reservationExpiresAt: { $lte: new Date() },
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
}

async function listSeats(req, res) {
  if (!isValidObjectId(req.params.eventId)) {
    return res.status(400).json({
      success: false,
      message: "Invalid event id",
    });
  }

  const event = await Event.exists({ _id: req.params.eventId });

  if (!event) {
    return res.status(404).json({
      success: false,
      message: "Event not found",
    });
  }

  // Release seats whose reservation time has expired.
  await releaseExpiredReservations(req.params.eventId);

  const seats = await Seat.find({
    eventId: req.params.eventId,
  }).sort({ seatNumber: 1 });

  return res.json({
    success: true,
    data: seats,
  });
}

async function reserveSeat(req, res) {
  const { eventId } = req.params;

  const missing = requireFields(req.body, ["seatNumber"]);

  if (!isValidObjectId(eventId)) {
    return res.status(400).json({
      success: false,
      message: "Invalid event id",
    });
  }

  if (missing.length) {
    return res.status(400).json({
      success: false,
      message: "seatNumber is required",
    });
  }

  // Release expired reservations before attempting a new reservation.
  await releaseExpiredReservations(eventId);

  const expiresAt = new Date(
    Date.now() + RESERVATION_TIMEOUT_SECONDS * 1000,
  );

  // Atomic reservation.
  // Only one concurrent request can change an available seat.
  const seat = await Seat.findOneAndUpdate(
    {
      eventId,
      seatNumber: req.body.seatNumber.trim(),
      status: "available",
    },
    {
      $set: {
        status: "reserved",
        reservedBy: req.user.id,
        reservedAt: new Date(),
        reservationExpiresAt: expiresAt,
      },
    },
    { new: true },
  );

  if (!seat) {
    return res.status(409).json({
      success: false,
      message: "Seat is already reserved or unavailable",
    });
  }

  return res.status(201).json({
    success: true,
    data: seat,
  });
}

module.exports = {
  listSeats,
  reserveSeat,
};