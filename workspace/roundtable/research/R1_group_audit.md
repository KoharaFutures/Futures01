# R1_group_audit — does the arithmetic do what the group name claims?

**Task:** `DISC-LEAD-05`. Round 1 audited **3 of 19** condition groups for name-versus-arithmetic and
found **3 of 3 misnamed** (`orderflow`, `openinterest`, `news` — `R1_flow_auction.md:13-223`). This
file audits the remaining **16**, plus the rest of `imbalance`.

**Why it matters and not just tidiness.** ~2,975,629 evaluations have already been screened against
these 79 conditions. A condition whose name does not describe its arithmetic does not produce a wrong
number — it produces a **correct number about a different object**, filed under the wrong heading.
Every published row that carries it is misread, and no re-run fixes that. This audit needs no new
data and no new code.

## Vocabulary — mine, from R1-D4, unchanged

| verdict | meaning |
|---|---|
| **CLEAN** | the arithmetic computes the object the name and description claim |
| **HONEST-DERIVED** | computes a *derived* quantity, and says so; no claim to read something it cannot |
| **PROXY** | named for an object it cannot see; computes a substitute, without saying so at the call site |
| **DEGRADED** | computes the right object from a degraded input, or with a threshold/tolerance that destroys the selectivity the name implies |
| **DEAD** | never fires, or fires so rarely on `csv/raw` that it cannot enter a result |
| **MISNAMED** | the name/description names a different object than the one computed — a reader is actively misled |

Two conditions can be CLEAN individually and the **group** still be MISNAMED, and the reverse.
Group verdict and per-condition verdict are recorded separately.

## Method

1. **Name/description vs arithmetic**, read line by line from `futures_agents/strategies/library.py`
   and every indicator and feature it reaches through.
2. **Firing census**, five cells, no backtest anywhere in it — no entries, no exits, no P&L. Each
   condition evaluated on every bar of a `SymbolFrame`, recording fires and the LONG/SHORT/FLAT split.
   `[measured: census.py over csv/raw — MCL_1h, MES_1h, MGC_1h, MNQ_1h (tfs 60,240) and MGC_5m
   (tfs 5,15,60), 5,000 bars each, 25,000 bar-evaluations per condition]`
   Four symbols are there because **every symbol is its own universe** — nothing below transfers
   between them unless the table shows it measured on each.
3. **`CONDITION_ERRORS` register empty in all five cells** `[measured: same run → errors {} ]`, so no
   verdict below is the silent-exception failure mode that `base.py:180-215` warns about.
4. **Which templates require it**, because a misnamed *optional* condition is a footnote and a
   misnamed *required* one is a misread published result.

---

## The template requirement map — read this before any verdict

`[repo-verified: futures_agents/strategies/combinator.py TEMPLATES, 13 templates]`
`[measured: python3 -c "from futures_agents.strategies.combinator import TEMPLATES; ..."]`

| group | REQUIRED by (a strategy of that template cannot exist without one of this group) | optional signal | base filter (unconditional) | optional filter |
|---|---|---|---|---|
| `trend` | **TREND, PULLBACK, FIBONACCI** | 7 | — | — |
| `structure` | **TREND, BREAKOUT, MULTI_TIMEFRAME** | 9 | — | — |
| `meanreversion` | **PULLBACK, REVERSAL, MEAN_REVERSION** | — | — | — |
| `liquidity` | **OPENING_RANGE, LIQUIDITY** | 2 | — | — |
| `volume` | **MOMENTUM, BREAKOUT** | 6 | — | — |
| `orderflow` | **REVERSAL** | 12 | — | — |
| `momentum` | **MOMENTUM** | 11 | — | — |
| `vwap` | **VWAP** | 9 | — | — |
| `profile` | **VOLUME_PROFILE** | 6 | — | — |
| `supplydemand` | **SUPPLY_DEMAND** | 5 | — | — |
| `multitimeframe` | **MULTI_TIMEFRAME** | 3 | `mtf_not_conflicted` in PULLBACK | — |
| `fibonacci` | **FIBONACCI** | 4 | — | `fib_sr_confluence` in FIBONACCI |
| `candlestick` | — | 4 | — | `inside_bar_compression` in SUPPLY_DEMAND |
| `imbalance` | — | 5 | — | `no_recent_imbalance` in 3 |
| `regime` | — | 2 | `regime_trending` TREND, `regime_ranging` MEAN_REVERSION | — |
| `volatility` | — | — | **`volatility_normal` in 12 of 13**; `volatility_compressed` BREAKOUT | `volatility_expanding` BREAKOUT |
| `openinterest` | — | 2 | — | `oi_expanding` in 2 |
| `time` | — | — | `avoid_lunch` REVERSAL, `opening_drive_window` OPENING_RANGE, `after_opening_range` LIQUIDITY | `power_hour` LIQUIDITY |
| `news` | — | — | — | `outside_news_blackout` **13 of 13**, `no_imminent_release` 12 of 13, `post_news_window` **0** |

**Three structural facts that fall straight out of this table and were not visible before it:**

- **`volume_not_thin` and `volatility_normal` are base filters in 12 of 13 templates each.** A base
  filter is unconditional — `generate_combinations` applies it to every strategy of that template
  `[repo-verified: combinator.py:581 region]`. So these two conditions are on the critical path of
  essentially the whole programme, and they are the two whose arithmetic most deserved an audit and
  had never had one. See `volatility` and `volume` below.
- **`post_news_window` is used by no template at all** — not required, not optional signal, not a
  base filter, not an optional filter. It is reachable only by hand. That is on top of round 1's
  finding that the group contains no news.
- **`orderflow` is required by REVERSAL, and REVERSAL is 1 of 13 templates.** My round-1 sentence
  "50.7% of a sample carries a proxy" came from the *optional* slots too: `orderflow` is an optional
  signal group in **12 of 13** templates, which is the widest optional reach of any group except
  `momentum` (11) and `structure` (9).

