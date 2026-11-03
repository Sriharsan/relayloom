# Sources

Primary sources only. The three about payments and controls are quoted from the pages themselves and are not used
for any customer, revenue, savings or industry percentage, and the project makes no such claim. Every number in the README and on the site comes from our own
runs, listed in [RESULTS.md](RESULTS.md).

| Used for | Source | Read |
| --- | --- | --- |
| Hackathon rules, judging, building period, themes, prizes | Official participant guide, https://cerebralvalley.ai/e/meta-ai-developer-hackathon/details | 30 Oct and 3 Nov 2026 |
| Muse Glimmer 30B: license, files, runtime flags, llama.cpp build needed | Model card, https://huggingface.co/meta-models/Muse-Glimmer-30B-GGUF (Apache 2.0, not gated) | 31 Oct 2026 |
| llama.cpp runtime | https://github.com/ggml-org/llama.cpp release b12020 (MIT) | 31 Oct 2026 |
| SAM 3.1 weights | https://huggingface.co/facebook/sam3.1 (gated, access granted to the founder's account under the SAM license) | 1 Nov 2026 |
| Running SAM 3.1 | Ultralytics 8.4 `SAM3SemanticPredictor` (AGPL-3.0), https://github.com/ultralytics/ultralytics | 1 Nov 2026 |
| Accounting software | ERPNext v16 (GPL-3.0) from https://github.com/frappe/frappe_docker `pwd.yml` | 31 Oct 2026 |
| Browser agent | Playwright for Python (Apache 2.0) | 31 Oct 2026 |
| Paying for goods not received is an improper payment | 31 U.S.C. § 3351(4) defines an improper payment to include "any payment for a good or service not received, except for those where authorized by law". https://www.law.cornell.edu/uscode/text/31/3351 (United States federal agencies) | 3 Nov 2026 |
| Invoices approved without proof of receipt | GAO-06-547, Department of Energy, published 31 May 2006: because the agency lacked an effective review and approval process for contractor invoices, "it had no assurance that goods and services billed had actually been received". https://www.gao.gov/products/gao-06-547 | 3 Nov 2026 |
| Controls reduce fraud losses | ACFE, Occupational Fraud 2026: A Report to the Nations (14th edition, 2,402 cases, 143 countries): "the presence of anti-fraud controls is associated with lower fraud losses and quicker fraud detection". https://www.acfe.com/fraud-resources/report-to-the-nations | 3 Nov 2026 |
| Structured output and reasoning effort for Muse Glimmer | Official Meta open-weight cookbook, https://github.com/meta-models/meta-oss-cookbook (Apache-2.0), recipes `muse-glimmer/recipes/structured-output` and `reasoning-effort`. The Reader sends a strict JSON schema so the server constrains decoding, and uses low reasoning effort. | 3 Nov 2026 |
| Computer use with Muse Glimmer (roadmap for the Disputer) | `muse-glimmer/recipes/computer-use-web` in the same cookbook. The Disputer's browser steps are code today. Choosing steps from screenshots with Muse Glimmer is the roadmap, and suits GPU class hardware. | 3 Nov 2026 |
| Signatures | `cryptography` Ed25519 (Apache 2.0 / BSD) in Python, WebCrypto Ed25519 in the browser | |

Reused material and licenses: the SAM license applies to the SAM 3.1 weights, which are not
redistributed here. Muse Glimmer and its GGUF files are not redistributed here either; recorded
outputs of these models are included with their route, date and timings.
