import { useCallback, useEffect, useState } from "react";
import {
  approvals, caseById, casePhotos, counters, rupees, run, STEPS, stepView, supplierName, todayRows, type BenchCase, type StepKey,
} from "@/data/site";
import { Photo, Pill, RunLabel, StepPill } from "@/components/bits";
import { FindingCard, citeId } from "@/components/finding";
import { run as runData } from "@/data/site";
import { Link } from "@/lib/router";

type Tab = "today" | "case" | "approvals";

const LABEL = "Rehearsal";
const STEP_LABELS: Record<StepKey, string> = {
  read: "Read", count: "Count", match: "Match", investigate: "Investigate", enter: "Enter", check: "Check",
};
const KIND_LABEL: Record<string, string> = {
  gstin: "Tax ID", bank_account: "Bank account", ifsc: "Bank code", phone: "Phone", email: "Email",
};

function scrollToCite(cite: string) {
  const el = document.getElementById(citeId(cite)) ?? (cite.startsWith("PHOTO:") ? document.getElementById("photo-" + cite.slice(6)) : null);
  if (!el) return;
  el.scrollIntoView({ block: "center", behavior: "smooth" });
  el.style.outline = "2px solid var(--amber)";
  el.style.outlineOffset = "2px";
  window.setTimeout(() => {
    el.style.outline = "";
    el.style.outlineOffset = "";
  }, 1400);
}

function Card({ title, right, children }: { title: string; right?: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-line bg-surface">
      <div className="flex items-center justify-between gap-3 border-b border-line px-5 py-3">
        <span className="kLabel">{title}</span>
        {right}
      </div>
      {children}
    </div>
  );
}


function CauseCard({ c }: { c: BenchCase }) {
  const d = c.diagnosis!;
  return (
    <div id="guide-cause" className="rounded-xl border border-line bg-surface">
      <div className="flex items-center justify-between gap-3 border-b border-line px-5 py-3">
        <span className="kLabel">Likely cause</span>
        <Pill tone={d.confidence === "high" ? "green" : d.confidence === "medium" ? "amber" : "muted"}>confidence {d.confidence}</Pill>
      </div>
      <div className="px-5 py-4">
        <h3 className="text-[16px] font-medium text-foreground">{d.label}</h3>
        <p className="mt-1 text-[13px] text-ink-muted">Probably: {d.responsible}.</p>
        <ul className="mt-3 space-y-2.5">
          {d.because.map((b, i) => (
            <li key={i} className="flex flex-col gap-1.5">
              <span className="text-[13.5px] leading-relaxed text-foreground">{b.text}</span>
              <span className="flex flex-wrap gap-1.5">
                {b.cites.map((x) => (
                  <button key={x} onClick={() => scrollToCite(x)} className="tnum pill bg-raised text-[10.5px] text-foreground transition-colors duration-150 hover:border-line-strong">{x}</button>
                ))}
              </span>
            </li>
          ))}
        </ul>
        <p className="mt-3 border-t border-line pt-3 text-[13px] text-ink-muted"><span className="text-foreground">Next:</span> {d.next_step}</p>
      </div>
    </div>
  );
}

