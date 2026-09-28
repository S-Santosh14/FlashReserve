require("dotenv").config();

const bcrypt = require("bcryptjs");
const readline = require("readline");

const connectDB = require("../config/db");
const User = require("../models/User");

const adminAccounts = [
  { name: "FlashReserve Admin One", email: "admin1@flashreserve.local" },
  { name: "FlashReserve Admin Two", email: "admin2@flashreserve.local" },
  { name: "FlashReserve Admin Three", email: "admin3@flashreserve.local" },
];

async function promptForPasswords() {
  const interface = readline.createInterface({ input: process.stdin, output: process.stdout });
  const passwords = [];
  for (const account of adminAccounts) {
    const password = await new Promise((resolve) => {
      interface.question(`Password for ${account.email}: `, resolve);
    });
    if (!password) {
      interface.close();
      throw new Error("Admin passwords cannot be empty.");
    }
    passwords.push(password);
  }
  interface.close();
  return passwords;
}

async function seedAdmins(passwords) {
  for (const [index, account] of adminAccounts.entries()) {
    const password = passwords[index];
    const hashedPassword = await bcrypt.hash(password, 12);
    await User.findOneAndUpdate(
      { email: account.email },
      { name: account.name, email: account.email, password: hashedPassword, role: "admin" },
      { upsert: true, new: true, runValidators: true, setDefaultsOnInsert: true },
    );
  }

  console.log("Exactly three admin accounts were seeded successfully.");
}

async function run() {
  try {
    await connectDB();
    const passwords = await promptForPasswords();
    await seedAdmins(passwords);
  } catch (error) {
    console.error(`Admin seed failed: ${error.message}`);
    process.exitCode = 1;
  } finally {
    const mongoose = require("mongoose");
    await mongoose.disconnect();
  }
}

run();