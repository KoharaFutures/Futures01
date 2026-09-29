# Automation audit: the REPLAY desk (R1, MES 60m)

**Written 2026-09-29 by an audit sub-agent. Read-only audit: nothing was modified, moved or committed.**
Sources read: `REPLAY.md`, `workspace/roundtable/lib/replay.py` (all 529 lines), `workspace/paper/REPLAY/R1/SUMMARY.md` (all),
`NOTES.md` (grepped, plus bursts 11, 14–17 and the E8 section read in full), `missed.py`, `mode.py`, `watch.py`, `view.py`,
`scenario.py` (header), `agents/C_merge.py`, `agents/C_regime.py`, `agents/E9_controls.py`, `agents/E9_levels_fair.py`,
`agents/C_substrate.md` §3, `DATA_HUB/tools/vp_levels.py`, `DATA_HUB/tools/bounce_levels.py`, `DATA_HUB/OPEN_QUESTIONS.md`.
Nothing in `Archived_Do_Not_Refference/` was opened.

Terms: **R** = one unit of risk (entry to stop). **Placebo** = the same trade with a direction or entry the
strategy didn't choose. **Luck bar** = √(2·ln N) for N ideas tried. **Win rate and payoff** (average win ÷ average loss) are always quoted together.

---

## 0. Two findings the desk hasn't recorded (verified in code this turn)

| # | finding | evidence | consequence |
|---|---|---|---|
| F1 | **The harness placebo reuses the agent's absolute stop and target prices, not its geometry.** Whenever the coin lands on the opposite side, the placebo's stop is on the wrong side of its own fill. It is stopped at the open of the fill bar for about −0.07R, every time. | `replay.py:398-400` copies `a.stop` and `a.target` verbatim into `placebo_pending`. `_resolve` at `replay.py:347-352` then sees `h ≥ stop` (short) or `l ≤ stop` (long) on the fill bar and closes at the open (`STOP_GAP`). Reproduced in a scratch copy with `R.PAPER` redirected: trade-1 geometry gives `PLACEBO_EXIT r −0.0671 net −11.82 STOP_GAP`, which is identical to R1 `journal.jsonl` line 3. The second placebo drew the same side and copied the real trade exactly (`r 1.854`). | The placebo isn't random-direction through the same exits. It's a 50/50 mix of **a copy of the real trade** and **a near-zero scratch**. Real-minus-placebo separation is therefore about halved, so the |z| > 4.5 leak alarm (`replay.py:491`) needs roughly 4× as many trades to fire. The published `z +1.021` (SUMMARY.md:14) compares 2 trades against 1 copy and 1 scratch. It carries no information. The desk can't fix this itself: `REPLAY.md:157-161` forbids it to edit the harness. The owner has to. |
| F2 | **"Flat by 16:00" exits at the close of the 16:00–17:00 bar**, about an hour after 16:00. | `_resolve` at `replay.py:358-359` closes at `bar["c"]` on the first bar whose stamp is ≥ 16:00 (`in_forbidden_window` at `:88-91`, `cycle_deadline_crossed` at `:94-101`). R1's tape has 146 bars stamped 16:xx in 3,400. | A position is exposed to the 16:00–17:00 hour. `missed.py:54-60`, `C_regime.py:105-109` and the `session_end` copies in E4/E5/E6/E9 all do the same, so they are consistent with each other. Walk-forward parity should keep this behaviour and label it (see §3). |

Minor, for the record: `replay.py:365` builds an `rng` it never uses. `:397` says the placebo enters "on a later bar", but it
fills on the same bar as the real order (`:372-376`). `ET` at `:81` is unused (timestamps carry their own −04/−05 offset, so DST
is handled correctly). `cmd_flat` (`:419-429`) doesn't close "on the next bar". It moves the stop to entry, so a winning position stays
open until price comes back to breakeven or the session ends. `source_bars` (`:194-203`) reads the **live** `data/archive/` file, which has
since grown to 11,316 bars against `state.json` `n_source` 11,287, so "end of series" moves every time `update_hub.sh` runs.

---

## 1. Every step of one firing, classified

MECHANICAL = no decision, a shell line would do it. ALREADY-SCRIPTED = code exists (file:function). JUDGMENT = needs an LLM.

