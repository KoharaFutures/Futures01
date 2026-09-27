"""BT5-ALGO-1, part 2: activity stratification of the settled finding.

R5's S2. Two layers, and they answer two different questions:

  **Layer 1, unit = bar.** Do the per-bar statistics `MAIN-01` names (ATR,
  relative volume, band widths, CLV) actually differ across activity strata on
  the wall-clock grid, and does that difference survive removing the
  time-of-day component? This is "does the footprint exist at all". It involves
  no strategies, no trades and no pooling, so nothing in it can be inflated by
  the three pooling levels this repository has measured.

  **Layer 2, unit = strategy.** Does the settled finding - expectancy, and rule
  3's win-rate/payoff cancellation - differ between low- and high-activity
  strata? R3 ruled that the unit of a finding over this artefact is
  **per-strategy**, so the primary number is the median over the 176 strategies
  of a within-strategy contrast. The pooled per-trade number is computed too,
  and reported only as a diagnostic of pooling.

**Three stratifier axes.** `MAIN-01`'s premise is that activity per bar is
unequal; `BRIEF.md` rule 6 already refutes hours filters, and activity is largely
time of day. So the raw axis is partly pre-answered and the content is in the
residualised axes:

  ``RAW``      signal-bar volume. The pre-answered form. Carries time of day.
  ``RELVOL``   the library's own ``relative_volume(bars, 20)`` at the signal
               bar: volume divided by the trailing-20-session mean of the *same
               ET clock bucket* [repo-verified:
               futures_agents/indicators/volume.py:266-286]. Causal, and it is
               the time-of-day norm `MGR-T13` exists to settle, so R1's binding
               constraint there ("both axes take the time-of-day norm or
               neither does") is satisfied by naming which axis each is.
  ``TODRANK``  within-(cell, ET clock bucket) percentile rank of signal-bar
               volume over the whole cell. Stricter than RELVOL: it removes any
               monotone time-of-day transform, not merely the level, and it
               forces each stratum to be uniform in time of day by
               construction. Not causal - it is a full-sample transform of the
               *bars*, identical for every strategy, so it can mis-assign a
               stratum but cannot manufacture an expectancy difference.

**The null and the placebo are the same object, by design.** R5 named the
control: "a stratifier with the same marginal distribution and no activity
content, e.g. a within-session shuffle of the activity labels". Permuting the
stratum labels among the bars *inside each (cell, ET clock bucket) block*
preserves the trade set, every strategy's R values, the per-block label
frequencies and the time-of-day composition of every stratum, and destroys only
the association between activity and trade. Applying the same permuted bar
labels to all 176 strategies preserves their mutual correlation too, which is
what makes this a legitimate test over correlated variants where a
strategy-level t-test would not be (D28).
"""
from __future__ import annotations

import json
import math
import os
import random
import statistics as st
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import activity as A  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "s2_report.json")

#: Pre-registered before measuring. Every additional value entered below is
#: counted in the search-size accounting in ALGOS.md.
N_STRATA = 3          # terciles; HIGH vs LOW is the contrast
MIN_N = 10            # per stratum per strategy for that strategy to contribute
DRAWS = 2000          # permutation draws
SEED = 20260927

STATS = ["atr_over_close", "rel_volume", "bb_width", "kc_width", "clv", "abs_ret"]
AXES = ["RAW", "RELVOL", "TODRANK"]


# --------------------------------------------------------------------------
# Stratifiers
# --------------------------------------------------------------------------
def _terciles(values: Sequence[float], k: int) -> List[float]:
    """Interior cut points of `k` equal-count strata."""
    v = sorted(values)
    return [v[int(round(j * len(v) / k))] for j in range(1, k)]


def _stratum(x: Optional[float], cuts: Sequence[float]) -> Optional[int]:
    if x is None:
        return None
    s = 0
    for cut in cuts:
        if x >= cut:
            s += 1
    return s


