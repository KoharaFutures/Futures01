# LVN/FIB AGENT

Paper desk on **MGC** and **MNQ**. Read `CHARTER.md` first — it states every rule, and the gate
that decides which of them may risk the account.

```bash
bash workspace/paper/LVNFIB/desk.sh            # plan (dry run), resolve, status
bash workspace/paper/LVNFIB/desk.sh --post     # also post the new callouts
python3 workspace/paper/LVNFIB/selftest.py     # prove the live logic == the backtested logic
```

| file | what it is |
|---|---|
| `CHARTER.md` | the rules, the arm/observe gate, the inherited risk rules, the known limits |
| `engine.py` | today's levels for each arm, stamped with the bar they came from |
| `plan.py` | callouts: trigger, limit, stop, target, sizing, budget refusals |
| `resolve.py` | resolves fills through the same engine that measured each prior |
| `status.py` | account state and each arm's running record next to its measured prior |
| `selftest.py` | 4 checks: levels, triggers, the quoted priors, and the fill-bar rule |
| `callouts.jsonl` | append-only. A callout is never edited after it is posted |
| `resolutions.jsonl` | append-only outcomes |
| `state.json` | equity, peak, max drawdown, closed count |

## What this desk will and will not do

- It trades **one rule, on gold**. MNQ is instrumented, not traded: the same rule measures
  **−0.2390R (t −1.932)** there and the overnight variant is a null.
- It will be **quiet** — arm A fired 33 times in two years, about 1.4 a month, and the budget funds
  roughly 60% of those. Silence is correct behaviour.
- It **refuses trades it cannot size** and logs the refusal rather than shrinking the stop.
- It applies **no exit overlay**. Breakeven-at-0.8R was measured over ~8,000 paired trades and does
  nothing; a full exit at 0.8R is worse on 8 of 8 arms.
- **Nothing here clears its luck bar.** It is a forward test.

## Before you believe any price it prints

`yfinance` is not installed in this container, so the desk reads `data/archive/` and the newest bar
is **2026-09-30**. Run `pip install yfinance` then
`python3 DATA_HUB/tools/refresh_archive.py --fetch` to bring it current. Until then no level the
desk prints is a current price, and `status.py` says so on every run.
