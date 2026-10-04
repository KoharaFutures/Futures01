"""LTA CONCEPT CALLOUTS — the small shared helpers the desk needs, in one file.

Self-contained on purpose: this repo does not depend on any other repo. Holds
  * bars: the B record, load() from desk/archive/ (optional) + desk/live/ (fetch.py)
  * the futures trading day (the 18:00 ET open belongs to the next day) and ATR14
  * the volume profile (POC, 70% value area, HVN/LVN) and zigzag swing legs
  * contract specs for MNQ / MES / MGC / MCL, and Eastern time
  * a terminal alert renderer (LONG blue, SHORT orange, NO TRADE grey)
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

HERE = pathlib.Path(__file__).resolve().parent
ARCHIVE = HERE / "archive"        # optional long history: <SYM>_<TF>m.jsonl, never rewritten
LIVE = HERE / "live"              # fetch.py cache
ET = ZoneInfo("America/New_York")
ATR_N = 14


# ------------------------------------------------------------------ bars
@dataclass
class B:
    ts: datetime
    o: float
    h: float
    l: float
    c: float
    v: float


def _read(p):
    out = []
    for line in p.read_text().splitlines():
        if line.strip():
            d = json.loads(line)
            if float(d.get("v", 0) or 0) == 0 and d["h"] == d["l"]:
                continue                       # vendor stub
            out.append(B(datetime.fromisoformat(d["ts"]), d["o"], d["h"], d["l"], d["c"], float(d.get("v", 0) or 0)))
    return sorted(out, key=lambda b: b.ts)


def load(sym: str, tf: int):
    """Archive bars (if any), then fetch-cache bars NEWER than the archive's newest."""
    a = ARCHIVE / f"{sym}_{tf}m.jsonl"
    arch = _read(a) if a.exists() else []
    p = LIVE / f"{sym}_{tf}m.jsonl"
    if not p.exists():
        return arch
    cut = arch[-1].ts if arch else None
    return arch + [b for b in _read(p) if cut is None or b.ts > cut]


def tday(ts: datetime):
    """Trading day: the 18:00 ET open belongs to the next calendar day's session."""
    return (ts + timedelta(hours=6)).date()


def atr_series(bars):
    out, trs, prev = [], [], None
    for b in bars:
        tr = b.h - b.l if prev is None else max(b.h - b.l, abs(b.h - prev), abs(b.l - prev))
        trs.append(tr)
        prev = b.c
        out.append(sum(trs[-ATR_N:]) / ATR_N if len(trs) >= ATR_N else None)
    return out


# ------------------------------------------------------------------ volume profile
N_BINS = 80
LVN_RATIO = 0.5          # valley <= 50% of the smaller neighbouring peak
HVN_MIN = 0.25           # a peak must hold >= 25% of the POC's volume
MIN_SEP_BINS = 4
ZIGZAG_ATR = 3.0
LEG_MIN_RANGE = 0.20


@dataclass
class Profile:
    lo: float
    hi: float
    step: float
    vol: list
    poc: float
    vah: float
    val: float
    hvn: list
    lvn: list
    shape: str          # BALANCED / TREND_UP / TREND_DOWN
    net: float


def _thin(idx, sm, sep):
    out = []
    for k in sorted(idx, key=lambda k: -sm[k]):
        if all(abs(k - j) >= sep for j in out):
            out.append(k)
    return sorted(out)


def build_profile(bars):
    """Volume spread evenly over each bar's high-low, smoothed; POC, 70% value area, HVN/LVN."""
    lo, hi = min(b.l for b in bars), max(b.h for b in bars)
    if hi <= lo:
        return None
    step = (hi - lo) / N_BINS
    vol = [0.0] * N_BINS
    for b in bars:
        a = min(N_BINS - 1, int((b.l - lo) / step))
        z = min(N_BINS - 1, int((b.h - lo) / step))
        share = b.v / (z - a + 1) if b.v > 0 else 0
        for k in range(a, z + 1):
            vol[k] += share
    sm = [sum(vol[max(0, k - 1):k + 2]) / len(vol[max(0, k - 1):k + 2]) for k in range(N_BINS)]
    tot = sum(sm)
    if tot <= 0:
        return None
    price = lambda k: lo + (k + 0.5) * step
    pk = max(range(N_BINS), key=sm.__getitem__)
    a = z = pk
    acc = sm[pk]
    while acc < 0.7 * tot and (a > 0 or z < N_BINS - 1):
        up = sm[z + 1] if z < N_BINS - 1 else -1
        dn = sm[a - 1] if a > 0 else -1
        if up >= dn:
            z += 1
            acc += sm[z]
        else:
            a -= 1
            acc += sm[a]
    peaks = [k for k in range(1, N_BINS - 1) if sm[k] >= sm[k - 1] and sm[k] >= sm[k + 1] and sm[k] >= HVN_MIN * sm[pk]]
    peaks = _thin(peaks, sm, MIN_SEP_BINS)
    lvns = []
    for p, q in zip(peaks, peaks[1:]):
        k = min(range(p + 1, q), key=sm.__getitem__, default=None)
        if k is not None and sm[k] <= LVN_RATIO * min(sm[p], sm[q]):
            lvns.append(k)
    net = (bars[-1].c - bars[0].o) / (hi - lo)
    shape = "TREND_UP" if net > 0.5 else "TREND_DOWN" if net < -0.5 else "BALANCED"
    return Profile(lo, hi, step, sm, price(pk), lo + (z + 1) * step, lo + a * step,
                   [price(k) for k in peaks], [price(k) for k in lvns], shape, round(net, 3))


