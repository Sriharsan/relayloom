import { useMemo, useState } from "react";
import { ArrowRight } from "lucide-react";
import { Link } from "@/lib/router";
import { run } from "@/data/site";
import { CopyBlock } from "@/components/bits";
import { EvidenceTool, Qr } from "@/components/evidence";
import { COUNTRIES, EXAMPLES, amounts, blankDelivery, check, country, isBlank, money, type Delivery, type Line } from "@/lib/matcher";
import { cryptoReady, saveText, signCheck, toJsonl, type Signed } from "@/lib/sign";
import { buildReport } from "@/lib/buildreport";
import { makeReport, savePdf } from "@/lib/report";

const input = "h-10 w-full min-w-0 rounded-lg border border-line bg-background px-3 text-[14px] text-foreground outline-none transition-colors duration-150 focus:border-foreground";
const num = `${input} tnum font-mono`;
const SITE = "https://relayloom.vercel.app/try";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[12px] text-ink-muted">{label}</span>
      {children}
    </label>
  );
}

function Num({ value, onChange, step, label }: { value: number; onChange: (n: number) => void; step?: string; label: string }) {
  return (
    <Field label={label}>
      <input type="number" inputMode="decimal" min="0" step={step} placeholder="0" className={num} value={value === 0 ? "" : value} onChange={(e) => onChange(e.target.value === "" ? 0 : Math.max(0, Number(e.target.value)))} />
    </Field>
  );
}

const blank = (): Line => ({ item_code: "", description: "", ordered_qty: 0, ordered_rate: 0, billed_qty: 0, billed_rate: 0, received: 0, damaged: 0 });

