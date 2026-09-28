const mongoose = require("mongoose");

const eventSchema = new mongoose.Schema(
  {
    title: { type: String, required: true, trim: true },
    category: { type: String, required: true, trim: true },
    venue: { type: String, required: true, trim: true },
    date: { type: Date, required: true },
    time: { type: String, required: true, trim: true },
    description: { type: String, required: true, trim: true },
    totalSeats: { type: Number, required: true, min: 0 },
    price: { type: Number, required: true, min: 0 },
    posterUrl: { type: String, default: "" },
  },
  { timestamps: true },
);

module.exports = mongoose.model("Event", eventSchema);