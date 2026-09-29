# Rules and pitfalls

Part A is for the trader. Part B is for the agents and scripts: traps that already cost earlier
teams days of work. The full lists with sources are in `sources/agent1_roundtable.md` §5,
`sources/agent2_research.md` §10 and `sources/agent3_desks.md` §2.

---

## Part A — trading rules (paper, $50,000 account)

### Risk
| rule | number | why |
|---|---|---|
| Hard floor | **$2,800 drawdown = account dead** (the allowed risk drops below the $25 minimum). Operate as if the floor is $2,600 | The account can't recover from there |
| Risk per trade | min(6% of room-to-floor, 0.75% of equity, $500). **$240 at zero drawdown** | Size shrinks automatically as drawdown grows |
| While nothing is proven | **Use ≤ 50% of that ($120)** | The only result in the project that clears its luck bar: shrinking size protects the account (z 6.2) |
| Count the whole book | Open **plus** pending orders count against the budget | The old desk once thought it had $120 of room when $22 was left |
| One contract | At $240, MNQ fits exactly 1 contract. MGC's daily-ATR stop doesn't fit at all | "Take half off at +0.8R" is impossible with 1 lot. Move the stop to breakeven instead |

### When to trade and when not to
| rule | number |
|---|---|
| Flat by **16:00 ET**, nothing held 16:00–18:00 | costs only 0.003R/trade |
| **No new entries 15:00–16:00 ET** | z −4.4 |
| **Volatility stand-down** | no new plan if ATR14 on 15m > **58 (MNQ)** or > **10 (MGC)** |
| Don't fade the first 60m bar after 09:30 | z −10.6 |
| Don't buy/sell a breakout in the direction of the move | worse than random 4/4 |
| Measured sessions | MGC 08:20–13:30, MNQ/MES 09:30–16:00, MCL 09:00–14:30 ET. Outside these, say "unmeasured" |
| MES/MNQ are one market | Two signals agreeing across them are **not** confirmation |

### Entries, stops, exits
- **Win rate and payoff always go together.** 70% winners at 0.4 payoff loses money.
- Stops: never tighter than **0.5 ATR**, and beyond where an obvious level's stops cluster.
- Anchor limit orders to **fixed structure**, not a moving average. Limits that trailed an EMA
  filled on exactly the bar that killed the setup (3/3).
- **Don't move entries toward the market to get filled.** That was the old desk's biggest leak
  (55–60% fill rate vs 4% for the disciplined replay desk).
- If a gap cuts reward:risk below 1.5, the plan is void. Re-plan.
- Every decision gets priced afterwards, including stand-downs ("what did not trading cost?").

---

## Part B — data & code pitfalls (for agents)

### Data
1. **The data is not real-time.** The Yahoo feed lags a median **13 min at 5m** and ~23 min at 15m.
   The newest 1–2 bars get **revised for ~28 min**, so a "break" on an unsettled bar isn't a break.
   Every level must carry the timestamp of its source bar.
2. **Stub bars:** volume 0 and high = low means the vendor filled a hole with the old price
   (once 12.2 pts wrong on MGC). `refresh_archive.py` and `bounce_levels.py` drop them.
3. **26% of MGC/MNQ 5m & 15m bars have no volume field.** Volume-based conditions read those as 0.
   The volume-profile scanner spreads real volume only. Treat 5m profiles with care.
4. **Timezones:** `csv/raw/` is UTC and `data/archive/` is ET. Normalise before comparing.
5. **Rolls:** MGC daily bars are spliced (10× jump at 2012-04-25) and fail the roll audit.
   **Never mix MGC daily with intraday levels.** MES 60m has two glued contract-roll stretches
   (Dec-24, Mar-25). MCL has no usable daily history (CL daily has a negative price in 2020).
   Grains are unusable. QQQ/SPY intraday volume is ~59% zeros.
6. **Yahoo caps:** 1m = 7 days, 5m/15m/30m = 60 days, 60m = 730 days. A request past the cap
   returns **empty with no error**. Futures need the `=F` suffix. There's no 4h bar (it's resampled).
   The micros are priced from the full-size contract (NQ=F for MNQ, etc.).
7. **`csv/raw/` is read-only** (`chattr +i`). Never write there. `data/archive/` is append-only via
   `BarArchive` and never shrinks.
8. `open[i+1] ≠ close[i]` on 57–80% of bars. Quote fills from the next **open**, never a close.
9. The Oanda 1m archive used by the old "deep ORB" work is gitignored and not in the repo.

### Method
10. **Every result needs a placebo** (random entries or random levels, same exits, same bars).
    Match placebos on *realised* trade counts, and use several draws.
11. **State the luck bar:** √(2·ln N) for N things tried. ~3 million candidates were generated in
    this repo, so that bar is ~5.5. Short data spans make it worse: 58 days of 5m data needs an
    annualised Sharpe ≈ 9 to clear a 465-variant search.
12. **Nested windows are one observation** (30/90/180/274-day windows ending on the same bar). Use
    disjoint slices or a 60/40 time split.
13. **The 20-trade floor secretly selects exit geometry.** Always report the floor-free census.
14. **Pre-register** a hypothesis before looking. A single pre-registered test only needs t ≥ 1.18.
15. **Numbers go in code output, not prose.** Earlier desks' prose had 27 errors, all leaning the
    author's way.

### Code (the `futures_agents` package and old harness)
16. Conditions that can never fire ("VOID"): 19% of generated strategies carry one, and a strict AND
    kills the whole strategy. Check firing rates, pairwise too.
17. Aliases: many conditions are the same thing under different names (e.g. OTE = fib golden
    pocket; `value_area_breakout` ≈ prior-day breakout). Jaccard-check new conditions.
18. `dataclasses.replace` can give two arms the same id, so their difference reads exactly zero.
    Assert unique ids.
19. `min_stop_ticks` silently turns VWAP-band/structure stops into fixed-tick stops (MGC 25 ticks).
20. With `exit_at_session_close=True`, any entry at or after 12:30 ET exits on its entry bar.
21. `Trade.gross_r` is already net of slippage. Scale-outs pay one round turn (costs are under-charged).
22. Stale fills across the weekend gap are 3–14× worse. Veto fills that lag by more than one bar.
23. `futures_agents/scanners/measure.py` is referenced but missing. The 99X1 breach-scanner numbers
    are hard-coded in `render.py`. Use `DATA_HUB/tools/bounce_levels.py` instead; it re-measures.
24. Scheduling: `CronCreate` runs in **UTC** in the container. Write crons in UTC and re-cut them
    when EDT→EST changes on **2026-11-01**. Session crons die when the worker restarts, so check
    with `CronList`.