export function Try() {
  const [d, setD] = useState<Delivery>(EXAMPLES.short!);
  const [signed, setSigned] = useState<Signed | null>(null);
  const [view, setView] = useState<"verdict" | "report">("verdict");
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<number | null>(null);
  const c = country(d);
  const a = useMemo(() => amounts(d), [d]);
  const verdict = useMemo(() => check(d), [d]);
  const items = d.lines.filter((l) => !isBlank(l));

  const edit = (patch: Partial<Delivery>) => { setD({ ...d, ...patch }); setSigned(null); setView("verdict"); };
  const editLine = (i: number, patch: Partial<Line>) => edit({ lines: d.lines.map((l, k) => (k === i ? { ...l, ...patch } : l)) });
  const load = (x: Delivery) => { setD(x); setSigned(null); setView("verdict"); };
  const chooseCountry = (code: string) => { const k = COUNTRIES.find((x) => x.code === code)!; edit({ country: code, tax_rate: k.rate, manual: false }); };

  const sign = async () => {
    setBusy(true);
    try { setSigned(await signCheck(d, verdict, run.policy_hash)); setView("report"); } finally { setBusy(false); }
  };
  const savePdfNow = async () => { if (signed) savePdf(makeReport(await buildReport(d, verdict, signed)), `relayloom-receipt-${d.bill_no || "check"}.pdf`); };
  const saveFiles = () => { if (!signed) return; saveText("receipts.jsonl", toJsonl(signed.receipts), "application/json"); window.setTimeout(() => saveText("public_key.txt", signed.publicKey + "\n"), 350); };

  return (
    <div>
      <section className="border-b border-line">
        <div className="mx-auto grid max-w-[1200px] items-center gap-10 px-6 py-14 sm:px-10 lg:grid-cols-[minmax(0,1fr)_auto] lg:px-14">
          <div>
            <p className="kLabel">Try it, live, on any device</p>
            <h1 className="mt-5 max-w-[16ch] text-balance text-[44px] font-bold leading-[1.02] tracking-[-0.03em] text-foreground sm:text-[68px]">Check a delivery yourself.</h1>
            <p className="mt-6 max-w-[58ch] text-[17px] leading-relaxed text-ink-muted">
              Enter the bill and what arrived, add a photo of the goods as evidence, and tap each item to count it. The same three way rules the agents use judge every change instantly, and the phone on the right
              signs a receipt you can save and verify anywhere. Nothing you enter or photograph leaves your device.
            </p>
            <div className="mt-7 flex flex-wrap gap-2">
              {[["short", "Short delivery"], ["damaged", "Damaged goods"], ["clean", "A clean delivery"]].map(([k, label]) => (
                <button key={k} type="button" onClick={() => load(EXAMPLES[k]!)} className="h-10 rounded-full border border-line px-4 text-[13px] text-foreground transition-colors duration-150 hover:bg-raised">{label}</button>
              ))}
              <button type="button" onClick={() => load(blankDelivery())} className="h-10 rounded-full border border-line px-4 text-[13px] text-ink-muted transition-colors duration-150 hover:text-foreground">Start a new case</button>
            </div>
          </div>
          <div className="flex items-center gap-4 rounded-2xl border border-line bg-surface p-4">
            <Qr text={SITE} size={116} />
            <div className="max-w-[18ch]">
              <p className="text-[14px] font-semibold text-foreground">Open it on your phone</p>
              <p className="mt-1 text-[12.5px] leading-snug text-ink-muted">Scan, then use the camera for the evidence photo.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="border-b border-line">
        <div className="mx-auto grid max-w-[1200px] gap-12 px-6 py-14 sm:px-10 lg:grid-cols-[minmax(0,1fr)_380px] lg:px-14">
          <div>
            <p className="kLabel">1 / The delivery</p>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <Field label="Supplier"><input className={input} value={d.supplier} onChange={(e) => edit({ supplier: e.target.value })} /></Field>
              <Field label="Country, for the tax">
                <select className={input} value={d.country} onChange={(e) => chooseCountry(e.target.value)}>
                  {COUNTRIES.map((k) => <option key={k.code} value={k.code}>{k.name}, {k.tax} {k.rate} percent</option>)}
                </select>
              </Field>
              <Field label="Bill number"><input className={input} value={d.bill_no} onChange={(e) => edit({ bill_no: e.target.value })} /></Field>
              <Field label="Order number"><input className={input} value={d.po_no} onChange={(e) => edit({ po_no: e.target.value })} /></Field>
            </div>

            <div className="mt-8 space-y-4">
              {d.lines.map((l, i) => (
                <fieldset key={i} className="rounded-2xl border border-line bg-surface p-4">
                  <legend className="px-2 text-[12px] text-ink-muted">Item {i + 1}</legend>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Field label="Item code"><input className={input} value={l.item_code} onChange={(e) => editLine(i, { item_code: e.target.value })} /></Field>
                    <Field label="Description"><input className={input} value={l.description} onChange={(e) => editLine(i, { description: e.target.value })} /></Field>
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
                    <Num label="Ordered" value={l.ordered_qty} onChange={(n) => editLine(i, { ordered_qty: n })} />
                    <Num label={`Order rate, ${c.currency}`} step="0.01" value={l.ordered_rate} onChange={(n) => editLine(i, { ordered_rate: n })} />
                    <Num label="Billed" value={l.billed_qty} onChange={(n) => editLine(i, { billed_qty: n })} />
                    <Num label={`Billed rate, ${c.currency}`} step="0.01" value={l.billed_rate} onChange={(n) => editLine(i, { billed_rate: n })} />
                    <Num label="Arrived" value={l.received} onChange={(n) => editLine(i, { received: n })} />
                    <Num label="Damaged" value={l.damaged} onChange={(n) => editLine(i, { damaged: n })} />
                  </div>
                  <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-line pt-4">
                    {l.photo ? <img src={l.photo} alt={`Evidence for ${l.description || "item"}`} className="h-16 w-24 rounded-lg border border-line object-cover" /> : <span className="flex h-16 w-24 items-center justify-center rounded-lg border border-dashed border-line text-[11px] text-ink-muted">No photo</span>}
                    <div>
                      <button type="button" onClick={() => setEditing(i)} className="h-10 rounded-full bg-foreground px-4 text-[13px] font-medium text-background">{l.photo ? "Edit the evidence" : "Add photo evidence"}</button>
                      <p className="mt-1.5 text-[12px] text-ink-muted">Tap each item on the photo to count it. The count fills in Arrived and Damaged for you.</p>
                    </div>
                    {d.lines.length > 1 && <button type="button" onClick={() => edit({ lines: d.lines.filter((_, k) => k !== i) })} className="ml-auto text-[12.5px] text-ink-muted underline underline-offset-4 hover:text-foreground">Remove</button>}
                  </div>
                </fieldset>
              ))}
              <button type="button" onClick={() => edit({ lines: [...d.lines, blank()] })} className="h-10 rounded-full border border-line px-4 text-[13px] text-foreground transition-colors duration-150 hover:bg-raised">Add an item</button>
            </div>

            <div className="mt-8 rounded-2xl border border-line bg-surface p-5">
              <p className="kLabel">Amounts, worked out for you</p>
              <dl className="mt-3 space-y-2 text-[14.5px]">
                <div className="flex justify-between"><dt className="text-ink-muted">Items</dt><dd className="tnum font-mono text-foreground">{money(a.subtotal, c.currency)}</dd></div>
                <div className="flex justify-between"><dt className="text-ink-muted">{c.tax} at {d.tax_rate} percent</dt><dd className="tnum font-mono text-foreground">{money(a.tax, c.currency)}</dd></div>
                <div className="flex justify-between border-t border-line pt-2"><dt className="font-semibold text-foreground">Bill total</dt><dd className="tnum font-mono text-[18px] font-semibold text-foreground">{money(a.total, c.currency)}</dd></div>
              </dl>
              <label className="mt-4 flex items-center gap-2 text-[13px] text-ink-muted">
                <input type="checkbox" checked={d.manual} onChange={(e) => edit({ manual: e.target.checked, tax: a.tax, total: a.total })} />
                The paper bill shows different amounts, let me type them
              </label>
              {d.manual && (
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  <Num label={`${c.tax} on the bill`} step="0.01" value={d.tax} onChange={(n) => edit({ tax: n })} />
                  <Num label="Bill total" step="0.01" value={d.total} onChange={(n) => edit({ total: n })} />
                </div>
              )}
            </div>
          </div>

          {/* The phone: the live verdict, the signed receipt and the report, all inside it. */}
          <div className="lg:sticky lg:top-24 lg:self-start">
            <p className="kLabel text-center">2 / The phone</p>
            <div className="mx-auto mt-4 w-full max-w-[360px] rounded-[44px] border-[6px] border-foreground/90 bg-foreground/90 p-1.5 shadow-2xl shadow-black/30">
              <div className="relative flex h-[700px] flex-col overflow-hidden rounded-[36px] bg-background">
                <div className="flex items-center justify-between px-6 pb-1 pt-3 text-[11px] font-medium text-foreground" aria-hidden="true"><span>9:41</span><span className="h-5 w-24 rounded-full bg-foreground/90" /><span>100%</span></div>
                <div className="flex items-center justify-between border-b border-line px-5 py-2.5">
                  <p className="text-[15px] font-bold tracking-tight text-foreground">Relayloom</p>
                  <p className="font-mono text-[10.5px] uppercase tracking-wider text-ink-muted">{view === "verdict" ? "Live check" : "Receipt"}</p>
                </div>

                <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4" role="status" aria-live="polite">
                  {view === "verdict" || !signed ? (
                    <>
                      <div className={`rounded-2xl border p-4 ${verdict.held ? "border-amber/50 bg-amber/5" : "border-green/50 bg-green/5"}`}>
                        <p className={`font-mono text-[10.5px] uppercase tracking-[0.18em] ${verdict.held ? "text-amber-ink" : "text-green-ink"}`}>{verdict.held ? "Held for a person" : "Clear to enter"}</p>
                        <p className="mt-2 text-[19px] font-bold leading-tight tracking-[-0.01em] text-foreground">{verdict.held ? `${d.bill_no || "This bill"} should not be paid as it stands.` : `${d.bill_no || "This bill"} matches the order and the goods.`}</p>
                        {verdict.held && (
                          <ul className="mt-3 space-y-1.5 text-[13px] leading-snug text-foreground">
                            {verdict.reasons.map((r) => <li key={r} className="flex gap-2"><span aria-hidden="true" className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-amber" />{r}</li>)}
                          </ul>
                        )}
                      </div>
                      <div className="mt-4 divide-y divide-line rounded-2xl border border-line">
                        {verdict.rows.map((r, i) => (
                          <div key={i} className="px-4 py-3 text-[13px]">
                            <p className="font-medium text-foreground">{r.description}</p>
                            <p className="mt-1 flex justify-between text-ink-muted"><span>Ordered {r.ordered} · Billed {r.billed}</span><span className={`tnum font-mono ${r.issues.length ? "text-amber-ink" : "text-green-ink"}`}>{r.received} good</span></p>
                          </div>
                        ))}
                        <div className="flex justify-between px-4 py-3 text-[13px]"><span className="text-ink-muted">Bill total</span><span className="tnum font-mono font-semibold text-foreground">{money(a.total, c.currency)}</span></div>
                      </div>
                      {items.some((l) => l.photo) && (
                        <div className="mt-4 flex gap-2 overflow-x-auto">
                          {items.filter((l) => l.photo).map((l, i) => <img key={i} src={l.photo} alt={`Evidence for ${l.description}`} className="h-20 w-28 shrink-0 rounded-xl border border-line object-cover" />)}
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="paper p-4 pb-7">
                      <div className="flex items-center justify-between gap-2"><p className="font-serif text-[16px] font-semibold text-foreground">Receipt</p>{signed.verified && <span className="stamp">Verified</span>}</div>
                      <p className="mt-1 text-[12.5px] text-ink-muted">{signed.receipts.length} steps, each signed and linked to the one before.</p>
                      <ol className="mt-3 space-y-1.5 text-[13px] text-foreground">
                        {signed.receipts.map((r) => <li key={r.hash} className="flex justify-between gap-3"><span>{r.body.seq}. {r.body.agent}, {r.body.step}</span><span className="tnum font-mono text-[11px] text-ink-muted">{r.hash.slice(0, 8)}</span></li>)}
                      </ol>
                      <div className="mt-4 rounded-xl border border-line bg-background/70 p-3 text-[13px]">
                        <p className="font-semibold text-foreground">{verdict.held ? "Held for a person" : "Clear to enter"}</p>
                        <p className="mt-1 text-ink-muted">{d.supplier || "Supplier"} · {d.bill_no || "Bill"} · {money(a.total, c.currency)}</p>
                        {signed.photos.length > 0 && <p className="mt-1 text-ink-muted">{signed.photos.length} evidence photo{signed.photos.length > 1 ? "s" : ""} fingerprinted in the receipt</p>}
                      </div>
                      <div className="mt-4 grid gap-2">
                        <button type="button" onClick={savePdfNow} className="h-11 rounded-full bg-foreground text-[13.5px] font-medium text-background">Save the PDF report</button>
                        <button type="button" onClick={saveFiles} className="h-11 rounded-full border border-line text-[13.5px] text-foreground hover:bg-raised">Save the signed files</button>
                        <button type="button" onClick={() => setView("verdict")} className="h-9 text-[12.5px] text-ink-muted underline underline-offset-4">Back to the live check</button>
                      </div>
                    </div>
                  )}
                </div>

                {view === "verdict" && (
                  <div className="border-t border-line p-4">
                    <button type="button" disabled={busy || !cryptoReady() || items.length === 0} onClick={sign} className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-full bg-foreground text-[14px] font-medium text-background transition-opacity duration-150 hover:opacity-90 disabled:opacity-50">
                      {busy ? "Signing" : "Sign a receipt"} <ArrowRight className="h-4 w-4" />
                    </button>
                    {!cryptoReady() && <p className="mt-2 text-center text-[11.5px] text-ink-muted">This browser needs Ed25519 support. Use a current Chrome, Edge, Safari or Firefox.</p>}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section>
        <div className="mx-auto max-w-[1200px] px-6 py-20 sm:px-10 lg:px-14">
          <p className="kLabel">Next, count with the models</p>
          <h2 className="mt-4 max-w-[22ch] text-balance text-[36px] font-bold leading-[1.05] tracking-[-0.025em] text-foreground sm:text-[48px]">The same receipt, with the goods counted for you.</h2>
          <p className="mt-5 max-w-[60ch] text-[16px] leading-relaxed text-ink-muted">
            Here you count by tapping. Muse Glimmer and SAM 3.1 count the goods in a photo and read a bill on hardware you control, so no bill or photo leaves it. The receipt is the same file either way.
          </p>
          <div className="mt-10 grid gap-px overflow-hidden rounded-3xl border border-line bg-line md:grid-cols-3">
            <div className="bg-background p-7">
              <p className="kLabel text-green-ink">On your machine</p>
              <p className="mt-3 text-[15px] leading-relaxed text-ink-muted">Install once, then add your photos as evidence in the PDF.</p>
              <div className="mt-4"><CopyBlock command="pip install relayloom" /></div>
              <div className="mt-2"><CopyBlock command="relayloom receipt receipts.jsonl --evidence dock.jpg" /></div>
            </div>
            <div className="bg-background p-7">
              <p className="kLabel text-green-ink">On a free GPU</p>
              <p className="mt-3 text-[15px] leading-relaxed text-ink-muted">The notebook behind the proof runs on a free Kaggle GPU. Open it and press run.</p>
              <a href="https://github.com/Sriharsan/relayloom/blob/main/kaggle/relayloom-gpu.ipynb" target="_blank" rel="noreferrer" className="mt-4 inline-flex h-10 items-center rounded-full border border-line px-4 text-[13px] text-foreground hover:bg-raised">Open the notebook</a>
            </div>
            <div className="bg-background p-7">
              <p className="kLabel text-green-ink">Read the code</p>
              <p className="mt-3 text-[15px] leading-relaxed text-ink-muted">Every rule, receipt and test is public. Fork it, or open an issue for a delivery you need handled.</p>
              <Link to="/developers" className="mt-4 inline-flex h-10 items-center rounded-full border border-line px-4 text-[13px] text-foreground hover:bg-raised">Developers</Link>
            </div>
          </div>
        </div>
      </section>

      {editing !== null && d.lines[editing] && (
        <EvidenceTool line={d.lines[editing]!} onClose={() => setEditing(null)} onSave={(patch) => editLine(editing, patch)} />
      )}
    </div>
  );
}
