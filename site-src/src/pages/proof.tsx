import { useCallback, useEffect, useState } from "react";
import {
  benchmark, glimmerRate, samBenchRows, samDemoRows, caseById, caseMeta, caseResult, fmtSeconds, glimmerSummary, meas, netcutPass, run, samSummary, samTrials,
  type SignedReceipt,
} from "@/data/site";
import { Pill, RunLabel, SectionHead } from "@/components/bits";
import { verifyChain, type Verdict } from "@/lib/receipts";

const LABEL = "Rehearsal";

function Tile({ value, label, tone = "foreground" }: { value: string; label: string; tone?: "foreground" | "green" | "amber" }) {
  const color = tone === "green" ? "text-green-ink" : tone === "amber" ? "text-amber-ink" : "text-foreground";
  return (
    <div className="rounded-xl border border-line bg-surface px-5 py-4">
      <span className={`tnum font-mono text-[26px] leading-none ${color}`}>{value}</span>
      <p className="mt-2 text-[12.5px] leading-snug text-ink-muted">{label}</p>
    </div>
  );
}

function Table({ head, children, min = 640 }: { head: { t: string; right?: boolean }[]; children: React.ReactNode; min?: number }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-line bg-surface">
      <table className="w-full text-left text-[13.5px]" style={{ minWidth: min }}>
        <thead>
          <tr className="border-b border-line text-ink-muted">
            {head.map((h) => (
              <th key={h.t} className={`px-5 py-3 font-medium ${h.right ? "text-right" : ""}`}>{h.t}</th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

const num = "tnum px-5 py-3 text-right font-mono text-[13px] text-foreground";

function Counting() {
  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-[1200px] px-4 py-14 sm:px-6">
        <SectionHead
          index="01 / Counting the goods"
          title="SAM 3.1 counted every delivery photo on this laptop"
          note="Each count is a real run of the open weight model on a CPU, saved with its photo hash, wording, count and time."
        />
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Tile value={`${samSummary.exact} of ${samSummary.runs}`} label="counts match the delivery record with the wordings in use" tone="green" />
          <Tile value={fmtSeconds(samSummary.mean)} label="average per photo on a laptop CPU" />
          <Tile value={`${fmtSeconds(samSummary.min)} to ${fmtSeconds(samSummary.max)}`} label="fastest to slowest photo" />
          <Tile value={`${samSummary.trialsZero} of ${samSummary.trials}`} label="other recount wordings tried returned 0, so wording is fixed per item" tone="amber" />
        </div>
        <div className="mt-6">
          <Table
            head={[{ t: "Photo" }, { t: "Goods" }, { t: "Wording" }, { t: "Counted", right: true }, { t: "Record", right: true }, { t: "Time", right: true }]}
            min={720}
          >
            {samDemoRows.map((r) => (
              <tr key={r.photo + r.prompt} className="border-b border-line last:border-0">
                <td className="tnum px-5 py-3 font-mono text-[12.5px] text-foreground">{r.photo}</td>
                <td className="px-5 py-3 text-foreground">{r.item}</td>
                <td className="px-5 py-3 font-mono text-[12.5px] text-ink-muted">{r.prompt}</td>
                <td className={num + (r.count === r.truth ? " !text-green-ink" : " !text-red-ink")}>{r.count}</td>
                <td className={num}>{r.truth}</td>
                <td className={num}>{r.infer_seconds.toFixed(1)} s</td>
              </tr>
            ))}
          </Table>
        </div>
        <p className="mt-3 max-w-[78ch] text-[12.5px] leading-relaxed text-ink-muted">
          The recount wording for each item was chosen from trials on these same photos, so this table shows the system at work, not a test on unseen photos.
          {` The ${samBenchRows.length} benchmark photos were counted the same way and are not listed here. The ${samTrials.length} trial runs are saved alongside.`}
        </p>
      </div>
    </section>
  );
}

function Reading() {
  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-[1200px] px-4 py-14 sm:px-6">
        <SectionHead
          index="02 / Reading the bills"
          title="Muse Glimmer 30B read bills on the same laptop"
          note={`${meas.glimmer[0]?.model}, ${meas.glimmer[0]?.route}. Every reading passed the strict schema, and none can return bank details.`}
        />
        <div className="mb-6 overflow-hidden rounded-xl border border-line bg-surface">
          <div className="border-b border-line px-5 py-3"><span className="kLabel">Recipe banner</span></div>
          <dl className="grid grid-cols-1 gap-x-8 px-5 py-2 text-[13px] sm:grid-cols-2">
            {[
              ["Model", "Muse Glimmer 30B"],
              ["Precision", "Q4_K_M, 17 GB"],
              ["Server", "llama.cpp b12020, one slot, 8192 context"],
              ["Hardware", meas.machine.cpu],
              ["Memory", meas.machine.memory + ", no GPU"],
              ["Offline", "Yes, after the weights are downloaded"],
              ["Output", "Strict JSON schema, low reasoning effort"],
              ["Output speed", `${glimmerRate.min.toFixed(1)} to ${glimmerRate.max.toFixed(1)} tokens per second end to end`],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between gap-4 border-b border-line py-2 last:border-0 sm:[&:nth-last-child(2)]:border-0">
                <dt className="text-ink-muted">{k}</dt>
                <dd className="text-right text-foreground">{v}</dd>
              </div>
            ))}
          </dl>
          <p className="border-t border-line px-5 py-3 text-[12.5px] leading-relaxed text-ink-muted">
            Meta's open-weight cookbook lists Intel Core Ultra laptops as verified for Q4_K_M but has no speed numbers for them yet. These are ours,
            from a Core Ultra 7 155U on the CPU alone, with prompts of 357 to 410 tokens.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-3">
          <Tile value={`${glimmerSummary.valid} of ${glimmerSummary.runs}`} label="readings valid against the schema" tone="green" />
          <Tile value={fmtSeconds(glimmerSummary.mean)} label="average per bill, CPU only" />
          <Tile value={`${fmtSeconds(glimmerSummary.min)} to ${fmtSeconds(glimmerSummary.max)}`} label="fastest to slowest bill" />
        </div>
        <div className="mt-6">
          <Table head={[{ t: "Reading" }, { t: "Recorded" }, { t: "Prompt tokens", right: true }, { t: "Output tokens", right: true }, { t: "Time", right: true }, { t: "Schema", right: true }]} min={680}>
            {meas.glimmer.map((g) => (
              <tr key={g.bill} className="border-b border-line last:border-0">
                <td className="px-5 py-3 text-foreground">{g.bill}</td>
                <td className="tnum px-5 py-3 font-mono text-[12.5px] text-ink-muted">{g.recorded_at.slice(0, 16)}</td>
                <td className={num}>{g.prompt_tokens}</td>
                <td className={num}>{g.output_tokens}</td>
                <td className={num}>{fmtSeconds(g.seconds)}</td>
                <td className="px-5 py-3 text-right"><Pill tone="green">{g.schema_check}</Pill></td>
              </tr>
            ))}
          </Table>
        </div>
        <p className="mt-3 font-mono text-[11.5px] text-ink-muted">
          Machine: {meas.machine.cpu}, {meas.machine.memory}, {meas.machine.gpu}, {meas.machine.os}.
        </p>
      </div>
    </section>
  );
}

function Cases() {
  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-[1200px] px-4 py-14 sm:px-6">
        <SectionHead
          index="03 / Seven cases"
          title="The agents, the policy and the ledger behave as written"
          note="One run of the real agents, matcher, Investigator, approval policy, ledger and Checker. Bill values come from the bill record, and counts from SAM 3.1 where a recording exists."
        />
        <Table head={[{ t: "Case" }, { t: "Likely cause" }, { t: "Outcome" }, { t: "Result", right: true }]} min={720}>
          {caseMeta.map((m) => {
            const c = caseById(m.id)!;
            const r = caseResult(m.id);
            return (
              <tr key={m.id} className="border-b border-line last:border-0">
                <td className="px-5 py-3 text-foreground">{m.title}</td>
                <td className="px-5 py-3 text-[13px] text-ink-muted">{c.diagnosis ? `${c.diagnosis.label}, confidence ${c.diagnosis.confidence}` : "none, nothing to investigate"}</td>
                <td className="px-5 py-3 text-[13px] text-ink-muted">{c.status}</td>
                <td className="px-5 py-3 text-right"><Pill tone={r === "PASS" ? "green" : "red"}>{r}</Pill></td>
              </tr>
            );
          })}
          <tr>
            <td className="px-5 py-3 text-foreground">Network cut mid batch</td>
            <td className="px-5 py-3 text-[13px] text-ink-muted">none, nothing to investigate</td>
            <td className="px-5 py-3 text-[13px] text-ink-muted">
              {run.netcut.in_books_while_cut} in the books while cut, {run.netcut.in_books_after_reconnect} after reconnect, none twice
            </td>
            <td className="px-5 py-3 text-right"><Pill tone={netcutPass ? "green" : "red"}>{netcutPass ? "PASS" : "FAIL"}</Pill></td>
          </tr>
        </Table>
      </div>
    </section>
  );
}