def within_bucket_rank(rows: List[dict]) -> List[Optional[float]]:
    """Percentile rank of `volume` inside each ET clock bucket of one cell.

    Ties take the average rank, so a block of equal-volume bars (every
    zero-volume bar, for instance) is not silently ordered by position in the
    file. A bucket with a single bar yields None: a rank of one observation
    carries no information and pretending it is 0.5 would put it in the middle
    stratum for free.
    """
    by = defaultdict(list)
    for r in rows:
        by[r["bucket"]].append(r["i"])
    out: List[Optional[float]] = [None] * len(rows)
    for _, idx in by.items():
        if len(idx) < 2:
            continue
        order = sorted(idx, key=lambda i: rows[i]["volume"])
        n = len(order)
        j = 0
        while j < n:
            k = j
            while k + 1 < n and rows[order[k + 1]]["volume"] == rows[order[j]]["volume"]:
                k += 1
            avg = (j + k) / 2.0
            for m in range(j, k + 1):
                out[order[m]] = avg / (n - 1)
            j = k + 1
    return out


def label_bars(bars: Dict[Tuple[str, int, str], List[dict]], axis: str, k: int
               ) -> Dict[Tuple[str, int, str], List[Optional[int]]]:
    """Stratum label for every bar of every cell, on one axis.

    Cuts are taken **per cell**, on the bar population rather than the trade
    population. Per cell because volume drifts across the three disjoint slices
    and a pooled cut would make stratum membership partly a slice indicator; on
    bars because the mechanism under test is a statement about bars, and letting
    the trades define the cuts would let a strategy's own selectivity move them.
    """
    out = {}
    for key, rows in bars.items():
        if axis == "RAW":
            vals = [float(r["volume"]) for r in rows]
        elif axis == "RELVOL":
            vals = [r["rel_volume"] for r in rows]
        elif axis == "TODRANK":
            vals = within_bucket_rank(rows)
        else:
            raise ValueError(axis)
        good = [v for v in vals if v is not None]
        cuts = _terciles(good, k) if len(good) >= k * 10 else []
        out[key] = [_stratum(v, cuts) if cuts else None for v in vals]
    return out


# --------------------------------------------------------------------------
# Layer 1 - bar-level footprint
# --------------------------------------------------------------------------
def _med(xs):
    xs = [x for x in xs if x is not None]
    return st.median(xs) if xs else None


def layer1(bars, labels, k: int = N_STRATA) -> List[dict]:
    """Per-bar statistics by activity stratum, aggregated per (symbol, tf)."""
    agg = defaultdict(lambda: defaultdict(list))
    tod = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for (sym, tf, sl), rows in bars.items():
        lab = labels[(sym, tf, sl)]
        for r, g in zip(rows, lab):
            if g is None:
                continue
            agg[(sym, tf)][g].append(r)
            tod[(sym, tf)][g][r["session"]] += 1
    out = []
    for (sym, tf) in sorted(agg):
        row = dict(symbol=sym, tf=tf)
        for g in range(k):
            rs = agg[(sym, tf)][g]
            row[f"n_{g}"] = len(rs)
            row[f"vol_{g}"] = _med([x["volume"] for x in rs])
            for s in STATS:
                row[f"{s}_{g}"] = _med([x[s] for x in rs])
        for s in STATS + ["vol"]:
            hi, lo = row.get(f"{s}_{k-1}"), row.get(f"{s}_0")
            row[f"{s}_ratio"] = (hi / lo) if (hi and lo) else None
        row["session_mix"] = {g: dict(tod[(sym, tf)][g]) for g in range(k)}
        out.append(row)
    return out


# --------------------------------------------------------------------------
# Layer 2 - trade-level, per strategy
# --------------------------------------------------------------------------
def _arm_stats(rs: List[dict]) -> dict:
    n = len(rs)
    if n == 0:
        return dict(n=0, mean_r=None, win=None, payoff=None)
    wins = [x["r"] for x in rs if x["r"] > 0]
    losses = [-x["r"] for x in rs if x["r"] <= 0]
    aw = st.mean(wins) if wins else 0.0
    al = st.mean(losses) if losses else 0.0
    return dict(n=n, mean_r=st.mean(x["r"] for x in rs),
                win=len(wins) / n, payoff=(aw / al) if al > 0 else None)


