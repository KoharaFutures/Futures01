# Automation audit — the CALL desk (paused 2026-09-29 00:58 ET)

**Question:** how much of the CALL desk's per-check work needs an LLM? **Answer:** almost none of
the per-check work. What does need one is (a) forming a new plan and (b) writing prose findings.
Everything else is already a script, or is simple arithmetic that the procedure spells out.

Sources read in full: `workspace/paper/CALL/CHECK_PROCEDURE.md` (1,138 lines, cited `CP:line`),
`CALLOUT.md`, every `workspace/paper/CALL/*.py`, `DATA_HUB/tools/*`, `futures_agents/data/archive.py`,
`futures_agents/config.py` (AccountConfig). Every tool was **executed** in a scratch copy
(`$SCRATCH/C`). Nothing in the repo was written except this file.

Terms: **MECH** = mechanical (a script can do it with no judgment, but none does yet) ·
**SCRIPTED** = already a script (named) · **JUDG** = needs an LLM or a human.

---

## 0. First finding: the tools are broken as they sit now

`workspace/paper/CALL/data/` was archived. Six tools hard-code it or other archived files. Verified by running each one in a scratch copy with and without data:

| hard-coded path | used by | what happens now (verified) |
|---|---|---|
| `HERE/"data"` | `fetch.py:31`, `resolve.py:51`, `chart.py:29` (and through them `regime`, `watch`, `status_card`, `heat`, `project`, `thesis`, `card_png.grade`) | **`resolve.py` silently does nothing.** It printed `open 0 closed 6 equity $49,958.36`, and CALL-0010 (PENDING, expires 2026-09-29T09:30 ET) can never trigger or expire because `load_bars` returns `[]` (`resolve.py:228-231`). `regime` prints `NO DATA` on every frame. `project.py` raises `IndexError`. `chart.py` says "only 0 real bars". `status_card.gather()` indexes `b[-1]` and crashes. `fetch.py` does `mkdir` and **re-creates** the archived directory. |
| `HERE/"feed_lag.jsonl"` | `fetch.py:32,116-119` | re-created empty, so the lag distribution starts over |
| `HERE/"bias_history.jsonl"` | `regime.py:34,104-128` | re-created empty. `reversal()` can't fire until 2 records exist |
| `HERE/"standdown_cost.txt"` | `status_card.py:107-111` | `try/except`: the "foreclosed" line on the status card is **silently blank** |
| `HERE/"confluence.py"` | `card_png.py:414,640,750` | `try/except`: the grade **silently loses criterion 6**, and the confluence panel and TP "why" text come out empty. The card still renders |
| `HERE/"NOTES.md"` | `index_notes.py:46` | `FileNotFoundError` |
| branch `claude/intelligent-feynman-ongyjw` | CP:20, CP:187 | already merged into this branch. Syncing to it is no longer meaningful |
| `PIL` and `numpy` not installed | `card_png.py:32`, `status_card.py:29,129` | `ModuleNotFoundError` in a fresh container. `pip install pillow numpy` fixes it |

**Fix that needs no logic changes (verified):** point the loaders at `data/archive/`. The archive
rows use the same `{"ts","o","h","l","c","v"}` schema. In the scratch copy I made a directory of
symlinks named `{SYM}_{N}m_fetched_0000-archive.jsonl → data/archive/{SYM}_{N}m.jsonl`. With it,
**every tool ran correctly**: `resolve` (0.07 s), `regime` (0.3 s), `watch` (0.5 s), `thesis`
(0.1 s), `heat` (0.2 s), `project` (0.4 s), `status_card 1 --auto` (0.6 s), and
`card_png CALL-0010 --scale 3` (**17 s**). The `glob` pattern can't confuse `5m` with `15m` or
`1m` with `1440m`, because the `m_` suffix is part of the match.

