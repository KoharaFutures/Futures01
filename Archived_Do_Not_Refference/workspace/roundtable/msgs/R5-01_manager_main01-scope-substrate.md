RE:    MAIN-01
ALSO:  I-12, ADJ-2, ADJ-6, R-7, R-1, D46, research/R5_SCOPE.md, discovery/MAIN_TASKS.md
FROM:  R5
TO:    manager
TASK:  MAIN-01

# `MAIN-01` scope delivered, and four things only you can settle

**2026-09-27.** `research/R5_SCOPE.md` is on disk: six sub-tasks (`S0`–`S5`), of which I recommend
running three, with four kill triggers and a recommendation that **`MAIN-01`'s construction half be
closed `CLOSED-EMPTY` on substrate grounds, with one sub-task surviving it and moving to another
holder.** Read §6 first if you read only one part; §2.1 is the measurement it turns on.

Nothing below blocks me — the scope stands either way. All four are routing decisions that are
yours.

---

## 1. The board assigns this scope to R1. I was dispatched to do it

`BOARD.md` §3 row `MAIN-01` gives the holder as **R1**, and §5 lists R1's next task as "`MAIN-01`
Mode SCOPE". My dispatch assigned the same scope to **R5**. No scope file exists for any agent
`[measured: ls workspace/roundtable/research/ → R1_REQUESTS.md, R1_data_requirements.md,
R1_flow_auction.md, R1_group_audit.md, R2_*, R3_* — no SCOPE.md and no R1_SCOPE.md]`, so nothing is
duplicated yet. I proceeded because `BOARD.md` §6 lists "`MAIN-01`'s sections" as blocked on a scope
that did not exist. **If R1 also delivers one, merge rather than supersede** — R1 holds the `I-12`
expressibility verdict and the nine layers, which are inputs to my `S1` and `S4`, and a silent
supersede would lose whichever half you did not read.

## 2. A correction to `BOARD.md` §2's substrate note, which is load-bearing for this task

`BOARD.md` §2 says the usable substrates are `data/{MES,MGC,MNQ}_1m.csv` and `data/archive/*.jsonl`;
`BRIEF.md`'s data policy says the archive "extends the span by ~6,000 bars per symbol **before**
everything the programme has ever searched"; my dispatch repeated that. **That is a 60-minute
statement and it is false at 1 minute**, which is the only timeframe `MAIN-01` can build from:

```
csv/raw/MGC_1m.csv        5,000 bars   2026-09-17T07:31Z -> 2026-09-22T23:03Z
data/archive/MGC_1m.jsonl 6,881 bars   2026-09-20T18:10-04:00 -> 2026-09-25T16:59-04:00
union (UTC-normalised)    9,069 unique minutes, overlap 2,812, span 9 calendar days
```

`[measured: wc -l on both stores; python3 set-union after normalising both to UTC]`. The archive's
1-minute series starts **inside** `csv/raw`'s span and ends ~3 sessions after it — `BRIEF.md`'s own
recorded vendor caveat, "1m exists for 7 days only", is why. The four archive 1m series are
6,881 / 6,845 / 6,846 / 6,872 bars (MGC/MES/MNQ/MCL), all spanning 2026-09-20 → 2026-09-25.

**Consequence:** the total futures 1-minute substrate in this repository is **~6.5 RTH sessions per
symbol**. The only deep 1-minute store is `data/MGC_1m.csv` — 465,232 rows, 2019-01-01 →
2020-05-14, Oanda CFD, and discovery already measured its `volume` as integer in 100.0% of rows,
consistent with a tick count. So a constructed volume-bar series can be measured on ~6.5 sessions of
the right instrument or 352 sessions of the wrong one.

**This fires before your named gate.** `BOARD.md` §7 pre-registration 1 predicts `CLOSED-EMPTY`
because the defensible bar-size range and the useful range do not overlap — an approximation-error
argument. I think the outcome is right and the mechanism is not: the task dies on **substrate**, one
gate earlier. **The reason matters for the ledger**, because `AVENUES.md`'s revisit rule turns on the
stated reason: a tape arriving would not fix a substrate problem, and "the approximation was too
poor" is a claim nobody will have measured. I have not measured any approximation error and am not
contradicting you about it — I am saying it is no longer the binding constraint.

## 3. `S2` is the cheapest sub-task, needs no constructed bars at all, and needs an owner

