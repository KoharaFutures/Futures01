"""BT5-ALGO-1 assertions. Run before trusting any number the algorithm prints.

Each check is a thing that, if it silently failed, would turn a measurement into
an artefact with no external signature. That is the failure mode this repository
keeps hitting (D38, D42, D44, D48), so the checks are part of the algorithm
rather than a test of it.
"""
from __future__ import annotations

import os
import random
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import activity as A  # noqa: E402
import s2  # noqa: E402

_CACHE = {}


def load():
    if "j" not in _CACHE:
        _CACHE["j"] = A.join()
    return _CACHE["j"]


# --------------------------------------------------------------------------
def check_join_is_total():
    """Every stored trade joins, and the coverage dict accounts for all of it."""
    _, _, cov = load()
    assert cov["trades"] == 21954, cov
    assert cov["joined"] == 21954, cov
    assert (cov["no_such_cell"] + cov["ts_not_a_bar"]
            + cov["entry_is_first_bar"]) == 0, cov
    return f"joined {cov['joined']}/{cov['trades']}, unjoined 0"


def check_signal_bar_precedes_entry_by_one_timeframe():
    """The stratified bar is the signal bar, not the fill bar.

    `Trade.entry_ts` is the fill bar [repo-verified: engine.py:372], so the bar
    whose statistics the strategy read is one bar earlier. If this ever slipped
    to the fill bar the stratifier would be conditioning on information the
    decision did not have, and the whole sub-task would be measuring a
    look-ahead instead of a mechanism.
    """
    joined, bars, _ = load()
    bad = 0
    for t in joined[:4000]:
        rows = bars[(t["symbol"], t["tf"], t["slice"])]
        sig, ent = rows[t["sig_i"]], rows[t["sig_i"] + 1]
        assert datetime.fromisoformat(ent["ts"]) == datetime.fromisoformat(t["ts"])
        gap = (datetime.fromisoformat(ent["ts"])
               - datetime.fromisoformat(sig["ts"]))
        if gap != timedelta(minutes=t["tf"]):
            bad += 1          # a session gap; the *bar* is still the prior bar
    return (f"4000 sampled trades: signal bar is the immediately preceding bar; "
            f"{bad} of them sit across a calendar gap wider than one timeframe")


def check_no_lookahead_in_stratifiers():
    """RAW and RELVOL use only information available when the signal fired.

    Appending later bars must not change an earlier bar's stratifier value.
    Truncating the cell at bar `m` and recomputing must reproduce the first `m`
    values of `volume` and of `relative_volume` exactly. TODRANK is a declared
    full-sample transform and is exempt - it is checked for the property it does
    claim instead, in `check_todrank_is_time_of_day_neutral`.
    """
    cells = A.build_cells()
    key = ("MGC", 60, "S2")
    rows = A.bar_table(cells[key])
    m = len(rows) // 2
    trunc = A.bar_table(cells[key][:m])
    for i in range(m):
        assert trunc[i]["volume"] == rows[i]["volume"], i
        assert trunc[i]["rel_volume"] == rows[i]["rel_volume"], i
        assert trunc[i]["atr"] == rows[i]["atr"], i
    return f"{m} bars: volume, rel_volume and atr unchanged by truncation"


def check_indicators_match_the_frame_the_study_used():
    """`bar_table`'s columns equal what `build_symbol_frame` put in front of the
    strategies. Recomputing rather than reading the frame is a shortcut, and
    this is the assertion that makes it a safe one."""
    from futures_agents.features import build_symbol_frame
    from futures_agents.scout import FRAMES
    cells = A.build_cells()
    key = ("MCL", 60, "S1")
    rows = A.bar_table(cells[key])
    frame = build_symbol_frame(cells[key], FRAMES[60])
    cols = frame.frames[60].cols
    n = 0
    for i, r in enumerate(rows):
        assert r["atr"] == cols["atr"][i], (i, r["atr"], cols["atr"][i])
        assert r["rel_volume"] == cols["rel_volume"][i], i
        n += 1
    return f"{n} bars of MCL 60m S1: atr and rel_volume identical to the frame"


def check_strata_are_count_balanced():
    """Each axis' terciles hold within 5% of a third of the bars in each cell."""
    _, bars, _ = load()
    worst = 0.0
    for axis in s2.AXES:
        lab = s2.label_bars(bars, axis, 3)
        for key, v in lab.items():
            c = Counter(g for g in v if g is not None)
            tot = sum(c.values())
            for g in range(3):
                worst = max(worst, abs(c[g] / tot - 1 / 3))
    assert worst < 0.05, worst
    return f"worst per-cell stratum share deviation from 1/3: {worst:.4f}"