Two more things the new hub tools get wrong:
- **`refresh_archive.py --fetch` does not reject stub bars.** Only the `--merge-fragments` path
  filters them (`refresh_archive.py:48-50` vs `67-81`). `README.md` and `RULES_AND_PITFALLS.md` B2
  say otherwise. Counted in the archive: MNQ_5m 1, MNQ_60m 2, MGC_60m 1 stubs. Every CALL loader and
  `bounce_levels.load` (`:69-79`, which `vp_levels` reuses) filters them when reading, so today no
  number is wrong. They are still stored permanently in an archive that is supposed to be
  append-only and clean.
- `data/archive/` is **git-tracked** (29 files, 21 MB), and `BarArchive._write` rewrites the whole
  file on every reconcile (`archive.py:209-227`). A 2-minute fetch into it would change 8 tracked
  files every check. A live store must be a separate, gitignored directory.

---

## 1. Every step, classified

### 1a. Fast check (every 2 min, 18:00→15:30 ET, CP:230-240, 887-991)

| # | step | class | why / where |
|---|---|---|---|
| F1 | Out-of-window firing: make zero tool calls, emit nothing | MECH | a clock comparison (CP:948-970). A script checks ET with `zoneinfo`, so it's immune to the UTC and DST problems |
| F2 | `CronList`. Re-create the 3 UTC crons if they're missing and report the gap | MECH | CP:972-991. Goes away entirely under a system scheduler |
| F3 | `git fetch && merge`, write `BASIS` | MECH | CP:17-22. Now obsolete (the branch is merged and the desk is paused) |
| F4 | Re-read `CALLOUT.md` only if HEAD moved | MECH detect / JUDG apply | CP:235. Detecting a change is a hash compare. Acting on new text is judgment (§2 J1) |
| F5 | `pip install yfinance` | MECH | CP:34 |
| F6 | Fetch bars, drop stubs, write the delta snapshot (new timestamp **or** revised OHLCV) | SCRIPTED | `fetch.py:main` (`is_stub:42`, `stored:46`, delta `96-102`). **Note:** the code fetches all 6 frames (`FRAMES:39`), not the "5m+15m only" that CP:236 says |
| F7 | Log feed lag | SCRIPTED | `fetch.py:104-119` → `feed_lag.jsonl` |
| F8 | Trigger, fill, stop, target, expire and void plans. Update the ledger | SCRIPTED | `resolve.py:main:618` → `check_triggers:212`, `unreachable:155`, `resolve_open:380`, `write_ledger:514` |
| F9 | Volatility stand-down (ATR14 15m > 58 MNQ / > 10 MGC) | SCRIPTED | `status_card.atr14:38`, `SPEC:34`, `auto_reason:45` |
| F10 | Rule 5 (no entries 15:00–16:00) | SCRIPTED | `status_card.auto_reason:74` |
| F11 | Per-frame bias + reversal gate | SCRIPTED | `regime.timeframe_bias:73`, `record:104`, `reversal:130` |
| F12 | Scan the side the headline is not on | SCRIPTED | `regime.reversal_setup:197` via `watch.counter_trend:191` (prints only) |
| F13 | Gate-flip levels + capacity (open + pending risk vs cap) | SCRIPTED | `watch.report:62` (prints, returns None), `watch.committed:140` (returns a tuple), `capacity:171` |
| F14 | HEAT: MAE and MFE for each trade | SCRIPTED | `heat.excursions:56` |
| F15 | ANSI bias chart | SCRIPTED | `chart.bias:68`, `chart.render:112` |
| F16 | Card: `card_png` for each PENDING plan, or `status_card --auto` | SCRIPTED | `card_png.render:491`, `status_card.render:115` |
| F17 | Send the card last. Push only on an event | MECH | CP:664-673, 844-851. Delivery is a channel, not a decision |
| F18 | ET time header, one-line report | MECH | CP:529-537, 567-592. Pure template |
| F19 | Stop conditions (dd ≥ $2,600; no plans + closed; 3 fetch failures) | MECH | CP:556-565 |
| F20 | 15:28 closing card: "unwatched until 18:00" | MECH | CP:929-936 |
| F21 | `check_ownership`, commit, push (one-line message) | MECH | CP:183-188, 252-266 |
| F22 | Re-arm the `send_later` chain | MECH | CP:629-661. Goes away under a system scheduler |

