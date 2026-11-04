import { useEffect, useState } from "react";
import { Github, Menu, Moon, Play, Sun, X } from "lucide-react";
import { Link, useLocation } from "@/lib/router";
import { footerNote, links } from "@/data/site";

const NAV = [
  { label: "The agent", to: "/", hash: "#agent" },
  { label: "The goods", to: "/", hash: "#goods" },
  { label: "Run it", to: "/", hash: "#run" },
  { label: "Try it", to: "/try", hash: "" },
  { label: "Proof", to: "/proof", hash: "" },
  { label: "Demo", to: "/demo", hash: "" },
  { label: "Developers", to: "/developers", hash: "" },
];

const readTheme = (): "dark" | "light" => {
  try {
    return localStorage.getItem("relayloom-theme") === "light" ? "light" : "dark";
  } catch {
    return "dark";
  }
};

function ThemeToggle() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  useEffect(() => setTheme(readTheme()), []);
  const toggle = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    try {
      localStorage.setItem("relayloom-theme", next);
    } catch {
      /* storage unavailable, the theme holds for this visit */
    }
    document.documentElement.classList.toggle("light", next === "light");
  };
  return (
    <button
      onClick={toggle}
      aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
      className="inline-flex h-11 w-11 items-center justify-center rounded-md border border-line text-ink-muted transition-colors duration-150 hover:bg-raised hover:text-foreground"
    >
      {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </button>
  );
}

export function Wordmark() {
  return (
    <Link to="/" className="flex items-center gap-2.5" aria-label="Relayloom home">
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
        <rect x="1" y="1" width="9" height="9" rx="2" stroke="var(--foreground)" strokeWidth="1.5" />
        <rect x="12" y="1" width="9" height="9" rx="2" stroke="var(--green)" strokeWidth="1.5" />
        <rect x="1" y="12" width="9" height="9" rx="2" stroke="var(--green)" strokeWidth="1.5" />
        <rect x="12" y="12" width="9" height="9" rx="2" stroke="var(--amber)" strokeWidth="1.5" strokeDasharray="2.5 2.5" />
      </svg>
      <span className="text-[15px] font-semibold tracking-tight text-foreground">Relayloom</span>
    </Link>
  );
}

const btnGhost =
  "inline-flex h-11 items-center gap-2 rounded-md border border-line px-3.5 text-[13px] font-medium text-foreground transition-colors duration-150 hover:bg-raised";
const btnSolid =
  "inline-flex h-11 items-center gap-2 rounded-md bg-foreground px-3.5 text-[13px] font-medium text-background transition-opacity duration-150 hover:opacity-90";

function Actions({ full = false }: { full?: boolean }) {
  const grow = full ? " flex-1 justify-center" : "";
  return (
    <>
      <a href={links.repo} target="_blank" rel="noreferrer" className={btnGhost + grow}>
        <Github className="h-4 w-4" />
        View code
      </a>
      {links.video && (
        <a href={links.video} target="_blank" rel="noreferrer" className={btnSolid + grow}>
          <Play className="h-4 w-4" />
          Watch demo
        </a>
      )}
    </>
  );
}

export function SiteHeader() {
  const [open, setOpen] = useState(false);
  const loc = useLocation();
  useEffect(() => setOpen(false), [loc.path, loc.hash]);
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-background/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-[1200px] items-center gap-6 px-4 sm:px-6">
        <Wordmark />
        <nav className="hidden items-center gap-1 md:flex" aria-label="Primary">
          {NAV.map((n) => {
            const active = !n.hash && loc.path === n.to;
            return (
              <Link
                key={n.label}
                to={n.to}
                hash={n.hash}
                className={`flex h-11 items-center rounded-md px-3 font-mono text-[12px] uppercase tracking-[0.12em] transition-colors duration-150 ${
                  active ? "text-foreground" : "text-ink-muted hover:text-foreground"
                }`}
              >
                {n.label}
              </Link>
            );
          })}
        </nav>
        <div className="ml-auto hidden items-center gap-2 md:flex">
          <ThemeToggle />
          <Actions />
        </div>
        <button
          className="ml-auto inline-flex h-11 w-11 items-center justify-center rounded-md border border-line text-foreground md:hidden"
          aria-expanded={open}
          aria-label={open ? "Close menu" : "Open menu"}
          onClick={() => setOpen((v) => !v)}
        >
          {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
        </button>
      </div>
      {open && (
        <div className="border-t border-line bg-background px-4 py-3 md:hidden">
          <nav className="flex flex-col" aria-label="Primary mobile">
            {NAV.map((n) => (
              <Link
                key={n.label}
                to={n.to}
                hash={n.hash}
                className="flex h-11 items-center rounded-md px-3 font-mono text-[12px] uppercase tracking-[0.12em] text-ink-muted hover:bg-raised hover:text-foreground"
              >
                {n.label}
              </Link>
            ))}
          </nav>
          <div className="mt-2 flex items-center gap-2 border-t border-line pt-3">
            <ThemeToggle />
            <Actions full />
          </div>
        </div>
      )}
    </header>
  );
}

export function SiteFooter() {
  const item = "transition-colors duration-150 hover:text-foreground";
  return (
    <footer className="border-t border-line">
      <div className="mx-auto flex max-w-[1200px] flex-col gap-6 px-4 py-10 sm:px-6 md:flex-row md:items-end md:justify-between">
        <div className="max-w-sm">
          <Wordmark />
          <p className="mt-3 text-[13px] leading-relaxed text-ink-muted">{footerNote}</p>
        </div>
        <nav className="flex flex-wrap items-center gap-x-6 gap-y-2 font-mono text-[12px] uppercase tracking-[0.12em] text-ink-muted" aria-label="Footer">
          <Link to="/" hash="#how" className={item}>How it works</Link>
          <Link to="/" hash="#cases" className={item}>Cases</Link>
          <Link to="/proof" className={item}>Proof</Link>
          <Link to="/demo" className={item}>Demo</Link>
          <Link to="/developers" className={item}>Developers</Link>
          <a href={links.repo} target="_blank" rel="noreferrer" className={item}>Code</a>
        </nav>
      </div>
    </footer>
  );
}
