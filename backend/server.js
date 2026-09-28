require("dotenv").config();

const cors = require("cors");
const express = require("express");
const path = require("path");

const connectDB = require("./config/db");
const chatRoutes = require("./routes/chatRoutes");
const adminRoutes = require("./routes/adminRoutes");
const authRoutes = require("./routes/authRoutes");
const bookingRoutes = require("./routes/bookingRoutes");
const eventRoutes = require("./routes/eventRoutes");
const paymentRoutes = require("./routes/paymentRoutes");
const seatRoutes = require("./routes/seatRoutes");

const app = express();
const port = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());
app.use("/uploads", express.static(path.join(__dirname, "uploads")));

app.use("/api/auth", authRoutes);
app.use("/api/events", eventRoutes);
app.use("/api", seatRoutes);
app.use("/api/bookings", bookingRoutes);
app.use("/api/payments", paymentRoutes);
app.use("/api/chat", chatRoutes);
app.use("/api/admin", adminRoutes);

app.get("/api/health", (_req, res) => {
  res.json({ success: true, status: "ok", service: "FlashReserve backend" });
});

app.use((_req, res) => {
  res.status(404).json({ success: false, message: "Route not found" });
});

app.use((error, _req, res, _next) => {
  const statusCode = error.statusCode || (error.name === "ValidationError" ? 400 : 500);
  const message = statusCode === 500 ? "Internal server error" : error.message;
  console.error(`Request failed (${statusCode}): ${error.name || "Error"}`);
  res.status(statusCode).json({ success: false, message });
});

async function startServer() {
  try {
    await connectDB();
    app.listen(port, () => {
      console.log(`FlashReserve backend listening on port ${port}.`);
    });
  } catch (_error) {
    console.error("FlashReserve backend could not start because MongoDB is unavailable.");
    process.exitCode = 1;
  }
}

if (require.main === module) {
  startServer();
}

module.exports = app;