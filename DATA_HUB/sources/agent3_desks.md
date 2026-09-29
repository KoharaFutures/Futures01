# Sweep agent 3 — the two paper desks (CALL live, REPLAY walk-forward)

Written 2026-09-29 by sweep agent 3 on branch `claude/admiring-heisenberg-doycyh`. Read-only sweep: nothing
moved, deleted or committed. **PAPER — UNVALIDATED throughout. Neither desk has a measured edge.**

Sources (all under `/home/user/Futures01/`): `CALLOUT.md`, `REPLAY.md`, `workspace/paper/CALL/{state.json,
LEDGER.md, journal.jsonl, pending.jsonl, DECISIONS.md, CONSOLIDATION.md, CHECK_PROCEDURE.md, FINDINGS_INDEX.md,
NOTES.md (N1–N264), *.py, data/}`, `workspace/paper/REPLAY/R1/{state.json, SUMMARY.md, NOTES.md, callouts.jsonl,
missed.jsonl, journal.jsonl, agents/*}`.

| desk | status | instrument / frame | period | owner of record |
|---|---|---|---|---|
| **CALL** | **PAUSED by owner 2026-09-29 00:58 ET** ("stop your call outs for now"); all crons deleted, Routine `trig_01NZGwNRd8mftXdxyLvuVpdD` disabled (N264) | MGC + MNQ, 15m gate, 1m/5m/15m/60m/4h/D/W read | live tape 2026-09-27 18:00 → 2026-09-29 00:47 ET | session `session_01EE6PFk7fGa2tM4KP6dpfWD` |
| **REPLAY R1** | **ACTIVE** (scheduled session, other branch); cursor 3400/11287 at last commit `90e2b0c` 2026-09-29 04:46Z | MES 60m, harness `workspace/roundtable/lib/replay.py` | bars 2024-10-06 19:00 → 2025-05-12 11:00 ET | session `session_01Aqg8aVp7jcAbzEF7sfZYjA` |

---

## 1. Trade ledgers

### 1a. CALL desk — every callout id (11 plans + 9 NO-TRADE journal rows)

Costs charged by `resolve.py:costs_per_contract` (fees + 1 tick/side): **MGC $3.44 RT, MNQ $2.44 RT**. All fills 1 contract.
R below is net of costs, from `state.json`.

| id | sym | side | entry type / price | stop | target (TP1) | risk $ | outcome | R | net $ | reason given (thesis, abbreviated) |
|---|---|---|---|---|---|---|---|---|---|---|
| CALL-0001 | MNQ | LONG | stop-entry 30998.50 (Fri 09-25 session high) | 30938.50 (60 pt) | 1.6R | 120 | **VOID_UNREACHABLE** 09-28 11:55 — 6.28 ATR away, 18 bars left (N202/N204) | 0 | 0 | BREAKOUT continuation above prior-session high; MNQ at 91% of 30-day range; `thesis.py`: DIRECTION WRONG (adv 251.75) |
| CALL-0002 | MGC | SHORT | stop-entry 4289.10 (Fri low = Sun low, "twice tested") | 4299.10 (10 pt) | 4273.00 (1.6R, 30-day low) | 100 | **Filled 4186.40** (gapped 102.70 pt past trigger), TP1 4170.40 → WIN | +1.566 | +156.56 | BREAKDOWN through twice-tested support. **EXCLUDED from desk stats (N155)** — created_bar_ts stamped in future/off-grid, resolver blind 6 h, filled at far end of a finished move; exclusion declared while in profit |
| CALL-0003 | MNQ | LONG | stop-entry reclaim 30767.25 (5m swing high) | 30715.25 (52 pt, under session low 30720.25) | 30850.70 (1.6R) | 104 | EXPIRED untriggered 02:00 ET | 0 | 0 | REVERSAL: −2.03σ with 4h/D/W bullish; DIRECTION WRONG (adv 105.25 vs 52 stop) |
| CALL-0004 | MGC | SHORT | sell-limit 4287.60 (50% fib of 4336.00→4239.20, 1.5 under broken 4289.10 shelf) | 4299.50 (above 61.8% 4299.02) | 4268.56 (1.6R) | 119 | EXPIRED untriggered 06:00 ET | 0 | 0 | FIB forward-projected sell; `thesis.py`: **DIRECTION RIGHT, entry unreachable** (fav 25.90 vs 19.04 needed) |
| CALL-0005 | MNQ | LONG | buy-limit 30595.88 (50% of 15m leg 30547.75→30644.00) | 30540.00 (55.88 pt) | 30679.69 (1.5R) | 111.75 | EXPIRED 09:30 ET; price traded through the limit 1 min later; counterfactual would have stopped −1R (N179/N185) | 0 | 0 | REVERSAL headline + fib pullback; bought at the day's high window (N194 cause 2) |
| CALL-0006 | MNQ | SHORT | sell-limit 30560.00 (under falling EMA20 30574.60) | 30618.00 (17 above 30601 swing high) | 30473.00 (1.5R) | 116 | Filled & stopped same 15m bar 12:15 (MFE +0.84R, HEAT 1.14); price ran +84.5 past stop | −1.021 | −118.44 | REVERSAL headline + EMA20 pullback; blind-spot excursion 202.5 pt vs 58-pt stop (N214) |
| CALL-0007 | MGC | SHORT | sell-limit 4159.00 (under 4159.40 evening swing high + EMA20 4159.79) | 4163.40 (4.4 pt = 0.69 ATR) | 4152.40 (1.5R) | 44 | Filled 19:15 bar (gate had lapsed pre-fill), TP1 20:00 → WIN; MFE +1.66R, HEAT 0.61 | +1.422 | +62.56 | REVERSAL 0-3 unanimous 15m; outside MGC RTH, sized 18% of permitted |
| CALL-0008 | MNQ | LONG | buy-limit 30588.00 (between 30586.75 higher low and rising EMA20 30590.05) | 30565.00 (23 pt = 0.61 ATR) | 30622.50 (1.5R) | 46 | Filled 19:45, stopped 20:15; MFE +0.83R, HEAT 1.43 | −1.053 | −48.44 | REVERSAL 3-0 bull 15m; 60m/4h disagreed; evening vol 5.5% of RTH |
| CALL-0009 | MGC | SHORT | sell-limit 4157.50 (0.69 under EMA20 4158.19) | 4161.60 (0.8 over 4160.80 lower high) | 4151.35/4151.40 (1.5R) | 41 | Filled & stopped on 21:15 bar **which also traded through TP1** (MFE +2.24R); resolver takes stop (entry-bar rule) — the one real ambiguous bar (N235/N253) | −1.084 | −44.44 | REVERSAL 0-3 held 2 checks; N233: sub-EMA limit migrated above falling EMA → filled as gate died |
| CALL-0010 | MNQ | SHORT | sell-limit 30550.00 (20.68 under EMA20, 18 under broken 30568 pivot low) | 30576.00 (26 pt) | 30511.00 (1.5R) | 52 | **PENDING, UNRESOLVED** — expiry 2026-09-29 09:30 ET passed with no checks running; nobody may hand-write EXPIRED (N264). Price last 30427.25, ~123 pt below limit. `thesis.py`: DIRECTION RIGHT, TARGET DISTANCE COVERED — trigger was the problem | — | — | REVERSAL 0-3 on two reads of ONE 15m bar (N231 violation, disclosed); retrace to underside of broken structure |
| CALL-0011 | MGC | LONG | buy-limit 4161.00 (0.49 over rising EMA20 4160.51, 0.80 over 38.2% 4160.20 of 4145.00→4169.60) | 4156.40 (1.5 under 4157.90 higher low) | 4167.90 (1.5R, 1.7 under 4169.60 high) | 46 | Filled 00:00 bar (gate died same bar), +1.00R MFE then stopped 00:30; HEAT 1.00 | −1.075 | −49.44 | First bullish gate; 60m/4h bearish; only 1m/5m agreed |

