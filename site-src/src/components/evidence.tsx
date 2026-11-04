import { useEffect, useRef, useState } from "react";
import qrcode from "qrcode-generator";
import type { Line } from "@/lib/matcher";

type Mark = { x: number; y: number; bad: boolean };
const MAX = 1100;

/** A photo is resized in the browser and never uploaded. */
export async function fileToJpeg(file: File): Promise<string> {
  const url = URL.createObjectURL(file);
  try {
    const img = await new Promise<HTMLImageElement>((ok, no) => { const i = new Image(); i.onload = () => ok(i); i.onerror = no; i.src = url; });
    const k = Math.min(1, MAX / Math.max(img.naturalWidth, img.naturalHeight));
    const c = document.createElement("canvas");
    c.width = Math.round(img.naturalWidth * k);
    c.height = Math.round(img.naturalHeight * k);
    c.getContext("2d")!.drawImage(img, 0, 0, c.width, c.height);
    return c.toDataURL("image/jpeg", 0.86);
  } finally {
    URL.revokeObjectURL(url);
  }
}

function paint(canvas: HTMLCanvasElement, img: HTMLImageElement, marks: Mark[]) {
  const ctx = canvas.getContext("2d")!;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
  const r = Math.max(11, canvas.width / 52);
  let good = 0;
  marks.forEach((m) => {
    ctx.beginPath();
    ctx.arc(m.x * canvas.width, m.y * canvas.height, r, 0, Math.PI * 2);
    ctx.fillStyle = m.bad ? "rgba(214,130,0,0.9)" : "rgba(18,140,86,0.88)";
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = "#fff";
    ctx.stroke();
    ctx.fillStyle = "#fff";
    ctx.font = `700 ${Math.round(r * 1.05)}px Figtree, Arial, sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(m.bad ? "!" : String(++good), m.x * canvas.width, m.y * canvas.height + 1);
  });
}

/** Tap each item on the photo to count it, tap in damaged mode to mark damage. The marked photo becomes evidence in the receipt. */
export function EvidenceTool({ line, onSave, onClose }: { line: Line; onSave: (patch: Partial<Line>) => void; onClose: () => void }) {
  const [raw, setRaw] = useState<string | undefined>(line.raw);
  const [marks, setMarks] = useState<Mark[]>(line.marks ?? []);
  const [bad, setBad] = useState(false);
  const canvas = useRef<HTMLCanvasElement>(null);
  const image = useRef<HTMLImageElement | null>(null);

  useEffect(() => {
    if (!raw) return;
    const img = new Image();
    img.onload = () => {
      image.current = img;
      const c = canvas.current!;
      c.width = img.naturalWidth;
      c.height = img.naturalHeight;
      paint(c, img, marks);
    };
    img.src = raw;
  }, [raw]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { if (image.current && canvas.current) paint(canvas.current, image.current, marks); }, [marks]);

  const tap = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    setMarks([...marks, { x: (e.clientX - r.left) / r.width, y: (e.clientY - r.top) / r.height, bad }]);
  };
  const goodCount = marks.filter((m) => !m.bad).length;
  const badCount = marks.length - goodCount;
  const save = () => {
    if (!raw || !canvas.current) return;
    onSave({ raw, photo: canvas.current.toDataURL("image/jpeg", 0.88), marks, received: goodCount + badCount, damaged: badCount });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-0 sm:items-center sm:p-6" role="dialog" aria-modal="true" aria-label="Photo evidence">
      <div className="flex max-h-[96vh] w-full max-w-[860px] flex-col overflow-hidden rounded-t-3xl border border-line bg-background sm:rounded-3xl">
        <div className="flex items-center justify-between gap-3 border-b border-line px-5 py-3">
          <p className="text-[15px] font-semibold text-foreground">Photo evidence: {line.description || line.item_code || "item"}</p>
          <button type="button" onClick={onClose} className="h-9 rounded-full border border-line px-4 text-[13px] text-foreground hover:bg-raised">Close</button>
        </div>
        <div className="overflow-y-auto p-5">
          <div className="flex flex-wrap items-center gap-3">
            <label className="inline-flex h-11 cursor-pointer items-center rounded-full bg-foreground px-5 text-[13.5px] font-medium text-background">
              {raw ? "Use another photo" : "Take or choose a photo"}
              <input type="file" accept="image/*" capture="environment" className="sr-only" onChange={async (e) => { const f = e.target.files?.[0]; if (f) { setRaw(await fileToJpeg(f)); setMarks([]); } }} />
            </label>
            {raw && (
              <>
                <div role="group" aria-label="Marking mode" className="flex gap-2">
                  <button type="button" onClick={() => setBad(false)} className={`h-10 rounded-full border px-4 text-[13px] ${!bad ? "border-green bg-green/15 text-green-ink" : "border-line text-ink-muted"}`}>Count good</button>
                  <button type="button" onClick={() => setBad(true)} className={`h-10 rounded-full border px-4 text-[13px] ${bad ? "border-amber bg-amber/15 text-amber-ink" : "border-line text-ink-muted"}`}>Mark damaged</button>
                </div>
                <button type="button" onClick={() => setMarks(marks.slice(0, -1))} className="h-10 rounded-full border border-line px-4 text-[13px] text-foreground hover:bg-raised">Undo</button>
                <button type="button" onClick={() => setMarks([])} className="h-10 rounded-full border border-line px-4 text-[13px] text-ink-muted hover:text-foreground">Clear</button>
              </>
            )}
          </div>
          {raw ? (
            <>
              <p className="mt-3 text-[13px] text-ink-muted">Tap every item on the photo. Each tap adds a numbered mark. The photo stays on your device.</p>
              <canvas ref={canvas} onPointerDown={tap} className="mt-3 max-h-[58vh] w-full touch-manipulation rounded-xl border border-line object-contain" style={{ cursor: "crosshair" }} aria-label="Photo to mark" />
              <div className="mt-4 flex items-center justify-between gap-3">
                <p className="text-[15px] text-foreground"><span className="tnum font-mono text-[28px] text-green-ink">{goodCount + badCount}</span> counted, <span className="tnum font-mono text-[28px] text-amber-ink">{badCount}</span> damaged</p>
                <button type="button" onClick={save} className="h-11 rounded-full bg-foreground px-6 text-[13.5px] font-medium text-background">Keep as evidence</button>
              </div>
            </>
          ) : (
            <p className="mt-5 rounded-2xl border border-dashed border-line p-8 text-center text-[14px] text-ink-muted">On a phone this opens the camera. On a computer, choose a photo of the delivery.</p>
          )}
        </div>
      </div>
    </div>
  );
}

/** A QR code drawn as an SVG, so a phone can open the page. */
export function Qr({ text, size = 132 }: { text: string; size?: number }) {
  const q = qrcode(0, "M");
  q.addData(text);
  q.make();
  const n = q.getModuleCount();
  const cells: string[] = [];
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (q.isDark(r, c)) cells.push(`M${c} ${r}h1v1h-1z`);
  return (
    <svg viewBox={`-2 -2 ${n + 4} ${n + 4}`} width={size} height={size} role="img" aria-label={`QR code for ${text}`} shapeRendering="crispEdges">
      <rect x="-2" y="-2" width={n + 4} height={n + 4} fill="#fff" />
      <path d={cells.join("")} fill="#111" />
    </svg>
  );
}
