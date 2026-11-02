/*
 * Receipt verifier that runs in the browser: Ed25519 signature, SHA-256 hash and chain order per case.
 * Same canonical JSON as relayloom/ap/receipts.py: sorted keys, no spaces, whole numbers without ".0".
 */
import type { SignedReceipt } from "@/data/site";

const FIELDS = [
  "agent", "approver", "case", "decision", "detail", "input_hash", "ledger_readback", "model",
  "policy_hash", "prev", "response_id", "route", "seq", "step", "time",
];
const GENESIS = "0".repeat(64);

export function canonical(value: unknown): string {
  if (Array.isArray(value)) return "[" + value.map(canonical).join(",") + "]";
  if (value && typeof value === "object") {
    const o = value as Record<string, unknown>;
    return "{" + Object.keys(o).sort().map((k) => JSON.stringify(k) + ":" + canonical(o[k])).join(",") + "}";
  }
  return JSON.stringify(value);
}

const bytes = (t: string) => new TextEncoder().encode(t);
const fromB64 = (b: string) => Uint8Array.from(atob(b), (c) => c.charCodeAt(0));
const hex = (buf: ArrayBuffer) => Array.from(new Uint8Array(buf), (b) => b.toString(16).padStart(2, "0")).join("");

export type Verdict = { ok: boolean; reason: string };

export async function verifyChain(receipts: SignedReceipt[], publicKeyB64: string): Promise<Verdict[]> {
  const subtle = globalThis.crypto.subtle;
  const key = await subtle.importKey("raw", fromB64(publicKeyB64), { name: "Ed25519" }, false, ["verify"]);
  const heads = new Map<string, [number, string]>();
  const out: Verdict[] = [];
  for (const r of receipts) {
    const body = r.body as Record<string, unknown>;
    if (Object.keys(body).sort().join() !== FIELDS.join()) {
      out.push({ ok: false, reason: "unexpected fields" });
      continue;
    }
    const data = bytes(canonical(body));
    const hashOk = hex(await subtle.digest("SHA-256", data)) === r.hash;
    const sigOk = await subtle.verify({ name: "Ed25519" }, key, fromB64(r.sig || ""), data);
    const [seq, prev] = heads.get(String(body.case)) ?? [0, GENESIS];
    const chainOk = body.seq === seq + 1 && body.prev === prev;
    heads.set(String(body.case), [Number(body.seq), r.hash]);
    out.push(
      !hashOk ? { ok: false, reason: "hash does not match the content" }
      : !sigOk ? { ok: false, reason: "signature does not verify" }
      : !chainOk ? { ok: false, reason: "chain order broken" }
      : { ok: true, reason: "signature, hash and chain verified" },
    );
  }
  return out;
}