def per_strategy(joined, gof, k: int = N_STRATA, min_n: int = MIN_N) -> dict:
    """Within-strategy HIGH-minus-LOW contrasts. `gof` maps trade -> stratum."""
    by = defaultdict(lambda: defaultdict(list))
    for t in joined:
        g = gof(t)
        if g is None:
            continue
        by[t["strategy"]][g].append(t)

    rows, d_r, d_win, d_pay = [], [], [], []
    for s in sorted(by):
        loq, hiq = by[s].get(0, []), by[s].get(k - 1, [])
        a, b = _arm_stats(loq), _arm_stats(hiq)
        ok = a["n"] >= min_n and b["n"] >= min_n
        row = dict(strategy=s, n_low=a["n"], n_high=b["n"], qualifies=ok,
                   mean_r_low=a["mean_r"], mean_r_high=b["mean_r"],
                   win_low=a["win"], win_high=b["win"],
                   payoff_low=a["payoff"], payoff_high=b["payoff"])
        if ok:
            row["d_mean_r"] = b["mean_r"] - a["mean_r"]
            row["d_win"] = b["win"] - a["win"]
            d_r.append(row["d_mean_r"])
            d_win.append(row["d_win"])
            if a["payoff"] and b["payoff"]:
                row["d_payoff"] = b["payoff"] - a["payoff"]
                d_pay.append(row["d_payoff"])
        rows.append(row)

    def summ(xs):
        if not xs:
            return dict(n=0)
        return dict(n=len(xs), median=st.median(xs), mean=st.mean(xs),
                    p25=st.quantiles(xs, n=4)[0] if len(xs) > 3 else None,
                    p75=st.quantiles(xs, n=4)[2] if len(xs) > 3 else None,
                    n_positive=sum(1 for x in xs if x > 0))
    return dict(strategies=len(rows), qualifying=len(d_r), rows=rows,
                d_mean_r=summ(d_r), d_win=summ(d_win), d_payoff=summ(d_pay))


def pooled(joined, gof, k: int = N_STRATA) -> dict:
    """The per-trade average over the whole file. A diagnostic of pooling."""
    by = defaultdict(list)
    for t in joined:
        g = gof(t)
        if g is not None:
            by[g].append(t)
    out = {f"stratum_{g}": _arm_stats(by.get(g, [])) for g in range(k)}
    a, b = _arm_stats(by.get(0, [])), _arm_stats(by.get(k - 1, []))
    out["d_mean_r"] = (b["mean_r"] - a["mean_r"]) if (a["n"] and b["n"]) else None
    out["d_win"] = (b["win"] - a["win"]) if (a["n"] and b["n"]) else None
    out["d_payoff"] = ((b["payoff"] - a["payoff"])
                       if (a["payoff"] and b["payoff"]) else None)
    return out


# --------------------------------------------------------------------------
# The permutation null / placebo
# --------------------------------------------------------------------------
def _blocks(bars, labels, block: str):
    """Bar positions grouped into permutation blocks, per cell."""
    out = {}
    for key, rows in bars.items():
        by = defaultdict(list)
        for r, g in zip(rows, labels[key]):
            if g is None:
                continue
            by[r["bucket"] if block == "bucket" else 0].append(r["i"])
        out[key] = list(by.values())
    return out


def permute(bars, labels, block: str, rng) -> Dict[Tuple[str, int, str], List[Optional[int]]]:
    """One draw: shuffle stratum labels among the bars inside each block."""
    blocks = _blocks(bars, labels, block)
    out = {}
    for key, lab in labels.items():
        new = list(lab)
        for idx in blocks[key]:
            pool = [lab[i] for i in idx]
            rng.shuffle(pool)
            for i, g in zip(idx, pool):
                new[i] = g
        out[key] = new
    return out


def _gof(labels):
    def f(t):
        return labels[(t["symbol"], t["tf"], t["slice"])][t["sig_i"]]
    return f


