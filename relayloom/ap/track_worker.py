"""Track items through a video with SAM 3.1 and print every track as JSON.

Usage: python -I track_worker.py WEIGHTS VIDEO PROMPT [--every N] [--max-frames M]
Runs in its own Python (like sam_worker.py) so torch stays out of the main app. Each item SAM follows keeps one id. The
output is {"fps", "frames", "size", "tracks": {id: [[frame, cx, cy], ...]}} with positions as fractions of the frame,
which relayloom.ap.crossing turns into a count. On a CPU use --every to track key frames only; on a GPU use 1.
"""
import json
import os
import sys
import time


def main():
    args = sys.argv[1:]
    weights, video, prompt = args[:3]
    every = int(args[args.index("--every") + 1]) if "--every" in args else 1
    limit = int(args[args.index("--max-frames") + 1]) if "--max-frames" in args else 0
    import cv2
    import torch
    from ultralytics.models.sam import SAM3VideoSemanticPredictor

    capture = cv2.VideoCapture(video)
    fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    width, height = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    source = video
    if every > 1 or limit:  # key frames only: write a thinner video so the tracker sees fewer frames
        thin = video + ".keyframes.mp4"
        writer = cv2.VideoWriter(thin, cv2.VideoWriter_fourcc(*"mp4v"), max(fps / every, 1.0), (width, height))
        index = kept = 0
        while True:
            ok, frame = capture.read()
            if not ok or (limit and kept >= limit):
                break
            if index % every == 0:
                writer.write(frame)
                kept += 1
            index += 1
        writer.release()
        source = thin
    capture.release()

    started = time.perf_counter()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    predictor = SAM3VideoSemanticPredictor(overrides=dict(conf=float(os.environ.get("SAM_CONF", "0.4")), task="segment", mode="predict",
                                                          model=weights, device=device, half=device == "cuda", save=False, verbose=False))
    tracks: dict[str, list] = {}
    frames = 0
    for number, result in enumerate(predictor(source=source, text=[prompt], stream=True)):
        frames += 1
        boxes = result.boxes
        if boxes is None or boxes.id is None:
            continue
        for track_id, (x1, y1, x2, y2) in zip(boxes.id.int().tolist(), boxes.xyxy.tolist()):
            tracks.setdefault(str(track_id), []).append([number * every, round((x1 + x2) / 2 / width, 4), round((y1 + y2) / 2 / height, 4)])
    print(json.dumps({"fps": fps, "frames": frames, "source_frames": total, "every": every, "size": [width, height], "prompt": prompt,
                      "device": device, "seconds": round(time.perf_counter() - started, 1), "tracks": tracks}))


if __name__ == "__main__":
    main()
