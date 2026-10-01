# CALL desk — operating brief v2 (2026-09-29)

**This replaces the 1,138-line `CHECK_PROCEDURE.md` as the thing you follow.** That file is now a
reference: every mechanical step in it is implemented in `desk_check.py`. You are the **judgment
layer only**. Scripts watch the market. You are woken when a pre-registered trigger fires, you
decide, and you go back to waiting.

Posture: **PAPER**, $50,000 account, MGC and MNQ, nothing is a real order. Owner's window: Sun 17:50 → (owner 2026-09-29: opens 10 min early; 17:50–18:00 = PRE-OPEN review, routine "CALL desk: 17:50 pre-open review" runs `preopen.py` and drafts plans; G2 allows planning then)
Fri 15:30 ET. Silence outside it.

---

## 1. Start-up (once per session, and after any restart)

```bash
git fetch origin claude/admiring-heisenberg-doycyh && git merge --no-edit FETCH_HEAD   # the consolidated hub
pip install -q yfinance pillow numpy
python3 workspace/paper/CALL/desk_check.py --render auto        # one check; prints one line
```

Then launch the watcher **as a background command** (Bash `run_in_background: true`), so it re-invokes
you only when it exits:

```bash
bash workspace/paper/CALL/desk_loop.sh          # checks every 2 min; exits 10 only on needs_attention
```

**OWNER OVERRIDE (2026-09-29 08:20 ET): report every 2 minutes with cards, like the old desk.** Run the
loop as `DESK_REPORT_EVERY=1 bash workspace/paper/CALL/desk_loop.sh` (background). Every in-window check
renders its cards and exits **0 = routine hand-off** (check `triggers` in desk_status.json for attention items; only exit 2 = data failure): write the one line (`one_line` from desk_status.json),
then send every file in `cards` with `SendUserFile` (`display: "render"`), card LAST, then restart the loop
(it waits out the rest of the 2 minutes itself). **Owner, 11:49 + 13:15 ET: a one-line update EVERY check; the card only when report_turn prints CARD_NEEDED** (a plan is live, or a trigger fired). No-trade → no-trade = text line only. Cards follow CHECK_PROCEDURE "EVERY CHECK EMITS A CARD":
`card_png` for each PENDING or OPEN plan (and on the check a plan closes), grey `card_STATUS.png` when none.
Exit 10 is still handled per §2.

**Do not** create 2-minute crons, `send_later` chains or `/loop`s. The loop replaces all of them. The hourly
Routine is only a backstop: if the loop is not running, restart it and say nothing else.

## 2. When the loop wakes you (exit 10)

Read `workspace/paper/CALL/desk_status.json` (`triggers`, `events`, `notes`, `one_line`). Then act by trigger:

| trigger | what you do (and nothing more) |
|---|---|
| `PLAN_EVENT` | A plan triggered, closed, hit TP, expired or voided. **resolve.py already wrote the outcome. Never edit it.** Report the event with the ledger line (win rate AND payoff, expectancy R, equity, drawdown), then send the card: `python3 workspace/paper/CALL/card_png.py` for a pending plan, `status_card.py` if the book is empty |
| `EVENT_ON_PROVISIONAL_BAR` | Say the event sits on a bar under 30 min old, and that the next check re-reads it. Don't act on it |
| `REVERSAL_CALLED` / `COUNTER_TREND_QUALIFIES` | The only route to a **new discretionary plan**. Use §3. Most of the time the answer is "no plan", with one line on why |
| `RULE_SIGNAL_READY` | A registered, walk-forward-tested rule fired **and** its draft passed every gate. Review the draft in `drafts/`, then commit it with `plan_builder.py --from-signal <file> --commit` or decline it in one line. (Refused rule signals are shadow-logged in `rule_signals.jsonl` automatically and never wake you) |
| `DATA_STALE` | Say which symbol/frame is stale and since when. Never state a price as current |
| `DRAWDOWN_FLOOR` | Drawdown ≥ $2,600: **stop all new plans** and tell the owner. The desk is closed until they reply |
| `DAILY_LOSS_LIMIT` | Owner rule (2026-09-29): trades closed this trading day (18:00→18:00 ET) have lost ≥ $1,000 realized. **No new plans until 18:00 ET.** Say so once; plan_builder gate G9 enforces it |
| `BRIEF_CHANGED` | Re-read this file and `CALLOUT.md`. If they conflict, CALLOUT.md wins; note it in one line |

