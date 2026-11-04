# Relayloom

**Pay for what arrived. Prove it.**

Relayloom matches a supplier bill with the purchase order and with what was actually counted on the dock, holds any payment the goods do not support, and writes **signed receipts** you can verify with the network off. Muse Glimmer and SAM 3.1, open weight Meta models, run on your own machine.

The paperwork says 50. The dock got 46. `relayloom check` says HELD, and says why.

```bash
python -m pip install relayloom
relayloom doctor
```

## Try it in a minute, no models needed

`bill.json` (what the bill says), `po.json` (what was ordered), and a count of what arrived:

```bash
relayloom check --bill-json bill.json --po po.json --counted 46
relayloom verify relayloom-out/receipts.jsonl
```

```text
Bill CAL-0990: billed 50, counted 46. Result: HELD
  - CARTON-HD: billed 50 with 0 already billed, received 46
Signed receipts: relayloom-out/receipts.jsonl   Verify: relayloom verify relayloom-out/receipts.jsonl
```

Exit code `0` means clear to enter, `3` means held, `2` means it could not run. Add `--json` for scripts.

## Count the goods from photos

```bash
python -m pip install "relayloom[models]"
python -m pip install git+https://github.com/ultralytics/CLIP.git   # text prompts for SAM 3.1 (a Git-only dependency, so it is not bundled)
export HF_TOKEN=...            # your own Hugging Face read token (SAM 3.1 needs the access request)
relayloom models pull          # one time; after this everything runs offline
relayloom models serve         # Muse Glimmer on 127.0.0.1, in another terminal
relayloom check --bill bill.pdf --photos dock/ --po po.json --agent
```

With `--agent`, Muse Glimmer proposes the words to look for, calls SAM 3.1 as a tool, and looks at the numbered overlay itself. **Code owns the number**: it is only ever the masks SAM returned, and a count is accepted only when two different words agree, or when Glimmer has looked at the overlay and no other count contradicts it. Otherwise the bill is held for a person.

## What it does not do

- It does not send a bill, a photo or a number anywhere. `relayloom doctor` and `verify` make no network calls at all.
- It does not pay anything. It decides, with evidence, and a person approves what the policy says needs approval.
- It does not claim real time on a CPU. Counting a photo takes about 40 seconds and reading a bill several minutes on a laptop CPU; measured timings are on the [Proof page](https://relayloom.vercel.app/proof).

## Commands

| Command | What it does |
| --- | --- |
| `relayloom check` | match a bill, a purchase order and the goods; write signed receipts |
| `relayloom verify RECEIPTS` | check signatures, hashes and chain order offline |
| `relayloom doctor` | say what is ready and the one command that fixes what is not |
| `relayloom models pull` / `serve` | download the models with your own token / start Muse Glimmer locally |
| `relayloom serve` | the demo app and phone alerts (needs a clone of the repository) |

Docs, the policy file and the receipt format: https://relayloom.vercel.app/developers. Source and threat model: https://github.com/Sriharsan/relayloom. MIT licensed.
