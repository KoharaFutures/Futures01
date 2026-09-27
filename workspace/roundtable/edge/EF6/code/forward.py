"""EF6 deliverable 4 — the strictly-causal forward roll, with the two comparisons
that made the old result interpretable.

The programme has already measured this once and the answer was negative:
trading last period's top 10 returned **−0.0155R against a −0.0104R null** and
**underperformed trading the whole qualifying universe** (+0.022R vs +0.057R)
`[repo-verified: workspace/studies/RANKING_FINDINGS.md:282-295]`. *Selecting was
worse than not selecting.* A list ranked in-sample and reported without this
test is the exact artefact this repo has been burned by, so this is the gate
every EF2-EF5 top 10 passes through.

## The design

Rank on the trailing window **ending the instant the trading period starts**,
trade the top k for the period, roll forward. No bar used for ranking is ever
used for scoring, and that is asserted per fold rather than trusted.

Four arms per fold, because one number is not interpretable:

1. **top-k** — what a trader following the list actually earns.
2. **universe** — trading every qualifier instead of picking. If this beats
   top-k, selection destroyed value, which is what happened last time.
3. **random-k** — k qualifiers drawn at random. Separates "ranking is
   uninformative" from "a k-sized portfolio is worse than a wide one". The prior
   study did not have this arm and the two explanations were not separated.
4. **permutation null** — realised R reassigned within (exit geometry x time
   block), which holds every strategy's trade count, every trade's timestamp and
   the pooled R of every geometry in every block fixed, and destroys only
   whether a given rule set is better than its neighbours. Method taken from
   `workspace/strategy_research/scratch/w4_core.py:permute_r` and reimplemented
   here so this module has no dependency on a scratch directory.

## Two things this adds that the prior study did not have

**The ranking criterion is a variable, not a constant.** The prior roll ranked
on **expectancy** alone. `EDGE_BRIEF.md` and the EF6 mandate say to rank on
*durability* — expectancy in R with a sample-size penalty, the t-statistic of
the R series, drawdown and consecutive losses. Whether that criterion survives
forward where expectancy did not is an open, answerable question, and
:func:`roll` takes ``criterion`` so both are measured on the same folds.

**Fold boundaries fall on 18:00->16:00 cycle edges.** A boundary in the middle of
a session splits a strategy's own holding period across the rank/score line,
which is a soft look-ahead: the score window inherits positions the rank window
opened. Boundaries are snapped to 18:00 ET.

## The ledger format EF2-EF5 emit

```json
{"symbol": "MGC", "setting": "swing", "base_tf": 60,
 "substrate": "data/archive", "screened": 812,
 "t0": <epoch>, "t1": <epoch>,
 "strategies": {"<strategy_id>": {
     "meta": {"group": "...", "stop": "ATRx1.5", "target": "3.0R",
              "primary_tf": 60},
     "trades": [[entry_epoch, exit_epoch, +1|-1, net_r], ...]}}}
```

``net_r`` must be **net of costs**. Gross R here would be a different, easier
question, and MCL is cost-fragile — costs flip 8 of 183 MCL 60m rows from
positive gross to negative net against 1 of 259 for MGC.
"""

from __future__ import annotations

import json
import math
import os
from datetime import datetime, time, timedelta
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from futures_agents.timeutil import ET, to_et

import deflation as D

__all__ = [
    "DAY", "Ledger", "cycle_boundaries", "rank_keys", "roll", "roll_report",
]

DAY = 86400.0


# --------------------------------------------------------------------------
# Ledger
# --------------------------------------------------------------------------

