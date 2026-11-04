/** A structured, human readable PDF report, built in the browser with no library. A4, Helvetica, with JPEG evidence photos. */
export interface Evidence { label: string; caption: string; jpeg: Uint8Array; w: number; h: number }
export interface ReportItem { item: string; ordered: number; billed: number; good: number; damaged: number; note: string }
export interface Report {
  title: string;
  held: boolean;
  headline: string;
  reasons: string[];
  facts: [string, string][];
  items: ReportItem[];
  totals: [string, string][];
  steps: string[];
  evidence: Evidence[];
  proof: string[];
  verified: boolean | null;
}

const W = 595;
const H = 842;
const M = 48;
const GREEN: [number, number, number] = [0.05, 0.43, 0.27];
const AMBER: [number, number, number] = [0.62, 0.38, 0.0];
const INK: [number, number, number] = [0.1, 0.1, 0.12];
const MUTED: [number, number, number] = [0.42, 0.44, 0.48];

const latin = (s: string) =>
  s.replace(/₹/g, "Rs ").replace(/[–—]/g, "-").replace(/[‘’]/g, "'").replace(/[“”]/g, '"').replace(/[^\x20-\x7e\xa0-\xff]/g, "?");
const esc = (s: string) => latin(s).replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)");
const bytesOf = (s: string) => Uint8Array.from(s, (c) => c.charCodeAt(0) & 255);
const textWidth = (s: string, size: number, bold = false) => latin(s).length * size * (bold ? 0.56 : 0.52);
const col = (c: [number, number, number]) => `${c[0]} ${c[1]} ${c[2]}`;

function wrap(text: string, size: number, width: number, bold = false): string[] {
  const out: string[] = [];
  let line = "";
  for (const word of latin(text).split(/\s+/)) {
    const next = line ? `${line} ${word}` : word;
    if (textWidth(next, size, bold) > width && line) { out.push(line); line = word; } else line = next;
  }
  out.push(line);
  return out;
}

class Doc {
  pages: string[][] = [];
  images: { name: string; jpeg: Uint8Array; w: number; h: number }[] = [];
  y = H - M;
  cur: string[] = [];
  constructor() { this.newPage(); }
  newPage() { this.cur = []; this.pages.push(this.cur); this.y = H - M; }
  need(h: number) { if (this.y - h < M + 20) this.newPage(); }
  text(x: number, y: number, s: string, size = 10.5, bold = false, c = INK) { this.cur.push(`BT /${bold ? "F2" : "F1"} ${size} Tf ${col(c)} rg ${x.toFixed(1)} ${y.toFixed(1)} Td (${esc(s)}) Tj ET`); }
  rect(x: number, y: number, w: number, h: number, fill: [number, number, number], stroke?: [number, number, number]) {
    this.cur.push(`${col(fill)} rg ${x.toFixed(1)} ${y.toFixed(1)} ${w.toFixed(1)} ${h.toFixed(1)} re f`);
    if (stroke) this.cur.push(`${col(stroke)} RG 0.8 w ${x.toFixed(1)} ${y.toFixed(1)} ${w.toFixed(1)} ${h.toFixed(1)} re S`);
  }
  rule(y: number, c: [number, number, number] = [0.85, 0.86, 0.88]) { this.cur.push(`${col(c)} RG 0.6 w ${M} ${y.toFixed(1)} m ${W - M} ${y.toFixed(1)} l S`); }
  heading(s: string) { this.need(40); this.y -= 14; this.text(M, this.y, s.toUpperCase(), 9.5, true, MUTED); this.y -= 6; this.rule(this.y); this.y -= 14; }
  para(s: string, size = 10.5, c = INK, bold = false, x = M, width = W - 2 * M) {
    for (const line of wrap(s, size, width, bold)) { this.need(size + 6); this.text(x, this.y, line, size, bold, c); this.y -= size + 5; }
  }
  image(e: Evidence, x: number, y: number, w: number, h: number) {
    const name = `Im${this.images.length + 1}`;
    this.images.push({ name, jpeg: e.jpeg, w: e.w, h: e.h });
    this.cur.push(`q ${w.toFixed(1)} 0 0 ${h.toFixed(1)} ${x.toFixed(1)} ${y.toFixed(1)} cm /${name} Do Q`);
  }
}