| # | step per firing | class | where / why |
|---|---|---|---|
| 1 | `git fetch … && git merge --no-edit FETCH_HEAD` | MECHANICAL | `REPLAY.md:145`. Fixed command. The only branch is the conflict case, which should halt, not be judged. |
| 2 | Re-read `REPLAY.md`, `CALLOUT.md`, print basis sha | MECHANICAL | `git rev-parse` is already in `replay.py:_basis` (`:110-116`). Re-reading prose each firing only matters to an LLM. |
| 3 | Decide 1 vs 3 agents | ALREADY-SCRIPTED | `R1/mode.py:mode` (`:27-45`). A pure function of wall-clock ET. It sizes LLM staffing and says nothing about the market being replayed. |
| 4 | `status` | ALREADY-SCRIPTED | `replay.py:cmd_status` / `_print_status` (`:432-454`) |
| 5 | Look at the tape (ATR, daily OHLC, last bars) | ALREADY-SCRIPTED | `R1/view.py` (module-level script, `:10-43`) |
| 6 | Roll-merge screen | ALREADY-SCRIPTED | `view.py:roll_flags` (`:49-118`), `view.py:gap_clusters` (`:121-150`), `agents/C_merge.py:straddled_corridor` (`:30-45`). Halting on a flag is a rule. The by-eye confirmation has already been turned into code three times. |
| 7 | Advance 50-bar chunks up to 400 | ALREADY-SCRIPTED | `replay.py:cmd_next` (`:362-386`). `watch.py:step` (`:56-70`) does one bar at a time with a halt condition. |
| 8 | **Decide trade / no-trade at each bar** | **JUDGMENT** (nominally) | This is the only real judgment step. In practice it is now a constant: bursts 16–17 covered 800 bars with **0 candidates** (NOTES.md:2119-2200). SUMMARY.md:67-68 says "the desk will not trade this instrument again until [a pre-registered predicate exists]". 51 callouts over 3,400 bars means 98.5% of bars get no journalled decision at all. |
| 9 | Order geometry checks (0.5-ATR floor, R:R ≥ 1.5 at the actual fill, rule 5's 15:00–16:00 window, bars to the flat, ladder size) | MECHANICAL / ALREADY-SCRIPTED | Sizing is in `replay.py:_size` (`:248-265`). `watch.py:main` (`:112-116`) prints the other re-checks. These are arithmetic. |
| 10 | Record `notrade` / `order` | ALREADY-SCRIPTED (call) + JUDGMENT (the `--why` prose) | `replay.py:cmd_notrade` (`:406-416`), `cmd_order` (`:389-403`). The prose is the only unscriptable part, and an LLM can't audit it afterwards: B_audit found 27 prose errors (NOTES.md:1289). |
| 11 | Placebo beside each order | ALREADY-SCRIPTED (defective, F1) | `replay.py:cmd_order` `:397-400` |
| 12 | `score --trials N` | ALREADY-SCRIPTED | `replay.py:cmd_score` (`:465-495`). N (the thesis count) is bookkeeping. |
| 13 | Stop conditions: \|z\| > 4.5, absorbing state, end of series, roll flag | MECHANICAL | `cmd_score:491`, `_size:256-259` / `_print_status:439-443`, `cmd_next:367-369`, and step 6. All four are boolean. |
| 14 | `missed.py` counterfactual | ALREADY-SCRIPTED | `R1/missed.py` (whole file. Module-level script, no functions exported for import. See §4.) |
| 15 | Append a NOTES.md burst | JUDGMENT (prose) over MECHANICAL numbers | Every number in bursts 14–17 comes from steps 4, 6, 12 and 14 and could be templated. The prose is where the 27 errors came from. |
| 16 | `check_ownership.py R1` | ALREADY-SCRIPTED | `workspace/roundtable/check_ownership.py` |
| 17 | Commit / push | MECHANICAL | fixed commands |
| 18 | (closed market) 3-agent research round | JUDGMENT | Produced E1–E9 and A–D. Its durable outputs are **scripts** (`agents/*.py`), which is the argument for doing research in code rather than on a timer. |

**Count: 18 steps. 16 are mechanical or already scripted. 2 are judgment, and one of those (#8) has returned the same answer for 800 consecutive bars.**

---

## 2. Purpose vs. product vs. cost

### What the desk is for (its own words)

| source | stated purpose |
|---|---|
| `REPLAY.md:10-12` | "exercise the process and accumulate an honest record — **not** to produce a statistic that proves an edge" |
| `REPLAY.md:14-20` | "a fresh discretionary decision at each bar… cannot be replicated, it has no pre-registration, and its search width is unbounded… **Never report its result as an edge.** What it can honestly produce is… an answer to 'does this process beat a coin flip through the same exits'" |
| `SUMMARY.md:62-68` | "Nothing in this record clears its own deflated threshold… the desk will not trade this instrument again until [a pre-registered predicate that survives OOS exists]" |

### What it has produced (cursor 3,400 / 11,287)

All figures below came from code this turn (`callouts.jsonl`, `state.json`, the caller's $160 figure):

| metric | value |
|---|---|
| bars advanced | 3,400 (30.1%) |
| callouts | 51 (49 NO_TRADE, 2 DISCRETIONARY) |
| trades | 2: +1.8949R, +1.8540R (win rate 100%, payoff undefined, n=2) |
| cost per bar / per callout / per trade | **$0.047 / $3.14 / $80** |
| bars per callout / per trade | 66.7 / 1,700 |
| projected cost to finish | **~$371 more**, for ~4.6 more trades (**~6.6 trades total**) |
| placebo z | +1.021, and not interpretable (F1) |
| trades needed for z = 2 at sd 1.3R | 0.20R edge: **169**. 0.10R: **676**. 0.05R: **2,704** |
| bars needed at the desk's trade rate | 169 trades would take **287,300 bars** (25× the series) |
| smallest edge this tape can resolve (E8, NOTES.md:1668-1671) | ≈ +0.19R/trade, against a cost hurdle of 0.081R |

### What that cost actually bought (SUMMARY.md:19-48), sorted by whether it needed the replay

| finding | needed walk-forward discretion? | what actually produced it |
|---|---|---|
| Walk-forward integrity held (E3/E7, 45/45 reconciled) | yes, this is the only replay-specific result | audit of the replay itself |
| MES 60m returns are a random walk (E2) | no | `agents/E2_randomwalk.py`, a whole-tape statistic |
| Costs ($2.69 = 2.15 ticks) exceed any structure (E5) | no | `agents/E5_costs.py` |
| Volatility moves the cost hurdle 3× | no | arithmetic on ATR |
| Stand-downs cost nothing (A grid, E9) | no, it's a counterfactual over bars | `missed.py`, `A_grid.py`, `E9_controls.py` |
| Two roll-merge regions (Dec 2024, Mar 2025) | **partly**: found by eye while replaying, then scripted | `view.py:roll_flags/gap_clusters`, `C_merge.py` |
| 18:00 ET bar has no volume Mon–Thu | no | E6 hour census |
| 16:00 flat costs ≈ 0.0032R/trade | no | `agents/E4_session.py` |
| Thesis 5 retired (105 trials, family-wise p 0.86, OOS flip) | no, it was retired *by* mechanising it | `C_regime.py`, E8 |

**Assessment.** Eight of the nine findings came from deterministic scripts over the visible tape. The one replay-specific finding
(integrity held) is the precondition for the desk's purpose, not the purpose itself. The purpose, "does this process beat a
coin flip through the same exits", **cannot be answered by this desk at all.** At 1 trade per 1,700 bars the whole series
yields about 7 trades, the placebo is defective (F1), and the desk has committed to not trading until a pre-registered
predicate exists. That predicate is exactly the input a deterministic engine takes.

| part of the purpose | needs discretion? | better instrument |
|---|---|---|
| "Does a rule beat a random-direction coin flip through the same exits?" | no | `walkforward.py` (§3). Hundreds of trades, seconds, with a correct placebo |
| "Is the fill / session / sizing / absorbing-state handling honest?" | no | the same engine, importing `replay.py`'s pure functions |
| "Does the owner's *judgment* at a level add anything over the mechanical rule?" | **yes** | a **blinded event-sample** (§5 option C): the engine lists N rule events, and the LLM gets only bars ≤ i for each and calls continue / bounce / skip. That gives n ≈ 200 in one session instead of ~7 in the rest of the series |
| "Write a testable hypothesis in the owner's style" | **yes** | an LLM writing `rules/*.py` + a pre-registration line, then handing off to the engine |
| "Spot data defects by eye" | partly | already converted to code (`gap_clusters`). Keep the scripts |

---

## 3. Spec: `DATA_HUB/tools/walkforward.py`

### 3.1 Contract

```
python3 DATA_HUB/tools/walkforward.py --rule DATA_HUB/tools/rules/lvn_fade_1w60.py \
        --symbol MES --tf 60 [--start 0] [--end N] [--placebo-draws 1000] [--seed wf-v1] \
        [--family-size N] [--roll-mask calendar|detector|none] [--parity] \
        --out DATA_HUB/walkforward/
```

| requirement | spec |
|---|---|
| input bars | `replay.source_bars(symbol, tf)` (`replay.py:194-203`), the *same* list the desk sees. Record `sha256` and `len` of the file in the output, because the archive grows (§0). Assert that `bounce_levels.load` (`bounce_levels.py:69-79`, which drops vendor stubs and sorts) returns the same length when a rule uses hub helpers. MES 60m has 0 stubs today (checked), so indices agree. |
| rule interface | Module exports `NAME`, `PREREG` (dict: hypothesis text, date, git sha, `family` id), `WARMUP` (bars), and `decide(view, i, ctx) -> Order | None`, where `Order = (side, stop, target, why)` in absolute prices. `ctx` offers causal helpers (`atr(i)`, `profile(i, window)`, `pivots(i)`). |
| causality guard | `view` is a read-only wrapper over `bars[:i+1]` that raises on any index > i. Also a **truncation-invariance test**: run the rule on `bars[:k]` and on `bars` for 5 random k and assert identical orders for every bar < k-1. This catches any precomputation that peeks forward. |
| decision timing | `decide` is called after bar i is "revealed", which is exactly where the LLM runs `order` (`replay.py:389-403`). It is called only when flat and nothing is pending (`:391-394`). |
| output | `trades.jsonl` (the same fields as the harness `EXIT` journal record, `replay.py:320-326`), `placebo.jsonl`, `summary.json`, and `summary.md` with n, win rate **and** payoff, mean R, sd, t, placebo stats, z (both forms), luck bar, verdict, first-half/second-half sign, max drawdown, refusals, absorbing flag, roll-masked count, and the data sha. |
| speed target | 11,287 bars plus 1,000 placebo draws in **under 10 s**. Scanner imports measured at 0.19 s to load MES 60m and build 504 one-week profiles. |

### 3.2 Per-bar loop: must equal `cmd_next` (`replay.py:366-384`) step for step

| order | step | harness semantics to reproduce (cite) |
|---|---|---|
| 1 | fill pending real order at `bar.o` | `_open` `:268-272`: entry = `_round(o + sign·1 tick)`, **one tick of slippage against you**. `stop = _round(order.stop)`. |
| 2 | size it | `_size(st, entry, stop)` `:248-265`: refuse if the stop is inside `min_stop_ticks` (MES 8 = 2.00 pts), if the ladder permits < `min_dollar_risk` $25 (**absorbing state**, `:256-259`), or if one contract exceeds the permitted risk. `contracts = floor(allowed / (|entry−stop|·pv))`. Ladder: `permitted_risk` `:66-77` (verified: $240 at dd 0, $21.60 ×0.30 at dd $2,800). |
| 3 | on refusal | log REFUSED and **drop the matched placebo too** (`:276-286`) |
| 4 | fill placebo(s) at the same bar's open | `_open` with `key="placebo_position"`, contracts = the real contracts (`:274-275`). **Fix F1 here (§3.4).** |
| 5 | resolve exits, real then placebo | `_resolve` `:339-359`: **stop is tested first and wins a same-bar tie** (`:349`). If the open is already through the stop, exit at the **open** (`STOP_GAP`, `:350-352`). If the open is through the target, exit at the **open** in your favour (`:355-356`). Otherwise exit at the exact stop or target. If nothing hit and the bar is in 16:00–18:00 or past the cycle's 16:00 deadline, exit at **that bar's close** (`SESSION_FLAT`, `:358-359`, F2). The fill bar itself is resolved (entry happens before step 5). |
| 6 | P&L | `_close` `:308-336`: `gross = (px−entry)·sign·pv·n`, `cost = 2.69·n` (`spec` `:171-176` = 2×(0.35+0.37) + 1 tick × $1.25), `net = gross − cost`, `r = net / risk_dollars` (risk excludes cost). Equity and trailing peak are updated **only for the real arm** (`:316-318`). The placebo never touches equity (`:334-335`). |
| 7 | stop conditions | end of series (`:367`), absorbing state (stop the run and mark `ABSORBED`), roll mask (§3.5) |
| 8 | call `decide` | only if `position is None and pending is None`. The returned Order becomes `pending`. |

Not enforced by `replay.py`, so **not** enforced by default for parity, but reported as a flag column: the daily loss
limit, max trades/day, max consecutive losses, and `min_reward_risk` 1.6 from `desk/desk-config.json`. `--desk-rules` turns them on as a declared second run.

### 3.3 What to import from `replay.py` vs. reimplement (signatures verified with `inspect.signature` this turn)

| function | signature | import? | why |
|---|---|---|---|
| `permitted_risk` | `(equity: float, drawdown: float) -> tuple[float, float]` | **import** | pure |
| `in_forbidden_window` | `(ts: str) -> bool` | **import** | pure |
| `cycle_deadline_crossed` | `(entry_ts: str, bar_ts: str) -> bool` | **import** | pure |
| `spec` | `(symbol: str) -> dict` | **import** | pure. Reads `futures_agents.config` |
| `source_bars` | `(symbol: str, tf: int) -> list[dict]` | **import** | read-only. Includes the MGC-1440 splice guard (`:201-202`) |
| `_round` | `(sp: dict, px: float) -> float` | **import** | pure |
| `_size` | `(st: dict, entry: float, stop: float) -> tuple[int, float, str]` | **import** | pure given a dict with `spec`, `equity`, `peak` (`:249-265`) |
| `CFG`, `USABLE` | module constants | **import** | import side effect is only reading `desk/desk-config.json` (`:62-63`). No writes. |
| `_open`, `_close`, `_resolve` | `(st, key, bar, …) -> None` | **reimplement** (≈40 lines) | They write `journal.jsonl` / `callouts.jsonl` under `PAPER/<id>` (`:206-211`, `:130-152`), shell out to `git` on every callout (`:110-116`), re-read the callouts file for uniqueness (`:140-142`, O(n²)), and rewrite the whole file on resolve (`:155-163`) |
| `cmd_next` | `(a) -> None` | **reimplement** | re-parses the whole series on every call (`:364`) and prints each bar |
| `cmd_score` | `(a) -> None` | **reimplement as a pure function** | same formula: Welch z `(m1−m2)/√(s1²/n1+s2²/n2)` (`:483-486`), `free_t = √(2·ln max(2,N))` (`:487`), alarm at \|z\| > 4.5 (`:491`) |

**Parity mode (`--parity`)** proves the reimplementation equals the harness. Import `replay` as `R`, set `R.PAPER` to a scratch
directory, `R._basis = lambda: "wf"`, `R._as_of = lambda st: "wf"`, then drive `R._open` / `R._resolve` with the same bars and orders
and assert that every EXIT `r`, `reason` and `exit_price` matches. **This route was run this turn**: it reproduced the
harness's `r −0.0671 STOP_GAP` placebo exactly. Regression fixture: inject R1's two journalled orders (ORDER at cursor 453 SHORT
stop 5804 target 5768, and cursor 1340 SHORT stop 5985.5 target 5950). The engine must return **+1.8949R TARGET** and **+1.8540R
TARGET**, and in legacy-placebo mode **−0.0671R** and **+1.8540R** (`journal.jsonl` rows 3–7).

### 3.4 Placebo: same geometry, done correctly

| arm | definition | purpose |
|---|---|---|
| **P1 direction placebo (default)** | For each real order: side = `Random(f"{seed}:{draw}:{i}").choice`. Its own fill = `_round(o ± 1 tick)` in *its* direction. Stop at `fill ∓ |real_entry − real_stop|`, target at `fill ± |real_target − real_entry|`, both mirrored. Same bar, same contracts, same exits (§3.2 steps 5–6). **K = 1,000 draws.** | answers "does direction choice beat a coin flip through the same exits". This is what `REPLAY.md:32-35` says the harness does. |
| **P2 time placebo** | Same side and same R-geometry (in ATR units), entry on a random bar drawn from the **same hour-of-day × ATR-quartile cell** as the real entry. Reuse `E9_controls.py:matched` logic (`:208-235`). | answers "does *when* beat an arbitrary bar with the same conditions" |
| **P3 level placebo** (level rules only) | Random price lines in the same range, with the same arming and touch rules. Reuse `vp_levels.scan(..., placebo=True)` (`vp_levels.py:241-242`, 2 lines per level) or `E9_levels_fair.py` variant D (`:122-128`: random lines kept ≥ 0.25 ATR from real levels, touch counts drawn from the real pool) | answers "is it the *level* or just the approach" |
| legacy | the harness's absolute-price placebo (F1), kept only for the parity fixture | continuity |

**Scoring** (numbers printed by the code, never hand-written):

| statistic | formula | threshold |
|---|---|---|
| harness-compatible z | Welch z, real vs pooled P1 trades (`replay.py:483-486`) | luck bar √(2·ln N_family). For a single pre-registered test, t ≥ 1.18 (`OPEN_QUESTIONS.md:4-5`) |
| empirical z / p | rank of the real mean among the K placebo-draw means. p = (1 + #{draw ≥ real}) / (K+1) | same |
| leak alarm | \|z\| > 4.5 prints the harness warning verbatim (`replay.py:491-495`) | stop and audit |
| stability | sign of mean R in the first vs second half of the trades | reported, not a gate |
| net-of-cost | every R is already net of $2.69/contract plus the entry tick | the cost hurdle (E5) is 0.081R at median ATR |

`N_family` comes from a ledger file `DATA_HUB/walkforward/LEDGER.tsv` (append-only: date, rule, sha, family). The engine refuses to
run a rule whose sha isn't in the ledger, and it prints the luck bar using the ledger's count for that family. That makes the search
width mechanical instead of self-declared (compare `--trials` in `replay.py:521`).

### 3.5 Roll mask

| mode | behaviour |
|---|---|
| `calendar` (default) | Mask entries from 5 trading days before to 1 day after each CME quarterly expiry (3rd Friday of Mar/Jun/Sep/Dec). This is **known ex-ante**, so it's causal. |
| `detector` | `gap_clusters(rows[:i+1])` from `view.py:121-150`, run causally every 50 bars. Used as an audit that the calendar mask covers the measured merges (1146–1158, 2517–2591; SUMMARY.md:39-40). Running the detector on the full series is mild look-ahead, so it's allowed only for the audit. |
| `none` | for comparison. Report masked-trade count and their R separately |

### 3.6 Rule #1 (`OPEN_QUESTIONS.md:12`) as a rule file, `rules/lvn_fade_1w60.py`

| element | pre-registered value | source it must match |
|---|---|---|
| profile | 60m bars, the prior **5 trading days** (trading day = `tday(ts)` = (ts+6h).date), built from days strictly before the current one | `vp_levels.WINDOWS (60,5,"1-week(60m)")` `:49-50`, `daily_profiles` `:160-173`, `tday` `bounce_levels.py:82-84` |
| LVN | `build_profile(...).lvn`: 80 bins, a valley ≤ 0.5 × the smaller neighbouring HVN, HVN ≥ 0.25 × POC, ≥ 4 bins apart | `vp_levels.py:51-54, 78-118` (**import directly**) |
| ATR | `atr_series(bars)[i-1]` (14-bar simple TR mean) | `bounce_levels.py:161-168`, as used in `scan` `:228` |
| arming "from below" | a level becomes armed when a prior bar's high is < L − 1.0·ATR. One trigger per arming. Key = (trading day, "LVN", round(L/tick)) | `vp_levels.scan` `:230-240` (ARM = 1.0) |
| trigger | bar i: armed-from-below **and** `h[i] ≥ L` | `scan` `:238-240` with `from_above=False` |
| order | **SHORT**, decided at bar i's close, fills at `o[i+1] − 1 tick`. Stop = fill + 1.0·ATR, target = fill − 1.0·ATR (both rounded to tick) | "stop = target = 1 ATR". The scanner measures ±1 ATR from **L** (`first_passage` `:183-213`), while the engine measures from the **fill**. This difference is declared in `PREREG`, not tuned. |
| fixed desk filters | skip if the fill bar is stamped 15:xx or 16:xx (rule 5), skip inside the roll mask. Harness `min_stop_ticks` and ladder apply automatically | `REPLAY.md:111-113`, `replay.py:251-253` |
| not included | no close-back-below-L condition, no trend or RVOL filter. Each of these would be a **new** ledger entry (+1 trial) | `OPEN_QUESTIONS.md:4-6` |
| family / bar | family "OQ1", N = 1 until more rules join it, so the bar is t ≥ 1.18. Also report per symbol (MES, MNQ, MGC, MCL) as N = 4, bar 1.67 | |

Sketch (spec only, not written to disk):

```python
# rules/lvn_fade_1w60.py
NAME, WARMUP = "OQ1_lvn_fade_1w60", 6 * 23
PREREG = {"family": "OQ1", "text": "short the 60m-built 1-week LVN on first touch from below, 1ATR/1ATR", "date": "YYYY-MM-DD"}
def decide(view, i, ctx):
    a = ctx.atr(i - 1); pf = ctx.profile(i, window_days=5, tf=60)      # causal: prior 5 tdays only
    if not a or not pf: return None                                   # rule 5 / roll mask on the fill bar: engine
    for L in pf.lvn:
        if ctx.armed_below(L, i, arm=1.0 * a) and view[i].h >= L:     # ctx keeps the scan() arming state
            ctx.disarm(L, i)
            return ("SHORT", None, None, f"LVN {L:.2f} touched from below, 1w60 profile")  # engine fills stop/target = fill ± 1ATR
    return None
```

`Order` accepts `stop=None, target=None` together with `stop_atr=1.0, target_atr=1.0`. The engine then resolves them against the actual fill
price, because the harness only takes absolute prices (`replay.py:395`) and the fill isn't known at decision time.

### 3.7 Retired thesis 5 as a rule file, `rules/thesis5_failed_retest.py` (a regression and negative control, not a live hypothesis)

| element | value | source |
|---|---|---|
| pivots | fractal k = 3 over a lookback of 300 bars. A pivot at j is usable once j + 3 ≤ i − 1 (strict inequality on neighbours) | `C_regime.py:pivots_known_at` `:92-103` |
| broken | some bar b in [max(j+4, i−24), i) closed beyond L by > 0.25·ATR14[i] (below for a pivot LOW, above for a HIGH) | `C_regime.py:132,137` |
| retest-reject | LOW: `h[i] ≥ L and c[i] < L` gives **SHORT**. HIGH: `l[i] ≤ L and c[i] > L` gives **LONG** | `C_regime.py:129-139` |
| geometry | stop = the signal bar's opposite extreme ± 1 tick. Target = 2.0 R from the fill | `C_regime.py:134,139`, `C_substrate.md` §3 |
| dedupe | one signal per (bar, side), keeping the level nearest to the close | `C_regime.py:144-150` |
| filters (Tier A) | stop ≥ 0.5·ATR, fill hour not 15 or 16, not in a merge | `C_regime.py:filt` `:155-160` |
| Tier B add-ons | trend bucket from `(c[i]−c[i−40])/ATR[i]` < −1.5 (DOWN) or > +1.5 (UP), side must agree. Break within 12 bars. First retest per (L, side) in 48 bars | `C_regime.py:45-52, 240-250` |
| expected outcome | Tier A n ≈ 442, **+0.023R gross**, 38.0% win rate, placebo-sd +0.70 (`C_substrate.md` §3). These were gross of cost and without gap-at-open stops (`C_regime.py:111-121`), so the engine's net figure should come in about 0.08R lower, **≈ −0.06R**. That would be a useful check that the engine charges costs. | |
| ledger | family "T5", already spent 105 trials (E8, NOTES.md:1650-1652). Luck bar √(2·ln 105) = 3.05 | |

---

## 4. Which REPLAY tools the engine can reuse

| tool | reusable? | how |
|---|---|---|
| `missed.py` (counterfactual) | **the idea, not the code** | It's a module-level script with global `rows` (`:38-39`) and it writes `missed.jsonl` when imported (`:244`). Its `simulate` (`:63-83`) differs from the harness: no gap-through-stop at the open (it always returns −1.0), **no costs**, and a fixed 2R target. Reimplement it as `walkforward.py --counterfactual journal.jsonl`: take any NO_TRADE bar list, run both directions through the engine's harness-exact exits, and compare against all eligible bars. That retires the gross-of-cost numbers E5 flagged. |
| `agents/E9_controls.py` (fair controls) | **yes, port `matched`** | The post-stratified hour × ATR-quartile estimator at `:208-235` (pairs each sample bar with the mean of its cell, z = mean(d)/SE(d)) becomes placebo P2. The rest of the file audits `missed.py`/`levels.py` specifically. |
| `agents/E9_levels_fair.py` | **yes, port variant D** | The random-level generator at `:122-128` becomes placebo P3 for level rules. Its `real_touch_pool` sampling keeps touch counts comparable, which is the fix for the withdrawn levels claim (`scenario.py` header, E7/C1). |
| `view.py:roll_flags`, `view.py:gap_clusters` | **yes, but copy them** | Both are pure `(rows, ...)` functions. However `view.py` runs its report at import (`:10-43`, reads `sys.argv`, prints). Move them into `DATA_HUB/tools/rolls.py` (copy; don't edit R1's lane) and use them for `--roll-mask detector`. |
| `agents/C_merge.py:straddled_corridor` | **yes, reimplement with a `rows` argument** | It depends on global `rows` (`:23-24`) and runs the sweep at import. It's a 15-line pure function, useful as a second roll-audit opinion. |
| `mode.py` | **no** | It picks LLM staffing (1 vs 3 agents) from wall-clock ET (`:27-45`). A deterministic engine has no staffing and no wall-clock dependence. Keep it only if an LLM desk survives. |
| `watch.py` | no (superseded) | It's a one-bar stepper with halt conditions. The engine steps every bar by construction. It was written because 50-bar chunks missed one-bar triggers 5 times (NOTES.md:1062-1072), a failure mode the engine can't have. |
| `levels.py`, `scenario.py` | no | Their odds were withdrawn (`scenario.py` header) and replaced by the hub scanners. |
| `agents/A_grid.py`, `E4/E5/E6` | results yes, code no | Their conclusions (costs, 16:00 flat, hours) become fixed engine defaults and filters. Their simulators are more copies of `missed.py:simulate`. |
| `agents/C_regime.py` | **yes, as the thesis-5 spec** (§3.7) | port `pivots_known_at`, `regime`, and the signal loop into the rule file |

---

## 5. Recommendation: **retire the 2-hourly LLM replay and replace it with `walkforward.py` plus a blinded discretion test**

| option | cost to reach the end of the series | trades it yields | can it answer "beats a coin flip"? | verdict |
|---|---|---|---|---|
| A. keep (2-hourly, as now) | **~$371** more (at $0.047/bar × 7,887 bars) | **~4.6 more (~6.6 total)** | no. It would need ≥ 169 trades for a 0.20R edge at z = 2, which is 287,300 bars at the current rate. The placebo is also defective (F1). | **retire** |
| B. reduce cadence (e.g. daily) | same $ per bar, spread over time | same ~6.6 | no. Cadence changes the calendar, not the sample size. | not recommended |
| **C. retire and replace** | `walkforward.py`: about 1 engineering session, then **seconds per rule** at ≈ $0 marginal cost. Discretion test: one LLM session over ~200 blinded engine events | hundreds per rule (thesis 5 Tier A alone gives 442) | **yes**, with a correct placebo, a ledger-based luck bar and net-of-cost R | **recommended** |

Numbers behind C:
- Per the desk's own ruling (SUMMARY.md:67-68, NOTES.md:2171-2176), every future firing records NO_TRADE by construction until a predicate exists. That is $0.047/bar spent to move a cursor.
- E8 showed this tape can't resolve an edge below ≈ 0.19R per trade even with n ≈ 444 (NOTES.md:1668-1671). About 7 discretionary trades can't resolve anything.
- Rule #1 on the engine gives MES plus the other three symbols in one run. That matches the pre-registration shape `OPEN_QUESTIONS.md:4-6` asks for.

**If the owner wants the discretion question answered** (the one thing that genuinely needs an LLM): the engine emits rule #1's events,
and a fresh LLM session sees each event's `bars[:i+1]` only (the same causality wrapper), in random order with dates hidden. It answers
FADE / WITH / SKIP plus a stop. The engine scores those calls against the mechanical rule and against P1 on the same events. That gives
n ≈ 200 decisions for roughly the cost of 2–3 current firings. It also tests the owner's continuation-vs-bounce judgement directly.

**Before anything else (owner action, since the desk can't touch the harness):** fix F1 in `replay.py:398-400` so the placebo mirrors
the geometry around its own fill, or stop quoting `replay.py score` z values. Also pin `source_bars` to a snapshot so "end of series"
stops moving.

---

## Ten-line summary

1. 16 of the 18 per-firing steps are mechanical or already scripted. Only the per-bar trade call (#8) and the NOTES prose (#15) need an LLM.
2. Step #8 has returned NO_TRADE on 800 consecutive bars, and SUMMARY.md:67-68 commits the desk to not trading MES until a pre-registered predicate exists.
3. Output so far: 3,400 bars, 51 callouts, 2 trades (+1.89R, +1.85R), about $160. That is $0.047/bar and $80/trade. Finishing costs ≈ $371 more for about 4.6 more trades.
4. A 0.20R edge needs ≥ 169 trades at z = 2, which is 287,300 bars at the desk's rate. The replay can't answer its own "beats a coin flip" question.
5. New finding F1: the harness placebo copies absolute stop and target prices (`replay.py:398-400`). An opposite-side draw is stopped out at the open for about −0.07R (reproduced exactly: −0.0671). The placebo is half copy, half scratch, so the z and the 4.5 leak alarm are about half as sensitive.
6. New finding F2: "flat by 16:00" actually exits at the close of the 16:00–17:00 bar (`replay.py:358-359`). Keep it for parity, but label it.
7. `walkforward.py` spec: import `permitted_risk`, `in_forbidden_window`, `cycle_deadline_crossed`, `spec`, `source_bars`, `_round`, `_size` directly. Reimplement `_open`/`_close`/`_resolve`/`cmd_next`/`cmd_score` because they write files and shell out to git.
8. The spec includes a parity mode (harness driven with `R.PAPER` redirected, already demonstrated), a regression fixture (R1's two trades plus placebos), mirrored-geometry P1, hour×ATR-matched P2, a random-level P3, and a ledger-based luck bar.
9. Rule #1 (60m 1-week LVN, first touch from below, short, stop 1 ATR / target 1 ATR from the fill) and thesis 5 (C_regime Tier A/B) are both fully specified as rule files with file:line sources.
10. Recommendation: retire the 2-hourly LLM replay. Build the engine, run rule #1 on four symbols in seconds, and test discretion with one blinded session of about 200 engine events.