def check_todrank_is_time_of_day_neutral():
    """TODRANK's strata have near-identical time-of-day composition; RAW's do
    not. This is the whole point of residualising, so it is asserted rather than
    assumed: if TODRANK's strata were still time-of-day-sorted, the
    "residualised" answer would be the raw answer wearing a different name."""
    _, bars, _ = load()
    out = {}
    for axis in ("RAW", "TODRANK"):
        lab = s2.label_bars(bars, axis, 3)
        mix = defaultdict(lambda: Counter())
        for key, rows in bars.items():
            for r, g in zip(rows, lab[key]):
                if g is not None:
                    mix[g][r["bucket"]] += 1
        buckets = set()
        for g in mix:
            buckets |= set(mix[g])
        tv = 0.0
        for b in buckets:
            lo = mix[0][b] / sum(mix[0].values())
            hi = mix[2][b] / sum(mix[2].values())
            tv += abs(hi - lo)
        out[axis] = tv / 2.0          # total variation distance in [0, 1]
    assert out["TODRANK"] < 0.05, out
    assert out["RAW"] > 0.25, out
    return (f"time-of-day TV distance between HIGH and LOW strata: "
            f"RAW {out['RAW']:.3f}, TODRANK {out['TODRANK']:.3f}")


def check_fast_path_matches_reference():
    """`_Compact.stats()` reproduces the reference `per_strategy` medians."""
    joined, bars, _ = load()
    msgs = []
    for axis in s2.AXES:
        lab = s2.label_bars(bars, axis, 3)
        ref = s2.per_strategy(joined, s2._gof(lab))
        comp = s2._Compact(joined, bars, lab, "bucket", 3, s2.MIN_N)
        a, b, c, q = comp.stats()
        assert q == ref["qualifying"], (axis, q, ref["qualifying"])
        for got, want in ((a, ref["d_mean_r"]["median"]),
                          (b, ref["d_win"]["median"]),
                          (c, ref["d_payoff"]["median"])):
            assert abs(got - want) < 1e-12, (axis, got, want)
        msgs.append(f"{axis} q={q}")
    return "fast path == reference on observed labels: " + ", ".join(msgs)


def check_permutation_preserves_block_composition():
    """A draw moves labels only inside a (cell, ET clock bucket) block.

    If it leaked across blocks the null would no longer be time-of-day-matched
    and the residualised result would be tested against the raw null.
    """
    _, bars, _ = load()
    lab = s2.label_bars(bars, "TODRANK", 3)
    comp = s2._Compact(joined_or(bars), bars, lab, "bucket", 3, s2.MIN_N)
    before = _block_counts(comp)
    rng = random.Random(7)
    for _ in range(5):
        comp.shuffle(rng)
    after = _block_counts(comp)
    assert before == after, "block label multiset changed"
    moved = sum(1 for c, l in enumerate(comp.lab)
                for i, g in enumerate(l) if g != lab[comp.cells[c]][i])
    assert moved > 0, "shuffle moved nothing - the null would be the observed"
    return (f"{len(before)} blocks: label multisets identical after 5 draws; "
            f"{moved} bar labels actually moved")


def _block_counts(comp):
    out = []
    for lab, blocks in zip(comp.lab, comp.blocks):
        for idx in blocks:
            out.append(tuple(sorted(Counter(lab[i] for i in idx).items())))
    return sorted(out)


def joined_or(bars):
    return load()[0]


def check_determinism():
    """Same seed, same p. Twice."""
    joined, bars, _ = load()
    lab = s2.label_bars(bars, "TODRANK", 3)
    a = s2.permutation_test(joined, bars, lab, "bucket", draws=40, seed=11)
    b = s2.permutation_test(joined, bars, lab, "bucket", draws=40, seed=11)
    assert a["d_mean_r"] == b["d_mean_r"], (a["d_mean_r"], b["d_mean_r"])
    return f"40 draws twice at seed 11: p={a['d_mean_r']['p_two_sided']} both times"


def check_r_is_not_recomputed():
    """Every reported R is the stored R. The artefact carries no price, no point
    distance and no dollar figure [cite: backtest/BT3/ALGOS.md choice 9, which
    had to re-run the generating study to recover stop distance], so S2
    re-aggregates `r` and never re-derives it."""
    joined, _, _ = load()
    import json
    with open(os.path.join(A.REPO, A.TRADES)) as fh:
        raw = json.load(fh)
    assert len(raw) == len(joined)
    assert sorted(t["r"] for t in raw) == sorted(t["r"] for t in joined)
    keys = set(raw[0])
    assert not (keys & {"entry", "entry_price", "stop", "initial_stop",
                        "risk_points", "risk_dollars", "pnl"}), keys
    return (f"{len(joined)} R values identical to the dump's; dump carries none "
            f"of entry/stop/risk_points/pnl")


CHECKS = [check_join_is_total,
          check_signal_bar_precedes_entry_by_one_timeframe,
          check_no_lookahead_in_stratifiers,
          check_indicators_match_the_frame_the_study_used,
          check_strata_are_count_balanced,
          check_todrank_is_time_of_day_neutral,
          check_fast_path_matches_reference,
          check_permutation_preserves_block_composition,
          check_determinism,
          check_r_is_not_recomputed]


if __name__ == "__main__":
    for fn in CHECKS:
        print(f"{fn.__name__:52s} {fn()}")
    print("all checks passed")