function Benchmark() {
  if (!benchmark) return null;
  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-[1200px] px-4 py-14 sm:px-6">
        <SectionHead
          index="04 / Benchmark"
          title="With the goods in the loop, more errors are caught and fewer clean bills are held"
          note={`Synthetic set built by us, ${benchmark.setSize} deliveries with known answers. ${benchmark.note}`}
        />
        <Table head={[{ t: "Metric" }, { t: "Paperwork only" }, { t: "Paperwork plus goods" }, { t: "Basis", right: true }]}>
          {benchmark.rows.map((r) => (
            <tr key={r.metric} className="border-b border-line last:border-0">
              <td className="px-5 py-3 text-foreground">{r.metric}</td>
              <td className="tnum px-5 py-3 font-mono text-[13px] text-foreground">{r.paperworkOnly}</td>
              <td className="tnum px-5 py-3 font-mono text-[13px] text-green-ink">{r.paperworkPlusGoods}</td>
              <td className="px-5 py-3 text-right text-[12px] text-ink-muted">{r.basis}</td>
            </tr>
          ))}
        </Table>
        <p className="mt-8 kLabel">Per scenario</p>
        <div className="mt-3">
          <Table head={[{ t: "Scenario" }, { t: "Right call" }, { t: "Deliveries", right: true }, { t: "Paperwork only", right: true }, { t: "Paperwork plus goods", right: true }]}>
            {benchmark.perScenario.map((s) => (
              <tr key={s.scenario} className="border-b border-line last:border-0">
                <td className="px-5 py-3 text-foreground">{s.scenario}</td>
                <td className="px-5 py-3 text-[12.5px] text-ink-muted">{s.rule}</td>
                <td className={num}>{s.deliveries}</td>
                <td className={num + (s.paperworkOnly < s.deliveries ? " !text-amber-ink" : "")}>{s.paperworkOnly} of {s.deliveries}</td>
                <td className={num + " !text-green-ink"}>{s.plusGoods} of {s.deliveries}</td>
              </tr>
            ))}
          </Table>
        </div>
      </div>
    </section>
  );
}

