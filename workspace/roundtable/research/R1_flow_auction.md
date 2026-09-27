# R1 — Flow, auction and participant information

**Track:** R1 (DIVISION §2). **Class:** I — participant information.
**Owner:** researcher R1. **Round:** 1. **Started:** 2026-09-27.
**Deliverables:** R1-D1 … R1-D6 per DIVISION §3. Companion file:
`workspace/roundtable/research/R1_data_requirements.md` (R1-D3).

Marking convention per `BRIEF.md` rule 3: `[general knowledge]`, `[repo-verified: path:line]`,
`[measured: command → result]`. Written incrementally, newest sections appended.

---

## HEADLINE — the three phantom condition groups

DIVISION §Appendix A lists nineteen condition groups. Three of them name information the CSV
does not contain: `orderflow` (3 conditions), `openinterest` (2), `news` (3). Eight conditions,
10% of the library. Here is what each is **actually computing**.

### The single sentence

> **`orderflow` is a bar-shape group.** All three of its conditions reduce to algebra on
> `(open, high, low, close, volume)` of a single bar or a trailing window of them. The middle one,
> `delta_confirms_bar`, does not use volume at all — it is `close > (high+low)/2 and close > open`.
> **`openinterest` is dead code on this data** — both conditions read a column that is `None` on
> every bar of all 48 files, and both return "no signal", which for the FILTER
> (`oi_expanding`) means it vetoes every trade in any strategy that carries it.
> **`news` contains no news** — it is a deterministic recurrence-rule clock; the only quantity
> any of its three conditions reads is *minutes to / since a projected timestamp*. No headline,
> no consensus, no actual, no surprise magnitude.

### The evidence chain for `orderflow`

**Step 1 — the repo's own promise.** `futures_agents/indicators/volume.py:1-9`:

> "Order-flow measures are only as good as the data behind them. Where a feed supplies a true
> bid/ask volume split these functions use it; where it does not, `Bar.delta` falls back to a
> close-location proxy and every result derived from it is flagged `estimated=True`. A strategy
> validated on estimated delta has been validated on a proxy, and the system says so rather than
> quietly presenting it as order flow."

`[repo-verified: futures_agents/indicators/volume.py:1-9]`. The docstring is honest. **The promise
in its last clause is not kept at the point of use** — see Step 5.

**Step 2 — the fallback is unconditional on this data.** `Bar.bid_volume` / `Bar.ask_volume` are
`Optional[float] = None` `[repo-verified: futures_agents/data/bars.py:44-45]`.
`delta_is_estimated` is `bid_volume is None or ask_volume is None`
`[repo-verified: futures_agents/data/bars.py:91-92]`. `Bar.delta` returns
`ask_volume - bid_volume` when both exist and otherwise `estimated_delta()`
`[repo-verified: futures_agents/data/bars.py:95-104]`.

All 48 files carry one header and it has six columns:
`[measured: for f in csv/raw/*.csv; do head -1 "$f"; done | sort | uniq -c → "48 open_time,open,high,low,close,volume"]`.
The loader *would* accept `bid_volume` / `ask_volume` / `open_interest` under a long alias list
`[repo-verified: futures_agents/data/loader.py:28,40-44,135-137]`, and nothing under `csv/`
supplies them: `[measured: grep -rl "bid_volume\|ask_volume\|open_interest\|openinterest" csv/ → no matches]`.

So on every bar of every file in this repo's frozen snapshot, `delta` is the proxy:

```
[measured: python3 -c "from futures_agents.data.loader import load_csv;
s = load_csv('csv/raw/MGC_1h.csv','MGC',minutes=60,max_bars=300); b=s.bars[5]; ..."
  → bid_volume None  ask_volume None  oi None
  → delta_is_estimated True
  → all OI None: True        (all 300 bars)
  → all delta estimated: True (all 300 bars)
  → clv*vol == delta: True]
```

**Step 3 — the arithmetic.** `estimated_delta()` `[repo-verified: futures_agents/data/bars.py:106-113]`:

```
CLV   = ((close - low) - (high - close)) / (high - low)
delta = CLV * volume            # 0.0 if range <= 0 or volume <= 0
```

**`delta` is Chaikin's Accumulation/Distribution increment.** The A/D line, published in the
1970s, is defined as the running sum of `((C-L)-(H-C))/(H-L) * V` `[general knowledge]`. That is
`estimated_delta` verbatim. And `cvd` is that running sum, reset at the session anchor:
`C["cvd"] = cumulative_delta(bars, "session")`
`[repo-verified: futures_agents/features.py:223; futures_agents/indicators/volume.py:131-141]`,
with `C["delta"] = [b.delta for b in bars]`
`[repo-verified: futures_agents/features.py:219,222]`.

**So this repo's "cumulative volume delta" is a session-anchored Chaikin A/D line.** It is not
cumulative delta. Cumulative delta is the running sum of (trades filled at the offer − trades
filled at the bid) and requires a per-trade aggressor flag; A/D is a bar-shape oscillator that a
1978 chart service could compute. The two agree in sign perhaps often and disagree exactly where
order-flow traders claim the edge lives — absorption, where price does not move and aggression
does — because a bar with no range has `CLV` undefined and returns `0.0`
`[repo-verified: futures_agents/data/bars.py:111]`, whereas true absorption is a *large*
delta with *zero* range. **The proxy returns zero precisely in the case the real measure returns
its maximum.** That is not a noisy estimate; it is sign-blind in the family's central setup.

**Step 4 — condition by condition.**

| condition | kind | as named | what the arithmetic is |
|---|---|---|---|
| `cvd_directional` | SIGNAL | "cumulative volume delta sign for the session" | sign of the session-reset Chaikin A/D line, gated `abs(cvd) >= 0.25 * volume_of_current_bar` `[repo-verified: futures_agents/strategies/library.py:439-453]` |
| `delta_confirms_bar` | SIGNAL | "bar delta agrees with the bar's direction" | `close > (high+low)/2 AND close > open` (long); mirror for short. **Volume cancels** — only `sign(delta)` is tested, and `sign(CLV*V) = sign(CLV)` for `V>0`. A pure OHLC bar-shape predicate `[repo-verified: futures_agents/strategies/library.py:455-467]` |
| `delta_divergence` | SIGNAL | "price extends but CVD does not — absorption" | 20-bar rolling price high vs 20-bar rolling A/D high, trailing window only `[repo-verified: futures_agents/indicators/volume.py:144-170; library.py:469-478]`. BEARISH fires when a new 20-bar high prints on a bar that closes **low in its own range** or thin — i.e. an upper-wick rejection bar at a range extreme. A real, tradeable price-action pattern; it is not CVD divergence and it is not absorption |

**`delta_confirms_bar` is the sharpest single instance of the gap.** A condition in a group called
`orderflow`, described as "bar delta agrees with the bar's direction", evaluates to a two-term
inequality on the same four prices a 19th-century candlestick trader had. No volume. No participant.
`[repo-verified: futures_agents/strategies/library.py:459-466]`

**Step 5 — the `estimated` flag is set and never read.** This is the finding that turns the
honest docstring into a defect.

```
[measured: grep -rn "estimated" futures_agents/ --include=*.py | grep -v __pycache__
  → 13 hits, all inside futures_agents/indicators/volume.py and futures_agents/data/bars.py]
```

Zero hits in `futures_agents/strategies/library.py`, zero in `futures_agents/features.py`, zero in
`futures_agents/backtest/`, zero in `futures_agents/reporting` or the scan machinery. Consequences:

- The three `orderflow` conditions read `s["delta"]` and `s["cvd"]` with **no `delta_is_estimated`
  check** `[repo-verified: futures_agents/strategies/library.py:443-447,459-460,472-474]`.
- `VolumeProfile.estimated` is computed at `futures_agents/indicators/volume.py:258` and
  serialised at `:199`, and **no consumer reads it**. It never reaches a report, a ranking filter,
  or a strategy verdict.
- Therefore the docstring's "the system says so rather than quietly presenting it as order flow"
  is true of the *dataclass* and false of the *pipeline*. Every `scan_reports/` row that contains
  an `orderflow` condition presents a bar-shape predicate under the order-flow name, with the
  `estimated` flag available and unconsulted. **This is a candidate new defect; I have not
  assigned it a D-number (not mine to assign) and have logged it in `OPEN_QUESTIONS.md`.**

**Step 6 — `VolumeProfile.estimated` flags the wrong approximation.** It is
`any(b.delta_is_estimated for b in bars)` `[repo-verified: futures_agents/indicators/volume.py:258]`
— a *bid/ask-split* flag. A volume profile does not need an aggressor split; it needs
volume-at-price. The approximation a profile built from bars actually makes is the one at
`futures_agents/indicators/volume.py:225-232`: **each bar's volume is spread uniformly across
every price bin its range touches** (`share = (b.volume or 1.0) / span`). The docstring says so
plainly at `:216-222`. That approximation is never flagged by any field. So the flag that exists
labels an irrelevant deficiency and the relevant one is unlabelled.

### The evidence chain for `openinterest`

`oi_price_confirmation` (SIGNAL) and `oi_expanding` (FILTER) both open with
`if not s or not s.has("oi_change", "open_interest"): return ConditionResult.no()`
`[repo-verified: futures_agents/strategies/library.py:1281-1282,1309-1310]`.
`has()` is `all(self.values.get(k) is not None for k in keys)`
`[repo-verified: futures_agents/features.py:160-162]`. The column is
`C["open_interest"] = [b.open_interest for b in bars]`, all `None` on this data
`[repo-verified: futures_agents/features.py:278-279]`, and `C["oi_change"]` is `None` wherever
either endpoint is `None` `[repo-verified: futures_agents/features.py:306-313]`.

`[measured: … all OI None: True on 300 MGC_1h bars]` (command in Step 2).

**Verdict: both conditions are structurally incapable of firing on any file in `csv/raw/`.** The
group's own header comment is candid about the design intent —

> "Every condition here returns 'no signal' when the feed carries no open interest, which is most
> intraday exports. That is deliberate: a strategy built on an absent column would backtest as
> never firing, which is the honest result, rather than firing on a default of zero."
> `[repo-verified: futures_agents/strategies/library.py:1270-1275]`

— and the design is right. But the *consequence* is not recorded anywhere I can find, and it is
sharp and asymmetric:

- `oi_price_confirmation` is a SIGNAL. A strategy requiring it takes **zero trades**.
- `oi_expanding` is a FILTER returning `no()`. **A filter that never passes vetoes every entry.**
  Any strategy carrying it also takes zero trades.

So `openinterest` is not merely uninformative: it is a **guaranteed-null pair that any sampler
which can emit it will silently convert into zero-trade strategies.** This is a
sample-accounting question for the ~2,975,629 evaluations (`BRIEF.md`), not a strategy question,
and it is worth checking whether those zero-trade evaluations were counted in any multiple-testing
denominator. *Reachability measurement below; count question flagged, not answered — producing an
answer would require re-running sweeps, which DIVISION §8 forbids this round.*

### The evidence chain for `news`

The group header states the design: "Driven by the rule-based economic calendar, not by headlines.
A recurrence rule projects identically backwards and forwards … Conditioning on a scraped headline
would mean reading an article written after the bar."
`[repo-verified: futures_agents/strategies/library.py:1325-1331]`

The three conditions read exactly three scalars, all of them clock readings:

| condition | kind | reads | arithmetic |
|---|---|---|---|
| `outside_news_blackout` | FILTER | `snap.in_news_blackout` | `-before <= (bar_ts - event_ts)/60 <= after` for any projected HIGH-impact event `[repo-verified: futures_agents/features.py:986-990]` |
| `no_imminent_release` | FILTER | `snap.minutes_to_high_impact` | `>= 30.0` `[repo-verified: futures_agents/strategies/library.py:1338-1342]` |
| `post_news_window` | FILTER | `snap.minutes_since_high_impact` | `NEWS_BLACKOUT_AFTER_MIN < since <= 60.0` `[repo-verified: futures_agents/strategies/library.py:1345-1362]` |

All three are functions of `bar.ts` and a hard-coded recurrence table, projected once per series
`[repo-verified: futures_agents/features.py:946-1000]`. **The gap between the name and the
arithmetic: `news` is a `time` group.** Structurally it is indistinguishable from
`avoid_lunch` / `power_hour` — a calendar-derived timestamp predicate. It carries no
market-reaction information whatsoever: not the released number, not the consensus, not
`actual − consensus`, not the revision, not whether the print was a surprise, not the tape's
response. Real event trading is conditioned on the surprise `[general knowledge]`; here the
surprise term does not exist as a data object anywhere in the repo.

Two honest positives, which I am recording because they are the opposite of a complaint:

1. **`news` is leak-free by construction, and this is unusual.** A projected recurrence rule is
   the correct way to build a news filter for a backtest. A scraped-headline feed would import
   look-ahead. The design note at `library.py:1325-1331` is right and should not be "fixed".
2. **`news` is the only one of the three phantom groups that actually fires on this data**, because
   the calendar is generated rather than loaded. Its conditions are testable *as time filters*.

The **inventory** of which releases the calendar projects is R2's (`DIVISION §5.2`, R2-D5). I do
not audit `econ_calendar.py`. One handoff I owe R2, written to `OPEN_QUESTIONS.md`: the plumbing
filters to `impact.rank >= Impact.HIGH.rank` before computing proximity
`[repo-verified: futures_agents/features.py:972-973]`, so every MEDIUM/LOW rule in `ECON_RULES` is
invisible to all three `news` conditions regardless of what the calendar holds.

### Why this matters more than an expectancy number

`BRIEF.md` settles that nothing here is live-eligible. This finding says something the
expectancy tables cannot: **for three of nineteen condition groups, the null result is not evidence
about the family the group is named after.** "Order flow does not work on MGC" has never been
tested here. What was tested was Chaikin A/D, a bar-midpoint comparison, and an A/D divergence.
`openinterest` was not tested at all — it could not fire. `news` was tested, but as a clock.

**The manager's §6 warning, taken:** I am *not* claiming order flow works, and I am not claiming
it does not. The honest form is **untested here**, and the reason it is untested is a missing
column, not a measured verdict.

---
## R1-D4a — Reachability of the phantom groups, measured

