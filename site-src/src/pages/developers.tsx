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
              <div key={name} className="flex items-center justify-between gap-3 rounded-lg border border-line bg-surface px-4 py-3">
                <span className="font-mono text-[12.5px] text-foreground">{name}</span>
                <Pill tone={LEVEL_TONE[op.level]}>{LEVEL_LABEL[op.level]}</Pill>
              </div>
            ))}
          </div>
          <p className="mt-4 font-mono text-[12px] text-ink-muted">
            limits: {Object.entries(policy.limits).map(([k, v]) => `${k}=${v}`).join("  ")}
          </p>
        </div>
      </section>

      <section className="border-b border-line">
        <div className="mx-auto max-w-[1200px] px-4 py-16 sm:px-6">
          <SectionHead index="Receipts" title="The receipt format" note="Each receipt is signed with Ed25519 and chained to the one before it. Change any field and the chain breaks." />
          <pre className="overflow-x-auto rounded-xl border border-line bg-surface p-5 font-mono text-[12px] leading-relaxed text-foreground">
            {JSON.stringify({ body: sample.body, hash: sample.hash, sig: sample.sig }, null, 2).slice(0, 1800)}
          </pre>
          <p className="mt-4 text-[13.5px] text-ink-muted">
            Verify a chain in your browser on the <Link to="/proof" className="text-foreground underline underline-offset-4">Proof page</Link>, or
            offline with <span className="font-mono">relayloom verify</span>.
          </p>
        </div>
      </section>
      <section className="border-b border-line">
        <div className="mx-auto max-w-[1200px] px-4 py-14 sm:px-6">
          <p className="kLabel">Languages</p>
          <p className="mt-3 max-w-[62ch] text-[15px] leading-relaxed text-ink-muted">
            Phone alerts and the approval screen come in English, Tamil and Hindi, with a language picker that remembers your choice. All 135 strings are listed in
            <span className="font-mono text-foreground"> docs/LANGUAGES.md</span> with the Tamil and Hindi next to the English.
            Muse Glimmer read a Hindi and a Tamil supplier bill with every field correct. Text made by the model or taken from the bill stays as written.
          </p>
        </div>
      </section>
      <section>
        <div className="mx-auto max-w-[1200px] px-4 py-14 sm:px-6">
          <p className="kLabel">Feedback</p>
          <p className="mt-3 max-w-[60ch] text-[15px] leading-relaxed text-ink-muted">
            Something failed, or a delivery you need is not handled yet? Run <span className="font-mono text-foreground">relayloom doctor --report</span> and{" "}
            <a href="https://github.com/Sriharsan/relayloom/issues/new/choose" className="text-foreground underline underline-offset-4" target="_blank" rel="noreferrer">open an issue</a>.
            Nothing is sent anywhere unless you send it, and no bill, photo or token is in the report.
          </p>
        </div>
      </section>
    </div>
  );
}
