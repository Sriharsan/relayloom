"""The receiving log: what the dock photographed, counted by SAM 3.1, with duplicate photos removed.

A delivery can have several photos (different crates or angles). A purchase order can have several receiving
events. Goods received for an order are the sum over its events, not the count in one photo.
"""
from __future__ import annotations

from pathlib import Path

import cv2

SAME_SCENE = 0.95  # normalized correlation after alignment; resaved or slightly cropped copies score above 0.99,
# different photos of similar stacks stayed below 0.76 on every pair in our fixtures
MARGIN = 14


def similarity(path_a: Path, path_b: Path) -> float:
    """Best normalized correlation of photo A's centre inside photo B, so a small crop or shift still matches."""
    a, b = cv2.imread(str(path_a), 0), cv2.imread(str(path_b), 0)
    if a is None or b is None or abs(a.shape[0] - b.shape[0]) > 0.04 * a.shape[0] or abs(a.shape[1] - b.shape[1]) > 0.04 * a.shape[1]:
        return 0.0
    template = a[MARGIN:a.shape[0] - MARGIN, MARGIN:a.shape[1] - MARGIN]
    if b.shape[0] < template.shape[0] or b.shape[1] < template.shape[1]:
        template = cv2.resize(template, (b.shape[1] - 2, b.shape[0] - 2))
    return float(cv2.matchTemplate(b, template, cv2.TM_CCOEFF_NORMED).max())


class Receiving:
    def __init__(self, world: dict, counter, fixtures: Path):
        self.world, self.counter, self.fixtures = world, counter, Path(fixtures)
        self.events = {e["id"]: e for e in world["receiving_events"]}
        self.items = world["items"]
        self.cache: dict[str, dict] = {}

    def add_event(self, event: dict):
        """Register a receiving event made at run time, such as the key frames of a dock video."""
        self.world["receiving_events"].append(event)
        self.events[event["id"]] = event
        self.cache.pop(event["id"], None)

    def events_for_po(self, po_number: str) -> list[dict]:
        return sorted((e for e in self.world["receiving_events"] if e["po_number"] == po_number), key=lambda e: e["date"])

    def count_photo(self, photo: dict, item_code: str, alternate: bool = False) -> dict:
        prompt = self.items[item_code]["alt_prompt" if alternate else "prompt"]
        result = self.counter.count(self.fixtures / photo["file"], prompt, photo["id"])
        return {"photo": photo["id"], "prompt": prompt, "count": result["count"], "model": result.get("model", "SAM 3.1"),
                "route": result["route"], "seconds": result.get("infer_seconds"), "overlay": result.get("overlay", ""),
                "recorded": result.get("recorded", False), "trace": result.get("trace", [])}

    def count_event(self, event_id: str) -> dict:
        """Count every unique photo of one receiving event. Duplicate photos are listed and not counted."""
        if event_id in self.cache:
            return self.cache[event_id]
        event = self.events[event_id]
        kept, rows = [], []
        for photo in event["photos"]:
            twin = next(((k, score) for k in kept if (score := similarity(self.fixtures / k["file"], self.fixtures / photo["file"])) >= SAME_SCENE), None)
            if twin:
                rows.append({"photo": photo["id"], "duplicate_of": twin[0]["id"], "count": 0, "counted": False,
                             "similarity": round(twin[1], 3)})
                continue
            kept.append(photo)
            counted = self.count_photo(photo, event["item_code"])
            rows.append({**counted, "counted": True})
        result = {"event_id": event_id, "po_number": event["po_number"], "item_code": event["item_code"],
                  "date": event["date"], "photos": rows, "total": sum(r["count"] for r in rows if r["counted"]),
                  "unique_photos": sum(1 for r in rows if r["counted"]),
                  "duplicate_photos": sum(1 for r in rows if not r["counted"]),
                  "seconds": round(sum(r.get("seconds") or 0 for r in rows), 1)}
        self.cache[event_id] = result
        return result

    def recount_event(self, event_id: str) -> dict:
        """Independent recount of every unique photo with a second wording of the prompt."""
        first = self.count_event(event_id)
        event = self.events[event_id]
        photos = {p["id"]: p for p in event["photos"]}
        rows = []
        for row in first["photos"]:
            if not row["counted"]:
                continue
            again = self.count_photo(photos[row["photo"]], event["item_code"], alternate=True)
            rows.append({"photo": row["photo"], "first": row["count"], "second": again["count"], "prompt": again["prompt"],
                         "agree": again["count"] == row["count"], "seconds": again.get("seconds")})
        return {"event_id": event_id, "photos": rows, "total_second": sum(r["second"] for r in rows),
                "agree": all(r["agree"] for r in rows)}

    def received_for_po(self, po_number: str) -> dict:
        events = [self.count_event(e["id"]) for e in self.events_for_po(po_number)]
        return {"po_number": po_number, "events": events, "total": sum(e["total"] for e in events),
                "seconds": round(sum(e["seconds"] for e in events), 1)}
