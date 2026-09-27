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
