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
            <p className="font-mono text-[11px] uppercase tracking-wider text-ink-muted">SAM 3.1 against hand counts, builder-provided test photos</p>
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
              Hand counts include far items. P01, P02, P03, P06 and P12 were counted by eye by the assistant, P07, P10 and P11 by the builder. At the first setting SAM over-counts clutter: when both words agree on a wrong
              number only a look at the overlay or a person catches it.
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
        <p className="mt-4 max-w-[70ch] text-[12.5px] leading-relaxed text-ink-muted">
          The purchase orders are rows of the State of California open data ({realworld.source}); the exception types come from published accounts payable sources. The first run found real problems and all were fixed:
          quantities above 100,000, fractional counts, orders with up to 12 lines, rows with a missing quantity, unit of measure differences, and several processes writing one receipt file.
        </p>
      </div>
    </section>
  );
}