---

## Running tally

Filled in as each group is audited. Round 1's three are carried in.

| # | group | round | group verdict | conditions CLEAN / other |
|---|---|---|---|---|
| 1 | `orderflow` | R1 | **MISNAMED** (bar-shape group) | 0 / 3 PROXY |
| 2 | `openinterest` | R1 | **DEAD** (FILTER vetoes every entry) | 0 / 2 DEAD |
| 3 | `news` | R1 | **MISNAMED** (contains no news) | 0 / 3 |

---

# Group 4 — `candlestick` (5 conditions) → **CLEAN**

The first clean group. Recording it as emphatically as the misnamed ones, because an audit that
returns "misnamed" every time is not an audit.

| condition | kind | arithmetic | verdict |
|---|---|---|---|
| `candle_reversal` | SIGNAL | `hammer`: lower wick ≥ 60% of range and body ≤ 35%; `shooting_star`: upper wick ≥ 60%, body ≤ 35% `[repo-verified: futures_agents/indicators/candles.py:107-113]` | **CLEAN** |
| `candle_engulfing` | SIGNAL | body bigger than prior body, opposite sign, and `close >= prev.open and open <= prev.close` `[repo-verified: candles.py:120-130]` — body-engulfing, which is the standard definition | **CLEAN** |
| `candle_decisive_close` | SIGNAL | `marubozu`: `body_fraction >= 0.85`, direction from `close > open` `[repo-verified: candles.py:103-106]` | **CLEAN** |
| `candle_close_strength` | SIGNAL | `abs(close_location_value) >= 0.6` `[repo-verified: library.py:1437-1449]` | **CLEAN** — and see the finding below |
| `inside_bar_compression` | FILTER | `high <= prev.high and low >= prev.low` `[repo-verified: candles.py:133-137]` | **CLEAN** |

Firing rates 5.2–45.2%, all five alive on all five cells, direction splits 46–59% LONG — no
degenerate bias. `[measured: census, 5 cells]`

**Required by:** nothing. Optional signal in TREND, REVERSAL, LIQUIDITY, SUPPLY_DEMAND;
`inside_bar_compression` is an optional filter in SUPPLY_DEMAND. A misnaming here would have been a
footnote; there is none.

### Finding C-1 — the library computes CLV twice, and only the `candlestick` copy is named honestly

`close_location_value(bar) = ((C−L) − (H−C)) / range` `[repo-verified: candles.py:51-61]`.
`Bar.estimated_delta() = ((C−L) − (H−C)) / range × volume` `[repo-verified: data/bars.py:106-117]`.
**These are the same quantity, up to a factor of volume.** Measured:
`sign(CLV) == sign(Bar.delta)` on **98.2–98.3%** of bars across four contracts (the residual is
zero-volume bars, where `estimated_delta` short-circuits to `0.0`), and 92–93% of
`candle_close_strength` firings are also `delta_confirms_bar` firings
`[measured: python3 over csv/raw/{MGC,MCL,MNQ,MES}_1h.csv → MGC 4904/4996, MCL 4901/4992,
MNQ 4907/4994, MES 4912/4998; both/ccs = 1961/2116, 1874/2014, 2065/2219, 2025/2202]`.

So the repository holds the same arithmetic in two groups:

- as `candlestick`/`candle_close_strength`, whose docstring states outright that CLV "carries most of
  what a candlestick NAME encodes and is continuous" `[repo-verified: library.py:1438-1439]` — an
  honest, accurate filing;
- as `orderflow`/`delta_confirms_bar`, filed under the aggressor's name (R1-D4, PROXY).

**This is the cleanest available proof of round 1's `orderflow` verdict.** It is not that the repo
lacks a correct home for CLV — it has one, correctly labelled, in `candlestick`. The `orderflow`
group is a second copy of it under a name that claims a data column this repo does not have.

### Finding C-2 — two detected patterns have no consumer

`classify_candle` detects `doji` and `outside_bar` `[repo-verified: candles.py:100-102,140-144]` and
**no condition anywhere reads either** `[measured: grep -c 'doji\|outside_bar' futures_agents/strategies/library.py → 0]`.
Dead code in the indicator, not a misnamed condition — recorded so it is not mistaken for coverage.
`outside_bar` is the only pattern in the file that uses the 20-bar average range, so `_avg_range` is
computed on every bar for a pattern nothing consumes.

---

# Group 5 — `fibonacci` (4 conditions) → **DEGRADED**

The ratios and the drawing convention are right. Two upstream facts degrade all four, and one
condition is a filter in name only.

**The convention is correct and I checked it specifically**, because it is the classic place this
goes wrong: `fib_zone` measures ratios from the **end** of the leg back toward its start
(`a, b = hi − upper*span, hi − lower*span` on an UP leg) `[repo-verified: features.py:133-151]`, so
0.618 of an up leg sits above 0.786. `fib_sr_confluence` reimplements the same convention inline and
its comment records that measuring every ratio from `lo` regardless of direction would mirror the
whole set `[repo-verified: library.py:1145-1150]`. Both are right.

| condition | kind | arithmetic | verdict |
|---|---|---|---|
| `fib_golden_pocket` | SIGNAL | close inside the 0.618–0.786 band of `swing_leg()`; LONG on an UP leg | **DEGRADED** (via D-F1) |
| `fib_shallow_retrace` | SIGNAL | same, 0.382–0.5 | **DEGRADED** (via D-F1) |
| `fib_extension_reached` | SIGNAL | close inside 1.272–1.618 **beyond** the leg; SHORT on an UP leg `[repo-verified: library.py:1115-1120]` | **DEGRADED** (via D-F1) |
| `fib_sr_confluence` | FILTER | any of 4 ratios within `0.4 × ATR` of any `sr_level` | **DEGRADED** — passes 56.8–80.2% |

### D-F1 — `swing_leg()` is not a leg on 14.4–17.2% of bars

