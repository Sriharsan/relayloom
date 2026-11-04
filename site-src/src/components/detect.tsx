import { useEffect, useRef, useState } from "react";
import { real } from "@/data/site";

const reduced = () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** The photo first, then a scan line sweeps across and every item turns green and numbered while the count climbs. */
export function DetectReveal({ raw, overlay, count, alt, play = 0 }: { raw?: string; overlay: string; count: number; alt: string; play?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const [p, setP] = useState(reduced() ? 1 : 0);
  const [seen, setSeen] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el || reduced()) { setP(1); return; }
    const io = new IntersectionObserver(([e]) => { if (e?.isIntersecting) setSeen(true); }, { threshold: 0.35 });
    io.observe(el);
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    if (!seen || reduced()) return;
    let raf = 0;
    const t0 = performance.now();
    const length = 3200;
    setP(0);
    const tick = (now: number) => {
      const k = Math.min(1, (now - t0) / length);
      setP(1 - Math.pow(1 - k, 2.2));
      if (k < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [seen, play, overlay]);

  const shown = Math.round(count * p);
  return (
    <div ref={ref} className="relative overflow-hidden rounded-xl border border-line bg-raised" style={{ aspectRatio: "4 / 3" }}>
      {raw && <img src={raw} alt="" className="absolute inset-0 h-full w-full object-contain opacity-90" loading="lazy" />}
      <img src={overlay} alt={alt} className="absolute inset-0 h-full w-full object-contain" style={{ clipPath: `inset(0 ${100 - p * 100}% 0 0)` }} loading="lazy" />
      {p > 0 && p < 1 && <span className="absolute inset-y-0 w-0.5 bg-green shadow-[0_0_14px_3px_var(--green)]" style={{ left: `${p * 100}%` }} aria-hidden="true" />}
      <div className="absolute bottom-3 left-3 rounded-lg border border-line bg-background/90 px-3 py-1.5 backdrop-blur">
        <p className="font-mono text-[10px] uppercase tracking-wider text-ink-muted">{p < 1 ? "SAM 3.1 detecting" : "SAM 3.1 counted"}</p>
        <p className="tnum font-mono text-[26px] leading-none text-green-ink">{shown}</p>
      </div>
    </div>
  );
}

/** Real photos, counted by SAM 3.1. Pick one and watch it count. */
export function RealCountPlayer() {
  const choices = real.rows.filter((r) => r.hand_count !== null && (r as { show?: boolean }).show !== false);
  const [i, setI] = useState(0);
  const [tick, setTick] = useState(0);
  const r = choices[i]!;
  const res = r.results[0]!;
  return (
    <section className="mb-8 rounded-2xl border border-line bg-surface p-5 sm:p-6" aria-label="Watch the count on a real photo">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="kLabel">Watch it count</p>
          <h2 className="mt-2 text-[24px] font-bold leading-tight tracking-[-0.02em] text-foreground sm:text-[30px]">A real photo, from the first look to the last green mark.</h2>
        </div>
        <button type="button" onClick={() => setTick((n) => n + 1)} className="h-10 rounded-full border border-line px-4 text-[13px] text-foreground transition-colors duration-150 hover:bg-raised">Replay</button>
      </div>
      <div className="mt-5 grid gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)] lg:items-center">
        <DetectReveal raw={`/img/real/${r.key}.jpg`} overlay={`/img/real/overlay/${res.overlay}`} count={res.count} alt={`${r.pid} with ${res.count} items outlined and numbered`} play={tick + i * 100} />
        <div>
          <div className="flex flex-wrap gap-2" role="group" aria-label="Choose a photo">
            {choices.map((c, k) => (
              <button key={c.key} type="button" onClick={() => { setI(k); setTick((n) => n + 1); }} className={`tnum h-9 rounded-full border px-3.5 font-mono text-[12px] transition-colors duration-150 ${k === i ? "border-foreground text-foreground" : "border-line text-ink-muted hover:text-foreground"}`}>{c.pid}</button>
            ))}
          </div>
          <dl className="mt-5 space-y-2 text-[14.5px]">
            <div className="flex justify-between"><dt className="text-ink-muted">SAM 3.1 counted</dt><dd className="tnum font-mono text-green-ink">{res.count}</dd></div>
            <div className="flex justify-between"><dt className="text-ink-muted">Counted by eye</dt><dd className="tnum font-mono text-foreground">{r.hand_count}</dd></div>
            <div className="flex justify-between"><dt className="text-ink-muted">The word searched</dt><dd className="font-mono text-foreground">{res.word}</dd></div>
          </dl>
          <p className="mt-5 text-[13.5px] leading-relaxed text-ink-muted">The photo is real. Muse Glimmer chooses the words, SAM 3.1 outlines and numbers every item, and the count goes into the receipt with the photo.</p>
        </div>
      </div>
    </section>
  );
}
