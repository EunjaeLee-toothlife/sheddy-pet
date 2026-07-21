"use strict";

const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const DIALOGUE_DIR = path.join(__dirname, "..", "dialogues", "ko");
const CATEGORIES = ["idle", "basic", "happy", "excited", "special", "sad"];
const mode = process.argv[2] || "check";

if (!new Set(["check", "sync"]).has(mode)) {
  console.error("Usage: node tools/dialogue_hashes.js [check|sync]");
  process.exit(2);
}

function normalize(text) {
  if (typeof text !== "string") throw new Error("text must be a string");
  const normalized = text.normalize("NFC").trim();
  if (!normalized) throw new Error("text must not be empty");
  return normalized;
}

function hashOf(text) {
  return `sha256:${crypto.createHash("sha256").update(text, "utf8").digest("hex")}`;
}

const seenTexts = new Map();
const seenHashes = new Map();
const errors = [];
const syncedFiles = [];

for (const category of CATEGORIES) {
  const file = path.join(DIALOGUE_DIR, `${category}.json`);
  let entries;
  try {
    entries = JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (error) {
    errors.push(`${category}: cannot read JSON (${error.message})`);
    continue;
  }

  if (!Array.isArray(entries) || entries.length === 0) {
    errors.push(`${category}: expected a non-empty array`);
    continue;
  }

  const synced = [];
  entries.forEach((entry, index) => {
    const location = `${category}[${index}]`;
    try {
      const text = normalize(typeof entry === "string" ? entry : entry?.text);
      const hash = hashOf(text);

      if (seenTexts.has(text)) {
        errors.push(`${location}: duplicate text (first: ${seenTexts.get(text)})`);
      } else {
        seenTexts.set(text, location);
      }
      if (seenHashes.has(hash)) {
        errors.push(`${location}: duplicate hash (first: ${seenHashes.get(hash)})`);
      } else {
        seenHashes.set(hash, location);
      }

      if (mode === "check") {
        if (!entry || typeof entry !== "object" || Array.isArray(entry)) {
          errors.push(`${location}: expected { hash, text } object`);
        } else if (entry.text !== text) {
          errors.push(`${location}: text is not trimmed NFC`);
        } else if (entry.hash !== hash) {
          errors.push(`${location}: hash mismatch (expected ${hash})`);
        } else if (Object.keys(entry).sort().join(",") !== "hash,text") {
          errors.push(`${location}: only hash and text fields are allowed`);
        }
      }

      synced.push({ hash, text });
    } catch (error) {
      errors.push(`${location}: ${error.message}`);
    }
  });

  syncedFiles.push({ file, entries: synced });
}

const actualCategories = fs.readdirSync(DIALOGUE_DIR)
  .filter(file => file.endsWith(".json"))
  .map(file => path.basename(file, ".json"))
  .sort();
const expectedCategories = [...CATEGORIES].sort();
if (actualCategories.join(",") !== expectedCategories.join(",")) {
  errors.push(`category files mismatch (expected: ${expectedCategories.join(", ")})`);
}

if (errors.length) {
  errors.forEach(error => console.error(`- ${error}`));
  process.exit(1);
}

if (mode === "sync") {
  syncedFiles.forEach(({ file, entries }) => {
    fs.writeFileSync(file, `${JSON.stringify(entries, null, 2)}\n`);
  });
}

console.log(`${mode}: ${seenTexts.size} dialogue lines across ${CATEGORIES.length} categories`);
