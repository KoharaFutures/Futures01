# EF5 burst 04 — the declared population, and what the census removes from it

Declared **before** any profitability number was produced, frozen to
`EF5/out/population.json` with every strategy id in it.
`[measured: EF5/code/population.py]`

## 1. The pre-registration

| axis | value | why this and not something else |
|---|---|---|
| symbols | MES, MNQ | my cell. Separate universes; one index complex, so agreement is not corroboration |
| primary timeframes | 5, 15, 30 | my cell |
| frames | 5 → [5,15,60]; 15 → [15,60,240]; 30 → [30,60,240] | the repo's own `scout.FRAMES`, adopted unchanged rather than invented. Every primary tf is the **bottom** of its frame, which is why `D-MTF1` cannot bite |
| groups | **all 13 templates**, both symbols | `SYMBOL_PROFILES` narrows MES and MNQ to 7 groups each, but its timeframe lists are (5,15,60) and (1,5,15,60) — **neither profile has any opinion about 30m**. Applying a 7-group prior written for a different question would be a narrowing I could not defend afterwards. Profile membership is carried as a column instead. Cost: ~0.1 t-units of `free_t`, against a required Sharpe of 2.96 |
| budget | `max_per_template=800`, `max_total=999999`, `seed=20260922` | the library's own default seed, unchanged |
| arms | **RTH** (`rth_only=True`, as emitted) and **SESSION** (`rth_only=False`) | the SESSION arm is the regime the programme's rule actually describes and it has never been run. Paired on the identical rule set |
| substrate | `data/archive/{SYM}_{TF}m.jsonl` | verified against `csv/raw` in burst 01 |

**Population size, frozen:**

| cell | per arm | RTH | SESSION | in symbol profile |
|---|---|---|---|---|
| MES 5m / 15m / 30m | 1,689 each | 1,689 | 1,689 | 900 of 1,689 |
| MNQ 5m / 15m / 30m | 1,821 each | 1,821 | 1,821 | 936 of 1,821 |
| **total** | | **10,134 (MES)** | **10,926 (MNQ)** | |
| | | | **21,060 evaluations** | |

`free_t = sqrt(2·ln n)`, and the Sharpe each threshold implies on my 0.1585-year span:

| scope | n | `free_t` | annualised Sharpe required |
|---|---|---|---|
| one EF5 cell, one arm (MES) | 1,689 | **3.855** | **9.68** |
| one EF5 cell, one arm (MNQ) | 1,821 | 3.875 | 9.73 |
| all of EF5 | 21,060 | **4.462** | **11.21** |
| a single pre-registered hypothesis | 1 | 1.177 | **2.96** |
| programme-wide (`RANKING_FINDINGS`) | ~2.98M | 5.46 | 13.71 |

**No row in this cell can clear a search-width threshold. That is arithmetic, decided before any
measurement, and it is the single most important thing about the cell.**

## 2. D48 — the guard, and what it asserts

`population.py:assert_arm_ids_unique` asserts two separate things and both passed:

1. no `strategy_id` appears in both the RTH and SESSION arm of the same cell;
2. no `strategy_id` appears under two different (cell, arm) keys anywhere.

`session_arm()` uses `replace(s, filters=replace(s.filters, rth_only=False), _id=None)`. Without
`_id=None` the memoised id (`base.py:585`, memoised at `:611-623`) is copied forward, both arms
collapse into one `BacktestResult`, and the between-arm difference measures **exactly zero** — which
in this repository is indistinguishable from the settled finding that operating axes do not move
expectancy. The assertion is what makes "the RTH/SESSION comparison found nothing" a readable result
rather than a possible artefact.

`D43` is also satisfied by construction: `StrategyFilters.label()`/`identity` now carries `rth_only`,
which is what makes the two arms' ids differ at all. I checked that rather than assuming it — the
assertion above is the check.

## 3. What the census removes — two counts, and they differ by a factor of ten

