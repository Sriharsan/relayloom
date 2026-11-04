"""A structured, human readable PDF receipt made offline from a signed receipt file, with optional evidence photos.

The writer is small on purpose: A4, Helvetica, JPEG photos, no network and no PDF library, so it runs on a disconnected machine.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import time

W, H, M = 595, 842, 48
GREEN, AMBER, INK, MUTED = (0.05, 0.43, 0.27), (0.62, 0.38, 0.0), (0.1, 0.1, 0.12), (0.42, 0.44, 0.48)

STEP_WORDS = {
    "intake": "Bill received", "mask": "Private numbers masked", "read": "Bill read", "injection_check": "Hidden text checked and ignored", "count": "Goods counted",
    "condition": "Condition of the goods checked", "evidence": "Photo evidence kept", "match": "Order, bill and goods compared", "investigate": "Evidence reviewed",
    "diagnose": "Likely cause named", "propose": "Next step proposed", "draft": "Supplier message drafted", "enter": "Bill entered in the books",
    "check": "Entry read back and checked", "file": "Case filed", "decision": "Owner decision", "send": "Message sent", "close": "Case closed",
    "reconcile": "Books reconciled after reconnecting", "dispute": "Dispute prepared", "hold": "Held for a person",
}


def _latin(text) -> str:
    text = str(text).replace("₹", "Rs ").replace("–", "-").replace("—", "-").replace("’", "'").replace("“", '"').replace("”", '"')
    return text.encode("latin-1", "replace").decode("latin-1")


def _esc(text) -> str:
    return _latin(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _width(text, size, bold=False) -> float:
    return len(_latin(text)) * size * (0.56 if bold else 0.52)


def _wrap(text, size, width, bold=False) -> list[str]:
    out, line = [], ""
    for word in _latin(text).split():
        nxt = f"{line} {word}".strip()
        if _width(nxt, size, bold) > width and line:
            out.append(line)
            line = word
        else:
            line = nxt
    out.append(line)
    return out


def _col(c) -> str:
    return f"{c[0]} {c[1]} {c[2]}"


def _money(value) -> str:
    try:
        return "Rs {:,.2f}".format(float(value))
    except (TypeError, ValueError):
        return str(value)


class Doc:
    def __init__(self):
        self.pages: list[list[str]] = []
        self.images: list[tuple[str, bytes, int, int]] = []
        self.y = H - M
        self.cur: list[str] = []
        self.new_page()

    def new_page(self):
        self.cur = []
        self.pages.append(self.cur)
        self.y = H - M

    def need(self, h):
        if self.y - h < M + 20:
            self.new_page()

    def text(self, x, y, s, size=10.5, bold=False, c=INK):
        self.cur.append(f"BT /{'F2' if bold else 'F1'} {size} Tf {_col(c)} rg {x:.1f} {y:.1f} Td ({_esc(s)}) Tj ET")

    def rect(self, x, y, w, h, fill, stroke=None):
        self.cur.append(f"{_col(fill)} rg {x:.1f} {y:.1f} {w:.1f} {h:.1f} re f")
        if stroke:
            self.cur.append(f"{_col(stroke)} RG 0.8 w {x:.1f} {y:.1f} {w:.1f} {h:.1f} re S")

    def rule(self, y, c=(0.85, 0.86, 0.88)):
        self.cur.append(f"{_col(c)} RG 0.6 w {M} {y:.1f} m {W - M} {y:.1f} l S")

    def heading(self, s):
        self.need(40)
        self.y -= 14
        self.text(M, self.y, s.upper(), 9.5, True, MUTED)
        self.y -= 6
        self.rule(self.y)
        self.y -= 14

    def para(self, s, size=10.5, c=INK, bold=False, x=M, width=W - 2 * M):
        for line in _wrap(s, size, width, bold):
            self.need(size + 6)
            self.text(x, self.y, line, size, bold, c)
            self.y -= size + 5

    def image(self, jpeg, w, h, x, y, dw, dh):
        name = f"Im{len(self.images) + 1}"
        self.images.append((name, jpeg, w, h))
        self.cur.append(f"q {dw:.1f} 0 0 {dh:.1f} {x:.1f} {y:.1f} cm /{name} Do Q")


def load_jpeg(path: Path, max_side=1100):
    """Read any photo and return (jpeg bytes, width, height), or None when no image library is available."""
    try:
        import cv2
    except ImportError:
        return None
    img = cv2.imread(str(path))
    if img is None:
        return None
    k = min(1.0, max_side / max(img.shape[:2]))
    if k < 1:
        img = cv2.resize(img, (int(img.shape[1] * k), int(img.shape[0] * k)))
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 86])
    return (bytes(buf), img.shape[1], img.shape[0]) if ok else None


def _summary(bodies: list[dict]) -> dict:
    s = {"bill": {}, "counts": {}, "problems": [], "decision": "", "damaged": None, "photos": []}
    for b in bodies:
        d = b.get("detail") or {}
        if b.get("step") == "read" and d.get("bill"):
            s["bill"] = d["bill"]
        elif b.get("step") == "count":
            s["counts"] = d.get("counts") or {}
        elif b.get("step") == "condition":
            s["damaged"] = b.get("decision")
        elif b.get("step") == "evidence":
            s["photos"] = d.get("photos") or []
        elif b.get("step") == "match":
            s["decision"] = b.get("decision", "")
            s["problems"] = d.get("problems") or []
    return s


def _plain_step(b: dict, s: dict) -> str:
    step, d = b.get("step", ""), b.get("detail") or {}
    bill = s["bill"]
    if step == "read" and d.get("bill"):
        lines = "; ".join(f"{l.get('qty'):g} x {l.get('description') or l.get('item_code')} at {_money(l.get('rate_inr'))}" for l in d["bill"].get("lines", []))
        return f"The bill {bill.get('bill_no')} from {bill.get('supplier_id')} was entered: {lines}."
    if step == "count":
        return "The goods were counted on arrival: " + (b.get("decision", "").replace("counted ", "") or "see the receipt") + "."
    if step == "condition":
        return d.get("reason") or f"Condition checked: {b.get('decision')}."
    if step == "evidence":
        n = len(d.get("photos") or [])
        return f"{n} photo{'s were' if n != 1 else ' was'} kept as evidence. Their fingerprints are in the signed receipt, so a photo cannot be swapped later."
    if step == "match":
        return "The order, the bill and the goods were compared and they agree within the policy limits." if "clear" in b.get("decision", "") else "The order, the bill and the goods were compared and they do not agree. The bill is held for a person."
    title = STEP_WORDS.get(step, step.replace("_", " ").capitalize())
    return f"{title}: {b.get('decision', '')}."


def build(receipts: list[dict], verified, case, evidence: list[Path]) -> bytes:
    bodies = [r["body"] for r in receipts if case in (None, r["body"].get("case"))]
    s = _summary(bodies)
    bill = s["bill"]
    held = "held" in s["decision"] and "clear" not in s["decision"]
    tone = AMBER if held else GREEN
    d = Doc()
    d.rect(0, H - 92, W, 92, GREEN)
    d.text(M, H - 48, "Relayloom", 24, True, (1, 1, 1))
    d.text(M, H - 68, "Delivery check receipt", 11, False, (0.82, 0.95, 0.88))
    d.text(W - M - 130, H - 48, time.strftime("%Y-%m-%d"), 11, False, (1, 1, 1))
    d.y = H - 92 - 28

    bill_no = bill.get("bill_no") or (bodies[0].get("case") if bodies else "")
    headline = f"{bill_no} should not be paid as it stands." if held else f"{bill_no} matches the order and the goods."
    reasons = list(s["problems"]) if held else ["Order, bill and goods agree."]
    if held and s["damaged"]:
        reasons = [f"{s['damaged']}."] + reasons
    rlines = [x for r in reasons for x in _wrap(r, 10, W - 2 * M - 52)]
    box_h = 74 + len(rlines) * 15
    d.need(box_h)
    d.rect(M, d.y - box_h + 8, W - 2 * M, box_h, (1, 0.96, 0.84) if held else (0.89, 0.97, 0.92), tone)
    d.rect(M, d.y - box_h + 8, 6, box_h, tone)
    d.text(M + 20, d.y - 12, "HELD FOR A PERSON" if held else "CLEAR TO ENTER", 10, True, tone)
    yy = d.y - 34
    for l in _wrap(headline, 15, W - 2 * M - 40, True):
        d.text(M + 20, yy, l, 15, True)
        yy -= 19
    yy -= 2
    for r in reasons:
        ls = _wrap(r, 10, W - 2 * M - 52)
        for i, l in enumerate(ls):
            d.text(M + (32 if i else 20), yy - i * 14, ("" if i else "- ") + l, 10)
        yy -= len(ls) * 14 + 1
    d.y -= box_h + 8

    d.heading("The delivery")
    facts = [("Supplier", bill.get("supplier_id", "-")), ("Bill number", bill_no or "-"), ("Order number", bill.get("po_number", "-")), ("Bill date", bill.get("bill_date", "-"))]
    for i in range(0, len(facts), 2):
        d.need(30)
        for k in range(2):
            if i + k < len(facts):
                x = M + k * ((W - 2 * M) / 2)
                d.text(x, d.y, facts[i + k][0], 8.5, False, MUTED)
                d.text(x, d.y - 13, str(facts[i + k][1]), 11, True)
        d.y -= 32

    d.heading("Items")
    cols = [M, M + 250, M + 322, M + 394]
    d.need(24)
    d.rect(M, d.y - 6, W - 2 * M, 20, (0.94, 0.95, 0.96))
    for i, h in enumerate(["Item", "Billed", "Counted", "Rate"]):
        d.text(cols[i] + 4, d.y, h, 8.5, True, MUTED)
    d.y -= 22
    for line in bill.get("lines", []):
        code = line.get("item_code")
        notes = [p.split(": ", 1)[-1] for p in s["problems"] if p.startswith(f"{code}:")]
        counted = s["counts"].get(code, "-")
        bad = re.match(r"(\d+) of (\d+) damaged", s["damaged"] or "")
        if bad and len(s["counts"]) == 1 and isinstance(counted, (int, float)):
            counted = f"{counted - int(bad.group(1)):g} good of {counted:g}"
        name_lines = _wrap(line.get("description") or code, 10.5, 240)
        note_lines = [x for n in notes for x in _wrap(n, 9.5, W - 2 * M - 8)]
        d.need(len(name_lines) * 14 + len(note_lines) * 13 + 16)
        for i, l in enumerate(name_lines):
            d.text(cols[0] + 4, d.y - i * 14, l, 10.5, True)
        d.text(cols[1] + 4, d.y, f"{line.get('qty'):g}", 10.5)
        d.text(cols[2] + 4, d.y, str(counted), 10.5, True, AMBER if notes else GREEN)
        d.text(cols[3] + 4, d.y, _money(line.get("rate_inr")), 10.5)
        d.y -= len(name_lines) * 14 + 2
        for l in note_lines:
            d.text(cols[0] + 4, d.y, l, 9.5, False, AMBER)
            d.y -= 13
        d.y -= 4
        d.rule(d.y + 2)
        d.y -= 8

    if bill:
        d.heading("Amounts")
        sub = sum(l.get("amount_inr", 0) for l in bill.get("lines", []))
        for k, v in (("Items", sub), ("Tax", bill.get("tax_inr", 0)), ("Bill total", bill.get("total_inr", 0))):
            d.need(18)
            d.text(M, d.y, k, 10.5, False, MUTED)
            val = _money(v)
            d.text(W - M - _width(val, 11, True), d.y, val, 11, True)
            d.y -= 18

    shots = [(p, load_jpeg(Path(p))) for p in evidence]
    shots = [(p, j) for p, j in shots if j]
    if shots:
        d.need(270)
        d.heading("Photo evidence")
        cw = (W - 2 * M - 16) / 2
        for i in range(0, len(shots), 2):
            pair = shots[i:i + 2]
            hs = [min(cw * (j[2] / j[1]), 190) for _, j in pair]
            row_h = max(hs) + 34
            d.need(row_h)
            for k, ((p, j), h) in enumerate(zip(pair, hs)):
                w = min(cw, h * (j[1] / j[2]))
                x = M + k * (cw + 16)
                d.image(j[0], j[1], j[2], x, d.y - h, w, h)
                d.text(x, d.y - h - 13, Path(p).name, 9.5, True)
                d.text(x, d.y - h - 26, "Evidence photo attached to this receipt", 8.5, False, MUTED)
            d.y -= row_h

    d.heading("What happened, step by step")
    for i, b in enumerate(bodies, 1):
        d.need(18)
        d.text(M, d.y, f"{i}.", 10.5, True, GREEN)
        d.para(_plain_step(b, s), 10.5, INK, False, M + 20, W - 2 * M - 20)
        d.y -= 3

    d.heading("Proof")
    if verified is True:
        d.para("Every step is signed and linked to the one before it. The signatures and the chain were checked on this machine and are intact.", 10.5, GREEN, True)
    elif verified is False:
        d.para("Warning: the signatures or the chain did not check out. Do not rely on this receipt.", 10.5, AMBER, True)
    else:
        d.para("Run relayloom verify with the public key to check every signature and link.", 10.5, MUTED)
    if receipts:
        d.para(f"Fingerprint of the last step: {receipts[-1].get('hash', '')}", 9, MUTED)
    d.para("Check it on any machine, offline: relayloom verify receipts.jsonl", 9, MUTED)
    return _assemble(d)


def _assemble(d: Doc) -> bytes:
    out = bytearray(b"%PDF-1.4\n")
    offsets: dict[int, int] = {}

    def obj(n, *parts):
        offsets[n] = len(out)
        out.extend(f"{n} 0 obj\n".encode())
        for p in parts:
            out.extend(p if isinstance(p, bytes) else p.encode("latin-1"))
        out.extend(b"\nendobj\n")

    n_pages = len(d.pages)
    img_base = 6 + n_pages * 2
    obj(1, "<< /Type /Catalog /Pages 2 0 R >>")
    obj(2, "<< /Type /Pages /Kids [" + " ".join(f"{6 + i * 2} 0 R" for i in range(n_pages)) + f"] /Count {n_pages} >>")
    obj(3, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    obj(4, "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    obj(5, "<< >>")
    xobj = " ".join(f"/{name} {img_base + i} 0 R" for i, (name, *_rest) in enumerate(d.images))
    for i, ops in enumerate(d.pages):
        footer = f"BT /F1 8 Tf {_col(MUTED)} rg {M} 28 Td (Relayloom  |  signed receipts, checked offline with: relayloom verify  |  page {i + 1} of {n_pages}) Tj ET"
        content = ("\n".join(ops) + "\n" + footer).encode("latin-1")
        obj(6 + i * 2, f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {W} {H}] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> /XObject << {xobj} >> >> /Contents {7 + i * 2} 0 R >>")
        obj(7 + i * 2, f"<< /Length {len(content)} >>\nstream\n".encode(), content, b"\nendstream")
    for i, (_name, jpeg, w, h) in enumerate(d.images):
        obj(img_base + i, f"<< /Type /XObject /Subtype /Image /Width {w} /Height {h} /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length {len(jpeg)} >>\nstream\n".encode(), jpeg, b"\nendstream")
    total = img_base + len(d.images)
    xref = len(out)
    out.extend(f"xref\n0 {total}\n0000000000 65535 f \n".encode())
    for n in range(1, total):
        out.extend(f"{offsets.get(n, 0):010d} 00000 n \n".encode())
    out.extend(f"trailer\n<< /Size {total} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(out)


def write_receipt_pdf(receipts_path, out_path, case=None, public_key_b64=None, evidence=None) -> dict:
    receipts = [json.loads(l) for l in Path(receipts_path).read_text(encoding="utf-8").splitlines() if l.strip()]
    verified = None
    if public_key_b64:
        from relayloom.ap.receipts import verify

        verified, _ = verify(receipts, public_key_b64)
    data = build(receipts, verified, case, [Path(p) for p in (evidence or [])])
    Path(out_path).write_bytes(data)
    return {"steps": len([r for r in receipts if case in (None, r["body"].get("case"))]), "verified": verified, "bytes": len(data), "photos": len(evidence or [])}
