import { useEffect, useState } from "react";
import { offlineRun } from "@/data/site";

const reduced = () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const JOURNEY = [
  { h: "The order", p: "The order fixes what should arrive and at what price." },
  { h: "Loaded", p: "The supplier loads the goods and sends the bill." },
  { h: "On the road", p: "Nobody checks anything between the yard and the door." },
  { h: "Photo and count at the door", p: "The goods are photographed and counted, damage included." },
  { h: "The signed receipt", p: "Bill, order and goods agree, or the gap is named. The receipt is signed." },
  { h: "Payment", p: "Cash at the door against the receipt, or online once the photo and the receipt are shared." },
];

/** The whole journey, from order to payment. The steps light up one after another. */
export function FlowStory() {
  const [on, setOn] = useState(reduced() ? JOURNEY.length - 1 : 0);
  useEffect(() => {
    if (reduced()) return;
    const id = window.setInterval(() => setOn((v) => (v + 1) % (JOURNEY.length + 2)), 1500);
    return () => window.clearInterval(id);
  }, []);
  const shown = Math.min(on, JOURNEY.length - 1);
  return (
    <section id="flow" className="border-b border-line">
      <div className="mx-auto max-w-[1200px] px-6 py-20 sm:px-10 lg:px-14">
        <p className="kLabel">The whole story</p>
        <h2 className="mt-5 max-w-[22ch] text-balance text-[38px] font-bold leading-[1.04] tracking-[-0.03em] text-foreground sm:text-[60px]">From the order to the payment, nothing is taken on trust.</h2>
        <div className="relative mt-14">
          <div className="absolute left-0 right-0 top-[22px] hidden h-0.5 bg-line lg:block" aria-hidden="true" />
          <div className="absolute left-0 top-[22px] hidden h-0.5 bg-green transition-[width] duration-700 lg:block" style={{ width: `${(shown / (JOURNEY.length - 1)) * 100}%` }} aria-hidden="true" />
          <ol className="relative grid gap-8 sm:grid-cols-2 lg:grid-cols-6 lg:gap-4">
            {JOURNEY.map((s, i) => (
              <li key={s.h} className={`transition-opacity duration-500 ${i <= shown ? "opacity-100" : "opacity-40"}`}>
                <span className={`flex h-11 w-11 items-center justify-center rounded-full border-2 font-mono text-[15px] transition-colors duration-500 ${i <= shown ? "border-green bg-green text-background" : "border-line bg-background text-ink-muted"} ${i === shown ? "ring-4 ring-green/25" : ""}`}>{i + 1}</span>
                <h3 className="mt-4 text-[17px] font-semibold leading-snug text-foreground">{s.h}</h3>
                <p className="mt-1.5 text-[13.5px] leading-relaxed text-ink-muted">{s.p}</p>
              </li>
            ))}
          </ol>
        </div>
        <p className="mt-10 max-w-[64ch] text-[17px] leading-relaxed text-ink-muted">
          Without the door step, the bill is paid on the supplier's word. With it, the photo, the count and the receipt travel with the payment.
        </p>
      </div>
    </section>
  );
}

const inr = (n: number) => (n >= 10000000 ? `${(n / 10000000).toFixed(2)} crore` : n >= 100000 ? `${(n / 100000).toFixed(2)} lakh` : n.toLocaleString("en-IN"));

