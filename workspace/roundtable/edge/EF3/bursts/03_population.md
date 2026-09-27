# EF3 burst 03 — the population, its exact size, and what the census removed

**Code:** `EF3/code/ef3_population.py`. **Output:** `EF3/out/population_4000.json`,
`EF3/out/population_ids_4000.json` (the full id manifest, so the population is citable).

## The population, pre-registered

`generate_combinations(sym, [60, 240], groups=groups_for(sym), confirm_map=…, max_total=4000,
seed=20260922)`, called twice per symbol — once with `confirm_map={60:(), 240:()}` and once with
`{60:(240,), 240:()}` — deduplicated by `strategy_id`, then doubled into an `rth_only` pair.

| | MES | MNQ | total |
|---|---|---|---|
| distinct rule sets after dedup | 3,011 | 2,952 | 5,963 |
| **× 2 `rth_only` arms = POPULATION** | **6,022** | **5,904** | **11,926** |

**Search size = 11,926 for the programme's purposes; 6,022 / 5,904 per symbol** (a top 10 is chosen
inside one symbol, so the symbol's own count is the honest `n` for that list).

| n | `free_t = sqrt(2·ln n)` | annualised Sharpe needed on 1.968 yr (sqrt = 1.403) |
|---|---|---|
| 5,904 (MNQ) | **4.167** | **2.970** |
| 6,022 (MES) | **4.172** | **2.974** |
| 11,926 (both) | 4.333 | 3.088 |
| 1 pre-registered hypothesis | 1.177 | **0.839** |

**Two things worth saying about those numbers rather than just printing them.** First, the span is
doing real work for once: the programme-wide requirement was a Sharpe of 5.82 on a 0.88-year span,
mine is **2.97** on 1.97 years — a factor of two better, from 2.2× the span and a 250× narrower
search. It is still not a Sharpe that exists. Second, **narrowing the search further is nearly
worthless**: n = 40,000 gives `free_t` 4.604 and n = 4,000 gives 4.073, so a tenfold change in
search width costs 0.53 t-units. There is no version of this cell where trimming the population
rescues a row. The only lever with real leverage is `free_t = 1.177`, which requires the hypothesis
to be fixed in writing before looking — and I have not earned that for any row here.

## The four cells, and what the census removed

| cell | n | removed (VOID) | % | live |
|---|---|---|---|---|
| MES 60m (×2 confirm arms × 2 rth arms) | 4,168 | 96 | **2.30%** | 4,072 |
| MES 240m (×2 rth arms) | 1,854 | 1,014 | **54.69%** | 840 |
| MNQ 60m (×2 confirm arms × 2 rth arms) | 3,868 | 688 | **17.79%** | 3,180 |
| MNQ 240m (×2 rth arms) | 2,036 | 902 | **44.30%** | 1,134 |
| **MES total** | **6,022** | **1,110** | **18.43%** | 4,912 |
| **MNQ total** | **5,904** | **1,590** | **26.93%** | 4,314 |

**MNQ: 1,590 of 5,904 = 26.93% removed.** That independently reproduces R1's **27.4%** from a
different sample (max_total=400 vs 4,000), a different group set (the symbol's research profile vs
all 13 templates), a different store (`data/archive` vs `csv/raw`) and a different timeframe set.
Two independent measurements agreeing to 0.5 points.

### `openinterest` on MNQ, specifically

| | MES | MNQ |
|---|---|---|
| carries a VOID `openinterest` condition | **0** | **610** (10.33% of the population) |
| removed by `openinterest` **and nothing else** | 0 | **538** |
| at 60m | 0 | 106 per arm-cell (×4 = 424) |
| at 240m | 0 | 93 per arm-cell (×2 = 186) |

**MES's zero is not a property of MES.** It is a property of its research profile: MES's profile
admits VWAP, VOLUME_PROFILE, MEAN_REVERSION, PULLBACK, REVERSAL, LIQUIDITY, MULTI_TIMEFRAME, and
**neither MOMENTUM nor BREAKOUT** — which are the only two templates offering the `openinterest`
group `[repo-verified: combinator.py TEMPLATES optional_groups / optional_filters]`. MNQ's profile
admits both. So the entire 60m gap between the two symbols' dead rates (2.30% vs 17.79%) is
`openinterest` plus `opening_range_fade`, and it comes from the *profile*, not from the tape. Change
MNQ's profile and this number changes; that is what makes it a property of the search, not of the
market.

### Full cause attribution

| cause group | MES carriers | MES sole cause | MNQ carriers | MNQ sole cause |
|---|---|---|---|---|
| `multitimeframe` (`mtf_aligned`/`mtf_strongly_aligned` at 240m) | 400 | 400 | 504 | 432 |
| `profile` (all six, at 240m) | 590 | 582 | 288 | 248 |
| `openinterest` | 0 | 0 | **610** | **538** |
| `liquidity` (`opening_range_fade` at 60m/240m) | 128 | 120 | 296 | 264 |

1,102 of MES's 1,110 and 1,482 of MNQ's 1,590 are killed by exactly one cause group, so the causes
are close to disjoint and each one's removal count is nearly its own marginal cost.

### The single most consequential line

**At 240m, roughly half the generated population cannot fire: 54.69% on MES, 44.30% on MNQ.** For
MES that is driven by `profile` — VOLUME_PROFILE is in MES's profile and it is *required*-group VOID
at 240m, so **every** VOLUME_PROFILE strategy at 240m is structurally zero-trade. And MULTI_TIMEFRAME
is in both symbols' profiles while 240m is the top of my frame, so **every** MULTI_TIMEFRAME strategy
at 240m is structurally zero-trade too. Two of seven admitted families are entirely unmeasurable at
240m on MES, and one of seven on MNQ.

This is the distinction the programme keeps losing: those are not weak results, they are **no
results**. A prior report that listed "MES 240m: no real strategy in the top 10 at all"
(`RANKING_FINDINGS.md`) was reading a table from which half the population had silently been deleted
before the ranking started.

## D48 guard, as required

Every `dataclasses.replace` in `ef3_population.py` passes `_id=None`, and the builder asserts
(a) `alt.strategy_id != st.strategy_id` for each arm pair at construction and (b)
`len(ids) == len(set(ids))` over the whole emitted population. Both assertions pass on both symbols.
Without (a) the `rth_only` pair collides into one `BacktestResult` and the arm difference measures
exactly zero — indistinguishable from "the overnight window makes no difference", which is precisely
the claim I am here to test.