`swing_leg` returns `(last_swing_low, last_swing_high, direction)` `[repo-verified: features.py:119-131]`.
Those are the most recent confirmed swing of each kind — which is a single impulse leg **only if no
other confirmed swing lies between them.** Measured, counting confirmed swings strictly between the
two indices:

| cell | last high & low adjacent | **leg spans other swings** | `swing_leg()` is `None` |
|---|---|---|---|
| MGC 1h | 3976 / 4784 = 83.1% | **808 = 16.9%** | 16 / 4800 = 0.3% |
| MCL 1h | 4073 / 4759 = 85.6% | **686 = 14.4%** | 41 / 4800 = 0.9% |
| MNQ 1h | 3943 / 4763 = 82.8% | **820 = 17.2%** | 37 / 4800 = 0.8% |

`[measured: python3 using TimeframeFrame.visible_swings(i) against last_swing_high_index / last_swing_low_index]`

On those bars `span = hi − lo` is the extent of *several* legs, so every ratio is computed off the
wrong base and each of the three retracement/extension conditions is reporting a level that no trader
drawing the same chart would draw. It is not a look-ahead bug and not a crash — it is the right
arithmetic on the wrong leg, one bar in six. The guard `hi <= lo → None` handles the degenerate case
and fires on under 1% of bars, so the group is not DEAD, it is DEGRADED.

**What the real object would require:** an *alternating* swing sequence — the last **pair** of
consecutive confirmed swings, not the last of each kind independently. `visible_swings()` already
returns the ordered list `[repo-verified: features.py:421-425]`, so this needs no new data and no new
indicator; it needs `swing_leg` to take the last two elements of that list instead of two independent
"most recent" pointers.

### D-F2 — `fib_sr_confluence` is not a confluence test; it is nearly unconditional

It passes on **56.8% (MCL) to 80.2% (MES)** of bars `[measured: census, 5 cells]`. The mechanism is
arithmetic, not market:

- four ratios are tested `(0.382, 0.5, 0.618, 0.786)` `[repo-verified: library.py:1144]`;
- the tolerance is `0.4 × ATR` on each side, i.e. a window **0.8 ATR wide** `[repo-verified: library.py:1143]`;
- so the union of the four windows covers up to **3.2 ATR** of price, against a median leg span that
  is frequently smaller than that. Measured, the four windows cover **100% of the leg span on the
  median bar**, and cover it entirely on **2903/4784 (MGC), 2967/4759 (MCL), 2709/4763 (MNQ)** bars
  `[measured: python3, min(1, 4×0.8×ATR / span) per bar]`;
- and there are a median of **6 (MCL) to 9 (MNQ)** `sr_levels` available to match, max 12
  `[measured: len(TFSnapshot.sr_levels) over 4,800 bars per symbol]`.

On the majority of bars, *every price in the leg* is "at a fib level", so the filter reduces to
"does any S/R level exist inside the leg" — which is almost always yes. **A filter that passes four
times in five is not conditioning on anything.** Any FIBONACCI strategy carrying it as its optional
filter is effectively carrying no filter.

**Required by:** `fibonacci` is **required by FIBONACCI** and is an optional signal in PULLBACK,
REVERSAL, MEAN_REVERSION, MULTI_TIMEFRAME. So **no FIBONACCI strategy can exist without one of the
three D-F1-affected conditions**, and every one of them is computed off a mis-identified leg on
roughly one bar in six.

### One thing that is not a defect but should be recorded

The group mixes **two opposite directional hypotheses** under one name. `fib_golden_pocket` and
`fib_shallow_retrace` take LONG on an UP leg (retracement = trend continuation); `fib_extension_reached`
takes **SHORT** on an UP leg, on the comment "extension of an up leg is exhaustion"
`[repo-verified: library.py:1117]`. Both readings are defensible discipline, but a template drawing
"one condition from `fibonacci`" is drawing from a bag containing a continuation signal and a reversal
signal, and the group name does not say which. FIBONACCI's `exclusive` tuple prevents any two of the
three co-occurring `[repo-verified: combinator.py TEMPLATES, FIBONACCI exclusive]`, which prevents the
contradiction inside one strategy but not the ambiguity in reading the group's aggregate results.

---

# Group 6 — `liquidity` (7 conditions) → **PROXY (name)**, with **2 conditions DEAD per symbol** and a hard-coded window that is wrong at 1h

This group produced the largest finding in the audit so far.

## Name versus arithmetic

All seven conditions compute **price against a previous-period reference level**: prior-day high/low,
overnight high/low, running session high/low, the opening range, the initial balance. **Not one of
them reads any liquidity observable** — no book, no resting size, no volume at price, no queue.

The *descriptions* are all accurate ("Ran previous-day high/low then closed back inside",
`library.py:582`), so per-condition the arithmetic matches per-condition documentation. The **group
name** is the ICT/SMC jargon sense of "liquidity" — resting stops at prior extremes — and the repo
cannot see a resting stop. **Same shape as my round-1 `imbalance` verdict: PROXY at the group name,
honest at the arithmetic.**

**What the real object would require:** resting book depth by price (a DOM snapshot series), or at
minimum volume-at-price with an aggressor split. Neither is in `csv/raw` — the header is
`open_time,open,high,low,close,volume` `[repo-verified: head -1 csv/raw/MGC_1h.csv]`.

## D-L1 — `opening_range_breakout` and `opening_range_fade` are DEAD at 1h on 3 of 4 symbols, and the cause is a hard-coded 30

`or_minutes = 30`, hard-coded `[repo-verified: futures_agents/features.py:865]`. The opening range
accumulates only over base bars satisfying `0 <= minutes_since_open(b.ts, spec.rth_open) < 30`
`[repo-verified: features.py:891-895]`. **Whether any bar ever satisfies that is a per-symbol,
per-timeframe accident of whether `rth_open` lands on the bar grid.**

