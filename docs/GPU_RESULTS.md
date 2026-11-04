# Free Kaggle GPU run (two T4s), 4 November 2026, notebook version 9

Muse Glimmer 30B Q4_K_M (llama.cpp CUDA) and SAM 3.1, from commit 5e11db6. The notebook is `kaggle/relayloom-gpu.ipynb`.

| Measure | Result |
| --- | --- |
| Bill read, first call | 88.1 s (about 24 s once warm; 21.8 to 27.6 s across reasoning settings) |
| SAM 3.1 per photo once loaded | about 1 s |
| Agent loop, 12 photos with delivery records | 11 exactly right, 1 held for a person (a repeat photo), 0 wrong. The first word alone was right on 5 of 12. |
| Agent loop, 8 real photos with hand counts | 3 exact (P02, P03, P07), 2 within 3 items (P01 26 vs 25, P12 23 vs 20), 3 held for a person (P06, P10, P11) |
| Laptop CPU for comparison | a bill takes 4.5 to 8.9 minutes |

A delivery is checked in under a minute once the models are loaded. Cold start is about 90 s. A count is accepted only when two words agree or Glimmer's own look at the overlay confirms it, and everything else goes to a person.