`generate_strategies` at `max_total <= 400` (DIVISION §8's permitted reachability check), MGC,
timeframes 5/15/60, all thirteen groups forced:

```
[measured: python3 -c "from futures_agents.strategies.combinator import generate_strategies, TEMPLATES;
sts = generate_strategies('MGC',[5,15,60],groups=[t.group for t in TEMPLATES],max_total=390) ..."
  → generated 284 strategies, 13 groups present
  → carrying an `openinterest` condition: 19  (BREAKOUT 14, MOMENTUM 5)  = 6.7%
  → carrying an `orderflow`  condition: 144  = 50.7%
  → REVERSAL n=20, all 20 carry an orderflow condition: True
  → per-condition appearances: cvd_directional 62, delta_divergence 58,
    delta_confirms_bar 24, oi_price_confirmation 12, oi_expanding 9]
```

Three consequences, each of which is a statement about published results and not about markets.

**1. Half of a generated set is carrying the proxy.** 50.7% of strategies in this sample contain a
condition from the `orderflow` group, i.e. contain a Chaikin A/D term presented as order flow.
`orderflow` is offered as an `optional_groups` entry by **all thirteen** templates
`[repo-verified: futures_agents/strategies/combinator.py:166-332]`.

**2. The REVERSAL group is defined by the proxy.** `StrategyTemplate(group="REVERSAL",
description="Exhaustion and absorption against the prevailing move",
required_groups=("meanreversion", "orderflow"), …)`
`[repo-verified: futures_agents/strategies/combinator.py:199-208]`. `orderflow` is **required**, so
every REVERSAL strategy the combinator can build carries one of the three proxy conditions
`[measured: all 20 REVERSAL strategies in the sample carry one → True]`. A sample entry:
`['bollinger_mean_pull', 'delta_confirms_bar', 'fib_golden_pocket', 'value_area_edge',
'volatility_normal', 'volume_not_thin', 'avoid_lunch']` — where `delta_confirms_bar` is
`close > (high+low)/2 and close > open`.

**Therefore: every REVERSAL row in every `scan_reports/` file is a result about a bar-shape
predicate, not about absorption**, despite the template's own description naming absorption. This
is one of the thirteen uppercase groups that all published results are grouped by. It is the
largest single instance of the name/arithmetic gap in the repo.

**3. `openinterest` reachability is per-symbol, and it is MNQ's problem, not MGC's.**
`[measured: python3 -c "from futures_agents.strategies.profiles import groups_for; ..." →
MGC 6 groups, none of REVERSAL/MOMENTUM/BREAKOUT; MES 7 groups incl. REVERSAL;
MNQ 7 groups incl. MOMENTUM and BREAKOUT; MCL/ES/NQ/SPY/QQQ/MZC/MZS/MZW → None (full 13)]`.
`openinterest` is offered only by MOMENTUM and BREAKOUT
`[repo-verified: futures_agents/strategies/combinator.py:213-229, 265-276]`. So:

| symbol | default group set | can a default sweep emit a guaranteed-zero-trade OI strategy? |
|---|---|---|
| MGC | 6, no MOMENTUM/BREAKOUT/REVERSAL | **No** |
| MES | 7, incl. REVERSAL | **No** (but every MES REVERSAL strategy carries the delta proxy) |
| MNQ | 7, incl. MOMENTUM + BREAKOUT | **Yes** |
| MCL, ES, NQ, SPY, QQQ, grains | unprofiled → all 13 | **Yes** |

Per the independence rule, I state that as four separate facts and not one. Nothing about MGC's
immunity transfers to MNQ.

*(`profiles.py` is R2's audit surface per DIVISION §2; I called `groups_for()` as a reachability
probe and did not audit the file's contents.)*

---
## R1-D4 Proxy audit — all 27 conditions in the six participant-information groups

DIVISION §3 R1-D4: of the 27 conditions in `orderflow` (3), `volume` (3), `profile` (6),
`vwap` (5), `liquidity` (7), `imbalance` (3), which read participant information and which are
OHLCV derivations wearing the name. Every row carries a verdict and a path.

**Three verdict labels, which I define once so the table is unambiguous:**

- **PROXY** — the name promises below-the-bar or participant information; the arithmetic is a
  function of `(o,h,l,c,v)` only. A real desk running this family reads a different object.
- **HONEST-DERIVED** — the name is a legitimate OHLCV quantity and the arithmetic matches it.
  No gap. (`volume_not_thin` really is "volume above a percentile"; nothing is being faked.)
- **DEGRADED** — the *object* is the right object and would be computed the same way at a desk,
  but the sampling resolution available here materially changes its value. Cited with the
  measurement.

### orderflow — 3 conditions, 3 PROXY

| condition | verdict | the arithmetic | path |
|---|---|---|---|
| `cvd_directional` | **PROXY** | sign of the session-reset **Chaikin A/D line** `Σ CLV·V`, gated `abs(cvd) >= 0.25*volume` | `library.py:439-453`; `features.py:222-223`; `bars.py:106-113` |
| `delta_confirms_bar` | **PROXY** (the extreme case) | `close > (high+low)/2 AND close > open`. **Volume cancels** — only `sign(CLV·V)` is tested | `library.py:455-467` |
| `delta_divergence` | **PROXY** | 20-bar price high vs 20-bar A/D high, trailing only. Fires on a new-extreme bar that closes weak or thin | `volume.py:144-170`; `library.py:469-478` |

Full chain in the HEADLINE section. Summary: `delta` is `CLV × volume`
`[repo-verified: futures_agents/data/bars.py:106-113]`, `delta_is_estimated` is `True` on every bar
of every file `[measured]`, and the `estimated` flag is never read by any consumer
`[measured: grep -rn "estimated" futures_agents/ → 13 hits, all in volume.py and bars.py]`.

### volume — 3 conditions, 3 HONEST-DERIVED

| condition | verdict | the arithmetic | path |
|---|---|---|---|
| `relative_volume_high` | **HONEST-DERIVED** | `rel_volume >= 1.10`, where `rel_volume` is bar volume / 20-bar mean | `library.py:389-412`; `features.py:259` |
| `volume_surge` | **HONEST-DERIVED** | `percent_rank(volume, 60) >= 0.90` | `library.py:415-422`; `features.py:330-339` |
| `volume_not_thin` | **HONEST-DERIVED** | `percent_rank(volume, 60) >= 0.10` | `library.py:425-432`; `features.py:330-339` |

No gap in any of the three. Total traded volume per bar **is** in the CSV; these conditions read
it and say so. This is the group with the cleanest name-to-arithmetic match in the library, and it
is worth saying because it shows the repo *can* name things accurately when the data is there.

One caveat, which is the repo's own and which I am echoing rather than discovering:
`relative_volume_high`'s docstring says its threshold was calibrated against synthetic bars and
"Real futures volume has a much fatter right tail than the generator's, so this threshold is one to
re-check on real bars rather than inherit" `[repo-verified: futures_agents/strategies/library.py:405-411]`.
A threshold calibrated on a generator is a parameter-selection risk on real data, which belongs on
the anti-overfitting list. Not a proxy problem; a calibration problem.

Two absences worth naming, because they are what a volume-reading desk actually uses and neither
exists here: **(a)** no separation of volume into aggressive-buy and aggressive-sell — that is the
missing aggressor flag; **(b)** no **trade count** (number of executions) alongside volume, so
average trade size is not computable, and average trade size is the standard cheap proxy for
"institutional vs retail participation" `[general knowledge]`. A `trades` / `tick_count` column is
a *much* smaller acquisition than tick data and it is not in the header
`[measured: 48 files, header `open_time,open,high,low,close,volume`]`.

### profile — 6 conditions, 6 DEGRADED

The conditions themselves are faithful implementations of the market-profile vocabulary, computed
**strictly from the prior completed session** `[repo-verified: futures_agents/features.py:600-623]`
— no look-ahead, and the docstring at `:601-607` says so correctly. The degradation is upstream, in
how the profile is built.

| condition | verdict | the arithmetic | path |
|---|---|---|---|
| `poc_reversion` | DEGRADED | inside prior value area and `abs(poc-close) >= 0.5*atr` | `library.py:940-960` |
| `value_area_edge` | DEGRADED | close within `0.35*atr` of prior VAL/VAH, wick through, close back inside | `library.py:962-981` |
| `value_area_breakout` | DEGRADED | close beyond prior VAH/VAL by `> 0.25*atr` | `library.py:983-1004` |
| `lvn_rejection` | DEGRADED | close within `0.3*atr` of a prior-profile LVN; direction from `close>open` | `library.py:1006-1026` |
| `away_from_hvn` | DEGRADED (FILTER) | nearest prior-profile HVN more than `0.25*atr` away | `library.py:1028-1044` |
| `open_outside_value` | DEGRADED (FILTER) | session open outside prior VAL..VAH | `library.py:1046-1060` |

**Why DEGRADED and not PROXY.** A volume profile needs **exchange volume-at-price**, which is a
distinct data object from bar volume. It is not below-the-bar in the aggressor sense — it needs no
bid/ask split — so it is *closer* to reachable than delta is. But it is not in the CSV, and the
repo reconstructs it by **spreading each bar's volume uniformly over every price bin its range
touches**: `share = (b.volume or 1.0) / span` `[repo-verified: futures_agents/indicators/volume.py:225-232]`.
The docstring is candid: "That is an approximation of true tick-level distribution, but it is the
standard one and it is stable" `[repo-verified: futures_agents/indicators/volume.py:216-222]`.

**How much is lost — measured.** `volume_profile(..., bins=40)` is applied to the prior session's
bars *at the strategy's own timeframe* `[repo-verified: futures_agents/features.py:620-623, 665]`.
Bins are 1/40 of the prior day's range, so the smearing depends on the timeframe:

```
[measured: python3 -c "... load_csv(csv/raw/MGC_{1m,5m,1h}.csv); bins=40 across each day's range;
count bins each bar's range touches ..."
  MGC_1h: 175 days, median 23 bars/day, median bar touches  8 of 40 bins, 98% touch >= 4
  MGC_5m:  16 days, median 276 bars/day, median bar touches 3 of 40 bins, 28% touch >= 4
  MGC_1m:   4 days, median 1089 bars/day, median bar touches 2 of 40 bins,  8% touch >= 4]
```

At 60 minutes the median bar's volume is spread across **20% of the entire day's range**. A profile
built that way is close to structureless: its POC is determined mainly by where bar ranges overlap,
not by where volume traded. That makes the 1h "volume profile" arithmetically nearer a very coarse
**TPO/time-at-price** estimate (23 brackets per day) than a volume profile.

**The invariance test, which is the decisive one.** A true volume profile is *invariant to bar
sampling* — volume at a price is volume at that price however you slice time. The repo's is not:

```
[measured: python3 -c "... volume_profile(day's 1m bars, bins=40) vs volume_profile(same day's
1h bars, bins=40); |dPOC| expressed in the 1h ATR(14) the conditions themselves use ..."
  MGC 2026-09-17 0.45 ATR | 09-18 0.00 | 09-21 0.40 | 09-22 0.47
  MCL 2026-09-17 0.04 ATR | 09-18 0.18 | 09-21 2.02 | 09-22 0.23
  MES 2026-09-17 0.01 ATR | 09-18 0.35 | 09-21 1.74 | 09-22 0.16
  (n = 4 overlapping trading days per symbol: csv/raw/*_1m.csv spans only ~4-5 days)]
```

Compare those to the tolerances the conditions decide on: `value_area_edge` uses a band of
**0.35 ATR**, `poc_reversion` a floor of **0.5 ATR**, `lvn_rejection` **0.3 ATR**, `away_from_hvn`
**0.25 ATR**. On 7 of 12 symbol-days the POC moved further than `value_area_edge`'s entire
tolerance band purely by changing which CSV you read it from, and on two days it moved by ~2 ATR.

**So the six `profile` conditions can flip sign on the same market day as a function of bar
sampling.** Sample is n=4 days per symbol (the 1m files are short — Appendix B fact 3), so this
establishes *existence and magnitude*, not a rate. It is enough to say: the profile object here is
not the invariant it is named after. Per the independence rule, note MCL's worst case (2.02 ATR)
and MES's (1.74 ATR) are separate facts about separate contracts; MGC's largest was 0.47 ATR.

**Second-order finding — the flag labels the wrong thing.** `VolumeProfile.estimated` is
`any(b.delta_is_estimated for b in bars)` `[repo-verified: futures_agents/indicators/volume.py:258]`,
i.e. a *bid/ask-split* flag on an object that does not need a bid/ask split. The approximation a
bar-built profile actually makes — uniform range allocation — has no flag at all. And neither is
read by anything `[measured: grep, above]`.

### vwap — 5 conditions, 5 HONEST-DERIVED (with one important qualifier)

| condition | verdict | the arithmetic | path |
|---|---|---|---|
| `above_vwap` | HONEST-DERIVED | `close > vwap + 1sd` / `< vwap - 1sd` | `library.py:292-325` |
| `vwap_proximity` | HONEST-DERIVED (FILTER) | `abs(close-vwap)/atr <= 0.5` | `library.py:328-337` |
| `vwap_band_extension` | HONEST-DERIVED | `close >= vwap + 2sd` → SHORT; mirror → LONG | `library.py:340-353` |
| `vwap_band1_bounce` | HONEST-DERIVED | wick through the 1sd band, close back inside it and on the VWAP side | `library.py:355-369` |
| `vwap_reclaim` | HONEST-DERIVED | bar opened one side of VWAP, traded through, closed the other side | `library.py:371-385` |

**VWAP is the one participant-behaviour object this repo can compute essentially correctly**, and
that is a genuine positive. VWAP needs price and volume per bar and nothing else; the exact desk
quantity is `Σ p·v / Σ v` over the session, and a bar-level approximation using the typical price
`(h+l+c)/3` is what every charting package does `[general knowledge]`. `vwap()` resets on the CME
18:00 ET trading day by default and offers an RTH variant, and the docstring is explicit that these
are different numbers `[repo-verified: futures_agents/indicators/volume.py:46-57, 33-44]`. The bands
are one and two standard deviations of the session's own volume-weighted distribution
`[repo-verified: futures_agents/indicators/volume.py:~95-105]`.

The qualifier, and it is the only real gap in this group: **VWAP is only an institutional benchmark
if you can see execution against it.** The tradeable content of I-10 as desks run it is not "price
is above VWAP"; it is "a large participant is working an order benchmarked to VWAP, so flow is
predictably one-sided until the order is done" `[general knowledge]`. That inference needs
participation-rate evidence — trade counts, print sizes, a child-order cadence. None exists here.
So: the *line* is right; the *institutional-benchmark interpretation* of the line is not supported
by any data in this repo. The conditions above are mean-reversion-to-a-band conditions computed on
a volume-weighted anchor, and that is exactly how they should be described.

Two capability notes, both positives and both **untested here**:
- `anchored_vwap(bars, anchor_index)` exists `[repo-verified: futures_agents/indicators/volume.py:108-120]`,
  as do anchor generators `major_move_anchors` and `swing_anchors`
  `[repo-verified: futures_agents/indicators/volume.py:26-28 (__all__)]`. **No condition in the
  library consumes any of them** `[measured: grep -n "anchored_vwap\|AnchorVWAP\|swing_anchors\|major_move_anchors" futures_agents/strategies/library.py → no matches]`.
  Anchored VWAP is built, reachable, and has never been made into a condition. See §7 Q2.
- `vwap()` takes `rth_only` `[repo-verified: futures_agents/indicators/volume.py:46-48]` but
  `features.py` calls `vwap_bands(bars, "session", (1.0, 2.0))` with no `rth_only` argument
  `[repo-verified: futures_agents/features.py:248]`, so **every `vwap` condition in the library reads
  the Globex-session VWAP only.** The RTH VWAP — the one most retail platforms draw, per the
  docstring — is implemented and never used by a condition. Also untested; also cheap.

### liquidity — 7 conditions, 7 HONEST-DERIVED

| condition | verdict | the arithmetic | path |
|---|---|---|---|
| `prior_day_sweep` | HONEST-DERIVED | wick through PDH/PDL, close back inside | `library.py:581-585` + `_level_sweep` `:565-579` |
| `overnight_sweep` | HONEST-DERIVED | same against ONH/ONL | `library.py:588-592` |
| `session_extreme_sweep` | HONEST-DERIVED | same against session high/low | `library.py:595-600` |
| `prior_day_breakout` | HONEST-DERIVED | close beyond PDH/PDL | `library.py:603-616` |
| `opening_range_breakout` | HONEST-DERIVED | close beyond a **completed** OR | `library.py:619-632` |
| `opening_range_fade` | HONEST-DERIVED | wick through a completed OR boundary, close back inside | `library.py:635-647` |
| `initial_balance_break` | HONEST-DERIVED | close beyond first-hour range, only after `minutes_since_open >= 60` | `library.py:650-663` |

No name/arithmetic gap anywhere in this group. Session levels, previous-day levels, overnight
levels, the opening range and the initial balance are all **exactly** computable from timestamped
OHLCV plus session boundaries, and that is what the code does. Two look-ahead guards are explicit
and correct: the OR conditions require `orr.complete` with the reason stated inline — "An OR
breakout signal on an incomplete range is a look-ahead artefact"
`[repo-verified: futures_agents/strategies/library.py:623-626]` — and `initial_balance_break`
refuses to fire before 60 minutes have elapsed `[repo-verified: library.py:655-656]`.

**This group is the honest core of Class I.** It is why the manager's §6 prediction that the
EXPRESSIBLE set "consists of things already measured and already null (session-level sweeps,
profile location, VWAP location)" is *half* right — see my §6 contradiction note below.

The one thing missing is the reason a desk cares: **liquidity mapping is about resting size, not
about the level.** "Stops are clustered under PDL" is a claim about the resting book, which needs
DOM depth; here the level is a geometric coordinate with no size attached. So the repo can express
*where the stop-run level is* with full fidelity and cannot express *how much is resting there*.
That distinction decides I-11's verdict below.

### imbalance — 3 conditions, 3 PROXY (name), HONEST-DERIVED (arithmetic)

This group needs its own verdict shape, because the **library header is accurate and the
indicator's own docstring is not**.

| condition | verdict | the arithmetic | path |
|---|---|---|---|
| `imbalance_bar` | PROXY-BY-NAME | this bar: `range >= 2.0 * 20-bar mean range` **and** `volume >= 1.2 * 20-bar mean volume`; direction `close>open` | `library.py:1168-1176`; `indicators/structure.py:442-463` |
| `imbalance_pullback` | PROXY-BY-NAME | most recent such bar was 1–10 bars ago, trade in its direction | `library.py:1178-1191`; `features.py:577-599` |
| `no_recent_imbalance` | PROXY-BY-NAME (FILTER) | no such bar in the last 3 | `library.py:1193-1202` |

**The gap.** In order-flow vocabulary an "imbalance" is a specific footprint object: at a given
price level, the volume filled at the offer exceeds the volume filled at the bid one tick below by
some ratio (commonly 3:1), and "stacked imbalances" means several such levels consecutively
`[general knowledge]`. It requires a per-price bid/ask ladder. What this repo computes is a
**range-and-volume expansion bar** — a displacement bar. That is a perfectly good, well-defined
price-action object; it is not an imbalance.

**And the indicator docstring mis-states its own arithmetic.**
`detect_imbalances` is documented as "Bars whose range and **delta** both far exceed the recent
norm … the footprint of a real initiative move"
`[repo-verified: futures_agents/indicators/structure.py:444-448]`, but the code computes
`v_mult = bars[i].volume / avg_vol` `[repo-verified: futures_agents/indicators/structure.py:455,459-460]`
— **volume, not delta.** `delta` appears nowhere in the function. The library's own group header,
by contrast, is exactly right: "Bar-level aggressive participation: range and volume both far above
the recent norm" `[repo-verified: futures_agents/strategies/library.py:1160-1166]`. So the docstring
is the error, not the code, and the fix is one line of prose. Two further words to drop: "footprint"
has a technical meaning this object does not satisfy, and "delta" is not read.

### Tally of the 27

| verdict | n | groups |
|---|---|---|
| **PROXY** (name promises participant info, arithmetic is OHLCV) | **6** | `orderflow` 3, `imbalance` 3 |
| **DEGRADED** (right object, sampling materially changes its value) | **6** | `profile` 6 |
| **HONEST-DERIVED** (name matches arithmetic) | **15** | `volume` 3, `vwap` 5, `liquidity` 7 |

Plus, outside the 27 but inside the manager's diagnostic: `openinterest` 2 = **structurally dead**
(cannot fire), `news` 3 = **a clock, not news** (fires correctly, as a time filter).

**Six of 27, plus 2 dead and 3 misnamed, is 11 of 79 conditions — 14% of the library — where the
group name does not describe what the code computes.** That is the number I would put in front of
anyone reading a `scan_reports/` table.

---
## R1-D4 addendum — corrections to my own table, from `DEFECTS.md`

Read after writing the table; two of my rows need qualifying, and one repo defect corroborates a
finding of mine from a different direction. I am recording all three rather than silently editing.

**Correction 1 — `session_extreme_sweep` and `overnight_sweep` are not cleanly HONEST-DERIVED.**
D36 `[repo-verified: workspace/studies/DEFECTS.md:530-540]`: `session_levels()` builds
`session_high` from bars with `b.ts <= cutoff`, **including the bar being tested**, so
`bar.high > session_high` is arithmetically impossible and the 0.61% firing rate is degeneracy. A
causal reimplementation fires at 2.7–3.9%; `overnight_sweep` at 9.3–12.3% against a library-reported
RTH-only 4.7%. PDH/PDL reproduces exactly, so `prior_day_sweep` and `prior_day_breakout` stand.
**Revised verdict:** `prior_day_sweep`, `prior_day_breakout`, `opening_range_breakout`,
`opening_range_fade`, `initial_balance_break` = HONEST-DERIVED; `session_extreme_sweep`,
`overnight_sweep` = HONEST-DERIVED-BUT-BROKEN (the concept is expressible from OHLCV; this
implementation leaks the current bar into its own reference level). Group tally becomes
`liquidity` 5 clean + 2 broken. Not a proxy problem — a causality problem, and already known.

**Correction 2 — three more liquidity/profile conditions have known reachability gates I should
not restate as market facts.** D5: `prior_session_profile` requires ≥10 bars in the prior session,
so all six `profile` conditions fire on **0.0% of 1,148 4h bars**
`[repo-verified: workspace/studies/DEFECTS.md:57-62]`. D30: the opening range is never constructed
at 60m or 240m `[repo-verified: workspace/studies/DEFECTS.md:423]`. D23: previous-day levels are
derived from `is_rth(b.ts)`-flagged bars and `is_rth` is False on 100% of daily bars
`[repo-verified: workspace/studies/DEFECTS.md:306-315]`. So `profile` is 5m/15m/30m/1h only,
and `liquidity` is intraday-only, for plumbing reasons rather than market reasons.

**Corroboration — D5 and my invariance measurement are the same defect seen from two ends.**
D5 says the profile *vanishes* when bars get too coarse (≥10-bar gate). My measurement says that
well before it vanishes it is already *unstable*: at 60m the median bar smears across 8 of 40 bins
and the POC moves up to 2.02 ATR versus the same day computed from 1m bars. D5 caught the cliff;
the slope leading to it was not recorded. I am not claiming a new D-number.

**The defect most consequential for my whole track is D37**
`[repo-verified: workspace/studies/DEFECTS.md:541-548]`: "`min_signals=2` requires two conditions
to fire **on the same bar**. A sweep and its consequence never co-occur by definition. So every
ordered-chain idea … is inexpressible in the template system." Every operating framework in Class I
is a sequence — footprint reading is *aggression, then absorption, then failure to extend*; market
profile is *open type, then initial balance, then range extension or acceptance*; a stop-run trade
is *sweep, then reclaim*. See §7 Q3.

---
# R1-D1 — Class I family catalogue

Fifteen families, DIVISION §1 Class I, each under the mandatory eight-field schema of DIVISION §4.
Verdict vocabulary is DIVISION §4's: EXPRESSIBLE / PARTIAL / INEXPRESSIBLE-DATA /
INEXPRESSIBLE-ARCHITECTURE. Every INEXPRESSIBLE names **one** missing primitive, collected in R1-D5.

A note on what "minimum data" means here, because it is the field that does the work. I write the
**primitive**, not the product name. "A per-trade aggressor flag" is a primitive; "order flow" is a
product. The distinction is the whole point of R1-D5.

## I-1 Order flow / footprint reading (bid-ask footprint, stacked imbalances, delta at extremes)

**Mechanism.** At any price there are resting limit orders and arriving market orders. A footprint
shows, per price per bar, how much traded into the offer and how much into the bid. When aggressive
buying arrives at a price and price does not advance, someone larger is selling passively into it;
the aggressor is the weaker hand because he has already paid the spread and has no inventory left
to deploy. The trade is to position with the passive side once the aggressive side is exhausted.
`[general knowledge]`

**Who runs it, at what size.** Almost entirely prop and discretionary intraday traders, plus
execution desks using it to time child orders. Retail-accessible (Sierra Chart, Jigsaw, Bookmap,
ATAS) at $5k–$250k of risk capital; horizon seconds to a few hours. Not a CTA family — it does not
scale, because the edge is in a queue and the queue has finite depth. `[general knowledge]`

**Where it lives.** Liquid single contracts with a thick book: ES, NQ, CL, GC, ZN, 6E, and the
micros as a cheaper venue with a thinner book. Footprint bars are usually 1–5 minutes, or volume /
range bars. RTH plus the London hours; not the Asian session, where the ladder is too thin for the
read to mean anything. `[general knowledge]`

**Minimum data.** (1) **A per-trade aggressor flag** — for every execution, whether it filled at
the bid or the offer. (2) Per-trade price and size, i.e. time-and-sales. (3) A price-level
aggregation of (1)+(2) per bar: the footprint matrix. Nothing less will do: bar-level net delta
without the per-price breakdown loses stacked imbalances, and bar-level totals without the
aggressor flag lose delta entirely.

**How it is operated.** `[general knowledge]` Read in this order: (a) is the bar's delta consistent
with its close — did buyers pay up and get range for it; (b) at the bar's extreme, is there a large
one-sided print with no follow-through (absorption); (c) are imbalances *stacked* — three or more
consecutive price levels each ≥3:1 in one direction, which marks a genuine initiative leg rather
than noise; (d) does the next bar fail to extend beyond the absorbed level. Entry on the failure to
extend, not on the absorption itself. Invalidation: a single tick beyond the absorbed extreme with
delta continuing in the same direction — the passive side was not big enough. Stop 2–4 ticks beyond
the absorbed extreme, because the thesis is "that level held" and one tick through it falsifies the
thesis; the stop is tight *by construction* rather than by preference. Exits are scalps to the next
liquidity pocket or a hold to the session reference. Reported shape: hit rate 55–70% with payoff
0.6–1.0R — win-rate-heavy, payoff-light, which is the mirror of a trend system. Hold: 30 seconds to
20 minutes.

**How it dies.** Two ways. (a) **Iceberg orders and spoofing** make the visible ladder a lie: the
absorption you read was a refresh you could not see, or the size you read was never there. (b) In a
one-way trending tape absorption reads keep firing against the trend and the tight stop turns the
family into a payout machine for the trend. The regime that kills it is sustained directional
expansion; the regime that feeds it is balance with high volume.

**Expressibility here.** **INEXPRESSIBLE-DATA.** The missing primitive is **a per-trade aggressor
flag**. `Bar.bid_volume` / `Bar.ask_volume` exist as `Optional[float] = None`
`[repo-verified: futures_agents/data/bars.py:44-45]`; the loader has aliases ready for eight vendor
spellings of each `[repo-verified: futures_agents/data/loader.py:40-43]`; and nothing under `csv/`
supplies them `[measured: grep -rl "bid_volume\|ask_volume\|open_interest\|openinterest" csv/ → no matches]`.
`Bar.delta` therefore returns `CLV × volume` on every bar
`[repo-verified: futures_agents/data/bars.py:95-113]` `[measured: all 300 MGC_1h bars delta_is_estimated True]`.
Even with the flag, the footprint *matrix* has no home: `Bar` has no per-price structure at all
`[repo-verified: futures_agents/data/bars.py:28-47]`, so supplying bid/ask totals would give
bar-level delta and still not give stacked imbalances — that is INEXPRESSIBLE-ARCHITECTURE on top
of the data gap.

**Already tested here?** **No — and this is the finding.** The three `orderflow` conditions were
screened in ~2.97M evaluations, but they compute Chaikin A/D, a bar-midpoint comparison and an A/D
divergence (R1-D4). `cvd_directional` is named once in the whole reports+findings corpus
`[measured: grep -rc across scan_reports/ and workspace/studies/*.md → cvd_directional 1,
delta_confirms_bar 0, delta_divergence 0]`, and that one mention is D22's note that its firing rate
is 0.84–0.86 `[repo-verified: workspace/studies/DEFECTS.md:297-305]` — a firing-rate observation,
not a performance test. **No result in this repo is evidence about footprint reading.**

## I-2 Absorption and stopping volume

**Mechanism.** Price approaches a level, aggressive volume expands sharply, and range does *not*
expand: the aggression is being absorbed by passive size. The subsequent failure to extend is the
signal, because the aggressors are now trapped and must cover. `[general knowledge]`

**Who runs it, at what size.** Prop intraday and discretionary futures traders; also the standard
entry-timing tool for swing traders sizing into a level. $10k–$1m. `[general knowledge]`

**Where it lives.** Any liquid future, at a reference level (prior day's extreme, VWAP, a value-area
edge, a swing). 1–5m footprint or volume bars. `[general knowledge]`

**Minimum data.** **A per-trade aggressor flag** plus the *sequence* of it against range. The
defining measurement is high delta magnitude with near-zero price displacement — a ratio of two
things, one of which is not available.

**How it is operated.** `[general knowledge]` Watch a level being approached. Confirmations, in
order: volume per bar 2–4× the recent norm; delta strongly one-sided; range at or below the norm
despite that volume; then a bar that closes back away from the level. Enter on that close or on the
retest that holds. Invalidation: acceptance beyond the level — two consecutive closes through it.
Stop just beyond the absorbed extreme; target the opposite side of the balance area. Shape: 55–65%
hit rate, payoff 1–2R when the level is a real edge of value and ~0.5R when it is arbitrary.

**How it dies.** Icebergs again, and "absorption" that was simply a pause. The regime that kills it
is a news-driven repricing, where the absorbing size steps away and the level evaporates.

**Expressibility here.** **INEXPRESSIBLE-DATA.** Missing primitive: **a per-trade aggressor flag**.
This family is worse-served by the proxy than I-1 is, and the reason is arithmetic rather than
resolution: absorption means *large delta, zero range*, and the proxy computes delta as
`((C-L)-(H-C))/(H-L) × V`, which **returns exactly 0.0 when range is 0**
`[repo-verified: futures_agents/data/bars.py:110-111]`. **The proxy returns its minimum in the
family's defining case.** It is not a degraded measure of absorption; its sign is undefined there.
The closest expressible relative is the `imbalance` group's inverse — a high-volume bar with *low*
range — which no condition computes: `detect_imbalances` requires `r_mult >= 2.0`, i.e. high volume
**and** high range `[repo-verified: futures_agents/indicators/structure.py:452-462]`.

**Already tested here?** No. `delta_divergence`'s description says "absorption"
`[repo-verified: futures_agents/strategies/library.py:469-470]` and its arithmetic is a 20-bar A/D
divergence; it is never named in any report `[measured: grep count 0]`. Note also that a
*volume-high, range-low* condition is buildable from the CSV today — see §7 Q2.

## I-3 Iceberg / hidden size detection; passive size discovery

**Mechanism.** A large passive order is shown in small increments; each time it is hit, the same
size reappears. Detecting the refresh identifies where a large participant is defending, which is a
better level than anything on the chart. `[general knowledge]`

**Who runs it, at what size.** Prop scalpers and execution algos. Small size per trade, very high
frequency of observation. `[general knowledge]`

**Where it lives.** ES, ZN, CL — instruments where institutional passive size is routine. Tick
resolution; no bar concept at all. `[general knowledge]`

**Minimum data.** **A timestamped level-2 book-update stream (MBO/MBP with per-order events)**:
you must see the resting quantity at a price *decrease as trades print and then be replenished*.
Trade prints alone cannot distinguish a refreshed iceberg from a new order.

**How it is operated.** `[general knowledge]` Count executed volume at a price against the
displayed quantity that was there; when executed ≫ displayed and the quote does not move, mark the
level as defended. Enter with the iceberg, stop beyond the level, scratch immediately when the level
trades through, because an iceberg that lifts is the strongest single signal of a real break.
Reported shape: very high hit rate (70%+), very small payoff, ruined by one failure to scratch.

**How it dies.** The iceberg is pulled, or it was a spoof. Regime: any fast repricing.

**Expressibility here.** **INEXPRESSIBLE-DATA.** Missing primitive: **a resting-order-book update
stream keyed by price level (MBP-10 or MBO)**. The finest bar is 1 minute
`[repo-verified: DIVISION.md Appendix B fact 2; measured: csv/raw/ contains *_1m.csv and nothing finer]`,
and `Bar` has no book field of any kind `[repo-verified: futures_agents/data/bars.py:28-47]`.
Not proxyable: no function of OHLCV can distinguish replenishment from arrival.

**Already tested here?** No. Nothing in the 79 conditions references depth
`[repo-verified: DIVISION.md Appendix A — no depth/book condition in any of the 19 groups]`.

## I-4 DOM and book pressure; spoof-and-go; queue-position scalping

**Mechanism.** Imbalance between resting bid and ask depth predicts the next few ticks, weakly and
briefly. Queue position converts that into a fill you get paid for rather than pay for.
`[general knowledge]`

**Who runs it, at what size.** HFT and semi-automated prop. Latency-sensitive; co-location matters.
Spoof-and-go is *illegal* under Dodd-Frank §747 and is listed here because it is part of why the
honest version of this family degrades — the displayed book is adversarial. `[general knowledge]`

**Where it lives.** The front month of the most liquid contracts, tick by tick, all hours in which
the book is thick. `[general knowledge]`

**Minimum data.** **A timestamped full-depth book snapshot or update stream** with queue position
inference; and for the honest version, order-level events to model cancellation behaviour.

**How it is operated.** `[general knowledge]` Quote or lift based on a depth-imbalance ratio
computed over the top 5–10 levels; hold for ticks, not points; cancel on adverse depth change.
Sizing is inventory-limited, not risk-limited. Shape: tens of thousands of trades, edge of a
fraction of a tick per trade, Sharpe reported high and capacity low.

**How it dies.** Adverse selection: your resting order fills exactly when you did not want it.
Latency arms race. Cancellation noise making depth uninformative.

**Expressibility here.** **INEXPRESSIBLE-DATA**, and **INEXPRESSIBLE-ARCHITECTURE** as well.
Missing primitive: **a timestamped book-depth snapshot (top-N resting quantity per side)**.
Architecturally, the backtester fills on bar geometry with a cost model
`[repo-verified: DIVISION §2 assigns futures_agents/backtest/costs.py to R3; I do not audit it]` and
has no queue, so even with depth data there is no place to express "I was 40 contracts back at the
bid". The `ContractSpec` tick size exists `[repo-verified: futures_agents/config.py — ContractSpec]`
but a tick-level fill model does not.

**Already tested here?** No.

## I-5 Market making / liquidity provision / spread capture

**Mechanism.** Quote both sides, earn the spread and any exchange rebate, manage the inventory that
accumulates when the market runs. The P&L is a fee-and-spread business with an adverse-selection
cost. `[general knowledge]`

**Who runs it, at what size.** Designated and non-designated market makers, HFT firms, and a small
number of prop desks in less-contested products. Capital is margin for inventory, not directional
risk. `[general knowledge]`

**Where it lives.** Everything from ES to illiquid back months; the less-contested the product, the
wider the spread and the slower the required latency. `[general knowledge]`

**Minimum data.** **A quote stream (best bid / best offer with sizes) at event resolution**, plus a
fill model with queue priority, plus the fee schedule including maker rebates.

**How it is operated.** `[general knowledge]` Set a fair-value estimate; quote symmetrically around
it; skew the quotes against accumulated inventory; widen or pull on volatility and before scheduled
releases. There is no "stop": the risk control is inventory limits and quote withdrawal. Shape: a
very high hit rate on tiny wins and rare large inventory losses — the payoff distribution is the
inverse of a trend follower's and the tail is on the losing side.

**How it dies.** A gap while carrying inventory. Fee-schedule changes. A faster competitor taking
queue priority.

**Expressibility here.** **INEXPRESSIBLE-DATA** + **INEXPRESSIBLE-ARCHITECTURE**. Missing
primitive: **a best-bid/best-offer quote stream with sizes**. The CSV has no bid, no ask, no spread
`[measured: header is open_time,open,high,low,close,volume on all 48 files]`. And a passive-fill
model is a different engine: this one has one position at a time
`[repo-verified: DIVISION §3 R3-D3 cites futures_agents/backtest/engine.py:303-308 as the
position-lifecycle rule — R3's surface, and I defer the verdict on that line to R3]`.

**Already tested here?** No.

## I-6 Tape scalping (aggressive, sub-minute, size-driven)

**Mechanism.** Read the speed and size of prints; join a burst of aggression for a few ticks; exit
before the mean reverts. The edge is reaction time plus the tape's short-horizon autocorrelation.
`[general knowledge]`

**Who runs it, at what size.** Discretionary prop scalpers, usually 1–20 contracts, hundreds of
trades a day; and the funded-account retail cohort. `[general knowledge]`

**Where it lives.** ES/NQ/CL front month, 09:30–11:00 and 14:00–16:00 ET. Sub-minute.
`[general knowledge]`

**Minimum data.** **Time-and-sales at millisecond resolution** (price, size, timestamp per print).
Aggressor side is helpful but the size-and-cadence read is the core.

**How it is operated.** `[general knowledge]` Hold a directional bias from a higher reference;
trigger on a cluster of large prints in that direction; stop 3–6 ticks; target 4–10 ticks; flatten
on any pause. Shape: 45–60% hit rate, payoff near 1R, and the distribution is dominated by costs —
at 2 ticks of round-trip friction on a 6-tick target, a third of gross edge is commission and
spread.

**How it dies.** Costs. Overtrading. A quiet tape where the bursts are noise.

**Expressibility here.** **INEXPRESSIBLE-DATA.** Missing primitive: **a per-print
(timestamp, price, size) trade record — time-and-sales**. The finest object here is a 1-minute bar
`[measured: csv/raw/ has *_1m.csv as the finest interval]`, and Appendix B fact 2 records the same.
A 1-minute bar summarises roughly 200–2,000 prints into four prices; there is no reconstruction.
Separately, the BRIEF's rule 7 says "sub-hourly is a graveyard — at 5 minutes, 11–16% of strategies
make money" `[repo-verified: workspace/roundtable/BRIEF.md rule 7]`; that is a fact about 5-minute
*bar* strategies and I explicitly do **not** extend it to sub-minute tape reading, which was never
sampled.

**Already tested here?** No.

## I-7 Market profile / TPO: day types and opening types

**Mechanism.** Auction theory: a market's purpose is to facilitate trade, and it advertises prices
until it finds two-sided activity. Plotting time-at-price produces a distribution whose shape says
whether the auction is balancing (bell-shaped, mean-reverting) or trending (elongated, one
time-frame). Knowing which, you know whether to fade the extremes or to hold for continuation.
`[general knowledge]`

**Who runs it, at what size.** Its native home is the CBOT/CME floor community and its descendants:
discretionary futures traders, some bank flow desks, and the Market Profile / auction-theory
teaching lineage (Steidlmayer, Dalton). Retail to mid-size prop; $25k to a few million; horizon one
session to several weeks for composite work. `[general knowledge]`

**Where it lives.** Originally grains and bonds, now index and energy futures equally. The native
unit is the **30-minute TPO bracket** over the RTH session, with a composite over multiple days.
`[general knowledge]`

**Minimum data.** (1) **Session boundaries** and a fixed bracket clock. (2) **Time-at-price**, i.e.
which price levels traded in each 30-minute bracket — obtainable from bars finer than 30 minutes,
so this is *cheaper* than it looks. (3) For the volume-profile overlay, exchange volume-at-price.
(4) For day-type labelling, the *whole session*, which is why falsifiability is a live question
(R1-D6).

**How it is operated.** Full sequence in R1-D2. In brief `[general knowledge]`: classify the open
against the prior day's value area and the prior close; watch whether the initial balance (first
hour) holds; trade range extension in the direction of initiative activity or fade it back into
value if the extension fails; use single prints and excess as the invalidation levels.