`[measured: EF5/code/eliminate.py → EF5/out/elimination.json]`

### (a) VOID carriers — R1's method (a condition with 0 fires at its own evaluation timeframe)

| cell | arm | n | VOID carriers | % | causes |
|---|---|---|---|---|---|
| MES 5m | RTH | 1,689 | **132** | 7.82% | `oi_expanding` 49, `oi_price_confirmation` 42, `session_extreme_sweep` 50 |
| MES 5m | SESSION | 1,689 | 132 | 7.82% | same three |
| **MES 15m** | **RTH** | 1,689 | **232** | **13.74%** | **`volatility_compressed` 138**, `oi_expanding` 49, `oi_price_confirmation` 42, `session_extreme_sweep` 50 |
| MES 15m | SESSION | 1,689 | 132 | 7.82% | the three |
| MES 30m | RTH / SESSION | 1,689 | 132 | 7.82% | the three |
| MNQ 5m | RTH / SESSION | 1,821 | **133** | **7.30%** | `oi_expanding` 56, `oi_price_confirmation` 49, `session_extreme_sweep` 44 |
| MNQ 15m | RTH / SESSION | 1,821 | 133 | 7.30% | same |
| MNQ 30m | RTH / SESSION | 1,821 | 133 | 7.30% | same |

**The answer to "how many strategies did the census remove on MNQ": 133 of 1,821 per cell per arm =
7.30%, i.e. 399 of 5,463 in each arm and 798 of 10,926 across MNQ's whole declared population.**
Breakdown of the 133 (they overlap; 56+49+44 = 149 condition-instances across 133 strategies):

* **105 carry an `openinterest` condition** — `oi_expanding` (an *optional filter* on MOMENTUM and
  BREAKOUT, `combinator.py:224,272`) on 56, `oi_price_confirmation` (an *optional signal* via the
  `openinterest` optional group on the same two templates) on 49. `D47`, re-confirmed on a new
  substrate at three new timeframes. **A FILTER returning `no()` vetoes the entry**
  (`base.py:670-674`), so `oi_expanding` is the more damaging of the two: it does not weaken a
  strategy, it deletes it.
* **44 carry `session_extreme_sweep`**, whose entire support in my cell is 16:00–16:55 ET — the
  window the session rule forbids (burst 02).
* By group: BREAKOUT 47 of 132, MOMENTUM 54 of 170, LIQUIDITY 16 of 116, OPENING_RANGE 12 of 144,
  REVERSAL 4 of 160.

**MNQ's 7.30% is far below its published 27.4%, and that is a per-timeframe fact, not a
disagreement.** R1's 27.4% was measured over `[5,15,60,240]` and its three largest causes were
`profile` at **240m** (98 strategies), `mtf_aligned` at the **top** of the frame (48) and
`opening_range_*` at **1h** (16). **None of those three configurations exists in my cell**: my
frames' top timeframes are 60m and 240m but my *primaries* are 5/15/30, `profile` is alive at
5m/15m/30m, and the opening range resolves at all three. The verdict is per (symbol, timeframe) and
in my cell it runs in the favourable direction. What remains is `openinterest` plus one new cause.

**MES is the symbol the census hits hardest here, not MNQ** — 13.74% at 15m RTH against MNQ's 7.30%,
because `volatility_compressed` is VOID on MES 15m RTH (0 of 1,066 bars) and it is BREAKOUT's
*nailed-in* base filter, so **all 138 MES 15m BREAKOUT strategies are structurally zero-trade**. That
is the reverse of the published per-symbol ordering (MES 22.6%, MNQ 27.4%) and it is a good
illustration of why a symbol-level dead rate does not transfer across timeframes.

### (b) Zero-signal strategies — the direct measure, and it is ten times larger

`Strategy.evaluate` run over every admissible bar, counting strategies that never once fire. This
catches everything (a): conjunctions that cannot co-occur, signals that can never agree in direction
(`D25`), and the scope gate itself.