NO-TRADE journal rows: CALL-NT-0001 (MGC, stale Sunday quote 4321.20 = prev close), CALL-NT-0002 (MNQ, same), CALL-NT-LATE-MGC
(owner asked 4235: already traded & rejected at 4235.10, N16), CALL-NT-LATE-MNQ (reversal_setup qualified, trigger slid 30767.25→30735.25),
CALL-NT-0003/0004 (MNQ reversal_setup qualified −1.87σ / −1.83σ with 1.94× flush; declined — sizing/decay), CALL-NT-0005 (+2 amendments,
MGC N75 retracement method VOID, condition 1 failed by 0.30). Plus 39 priced decisions in `DECISIONS.md` (rows 1–39).

**Plan dispositions:** 11 plans → 6 TRIGGERED, 3 EXPIRED, 1 VOID_UNREACHABLE, 1 PENDING (stale). Fill rate 6/10 resolved = 60% (CONSOLIDATION says 55% = 6/11).

### 1b. CALL summary stats — three different "records" exist

| basis | n | W/L | win rate | payoff (avg W R / avg L R) | expectancy | net $ | equity | peak | max DD |
|---|---|---|---|---|---|---|---|---|---|
| **`state.json` / `LEDGER.md`** (all closed, incl. CALL-0002) | 6 | 2/4 | 33.3% | **1.41** R (1.494/1.058); $-payoff 1.68 ($109.56/$65.19) | **−0.207R** | −41.64 | **$49,958.36** | $50,156.56 | **$198.20** (0.4%; $2,601.80 to $2,800 absorbing state) |
| **Desk "measured record"** (N155 excludes CALL-0002; N263/N264, DECISIONS row 39) | 5 | 1/4 | **20%** | **1.34** | **−0.562R** | −198.20 | (would be $49,801.80) | $50,000 | $198.20 |
| `CONSOLIDATION.md` §1 (written 00:45, **stale** — before CALL-0011 closed) | 4 measured / 5 closed | 1/3 | 25% | 1.35 | −0.434R | +7.80 | $50,007.80 | $50,156.56 | $148.76 |

Equity path (state.json): 50,000 → 50,156.56 (0002) → 50,038.12 (0006) → 50,100.68 (0007) → 50,052.24 (0008) → 50,007.80 (0009) → 49,958.36 (0011).
Exits: **6/6 fills reached ≥ +0.83R MFE; losers' mean MFE +1.23R; mean HEAT 1.08** (N261/N263). `LEDGER.md` says "ambiguous-bar resolutions 0" but
N253 shows CALL-0009 is ambiguous and structurally uncountable by `resolve.py:556`. Placebo/counterfactual: **none exists** (CONSOLIDATION §2).

### 1c. REPLAY R1 — every callout (51 = 2 trades + 49 NO_TRADE)

Harness fills next bar open + 1 tick; commission $2.69 RT charged in net/R; 3 contracts each (ladder ×1.0, permitted $240).

| id | bar / as_of (ET) | side | entry | stop | target | R:R | contracts / risk | outcome | R | net $ | reason given |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R1-00014-b000453 | 452 / 2024-11-01 10:00 | SHORT | 5791.75 | 5804.00 | 5768.00 | 1.94 | 3 / $183.75 | TARGET 13:00 | **+1.895** | +348.18 | Failed retest of broken 5801 range low: bar poked 5803.0, closed 5792.0 on 203k (heaviest bar); downtrend LH 5927→5770.5; pre-stated method (bar 431) |
| R1-00033-b001340 | 1339 / 2024-12-31 09:00 | SHORT | 5973.25 | 5985.50 | 5950.00 | 1.90 | 3 / $183.75 | TARGET 11:00 | **+1.854** | +340.68 | Failed retest of broken 12/27 low 5982.75 (rally 5983.5, close 5972.0); **level identified post-hoc at the bar, off-process** (disclosed; agent C/D) |

State (`REPLAY/R1/state.json`): equity **$50,688.86** = peak, **DD $0**, 2 closed, cursor 3400, callout_seq 51.
Win rate 100% (2/2), payoff undefined (no losers), mean +1.875R. **Placebo separation z +1.021 vs free_t(20) 2.448 — does not clear**; `t +91.66`
is an n=2 sd-collapse artefact. Counterfactual on stand-downs (n=48): always-long +0.299R vs control +0.383R (z +1.88), always-short +0.004 vs
−0.024 (z −0.13), coin-flip +0.259 vs +0.290 (z +1.41) — **nothing |z|≥2**. Geometry sweep (agent A): 0/36 cells reach |z| 2. Search width
**20 theses / 297 desk-wide (free_t 3.37)**. Largest |z| anywhere +4.30 = broken 18:00 volume field, not a trade.

Notable REPLAY non-trades that resolved (counterfactuals written in `why`): bar 263 tick-through of 5865 range low would have lost −1R;
bar 291 acceptance break of 5865 missed ~+2R; bar 413 break of 5837.5 compression low missed ~+2.3R; bar 428 break of 5801 missed (late);
coil 6021/6032.5 both legs −1R (bars 607/612); 6053.25 failed-retest long would have lost −1R (bar 921); bar 1502 failed retest of 5845
declined on rule-4 floor → would have won ~+2R; 5868 fired 3× → all would have lost; 6032 **gapped through** (R:R 2.00→1.55, declined);
6045.50 break missed ~+1.68R (bar 1618–1621). Net of misses ≈ a wash (NOTES burst 6/8).

