"""Video evidence: detect a delivery on a dock camera and keep the stable key frames.

DockWatcher reads a video file or a camera stream with OpenCV. It looks only at cheap frame to frame change on a small
grayscale copy, so detection takes a few milliseconds a frame and works in real time on any laptop. The moment movement
starts it calls on_detect, which is what raises the phone alert. When the scene settles it keeps a sharp, stable frame
for each distinct view of the goods. When the dock has been quiet long enough the delivery is over and on_event receives
the key frames. Those frames are ordinary photographs from then on: SAM 3.1 counts them, repeated views are counted once,
and they add up on the purchase order like any other receiving event.

Counting is the slow step on a CPU. Detection is not, so the alert does not wait for the count.
"""
from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np

SMALL = (160, 90)


def _small(frame) -> np.ndarray:
    return cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), SMALL, interpolation=cv2.INTER_AREA).astype(np.float32)


def sharpness(frame) -> float:
    return float(cv2.Laplacian(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())


class DockWatcher:
    """motion_high starts a delivery, motion_low means the scene is steady, scene_change is how different a new key frame must be."""

    def __init__(self, motion_high: float = 6.0, motion_low: float = 1.5, scene_change: float = 5.0, settle_seconds: float = 4.0,
                 stable_seconds: float = 0.4, sample_fps: float = 5.0, max_frames: int = 8):
        self.motion_high, self.motion_low, self.scene_change = motion_high, motion_low, scene_change
        self.settle_seconds, self.stable_seconds = settle_seconds, stable_seconds
        self.sample_fps, self.max_frames = sample_fps, max_frames

    def watch(self, source, on_detect=None, on_event=None, stop=None) -> list[dict]:
        """source is a file path, a camera index or a stream address. Returns the deliveries found."""
        capture = cv2.VideoCapture(source)
        if not capture.isOpened():
            raise ValueError(f"cannot open video source {source!r}")
        fps = capture.get(cv2.CAP_PROP_FPS) or 10.0
        is_file = isinstance(source, (str, Path)) and Path(str(source)).exists()
        step = max(1, round(fps / self.sample_fps))
        started = time.monotonic()
        events, keys, previous, last_key, baseline = [], [], None, None, None
        active, first_motion, quiet_since, event_start, per_frame = False, 0.0, None, 0.0, []
        index = -1
        try:
            while not (stop and stop()):
                ok, frame = capture.read()
                if not ok:
                    break
                index += 1
                if index % step:
                    continue
                t = index / fps if is_file else time.monotonic() - started
                tick = time.perf_counter()
                small = _small(frame)
                motion = float(np.abs(small - previous).mean()) if previous is not None else 0.0
                moved_from = previous_t if previous is not None else t
                before, previous, previous_t = previous, small, t
                if not active:
                    if motion >= self.motion_high:
                        active, event_start, first_motion, keys, last_key, quiet_since = True, t, moved_from, [], None, None
                        baseline = before  # the dock as it looked just before anything moved
                        if on_detect:
                            on_detect({"detected_at_s": round(t, 2), "first_motion_s": round(first_motion, 2),
                                       "detection_lag_s": round(t - first_motion, 2)})
                    per_frame.append((time.perf_counter() - tick) * 1000)
                    continue
                if motion <= self.motion_low:
                    quiet_since = t if quiet_since is None else quiet_since
                    steady = t - quiet_since
                    distinct = ((last_key is None or float(np.abs(small - last_key).mean()) >= self.scene_change)
                                and float(np.abs(small - baseline).mean()) >= self.scene_change)  # an empty dock is not goods
                    if steady >= self.stable_seconds and distinct and len(keys) < self.max_frames:
                        keys.append({"t": round(t, 2), "frame": frame.copy(), "sharpness": round(sharpness(frame), 1)})
                        last_key = small
                    if steady >= self.settle_seconds and keys:
                        events.append(self._finish(event_start, t, keys, per_frame))
                        if on_event:
                            on_event(events[-1])
                        active, keys, quiet_since = False, [], None
                else:
                    quiet_since = None
                per_frame.append((time.perf_counter() - tick) * 1000)
            if active and keys:  # the video ended while the dock was still being worked
                events.append(self._finish(event_start, previous_t, keys, per_frame))
                if on_event:
                    on_event(events[-1])
        finally:
            capture.release()
        return events

    @staticmethod
    def _finish(start: float, end: float, keys: list[dict], per_frame: list[float]) -> dict:
        ordered = sorted(per_frame)
        return {"started_s": round(start, 2), "ended_s": round(end, 2), "frames": list(keys),
                "median_ms_per_frame": round(ordered[len(ordered) // 2], 2) if ordered else 0.0}


def save_frames(event: dict, directory: Path, prefix: str) -> list[Path]:
    """Write the key frames as JPEG photographs named PREFIX-F1.jpg, PREFIX-F2.jpg."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for number, key in enumerate(event["frames"], 1):
        path = directory / f"{prefix}-F{number}.jpg"
        cv2.imwrite(str(path), key["frame"], [cv2.IMWRITE_JPEG_QUALITY, 95])
        paths.append(path)
    return paths


def make_demo_clip(path: Path, images: list, size=(640, 480), fps: float = 8.0, hold: float = 3.0, slide: float = 1.0,
                   lead: float = 1.5, tail: float = 5.0, codec: str = "mp4v") -> Path:
    """A synthetic dock clip: an empty dock, each image slides in and holds, slides out, then the dock is empty again."""
    width, height = size
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*codec), fps, size)
    background = np.full((height, width, 3), 72, np.uint8)

    def fit(image):
        scale = min(width / image.shape[1], height / image.shape[0])
        resized = cv2.resize(image, (int(image.shape[1] * scale), int(image.shape[0] * scale)))
        canvas = background.copy()
        y, x = (height - resized.shape[0]) // 2, (width - resized.shape[1]) // 2
        canvas[y:y + resized.shape[0], x:x + resized.shape[1]] = resized
        return canvas

    def shifted(canvas, dx):
        out = background.copy()
        if dx >= 0:
            out[:, dx:] = canvas[:, :width - dx] if dx < width else out[:, dx:]
        else:
            out[:, :width + dx] = canvas[:, -dx:] if -dx < width else out[:, :width + dx]
        return out

    def hold_frames(frame, seconds):
        for _ in range(int(seconds * fps)):
            writer.write(frame)

    hold_frames(background, lead)
    for image in images:
        canvas = fit(image)
        frames = max(1, int(slide * fps))
        for i in range(frames):  # slide in from the right with an ease out
            progress = 1 - (1 - (i + 1) / frames) ** 2
            writer.write(shifted(canvas, int(width * (1 - progress))))
        hold_frames(canvas, hold)
        for i in range(frames):  # slide out to the left
            writer.write(shifted(canvas, -int(width * (i + 1) / frames)))
        hold_frames(background, 0.5)
    hold_frames(background, tail)
    writer.release()
    return Path(path)
