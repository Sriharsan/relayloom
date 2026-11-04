import { ArrowUpRight } from "lucide-react";
import { cases } from "@/data/site";

const TONE: Record<string, string> = {
  convicted: "text-red-ink border-red/40",
  substantiated: "text-red-ink border-red/40",
  alleged: "text-amber-ink border-amber/50",
  "audit finding": "text-amber-ink border-amber/50",
  enforcement: "text-ink-muted border-line",
  analysis: "text-ink-muted border-line",
};

/** Real cases from courts, audits and news, each read at its source. */
export function RealCases({ id = "cases" }: { id?: string }) {
  return (
    <section id={id} className="border-b border-line">
      <div className="mx-auto max-w-[1200px] px-4 pt-16 sm:px-6">
        <p className="kLabel">Real cases</p>
        <div className="mt-3 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <h2 className="max-w-[20ch] text-balance text-[34px] font-bold leading-[1.05] tracking-[-0.02em] text-foreground sm:text-[46px]">
            Paying for goods that did not arrive happens.
          </h2>
          <p className="max-w-[44ch] text-[14px] leading-relaxed text-ink-muted">
            Real cases from courts, audits and news, each linked to its source. Where a source calls a case an allegation, the card says so.
          </p>
        </div>
      </div>
      <div className="mt-8 flex snap-x gap-4 overflow-x-auto px-4 pb-12 sm:px-6 [scrollbar-width:thin]" tabIndex={0} aria-label="Real cases">
        {cases.map((c) => (
          <a
            key={c.id}
            href={c.url}
            target="_blank"
            rel="noreferrer noopener"
            className="group flex w-[310px] max-w-[84vw] shrink-0 snap-start flex-col justify-between rounded-2xl border border-line bg-surface p-5 transition-colors duration-150 hover:bg-raised"
          >
            <div>
              <span className={`inline-block rounded-full border px-2.5 py-0.5 font-mono text-[10.5px] uppercase tracking-wider ${TONE[c.status] ?? "text-ink-muted border-line"}`}>{c.status}</span>
              <p className="tnum mt-4 font-mono text-[34px] leading-none text-foreground">{c.figure}</p>
              <p className="mt-1 text-[12.5px] text-ink-muted">{c.short}</p>
              <h3 className="mt-4 text-[15.5px] font-semibold leading-snug text-foreground">{c.title}</h3>
              <p className="mt-2 text-[13px] leading-relaxed text-ink-muted">{c.text}</p>
            </div>
            <p className="mt-5 flex items-center justify-between gap-2 border-t border-line pt-3 font-mono text-[11px] text-ink-muted">
              <span>{c.place}. {c.source}, {c.date}</span>
              <ArrowUpRight className="h-4 w-4 shrink-0 text-foreground transition-transform duration-150 group-hover:-translate-y-0.5 group-hover:translate-x-0.5" aria-hidden="true" />
            </p>
          </a>
        ))}
      </div>
    </section>
  );
}
