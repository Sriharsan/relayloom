/** The crew: five small agents, each with its own signature move, looping while the page is open. */
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
  { name: "Reader", Bot: Reader, line: "Reads every bill into a strict form." },
  { name: "Counter", Bot: Counter, line: "Counts the goods in the photo." },
  { name: "Matcher", Bot: Matcher, line: "Sets order, bill and goods side by side." },
  { name: "Investigator", Bot: Investigator, line: "Follows the evidence and cites every claim." },
  { name: "Clerk", Bot: Clerk, line: "Enters the bill and signs the receipt." },
];

export function Crew() {
  return (
    <ul className="grid grid-cols-2 gap-x-4 gap-y-8 text-ink-muted sm:grid-cols-3 lg:grid-cols-5">
      {CREW.map(({ name, Bot, line }) => (
        <li key={name} className="flex flex-col items-start">
          <Bot />
          <p className="mt-2 text-[16px] font-semibold text-foreground">{name}</p>
          <p className="mt-1 max-w-[22ch] text-[13.5px] leading-snug">{line}</p>
        </li>
      ))}
    </ul>
  );
}
