"""EF4 - the declared population. Size fixed in code before any measurement.

Two tracks of deliberately different width, because the *difference between them* is
the deliverable: on a 0.1585-year span the deflation threshold is the binding
constraint, `free_t = sqrt(2 ln n)`, and the only lever an agent controls is n.

    Track A  - 36 arms.  6 named, pre-registered hypotheses x 2 symbols x 3 timeframes,
               ONE fixed exit geometry.  free_t = 2.676.
    Track B  - the broad census-gated screen.  Exact size printed before the run.
               free_t stated with it.

Both share one exit geometry. **Exits are not searched.** That is the single cheapest
anti-overfitting decision available here: the repo's own catalogue offers 11 geometries
and sweeping them would multiply n by 11 and add 1.2 t-units to the threshold for a
dimension BRIEF rule 3 already says does not move expectancy.

## Declared construction rules (fixed before measuring)

1. **Census gate.** A condition enters a pool only if its verdict in THAT cell is LIVE or
   THIN. VOID and NEAR_VOID are excluded per (symbol, timeframe), never globally.
2. **Rate band.** Signals 2%-60%; filters 2%-90%. The upper bound removes the always-on
   degenerates (burst 04): a filter passing on 99% of bars cannot veto and inflates the
   apparent condition count.
3. **Duplicate halves dropped:** `macd_hist_direction` (= `macd_directional`) and
   `regime_matches_direction` (= `regime_trending`), Jaccard 1.0 in all six cells.
4. **Two signals and one filter is the ceiling** (BRIEF rule 1). Singles and
   distinct-group pairs only; 0 or 1 filter.
5. **`rth_only=False` on every arm.** The default is `True` `[repo-verified: base.py:393]`,
   which would veto every overnight bar and reduce this cell to 22-24% of its bars - and
   the overnight half is the regime this programme exists to measure. D24 measured
   `rth_only=False` as buying sample and costing expectancy, but it measured it under the
   OLD regime where the position was flattened at the contract's RTH close, so that result
   does not transfer and is not assumed here.
6. **`exit_at_session_close=False`** on the exit, because the harness's 16:00 ET flat is
   the session rule and the engine's own RTH-close exit is the wrong clock (13:30 MGC,
   14:30 MCL).
7. **`_id=None` on every `dataclasses.replace`** and an arm-id uniqueness assertion at
   emission (D48).

## The fixed exit, and why these numbers

`ExitModel(StopKind.ATR, 1.0, targets_r=(1.5,), scale_out=(1.0,), breakeven_at_r=None,
time_stop_bars=24, exit_at_session_close=False)`

- **ATR 1.0, not tighter.** BRIEF rule 4 says never tighter than ~0.5 ATR, and burst 02
  shows 0.5 ATR at 5m is *below* `min_stop_ticks` on both contracts (23.8 ticks vs a
  25-tick floor on MGC, 10.2 vs 15 on MCL), so a 0.5-ATR request is silently widened to
  the floor `[repo-verified: base.py:313-314]`. At 1.0 ATR the floor does not bind
  (47.5 ticks MGC 5m, 20.4 MCL 5m) and the stop the strategy asked for is the stop it gets.
- **One target, full size, no scale-out and no breakeven move.** Then net R per trade is a
  single unambiguous number and the R series' t-statistic means what it says. Scale-outs
  make `net_r` a weighted average of legs and inflate the apparent Sharpe by shrinking
  variance without adding edge.
- **`time_stop_bars=24`** in the strategy's OWN bars `[repo-verified: engine.py:404-406]`
  = 2h at 5m, 6h at 15m, 12h at 30m. All three fit inside the 22-hour maximum hold, so
  the time stop is live at all three timeframes rather than inert at one of them.

## Track A - the six pre-registered hypotheses

Each is one named trading idea from the mandate, chosen for a reason stated BEFORE
measuring, and each is a single arm per cell - not a family to be searched.

| id | signal(s) | filter | why pre-registered |
|---|---|---|---|
| `A1_ON_SWEEP` | `overnight_sweep` | none | The ONH/ONL is the level this programme can newly trade against: holding through Globex was structurally impossible in all ~2.97M prior evaluations. Fires 1.1-3.3%. |
| `A2_PD_SWEEP` | `prior_day_sweep` | none | Previous-day levels, the most-cited intraday reference. Fires 3.1-10.4%. |
| `A3_VA_EDGE` | `value_area_edge` | none | The only `profile` condition with a rate low enough to be informative (1.9-5.2%); the other five fire on 20-84% of bars. |
| `A4_VWAP_BAND` | `vwap_band1_bounce` | none | Mean reversion to VWAP's first band; 11-25%, and its stop twin `StopKind.VWAP_BAND` is D45's open question. |
| `A5_ORB` | `opening_range_breakout` | `after_opening_range` | A **replication attempt of a published negative.** R6's audit today found the ORB conclusion STANDS at tf in {5,15}. Pre-registered expectation: negative. A pre-registered prediction of failure is still a prediction. |
| `A6_ON_COMPRESSION` | `prior_day_breakout` | `volatility_compressed` | The newly measurable regime: `volatility_compressed` fires 98-100% outside RTH, so under the old rules this pairing could barely exist. |
"""
from __future__ import annotations

