"use strict";
// Offline receipt verifier: Ed25519 signature, SHA-256 hash and chain order per case.
// Same canonical JSON as relayloom/ap/receipts.py: sorted keys, no spaces, whole numbers without ".0".

const FIELDS = ["agent", "approver", "case", "decision", "detail", "input_hash", "ledger_readback", "model",
  "policy_hash", "prev", "response_id", "route", "seq", "step", "time"];
const GENESIS = "0".repeat(64);

function canonical(value) {
  if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]";
  if (value && typeof value === "object") {
    return "{" + Object.keys(value).sort().map((k) => JSON.stringify(k) + ":" + canonical(value[k])).join(",") + "}";
  }
  return JSON.stringify(value);
}

const bytes = (text) => new TextEncoder().encode(text);
const fromB64 = (b64) => Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
const hex = (buffer) => Array.from(new Uint8Array(buffer), (b) => b.toString(16).padStart(2, "0")).join("");

async function verifyReceipts(receipts, publicKeyB64, subtle = globalThis.crypto.subtle) {
  const key = await subtle.importKey("raw", fromB64(publicKeyB64), { name: "Ed25519" }, false, ["verify"]);
  const problems = [];
  const heads = new Map();
  for (const [index, receipt] of receipts.entries()) {
    const body = receipt.body || {};
    if (Object.keys(body).sort().join() !== FIELDS.join()) { problems.push(`receipt ${index}: unexpected fields`); continue; }
    const data = bytes(canonical(body));
    if (hex(await subtle.digest("SHA-256", data)) !== receipt.hash) problems.push(`receipt ${index}: hash does not match body`);
    if (!(await subtle.verify({ name: "Ed25519" }, key, fromB64(receipt.sig || ""), data))) problems.push(`receipt ${index}: bad signature`);
    const [seq, prev] = heads.get(body.case) || [0, GENESIS];
    if (body.seq !== seq + 1 || body.prev !== prev) problems.push(`receipt ${index}: chain broken for case ${body.case}`);
    heads.set(body.case, [body.seq, receipt.hash]);
  }
  return { ok: problems.length === 0, problems, count: receipts.length, cases: heads.size };
}

if (typeof module !== "undefined") module.exports = { canonical, verifyReceipts };
