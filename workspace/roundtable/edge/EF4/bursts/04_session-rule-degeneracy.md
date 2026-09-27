# EF4 burst 04 — the three ways a census row lies, and what the 16:00–18:00 rule costs

`code/degeneracy.py` → `out/degeneracy.json`. Six single-timeframe cells.

A firing-rate table answers "can it fire". It does not answer whether the condition
*contributes*, and there are three separate ways it can fire and contribute nothing.

## 1. ALWAYS_ON — a filter that cannot veto

**`mtf_not_conflicted` fires on 100.00% of bars in all six single-timeframe cells**
(11,216/11,216; 3,746/3,746; 1,875/1,875; 11,212/11,212; 3,744/3,744; 1,873/1,873).

It is not VOID; it is the opposite. A "two signals + one filter" strategy carrying it is two
signals and nothing, while the combinator still counts it as a filter — so the strategy
*looks* like a three-condition confluence and is a two-condition one. On the 5+15+30 group
frame it drops to 71.5% (MGC) / 67.7% (MCL) and becomes a real filter.

Two near-neighbours in the same class: `outside_news_blackout` and `no_imminent_release`
pass on **99.1–99.6%** of bars in every cell and are **Jaccard 0.992–1.000** with each other
(exactly 1.000 at 30m on both symbols). A confluence containing both claims two independent
news checks and has one, which passes essentially always.

*Independently reproduces R1-D-MTF3 and R4's measurement of `mtf_not_conflicted` at 100% in a
frame of one, and R2's "`no_imminent_release` is identically TRUE".* I measured mine before
reading theirs; on reading them afterwards the verdicts agree, which is corroboration in the
sense the shared brief means it, and the credit for priority is theirs.

## 2. DUPLICATE — one condition, two names

Exact-identical fire sets (Jaccard = 1.0) in **all six** cells:

| pair | MGC 5m | MGC 15m | MGC 30m | MCL 5m | MCL 15m | MCL 30m |
|---|---|---|---|---|---|---|
| `macd_directional` ≡ `macd_hist_direction` | 9,175 | 3,052 | 1,561 | 9,137 | 3,114 | 1,512 |
| `regime_trending` ≡ `regime_matches_direction` | 1,955 | 735 | 363 | 2,226 | 756 | 397 |

Both were already found by R1 (`D-M1`), R4 (`R4-MO1`) and R6 (`D-R2`). This is replication in
six cells they did not report, not a new finding.

Beyond the exact pairs, **11–16 further pairs per cell exceed Jaccard 0.95**, and almost every
one involves an always-on member (`mtf_not_conflicted`, the two news filters, `away_from_zone`
at 95.5–97.9%). That is the mechanical reason: two conditions that each pass on ~99% of bars
are necessarily ~98% identical, whatever they compute. **A Jaccard screen on a population of
near-always-on filters will report duplication that is an artefact of base rate, not of shared
content.** Anyone using Jaccard as a de-duplication gate here needs to condition on fire rate.

## 3. UNTRADEABLE WINDOW — the one a census cannot see, and it is specific to this programme

The engine fills at the **next** bar's open (`FillModel.entry_on_next_open`,
`engine.py:291-297`). Under this programme's rule no position may be opened in
[16:00, 18:00) ET. So a signal on the bar before that window produces a fill inside it and is
**not actionable** — and the census counted it as a fire.

The substrate makes this concrete rather than theoretical: `data/archive/` carries a **full**
set of bars in hour 16 and essentially none in hour 17
`[measured: bar counts by ET hour → MGC 5m: hour 16 = 492 bars (41 days × 12), hour 17 = 3]`.
The real CME break for these contracts is 17:00–18:00; the programme's rule is one hour
stricter and therefore removes an hour of genuinely traded time, ~4.4% of 5m bars.

Fires lost to the prohibition, worst conditions per cell:

| condition | cell | fires | illegal | % lost | share of fires outside RTH |
|---|---|---|---|---|---|
| `session_extreme_sweep` | MCL 30m | 26 | 17 | **65.4%** | **100%** |
| `session_extreme_sweep` | MCL 15m | 31 | 17 | 54.8% | 100% |
| `session_extreme_sweep` | MCL 5m | 55 | 25 | 45.5% | 100% |
| `session_extreme_sweep` | MGC 30m | 32 | 13 | 40.6% | 100% |
| `session_extreme_sweep` | MGC 15m | 40 | 14 | 35.0% | 100% |
| `session_extreme_sweep` | MGC 5m | 57 | 16 | 28.1% | 100% |
| `initial_balance_break` | MCL 30m | 374 | 83 | 22.2% | 37% |
| `opening_range_breakout` | MCL 30m | 453 | 96 | 21.2% | 35% |
| `open_outside_value` | MCL 30m | 497 | 94 | 18.9% | 31% |
| `volatility_compressed` | MCL 5m | 3,601 | 325 | 9.0% | **100%** |

### `session_extreme_sweep` is MISNAMED in my cells, and the session rule finishes it off

It fires **100% outside RTH in all six cells**, and the mechanism is exact.
`lv.session_high` is `rth_high`, the running RTH extreme, and `_build_session_state` updates
it with the current bar *before* building the snapshot `[repo-verified: features.py:881-885]`
— so during RTH the test `b.high > lv.session_high` compares a value against a maximum that
already includes it and is arithmetically impossible. It can only fire on a bar where
`rth_high` is frozen, i.e. **after** the contract's RTH close and **before** `trading_day`
rolls at 18:00 `[repo-verified: timeutil.py:169-180]`. So what it detects is "swept the
*completed* RTH high/low during the post-close extension", not "swept the session extreme".

Then the session rule removes 28–65% of what is left:

| cell | fires | legal entries | verdict after the session rule |
|---|---|---|---|
| MGC 5m | 57 | **41** | NEAR_VOID-adjacent |
| MGC 15m | 40 | **26** | **NEAR_VOID** |
| MGC 30m | 32 | **19** | **NEAR_VOID** |
| MCL 5m | 55 | **30** | at the floor exactly |
| MCL 15m | 31 | **14** | **NEAR_VOID** |
| MCL 30m | 26 | **9** | **NEAR_VOID** |

**Four of six cells fall below the 30-trade floor purely because of the session rule** —
before any strategy filter narrows it further. This is the census verdict changing *because
of the programme's defining rule*, which is exactly the class of effect that has never been
measurable in this repository before.

`volatility_compressed` (MCL 5m, 3,601 fires, **100% outside RTH**) is the same shape without
the rarity: a condition whose entire population lives in the overnight session. Under the old
RTH-only regime it was untestable; under this rule it is the *most* testable thing in the cell
and also the thinnest-book, highest-slippage one. Burst 02's thin-book penalty is not a
correction to these rows — it is their dominant term.
