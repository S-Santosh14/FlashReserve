const express = require("express");

const asyncHandler = require("../utils/asyncHandler");
const { listEvents, getEvent } = require("../controllers/eventController");

const router = express.Router();
router.get("/", asyncHandler(listEvents));
router.get("/:id", asyncHandler(getEvent));

module.exports = router;