**How it dies.** Composite value areas widen in a trend until "value" describes the whole range and
the framework says nothing. Overnight-driven gaps break the prior-day reference. Day types are
assigned with hindsight and the assignment is where the edge silently leaks out — see R1-D6.

**Expressibility here.** **PARTIAL.** What exists: `session_levels` gives previous-day high/low/
close, overnight high/low, session high/low, initial balance high/low and the day open
`[repo-verified: futures_agents/indicators/structure.py:305-318]`; a nine-window session map
including `RTH_OPEN`, `LUNCH` and `RTH_CLOSE` with "Closing imbalance and MOC flow"
`[repo-verified: futures_agents/timeutil.py:100-122]`; `initial_balance_break`
`[repo-verified: futures_agents/strategies/library.py:650-663]`; and `open_outside_value`, which is
literally the open-type test — "Session opened outside the prior value area (open-drive day type)"
`[repo-verified: futures_agents/strategies/library.py:1046-1060]`. What is lost: (a) there is **no
TPO bracket object** — no 30-minute time-at-price count anywhere
`[measured: grep -rn "TPO\|tpo\|bracket" futures_agents/ --include=*.py → see R1-D5]`; (b) profiles
are volume-smeared and timeframe-dependent (R1-D4); (c) **only the immediately prior session** is
available — `prior_session_profile` takes `self._day_order[position - 1]`
`[repo-verified: futures_agents/features.py:615-622]` — so **no composite profile and no naked POC**;
(d) D37 blocks the sequence. Verdict PARTIAL rather than INEXPRESSIBLE because the *location*
statements (open outside value, IB break, value-area edge) are all reachable today.

