import { useMemo, useState } from "react";
import { ArrowRight } from "lucide-react";
import { Link } from "@/lib/router";
import { run } from "@/data/site";
import { CopyBlock } from "@/components/bits";
import { EXAMPLES, check, money, type Delivery, type Line } from "@/lib/matcher";
import { cryptoReady, saveText, signCheck, toJsonl, type Signed } from "@/lib/sign";
import { downloadReceipt } from "@/lib/receiptpdf";

const input = "h-10 w-full min-w-0 rounded-lg border border-line bg-background px-3 text-[14px] text-foreground outline-none transition-colors duration-150 focus:border-foreground";
const num = `${input} tnum font-mono`;

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[12px] text-ink-muted">{label}</span>
      {children}
    </label>
  );
}

const blank: Line = { item_code: "", description: "", ordered_qty: 0, ordered_rate: 0, billed_qty: 0, billed_rate: 0, received: 0, damaged: 0 };

export function Try() {
  const [d, setD] = useState<Delivery>(EXAMPLES.short!);
  const [signed, setSigned] = useState<Signed | null>(null);
  const [busy, setBusy] = useState(false);
  const verdict = useMemo(() => check(d), [d]);

  const edit = (patch: Partial<Delivery>) => { setD({ ...d, ...patch }); setSigned(null); };
  const editLine = (i: number, patch: Partial<Line>) => edit({ lines: d.lines.map((l, k) => (k === i ? { ...l, ...patch } : l)) });
  const fill = () => {
    const subtotal = Math.round(d.lines.reduce((s, l) => s + l.billed_qty * l.billed_rate, 0) * 100) / 100;
    const tax = Math.round(subtotal * d.tax_rate) / 100;
    edit({ tax, total: Math.round((subtotal + tax) * 100) / 100 });
  };
  const sign = async () => {
    setBusy(true);
    try { setSigned(await signCheck(d, verdict, run.policy_hash)); } finally { setBusy(false); }
  };
  const n = (v: string) => (v === "" ? 0 : Number(v));

  return (
    <div>
      <section className="border-b border-line">
        <div className="mx-auto max-w-[1200px] px-6 py-16 sm:px-10 lg:px-14">
          <p className="kLabel">Try it, live</p>
          <h1 className="mt-5 max-w-[16ch] text-balance text-[44px] font-bold leading-[1.02] tracking-[-0.03em] text-foreground sm:text-[72px]">Check a delivery yourself.</h1>
          <p className="mt-6 max-w-[58ch] text-[18px] leading-relaxed text-ink-muted">
            Type the bill, the order and what arrived. The same three way rules the agents use run right here in your browser, and every change is judged instantly.
            Then sign a receipt that verifies on any machine. Nothing you type is sent to a server.
          </p>
          <div className="mt-7 flex flex-wrap gap-2">
            {[["short", "Short delivery"], ["damaged", "Damaged goods"], ["clean", "A clean delivery"]].map(([k, label]) => (
              <button key={k} type="button" onClick={() => { setD(EXAMPLES[k]!); setSigned(null); }} className="h-10 rounded-full border border-line px-4 text-[13px] text-foreground transition-colors duration-150 hover:bg-raised">{label}</button>
            ))}
            <button type="button" onClick={() => { setD({ supplier: "", bill_no: "", po_no: "", tax_rate: 18, tax: 0, total: 0, lines: [{ ...blank }] }); setSigned(null); }} className="h-10 rounded-full border border-line px-4 text-[13px] text-ink-muted transition-colors duration-150 hover:text-foreground">Start from blank</button>
          </div>
        </div>
      </section>

      <section className="border-b border-line">
        <div className="mx-auto grid max-w-[1200px] gap-10 px-6 py-14 sm:px-10 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)] lg:px-14">
          <div>
            <p className="kLabel">1 / The delivery</p>
            <div className="mt-4 grid gap-4 sm:grid-cols-3">
              <Field label="Supplier"><input className={input} value={d.supplier} onChange={(e) => edit({ supplier: e.target.value })} /></Field>
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
                    <Field label="Ordered"><input type="number" min="0" className={num} value={l.ordered_qty} onChange={(e) => editLine(i, { ordered_qty: n(e.target.value) })} /></Field>
                    <Field label="Order rate"><input type="number" min="0" step="0.01" className={num} value={l.ordered_rate} onChange={(e) => editLine(i, { ordered_rate: n(e.target.value) })} /></Field>
                    <Field label="Billed"><input type="number" min="0" className={num} value={l.billed_qty} onChange={(e) => editLine(i, { billed_qty: n(e.target.value) })} /></Field>
                    <Field label="Billed rate"><input type="number" min="0" step="0.01" className={num} value={l.billed_rate} onChange={(e) => editLine(i, { billed_rate: n(e.target.value) })} /></Field>
                    <Field label="Arrived"><input type="number" min="0" className={num} value={l.received} onChange={(e) => editLine(i, { received: n(e.target.value) })} /></Field>
                    <Field label="Damaged"><input type="number" min="0" className={num} value={l.damaged} onChange={(e) => editLine(i, { damaged: n(e.target.value) })} /></Field>
                  </div>
                  {d.lines.length > 1 && (
                    <button type="button" onClick={() => edit({ lines: d.lines.filter((_, k) => k !== i) })} className="mt-3 text-[12.5px] text-ink-muted underline underline-offset-4 hover:text-foreground">Remove this item</button>
                  )}
                </fieldset>
              ))}
              <button type="button" onClick={() => edit({ lines: [...d.lines, { ...blank }] })} className="h-10 rounded-full border border-line px-4 text-[13px] text-foreground transition-colors duration-150 hover:bg-raised">Add an item</button>
            </div>

            <div className="mt-8 grid gap-4 sm:grid-cols-4">
              <Field label="Order tax rate, percent"><input type="number" min="0" className={num} value={d.tax_rate} onChange={(e) => edit({ tax_rate: n(e.target.value) })} /></Field>
              <Field label="Tax on the bill"><input type="number" min="0" step="0.01" className={num} value={d.tax} onChange={(e) => edit({ tax: n(e.target.value) })} /></Field>
              <Field label="Bill total"><input type="number" min="0" step="0.01" className={num} value={d.total} onChange={(e) => edit({ total: n(e.target.value) })} /></Field>
              <div className="flex items-end"><button type="button" onClick={fill} className="h-10 w-full rounded-lg border border-line px-3 text-[13px] text-foreground transition-colors duration-150 hover:bg-raised">Fill tax and total</button></div>
            </div>
          </div>

          <div className="lg:sticky lg:top-24 lg:self-start">
            <p className="kLabel">2 / The verdict, live</p>
            <div className={`mt-4 rounded-3xl border p-6 ${verdict.held ? "border-amber/50 bg-amber/5" : "border-green/50 bg-green/5"}`} role="status" aria-live="polite">
              <p className={`font-mono text-[12px] uppercase tracking-[0.18em] ${verdict.held ? "text-amber-ink" : "text-green-ink"}`}>{verdict.held ? "Held for a person" : "Clear to enter"}</p>
              <p className="mt-3 text-[26px] font-bold leading-tight tracking-[-0.02em] text-foreground">
                {verdict.held ? `${d.bill_no || "This bill"} should not be paid as it stands.` : `${d.bill_no || "This bill"} matches the order and the goods.`}
              </p>
              {verdict.held ? (
                <ul className="mt-4 space-y-2 text-[14.5px] leading-snug text-foreground">
                  {verdict.reasons.map((r) => <li key={r} className="flex gap-2"><span aria-hidden="true" className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-amber" />{r}</li>)}
                </ul>
              ) : (
                <p className="mt-3 text-[14.5px] text-ink-muted">Order, bill and goods agree within the policy limits. Total {money(d.total)}.</p>
              )}
            </div>

            <div className="mt-6 overflow-x-auto rounded-2xl border border-line bg-surface">
              <table className="w-full min-w-[420px] text-left text-[13px]">
                <thead className="text-[11px] uppercase tracking-wide text-ink-muted"><tr><th className="px-4 py-3">Item</th><th className="px-4 py-3 text-right">Ordered</th><th className="px-4 py-3 text-right">Billed</th><th className="px-4 py-3 text-right">Good on arrival</th></tr></thead>
                <tbody>
                  {verdict.rows.map((r, i) => (
                    <tr key={i} className="border-t border-line">
                      <td className="px-4 py-2.5">{r.description || r.item_code}</td>
                      <td className="tnum px-4 py-2.5 text-right font-mono">{r.ordered}</td>
                      <td className="tnum px-4 py-2.5 text-right font-mono">{r.billed}</td>
                      <td className={`tnum px-4 py-2.5 text-right font-mono ${r.issues.length ? "text-amber-ink" : "text-green-ink"}`}>{r.received}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="kLabel mt-8">3 / The receipt</p>
            <div className="paper mt-4 p-5 pb-8">
              {!signed ? (
                <>
                  <p className="text-[14.5px] leading-relaxed text-foreground">Sign this check as a chain of receipts. Your browser makes a fresh key, signs every step, and checks the chain.</p>
                  <button type="button" disabled={busy || !cryptoReady()} onClick={sign} className="mt-4 inline-flex h-11 items-center gap-2 rounded-full bg-foreground px-5 text-[13.5px] font-medium text-background transition-opacity duration-150 hover:opacity-90 disabled:opacity-50">
                    {busy ? "Signing" : "Sign a receipt"} <ArrowRight className="h-4 w-4" />
                  </button>
                  {!cryptoReady() && <p className="mt-3 text-[12.5px] text-ink-muted">This browser needs Ed25519 support. Use a current Chrome, Edge, Safari or Firefox.</p>}
                </>
              ) : (
                <>
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-serif text-[15px] font-semibold text-foreground">{signed.receipts.length} steps signed</p>
                    {signed.verified && <span className="stamp">Verified</span>}
                  </div>
                  <ol className="mt-3 space-y-1.5 text-[13.5px] text-foreground">
                    {signed.receipts.map((r) => <li key={r.hash} className="flex justify-between gap-3"><span>{r.body.seq}. {r.body.agent}, {r.body.step}</span><span className="tnum font-mono text-[11.5px] text-ink-muted">{r.hash.slice(0, 8)}</span></li>)}
                  </ol>
                  <div className="mt-5 flex flex-wrap gap-2">
                    <button type="button" onClick={() => downloadReceipt(signed.receipts, signed.verified, d.bill_no || "live-check")} className="h-10 rounded-full bg-foreground px-4 text-[13px] font-medium text-background">Download the PDF</button>
                    <button type="button" onClick={() => { saveText("receipts.jsonl", toJsonl(signed.receipts), "application/json"); window.setTimeout(() => saveText("public_key.txt", signed.publicKey + "\n"), 350); }} className="h-10 rounded-full border border-line px-4 text-[13px] text-foreground hover:bg-raised">Download the signed files</button>
                  </div>
                  <p className="mt-4 text-[12.5px] leading-relaxed text-ink-muted">Put both files in one folder and check them on any machine, with the network off:</p>
                  <div className="mt-2"><CopyBlock command="relayloom verify receipts.jsonl" /></div>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      <section>
        <div className="mx-auto max-w-[1200px] px-6 py-20 sm:px-10 lg:px-14">
          <p className="kLabel">Next, with your own photos</p>
          <h2 className="mt-4 max-w-[20ch] text-balance text-[36px] font-bold leading-[1.05] tracking-[-0.025em] text-foreground sm:text-[48px]">The models count the goods. You choose where they run.</h2>
          <p className="mt-5 max-w-[60ch] text-[16px] leading-relaxed text-ink-muted">
            This page judges the paperwork against the goods you enter. Muse Glimmer and SAM 3.1 are what count the goods in a photo and read a bill, and they run on hardware you control, so no bill or photo leaves it.
          </p>
          <div className="mt-10 grid gap-px overflow-hidden rounded-3xl border border-line bg-line md:grid-cols-3">
            <div className="bg-background p-7">
              <p className="kLabel text-green-ink">On your machine</p>
              <p className="mt-3 text-[15px] leading-relaxed text-ink-muted">Install once. The same rules, plus the models, with your photos and your bill.</p>
              <div className="mt-4"><CopyBlock command="pip install relayloom" /></div>
            </div>
            <div className="bg-background p-7">
              <p className="kLabel text-green-ink">On a free GPU</p>
              <p className="mt-3 text-[15px] leading-relaxed text-ink-muted">The notebook that produced the proof runs on a free Kaggle GPU. Open it and press run.</p>
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
    </div>
  );
}
