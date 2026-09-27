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