class _Compact:
    """Flat arrays for the permutation loop.

    The reference path (`permute` + `per_strategy`) is kept and
    `checks.py::check_fast_path_matches_reference` asserts the two agree on the
    observed labels and on seeded draws. A hand-rolled inner loop that silently
    disagrees with its own reference is exactly how a permutation p becomes
    unfalsifiable, so the reference is not deleted after optimising.
    """

    def __init__(self, joined, bars, labels, block: str, k: int, min_n: int):
        self.k, self.min_n = k, min_n
        self.cells = sorted(bars)
        ci = {c: j for j, c in enumerate(self.cells)}
        self.lab = [list(labels[c]) for c in self.cells]
        self.blocks = []
        for c in self.cells:
            by = defaultdict(list)
            for r, g in zip(bars[c], labels[c]):
                if g is not None:
                    by[r["bucket"] if block == "bucket" else 0].append(r["i"])
            self.blocks.append([v for v in by.values() if len(v) > 1])
        strats = sorted({t["strategy"] for t in joined})
        si = {s: j for j, s in enumerate(strats)}
        self.n_strat = len(strats)
        self.t_s = [si[t["strategy"]] for t in joined]
        self.t_c = [ci[(t["symbol"], t["tf"], t["slice"])] for t in joined]
        self.t_b = [t["sig_i"] for t in joined]
        self.t_r = [t["r"] for t in joined]

    def shuffle(self, rng) -> None:
        for lab, blocks in zip(self.lab, self.blocks):
            for idx in blocks:
                pool = [lab[i] for i in idx]
                rng.shuffle(pool)
                for i, g in zip(idx, pool):
                    lab[i] = g

    def stats(self):
        """(median d_mean_r, median d_win, median d_payoff, qualifying)."""
        k, ns = self.k, self.n_strat
        n = [[0] * ns, [0] * ns]
        sr = [[0.0] * ns, [0.0] * ns]
        nw = [[0] * ns, [0] * ns]
        sw = [[0.0] * ns, [0.0] * ns]
        sl = [[0.0] * ns, [0.0] * ns]
        lab, t_s, t_c, t_b, t_r = self.lab, self.t_s, self.t_c, self.t_b, self.t_r
        for j in range(len(t_s)):
            g = lab[t_c[j]][t_b[j]]
            if g == 0:
                a = 0
            elif g == k - 1:
                a = 1
            else:
                continue
            s, r = t_s[j], t_r[j]
            n[a][s] += 1
            sr[a][s] += r
            if r > 0:
                nw[a][s] += 1
                sw[a][s] += r
            else:
                sl[a][s] -= r
        d_r, d_w, d_p = [], [], []
        for s in range(ns):
            if n[0][s] < self.min_n or n[1][s] < self.min_n:
                continue
            d_r.append(sr[1][s] / n[1][s] - sr[0][s] / n[0][s])
            d_w.append(nw[1][s] / n[1][s] - nw[0][s] / n[0][s])
            po = []
            for a in (0, 1):
                nl = n[a][s] - nw[a][s]
                if nw[a][s] and nl and sl[a][s] > 0:
                    po.append((sw[a][s] / nw[a][s]) / (sl[a][s] / nl))
                else:
                    po.append(None)
            if po[0] and po[1]:
                d_p.append(po[1] - po[0])
        return (st.median(d_r) if d_r else None,
                st.median(d_w) if d_w else None,
                st.median(d_p) if d_p else None, len(d_r))


def permutation_test(joined, bars, labels, block: str, *, draws: int = DRAWS,
                     seed: int = SEED, k: int = N_STRATA, min_n: int = MIN_N
                     ) -> dict:
    """Two-sided permutation p for three per-strategy statistics at once.

    The observed statistic is the **median across qualifying strategies** of the
    within-strategy HIGH-minus-LOW contrast. The null draws share the seed
    stream across the three statistics so they describe the same ensemble.
    """
    obs = per_strategy(joined, _gof(labels), k, min_n)
    keys = ["d_mean_r", "d_win", "d_payoff"]
    observed = {kk: obs[kk].get("median") for kk in keys}
    ge = {kk: 0 for kk in keys}
    null = {kk: [] for kk in keys}
    rng = random.Random(seed)
    placebo_draw = None
    comp = _Compact(joined, bars, labels, block, k, min_n)
    for d in range(draws):
        comp.shuffle(rng)
        vals = comp.stats()
        if d == 0:
            placebo_draw = dict(zip(keys, vals[:3]))
            placebo_draw["qualifying"] = vals[3]
        for kk, v in zip(keys, vals[:3]):
            if v is None or observed[kk] is None:
                continue
            null[kk].append(v)
            if abs(v) >= abs(observed[kk]):
                ge[kk] += 1
    out = {}
    for kk in keys:
        n = len(null[kk])
        out[kk] = dict(
            observed=observed[kk], draws=n,
            p_two_sided=((ge[kk] + 1) / (n + 1)) if n else None,
            null_median=st.median(null[kk]) if null[kk] else None,
            null_sd=st.pstdev(null[kk]) if len(null[kk]) > 1 else None,
            null_p05=(st.quantiles(null[kk], n=20)[0] if len(null[kk]) > 19 else None),
            null_p95=(st.quantiles(null[kk], n=20)[18] if len(null[kk]) > 19 else None),
        )
        if out[kk]["null_sd"]:
            out[kk]["z_vs_null"] = ((observed[kk] - out[kk]["null_median"])
                                   / out[kk]["null_sd"])
    out["block"] = block
    out["qualifying"] = obs["qualifying"]
    out["placebo_single_draw"] = placebo_draw
    return out