class Ledger:
    """A (symbol, setting) trade ledger flattened into arrays."""

    def __init__(self, doc: dict):
        self.symbol = doc["symbol"]
        self.setting = doc.get("setting", "")
        self.base_tf = int(doc.get("base_tf", 0))
        self.substrate = doc.get("substrate", "unknown")
        self.screened = int(doc.get("screened", 0))
        sids = sorted(doc["strategies"])
        self.sids = sids
        self.idx = {s: i for i, s in enumerate(sids)}
        self.meta = {s: doc["strategies"][s].get("meta", {}) for s in sids}
        sid_i, ts, tex, r, geom, dr = [], [], [], [], [], []
        gmap: Dict[Tuple, int] = {}
        for s in sids:
            m = self.meta[s]
            g = (m.get("stop"), m.get("target"))
            gi = gmap.setdefault(g, len(gmap))
            for t in doc["strategies"][s]["trades"]:
                sid_i.append(self.idx[s])
                ts.append(float(t[0]))
                tex.append(float(t[1]))
                dr.append(int(t[2]))
                r.append(float(t[3]))
                geom.append(gi)
        self.sid_i = np.asarray(sid_i, dtype=np.int32)
        self.ts = np.asarray(ts, dtype=np.float64)
        self.tex = np.asarray(tex, dtype=np.float64)
        self.dir = np.asarray(dr, dtype=np.int8)
        self.r = np.asarray(r, dtype=np.float64)
        self.geom = np.asarray(geom, dtype=np.int32)
        self.S = len(sids)
        self.t0 = float(doc.get("t0", self.ts.min() if len(self.ts) else 0.0))
        self.t1 = float(doc.get("t1", self.tex.max() if len(self.tex) else 0.0))

    # ---- window arithmetic -------------------------------------------
    def measure(self, lo: float, hi: float, *, r: Optional[np.ndarray] = None,
                floor: int = 20, collapse: bool = True) -> dict:
        """Per-strategy stats over ``[lo, hi)`` by **entry** timestamp.

        Clone collapse is on by default. Without it a top 10 is routinely the
        top 2 listed ten times - the prior study measured MES 60m over 274 days
        listing the same TREND rule set four times
        `[repo-verified: w4_core.py:76-82]`.
        """
        rv_all = self.r if r is None else r
        m = (self.ts >= lo) & (self.ts < hi)
        sid, rv = self.sid_i[m], rv_all[m]
        n = np.bincount(sid, minlength=self.S)
        s1 = np.bincount(sid, weights=rv, minlength=self.S)
        s2 = np.bincount(sid, weights=rv * rv, minlength=self.S)
        w = np.bincount(sid, weights=(rv > 0).astype(float), minlength=self.S)
        with np.errstate(invalid="ignore", divide="ignore"):
            exp = np.where(n > 0, s1 / np.maximum(n, 1), np.nan)
            var = np.where(n > 1, (s2 - n * exp ** 2) / np.maximum(n - 1, 1), np.nan)
            t = np.where((n > 1) & (var > 0),
                         exp / np.sqrt(np.maximum(var, 1e-12) / np.maximum(n, 1)), 0.0)
        qual = n >= floor
        if collapse and qual.any():
            key = self.ts[m] * 2 + (self.dir[m] > 0)
            seen: Dict[int, int] = {}
            order = np.argsort(sid, kind="stable")
            ssid, skey = sid[order], key[order]
            edges = np.flatnonzero(np.r_[True, ssid[1:] != ssid[:-1], True])
            for a, b in zip(edges[:-1], edges[1:]):
                i = int(ssid[a])
                if not qual[i]:
                    continue
                fp = hash(skey[a:b].tobytes())
                if fp in seen:
                    qual[i] = False
                else:
                    seen[fp] = i
        return {"n": n, "exp": exp, "t": t,
                "win": np.where(n > 0, w / np.maximum(n, 1), np.nan),
                "sd": np.sqrt(np.where(np.isfinite(var), np.maximum(var, 0.0), np.nan)),
                "qual": qual, "sum_r": s1}

    def permute(self, rng: np.random.Generator, block_days: float = 30.0) -> np.ndarray:
        """Reassign realised R within (exit geometry x time block).

        Holds fixed: every strategy's trade count, every trade's timestamp, and
        the pooled R of every geometry inside every block - so the market's own
        month-to-month swings survive and only "is this rule set better than its
        neighbours" is destroyed. Blocking on time matters: without it the
        shuffle drags R across periods and the null acquires a different
        per-period baseline from the observation.
        """
        out = self.r.copy()
        blk = np.floor((self.ts - self.t1) / (block_days * DAY)).astype(np.int64)
        key = self.geom.astype(np.int64) * 1_000_003 + blk
        order = np.argsort(key, kind="stable")
        ks = key[order]
        edges = np.flatnonzero(np.r_[True, ks[1:] != ks[:-1], True])
        for a, b in zip(edges[:-1], edges[1:]):
            ix = order[a:b]
            if len(ix) > 1:
                out[ix] = self.r[ix[rng.permutation(len(ix))]]
        return out


# --------------------------------------------------------------------------
# Fold boundaries on 18:00 ET cycle edges
# --------------------------------------------------------------------------

