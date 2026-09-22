const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");

const User = require("../models/User");
const { requireFields } = require("../utils/validation");

function publicUser(user) {
  return { id: user._id, name: user.name, email: user.email, role: user.role, createdAt: user.createdAt };
}

function createToken(user) {
  if (!process.env.JWT_SECRET) {
    const error = new Error("JWT configuration is unavailable");
    error.statusCode = 500;
    throw error;
  }

  return jwt.sign({ id: user._id.toString(), role: user.role, email: user.email }, process.env.JWT_SECRET, { expiresIn: "1d" });
}

async function register(req, res) {
  const missing = requireFields(req.body, ["name", "email", "password"]);
  if (missing.length) {
    return res.status(400).json({ success: false, message: `Missing required fields: ${missing.join(", ")}` });
  }

  const email = req.body.email.trim().toLowerCase();
  if (!/^\S+@\S+\.\S+$/.test(email) || typeof req.body.password !== "string" || req.body.password.length < 8) {
    return res.status(400).json({ success: false, message: "Provide a valid email and a password of at least 8 characters" });
  }

  const existingUser = await User.findOne({ email });
  if (existingUser) {
    return res.status(409).json({ success: false, message: "Email is already registered" });
  }

  try {
    const user = await User.create({ name: req.body.name, email, password: await bcrypt.hash(req.body.password, 12), role: "customer" });
    return res.status(201).json({ success: true, data: { user: publicUser(user), token: createToken(user) } });
  } catch (error) {
    if (error.code === 11000) {
      return res.status(409).json({ success: false, message: "Email is already registered" });
    }
    throw error;
  }
}

async function login(req, res) {
  const missing = requireFields(req.body, ["email", "password"]);
  if (missing.length) {
    return res.status(400).json({ success: false, message: `Missing required fields: ${missing.join(", ")}` });
  }

  const user = await User.findOne({ email: req.body.email.trim().toLowerCase() }).select("+password");
  if (!user || !(await bcrypt.compare(req.body.password, user.password))) {
    return res.status(401).json({ success: false, message: "Invalid email or password" });
  }

  return res.json({ success: true, data: { user: publicUser(user), token: createToken(user) } });
}

module.exports = { register, login };