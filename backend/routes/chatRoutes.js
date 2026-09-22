const express = require("express");

const authenticate = require("../middleware/authMiddleware");
const asyncHandler = require("../utils/asyncHandler");
const { chat, health } = require("../controllers/chatController");

const router = express.Router();
router.get("/health", asyncHandler(health));
router.post("/", authenticate, asyncHandler(chat));

module.exports = router;