### 1b. Hourly full check (the backstop Routine + CP)

| # | step | class | why / where |
|---|---|---|---|
| H1 | List crons/triggers and repair them | MECH | CP:675-702, 943-946 |
| H2 | ET clock and window check | MECH | CP:892-922 |
| H3 | Re-read `CALLOUT.md` in full | JUDG | CP:24-27. "CALLOUT wins" means interpreting new prose (J1) |
| H4 | Fetch 1/5/15/60m (60m/30d) | SCRIPTED | `fetch.py:main` (already includes 60m/30d, 240m, 1440m) |
| H5 | **Form a fresh directional read on both symbols** | JUDG | CP:148-172, 268-273 (J2) |
| H6 | Thesis tracking of PENDING plans | SCRIPTED | `thesis.track:42` |
| H7 | Ledger: win rate **with** payoff, expectancy R, equity, drawdown, distance to $2,800, ambiguous count | SCRIPTED | `resolve.write_ledger:514-570`. Payoff shows only as avg win / avg loss; the ratio is 1 line of MECH |
| H8 | Sizing from drawdown (usable, base, ladder), ≤ 50% | MECH (not scripted in CALL) | CP:117-143. `futures_agents.config.AccountConfig.usable_buffer/derisk_multiplier` reproduces the CP table exactly (checked: dd $2,800 → mult 0.30 → $21.60). **`status_card.py:35` hard-codes `PERMITTED, CAP = 240, 120`**. At today's dd $198.20 the correct numbers are budget **$228.11** and cap **$114.05**, so `watch.capacity` overstates room by $5.95 |
| H9 | Volatility stand-down, stated with the ATR | SCRIPTED | as F9 |
| H10 | Treat the newest 1–2 bars as provisional (~28 min of revisions) | MECH (**not scripted**) | `RULES_AND_PITFALLS` B1. `YahooFeed` drops only the forming bar (`yahoo.py:366-370`). `resolve`, `atr14` and `unreachable` all use the newest held bar as final |
| H11 | Forward levels (fib/VWAP within ATR reach) | SCRIPTED | `project.forward_levels:90` |
| H12 | SCALP/SWING label | SCRIPTED | `regime.classify:269` |
| H13 | Register a plan in `pending.jsonl` (trigger, stop, TPs, expiry, contracts, `why_short`, weakness, `strategy_basis`) | JUDG (numbers MECH) | CP:169-172, 339-379 (J3) |
| H14 | Veto chain before registering (stand-down, rule 5, capacity, breakout prohibition, opposing-plan band, RTH note, untested family) | MECH (**only partly scripted**) | CP:152-167, 712-744, 1133-1138. The breakout prohibition exists only in the research harness (`cont1.py:79-100`) |
| H15 | Journal every callout and every NO TRADE | MECH | CP:174-181. `resolve` journals fills and voids. A NO TRADE caused by a veto is MECH |
| H16 | Price each decision in `DECISIONS.md` (foreclosed / marginal / realized) | MECH numbers, JUDG reflection | CP:853-883 (J5) |
| H17 | Findings to `NOTES.md` | JUDG | (J5) |
| H18 | Report lag distribution at the first full check of a session | MECH | CP:552-554 |
| H19 | Re-render and send cards for PENDING plans (never re-send an old PNG) | SCRIPTED | CP:594-627, `card_png.main:809` |
| H20 | Push a notification only for a fill, stop, target, floor or broken chain | MECH | CP:664-673 (J6) |

**Count: 42 steps. 20 SCRIPTED, 17 MECH, 5 JUDG** (F4-apply, H3, H5, H13 prose, H16/H17 reflection).

---

## 2. Can each JUDGMENT step become a pre-registered rule?