def cycle_boundaries(t0: float, t1: float, trade_days: int) -> List[Tuple[float, float]]:
    """Consecutive non-overlapping periods whose edges fall at 18:00 ET.

    A boundary inside a session splits a holding period across the rank/score
    line, so the score window inherits a position the rank window opened. That
    is a soft look-ahead and it is avoidable for free.
    """
    def snap_up(ts: float) -> float:
        d = to_et(datetime.fromtimestamp(ts, tz=ET))
        b = datetime.combine(d.date(), time(18, 0), tzinfo=ET)
        if b.timestamp() < ts:
            b = b + timedelta(days=1)
        return b.timestamp()

    out: List[Tuple[float, float]] = []
    lo = snap_up(t0)
    while True:
        hi = snap_up(lo + trade_days * DAY)
        if hi > t1:
            break
        out.append((lo, hi))
        lo = hi
    return out


# --------------------------------------------------------------------------
# Ranking criteria
# --------------------------------------------------------------------------

def rank_keys(m: dict, criterion: str, *, floor: int = 20) -> np.ndarray:
    """Sort key (higher = better) for each strategy. NaN where not rankable.

    ``expectancy``  — mean net R. What the prior study ranked on, and what
                      failed forward.
    ``t``           — the t-statistic of the R series. Expectancy with the
                      sample size and the dispersion folded in.
    ``durability``  — the mandate's criterion: expectancy in R shrunk toward
                      zero by a sample-size penalty, then penalised for
                      dispersion. Implemented as
                      ``exp * n/(n + floor) / (1 + sd)``, which is a
                      James-Stein-flavoured shrink: a profit factor of 1.8 over
                      18 trades is shrunk by 18/38 = 0.47 while the same
                      expectancy over 200 trades keeps 0.91 of itself.
    """
    n, exp, t, sd = m["n"], m["exp"], m["t"], m["sd"]
    with np.errstate(invalid="ignore", divide="ignore"):
        if criterion == "expectancy":
            k = exp
        elif criterion == "t":
            k = t
        elif criterion == "durability":
            shrink = n / (n + float(floor))
            k = exp * shrink / (1.0 + np.where(np.isfinite(sd), sd, 0.0))
        else:
            raise ValueError(f"unknown criterion {criterion!r}")
    return np.where(m["qual"], k, np.nan)


def _order(keys: np.ndarray) -> np.ndarray:
    ix = np.flatnonzero(np.isfinite(keys))
    if len(ix) == 0:
        return ix
    return ix[np.argsort(-keys[ix], kind="stable")]


# --------------------------------------------------------------------------
# The roll
# --------------------------------------------------------------------------

def _pooled(m: dict, sel: Sequence[int]) -> Tuple[float, int]:
    sel = [i for i in sel if m["n"][i] > 0]
    if not sel:
        return float("nan"), 0
    num = float((m["exp"][sel] * m["n"][sel]).sum())
    den = float(m["n"][sel].sum())
    return (num / den if den else float("nan")), int(den)