The 1h grid is 4,992 bars at `:00` and 8 bars at `:30`
`[measured: Counter(to_et(b.ts).minute) over csv/raw/{MGC,MNQ,MCL}_1h.csv → {0: 4992, 30: 8}]`.
RTH opens: MGC **08:20**, MCL **09:00**, MNQ/MES **09:30** `[repo-verified: futures_agents/config.py — get_contract(...).rth_open]`.

| cell | bars with `0 <= mso < 30` | bars where `opening_range` exists | complete | census: `opening_range_breakout` | census: `opening_range_fade` |
|---|---|---|---|---|---|
| **MGC 1h** | **0 / 5000** | **0** | 0 | **0 / 5000** | **0 / 5000** |
| **MNQ 1h** | **2 / 5000** | 10 | 8 | 7 / 5000 (**100% LONG**) | **0 / 5000** |
| **MES 1h** | **2 / 5000** | 10 | 8 | 8 / 5000 (**100% LONG**) | **0 / 5000** |
| MCL 1h | 215 / 5000 | 1709 | 1494 | 866 / 5000 | 390 / 5000 |
| MGC 5m | 108 / 5000 | 1873 | 1765 | 1033 / 5000 | 152 / 5000 |
| MNQ 5m | 114 / 5000 | 1710 | 1596 | — | — |
| MES 5m | 114 / 5000 | 1710 | 1596 | — | — |
| MCL 5m | 114 / 5000 | 1824 | 1710 | — | — |

`[measured: python3 over csv/raw, SymbolFrame._session_state; census columns from the 5-cell census]`

- **MGC at 1h: the opening range does not exist on a single one of 5,000 bars.** 08:20 + 1h grid can
  only give `mso ∈ {−20, 40, 70, 100}` `[measured: sorted distinct mso near the open]`. Both
  conditions are **DEAD**, not rare.
- **MNQ and MES at 1h: the opening range exists on 10 bars, and those 10 come from exactly two
  dates — 2025-11-28 and 2025-12-24** `[measured: the only 1h bars with 0 <= mso < 30 are
  2025-11-28 09:30 ET and 2025-12-24 09:30 ET]`. Both are **holiday half-sessions**, which is where
  the 8 off-grid `:30` bars come from. So **every opening-range signal MNQ and MES ever produced at
  1h came from Thanksgiving Friday and Christmas Eve** — and all 7/8 were LONG. That is not a small
  sample, it is a two-holiday sample wearing a 5,000-bar denominator.
- **MCL at 1h works by coincidence** — RTH opens 09:00, which is on the grid. But the range it builds
  is **one 1h bar = 60 minutes wide**, while `OpeningRange.minutes` reports **30**
  `[repo-verified: features.py:911]`. Every consumer that reads `.minutes` is told 30. **MISNAMED.**
- **At 5m all four symbols work**, because 08:20, 09:00 and 09:30 are all on the 5m grid.

**Nothing here transfers between symbols and nothing transfers between timeframes.** This is exactly
the independence rule: `opening_range_breakout` is a live condition on MCL 1h, a two-holiday artifact
on MNQ/MES 1h, and non-existent on MGC 1h.

## D-L2 — the template consequence: OPENING_RANGE strategies on 3 symbols contain no opening range

`liquidity` is **required by OPENING_RANGE and LIQUIDITY**
`[measured: TEMPLATES → required_groups]`, and OPENING_RANGE carries `opening_drive_window` as a
**base filter**. Since 2 of the 7 `liquidity` conditions are dead at 1h on MGC/MNQ/MES, the template
does not fail — it silently draws one of the other five. **So an "OPENING_RANGE" strategy on MGC at
1h is a prior-day / overnight / session-sweep / initial-balance strategy, filed under the opening
range's name.** That is the audit's whole thesis in one line: nothing crashed, no number is
arithmetically wrong, and the published heading describes a different object.

## D-L3 — cross-track: `StopKind.RANGE` is `StopKind.ATR` on MGC at 1h, on every bar

Not my vocabulary to rule on — R3 owns `StopKind` — but it follows directly from D-L1 and R3 cannot
see it without this measurement. `stop_price` for `StopKind.RANGE` reads `snap.opening_range` and
**falls through to `stop_mult * atr` when it is `None` or zero-size**
`[repo-verified: futures_agents/strategies/base.py:301-309]`:

```
elif self.stop_kind is StopKind.RANGE:
    orr = snap.opening_range
    if orr is None or orr.size <= 0:
        a = s["atr"]
        if not a: return None
        dist = self.stop_mult * a          # <- identical to StopKind.ATR
    else:
        dist = orr.size * self.stop_mult * 0.5
```

On **MGC 1h that branch is taken on 5,000 of 5,000 bars**, and on MNQ/MES 1h on 4,990 of 5,000. So
`StopKind.RANGE` and `StopKind.ATR` are **the same stop**, with no flag, on three of four symbols at
1h. Sent to R3 as `msgs/05_R1_R3_stopkind-RANGE.md`.

## Per-condition table

| condition | kind | verdict | note |
|---|---|---|---|
| `prior_day_sweep` | SIGNAL | **CLEAN** (arithmetic) / PROXY (group name) | 4.3–13.2%; reads `prev_day_high/low` |
| `overnight_sweep` | SIGNAL | **CLEAN** / PROXY (name) | 1.4–5.1% |
| `session_extreme_sweep` | SIGNAL | **CLEAN** / PROXY (name) | 0.5–1.8%; thinnest of the seven, MES/MNQ 1h at 29/28 fires |
| `prior_day_breakout` | SIGNAL | **CLEAN** / PROXY (name) | 41–52%. Note it is a *state*, not an event: it fires on every bar that closes beyond the PDH, not on the bar that crossed it |
| `opening_range_breakout` | SIGNAL | **DEAD** on MGC 1h; **DEAD-in-effect** on MNQ/MES 1h (2 holiday dates); alive MCL 1h and all 5m | D-L1 |
| `opening_range_fade` | SIGNAL | **DEAD** on MGC/MNQ/MES 1h (0 fires each); alive MCL 1h, MGC 5m | D-L1 |
| `initial_balance_break` | SIGNAL | **CLEAN** / PROXY (name) | 13.8–17.4%. Uses its own `mso < 60` accumulation `[repo-verified: features.py:888-890]`, which is **not** gated on the 30-minute window, which is why it survives where the OR conditions die |

