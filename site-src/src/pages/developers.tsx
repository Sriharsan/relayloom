import { useState } from "react";
import langs from "@/data/langs.json";
import { Link } from "@/lib/router";
import { CopyBlock, Pill, SectionHead } from "@/components/bits";
import { links, run } from "@/data/site";
import policy from "@/data/policy.json";

const LEVEL_TONE: Record<string, "green" | "amber" | "red"> = { run_alone: "green", run_with_approval: "amber", never: "red" };
const LEVEL_LABEL: Record<string, string> = { run_alone: "runs alone", run_with_approval: "needs approval", never: "never" };

const COMMANDS = [
  { cmd: "relayloom doctor", what: "Says what is ready on this machine and the one command that fixes what is missing. It makes no network calls." },
  { cmd: "relayloom check --bill-json bill.json --po po.json --counted 46", what: "Needs no models: give the count, get HELD or clear, and signed receipts. Add --json for scripts." },
  { cmd: "relayloom check --bill bill.pdf --photos dock/ --po po.json --agent", what: "Reads the bill with Muse Glimmer, counts the photos with SAM 3.1, matches against the order, and writes signed receipts. Exit code 0 is clear to enter, 3 is held." },
  { cmd: "relayloom verify relayloom-out/receipts.jsonl", what: "Checks every signature, hash and chain link with no network. Exit code 0 is a clean chain, 1 is broken." },
  { cmd: "relayloom serve --batch --phone", what: "Starts the app on 127.0.0.1 and phone alerts on your local network, with a QR code for the phone." },
  { cmd: "relayloom models pull", what: "Downloads SAM 3.1 and Muse Glimmer with your own Hugging Face token. After this the checks run with the network off." },
];

const LANG_TABS: [keyof typeof langs, string][] = [["en", "English"], ["ta", "தமிழ்"], ["hi", "हिन्दी"]];

