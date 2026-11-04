/** The three way match, ported from relayloom/ap/matcher.py so a visitor can run it live in the browser. Same rules, same limits. */
export const LIMITS = { owner_amount_limit_inr: 100000, quantity_tolerance_units: 0, rate_tolerance_percent: 0.5, total_tolerance_inr: 1 };

export interface Line {
  item_code: string;
  description: string;
  ordered_qty: number;
  ordered_rate: number;
  billed_qty: number;
  billed_rate: number;
  received: number;
  damaged: number;
}
export interface Delivery {
  supplier: string;
  bill_no: string;
  po_no: string;
  tax_rate: number;
  tax: number;
  total: number;
  lines: Line[];
}
export interface Row {
  item_code: string;
  description: string;
  ordered: number;
  billed: number;
  received: number;
  damaged: number;
  issues: string[];
}
export interface Verdict {
  held: boolean;
  reasons: string[];
  rows: Row[];
  subtotal: number;
  needs_owner_for_amount: boolean;
}

const r2 = (n: number) => Math.round(n * 100) / 100;
export const money = (n: number) => n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export function check(d: Delivery): Verdict {
  const L = LIMITS;
  const rows: Row[] = [];
  const reasons: string[] = [];
  for (const l of d.lines) {
    const usable = Math.max(0, l.received - l.damaged);
    const issues: string[] = [];
    if (l.billed_qty > l.ordered_qty + L.quantity_tolerance_units) issues.push(`${l.billed_qty} billed, only ${l.ordered_qty} ordered`);
    if (Math.abs(l.billed_rate - l.ordered_rate) > l.ordered_rate * (L.rate_tolerance_percent / 100)) issues.push(`rate ${money(l.billed_rate)} is not the order rate ${money(l.ordered_rate)}`);
    if (l.damaged > 0) issues.push(`${l.damaged} of ${l.received} arrived damaged and do not count as received`);
    if (l.billed_qty > usable + L.quantity_tolerance_units) issues.push(`${l.billed_qty} billed but ${usable} received in good condition`);
    rows.push({ item_code: l.item_code, description: l.description, ordered: l.ordered_qty, billed: l.billed_qty, received: usable, damaged: l.damaged, issues });
    reasons.push(...issues.map((i) => `${l.item_code}: ${i}`));
  }
  const subtotal = r2(d.lines.reduce((s, l) => s + l.billed_qty * l.billed_rate, 0));
  if (Math.abs(subtotal + d.tax - d.total) > L.total_tolerance_inr) reasons.push(`The total ${money(d.total)} is not the lines ${money(subtotal)} plus tax ${money(d.tax)}`);
  const expectedTax = r2(subtotal * (d.tax_rate / 100));
  if (Math.abs(expectedTax - d.tax) > L.total_tolerance_inr) reasons.push(`Tax ${money(d.tax)} differs from ${money(expectedTax)} at the order tax rate of ${d.tax_rate} percent`);
  const needs = d.total > L.owner_amount_limit_inr;
  if (needs) reasons.push(`The total ${money(d.total)} is over the owner approval limit of ${money(L.owner_amount_limit_inr)}, so a person approves it`);
  return { held: reasons.length > 0, reasons, rows, subtotal, needs_owner_for_amount: needs };
}

export const EXAMPLES: Record<string, Delivery> = {
  short: {
    supplier: "Calder Packaging", bill_no: "CAL-0990", po_no: "PO-2002", tax_rate: 18, tax: 1062, total: 6962,
    lines: [{ item_code: "CARTON-HD", description: "Heavy duty shipping carton", ordered_qty: 50, ordered_rate: 118, billed_qty: 50, billed_rate: 118, received: 46, damaged: 0 }],
  },
  damaged: {
    supplier: "Arden Fluids Ltd", bill_no: "ARD-5101", po_no: "PO-1950", tax_rate: 18, tax: 3283.2, total: 21523.2,
    lines: [{ item_code: "COOLANT-5L", description: "Coolant can, 5 litre", ordered_qty: 60, ordered_rate: 304, billed_qty: 60, billed_rate: 304, received: 60, damaged: 9 }],
  },
  clean: {
    supplier: "Briarwood Polymers", bill_no: "BRI-0735", po_no: "PO-1998", tax_rate: 18, tax: 1620, total: 10620,
    lines: [{ item_code: "SACK-25", description: "Polymer sack, 25 kg", ordered_qty: 30, ordered_rate: 300, billed_qty: 30, billed_rate: 300, received: 30, damaged: 0 }],
  },
};