---

# Group 7 — `meanreversion` (3 conditions) → **CLEAN**, with a strict-subset pair

| condition | kind | arithmetic | verdict |
|---|---|---|---|
| `bollinger_extreme` | SIGNAL | `close <= bb_lower` → LONG, `close >= bb_upper` → SHORT `[repo-verified: library.py:670-682]` | **CLEAN** |
| `bollinger_mean_pull` | SIGNAL | `bb_pctb <= 0.15` → LONG, `>= 0.85` → SHORT `[repo-verified: library.py:685-696]` | **CLEAN** |
| `keltner_outside` | SIGNAL | `close` outside the Keltner channel `[repo-verified: library.py:699-709]` | **CLEAN** |

Names, descriptions and arithmetic agree in all three. Firing 12.0–34.3%, direction 42.6–55.2% LONG,
alive on all five cells `[measured: census]`.

### D-MR1 — `bollinger_extreme` is a strict subset of `bollinger_mean_pull`

`%B <= 0` is the same statement as `close <= bb_lower`, and `0 < 0.15`, so the containment is
algebraic. Measured, **every** `bollinger_extreme` firing is also a `bollinger_mean_pull` firing **in
the same direction**: 601/601 (MGC), 686/686 (MCL), 635/635 (MNQ)
`[measured: python3 over csv/raw/{MGC,MCL,MNQ}_1h.csv, 5,000 bars each]`. And `keltner_outside`
overlaps `bollinger_extreme` on 77–83% of the latter's firings.

**Why this matters and is not pedantry.** `meanreversion` is **required by PULLBACK, REVERSAL and
MEAN_REVERSION** — three of thirteen templates, more than any group but `trend` and `structure`. The
combinator draws *one* condition from the required group, so this is not a double-count inside one
strategy. It is a **search-space claim**: the three "distinct" required conditions span a nested
family, so the effective variety the required slot offers is closer to 1.5 than to 3, and any
condition-level comparison among them is comparing overlapping populations rather than alternatives.
Not a defect. A fact that should be stated wherever `meanreversion` conditions are ranked against
each other.

### Note on the name

The arithmetic computes **location only** — "price is stretched from its band". Reversion is the
*direction assignment* (`LONG` below the lower band), which is a hypothesis, not a measurement. The
group name therefore names a hypothesis rather than an observable, but it does so transparently and
every description says what it computes. **CLEAN.**

---

# Group 8 — `momentum` (6 conditions) → **MISNAMED**, and it contains one exact duplicate

Two separate problems, either of which alone would change how the group's results read.

## D-M1 — `macd_directional` and `macd_hist_direction` are the same condition

By definition `macd_hist = macd_line − macd_signal`
`[repo-verified: futures_agents/indicators/core.py:198-199 — hist = [a − b for a, b in zip(line, sig)]]`,
and the feature layer stores all three from one `macd(c, 12, 26, 9)` call
`[repo-verified: features.py:233]`. Then:

- `macd_directional` computes `d = s["macd"] − s["macd_signal"]` and gates on `_deadband(s, d, 0.05)` `[repo-verified: library.py:245-248]`
- `macd_hist_direction` computes `h = s["macd_hist"]` and gates on `_deadband(s, h, 0.05)` `[repo-verified: library.py:257-260]`

`d` and `h` are the same number, the deadband fraction is the same `0.05`, and the direction rule is
the same sign test. **They are one condition with two names.** Measured: identical `(triggered,
direction)` on **5000/5000 bars in every cell** — MGC, MCL, MNQ at 1h
`[measured: python3 over csv/raw/{MGC,MCL,MNQ}_1h.csv → 100.00%]`, and the census shows identical
fire counts *and* identical LONG shares in all five cells (MCL 4052/4052 @ 50.1%, MES 4056/4056 @
48.6%, MGC 5m 4132/4132 @ 50.1%, MGC 1h 3974/3974 @ 48.9%, MNQ 4090/4090 @ 49.3%).

**Consequence for the search-size accounting, which is the part that matters.** `momentum` is
**required by MOMENTUM** and is an optional signal group in **11 of 13** templates — the widest
optional reach of any group. Every enumeration that offered "6 momentum conditions" was offering
**5**, and any two-condition confluence that happened to draw both MACD conditions was **counting one
reading twice and calling it agreement**. That is the identical failure mode the `mtf_aligned`
docstring records as already found and fixed for the multitimeframe group
`[repo-verified: library.py:795-801]` — it is still live here.

## D-M2 — 2 of the 6 are mean-reversion conditions, and their direction is the negation of the other 4

| condition | direction rule | hypothesis |
|---|---|---|
| `rsi_directional` | `RSI > 53` → LONG | momentum |
| `macd_directional` | `hist > 0` → LONG | momentum |
| `macd_hist_direction` | same | momentum (duplicate) |
| `stoch_directional` | `%K > %D` → LONG | momentum |
| **`rsi_extreme_reversal`** | **`RSI <= 30` → LONG** | **mean reversion** |
| **`stoch_extreme`** | **`%K <= 20` → LONG** | **mean reversion** |

`[repo-verified: library.py:212-285]`

`rsi_extreme_reversal`'s own description says it: "RSI below 30 / above 70 — **mean-reversion
trigger**" `[repo-verified: library.py:225]`. The condition is honestly described and **filed in the
wrong group.** `rsi_directional` would return SHORT on the same bar `rsi_extreme_reversal` returns
LONG, and both are `momentum`.

