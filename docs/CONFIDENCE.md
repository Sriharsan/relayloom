# SAM confidence: what the setting does

SAM 3.1 returns a score for every mask. Raising the lowest score kept (`--confidence`) removes doubtful masks. The count is recomputed from the saved scores, so every row is a real model run.

## Builder's test photos (8 photos with a hand count, first word)

| Lowest score kept | Total error in items | Exact | Within 10 percent |
| --- | --- | --- | --- |
| 0.4 | 33 | 1 of 8 | 4 of 8 |
| 0.45 | 23 | 1 of 8 | 7 of 8 |
| 0.5 | 12 | 3 of 8 | 7 of 8 |
| 0.55 | 10 | 4 of 8 | 6 of 8 |
| 0.6 | 15 | 3 of 8 | 6 of 8 |
| 0.65 | 27 | 3 of 8 | 5 of 8 |
| 0.7 | 51 | 2 of 8 | 3 of 8 |

## Rendered benchmark photos (102 runs with a known count)

| Lowest score kept | Total error in items | Exact | Within 10 percent |
| --- | --- | --- | --- |
| 0.4 | 10 | 101 of 102 | 101 of 102 |
| 0.45 | 38 | 98 of 102 | 99 of 102 |
| 0.5 | 81 | 95 of 102 | 96 of 102 |
| 0.55 | 150 | 91 of 102 | 93 of 102 |
| 0.6 | 248 | 85 of 102 | 86 of 102 |
| 0.65 | 304 | 81 of 102 | 83 of 102 |
| 0.7 | 336 | 78 of 102 | 80 of 102 |

Reading it: on real photos 0.4 over-counts (doubtful masks on clutter and far items) and 0.5 to 0.55 is much closer. On the clean rendered photos 0.4 is best. No single number is best everywhere, so it is a setting. The command defaults to 0.5 because real photos are what it is for. The value was chosen on 8 photos, so treat it as a starting point and check it on your own goods.