/** Small gaps, repeated. An illustration with the vendor's own numbers, not a measured figure. */
export function SmallGaps() {
  const [per, setPer] = useState(1000);
  const gap = 25;
  const year = gap * per * 365;
  return (
    <section id="small" className="border-b border-line bg-raised">
      <div className="mx-auto grid max-w-[1200px] gap-12 px-6 py-20 sm:px-10 lg:grid-cols-2 lg:items-center lg:px-14">
        <div>
          <p className="kLabel">Not only for bulk orders</p>
          <h2 className="mt-5 max-w-[16ch] text-balance text-[38px] font-bold leading-[1.04] tracking-[-0.03em] text-foreground sm:text-[56px]">A small gap, repeated, is a large loss.</h2>
          <p className="mt-6 max-w-[48ch] text-[17px] leading-relaxed text-ink-muted">
            A street vendor buys oranges from a supplier and pays for a hundred rupees worth. Only seventy five rupees worth reaches the stall. The other twenty five rupees were paid for goods that never came, and the supplier keeps them.
            Counted across a city and a year, it is a different level of money, and of tax that never gets paid. A photo and a receipt at the door close it.
          </p>
        </div>
        <div className="rounded-3xl border border-line bg-background p-6 sm:p-8">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="font-mono text-[11px] uppercase tracking-wider text-ink-muted">Paid for</p>
              <p className="tnum font-mono text-[44px] leading-none text-foreground">Rs 100</p>
              <div className="mt-3 h-3 rounded bg-green/80" />
            </div>
            <div>
              <p className="font-mono text-[11px] uppercase tracking-wider text-ink-muted">Reached the stall</p>
              <p className="tnum font-mono text-[44px] leading-none text-amber-ink">Rs 75</p>
              <div className="mt-3 h-3 rounded bg-amber/80" style={{ width: "75%" }} />
            </div>
          </div>
          <label className="mt-8 block">
            <span className="flex items-baseline justify-between text-[14px] text-ink-muted"><span>Deliveries with this gap, a day</span><span className="tnum font-mono text-[18px] text-foreground">{per.toLocaleString("en-IN")}</span></span>
            <input type="range" min="100" max="100000" step="100" value={per} onChange={(e) => setPer(Number(e.target.value))} className="mt-3 w-full accent-[var(--green)]" aria-label="Deliveries with this gap, a day" />
          </label>
          <div className="mt-6 rounded-2xl border border-amber/50 bg-amber/5 p-5">
            <p className="text-[13px] text-ink-muted">Rs 25 paid for goods that never came, on every delivery, over a year</p>
            <p className="tnum mt-1 font-mono text-[40px] leading-none text-amber-ink">Rs {inr(year)}</p>
          </div>
          <p className="mt-4 text-[12.5px] text-ink-muted">An illustration with round numbers, not a measured figure.</p>
        </div>
      </div>
    </section>
  );
}

/** Fully disconnected. The run with the network cut, step by step. */
export function AirGap() {
  return (
    <section id="airgap" className="border-b border-line">
      <div className="mx-auto grid max-w-[1200px] gap-12 px-6 py-20 sm:px-10 lg:grid-cols-2 lg:items-center lg:px-14">
        <div>
          <p className="kLabel">Air gapped, on purpose</p>
          <h2 className="mt-5 max-w-[16ch] text-balance text-[38px] font-bold leading-[1.04] tracking-[-0.03em] text-foreground sm:text-[56px]">It works with the network cut.</h2>
          <p className="mt-6 max-w-[48ch] text-[17px] leading-relaxed text-ink-muted">
            Muse Glimmer and SAM 3.1 run on the machine, so no bill, no photo and no key ever leaves it. A business that cannot send its books to a cloud can still check every delivery, and still hand over a receipt anyone can verify offline.
          </p>
        </div>
        <div className="rounded-3xl border border-line bg-surface p-6 sm:p-8">
          <div className="flex items-center gap-3">
            <svg viewBox="0 0 48 48" className="h-10 w-10 text-amber-ink" aria-hidden="true"><path d="M8 18a24 24 0 0 1 32 0M14 25a15 15 0 0 1 20 0M20 32a7 7 0 0 1 8 0" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" /><circle cx="24" cy="39" r="2.5" fill="currentColor" /><path d="M6 6l36 36" stroke="var(--red)" strokeWidth="4" strokeLinecap="round" /></svg>
            <p className="text-[15px] font-semibold text-foreground">Network off, run on 3 November 2026</p>
          </div>
          <ul className="mt-5 divide-y divide-line">
            {offlineRun.steps.map((s) => (
              <li key={s.step} className="flex items-center justify-between gap-4 py-3 text-[14.5px]">
                <span className="text-foreground">{s.step}</span>
                <span className="font-mono text-[12px] text-green-ink">{s.result}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