**The template consequence is the real finding.** MOMENTUM's `required_groups` are `['momentum',
'volume']` `[measured: TEMPLATES]`, and the combinator satisfies the requirement with **any one**
member of the group. So a strategy whose only `momentum` condition is `rsi_extreme_reversal` is a
**mean-reversion strategy published under the MOMENTUM template's name**, with a `volume` filter on it.
Nothing is arithmetically wrong; the heading names the opposite hypothesis. Measured population:
`rsi_extreme_reversal` fires 8.0–13.9% and `stoch_extreme` 35.3–40.6% of bars, with LONG shares of
35.5–48.6% and 32.3–52.8% `[measured: census]` — so these are not rare corners, they are a third of
the group's firing mass.

**Verdict per condition:** `rsi_directional` **CLEAN** (note: description says "above/below 50", the
arithmetic is above 53 / below 47 — the deadband is undocumented but does not misname the object);
`macd_directional` **CLEAN**; `macd_hist_direction` **DEGRADED — exact duplicate, no independent
content**; `stoch_directional` **CLEAN**; `rsi_extreme_reversal` **MISNAMED (group)**, clean
arithmetic and honest description; `stoch_extreme` **MISNAMED (group)**, clean arithmetic, description
silent on the direction hypothesis.

**Group verdict MISNAMED:** the group holds 4 distinct momentum conditions, 1 duplicate of one of
them, and 2 conditions whose direction rule is momentum's negation.

---

# Group 9 — `multitimeframe` (3 conditions) → **DEGRADED**, and **DEAD at the frame's top timeframe**

This group's docstrings are the most candid in the library — they record two defects already found and
fixed (`mtf_aligned` calling `snap.alignment()` with no argument, so the timeframe binding was inert
on all 428 sampled bars; and `mtf_aligned` returning `structure_trend`'s verdict on 4259/4259 MNQ bars
at the top timeframe) `[repo-verified: library.py:784-801]`. **The audit's finding is that the
same two defects are still live in one form each.**

Measured with the programme's own timeframe set, `tfs = [5, 15, 60, 240]`, 5m base, 5,000 bars:

| binding | `mtf_aligned` | `mtf_strongly_aligned` | identical `(fired, direction)` | `mtf_not_conflicted` | voting timeframes |
|---|---|---|---|---|---|
| MGC tf=5 | 1616 | 1403 | 4331/5000 = **86.6%** | 2774 | 0–4 |
| MGC tf=15 | 1470 | 1204 | 4732/4998 = **94.7%** | 2772 | 0–3 |
| MGC tf=60 | 746 | 746 | 4989/4989 = **100.0%** | 2763 | 0–2 |
| **MGC tf=240** | **0** | **0** | 4965/4965 = 100.0% | 2739 | 0–1 |
| MNQ tf=5 | 2080 | 1702 | 4130/5000 = 82.6% | 2979 | 0–4 |
| MNQ tf=15 | 1850 | 1521 | 4670/4999 = 93.4% | 2978 | 0–3 |
| MNQ tf=60 | 1293 | 1293 | 4999/4999 = **100.0%** | 2978 | 0–2 |
| **MNQ tf=240** | **0** | **0** | 4999/4999 = 100.0% | 2978 | 0–1 |

`[measured: python3 over csv/raw/{MGC,MNQ}_5m.csv, build_symbol_frame(s, [5,15,60,240]), each condition evaluated at each binding on every bar]`

## D-MTF1 — both signal conditions are DEAD at the frame's top timeframe, so MULTI_TIMEFRAME cannot exist there

`agreeing_timeframes(from_tf=tf)` counts only timeframes **at or above** `tf`, and both conditions
return `no()` when `voting < 2` `[repo-verified: library.py:793-801, 822-824]`. At the top timeframe
of the frame there is nothing above it, so voting never reaches 2 and **both fire zero times**:
0/4965 (MGC) and 0/4999 (MNQ) at tf=240.

The `no()` is *correct* — the docstring explains that the previous behaviour was to aggregate a single
vote and duplicate `structure_trend`, which was worse. But `multitimeframe` is **required by
MULTI_TIMEFRAME**, and only `mtf_aligned` and `mtf_strongly_aligned` are SIGNALs. So **a
MULTI_TIMEFRAME strategy whose primary timeframe is the top of its frame can never emit a signal** —
it is a structurally zero-trade strategy, exactly the shape of round 1's `openinterest` finding
(R1-Q2). Whether any such strategies entered the ~2,975,629 denominator is the same open question,
and I still cannot answer it without a sweep.

## D-MTF2 — `mtf_strongly_aligned` is indistinguishable from `mtf_aligned` at the top two timeframes

At `tf=60` with this frame the two conditions return **identical results on 100% of bars**, both
symbols. At `tf=15`, 93.4–94.7%. Only at the base timeframe, where 4 timeframes vote, does the
"graded half" distinguish a meaningful fraction (82.6–86.6% identical, i.e. it differs on 13–17%).

The docstring's stated purpose — "needs a condition that can tell three-of-three from two-of-three"
`[repo-verified: library.py:816-817]` — **is unreachable when only two timeframes vote**, and how many
vote is a function of the strategy's primary timeframe *and* of which timeframes the runner happened
to build. **DEGRADED**, and degraded by an amount that varies per binding.

## D-MTF3 — `mtf_not_conflicted` ignores its `tf` argument entirely, and it is a base filter in PULLBACK

```
library.py:837-841
def _mtf_ok(snap, tf):
    trends = {s.structure_trend for s in snap.tfs.values()}
    conflicted = "UPTREND" in trends and "DOWNTREND" in trends