import itertools
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

ROOT = Path("/home/user/Futures01")
sys.path.insert(0, str(ROOT))

from futures_agents.schema import Direction                     # noqa: E402
from futures_agents.strategies.base import (ConditionKind, ExitModel, StopKind,
                                            Strategy, StrategyFilters)  # noqa: E402
from futures_agents.strategies.library import CONDITIONS         # noqa: E402

CENSUS = ROOT / "workspace/roundtable/edge/EF4/out/census.json"

DUP_HALVES = {"macd_hist_direction", "regime_matches_direction"}
SIGNAL_RATE = (0.02, 0.60)
FILTER_RATE = (0.02, 0.90)

FIXED_EXIT = ExitModel(
    stop_kind=StopKind.ATR, stop_mult=1.0,
    targets_r=(1.5,), scale_out=(1.0,),
    breakeven_at_r=None, trail_atr_mult=None,
    time_stop_bars=24, exit_at_session_close=False,
)
OPEN_FILTERS = StrategyFilters(rth_only=False)

TRACK_A: Sequence[Tuple[str, Tuple[str, ...], Tuple[str, ...], str]] = (
    ("A1_ON_SWEEP", ("overnight_sweep",), (), "LIQUIDITY"),
    ("A2_PD_SWEEP", ("prior_day_sweep",), (), "LIQUIDITY"),
    ("A3_VA_EDGE", ("value_area_edge",), (), "VOLUME_PROFILE"),
    ("A4_VWAP_BAND", ("vwap_band1_bounce",), (), "VWAP"),
    ("A5_ORB", ("opening_range_breakout",), ("after_opening_range",), "OPENING_RANGE"),
    ("A6_ON_COMPRESSION", ("prior_day_breakout",), ("volatility_compressed",), "BREAKOUT"),
)

#: Track B's filter slot. Declared here, before measuring, and chosen for MANDATE
#: coverage - one filter per axis the mandate names - not for anything observed.
TRACK_B_FILTERS: Sequence[str] = (
    "volatility_normal",       # volatility regime
    "relative_volume_high",    # volume regime
    "adx_trending",            # trend strength
    "after_opening_range",     # time of day / session location
    "away_from_hvn",           # market-profile location
    "volume_not_thin",         # liquidity
)


def census_pools(cell: str) -> Tuple[List[dict], List[dict]]:
    rows = [r for r in json.loads(CENSUS.read_text()) if r["cell"] == cell]
    sig = [r for r in rows
           if r["kind"] == "SIGNAL" and r["verdict"] in ("LIVE", "THIN")
           and r["condition"] not in DUP_HALVES
           and SIGNAL_RATE[0] <= r["rate"] <= SIGNAL_RATE[1]]
    flt = [r for r in rows
           if r["kind"] == "FILTER" and r["verdict"] in ("LIVE", "THIN")
           and r["condition"] not in DUP_HALVES
           and FILTER_RATE[0] <= r["rate"] <= FILTER_RATE[1]]
    return sorted(sig, key=lambda r: r["condition"]), sorted(flt, key=lambda r: r["condition"])