def zigzag_legs(bars, atr):
    """Split bars into swing legs: a new leg starts when price reverses 3 ATR (and 20% of range)."""
    if not bars or not atr:
        return []
    th = max(ZIGZAG_ATR * atr, LEG_MIN_RANGE * (max(b.h for b in bars) - min(b.l for b in bars)))
    legs, piv, piv_p, direction = [], 0, bars[0].c, 0
    ext_i, ext_p = 0, bars[0].c
    for i, b in enumerate(bars):
        if direction == 1 and b.h > ext_p:
            ext_i, ext_p = i, b.h
        if direction == -1 and b.l < ext_p:
            ext_i, ext_p = i, b.l
        if direction == 0:
            if b.h - piv_p >= th:
                direction, ext_i, ext_p = 1, i, b.h
            elif piv_p - b.l >= th:
                direction, ext_i, ext_p = -1, i, b.l
            continue
        if direction == 1 and ext_p - b.l >= th:
            legs.append(("UP", piv_p, ext_p, bars[piv].ts, bars[ext_i].ts))
            piv, piv_p, direction, ext_i, ext_p = ext_i, ext_p, -1, i, b.l
        elif direction == -1 and b.h - ext_p >= th:
            legs.append(("DOWN", piv_p, ext_p, bars[piv].ts, bars[ext_i].ts))
            piv, piv_p, direction, ext_i, ext_p = ext_i, ext_p, 1, i, b.h
    if direction:
        legs.append(("UP" if direction == 1 else "DOWN", piv_p, ext_p, bars[piv].ts, bars[ext_i].ts))
    return legs


# ------------------------------------------------------------------ contracts & time
@dataclass(frozen=True)
class Contract:
    symbol: str
    tick_size: float
    point_value: float
    round_turn_cost: float     # 2 x (commission 0.35 + exchange fee 0.37) + 1 tick slippage
    group: str


CONTRACTS = {
    "MNQ": Contract("MNQ", 0.25, 2.0, 1.94, "US_INDEX"),
    "MES": Contract("MES", 0.25, 5.0, 2.69, "US_INDEX"),
    "MGC": Contract("MGC", 0.10, 10.0, 2.44, "METALS"),
    "MCL": Contract("MCL", 0.01, 100.0, 2.44, "ENERGY"),
}


def get_contract(sym: str) -> Contract:
    return CONTRACTS[sym.upper()]


def correlated_symbols(sym: str):
    g = get_contract(sym).group
    return [s for s, c in CONTRACTS.items() if c.group == g and s != sym.upper()]


def now_et() -> datetime:
    return datetime.now(tz=ET)


# ------------------------------------------------------------------ terminal alert
class Priority:
    LONG, SHORT, NO_TRADE = "LONG", "SHORT", "NO_TRADE"


_BG = {"LONG": "\033[48;5;27;97m", "SHORT": "\033[48;5;208;30m", "NO_TRADE": "\033[48;5;250;30m"}


def alert(priority: str, headline: str, body: str = "") -> str:
    """Print a callout, Eastern-time stamp first. Colour only on a real terminal."""
    stamp = now_et().strftime("[%Y-%m-%d %H:%M:%S %Z (%a)]")
    color = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
    head = f"{_BG[priority]} {headline} \033[0m" if color else f"*** {headline} ***"
    text = f"{stamp}\n  {head}\n{body}"
    print(text)
    return text
