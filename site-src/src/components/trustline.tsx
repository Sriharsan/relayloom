import { Link } from "@/lib/router";

const STEPS = [
  { n: "1", h: "The photo is attached", p: "The goods are photographed at the door and counted, and the photo's fingerprint goes into the receipt." },
  { n: "2", h: "Bill side and goods side agree", p: "The bill, the order and the count are set against each other. Any gap stops here, with the reason in plain words." },
  { n: "3", h: "The receipt is signed and verified", p: "Every step is signed and chained. Anyone can verify it offline, on any machine." },
  { n: "4", h: "The receipt goes to payment", p: "Payment is released against a verified receipt with its photo, and not before." },
];

/** The core idea in one place. */
export function TrustLine() {
  return (
    <section id="trust" className="border-b border-line">
      <div className="mx-auto max-w-[1200px] px-6 py-20 sm:px-10 lg:px-14">
        <p className="kLabel">The idea</p>
        <h2 className="mt-5 max-w-[20ch] text-balance text-[40px] font-bold leading-[1.02] tracking-[-0.03em] text-foreground sm:text-[68px]">
          No photo, no receipt, no proof. <span className="text-green-ink">No payment.</span>
        </h2>
        <p className="mt-6 max-w-[58ch] text-[19px] leading-relaxed text-ink-muted">
          A bill is paid only when the photo, the receipt and the verification stand together. That is trust, and that is Relayloom.
        </p>
        <ol className="relative mt-14 grid gap-px overflow-hidden rounded-3xl border border-line bg-line md:grid-cols-4">
          {STEPS.map((s) => (
            <li key={s.n} className="bg-background p-7">
              <p className="tnum font-mono text-[44px] leading-none text-green-ink">{s.n}</p>
              <h3 className="mt-4 text-[18px] font-semibold leading-snug text-foreground">{s.h}</h3>
              <p className="mt-2 text-[14px] leading-relaxed text-ink-muted">{s.p}</p>
            </li>
          ))}
        </ol>
        <svg viewBox="0 0 1000 24" className="mt-0 hidden h-6 w-full md:block" aria-hidden="true" preserveAspectRatio="none">
          <line x1="20" y1="12" x2="980" y2="12" stroke="var(--green)" strokeWidth="2" className="flow-line" />
        </svg>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link to="/try" className="inline-flex h-12 items-center rounded-full bg-foreground px-6 text-sm font-medium text-background transition-opacity duration-150 hover:opacity-90">Try it with your bill</Link>
          <Link to="/proof" hash="#verifier" className="inline-flex h-12 items-center rounded-full border border-line px-6 text-sm font-medium text-foreground transition-colors duration-150 hover:bg-raised">Verify a receipt</Link>
        </div>
      </div>
    </section>
  );
}
