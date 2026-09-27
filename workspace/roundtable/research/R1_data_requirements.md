# R1-D3 — Data-requirement ledger for Class I

**Track:** R1 (DIVISION §2). **Deliverable:** R1-D3 per DIVISION §3.
**Companion:** `workspace/roundtable/research/R1_flow_auction.md` (R1-D1, D2, D4, D5, D6, §7 answers).
**Rule:** no cell is blank, and every **NO** cites a path. Marking per `BRIEF.md` rule 3.

---

## 0. The seven data objects, and whether `csv/raw/` supplies any of them

Established once here, then referenced by the family table. All 48 files carry one header:

```
[measured: for f in csv/raw/*.csv; do head -1 "$f"; done | sort | uniq -c
  → 48 open_time,open,high,low,close,volume]
[measured: ls csv/raw/ | 48 files; intervals present: 1m ×7, 5m ×11, 15m ×7, 30m ×7, 1h ×11, 1d ×5.
  No interval finer than 1m exists.]
```

| # | data object | in `csv/raw/`? | evidence |
|---|---|---|---|
| **O1** | **Time-and-sales** — per-print `(timestamp, price, size)` | **NO** | Finest file is `*_1m.csv` `[measured: ls csv/raw/ → intervals 1m/5m/15m/30m/1h/1d only]`. Confirmed by DIVISION Appendix B fact 2. A 1m bar is four prices plus a volume sum; the summands are not recoverable. |
| **O2** | **Bid/ask volume split** (aggressor side, bar-level) | **NO** | The `Bar` fields exist and default to `None` `[repo-verified: futures_agents/data/bars.py:44-45]`; the loader accepts eight aliases for each `[repo-verified: futures_agents/data/loader.py:40-43]`; nothing under `csv/` supplies them `[measured: grep -rl "bid_volume\|ask_volume\|open_interest\|openinterest" csv/ → no matches]`. Consequence: `delta_is_estimated` is `True` on every bar `[measured: all 300 MGC_1h bars → True]` and `Bar.delta` returns `CLV × volume` `[repo-verified: futures_agents/data/bars.py:95-113]`. |
| **O3** | **Per-price footprint matrix** (bid/ask volume per price per bar) | **NO** | `Bar` is a flat frozen dataclass with ten scalar fields and no per-price container `[repo-verified: futures_agents/data/bars.py:28-47]`. Not merely absent from the data — absent from the type. |
| **O4** | **DOM / book depth** (resting quantity per side per level) | **NO** | No depth field, no quote field, no book object anywhere in the package `[measured: grep -rni "\bdepth\b\|order_book\|best_bid\|best_ask\|bid_price\|ask_price" futures_agents/ --include=*.py → only unrelated "drawdown depth" (backtest/objectives.py:23,97) and recursion-depth parameters]`. |
| **O5** | **Exchange volume-at-price** (traded volume per price level per session) | **NO** | Reconstructed instead, by spreading each bar's volume uniformly across every bin its range touches: `share = (b.volume or 1.0) / span` `[repo-verified: futures_agents/indicators/volume.py:225-232]`, docstring acknowledging the approximation at `:216-222`. Magnitude of the loss measured in `R1_flow_auction.md` R1-D4. |
| **O6** | **Sub-minute bars** | **NO** | `[measured: ls csv/raw/ → no interval below 1m]`. `align_bucket` supports `minutes < 60` down to 1 `[repo-verified: futures_agents/data/bars.py:155-156]`, so the code could carry them; the data does not exist. |
| **O7** | **Session boundaries** | **YES** | A nine-window session map with explicit ET times `[repo-verified: futures_agents/timeutil.py:103-122]`, plus `classify_session`, `session_of`, `minutes_since_open`, `is_rth`, `rth_bounds`, `trading_day`, `time_bucket`, and a holiday calendar `[repo-verified: futures_agents/timeutil.py:23-28]`. Per-contract RTH and Globex times on `ContractSpec` `[repo-verified: futures_agents/config.py:42-44]`. Derived reference levels in `SessionLevels` `[repo-verified: futures_agents/indicators/structure.py:305-318]`. **This is the one object on the list the repo has in full.** |

Two extra objects that turned out to matter enough to name, because they are the cheap ones:

| # | data object | in `csv/raw/`? | evidence |
|---|---|---|---|
| **O8** | **Per-bar trade count** (number of executions) | **NO** | Not in the header `[measured: 48 files, `open_time,open,high,low,close,volume`]`; no `Bar` field `[repo-verified: futures_agents/data/bars.py:38-47]`; no loader alias `[repo-verified: futures_agents/data/loader.py:28,40-44]`. One integer column. Gives average print size per bar. |
| **O9** | **Official daily settlement price** | **NO** | `settle` is accepted **only as an alias for `close`** `[repo-verified: futures_agents/data/loader.py:38]`, so a vendor supplying both would overwrite the close and nothing would flag it. `ContractSpec` has no settlement field `[repo-verified: futures_agents/config.py:31-44]`. |

