# Automation backlog — CALL desk

Add a line whenever the desk repeats a judgment. The trigger, the rule, and the script that should own it.

| # | idea | status |
|---|---|---|
| 1 | Pre-register stop-to-breakeven at +0.8R as an exit overlay; test on the archive with `walkforward.py` (needs an exit-overlay hook in the engine) | open |
| 2 | Pre-register a MES/MGC-only variant of OQ1 at desk-sized stops (1 ATR(60m) doesn't fit the 50% cap on MNQ/MGC) | open |
| 3 | Sweep & reclaim of prior-day / prior-RTH high → short, as a rule file (OPEN_QUESTIONS #4) | open |
| 4 | Plan-construction template for REVERSAL_CALLED (the audit's §2 proposal): run it in shadow against a placebo before it may register plans | open |
| 5 | Resolve stops on 1m bars to cut the 15–27 min blind spot (N214 B) | open |
| 6 | Push notification from the GitHub `call-desk` workflow (issue → phone) once the desk runs on Actions | built, schedule off |
