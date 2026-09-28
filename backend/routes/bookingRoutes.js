const express = require("express");

const authenticate = require("../middleware/authMiddleware");
const asyncHandler = require("../utils/asyncHandler");
const { createBooking, listBookings, getBooking, cancelBooking } = require("../controllers/bookingController");

const router = express.Router();
router.use(authenticate);
router.post("/", asyncHandler(createBooking));
router.get("/", asyncHandler(listBookings));
router.get("/:id", asyncHandler(getBooking));
router.put("/:id/cancel", asyncHandler(cancelBooking));

module.exports = router;