def sign_test(xs: Sequence[float]) -> dict:
    """Exact two-sided binomial sign test. Named per PIPELINE 4 obligation 3.

    Reported as a **secondary** statistic only: the 176 strategies are
    correlated variants of one signal, so its nominal p is optimistic. The
    permutation test above is the primary, and it accounts for the correlation
    by construction.
    """
    pos = sum(1 for x in xs if x > 0)
    neg = sum(1 for x in xs if x < 0)
    n = pos + neg
    if n == 0:
        return dict(n=0)
    kk = min(pos, neg)
    tail = sum(math.comb(n, j) for j in range(kk + 1)) / (2.0 ** n)
    return dict(n=n, positive=pos, negative=neg, p_two_sided=min(1.0, 2 * tail))


# --------------------------------------------------------------------------
def run() -> dict:
    joined, bars, cov = A.join()
    rep = dict(coverage=cov, params=dict(n_strata=N_STRATA, min_n=MIN_N,
                                        draws=DRAWS, seed=SEED),
               dispersion=[], axes={})
    for (sym, tf), rows in sorted(_by_symtf(bars).items()):
        v = sorted(r["volume"] for r in rows)
        n = len(v)
        rep["dispersion"].append(dict(
            symbol=sym, tf=tf, bars=n,
            zero_volume_bars=sum(1 for x in v if x == 0),
            p10=v[int(.10 * n)], p50=v[int(.50 * n)], p90=v[int(.90 * n)],
            p90_over_p10=(v[int(.90 * n)] / v[int(.10 * n)]
                          if v[int(.10 * n)] else None)))

    for axis in AXES:
        labels = label_bars(bars, axis, N_STRATA)
        gof = _gof(labels)
        block = "cell" if axis == "RAW" else "bucket"
        ent = dict(
            layer1=layer1(bars, labels),
            per_strategy=per_strategy(joined, gof),
            pooled=pooled(joined, gof),
            by_symbol_tf=by_symbol_tf(joined, gof),
            cancellation=cancellation(joined, gof),
            by_stop_distance=by_stop_distance(joined, gof),
            permutation=permutation_test(joined, bars, labels, block),
            block=block)
        qual = [r for r in ent["per_strategy"]["rows"] if r.get("qualifies")]
        ent["sign_test_d_mean_r"] = sign_test([r["d_mean_r"] for r in qual])
        # RAW carries time of day; the bucket-blocked null isolates the part of
        # it that is not time of day, so RAW gets both nulls.
        if axis == "RAW":
            ent["permutation_bucket_blocked"] = permutation_test(
                joined, bars, labels, "bucket")
        rep["axes"][axis] = ent

    # Sensitivity. Every row here is counted in ALGOS.md's search accounting.
    sens = []
    for axis in AXES:
        for k, min_n in ((2, MIN_N), (5, MIN_N), (N_STRATA, 20), (N_STRATA, 5)):
            labels = label_bars(bars, axis, k)
            block = "cell" if axis == "RAW" else "bucket"
            pt = permutation_test(joined, bars, labels, block, draws=500,
                                 k=k, min_n=min_n)
            sens.append(dict(axis=axis, n_strata=k, min_n=min_n, draws=500,
                             qualifying=pt["qualifying"],
                             observed=pt["d_mean_r"]["observed"],
                             p_two_sided=pt["d_mean_r"]["p_two_sided"],
                             null_median=pt["d_mean_r"]["null_median"],
                             z_vs_null=pt["d_mean_r"].get("z_vs_null")))
    rep["sensitivity"] = sens
    rep["search_size"] = dict(
        primary_tests=len(AXES) * 3 + 3,       # 3 axes x 3 statistics + RAW's
                                               # second null x 3 statistics
        sensitivity_tests=len(sens),
        total=len(AXES) * 3 + 3 + len(sens),
        free_t=math.sqrt(2 * math.log(max(2, len(AXES) * 3 + 3 + len(sens)))))
    return rep