| id | judgment step | replaceable? | how, or why not |
|---|---|---|---|
| J1 | Re-read the brief and apply its changes (F4, H3) | **Detect yes, apply no** | Hash `CALLOUT.md`, `CHECK_PROCEDURE.md` and `DATA_HUB/RULES_AND_PITFALLS.md` every check. A changed hash raises `needs_attention: BRIEF_CHANGED`. Move every number a script uses (58, 10, $120 cap, the window, the 15:00 rule) into one constants block in `desk_check.py`, so a prose edit can't silently diverge from code. Interpreting new prose stays with the LLM, but it happens once per change instead of 669 times a day |
| J2 | Fresh directional read (H5) | **Yes, and this is the recommended rule** | The deterministic parts already exist: `timeframe_bias` + `reversal` (4 conditions, CP:428-437) + `reversal_setup` (CP:492-520). The hub's verdict is that nothing, discretionary reads included, beats placebo (`README.md` 1-3). A rule-based read is therefore no worse than the LLM's, and it is the only kind that can be pre-registered and placebo-tested. Rule: *a read is BULL/BEAR only when `reversal()["called"]` or `reversal_setup()["qualifies"]`, otherwise NONE.* Run it in shadow mode against the archive with a placebo before letting it register plans |
| J3 | Build the plan (H13) | **Numbers yes, prose partly** | trigger = `reversal_setup()["trigger"]` (a reclaim, never the print). stop = max(0.5·ATR14(frame), structure + 1 tick) per rule 4. TP1 = a fixed pre-registered R (1.6R is `classify`'s default, `regime.py:304`). expiry = N bars, fixed in advance. contracts = floor(0.5·budget ÷ (stop·pv)). `why_short` and weakness are generated from the gate facts (for example "15m 0-3 unanimous, held 2 bars, 4h agrees; weakness: MGC BREAKOUT family never generated"). Free-text nuance is lost, and CP:374-379 shows auto-trimmed prose once argued the opposite of its own plan, so a template is safer |
| J4 | NO TRADE vs plan | **Yes** | Veto chain H14 in fixed order. The first failing veto becomes the journalled `why` |
| J5 | NOTES/DECISIONS reflection (H16/H17) | **No** for prose, **yes** for the numbers | Foreclosed = the extreme-to-extreme move in the window at the max stop. Marginal = 0 if no gate fired in the window, else foreclosed. Realized comes from `state.json`. All three are computable. Deciding what a pattern *means* is judgment, and it can wait for a daily wake |
| J6 | "Would he want to know now?" (push) | **Yes** | Whitelist: TRIGGERED, CLOSED, TP hit, VOID/EXPIRED, dd crossing $2,600, 3 fetch failures (CP:664-673) |
| — | Interpreting HEAT or thesis verdicts | No, and nothing requires it | Report only. HEAT is a lower bound (CP:1043-1047) |

---

## 3. Spec: `workspace/paper/CALL/desk_check.py` (one deterministic entry point)

### 3.1 Inputs
```
python3 workspace/paper/CALL/desk_check.py [--mode fast|full|auto] [--no-fetch]
        [--live-dir data/live] [--render auto|none|always] [--scale 3] [--now ISO8601]
```
- `--mode auto` (default): `full` on the first run of each ET hour, otherwise `fast`.
- `--now` makes runs reproducible in tests. Every time is computed in `America/New_York` via `zoneinfo`.
- Reads: `state.json`, `pending.jsonl`, `BASIS`, `DATA_HUB/levels/{MGC,MNQ}_bounce.json` and
  `_volume_profile.json`, `data/live/*` (bars), and the previous `desk_status.json` (for diffs and hysteresis).
- Needs: `yfinance`, `pillow`, `numpy`.

### 3.2 Order of calls (every signature checked against the code; module = `importlib` load, as `thesis._load:35` does)

| # | call | signature (verified) | side effects |
|---|---|---|---|
| 0 | clock and window: in-window = Sun 18:00 → Fri 15:30 ET, excluding 15:30–18:00 | — | none |
| 1 | **bars**: for sym in MGC, MNQ and m in {1,5,15,60} (+{240,1440} in full): `YahooFeed().fetch(sym, minutes=m, days=d)` → drop `is_stub` → `BarArchive(live_dir).reconcile_result(res)` | `yahoo.py:339 fetch(symbol, minutes=60, days=30.0)`; `archive.py:194 reconcile_result(result) -> ReconcileReport(.added,.updated,.conflicts,.retracted)` | rewrites `data/live/{SYM}_{m}m.jsonl` (gitignored). Measured: 4 frames × 2 symbols = **8.5 s**. **Don't call `refresh_archive.fetch`**: it returns `None` (prints only) and doesn't filter stubs. **Don't call `fetch.py:main`**: it writes deltas into the archived `CALL/data` |
| 1b | feed lag per frame = now − newest real bar; `stale` if 5m lag > 30 min in window | mirrors `fetch.py:104-110` | append one row to `data/live/feed_lag.jsonl` |
| 2 | **loader shim**: keep `CALL/data/` as a gitignored directory of symlinks `{SYM}_{m}m_fetched_0000-live.jsonl → data/live/{SYM}_{m}m.jsonl` (preferred long-term alternative: a 1-line `DATA = Path(os.environ.get("CALL_DATA_DIR", HERE/"data"))` in `fetch.py:31`, `resolve.py:51`, `chart.py:29`) | — | verified working in scratch |
| 3 | snapshot `state.json` + `pending.jsonl` (bytes) | — | none |
| 4 | **resolve**: `rs.load_state()` → `rs.check_triggers(state, now_iso, basis)` → `rs.resolve_open(state, now_iso)` → `rs.save_state(state)` → `rs.write_ledger(state, basis, now_iso)` | `resolve.py:99, 212 (state, now_iso, basis)->list[str], 380 (state, now_iso)->list[str], 113, 514` | writes `pending.jsonl` (on change), **appends/rewrites `journal.jsonl`**, `state.json` (always, byte-identical if nothing changed), `LEDGER.md` (only on real change, `:607-612`). **The only writer of outcomes. Never re-implement it** |
| 5 | events = structural diff of step 3 vs step 4 (new `open` ids → TRIGGERED; new `closed` → CLOSED with `result`, `r_multiple`, `ambiguous`; plan `status` changes → VOID_UNREACHABLE/EXPIRED; `tps[].hit` flips → TP) | — | none |
| 6 | sizing: `AccountConfig().usable_buffer(eq, peak)`, `.derisk_multiplier(eq, peak)`; base = min(usable·0.06, eq·0.0075, 500); budget = base·mult; cap = 0.5·budget | `config.py:430` | none |
| 7 | `watch.committed()` → (open_risk, pend_risk, labels); room = cap − open − pend | `watch.py:140` | none (use computed cap, **not** `status_card.CAP`) |
| 8 | ATR and stand-down: `status_card.atr14(sym)` vs `SPEC[sym]["line"]` | `status_card.py:38 (sym)->float`, `:34` | none |
| 9 | `tfs = regime.timeframe_bias(sym)`; `rv = regime.reversal(sym, tfs)`; `rs_ = regime.reversal_setup(sym, tfs)`; **then** `regime.record(sym, tfs)`, **only when a new completed 15m bar exists** | `regime.py:73 (symbol, frames=FRAMES, n=40)->list[dict]`, `:130 (symbol, tfs)->dict{called,reasons,…}`, `:197 (symbol, tfs=None)->dict{qualifies,side,sigma,trigger,…}`, `:104 (symbol, tfs)` | `record` appends `bias_history.jsonl`. See pitfall P9: this changes "held 2 checks" to "held 2 bars", a rule change the owner has to approve |
| 10 | `thesis.track(plan)` for each PENDING plan; `heat.excursions(pos)` for each open position | `thesis.py:42 (plan)->dict`, `heat.py:56 (pos)->dict` | none |
| 11 | full only: `project.forward_levels(sym)`; `regime.classify(plan)` for PENDING | `project.py:90 (symbol, frame=15, horizon_bars=6)->dict`, `regime.py:269` | none |
| 12 | **hub levels**: from `{SYM}_bounce.json[i]["current"]["levels"][]` (price, type, side, `history.touch.z`) and `{SYM}_volume_profile.json["current"][]` (`lvn[].price`, `poc`, `vah`, `val`, `window`, `asof`). Distance to the last real 5m close in ATR14(15m). Hysteresis state: **arm** at ≥ 1.0 ATR (the same `ARM` as `bounce_levels.py:48`), **touch** at ≤ 0.25 ATR | JSON keys verified | writes the arm state into `desk_status.json` |
| 13 | render (see 3.4): PENDING → `C.SCALE=s; C.render(plan, HERE/f"card_{sym}_{id}.png")`; none → `SC.C.SCALE=s; SC.render(HERE/"card_STATUS.png", SC.auto_reason())` | `card_png.py:491 (plan, out)->Path`, `status_card.py:115 (out, reason)->Path`, `:45 ()->str` | **`card_png.render` calls `regime.record` internally (`card_png.py:695`)**, so render only after step 9, or the held counter double-counts (N248) |
| 14 | write `desk_status.json` (overwrite) + append `desk_events.jsonl`; exit code 0 = quiet, 10 = needs_attention, 2 = data failure | — | 2 files |

### 3.3 Output: `workspace/paper/CALL/desk_status.json`
```json
{"now_utc":"…","now_et":"02:00 AM EDT","in_window":true,"mode":"fast","basis":"285962f",
 "data":{"MNQ":{"5":{"newest_real_bar":"2026-09-29T01:50:00-04:00","lag_min":10.4,"added":11,
         "revised":3,"provisional_bars":["…01:45","…01:50"]}}, "fetch_failures":[]},
 "ledger":{"closed":6,"wins":2,"losses":4,"win_rate":0.333,"payoff":1.68,"expectancy_r":-0.21,
           "ambiguous":0,"equity":49958.36,"drawdown":198.20,"to_2800":2601.80,"to_2600":2401.80},
 "sizing":{"budget":228.11,"cap_50pct":114.05,"committed":52.00,"room":62.05},
 "standdown":{"MNQ":{"atr14_15m":43.9,"line":58,"binding":false},"MGC":{…}},
 "rule5_active":false,
 "frames":{"MNQ":{"15":"BEARISH 0-2",…},"reversal":{"called":false,"reasons":[…]},
           "reversal_setup":{"qualifies":false,"side":"LONG","sigma":-1.21,"trigger":30445.25}},
 "book":{"pending":["CALL-0010"],"open":[],"thesis":{…},"heat":{…}},
 "hub_levels":{"MNQ":[{"src":"bounce","type":"ROUND","price":30400.0,"dist_atr":0.7,
               "state":"armed","hub_asof":"2026-09-29T00:55:00-04:00"}]},
 "events":[], "card_png":"workspace/paper/CALL/card_STATUS.png",
 "one_line":"02:00 ET · no new real bar since … (lag 10m) · CALL-0010 pending · dd $198",
 "needs_attention":false, "triggers":[]}
```
(Numbers are from the scratch run on archive bars: payoff = $109.56 avg win / $65.19 avg loss = 1.68; expectancy = −0.2075R over 6 closed trades.)

### 3.4 `needs_attention` triggers (pre-registered; anything that isn't here is quiet)

| trigger | fires when | wakes the LLM? |
|---|---|---|
| `PLAN_EVENT` | step 5 found TRIGGERED / CLOSED / TP / VOID / EXPIRED | yes, plus a push |
| `EVENT_ON_PROVISIONAL_BAR` | the bar behind an event is < 30 min old. Re-check its OHLC next run; raise `REVISION_CONTRADICTS` if the revised bar no longer touches the level | yes (the LLM decides whether to note it; it must **not** edit the outcome) |
| `REVERSAL_CALLED` | `reversal()["called"]` flips false → true | yes, the only in-window route to a new plan |
| `COUNTER_TREND_QUALIFIES` | `reversal_setup()["qualifies"]` flips false → true | yes (CP:1130-1131 "say it out loud") |
| `STANDDOWN_CHANGE` | either symbol's `binding` flips | no wake; card + one line |
| `HUB_LEVEL_TOUCH` | an armed level's distance drops to ≤ 0.25 ATR | **no wake by itself**. It attaches to the status. Measured fresh touches: MNQ 42 and MGC 42 per trading day on 5m levels, 11 and 9 per day on 60m levels. The hub says levels don't beat placebo, so a touch alone isn't worth a wake. It wakes only together with `REVERSAL_CALLED` or `COUNTER_TREND_QUALIFIES` on the same symbol |
| `DATA_STALE` | 5m lag > 30 min in window, or 3 consecutive fetch failures (CP:565) | yes, once |
| `DRAWDOWN_FLOOR` | dd ≥ $2,600 (CP:563) | yes, plus a push, and the desk stops |
| `BRIEF_CHANGED` | hash of CALLOUT/CHECK_PROCEDURE/RULES changed | yes, once |
| `SIZING_MISMATCH` | computed cap ≠ `status_card.CAP` | no. Logged until someone fixes the constant |
| `WINDOW_CLOSE` | first run ≥ 15:28 ET with a PENDING plan | no wake. Closing card: "unwatched until 18:00" |
| `HUB_STALE` | hub `asof` > 24 h old | no wake. Run `update_hub.sh --no-fetch` (measured ≈ 30 s for MNQ + MGC) |

Rendering: when `--render auto`, render a card only if an event happened, on the first run of
each hour, or at `WINDOW_CLOSE`. A 3× plan card costs 17 s, so rendering one every 2 minutes
would take 14% of wall time and repeat the stale-card-by-timestamp issue.

---

## 4. Estimated LLM wake reduction

| | wakes per weekday | basis |
|---|---|---|
| **Old desk** | **645 fast + 24 hourly = 669** | crons `*/2 22-23 * * 0-4` (60) + `*/2 0-18 * * 1-5` (570) + `0-28/2 19` (15), CP:900-904. About $900 over ~30 h |
| New, strict (PLAN_EVENT, REVERSAL, COUNTER_TREND, DATA, FLOOR, BRIEF) | **~10–30** | Plan events ran at ~22 per 30 h on the old desk (11 plans, 6 fills, 6 closes, 5 void/expire), and new plans now need a wake, so this falls. Sign-change events where the 15m headline is unanimous and held 2 bars: **5.0 per day on MNQ and 5.2 per day on MGC**, measured over 42 days of archive 15m bars (condition 4 ignored, so this is an upper bound) |
| + one scheduled "fresh read" per hour in the window | +21 | only if the owner wants the hourly discretionary read kept |
| + wake on every 60m hub-level touch | +~20 | not recommended (the levels don't beat placebo) |

**Net: 669 → about 10–50 wakes a day, a 93–98% cut.** The script itself costs about 10 s of CPU
per fast run and no tokens. The remaining wakes are the ones where something actually happened,
which is what CP:201-202 and 664-673 asked for anyway.

---

## 5. Pitfalls a script must preserve (from the procedure and code)

| # | pitfall | must preserve | source |
|---|---|---|---|
| P1 | **Stub bars** (v = 0 and h = l) carry a stale price, once 12.20 pts wrong | Drop them before storing **and** when reading. Never quote a price from one. `refresh_archive --fetch` doesn't drop them (§0) | CP:78-92, `resolve.py:60`, `fetch.py:42` |
| P2 | **Revisions**: freshness means a new timestamp **or** changed OHLCV. A bar frozen mid-formation at a session or weekend close hides a stop touch | Reconcile keeps revisions (`archive.py:158-173`). Never key on timestamp alone | CP:68-76 |
| P3 | **Provisional newest 1–2 bars** (revised for ~28 min; lag median 12.9 min at 5m, ~23 at 15m) | Flag them. `resolve` treats them as final and journals irreversibly, so raise `EVENT_ON_PROVISIONAL_BAR` and re-verify later. Never edit an outcome | RULES B1, CP:522-527 |
| P4 | **Stop wins** when one bar holds both stop and target; flag it `ambiguous` | Reuse `resolve_open`, never re-implement it | CP:108-110, `resolve.py:435-446` |
| P5 | **No target on the entry bar**. A stop on the entry bar counts only when the ordering is forced (limit entries) | same | `resolve.py:407-431` |
| P6 | Stop entries fill at the trigger **or worse** (gap → open + 1 tick). Limits fill at the price or better with no slippage. Costs are charged on both sides | same | CP:107-111, `resolve.py:250-265` |
| P7 | **Only `resolve.py` writes outcomes.** Never hand-edit LEDGER, state or journal outcomes. A plan is never edited after price is watched (N8). A void only ever removes | The script calls functions and never writes those fields | CP:100-115, 778-792 |
| P8 | **Future `created_bar_ts`** makes a plan inert: `resolve` skips it forever | Detect `created_bar_ts > now` and surface it (as `card_png.live_status:266-280` does) | `card_png.py:266-280` |
| P9 | **Held counter counts invocations** (N248). `card_png.render` also calls `record` | Record once per new completed 15m bar. Render after the gate. Owner has to sign off the rule change | `regime.py:130-150`, `card_png.py:695` |
| P10 | **UTC cron**: `CronCreate` runs in UTC. The first attempt fired all evening | Compute the window in ET inside the script and run the scheduler every 2 min in any zone | CP:896-915 |
| P11 | **2026-11-01 DST**: the UTC crons shift an hour early (open 17:00, close window 14:00–14:28) | ET-in-script makes this a non-event. If crons are kept, re-cut to 23 / 0-19 / 20 that day | CP:917-920, RULES B24 |
| P12 | **Session-only crons die** with the worker (twice on 2026-09-28) | Use a durable system scheduler. Still check "last run < 5 min" from `desk_status.json` | CP:972-991 |
| P13 | **Silence outside the window**, but still verify the schedule | No card and no wake outside the window. Queue events for the 18:00 run | CP:948-991 |
| P14 | **PENDING at 15:30 goes unwatched until 18:00** | The closing card says so. `resolve` is retrospective, so it catches up correctly | CP:210-214, 934-936 |
| P15 | Win rate is **never quoted without payoff**. Stand-downs are stated as decisions, never as "no setup" | Both go in the JSON and on the card | CP:196-199, 813-815 |
| P16 | Location % always carries its range endpoints | Keep the `[lo, hi]` from `chart.bias` | CP:704-710 |
| P17 | Colours fixed (27 / 208 / 250; PNG uses the same hues). Grey never means a live direction | Reuse `card_png` and `status_card` unchanged | CP:285-307, 331-337, 387-391 |
| P18 | MGC DAILY/WEEKLY are NOT ELIGIBLE (roll audit fails) | Reuse `regime.NOT_ELIGIBLE` | CP:413-426, `regime.py:46-51` |
| P19 | Opposing plan on the same symbol within 1 ATR14(15m) must wait | Add this veto at registration | CP:1133-1138 |
| P20 | No breakout entry in the direction of displacement (\|c − EMA20\| > 0.5 ATR with the slope agreeing) | Add this veto at registration; it's missing from the live tools | CP:712-744, `cont1.py:79-100` |
| P21 | Sizing ladder is taken over the **usable** buffer. $2,600 is the operational floor, $2,800 the absorbing state | Use `AccountConfig`, not the hard-coded 240/120 | CP:117-143, `status_card.py:35` |
| P22 | Snapshot filenames need **second** resolution (a delta is the only copy of a revision) | Only matters if `fetch.py` deltas are kept. `BarArchive` writes atomically (`archive.py:209-227`) | CP:61-66 |
| P23 | Don't commit tracked files every 2 min (stop hook, repo bloat) | Keep the live store and status files gitignored. Commit only on PLAN_EVENT | CP:242-266 |

_Paper only. Nothing here places orders._
