// Copies the real SAM 3.1 overlays and the delivery photos the site shows into public/img.
import { copyFileSync, existsSync, mkdirSync, readFileSync } from "node:fs";

const root = new URL("../", import.meta.url);
const out = new URL("./public/img/", import.meta.url);
mkdirSync(out, { recursive: true });

const measured = JSON.parse(readFileSync(new URL("./src/data/measured.json", import.meta.url)));
for (const run of measured.sam) {
  const src = new URL(`fixtures/recorded/sam/${run.overlay}`, root);
  if (existsSync(src)) copyFileSync(src, new URL(run.overlay, out));
}

const bench = JSON.parse(readFileSync(new URL("./src/data/bench.json", import.meta.url)));
for (const c of bench.cases) {
  for (const event of c.counter?.events ?? []) {
    for (const photo of event.photos) {
      const src = new URL(`fixtures/photos/${photo.photo}.jpg`, root);
      if (existsSync(src)) copyFileSync(src, new URL(`${photo.photo}.jpg`, out));
    }
  }
}
console.log("images copied");
