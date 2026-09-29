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
| 7 | Status card with an OPEN position: title reads "NO TRADE — DESK STATUS" and shows no entry/stop/TP/unrealised R for the open plan (seen 2026-09-29 03:21 on CALL-0010). `card_png.py` renders pending plans only. Make `status_card.py` (or `card_png.py`) draw an "OPEN" block from state.json `open` so the PLAN_EVENT card needs no prose | open |
| 8 | PLAN_EVENT report text: desk_check could emit a ready-made `report` field (event + ledger line with win rate/payoff/E[R]/equity/dd), so the agent copies it rather than composing it each wake | open |
| 9 | REVERSAL_CALLED wake with `setup_qualifies: false` outside the symbol's measured session (MGC 08:20–13:30, MNQ 09:30–16:00) always ends "no plan" (first seen 2026-09-29 03:31, MGC 1m/5m/15m BULL vs 60m/4h BEAR). Proposal (owner decides; it changes a trigger): log it quietly as a note instead of exit 10 unless a qualifying setup or rule signal comes with it — repeated 03:32 for MNQ (same shape; also blocked by one-plan-per-symbol with CALL-0010 open). Also: skip the wake when the symbol already has an open/pending plan | open |
