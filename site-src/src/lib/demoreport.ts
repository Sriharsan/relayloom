import { casePhotos, supplierName, type BenchCase, type SignedReceipt } from "@/data/site";
import type { Report } from "@/lib/report";

const STEP: Record<string, string> = {
  intake: "Bill received", mask: "Private numbers masked", read: "Bill read", injection_check: "Hidden text checked and ignored", count: "Goods counted",
  match: "Order, bill and goods compared", investigate: "Evidence reviewed", diagnose: "Likely cause named", propose: "Next step proposed", draft: "Supplier message drafted",
  enter: "Bill entered in the books", check: "Entry read back and checked", file: "Case filed", decision: "Owner decision", send: "Message sent", close: "Case closed",
  reconcile: "Books reconciled after reconnecting",
};
const inr = (n: number) => `Rs ${n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

async function toJpeg(url: string): Promise<{ jpeg: Uint8Array; w: number; h: number } | null> {
  try {
    const blob = await (await fetch(url)).blob();
    const bmp = await createImageBitmap(blob);
    const c = document.createElement("canvas");
    c.width = bmp.width;
    c.height = bmp.height;
    c.getContext("2d")!.drawImage(bmp, 0, 0);
    const data = atob(c.toDataURL("image/jpeg", 0.86).split(",")[1] ?? "");
    return { jpeg: Uint8Array.from(data, (ch) => ch.charCodeAt(0)), w: bmp.width, h: bmp.height };
  } catch {
    return null;
  }
}

/** The demo case as a structured report, with the counted photos attached as evidence. */
export async function buildDemoReport(c: BenchCase, receipts: SignedReceipt[], verified: boolean, publicKey: string): Promise<Report> {
  const rows = c.match?.rows ?? [];
  const held = !(c.match?.matched ?? true);
  const reasons = rows.flatMap((r) => r.issues.map((i) => `${r.description}: ${i}`));
  const bill = c.bill;
  const evidence: Report["evidence"] = [];
  for (const p of casePhotos(c).filter((x) => x.counted).slice(0, 4)) {
    const img = await toJpeg(p.image);
    if (img) evidence.push({ label: p.photo, caption: `${p.count} counted by SAM 3.1. Each item is outlined and numbered.`, ...img });
  }
  return {
    title: "Delivery check receipt, from the recorded demo run",
    held,
    headline: held ? `${c.bill_no} should not be paid as it stands.` : `${c.bill_no} matches the order and the goods.`,
    reasons: held ? reasons : ["Order, bill and goods agree."],
    facts: [["Supplier", supplierName(c.supplier_id)], ["Bill number", c.bill_no], ["Order number", c.po_number], ["Bill date", bill?.bill_date ?? "-"]],
    items: rows.map((r) => ({ item: r.description, ordered: r.po_qty, billed: r.bill_qty, good: r.received, damaged: 0, note: r.issues.join(". ") })),
    totals: bill ? [["Items", inr(bill.total_inr - bill.tax_inr)], ["Tax", inr(bill.tax_inr)], ["Bill total", inr(bill.total_inr)]] : [],
    steps: receipts.map((r) => `${STEP[r.body.step] ?? r.body.step.replace(/_/g, " ")}: ${r.body.decision}.`),
    evidence,
    proof: [`Public key: ${publicKey}`, `Fingerprint of the last step: ${receipts[receipts.length - 1]?.hash ?? ""}`, "Verify the chain in your browser on the Proof page, or offline with relayloom verify."],
    verified,
  };
}
