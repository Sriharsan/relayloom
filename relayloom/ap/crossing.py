"""Count each item once as it crosses a line on screen.

SAM 3.1 video tracking gives every item an id that stays with it from frame to frame. An item is counted the first time
its centre moves from one side of the line to the other, in the chosen direction, and never again, so an item that
jitters on the line, or is lost and found again, is not counted twice. The counter is plain code over the tracks, so
the rule is testable and the number can be checked by anyone with the track file.
"""
from __future__ import annotations


def count_crossings(tracks: dict, line: float, axis: str = "x", direction: str = "increasing", margin: float = 0.0) -> dict:
    """tracks: {id: [(frame, x, y), ...]} with positions as a fraction of the frame (0 to 1).

    A crossing needs the item to be at least `margin` before the line, then at least `margin` past it, which stops a
    jittering item from counting. direction is "increasing" (towards larger x or y), "decreasing" or "either".
    """
    index = 1 if axis == "x" else 2
    crossed, rows = [], []
    for track_id, points in sorted(tracks.items(), key=lambda kv: str(kv[0])):
        ordered = sorted(points)
        before = after = None
        for point in ordered:
            value = point[index]
            if value <= line - margin and before is None:
                before = point[0]
            if before is not None and value >= line + margin:
                after = point[0]
                break
        went_up = before is not None and after is not None
        wrong_way = False
        if direction in ("decreasing", "either"):
            low = high = None
            for point in ordered:
                value = point[index]
                if value >= line + margin and high is None:
                    high = point[0]
                if high is not None and value <= line - margin:
                    low = point[0]
                    break
            if direction == "decreasing":
                went_up, wrong_way = (high is not None and low is not None), went_up
            else:
                went_up = went_up or (high is not None and low is not None)
        row = {"id": track_id, "frames_seen": len(ordered), "crossed": bool(went_up), "against_direction": bool(wrong_way)}
        rows.append(row)
        if went_up:
            crossed.append(track_id)
    return {"count": len(crossed), "ids": crossed, "tracks": len(tracks), "rows": rows}
