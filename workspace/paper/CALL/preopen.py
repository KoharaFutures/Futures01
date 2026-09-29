#!/usr/bin/env python3
"""Pre-open review (owner, 2026-09-29 17:53 ET): in the 10 minutes before the 18:00 ET reopen, build
24h / 48h / 72h volume profiles for MGC and MNQ from the desk's 5m bars and list POC, value area and
LVNs nearest the last price, so candidate positions can be drafted with plan_builder before the open.

    python3 workspace/paper/CALL/preopen.py            # prints a report, writes preopen/<date>.md

Method: each 5m bar's volume is spread evenly across the price bins its high-low range covers
(MNQ 5-pt bins, MGC 1-pt bins). POC = busiest bin; value area = 70% of volume grown out from the POC;
LVN = a bin whose 3-bin smoothed volume is a local minimum below 50% of the POC's, with heavier volume on
both sides. Caveat from the hub: LVNs on 5m-built 1-3 day profiles have measured as coin flips; the
60m-built 1-week+ profiles are where the bounce lean was found. This is a map, not an edge.
"""
from __future__ import annotations

import pathlib
import sys
from datetime import datetime, timedelta

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import resolve  # noqa: E402

BIN = {"MNQ": 5.0, "MGC": 1.0}
WINDOWS = (24, 48, 72)


def profile(bars, step):
    vol = {}
    for b in bars:
        lo, hi, v = b["l"], b["h"], float(b.get("v") or 0)
        if v <= 0:
            continue
        k0, k1 = int(lo // step), int(hi // step)
        n = k1 - k0 + 1
        for k in range(k0, k1 + 1):
            vol[k] = vol.get(k, 0.0) + v / n
    return vol


def summarize(vol, step):
    ks = sorted(vol)
    tot = sum(vol.values())
    poc = max(vol, key=vol.get)
    lo = hi = poc
    acc = vol[poc]
    while acc < 0.7 * tot and (lo > ks[0] or hi < ks[-1]):
        dn = vol.get(lo - 1, 0.0) if lo > ks[0] else -1
        up = vol.get(hi + 1, 0.0) if hi < ks[-1] else -1
        if up >= dn:
            hi += 1; acc += max(up, 0)
        else:
            lo -= 1; acc += max(dn, 0)
    sm = {k: (vol.get(k - 1, 0) + vol.get(k, 0) + vol.get(k + 1, 0)) / 3 for k in ks}
    pv = vol[poc]
    lvns = []
    for k in ks[2:-2]:
        if sm[k] < sm[k - 1] and sm[k] <= sm[k + 1] and sm[k] < 0.5 * pv:
            left = max(sm[j] for j in ks if j < k)
            right = max(sm[j] for j in ks if j > k)
            if left > 1.5 * sm[k] and right > 1.5 * sm[k]:
                lvns.append(k)
    mid = lambda k: round((k + 0.5) * step, 2)
    return {"poc": mid(poc), "vah": round((hi + 1) * step, 2), "val": round(lo * step, 2),
            "lvns": [mid(k) for k in lvns], "range": (round(ks[0] * step, 2), round((ks[-1] + 1) * step, 2))}


def main():
    out = [f"# Pre-open review {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}", ""]
    for sym in ("MNQ", "MGC"):
        bars = resolve.load_bars(sym, 5)
        last = bars[-1]
        t_last = datetime.fromisoformat(last["ts"])
        out.append(f"## {sym}: last {last['c']} (5m bar {last['ts']})")
        for h in WINDOWS:
            w = [b for b in bars if datetime.fromisoformat(b["ts"]) > t_last - timedelta(hours=h)]
            s = summarize(profile(w, BIN[sym]), BIN[sym])
            near = sorted(s["lvns"], key=lambda p: abs(p - last["c"]))[:4]
            out.append(f"- **{h}h** ({len(w)} bars, range {s['range'][0]}-{s['range'][1]}): POC {s['poc']} · "
                       f"VAH {s['vah']} · VAL {s['val']} · LVNs nearest price {near}")
        out.append("")
    txt = "\n".join(out)
    d = HERE / "preopen"
    d.mkdir(exist_ok=True)
    (d / f"{datetime.now():%Y-%m-%d}.md").write_text(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
