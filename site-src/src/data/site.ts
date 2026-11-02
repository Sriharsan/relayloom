/*
 * Single source for everything the site shows. Every figure is read from the exported run files:
 *   bench.json     made by scripts/export_bench_run.py (agents, matcher, Investigator, policy, ledger, Checker, receipts)
 *   measured.json  made by scripts/export_measurements.py (SAM 3.1 and Muse Glimmer timings and counts)
 *   benchmark.json made by scripts/export_benchmark.py when the benchmark has run
 * Run `npm run data` in site-src to refresh all of them. Nothing is typed in by hand.
 */
import bench from "./bench.json";
import measured from "./measured.json";

export const links = {
  repo: "https://github.com/Sriharsan/relayloom",
  video: null as string | null,
};

export const footerNote =
  "Synthetic data. The working system runs on the business's own machine; this site does not.";

export const company = { name: "Northgate Components", note: "All data is synthetic." };

/* ----------------------------- run data types ----------------------------- */

export interface Step {
  state: string;
  seconds: number | null;
  note: string;
}
export interface Photo {
  photo: string;
  prompt?: string;
  count: number;
  counted: boolean;
  model?: string;
  route?: string;
  seconds?: number;
  overlay?: string;
  duplicate_of?: string;
  similarity?: number;
}
export interface Statement {
  text: string;
  cites: string[];
}
export interface BenchCase {
  id: string;
  bill_no: string;
  supplier_id: string;
  po_number: string;
  state: string;
  status: string;
  steps: Record<string, Step>;
  masks: { kind: string; length: number; sha256: string }[];
  injection: { hidden_text: boolean; lines: string[]; action: string } | "";
  bill: {
    supplier_id: string;
    bill_no: string;
    bill_date: string;
    po_number: string;
    lines: { item_code: string; description: string; qty: number; rate_inr: number; amount_inr: number }[];
    tax_inr: number;
    total_inr: number;
  } | null;
  counter: {
    total: number;
    model: string;
    route: string;
    events: { event_id: string; total: number; unique_photos: number; duplicate_photos: number; photos: Photo[] }[];
  };
  investigation: {
    finding: { statements: Statement[]; verified: boolean; written_by: string };
    evidence: Record<string, { id: string; kind: string; text: string }>;
    checks: Record<string, number | boolean>;
  } | null;
  match: {
    matched: boolean;
    rows: {
      item_code: string;
      description: string;
      po_qty: number;
      bill_qty: number;
      received: number;
      billed_before: number;
      issues: string[];
    }[];
  } | null;
  proposal: { action: string; reason: string; policy_level: string } | "";
  decision: { decision: string; by: string; at: string; action: string; policy_hash: string } | "";
  invoice_id: string;
  readback: { differences: unknown[]; ledger: string } | "";
  pay_to: { source: string; account_last4: string; ifsc: string } | "";
  dispute: { text: string; model: string; sent: boolean; portal_ref?: string; form_filled_by: string } | "";
}
export interface SignedReceipt {
  body: {
    case: string;
    seq: number;
    prev: string;
    time: string;
    agent: string;
    step: string;
    decision: string;
    approver: string;
    model: string;
    detail: unknown;
  } & Record<string, unknown>;
  hash: string;
  sig: string;
}

export const run = bench as unknown as {
  ran_at: string;
  policy_hash: string;
  public_key: string;
  receipts_verified: boolean;
  suppliers: Record<string, string>;
  cases: BenchCase[];
  netcut: {
    held: { id: string; bill_no: string; state: string; status: string; read: boolean }[];
    after: { id: string; bill_no: string; state: string; status: string }[];
    in_books_while_cut: number;
    in_books_after_reconnect: number;
  };
  receipts: SignedReceipt[];
};

export const meas = measured as unknown as {
  sam: {
    photo: string;
    item: string;
    prompt: string;
    count: number;
    truth: number;
    infer_seconds: number;
    wall_seconds: number;
    device: string;
    route: string;
    overlay: string;
    recorded_at: string;
    used: boolean;
    world: "demo" | "benchmark";
  }[];
  glimmer: {
    bill: string;
    seconds: number;
    model: string;
    route: string;
    prompt_tokens: number;
    output_tokens: number;
    schema_check: string;
    recorded_at: string;
  }[];
  machine: { os: string; cpu: string; memory: string; gpu: string };
};

/* ---------------------------- optional benchmark ---------------------------- */

export interface BenchmarkResult {
  setSize: number;
  rows: { metric: string; paperworkOnly: string; paperworkPlusGoods: string; basis: string }[];
  perScenario: { scenario: string; deliveries: number; rule: string; paperworkOnly: number; plusGoods: number }[];
  note: string;
}
const found = import.meta.glob("./benchmark.json", { eager: true, import: "default" }) as Record<string, BenchmarkResult>;
export const benchmark: BenchmarkResult | null = Object.values(found)[0] ?? null;

/* -------------------------------- helpers -------------------------------- */

