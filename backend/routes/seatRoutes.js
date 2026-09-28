const express = require("express");

const authenticate = require("../middleware/authMiddleware");
const asyncHandler = require("../utils/asyncHandler");
const { listSeats, reserveSeat } = require("../controllers/seatController");

const router = express.Router();
router.get("/events/:eventId/seats", authenticate, asyncHandler(listSeats));
router.post("/events/:eventId/seats/reserve", authenticate, asyncHandler(reserveSeat));

module.exports = router;