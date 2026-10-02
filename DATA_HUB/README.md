# DATA HUB — start here

**Consolidated 2026-09-29.** Everything the earlier agent teams (≈10 sessions, ~30 sub-agents,
≈3 million strategy tests) learned about MNQ, MES, MGC and MCL is in this folder. The rest of
the old material sits in `Archived_Do_Not_Refference/` with an index. **Don't re-open it.**

---

## The whole story in five sentences

1. **Nothing has a proven edge yet.** No strategy on any symbol beat the "you tested so many
   things that one had to look good by luck" bar. Random entries through the same stops and
   targets did about as well as the best "real" strategies.
2. **Picking last month's best strategies does worse than trading all of them.** Past
   top-10 lists don't repeat.
3. **Price levels (support/resistance, prior-day high/low, VWAP, POC, round numbers, low-volume
   nodes) don't bounce or break more often than random prices do.** We measured this four
   independent ways, including two new scanners built for this hub. *Knowing where the level
   is* isn't enough. What happens *at* it, and what you do with the stop, decides the trade.
4. **The rules that do hold up are "don'ts" and risk rules.** Don't buy breakouts in the
   direction of the move. Stand down when volatility is too high for your stop. Don't open
   trades 15:00–16:00 ET. Size small (≤50% of the allowed risk). Those protect the account.
5. **The most promising untested idea:** every live paper trade went at least +0.83R in
   profit before most of them lost. Moving the stop to breakeven at about +0.8R has
   never been tested on the archive, and it's the first thing to test.

---

## What's in here

| file | read it for |
|---|---|
| [`STRATEGIES_BY_SYMBOL.md`](STRATEGIES_BY_SYMBOL.md) | **Top strategies for each symbol**, ranked by how well-supported they are, in plain English |
| [`BOUNCE_AND_VOLUME_PROFILE_PLAYBOOK.md`](BOUNCE_AND_VOLUME_PROFILE_PLAYBOOK.md) | **Your style:** bounce levels, multi-timeframe volume profile, LVNs, continuation vs bounce, *why* a level holds, and today's levels |
| [`RULES_AND_PITFALLS.md`](RULES_AND_PITFALLS.md) | Risk rules, session rules, data traps that already cost earlier agents |
| [`OPEN_QUESTIONS.md`](OPEN_QUESTIONS.md) | What to test next, in priority order, and the obligations left open |
| [`LTA_CONCEPTS.md`](LTA_CONCEPTS.md) | **The LTA Concepts 2.0 e-book, digested:** volume-profile levels (PD/EPD/PW/EPW/CW, Sunday Open, fixed & swing), entry models EM1–EM4, COT/valuation/seasonal bias, supply & demand, 2/2/2 risk, and how each claim lines up with what this repo measured. Used by the **LTA Concept Callouts** desk (`workspace/paper/LTA/`) |
| [`AUTOMATION.md`](AUTOMATION.md) | **What now runs without an LLM:** desk check script, walk-forward engine, daily data refresh, and the first pre-registered test of your LVN idea |
| [`MAP.md`](MAP.md) | **Every live file in the repo, one line each** (generated) |
| [`SESSIONS_AND_AGENTS.md`](SESSIONS_AND_AGENTS.md) | Who did what before, where their data went, which sessions are archived or paused |
| `levels/` | **Generated** reports: `<SYM>_bounce.md`, `<SYM>_volume_profile.md`, `CONSISTENCY.md` |
| `tools/` | **Scripts.** Everything below is automated |
| `sources/` | The three sweep reports these pages were written from (full numbers and file citations) and the KEEP/ARCHIVE manifests |

## Refresh everything with one command

```bash
pip install yfinance                     # once per container
bash DATA_HUB/tools/update_hub.sh        # pull fresh bars → re-measure levels → rebuild reports
bash DATA_HUB/tools/update_hub.sh --no-fetch   # re-analyse without pulling
```