Then restart `desk_loop.sh` in the background and end the turn. Lead every message with the ET time.

**OWNER OVERRIDE (2026-09-30 21:37 ET, "option 3"): TEST trades.** When a REVERSAL/COUNTER_TREND/level setup
would otherwise be skipped only because of the soft lessons (#22 borderline 15m close, #23 stacked levels /
coin-flip LVN history), take it as a 1-contract TEST: add `--test` to plan_builder (sets confidence=TEST,
strategy "TEST: ..."). Every hard gate still applies (stand-down, G2, G3, R:R, room, floors, daily loss).
Hard "don'ts" (breakout chasing, fading the first 60m bar after 09:30, gold overnight-sweep fades) are NOT
overridden. Report TEST trades separately from the measured record. In parallel the deep-LVN fade (#17) and
reclaim entry (#18) were walk-forward tested 2026-09-30 (`research/RESULTS_2026-09-30_lvn.md`): sweep &
reclaim LOSES (B60: 610 trades, 33.6% wins x payoff 1.51, -0.17R, t -3.21; B15: 269 trades, -0.18R), stacked
or not. So TEST trades are NOT taken on sweep/reclaim setups; they apply only to deep-LVN fades (#17),
which had too few trades (5-10) to judge.

**OWNER OVERRIDE (2026-10-01 19:20 ET, "option 2"): stacked-level TEST trades.** The owner saw a full day of
zero trades (every trigger declined; 4 stacked-level declines were right, 2 were missed bounces: MNQ 30800
03:39 ET, MNQ 30605 10:29 ET). From now on a REVERSAL_CALLED / COUNTER_TREND_QUALIFIES / level setup that is
declined ONLY because its level is stacked (#23, 2+ levels within 1/4 ATR) is taken as a 1-contract TEST
(`plan_builder.py --test`), in addition to the deep-LVN (#17) TESTs above. Unchanged: every hard gate, the
hard don'ts, stand-down, and the sweep & reclaim exclusion (a measured loser). Pre-registered
(`research/PREREG_2026-10-01_stacked_test.md`): stacked-level TESTs are expected to LOSE (H0: expectancy
<= 0R); judge only after 20 closed TESTs, against the B60 sweep/reclaim baseline (-0.17R) and a placebo of
the same fade at a random price 0.5-1.5 ATR away; luck bar sqrt(2 ln N) over every variant tried.

## 3. Making a plan: `plan_builder.py` only, never by hand

```bash
python3 workspace/paper/CALL/plan_builder.py --symbol MGC --side LONG --entry 4150 --stop-beyond 4143 \
    --tp-r 1.8 --why "<=2 lines: the read>" --invalidation "<=1 line>"          # prints gates, writes drafts/
# only if every gate PASSES and you still want it:
python3 workspace/paper/CALL/plan_builder.py ... --commit
```

The builder does entry/stop/target/expiry/sizing/book-room and eight hard gates: volatility stand-down,
no entries 15:00–18:00, no breakout chasing, stop ≥ 0.5 ATR, R:R ≥ 1.6 after costs, 50%-cap book room,
drawdown floor, and max 3 plans per symbol (owner 2026-09-29; was one). It also attaches the hub's measured record for every level
near the entry. **Your job is two lines of "why" and one line of invalidation, plus the yes/no.** If a
gate fails, there is no plan. Don't argue with a gate. Gates change only through the owner.

## 4. What the research established (everything compiled so far, for MGC/MNQ)

Full detail: `DATA_HUB/README.md` → `STRATEGIES_BY_SYMBOL.md`, `BOUNCE_AND_VOLUME_PROFILE_PLAYBOOK.md`,
`RULES_AND_PITFALLS.md`, `AUTOMATION.md`. Never open `Archived_Do_Not_Refference/`.

**Nothing has a proven edge.** Every call is DISCRETIONARY, sized at ≤50%, and says so.

**Proven "don'ts" (the strongest findings in the project):**
1. Don't enter a breakout in the direction of the move (worse than random 4/4, z −2.6 to −4.7).
2. Don't fade the first 60m bar after 09:30 (z −10.6).
3. No new entries 15:00–16:00 ET (z −4.4). Flat by 16:00.
4. **Don't rest an order on a stacked level** (2+ levels within ¼ ATR). They get swept (combined z −5.1).
   Wait for the reclaim, or skip.
5. Don't buy plain swing lows as support. On MGC 5m that's worse than random (z −3.2).
6. Don't fade overnight-high/low sweeps on gold (z −3.0).
7. Volatility stand-down: MNQ ATR14(15m) > **80** (owner raised it from 58, 2026-09-29 13:55 ET), MGC > 10.
8. **Sizing (owner, 2026-09-29 13:55 ET):** plans may use the FULL permitted risk (was ≤50%).

**The owner's style: volume-profile LVNs and bounce levels (the playbook's checklist):**
- LVNs on **60m-built 1-week/1-month/3-month profiles** lean bounce vs random on all 4 symbols.
  5m-built 1–3-day LVNs are coin flips.
- Price **rising into** an LVN, and a **heavy-volume touch**, are the strongest bounce leans.
- **Pre-registered test (OQ1, LVN fade, 1-week 60m profile):** 106 trades, +0.06R, t 0.64. **Not an edge.**
  MGC +0.23R (18 trades), MNQ −0.05R (24 trades). This rule runs live as a shadow signal. At 1 ATR(60m) it
  doesn't fit the desk's size, so it's logged, not traded.
- Prior-day VWAP / close as resistance, and prior-day or prior-RTH-high **sweep & reclaim → short**, are
  the best classic levels (still under the luck bar).
- First touches are worse than retests. Prefer a level that has held once.
- **Owner's lesson (MGC 4220, 2026-09-29): the reversal zone is the DEEPEST LVN, and the first one outside
  value.** On the 48h profile, 4220 was the thinnest valley (0.19x the smaller flanking peak) between the
  value-area top shelf (4205-07) and the next heavy node (4228-30). Price rose out of value into it and
  was rejected twice (4220.0, 4219.5). The shallow LVN at 4210.5 (0.6x) got run straight through.
  `preopen.py` now scores every LVN's depth and flags the first LVN above/below value: prefer deep
  (< ~0.35) first-outside-value LVNs, approached from inside value. Hypothesis, not yet tested:
  AUTOMATE_NEXT #17.
- **MGC is the best market for profile levels** (value-area edge, POC reversion at 30m). MGC daily bars are a
  different contract: never mix them with intraday levels.

**Exits:** every past fill reached ≥ +0.83R before most lost. Stop-to-breakeven at +0.8R is the top
*untested* idea (OPEN_QUESTIONS #2). **Don't apply it live until it's pre-registered and tested with
`DATA_HUB/tools/walkforward.py`.**

**Your own record:** 6 closed, 2W/4L, 33%, payoff 1.41, −0.21R (state.json basis). The measured record
excluding CALL-0002 is 1W/4L. CALL-0010 (MNQ short 30,550) expires 09:30 ET 2026-09-29, and `desk_check`
resolves it. Tracking CALL-0010 through `thesis.py` gives the verdict "direction right, target distance
covered — the trigger was the problem".

## 5. Reporting

- Quiet checks produce **no message**. The loop writes `desk_status.json` and `desk_events.jsonl` silently.
- On a wake: ET time first, then the event, then the ledger line, then the card last.
- Numbers come from script output, never from memory or prose.
- Commit only paths you own (`workspace/paper/CALL/**`), merge before pushing, never force.

## 6. Ways to automate more (write them down when you see them)

If you do the same reasoning twice, it belongs in a script. Append the idea to `AUTOMATE_NEXT.md` with
the trigger and the rule. Pre-register any new signal as a rule file under `DATA_HUB/tools/rules/`. Run it
through `walkforward.py`, and it joins the live shadow signals automatically once it's in the ledger.
