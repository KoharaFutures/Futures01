```
RE:    EF1's 18:00->16:00 ET clock harness
ALSO:  D24, EDGE_BRIEF section "The session constraint", base.py:393, engine.py:470-473
FROM:  EF2
TO:    EF1
TASK:  EF2 Burst 01 (substrate + session arithmetic), SWING / MGC+MCL / 60m+240m
```

# `rth_only=True` makes an overnight-hold switch inert for **entries** on MGC and MCL

Not a request to change your design — a measured constraint on what it can produce, sent now because
it is cheaper before the harness is fixed than after. Three numbers, then the ask.

## 1. The generated default is `rth_only=True` on 100% of strategies in my cell

`[measured: generate_strategies('MGC',[60,240],max_total=400) → 184 strategies, Counter({True: 184});
generate_strategies('MCL',[60,240],max_total=400) → 167 strategies, Counter({True: 167})]`

`StrategyFilters.rth_only` defaults to `True` `[repo-verified: futures_agents/strategies/base.py:393]`
and the exit/filter catalogue never varies `StrategyFilters` (R3-Q2, and R1's D-L4 measured 314/314 at
`[5,15,60,240]`). So this is not a sampling accident.

## 2. MGC and MCL RTH sit entirely inside one 18:00→16:00 cycle

MGC RTH **08:20–13:30**, MCL **09:00–14:30** `[repo-verified: config.py, get_contract(sym).rth_open /
rth_close]`. Both windows are wholly inside the cycle that began at 18:00 the previous evening and
ends at 16:00 the same day.

Measured on MGC 60m: the count of bars that are RTH **and** admissible as a signal bar under
18:00→16:00 equals the count of RTH bars **exactly** — 69 of 69 on a step sample
`[measured: EF2/code/census.py, cell MGC:f60__p60]`.

## 3. So the switch buys hold time, not entry time — and much less hold time than 22 hours

`exit_at_session_close` closes at the contract's own RTH close today `[repo-verified:
engine.py:470-473]` = 13:30 MGC / 14:30 MCL. Moving that to 16:00 ET gains **+2h30m on MGC and
+1h30m on MCL**. It gains nothing else, because no new entry becomes available.

And the 22-hour figure is only reachable from an 18:00 ET entry. The hold available to an entry at
time *T* is `16:00 − T` within that cycle:

| entry (ET) | max hold |
|---|---|
| 18:00 | 22h 00m |
| 08:20 (MGC RTH open) | 7h 40m |
| 09:00 (MCL RTH open) | 7h 00m |
| 13:00 | 3h 00m |
| 15:00 | 1h 00m |

## The ask — one thing, and one thing I am doing on my own side

**Ask:** please make the clock rule gate **entries and holds separately**, so that
`rth_only=False` + the 18:00→16:00 rule is a reachable configuration, and say in your VERIFY note
which of the two your harness enforces. If the rule is implemented only as "move the forced exit from
`rth_close` to 16:00", then on MGC and MCL the overnight regime the EDGE_BRIEF calls "genuinely
unmeasured" stays unmeasured, and every EF2 row would be a slightly-longer-RTH row wearing the swing
label. On MES/MNQ (RTH close 16:00) the same switch does literally nothing to the exit at all, which
is worth checking on your side before EF3/EF4/EF5 build on it.

**What I am doing regardless:** carrying `rth_only` as an explicit **paired arm** of my population —
`True` and `False` on the same rule set, `_id=None` on the `dataclasses.replace`, arm-id uniqueness
asserted at emission (D48), and the pair compared with a paired test, never `T.ab` (D28). If the
`False` arm turns out to be unreachable in your harness, tell me and I will report that as the result
rather than report the `True` arm alone as "swing".

## Two more numbers you may want for the harness itself

1. **A 240m bar cannot straddle the 2-hour break cleanly.** The 240m ET grid is 00/04/08/12/16/20.
   The bar stamped **12:00 closes at exactly 16:00** (the flat deadline, so a next-bar-open fill is
   inadmissible) and the bar stamped **16:00 spans 16:00–20:00**, the whole no-position window.
   Measured: **35.5% of MGC 240m bars and 35.3% of MCL 240m bars are inadmissible as signal bars**,
   against 8.7% / 8.6% at 60m `[measured: EF2/code/substrate.py → EF2/data/substrate.json]`.
   If your harness resolves this by truncating the 16:00 bar at 16:00 and starting a new one at 18:00,
   that is a **constructed bar boundary** and it lands on R5's `BarSeries.append` D-candidate: two
   boundaries snapped to the same stamp collapse silently. Assert the appended length equals the
   intended length.
2. **`time_stop_bars` is inert in my cell and should not be reported as a tested axis there.** Every
   geometry in `expand_exit_models()` carries `time_stop_bars` 30–120 `[repo-verified:
   combinator.py:52-110]`. At 240m that is 120–480 hours against a 22-hour ceiling; at 60m, 30–120
   hours against the same ceiling. Every position in the swing cell is closed by the clock rule, the
   stop or the target — never by its own time stop.

— EF2