def by_symbol_tf(joined, gof, k: int = N_STRATA, min_n: int = MIN_N) -> List[dict]:
    """The per-strategy contrast, conditioned on (symbol, tf).

    Pooling across cells is the second of this repository's three measured
    pooling levels, so the 176-strategy median is also cut eight ways. 22
    strategies per (symbol, tf).
    """
    out = []
    for sym in A.SYMBOLS:
        for tf in A.TFS:
            sub = [t for t in joined if t["symbol"] == sym and t["tf"] == tf]
            ps = per_strategy(sub, gof, k, min_n)
            q = [r for r in ps["rows"] if r.get("qualifies")]
            out.append(dict(symbol=sym, tf=tf, strategies=ps["strategies"],
                            qualifying=len(q),
                            median_d_mean_r=ps["d_mean_r"].get("median"),
                            median_d_win=ps["d_win"].get("median"),
                            median_d_payoff=ps["d_payoff"].get("median"),
                            n_positive=ps["d_mean_r"].get("n_positive")))
    return out


def cancellation(joined, gof, k: int = N_STRATA, min_n: int = MIN_N) -> dict:
    """Rule 3's win-rate/payoff cancellation, inside each activity stratum.

    `BRIEF.md` rule 3: moving a stop wider raises payoff ~89% and drops win rate
    ~14 points for no expectancy gain. If activity is a live confound in that
    measurement, the cancellation should not hold equally in a thin stratum and
    a busy one. Descriptive: per-stratum medians across strategies of win rate,
    payoff and mean R. No separate significance test is attached - the
    stratum contrast is already tested in `permutation_test`, and adding a
    second test here would buy multiplicity for nothing.
    """
    ps = per_strategy(joined, gof, k, min_n)
    q = [r for r in ps["rows"] if r.get("qualifies")]
    out = {}
    for side in ("low", "high"):
        out[side] = dict(
            median_win=st.median([r[f"win_{side}"] for r in q]),
            median_payoff=st.median([r[f"payoff_{side}"] for r in q
                                     if r[f"payoff_{side}"]]),
            median_mean_r=st.median([r[f"mean_r_{side}"] for r in q]))
    out["strategies"] = len(q)
    return out


def by_stop_distance(joined, gof, k: int = N_STRATA, min_n: int = 8) -> List[dict]:
    """Win rate and mean R by **modelled** invalidation distance, within stratum.

    R5's third S2 question. The dump records no stop distance
    [cite: backtest/BT3/ALGOS.md choice 9], so this uses the modelled distance
    `stop_mult x atr(signal bar) / close`, which is recoverable exactly, and not
    the realised `|entry - stop|`, which is not. Bucketed per (symbol, tf) so the
    terciles are not a symbol-price artefact.
    """
    cuts = {}
    for sym in A.SYMBOLS:
        for tf in A.TFS:
            vals = [t["sig_stop_pct_modelled"] for t in joined
                    if t["symbol"] == sym and t["tf"] == tf
                    and t["sig_stop_pct_modelled"] is not None]
            cuts[(sym, tf)] = _terciles(vals, k) if len(vals) >= k * 10 else []
    cross = defaultdict(list)
    for t in joined:
        g = gof(t)
        if g is None or t["sig_stop_pct_modelled"] is None:
            continue
        d = _stratum(t["sig_stop_pct_modelled"], cuts[(t["symbol"], t["tf"])])
        if d is None:
            continue
        cross[(g, d)].append(t)
    out = []
    for (g, d), rs in sorted(cross.items()):
        if len(rs) < min_n:
            continue
        s = _arm_stats(rs)
        out.append(dict(activity_stratum=g, distance_stratum=d, **s))
    return out


def _by_symtf(bars):
    out = defaultdict(list)
    for (sym, tf, _), rows in bars.items():
        out[(sym, tf)].extend(rows)
    return out


if __name__ == "__main__":
    r = run()
    with open(OUT, "w") as fh:
        json.dump(r, fh, indent=1, default=str)
    print("wrote", OUT)
    for axis in AXES:
        e = r["axes"][axis]
        ps, pm = e["per_strategy"], e["permutation"]
        print(f"\n=== {axis} (null block={e['block']}) ===")
        print(f"  qualifying strategies {ps['qualifying']}/{ps['strategies']}")
        for kk in ("d_mean_r", "d_win", "d_payoff"):
            o = pm[kk]
            print(f"  {kk:9s} per-strategy median {o['observed']!s:>10.10s}"
                  f"  p={o['p_two_sided']}  null med {o['null_median']!s:>9.9s}"
                  f"  z={o.get('z_vs_null')}")
        print(f"  POOLED d_mean_r {e['pooled']['d_mean_r']}")
        print(f"  sign test {e['sign_test_d_mean_r']}")