**Also confirmed absent, for the record:** open interest — `Bar.open_interest` exists and is `None` on
every bar `[repo-verified: futures_agents/data/bars.py:46; futures_agents/features.py:278-279]`
`[measured: all 300 MGC_1h bars → open_interest None]`, which makes both `openinterest` conditions
unable to fire `[repo-verified: futures_agents/strategies/library.py:1281-1282,1309-1310]`.

---

## 1. The ledger — one row per Class I family

**KEY.** `REQ` = required for the family to exist as operated. `HELP` = improves it materially.
`—` = not required. The **Supplied?** column answers *"does `csv/raw/` supply everything marked REQ"*.
No cell is blank.

| family | O1 T&S | O2 bid/ask split | O3 footprint matrix | O4 DOM depth | O5 vol@price | O6 sub-minute | O7 session bounds | O8 trade count | O9 settlement | Supplied? | binding gap |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **I-1** Order flow / footprint | REQ | **REQ** | **REQ** | HELP | HELP | REQ | HELP | HELP | — | **NO** | O2 then O3 |
| **I-2** Absorption / stopping volume | HELP | **REQ** | HELP | HELP | HELP | REQ | HELP | HELP | — | **NO** | O2 |
| **I-3** Iceberg / hidden size | REQ | HELP | — | **REQ** | — | REQ | — | HELP | — | **NO** | O4 (order-level events) |
| **I-4** DOM / book pressure / queue | REQ | HELP | — | **REQ** | — | REQ | — | HELP | — | **NO** | O4 |
| **I-5** Market making / spread capture | REQ | HELP | — | **REQ** | — | REQ | — | HELP | — | **NO** | O4 (best bid/offer + sizes) |
| **I-6** Tape scalping | **REQ** | HELP | — | HELP | — | REQ | HELP | REQ | — | **NO** | O1 |
| **I-7** Market profile / TPO | — | — | — | — | **REQ** | HELP | **REQ** | — | — | **NO** | O5; plus TPO counts (code, not data) |
| **I-8** Auction market theory | — | HELP | — | — | **REQ** | HELP | **REQ** | — | — | **NO** | O5; plus time-at-price per bracket |
| **I-9** Volume profile | — | — | — | — | **REQ** | HELP | **REQ** | — | — | **NO** | O5 |
| **I-10** VWAP as institutional benchmark | HELP | HELP | — | — | HELP | HELP | **REQ** | **REQ** | — | **NO** | O8 (the benchmark *line* is supplied; the *inference* is not) |
| **I-11** Liquidity mapping / stop runs | — | HELP | — | **REQ** for the liquidity claim | — | HELP | **REQ** | — | — | **PARTIAL** | O4 for size-behind-level; geometry needs nothing missing |
| **I-12** Alternative bar sampling | **REQ** | REQ (imbalance/run bars only) | — | — | — | REQ | — | HELP | — | **NO** | O1; and separately a non-minute bar identity (architecture) |
| **I-13** CVD divergence / footprint shape | HELP | **REQ** (a) | REQ (b) | — | **REQ** (b) | HELP | HELP | — | — | **NO** | O2 for (a), O5 for (b) |
| **I-14** Block / large-print detection | **REQ** | HELP | — | — | — | REQ | — | REQ (weak form) | — | **NO** | O1; O8 gives a weak substitute |
| **I-15** Opening auction / settlement window | HELP | — | — | HELP | — | **REQ** (the open) | **REQ** | — | **REQ** | **NO** | O9, plus a cash-market closing imbalance (a second observable — R2's class) |

**Column totals.** Objects required by at least one family: O1 (4 families REQ), O2 (4), O3 (2),
O4 (4), O5 (5), O6 (7), O7 (6 — **the only one supplied**), O8 (2), O9 (1).
**Families for which `csv/raw/` supplies every REQ object: 0 of 15.** The nearest is I-11, whose
level-geometry half is fully supplied and whose liquidity claim is not.

---

## 2. What each NO would cost to turn into a YES

Cross-referenced to the primitives P1–P11 in `R1_flow_auction.md` R1-D5.

| object | primitive | acquisition | code required | families moved |
|---|---|---|---|---|
| **O7** | — | already held | none | — |
| **O8** | P6 | **one integer column** from any professional vendor or broker export | one `Bar` field + one loader alias (the alias table already exists, `loader.py:40-44`) | I-10 (inference half), I-14 (weak form) |
| **O5** | P5 | volume-at-price product; far smaller than tick data | populate `VolumeProfile.histogram` from measured data instead of the smear at `volume.py:225-232` | I-7, I-8, I-9, I-13b — and repairs the six `profile` conditions |
| **O2** | P1 | MBP-1 / MDP3 historical, aggregated to bar-level bid/ask volume | **zero for ingestion** — `Bar.bid_volume`/`ask_volume` and the `delta` switch already exist (`bars.py:44-45, 95-104`); ~30 lines for tick→bar aggregation | I-1 (partly), I-2, I-13a, I-6 (partly) — and repairs the three `orderflow` conditions |
| **O9** | P10 | one column from the exchange's settlement file | new `Bar` field; **and fix the `settle`→`close` alias first** (`loader.py:38`) or it will silently corrupt closes | I-15 (partly) |
| **O1** | P4 | full tick history — the largest purchase on the list | a tick store, plus bar construction | I-6, I-12, I-14 |
| **O3** | P2 | derived from O1 | new per-price container on a frozen `Bar` that every layer depends on (`bars.py:28-47`) — days, and invasive | I-1, I-13b |
| **O4** | P3 | book data — largest purchase, plus a queue-aware fill model (a different backtester) | new engine | I-3, I-4, I-5, I-11 (liquidity half) |
| **O6** | — | sub-minute bars are a by-product of O1 | `align_bucket` already handles `minutes` down to 1 (`bars.py:155-156`); sub-minute would need fractional-minute identity, i.e. P11 | the sub-minute half of I-1, I-2, I-6 |

**Two items need no data at all** and are therefore not in this table — they are pure code and they
are the top of my build ranking: **P7** TPO / time-at-price counts (zero occurrences anywhere:
`[measured: grep -rni "tpo\|time_at_price\|bracket" futures_agents/ --include=*.py → no matches]`)
and **P8** composite / multi-session profile plus POC persistence (`prior_session_profile` reads
exactly `self._day_order[position - 1]` `[repo-verified: futures_agents/features.py:615-622]`).

---

## 3. The two live-data stores, against this ledger

`BRIEF.md` records a correction: Yahoo Finance *is* reachable, and `data/archive/` now holds 29 JSONL
series (~157,000 bars, newest 2026-09-25T16:00-04:00). **It changes nothing in this ledger, and I
checked rather than assumed.**

- **The Yahoo ingestion path constructs a `Bar` with six fields and nothing else:**
  `Bar(ts=ts, open=op, high=hi, low=lo, close=cl, volume=max(0.0, volume), minutes=plan.fetch_minutes, complete=True)`
  `[repo-verified: futures_agents/data/yahoo.py:398-400]`. `bid_volume`, `ask_volume` and
  `open_interest` are never passed, so they take their `None` defaults
  `[repo-verified: futures_agents/data/bars.py:44-46]` and `delta_is_estimated` is `True` on every
  bar the live feed produces, exactly as for `csv/raw/`.
- **The archive's own record schema is six keys:**
  `{"ts": ..., "o": ..., "h": ..., "l": ..., "c": ..., "v": ...}`
  `[measured: head -c 400 data/archive/CL_1440m.jsonl → six keys per line, no bid/ask, no OI, no trade count]`.
- **Yahoo's interval table caps 1-minute history at 7 days**
  `[repo-verified: futures_agents/data/yahoo.py:78-87 → INTERVALS[1] = ("1m", timedelta(days=7))]`,
  which is *shorter* than the `csv/raw` 1m files, and it serves no interval finer than 1 minute at all.

**So for Class I, a free OHLCV feed is not an acquisition — it is more of exactly what we already
have.** All nine objects O1–O6, O8, O9 remain NO against both stores; only O7 is supplied. The
acquisitions that would matter are O8 (one column), then O5, then O2 — none of which any reachable
free feed provides.

---

## 4. What I did not audit, and who owns it

Per DIVISION §5 and §2, and stated so nobody double-audits:

- `futures_agents/backtest/costs.py` and the fill model — **R3's**. Named in my anti-overfitting
  table as the risk that binds hardest on Class I (2–10 tick targets), not adjudicated.
- `futures_agents/strategies/profiles.py` — **R2's**. I called `groups_for()` as a reachability probe
  and read none of its contents.
- `futures_agents/econ_calendar.py` and the `ECON_RULES` inventory — **R2's** (R2-D5). I audited only
  the three `news` conditions' arithmetic and the proximity plumbing at `features.py:946-1000`, and
  handed R2 the HIGH-impact filter point as Q3 in `OPEN_QUESTIONS.md`.
- `futures_agents/backtest/engine.py` — **R2's** entry points and **R3's** position lifecycle. I cite
  neither.
- `StopKind.VWAP_BAND` as a stop primitive — **R3's** (DIVISION §5.3). I own VWAP as a
  participant-behaviour object and the five `vwap` conditions, and I did not touch the stop.