def _mk(symbol: str, tf: int, name: str, group: str,
        signals: Sequence[str], filters: Sequence[str]) -> Strategy:
    conds = tuple(CONDITIONS[n] for n in list(signals) + list(filters))
    return Strategy(
        name=name, group=group, symbol=symbol, primary_tf=tf,
        conditions=conds, exit=FIXED_EXIT, filters=OPEN_FILTERS,
        allowed_directions=frozenset({Direction.LONG, Direction.SHORT}),
        confirm_tfs=(), description=f"EF4 {name}",
        _id=None,
    )


def build_track_a(symbol: str, tf: int) -> List[Strategy]:
    out = []
    for aid, sigs, flts, grp in TRACK_A:
        out.append(_mk(symbol, tf, f"{aid}", grp, sigs, flts))
    return out


def build_track_b(symbol: str, tf: int) -> List[Strategy]:
    cell = f"{symbol}-{tf}m"
    sig, _ = census_pools(cell)
    names = [r["condition"] for r in sig]
    grp = {r["condition"]: r["group"] for r in sig}
    combos: List[Tuple[str, ...]] = [(n,) for n in names]
    combos += [(a, b) for a, b in itertools.combinations(names, 2) if grp[a] != grp[b]]
    filters: List[Tuple[str, ...]] = [()] + [(f,) for f in TRACK_B_FILTERS
                                             if f in CONDITIONS]
    out = []
    for c in combos:
        for f in filters:
            nm = "+".join(c) + ("|" + f[0] if f else "")
            out.append(_mk(symbol, tf, nm, "EF4_SCREEN", c, f))
    return out


def assert_unique(strats: Sequence[Strategy], label: str) -> None:
    """D48 guard. Two arms colliding into one id makes their difference exactly zero."""
    ids = [s.strategy_id for s in strats]
    if len(set(ids)) != len(ids):
        from collections import Counter
        dup = [k for k, v in Counter(ids).items() if v > 1]
        raise AssertionError(f"{label}: {len(ids) - len(set(ids))} arm-id collisions, "
                             f"e.g. {dup[:3]}")


def main() -> None:
    import math
    cells = [(s, tf) for s in ("MGC", "MCL") for tf in (5, 15, 30)]
    tot_a = tot_b = 0
    print("DECLARED POPULATION - printed before any backtest is run\n")
    for sym, tf in cells:
        a = build_track_a(sym, tf)
        b = build_track_b(sym, tf)
        assert_unique(a, f"A {sym} {tf}m")
        assert_unique(b, f"B {sym} {tf}m")
        sig, flt = census_pools(f"{sym}-{tf}m")
        tot_a += len(a); tot_b += len(b)
        print(f"{sym} {tf:>2}m  eligible signals={len(sig):<3} "
              f"TrackA={len(a):<3} TrackB={len(b):<5}")
    print(f"\nTrack A total n = {tot_a}   free_t = {math.sqrt(2*math.log(tot_a)):.3f}")
    print(f"Track B total n = {tot_b}   free_t = {math.sqrt(2*math.log(tot_b)):.3f}")
    print(f"combined      n = {tot_a+tot_b}   free_t = "
          f"{math.sqrt(2*math.log(tot_a+tot_b)):.3f}")
    print(f"\nSharpe required on 0.1585y: A {math.sqrt(2*math.log(tot_a))/0.398:.2f}   "
          f"B {math.sqrt(2*math.log(tot_b))/0.398:.2f}")
    (ROOT / "workspace/roundtable/edge/EF4/out/population_size.json").write_text(
        json.dumps({"track_a": tot_a, "track_b": tot_b,
                    "free_t_a": math.sqrt(2*math.log(tot_a)),
                    "free_t_b": math.sqrt(2*math.log(tot_b))}, indent=2))


if __name__ == "__main__":
    main()