def roll(led: Ledger, *, lookback_days: int, trade_days: int = 30,
         floor: int = 20, k: int = 10, criterion: str = "durability",
         nperm: int = 200, seed: int = 23, r: Optional[np.ndarray] = None) -> dict:
    """One forward roll. Returns per-fold detail and the four pooled arms."""
    rng = np.random.default_rng(seed)
    periods = cycle_boundaries(led.t0, led.t1, trade_days)
    rv = led.r if r is None else r

    def one(rvec) -> dict:
        folds = []
        top_num = top_den = 0.0
        uni_num = uni_den = 0.0
        rnd_num = rnd_den = 0.0
        sel_sets: List[set] = []
        for lo, hi in periods:
            rk_lo = lo - lookback_days * DAY
            if rk_lo < led.t0:
                continue
            a = led.measure(rk_lo, lo, r=rvec, floor=floor)
            b = led.measure(lo, hi, r=rvec, floor=floor)
            order = _order(rank_keys(a, criterion, floor=floor))
            if len(order) == 0:
                folds.append({"span": [_iso(lo), _iso(hi)], "qualifiers": 0,
                              "skipped": "nothing cleared the floor in the "
                                         "ranking window"})
                continue
            # --- strict causality, asserted rather than trusted -----------
            mrank = (led.ts >= rk_lo) & (led.ts < lo)
            if mrank.any():
                assert led.ts[mrank].max() < lo, "ranking trade entered at/after the fold"
            top = [int(i) for i in order[:k]]
            sel_sets.append(set(top))
            # "Trading the entire qualifying universe" means every strategy the
            # top-k was CHOSEN FROM - i.e. everything that cleared the floor in
            # the ranking window - scored on the next period. Defining it as
            # "qualifiers in the scoring window" instead would compare two
            # different populations and is not the comparison that made the old
            # result interpretable.
            allq = [int(i) for i in order]
            pool = [int(i) for i in order]
            rnd = [int(x) for x in rng.choice(pool, size=min(k, len(pool)),
                                             replace=False)]
            te, tn = _pooled(b, top)
            ue, un = _pooled(b, allq)
            re_, rn = _pooled(b, rnd)
            if tn:
                top_num += te * tn
                top_den += tn
            if un:
                uni_num += ue * un
                uni_den += un
            if rn:
                rnd_num += re_ * rn
                rnd_den += rn
            folds.append({
                "span": [_iso(lo), _iso(hi)],
                "rank_span": [_iso(rk_lo), _iso(lo)],
                "qualifiers_rank_window": int(a["qual"].sum()),
                "qualifiers_score_window": int(b["qual"].sum()),
                "selected": len(top),
                # When the ranking window holds <= k qualifiers the "top k" IS
                # the whole universe and no selection happened. The prior study
                # hit exactly this on its 240m cells (1-9 qualifiers).
                "topk_is_whole_universe": len(order) <= k,
                "in_sample_key": _r4(float(np.nanmean(
                    rank_keys(a, criterion, floor=floor)[top]))),
                "in_sample_exp_r": _r4(float(np.nanmean(a["exp"][top]))),
                "oos_trades": tn, "oos_exp_r": _r4(te),
                "universe_trades": un, "universe_exp_r": _r4(ue),
                "randomk_exp_r": _r4(re_),
                "top1": led.sids[top[0]],
            })
        return {
            "folds": folds, "sel": sel_sets,
            "topk_exp_r": (top_num / top_den) if top_den else float("nan"),
            "topk_trades": int(top_den),
            "universe_exp_r": (uni_num / uni_den) if uni_den else float("nan"),
            "universe_trades": int(uni_den),
            "randomk_exp_r": (rnd_num / rnd_den) if rnd_den else float("nan"),
            "randomk_trades": int(rnd_den),
        }

    obs = one(rv)
    nulls, unulls = [], []
    for _ in range(nperm):
        p = led.permute(rng, block_days=trade_days)
        x = one(p)
        if x["topk_trades"]:
            nulls.append(x["topk_exp_r"])
        if x["universe_trades"]:
            unulls.append(x["universe_exp_r"])
    nm = float(np.mean(nulls)) if nulls else float("nan")
    ns = float(np.std(nulls)) if nulls else float("nan")
    # The universe arm needs its own null, because when the top-k IS the whole
    # qualifying universe the two z's are the same number measuring a DIFFERENT
    # thing. The permutation preserves every trade count, so `qual` is identical
    # under it - therefore a non-zero z on the universe arm is not a ranking
    # effect at all. It says that strategies which cleared the trade floor
    # earned more per trade than a reassignment of R within their own (exit
    # geometry x time block) pool would give, i.e. an ACTIVITY effect. Reporting
    # that as "the top 10 works" would be wrong.
    unm = float(np.mean(unulls)) if unulls else float("nan")
    uns = float(np.std(unulls)) if unulls else float("nan")

    sel = obs["sel"]
    js = [len(sel[i] & sel[i + 1]) / max(len(sel[i] | sel[i + 1]), 1)
          for i in range(len(sel) - 1)]
    used = [f for f in obs["folds"] if f.get("oos_trades")]
    top1 = [f["top1"] for f in obs["folds"] if f.get("top1")]
    vacuous = sum(1 for f in obs["folds"] if f.get("topk_is_whole_universe"))
    scored = [f for f in obs["folds"] if "topk_is_whole_universe" in f]

    th = D.threshold(max(2, led.screened),
                     D.SPAN_DAYS.get((led.symbol, led.base_tf),
                                     (led.t1 - led.t0) / DAY))
    return {
        "symbol": led.symbol, "setting": led.setting, "base_tf": led.base_tf,
        "substrate": led.substrate, "criterion": criterion,
        "lookback_days": lookback_days, "trade_days": trade_days,
        "floor": floor, "top_k": k, "n_strategies": led.S,
        "folds_total": len(periods), "folds_traded": len(used),
        "oos_trades": obs["topk_trades"],
        "topk_exp_r": _r4(obs["topk_exp_r"]),
        "universe_exp_r": _r4(obs["universe_exp_r"]),
        "randomk_exp_r": _r4(obs["randomk_exp_r"]),
        "selection_edge_vs_universe_r": _r4(obs["topk_exp_r"] - obs["universe_exp_r"]),
        "selection_edge_vs_randomk_r": _r4(obs["topk_exp_r"] - obs["randomk_exp_r"]),
        "null_exp_r": _r4(nm), "null_sd": _r4(ns),
        "universe_null_exp_r": _r4(unm), "universe_null_sd": _r4(uns),
        "universe_z_vs_null": (
            round((obs["universe_exp_r"] - unm) / uns, 2)
            if uns and uns > 1e-12 and obs["universe_exp_r"] == obs["universe_exp_r"]
            else None),
        "z_vs_null": (round((obs["topk_exp_r"] - nm) / ns, 2)
                      if ns and ns > 1e-12 and obs["topk_exp_r"] == obs["topk_exp_r"]
                      else None),
        "folds_where_topk_is_the_whole_universe": f"{vacuous} of {len(scored)}",
        "mean_rank_window_qualifiers": (
            round(sum(f["qualifiers_rank_window"] for f in scored) / len(scored), 1)
            if scored else None),
        "folds_profitable": f"{sum(1 for f in used if (f['oos_exp_r'] or 0) > 0)}"
                            f" of {len(used)}",
        "folds_beating_universe": f"{sum(1 for f in used if f['universe_exp_r'] is not None and f['oos_exp_r'] > f['universe_exp_r'])} of {len(used)}",
        "consecutive_jaccard": _r4(float(np.mean(js))) if js else None,
        "union_selected": len(set().union(*sel)) if sel else 0,
        "top1_changed": f"{sum(1 for i in range(len(top1) - 1) if top1[i] != top1[i+1])}"
                        f" of {max(len(top1) - 1, 0)}",
        "deflation": th,
        "folds": obs["folds"],
    }


