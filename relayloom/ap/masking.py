"""Find private numbers in bill text and replace them before anything is sent out."""
from __future__ import annotations

import hashlib
import re

# Order matters: GSTIN contains a PAN, IFSC looks like a code, long digit runs may be accounts or phones.
PATTERNS = (
    ("gstin", re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b")),
    ("ifsc", re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("phone", re.compile(r"(?<![\d])(?:\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?![\d])")),
    ("bank_account", re.compile(r"(?<![\d])\d{9,18}(?![\d])")),
)


def mask(text: str) -> tuple[str, list[dict]]:
    """Return masked text and one record per mask. Records hold a hash, never the value."""
    records = []
    for kind, pattern in PATTERNS:
        def replace(match, kind=kind):
            value = match.group(0)
            records.append({"kind": kind, "length": len(value),
                            "sha256": hashlib.sha256(value.encode()).hexdigest()[:16]})
            return f"[{kind.upper()} MASKED]"
        text = pattern.sub(replace, text)
    return text, records


def find(text: str) -> list[str]:
    """Kinds of private number still present. Used to refuse egress if masking missed one."""
    return [kind for kind, pattern in PATTERNS if pattern.search(text)]
