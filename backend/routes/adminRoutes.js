const express = require("express");
const multer = require("multer");
const path = require("path");

const authenticate = require("../middleware/authMiddleware");
const requireAdmin = require("../middleware/adminMiddleware");
const asyncHandler = require("../utils/asyncHandler");
const { listUsers, listBookings, listEvents, getStats, listSeats, updateSeat, createEvent, updateEvent, deleteEvent } = require("../controllers/adminController");

const router = express.Router();
const upload = multer({
	storage: multer.diskStorage({
		destination: path.join(__dirname, "../uploads/events"),
		filename: (_req, file, callback) => callback(null, `${Date.now()}-${file.originalname.replace(/[^a-zA-Z0-9._-]/g, "_")}`),
	}),
	limits: { fileSize: 5 * 1024 * 1024 },
	fileFilter: (_req, file, callback) => callback(null, ["image/png", "image/jpeg", "image/webp"].includes(file.mimetype)),
});
router.use(authenticate, requireAdmin);
router.get("/users", asyncHandler(listUsers));
router.get("/bookings", asyncHandler(listBookings));
router.get("/events", asyncHandler(listEvents));
router.get("/stats", asyncHandler(getStats));
router.get("/events/:eventId/seats", asyncHandler(listSeats));
router.put("/seats/:seatId", asyncHandler(updateSeat));
router.post("/events", upload.single("poster"), asyncHandler(createEvent));
router.put("/events/:id", upload.single("poster"), asyncHandler(updateEvent));
router.delete("/events/:id", asyncHandler(deleteEvent));

module.exports = router;