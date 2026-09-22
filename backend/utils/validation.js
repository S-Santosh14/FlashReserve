const mongoose = require("mongoose");

function isValidObjectId(value) {
  return mongoose.isValidObjectId(value);
}

function requireFields(body, fields) {
  return fields.filter((field) => body[field] === undefined || body[field] === null || body[field] === "");
}

module.exports = { isValidObjectId, requireFields };