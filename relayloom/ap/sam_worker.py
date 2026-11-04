"""Count instances of one text prompt with SAM 3.1 (Ultralytics) and draw numbered masks.

One shot:  python -I sam_worker.py WEIGHTS PHOTO PROMPT OVERLAY_OUT   prints one JSON line.
Serving:   python -I sam_worker.py --serve WEIGHTS                    loads the model once, then reads one JSON request per
           line from stdin ({"photo", "prompt", "overlay"}) and answers one JSON line each. A photo's image features are kept,
           so a second word for the same photo costs only the text step.
Runs in its own Python so torch and the weights stay out of the main app.
"""
import json
import os
import sys
import time


class Counter:
    def __init__(self, weights: str):
        import cv2
        import numpy as np
        import torch
        from ultralytics.models.sam import SAM3SemanticPredictor

        self.cv2, self.np = cv2, np
        started = time.perf_counter()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.weights = weights
        self.predictor = SAM3SemanticPredictor(overrides=dict(conf=float(os.environ.get("SAM_CONF", "0.4")), task="segment", mode="predict", model=weights,
                                                              device=self.device, half=False, save=False, verbose=False))
        self.load_seconds = round(time.perf_counter() - started, 1)
        self.current = None  # the photo whose image features are loaded

    def count(self, photo: str, prompt: str, overlay: str) -> dict:
        cv2, np = self.cv2, self.np
        started = time.perf_counter()
        if self.current != photo:
            self.predictor.set_image(photo)
            self.current = photo
        results = self.predictor(text=[prompt])
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
        return {"count": int(len(masks)), "prompt": prompt, "model": self.weights.replace("\\", "/").split("/")[-1], "device": self.device,
                "load_seconds": self.load_seconds, "infer_seconds": round(inferred - started, 1), "scores": [round(s, 3) for s in scores],
                "image_size": [width, height]}


def main():
    if sys.argv[1] == "--serve":
        protocol, sys.stdout = sys.stdout, sys.stderr  # anything a library prints must not mix with the JSON lines
        counter = Counter(sys.argv[2])
        print(json.dumps({"ready": True, "load_seconds": counter.load_seconds, "device": counter.device}), file=protocol, flush=True)
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
                answer = counter.count(request["photo"], request["prompt"], request["overlay"])
            except Exception as error:  # one bad request never stops the worker
                answer = {"error": f"{type(error).__name__}: {error}"}
            print(json.dumps(answer), file=protocol, flush=True)
        return
    weights, photo, prompt, overlay = sys.argv[1:5]
    counter = Counter(weights)
    print(json.dumps(counter.count(photo, prompt, overlay)))


if __name__ == "__main__":
    main()
