/** The three way match, ported from relayloom/ap/matcher.py so a visitor can run it live in the browser. Same rules, same limits. */
export const LIMITS = { owner_amount_limit_inr: 100000, quantity_tolerance_units: 0, rate_tolerance_percent: 0.5, total_tolerance_inr: 1 };

/** Common sales tax names and standard rates, so the amounts calculate themselves. The visitor can match the paper bill by hand. */
export const COUNTRIES: { code: string; name: string; tax: string; rate: number; currency: string }[] = [
  { code: "IN", name: "India", tax: "GST", rate: 18, currency: "Rs" },
  { code: "US", name: "United States", tax: "Sales tax", rate: 7, currency: "USD" },
  { code: "GB", name: "United Kingdom", tax: "VAT", rate: 20, currency: "GBP" },
  { code: "AE", name: "United Arab Emirates", tax: "VAT", rate: 5, currency: "AED" },
  { code: "SG", name: "Singapore", tax: "GST", rate: 9, currency: "SGD" },
  { code: "DE", name: "Germany", tax: "VAT", rate: 19, currency: "EUR" },
  { code: "AU", name: "Australia", tax: "GST", rate: 10, currency: "AUD" },
  { code: "CA", name: "Canada", tax: "GST", rate: 5, currency: "CAD" },
];

export interface Line {
  item_code: string;
  description: string;
  ordered_qty: number;
  ordered_rate: number;
  billed_qty: number;
  billed_rate: number;
  received: number;
  damaged: number;
  photo?: string; // the marked evidence photo, resized in the browser, never uploaded
  raw?: string; // the photo before marking, so it can be marked again
  marks?: { x: number; y: number; bad: boolean }[];
}
export interface Delivery {
  supplier: string;
  bill_no: string;
  po_no: string;
  country: string;
  tax_rate: number;
  manual: boolean; // the tax and the total are typed to match a paper bill
  tax: number;
  total: number;
  lines: Line[];
}
export interface Row { item_code: string; description: string; ordered: number; billed: number; received: number; damaged: number; issues: string[] }
export interface Verdict { held: boolean; reasons: string[]; rows: Row[]; subtotal: number; tax: number; total: number; needs_owner_for_amount: boolean }

const r2 = (n: number) => Math.round(n * 100) / 100;
export const money = (n: number, cur = "Rs") => `${cur} ${n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

export const isBlank = (l: Line) => !l.item_code.trim() && !l.description.trim() && !l.ordered_qty && !l.billed_qty && !l.received;
export const country = (d: Delivery) => COUNTRIES.find((c) => c.code === d.country) ?? COUNTRIES[0]!;

export function amounts(d: Delivery) {
  const subtotal = r2(d.lines.filter((l) => !isBlank(l)).reduce((s, l) => s + l.billed_qty * l.billed_rate, 0));
  if (d.manual) return { subtotal, tax: d.tax, total: d.total };
  const tax = r2(subtotal * (d.tax_rate / 100));
  return { subtotal, tax, total: r2(subtotal + tax) };
}

export function check(d: Delivery): Verdict {
  const L = LIMITS;
  const cur = country(d).currency;
  const rows: Row[] = [];
  const reasons: string[] = [];
  const { subtotal, tax, total } = amounts(d);
  for (const l of d.lines.filter((x) => !isBlank(x))) {
    const usable = Math.max(0, l.received - l.damaged);
    const name = l.description || l.item_code || "Item";
    const issues: string[] = [];
    if (l.billed_qty > l.ordered_qty + L.quantity_tolerance_units) issues.push(`${l.billed_qty} billed, only ${l.ordered_qty} ordered`);
    if (Math.abs(l.billed_rate - l.ordered_rate) > l.ordered_rate * (L.rate_tolerance_percent / 100)) issues.push(`rate ${money(l.billed_rate, cur)} is not the order rate ${money(l.ordered_rate, cur)}`);
    if (l.damaged > 0) issues.push(`${l.damaged} of ${l.received} arrived damaged and do not count as received`);
    if (l.billed_qty > usable + L.quantity_tolerance_units) issues.push(`${l.billed_qty} billed but ${usable} received in good condition`);
    rows.push({ item_code: l.item_code, description: name, ordered: l.ordered_qty, billed: l.billed_qty, received: usable, damaged: l.damaged, issues });
    reasons.push(...issues.map((i) => `${name}: ${i}`));
  }
  if (Math.abs(subtotal + tax - total) > L.total_tolerance_inr) reasons.push(`The total ${money(total, cur)} is not the items ${money(subtotal, cur)} plus tax ${money(tax, cur)}`);
  const expectedTax = r2(subtotal * (d.tax_rate / 100));
  if (Math.abs(expectedTax - tax) > L.total_tolerance_inr) reasons.push(`Tax ${money(tax, cur)} differs from ${money(expectedTax, cur)} at ${d.tax_rate} percent`);
  const needs = cur === "Rs" && total > L.owner_amount_limit_inr;
  if (needs) reasons.push(`The total ${money(total, cur)} is over the owner approval limit of ${money(L.owner_amount_limit_inr, cur)}, so a person approves it`);
  return { held: reasons.length > 0, reasons, rows, subtotal, tax, total, needs_owner_for_amount: needs };
}

const base = (): Delivery => ({ supplier: "", bill_no: "", po_no: "", country: "IN", tax_rate: 18, manual: false, tax: 0, total: 0, lines: [] });
export const EXAMPLES: Record<string, Delivery> = {
  short: {
    ...base(), supplier: "Calder Packaging", bill_no: "CAL-0990", po_no: "PO-2002",
    lines: [{ item_code: "CARTON-HD", description: "Heavy duty shipping carton", ordered_qty: 50, ordered_rate: 118, billed_qty: 50, billed_rate: 118, received: 46, damaged: 0 }],
  },
  damaged: {
    ...base(), supplier: "Arden Fluids Ltd", bill_no: "ARD-5101", po_no: "PO-1950",
    lines: [{ item_code: "COOLANT-5L", description: "Coolant can, 5 litre", ordered_qty: 60, ordered_rate: 304, billed_qty: 60, billed_rate: 304, received: 60, damaged: 9 }],
  },
  clean: {
    ...base(), supplier: "Briarwood Polymers", bill_no: "BRI-0735", po_no: "PO-1998",
    lines: [{ item_code: "SACK-25", description: "Polymer sack, 25 kg", ordered_qty: 30, ordered_rate: 300, billed_qty: 30, billed_rate: 300, received: 30, damaged: 0 }],
  },
};
export const blankDelivery = (): Delivery => ({ ...base(), lines: [{ item_code: "", description: "", ordered_qty: 0, ordered_rate: 0, billed_qty: 0, billed_rate: 0, received: 0, damaged: 0 }] });