def roll_report(res: dict) -> str:
    """One paragraph a reader can act on, with the verdict spelled out."""
    t, u, rk, z = (res["topk_exp_r"], res["universe_exp_r"],
                   res["randomk_exp_r"], res["z_vs_null"])
    lines = [
        f"{res['symbol']} {res['setting']} {res['base_tf']}m  "
        f"criterion={res['criterion']}  lookback={res['lookback_days']}d  "
        f"trade={res['trade_days']}d  floor={res['floor']}  k={res['top_k']}",
        f"  folds traded {res['folds_traded']}/{res['folds_total']}   "
        f"oos trades {res['oos_trades']}",
        f"  top-{res['top_k']}  {t}R      universe {u}R      random-k {rk}R"
        f"      null {res['null_exp_r']}R (sd {res['null_sd']})   z={z}",
        f"  universe vs its own null: {res['universe_exp_r']}R vs "
        f"{res['universe_null_exp_r']}R (sd {res['universe_null_sd']})   "
        f"z={res['universe_z_vs_null']}   <- an ACTIVITY effect, not a ranking one",
        f"  selection edge vs universe {res['selection_edge_vs_universe_r']}R   "
        f"vs random-k {res['selection_edge_vs_randomk_r']}R",
        f"  rank-window qualifiers mean {res['mean_rank_window_qualifiers']}   "
        f"top-k was the whole universe in {res['folds_where_topk_is_the_whole_universe']} folds",
        f"  folds profitable {res['folds_profitable']}   "
        f"beating universe {res['folds_beating_universe']}   "
        f"consecutive Jaccard {res['consecutive_jaccard']}   "
        f"top1 changed {res['top1_changed']}",
    ]
    verdict = []
    vac = res["folds_where_topk_is_the_whole_universe"]
    nv, nt = (int(x) for x in vac.split(" of "))
    if nt and nv == nt:
        verdict.append(f"TOP-{res['top_k']} IS NOT A SELECTION - the ranking "
                       f"window held <= k qualifiers in {vac} folds "
                       f"(mean {res['mean_rank_window_qualifiers']})")
    if t is None or t != t:
        verdict.append("NO FORWARD RESULT - no fold traded")
    else:
        if u is not None and u == u and t <= u:
            verdict.append("SELECTION DESTROYED VALUE (top-k <= universe)")
        if z is not None and z <= 0:
            verdict.append("TOP-K AT OR BELOW THE NO-EDGE NULL")
        if not verdict:
            verdict.append("top-k beat both universe and null - report with the "
                           "deflation threshold below")
    lines.append("  VERDICT: " + "; ".join(verdict))
    d = res["deflation"]
    lines.append(f"  threshold: n={d['n_screened']} free_t={d['free_t']} on "
                 f"{d['span_days']}d (sqrt y {d['sqrt_years']}) -> needs "
                 f"annualised Sharpe {d['required_annual_sharpe']}")
    return "\n".join(lines)


def _iso(ts: float) -> str:
    return to_et(datetime.fromtimestamp(ts, tz=ET)).isoformat()


def _r4(x) -> Optional[float]:
    try:
        return round(float(x), 4) if x == x else None
    except (TypeError, ValueError):
        return None
