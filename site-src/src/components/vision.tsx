import { useEffect, useState } from "react";
import { Crew } from "@/components/bots";

const still = () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Dots light up one by one while a number counts, then it starts again. */
function CountLoop() {
  const total = 24;
  const [n, setN] = useState(still() ? total : 0);
  useEffect(() => {
    if (still()) return;
    const id = window.setInterval(() => setN((v) => (v >= total + 8 ? 0 : v + 1)), 140);
    return () => window.clearInterval(id);
  }, []);
  const shown = Math.min(n, total);
  return (
    <div className="flex items-center gap-6" role="img" aria-label="Goods counted one by one at the door">
      <div className="grid grid-cols-6 gap-2">
        {Array.from({ length: total }, (_, i) => (
          <span key={i} className={`h-4 w-4 rounded-[5px] border transition-colors duration-200 ${i < shown ? "border-green bg-green/70" : "border-line bg-raised"}`} />
        ))}
      </div>
      <p className="tnum font-mono text-[56px] leading-none text-green-ink">{shown}</p>
    </div>
  );
}

/** Signed blocks bob in a row, linked by a moving line. */
function ChainLoop() {
  return (
    <svg viewBox="0 0 360 110" className="w-full max-w-[420px]" role="img" aria-label="Signed receipts linked in a chain">
      <line x1="60" y1="55" x2="300" y2="55" stroke="var(--green)" strokeWidth="2" className="flow-line" />
      {[0, 1, 2, 3].map((i) => (
        <g key={i} className="chain-block" style={{ animationDelay: `${i * 0.3}s` }}>
          <rect x={20 + i * 88} y="30" width="64" height="50" rx="10" fill="var(--surface)" stroke="var(--line)" strokeWidth="2" />
          <path d={`M${36 + i * 88} 48h32M${36 + i * 88} 56h24M${36 + i * 88} 64h30`} stroke="var(--ink-muted)" strokeWidth="2" strokeLinecap="round" />
          <circle cx={72 + i * 88} cy="36" r="5" fill="var(--green)" />
        </g>
      ))}
    </svg>
  );
}

/** Data flows inside the wall and stops at the gateway. */
function WallLoop() {
  return (
    <svg viewBox="0 0 360 110" className="w-full max-w-[420px]" role="img" aria-label="Data moves inside the company wall and stops at the gateway">
      <rect x="14" y="14" width="250" height="82" rx="16" fill="var(--surface)" stroke="var(--line)" strokeWidth="2" />
      <line x1="40" y1="42" x2="230" y2="42" stroke="var(--green)" strokeWidth="2" className="flow-line" />
      <line x1="40" y1="70" x2="230" y2="70" stroke="var(--green)" strokeWidth="2" className="flow-line" style={{ animationDelay: "0.4s" }} />
      <rect x="276" y="34" width="70" height="42" rx="10" fill="var(--background)" stroke="var(--amber)" strokeWidth="2" />
      <text x="311" y="59" textAnchor="middle" fontSize="11" fontFamily="JetBrains Mono, monospace" fill="var(--amber-ink, var(--amber))">GATEWAY</text>
      <circle cx="264" cy="55" r="6" fill="var(--amber)" className="ring-pulse" />
      <circle cx="264" cy="55" r="4" fill="var(--amber)" />
    </svg>
  );
}

const ROWS = [
  { n: "01", h: "A counter at every door.", p: "What arrives is counted the moment it arrives, and the bill meets that number before any money moves.", Visual: CountLoop },
  { n: "02", h: "A receipt for every decision.", p: "Each step is signed and chained. Anyone with the public key checks the whole story, offline, years later.", Visual: ChainLoop },
  { n: "03", h: "Your machine, your data.", p: "Muse Glimmer and SAM 3.1 run inside the business, even with the network off. No bill, photo or bank detail leaves the building.", Visual: WallLoop },
];

export function Vision() {
  return (
    <section id="vision" className="border-b border-line">
      <div className="mx-auto max-w-[1200px] px-6 py-24 sm:px-10 lg:px-14">
        <p className="kLabel">05 / The vision</p>
        <h2 className="mt-6 max-w-[17ch] text-balance text-[44px] font-bold leading-[1.02] tracking-[-0.03em] text-foreground sm:text-[72px]">
          One quiet <span className="serif-italic text-green-ink text-[1.12em]">mastermind</span> between every supplier and every payment.
        </h2>
        <p className="mt-8 max-w-[56ch] text-[19px] leading-[1.6] text-ink-muted">
          The cases above ran for years because nobody counted at the door. Relayloom counts at the door, writes down what it saw, and signs it. With persistence and real funding,
          that one simple check becomes the standard at every dock.
        </p>

        <div className="mt-16 divide-y divide-line border-y border-line">
          {ROWS.map(({ n, h, p, Visual }) => (
            <div key={n} className="grid items-center gap-8 py-12 md:grid-cols-[4rem_minmax(0,1fr)_minmax(0,1fr)]">
              <span className="font-mono text-[14px] text-ink-muted">{n}</span>
              <div>
                <h3 className="text-[28px] font-semibold leading-tight tracking-[-0.02em] text-foreground sm:text-[34px]">{h}</h3>
                <p className="mt-3 max-w-[40ch] text-[17px] leading-relaxed text-ink-muted">{p}</p>
              </div>
              <div className="flex justify-start md:justify-end"><Visual /></div>
            </div>
          ))}
        </div>

        <p className="kLabel mt-20">The crew</p>
        <h3 className="mt-3 max-w-[22ch] text-[30px] font-semibold leading-tight tracking-[-0.02em] text-foreground sm:text-[38px]">Five agents, each with one job.</h3>
        <div className="mt-8"><Crew /></div>
      </div>
    </section>
  );
}
