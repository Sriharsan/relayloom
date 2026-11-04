"""English, Tamil and Hindi for the phone alerts and the approval screen.

strings.json is made by scripts/make_strings.py and is read by this module, by the phone page and by the approval screen, so
all three show the same words. A string is a template such as "{bill} needs you". A parameter named like cause_key is looked
up as a string key and replaces the parameter cause, so a cause label is translated too. Anything else in a parameter
(a bill number, a count, text made by the matcher) is shown as it is.
"""
from __future__ import annotations

import json
from pathlib import Path
import re

PATH = Path(__file__).with_name("strings.json")
_DATA = json.loads(PATH.read_text(encoding="utf-8"))
LANGUAGES: dict[str, str] = _DATA["languages"]
STRINGS: dict[str, dict] = _DATA["strings"]


class _Keep(dict):
    def __missing__(self, key):  # a missing parameter stays visible instead of raising
        return "{" + key + "}"


def t(key: str, lang: str = "en", **params) -> str:
    entry = STRINGS.get(key)
    if entry is None:
        return key
    template = entry.get(lang) or entry["en"]
    values = {k: v for k, v in params.items() if not k.endswith("_key")}
    for name, value in params.items():
        if name.endswith("_key"):
            values[name[:-4]] = t(value, lang)
    return template.format_map(_Keep(values))


def placeholders(text: str) -> set[str]:
    return set(re.findall(r"\{(\w+)\}", text))


def alert(kind: str, key: str, **params) -> dict:
    """An alert in English plus the key and parameters, so the phone can show it in the person's language."""
    return {"kind": kind, "key": key, "params": {k: (v if isinstance(v, (int, float)) else str(v)) for k, v in params.items()},
            "title": t(key + ".title", "en", **params), "body": t(key + ".body", "en", **params)}
