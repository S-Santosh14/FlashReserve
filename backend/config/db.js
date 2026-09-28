require("dotenv").config();

const mongoose = require("mongoose");

async function connectDB() {
  if (!process.env.MONGODB_URI) {
    throw new Error("MONGODB_URI is missing from environment variables.");
  }

  const hasSupportedScheme = process.env.MONGODB_URI.startsWith("mongodb://") || process.env.MONGODB_URI.startsWith("mongodb+srv://");
  if (!hasSupportedScheme) {
    throw new Error("MONGODB_URI has an invalid MongoDB scheme.");
  }

  try {
    await mongoose.connect(process.env.MONGODB_URI);
    console.log(`MongoDB connected successfully (database: ${mongoose.connection.name}).`);
  } catch (error) {
    const sanitizedError = new Error(error.name === "MongoParseError" ? "MongoDB connection string could not be parsed." : "MongoDB connection failed.");
    sanitizedError.name = error.name || "MongoDBConnectionError";
    console.error(`MongoDB connection failed (${sanitizedError.name}): ${sanitizedError.message}`);
    throw sanitizedError;
  }
}

module.exports = connectDB;