### 1d. state.json vs measured — differences to carry

1. CALL `state.json` counts CALL-0002 (+$156.56); desk policy (N155) excludes it → −0.207R vs −0.562R. Both are "true"; quote which.
2. CALL-0010 sits PENDING past its 09:30 ET 09-29 expiry — `state.json`/`pending.jsonl` are stale until one `resolve.py` run.
3. `LEDGER.md` ambiguous-bar count 0 is wrong by 1 (N253).
4. CONSOLIDATION §1 CALL column is stale (5 closed, +$7.80, DD $148.76). REPLAY column says "50 callouts / 2 fills" — now 51.
5. REPLAY `SUMMARY.md` "51 decisions (2 trades, 49 stand-downs)" matches callouts.jsonl; REPLAY's pre-E5 study R figures (missed/levels/thesis-5) were **gross of the $2.69** (E5).

---

## 2. Durable lessons / rules (with source and one-line why)

### Risk & sizing
| rule | source | why |
|---|---|---|
| Budget = min(usable×0.06, eq×0.0075, 500) × ladder; **$240 at DD 0**; **DEAD at DD $2,800** ($21.60 < $25 min), `has_failed` stays False; operational floor **$2,600** | CHECK_PROCEDURE Step 3, N2 | absorbing state is one $100 step wide |
| **Size ≤ 50% of permitted while DISCRETIONARY** ($120 cap at DD 0) | CHECK_PROCEDURE Step 3; CALLOUT §1 | only result in programme clearing its threshold: size-shrinking governors net protective, |z| 6.164/5.543 vs free_t 2.229 |
| Cap the **BOOK** (open + pending `risk_dollars_intended`), not open only | N249 | `capacity()` reported $120 room when $22 remained |
| At $240 MGC 1-ATR(daily) stop does not fit; MNQ exactly 1 contract | N3 | ATR vs budget |
| 5 of 9 shipped exit models need 10 contracts — unexecutable at this size; **50% partial impossible at 1 lot** | N6, CONSOLIDATION §8.2 | the "+0.8R half-off" idea was unexecutable; use stop-to-BE at +0.8R instead |
| `RiskManager.evaluate()` vetoes every DISCRETIONARY callout | N1 | conflict between CALLOUT risk rule and paper-mode confidence |
### Session / hours
| rule | source | why |
|---|---|---|
| **Flat 16:00 ET, nothing held 16:00–18:00** (owner); costs **0.0032R/trade**, 95% CI [0.016 saved, 0.022 spent] | REPLAY E4, SUMMARY #8 | scratches winners & rescues losers equally — keep it |
| No entries 15:00–16:00 ET (z −4.43, median −0.617R) | BRIEF rule 5; REPLAY E6 | census cannot replicate a direction-selected result (z +0.10 on MES census) — keep |
| No hours filter improves expectancy: 0/22 hours clear | rule 6; REPLAY E6 | lunch-avoidance etc refuted |
| MGC RTH 08:20–13:30, MNQ 09:30–16:00, MCL 09:00–14:30; outside = unmeasured territory, say so | CALLOUT §3, CHECK_PROCEDURE Step 4 | `rth_only=True` on every generated strategy |
| Decline short-runway trades because the bracket can't operate (flat decides 79% at 1–2 bars), **not** because R is worse | REPLAY E4 | runway doesn't predict expectancy (|z|≤0.39) |
| **Cron timezone bug:** `CronCreate` runs in container UTC; windows written in ET fired 14:00–19:59 ET. Re-cut on **2026-11-01** (EDT→EST) | DECISIONS row 18 | desk fired ~40 stray times |
| Session crons die with worker restarts (twice: ~12:55, before 18:00) → verify by `CronList`, never by memory; out-of-window hourly must still verify | N215, DECISIONS row 19, CHECK_PROCEDURE | 34–44 min lost silently |
### Data / feed
| rule | source | why |
|---|---|---|
| Feed lag median **12.9 min at 5m** (80 samples), ~23 min at 15m; a 10-min trade is impossible; scalps floored ~30 min | N7, CHECK_PROCEDURE | Yahoo not real-time |
| `lag` measured from bar OPEN stamp → a frame reads L+δ..2L+δ when current | N60 | 117 min on 60m is normal |
| **Provisional bars:** newest 1–2 bars revise; 15m bar settles at **stamp+28/29 min** (last revision median +12.3 min after completion, p90 +14.2) | N41, N65, N89 | a break on an unsettled bar is not a break |
| Break-depth test: largest non-session-open 15m revision — lows MNQ 27.25 / MGC 6.80; highs MNQ 19.75 / MGC 6.20; 18:00 bar revises most (74.00/20.00) — exclude it | N70, N89 | calibrated "is this a real break" |
| `new=0 revised=1` ⇒ any changed reading is a revision/window slide, never price | N140, N55 | 2 of 3 checks carry no new settled data |
| Sunday reopen: vendor stamps live time on stale price (o=h=l=c=prev close, v=0) — stub; reject `v==0 and h==l` | N5, fetch.py | "the one error that costs money" |
| Truncated per-frame pulls (5m went 95 min backward) — `fetch.py` headline reports pull not store; per-symbol BLIND at 20 min 1m age | N19, N255, N256, N258 | feed not down, just stale on some frames |
| **26% of MGC/MNQ 5m & 15m bars have NO volume field** (identical 102 timestamps on both) → `climax_x` reads 0 as "no capitulation" | N262 | vendor omission; volume claims unsupported |
| MES 60m 18:00 ET bar zero-volume 79% (Mon–Thu 100%, Sun populated) while widest overnight hour (z +4.30) | REPLAY SUMMARY #7, E6 | never condition on 18:00 volume |
| MES 60m contains contract-merge regions: bars 1146–1158 (Dec-24) and **2517–2591 (Mar-25)**; ~5.3% of tape; SERIES_AUDIT misses it | REPLAY SUMMARY #6, C_merge.py | any roll-week result measures the calendar spread |
| MGC 1440m 09-28 bar low 4111.30/close 4136.40 vs intraday 15m low 4143.00/close ~4158 — different contract/roll; MGC daily unusable unadjusted | this sweep; CALLOUT §4 | never mix daily and intraday MGC levels |
| No delta/orderflow exists — OHLCV only | N221, CALLOUT §5 | anyone quoting "delta" is guessing |
| Quote entries from traded prices, never a derived close (`open[i+1]!=close[i]` 57–80%) | CALLOUT §4 | fill is next open |
### Entries, gates, exits
| rule | source | why |
|---|---|---|
| **PROHIBITION: no breakout entry in direction of displacement** (CONT-1: E −0.23..−0.36R, t −3.6..−5.1; **z −2.61..−4.72 vs placebo, 4/4 cells**) | N195/N196, CHECK_PROCEDURE, cont1.py | measurably worse than random |
| FADE-1 (inverse) is dead: largest t +1.245 on untouched MES/MCL | N197/N198 | rule 3: flipping a loser gives zero, not a winner |
| **Win rate and payoff cancel — never quote apart** (CONT-1 26–32%/1.45 vs FADE-1 41–48%/1.36) | BRIEF rule 3, N198, LEDGER | |
| **Volatility stand-down:** no plan when P(27-min blind-spot excursion > max stop) > 25% ≈ **MNQ ATR14(15m) > 58, MGC > 10** | N214, CHECK_PROCEDURE | at MNQ ATR 97.5, 69.4% of windows exceed the 60-pt cap stop |
| Unreachable-void: void pending when `distance_ATR > 1.2·√bars_remaining` (10% reach contour) | N202, resolve.py `unreachable()` | CALL-0001 sat 17 h at 6.28 ATR |
| Don't edit a pre-registered plan after watching price (N8); new void rules only pre-registered | N8, DECISIONS rows 21–22 | 19:00 "gate lapse" was a revision that reverted |
| 15m unanimity does NOT mark turns (2,134 onsets, max |t| 1.61) | N213/N214 | contrarian story false |
| Persistence must be a NEW or REVISED bar, not a new check; `held` counter counts invocations | N231, N248 | `reversal()` anti-whipsaw was vacuous at 2-min cadence |
| `reversal()` can't fire on continuation days (needs prior differing headline); `swings()` compares last 2 pivots → strips unanimity mid-trend | N194 causes 1/3, N199 | desk flat through 3×ATR day (MGC −90.2, MNQ −402.75 pts) |
| Limits anchored to a moving EMA decay into the gate's death (3/3, 2 fills) → anchor to fixed structure | N233, N257, CONSOLIDATION §5.5 | fills happen on the bar that inverts the gate |
| Moving entries toward market to get fills = the leak (CALL 55–60% fill vs REPLAY 4%) | CONSOLIDATION §4 | |
| **6/6 fills reached ≥ +0.83R MFE, 2 closed positive** → test (pre-registered) stop-to-BE at +0.8R on 1 lot; then full exit at 0.8R (needs ~55% WR) | N261, N263 | the exit, not the entry, returns the move |
| Resolve on entry bar: stop only, never target (same-bar TP credit invents wins) | resolve.py, N235 | honest pessimism |
| Resolve stops on finest frame (1m) — specified, not installed | N214(B) | cuts blind spot 15–27 → ~12 min |
| Structural stop ≥ 0.5 ATR (rule 4) — but it is a **smooth cost gradient, not a cliff** (−0.267R at 0.25 ATR → +0.033R at 1.5 ATR; ~52% cost) | BRIEF rule 4; REPLAY agent A, E5 | floor refused a +2R winner (bar 1502) |
| A stop can pass the ATR floor and still be in the wrong place (must clear the invalidating low) | N236 | |
| Pullback trigger for "don't chase": measure extension from the pullback, not the swing origin | N194 cause 5 | old test was a permanent veto on trend days |
| Two-bar acceptance triggers need the replay standing ON the confirmation bar → `watch.py` halts on armed conditions | REPLAY burst 3/11, watch.py | 5 missed triggers from chunked advance |
| Gapped-through level: if gap cuts R:R < 1.5, plan VOID, re-arm | REPLAY burst 10 | 4th scenario branch |
| Costs: MES $2.69 RT = 2.15 ticks → hurdle **0.081R** vs gross +0.0225R; MGC $3.44 (0.0748R on CALL-0011); MNQ $2.44 = 4.88 ticks (0.0469R on CALL-0010) | REPLAY E5, CONSOLIDATION §8.1 | "any structure at 60m is smaller than the cost of trading it" |
| **Costs vs structure:** hurdle falls 0.1019R (low ATR) → 0.0756 (median) → 0.0365R (ATR 21.6); vol is the only lever, moves it 3× | REPLAY SUMMARY #4, burst 16 | a cost claim, not an edge claim |
| MES 60m is a random walk (VR p ≥ 0.74; naive ACF p 1e-7 is kurtosis-24 artefact); volatility predictable (R² 0.112) and directionless | REPLAY E2 | use vol to size/stand down, never for direction |
| Stand-downs cost nothing measurable (0/36 geometries |z|≥2); 19% of stand-downs lose both ways | REPLAY SUMMARY #5 | but CALL's morning stand-down foreclosed up to $902/$805 per contract (upper bound) |
| Price every decision (foreclosed upper bound / marginal / realized) | DECISIONS.md, N218 | a veto that is never priced always wins |
| Every check emits a card; card commands take parameters, never hand-typed numbers; LONG blue 27 / SHORT orange 208 / NO TRADE grey 250 | N217, N222, CALLOUT | owner reads cards only |
| Tool must not disagree with its authority (`watch.py` 66/34 vs `chart.py` 60/40 location → ~22 pt wrong; own pivots; slope) — `watch.py` decides nothing | N228, N240, N241, N249 | 5 tool-vs-rule disagreements in one session, all errors toward caution ("luck, not a safeguard") |
| Scan the side the headline is NOT on, every check (`counter_trend()`) | N234, CHECK_PROCEDURE | missed owner's MNQ 30430 / MGC 4145 longs |
| `reversal_setup()` extension & reclaim conditions anti-correlated by construction — qualifies only when not entrable; sigma latency-sensitive | N252, N234 | detector sees flushes only after they've gone |
| Volume at 1m/5m bounces says nothing directional (24 cells, max |t| 1.97, non-monotonic) | N221 (VOL-1) | owner asked; null |
| REPLAY: "two fabricated figures reached live decisions; both pushed toward safety — luck, not a safeguard"; prose had 27 errors all leaning the author's way | REPLAY SUMMARY, agent B | put numbers in code, not prose |
| Declare search width; thesis 5 retired at 105 declared cuts (free_t 3.05, FW p 0.86, OOS sign flip) | REPLAY E8 | in-sample z 3.62 flipped to −2.01 OOS |
| Commit only paths you own (not `git add -A` on a lane with concurrent writers) | REPLAY NOTES (E4/E6) | swept partial files |

