import { boundary, offlineRun, caseById, run } from "@/data/site";
import { Pill, RunLabel, SectionHead } from "@/components/bits";

const RUN_LABEL = "Recorded run";

const INSIDE = ["Agents", "Muse Glimmer", "SAM 3.1", "Ledger", "Checker", "Receipts"];
const KIND_LABEL: Record<string, string> = {
  gstin: "Tax ID", bank_account: "Bank account", ifsc: "Bank code", phone: "Phone", email: "Email",
};

export function Boundary() {
  const injection = caseById("injection")!;
  const masks = injection.masks;
  const hidden = injection.injection && typeof injection.injection === "object" ? injection.injection : null;
  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-[1200px] px-4 py-16 sm:px-6">
        <SectionHead
          index="06 / The boundary"
          title="Private numbers are masked before anything leaves the building"
          note="Models run on the machine. Tax ids, bank accounts, phones and emails are masked in what any model sees, and the originals stay inside."
        />
        <div className="rounded-xl border border-line bg-surface p-4 sm:p-8">
          <svg viewBox="0 0 760 300" className="h-auto w-full" role="img" aria-label="Diagram of the company network boundary with an egress gateway on the edge">
            <rect x="24" y="24" width="640" height="252" rx="16" fill="var(--raised)" stroke="var(--line-strong)" strokeWidth="1.5" />
            <text x="52" y="58" fill="var(--ink-muted)" fontSize="11" fontFamily="JetBrains Mono, monospace" letterSpacing="2">INSIDE THE COMPANY NETWORK</text>
            {INSIDE.map((label, i) => {
              const x = 52 + (i % 3) * 196;
              const y = 84 + Math.floor(i / 3) * 92;
              const model = label.includes("Muse") || label.includes("SAM");
              return (
                <g key={label}>
                  <rect x={x} y={y} width="176" height="68" rx="10" fill="var(--surface)" stroke="var(--line)" />
                  <circle cx={x + 20} cy={y + 24} r="3.5" fill={model ? "var(--amber)" : "var(--green)"} />
                  <text x={x + 34} y={y + 28} fill="var(--foreground)" fontSize="13" fontFamily="Figtree, Inter, sans-serif" fontWeight="500">{label}</text>
                  <text x={x + 20} y={y + 50} fill="var(--ink-muted)" fontSize="10.5" fontFamily="JetBrains Mono, monospace">{model ? "open weight model" : "on machine"}</text>
                </g>
              );
            })}
            <rect x="648" y="128" width="104" height="44" rx="8" fill="var(--surface)" stroke="var(--amber)" strokeWidth="1.5" />
            <text x="700" y="146" textAnchor="middle" fill="var(--amber-ink)" fontSize="10.5" fontFamily="JetBrains Mono, monospace">EGRESS</text>
            <text x="700" y="160" textAnchor="middle" fill="var(--amber-ink)" fontSize="10.5" fontFamily="JetBrains Mono, monospace">GATEWAY</text>
            <text x="700" y="196" textAnchor="middle" fill="var(--ink-muted)" fontSize="10.5" fontFamily="JetBrains Mono, monospace">off by default</text>
          </svg>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="overflow-hidden rounded-xl border border-line bg-surface">
            <div className="flex items-center justify-between border-b border-line px-5 py-3">
              <span className="kLabel">Masked in bill {injection.bill_no}</span>
              <RunLabel label={RUN_LABEL} />
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[420px] text-left font-mono text-[12px]">
                <thead>
                  <tr className="border-b border-line text-ink-muted">
                    <th className="px-5 py-2.5 font-medium">what</th>
                    <th className="px-5 py-2.5 text-right font-medium">length</th>
                    <th className="px-5 py-2.5 font-medium">fingerprint</th>
                  </tr>
                </thead>
                <tbody>
                  {masks.map((m, i) => (
                    <tr key={i} className="border-b border-line last:border-0">
                      <td className="px-5 py-2.5 text-foreground">{KIND_LABEL[m.kind] ?? m.kind}</td>
                      <td className="tnum px-5 py-2.5 text-right text-foreground">{m.length}</td>
                      <td className="tnum px-5 py-2.5 text-ink-muted">{m.sha256}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          {hidden && (
            <div className="rounded-xl border border-red/30 bg-surface">
              <div className="flex items-center justify-between border-b border-line px-5 py-3">
                <span className="kLabel">Hidden text found in the bill</span>
                <Pill tone="red">ignored</Pill>
              </div>
              <div className="px-5 py-4">
                <p className="rounded-lg border border-line bg-raised px-3.5 py-3 font-mono text-[12px] leading-relaxed text-foreground">{hidden.lines[0]}</p>
                <p className="mt-3 text-[13.5px] leading-relaxed text-ink-muted">
                  The text asked to move the payment to a new account. The attempt is receipted, and payment goes to the account in the
                  ledger's supplier master: ending {injection.pay_to && typeof injection.pay_to === "object" ? injection.pay_to.account_last4 : ""}.
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="mt-4 overflow-hidden rounded-xl border border-line bg-surface">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-5 py-3">
            <span className="kLabel">Tested in Docker, no route out</span>
            <Pill tone={boundary.passed ? "green" : "red"}>{boundary.passed ? "all checks pass" : "failed"}</Pill>
          </div>
          <div className="grid grid-cols-1 gap-0 lg:grid-cols-2">
            <ul className="border-b border-line px-5 py-4 lg:border-b-0 lg:border-r">
              {boundary.checks.map((c) => (
                <li key={c.check} className="flex items-start justify-between gap-3 py-1.5 text-[13px]">
                  <span className="text-foreground">{c.check}</span>
                  <span className="shrink-0 font-mono text-[11px] text-green-ink">{c.result.toLowerCase()}</span>
                </li>
              ))}
            </ul>
            <div className="overflow-x-auto px-5 py-4">
              <p className="kLabel">Gateway log from that run</p>
              <table className="mt-2 w-full min-w-[360px] text-left font-mono text-[12px]">
                <tbody>
                  {boundary.gateway_log.map((e, i) => (
                    <tr key={i} className="border-b border-line last:border-0">
                      <td className="py-1.5 pr-3 text-ink-muted">{e.time.slice(11, 19)}</td>
                      <td className="py-1.5 pr-3 text-foreground">{e.host}</td>
                      <td className="py-1.5 text-amber-ink">{e.decision}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="mt-3 text-[12px] leading-relaxed text-ink-muted">
                The agents ran the cases on a Docker network with no route out. Direct connections failed, and the gateway refused hosts that are not in the policy.
                Network isolation verified in Docker on {boundary.time.slice(0, 10)}.
              </p>
              <p className="kLabel mt-5">Tested fully disconnected, {offlineRun.started.slice(0, 10)}</p>
              <p className="mt-1 text-[12.5px] leading-relaxed text-ink-muted">
                Airplane mode on and every cable unplugged. The laptop had no route to the internet, and then the agents ran on it.
              </p>
              <ul className="mt-2 divide-y divide-line text-[13px]">
                {offlineRun.steps.map((st) => (
                  <li key={st.step} className="flex items-start justify-between gap-3 py-2">
                    <span className="text-foreground">{st.step}</span>
                    <span className="shrink-0 font-mono text-[11px] text-green-ink">{st.result.toLowerCase()}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-2 text-[12px] text-ink-muted">Live Muse Glimmer read a bill in 194 s and live SAM 3.1 counted 24 of 24 cans in 39 s, with no network. Full report: docs/OFFLINE_RUN.md in the repository.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}


export function AcrossSuppliers() {
  const found = run.supplier_patterns;
  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-[1200px] px-4 py-16 sm:px-6">
        <SectionHead
          index="Across suppliers"
          title="Where the money leaks first"
          note="Every supplier file is read together. Suppliers rank by units billed and never received, and a repeat pattern is flagged with the invoices it rests on."
        />
        <div className="overflow-x-auto rounded-xl border border-line bg-surface">
          <table className="w-full min-w-[480px] text-left text-[13px]">
            <thead className="text-[11px] uppercase tracking-wide text-ink-muted">
              <tr><th className="px-4 py-3">Supplier</th><th className="px-4 py-3">Counted orders</th><th className="px-4 py-3">Short orders</th><th className="px-4 py-3">Units missing</th><th className="px-4 py-3">Evidence</th></tr>
            </thead>
            <tbody>
              {found.suppliers.map((r) => (
                <tr key={r.supplier_id} className="border-t border-line">
                  <td className="px-4 py-3 text-foreground">{r.name}</td>
                  <td className="tnum px-4 py-3">{r.orders_counted}</td>
                  <td className="tnum px-4 py-3">{r.short_orders}</td>
                  <td className="tnum px-4 py-3 font-mono">{r.units_missing}</td>
                  <td className="px-4 py-3 font-mono text-[12px] text-ink-muted">{r.evidence.join(", ") || "none"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-[12.5px] text-ink-muted">{found.flags.length ? found.flags.map((f) => f.text).join(" ") : "No supplier has two or more short orders yet, so nothing is flagged as a repeat pattern."}</p>
      </div>
    </section>
  );
}
