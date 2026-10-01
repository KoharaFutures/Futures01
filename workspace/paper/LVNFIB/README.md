# LVN/FIB AGENT

Paper desk on **MGC** and **MNQ**. Read `CHARTER.md` first — it states every rule, and the gate
that decides which of them may risk the account.

```bash
bash workspace/paper/LVNFIB/desk.sh            # the gated turn: 0 quiet / 10 attention / 2 data failure
bash workspace/paper/LVNFIB/desk.sh --manual   # plan, resolve and full status, for a human
python3 workspace/paper/LVNFIB/selftest.py     # prove the live logic == the backtested logic
```

## How it is scheduled

`desk_check.py` is the mechanical turn and it decides whether anyone needs waking, following
`DATA_HUB/AUTOMATION.md`: the script does the repeating work every cycle, an LLM is woken only
when a pre-registered trigger actually fires.

| exit | meaning | the routine should |
|---|---|---|
| **0** | quiet, inside an entry window — no trigger armed, nothing resolved | say nothing at all |
| **3** | dormant — no window open, nothing waiting to resolve | sleep 10 min |
| **10** | an armed trigger, a resolved trade, a size refusal, a drawdown alert, or a failed fetch | report, and use judgment |
| **2** | the desk could not form a view | report the failure |

Arm A fires roughly **1.4 times a month**, so almost every cycle is a 0 and must cost nothing.
Every cycle appends one line to `desk_events.jsonl` whether it wakes anyone or not.

| file | what it is |
|---|---|
| `CHARTER.md` | the rules, the arm/observe gate, the inherited risk rules, the known limits |
| `engine.py` | today's levels for each arm, stamped with the bar they came from |
| `plan.py` | callouts: trigger, limit, stop, target, sizing, budget refusals |
| `resolve.py` | resolves fills through the same engine that measured each prior |
| `status.py` | account state and each arm's running record next to its measured prior |
| `desk_check.py` | the gated mechanical turn; exit 0/3/10/2 decides whether to wake an LLM |
| `desk_loop.sh` | runs the check every 2 min, exits only when a decision is needed |
| `desk_events.jsonl` | one line per cycle, woken or not |
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

## Running it continuously

```bash
bash workspace/paper/LVNFIB/desk_loop.sh        # every 2 minutes; exits only when a decision is needed
bash workspace/paper/LVNFIB/desk_loop.sh 300    # a slower cadence
```

The loop runs `desk_check.py` every 120 s and **exits** on 10 (attention) or 2 (three consecutive
failures), so the agent that launched it in the background is woken for judgment and never for a
routine check. On exit 3 (dormant — no entry window open and nothing waiting to resolve) it sleeps
10 minutes at a time, so it is safe to leave running across the 15:30–18:00 break and the weekend.

The loop lives inside a session and dies when the worker restarts, which is why the hourly routine
is a **backstop**: it checks whether the loop is alive and restarts it if not.

**What the 2-minute cadence does and does not buy:** arm A's trigger needs a 60m bar to *close*,
so a new trigger can only appear once an hour. The fast cadence catches a resting limit's fill, the
newest bar settling after revision, and drawdown or budget changes. It cannot find a trigger that
does not exist yet. The feed is throttled to 300 s separately — see `CHARTER.md` §4.

## Before you believe any price it prints

The feed is live as of 2026-10-01. But Yahoo lags a median **13 min at 5m** and ~23 min at 15m, and
the **newest 1–2 bars revise for ~28 min** — so a level touched on an unsettled bar is not touched.
Every level the engine emits carries its source bar's timestamp; quote it.
