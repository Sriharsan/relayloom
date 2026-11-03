import { ArrowRight, MoveRight, ShieldCheck } from "lucide-react";
import { Link } from "@/lib/router";
import { benchmark, fmtSeconds, glimmerSummary, samSummary, video } from "@/data/site";
import {
  boundary, offlineRun, caseById, caseMeta, caseResult, casePhotos, company, firstImage, links, netcutPass, rupees, run, supplierName,
} from "@/data/site";
import { CopyBlock, Photo, Pill, RunLabel, SectionHead } from "@/components/bits";
import { FindingCard } from "@/components/finding";

const SHORT = caseById("short")!;
const BILL_QTY = SHORT.bill!.lines[0]!.qty;
const GOODS = SHORT.counter.total;
const GAP = BILL_QTY - GOODS;
const SHORT_PHOTOS = casePhotos(SHORT).filter((p) => p.counted);
const RUN_LABEL = "Recorded run";

const primary =
  "inline-flex h-12 items-center gap-2 rounded-lg bg-foreground px-5 text-sm font-medium text-background transition-opacity duration-150 hover:opacity-90";
const secondary =
  "inline-flex h-12 items-center gap-2 rounded-lg border border-line bg-surface px-5 text-sm font-medium text-foreground transition-colors duration-150 hover:bg-raised";

function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-line">
      <div className="blueprint absolute inset-0" aria-hidden="true" />
      <div className="relative mx-auto grid max-w-[1200px] grid-cols-1 gap-12 px-4 pb-16 pt-14 sm:px-6 md:pb-24 md:pt-20 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
        <div>
          <p className="kLabel">Autonomous accounts payable</p>
          <h1 className="mt-4 max-w-[19ch] text-balance text-[34px] font-semibold leading-[1.08] tracking-[-0.03em] text-foreground sm:text-[46px] lg:text-[54px]">
            It checks the goods, not just the paperwork.
          </h1>
          <p className="mt-5 max-w-[52ch] text-[15.5px] leading-relaxed text-ink-muted">
            Agents read the bill, look at what actually arrived, investigate any gap with evidence, and pay only what the
            books and the goods both support. Runs inside the company's own network on Meta open weight models.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link to="/demo" className={primary}>
              Take the 60 second tour
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link to="/proof" className={secondary}>See the proof</Link>
            {links.video && (
              <a href={links.video} target="_blank" rel="noreferrer" className={secondary}>
                Watch the 3 minute video
              </a>
            )}
          </div>
          <p className="mt-8 font-mono text-[11.5px] leading-relaxed text-ink-muted">
            Demo company: {company.name}. {company.note} Muse Glimmer 30B reads bills. SAM 3.1 counts delivered goods.
            Everything else is code.
          </p>
        </div>

        <div className="relative">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-[0.8fr_1.2fr]">
            <div className="rounded-xl border border-line bg-surface p-4">
              <div className="flex items-center justify-between">
                <span className="font-mono text-[11px] text-ink-muted">Bill</span>
                <span className="tnum font-mono text-[12px] text-foreground">{SHORT.bill_no}</span>
              </div>
              <p className="mt-4 text-[15px] font-medium text-foreground">{supplierName(SHORT.supplier_id)}</p>
              <p className="mt-1 text-[13px] text-ink-muted">{SHORT.bill!.lines[0]!.description}, qty {BILL_QTY}</p>
              <p className="tnum mt-4 font-mono text-[15px] text-foreground">{rupees(SHORT.bill!.total_inr)}</p>
              <div className="mt-4 border-t border-line pt-3">
                <Pill tone="muted">order {SHORT.po_number}</Pill>
              </div>
            </div>
            <div className="rounded-xl border border-line bg-surface p-4">
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-[11px] text-ink-muted">Dock photos</span>
                <Pill tone="green">counted by SAM 3.1</Pill>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2">
                {SHORT_PHOTOS.map((p) => (
                  <figure key={p.photo}>
                    <Photo src={p.image} alt={`${p.photo} with ${p.count} items outlined and numbered`} />
                    <figcaption className="tnum mt-1 font-mono text-[10.5px] text-ink-muted">{p.photo}: {p.count}</figcaption>
                  </figure>
                ))}
              </div>
              <div className="mt-3 flex items-baseline justify-between">
                <span className="text-[12px] text-ink-muted">counted on the dock</span>
                <span className="tnum font-mono text-[26px] font-medium leading-none text-green-ink">{GOODS}</span>
              </div>
            </div>
          </div>
          <div className="mt-4 flex items-center justify-center">
            <span className="pill !whitespace-normal text-center border-amber/40 bg-amber/10 px-3 py-1.5 text-[11.5px] text-amber-ink">
              <span className="h-1.5 w-1.5 rounded-full bg-amber" aria-hidden="true" />
              Gap of {GAP}. Investigator finding ready. Held for a person.
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}

