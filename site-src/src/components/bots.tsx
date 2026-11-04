import { useRef, useState } from "react";

/** The crew: five small agents. Press one to see its signature move, drag it around, or let them all run. */
const BODY = "var(--surface)";
const LINE = "var(--line)";

function Frame({ children, label }: { children: React.ReactNode; label: string }) {
  return (
    <svg viewBox="0 0 96 96" className="h-32 w-32" role="img" aria-label={label}>
      <ellipse cx="48" cy="88" rx="22" ry="3.5" fill="currentColor" opacity="0.12" />
      <g className="bot">{children}</g>
    </svg>
  );
}

function Face({ y = 34 }: { y?: number }) {
  return (
    <>
      <circle cx="40" cy={y} r="2.6" fill="var(--foreground)" />
      <circle cx="56" cy={y} r="2.6" fill="var(--foreground)" />
    </>
  );
}

export function Reader() {
  return (
    <Frame label="Reader reads the bill">
      <rect x="26" y="20" width="44" height="52" rx="12" fill={BODY} stroke={LINE} strokeWidth="2" />
      <Face />
      <rect x="34" y="44" width="28" height="22" rx="3" fill="var(--background)" stroke={LINE} />
      <path d="M38 50h20M38 55h14M38 60h18" stroke="var(--ink-muted)" strokeWidth="1.6" strokeLinecap="round" />
      <rect x="34" y="42" width="28" height="2.5" rx="1.2" fill="var(--green)" className="bot-scan" />
    </Frame>
  );
}

export function Counter() {
  return (
    <Frame label="Counter counts the goods">
      <rect x="26" y="20" width="44" height="52" rx="12" fill={BODY} stroke={LINE} strokeWidth="2" />
      <Face />
      {[0, 1, 2, 3, 4].map((i) => (
        <circle key={i} cx={34 + i * 7} cy="56" r="2.8" fill="var(--green)" className="bot-tick" style={{ animationDelay: `${i * 0.22}s` }} />
      ))}
      <path d="M36 66h24" stroke={LINE} strokeWidth="2" strokeLinecap="round" />
    </Frame>
  );
}

export function Matcher() {
  return (
    <Frame label="Matcher compares order, bill and goods">
      <rect x="26" y="20" width="44" height="52" rx="12" fill={BODY} stroke={LINE} strokeWidth="2" />
      <Face />
      <circle cx="36" cy="60" r="4" fill="var(--green)" />
      <circle cx="60" cy="60" r="4" fill="var(--amber)" />
      <circle cx="48" cy="49" r="4" fill="var(--foreground)" />
      <path d="M36 60 48 49 60 60 36 60" fill="none" stroke="var(--ink-muted)" strokeWidth="1.6" className="bot-link" />
    </Frame>
  );
}

export function Investigator() {
  return (
    <Frame label="Investigator follows the evidence">
      <rect x="26" y="20" width="44" height="52" rx="12" fill={BODY} stroke={LINE} strokeWidth="2" />
      <Face />
      <path d="M34 56h28M34 63h20" stroke="var(--ink-muted)" strokeWidth="1.6" strokeLinecap="round" />
      <g className="bot-sweep">
        <circle cx="46" cy="52" r="8" fill="var(--background)" fillOpacity="0.6" stroke="var(--foreground)" strokeWidth="2" />
        <path d="m52 58 7 8" stroke="var(--foreground)" strokeWidth="3" strokeLinecap="round" />
      </g>
    </Frame>
  );
}

export function Clerk() {
  return (
    <Frame label="Clerk enters the bill and signs the receipt">
      <rect x="26" y="26" width="44" height="46" rx="12" fill={BODY} stroke={LINE} strokeWidth="2" />
      <Face y={40} />
      <rect x="32" y="60" width="32" height="8" rx="2" fill="var(--background)" stroke={LINE} />
      <path d="M38 64h20" stroke="var(--green)" strokeWidth="2" strokeLinecap="round" className="bot-ink" />
      <g className="bot-stamp">
        <rect x="42" y="6" width="12" height="6" rx="2" fill="var(--foreground)" />
        <rect x="46" y="12" width="4" height="14" fill="var(--foreground)" />
        <rect x="40" y="24" width="16" height="5" rx="2" fill="var(--green)" />
      </g>
    </Frame>
  );
}