---

## 3. Per symbol — setups tried, ranked as candidate strategies by evidence

Evidence rank (best-evidenced first). **None clears its threshold.** "Neg" = evidence against.

| rank | candidate | symbol(s) | evidence | verdict |
|---|---|---|---|---|
| 1 | **Breakout-continuation (CONT-1)** as a PROHIBITION | MGC, MNQ 15m/60m | n=121/444/125/498, E −0.364/−0.276/−0.360/−0.226R, z vs placebo −2.61/−4.72/−3.25/−2.97 | **Strong NEG → installed veto** |
| 2 | Volatility stand-down (veto, not a strategy) | MNQ, MGC | 27-min excursion table (~3,645 origins/sym) | installed |
| 3 | **Level bounce / fade at detected S/R** | MES 60m | fair control (E9 D): bounce arm z +2.52 (seeds +1.57…+3.20) but real levels earn **+0.043R < 0.081R hurdle**; separation from control being worse (−0.294R) | best "bounce" evidence; net unprofitable; pre-register if pursued |
| 4 | Failed retest of broken level ("thesis 5") | MES 60m | 2/2 live wins (+1.895, +1.854R, 1 off-process); mechanised Tier A n=444 **+0.025R, 38.1% win, z +0.59**; 105-cut predicate search FW p 0.86 | **retired** |
| 5 | Stop-to-breakeven at +0.8R (exit overlay) | MGC, MNQ | 6/6 fills MFE ≥ +0.83R; losers' mean MFE +1.23R; untested on archive | **top untested hypothesis** — pre-register & backtest |
| 6 | FADE-1 (fade 3-bar breakout) | MCL, MES (MGC/MNQ contaminated) | MCL 15m +0.148R t 1.245 z +2.70 vs placebo; MCL 60m −0.009 (z +1.46); MES 15m −0.049, 60m −0.015; MGC/MNQ contaminated +0.01..+0.05 | dead (fails t>3, fails MCL 60m) |
| 7 | Range-edge acceptance break (close beyond + fail to reclaim) | MES 60m | ~4 counterfactual fires: 2 missed ~+2R winners, 1 missed +1.68R, coil version 2× −1R; not mechanised | anecdotal |
| 8 | 15m 3-component unanimity **reversal gate** (`regime.reversal`) + EMA20/structure pullback limit | MGC (0007 W, 0009 L, 0011 L), MNQ (0006 L, 0008 L) | live 1W/4L measured, −0.562R; unanimity onsets null (2,134, max |t| 1.61); gate defective (N194/N225/N248) | NEG-leaning; do not resume without placebo |
| 9 | Fib retracement pullback (50%/61.8%/38.2%/78.6%) | MGC (family generated), MNQ (family EXCLUDED by profile) | CALL-0004 unreached (direction right), CALL-0005 expired then −1R counterfactual, CALL-0011 L; no random-level control ever run | untested |
| 10 | `reversal_setup` counter-trend (|σ|>1.5 into ≥2 HTF, reclaim trigger) | MNQ mostly | qualified ~8 times, never traded; anti-correlated conditions (N252); CALL-0003 direction wrong | structurally near-untradeable |
| 11 | Prior-session-high breakout stop-entry | MNQ | CALL-0001 void, direction wrong; also a CONT-1 relative | NEG |
| 12 | Volume/climax confirmation | MGC, MNQ | VOL-1 null; 26% missing volume | NEG |

