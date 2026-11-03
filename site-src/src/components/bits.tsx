import { useState, type ReactNode } from "react";

export function RunLabel({ label }: { label: string }) {
  return <span className="kLabel">{label}</span>;
}

type Tone = "green" | "amber" | "red" | "muted";

export function Pill({ tone, children }: { tone: Tone; children: ReactNode }) {
  const color =
    tone === "green" ? "text-green-ink border-green/30 bg-green/10"
    : tone === "amber" ? "text-amber-ink border-amber/30 bg-amber/10"
    : tone === "red" ? "text-red-ink border-red/30 bg-red/10"
    : "text-ink-muted border-line bg-raised";
  const dot = tone === "green" ? "bg-green" : tone === "amber" ? "bg-amber" : tone === "red" ? "bg-red" : "bg-ink-muted";
  return (
    <span className={`pill ${color}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} aria-hidden="true" />
      {children}
    </span>
  );
}

export function StepPill({ name, status, time }: { name: string; status: "done" | "held" | "skipped" | "waiting"; time: string }) {
  const tone: Tone = status === "done" ? "green" : status === "held" ? "amber" : "muted";
  const label = status === "held" ? `${name}, held` : status === "skipped" ? `${name}, skipped` : name;
  return (
    <div className="flex flex-col items-start gap-1">
      <Pill tone={tone}>{label}</Pill>
      <span className="tnum font-mono text-[10.5px] text-ink-muted">{time || " "}</span>
    </div>
  );
}

export function SectionHead({ index, title, note }: { index: string; title: string; note?: string }) {
  return (
    <div className="mb-8 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
      <div>
        <p className="kLabel">{index}</p>
        <h2 className="mt-2 text-2xl font-semibold tracking-tight text-foreground sm:text-[26px]">{title}</h2>
      </div>
      {note && <p className="max-w-md text-[13.5px] leading-relaxed text-ink-muted">{note}</p>}
    </div>
  );
}

/** A real delivery photo or SAM 3.1 overlay. Draws a quiet empty state if the file is missing. */
export function Photo({ src, alt, aspect = "4 / 3" }: { src: string | null; alt: string; aspect?: string }) {
  if (!src) {
    return <div className="rounded-lg border border-dashed border-line bg-raised/60" style={{ aspectRatio: aspect }} role="img" aria-label={alt} />;
  }
  return (
    <div className="overflow-hidden rounded-lg border border-line bg-raised" style={{ aspectRatio: aspect }}>
      <img src={src} alt={alt} loading="lazy" className="h-full w-full object-cover" />
    </div>
  );
}

/** A command with a copy button. */
export function CopyBlock({ command }: { command: string }) {
  const [done, setDone] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(command);
      setDone(true);
      window.setTimeout(() => setDone(false), 1600);
    } catch {
      /* clipboard unavailable, the text can still be selected */
    }
  };
  return (
    <div className="flex items-start gap-2 rounded-lg border border-line bg-raised">
      <pre className="min-w-0 flex-1 overflow-x-auto px-3.5 py-3 font-mono text-[12.5px] leading-relaxed text-foreground">{command}</pre>
      <button
        onClick={copy}
        aria-label={`Copy: ${command}`}
        className="m-1.5 h-9 shrink-0 rounded-md border border-line px-3 font-mono text-[11px] text-ink-muted transition-colors duration-150 hover:bg-surface hover:text-foreground"
      >
        {done ? "Copied" : "Copy"}
      </button>
    </div>
  );
}
