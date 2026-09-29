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
| 7 | Status card with an OPEN position: title reads "NO TRADE — DESK STATUS" and shows no entry/stop/TP/unrealised R for the open plan (seen 2026-09-29 03:21 on CALL-0010). `card_png.py` renders pending plans only. Make `status_card.py` (or `card_png.py`) draw an "OPEN" block from state.json `open` so the PLAN_EVENT card needs no prose | built 08:25 (desk_check renders card_png for PENDING + OPEN plans and on close; status card only when none live) |
| 8 | PLAN_EVENT report text: desk_check could emit a ready-made `report` field (event + ledger line with win rate/payoff/E[R]/equity/dd), so the agent copies it rather than composing it each wake | open |
| 9 | REVERSAL_CALLED wake with `setup_qualifies: false` outside the symbol's measured session (MGC 08:20–13:30, MNQ 09:30–16:00) always ends "no plan" (first seen 2026-09-29 03:31, MGC 1m/5m/15m BULL vs 60m/4h BEAR). Proposal (owner decides; it changes a trigger): log it quietly as a note instead of exit 10 unless a qualifying setup or rule signal comes with it — repeated 03:32 for MNQ (same shape; also blocked by one-plan-per-symbol with CALL-0010 open). Also: skip the wake when the symbol already has an open/pending plan | open |
| 10 | REVERSAL_CALLED re-fires when `reversal_called` flaps false→true between checks (3rd wake by 04:13 on 2026-09-29, same LTF-bull vs 60m/4h-bear shape, no plan each time). Add hysteresis: re-arm only after the call has been off for ≥1 new 15m bar, or key the trigger on (symbol, side, 15m bar) so the same reversal wakes once | built 04:30 (desk_check REVERSAL_REARM_MIN=60, keyed on symbol+side; repeats → note REVERSAL_REPEAT) |
| 11 | Each 2-min report turn repeated the same read/commit/push steps: `report_turn.sh` does them; the agent only sends cards and restarts the loop | built 08:46 |
| 12 | COUNTER_TREND_QUALIFIES woke at 09:53 (MNQ LONG into a 4-level stack 30549–30557, inside 09:30–10:30). Both proven dont's (fade first 60m z −10.6; stacked level z −5.1) decided it. Proposal (owner decides, it adds gates): encode both in plan_builder gates + desk_check so such setups become a quiet note, not a wake | open |
| 13 | COUNTER_TREND_QUALIFIES woke at 11:29 for MNQ while its volatility stand-down was binding (ATR 68.1 > 58): G1 fails, so no plan is possible. desk_check should not wake for a setup on a symbol whose stand-down is binding (note it instead). Encodes an existing gate, no new rule | built 11:57 (quiet notes SETUP_UNDER_STANDDOWN, REVERSAL_UNDER_STANDDOWN) |