export const CREW = [
  { name: "Reader", Bot: Reader, line: "Reads every bill into a strict form.", shout: "Page one, line by line!" },
  { name: "Counter", Bot: Counter, line: "Counts the goods in the photo.", shout: "Twenty four, and every one numbered!" },
  { name: "Matcher", Bot: Matcher, line: "Sets order, bill and goods side by side.", shout: "Order, bill, goods. Do they agree?" },
  { name: "Investigator", Bot: Investigator, line: "Follows the evidence and cites every claim.", shout: "Show me the record behind that." },
  { name: "Clerk", Bot: Clerk, line: "Enters the bill and signs the receipt.", shout: "Signed. Nobody changes this quietly." },
];

function CrewMember({ i, running, name, Bot, line, shout }: { i: number; running: boolean; name: string; Bot: () => React.ReactElement; line: string; shout: string }) {
  const [act, setAct] = useState(false);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const [drag, setDrag] = useState(false);
  const start = useRef<{ x: number; y: number } | null>(null);
  const moved = useRef(false);

  const play = () => {
    setAct(true);
    window.setTimeout(() => setAct(false), 2200);
  };
  return (
    <li className="relative flex flex-col items-start">
      {act && (
        <p className="crew-shout absolute -top-9 left-2 z-10 whitespace-nowrap rounded-full border border-line bg-background px-3 py-1.5 text-[12.5px] text-foreground shadow-lg">{shout}</p>
      )}
      <button
        type="button"
        aria-label={`${name}: press for its signature move, or drag it`}
        className={`touch-none select-none ${running ? "crew-run" : ""} ${act ? "crew-act" : ""} ${drag ? "cursor-grabbing" : "cursor-grab"}`}
        style={{ transform: `translate(${pos.x}px, ${pos.y}px)`, transition: drag ? "none" : "transform 520ms cubic-bezier(0.3, 1.5, 0.5, 1)", animationDelay: `${i * 140}ms` }}
        onPointerDown={(e) => { (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId); start.current = { x: e.clientX - pos.x, y: e.clientY - pos.y }; moved.current = false; setDrag(true); }}
        onPointerMove={(e) => { if (!start.current) return; const nx = e.clientX - start.current.x, ny = e.clientY - start.current.y; if (Math.abs(nx) + Math.abs(ny) > 6) moved.current = true; setPos({ x: nx, y: ny }); }}
        onPointerUp={() => { start.current = null; setDrag(false); setPos({ x: 0, y: 0 }); if (!moved.current) play(); }}
        onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); play(); } }}
      >
        <Bot />
      </button>
      <p className="mt-2 text-[16px] font-semibold text-foreground">{name}</p>
      <p className="mt-1 max-w-[22ch] text-[13.5px] leading-snug text-ink-muted">{line}</p>
    </li>
  );
}

export function Crew() {
  const [running, setRunning] = useState(false);
  const [round, setRound] = useState(0);
  const run = () => {
    setRunning(false);
    window.setTimeout(() => { setRound((n) => n + 1); setRunning(true); }, 30);
    window.setTimeout(() => setRunning(false), 4200);
  };
  return (
    <div id="crew" className="scroll-mt-24 text-ink-muted">
      <div className="flex flex-wrap items-center gap-3">
        <button type="button" onClick={run} className="inline-flex h-10 items-center rounded-full bg-foreground px-5 text-[13px] font-medium text-background">Let them run</button>
        <span className="text-[13.5px]">Press a bot for its signature move. Drag one anywhere and let go.</span>
      </div>
      <ul key={round} className="mt-12 grid grid-cols-2 gap-x-4 gap-y-12 sm:grid-cols-3 lg:grid-cols-5">
        {CREW.map((c, i) => <CrewMember key={c.name} i={i} running={running} {...c} />)}
      </ul>
    </div>
  );
}
