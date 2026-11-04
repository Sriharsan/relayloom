/** Signs a live check as a receipt chain in the browser. The files verify with `relayloom verify` on any machine, offline. */
import { canonical, verifyChain } from "@/lib/receipts";
import type { SignedReceipt } from "@/data/site";
import type { Delivery, Verdict } from "@/lib/matcher";

const GENESIS = "0".repeat(64);
const enc = (t: string) => new TextEncoder().encode(t);
const hex = (buf: ArrayBuffer) => Array.from(new Uint8Array(buf), (b) => b.toString(16).padStart(2, "0")).join("");
const b64 = (buf: ArrayBuffer) => btoa(String.fromCharCode(...new Uint8Array(buf)));

export const cryptoReady = () => typeof globalThis.crypto?.subtle !== "undefined";

function stamp(): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  const off = -d.getTimezoneOffset();
  const sign = off >= 0 ? "+" : "-";
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}${sign}${p(Math.floor(Math.abs(off) / 60))}${p(Math.abs(off) % 60)}`;
}

export interface Signed {
  receipts: SignedReceipt[];
  publicKey: string;
  verified: boolean;
}

export async function signCheck(d: Delivery, v: Verdict, policyHash: string): Promise<Signed> {
  const subtle = globalThis.crypto.subtle;
  const pair = (await subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"])) as CryptoKeyPair;
  const publicKey = b64(await subtle.exportKey("raw", pair.publicKey));
  const steps: { agent: string; step: string; decision: string; detail: Record<string, unknown>; input: unknown }[] = [
    { agent: "Reader", step: "read", decision: "given as structured data", input: d, detail: { bill: { supplier_id: d.supplier, bill_no: d.bill_no, po_number: d.po_no, total_inr: d.total, tax_inr: d.tax,
      lines: d.lines.map((l) => ({ item_code: l.item_code, description: l.description, qty: l.billed_qty, rate_inr: l.billed_rate, amount_inr: Math.round(l.billed_qty * l.billed_rate * 100) / 100 })) } } },
    { agent: "Counter", step: "count", decision: "counted " + d.lines.map((l) => `${l.item_code} ${l.received}`).join(", "), input: d.lines.map((l) => l.received), detail: { counts: Object.fromEntries(d.lines.map((l) => [l.item_code, l.received])) } },
  ];
  const damaged = d.lines.reduce((s, l) => s + l.damaged, 0);
  if (damaged > 0) {
    const arrived = d.lines.reduce((s, l) => s + l.received, 0);
    steps.push({ agent: "Counter", step: "condition", decision: `${damaged} of ${arrived} damaged`, input: d.lines.map((l) => l.damaged), detail: { reason: `${damaged} of ${arrived} units arrived damaged, so only ${arrived - damaged} count as received.` } });
  }
  steps.push({ agent: "Matcher", step: "match", decision: v.held ? "held" : "clear to enter", input: v, detail: { problems: v.reasons } });

  const caseId = d.bill_no || "live-check";
  const receipts: SignedReceipt[] = [];
  let prev = GENESIS;
  for (let i = 0; i < steps.length; i++) {
    const s = steps[i]!;
    const body = {
      case: caseId, seq: i + 1, prev, time: stamp(), agent: s.agent, step: s.step, policy_hash: policyHash,
      input_hash: hex(await subtle.digest("SHA-256", enc(canonical(s.input)))), model: "", route: "your browser", response_id: "", decision: s.decision,
      approver: "", ledger_readback: "", detail: s.detail,
    };
    const data = enc(canonical(body));
    const hash = hex(await subtle.digest("SHA-256", data));
    const sig = b64(await subtle.sign({ name: "Ed25519" }, pair.privateKey, data));
    receipts.push({ body: body as SignedReceipt["body"], hash, sig });
    prev = hash;
  }
  const verdicts = await verifyChain(receipts, publicKey);
  return { receipts, publicKey, verified: verdicts.every((x) => x.ok) };
}

export function toJsonl(receipts: SignedReceipt[]): string {
  return receipts.map((r) => JSON.stringify(r)).join("\n") + "\n";
}

export function saveText(name: string, text: string, type = "text/plain") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 2000);
}