Per-symbol notes:
- **MNQ** (live, 15m): 6 plans, 2 fills, 0 wins (−1.021, −1.053R). Programme: sign z +3.41 on 15m rth_only=False, deflated 2.17 — misses; down-tape third z +0.19. Blind-spot risk worst here (ATR 46–98 on 09-28). Round-turn 4.88 ticks.
- **MGC** (live, 15m): 5 plans, 4 fills, 1 counted win (+1.422), 2 losses, 1 excluded win. Profile generates FIB, not BREAKOUT/VWAP. N213 incidental: MGC 60m directional headline → +0.1575 ATR at T=16, t 3.29 (continuation), one cell of 12, not acted on. MGC daily/weekly NOT ELIGIBLE (roll).
- **MES** (replay, 60m): 2 trades both W; random walk; cost dominates; thesis 5 retired; desk "will not trade this instrument again until" a pre-registered predicate survives OOS.
- **MCL**: only FADE-1 test (above). Programme max t +1.12 < 1.177. MCL 60m thin 2026-01-12→03-10; no daily.

---

## 4. BOUNCE LEVELS — every level the desks named, held vs broke, stated reasoning

### 4a. Level-quality measurements (the only controlled evidence)

| study | sample | result |
|---|---|---|
| REPLAY `levels.py` v1 (asymmetric) | MES 60m | 83.1% "bounce" — artefact; random lines scored 77% |
| REPLAY `levels.py` symmetric (both on close, same distance) | fresh 1-touch n=162 / retested 2+ n=175 / random n=200 | bounce 45.7% / 53.7% / **55.0%**; trade arms +0.048/+0.060/+0.036R — "retested levels sit on top of random" |
| touch-count buckets 2/3/4/5/6+ | | 48.6/52.9/63.6/70.0/54.3% vs control 53.6/54.7/60.0 — **WITHDRAWN** (control fabricated touch counts `rng.choice([2,2,3,4])`) |
| support vs resistance | | support bounces 59.4% but trade −0.084R; resistance 47.9% but +0.213R — rule 3 inversion |
| with-trend vs against | | 55.7% vs 52.0%; control 54.3 vs 55.8 — nothing |
| **E9 fair control** (touch-matched, count-matched, decontaminated, ATR-matched, 10 seeds) | 32,195 level-instances | bounce trade arm z **+0.08 → +2.52**; break arm +1.17 → −0.82; "fresh extreme breaks more" −8.8pp z 1.76 → **−3.9pp z −0.73 (RETRACTED)**; real levels +0.043R vs control −0.294R; below 0.081R hurdle |
| Control was unfair because | | ATR at test 11.64 real vs 15.22 control (×1.308); 20.9–46.8% of random lines landed on real levels; 0% 1-touch vs 58.7% real |
| Session 99X1 key-level breach scan (outside this lane, cited in CONSOLIDATION §3) | 5,717 real vs 4,729 placebo levels | **indistinguishable** |
| CALL: no level was ever tested against a random-level control; FVG/order-block fill rates reproduced by random zones (rule 8) | — | CALL touch-count claims (4145 "five-times-tested", 30425–30434 base) **withdrawn as evidence** (CONSOLIDATION §8.4, N262) |

### 4b. CALL desk levels (MGC / MNQ, 2026-09-25 → 09-29)

