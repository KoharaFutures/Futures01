# EF6 burst 02 — the 18:00→16:00 window as a bar-level predicate, and the timeframes it forbids

**Built:** `EF6/code/window.py` — `in_window`, `bar_status`, `window_mask`,
`signal_mask`, `cycle_id`, `straddle_report`. **Scope:** EF1 owns the *engine* rule. This is the
*accounting* predicate every EF6 control and census applies, so a placebo, a firing rate and a
realised backtest are all counted over the same bars. If the two ever disagree, the control is
measured on a different universe from the thing it controls.

## The rule is the complement of an existing session, not a new convention

`timeutil.SESSIONS` already names the forbidden span exactly: `POST_CLOSE = 16:00 → 18:00`
`[repo-verified: futures_agents/timeutil.py:120-122]`. So `in_window(ts) ==
(classify_session(ts) != "POST_CLOSE")`, asserted on every 5-minute stamp of a 24-hour day in
`tests/test_ef6_guards.py::test_window_is_exactly_the_complement_of_post_close`.

**Entries fill at the *next* bar's open** `[repo-verified: engine.py:293-299 → `_open_position`
fills at `bar.open`; signals are queued into `pending` at bar *i* and filled at bar *i+1*,
engine.py:317-318, 287-291]`. So legality is a property of bar **i+1**, not bar **i**. A census
that forgets this over-counts eligible signals at the last slot before 16:00. `signal_mask` is
`window_mask` shifted by one, taken from the **actual next bar in the series**, not from
`ts + minutes` — the 17:00–18:00 maintenance break means the bar after a 16:00 60m bar is
usually 18:00, and arithmetic on `ts + minutes` gets that wrong.

## Measured: what fraction of the substrate the rule admits

`[measured: python3 -c "... straddle_report(archive.load(sym,tf).bars, tf) ..." over
data/archive, all 4 symbols × 7 timeframes, 2026-09-27]`

| tf | n bars | IN window | OUT (16:00–18:00) | **STRADDLE** | % signal-eligible | expressible |
|---|---|---|---|---|---|---|
| 1m | 6,845–6,881 | 6,549–6,585 | 296–297 | 0 | 95.65–95.68 | **yes** |
| 5m | 11,182–11,216 | 10,689–10,721 | 493–495 | 0 | 95.58–95.59 | **yes** |
| 15m | 3,744–3,746 | 3,579 | 165–167 | 0 | 95.52–95.57 | **yes** |
| 30m | 1,873–1,875 | 1,790 | 83–85 | 0 | 95.41–95.52 | **yes** |
| 60m | 10,934–11,297 | 10,460–10,802 | 474–497 | 0 | 95.59–95.66 | **yes** |
| **240m** | 2,990–3,052 | 2,427–2,466 | **0** | **563–586, all stamped 16:00** | 80.80–81.17 | **NO** |
| **1440m** | 1,863–4,008 | **0** | 0 | **all of them, stamped 00:00** | **0.00** | **NO** |
| 120m (resampled from the 60m archive) | 5,742–5,899 | 5,272–5,411 | 470–488 | **0** | — | **yes** |
| 180m (resampled from the 60m archive) | 3,838–3,933 | 3,368–3,445 | 0 | **470–488, all stamped 15:00** | — | **NO** |

Identical on all four symbols. The 5–15m/30m/60m timeframes lose ~4.4% of bars to the rule and
lose nothing to ambiguity.

## The finding: **240m cannot express this programme's own rule, and 120m can**

A 240m bar stamped 16:00 ET spans **16:00 → 20:00**. Two of those hours are forbidden and two
are legal, and `align_bucket` puts multi-hour buckets on a midnight grid
`[repo-verified: futures_agents/data/bars.py:150-154 → "Align multi-hour buckets to midnight so
4h bars fall on 00/04/08/12/16/20"]`. So the 18:00 reopen is **not on the 4-hour grid at all**,
and both available choices are wrong:

* **exclude the 16:00 bar** → you discard the Globex reopen, which is the one regime
  `EDGE_BRIEF.md:26-30` says is genuinely unmeasured and is the entire stated opportunity;
* **include it** → you hold through 16:00–18:00, which the rule forbids.

**The arithmetic behind it, which generalises.** The window is 22 hours = **1320 minutes**, and
`1320 = 2³·3·5·11`. A base timeframe can tile the window iff it divides 1320:

```
divisors of 1320 in our grid:  1, 5, 15, 30, 60, 120       ✓
not divisors:                  240 (1320/240 = 5.5), 1440   ✗
```

**Constructive fix, and it costs nothing.** `120m` divides the window exactly 11 times, resamples
from the same 60m archive, carries the same **718.88-day span**, and measures **0 straddles on
all four symbols** `[measured: archive.load(sym,60).resample(120, keep_partial=False) →
straddle_report, MGC 5,899 bars / 5,411 IN / 488 OUT / 0 STRADDLE; MCL 5,742/5,272/470/0;
MES 5,894/5,407/487/0; MNQ 5,894/5,407/487/0]`. **180m does not work** — its 15:00 bar spans
15:00–18:00 and straddles 16:00.

**Second fix, equally valid and probably better.** The straddle is a property of the **base**
timeframe — the grid the engine steps on — not of the timeframe a thesis is read on. `run_many`
iterates `self.frame.base.bars` `[repo-verified: engine.py:267-283]` and `Strategy.evaluate`
reads higher timeframes out of the snapshot. So a **240m thesis on a 60m base frame** is fully
expressible: the position opens and closes on 60m boundaries, which land exactly on 16:00 and
18:00, while the confluence is read at 240m. The existing sweeps do not do this — `toolkit._series`
loads the series *at* the primary timeframe, so base == primary and a 240m strategy steps in 240m
bars. **Recommendation to EF2–EF5: never make 240m or 1440m the base of a frame under this rule.
Use them as reading timeframes above a 60m or 120m base.**

## Consequence for the SWING setting specifically

`EDGE_BRIEF.md` puts swing at 60m/240m. Measured: **60m is expressible, 240m is not.** So the
swing setting is 60m and 120m, or 60m-based frames that read 240m. A swing top 10 whose rows
have `primary_tf = 240` and a 240m base is not a top 10 under this programme's rule — it is a
top 10 under a different rule that holds through the settlement break.

## Consequence for DAILY, which the brief's substrate table undersells and oversells at once

MGC daily is **15.98 years** and MES/MNQ daily **7.40 years** (burst 01) — by far the deepest
substrate here, and the only cell where a *wide* search is affordable (MGC daily at an assumed
SR of 1.0 affords n = 2,944). But every daily bar is stamped 00:00 ET and spans 24 hours, so
**100% of them straddle**, and the maximum hold the rule permits is 22 of those 24 hours. A daily
strategy under this rule is a 1440-minute *signal* with a sub-bar hold, which only works on a
finer base. It is not excluded — it is a **60m-base frame reading a 1440m timeframe**, and that
is a different object from "a daily strategy", so it must not be labelled as one.

## Anti-overfitting and correctness checks in this burst

| hazard | checked | finding |
|---|---|---|
| look-ahead in the predicate | yes | `in_window` and `bar_status` read only the bar's own timestamp and duration. `signal_mask` looks *forward* one bar — deliberately, because that is where the fill happens, and it uses no price from that bar |
| next-bar arithmetic vs the actual series | yes | `signal_mask` indexes the real next bar. `ts + minutes` is wrong across the 17:00–18:00 break, where the 60m series has only 6 bars against ~490 per other hour `[measured: ET time-of-day histogram, MGC 60m]` |
| a straddle silently counted as tradeable | yes | `bar_status` returns a third value and `window_mask` treats STRADDLE as **False**. Nothing in EF6 trades a straddle bar |
| convention drift vs `timeutil.trading_day` | yes | `trading_day` rolls at 18:00 to the CME's *17:00* close convention and would assign the 16:00–18:00 bars to the cycle that must be flat. `cycle_id` assigns them forward. Both are correct for their own purpose and they are **not** interchangeable; the test pins the difference |
| repainting / future data | n/a | no indicator touched |