```

`tf` is accepted and **never read**. `snap.tfs.values()` is every timeframe in the frame. **This is
precisely the defect the `mtf_aligned` docstring says was fixed** — "Previously this called
`snap.alignment()` with no argument, which aggregates every timeframe in the snapshot … the timeframe
binding was inert" `[repo-verified: library.py:786-791]`. The fix was applied to `mtf_aligned` and
`mtf_strongly_aligned` via `from_tf=tf`; **`mtf_not_conflicted` never got it.** The table above shows
the signature: on MNQ it fires **2978 times at tf=15, tf=60 and tf=240 alike.**

Two consequences, and the second is worse than the first:

1. **`mtf_not_conflicted` is a base filter in PULLBACK** `[measured: TEMPLATES]` — unconditional on
   every PULLBACK strategy. So every PULLBACK strategy carries a veto that is *the same veto* whatever
   timeframe the strategy trades.
2. **Its strictness is a property of the harness, not of the strategy.** With `tfs = [60, 240]` it
   passes 80.8–86.3% of bars (5-cell census); with `tfs = [5, 15, 60, 240]` it passes **55.5–59.6%**.
   Adding a timeframe to the frame adds another chance of an `UPTREND`/`DOWNTREND` pair, so **the same
   PULLBACK strategy is filtered ~25 percentage points harder depending on which timeframes the runner
   built** — a variable no report records and no strategy parameter controls. That is a
   measurement-artifact confound on a whole template, and it is the strongest single argument in this
   file for re-reading rather than re-running.

**Per condition:** `mtf_aligned` **CLEAN** (with D-MTF1's DEAD-at-top caveat);
`mtf_strongly_aligned` **DEGRADED** (no independent content at the top two bindings, DEAD at the top);
`mtf_not_conflicted` **DEGRADED — timeframe-inert**.

**One thing I want to record in the group's favour**, because it bears on `BRIEF` rule 2 ("multi-timeframe
agreement measured *worse*"): that conclusion was drawn from a group in which, at the two highest
bindings, the "strong" condition was a duplicate of the "weak" one, the base-filter member was
timeframe-blind, and the signal conditions were dead at the top timeframe. **Whether multi-timeframe
alignment helps is therefore still an open question here, not a settled negative** — what was measured
was this implementation of it. That is a finding, not a defence of the hypothesis.

---

# Group 10 — `profile` (6 conditions) → **DEGRADED** (round-1 verdict confirmed and quantified), plus **DEAD at 4h**

Round 1 filed all six as DEGRADED (`R1_flow_auction.md:339-408`) and claimed they can flip sign on the
same market day depending on which CSV is read. **Both now measured.**

Every one of the six reads `TFSnapshot.prior_profile` `[repo-verified: library.py:935-937]`, which is
`prior_session_profile` — `volume_profile(prior_bars, bins=40)` built from **that timeframe's own bars
of the previous completed session**, requiring `len(prior_bars) >= 10`
`[repo-verified: features.py:600-624]`.

## D-P1 — all six are DEAD at 240m, and `profile` is required by VOLUME_PROFILE

A CME trading day is 23 hours, so a 4h series has 5–6 bars per session — under the `>= 10` guard. So
the profile is never built.

| cell | `prior_profile is None` |
|---|---|
| MGC 60m | 151 / 5000 = 3.0% |
| MGC **240m** | **1348 / 1348 = 100.0%** |
| MCL 60m | 231 / 5000 = 4.6% |
| MCL **240m** | **1384 / 1384 = 100.0%** |
| MNQ 60m | 170 / 5000 = 3.4% |
| MNQ **240m** | **1347 / 1347 = 100.0%** |

`[measured: python3 over csv/raw/{MGC,MCL,MNQ}_1h.csv, TimeframeFrame.snapshot(i).prior_profile, every bar of each timeframe]`

`profile` is **required by VOLUME_PROFILE**, and four of the six are its only SIGNALs. So **a
VOLUME_PROFILE strategy at 240m is structurally zero-trade** — the third instance of that shape in
this audit, after `openinterest` (R1, round 1) and `multitimeframe` at the top timeframe (D-MTF1).
It also silently removes the `away_from_hvn` and `open_outside_value` filters at 4h: both return
`no()` when the profile is missing, and a FILTER returning `no()` **vetoes the entry**
`[repo-verified: library.py:1032-1033, 1050-1051]` — so at 4h they do not merely abstain, they block.

## D-P2 — the value area is a function of which CSV was loaded, measured

`volume_profile` bins **the bars of the timeframe it is called on**, so the same market session
produces a different POC/VAH/VAL depending on whether 5m, 15m or 60m bars were the source. Measured on
bars where all three profiles exist:

| cell | `in_value_area(close)` disagrees 5m vs 15m | 5m vs 60m | 15m vs 60m | median \|POC(5m) − POC(60m)\| | in ticks |
|---|---|---|---|---|---|
| MGC | 190 / 4617 = 4.1% | **279 = 6.0%** | 343 = 7.4% | 2.795 | ~28 ticks |
| MCL | 213 / 4616 = 4.6% | **308 = 6.7%** | 341 = 7.4% | 0.133 | ~13 ticks |
| MNQ | 149 / 4879 = 3.1% | **513 = 10.5%** | 428 = 8.8% | 24.99 | **~100 ticks** |

`[measured: python3, build_symbol_frame(MGC/MCL/MNQ 5m, [5,15,60]), comparing prior_profile.in_value_area(close) across the three timeframes at the same base bar]`

`in_value_area` is the **gate** of `poc_reversion` (`library.py:950`), the inverse gate of
`value_area_breakout` via VAH/VAL, and the whole of `open_outside_value` (`library.py:1055`). So on
6–10.5% of bars a `profile` condition's verdict — including its **direction** — is determined by the
runner's timeframe choice rather than by the session's auction. The round-1 claim stands, and the
effect is larger on the index micros than on gold or crude, which is again a per-symbol fact.

## Per-condition table

| condition | kind | verdict | note |
|---|---|---|---|
| `poc_reversion` | SIGNAL | **DEGRADED** | gated on `in_value_area` (D-P2); direction is `sign(poc − close)` with a `0.5 ATR` deadband. Description "rotating back toward the POC" claims **rotation** — the arithmetic tests only *position*, never that price is moving toward the POC. **Closer to MISNAMED than the others**: no velocity term exists anywhere in it `[repo-verified: library.py:942-959]` |
| `value_area_edge` | SIGNAL | **DEGRADED** | `abs(close − VAL) <= 0.35 ATR and low <= VAL and close >= VAL` — a genuine tag-and-hold test, the most faithful of the six. Thinnest: 82–383 fires per cell |
| `value_area_breakout` | SIGNAL | **DEGRADED** | `close > VAH + 0.25 ATR`. Description says "**Accepted** beyond" — acceptance in auction theory is *two closes* or time-at-price; the arithmetic is one close plus a margin. MISNAMED on "accepted", and it is the **only** `profile` condition ever named in the reports corpus (R1-D4) |
| `lvn_rejection` | SIGNAL | **DEGRADED** | within `0.3 ATR` of the nearest LVN, direction from `close > open`. Description says "**rejection** — price does not linger there"; the arithmetic tests **proximity** plus bar colour, never traversal or time-at-price. **MISNAMED** |
| `away_from_hvn` | FILTER | **DEGRADED** | and it **blocks** rather than abstains when the profile is missing (D-P1) |
| `open_outside_value` | FILTER | **DEGRADED** | reads `session_levels.day_open` against the prior value area; D-P2 applies directly |

**Required by:** VOLUME_PROFILE. Optional signal in TREND, VWAP, REVERSAL, OPENING_RANGE,
MEAN_REVERSION, BREAKOUT (6 templates); `away_from_hvn` optional filter in MEAN_REVERSION and
VOLUME_PROFILE; `open_outside_value` optional filter in VOLUME_PROFILE.

---

# Group 11 — `regime` (3 conditions) → **DEGRADED**: all three are timeframe-inert, and two are the same predicate

## D-R1 — `tf` is accepted and never read by any of the three

```
library.py:752-754   def _reg_trend(snap, tf):  r = snap.regime.regime      # tf unused
library.py:760-762   def _reg_range(snap, tf):  r = snap.regime.regime      # tf unused
library.py:768-774   def _reg_dir(snap, tf):    r = snap.regime.regime      # tf unused
```

`snap.regime` comes from `regime_at`, which reads `self.regime_tf` — **one timeframe chosen for the
whole frame** `[repo-verified: features.py:928-943]` — and `_default_regime_tf` picks the first of
`(15, 30, 5, 60, 10, 3, 1)` present `[repo-verified: features.py:819-825]`.

**So which timeframe the regime is read off is a property of the frame the runner built, not of the
strategy.** Measured, varying only `tfs` on an identical 5m base series:

| symbol | `tfs` | chosen `regime_tf` | `regime_trending` | `regime_ranging` |
|---|---|---|---|---|
| MGC | `[60, 240]` | 60 | 1117 / 5000 = 22.3% | 2758 = **55.2%** |
| MGC | `[5, 15, 60, 240]` | 15 | 981 = 19.6% | 3297 = 65.9% |
| MGC | `[5, 60]` | **5** | 849 = 17.0% | 3409 = **68.2%** |
| MGC | `[15, 60, 240]` | 15 | 981 = 19.6% | 3297 = 65.9% |
| MNQ | `[60, 240]` | 60 | 1112 = 22.2% | 2872 = 57.4% |
| MNQ | `[5, 15, 60, 240]` | 15 | 1246 = **24.9%** | 2804 = 56.1% |
| MNQ | `[5, 60]` | **5** | 1082 = 21.6% | 3204 = **64.1%** |

`[measured: python3, identical csv/raw/{MGC,MNQ}_5m.csv base, only the timeframe list varied]`

`regime_trending` is a **base filter in TREND** and `regime_ranging` a **base filter in
MEAN_REVERSION** `[measured: TEMPLATES]` — both unconditional on every strategy of those templates. So
a **13-percentage-point swing in MEAN_REVERSION's base filter (55.2% → 68.2% on MGC) is produced by
adding or removing a timeframe the strategy does not trade.** Same defect class as D-MTF3, on two more
templates, and this one is not even partially fixed: there is no `from_tf` anywhere in the group.

A 4h TREND strategy in a `[5, 15, 60, 240]` frame is gated by the **15-minute** regime. That is the
plain reading of `features.py:819-825` and there is nothing in the condition's name or description to
warn a reader of it.

## D-R2 — `regime_matches_direction` is `regime_trending` plus a direction vote

Both gate on `regime in ("TREND_UP", "TREND_DOWN")` `[repo-verified: library.py:754, 770-773]`.
Measured identical fire counts in all five census cells: MCL 1106/1106, MES 1112/1112, MGC 5m 981/981,
MGC 1h 1012/1012, MNQ 1105/1105 `[measured: census]`.

TREND carries `regime_trending` as a **base filter** *and* offers `regime` as an optional signal group.
So a TREND strategy that picks `regime_matches_direction` as one of its three optional signals adds
**zero additional gating** — the base filter has already applied the identical test — and contributes
only a direction vote, while occupying one of three optional slots and appearing in the strategy's
identity as a distinct condition. Any confluence count on such a strategy is one higher than the
number of independent readings it makes.

| condition | kind | verdict |
|---|---|---|
| `regime_trending` | FILTER | **DEGRADED** — timeframe-inert, frame-composition-dependent |
| `regime_ranging` | FILTER | **DEGRADED** — same |
| `regime_matches_direction` | SIGNAL | **DEGRADED** — same, plus no independent gate over `regime_trending` |

The three conditions' *arithmetic* faithfully reports what `classify_regime` returned, and the
descriptions say "Regime classifier says …", which is honest. The degradation is entirely in **which
series the classifier was run on** — invisible at the call site and not chosen by the strategy.
