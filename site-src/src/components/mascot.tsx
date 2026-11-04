import { useEffect, useState } from "react";

type Props = {
  /** What Loom says when it arrives. */
  message: string;
  /** The button: it either scrolls to an element id or does something. */
  cta: { label: string; target?: string; click?: () => void };
  /** A second line Loom says after a hop, to point the visitor onward. */
  nudges?: string[];
  storageKey: string;
};

function Cloud({ className, style }: { className?: string; style?: React.CSSProperties }) {
  return (
    <svg viewBox="0 0 96 40" className={`cloud h-8 w-20 ${className ?? ""}`} style={style} aria-hidden="true">
      <path d="M22 34a12 12 0 0 1 1-24 16 16 0 0 1 30-3 14 14 0 0 1 19 13 10 10 0 0 1 2 14z" fill="currentColor" />
    </svg>
  );
}

/** Loom runs in from the left under drifting clouds, stops in the corner, waves, and invites the visitor onward. A hop moves it to its next line. */
export function Mascot({ message, cta, nudges = [], storageKey }: Props) {
  const [gone, setGone] = useState(false);
  const [arrived, setArrived] = useState(false);
  const [hop, setHop] = useState(0);

  useEffect(() => {
    try { if (sessionStorage.getItem(storageKey) === "1") setGone(true); } catch { /* storage unavailable */ }
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const id = window.setTimeout(() => setArrived(true), reduce ? 0 : 6200);
    return () => window.clearTimeout(id);
  }, [storageKey]);

  if (gone) return null;
  const close = () => {
    setGone(true);
    try { sessionStorage.setItem(storageKey, "1"); } catch { /* ignore */ }
  };
  const act = () => {
    if (cta.target) document.getElementById(cta.target)?.scrollIntoView({ behavior: "smooth", block: "start" });
    cta.click?.();
    if (cta.target) close();
  };
  const line = hop > 0 && nudges.length ? nudges[(hop - 1) % nudges.length] : message;

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-3 z-40 h-28" aria-live="polite">
      <div className="absolute inset-0 overflow-hidden" aria-hidden="true">
      <Cloud className="!top-1" style={{ animationDuration: "42s" }} />
      <Cloud className="!top-9 scale-75" style={{ animationDuration: "55s", animationDelay: "-20s" }} />
      <Cloud className="!top-3 scale-90" style={{ animationDuration: "48s", animationDelay: "-33s" }} />
      </div>
      <div className={`loom-runner pointer-events-auto absolute bottom-0 ${arrived ? "loom-arrived" : ""}`}>
        {arrived && (
          <div className="loom-bubble absolute -top-[5.4rem] right-0 w-[230px] rounded-2xl border border-line bg-background p-3 text-[13px] leading-snug text-foreground shadow-xl" key={line}>
            <button type="button" onClick={close} aria-label="Close" className="absolute right-2 top-1 text-[15px] text-ink-muted hover:text-foreground">×</button>
            <p className="pr-4"><span className="font-semibold">I'm Loom.</span> {line}</p>
            <button type="button" onClick={act} className="mt-2 inline-flex h-8 items-center rounded-full bg-foreground px-3 text-[12px] font-medium text-background">{cta.label}</button>
          </div>
        )}
        <button type="button" onClick={() => setHop((n) => n + 1)} aria-label="Loom, the guide. Press to make it hop and hear the next tip" className="block">
          <svg key={hop} viewBox="0 0 80 80" className={`h-20 w-20 ${hop ? "loom-hop" : ""}`} role="img" aria-hidden="true">
            <ellipse cx="40" cy="74" rx="16" ry="3" fill="currentColor" opacity="0.15" />
            <g className={arrived ? "bot" : "loom-run"}>
              <rect x="20" y="14" width="40" height="38" rx="14" fill="var(--surface)" stroke="var(--green)" strokeWidth="2.5" />
              <circle cx="32" cy="32" r="3" fill="var(--foreground)" />
              <circle cx="48" cy="32" r="3" fill="var(--foreground)" />
              <path d="M33 41q7 6 14 0" fill="none" stroke="var(--foreground)" strokeWidth="2" strokeLinecap="round" />
              <path d="M40 14V6" stroke="var(--green)" strokeWidth="2.5" strokeLinecap="round" />
              <circle cx="40" cy="5" r="3" fill="var(--green)" className="bot-tick" />
              <rect x="26" y="52" width="6" height="14" rx="3" fill="var(--foreground)" className="loom-leg" />
              <rect x="48" y="52" width="6" height="14" rx="3" fill="var(--foreground)" className="loom-leg loom-leg-b" />
              <path d="M60 30l9-8" stroke="var(--foreground)" strokeWidth="3" strokeLinecap="round" className={arrived ? "loom-wave" : ""} />
            </g>
          </svg>
        </button>
      </div>
    </div>
  );
}