export function makeReport(r: Report): Blob {
  const d = new Doc();
  const tone = r.held ? AMBER : GREEN;

  d.rect(0, H - 92, W, 92, GREEN);
  d.text(M, H - 48, "Relayloom", 24, true, [1, 1, 1]);
  d.text(M, H - 68, r.title, 11, false, [0.82, 0.95, 0.88]);
  d.text(W - M - 130, H - 48, new Date().toISOString().slice(0, 10), 11, false, [1, 1, 1]);
  d.y = H - 92 - 28;

  const reasonLines = r.reasons.flatMap((x) => wrap(x, 10, W - 2 * M - 40));
  const boxH = 74 + reasonLines.length * 15;
  d.need(boxH);
  d.rect(M, d.y - boxH + 8, W - 2 * M, boxH, r.held ? [1, 0.96, 0.84] : [0.89, 0.97, 0.92], tone);
  d.rect(M, d.y - boxH + 8, 6, boxH, tone);
  d.text(M + 20, d.y - 12, r.held ? "HELD FOR A PERSON" : "CLEAR TO ENTER", 10, true, tone);
  let yy = d.y - 34;
  for (const l of wrap(r.headline, 15, W - 2 * M - 40, true)) { d.text(M + 20, yy, l, 15, true); yy -= 19; }
  yy -= 2;
  for (const reason of r.reasons) {
    const ls = wrap(reason, 10, W - 2 * M - 52);
    ls.forEach((l, i) => d.text(M + (i ? 32 : 20) + (i ? 0 : 0), yy - i * 14, (i ? "" : "- ") + l, 10));
    yy -= ls.length * 14 + 1;
  }
  d.y -= boxH + 8;

  d.heading("The delivery");
  for (let i = 0; i < r.facts.length; i += 2) {
    d.need(30);
    for (let k = 0; k < 2; k++) {
      const f = r.facts[i + k];
      if (!f) continue;
      const x = M + k * ((W - 2 * M) / 2);
      d.text(x, d.y, f[0], 8.5, false, MUTED);
      d.text(x, d.y - 13, f[1], 11, true);
    }
    d.y -= 32;
  }

  d.heading("Items");
  const cols = [M, M + 250, M + 322, M + 394];
  d.need(24);
  d.rect(M, d.y - 6, W - 2 * M, 20, [0.94, 0.95, 0.96]);
  ["Item", "Ordered", "Billed", "Good on arrival"].forEach((h, i) => d.text(cols[i]! + 4, d.y, h, 8.5, true, MUTED));
  d.y -= 22;
  for (const it of r.items) {
    const noteLines = it.note ? wrap(it.note, 9.5, W - 2 * M - 8) : [];
    const nameLines = wrap(it.item, 10.5, 240);
    d.need(nameLines.length * 14 + noteLines.length * 13 + 16);
    nameLines.forEach((l, i) => d.text(cols[0]! + 4, d.y - i * 14, l, 10.5, true));
    d.text(cols[1]! + 4, d.y, String(it.ordered), 10.5);
    d.text(cols[2]! + 4, d.y, String(it.billed), 10.5);
    d.text(cols[3]! + 4, d.y, String(it.good), 10.5, true, it.note ? AMBER : GREEN);
    d.y -= nameLines.length * 14 + 2;
    noteLines.forEach((l) => { d.text(cols[0]! + 4, d.y, l, 9.5, false, AMBER); d.y -= 13; });
    d.y -= 4;
    d.rule(d.y + 2);
    d.y -= 8;
  }

  d.heading("Amounts");
  for (const [k, v] of r.totals) {
    d.need(18);
    d.text(M, d.y, k, 10.5, false, MUTED);
    d.text(W - M - textWidth(v, 11, true), d.y, v, 11, true);
    d.y -= 18;
  }

  if (r.evidence.length) {
    d.need(270);
    d.heading("Photo evidence");
    const cw = (W - 2 * M - 16) / 2;
    for (let i = 0; i < r.evidence.length; i += 2) {
      const pair = r.evidence.slice(i, i + 2);
      const hs = pair.map((e) => Math.min(cw * (e.h / e.w), 190));
      const rowH = Math.max(...hs) + 34;
      d.need(rowH);
      pair.forEach((e, k) => {
        const w = Math.min(cw, hs[k]! * (e.w / e.h));
        const x = M + k * (cw + 16);
        d.image(e, x, d.y - hs[k]!, w, hs[k]!);
        d.text(x, d.y - hs[k]! - 13, e.label, 9.5, true);
        d.text(x, d.y - hs[k]! - 26, e.caption, 8.5, false, MUTED);
      });
      d.y -= rowH;
    }
  }

  d.heading("What happened, step by step");
  r.steps.forEach((s, i) => { d.need(18); d.text(M, d.y, `${i + 1}.`, 10.5, true, GREEN); d.para(s, 10.5, INK, false, M + 20, W - 2 * M - 20); d.y -= 3; });

  d.heading("Proof");
  if (r.verified === true) d.para("Every step is signed and linked to the one before it. The signatures and the chain were checked and are intact.", 10.5, GREEN, true);
  else if (r.verified === false) d.para("Warning: the signatures or the chain did not check out. Do not rely on this receipt.", 10.5, AMBER, true);
  for (const p of r.proof) d.para(p, 9, MUTED);

  // assemble the file
  const chunks: Uint8Array[] = [];
  let len = 0;
  const push = (b: Uint8Array | string) => { const u = typeof b === "string" ? bytesOf(b) : b; chunks.push(u); len += u.length; };
  const offsets: number[] = [];
  const obj = (n: number, parts: (Uint8Array | string)[]) => { offsets[n] = len; push(`${n} 0 obj\n`); parts.forEach(push); push("\nendobj\n"); };
  const nP = d.pages.length;
  const imgBase = 6 + nP * 2;
  push("%PDF-1.4\n");
  obj(1, ["<< /Type /Catalog /Pages 2 0 R >>"]);
  obj(2, [`<< /Type /Pages /Kids [${d.pages.map((_, i) => `${6 + i * 2} 0 R`).join(" ")}] /Count ${nP} >>`]);
  obj(3, ["<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"]);
  obj(4, ["<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"]);
  obj(5, ["<< >>"]);
  const xobj = d.images.map((im, i) => `/${im.name} ${imgBase + i} 0 R`).join(" ");
  d.pages.forEach((ops, i) => {
    const footer = `BT /F1 8 Tf ${col(MUTED)} rg ${M} 28 Td (Relayloom  |  signed receipts, checked offline with: relayloom verify  |  page ${i + 1} of ${nP}) Tj ET`;
    const content = ops.join("\n") + "\n" + footer;
    obj(5 + i * 2 + 1, [`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${W} ${H}] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> /XObject << ${xobj} >> >> /Contents ${5 + i * 2 + 2} 0 R >>`]);
    obj(5 + i * 2 + 2, [`<< /Length ${content.length} >>\nstream\n`, content, "\nendstream"]);
  });
  d.images.forEach((im, i) => obj(imgBase + i, [`<< /Type /XObject /Subtype /Image /Width ${im.w} /Height ${im.h} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${im.jpeg.length} >>\nstream\n`, im.jpeg, "\nendstream"]));
  const total = imgBase + d.images.length;
  const xref = len;
  push(`xref\n0 ${total}\n0000000000 65535 f \n`);
  for (let n = 1; n < total; n++) push(`${String(offsets[n] ?? 0).padStart(10, "0")} 00000 n \n`);
  push(`trailer\n<< /Size ${total} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`);
  const out = new Uint8Array(len);
  let p = 0;
  for (const c of chunks) { out.set(c, p); p += c.length; }
  return new Blob([out], { type: "application/pdf" });
}

export function savePdf(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 2000);
}
