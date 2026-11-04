/** A plain language PDF receipt, made in the browser with no library and no network. Same layout as `relayloom receipt`. */
import type { SignedReceipt } from "@/data/site";

type Style = "title" | "head" | "body" | "small";
const SIZES: Record<Style, [number, number, number]> = { title: [20, 28, 52], head: [12.5, 20, 78], body: [10.5, 15, 92], small: [8.5, 12, 112] };

const STEP_WORDS: Record<string, string> = {
    intake: "Bill received", mask: "Private numbers masked", read: "Bill read", injection_check: "Hidden text checked and ignored", count: "Goods counted", condition: "Condition of the goods checked",
  match: "Order, bill and goods compared", investigate: "Evidence reviewed", diagnose: "Likely cause named", propose: "Next step proposed", draft: "Supplier message drafted",
  enter: "Bill entered in the books", check: "Entry read back and checked", file: "Case filed", decision: "Owner decision", send: "Message sent", close: "Case closed",
  reconcile: "Books reconciled after reconnecting", dispute: "Dispute prepared", hold: "Held for a person",
};

const latin = (s: string) =>
  s.replace(/₹/g, "Rs ").replace(/[–—]/g, "-").replace(/[‘’]/g, "'").replace(/[“”]/g, '"').replace(/[^\x20-\x7e\xa0-\xff]/g, "?");
const esc = (s: string) => latin(s).replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");

function wrap(text: string, width: number): string[] {
  const out: string[] = [];
  let line = "";
  for (const word of latin(text).split(/\s+/)) {
    if ((line + " " + word).trim().length > width) { out.push(line); line = word; } else line = (line + " " + word).trim();
  }
  out.push(line);
  return out;
}

export function makePdf(lines: [Style, string][]): Blob {
  const pages: { style: Style; size: number; y: number; text: string }[][] = [];
  let page: typeof pages[number] = [];
  let y = 800;
  for (const [style, text] of lines) {
    const [size, lead, width] = SIZES[style];
    for (const chunk of wrap(text, width)) {
      if (y - lead < 56) { pages.push(page); page = []; y = 800; }
      y -= lead;
      page.push({ style, size, y, text: chunk });
    }
  }
  pages.push(page);
  const objs: string[] = ["", "", "<< >>", "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>", "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"];
  const kids: number[] = [];
  for (const p of pages) {
    const ops = p.map((l) => `BT /${l.style === "title" || l.style === "head" ? "F2" : "F1"} ${l.size} Tf ${l.style === "small" ? "0.4 0.4 0.4" : "0 0 0"} rg 56 ${l.y.toFixed(1)} Td (${esc(l.text)}) Tj ET`).join("\n");
    objs.push(`<< /Length ${ops.length} >>\nstream\n${ops}\nendstream`);
    objs.push(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents ${objs.length} 0 R >>`);
    kids.push(objs.length);
  }
  objs[0] = "<< /Type /Catalog /Pages 2 0 R >>";
  objs[1] = `<< /Type /Pages /Kids [${kids.map((k) => `${k} 0 R`).join(" ")}] /Count ${kids.length} >>`;
  let out = "%PDF-1.4\n";
  const offsets: number[] = [];
  objs.forEach((body, i) => { offsets.push(out.length); out += `${i + 1} 0 obj\n${body}\nendobj\n`; });
  const xref = out.length;
  out += `xref\n0 ${objs.length + 1}\n0000000000 65535 f \n` + offsets.map((o) => `${String(o).padStart(10, "0")} 00000 n \n`).join("");
  out += `trailer\n<< /Size ${objs.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
  return new Blob([out], { type: "application/pdf" });
}

const money = (v: unknown) => `Rs ${Number(v).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

function facts(detail: unknown): string {
  const d = (detail ?? {}) as Record<string, unknown>;
  const bill = d.bill as { supplier_id?: string; bill_no?: string; total_inr?: number; lines?: { qty: number; description: string; rate_inr: number }[] } | undefined;
  if (bill && bill.bill_no) return `Supplier ${bill.supplier_id}, bill ${bill.bill_no}, total ${money(bill.total_inr)}. ` + (bill.lines ?? []).map((l) => `${l.qty} x ${l.description} at ${money(l.rate_inr)}`).join("; ");
  for (const k of ["reason", "summary", "message", "note"]) if (typeof d[k] === "string") return d[k] as string;
  return "";
}

export function receiptLines(receipts: SignedReceipt[], verified: boolean): [Style, string][] {
  const out: [Style, string][] = [["title", "Relayloom receipt"], ["small", "What the agents did, in order, with the proof that nothing was changed afterwards."]];
  out.push(["head", `${receipts.length} steps, in the order they happened`]);
  out.push(["body", verified
    ? "Proof: every step is signed and linked to the one before it. The signatures and the chain were checked and are intact."
    : "Warning: the signatures or the chain did not check out. Do not rely on this receipt."]);
  for (const r of receipts) {
    const b = r.body;
    out.push(["head", `${b.seq}. ${STEP_WORDS[b.step] ?? b.step.replace(/_/g, " ")} by ${b.agent}`]);
    out.push(["small", b.time]);
    if (b.decision) out.push(["body", `Result: ${b.decision}`]);
    const f = facts(b.detail);
    if (f) out.push(["body", f]);
    if (b.approver) out.push(["body", `Approved by ${b.approver}`]);
  }
  out.push(["small", `Fingerprint of the last step: ${receipts[receipts.length - 1]?.hash}`]);
  return out;
}

export function downloadReceipt(receipts: SignedReceipt[], verified: boolean, name: string) {
  const url = URL.createObjectURL(makePdf(receiptLines(receipts, verified)));
  const a = document.createElement("a");
  a.href = url;
  a.download = `relayloom-receipt-${name}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 2000);
}
