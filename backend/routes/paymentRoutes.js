const express = require("express");

const authenticate = require("../middleware/authMiddleware");
const asyncHandler = require("../utils/asyncHandler");
const { mockPayment } = require("../controllers/paymentController");

const router = express.Router();
router.post("/mock", authenticate, asyncHandler(mockPayment));

module.exports = router;