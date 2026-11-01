"""Count instances of one text prompt with SAM 3.1 (Ultralytics) and draw numbered masks.

Usage: python -I sam_worker.py WEIGHTS PHOTO PROMPT OVERLAY_OUT. Prints one JSON line.
Runs in its own Python so torch and the weights stay out of the main app.
"""
import json
import sys
import time


def main():
    weights, photo, prompt, overlay = sys.argv[1:5]
    import cv2
    import numpy as np
    import torch
    from ultralytics.models.sam import SAM3SemanticPredictor

    started = time.perf_counter()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    predictor = SAM3SemanticPredictor(overrides=dict(conf=float(__import__("os").environ.get("SAM_CONF", "0.4")), task="segment", mode="predict", model=weights,
                                                     device=device, half=False, save=False, verbose=False))
    loaded = time.perf_counter()
    predictor.set_image(photo)
    results = predictor(text=[prompt])
    inferred = time.perf_counter()
    result = results[0]
    masks = result.masks.data.cpu().numpy() if result.masks is not None else np.zeros((0, 1, 1))
    scores = result.boxes.conf.cpu().numpy().tolist() if result.boxes is not None else []
    image = cv2.imread(photo)
    height, width = image.shape[:2]
    colour = np.array([60, 200, 120], dtype=np.uint8)
    for index, mask in enumerate(masks, start=1):
        if mask.shape != (height, width):
            mask = cv2.resize(mask.astype(np.uint8), (width, height), interpolation=cv2.INTER_NEAREST)
        region = mask.astype(bool)
        image[region] = (image[region] * 0.45 + colour * 0.55).astype(np.uint8)
        contours, _ = cv2.findContours(region.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(image, contours, -1, (255, 255, 255), 2)
        ys, xs = np.nonzero(region)
        if len(xs):
            x, y = int(xs.mean()), int(ys.mean())
            cv2.putText(image, str(index), (x - 10, y + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4, cv2.LINE_AA)
            cv2.putText(image, str(index), (x - 10, y + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.imwrite(overlay, image, [cv2.IMWRITE_JPEG_QUALITY, 85])
    print(json.dumps({"count": int(len(masks)), "prompt": prompt, "model": weights.replace("\\", "/").split("/")[-1],
                      "device": device, "load_seconds": round(loaded - started, 1),
                      "infer_seconds": round(inferred - loaded, 1), "scores": [round(s, 3) for s in scores],
                      "image_size": [width, height]}))


if __name__ == "__main__":
    main()