`S2` tests the confound **mechanism's footprint on the grid we already have**: per-bar statistics
weight unequal-activity bars equally, a volume clock equalises activity per bar, so if the mechanism
operates the settled finding must differ across activity strata measured on the wall-clock grid. It
constructs nothing, so **constraint 1 cannot kill it**. It reads
`workspace/strategy_research/scratch/geo_trades.json` — 21,954 trades, `tf ∈ {60: 16,984,
240: 4,970}`, four symbols, ts 2025-10-17 → 2026-09-22, carrying `r`, `mae`, `mfe`, `session`,
`regime`, `exitm`, `arm` `[measured: json.load + Counter]` — joined on `(symbol, tf, ts)` to
`csv/raw`'s volume column. One to two bursts.

**It is also the only trade-level artefact with timestamps on disk.** The sub-hourly verdict's
artefacts are aggregate-only: `workspace/focus/cells/MES_5m_27d.json` holds 191 per-strategy rows and
**no trades** `[measured: json.load → keys avg_loss, avg_win, clones, exec_tf, exp, group, id,
maxdd, n, pf, rr, t, tf, win, win_hi, win_lo]`, so that target needs a 13,235-strategy-per-cell sweep
re-run.

**Two rulings I need.** (a) **Who owns `S2`?** It reads R3's target artefact and depends on R1's
`MGR-T13` norm, while `BOARD.md` §2 splits gate-ownership (R1) from target-ownership (R3).
(b) **If `MAIN-01` closes, does `S2` survive it?** My recommendation is that it should, re-filed under
the board task that already owns the volume-normalisation question at the same join — R1's, per
ADJ-10d. Its raw form is partly pre-answered (activity is largely time of day, and `BRIEF.md` rule 6
already refutes hours filters), so the content is in the **time-of-day-residualised** stratum, which
is exactly the distinction that task was promoted to settle, and R1's binding constraint there —
both axes take the time-of-day norm or neither does — applies verbatim.

## 4. The verdict vocabulary has no shape for what I am recommending

`PIPELINE.md` §1's verdicts are whole-avenue. I am recommending a **split**: `CLOSED-EMPTY` on the
minute-snapped construction (substrate — and a tape would not fix it, so **not** `DEFERRED`), while
the tape-blocked schemes stay `DEFERRED` under `BLOCK-SUBBAR` (that reason *can* change), and one
sub-task moves to another board task. Only discovery writes `AVENUES.md` and only you write
`BOARD.md`, so I cannot record this. **Which single verdict should the ledger carry, so the avenue is
reopenable on the right grounds rather than the wrong ones?**

---

## Three smaller things, none needing a ruling

- **A 1-minute store reconciliation is a genuine gap.** `MGR-T6` is scoped to the overlap, but
  `BRIEF.md`'s table is 60m only and its own condition 2 says not to assume it generalises.
  `MAIN-01`'s substrate is the *union of both stores at 1 minute*, and `R-7` forbids pooling them
  inside one statistic. The 1m overlap is 2,812 bars for MGC — cheap. It is `S0(c)` in my scope; if
  you would rather it extend `MGR-T6`, that works too.
- **A `D46`-class instance, described and not numbered per `R-9`.** `metrics.py:31` comments "*Bars
  per year* used to annualise the Sharpe/Sortino" above `TRADING_DAYS_PER_YEAR = 252`, but the code
  computes `per_year = m.trades_per_calendar_day * TRADING_DAYS_PER_YEAR` `[:214-215]` from **trade
  timestamps** `[:199-208]`. So the annualisation does *not* scale by bar count and is clock-robust;
  `MAIN_TASKS.md` lists it as an architecture cost on the strength of the comment. Same shape as
  `D46`: a documented input the code does not read. `costs.py` likewise has **zero** `minutes`
  references `[measured: grep -c → 0]`, so two of discovery's four named architecture costs are not
  real. That is the cheap half of "the price of changing it" and it is now on disk in my §2.4.
- **A silent bar-loss path nobody has named, and it is a fifth false-null mechanism.**
  `BarSeries.append` raises on a duration mismatch `[repo-verified: futures_agents/data/bars.py:
  192-195]` but on an **equal timestamp** silently replaces: "`# Same bucket: replace`" →
  `self._bars[-1] = b; return` `[:203-207]`, and it does not enforce contiguity. So **any two snapped
  volume-bar boundaries landing in the same minute collapse into one bar, with no warning** — making
  the fine end of the bar-size range a correctness failure, not an accuracy one. Its signature is an
  attenuated or exact-zero difference, indistinguishable from this programme's settled nulls, which
  is the same shape as `D38`, `D42`, `D44` and `D48`. I am describing it rather than naming a number,
  per `R-9`. It is `S1a`'s subject and the floor it computes is exact and needs no tape.

**Not asked, deliberately.** I did not re-ask the expressibility question (constraint 3), did not
rescope to range bars (constraint 2), ran no sweep, computed no expectancy, z or t, and wrote nothing
under `csv/` or `workspace/strategy_research/`.
