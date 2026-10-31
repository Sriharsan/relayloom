// The browser verifier accepts receipts signed by Python and rejects tampered ones.
const test = require("node:test");
const assert = require("node:assert");
const { execFileSync } = require("node:child_process");
const path = require("node:path");
const { verifyReceipts } = require("../site/verify.js");

const root = path.resolve(__dirname, "..");
const script = `
import json, tempfile, pathlib
from relayloom.ap.receipts import Signer, ReceiptChain
d = pathlib.Path(tempfile.mkdtemp())
s = Signer(d / "k"); c = ReceiptChain(d / "r.jsonl", s, "p" * 64)
c.append("match", "Reader", "read", "extracted", model="glimmer", detail={"bill": {"qty": 24.0, "tax": 1771.2, "name": "Velan é"}})
c.append("match", "Checker", "check", "entered and checked", detail={"ok": True, "lines": [1, 2.5]})
c.append("short", "Matcher", "match", "mismatch", detail={})
print(json.dumps({"key": s.public_key, "receipts": c.read()}))`;
const out = JSON.parse(execFileSync("python", ["-c", script], { cwd: root, encoding: "utf8" }));

test("receipts signed in Python verify in the browser code", async () => {
  const result = await verifyReceipts(out.receipts, out.key);
  assert.deepStrictEqual(result.problems, []);
  assert.strictEqual(result.cases, 2);
});

test("a changed decision or a dropped receipt fails", async () => {
  const changed = JSON.parse(JSON.stringify(out.receipts));
  changed[1].body.decision = "something else";
  assert.strictEqual((await verifyReceipts(changed, out.key)).ok, false);
  assert.strictEqual((await verifyReceipts([out.receipts[0], out.receipts[2], out.receipts[1]].slice(1), out.key)).ok, false);
});
