import { confidence, real } from "@/data/site";
import realworld from "@/data/realworld.json";
import scenarios from "@/data/scenarios.json";
import packagecheck from "@/data/packagecheck.json";

const sign = (n: number) => (n > 0 ? `+${n}` : String(n));

/** What was tested on real data: test photos against hand counts, the confidence setting, real California purchase orders, command line scenarios. */
export function RealEvidence() {
  const counted = real.rows.filter((r) => r.hand_count !== null);
  const worst = Math.max(...confidence.real.map((r) => r.total_abs_error), ...confidence.rendered.map((r) => r.total_abs_error));
  return (
    <section id="real-evidence" className="border-b border-line">
      <div className="mx-auto max-w-[1200px] px-4 py-16 sm:px-6">
        <p className="kLabel">Tested on real data</p>
        <h2 className="mt-3 max-w-[22ch] text-balance text-[34px] font-bold leading-[1.05] tracking-[-0.02em] text-foreground sm:text-[46px]">
          What real photos and real orders taught the product.
        </h2>

        <div className="mt-10 grid gap-10 grid-cols-1 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-wider text-ink-muted">SAM 3.1 against hand counts on real photos</p>
            <div className="mt-3 overflow-x-auto rounded-xl border border-line bg-surface">
              <table className="w-full min-w-[520px] text-left text-[13px]">
                <thead className="text-[11px] uppercase tracking-wide text-ink-muted">
                  <tr><th className="px-4 py-3">Photo</th><th className="px-4 py-3">Word 1</th><th className="px-4 py-3">Word 2</th><th className="px-4 py-3">Hand count</th><th className="px-4 py-3">Error</th></tr>
                </thead>
                <tbody>
                  {counted.map((r) => (
                    <tr key={r.key} className="border-t border-line">
                      <td className="px-4 py-2.5 font-mono">{r.pid}</td>
                      <td className="tnum px-4 py-2.5 font-mono">{r.results[0].word}: {r.results[0].count}</td>
                      <td className="tnum px-4 py-2.5 font-mono">{r.results[1].word}: {r.results[1].count}</td>
                      <td className="tnum px-4 py-2.5 font-mono">{r.hand_count}</td>
                      <td className={`tnum px-4 py-2.5 font-mono ${r.first_word_error === 0 ? "text-green-ink" : "text-amber-ink"}`}>{sign(r.first_word_error ?? 0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 max-w-[62ch] text-[12.5px] leading-relaxed text-ink-muted">
              Hand counts include far items, counted by eye. At confidence 0.5 the totals sit within a few items of them, and the agent loop looks at the overlay before it accepts a count.
            </p>
          </div>

          <div>
            <p className="font-mono text-[11px] uppercase tracking-wider text-ink-muted">Total counting error by the lowest mask score kept</p>
            <div className="mt-3 space-y-2 rounded-xl border border-line bg-surface p-5">
              {confidence.real.map((r, i) => (
                <div key={r.threshold} className="grid grid-cols-[3rem_1fr_3rem] items-center gap-3 font-mono text-[12px]">
                  <span className="text-ink-muted">{r.threshold}</span>
                  <span className="h-3 rounded bg-raised"><span className="block h-3 rounded bg-green" style={{ width: `${Math.max(2, (r.total_abs_error / worst) * 100)}%` }} /></span>
                  <span className="tnum text-foreground">{r.total_abs_error}</span>
                  <span className="col-span-3 -mt-1 pl-[3.75rem] text-[10.5px] text-ink-muted">{i === 0 ? "builder's photos, 8 with hand counts. Rendered photos at the same setting: error " + confidence.rendered[0].total_abs_error : ""}</span>
                </div>
              ))}
            </div>
            <p className="mt-3 text-[12.5px] leading-relaxed text-ink-muted">
              Real photos moved the default from 0.4 to 0.5. On the clean rendered benchmark 0.4 is best, so no single value fits everywhere and it is a setting.
            </p>
          </div>
        </div>

        <div className="mt-14 grid gap-px overflow-hidden rounded-3xl border border-line bg-line sm:grid-cols-2 lg:grid-cols-4">
          {[
            { v: `${realworld.passed} of ${realworld.cases}`, l: `cases on ${realworld.orders} real California purchase orders, each with a documented exception type`, h: "docs/REAL_WORLD_CHECK.md" },
            { v: `${scenarios.passed} of ${scenarios.total}`, l: "command line scenarios: typical, varied, extreme, repeated, damaged receipts", h: "docs/PACKAGE_SCENARIOS.md" },
            { v: `${packagecheck.passed} of ${packagecheck.steps}`, l: "steps of a clean install with the network blocked", h: "docs/PACKAGE_CHECK.md" },
            { v: "2 of 2", l: "supplier bills, one Hindi and one Tamil, read by Muse Glimmer with every field correct", h: "docs/LANGUAGE_BILL_RESULT.md" },
          ].map((x) => (
            <div key={x.v + x.h} className="bg-background p-6">
              <p className="tnum font-mono text-[34px] leading-none text-foreground">{x.v}</p>
              <p className="mt-3 text-[13px] leading-relaxed text-ink-muted">{x.l}</p>
              <p className="mt-3 font-mono text-[11px] text-ink-muted">{x.h}</p>
            </div>
          ))}
        </div>
        <div className="mt-14">
          <p className="kLabel">Agent loop on a free Kaggle GPU (two T4s)</p>
          <div className="mt-4 grid gap-px overflow-hidden rounded-3xl border border-line bg-line sm:grid-cols-2 lg:grid-cols-4">
            {[
              { v: "11 of 12", l: "photos counted exactly right after the loop, against the delivery records. The twelfth was held for a person and none were wrong. The first word alone was right on 5 of 12." },
              { v: "5 of 8", l: "real photos with hand counts accepted by the loop, within 3 items of the hand count. The other 3 went to a person, which is the job." },
              { v: "24 s", l: "for Muse Glimmer to read a bill once warm (88 s on the first call). On a laptop CPU the same bill takes 4.5 to 8.9 minutes." },
              { v: "1 s", l: "for SAM 3.1 to count a photo once loaded. A delivery is checked in under a minute." },
            ].map((x) => (
              <div key={x.v} className="bg-background p-6">
                <p className="tnum font-mono text-[34px] leading-none text-green-ink">{x.v}</p>
                <p className="mt-3 text-[13px] leading-relaxed text-ink-muted">{x.l}</p>
              </div>
            ))}
          </div>
        </div>
        <p className="mt-4 max-w-[70ch] text-[12.5px] leading-relaxed text-ink-muted">
          The purchase orders are rows of the State of California open data ({realworld.source}); the exception types come from published accounts payable sources. Real orders sharpened the product, and it now handles quantities above 100,000, fractional counts, orders with up to 12 lines, rows with a missing quantity, unit of measure differences, and several processes writing one receipt file.
        </p>
      </div>
    </section>
  );
}
