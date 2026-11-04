"""A plain-language receipt as a PDF, made offline from a signed receipt file.

The PDF writer is small on purpose: text only, Helvetica, A4, no dependencies, so it runs on a disconnected machine.
"""
from __future__ import annotations

import json
from pathlib import Path
import textwrap

STEP_WORDS = {
    "intake": "Bill received", "mask": "Private numbers masked", "read": "Bill read", "injection_check": "Hidden text checked and ignored", "count": "Goods counted", "condition": "Condition of the goods checked",
    "match": "Order, bill and goods compared", "investigate": "Evidence reviewed", "diagnose": "Likely cause named", "propose": "Next step proposed",
    "draft": "Supplier message drafted", "enter": "Bill entered in the books", "check": "Entry read back and checked", "file": "Case filed", "decision": "Owner decision",
    "send": "Message sent", "close": "Case closed", "reconcile": "Books reconciled after reconnecting", "dispute": "Dispute prepared", "hold": "Held for a person",
}


def _latin(text: str) -> str:
    text = str(text).replace("₹", "Rs ").replace("–", "-").replace("—", "-").replace("’", "'").replace("“", '"').replace("”", '"')
    return text.encode("latin-1", "replace").decode("latin-1")


def _escape(text: str) -> str:
    return _latin(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_pdf(lines: list[tuple[str, str]]) -> bytes:
    """lines: (style, text) with style 'title', 'head', 'body' or 'small'. Returns the bytes of a PDF."""
    sizes = {"title": (20, 28), "head": (12.5, 20), "body": (10.5, 15), "small": (8.5, 12)}
    pages, page, y = [], [], 800.0
    for style, text in lines:
        size, lead = sizes[style]
        width = {"title": 52, "head": 78, "body": 92, "small": 112}[style]
        for chunk in (textwrap.wrap(text, width) or [""]):
            if y - lead < 56:
                pages.append(page)
                page, y = [], 800.0
            y -= lead
            page.append((style, size, y, chunk))
    pages.append(page)
    objs: list[bytes] = [b"", b"", b"", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
                         b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"]
    kids = []
    for page in pages:
        ops = []
        for style, size, yy, chunk in page:
            font = "F2" if style in ("title", "head") else "F1"
            grey = "0.4 0.4 0.4 rg" if style == "small" else "0 0 0 rg"
            ops.append(f"BT /{font} {size} Tf {grey} 56 {yy:.1f} Td ({_escape(chunk)}) Tj ET")
        stream = "\n".join(ops).encode("latin-1")
        objs.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
        content_id = len(objs)
        objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents {content_id} 0 R >>".encode())
        kids.append(len(objs))
    objs[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objs[1] = ("<< /Type /Pages /Kids [" + " ".join(f"{k} 0 R" for k in kids) + f"] /Count {len(kids)} >>").encode()
    objs[2] = b"<< >>"
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


def _money(value) -> str:
    try:
        return "Rs {:,.2f}".format(float(value))
    except (TypeError, ValueError):
        return str(value)


def _facts(body: dict) -> str:
    detail = body.get("detail") or {}
    bill = detail.get("bill") or {}
    if bill and bill.get("bill_no"):
        lines = "; ".join(f"{l.get('qty'):g} x {l.get('description')} at {_money(l.get('rate_inr'))}" for l in bill.get("lines", []))
        return f"Supplier {bill.get('supplier_id')}, bill {bill.get('bill_no')}, total {_money(bill.get('total_inr'))}. {lines}"
    for key in ("reason", "summary", "message", "note"):
        if isinstance(detail.get(key), str):
            return detail[key]
    counted = detail.get("counted", detail.get("count"))
    if counted is not None:
        return f"Counted {counted}"
    return ""


def receipt_lines(receipts: list[dict], verified: bool | None, case: str | None = None) -> list[tuple[str, str]]:
    bodies = [r["body"] for r in receipts if case in (None, r["body"].get("case"))]
    out: list[tuple[str, str]] = [("title", "Relayloom receipt"), ("small", "What the agents did, in order, with the proof that nothing was changed afterwards.")]
    if not bodies:
        return out + [("body", "No steps were found for this case.")]
    out.append(("head", f"{len(bodies)} steps, in the order they happened"))
    if verified is True:
        out.append(("body", "Proof: every step is signed and linked to the one before it. The signatures and the chain were checked on this machine and are intact."))
    elif verified is False:
        out.append(("body", "Warning: the signatures or the chain did not check out. Do not rely on this receipt."))
    else:
        out.append(("body", "Proof: run relayloom verify with the public key to check every signature and link."))
    for b in bodies:
        title = STEP_WORDS.get(b.get("step", ""), str(b.get("step", "")).replace("_", " ").capitalize())
        out.append(("head", f"{b.get('seq')}. {title} by {b.get('agent')}"))
        out.append(("small", str(b.get("time", ""))))
        if b.get("decision"):
            out.append(("body", f"Result: {b['decision']}"))
        facts = _facts(b)
        if facts:
            out.append(("body", facts))
        if b.get("approver"):
            out.append(("body", f"Approved by {b['approver']}"))
        if b.get("model"):
            out.append(("small", f"Model used: {b['model']} {b.get('route', '')}".strip()))
    last = receipts[-1]
    out.append(("small", f"Fingerprint of the last step: {last.get('hash', '')}"))
    return out


def write_receipt_pdf(receipts_path: str | Path, out_path: str | Path, case: str | None = None, public_key_b64: str | None = None) -> dict:
    receipts = [json.loads(l) for l in Path(receipts_path).read_text(encoding="utf-8").splitlines() if l.strip()]
    verified = None
    if public_key_b64:
        from relayloom.ap.receipts import verify

        verified, _ = verify(receipts, public_key_b64)
    data = make_pdf(receipt_lines(receipts, verified, case))
    Path(out_path).write_bytes(data)
    return {"steps": len([r for r in receipts if case in (None, r["body"].get("case"))]), "verified": verified, "bytes": len(data)}