function SupplierCard({ c }: { c: BenchCase }) {
  const sf = runData.supplier_files[c.supplier_id];
  if (!sf) return null;
  return (
    <Card title="Supplier file" right={<span className="font-mono text-[11px] text-ink-muted">{sf.short_orders} short of {sf.orders.length} orders</span>}>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[300px] text-left text-[12.5px]">
          <thead>
            <tr className="border-b border-line text-ink-muted">
              <th className="px-5 py-2 font-medium">Order</th>
              <th className="px-5 py-2 text-right font-medium">Billed</th>
              <th className="px-5 py-2 text-right font-medium">Counted</th>
            </tr>
          </thead>
          <tbody>
            {sf.orders.map((o) => (
              <tr key={o.invoice} className={`border-b border-line last:border-0 ${o.short ? "bg-amber/5" : ""}`}>
                <td className="tnum px-5 py-2 font-mono text-foreground">{o.po}</td>
                <td className="tnum px-5 py-2 text-right font-mono text-foreground">{o.billed}</td>
                <td className={`tnum px-5 py-2 text-right font-mono ${o.short ? "text-amber-ink" : "text-foreground"}`}>{o.counted ?? "no photos"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="border-t border-line px-5 py-3 text-[12px] leading-relaxed text-ink-muted">
        {sf.name}. Every new investigation of this supplier reads this record.
      </p>
    </Card>
  );
}

function CaseFileCard({ c }: { c: BenchCase }) {
  if (!c.casefile) return null;
  return (
    <Card title="Case file" right={<Pill tone="green">filed</Pill>}>
      <div className="px-5 py-4 text-[13px] leading-relaxed text-ink-muted">
        <p>
          Filed when the case ended as <span className="text-foreground">{c.casefile.state.replace(/_/g, " ")}</span>: the bill, the count, the cause and its reasons,
          the decision and the supplier's record at that time.
        </p>
        <p className="mt-2 break-all font-mono text-[11px] text-foreground">{c.casefile.file} · {c.casefile.sha256.slice(0, 16)}</p>
        <p className="mt-2">Its hash is in the signed receipt chain, so it cannot be changed quietly.</p>
      </div>
    </Card>
  );
}

function CaseView({ c }: { c: BenchCase }) {
  const photos = casePhotos(c);
  const receipts = run.receipts.filter((r) => r.body.case === c.id);
  const proposal = c.proposal && typeof c.proposal === "object" ? c.proposal : null;
  const decision = c.decision && typeof c.decision === "object" ? c.decision : null;
  const evidence = c.investigation ? Object.values(c.investigation.evidence) : [];
  const readback = c.readback && typeof c.readback === "object" ? c.readback : null;
  const payTo = c.pay_to && typeof c.pay_to === "object" ? c.pay_to : null;
  const hidden = c.injection && typeof c.injection === "object" ? c.injection : null;
  const received = c.counter.total;

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
      <div className="flex flex-col gap-4">
        <Card title="Bill" right={<RunLabel label={LABEL} />}>
          <dl className="px-5 py-4 text-[13.5px]">
            {[
              ["Supplier", supplierName(c.supplier_id)],
              ["Invoice", c.bill_no],
              ["Order", c.po_number],
              ["Date", c.bill?.bill_date ?? ""],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between gap-4 py-1.5">
                <dt className="text-ink-muted">{k}</dt>
                <dd className="tnum font-mono text-[12.5px] text-foreground">{v}</dd>
              </div>
            ))}
            <div className="mt-2 flex justify-between gap-4 border-t border-line pt-2">
              <dt className="text-ink-muted">Total</dt>
              <dd className="tnum font-mono text-[13px] text-foreground">{rupees(c.bill?.total_inr ?? 0)}</dd>
            </div>
          </dl>
          <div className="border-t border-line px-5 py-3">
            <p className="kLabel">Masked before any model saw it</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {c.masks.map((m, i) => (
                <span key={i} className="pill bg-raised text-[10.5px] text-foreground">
                  {KIND_LABEL[m.kind] ?? m.kind} ••••
                </span>
              ))}
            </div>
          </div>
          {hidden && (
            <div className="border-t border-line px-5 py-3">
              <p className="kLabel text-red-ink">Hidden text found and ignored</p>
              <p className="mt-2 font-mono text-[11.5px] leading-relaxed text-ink-muted">{hidden.lines[0]}</p>
              <p className="mt-2 text-[12.5px] text-foreground">{hidden.action}</p>
            </div>
          )}
        </Card>

        <Card
          title="Ledger readback"
          right={
            <Pill tone={c.state === "entered_checked" ? "green" : c.state === "held_offline" ? "muted" : "amber"}>
              {c.state === "entered_checked" ? "checked" : c.state === "held_offline" ? "offline" : "nothing entered"}
            </Pill>
          }
        >
          <ul className="px-5 py-4">
            {readback ? (
              <>
                <li className="font-mono text-[12px] leading-relaxed text-ink-muted"><span className="text-foreground">$ </span>{c.invoice_id} posted to the {readback.ledger}</li>
                <li className="font-mono text-[12px] leading-relaxed text-ink-muted"><span className="text-foreground">$ </span>every field read back separately: {readback.differences.length} differences</li>
                {payTo && (
                  <li className="font-mono text-[12px] leading-relaxed text-ink-muted"><span className="text-foreground">$ </span>pay to account ending {payTo.account_last4}, from the {payTo.source}</li>
                )}
              </>
            ) : (
              <li className="font-mono text-[12px] leading-relaxed text-ink-muted"><span className="text-foreground">$ </span>{c.status}</li>
            )}
          </ul>
        </Card>
        <SupplierCard c={c} />
        <CaseFileCard c={c} />
      </div>

      <div className="flex flex-col gap-4">
        <Card title="Delivery photos" right={<Pill tone="green">counted by SAM 3.1</Pill>}>
          <div className="grid grid-cols-1 gap-4 px-5 py-4 sm:grid-cols-2">
            {photos.map((p) => (
              <figure key={p.photo} id={"photo-" + p.photo} className="scroll-mt-24 rounded-lg border border-line bg-raised p-3">
                {p.counted ? (
                  <Photo src={p.image} alt={`${p.photo} with ${p.count} items outlined and numbered`} />
                ) : (
                  <div className="flex aspect-[4/3] items-center justify-center rounded-lg border border-dashed border-line px-3 text-center font-mono text-[11px] text-ink-muted">
                    repeat of {p.duplicate_of}, similarity {p.similarity}
                  </div>
                )}
                <figcaption className="mt-2.5 flex items-baseline justify-between gap-2">
                  <span className="tnum font-mono text-[11px] text-ink-muted">{p.photo}</span>
                  {p.counted ? <span className="tnum font-mono text-[18px] leading-none text-green-ink">{p.count}</span> : <span className="font-mono text-[11px] text-ink-muted">repeat</span>}
                </figcaption>
                <span className="mt-1 block font-mono text-[10.5px] text-ink-muted">
                  {p.counted ? (p.sam ? `SAM 3.1, ${Math.round(p.seconds ?? 0)} s on CPU` : "count from the delivery record") : "not counted twice"}
                </span>
              </figure>
            ))}
          </div>
          <div className="border-t border-line px-5 py-3">
            <span className="tnum font-mono text-[12px] text-foreground">Running total on {c.po_number}: {received} received</span>
          </div>
        </Card>

        <Card title="Three way match">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[300px] text-left text-[13px]">
              <thead>
                <tr className="border-b border-line text-ink-muted">
                  <th className="px-5 py-2.5 font-medium">Item</th>
                  <th className="px-5 py-2.5 text-right font-medium">Order</th>
                  <th className="px-5 py-2.5 text-right font-medium">Bill</th>
                  <th className="px-5 py-2.5 text-right font-medium">Goods</th>
                </tr>
              </thead>
              <tbody>
                {c.match?.rows.map((r) => (
                  <tr key={r.item_code} className={`border-b border-line last:border-0 ${r.issues.length ? "bg-amber/5" : ""}`}>
                    <td className="px-5 py-2.5 text-foreground">{r.description}</td>
                    <td className="tnum px-5 py-2.5 text-right font-mono text-[12.5px] text-foreground">{r.po_qty}</td>
                    <td className="tnum px-5 py-2.5 text-right font-mono text-[12.5px] text-foreground">{r.bill_qty}</td>
                    <td className={`tnum px-5 py-2.5 text-right font-mono text-[12.5px] ${r.issues.length ? "text-amber-ink" : "text-foreground"}`}>{r.received}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {c.match?.rows.some((r) => r.issues.length) && (
            <p className="border-t border-line px-5 py-3 font-mono text-[11.5px] text-ink-muted">{c.match.rows.flatMap((r) => r.issues).join(". ")}</p>
          )}
        </Card>
      </div>

      <div className="flex flex-col gap-4">
        {c.investigation ? (
          <>
            {c.diagnosis && <CauseCard c={c} />}
            <div id="guide-finding">
              <FindingCard title={`${c.bill_no} on ${c.po_number}`} statements={c.investigation.finding.statements} label={LABEL} onCite={scrollToCite} />
            </div>
            {proposal && (
              <div className="flex flex-wrap items-center gap-2">
                <span className="pill !whitespace-normal border-line bg-raised text-[11.5px] text-foreground">Proposed: {proposal.reason}</span>
                <span className="pill border-amber/40 bg-amber/10 text-[11.5px] text-amber-ink">
                  Policy: {proposal.policy_level === "run_with_approval" ? "needs approval" : proposal.policy_level.replace(/_/g, " ")}
                </span>
              </div>
            )}
            {decision && (
              <p className="font-mono text-[12px] text-green-ink">
                Owner decision: {decision.decision}d, policy {decision.policy_hash.slice(0, 8)}
              </p>
            )}
            <Card title="Evidence">
              <ul className="px-5 py-4">
                {evidence.map((e) => (
                  <li key={e.id} id={citeId(e.id)} className="scroll-mt-24 border-b border-line py-2 last:border-0">
                    <span className="tnum font-mono text-[11px] text-foreground">{e.id}</span>
                    <span className="mt-0.5 block text-[12px] leading-relaxed text-ink-muted">{e.text}</span>
                  </li>
                ))}
              </ul>
            </Card>
          </>
        ) : (
          <div className="rounded-xl border border-line bg-surface p-5">
            <p className="kLabel">Investigator</p>
            <p className="mt-3 font-mono text-[12px] text-ink-muted">Bill, order and goods agree. Nothing to investigate.</p>
          </div>
        )}

        <Card title="Receipt chain" right={<span className="font-mono text-[11px] text-ink-muted">signed, verified in your browser on Proof</span>}>
          <ul className="max-h-[360px] overflow-y-auto px-5 py-4">
            {receipts.map((r, i) => (
              <li key={r.hash} className="relative pb-4 pl-6 last:pb-0">
                {i < receipts.length - 1 && <span className="absolute left-[5px] top-3 h-full w-px bg-line" aria-hidden="true" />}
                <span className="absolute left-0 top-1.5 h-[11px] w-[11px] rounded-full border-2 border-green bg-green/20" aria-hidden="true" />
                <div className="flex items-baseline justify-between gap-3">
                  <span className="tnum font-mono text-[12px] text-foreground">{r.body.agent}, {r.body.step}</span>
                  <span className="tnum font-mono text-[11px] text-green-ink">{r.hash.slice(0, 8)}</span>
                </div>
                <span className="mt-0.5 block text-[12px] text-ink-muted">{r.body.decision}</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}

function ApprovalsView() {
  const [shown, setShown] = useState<Record<string, string>>({});

  const press = useCallback((id: string, verb: "approve" | "reject") => {
    const a = approvals.find((x) => x.id === id)!;
    const recorded = a.decision.decision;
    setShown((prev) => ({
      ...prev,
      [id]:
        recorded === verb
          ? `Matches the recorded decision: ${recorded}d by ${a.decision.by} at ${a.decision.at.slice(11, 16)}, policy ${a.decision.policy_hash.slice(0, 8)}`
          : `The recorded decision was ${recorded}. This replay shows recorded outcomes only.`,
    }));
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLElement && ["INPUT", "TEXTAREA"].includes(e.target.tagName)) return;
      const next = approvals.find((a) => !shown[a.id]);
      if (!next) return;
      if (e.key === "a" || e.key === "A") press(next.id, "approve");
      if (e.key === "r" || e.key === "R") press(next.id, "reject");
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [shown, press]);

  return (
    <div id="guide-approvals" className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {approvals.map((a) => (
        <article key={a.id} className="flex flex-col rounded-xl border border-line bg-surface">
          <div className="flex items-center justify-between border-b border-line px-5 py-3">
            <span className="tnum font-mono text-[12px] text-foreground">{a.bill}</span>
            <RunLabel label={LABEL} />
          </div>
          <div className="flex flex-1 flex-col px-5 py-4">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <span className="text-[14.5px] font-medium text-foreground">{a.supplier}</span>
              <span className="pill !whitespace-normal border-amber/40 bg-amber/10 text-[11px] text-amber-ink">{a.gap}</span>
            </div>
            <p className="mt-2 text-[13.5px] leading-relaxed text-ink-muted">{a.summary}</p>
            {a.draft && (
              <div className="mt-3 rounded-lg border border-line bg-raised px-3.5 py-3">
                <span className="kLabel">Dispute draft preview</span>
                <p className="mt-2 whitespace-pre-wrap font-mono text-[11.5px] leading-relaxed text-foreground">{a.draft}</p>
                <p className="mt-2 font-mono text-[10.5px] text-ink-muted">Text from a template in this replay. Muse Glimmer writes it in the live app.</p>
              </div>
            )}
            <div className="flex-1" />
            {shown[a.id] ? (
              <p className="mt-4 font-mono text-[12px] text-green-ink">{shown[a.id]}</p>
            ) : (
              <div className="mt-4 flex items-center gap-2">
                <button
                  onClick={() => press(a.id, "approve")}
                  className="inline-flex h-11 items-center gap-2 rounded-md border border-green/40 bg-green/10 px-4 text-[13px] font-medium text-green-ink transition-colors duration-150 hover:bg-green/20"
                >
                  Approve
                  <kbd className="tnum rounded border border-green/30 px-1.5 font-mono text-[10.5px]">A</kbd>
                </button>
                <button
                  onClick={() => press(a.id, "reject")}
                  className="inline-flex h-11 items-center gap-2 rounded-md border border-red/40 bg-red/10 px-4 text-[13px] font-medium text-red-ink transition-colors duration-150 hover:bg-red/20"
                >
                  Reject
                  <kbd className="tnum rounded border border-red/30 px-1.5 font-mono text-[10.5px]">R</kbd>
                </button>
              </div>
            )}
          </div>
        </article>
      ))}
      <p className="font-mono text-[11.5px] text-ink-muted lg:col-span-2">
        In the replay, Approve and Reject show the decision recorded in the run. Nothing is sent anywhere.
      </p>
    </div>
  );
}

function TodayView({ onOpen }: { onOpen: (id: string) => void }) {
  return (
    <div>
      <div id="guide-counters" className="mb-6 grid gap-3 sm:grid-cols-3">
        <div className="rounded-xl border border-green/30 bg-surface px-5 py-4">
          <span className="tnum font-mono text-[26px] leading-none text-green-ink">{counters.entered}</span>
          <p className="mt-2 text-[12.5px] text-ink-muted">Entered and checked</p>
        </div>
        <div className="rounded-xl border border-amber/30 bg-surface px-5 py-4">
          <span className="tnum font-mono text-[26px] leading-none text-amber-ink">{counters.decided}</span>
          <p className="mt-2 text-[12.5px] text-ink-muted">Decided by the owner</p>
        </div>
        <div className="rounded-xl border border-line bg-surface px-5 py-4">
          <span className="tnum font-mono text-[26px] leading-none text-foreground">{counters.offline}</span>
          <p className="mt-2 text-[12.5px] text-ink-muted">Held offline, then resumed with none entered twice</p>
        </div>
      </div>

      <div className="hidden overflow-x-auto rounded-xl border border-line bg-surface md:block">
        <table className="w-full min-w-[980px] text-left text-[13px]">
          <thead>
            <tr className="border-b border-line text-ink-muted">
              <th className="px-5 py-3 font-medium">Bill</th>
              <th className="px-5 py-3 font-medium">Supplier</th>
              <th className="px-5 py-3 text-right font-medium">Amount</th>
              {STEPS.map((s) => (
                <th key={s} className="px-3 py-3 font-medium">{STEP_LABELS[s]}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {todayRows.map((b) => (
              <tr
                key={b.id}
                tabIndex={0}
                onClick={() => onOpen(b.id)}
                onKeyDown={(e) => e.key === "Enter" && onOpen(b.id)}
                className="cursor-pointer border-b border-line transition-colors duration-150 last:border-0 hover:bg-raised/60"
              >
                <td className="tnum px-5 py-3 font-mono text-[12.5px] text-foreground">{b.bill}</td>
                <td className="px-5 py-3 text-foreground">{b.supplier}</td>
                <td className="tnum px-5 py-3 text-right font-mono text-[12.5px] text-foreground">{b.amount}</td>
                {STEPS.map((s) => {
                  const v = stepView(b.c, s);
                  return (
                    <td key={s} className="px-3 py-3">
                      <StepPill name={STEP_LABELS[s]} status={v.status} time={v.time} />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex flex-col gap-3 md:hidden">
        {todayRows.map((b) => (
          <button key={b.id} onClick={() => onOpen(b.id)} className="rounded-xl border border-line bg-surface p-4 text-left transition-colors duration-150 hover:bg-raised/60">
            <div className="flex items-baseline justify-between gap-2">
              <span className="tnum font-mono text-[12.5px] text-foreground">{b.bill}</span>
              <span className="tnum font-mono text-[12.5px] text-foreground">{b.amount}</span>
            </div>
            <span className="mt-0.5 block text-[12.5px] text-ink-muted">{b.supplier}</span>
            <div className="mt-3 flex flex-wrap gap-2">
              {STEPS.map((s) => {
                const v = stepView(b.c, s);
                return <StepPill key={s} name={STEP_LABELS[s]} status={v.status} time={v.time} />;
              })}
            </div>
          </button>
        ))}
      </div>

      <div className="mt-6 rounded-xl border border-line bg-surface p-5">
        <p className="kLabel">Network cut mid batch</p>
        <ul className="mt-3 grid gap-2 sm:grid-cols-3">
          {run.netcut.held.map((h, i) => (
            <li key={h.id} className="rounded-lg border border-line bg-raised px-4 py-3">
              <span className="tnum font-mono text-[12px] text-foreground">{h.bill_no}</span>
              <span className="mt-1 block font-mono text-[11.5px] text-amber-ink">{h.status}</span>
              <span className="mt-1 block font-mono text-[11.5px] text-green-ink">after reconnect: {run.netcut.after[i]?.status}</span>
            </li>
          ))}
        </ul>
        <p className="mt-3 font-mono text-[11.5px] text-ink-muted">
          {run.netcut.in_books_while_cut} invoice in the books while the link was down. {run.netcut.in_books_after_reconnect} after reconnect, none entered twice.
        </p>
      </div>
    </div>
  );
}


type GuideStep = { tab: Tab; case?: string; target?: string; title: string; body: string };

const GUIDE: GuideStep[] = [
  { tab: "today", target: "guide-counters", title: "A batch runs by itself",
    body: "Six bills went through Read, Count, Match, Investigate, Enter and Check without a person. Green means entered and checked. Amber means someone had to decide." },
  { tab: "case", case: "short", target: "photo-REC-H06-P1", title: "See the gap on bill CAL-0990",
    body: "The bill says 50 cartons. SAM 3.1 counted the dock photos: 28 and 18. A third photo repeats the first, so it is counted once. That is 46." },
  { tab: "case", case: "short", target: "guide-cause", title: "Read the likely cause",
    body: "Before the evidence, the Investigator says what is probably wrong, who is probably responsible, and how sure the records let it be. Unclear is a valid answer." },
  { tab: "case", case: "short", target: "guide-finding", title: "Follow the evidence",
    body: "Every statement carries citations. Click one, such as PHOTO:REC-H06-P3, and the record it rests on lights up on the right." },
  { tab: "approvals", target: "guide-approvals", title: "Decide with one key",
    body: "The proposal sits next to the policy decision. Press A to approve or R to reject. The replay shows the decision recorded in the run." },
  { tab: "approvals", title: "Check the receipts yourself",
    body: "Every step above left a signed receipt. The Proof page verifies all of them in your browser, and breaks the chain if you change one decision." },
];

function readGuideOff(): boolean {
  try {
    return localStorage.getItem("relayloom-guide") === "off";
  } catch {
    return false;
  }
}

function Guide({ step, setStep, onHide }: { step: number; setStep: (n: number) => void; onHide: () => void }) {
  const g = GUIDE[step]!;
  const last = step === GUIDE.length - 1;
  return (
    <div className="sticky top-16 z-30 border-b border-line bg-background/95 backdrop-blur-md" role="region" aria-label="Guided tour">
      <div className="mx-auto flex max-w-[1200px] flex-col gap-3 px-4 py-3 sm:px-6 md:flex-row md:items-center">
        <div className="flex-1">
          <p className="kLabel">Guide, step {step + 1} of {GUIDE.length}</p>
          <p className="mt-1 text-[14px] font-medium text-foreground">{g.title}</p>
          <p className="mt-0.5 max-w-[78ch] text-[13px] leading-relaxed text-ink-muted">{g.body}</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setStep(Math.max(0, step - 1))}
            disabled={step === 0}
            className="inline-flex h-11 items-center rounded-md border border-line px-3.5 text-[13px] font-medium text-foreground transition-colors duration-150 hover:bg-raised disabled:opacity-40"
          >
            Back
          </button>
          {last ? (
            <Link to="/proof" hash="#verifier" className="inline-flex h-11 items-center rounded-md bg-foreground px-4 text-[13px] font-medium text-background transition-opacity duration-150 hover:opacity-90">
              Open the verifier
            </Link>
          ) : (
            <button
              onClick={() => setStep(step + 1)}
              className="inline-flex h-11 items-center rounded-md bg-foreground px-4 text-[13px] font-medium text-background transition-opacity duration-150 hover:opacity-90"
            >
              Next
            </button>
          )}
          <button onClick={onHide} className="inline-flex h-11 items-center rounded-md px-3 text-[13px] text-ink-muted transition-colors duration-150 hover:text-foreground">
            Hide
          </button>
        </div>
      </div>
      <div className="h-0.5 bg-line" aria-hidden="true">
        <div className="h-full bg-foreground" style={{ width: `${((step + 1) / GUIDE.length) * 100}%` }} />
      </div>
    </div>
  );
}

export function Demo() {
  const query = new URLSearchParams(window.location.search);
  const qTab = query.get("tab");
  const qCase = query.get("case");
  const [tab, setTab] = useState<Tab>(qTab === "case" || qTab === "approvals" || qTab === "today" ? qTab : "today");
  const [caseId, setCaseId] = useState(qCase && caseById(qCase) ? qCase : "short");
  const [step, setStep] = useState<number | null>(() => (readGuideOff() ? null : qTab === "case" ? 1 : qTab === "approvals" ? 4 : 0));

  useEffect(() => {
    if (step === null) return;
    const g = GUIDE[step]!;
    setTab(g.tab);
    if (g.case) setCaseId(g.case);
    const timer = window.setTimeout(() => {
      document.querySelectorAll(".guide-ring").forEach((el) => el.classList.remove("guide-ring"));
      const el = g.target ? document.getElementById(g.target) : null;
      if (el) {
        el.classList.add("guide-ring");
        el.scrollIntoView({ block: "center", behavior: "smooth" });
      }
    }, 140);
    return () => window.clearTimeout(timer);
  }, [step]);

  const hideGuide = () => {
    document.querySelectorAll(".guide-ring").forEach((el) => el.classList.remove("guide-ring"));
    setStep(null);
    try {
      localStorage.setItem("relayloom-guide", "off");
    } catch {
      /* storage unavailable, the guide stays hidden for this visit */
    }
  };
  const showGuide = () => {
    setStep(0);
    try {
      localStorage.removeItem("relayloom-guide");
    } catch {
      /* ignore */
    }
  };
  const open = useCallback((id: string) => {
    setCaseId(id);
    setTab("case");
  }, []);
  const c = caseById(caseId)!;
  const tabs: { id: Tab; label: string }[] = [
    { id: "today", label: "Today" },
    { id: "case", label: "Case" },
    { id: "approvals", label: "Approvals" },
  ];

  return (
    <div>
      <div className="border-b border-line bg-amber/5">
        <div className="mx-auto flex max-w-[1200px] flex-wrap items-center gap-x-4 gap-y-1 px-4 py-2.5 sm:px-6">
          <span className="pill border-amber/40 bg-amber/10 text-amber-ink">
            <span className="h-1.5 w-1.5 rounded-full bg-amber" aria-hidden="true" />
            Replay of a run on synthetic data. Read only.
          </span>
          <RunLabel label={LABEL} />
          <span className="tnum font-mono text-[11px] text-ink-muted">run at {run.ran_at.slice(11, 16)}, {run.ran_at.slice(0, 10)}</span>
        </div>
      </div>
      {step !== null && <Guide step={step} setStep={setStep} onHide={hideGuide} />}
      <div className="mx-auto max-w-[1200px] px-4 py-8 sm:px-6">
        {step === null && (
          <button onClick={showGuide} className="mb-4 inline-flex h-11 items-center rounded-md border border-line px-3.5 text-[13px] font-medium text-foreground transition-colors duration-150 hover:bg-raised">
            Show the guide
          </button>
        )}
        <div role="tablist" aria-label="Demo sections" className="mb-6 flex gap-1 border-b border-line">
          {tabs.map((t) => (
            <button
              key={t.id}
              role="tab"
              aria-selected={tab === t.id}
              onClick={() => setTab(t.id)}
              className={`-mb-px flex h-11 items-center border-b-2 px-4 font-mono text-[12px] uppercase tracking-[0.12em] transition-colors duration-150 ${
                tab === t.id ? "border-foreground text-foreground" : "border-transparent text-ink-muted hover:text-foreground"
              }`}
            >
              {t.label}
              {t.id === "approvals" && (
                <span className="tnum ml-2 rounded-full border border-amber/40 bg-amber/10 px-1.5 text-[10.5px] text-amber-ink">{approvals.length}</span>
              )}
            </button>
          ))}
        </div>
        {tab === "case" && (
          <div className="mb-4 flex flex-wrap gap-2" role="group" aria-label="Choose a case">
            {todayRows.map((b) => (
              <button
                key={b.id}
                onClick={() => setCaseId(b.id)}
                className={`tnum inline-flex h-11 items-center rounded-md border px-3.5 font-mono text-[12px] transition-colors duration-150 ${
                  caseId === b.id ? "border-foreground text-foreground" : "border-line text-ink-muted hover:bg-raised hover:text-foreground"
                }`}
              >
                {b.bill}
              </button>
            ))}
          </div>
        )}
        {tab === "today" && <TodayView onOpen={open} />}
        {tab === "case" && <CaseView key={caseId} c={c} />}
        {tab === "approvals" && <ApprovalsView />}
      </div>
    </div>
  );
}
