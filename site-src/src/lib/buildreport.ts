import { amounts, country, isBlank, money, type Delivery, type Verdict } from "@/lib/matcher";
import type { Report } from "@/lib/report";
import type { Signed } from "@/lib/sign";

const jpegBytes = (dataUrl: string) => Uint8Array.from(atob(dataUrl.split(",")[1] ?? ""), (c) => c.charCodeAt(0));

export async function imageSize(dataUrl: string): Promise<{ w: number; h: number }> {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = () => resolve({ w: img.naturalWidth, h: img.naturalHeight });
    img.onerror = () => resolve({ w: 800, h: 600 });
    img.src = dataUrl;
  });
}

/** Everything in plain words: what was billed, what arrived, why it was held, and the proof. */
export async function buildReport(d: Delivery, v: Verdict, s: Signed): Promise<Report> {
  const c = country(d);
  const lines = d.lines.filter((l) => !isBlank(l));
  const a = amounts(d);
  const evidence: Report["evidence"] = [];
  for (const l of lines) {
    if (!l.photo) continue;
    const size = await imageSize(l.photo);
    const bad = l.damaged ? `, ${l.damaged} marked damaged` : "";
    evidence.push({ label: l.description || l.item_code, caption: `${l.received} counted on the photo${bad}. Numbered marks show each item.`, jpeg: jpegBytes(l.photo), w: size.w, h: size.h });
  }
  const damaged = lines.reduce((x, l) => x + l.damaged, 0);
  const steps = [
    `The bill ${d.bill_no || "(no number)"} from ${d.supplier || "the supplier"} was entered: ${lines.map((l) => `${l.billed_qty} x ${l.description || l.item_code} at ${money(l.billed_rate, c.currency)}`).join("; ")}.`,
    `The goods were counted on arrival: ${lines.map((l) => `${l.received} of ${l.description || l.item_code}`).join("; ")}.`,
    ...(damaged ? [`${damaged} units arrived damaged, so they do not count as received.`] : []),
    ...(evidence.length ? [`${evidence.length} photo${evidence.length > 1 ? "s were" : " was"} kept as evidence. Their fingerprints are in the signed receipt, so a photo cannot be swapped later.`] : []),
    v.held ? "The order, the bill and the goods were compared and they do not agree. The bill is held for a person." : "The order, the bill and the goods were compared and they agree within the policy limits.",
  ];
  return {
    title: "Delivery check receipt",
    held: v.held,
    headline: v.held ? `${d.bill_no || "This bill"} should not be paid as it stands.` : `${d.bill_no || "This bill"} matches the order and the goods.`,
    reasons: v.held ? v.reasons : [`Order, bill and goods agree. Total ${money(a.total, c.currency)}.`],
    facts: [["Supplier", d.supplier || "-"], ["Bill number", d.bill_no || "-"], ["Order number", d.po_no || "-"], ["Country and tax", `${c.name}, ${c.tax} ${d.tax_rate} percent`]],
    items: v.rows.map((r) => ({ item: r.description, ordered: r.ordered, billed: r.billed, good: r.received, damaged: r.damaged, note: r.issues.join(". ") })),
    totals: [["Items", money(a.subtotal, c.currency)], [`${c.tax} at ${d.tax_rate} percent`, money(a.tax, c.currency)], ["Bill total", money(a.total, c.currency)]],
    steps,
    evidence,
    proof: [`Public key: ${s.publicKey}`, `Fingerprint of the last step: ${s.receipts[s.receipts.length - 1]?.hash ?? ""}`, "Check it on any machine, offline: put receipts.jsonl and public_key.txt in one folder and run relayloom verify receipts.jsonl"],
    verified: s.verified,
  };
}
