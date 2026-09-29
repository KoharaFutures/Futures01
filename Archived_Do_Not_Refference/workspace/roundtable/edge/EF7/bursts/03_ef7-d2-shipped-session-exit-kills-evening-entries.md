# EF7 burst 03 — EF7-D2: the shipped session exit closes an evening entry on its entry bar

Found while building the *control* for "the shipped exit is inert under `allow_overnight=True`".
The control failed, and it failed for a reason that is more interesting than the thing it was
controlling for.

## The arithmetic

`futures_agents/backtest/engine.py:470-473`:

```python
if exit_model.exit_at_session_close and not self.allow_overnight:
    elapsed = minutes_since_open(bar.ts, spec.rth_open) + bar.minutes
    if elapsed >= self._rth_minutes:
        return self._close(pos, i, bar, bar.close, ExitReason.SESSION_CLOSE)
```

`minutes_since_open` is measured from the RTH open **of the bar's own calendar date**
(`futures_agents/timeutil.py:158-166`) and is never clamped. For MGC, `_rth_minutes` = 310
(08:20→13:30). So `elapsed >= 310` reduces to *the bar opens at or after 12:30 ET* — and it stays
true for the whole evening:

`[measured: minutes_since_open(ts,"08:20") + 60, MGC]`

| bar opens (ET) | elapsed | fires? |
|---|---|---|
| 02:00 | −320 | no |
| 08:00 | 40 | no |
| 12:00 | 280 | no |
| 13:00 | 340 | **yes** |
| 16:00 | 520 | **yes** |
| 19:00 | 700 | **yes** |
| 23:00 | 940 | **yes** |

It goes negative again after midnight, so 00:00–12:29 ET holds normally.

## The consequence, measured

A position entered in the evening session is closed on its **entry bar** — one bar held, a full
round turn paid. On a two-cycle fixture with `rth_only=False`:

```
entry 06-09 19:00  exit 06-09 19:00  SESSION_CLOSE  bars=1
entry 06-09 20:00  exit 06-09 20:00  SESSION_CLOSE  bars=1
...
entry 06-10 00:00  exit 06-10 13:00  SESSION_CLOSE  bars=14   <- post-midnight holds
```
`bars_held` distribution: **{1: 17, 14: 2}**, 19 trades, all `SESSION_CLOSE`.

## Why it matters to this programme specifically

1. **It strengthens `BRIEF.md`'s point 2 and changes its wording.** The brief says every prior
   evaluation "was flat by its contract's RTH close." That understates it: the shipped engine
   **cannot carry an overnight position at all** — an evening entry does not reach a second bar.
2. **It contaminates any arm-A baseline on a `rth_only=False` population.** Arm A there is not
   "intraday trading"; it is "intraday trading plus a tranche of one-bar trades each paying a full
   round turn." A window-rule-vs-shipped comparison on that population measures this artefact as
   much as it measures the rule.
3. **It bears on D24.** D24 records that `rth_only=False` buys 2–4× the sample while *costing*
   expectancy in every paired test. A mechanism that turns every evening entry into a one-bar
   round-turn-paying trade is a candidate explanation that has nothing to do with overnight
   liquidity. I am not claiming D24 is wrong — I have not re-measured it — but the paired tests
   behind it should be re-read with this in front of them. **Routed to the manager.**

Regression test: `tests/test_ef7_session_window.py::test_ef7_d2_shipped_session_exit_closes_an_evening_entry_on_its_entry_bar`,
which also asserts the post-midnight half (those entries *are* held) so the mechanism is pinned
rather than just the symptom.

Not fixed. `futures_agents/` is not mine to change here and `SessionWindowEngine` forces
`allow_overnight=True`, which makes the branch dead inside the window rule. Reported instead.
