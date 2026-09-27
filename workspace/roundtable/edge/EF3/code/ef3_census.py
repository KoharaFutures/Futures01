"""EF3 burst 02 - the firing-rate census for MES/MNQ x 60m/240m.

No entries, no exits, no P&L. Every one of the 79 CONDITIONS is evaluated on
every base bar at binding tf=60 and tf=240, and the fires / direction split /
error count recorded. Also records the availability of the objects the known
VOID configurations turn on:

  * snap.opening_range        -> StopKind.RANGE collapse (D49) and liquidity OR
  * prior_profile per tf      -> the six `profile` conditions (D-P1)
  * vwap band width == 0      -> StopKind.VWAP_BAND -> FIXED_TICKS (D45)
  * agreeing_timeframes(top)  -> MULTI_TIMEFRAME signals at the frame top
  * open_interest             -> openinterest group (D47)

Substrate: data/archive 60m, resampled to 240m inside SymbolFrame (verified
bit-identical to the archive's own 240m series - see ef3_substrate.py).
"""
from __future__ import annotations
import json, sys, time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, "/home/user/Futures01")
from futures_agents.config import get_contract
from futures_agents.data.archive import BarArchive
from futures_agents.features import build_symbol_frame
from futures_agents.schema import Direction
from futures_agents.strategies.base import CONDITION_ERRORS, ConditionKind
from futures_agents.strategies.library import CONDITIONS
from futures_agents.timeutil import to_et

OUT = Path("/home/user/Futures01/workspace/roundtable/edge/EF3/out")
TFS = (60, 240)


def census(sym: str) -> dict:
    arch = BarArchive("/home/user/Futures01/data/archive")
    base = arch.load(sym, 60)
    frame = build_symbol_frame(base, list(TFS), get_contract(sym))
    n = len(base.bars)
    CONDITION_ERRORS.clear()

    fires = {tf: Counter() for tf in TFS}
    dirs = {tf: defaultdict(Counter) for tf in TFS}
    evaluable = {tf: 0 for tf in TFS}      # bars where snap.tf(tf) is not None

    # object-availability counters
    avail = Counter()
    t0 = time.time()
    for i in range(n):
        snap = frame.snapshot(i)
        if snap is None:
            continue
        cache = {}
        for tf in TFS:
            if snap.tf(tf) is not None:
                evaluable[tf] += 1
        for name, cond in CONDITIONS.items():
            for tf in TFS:
                res = cond.evaluate(snap, tf, cache)
                if res.triggered:
                    fires[tf][name] += 1
                    dirs[tf][name][res.direction.value] += 1
        # --- objects the VOID configurations depend on
        orr = snap.opening_range
        if orr is not None:
            avail["opening_range_not_none"] += 1
            if orr.size > 0:
                avail["opening_range_size_gt0"] += 1
        for tf in TFS:
            s = snap.tf(tf)
            if s is None:
                continue
            if getattr(s, "prior_profile", None) is not None:
                avail[f"prior_profile_tf{tf}"] += 1
            u1, l1 = s["vwap_u1"], s["vwap_l1"]
            vw = s["vwap"]
            if u1 is None or l1 is None:
                avail[f"vwap_band_none_tf{tf}"] += 1
            elif abs(u1 - l1) < 1e-12:
                avail[f"vwap_band_zero_tf{tf}"] += 1
            if s["atr"]:
                avail[f"atr_present_tf{tf}"] += 1
            if s.last_swing_low is not None and s.last_swing_high is not None:
                avail[f"swings_present_tf{tf}"] += 1
        # multi-timeframe voting from the top of the frame
        for tf in TFS:
            try:
                ag = snap.agreeing_timeframes(from_tf=tf)
            except TypeError:
                ag = None
            if ag is not None:
                voting = ag[1] if isinstance(ag, tuple) and len(ag) > 1 else None
                if voting is not None:
                    avail[f"mtf_voters_tf{tf}_sum"] += int(voting)
                    if int(voting) >= 2:
                        avail[f"mtf_voters_tf{tf}_ge2"] += 1
        if base.bars[i].open_interest is not None:
            avail["open_interest_present"] += 1
        if i and i % 2000 == 0:
            print(f"  {sym} {i}/{n}  {time.time()-t0:.0f}s", flush=True)

    rows = []
    for name, cond in sorted(CONDITIONS.items()):
        r = {"condition": name, "group": cond.group, "kind": cond.kind.value}
        for tf in TFS:
            f = fires[tf][name]
            r[f"fires_{tf}"] = f
            r[f"rate_{tf}"] = f / max(1, evaluable[tf])
            d = dirs[tf][name]
            tot = sum(d.values()) or 1
            r[f"long_share_{tf}"] = d.get("LONG", 0) / tot
            r[f"verdict_{tf}"] = ("VOID" if f == 0 else
                                  "NEAR-VOID" if f / max(1, evaluable[tf]) < 0.002 else
                                  "ALIVE")
        rows.append(r)

    return {
        "symbol": sym, "substrate": "data/archive 60m base, tfs [60,240]",
        "bars": n, "evaluable": evaluable,
        "span_et": [to_et(base.bars[0].ts).isoformat(), to_et(base.bars[-1].ts).isoformat()],
        "conditions": rows,
        "availability": dict(avail),
        "condition_errors": {f"{k[0]}:{k[1]}": v for k, v in CONDITION_ERRORS.items()},
        "elapsed_s": round(time.time() - t0, 1),
    }


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for sym in sys.argv[1:] or ["MES", "MNQ"]:
        res = census(sym)
        (OUT / f"census_{sym}.json").write_text(json.dumps(res, indent=1))
        print(f"{sym}: wrote census, {res['elapsed_s']}s, errors={res['condition_errors']}")