**Already tested here?** Partly, at the group level and never as auction theory. The
`VOLUME_PROFILE` group was screened `[repo-verified: scan_reports/2026-09-23_MGC-MES-NQ_deep-scan.md:117-120,162-165]`
and D5 records that it cannot produce a strategy at 4h or daily at all
`[repo-verified: workspace/studies/DEFECTS.md:57-62]`. `open_outside_value` — the one day-type
condition in the library — is named **zero** times in the whole reports and findings corpus
`[measured: grep -rc → 0]`. Day types and opening types have never been tested here in any form.

## I-8 Auction market theory: initiative vs responsive, excess, poor high/low, single prints, value migration

**Mechanism.** Classify each move by *who* is doing it. Initiative activity is a participant buying
above value or selling below it — they need the market to move. Responsive activity is buying below
value or selling above it — they need it to stop. Excess (a sharp tail at an extreme) marks a
price the auction rejected outright; a poor high (a flat, un-tailed extreme) marks one it did not
finish with and will likely revisit. Value migration day over day is the trend statement.
`[general knowledge]`

**Who runs it, at what size.** The same community as I-7, and the framework a great deal of
discretionary futures commentary is written in. `[general knowledge]`

**Where it lives.** Index, energy, metals, rates futures; RTH session with composite context.
`[general knowledge]`

**Minimum data.** (1) The prior session's value area — so `volume-at-price` or TPO counts;
(2) session extremes with their **tail structure**, i.e. how much *time* traded at the extreme —
one TPO wide is excess, several is a poor extreme. That is a time-at-price statement, so it needs
bars finer than the bracket, which the repo has at 1m/5m. (3) Two or more consecutive sessions, for
migration.

**How it is operated.** `[general knowledge]` Each session: mark prior VAH/VAL/POC; classify the
open; label the first-hour extremes as excess or poor; take responsive trades at value edges when
the day is balancing and initiative trades on range extension when it is not; the invalidation is
acceptance (multiple closes / several brackets) beyond the level you are defending. Stops go beyond
the *excess* — the tail — because the tail is the price the auction already rejected and trading
back through it falsifies the rejection. Reported shape: modest hit rate with good payoff on
initiative trades; the reverse on responsive trades.

**How it dies.** Every label is easier to apply after the fact. Assigning "initiative" to a move
that already happened is the failure mode and it is not detectable from performance alone.