function Verifier() {
  const [receipts, setReceipts] = useState<SignedReceipt[]>(run.receipts);
  const [verdicts, setVerdicts] = useState<Verdict[] | null>(null);
  const [tampered, setTampered] = useState(false);
  const [error, setError] = useState("");

  const verify = useCallback(async (list: SignedReceipt[]) => {
    try {
      setVerdicts(await verifyChain(list, run.public_key));
      setError("");
    } catch {
      setError("This browser cannot verify Ed25519 signatures. Use a current Chrome, Edge, Safari or Firefox.");
    }
  }, []);

  useEffect(() => {
    void verify(run.receipts);
  }, [verify]);

  const tamper = () => {
    const copy = run.receipts.map((r) => ({ ...r, body: { ...r.body } }));
    const target = Math.min(2, copy.length - 1);
    copy[target]!.body.decision = "changed after signing";
    setReceipts(copy);
    setTampered(true);
    void verify(copy);
  };
  const restore = () => {
    setReceipts(run.receipts);
    setTampered(false);
    void verify(run.receipts);
  };

  const okCount = verdicts?.filter((v) => v.ok).length ?? 0;
  const cases = new Set(receipts.map((r) => r.body.case)).size;

  return (
    <div id="verifier" className="scroll-mt-24 rounded-xl border border-line bg-surface">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-5 py-3">
        <span className="kLabel">Receipt verifier</span>
        <span className="font-mono text-[11px] text-ink-muted">runs in your browser, nothing uploaded</span>
      </div>
      <div className="px-5 py-4">
        <p className="max-w-[70ch] text-[13.5px] leading-relaxed text-ink-muted">
          Every step of every case left a receipt signed with Ed25519 and chained to the one before it. This page recomputes each SHA 256 hash and checks each
          signature against the run's public key. Change one decision and the chain breaks at that step.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          {tampered ? (
            <button onClick={restore} className="inline-flex h-11 items-center rounded-md bg-foreground px-4 text-[13px] font-medium text-background transition-opacity duration-150 hover:opacity-90">
              Restore the receipts
            </button>
          ) : (
            <button onClick={tamper} className="inline-flex h-11 items-center rounded-md border border-line px-4 text-[13px] font-medium text-foreground transition-colors duration-150 hover:bg-raised">
              Change one decision and verify again
            </button>
          )}
          {verdicts && (
            <Pill tone={okCount === receipts.length ? "green" : "red"}>
              {okCount} of {receipts.length} verified across {cases} cases
            </Pill>
          )}
        </div>
        {error && <p className="mt-3 text-[13px] text-red-ink">{error}</p>}
        <p className="mt-3 break-all font-mono text-[10.5px] text-ink-muted">public key {run.public_key}</p>
        {verdicts && (
          <div className="mt-4 max-h-[420px] overflow-auto rounded-lg border border-line">
            <table className="w-full min-w-[640px] text-left font-mono text-[12px]">
              <thead className="sticky top-0 bg-raised">
                <tr className="border-b border-line text-ink-muted">
                  <th className="px-4 py-2.5 font-medium">case</th>
                  <th className="px-4 py-2.5 font-medium">step</th>
                  <th className="px-4 py-2.5 font-medium">hash</th>
                  <th className="px-4 py-2.5 text-right font-medium">result</th>
                </tr>
              </thead>
              <tbody>
                {receipts.map((r, i) => {
                  const v = verdicts[i];
                  return (
                    <tr key={i} className={`border-b border-line last:border-0 ${v && !v.ok ? "bg-red/5" : ""}`}>
                      <td className="px-4 py-2 text-foreground">{r.body.case}</td>
                      <td className="px-4 py-2 text-ink-muted">{r.body.agent}, {r.body.step}</td>
                      <td className="tnum px-4 py-2 text-ink-muted">{r.hash.slice(0, 12)}</td>
                      <td className="px-4 py-2 text-right">
                        <span className={`pill ${v?.ok ? "border-green/30 bg-green/10 text-green-ink" : "border-red/30 bg-red/10 text-red-ink"}`}>
                          {v?.ok ? "verified" : (v?.reason ?? "checking")}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

const LABELS = [
  { item: "SAM 3.1 counts and times", kind: "Measured", note: "real runs of the open weight model on this laptop's CPU, saved with photo hashes" },
  { item: "Muse Glimmer 30B bill readings and times", kind: "Measured", note: "real runs on the same laptop, each checked against the strict schema" },
  { item: "Case outcomes and receipts", kind: "Measured", note: "the real agents, policy, built in ledger and Checker, with signed receipts" },
  { item: "Bill values in the replay", kind: "Labelled", note: "taken from the bill record, not re-read by the model in that run" },
  { item: "Delivery photos, companies, suppliers and money", kind: "Labelled", note: "synthetic: our own drawings, fictional names, amounts in rupees" },
];

export function Proof() {
  return (
    <div>
      <section className="border-b border-line">
        <div className="mx-auto max-w-[1200px] px-4 py-14 sm:px-6">
          <div className="flex items-center gap-3">
            <RunLabel label={LABEL} />
            <span className="font-mono text-[11px] text-ink-muted">/proof</span>
          </div>
          <h1 className="mt-4 max-w-[24ch] text-balance text-[30px] font-semibold leading-[1.12] tracking-[-0.02em] text-foreground sm:text-[40px]">
            Every number on this page came from our own runs on synthetic data.
          </h1>
        </div>
      </section>
      <Counting />
      <Reading />
      <Cases />
      <Benchmark />
      <section className="border-b border-line">
        <div className="mx-auto max-w-[1200px] px-4 py-14 sm:px-6">
          <SectionHead index={benchmark ? "05 / Receipt chain" : "04 / Receipt chain"} title="Check the chain in your own browser" />
          <Verifier />
        </div>
      </section>
      <section>
        <div className="mx-auto max-w-[1200px] px-4 py-14 sm:px-6">
          <SectionHead index={benchmark ? "06 / Labels" : "05 / Labels"} title="What is measured and what is labelled" />
          <ul className="overflow-hidden rounded-xl border border-line bg-surface">
            {LABELS.map((l) => (
              <li key={l.item} className="flex flex-col gap-1 border-b border-line px-5 py-3.5 last:border-0 sm:flex-row sm:items-center sm:justify-between">
                <span className="text-[13.5px] text-foreground">{l.item}</span>
                <span className="flex items-center gap-3">
                  <span className="text-[12.5px] text-ink-muted">{l.note}</span>
                  <span className="pill bg-raised text-[11px] text-foreground">{l.kind}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}
