# Video script (2 minutes 50 seconds)

Everything recorded with this script is the **local rehearsal**: invented
records, deterministic specialist outputs written by code, zero model calls.
Do not caption any part as AI output or Meta output. Live Meta inference has
not been run; if it is run later, record it as a separate clip with its own
caption and the output of `scripts/check_meta.ps1 --i-have-credit`.

Caption labels used below:

- **REHEARSAL**: invented records, deterministic outputs, no model calls.
- **LOCAL AI**: not available. Relayloom has no local model path today. Do not use this label.
- **LIVE META**: not recorded. Use only for a clip that actually called the Meta API.

## Before recording

1. Open a terminal in the repository root.
2. Run `scripts/check_demo.ps1` (or `sh scripts/check_demo.sh`). Every line must say PASS.
3. Start the workroom: `.\demo.ps1` (or `./demo.sh`). It opens http://127.0.0.1:8800.
4. Use a browser window at 1440 by 900. Keep a second browser profile ready if you
   want to show a teammate joining (optional, not in the timing below).

## Shots

| Time | Do exactly this | On screen caption |
| --- | --- | --- |
| 0:00 to 0:15 | Show the welcome page. | "Relayloom: people and AI specialists on one goal. REHEARSAL: invented records, no model calls." |
| 0:15 to 0:30 | Click **Create a workroom**. Name: `Ada`. Workroom: `Refund policy`. Goal: `Draft a fictional refund policy for the Relayloom demo store.` Click **Create workroom**. | "REHEARSAL. You are the owner." |
| 0:30 to 0:55 | Point at the Autonomy policy panel. Click **Run specialists**. Watch Product and Engineering both show WORKING, Support waiting. | "Within limits: specialists run on their own. Product and Engineering in parallel. Support waits for both." |
| 0:55 to 1:15 | When all three are done, click **Change intent**. Set Refund window to `14`. Click **Save new revision**. Point at the loom: Product thread continues (kept), Engineering and Support marked to redo. | "Intent changed. Kept: work whose inputs did not change. Redo: only what the change touched." |
| 1:15 to 1:40 | Click **Run specialists**. While Engineering shows WORKING, click **Change intent**, set `21`, save. Open **Activity**. | "A late result from the old revision is refused, not published." |
| 1:40 to 1:55 | Click **Run specialists** and wait for all three to finish. Point at the loom row for Engineering: "late, refused" then "redone". | "REHEARSAL. The loom shows every revision: kept, redone, refused." |
| 1:55 to 2:10 | Point at **Approval and proof**: Decision says no approval recorded. The Publish button is disabled. | "Explicit approval where it matters. No approval record, no publication." |
| 2:10 to 2:30 | Tick **Approve publication of this revision**. Click **Publish checked artifact**. | "Approval recorded: who, which action, when, which limit." |
| 2:30 to 2:45 | Point at the checks and **Verified outcome**. | "Proof after the action: the stored artifact was read back and matched its approval. This outcome passed these checks." |
| 2:45 to 2:50 | Show the terminal with `check_demo` PASS lines and the repository URL. | "Open source, MIT. Rehearsal tested. Live Meta inference not yet run." |

## Do not

- Do not say or caption that a model wrote the outputs.
- Do not show a `.env` file, an API key or the terminal environment.
- Do not claim customers, savings, speed or cost numbers.