const PROBLEMS = [
  { n: "01", title: `The bill says ${BILL_QTY}. The dock got ${GOODS}.`, body: "The paperwork matches itself. The goods on the floor never get asked." },
  { n: "02", title: "Paperwork matching cannot see the goods.", body: "A three way match on documents only proves the documents agree, not that anything arrived." },
  { n: "03", title: "Someone pays the gap or spends the afternoon chasing it.", body: "Short deliveries get paid in full, or a person spends hours gathering proof." },
];

const bench = (metric: string) => benchmark?.rows.find((r) => r.metric === metric);

function Story() {
  const caught = bench("Bad bills caught");
  const made = bench("Wrong payments made");
  return (
    <section className="border-b border-line bg-surface/40">
      <div className="mx-auto grid max-w-[1200px] grid-cols-1 gap-px px-4 py-12 sm:px-6 lg:grid-cols-3">
        <div className="pb-8 lg:pb-0 lg:pr-10">
          <p className="kLabel">Who we are</p>
          <h2 className="mt-3 text-[20px] font-semibold leading-snug tracking-tight text-foreground">One founder, one promise.</h2>
          <p className="mt-3 text-[14px] leading-relaxed text-ink-muted">
            Relayloom is built by Sriharsan B S. The promise is simple: a company pays a supplier only for what actually arrived, and can prove it.
            Open source, on Meta open weights, on the company's own machine.
          </p>
          <a href="#who" className="mt-3 inline-block text-[13px] text-foreground underline underline-offset-4">Meet the founder</a>
        </div>
        <div className="border-line py-8 lg:border-l lg:px-10 lg:py-0">
          <p className="kLabel">Why we matter</p>
          <h2 className="mt-3 text-[20px] font-semibold leading-snug tracking-tight text-foreground">Paperwork cannot see the dock.</h2>
          <p className="mt-3 text-[14px] leading-relaxed text-ink-muted">
            Bills get paid on documents that only agree with each other. U.S. federal law names paying for goods not received as an improper payment, and
            auditors keep finding invoices approved with no proof of receipt.
          </p>
          <a href="#stakes" className="mt-3 inline-block text-[13px] text-foreground underline underline-offset-4">See the sources</a>
        </div>
        <div className="border-line pt-8 lg:border-l lg:pl-10 lg:pt-0">
          <p className="kLabel">Why you need us</p>
          <h2 className="mt-3 text-[20px] font-semibold leading-snug tracking-tight text-foreground">It catches what paperwork lets through.</h2>
          <p className="mt-3 text-[14px] leading-relaxed text-ink-muted">
            On a demo set of 30 deliveries, paperwork alone caught {caught?.paperworkOnly} bad bills and paid {made?.paperworkOnly} wrongly. With the goods in the loop,
            Relayloom caught {caught?.paperworkPlusGoods} and paid {made?.paperworkPlusGoods} wrongly.
          </p>
          <Link to="/proof" className="mt-3 inline-block text-[13px] text-foreground underline underline-offset-4">See the proof</Link>
        </div>
      </div>
    </section>
  );
}

const STAKES = [
  { title: "Law calls it an improper payment", body: "U.S. federal law defines an improper payment to include a payment for a good or service not received.", source: "31 U.S.C. § 3351", href: "https://www.law.cornell.edu/uscode/text/31/3351" },
  { title: "Auditors find invoices approved blind", body: "When an agency lacked an effective review of contractor invoices, it had no assurance that the goods and services billed had been received.", source: "GAO-06-547", href: "https://www.gao.gov/products/gao-06-547" },
  { title: "Controls cut losses and speed up detection", body: "The largest global study of occupational fraud links anti-fraud controls to lower losses and faster detection.", source: "ACFE, Occupational Fraud 2026", href: "https://www.acfe.com/fraud-resources/report-to-the-nations" },
];

