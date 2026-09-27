"""EF6 deliverable 3 — deflation accounting for THIS programme, span included.

One function, so nobody derives a threshold by hand and nobody quotes 5.46 out
of habit:

    threshold(n_screened, span_days) -> dict

``5.46`` is the programme-wide historical figure for ~2.98M evaluations
(``BRIEF.md``). **It is not this programme's number.** This programme screens
what EF2-EF5 actually generate, and `free_t = sqrt(2*ln n)` is logarithmic, so
quoting the wrong *n* is not a rounding error in one direction only - at
n = 40,000 the threshold is 4.60, at n = 1,000 it is 3.72, and at n = 1 (a
single pre-registered hypothesis) the code's own floor is 1.177.

Deflation has TWO inputs and this repository has only ever turned one.

* ``free_t``   grows with how many things were searched.
* the **span** decides how much *t* a real edge can possibly have produced.

Lo (2002), and it is an identity rather than an approximation given the
definitions below:

    t = mean(R) / se(mean(R)) = sqrt(N) * mean(R)/sd(R)
    SR_annual = (mean(R)/sd(R)) * sqrt(N / Y)          # N trades over Y years
    =>  t = SR_annual * sqrt(Y)                        # exactly

So a threshold in t converts to a *required annualised Sharpe* by dividing by
sqrt(Y), and that is the number a reader can judge. A required Sharpe of 1.1 is
ordinary. A required Sharpe of 3.0 is not a thing that exists in futures, and
saying "this cell did not clear its threshold" without saying that is reporting
a property of the experiment as a discovery about the market.

Measured spans, the substrate this programme runs on
`[measured: python3 over data/archive/*.jsonl, first and last ts, 2026-09-27]`:

| tf     | span (calendar days) | years | sqrt(years) |
|--------|----------------------|-------|-------------|
| 1m     |   4.95               | 0.014 | 0.116       |
| 5m     |  57.90               | 0.159 | 0.398       |
| 15m    |  57.90               | 0.159 | 0.398       |
| 30m    |  57.90               | 0.159 | 0.398       |
| 60m    | 718.88               | 1.968 | 1.403       |
| 240m   | 718.83               | 1.968 | 1.403       |
| 1440m  | MGC 5835 / MES,MNQ 2702 / MCL unusable (1 bar) |

Calendar-days / 365.25 is the convention `BRIEF.md` already uses (322/365.25 =
0.939). Cross-checked against a trading-session convention and they agree to
three decimals here: the 5m series holds 49 distinct calendar dates ~= 41
18:00->16:00 sessions, 41/252 = 0.163y (sqrt 0.403 vs 0.398); the 60m series
holds 596 dates ~= 490 sessions, 490/252 = 1.944y (sqrt 1.394 vs 1.403). The
choice of convention is not load-bearing. `[measured: distinct ts[:10] counts]`
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, Optional, Sequence, Tuple

__all__ = [
    "DAYS_PER_YEAR", "SPAN_DAYS", "PREREG_FLOOR", "PROGRAMME_WIDE_FREE_T",
    "free_t", "span_years", "threshold", "for_cell", "group_span_days",
    "implied_annual_sharpe", "verdict", "table", "max_n_answerable",
    "budget_table", "topn_threshold",
]

DAYS_PER_YEAR = 365.25

#: The code's own floor for a *single pre-registered* hypothesis:
#: ``toolkit.free_t`` is ``sqrt(2*ln(max(2, trials)))`` so trials=1 gives
#: sqrt(2*ln 2) [repo-verified: workspace/studies/toolkit.py:56-58].
PREREG_FLOOR = math.sqrt(2.0 * math.log(2.0))          # 1.1774

#: Quoted for context only. Never use it as this programme's threshold.
PROGRAMME_WIDE_FREE_T = 5.46

#: Measured calendar-day span of `data/archive/` per (symbol, timeframe).
#: 1440m is per-symbol because the vendor's daily depth is not uniform, and
#: MCL 1440m holds exactly one row - there is no daily MCL.
SPAN_DAYS: Dict[Tuple[str, int], float] = {}
for _sym in ("MGC", "MCL", "MES", "MNQ"):
    SPAN_DAYS[(_sym, 1)] = 4.95
    SPAN_DAYS[(_sym, 5)] = 57.90
    SPAN_DAYS[(_sym, 15)] = 57.90
    SPAN_DAYS[(_sym, 30)] = 57.90
    SPAN_DAYS[(_sym, 60)] = 718.88
    SPAN_DAYS[(_sym, 240)] = 718.83
SPAN_DAYS[("MGC", 1440)] = 5835.0
SPAN_DAYS[("MES", 1440)] = 2702.0
SPAN_DAYS[("MNQ", 1440)] = 2702.0
# MCL 1440m deliberately absent: 1 bar. for_cell() raises rather than guessing.


def free_t(n_screened: int) -> float:
    """t-units bought by search alone. Anything under this is not evidence.

    Identical arithmetic to ``workspace/studies/toolkit.free_t``, restated here
    so this module has no import-time dependency on the studies package.
    """
    return math.sqrt(2.0 * math.log(max(2, int(n_screened))))


def span_years(span_days: float) -> float:
    return float(span_days) / DAYS_PER_YEAR


def group_span_days(symbol: str, timeframes: Sequence[int]) -> float:
    """Usable span of a multi-timeframe GROUP = the span of its shortest member.

    A 5m+60m frame can only be evaluated where both series exist, and the 5m
    series is 57.9 days long. Taking the 60m span for such a group would
    overstate sqrt(years) by 3.5x and understate the required Sharpe by the
    same factor. The binding constraint is the intersection, i.e. the minimum.
    """
    if not timeframes:
        raise ValueError("timeframes must be non-empty")
    spans = []
    for tf in timeframes:
        key = (symbol.upper(), int(tf))
        if key not in SPAN_DAYS:
            raise KeyError(
                f"no measured span for {symbol} {tf}m - "
                "MCL has no usable daily history (1 bar); add a measured span "
                "rather than guessing one")
        spans.append(SPAN_DAYS[key])
    return min(spans)


def implied_annual_sharpe(t: float, span_days: float) -> float:
    """The annualised Sharpe an observed t implies on this span. t / sqrt(Y)."""
    y = span_years(span_days)
    if y <= 0:
        return float("nan")
    return float(t) / math.sqrt(y)


def threshold(n_screened: int, span_days: float, *,
              preregistered: bool = False) -> dict:
    """THE function. Give it what you screened and how long you watched.

    Parameters
    ----------
    n_screened
        The number of variants **actually screened in this programme** to
        produce the row being judged. Not 2.97M, not 40,000 unless you really
        screened 40,000. If a cell's top 10 came from ranking 812 strategies in
        that cell, and the cell was one of 56 cells you ranked, the honest n for
        a *cell-local* claim is 812 and for a *best-of-programme* claim is the
        total across cells. Report both if you are unsure which you are making;
        they bracket the answer.
    span_days
        Calendar days of substrate the row was measured on. Use
        :data:`SPAN_DAYS` or :func:`group_span_days`, never a guess.
    preregistered
        True only if the hypothesis was fixed in writing *before* looking. Then
        the floor is :data:`PREREG_FLOOR` = 1.177 rather than sqrt(2 ln n).
        Carry DISC2's counter with it: a borrowed idea from the literature is
        the survivor of a large undocumented collective search, so its honest
        n is not 1 either.

    Returns a dict with the threshold in t, the annualised Sharpe that
    threshold demands on this span, and the same for the pre-registered floor
    so the two are always visible together.
    """
    n = max(1, int(n_screened))
    y = span_years(span_days)
    sq = math.sqrt(y) if y > 0 else float("nan")
    t_req = PREREG_FLOOR if preregistered else free_t(n)
    out = {
        "n_screened": n,
        "preregistered": bool(preregistered),
        "span_days": round(float(span_days), 2),
        "span_years": round(y, 4),
        "sqrt_years": round(sq, 4),
        "free_t": round(free_t(n), 4),
        "prereg_floor_t": round(PREREG_FLOOR, 4),
        "threshold_t": round(t_req, 4),
        "required_annual_sharpe": round(t_req / sq, 3) if sq == sq and sq > 0 else None,
        "required_annual_sharpe_prereg": (
            round(PREREG_FLOOR / sq, 3) if sq == sq and sq > 0 else None),
        # The t a genuinely good, ordinary strategy would produce on this span.
        # SR 1.0 is a respectable systematic futures strategy; SR 2.0 is very
        # good. If neither reaches threshold_t, the cell cannot answer the
        # question being asked of it, whatever the market is doing.
        "t_at_sharpe_1": round(1.0 * sq, 3) if sq == sq else None,
        "t_at_sharpe_2": round(2.0 * sq, 3) if sq == sq else None,
        "t_at_sharpe_3": round(3.0 * sq, 3) if sq == sq else None,
    }
    out["answerable_at_sharpe_2"] = (
        out["t_at_sharpe_2"] is not None and out["t_at_sharpe_2"] >= out["threshold_t"])
    out["answerable_prereg_at_sharpe_2"] = (
        out["t_at_sharpe_2"] is not None and out["t_at_sharpe_2"] >= PREREG_FLOOR)
    return out


def for_cell(symbol: str, timeframes, n_screened: int, *,
             preregistered: bool = False) -> dict:
    """:func:`threshold` with the span looked up from the measured table.

    ``timeframes`` may be an int (single timeframe) or a sequence (a group, in
    which case the shortest member's span binds).
    """
    tfs = [timeframes] if isinstance(timeframes, int) else list(timeframes)
    span = group_span_days(symbol, tfs)
    out = threshold(n_screened, span, preregistered=preregistered)
    out["symbol"] = symbol.upper()
    out["timeframes"] = [int(t) for t in tfs]
    out["span_binding_tf"] = min(
        ((SPAN_DAYS[(symbol.upper(), int(t))], int(t)) for t in tfs))[1]
    return out


def verdict(t_observed: float, n_screened: int, span_days: float, *,
            preregistered: bool = False) -> dict:
    """Judge one observed t. Returns the threshold, the gap, and the Sharpe read."""
    th = threshold(n_screened, span_days, preregistered=preregistered)
    th["t_observed"] = round(float(t_observed), 4)
    th["deflated_t"] = round(float(t_observed) - th["threshold_t"], 4)
    th["clears"] = float(t_observed) > th["threshold_t"]
    th["clears_prereg_floor"] = float(t_observed) > PREREG_FLOOR
    th["implied_annual_sharpe"] = round(
        implied_annual_sharpe(t_observed, span_days), 3)
    return th


def max_n_answerable(span_days: float, assumed_annual_sharpe: float) -> Optional[int]:
    """The SEARCH BUDGET this span can afford, at an assumed true Sharpe.

    This is the inverse of :func:`threshold` and it is the operationally useful
    direction. Invert ``free_t(n) = SR * sqrt(Y)``:

        n_max = exp( (SR^2 * Y) / 2 )

    A strategy whose *true* annualised Sharpe is ``assumed_annual_sharpe``
    produces an expected t of ``SR * sqrt(Y)`` on this span. If that is below
    ``free_t(n)``, the search is wider than the evidence can pay for and the
    cell cannot answer the question regardless of what is true about the market.

    Returns ``None`` when even a single pre-registered hypothesis
    (``free_t`` floor 1.177) is out of reach - i.e. the cell is unanswerable at
    that Sharpe at *any* search width.
    """
    y = span_years(span_days)
    t_exp = float(assumed_annual_sharpe) * math.sqrt(y)
    if t_exp <= PREREG_FLOOR:
        return None
    return int(math.floor(math.exp(t_exp * t_exp / 2.0)))


def budget_table(span_days: float, sharpes=(0.75, 1.0, 1.5, 2.0, 2.5, 3.0)) -> str:
    """Search budget vs assumed true Sharpe, for one span."""
    rows = ["| assumed true annual Sharpe | expected t on this span | max n screenable |",
            "|---|---|---|"]
    y = span_years(span_days)
    for sr in sharpes:
        t_exp = sr * math.sqrt(y)
        n = max_n_answerable(span_days, sr)
        rows.append(f"| {sr:.2f} | {t_exp:.3f} | "
                    f"{'**0 — unanswerable at any width**' if n is None else f'{n:,}'} |")
    return "\n".join(rows)


def topn_threshold(span_days: float, n_reported: int = 10,
                   n_screened: Optional[int] = None) -> dict:
    """The threshold a **top-N list** faces, and why it is not optional.

    To rank a top 10 you must have compared at least 10 candidates, so
    ``n >= n_reported`` by construction - there is no such thing as a top 10 at
    n = 1. That makes the *floor* on a top-10 list's threshold
    ``free_t(10) = 2.146``, and the required annualised Sharpe for the
    number-one row is ``2.146 / sqrt(Y)``.

    ``n_screened`` is the real search width if you know it; it is only ever
    larger than ``n_reported``, so the floor is the most generous reading a
    top-N list can be given.
    """
    n = max(int(n_reported), int(n_screened or n_reported))
    y = span_years(span_days)
    sq = math.sqrt(y)
    ft_floor = free_t(n_reported)
    ft_real = free_t(n)
    return {
        "span_days": round(float(span_days), 2),
        "sqrt_years": round(sq, 4),
        "n_reported": int(n_reported),
        "n_screened": n,
        "free_t_floor_from_list_size": round(ft_floor, 4),
        "free_t_at_actual_search": round(ft_real, 4),
        "required_annual_sharpe_floor": round(ft_floor / sq, 3),
        "required_annual_sharpe_actual": round(ft_real / sq, 3),
    }


def table(cells: Iterable[Tuple[str, Sequence[int]]], n_screened: int) -> str:
    """A markdown table of thresholds, for pasting into a findings file."""
    rows = ["| symbol | timeframes | span (d) | sqrt(y) | free_t | req. ann. Sharpe "
            "| req. Sharpe if pre-reg | t at SR 2.0 |",
            "|---|---|---|---|---|---|---|---|"]
    for sym, tfs in cells:
        r = for_cell(sym, tfs, n_screened)
        rows.append(
            f"| {r['symbol']} | {'+'.join(str(t) + 'm' for t in r['timeframes'])} "
            f"| {r['span_days']:.1f} | {r['sqrt_years']:.3f} | {r['free_t']:.3f} "
            f"| **{r['required_annual_sharpe']:.2f}** "
            f"| {r['required_annual_sharpe_prereg']:.2f} "
            f"| {r['t_at_sharpe_2']:.2f} |")
    return "\n".join(rows)


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) >= 3:
        print(json.dumps(threshold(int(sys.argv[1]), float(sys.argv[2])), indent=1))
    else:
        for n in (1, 100, 1_000, 10_000, 40_000, 100_000, 2_975_629):
            for label, span in (("scalp 5/15/30m", 57.90), ("swing 60/240m", 718.88)):
                r = threshold(n, span)
                print(f"n={n:>9}  {label:<15} free_t={r['free_t']:.3f}  "
                      f"req ann SR={r['required_annual_sharpe']:.2f}  "
                      f"(pre-reg floor needs {r['required_annual_sharpe_prereg']:.2f})")
