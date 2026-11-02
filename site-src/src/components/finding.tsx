import type { Statement } from "@/data/site";
import { RunLabel } from "./bits";

export const citeId = (cite: string) => "cite-" + cite.toLowerCase().replace(/[^a-z0-9]+/g, "-");

/** The Investigator's finding. Every statement carries the ids of the records it rests on. */
export function FindingCard({
  title,
  statements,
  label,
  onCite,
}: {
  title: string;
  statements: Statement[];
  label: string;
  onCite?: (cite: string) => void;
}) {
  return (
    <div className="rounded-xl border border-line bg-surface">
      <div className="flex items-center justify-between border-b border-line px-5 py-3">
        <span className="kLabel">Investigator finding</span>
        <RunLabel label={label} />
      </div>
      <div className="px-5 py-4">
        <h3 className="text-[15.5px] font-medium text-foreground">{title}</h3>
        <ul className="mt-4 space-y-3">
          {statements.map((s, i) => (
            <li key={i} className="flex flex-col gap-1.5">
              <span className="flex items-start gap-2.5">
                <span className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-ink-muted/60" aria-hidden="true" />
                <span className="text-[13.5px] leading-relaxed text-foreground">{s.text}</span>
              </span>
              <span className="ml-4 flex flex-wrap gap-1.5">
                {s.cites.map((c) =>
                  onCite ? (
                    <button
                      key={c}
                      onClick={() => onCite(c)}
                      className="tnum pill bg-raised text-[10.5px] text-foreground transition-colors duration-150 hover:border-line-strong"
                    >
                      {c}
                    </button>
                  ) : (
                    <span key={c} className="tnum pill bg-raised text-[10.5px] text-foreground">{c}</span>
                  ),
                )}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
