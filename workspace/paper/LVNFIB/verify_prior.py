#!/usr/bin/env python3
"""Assert that the desk's live logic still reproduces the prior CHARTER.md §1 arms arm A on.

selftest.py PRINTS its four checks but never asserts, so its exit code is not a verdict.
This one is: exit 0 only if the armed prior reproduces to the digit, else exit 3.
"""
from __future__ import annotations

import re
import subprocess
import sys
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
EXPECT = {"levels_mismatch": 0, "triggers": 164, "symdiff": 0,
          "limit_n": 24, "limit_r": "+0.2379", "market_n": 33, "market_r": "+0.4324"}

r = subprocess.run([sys.executable, str(HERE / "selftest.py")],
                   capture_output=True, text=True, cwd=HERE.parents[2])
out = r.stdout
if r.returncode != 0:
    print(f"VERIFY FAIL: selftest crashed rc={r.returncode}\n{r.stderr[-800:]}")
    sys.exit(4)

fail = []
m = re.search(r"levels: (\d+) trading days checked, (\d+) mismatch", out)
if not m or int(m.group(2)) != EXPECT["levels_mismatch"]:
    fail.append(f"levels mismatches != 0 ({m.group(2) if m else '?'})")
m = re.search(r"desk (\d+), backtest (\d+), symmetric difference (\d+)", out)
if not m or (int(m.group(1)), int(m.group(2)), int(m.group(3))) != \
        (EXPECT["triggers"], EXPECT["triggers"], EXPECT["symdiff"]):
    fail.append(f"trigger set moved: {m.groups() if m else '?'} vs "
                f"({EXPECT['triggers']}, {EXPECT['triggers']}, 0)")
m = re.search(r"OOS limit\s*: n=(\d+) avgR=([+-][\d.]+)", out)
if not m or (int(m.group(1)), m.group(2)) != (EXPECT["limit_n"], EXPECT["limit_r"]):
    fail.append(f"armed arm-A prior moved: {m.groups() if m else '?'} vs "
                f"({EXPECT['limit_n']}, {EXPECT['limit_r']})")
m = re.search(r"OOS market: n=(\d+) avgR=([+-][\d.]+)", out)
if not m or (int(m.group(1)), m.group(2)) != (EXPECT["market_n"], EXPECT["market_r"]):
    fail.append(f"arm A-mkt prior moved: {m.groups() if m else '?'}")
m = re.search(r"targets booked on the fill bar = (\d+)", out)
if not m or int(m.group(1)) != 0:
    fail.append("look-ahead: targets booked on a limit's fill bar != 0")

if fail:
    print("VERIFY FAIL - do not trade this desk (CHARTER.md: live logic must match "
          "the backtest that produced its prior):")
    for f in fail:
        print(f"  - {f}")
    print(out)
    sys.exit(4)
print("verify_prior: OK - arm A reproduces n=24 +0.2379R t +1.027 win 50.0% payoff 1.58; "
      "164/164 triggers, symdiff 0, 0 look-ahead targets")
sys.exit(0)