**Expressibility here.** **PARTIAL, leaning INEXPRESSIBLE-ARCHITECTURE.** Location primitives
exist (value area edges, session extremes, prior-day levels — see I-7's citations). Three things
are missing and each is specific: (1) **a time-at-price count per price level per bracket** — the
primitive that distinguishes excess from a poor high; nothing in the repo counts time at price
`[repo-verified: futures_agents/indicators/volume.py:203-262 builds a volume histogram only]`;
(2) **value migration needs ≥2 prior sessions' profiles simultaneously**, and
`prior_session_profile` returns exactly one `[repo-verified: futures_agents/features.py:615-622]`;
(3) initiative-vs-responsive is a *directional* statement about who is transacting, which without
an aggressor flag reduces to "where price is relative to value" — expressible, and a different
claim. D37 blocks the session-long sequence `[repo-verified: workspace/studies/DEFECTS.md:541-548]`.

**Already tested here?** No. No condition in any of the 19 groups names excess, tails, single
prints, poor highs or value migration `[repo-verified: DIVISION.md Appendix A, full 79-condition
table]`.

## I-9 Volume profile: POC / VAH / VAL / HVN / LVN, composite vs session, naked POC

**Mechanism.** Volume traded at a price is a record of where the market found agreement. Prices with
a lot of volume behind them attract price back (an unfinished auction is finished); prices with very
little act as vacuums, traversed quickly. Trading location against that distribution gives you a
reference for both entry and invalidation. `[general knowledge]`

**Who runs it, at what size.** Very widely used — discretionary futures traders, prop firms, some
systematic intraday desks. It is the most retail-accessible member of this class because every
platform draws it. $10k to tens of millions; horizon intraday to multi-week for composites.
`[general knowledge]`

**Where it lives.** All liquid futures. Session profiles intraday; composite profiles (weekly,
monthly, "balance area") for swing context. `[general knowledge]`

**Minimum data.** **Exchange volume-at-price** — the traded volume at each price level, per
session. No aggressor split required, which makes this the *cheapest* acquisition on my whole track.
For composites: N consecutive sessions of the same. For a naked POC: a POC from an arbitrary past
session, retained until touched.

**How it is operated.** `[general knowledge]` Mark prior POC, VAH, VAL. Responsive trades: fade the
value-area edge back toward POC when the day is balancing, stop beyond the edge by a small multiple
of the profile's own bin width or a fraction of ATR, target POC. Initiative trades: on acceptance
outside value (two or more closes, or a bracket's worth of time), target the next HVN or the
opposite edge of the developing profile. LVNs are used as *stop locations*, not entries, because
price does not linger there and a stop placed inside an LVN is either not touched or blown straight
through. Naked POCs are magnets: enter toward them, exit at them. Shape: high hit rate on responsive
trades (60–70%) with payoff below 1R; lower hit rate with payoff 1.5–3R on initiative trades.

**How it dies.** Trend. In a directional market the value area migrates every day and yesterday's
edges are inside today's range before the open. The composite widens until it no longer discriminates.

**Expressibility here.** **PARTIAL.** Every location concept exists as a condition: `poc_reversion`,
`value_area_edge`, `value_area_breakout`, `lvn_rejection`, `away_from_hvn`, `open_outside_value`
`[repo-verified: futures_agents/strategies/library.py:940-1060]`, computed strictly from the prior
completed session with an explicit look-ahead guard
`[repo-verified: futures_agents/features.py:600-607]`. Three losses, each specific:

1. **The profile is reconstructed, not measured.** Bar volume is spread uniformly across every bin a
   bar's range touches `[repo-verified: futures_agents/indicators/volume.py:225-232]`, and the
   consequence is quantified in R1-D4: at 60m the median bar smears over 8 of 40 bins, and the POC
   for the same trading day moves by up to 2.02 ATR (MCL), 1.74 ATR (MES), 0.47 ATR (MGC) depending
   on which CSV you compute it from — against tolerance bands of 0.25–0.5 ATR in the conditions
   themselves. Missing primitive: **exchange volume-at-price per session**.
2. **No composite and no naked POC.** `prior_session_profile` reads exactly `position - 1`
   `[repo-verified: futures_agents/features.py:615-622]`. There is no multi-session profile and no
   persistence of an untouched POC. This is INEXPRESSIBLE-ARCHITECTURE and it is **cheap to fix** —
   the function already has `self._day_order` and `self._day_bars`, so a composite is a loop bound
   change plus a cache key.
3. **Unavailable above 1h.** D5: `prior_session_profile` requires ≥10 prior-session bars, so all six
   conditions fire on 0.0% of 1,148 4h bars `[repo-verified: workspace/studies/DEFECTS.md:57-62]`.

**Already tested here?** **Yes, more than any other Class I family, and it is the one place a Class I
group produced the repo's better-looking rows** — MGC 1h VOLUME_PROFILE n=28 win 71.4% e=+0.295
t=1.53; MES 1h n=20 e=+0.448 t=3.04; MES 15m n=24 e=+0.312 t=2.00
`[repo-verified: scan_reports/2026-09-23_MGC-MES-NQ_deep-scan.md:117-120,136]`. **And all of it is
subject to the programme-wide verdict:** best t anywhere is 3.923 against `free_t = 5.46`, nothing is
live-eligible, and D6 records that the 20-trade floor selects on stop width — measured on NQ
`value_area_breakout` itself `[repo-verified: workspace/studies/DEFECTS.md:63-69]`. I state the rows
and stop, per DIVISION §4.

## I-10 VWAP as an institutional benchmark; TWAP; anchored VWAP; execution-algo footprints

**Mechanism.** Large orders are benchmarked to VWAP or TWAP, so the desk executing them must
participate throughout the session. That creates predictable one-sided pressure that persists until
the parent order completes, and it makes the VWAP line itself a level where the benchmark-followers
become buyers or sellers. `[general knowledge]`

**Who runs it, at what size.** Two distinct groups. (a) Execution desks and algo providers, who
*are* the flow. (b) Traders positioning around it: prop intraday, and the very large retail cohort
who use VWAP as a mean-reversion anchor without any institutional inference at all.
`[general knowledge]`

**Where it lives.** Index futures most of all, because their VWAP is tied to cash-equity execution.
Intraday, RTH-anchored for the equity-linked read and Globex-anchored for the futures-native read —
different numbers. `[general knowledge]`

**Minimum data.** For the *anchor*: price and volume per bar — available. For the *institutional
inference*: **a participation-rate observable** — trade count per bar, or average print size, or
child-order cadence. Without one, "an algo is working" is unfalsifiable.

**How it is operated.** `[general knowledge]` Anchor VWAP to the session for intraday fair value, or
to an event (a gap, a release, a swing) for "what has everyone in since then paid". Trade toward the
anchor when extended past a band; trade away from it on a reclaim. Stop on the other side of the
band you are using; the band, not a fixed distance, because it scales with the session's own
dispersion. Institutional read: if price holds above session VWAP all day on rising volume, assume a
buy program and do not fade. Shape: mean-reversion-to-band trades are high hit rate / low payoff;
VWAP-reclaim trend trades are the reverse.

**How it dies.** On a trend day VWAP is beneath price all day and every fade loses. The
institutional inference dies whenever the flow was not benchmarked — which you cannot check.

**Expressibility here.** **PARTIAL — and this is the strongest positive on my track.** The anchor
itself is computed correctly: `vwap()` resets on the CME 18:00 ET trading day, offers an RTH variant,
and its docstring states plainly that these are different numbers
`[repo-verified: futures_agents/indicators/volume.py:33-57]`; bands are volume-weighted standard
deviations of the session's own distribution `[repo-verified: futures_agents/indicators/volume.py:72-105]`;
five conditions consume them `[repo-verified: futures_agents/strategies/library.py:292-385]`. What is
lost:

1. **The institutional inference.** Missing primitive: **a per-bar trade count (number of
   executions)**. With volume alone you cannot compute average trade size, which is the standard
   cheap proxy for participant mix `[general knowledge]`. The CSV has no such column
   `[measured: 48 files, header open_time,open,high,low,close,volume]`. This is a far smaller
   acquisition than tick data and it is the single cheapest thing on my whole ledger.
2. **Anchored VWAP is fully built and wired to nothing.** `AnchorVWAP` with a `knowable_index`
   look-ahead guard and a `value_at()` that returns `None` before the anchor was identifiable
   `[repo-verified: futures_agents/indicators/volume.py:317-352]`; `build_anchor_vwap`
   `[:361-386]`; `major_move_anchors` `[:389-419]`; `swing_anchors` `[:421-435]`; and a dedicated
   test file `[repo-verified: tests/test_anchored_vwap.py:16-90]`. **No condition and no feature
   consumes any of it**
   `[measured: grep -rn "anchored_vwap\|AnchorVWAP\|swing_anchors\|major_move_anchors\|build_anchor_vwap" futures_agents/ → hits only in indicators/volume.py and indicators/__init__.py re-exports; grep -c in strategies/library.py → 0]`.
   The `AnchorVWAP` docstring asserts "the feature layer never exposes an anchor that is not yet
   knowable" `[repo-verified: futures_agents/indicators/volume.py:330-331]` — **vacuously true,
   because the feature layer exposes no anchors at all.** A built, guarded, unit-tested subsystem
   with no caller.
3. **Only the Globex-session VWAP is reachable.** `features.py` calls
   `vwap_bands(bars, "session", (1.0, 2.0))` with no `rth_only` and no `week` anchor
   `[repo-verified: futures_agents/features.py:248]`, although `vwap_bands` accepts both
   `[repo-verified: futures_agents/indicators/volume.py:72-74]`. The RTH VWAP — the line most
   platforms draw and the one tied to cash execution — is implemented and unreachable by any
   condition. TWAP is not implemented at all `[measured: grep -rni "twap" futures_agents/ → none]`.

**Already tested here?** Partly. The `VWAP` group was screened — e.g. MES 4h VWAP n=21 e=+0.479
t=1.57, MGC 1h VWAP n=21 e=+0.019 t=0.14
`[repo-verified: scan_reports/2026-09-23_MGC-MES-NQ_deep-scan.md:118,139]` — under the programme-wide
null. `above_vwap`'s own docstring records that as `close != vwap` it fired on 99.99% of bars and
produced the family's largest trade counts with negative expectancy, which is why it was tightened
to the first band `[repo-verified: futures_agents/strategies/library.py:295-312]`. **Anchored VWAP,
RTH-anchored VWAP, weekly-anchored VWAP and TWAP have never been tested here at all.**

## I-11 Liquidity mapping and stop-run harvesting; relative-liquidity models

**Mechanism.** Stops and resting orders cluster at obvious levels — prior day's extremes, overnight
extremes, session extremes, round numbers, the opening range. Running them produces a burst of
forced flow; if that flow is absorbed rather than continued, the run was liquidity-taking rather
than a real break, and the reversion is the trade. `[general knowledge]`

**Who runs it, at what size.** Prop intraday, and it is the mechanical core of most of the retail
"smart money" literature. Also, in a quieter form, execution desks choosing where to work orders.
$5k to a few million. `[general knowledge]`

**Where it lives.** Index and energy futures particularly; the London and RTH opens; 1m–15m.
`[general knowledge]`

**Minimum data.** The *levels* need only timestamped OHLCV plus session boundaries. The *edge*
needs **resting-size-by-price (book depth)** to know whether a level actually has size behind it —
and that is what separates a liquidity map from a list of coordinates.

**How it is operated.** `[general knowledge]` Mark PDH/PDL, ONH/ONL, the session extremes, the IB.
Wait for price to trade through one and close back inside within a small number of bars. Enter on
the reclaim; stop just beyond the sweep extreme; target the opposite reference or the mid. The
invalidation is *acceptance* beyond the level. Shape: 50–60% hit rate, 1–2R payoff; degrades sharply
when the swept level is not one others were watching.

**How it dies.** When the level is arbitrary, or when the run is a real break. And relative-liquidity
models die when the crowd learns the level and front-runs it.

**Expressibility here.** **PARTIAL** — EXPRESSIBLE for the level geometry, INEXPRESSIBLE-DATA for the
liquidity claim, and PARTIAL is the label because the two halves are different strategies.
Seven conditions cover the geometry `[repo-verified: futures_agents/strategies/library.py:581-663]`
and `SessionLevels` carries exactly the desk's reference set
`[repo-verified: futures_agents/indicators/structure.py:305-318]`. Two implementation caveats which
are already this repo's own findings and which I do not re-derive: D36 — `session_extreme_sweep` and
`overnight_sweep` are self-referential, the current bar is inside its own reference level
`[repo-verified: workspace/studies/DEFECTS.md:530-540]`; D23 — previous-day levels come from
`is_rth`-flagged bars, so they are unavailable on daily bars
`[repo-verified: workspace/studies/DEFECTS.md:306-315]`. The missing primitive for the *edge* is
**resting quantity by price level (book depth)**. What the repo expresses is "price traded through a
coordinate and came back", which is a price-action pattern; "there was size resting there" is not
observable.

**Already tested here?** **Yes, extensively, and the verdict is negative.** The `LIQUIDITY` group
was screened (MGC LIQUIDITY n=31 e=−0.053; MES 15m LIQUIDITY n=20 e=−0.076 at 5.4R
`[repo-verified: scan_reports/2026-09-23_MGC-MES-NQ_deep-scan.md:99,148]`), and the ORB/ICT programme
found FVG and order-block fill rates reproduced by random zones, three of the five most durable rule
sets containing `ict_placebo_ob`, and the sweep→shift→retrace sequence adding nothing over its parts
`[repo-verified: workspace/studies/ORB_ICT_FINDINGS.md:76-99; workspace/roundtable/BRIEF.md rule 8]`.
One line and stop, per DIVISION §4. **But note what that does and does not settle:** it settles
sweeps-as-geometry on this data. It says nothing about sweeps conditioned on resting size, which was
never observable.

## I-12 Alternative bar sampling: tick, volume, range, dollar, imbalance and run bars

**Mechanism.** Time is the wrong clock. Information arrives in trades, not in seconds, so sampling
every N ticks / N contracts / N dollars / N points of range produces bars whose returns are closer
to i.i.d. and far closer to normally distributed than time bars, which makes every statistic
computed on them better behaved. `[general knowledge; the canonical treatment is López de Prado,
*Advances in Financial Machine Learning*, ch. 2]`

**Who runs it, at what size.** Quant and systematic shops as infrastructure rather than as a
strategy; discretionary footprint traders use volume and range bars as their default chart. It is a
*sampling* choice that sits beneath every other family on this track. `[general knowledge]`

**Where it lives.** Everywhere. Range bars for scalping, volume bars for footprint, dollar bars for
cross-instrument comparability, imbalance/run bars for event-driven sampling. `[general knowledge]`

**Minimum data.** **Time-and-sales** (per-print price, size, timestamp) for tick / volume / dollar /
imbalance / run bars. **Range bars alone can be built from 1-minute OHLCV approximately** — and the
approximation is poor, because the intrabar path is unknown and a range bar boundary is a path
statement.

**How it is operated.** `[general knowledge]` Choose a bar size so that a typical session produces
50–200 bars; recompute every indicator on the new series; nothing else changes. Volume bars make
volume-per-bar constant, which turns "volume surge" into "bars arriving faster" — a cleaner
statement. Imbalance and run bars sample when *cumulative signed* flow crosses a threshold, so they
require an aggressor flag.

**How it dies.** Bar-size choice is a free parameter with no natural value, so it is a
data-mining surface. Volume bars change character across the session and across contract rolls.
Backtest fills on non-time bars are easy to get wrong, because a bar's close is not a moment.

**Expressibility here.** **INEXPRESSIBLE-ARCHITECTURE**, and it is the cleanest architectural
verdict I have. Missing primitive: **a bar-identity that is not an integer minute count.** The
integer-minutes assumption is load-bearing at every layer:
`Bar.minutes: int = 1` `[repo-verified: futures_agents/data/bars.py:43]`;
`BarSeries.__init__(symbol, minutes: int, ...)` `[:164]`;
`resample(series, minutes: int)` `[:302]`, which raises if `minutes < series.minutes` `[:309-311]`;
`align_bucket(ts, minutes: int)` with hard-coded hour / midnight / 18:00-ET alignment rules
`[:138-156]`; `TFSnapshot.timeframe: int` `[repo-verified: futures_agents/features.py:83]`;
`FeatureSnapshot.tfs: Dict[int, TFSnapshot]` `[:693]`; `FeatureHub.frames: Dict[int, TimeframeFrame]`
`[:809]`; `Strategy.primary_tf: int` `[repo-verified: futures_agents/strategies/base.py:505,555]`;
`TIMEFRAME_LABELS` and `TIMEFRAME_GROUPS` keyed on minutes
`[repo-verified: futures_agents/config.py:305-323]`; and `confirm_map: Optional[Dict[int, Tuple[int, ...]]]`
in the combinator `[repo-verified: futures_agents/strategies/combinator.py:472]`. Nothing in the
package mentions any alternative sampling
`[measured: grep -rni "tick_bar\|volume_bar\|range_bar\|dollar_bar" futures_agents/ → no matches]`.
A range-bar series could be *constructed* from 1m data and loaded as a `BarSeries` with a fake
`minutes` value, but then `align_bucket`, `resample`, the timeframe groups and every multi-timeframe
condition would be computing nonsense — so the honest verdict is architecture, not data.

**Already tested here?** No. Every result in the repo is on time bars at one of
{1, 3, 5, 15, 30, 60, 240, 1440} minutes `[repo-verified: futures_agents/config.py:305-307]`.

## I-13 Cumulative-delta divergence; footprint shape (P / b distributions)

**Mechanism.** Two separate reads. (a) CVD divergence: price makes a new extreme, cumulative signed
aggression does not — the move is being carried by passive flow and is likely to fail. (b) Footprint
/ profile *shape*: a "P" distribution (thin below, fat above) is short covering and resolves
downward as often as up; a "b" (fat below, thin above) is long liquidation. Shape tells you what kind
of participant produced the move. `[general knowledge]`

**Who runs it, at what size.** Prop intraday and auction-theory traders. `[general knowledge]`

**Where it lives.** Liquid futures, 1–15m and the session profile. `[general knowledge]`

**Minimum data.** (a) **A per-trade aggressor flag**, cumulated. (b) A **volume-at-price
distribution per session** whose shape is not an artefact of bar sampling.

**How it is operated.** `[general knowledge]` For (a): mark the swing extreme; compare CVD at the new
extreme with CVD at the prior one; require the divergence to resolve with a close back inside;
enter on that close, stop beyond the extreme, target the prior swing. For (b): classify the session's
distribution; a P at the top of a downtrend is a covering rally to sell, not a bottom.

**How it dies.** Divergence is the most over-fitted read in the family — CVD can diverge for many
bars before anything happens, and there is no natural definition of "the divergence failed", so it is
easy to hold a loser while the divergence is "still valid".

**Expressibility here.** **INEXPRESSIBLE-DATA for (a); PARTIAL-but-degraded for (b).**
(a) missing primitive: **a per-trade aggressor flag**. What exists is `delta_divergence`, which
compares a 20-bar price high to a 20-bar **Chaikin A/D** high
`[repo-verified: futures_agents/indicators/volume.py:144-170]` — the arithmetic is a
new-extreme-closing-weak-or-thin detector (R1-D4), and the `estimated` flag that was meant to mark
the substitution is never read `[measured: grep -rn "estimated" futures_agents/ → 13 hits, none
outside volume.py and bars.py]`. (b) shape *is* computable from the existing histogram
(`VolumeProfile.histogram` is a list of `(price, volume)` `[repo-verified: futures_agents/indicators/volume.py:180-188]`)
and no condition reads it — `hvn`/`lvn` are extracted at `:250-252` and shape is not. But the
histogram is smeared and timeframe-dependent (R1-D4), so a P/b classifier built on it would be
classifying a sampling artefact.

**Already tested here?** No. `delta_divergence` is named zero times in reports or findings
`[measured: grep -rc → 0]`.

## I-14 Block and large-print detection; time-and-sales filtering

**Mechanism.** Filter the tape to prints above a size threshold. Large prints are institutional, and
where they cluster marks a level someone with size cared about. `[general knowledge]`

**Who runs it, at what size.** Discretionary intraday traders with a "large trader" tape filter, and
more seriously, desks reconstructing counterparty behaviour. `[general knowledge]`

**Where it lives.** ES, CL, ZN. Tick resolution. `[general knowledge]`

**Minimum data.** **A per-print size** (and, to be useful, its aggressor side). A print-size
threshold is meaningless without prints.

**How it is operated.** `[general knowledge]` Set a threshold at a high percentile of that
contract's print-size distribution; mark levels where large prints cluster; trade with the direction
of the aggressive large prints, using the cluster as the stop reference. Shape: low frequency,
moderate hit rate; used mostly as confirmation rather than as a standalone trigger.

**How it dies.** Order-slicing algos destroy it: a 5,000-lot parent order arrives as 1-lot children
and never prints large. That is the normal state of modern index futures, which is why this family
has decayed. `[general knowledge]`

**Expressibility here.** **INEXPRESSIBLE-DATA.** Missing primitive: **a per-print size — the trade
record itself**. Bar volume is the *sum* of print sizes and no function of a sum recovers its
summands. Note the adjacency: **a per-bar trade count** would give average print size per bar, which
is a legitimate weak version of this family, and that column is not in the CSV either
`[measured: header open_time,open,high,low,close,volume]`. Of the two, the trade count is by far the
cheaper acquisition and it unlocks a weak form of I-14 and the participation-rate half of I-10.

**Already tested here?** No.

## I-15 Opening auction and settlement-window behaviour; MOC-imbalance analogues

**Mechanism.** Two scheduled liquidity events per day. The open concentrates overnight order
imbalance into a few minutes; the close concentrates index-tracking and settlement-referenced flow.
Both are periods where the flow is *known to be non-informational*, which is what makes them
tradeable — you are providing liquidity to someone who must trade. `[general knowledge]`

**Who runs it, at what size.** Bank and broker desks (who see the imbalance), index arbitrageurs,
and systematic desks trading the settlement window. In equities the MOC imbalance is published; in
futures it is not, so futures traders infer it from the cash-market publication.
`[general knowledge]`

**Where it lives.** Index futures around the 09:30 cash open and the 15:45–16:00 close; the
CME settlement windows for each product. `[general knowledge]`

**Minimum data.** For the open: **the opening-auction print and its imbalance**, or at minimum
sub-minute bars across 09:30. For the close: **the published MOC imbalance** (a cash-equity data
feed — this is a second observable and edges toward R2's class; I flag it rather than claim it) and
**the official settlement price**, which is a distinct object from the last traded price.

**How it is operated.** `[general knowledge]` Closing-imbalance trades: read the published imbalance
at 15:45, take the other side into the print, flatten on or just after the close. Opening: fade the
opening extreme when the open is outside prior value and the first minutes fail to extend. Both are
time-boxed — the invalidation is the clock, not a price.

**How it dies.** Crowding (the closing-imbalance trade is heavily traded and its edge has compressed)
and any day where the imbalance is informational rather than mechanical.

**Expressibility here.** **INEXPRESSIBLE-DATA**, with a partially expressible time-window shadow.
Missing primitive: **the official daily settlement price** (and, for the MOC family, the published
closing imbalance, which is not this contract's own data). No settlement column exists — the loader
accepts `settle` only as an *alias for close* `[repo-verified: futures_agents/data/loader.py:38]`,
which means if a vendor ever supplied both, the settlement would silently overwrite the close and
nothing would flag it. Nothing anywhere computes a settlement or an auction print
`[measured: grep -rn "settle\|MOC\|auction" futures_agents/ → the only matches are that loader alias,
the timeutil session descriptions, and unrelated dashboard code]`. What *is* expressible is the
**clock**: the session map has `RTH_CLOSE 15:00–16:00 "Closing imbalance and MOC flow"` and
`RTH_OPEN 09:30–10:30 "Opening drive"` `[repo-verified: futures_agents/timeutil.py:113-122]`, and
`StrategyFilters` exposes time gating. And the repo has already measured that window: **no intraday
entries 15:00–16:00 ET, z = −4.43, median −0.617R, replicated**
`[repo-verified: workspace/roundtable/BRIEF.md rule 5]`. That is the strongest single time-of-day
result in the repo and it is precisely the settlement window — which is a *finding about this
family*, and it points the opposite way to the folk version: on this data the close window is where
entries lose, not where liquidity is free.

**Already tested here?** Partly — the *window* is tested and negative (BRIEF rule 5). The
*imbalance-driven* trade has never been tested and cannot be, without the imbalance.

---

# R1-D2 Operating manual

DIVISION §3: a reader who has never traded either framework must be able to state, for each — what
you look at and in what order, what makes you act, what makes you stand aside, where the stop goes
and why it goes *there*, and what invalidates the read mid-trade. Everything in this section is
`[general knowledge]` unless it carries a path. It is a description of how the frameworks are
operated by people who run them, written so that the expressibility verdicts above can be checked
against something concrete.

## Part A — Market profile / TPO

### A.0 The object

Split the RTH session into 30-minute **brackets**, labelled A, B, C, … Each bracket, mark every price
that traded during it with one letter — one **TPO** (time-price opportunity). Collapse the letters
leftward and you have a horizontal histogram of *time* at each price. Three numbers come out:

- **POC** — the price with the most TPOs: where the auction spent most of its time, i.e. where the
  most agreement was found.
- **Value area (VAH/VAL)** — the contiguous band around the POC containing ~70% of the day's TPOs.
  One standard deviation of the day's own distribution, by construction.
- **Tails / excess** — a run of prices at an extreme that are only **one TPO wide**. One bracket
  traded there and never again: the auction rejected that price outright.

A volume profile is the same picture with volume substituted for time. They usually agree; where
they disagree, the difference is itself information (lots of volume, little time = a fast, heavily
traded rejection).

### A.1 The four opening types, in the order you check them

Checked in the first 10–30 minutes, against two prior-day references: the prior **value area** and
the prior **close**.

1. **Open-Drive.** Price opens and goes, immediately, one direction, without trading back through
   the open. Highest-conviction open there is: one side decided before the bell. The opening print
   tends to be the session extreme. **Action:** join it on the first shallow pullback that holds
   above the open. Stop *below the opening print* — because the definition of an open-drive is that
   the open was the extreme, so a trade back through the open has falsified the label, not merely
   gone against you. That is the general principle in this framework: **the stop goes at the price
   that makes the label false.**
2. **Open-Test-Drive.** Price opens, probes *against* the eventual direction to test a reference
   (prior day's extreme, overnight extreme), fails there, then drives the other way. **Action:**
   enter on the failure of the test. Stop beyond the tested reference. Better risk than the
   open-drive because the stop is defined by the test, not by the open.
3. **Open-Rejection-Reverse.** Price opens, moves one way, then reverses back through the open and
   continues past it. **Action:** enter on the move back through the open; stop beyond the initial
   extreme. Weaker: this is the open type that most often becomes a two-sided day.
4. **Open-Auction.** Price opens inside prior value and goes nowhere. **Action:** stand aside, or
   trade responsively between the prior value-area edges with small size. This is the most common
   open and the one that punishes anyone looking for a trend.

**What makes you stand aside at this stage:** an open inside prior value with no directional
conviction in the first two brackets; or a day where the overnight session already made a wide range
(the day's move may have happened while you were asleep, and the prior-day reference is stale).

### A.2 The day types, and what each one tells you to do

1. **Trend day.** One-timeframe: each bracket's low is above the previous bracket's low (up-trend
   day). Value migrates all session, the close is at or near the extreme, the profile is thin and
   elongated. **Operate:** hold; buy every pullback to the developing VWAP or the previous bracket's
   extreme; do not take profit at targets. Occurs perhaps 10–15% of sessions.
2. **Normal day.** A very wide first bracket (the IB is the day's range or nearly) and then nothing.
   **Operate:** fade the IB extremes; the range is already set.
3. **Normal-variation day.** IB set, then one range extension of roughly half the IB again, then
   balance. The most common day type. **Operate:** trade the range extension in its direction, then
   stop; expect the second half of the session to balance.
4. **Neutral day.** Range extension on *both* sides of the IB. Two-sided, no winner. If it closes
   in the middle ("neutral-centre") it is maximally indecisive; if it closes at one extreme
   ("neutral-extreme") that extreme is the direction with the better odds tomorrow.
   **Operate:** reduce size; this is the day type that destroys breakout traders.
5. **Double-distribution day.** Two separate value areas with a thin band between them — the market
   balanced, broke out, and balanced again elsewhere. **Operate:** the thin band between the two
   distributions is the highest-quality stop location and the best reference for "has the move
   failed". Price returning into the lower distribution invalidates the upper one.

### A.3 The read, in order, live

1. Before the open: mark prior POC / VAH / VAL, prior high/low/close, overnight high/low.
2. 09:30–09:40: classify the **open type** against prior value and prior close.
3. 09:30–10:30: let the **initial balance** form. Note whether the extremes are *excess* (single
   TPOs, a tail) or *poor* (several TPOs flat at the extreme — unfinished business, likely revisited).
4. After 10:30: watch for **range extension** beyond the IB. Extension with the open type is the
   highest-probability continuation in this framework. Extension against it is a warning.
5. Through the session: is value **migrating** (each bracket's value above the last: trend) or
   **rotating** (brackets overlapping around one POC: balance)? This is the single question that
   decides whether you are fading extremes or holding for continuation.
6. 15:00 onwards: where is the close relative to value? A close outside value is the strongest
   single piece of information for tomorrow's open type.

### A.4 Where the stop goes, and why *there*

Not at an ATR multiple. At **the price that makes your structural read false**:

- Long from a value-area low on a balancing day → stop below the VAL, because acceptance below VAL
  means the value area was wrong.
- Long on range extension above the IB → stop back inside the IB, because re-entry into the IB means
  the extension failed.
- Long after an open-drive → stop below the opening print.
- Long from the upper distribution of a double-distribution day → stop in the thin band, not through
  it, because the thin band is the price the market does not want to spend time at, so a stop there
  is either missed or definitively hit.

This is exactly the structural-stop discipline the repo has measured: widening a structural stop to
an ATR stop raises payoff ~89% and drops win rate ~14 points for **no** expectancy gain
`[repo-verified: workspace/roundtable/BRIEF.md rule 3]`, and structural stops should never be
tighter than ~0.5 ATR `[repo-verified: workspace/roundtable/BRIEF.md rule 4]`. Those two rules are
the empirical form of the auction-theory stop convention, and they are settled — I do not re-argue
them.

### A.5 What invalidates the read mid-trade

- **Acceptance** where you expected rejection. Acceptance is *time*, not price: two or more
  30-minute brackets trading beyond the level, or a bracket closing beyond it. One tick through is
  noise; a bracket through is a different auction.
- **Range extension against your day-type label.** If you are holding for a trend day and the market
  extends the other side of the IB, the label is now "neutral" and the trade is now a mistake.
- **Value migrating against you.** The developing POC moving through your entry means the market has
  found agreement on the other side of you.
- **A poor extreme forming at your target.** If your target is an extreme with several TPOs flat
  against it, the market is not finished there and will probably come back; take the trade off.

### A.6 What of this is testable here

Expressible today: open outside prior value (`open_outside_value`), the IB break
(`initial_balance_break`), value-area edge and breakout, POC reversion, LVN location
`[repo-verified: futures_agents/strategies/library.py:650-663, 940-1060]`. Not expressible: the TPO
bracket itself, excess vs poor extremes, value migration across sessions, the composite profile, the
double-distribution classification, and the whole session-long sequence — with the specific missing
primitives listed in R1-D5. Also note that `open_outside_value` is the one condition in the library
that encodes an opening type, and it has **never been named in any report or findings file**
`[measured: grep -rc "open_outside_value" scan_reports/ workspace/studies/*.md workspace/chrono/*.md → 0]`.

## Part B — Footprint / order-flow reading

### B.0 The object

A footprint bar is a *matrix*, not four prices. For each price level the bar traded at, two numbers:
volume filled **at the bid** (a seller crossed the spread) and volume filled **at the offer** (a
buyer crossed). Derived quantities:

- **Delta** per level = ask-volume − bid-volume. **Bar delta** = the sum. **CVD** = the running sum
  across the session.
- **Diagonal imbalance** — the standard footprint object: ask-volume at price P compared to
  bid-volume at price P−1 tick. Ratio ≥ 3:1 is an imbalance. Comparing *diagonally* is the point:
  the buyer at P and the seller at P−1 were competing for the same liquidity.
- **Stacked imbalances** — 3+ consecutive price levels imbalanced the same way. This is the
  footprint's signature of a genuine initiative leg.
- **Point of control of the bar** — the level with the most volume inside that single bar.

**Everything in this list requires the per-price bid/ask split. This repo has the bar's four prices
and its total volume, so none of these objects exists here** — see I-1's verdict.

### B.1 The read, in order

1. **Context first, always.** Footprint is a timing tool, not a direction tool. Before looking at a
   single number you must have a level and a bias from a higher timeframe: a value-area edge, VWAP,
   prior day's extreme, a swing. Footprint traders who reverse this — trade the footprint and then
   look for a reason — are the ones who lose. This is the single most-repeated instruction in the
   discipline.
2. **Is aggression arriving?** Bar volume well above its recent norm, with delta strongly one-sided.
3. **Is the aggression getting paid?** Compare delta to *range*. Large delta with large range =
   initiative, trend continuation. **Large delta with small range = absorption**, and that is the
   reversal setup. This ratio is the whole family.
4. **Where in the bar?** Delta at the *extreme* of the bar matters; delta in the middle does not.
   Aggressive buying at the high of a bar that then closes at its low is trapped buying.
5. **Stacked imbalances?** 3+ consecutive levels one way = a real leg. Note the price at which the
   stack *started* — that becomes your invalidation level.
6. **Does the next bar extend?** Absorption is only a setup. The **entry is the failure to extend**:
   the following bar does not trade beyond the absorbed extreme and closes away from it.

### B.2 What makes you act

A long entry, fully specified: price is at a reference level you marked *before* the bar; a bar
prints volume 2–4× its recent norm with strongly negative delta (heavy aggressive selling); the
bar's range is *at or below* its recent norm (the selling did not achieve anything); the bar closes
in its upper half; and the next bar fails to trade below that bar's low. Enter at the close of the
failure bar or on a limit inside it.

### B.3 What makes you stand aside

- **No level.** No context = no trade, regardless of the footprint.
- **Delta and range both large** at your reversal level: that is initiative against you, not
  absorption. Stand aside and consider the other side.
- **Thin book / thin tape** (the Asian session, holidays, lunch): the footprint's numbers are too
  small to be a distribution.
- **Inside a scheduled release window.** Aggression during a release is mechanical and the read is
  noise. This is the one part of the framework the repo *can* express, via the `news` blackout clock
  `[repo-verified: futures_agents/strategies/library.py:1332-1343]`.
- **After you have already been wrong twice at the same level.** The level is not holding.

### B.4 Where the stop goes, and why *there*

**2–4 ticks beyond the absorbed extreme.** The reason is definitional, not preferential: the thesis
is "passive size defended this price". One tick through it and the passive size was not big enough —
the thesis is falsified and there is nothing left to be right about. The 2–4 tick buffer exists only
because the extreme print may be a single lot.

This is why the family has a *high hit rate and a small payoff*: the stop is placed at the
falsification price, which is very close, so the position is large per unit of risk and the target is
whatever the next liquidity pocket offers. It is the structural mirror of a trend system.

Note the interaction with this repo's own measurement: BRIEF rule 4 says structural stops should
never be tighter than ~0.5 ATR `[repo-verified: workspace/roundtable/BRIEF.md rule 4]`. A 2–4 tick
footprint stop is far tighter than 0.5 ATR on any of these contracts. **These are not in conflict —
they are two different populations.** Rule 4 was measured on strategies whose entries come from bar
signals, where a sub-0.5-ATR stop is inside the noise of the signal. A footprint stop is tight
because the *entry* is precise to a tick, which a bar-derived entry never is. The correct reading is:
**you cannot import the footprint stop convention into a bar-signal strategy**, and this repo can
only build bar-signal strategies.

### B.5 What invalidates the read mid-trade

- **Trade beyond the absorbed extreme with delta continuing in the same direction.** Absorption
  failed; the aggressor was the bigger side after all. Exit, do not wait for the stop.
- **Your own side's aggression arrives and achieves nothing.** You are long after absorption of
  selling; now buyers are paying up and price is not advancing. You are now the trapped side.
- **CVD makes a new extreme against you while price does not.** Aggression is accumulating on the
  other side.
- **Time.** Absorption trades resolve quickly. A footprint trade that has not worked within a handful
  of bars has failed even if it has not been stopped — the discipline is to scratch it. Time-based
  invalidation is an operating rule (R3's `ExitModel` territory, DIVISION §5.2/§5.6 — I name it and do
  not adjudicate it).

### B.6 What of this is testable here

**Essentially none of it, and the reason is one column.** The context half (levels, VWAP, value area)
is expressible; the confirmation half — every number in B.0 — needs a per-trade aggressor flag.
The repo's substitute is `delta = ((C−L)−(H−C))/(H−L) × V`
`[repo-verified: futures_agents/data/bars.py:106-113]`, which returns **0.0 when range is 0**
`[:110-111]` — i.e. exactly zero in step B.1.3's defining case. And the three-step sequence
(aggression → absorption → failure to extend) is blocked by D37 independently of the data
`[repo-verified: workspace/studies/DEFECTS.md:541-548]`.

**So footprint reading is doubly blocked here: the data cannot see the aggressor, and the combinator
cannot express the sequence.** Fixing either one alone does not make the family testable. That is the
single most useful sentence I can give a round-2 build-priority decision.

---

# R1-D5 The named-blindness list

Every INEXPRESSIBLE or partially-blocked verdict in R1-D1, with **one** specific missing primitive
and an estimate of what supplying it would take. Per DIVISION §4 and the manager's cover note: this
is a build-and-acquire order, not a complaint. Nine distinct primitives account for all fifteen
families.

| # | missing primitive | exactly what it is | families it blocks | cost to supply |
|---|---|---|---|---|
| **P1** | **Per-trade aggressor flag** | for each execution, whether it filled at the bid or the offer | I-1, I-2, I-6(part), I-13(a) — and it is what would make `orderflow`'s 3 conditions mean their names | **Data purchase.** Databento MBP-1/MBP-10 or CME MDP3 historical; the `Bar` fields already exist (`bid_volume`/`ask_volume`, `bars.py:44-45`) and the loader already aliases eight vendor spellings of each (`loader.py:40-43`), so **bar-level ingestion is zero code**. Aggregation from ticks to bar-level bid/ask volume is ~30 lines. |
| **P2** | **Per-price footprint matrix per bar** | volume at bid and at offer, *per price level*, per bar | I-1 (stacked imbalances), I-13(b) | **New data structure.** `Bar` is a flat frozen dataclass with no per-price container (`bars.py:28-47`). Needs a `footprint: Dict[float, Tuple[float,float]]` field, resampling support for it, and a feature-layer exposure. Days of work, and it changes a frozen dataclass every layer depends on. |
| **P3** | **Resting-order-book depth (top-N quantity per side, timestamped)** | the book, not the tape | I-3, I-4, I-5, I-11 (the liquidity half) | **Data purchase + new engine.** No depth field anywhere (`[measured: grep for depth/order_book/best_bid/best_ask in futures_agents/ → only unrelated "drawdown depth" and recursion-depth hits]`). Also needs a queue-aware fill model, which is a different backtester. |
| **P4** | **Time-and-sales: per-print (timestamp, price, size)** | the tape itself | I-6, I-12, I-14 | **Data purchase**, large. The finest object in the repo is a 1-minute bar (`csv/raw/*_1m.csv`); a 1m bar summarises hundreds to thousands of prints into four numbers and is not invertible. |
| **P5** | **Exchange volume-at-price per session** | traded volume at each price level, per session — **no aggressor split needed** | I-7, I-8, I-9, I-13(b) | **The cheapest genuinely new data on this track.** Vendors publish it as a standalone product and it is a fraction of the size of tick data. `VolumeProfile` already has the right shape (`volume.py:174-201`); the change is to populate `histogram` from measured volume-at-price instead of the uniform-smear reconstruction at `volume.py:225-232`. ~50 lines plus an ingestion path. |
| **P6** | **Per-bar trade count (number of executions)** | one extra integer column beside `volume` | I-10 (the institutional-benchmark half), I-14 (a weak form) | **Smallest acquisition on the whole ledger.** One column. Yahoo does not supply it; Databento/CME do, and many broker exports do. Gives average print size per bar = the standard cheap proxy for participant mix. Needs a new `Bar` field and a loader alias — the alias pattern already exists at `loader.py:40-44`. |
| **P7** | **Time-at-price per bracket (TPO counts)** | how many 30-minute brackets traded at each price | I-7, I-8 (excess vs poor extremes) | **No new data. Pure code.** Computable from existing 1m/5m bars. Nothing in the package mentions it: `[measured: grep -rni "tpo\|time_at_price\|bracket" futures_agents/ → zero matches]`. A `tpo_profile(bars, bracket_minutes=30)` beside `volume_profile` plus two conditions. **This is the highest value-per-line item I found.** |
| **P8** | **A multi-session / composite profile, and POC persistence** | ≥2 prior sessions' profiles simultaneously; an untouched POC retained until traded through | I-7, I-8 (value migration), I-9 (composite, naked POC) | **No new data. Small code.** `prior_session_profile` takes exactly `self._day_order[position - 1]` (`features.py:615-622`) and already holds `_day_order` and `_day_bars`; a composite is a loop-bound and a cache-key change. ~40 lines plus conditions. |
| **P9** | **A sequence primitive (ordered conditions across bars) — D37** | "A on bar i, then B within k bars" | the *operating form* of I-1, I-2, I-7, I-8, I-11 | **Architecture.** `min_signals=2` requires two conditions on the **same bar** (`[repo-verified: workspace/studies/DEFECTS.md:541-548]`). R3 owns the combinator's exit catalogue and R3-D6 is scoped to this; I state the dependency from my side and do not cost it. |
| **P10** | **Official daily settlement price** | distinct from the last traded price | I-15 | **One column, and a latent hazard.** `settle` is currently only an *alias for close* (`loader.py:38`), so a vendor supplying both would silently overwrite the close with the settlement and nothing would flag it. |
| **P11** | **A non-minute bar identity** | a bar whose size is N ticks / N contracts / N dollars / N points, not N minutes | I-12 | **Architecture, deep.** Integer minutes are load-bearing in `Bar.minutes` (`bars.py:43`), `BarSeries.__init__` (`:164`), `resample` (`:302-311`), `align_bucket` (`:138-156`), `TFSnapshot.timeframe` (`features.py:83`), `FeatureSnapshot.tfs: Dict[int,...]` (`:693`), `FeatureHub.frames: Dict[int,...]` (`:809`), `Strategy.primary_tf` (`base.py:505,555`), `TIMEFRAME_LABELS`/`TIMEFRAME_GROUPS` (`config.py:305-323`) and `confirm_map` (`combinator.py:472`). |

**Ranked by families unlocked per unit of cost** — the ordering I would hand a round-2 build decision:

1. **P7 (TPO counts)** — 2 families, zero data cost, pure code. Nothing in the repo computes time at price.
2. **P8 (composite profile + POC persistence)** — 3 families, zero data cost, small code.
3. **P6 (per-bar trade count)** — 1.5 families, one column.
4. **P5 (volume-at-price)** — 4 families, and it repairs the six `profile` conditions from DEGRADED to honest.
5. **P1 (aggressor flag)** — 4 families, and it converts the three `orderflow` conditions from proxies into the thing they are named after. Ingestion is already written.
6. **P9 (sequence)** — blocks the *operating form* of 5 families; needed *in addition to* P1/P2 for footprint, not instead of.
7. **P2, P3, P4, P10, P11** — expensive, and each unlocks fewer families than the five above.

**The one sentence.** Five of the nine primitives that block Class I here (**P5, P6, P7, P8, P10**)
are *not* tick data. Two of them (**P7, P8**) need no new data at all. The repo's Class I blindness
is not one wall labelled "we have no order flow"; it is a short ladder, and the bottom two rungs are
code it can write this week.

---

# R1-D6 Falsifiability audit of the day-type and opening-type taxonomies

The precedent is this repo's own. `workspace/studies/DEFECTS.md:481-483` lists concepts "not
falsifiable as stated — do not build on these", and the head of the list is **"Power of Three —
labels every day post-hoc and refutes none"**; the report states the same and adds that three other
ICT concepts were excluded on the same ground `[repo-verified: scan_reports/2026-09-24_ORB-and-ICT.md:42-45]`.
The test applied there has two parts: **(a) is the label assignable before the outcome it predicts?**
and **(b) does the taxonomy have a residual — is there any observation it excludes?**

## The four opening types — **they survive**

| label | knowable when? | verdict |
|---|---|---|
| Open-Drive | within a pre-committed window (first bracket): did price trade back through the open? | **FORWARD-ASSIGNABLE** |
| Open-Test-Drive | same window: was a named prior reference probed and rejected? | **FORWARD-ASSIGNABLE** |
| Open-Rejection-Reverse | same window: did price cross back through the open and continue? | **FORWARD-ASSIGNABLE** |
| Open-Auction | same window: did price stay inside prior value? | **FORWARD-ASSIGNABLE** |

All four reduce to comparisons of the open, the prior value area and the first bracket's path — all
knowable at the end of the classification window, and the window is pre-committable. **Condition (a)
passes, provided the window is fixed in advance.** That proviso is doing real work: as taught, the
window is usually left implicit ("the open drove all day"), and *that* version is post-hoc. So the
honest statement is: **the opening-type taxonomy is falsifiable once you fix the classification
window, and unfalsifiable if you do not.** The fix is a parameter, not a new concept.

Condition (b) — the four labels are exhaustive, with no residual. That is the same structural
property Power of Three has. **But it does not have the same consequence**, and this is the
distinction the ORB/ICT disposition did not need to make: Power of Three's label ("accumulation →
manipulation → distribution") makes *no differential forward prediction* — every day fits and every
day is consistent with it. Each opening type makes a *different* forward prediction (open-drive: the
open is the session extreme; open-auction: the day is range-bound), so the labels are mutually
falsifiable against each other even though the set is exhaustive. **Exhaustive is not the same as
vacuous.**

Repo evidence that the forward-assignable residue is not empty: `open_outside_value` is exactly a
fixed-window opening-type test — "Session opened outside the prior value area (open-drive day type)"
`[repo-verified: futures_agents/strategies/library.py:1046-1060]` — and `initial_balance_break` is
the range-extension trigger, gated on `minutes_since_open >= 60`
`[repo-verified: futures_agents/strategies/library.py:650-656]`. Both are computable at the moment
they fire. Neither has ever been reported: `open_outside_value` appears **0** times and
`initial_balance_break` **3** times in the whole reports-and-findings corpus
`[measured: grep -rc across scan_reports/ workspace/studies/*.md workspace/chrono/*.md]`.

## The five day types — **three dissolve, two survive**

| label | earliest assignable | verdict |
|---|---|---|
| Trend day | the close (needs value migrating *all* session and a close at the extreme) | **POST-HOC** |
| Normal day | the close (needs "the IB was the day's range", i.e. that nothing further happened) | **POST-HOC** |
| Normal-variation day | the close (needs "the extension stopped there") | **POST-HOC** |
| Neutral day | mid-session, the moment the second-side extension occurs | **FORWARD-ASSIGNABLE** |
| Double-distribution day | mid-session, once the second distribution has formed | **FORWARD-ASSIGNABLE (late)** |

**So the manager's §6 prediction is half right and I am flagging the half that is wrong, loudly.**
The prediction was: "I expect one family to dissolve on inspection: the day-type **and
opening-type** taxonomy, reducing to post-hoc labelling of the same shape as Power of Three." The
day-type taxonomy does behave that way for three of its five labels. **The opening-type taxonomy
does not dissolve** — all four labels are assignable inside a pre-committable window, and the repo
already contains one of them as a working condition. Treating the two taxonomies as one object was
the error; they have different epistemic status.

**And the day types have a forward-computable residue that is not vacuous.** Substituting a
mechanical, forward-computable operationalisation — IB = 09:30–10:30 RTH, extension = any trade
beyond the IB after 10:30, "trend" = one-sided extension ≥ 1.0 × IB — gives this distribution:

```
[measured: python3 -c "load_csv(csv/raw/{MGC,MES,MNQ,MCL}_15m.csv, 15m); RTH sessions with a
full 4-bar IB; classify by extension side(s) and magnitude" → n = 41 sessions per symbol]

MGC  normal-variation 36.6% | trend 36.6% | neutral 17.1% | normal  9.8%
MES  normal-variation 51.2% | neutral 29.3% | trend 14.6% | normal  4.9%
MNQ  normal-variation 58.5% | neutral 17.1% | normal 12.2% | trend 12.2%
MCL  trend 43.9%            | neutral 34.1% | normal-variation 19.5% | normal 2.4%
```

Three things follow, and I am careful about each.

1. **The taxonomy discriminates.** No label absorbs more than 58.5% on any symbol, and all four
   labels are populated on all four symbols. That is the opposite of Power of Three, where the label
   covers 100% by construction. A partition with this much dispersion can be conditioned on.
2. **The distribution is a per-symbol fact and does not transfer.** MCL's modal day is **trend**
   (43.9%) with only 19.5% normal-variation; MNQ's modal day is **normal-variation** (58.5%) with
   only 12.2% trend. Per the independence rule those are four separate results, and anyone importing
   a day-type prior from an index contract to crude would have it backwards.
3. **Three caveats I will not bury.** (i) **n = 41 RTH sessions per symbol** — the 15m files carry
   ~58 days total `[repo-verified: scan_reports/2026-09-23_MGC-MES-NQ_deep-scan.md:242 "30m and 15m
   have 58 days total"]`. This is a descriptive frequency on a small sample, not an estimate.
   (ii) The four-way split is **my** mechanical operationalisation, not Dalton's definition; a real
   trend day is a *one-timeframe* statement (each bracket's low above the last), which my
   extension-magnitude proxy only approximates. The proxy is the falsifiable residue; the taxonomy
   itself is not what I measured. (iii) This is a frequency count. **It contains no expectancy, no
   z-score and no comparison** — DIVISION §8 forbids those in round 1 and none is offered.

## What this means for building

The day-type *labels* are not buildable as stated and should not be. The **conditionals derived from
them** are: "IB extended by ≥ X and value migrating → hold rather than fade" is a statement about
observables available at the moment you act. That is what `initial_balance_break` already is. So the
correct disposition is **not** "market profile is unfalsifiable" — it is "the labels are post-hoc,
the triggers are not, and the triggers are the part that was already in the library and never
reported."

---

# R1-X Anti-overfitting and validity audit for this track

Round 1 produced no performance numbers, so there is no expectancy to over-fit. What there *is* to
check is whether the **conditions and features on my track** carry validity defects that would
corrupt any future measurement. I state what I checked and what I found, including the checks that
came back clean.

| risk | checked? | finding on this track |
|---|---|---|
| **Look-ahead / future-data leakage** | Yes | **Mostly clean, and unusually careful.** `delta_divergence` uses a strictly trailing window `[repo-verified: futures_agents/indicators/volume.py:158-168]`. `prior_session_profile` uses only completed prior sessions with the reason stated `[repo-verified: futures_agents/features.py:600-607]`. `opening_range_breakout`/`_fade` require `orr.complete` with the reason inline `[repo-verified: futures_agents/strategies/library.py:623-626]`. `initial_balance_break` waits 60 minutes `[:655-656]`. `AnchorVWAP` carries a `knowable_index` guard `[repo-verified: futures_agents/indicators/volume.py:320-331]`. `Bar` carries a `complete` flag with a module-level invariant `[repo-verified: futures_agents/data/bars.py:1-14]`. The ORB/ICT programme also ran a *positive* control for leakage — peeking 2 bars early lifts win rate to 67–70%, z +4.2 to +7.0 — so the harness demonstrably can detect leakage `[repo-verified: workspace/studies/ORB_ICT_FINDINGS.md:88-91]`. |
| **Self-reference (a bar inside its own reference level)** | Yes | **One real instance, already known.** D36: `session_extreme_sweep` and `overnight_sweep` build their reference from bars including the bar under test, making the sweep arithmetically impossible `[repo-verified: workspace/studies/DEFECTS.md:530-540]`. PDH/PDL reproduces exactly, so `prior_day_sweep` and `prior_day_breakout` are clean. |
| **Repainting indicators** | Yes | Clean on my surface. The ORB/ICT audit rebuilt every bar-state from series truncated at 35/60/85% and found **0 mismatches over ~50,000 bar-states** `[repo-verified: workspace/studies/ORB_ICT_FINDINGS.md:92-93]`. Note `fair_value_gaps(bars, as_of=n-1, ...)` is called with the last index `[repo-verified: futures_agents/features.py:295]`, but FVG is in the `structure` group, not mine — flagged, not adjudicated. |
| **Mislabelled / proxied features** | Yes | **The central finding.** 6 of 27 conditions are OHLCV proxies wearing a participant-information name; 6 more are degraded; 2 are structurally dead; 3 are a clock named `news` (R1-D4). And the flag built to mark exactly this — `delta_is_estimated` / `VolumeProfile.estimated` — is **never read** `[measured: grep -rn "estimated" futures_agents/ → 13 hits, all inside volume.py and bars.py]`. |
| **Parameter sensitivity** | Partly | Not measurable without sweeps. But I can name the surfaces: `volume_profile(bins=60)` default vs `bins=40` as actually called `[repo-verified: futures_agents/indicators/volume.py:203 vs futures_agents/features.py:622]`; `value_area_pct=0.70`; HVN/LVN thresholds `1.5×` and `0.4×` of mean bin volume `[:250-252]`; the four ATR fractions in the profile conditions (0.25/0.3/0.35/0.5); `detect_imbalances(threshold=2.0)` with the volume leg at `threshold*0.6` `[repo-verified: futures_agents/indicators/structure.py:442,460]`; `cvd_directional`'s `0.25 × volume` gate; `relative_volume_high`'s `1.10`. **Eleven free parameters across 27 conditions, none of which any completed study has varied on my surface.** |
| **Threshold calibrated on the wrong data** | Yes | **Found one, self-declared.** `relative_volume_high`'s own docstring: calibrated against the synthetic generator's distribution, and "Real futures volume has a much fatter right tail than the generator's, so this threshold is one to re-check on real bars rather than inherit" `[repo-verified: futures_agents/strategies/library.py:405-411]`. Never re-checked as far as I can find. |
| **Insufficient sample size** | Yes | My own R1-D4 invariance test is n=4 days/symbol and my R1-D6 frequency count is n=41 sessions/symbol; both are labelled as such in place. On the repo's side the relevant fact is already settled — programme-wide `free_t = 5.46`, largest t anywhere 3.923 `[repo-verified: workspace/roundtable/BRIEF.md]` — and D6 records that the 20-trade floor selects on stop width `[repo-verified: workspace/studies/DEFECTS.md:63-69]`. |
| **Data-mining bias / selection** | Yes, by not doing it | I ranked nothing and selected nothing. The repo has already measured that selecting last period's top 10 underperforms trading the whole qualifying universe `[repo-verified: workspace/roundtable/BRIEF.md]`. |
| **Structurally-null candidates inflating the search size** | Yes — **new** | 6.7% of a 284-strategy MGC sample carries an `openinterest` condition that cannot fire on this data `[measured, R1-D4a]`, and MNQ's default group set reaches them while MGC's does not. Whether these entered the ~2.97M denominator is logged as Q2 in `OPEN_QUESTIONS.md`. |
| **Unrealistic fills / understated costs and slippage** | Named, not audited | `ContractSpec` carries `commission_per_side`, `exchange_fee_per_side` and `typical_slippage_ticks` `[repo-verified: futures_agents/config.py:38-40]`. The cost model and the fill model are R3's surface (DIVISION §2) and I do not audit them. One Class-I-specific note: **every family on my track trades at 2–10 tick targets, where round-trip friction is a third or more of gross edge** `[general knowledge]`, so cost realism binds harder here than on any other track. D35 (a one-sided fill bug) and D13 (scale-out legs charged neither commission nor slippage) are relevant and are R3's `[repo-verified: workspace/studies/DEFECTS.md:515,169]`. |
| **Survivorship bias** | Yes | Not a live risk on my track — single-contract continuous series, no universe selection. The adjacent hazard is **contract splicing**: D40 records that the micro-grain CSVs splice more than one contract month `[repo-verified: workspace/studies/DEFECTS.md:583]` and they are excluded. Note for I-9/I-15: a spliced series corrupts *any* price-level reference (POC, PDH, settlement) across the splice, which matters more for level-based Class I families than for indicator-based ones. |
| **Vendor / series identity** | Yes | `MNQ=F` is not TradingView's `MNQ1!`; NQ and MNQ are not the same series (D41); MCL has no daily history and full-size `CL=F` is not a substitute `[repo-verified: workspace/roundtable/BRIEF.md; workspace/studies/DEFECTS.md:602]`. I cited no cross-vendor comparison. |

---

# Answers to the manager's three questions

## Q1 — Is our null result a property of the market, or of our information set?

**On my class: overwhelmingly of the information set, and I can put a number on it.**

Of fifteen Class I families, **eleven require information this repo has never had** — a per-trade
aggressor flag (I-1, I-2, I-13a), a footprint matrix (I-1, I-13b), book depth (I-3, I-4, I-5, and the
liquidity half of I-11), time-and-sales (I-6, I-12, I-14), exchange volume-at-price (I-7, I-8, I-9 in
their measured rather than reconstructed form), or a settlement print (I-15). Verdict split:

Strict single-label tally, DIVISION §4's vocabulary, one label per family:

| verdict | n | families |
|---|---|---|
| **EXPRESSIBLE** | **0** | none |
| **PARTIAL** | **5** | I-7, I-8, I-9, I-10, I-11 |
| **INEXPRESSIBLE-DATA** | **9** | I-1, I-2, I-3, I-4, I-5, I-6, I-13, I-14, I-15 |
| **INEXPRESSIBLE-ARCHITECTURE** | **1** | I-12 |

Two boundary notes, so the tally can be checked rather than taken. **I-8** is the one I could
defensibly have put in either column: its *location* half is expressible and its defining primitives
(time-at-price per bracket, multi-session profiles) are absent — if it is moved to architecture the
split becomes 0 / 4 / 9 / 2. **I-11** is the only family with a fully expressible half: the level
geometry is complete and correct, and the liquidity claim that gives the family its name is not
observable at all. I record it as PARTIAL rather than EXPRESSIBLE because "price traded through a
coordinate and came back" is a different strategy from "a level with resting size behind it was run".

**This contradicts the manager's §6 pre-registration in two places.** He predicted "≥10 of the 15
Class I families land on INEXPRESSIBLE-DATA" — I get **9**, one short, with a tenth (I-12) landing on
architecture instead. And he predicted "the EXPRESSIBLE set is ≤3 and consists of things already
measured and already null" — under a strict one-label reading it is **0**, i.e. *below* the floor of
his expectation rather than inside it. I-12 is the family that moved: the data to build range bars
partially exists and the **architecture** forbids it, because a timeframe's identity in this repo *is*
an integer minute count at nine separate layers (R1-D1 I-12).

**But the sharper answer to Q1 is not the count. It is this:** for three of nineteen condition
groups, the null result is not evidence about the family the group is named after. `orderflow` was
screened in ~2.97M evaluations and what was screened was **Chaikin's Accumulation/Distribution
line**, a bar-midpoint comparison, and an A/D divergence. `openinterest` was not screened at all —
its two conditions cannot fire. `news` was screened as a clock. **Half a generated strategy set
carries one of these proxies** (50.7% of a 284-strategy sample, and 100% of the REVERSAL group,
whose template *requires* `orderflow` `[measured, R1-D4a]`).

So the repo's settled negative verdict stands as stated — nothing here is live-eligible — and it does
**not** license the sentence "order flow does not work". The honest form is **untested here**, and the
reason is a missing column.

## Q2 — Any family expressible with today's combinator, widely operated, and never tested here?

**Strictly as asked — expressible with *today's* combinator, meaning no new condition function —
the answer on my track is essentially empty, and I want to be exact about why.** Every one of the 79
conditions is already reachable `[repo-verified: DIVISION.md Appendix B fact 6:
unreachable_conditions() → []]`, and the four existing scans screened all thirteen templates. So
"expressible today and never tested" can only mean **a condition that exists and was screened but was
never varied or reported at the condition level** — which is a reporting gap, not a new hypothesis.
20 of the 32 conditions I looked at are named **zero** times in the whole reports-and-findings corpus
`[measured: grep -rc across scan_reports/ and workspace/studies/*.md and workspace/chrono/*.md]`,
including all six `profile` conditions except `value_area_breakout`, all five `vwap` conditions except
`above_vwap`, and all three `imbalance` conditions.

**Relaxing "today's combinator" by one notch — one new condition function, no new data — gives a
real, ranked list.** I report it as the answer to the spirit of Q2 while flagging that it fails the
letter:

| rank | hypothesis | why it is not already covered | cost |
|---|---|---|---|
| 1 | **High volume, LOW range** (the absorption shape) | `detect_imbalances` requires `r_mult >= 2.0` **and** `v_mult >= 1.2` — high volume **and** high range `[repo-verified: futures_agents/indicators/structure.py:452-462]`. The inverse — volume ≥2× norm with range ≤ norm — is the defining shape of I-2 and **no condition in the library computes it**. Both inputs are in the CSV. | ~15 lines, one condition, zero new data. **The single cheapest untested Class I hypothesis I found.** |
| 2 | **Anchored VWAP** | `AnchorVWAP`, `build_anchor_vwap`, `major_move_anchors`, `swing_anchors` are all implemented, look-ahead-guarded and unit-tested, and **nothing consumes them** `[measured: grep → hits only in indicators/volume.py + __init__ re-exports; 0 in strategies/library.py]`. The docstring's claim that "the feature layer never exposes an anchor that is not yet knowable" `[repo-verified: futures_agents/indicators/volume.py:330-331]` is vacuously true — the feature layer exposes none. | ~20 lines: a feature-layer field plus one or two conditions. |
| 3 | **RTH-anchored and week-anchored VWAP** | `vwap_bands` accepts `rth_only` and an anchor `[repo-verified: futures_agents/indicators/volume.py:72-74]`; `features.py:248` calls it with `"session"` and no `rth_only`, so only the Globex VWAP is reachable. The RTH VWAP is the one tied to cash-equity execution. | ~10 lines: extra feature columns + condition variants. |
| 4 | **TPO / time-at-price counts (P7)** | Zero occurrences of TPO, time-at-price or bracket anywhere `[measured: grep → 0]`. Unlocks excess-vs-poor-extreme, which is the invalidation primitive of I-8. | ~60 lines, zero new data. |
| 5 | **Composite / multi-session profile and naked POC (P8)** | `prior_session_profile` reads exactly `position - 1` `[repo-verified: futures_agents/features.py:615-622]`. | ~40 lines, zero new data. |

**Two honesty notes on this list.** (i) Items 2 and 3 are *implemented-but-unwired*, which is a
stronger claim than "never tested" and a weaker one than "expressible today" — they need a wire, not
a build. (ii) **None of these five is a prediction that anything will work.** Given that placebo
entries rank alongside real signals and nothing has ever cleared `free_t`
`[repo-verified: workspace/roundtable/BRIEF.md]`, the prior on all five is "null". They are worth
listing because they are *cheap and never asked*, not because they are promising.

## Q3 — Which single missing primitive unlocks the most families in your class?

**A per-trade aggressor flag — P1 in R1-D5 — and the count is 4 of 15** (I-1 order flow/footprint,
I-2 absorption, I-13 CVD divergence, and the confirmation half of I-6 tape scalping). It also
converts the three `orderflow` conditions from proxies into the measure they are named after, which
is what makes it the answer rather than merely a large number: **it is the only primitive on my list
that repairs conditions the repo has already screened 2.97M times.**

**Three qualifications that a build decision needs, and the third is the one that matters:**

1. **Cheapest ingestion of any primitive on my ledger.** `Bar.bid_volume` / `Bar.ask_volume` already
   exist `[repo-verified: futures_agents/data/bars.py:44-45]`, `delta` already switches to the true
   split when both are present `[:95-104]`, and the loader already aliases eight vendor spellings of
   each `[repo-verified: futures_agents/data/loader.py:40-43]`. **Bar-level ingestion is zero lines
   of new code.** No other primitive on my track has its consumer already written.
2. **It is not the most families per unit cost.** **P5, exchange volume-at-price, unlocks 4 as well**
   (I-7, I-8, I-9, I-13b) and is a smaller, cheaper dataset than tick-level aggressor data. And two
   primitives unlock families for **zero data cost**: P7 (TPO counts, 2 families) and P8 (composite
   profile, 3 families) are pure code. If the manager's reconciliation is "what should we build
   first", the answer is **P7 then P8** — not P1. If it is "what single acquisition changes the most
   about what we have already measured", the answer is **P1**.
3. **P1 alone does not make I-1 or I-2 *operable*.** Footprint reading needs the per-price matrix
   (P2) for stacked imbalances, and every operating form in Class I is a **sequence**, which D37
   blocks independently of any data `[repo-verified: workspace/studies/DEFECTS.md:541-548]`. So for my
   class the build order is conjunctive, not a single choice: **P1 (see the aggressor) AND P9
   (express "A then B")**. Buying P1 without P9 buys a better `delta` column and still cannot express
   "absorption, then failure to extend".

**The one-line answer for reconciliation across tracks:** *a per-trade aggressor flag unlocks 4 of
15 Class I families and repairs 3 already-screened conditions; a sequence primitive is required in
addition for the operating form of 5; and the two cheapest unlocks on my track (TPO counts, composite
profile) need no new data at all.*

---

# R1-Z Against the manager's §6 pre-registration for R1 — consolidated

The manager asked to be told loudly where he was refuted. Four predictions, four dispositions.

**1. "Hardest: separating *our order flow is a proxy* from *order flow does not work*. I expect R1 to
establish the first from `volume.py:1-9` and then be tempted into asserting the second's negation.
Do not. The honest form is 'untested here'." → CONFIRMED, and I took the instruction.** Established
the first from exactly that docstring plus `bars.py:106-113`, and everywhere the second could be
asserted I have written **untested here** (I-1, I-2, I-13, and §7 Q1's closing paragraph). I also
found a stronger version of the first than the docstring supports: the `estimated` flag the docstring
promises is **never read by any consumer** `[measured: grep -rn "estimated" futures_agents/ → 13 hits,
all inside indicators/volume.py and data/bars.py]`, so the "the system says so" clause is true of the
dataclass and false of the pipeline.

**2. "I predict ≥10 of the 15 Class I families land on INEXPRESSIBLE-DATA, and the EXPRESSIBLE set is
≤3 and consists of things already measured and already null." → REFUTED in both halves.**
INEXPRESSIBLE-DATA is **9**, one short of the prediction; the tenth (I-12) lands on
INEXPRESSIBLE-ARCHITECTURE because a timeframe's identity here *is* an integer minute count at nine
layers. And the strict EXPRESSIBLE set is **0**, not ≤3 — *below* the floor of the expectation. The
five PARTIALs (I-7, I-8, I-9, I-10, I-11) are where the content is, and the manager's parenthetical
list — "session-level sweeps, profile location, VWAP location" — names exactly those three, so his
*identification* was right and his *label* was too generous: none of them is expressible in the
sense of "the desk's object is available", because in each case the object is reconstructed from bar
geometry.

**3. "I expect a specific surprise: that market profile / TPO turns out to be the best-documented
operating framework in the whole roundtable and simultaneously among the least testable here."
→ CONFIRMED on documentation, and REFINED on testability.** It is the best-documented framework on my
track by a wide margin (R1-D2 Part A is the longest operating description I wrote, and it is the one
with an actual published lineage rather than vendor blogs — contrast the repo's own note that "every
ICT source retrieved is a broker blog, indicator vendor or teaching site, none peer-reviewed"
`[repo-verified: workspace/studies/DEFECTS.md:491-494]`). But **"least testable" is wrong in an
important direction**: market profile is the family whose blindness is *cheapest to remove*. Two of
its three missing primitives need **no new data at all** — TPO/time-at-price counts (P7) and a
composite profile with POC persistence (P8) are pure code, and nothing in the package computes either
`[measured: grep -rni "tpo\|time_at_price\|bracket" futures_agents/ → no matches; repo-verified:
futures_agents/features.py:615-622 reads exactly position-1]`. Footprint (I-1) is the least testable
family on my track, not profile.

**4. "I expect one family to dissolve on inspection: the day-type and opening-type taxonomy, reducing
to post-hoc labelling of the same shape as Power of Three." → HALF REFUTED, and the half matters.**
The **day types** do behave that way for three of five labels (trend, normal, normal-variation are
close-only; neutral and double-distribution are assignable mid-session). The **opening types do
not** — all four are assignable inside a pre-committable window, and the library already contains one
of them as a working, forward-computable condition (`open_outside_value`
`[repo-verified: futures_agents/strategies/library.py:1046-1060]`) that **no report has ever named**
`[measured: grep -rc → 0]`. Treating the two taxonomies as one object was the error; they have
different epistemic status. Full argument in R1-D6, including a descriptive four-way day-type
frequency count (n=41 sessions/symbol) showing the partition is **not** vacuous — no label absorbs
more than 58.5% on any symbol, and the modal day type differs between MCL (trend, 43.9%) and MNQ
(normal-variation, 58.5%), which is a per-symbol fact that does not transfer.

**And against the manager's roundtable-wide risk** — "that all three tracks return 'inexpressible' and
the catalogue becomes a restatement of *we only have OHLCV on one contract*" — the defence from my
side is R1-D5: **eleven named primitives, of which two (P7, P8) need no new data, one (P6) is a single
integer column, one (P1) already has its consumer written, and only four are genuinely expensive.**
Class I blindness here is a short ladder, not one wall.

---

# Manifest

| deliverable | where |
|---|---|
| HEADLINE — the three phantom condition groups | `## HEADLINE` above |
| R1-D1 Class I family catalogue, I-1…I-15 | `# R1-D1` |
| R1-D2 Operating manual (market profile/TPO; footprint) | `# R1-D2` |
| R1-D3 Data-requirement ledger | `workspace/roundtable/research/R1_data_requirements.md` |
| R1-D4 Proxy audit, all 27 conditions + addendum | `## R1-D4a`, `## R1-D4`, `## R1-D4 addendum` |
| R1-D5 Named-blindness list (P1…P11) | `# R1-D5` |
| R1-D6 Falsifiability audit of day/opening types | `# R1-D6` |
| Anti-overfitting and validity audit | `# R1-X` |
| Answers to the manager's three questions | `# Answers to the manager's three questions` |
| Contradictions of §6 | `# R1-Z` |
| Questions raised for others | `workspace/roundtable/OPEN_QUESTIONS.md` Q1 (new-defect candidate), Q2 (zero-trade denominator), Q3 (HIGH-impact filter, to R2) |

**Run budget compliance (DIVISION §8).** Everything I ran was a read, a `grep`, a short `python3 -c`
inspection, one `generate_strategies` call at `max_total=390`, or a descriptive frequency count on raw
bars. I ran no `run_portfolio`, no `run_backtest`, no sweep. **No expectancy and no z-score appears
anywhere in my output except where quoted from an existing committed report with its path.** I wrote
nothing under `csv/`, nothing under another agent's directory, and I did not commit or push.
