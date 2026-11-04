import { ArrowRight } from "lucide-react";
import { Link } from "@/lib/router";
import { agent, benchmark, confidence, fmtSeconds, glimmerSummary, links, offlineRun, real, samSummary, video } from "@/data/site";
import { CopyBlock, Photo } from "@/components/bits";
import { RealCases } from "@/components/realcases";


const btn =
  "inline-flex h-12 items-center gap-2 rounded-full bg-foreground px-6 text-sm font-medium text-background transition-opacity duration-150 hover:opacity-90";
const btnLine =
  "inline-flex h-12 items-center gap-2 rounded-full border border-line px-6 text-sm font-medium text-foreground transition-colors duration-150 hover:bg-raised";

const bench = (metric: string) => benchmark?.rows.find((r) => r.metric === metric);
const caught = bench("Bad bills caught")?.paperworkPlusGoods;
const wrongPaid = bench("Money paid wrongly")?.paperworkPlusGoods;

/* ------------------------------------------------------------------ hero */
function Hero() {
  const lead = real.rows.find((r) => r.pid === "P01")!;
  const overlay = lead.results[0];
  const BILLED = 30; // a sample bill written for this real photo
  return (
    <section className="relative border-b border-line">
      <div className="blueprint absolute inset-0" aria-hidden="true" />
      <div className="relative mx-auto max-w-[1200px] px-4 pb-14 pt-14 sm:px-6 md:pt-24">
        <p className="kLabel">Autonomous accounts payable</p>
        <h1 className="mt-5 max-w-[11ch] text-balance text-[56px] font-bold leading-[0.95] tracking-[-0.035em] text-foreground sm:text-[88px] lg:text-[124px]">
          Pay for what arrived.
          <span className="block text-green-ink">Prove it.</span>
        </h1>
        <div className="mt-10 grid gap-10 lg:grid-cols-[minmax(0,420px)_1fr] lg:items-end">
          <div>
            <p className="max-w-[44ch] text-[17px] leading-relaxed text-ink-muted">
              Agents read the bill, count the goods in the photo, and hold any payment the goods do not support. Meta open weight models, on the
              company's own machine.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link to="/proof" className={btn}>
                See the proof <ArrowRight className="h-4 w-4" />
              </Link>
              <Link to="/developers" className={btnLine}>Run it yourself</Link>
              {links.video && (
                <a href={links.video} target="_blank" rel="noreferrer" className={btnLine}>Watch the film</a>
              )}
            </div>
          </div>
          <div className="relative pb-6">
            <div className="overflow-hidden rounded-[28px] border border-line bg-raised shadow-2xl shadow-black/30">
              <Photo src={`/img/real/overlay/${overlay.overlay}`} alt="A van full of boxes, each box outlined and numbered by SAM 3.1" aspect="3 / 2" />
            </div>
            <div className="absolute -top-5 left-4 rotate-[-2deg] rounded-xl border border-line bg-background px-4 py-3 shadow-xl sm:left-8">
              <p className="font-mono text-[10.5px] uppercase tracking-wider text-ink-muted">A sample bill says</p>
              <p className="tnum font-mono text-[40px] leading-none text-foreground">{BILLED}</p>
            </div>
            <div className="absolute -bottom-5 right-4 rotate-[1.5deg] rounded-xl border border-amber/50 bg-background px-4 py-3 shadow-xl sm:right-8">
              <p className="font-mono text-[10.5px] uppercase tracking-wider text-amber-ink">SAM 3.1 counted</p>
              <p className="tnum font-mono text-[40px] leading-none text-amber-ink">{overlay.count}</p>
              <p className="mt-1 text-[12px] text-ink-muted">by eye: {lead.hand_count}. Short by {BILLED - overlay.count}, held for a person</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------ number strip */
function Strip() {
  const items = [
    caught ? `${caught} bad bills caught` : "",
    wrongPaid ? `${wrongPaid} paid wrongly` : "",
    `${samSummary.exact} of ${samSummary.runs} SAM counts exact`,
    `${offlineRun.steps.length} of ${offlineRun.steps.length} steps passed with the network off`,
    `receipts verified in your browser`,
  ].filter(Boolean);
  return (
    <section className="border-b border-line bg-surface" aria-label="Measured results">
      <div className="mx-auto flex max-w-[1200px] flex-wrap items-center gap-x-8 gap-y-2 px-4 py-5 font-mono text-[12.5px] text-ink-muted sm:px-6">
        {items.map((x, i) => (
          <span key={x} className="flex items-center gap-8">
            <span className="text-foreground">{x}</span>
            {i < items.length - 1 && <span aria-hidden="true">/</span>}
          </span>
        ))}
      </div>
    </section>
  );
}

/* ----------------------------------------------------- 1. the agent decides */
function Looks() {
  const steps = agent.trace;
  return (
    <section id="agent" className="border-b border-line bg-raised">
      <div className="mx-auto grid max-w-[1200px] gap-12 px-4 py-20 sm:px-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <div className="lg:sticky lg:top-24 lg:self-start">
          <p className="kLabel">01 / The agent decides what to look for</p>
          <h2 className="mt-4 text-balance text-[38px] font-bold leading-[1.04] tracking-[-0.02em] text-foreground sm:text-[52px]">
            One word found nothing. Another found {agent.trace.find((t) => t.words === "can")?.count} cans.
          </h2>
          <p className="mt-5 max-w-[46ch] text-[15.5px] leading-relaxed text-ink-muted">
            Muse Glimmer proposes the words, calls SAM 3.1 as a tool, and looks at the numbered picture itself. Code owns the number: it is always the masks SAM
            returned, and a count is accepted when two words agree or when Glimmer's own look at the overlay confirms it. Everything else goes to a person.
          </p>
          <dl className="mt-8 grid grid-cols-2 gap-x-6 gap-y-5 border-t border-line pt-6">
            <div><dt className="kLabel">Delivery record</dt><dd className="tnum mt-1 font-mono text-[28px] text-foreground">{agent.hand_count ?? "n/a"}</dd></div>
            <div><dt className="kLabel">First word</dt><dd className="tnum mt-1 font-mono text-[28px] text-amber-ink">{agent.first_try_count}</dd></div>
            <div><dt className="kLabel">Tool calls</dt><dd className="tnum mt-1 font-mono text-[28px] text-foreground">{agent.calls}</dd></div>
            <div><dt className="kLabel">Run</dt><dd className="mt-1 text-[13px] leading-snug text-ink-muted">{agent.route}, {fmtSeconds(agent.seconds)}</dd></div>
          </dl>
        </div>
        <ol className="relative">
          <span className="absolute bottom-2 left-[15px] top-2 w-px bg-line" aria-hidden="true" />
          {steps.map((s, i) => (
            <li key={i} className="relative pb-7 pl-12 last:pb-0">
              <span
                className={`absolute left-0 top-0.5 flex h-[31px] w-[31px] items-center justify-center rounded-full border bg-background font-mono text-[11px] ${
                  s.tool === "glimmer" ? "border-amber/60 text-amber-ink" : "border-green/60 text-green-ink"
                }`}
                aria-hidden="true"
              >
                {i + 1}
              </span>
              {s.tool === "sam3.1" ? (
                <div className="flex flex-wrap items-start gap-4">
                  {s.overlay && (
                    <div className="w-[148px] shrink-0">
                      <Photo src={`/img/agent/${s.overlay}`} alt={`SAM 3.1 overlay for the word ${s.words}`} aspect="4 / 3" />
                    </div>
                  )}
                  <div>
                    <p className="font-mono text-[11px] uppercase tracking-wider text-green-ink">SAM 3.1 tool call</p>
                    <p className="mt-1 text-[17px] text-foreground">
                      looks for <span className="rounded bg-surface px-1.5 py-0.5 font-mono text-[15px]">{s.words}</span>
                    </p>
                    <p className="tnum mt-1 font-mono text-[34px] leading-none text-foreground">{s.count}<span className="ml-2 text-[13px] text-ink-muted">found</span></p>
                  </div>
                </div>
              ) : s.output?.words ? (
                <div>
                  <p className="font-mono text-[11px] uppercase tracking-wider text-amber-ink">Muse Glimmer proposes words</p>
                  <p className="mt-2 flex flex-wrap gap-2">
                    {s.output.words.map((w) => (
                      <span key={w} className="rounded-full border border-line bg-background px-3 py-1 font-mono text-[13px] text-foreground">{w}</span>
                    ))}
                  </p>
                </div>
              ) : (
                <div>
                  <p className="font-mono text-[11px] uppercase tracking-wider text-amber-ink">Muse Glimmer looks at the overlay</p>
                  <p className="mt-2 max-w-[52ch] text-[16px] italic leading-snug text-foreground">"{s.output?.note}"</p>
                  <p className="mt-1 font-mono text-[11.5px] text-ink-muted">verdict: {s.output?.verdict}, {fmtSeconds(s.seconds ?? 0)}</p>
                </div>
              )}
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

/* -------------------------------------------------------- 2. real goods strip */
function Goods() {
  const rows = [...real.rows].filter((r) => r.results[0].count > 0).sort((a, b) => Number(b.hand_count !== null) - Number(a.hand_count !== null));
  const at = (t: number) => confidence.real.find((r) => r.threshold === t)!;
  return (
    <section id="goods" className="border-b border-line">
      <div className="mx-auto max-w-[1200px] px-4 pt-20 sm:px-6">
        <p className="kLabel">02 / The goods</p>
        <div className="mt-4 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <h2 className="max-w-[18ch] text-balance text-[38px] font-bold leading-[1.04] tracking-[-0.02em] text-foreground sm:text-[52px]">
            Real photos expose what clean ones hide.
          </h2>
          <p className="max-w-[44ch] text-[14.5px] leading-relaxed text-ink-muted">
            Real photos, free-licence stock and the builder's own. SAM 3.1 outlines and numbers every item, and each count sits next to a hand count that includes the far items.
          </p>
        </div>
        <div className="mt-8 grid gap-px overflow-hidden rounded-3xl border border-line bg-line sm:grid-cols-3">
          <div className="bg-background p-6">
            <p className="font-mono text-[11px] uppercase tracking-wider text-ink-muted">Lowest score kept 0.4</p>
            <p className="tnum mt-3 font-mono text-[44px] leading-none text-amber-ink">{at(0.4).total_abs_error}<span className="ml-2 text-[14px] text-ink-muted">items wrong in all</span></p>
          </div>
          <div className="bg-background p-6">
            <p className="font-mono text-[11px] uppercase tracking-wider text-ink-muted">Lowest score kept 0.5</p>
            <p className="tnum mt-3 font-mono text-[44px] leading-none text-green-ink">{at(0.5).total_abs_error}<span className="ml-2 text-[14px] text-ink-muted">items wrong in all</span></p>
          </div>
          <div className="bg-background p-6">
            <p className="text-[13.5px] leading-relaxed text-ink-muted">
              On {at(0.4).photos} hand-counted photos the first setting over-counted clutter. Real photos moved the default from 0.4 to 0.5. On clean rendered photos 0.4 is still best, so it is a setting.
            </p>
          </div>
        </div>
      </div>
      <div className="mx-auto mt-10 grid max-w-[1200px] gap-5 px-4 pb-16 sm:grid-cols-2 sm:px-6 lg:grid-cols-4" aria-label="Real photos with counts">
        {rows.map((r) => (
          <figure key={r.key} className="overflow-hidden rounded-2xl border border-line bg-surface">
            <Photo src={`/img/real/overlay/${r.results[0].overlay}`} alt={`${r.pid} with ${r.results[0].count} items outlined and numbered`} aspect="4 / 3" fit="contain" />
            <figcaption className="flex items-end justify-between gap-3 border-t border-line p-4">
              <span className="font-mono text-[11.5px] leading-snug text-ink-muted">
                {r.pid} · {r.results[0].word}
                <br />
                {r.hand_count !== null ? `by eye ${r.hand_count}` : "counted by SAM 3.1"}
              </span>
              <span className="tnum font-mono text-[38px] leading-none text-green-ink">{r.results[0].count}</span>
            </figcaption>
          </figure>
        ))}
      </div>
    </section>
  );
}

/* ---------------------------------------------------- 3. counted on arrival */
function Arrival() {
  const d = video.detection;
  const marks = [
    { t: d.first_motion_s, label: "movement", tone: "text-ink-muted" },
    { t: d.detected_at_s, label: "alert 1", tone: "text-amber-ink" },
    ...video.frames.map((f, i) => ({ t: f.t, label: `view ${i + 1}: ${f.count}`, tone: "text-green-ink" })),
  ];
  return (
    <section id="arrival" className="border-b border-line">
      <div className="mx-auto max-w-[1200px] px-4 py-20 sm:px-6">
        <p className="kLabel">03 / The moment it arrives</p>
        <h2 className="mt-4 max-w-[20ch] text-balance text-[38px] font-bold leading-[1.04] tracking-[-0.02em] text-foreground sm:text-[52px]">
          The alert fires {d.detection_lag_s.toFixed(2)} seconds after the first movement.
        </h2>
        <div className="mt-12 grid gap-px overflow-hidden rounded-3xl border border-line bg-line md:grid-cols-[1fr_2fr_1fr]">
          <div className="flex flex-col justify-between bg-background p-7">
            <p className="font-mono text-[11px] uppercase tracking-wider text-ink-muted">Detector</p>
            <p className="tnum mt-6 font-mono text-[56px] leading-none text-foreground">{video.median_ms_per_frame}<span className="block text-[14px] text-ink-muted">ms a frame</span></p>
            <p className="mt-6 text-[13.5px] leading-relaxed text-ink-muted">Keeps up with a live camera on a laptop CPU. The slower count follows as a second alert.</p>
          </div>
          <div className="relative bg-background p-7">
            <p className="font-mono text-[11px] uppercase tracking-wider text-ink-muted">Timeline of the clip, seconds</p>
            <div className="relative mt-24 h-[200px]">
              <span className="absolute inset-x-0 top-1/2 h-px bg-line" aria-hidden="true" />
              {marks.map((m, i) => (
                <span key={i} className="absolute top-1/2 -translate-x-1/2" style={{ left: `${Math.min(96, (m.t / video.clip.seconds) * 100)}%` }}>
                  <span className={`block h-3 w-3 -translate-y-1/2 rounded-full border-2 border-current bg-background ${m.tone}`} />
                  <span className={`absolute whitespace-nowrap font-mono text-[11px] ${m.tone} ${["-top-9", "top-4", "top-16", "-top-[4.5rem]"][i % 4]}`}>{m.label}<br />{m.t.toFixed(2)} s</span>
                </span>
              ))}
            </div>
          </div>
          <div className="flex flex-col justify-between bg-background p-7">
            <p className="font-mono text-[11px] uppercase tracking-wider text-amber-ink">Result</p>
            <p className="tnum mt-6 font-mono text-[56px] leading-none text-amber-ink">{video.total}<span className="text-[22px] text-ink-muted"> / {video.billed}</span></p>
            <p className="mt-6 text-[13.5px] leading-relaxed text-ink-muted">Held for the owner, with the investigation and the supplier dispute drafted.</p>
          </div>
        </div>
      </div>
    </section>
  );
}

/* -------------------------------------------------------------- 4. run it */
function RunIt() {
  const lines: { cmd: string; out: string }[] = [
    { cmd: "pip install relayloom", out: "installs the package and the relayloom command" },
    { cmd: "relayloom models pull", out: "downloads Muse Glimmer and SAM 3.1 with your own token, once" },
    { cmd: "relayloom check --bill bill.pdf --photos dock/ --po po.json --agent", out: "exit 0 is clear to enter, exit 3 is held" },
    { cmd: "relayloom verify relayloom-out/receipts.jsonl", out: "chain verified with the network off, or BROKEN" },
  ];
  return (
    <section id="run" className="border-b border-line bg-raised">
      <div className="mx-auto max-w-[1200px] px-4 py-20 sm:px-6">
        <p className="kLabel">04 / Anyone can run it</p>
        <h2 className="mt-4 max-w-[22ch] text-balance text-[38px] font-bold leading-[1.04] tracking-[-0.02em] text-foreground sm:text-[52px]">
          Your photos. Your bill. Your machine.
        </h2>
        <div className="mt-10 divide-y divide-line overflow-hidden rounded-3xl border border-line bg-background">
          {lines.map((l, i) => (
            <div key={l.cmd} className="grid gap-3 p-5 md:grid-cols-[2.2rem_minmax(0,3fr)_minmax(0,2fr)] md:items-center md:gap-6 md:p-6">
              <span className="tnum font-mono text-[13px] text-ink-muted">{String(i + 1).padStart(2, "0")}</span>
              <CopyBlock command={l.cmd} />
              <p className="text-[13.5px] leading-snug text-ink-muted">{l.out}</p>
            </div>
          ))}
        </div>
        <p className="mt-4 text-[12.5px] text-ink-muted">
          Glimmer reads a bill in {fmtSeconds(glimmerSummary.min)} to {fmtSeconds(glimmerSummary.max)} on a laptop CPU. See the <Link to="/developers" className="underline underline-offset-4">Developers page</Link> for the policy file and the receipt format.
        </p>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------ 5. vision */
function Vision() {
  const beats = [
    { h: "A count at every door", p: "Each dock gets a camera and a counter. What arrives is counted the moment it arrives, and the bill meets that number before any money moves." },
    { h: "A receipt for every decision", p: "Every step is signed and chained, so anyone with the public key can check the whole story, offline, years later." },
    { h: "Open weights, your machine", p: "Muse Glimmer and SAM 3.1 run inside the business, even with the network off. No bill, photo or bank detail leaves the building." },
  ];
  return (
    <section id="vision" className="border-b border-line bg-raised">
      <div className="mx-auto max-w-[1200px] px-4 py-20 sm:px-6">
        <p className="kLabel">05 / The vision</p>
        <h2 className="mt-4 max-w-[22ch] text-balance text-[38px] font-bold leading-[1.04] tracking-[-0.02em] text-foreground sm:text-[52px]">
          A simple way to end paying for goods that never came.
        </h2>
        <p className="mt-5 max-w-[62ch] text-[16px] leading-relaxed text-ink-muted">
          The cases above ran for years because nobody counted at the door. One camera, one count and one signed receipt per bill is a small idea with a large reach.
          With persistence and real funding it becomes the standard check between every supplier and every payment.
        </p>
        <div className="mt-10 grid gap-px overflow-hidden rounded-3xl border border-line bg-line md:grid-cols-3">
          {beats.map((b) => (
            <div key={b.h} className="bg-background p-7">
              <h3 className="text-[18px] font-semibold text-foreground">{b.h}</h3>
              <p className="mt-3 text-[14px] leading-relaxed text-ink-muted">{b.p}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Closing() {
  return (
    <section>
      <div className="mx-auto max-w-[1200px] px-4 py-24 text-center sm:px-6">
        <p className="mx-auto max-w-[18ch] text-balance text-[44px] font-bold leading-[1.02] tracking-[-0.03em] text-foreground sm:text-[76px]">
          Pay for what arrived.
        </p>
        <p className="mt-5 text-[14px] text-ink-muted">Built by Sriharsan B S. One person, one laptop, open weights.</p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link to="/proof" className={btn}>See the proof</Link>
          {links.video ? <a href={links.video} target="_blank" rel="noreferrer" className={btnLine}>Watch the film</a> : null}
          <a href={links.repo} target="_blank" rel="noreferrer" className={btnLine}>Read the code</a>
        </div>
      </div>
    </section>
  );
}

export function Home() {
  return (
    <>
      <Hero />
      <Strip />
      <RealCases />
      <Looks />
      <Goods />
      <Arrival />
      <RunIt />
      <Vision />
      <Closing />
    </>
  );
}