function LanguagesBlock() {
  const [lang, setLang] = useState<keyof typeof langs>("en");
  const x = langs[lang];
  return (
    <section className="border-b border-line">
      <div className="mx-auto grid max-w-[1200px] items-center gap-12 px-6 py-20 sm:px-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:px-14">
        <div>
          <p className="kLabel">Languages</p>
          <h2 className="mt-4 max-w-[16ch] text-balance text-[36px] font-bold leading-[1.05] tracking-[-0.025em] text-foreground sm:text-[48px]">The alert speaks the owner's language.</h2>
          <p className="mt-5 max-w-[46ch] text-[16px] leading-relaxed text-ink-muted">
            Phone alerts and the approval screen come in English, Tamil and Hindi, and the picker remembers the choice. All 135 strings sit in
            <span className="font-mono text-foreground"> docs/LANGUAGES.md</span>, Tamil and Hindi beside the English. Muse Glimmer read a Hindi and a Tamil supplier bill with every field correct.
          </p>
        </div>
        <div className="mx-auto w-full max-w-[420px]">
          <div role="tablist" aria-label="Alert language" className="mb-4 flex gap-2">
            {LANG_TABS.map(([k, label]) => (
              <button key={k} role="tab" aria-selected={lang === k} onClick={() => setLang(k)}
                className={`h-9 rounded-full border px-4 text-[13px] transition-colors duration-150 ${lang === k ? "border-foreground bg-foreground text-background" : "border-line text-ink-muted hover:text-foreground"}`}>{label}</button>
            ))}
          </div>
          <div className="rounded-[28px] border border-line bg-surface p-3 shadow-2xl shadow-black/20">
            <div className="rounded-[20px] border border-line bg-background p-5">
              <p className="font-mono text-[10.5px] uppercase tracking-wider text-ink-muted">Relayloom · now</p>
              <p className="mt-2 text-[18px] font-semibold leading-snug text-foreground">{x.title}</p>
              <p className="mt-2 text-[14.5px] leading-relaxed text-ink-muted">{x.body}</p>
              <p className="mt-4 inline-flex rounded-full border border-amber/50 px-3 py-1 text-[12.5px] text-amber-ink">{x.state}</p>
              <p className="mt-4 rounded-xl bg-foreground px-4 py-3 text-center text-[14px] font-medium text-background">{x.action}</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function FeedbackBlock() {
  return (
    <section>
      <div className="mx-auto grid max-w-[1200px] gap-12 px-6 py-20 sm:px-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:px-14">
        <div>
          <p className="kLabel">Feedback</p>
          <h2 className="mt-4 max-w-[16ch] text-balance text-[36px] font-bold leading-[1.05] tracking-[-0.025em] text-foreground sm:text-[48px]">A delivery we do not handle yet? Tell us.</h2>
          <p className="mt-5 max-w-[46ch] text-[16px] leading-relaxed text-ink-muted">
            One command writes a report you can read before you send anything. Nothing leaves your machine unless you post it.
          </p>
          <a href="https://github.com/Sriharsan/relayloom/issues/new/choose" target="_blank" rel="noreferrer"
            className="mt-7 inline-flex h-12 items-center rounded-full bg-foreground px-6 text-sm font-medium text-background transition-opacity duration-150 hover:opacity-90">Open an issue</a>
        </div>
        <div className="overflow-hidden rounded-2xl border border-line bg-surface">
          <div className="flex items-center gap-2 border-b border-line px-4 py-3" aria-hidden="true">
            <span className="h-2.5 w-2.5 rounded-full bg-red/70" /><span className="h-2.5 w-2.5 rounded-full bg-amber/70" /><span className="h-2.5 w-2.5 rounded-full bg-green/70" />
          </div>
          <pre className="overflow-x-auto p-5 font-mono text-[13px] leading-relaxed text-foreground">{"$ relayloom doctor --report\nok      Python 3.13\nok      signed receipts\nto do   SAM 3.1 weights\nreport written: relayloom-report.txt"}</pre>
          <div className="grid gap-px border-t border-line bg-line sm:grid-cols-2">
            <div className="bg-surface p-5"><p className="kLabel text-green-ink">In the report</p><p className="mt-2 text-[14px] leading-relaxed text-ink-muted">Versions, what is installed, the exact command that failed.</p></div>
            <div className="bg-surface p-5"><p className="kLabel text-amber-ink">Never in it</p><p className="mt-2 text-[14px] leading-relaxed text-ink-muted">Bills, photos, bank details and tokens.</p></div>
          </div>
        </div>
      </div>
    </section>
  );
}

export function Developers() {
  const operations = Object.entries(policy.operations as Record<string, { level: string }>);
  const sample = run.receipts[run.receipts.length - 1];
  return (
    <div>
      <section className="border-b border-line">
        <div className="mx-auto max-w-[1200px] px-4 py-16 sm:px-6">
          <p className="kLabel">Developers</p>
          <h1 className="mt-3 max-w-[22ch] text-balance text-[34px] font-semibold leading-tight tracking-[-0.02em] text-foreground sm:text-[44px]">
            Run the check on your own deliveries today.
          </h1>
          <p className="mt-4 max-w-[60ch] text-[16px] leading-relaxed text-ink-muted">
            One command takes a bill, a purchase order and a folder of photos, and says whether to pay. It runs on your machine with
            open weight Meta models, and it writes receipts you can verify with the network off.
          </p>
          <div className="mt-6 grid max-w-[720px] gap-2">
            <CopyBlock command={`pip install git+${links.repo}.git`} />
            <CopyBlock command="relayloom models pull" />
          </div>
          <p className="mt-3 text-[12.5px] text-ink-muted">
            A PyPI release of the same package follows; until then the install above is the same code. Needs Python 3.11 or newer.
          </p>
        </div>
      </section>

      <section className="border-b border-line">
        <div className="mx-auto max-w-[1200px] px-4 py-16 sm:px-6">
          <SectionHead index="Commands" title="Six commands" note="Each one runs on this machine. None sends a bill, a photo or a number anywhere." />
          <div className="grid gap-3 md:grid-cols-2">
            {COMMANDS.map((c) => (
              <div key={c.cmd} className="rounded-xl border border-line bg-surface p-5">
                <CopyBlock command={c.cmd} />
                <p className="mt-3 text-[13.5px] leading-relaxed text-ink-muted">{c.what}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-b border-line">
        <div className="mx-auto max-w-[1200px] px-4 py-16 sm:px-6">
          <SectionHead index="Policy" title="What runs alone, what asks, what never happens" note="One file, read once at start, outside the model's reach. Its hash is on every receipt." />
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {operations.map(([name, op]) => (
              <div key={name} className="flex min-w-0 flex-wrap items-center justify-between gap-x-3 gap-y-2 rounded-lg border border-line bg-surface px-4 py-3">
                <span className="min-w-0 break-words text-[14px] text-foreground">{name.replace(/_/g, " ")}</span>
                <span className="shrink-0"><Pill tone={LEVEL_TONE[op.level]}>{LEVEL_LABEL[op.level]}</Pill></span>
              </div>
            ))}
          </div>
          <ul className="mt-5 flex flex-wrap gap-2">
            {Object.entries(policy.limits).map(([k, v]) => (
              <li key={k} className="rounded-full border border-line bg-surface px-3 py-1.5 text-[12.5px] text-ink-muted">
                {k.replace(/_/g, " ")} <span className="font-mono text-foreground">{String(v)}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="border-b border-line">
        <div className="mx-auto max-w-[1200px] px-4 py-16 sm:px-6">
          <SectionHead index="Receipts" title="The receipt format" note="Each receipt is signed with Ed25519 and chained to the one before it. Change any field and the chain breaks." />
          <pre className="paper overflow-x-auto p-5 pb-8 font-mono text-[12px] leading-relaxed text-foreground">
            {JSON.stringify({ body: sample.body, hash: sample.hash, sig: sample.sig }, null, 2).slice(0, 1800)}
          </pre>
          <p className="mt-4 text-[13.5px] text-ink-muted">
            Verify a chain in your browser on the <Link to="/proof" className="text-foreground underline underline-offset-4">Proof page</Link>, or
            offline with <span className="font-mono">relayloom verify</span>.
          </p>
        </div>
      </section>
      <LanguagesBlock />
      <FeedbackBlock />
    </div>
  );
}