| symbol | level | type | stated reasoning | what happened |
|---|---|---|---|---|
| MGC | **4289.10** | Fri 09-25 low = Sun reopen low ("twice tested") | support; short on break (CALL-0002) | **BROKE** — fell to 4172.60 (05:00) and 4143.00 (10:45) |
| MGC | 4287.60 / 4299.02 | 50% / 61.8% fib of 4336.00→4239.20 | forward resistance (CALL-0004) | never reached (price fell away) |
| MGC | 4235 (4235.10) | owner-named | — | **HELD as resistance** (22:55 bar high 4235.10, closed 40-bar low 4227.30) |
| MGC | 4233.20 | 09-28 00:30 session high | | held (day high) |
| MGC | 4174.30 → 4172.60 | overnight settled lows | double-low area | broke by 1.70 (inside revision range, N70) then round-tripped (N93) |
| MGC | 4185.20 / **4193.10** | settled lower highs | N99: 4193.10 decisive | **HELD** — 15m 4191.40, 5m spike 4193.40 rejected 8.20 in one bar (N119) |
| MGC | 4203.80 | 08:15 high at RTH open | | held; RTH decline −60.8 to 4143.00 |
| MGC | **4143.00–4146.50 shelf** | 09-28 10:45 session low (leg origin of +38 to 4181.00), 40-bar range floor; lows 4143.00/4143.90/4146.30/4145.50/**4145.00** | owner: "4145 should have been a long"; 95% retracement of up-leg; 3.12× "flush" volume (now unsupported, N262) | **HELD / BOUNCED**: 4145.00 (21:00) → 4155.90 (+10.90, $109/ct), → 4169.10 (21:45), 4171.70 (23:30) = **+26.70**. Not traded (N234 blindness) |
| MGC | 4159.40 / EMA20 4159.79 | evening lower swing high | resistance (CALL-0007) | **HELD** → short won +1.422R |
| MGC | 4160.80 / 4161.70 | lower swing highs | resistance (CALL-0009) | **BROKE** (21:15 bar h 4163.10, also hit TP) |
| MGC | 4160.20 38.2% + EMA20 4160.51, higher low 4157.90 | pullback support (CALL-0011) | support | filled, +1.00R, then **BROKE** (stop 4156.40, 00:30) |
| MNQ | **30998.50** | Fri 09-25 high | breakout (CALL-0001) | never reached (void) |
| MNQ | 30767.25 → 30735.25 → 30661.75 → 30637.75 | reclaim triggers (5m swing high, sliding) | reversal reclaim | never reclaimed |
| MNQ | 30720.25 | 09-27 evening session low | stop anchor (CALL-0003) | broke (adv 105.25) |
| MNQ | **30571.00 double bottom** | settled swing lows 30571.00→30571.00 | N66: "not trading a double bottom into a bearish stack (rule 8)" | **BROKE** on settled 05:00 bar (low 30536.25, −34.75), then **sweep-and-reclaim** +44 (05:15 close 30587.25, low 30535.00), then half faded on revision (N74/N79) |
| MNQ | 30547.75 → 30644.00 leg, 50% 30595.88 | fib pullback (CALL-0005) | support | price ran away to 30759.25 (09:30 high), then traded through; would have stopped −1R |
| MNQ | 30759.25 | 09-28 RTH open high (unanimous-bull top) | — | held (day high); −402.75 to 30356.50 by 10:45 |
| MNQ | 30601.00 / EMA20 30574.60 | 10:15 swing high | resistance (CALL-0006) | **BROKE** — squeezed to 30722.00 (202.5 pts in blind spot) |
| MNQ | 30356.50 | 09-28 day low 10:45 | — | held; +365.5 leg to 30722.00 |
| MNQ | 30586.75 higher low / EMA20 30590.05 | support (CALL-0008) | | **BROKE** (stop 30565, 20:15) |
| MNQ | 30568.00 broken pivot low (underside) | resistance (CALL-0010) | | never retested — price fell ~140 pts |
| MNQ | **30430.00** = 78.6% fib of 30356.50→30722.00 (30434.72) + morning 10:30 base 30425.25–30434 | owner: "beautiful buy at 30430"; reversal_setup qualified −2.80σ, D+W support | **BOUNCED then BROKE then HELD**: 21:15 low 30430.00 → 30537.75 (22:15) = **+107.75**; broke to **30412.50** (23:00, −17.5 through); higher low 30427.75 registered (N260); back at 30427.25 at 00:47 in full bearish cascade |

Scorecard (CALL levels with a resolved touch): **held/bounced 7** (4235, 4193.10, 4143–4146 shelf, 4159.40, 30759.25, 30356.50, 30430 first touch), **broke 9** (4289.10, 4172.6-area [provisional], 4160.8, 4157.9/4160.2, 30720.25, 30571 [then reclaimed], 30601, 30586.75, 30430 second touch). Uncontrolled; n tiny; 4/5 filled level trades by the desk broke.

### 4c. REPLAY desk levels (MES 60m, 2024-10 → 2025-05)

| level | type | reasoning | outcome |
|---|---|---|---|
| 5795–5808 | visible supply overhead (bar 39) | resistance | declined (extended run) |
| 5914.0 | prior RTH close (bar 136) | overnight must hold it for RTH-open long | condition failed → no trade |
| 5918–5927 | double rejection (10/15, 10/17; 5927.0 rejected 31 pt on 182k) | resistance | **HELD** (range top) |
| 5865.0 | range low bought hard (21-pt tail, 153k) | support | tick-through at bar 263 then **HELD** (−1R if shorted); acceptance break bar 291 **BROKE** (missed ~+2R) |
| 5837.5–5893.0 | compression inside 5801–5927 | acceptance-break plan | 5837.5 **BROKE** (bar 413, missed +2.3R to 5801) |
| **5801.0** | broken range low | failed-retest short | **HELD as resistance** (poke 5803.0, close 5792.0) → WIN +1.895R |
| 5770–5801 shelf; 5730.0 | named short zone / armed break | | 5730 traded to 5724.25 (V-bottom 11/04) — missed while advancing |
| 6021.0 / 6032.5 | 24-pt coil edges | symmetric breakout | **both false breaks** → both −1R |
| 6053.25 | 11/11 blow-off high | failed-retest short / break long | disarmed; later broke up and failed (−1R counterfactual) |
| 6009.25–6015.25 | 6-pt coil | | broke both ways (63-pt round trip) |
| 6059.25 | breakdown level | failed-retest short | **reclaimed** (retest succeeded; short correctly not triggered) |
| **5982.75** | 12/27 low, broken 12/30 | failed-retest short | **HELD as resistance** (rally 5983.5, close 5972.0; 1338/1339 capped 5980.0) → WIN +1.854R |
| 5987.25 | armed short | | never retested |
| 5845.0 | broken support (crossed 4× in 6 bars = chop midpoint) | declined, rule-4 floor & "not clean" | **HELD** as resistance → would have won ~+2R |
| 5868.0 | armed failed-retest | | fired 3× — all **BROKE** (−1R each) |
| 6032.00 | fresh 1-touch swing extreme | scenario map | **GAPPED THROUGH** (holiday open 6042.75) |
| 6045.50 | break level | | **BROKE** → missed +1.68R |
| 6100 | blue sky, nothing above | | no trade |

### 4d. MOST RECENT KEY LEVELS (not current — each stamped with its source bar, ET)

Computed by this sweep from merged `workspace/paper/CALL/data/` deltas (stubs dropped). **Newest bar held: 1m 2026-09-29T00:47-04:00; 15m 2026-09-29T00:30-04:00. These are ~stale; do not quote as live.**

| | **MGC** | **MNQ** |
|---|---|---|
| last price (1m 00:47) | 4158.20 | 30427.25 |
| ATR14(15m) @ 00:30 | 7.44 (stand-down line 10) | 46.25 (line 58) |
| Fri 09-25 session (09-24 18:00→09-25 17:00) H / L | 4351.60 (07:00) / **4289.10** (10:00) | **30998.50** (07:30) / 30680.00 (09-24 20:15) |
| Mon 09-28 session H / L / close / VWAP | 4310.30 (09-27 18:00) / **4143.00** (09-28 10:45) / 4148.70 / 4199.73 | 30900.50 (20:15) / **30356.50** (10:45) / 30556.75 / 30610.14 |
| 09-28 RTH H / L / VWAP | 4193.20 (09:45) / 4143.00 (10:45) / 4168.14 [08:20–13:30] | 30759.25 (09:30) / 30356.50 (10:45) / 30570.44 [09:30–16:00] |
| 09-28 overnight (18:00→RTH) H / L | 4310.30 / 4172.60 (05:00) | 30900.50 / 30535.00 (05:15) |
| Tue 09-29 session so far (from 09-28 18:00) H / L / VWAP | 4171.70 (23:30) / **4145.00** (21:00) / 4159.4 | 30615.25 (18:00) / **30412.50** (23:00) / 30513–30516 |
| 40-bar 15m range | 4143.90 – 4175.50 (13:30→00:30) | 30412.50 – 30650.75 |
| recent 15m swing lows (K=2) | 4143.00 (10:45), 4147.40 (11:45), 4143.90 (16:45), 4152.70 (18:45), **4145.00 (21:00)** | 30356.50 (10:45), 30534.00 (15:45), 30531.75 (16:45), **30430.00 (21:15)**, **30412.50 (23:00)**; desk-registered higher low 30427.75 (N260) |
| recent 15m swing highs | 4181.00 (12:15), 4175.50 (14:45), 4161.70 (19:30), 4169.10 (21:45), **4171.70 (23:30)** | 30722.00 (12:15), 30650.75 (14:45), 30615.25 (18:00), 30537.75 (22:15), **30500.00 (23:30)** |
| round numbers nearby | 4150, 4200 | 30400, 30500 |
| MGC daily caveat | 1440m 09-28 bar L 4111.30 C 4136.40 ≠ intraday — different contract/roll; do not use | MNQ daily 09-28 H 30920.75 L 30356.50 C 30566.25 (clean series) |

**MES (REPLAY, historical, bar 3399 = 2025-05-12T11:00-04:00, price 5817.50)** — replay "now", not market now: 05-12 session H 5865.50 (07:00) / L 5734.00 (05-11 18:00);
05-09 session H 5715.75 / L 5662.75; recent 60m swing lows 5596.00 (05-07 14:00), 5652.75 (05-08 10:00), 5662.75 (05-09 10:00); highs 5741.00 (05-08 12:00), 5773.50 (05-11 18:00), 5865.50 (05-12 07:00); April crash low 4909.25.

---

## 5. Tooling inventory

### CALL (`workspace/paper/CALL/`) — all read `data/` deltas; several import `futures_agents` (repo package)

| script | reusable? | one-line usage |
|---|---|---|
| `fetch.py` | **REUSABLE** | `python3 fetch.py` — Yahoo pull MGC/MNQ 1m–1440m via `futures_agents.data.yahoo`, stub rejection, writes delta snapshot `data/<SYM>_<tf>_fetched_<UTC>.jsonl` + `feed_lag.jsonl`. Symbols hard-coded MGC/MNQ |
| `chart.py` | **REUSABLE** (library core) | `python3 chart.py MGC MNQ --frame 15 --bars 44 [--json]` — merges deltas (`load()`), `ema`, `swings`, 3-component `bias()`, ANSI chart |
| `regime.py` | REUSABLE with known defects | `python3 regime.py MGC MNQ` — 7-frame bias, `reversal()` gate, `reversal_setup()`, `classify()` scalp/swing; **appends `bias_history.jsonl`** (held counter = invocations, N248; condition-4 continuation blindness, N194) |
| `resolve.py` | **REUSABLE** (the honest resolver) | `python3 resolve.py` — triggers/fills/outcomes from real bars only, costs, `unreachable()` void, writes state.json/journal/LEDGER.md. Known: 15m resolution, ambiguous-count gap (N253) |
| `heat.py` | REUSABLE | `python3 heat.py` — MAE/MFE/HEAT per trade on finest bars |
| `thesis.py` | REUSABLE | `python3 thesis.py` — "direction right / entry unreachable vs direction wrong" for NO_FILL plans |
| `project.py` | REUSABLE | `python3 project.py MGC MNQ` — forward fib levels of live leg, session VWAP ± bands, ATR reach envelope |
| `watch.py` | REUSABLE (display only) | `python3 watch.py` — per-direction gate distances as levels, `capacity()` (book-level), `counter_trend()` |
| `card.py` | REUSABLE | `python3 card.py [--only CALL-0010]` — ANSI cards from pending/state via `futures_agents.alerts` |
| `card_png.py` | REUSABLE (cosmetic) | `python3 card_png.py [ids] [--scale] [--blank]` — PNG "laser" cards (needs PIL) |
| `status_card.py` | REUSABLE (cosmetic) | `python3 status_card.py 3.0 --auto` — desk-state PNG; reads BASIS, standdown_cost.txt |
| `index_notes.py` | REUSABLE | `python3 index_notes.py` — regenerates FINDINGS_INDEX.md from NOTES.md |
| `cont1.py` | one-off pre-registered test (keep: backs the prohibition) | reads `data/archive/{MGC,MNQ}_{15m,60m}`, writes `cont1_results.json`; FADE-1 variant was run inline (no file) |
| `vol1.py` | one-off (VOL-1 null) | pivot-volume vs direction, placebo 200 draws |
| `confluence.py` | one-off/early | 13-family disagreement surfacer + `levels()`; superseded by regime/watch |

### REPLAY (`workspace/paper/REPLAY/R1/`) — read only `visible.jsonl` (+callouts); harness itself is `workspace/roundtable/lib/replay.py` (not in lane)

| script | reusable? | usage |
|---|---|---|
| `view.py` | REUSABLE | `python3 view.py [detail=12] [sessions=8]` — compact tape view, `roll_flags`, gap clusters |
| `watch.py` | REUSABLE | `python3 watch.py --id R1 --budget 60 --cond ...` — steps harness 1 bar at a time, halts on armed condition |
| `levels.py` | REUSABLE, **control deprecated** | walk-forward fractal S/R levels + bounce/break outcome study (use E9_levels_fair control) |
| `scenario.py` | REUSABLE | `python3 scenario.py [bar]` — nearest levels, 4 branches (hold/break/neither/gapped) |
| `missed.py` | REUSABLE | counterfactual on every stand-down vs all-bar control; **rewrites missed.jsonl at import** |
| `mode.py` | REUSABLE | 1 vs 3 agents by CME clock |
| `agents/C_merge.py` | **REUSABLE** (adopted primary roll screen) | straddled-forbidden-corridor contract-merge detector |
| `agents/E9_levels_fair.py` | **REUSABLE** (the fair level control) | touch/count/ATR-matched, decontaminated random-line control |
| `agents/E2_randomwalk.py` | REUSABLE | VR, robust ACF, Ljung-Box, runs, Hurst battery on closes |
| `agents/E5_costs.py` | REUSABLE | cost-as-fraction-of-R by ATR regime |
| `agents/E4_session.py`, `E6_hours.py`, `E9_controls.py`, `A_grid.py`, `C_regime.py`, `C_shape.py`, `D_discretion.py` | one-off analyses (reproducers for E4/E6/E9/A/C/D findings) | read `visible.jsonl`; C_regime.py is the thesis-5 signal generator E8 reuses |

---

## 6. Contradictions — CALL vs REPLAY (and within)

| # | topic | CALL says | REPLAY says | better evidenced |
|---|---|---|---|---|
| 1 | **Volatility and trading** | High vol ⇒ **stand down** (MNQ ATR>58, MGC>10): blind-spot excursion exceeds max stop (N214) | High vol ⇒ **cheapest to trade**: cost hurdle 0.0365R at ATR 21.6 vs 0.1019R low-vol (SUMMARY #4) | Both right in their frame: CALL's is a live feed-lag + fixed-$-cap constraint; REPLAY's is cost-per-R with no observation gap. For a live desk the CALL veto binds; they share "vol for sizing/stand-down, never direction" |
| 2 | Cost of standing aside | Morning stand-down foreclosed up to **$902 MGC / $805 MNQ per contract**, marginal = full (DECISIONS row 2) | Stand-downs cost **nothing measurable**, 0/36 |z|≥2 (SUMMARY #5) | REPLAY (controlled counterfactual n=48); CALL figure is an upper bound on one day, and CONT-1 shows the obvious entry would have lost |
| 3 | Levels | Used shelves/touch counts/fib as confluence (4289.10 "twice tested", 4145 "five times", 30425–30434 base) | Levels ≈ random under naive control; fair control bounce arm z +2.52 but +0.043R < cost; touch counts withdrawn | REPLAY; CALL has conceded (CONSOLIDATION §8.4, N262) |
| 4 | Rule 4 floor | Hard floor; N236 adds "floor not sufficient" | Smooth gradient, no knee at 0.5 ATR, ~52% cost; floor refused a +2R winner | REPLAY (agent A grid) for mechanism; both keep rule |
| 5 | Rule 5 (15:00–16:00) | Binding veto | Census z +0.10 (cannot replicate), kept on reasoning | Programme result stands; REPLAY shows its instrument can't test it |
| 6 | Hours / evening tape | CONSOLIDATION §5.3: stop selecting sides evening/overnight (MGC outside 08:20–13:30) | Rule 6 holds: 0/22 hours differ; MES overnight thin but not worse in R | Neither measured on MGC/MNQ; REPLAY's is the only test (MES). CALL's is a "measured territory" argument, not an expectancy one |
| 7 | Fill discipline | 60% fill rate, entries moved toward market | ~4% (2/51) — declines logged with counterfactual | REPLAY (CALL concedes, CONSOLIDATION §4) |
| 8 | Placebo / counterfactual | none | every bar | REPLAY |
| 9 | Costs in R | resolve.py always nets costs; hurdle never reported until §8.1 | harness nets commission, but study R figures were gross until E5 | tie; MNQ 4.88-tick RT is worse than MES 2.15 |
| 10 | Record headline | state.json −0.207R vs desk −0.562R (CALL-0002 exclusion) | 2/2 wins "not evidence" | n/a — quote both CALL figures with basis |
| 11 | Search width | never counted | 20 theses / 297 desk-wide, free_t 3.37; thesis-5 filters vs 105 | REPLAY |
| 12 | Volume evidence | climax_x 3.12× "flush" as confluence | 18:00 volume field missing | converged: CALL N262 finds 26% missing, claim unsupported |
| 13 | Within CALL: rule 2 | desk read alignment as contrarian (N183–N190) | — | N194 cause 4 retracts; N213 unanimity null |
| 14 | Within CALL: "unanimity marks turns" | N194 cause 2 anecdote | — | N214 (2,134 onsets) refutes |

CONSOLIDATION §6 claims "no contradictions of substance" — this sweep finds #1, #2, #6 are substantive framing conflicts that must be stated together.

---

## 7. Open obligations left by the desks

1. CALL-0010 needs one `resolve.py` run at/after 09:30 ET 09-29 to close honestly (N264). Do not hand-write EXPIRED.
2. Before CALL ever calls again (N264 register): placebo + counterfactual; pre-registered stop-to-BE at +0.8R test on archive; no side-selection on evening tape; fixed-structure entries; count gate search width; `climax_x=None` when v==0.
3. Cron expressions (if ever re-armed) assume EDT — re-cut 2026-11-01.
4. REPLAY: next roll ~2025-06-20 (~800 bars ahead of cursor 3400); `levels.py` control must be replaced by E9's; thesis 5 retired; no instrument-appropriate predicate exists.