| cell | arm | n | zero-signal | % | **≥ 20 signals** | median signals (non-zero) |
|---|---|---|---|---|---|---|
| MES 5m | RTH | 1,689 | 1,261 | 74.7% | **103** | 4 |
| MES 5m | SESSION | 1,689 | 1,047 | 62.0% | **183** | 5 |
| MES 15m | RTH | 1,689 | 1,383 | 81.9% | **72** | 5 |
| MES 15m | SESSION | 1,689 | 1,219 | 72.2% | **114** | 4 |
| MES 30m | RTH | 1,689 | 1,376 | 81.5% | **60** | 3 |
| MES 30m | SESSION | 1,689 | 1,239 | 73.4% | **89** | 3 |
| MNQ 5m | RTH | 1,821 | 1,289 | 70.8% | **152** | 6 |
| MNQ 5m | SESSION | 1,821 | 1,099 | 60.4% | **277** | 9 |
| MNQ 15m | RTH | 1,821 | 1,457 | 80.0% | **76** | 5 |
| MNQ 15m | SESSION | 1,821 | 1,281 | 70.3% | **159** | 6 |
| MNQ 30m | RTH | 1,821 | 1,457 | 80.0% | **65** | 3 |
| MNQ 30m | SESSION | 1,821 | 1,330 | 73.0% | **102** | 4 |

**This is the number that decides whether my deliverable can be ten rows.** Signals are an *upper
bound* on trades — the engine refuses a new entry while a position is open — so the population that
could possibly reach a 20-trade floor is at most:

```
MES  RTH      103 + 72 + 60 = 235 of 5,067  (4.6%)
MES  SESSION  183 + 114 + 89 = 386 of 5,067  (7.6%)
MNQ  RTH      152 + 76 + 65 = 293 of 5,463  (5.4%)
MNQ  SESSION  277 + 159 + 102 = 538 of 5,463  (9.8%)
                       TOTAL  1,452 of 21,060 (6.9%)
```

Per cell that is **60–277 candidates**, and realised trades will be strictly fewer than signals. A
top 10 drawn from 60 candidates is not a selection from a population; it is **a sixth of the
population**, which is exactly the regime `RANKING_FINDINGS` worker 1 flagged as "report, do not
interpret" — the thin cells where the placebo cohort's own share forces the best placebo to rank 1–4
regardless of whether anything has an edge.

### The gap between (a) and (b) is itself the finding

`EF5/code/verify_census.py` cross-checks the two, and on MES 5m RTH:

```
void_carriers                    132
CHECK1 carriers with signals       0   -> PASS (census and evaluator agree)
non-VOID strategies             1,557
CHECK2 non-VOID but zero-signal 1,129
CHECK3 positive control fires   3,096   -> PASS (the harness sees signals)
```

**The condition-level VOID test sees 132 of 1,261 zero-signal strategies — 10.5%.** So R1's method,
applied honestly, catches only a tenth of the strategies in my cell that could never produce
evidence. The other 1,129 are killed by conjunction: two or three signals from distinct groups that
each fire 1–30% of the time and must also agree on direction, under filters that pass 77–99% of
bars. That is not a defect in anything — it is what "two signals and one filter is the ceiling"
(BRIEF rule 1) looks like from underneath.

**And it is the fourth-plus mechanism by which a null here could be an artefact**, so I say which
null I have: **for 60–82% of my declared population I have "the detector never fired", not "we
measured absence".** Only the remainder is capable of producing a result.

### Positive control, stated because a null without one is not readable

`CHECK3` builds a one-condition strategy (`price_above_ema50`, no optional filters) and runs it
through the same evaluator on the same bars: **3,096 signals on MES 5m RTH**. The evaluator, the
frame, the snapshots and the gate all work. The zero-signal counts above are a property of the
conjunctions, not of a broken harness.