| tool | what it does |
|---|---|
| `tools/refresh_archive.py` | Pulls the newest Yahoo bars into `data/archive/`, append-only and never deleting. Also folds loose fetch files into the archive (`--merge-fragments DIR`). Rejects vendor "stub" bars. |
| `tools/bounce_levels.py` | Classic levels (prior day/week high-low-close, overnight high/low, prior-day POC & VWAP, 60m swings, round numbers). Every touch is tested two ways, *buy at the level* and *sweep & reclaim*, against fake levels. Lists the levels near price now. |
| `tools/vp_levels.py` | **Multi-timeframe volume profiles** (1-day, 3-day, 1-week, 2-week on 5m bars; 1-week, 1-month, 3-month on 60m bars). Finds POC, value area, HVNs and **LVNs**, splits each range into its trend legs, and measures **continuation vs bounce** at LVNs against random prices. |
| `tools/level_consistency.py` | Which of those findings repeat across **all** symbols, the only kind worth trusting. |
| `tools/walkforward.py` | Replays any **pre-registered** rule bar by bar with the replay harness's exact fills, a corrected placebo and a ledger-counted luck bar. Rules live in `tools/rules/`. |
| `tools/build_map.py` | Regenerates `MAP.md` from each file's own docstring/heading. |
| `tools/apply_archive.py` | Moves files listed ARCHIVE in a manifest into `Archived_Do_Not_Refference/` and rewrites its index. |

Data on disk: `data/archive/` runs through **2026-09-29 00:58 ET** (after this consolidation's
refresh). `csv/raw/` is older, read-only CME data that ends 2026-09-22.

---

## Words used in these pages

| term | meaning |
|---|---|
| **R** | One unit of risk: the distance from entry to stop. +0.10R per trade = you make 10% of what you risk, on average. |
| **Expectancy** | Average R per trade *after* costs (commission + slippage). |
| **Win rate / payoff** | % of trades that win / average win ÷ average loss. **Quote both together, never one alone.** A high win rate with small wins can still lose money. |
| **ATR** | Average True Range: the typical size of one bar. Used to set stops and distances so they scale with volatility. |
| **Placebo / fake / random** | The same test on randomly chosen entries or prices. If the real thing doesn't beat it, the real thing isn't what's working. |
| **z** | How many "standard errors" real beats placebo by. 2 sounds good but is common by luck when you test many things. |
| **Luck bar (free z / free t)** | The z you'd expect from the *best of N random tries*: √(2·ln N). Testing 40 things gives a luck bar ≈ 2.7. Testing 3 million gives ≈ 5.5. |
| **In-sample / out-of-sample (OOS)** | Data used to find a rule / fresh data used to check it. Only OOS counts. |
| **PDH / PDL / PDC** | Prior day's high / low / close. **ONH/ONL** = overnight high/low. **PWH/PWL** = prior week. |
| **RTH** | Regular trading hours: 09:30–16:00 ET for index futures. |
| **Volume profile** | Volume traded at each price over a range. **POC** = busiest price. **Value area** = the 70% of volume around it. **HVN** = heavy area. **LVN** = thin area between two heavy ones. |
| **Continuation vs bounce** | Arriving at a level: price keeps going through it (continuation) or turns back (bounce). |
| **Sweep & reclaim** | Price pokes through a level (runs the stops), then closes back on the other side. |

---

## Ground rules for every agent on the new team

1. **Read this README first, then the page for your task.** Don't open
   `Archived_Do_Not_Refference/`. Its `ARCHIVE_INDEX.md` lists what every item contained, and
   the findings are already here.
2. **Every result needs a placebo and a luck bar.** "It won 60%" means nothing until you know
   what random did on the same bars.
3. **Never state a price as current unless you fetched it this turn.** Stamp every level with
   the bar it came from.
4. **Put numbers in code, not prose.** Earlier desks found 27 prose errors, all leaning the way
   the author wanted.
5. **Paper only.** Nothing here places orders. Account: $50,000, hard floor at $2,800 drawdown.
6. **Owner's style comes first:** bounce levels, volume profile across timeframes, LVNs,
   continuation vs bounce. See the playbook.

_This is research and decision support, not financial advice._