function Stakes() {
  return (
    <section id="stakes" className="scroll-mt-20 border-b border-line">
      <div className="mx-auto max-w-[1200px] px-4 py-16 sm:px-6">
        <SectionHead
          index="Why it matters"
          title="The risk is written into law and into every audit"
          note="Three primary sources. They describe the problem. The results further down are our own measurements."
        />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {STAKES.map((s) => (
            <a key={s.source} href={s.href} target="_blank" rel="noreferrer" className="group flex flex-col rounded-xl border border-line bg-surface p-6 transition-colors duration-150 hover:border-line-strong">
              <h3 className="text-[16px] font-medium leading-snug text-foreground">{s.title}</h3>
              <p className="mt-2 flex-1 text-[13.5px] leading-relaxed text-ink-muted">{s.body}</p>
              <span className="mt-4 font-mono text-[11.5px] text-foreground underline-offset-4 group-hover:underline">{s.source}</span>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}

const PRINCIPLES = [
  { title: "Evidence before payment", body: "Nothing is entered unless the books and the goods agree." },
  { title: "Autonomy inside a policy", body: "What runs alone and what waits for the owner is set in a file the models cannot change." },
  { title: "Every claim traceable", body: "Findings cite records and photos, and code checks each citation before anyone reads it." },
  { title: "Private by default", body: "Models run on the company's own machine, and private numbers are masked before any model sees them." },
];

function WhoWeAre() {
  return (
    <section id="who" className="scroll-mt-20 border-b border-line">
      <div className="mx-auto grid max-w-[1200px] grid-cols-1 gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[0.9fr_1.1fr]">
        <div>
          <SectionHead index="Who we are" title="A founder who ships the proof" />
          <p className="max-w-[54ch] text-[14.5px] leading-relaxed text-ink-muted">
            Relayloom is built by <span className="text-foreground">Sriharsan B S</span>, founder and engineer. It was built between 27 October and 4 November 2026
            for the Meta Global AI Developer Hackathon, on Meta's open weight models: Muse Glimmer 30B reads the bill and SAM 3.1 counts the goods.
            Every commit in the repository has one author, and every figure on this site comes from a run you can repeat.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <a href={links.repo} target="_blank" rel="noreferrer" className={primary}>Read the code<ArrowRight className="h-4 w-4" /></a>
            <Link to="/proof" className={secondary}>Check the numbers</Link>
          </div>
        </div>
        <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {PRINCIPLES.map((x, i) => (
            <li key={x.title} className="rounded-xl border border-line bg-surface p-5">
              <span className="tnum font-mono text-[11px] text-ink-muted">0{i + 1}</span>
              <h3 className="mt-2 text-[15px] font-medium text-foreground">{x.title}</h3>
              <p className="mt-1.5 text-[13px] leading-relaxed text-ink-muted">{x.body}</p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

function Problem() {
  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-[1200px] px-4 py-16 sm:px-6">
        <SectionHead index="01 / The problem" title="Every bill is a claim. Few of them get checked against the floor." />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {PROBLEMS.map((p) => (
            <div key={p.n} className="rounded-xl border border-line bg-surface p-6">
              <span className="tnum font-mono text-[11px] text-ink-muted">{p.n}</span>
              <h3 className="mt-3 text-[16px] font-medium leading-snug text-foreground">{p.title}</h3>
              <p className="mt-2 text-[13.5px] leading-relaxed text-ink-muted">{p.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

const AGENTS = [
  { name: "Intake", does: "Takes bills and dock photos in and masks private numbers.", chip: "code" },
  { name: "Reader", does: "Reads the bill line by line into a strict schema.", chip: "Muse Glimmer 30B" },
  { name: "Counter", does: "Counts delivered goods in every dock photo.", chip: "SAM 3.1" },
  { name: "Matcher", does: "Compares order, bill and counted goods as a running total.", chip: "code" },
  { name: "Investigator", does: "Chases any gap and cites every statement. Muse Glimmer can write the text when it runs live.", chip: "code, cited" },
  { name: "Clerk", does: "Posts matching bills to the ledger. Entry and verification are separate duties.", chip: "ledger" },
  { name: "Checker", does: "Independent verification: a separate request reads the ledger back and compares every field.", chip: "independent readback" },
  { name: "Disputer", does: "Drafts the dispute and files it once a person approves.", chip: "Muse Glimmer 30B + browser agent" },
];

function HowItWorks() {
  return (
    <section id="how" className="scroll-mt-20 border-b border-line">
      <div className="mx-auto max-w-[1200px] px-4 py-16 sm:px-6">
        <SectionHead
          index="02 / How it works"
          title="Eight agents, each one auditable"
          note="Models read and count. Code matches, enters and verifies. Every step leaves a signed, chained receipt, so any edit to a recorded decision is detectable."
        />
        <ol className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {AGENTS.map((a, i) => (
            <li key={a.name}>
              <div className="h-full rounded-xl border border-line bg-surface p-4 transition-colors duration-150 hover:border-line-strong">
                <div className="flex items-center justify-between">
                  <span className="tnum font-mono text-[10.5px] text-ink-muted">{String(i + 1).padStart(2, "0")}</span>
                  <MoveRight className="h-3.5 w-3.5 text-ink-muted lg:hidden" aria-hidden="true" />
                </div>
                <h3 className="mt-2.5 text-[15px] font-medium text-foreground">{a.name}</h3>
                <p className="mt-1.5 text-[13px] leading-relaxed text-ink-muted">{a.does}</p>
                <div className="mt-3">
                  <Pill tone={a.chip.includes("Muse") || a.chip.includes("SAM") ? "amber" : "muted"}>{a.chip}</Pill>
                </div>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

const COLUMNS = [
  {
    title: "Runs alone", tone: "green",
    items: ["Read bills", "Count goods", "Match", "Investigate any gap", "Enter matching bills", "Check the readback", "Reconcile after reconnect"],
  },
  {
    title: "Waits for a person", tone: "amber",
    items: ["Any mismatch", "Bills above the limit", "Sending a dispute", "A new supplier or changed bank details"],
  },
  {
    title: "Never", tone: "red",
    items: ["Change bank details from invoice text", "Enter a bill whose readback failed", "Change the books while offline"],
  },
] as const;

function Autonomy() {
  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-[1200px] px-4 py-16 sm:px-6">
        <SectionHead index="03 / Autonomy" title="Where it runs alone, where it waits" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {COLUMNS.map((c) => (
            <div key={c.title} className={`rounded-xl border bg-surface p-6 ${c.tone === "amber" ? "border-amber/30" : c.tone === "red" ? "border-red/30" : "border-line"}`}>
              <h3 className={`text-[15px] font-medium ${c.tone === "amber" ? "text-amber-ink" : c.tone === "red" ? "text-red-ink" : "text-foreground"}`}>{c.title}</h3>
              <ul className="mt-4 space-y-2.5">
                {c.items.map((t) => (
                  <li key={t} className="flex items-start gap-2.5 text-[13.5px] text-ink-muted">
                    <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${c.tone === "amber" ? "bg-amber" : c.tone === "red" ? "bg-red" : "bg-green"}`} aria-hidden="true" />
                    {t}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <p className="mt-5 text-[13px] text-ink-muted">These levels live in a policy file the models cannot change. Every action leaves a tamper-evident audit trail.</p>
      </div>
    </section>
  );
}

function Spotlight() {
  const inv = SHORT.investigation!;
  const proposal = SHORT.proposal as { reason: string; policy_level: string };
  const cites = [...new Set(inv.finding.statements.flatMap((s) => s.cites))].slice(0, 5);
  return (
    <section className="border-b border-line">
      <div className="mx-auto grid max-w-[1200px] grid-cols-1 gap-8 px-4 py-16 sm:px-6 lg:grid-cols-[1fr_0.9fr] lg:items-start">
        <div>
          <SectionHead index="04 / Investigation" title="A gap becomes evidence before it becomes a question" />
          <p className="max-w-lg text-[14.5px] leading-relaxed text-ink-muted">
            When the count and the bill disagree, the Investigator recounts every photo, adds up earlier deliveries on the
            same order, checks the price and the supplier's history, and writes a finding. Every statement carries its citation.
          </p>
          <div className="mt-6 flex flex-col gap-3 rounded-xl border border-line bg-surface p-5">
            <p className="font-mono text-[11px] text-ink-muted">Code checks every citation and every number before a person sees the finding.</p>
            <div className="flex flex-wrap gap-2">
              {cites.map((c) => (
                <span key={c} className="tnum pill bg-raised text-[11px] text-foreground">{c}</span>
              ))}
            </div>
          </div>
        </div>
        <div className="lg:pt-24">
          <FindingCard title={`Short delivery on ${SHORT.po_number}`} statements={inv.finding.statements} label={RUN_LABEL} />
          {SHORT.diagnosis && (
            <div className="mb-4 rounded-xl border border-line bg-surface px-5 py-4">
              <p className="kLabel">Likely cause</p>
              <p className="mt-2 text-[15.5px] font-medium text-foreground">{SHORT.diagnosis.label}</p>
              <p className="mt-1 text-[13px] text-ink-muted">Probably: {SHORT.diagnosis.responsible}. Confidence {SHORT.diagnosis.confidence}.</p>
            </div>
          )}
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <span className="pill !whitespace-normal border-line bg-raised text-[11.5px] text-foreground">Proposed: {proposal.reason}</span>
            <span className="pill border-amber/40 bg-amber/10 text-[11.5px] text-amber-ink">
              Policy: {proposal.policy_level === "run_with_approval" ? "needs approval" : proposal.policy_level.replace(/_/g, " ")}
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}

function Cases() {
  return (
    <section id="cases" className="scroll-mt-20 border-b border-line">
      <div className="mx-auto max-w-[1200px] px-4 py-16 sm:px-6">
        <SectionHead
          index="05 / Cases"
          title="Seven runs, seven outcomes"
          note="Each card is one run of the real agents, ledger and receipts on demo bills and delivery photos."
        />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {caseMeta.map((m) => {
            const c = caseById(m.id)!;
            const result = caseResult(m.id);
            return (
              <article key={m.id} className="flex flex-col rounded-xl border border-line bg-surface p-5">
                <div className="flex items-center justify-between gap-2">
                  <Pill tone={result === "PASS" ? "green" : "red"}>{result}</Pill>
                  <RunLabel label={RUN_LABEL} />
                </div>
                <h3 className="mt-4 text-[15.5px] font-medium leading-snug text-foreground">{m.title}</h3>
                <p className="mt-2 text-[13.5px] leading-relaxed text-ink-muted">{m.sentence}</p>
                <p className="mt-3 font-mono text-[11.5px] text-foreground">{c.status}</p>
                <div className="mt-4 flex-1" />
                <Photo src={firstImage(c)} alt={`${m.title}, delivery photo`} aspect="16 / 10" />
              </article>
            );
          })}
          <article className="flex flex-col rounded-xl border border-line bg-surface p-5">
            <div className="flex items-center justify-between gap-2">
              <Pill tone={netcutPass ? "green" : "red"}>{netcutPass ? "PASS" : "FAIL"}</Pill>
              <RunLabel label={RUN_LABEL} />
            </div>
            <h3 className="mt-4 text-[15.5px] font-medium leading-snug text-foreground">Network cut mid batch</h3>
            <p className="mt-2 text-[13.5px] leading-relaxed text-ink-muted">
              The link drops after the first invoice. Reading continues, nothing else is entered. On reconnect the ledger is read first and nothing is entered twice.
            </p>
            <div className="mt-4 flex-1" />
            <dl className="grid grid-cols-2 gap-3 rounded-lg border border-line bg-raised p-4">
              <div>
                <dd className="tnum font-mono text-[26px] leading-none text-amber-ink">{run.netcut.in_books_while_cut}</dd>
                <dt className="mt-1.5 text-[12px] text-ink-muted">in the books while cut</dt>
              </div>
              <div>
                <dd className="tnum font-mono text-[26px] leading-none text-green-ink">{run.netcut.in_books_after_reconnect}</dd>
                <dt className="mt-1.5 text-[12px] text-ink-muted">after reconnect, none twice</dt>
              </div>
            </dl>
          </article>
        </div>
      </div>
    </section>
  );
}

const INSIDE = ["Agents", "Muse Glimmer", "SAM 3.1", "Ledger", "Checker", "Receipts"];
const KIND_LABEL: Record<string, string> = {
  gstin: "Tax ID", bank_account: "Bank account", ifsc: "Bank code", phone: "Phone", email: "Email",
};

function Boundary() {
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
                  <text x={x + 34} y={y + 28} fill="var(--foreground)" fontSize="13" fontFamily="Candara, Nunito Sans, sans-serif" fontWeight="500">{label}</text>
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


const TOUR = [
  { n: "1", title: "Watch a batch run itself", body: "Six bills went through Read, Count, Match, Investigate, Enter and Check without a person. Green is entered and checked. Amber waits for you.", cta: "Open Today", to: "/demo?tab=today" },
  { n: "2", title: "See the gap on bill CAL-0990", body: `The bill says ${BILL_QTY} cartons. SAM 3.1 counted ${GOODS} across two dock photos, and a repeated photo was counted once.`, cta: "Open the case", to: "/demo?tab=case&case=short" },
  { n: "3", title: "Follow the evidence", body: "Click any citation under the finding. The record or photo it rests on lights up.", cta: "Open the finding", to: "/demo?tab=case&case=short" },
  { n: "4", title: "Decide with one key", body: "Press A to approve or R to reject. A dispute goes out only after you decide.", cta: "Open approvals", to: "/demo?tab=approvals" },
  { n: "5", title: "Check the receipts yourself", body: `Verify all ${run.receipts.length} signed receipts in your browser, then change one decision and watch the chain break.`, cta: "Open the verifier", to: "/proof#verifier" },
];

function TryIt() {
  return (
    <section id="try" className="scroll-mt-20 border-b border-line">
      <div className="mx-auto max-w-[1200px] px-4 py-16 sm:px-6">
        <SectionHead
          index="Start here"
          title="Five clicks show the whole idea"
          note="Nothing is sent anywhere. The Demo page also walks you through it with a guide that points at each thing to look at."
        />
        <ol className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-5">
          {TOUR.map((s) => (
            <li key={s.n} className="flex">
              <div className="flex w-full flex-col rounded-xl border border-line bg-surface p-5">
                <span className="tnum font-mono text-[11px] text-ink-muted">Step {s.n}</span>
                <h3 className="mt-2 text-[15px] font-medium leading-snug text-foreground">{s.title}</h3>
                <p className="mt-2 flex-1 text-[13px] leading-relaxed text-ink-muted">{s.body}</p>
                <Link
                  to={s.to.split("#")[0]!}
                  hash={s.to.includes("#") ? "#" + s.to.split("#")[1] : ""}
                  className="mt-4 inline-flex h-11 items-center justify-between gap-2 rounded-md border border-line px-3.5 text-[13px] font-medium text-foreground transition-colors duration-150 hover:bg-raised"
                >
                  {s.cta}
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

const FIXES = [
  ["SAM 3.1 counts 0", "The wording does not match the picture. 8 of our 13 trial wordings returned 0.", "Try another noun. Keep two wordings that agree: one for the count and one for the Investigator's recount."],
  ["Muse Glimmer needs minutes per bill", "CPU only, about 1 output token a second on this laptop.", "Run bills as a background batch, or serve the model on a GPU."],
  ["Hugging Face answers 403 for SAM 3.1", "The weights are gated.", "Request access with your own account and put a read token in .env as HF_TOKEN."],
  ["llama-server runs out of memory loading Glimmer", "Weight repacking needs about 12 GB more.", "Start llama-server with --no-repack."],
  ["A bill is held as a recount disagreement", "The two counts differ.", "A person recounts. That hold is the design, not an error."],
];

function SetUp() {
  const lines = run.cases.map((c) => `${c.id.padEnd(10)} ${c.state}`).concat([
    `netcut     held_offline, then entered_checked (${run.netcut.in_books_while_cut} in the books while cut, ${run.netcut.in_books_after_reconnect} after reconnect)`,
    `receipts   ${run.receipts.length} signed, verified: ${run.receipts_verified ? "yes" : "no"}`,
  ]);
  return (
    <section id="setup" className="scroll-mt-20 border-b border-line">
      <div className="mx-auto max-w-[1200px] px-4 py-16 sm:px-6">
        <SectionHead
          index="Set it up for your work"
          title="Three commands to see it run, then make it yours"
          note="Laid out like Meta's open-weight cookbook: what you need, a quickstart, what you should see, how to change it, and what to do when something fails."
        />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="rounded-xl border border-line bg-surface">
            <div className="border-b border-line px-5 py-3"><span className="kLabel">What you need</span></div>
            <dl className="px-5 py-4 text-[13.5px]">
              {[
                ["Models", "Muse Glimmer 30B (Q4_K_M) and SAM 3.1"],
                ["Hardware we used", "Intel Core Ultra 7 155U laptop, 32 GB, CPU only"],
                ["Offline", "Yes, once the weights are downloaded"],
                ["Ledger", "Built in, or ERPNext in Docker"],
                ["Speed on this laptop", `${fmtSeconds(glimmerSummary.min)} to ${fmtSeconds(glimmerSummary.max)} per bill and about ${Math.round(samSummary.mean)} seconds per photo`],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between gap-4 border-b border-line py-2 last:border-0">
                  <dt className="text-ink-muted">{k}</dt>
                  <dd className="text-right text-foreground">{v}</dd>
                </div>
              ))}
            </dl>
          </div>
          <div className="flex flex-col gap-3">
            <p className="kLabel">Quickstart</p>
            <CopyBlock command={`git clone ${links.repo} && cd relayloom && pip install -r requirements-ap.txt`} />
            <CopyBlock command="python -m pytest -q" />
            <CopyBlock command="python scripts/export_bench_run.py out.json" />
            <p className="kLabel mt-2">What you should see</p>
            <pre className="overflow-x-auto rounded-lg border border-line bg-raised px-3.5 py-3 font-mono text-[12px] leading-relaxed text-foreground">{lines.join("\n")}</pre>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div className="rounded-xl border border-line bg-surface p-5">
            <p className="kLabel">Make it yours</p>
            <ul className="mt-3 space-y-2.5 text-[13.5px] leading-relaxed text-ink-muted">
              <li><span className="text-foreground">Change what runs alone.</span> Edit <code className="font-mono text-[12px] text-foreground">relayloom/ap/policy.json</code>: levels, limits, tolerances. The models cannot change it.</li>
              <li><span className="text-foreground">Count your own goods.</span> Change the item words in the catalogue, for example "cardboard box", and give each item a second wording for the recount.</li>
              <li><span className="text-foreground">Use your books.</span> Put your ERPNext address and keys in <code className="font-mono text-[12px] text-foreground">.env</code> and run with <code className="font-mono text-[12px] text-foreground">--live</code>.</li>
              <li><span className="text-foreground">Run the models yourself.</span> Muse Glimmer through llama.cpp and SAM 3.1 through Ultralytics, as in the README.</li>
            </ul>
          </div>
          <div className="overflow-hidden rounded-xl border border-line bg-surface">
            <div className="border-b border-line px-5 py-3"><span className="kLabel">If something fails</span></div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[520px] text-left text-[12.5px]">
                <thead>
                  <tr className="border-b border-line text-ink-muted">
                    <th className="px-5 py-2.5 font-medium">Symptom</th>
                    <th className="px-5 py-2.5 font-medium">Cause</th>
                    <th className="px-5 py-2.5 font-medium">Fix</th>
                  </tr>
                </thead>
                <tbody>
                  {FIXES.map(([a, b, c]) => (
                    <tr key={a} className="border-b border-line align-top last:border-0">
                      <td className="px-5 py-2.5 text-foreground">{a}</td>
                      <td className="px-5 py-2.5 text-ink-muted">{b}</td>
                      <td className="px-5 py-2.5 text-ink-muted">{c}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <p className="mt-4 text-[13px] text-ink-muted">
          Next: <Link to="/demo" className="text-foreground underline underline-offset-4">the demo</Link>,{" "}
          <Link to="/proof" className="text-foreground underline underline-offset-4">the proof</Link>, or{" "}
          <a href={links.repo} target="_blank" rel="noreferrer" className="text-foreground underline underline-offset-4">the code</a>.
        </p>
      </div>
    </section>
  );
}


function VideoEvidence() {
  const v = video;
  const steps = [
    { at: `${v.detection.first_motion_s.toFixed(2)} s`, title: "Movement starts on the dock", body: "The detector compares each frame with the one before it." },
    { at: `${v.detection.detected_at_s.toFixed(2)} s`, title: `Delivery detected, ${v.detection.detection_lag_s.toFixed(2)} s after it began`, body: `First phone alert. The detector uses ${v.median_ms_per_frame} ms per frame, so it keeps up with a live camera.` },
    ...v.frames.map((f) => ({ at: `${f.t.toFixed(2)} s`, title: `Steady view ${f.id.slice(-2)} kept: ${f.count} counted`, body: `SAM 3.1, ${Math.round(f.seconds ?? 0)} s on this CPU. A second wording agrees.` })),
    { at: "result", title: `${v.total} counted against ${v.billed} billed`, body: `${v.diagnosis?.label}, confidence ${v.diagnosis?.confidence}. Second phone alert: the delivery needs the owner.` },
  ];
  return (
    <section id="video" className="scroll-mt-20 border-b border-line">
      <div className="mx-auto grid max-w-[1200px] grid-cols-1 gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[1fr_1fr] lg:items-start">
        <div>
          <SectionHead index="Built" title="The dock camera raises the alert in under a second" />
          <p className="max-w-[60ch] text-[14.5px] leading-relaxed text-ink-muted">
            A video file or a camera stream goes through the same reader. Movement is detected within a quarter of a second, steady views are kept as
            photographs, and they join the purchase order like any other delivery evidence. Counting is the slower step on a CPU, so the alert does not wait for it.
          </p>
          <ol className="mt-6 space-y-0">
            {steps.map((s, i) => (
              <li key={i} className="relative flex gap-4 pb-5 last:pb-0">
                {i < steps.length - 1 && <span className="absolute left-[41px] top-6 h-full w-px bg-line" aria-hidden="true" />}
                <span className="tnum w-[64px] shrink-0 pt-0.5 text-right font-mono text-[11.5px] text-ink-muted">{s.at}</span>
                <span className="relative mt-1.5 h-[11px] w-[11px] shrink-0 rounded-full border-2 border-green bg-green/20" aria-hidden="true" />
                <div>
                  <p className="text-[14px] font-medium text-foreground">{s.title}</p>
                  <p className="mt-0.5 text-[12.5px] leading-relaxed text-ink-muted">{s.body}</p>
                </div>
              </li>
            ))}
          </ol>
          <div className="mt-5 max-w-[60ch]">
            <CopyBlock command="python scripts/dock_watch.py 0 --phone --count CARTON-HD" />
          </div>
          <p className="mt-3 max-w-[60ch] text-[12.5px] leading-relaxed text-ink-muted">
            The clip is a demo: two pallet photographs slide into an empty dock. The detector, the counts and the case are real. Cameras and streams use the
            same reader, and this run was verified on a video file.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {v.frames.map((f) => (
            <figure key={f.id} className="rounded-xl border border-line bg-surface p-3">
              <Photo src={`/img/${f.overlay || f.id + ".jpg"}`} alt={`Key frame ${f.id} with ${f.count} items outlined and numbered`} />
              <figcaption className="mt-2 flex items-baseline justify-between">
                <span className="tnum font-mono text-[11px] text-ink-muted">{f.id} at {f.t.toFixed(2)} s</span>
                <span className="tnum font-mono text-[20px] leading-none text-green-ink">{f.count}</span>
              </figcaption>
            </figure>
          ))}
          <div className="col-span-2 flex items-baseline justify-between rounded-xl border border-amber/40 bg-surface px-5 py-4">
            <span className="text-[13px] text-ink-muted">Video total against the bill</span>
            <span className="tnum font-mono text-[24px] leading-none text-amber-ink">{v.total} of {v.billed}</span>
          </div>
        </div>
      </div>
    </section>
  );
}

function PhoneAlerts() {
  const alerts = run.alerts.filter((a) => a.kind !== "offline").slice(0, 4);
  return (
    <section id="phone" className="scroll-mt-20 border-b border-line">
      <div className="mx-auto grid max-w-[1200px] grid-cols-1 items-center gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[1fr_340px]">
        <div>
          <SectionHead index="Built" title="The alert reaches your phone, without the internet" />
          <ul className="max-w-[60ch] space-y-3 text-[14.5px] leading-relaxed text-ink-muted">
            <li><span className="text-foreground">Raised by the agents.</span> A delivery that needs you, hidden text that tried to change a bank account, a failed readback, a cut network.</li>
            <li><span className="text-foreground">Local network only.</span> Start it with <code className="font-mono text-[12.5px] text-foreground">--phone</code>. It prints a link with a random token. Open it on a phone on the same Wi-Fi. No cloud, no account, no internet.</li>
            <li><span className="text-foreground">Read only.</span> The phone page shows alerts and can change nothing. The main app stays on the laptop's own address.</li>
          </ul>
          <div className="mt-5 max-w-[60ch]"><CopyBlock command="python -m relayloom.ap --phone --batch" /></div>
          <p className="mt-3 max-w-[60ch] text-[12.5px] leading-relaxed text-ink-muted">
            Tested with unit tests (wrong token, read only, instant delivery) and in a phone sized browser. The alerts on the right are the ones this run raised.
          </p>
        </div>
        <div className="mx-auto w-full max-w-[320px] rounded-[28px] border border-line-strong bg-surface p-3">
          <div className="rounded-[20px] border border-line bg-background px-3 pb-4 pt-3">
            <p className="text-[15px] font-semibold text-foreground">Relayloom alerts</p>
            <p className="text-[12px] text-ink-muted">Connected, waiting for deliveries</p>
            <div className="mt-3 flex flex-col gap-2">
              {alerts.map((a) => (
                <div key={a.id} className={`rounded-xl border bg-surface p-3 ${a.kind === "needs_owner" ? "border-amber/50" : a.kind === "injection" ? "border-red/50" : "border-line"}`}>
                  <p className="text-[14px] font-medium text-foreground">{a.title}</p>
                  <p className="mt-1 text-[12.5px] leading-snug text-ink-muted">{a.body}</p>
                  <p className="mt-2 font-mono text-[10.5px] text-ink-muted">{a.time} · {a.case}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

const PLANNED = [
  { title: "Many cameras, one dock", body: "Several cameras per dock, each steady view matched to its purchase order automatically, counted on a GPU server." },
  { title: "Real time on a GPU server", body: `Every match, policy and security step completes in under a second. On this laptop, with no GPU, Muse Glimmer reads a bill in ${fmtSeconds(glimmerSummary.min)} to ${fmtSeconds(glimmerSummary.max)} and SAM 3.1 counts a photo in about ${Math.round(samSummary.mean)} seconds. A GPU server is the target for real time.` },
  { title: "Supplier intelligence", body: "The supplier file is in place and every investigation reads it. Patterns across suppliers and over time build on it." },
];

function Planned() {
  return (
    <section className="border-b border-line">
      <div className="mx-auto max-w-[1200px] px-4 py-16 sm:px-6">
        <SectionHead
          index="Roadmap"
          title="Where the evidence loop goes next"
          note="Everything above is built and measured. These steps extend the same loop: evidence first, then the decision."
        />
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-4">
          {PLANNED.map((x) => (
            <div key={x.title} className="rounded-xl border border-dashed border-line bg-surface p-5">
              <Pill tone="muted">roadmap</Pill>
              <h3 className="mt-3 text-[15px] font-medium text-foreground">{x.title}</h3>
              <p className="mt-2 text-[13px] leading-relaxed text-ink-muted">{x.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function ClosingBand() {
  return (
    <section className="relative overflow-hidden">
      <div className="relative mx-auto max-w-[1200px] px-4 py-20 text-center sm:px-6">
        <ShieldCheck className="mx-auto h-5 w-5 text-green-ink" aria-hidden="true" />
        <h2 className="mx-auto mt-4 max-w-[24ch] text-balance text-[28px] font-semibold leading-tight tracking-[-0.02em] text-foreground sm:text-[36px]">
          Pay for what arrived. Prove it.
        </h2>
        <p className="mx-auto mt-3 max-w-[56ch] text-[14.5px] leading-relaxed text-ink-muted">
          Agents read the bill, look at what actually arrived, investigate any gap with evidence, and pay only what the books and the goods both support.
          Every step leaves a tamper-evident receipt.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link to="/demo" className={primary}>
            Take the 60 second tour
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link to="/proof" className={secondary}>See the proof</Link>
          <a href={links.repo} target="_blank" rel="noreferrer" className={secondary}>Read the code</a>
        </div>
      </div>
    </section>
  );
}

export function Home() {
  return (
    <div>
      <Hero />
      <Story />
      <Problem />
      <Stakes />
      <TryIt />
      <HowItWorks />
      <Autonomy />
      <Spotlight />
      <Cases />
      <Boundary />
      <SetUp />
      <VideoEvidence />
      <PhoneAlerts />
      <Planned />
      <WhoWeAre />
      <ClosingBand />
    </div>
  );
}