export const rupees = (n: number) =>
  "₹ " + new Intl.NumberFormat("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n);

export const supplierName = (id: string) => run.suppliers[id] ?? id;

const total = (c: BenchCase) => c.bill?.total_inr ?? 0;

/* ------------------------------ case catalogue ------------------------------ */

export interface CaseMeta {
  id: string;
  title: string;
  sentence: string;
  expect: string;
}
export const caseMeta: CaseMeta[] = [
  {
    id: "match",
    title: "Matching delivery",
    sentence: "Bill, order and counted goods agree. The bill is entered and a separate check reads it back. No person involved.",
    expect: "entered_checked",
  },
  {
    id: "short",
    title: "Short delivery",
    sentence: "The bill says 50. The dock got 46. The Investigator recounts, repeats nothing twice and cites every statement.",
    expect: "dispute_sent",
  },
  {
    id: "price",
    title: "Price above the order",
    sentence: "The bill charges more than the purchase order. The owner reviews the evidence, rejects, and nothing is entered or sent.",
    expect: "closed_by_owner",
  },
  {
    id: "injection",
    title: "Hidden text asks to change the bank account",
    sentence: "White text on the bill names a new account. It is ignored and receipted, and payment details come from the ledger.",
    expect: "entered_checked",
  },
  {
    id: "duplicate",
    title: "Duplicate bill under a new number",
    sentence: "Same supplier, amount and date as a bill already in the books. The Investigator finds it and the duplicate is rejected.",
    expect: "closed_by_owner",
  },
  {
    id: "split",
    title: "Split delivery, one bill",
    sentence: "One order arrived in two deliveries and was billed once. Receiving events add up as a running total, so it matches.",
    expect: "entered_checked",
  },
];

export const caseById = (id: string) => run.cases.find((c) => c.id === id);

export const caseResult = (id: string): "PASS" | "FAIL" => {
  const c = caseById(id);
  const meta = caseMeta.find((m) => m.id === id);
  return c && meta && c.state === meta.expect && run.receipts_verified ? "PASS" : "FAIL";
};

export const netcutPass =
  run.netcut.held.every((c) => c.state === "held_offline") &&
  run.netcut.in_books_while_cut === 1 &&
  run.netcut.after.every((c) => c.state === "entered_checked") &&
  run.netcut.in_books_after_reconnect === 3;

/** Photos for a case with the best image to show: the SAM 3.1 overlay when one was recorded, else the delivery photo. */
export function casePhotos(c: BenchCase) {
  return c.counter.events.flatMap((e) =>
    e.photos.map((p) => ({
      ...p,
      eventId: e.event_id,
      image: p.overlay ? `/img/${p.overlay}` : `/img/${p.photo}.jpg`,
      sam: p.model === "SAM 3.1",
    })),
  );
}

export const firstImage = (c: BenchCase) => casePhotos(c).find((p) => p.counted)?.image ?? null;

/* -------------------------------- Today table -------------------------------- */

export const STEPS = ["read", "count", "match", "investigate", "enter", "check"] as const;
export type StepKey = (typeof STEPS)[number];

export function stepView(c: BenchCase, key: StepKey): { status: "done" | "held" | "skipped" | "waiting"; time: string } {
  const s = c.steps[key];
  const status = (s?.state === "done" ? "done" : s?.state === "held" ? "held" : s?.state === "skipped" ? "skipped" : "waiting") as
    | "done"
    | "held"
    | "skipped"
    | "waiting";
  let time = "under 1 s";
  if (key === "read") time = "bill record";
  if (key === "count") {
    const sam = casePhotos(c).filter((p) => p.sam && p.counted);
    time = sam.length ? `${Math.round(sam.reduce((a, p) => a + (p.seconds ?? 0), 0))} s SAM 3.1` : "delivery record";
  }
  if (status === "skipped" || status === "waiting") time = "";
  return { status, time };
}

export const todayRows = run.cases.map((c) => ({
  id: c.id,
  bill: c.bill_no,
  supplier: supplierName(c.supplier_id),
  amount: rupees(total(c)),
  c,
}));

export const counters = {
  entered: run.cases.filter((c) => c.state === "entered_checked").length + run.netcut.after.filter((c) => c.state === "entered_checked").length,
  decided: run.cases.filter((c) => c.decision).length,
  offline: run.netcut.held.length,
};

/* ------------------------------ SAM summary ------------------------------ */

/** Runs with the wordings the system uses. Other wordings were trials, listed separately. */
export const samUsed = meas.sam.filter((r) => r.used);
export const samTrials = meas.sam.filter((r) => !r.used);
export const samDemoRows = samUsed.filter((r) => r.world === "demo");
export const samBenchRows = samUsed.filter((r) => r.world === "benchmark");

export const samSummary = (() => {
  const runs = samUsed;
  const exact = runs.filter((r) => r.count === r.truth).length;
  const secs = runs.map((r) => r.infer_seconds);
  return {
    runs: runs.length,
    exact,
    misses: runs.filter((r) => r.count !== r.truth),
    trials: samTrials.length,
    trialsZero: samTrials.filter((r) => r.count === 0).length,
    min: Math.min(...secs),
    max: Math.max(...secs),
    mean: secs.reduce((a, b) => a + b, 0) / secs.length,
  };
})();

export const glimmerSummary = (() => {
  const s = meas.glimmer.map((g) => g.seconds);
  return {
    runs: s.length,
    valid: meas.glimmer.filter((g) => g.schema_check === "valid").length,
    min: Math.min(...s),
    max: Math.max(...s),
    mean: s.reduce((a, b) => a + b, 0) / s.length,
  };
})();

export const approvals = run.cases
  .filter((c) => c.decision)
  .map((c) => ({
    id: c.id,
    bill: c.bill_no,
    supplier: supplierName(c.supplier_id),
    gap: c.proposal && typeof c.proposal === "object" ? c.proposal.reason : "",
    summary: c.investigation?.finding.statements[0]?.text ?? "",
    draft: c.dispute && typeof c.dispute === "object" ? c.dispute.text : "",
    decision: c.decision as { decision: string; by: string; at: string; policy_hash: string },
  }));

export const fmtSeconds = (s: number) => (s >= 60 ? `${Math.floor(s / 60)} min ${Math.round(s % 60)} s` : `${s.toFixed(1)} s`);
