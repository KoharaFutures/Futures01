#!/usr/bin/env python3
"""Step the replay one bar at a time and HALT the moment an armed condition fires.

WHY THIS EXISTS. Five separate times this desk specified a trigger correctly, then
advanced past it in a chunk and never saw it fire: bars 414, 429, 607/612,
1515/1535/1538, and 1619. Each time the diagnosis was written down and a smaller
chunk resolved on, and each time the next burst repeated it - the last one INSIDE
the n<=10 rule, because the trigger fired on the second bar of a ten-bar chunk.

The arithmetic is unforgiving: a one-bar confirmation has to be observed ON the
confirmation bar, so any n>1 misses it with probability about (n-1)/n. No rule
about chunk size fixes that; only stepping one bar at a time does, and a human
intention to step one bar at a time has now failed five times. So the cadence is
enforced by this program instead.

It shells out to the harness CLI exactly as a hand-typed `next --id R1 --n 1`
would, one bar per call, and reads the appended bar from visible.jsonl. It cannot
see further ahead than doing it by hand would: the condition is evaluated on the
bar just revealed, and the fill would land on the NEXT bar, which is still unknown.

USAGE
  python3 watch.py --id R1 --budget 60 \
      --cond "close_above:6049.13:LONG"  \
      --cond "close_below:6020.00:SHORT"
Each --cond is kind:price:side. Kinds:
  close_above / close_below   a bar CLOSES beyond the price
  touch_above / touch_below   a bar's high/low reaches the price
It halts on the first match, prints the bar and the side, and leaves the cursor on
that bar so `order` fills at the next open. With no match it stops at the budget.
"""
import argparse, json, os, subprocess, sys

D = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(D, "..", "..", "..", ".."))  # R1/REPLAY/paper/workspace -> repo root
HARNESS = os.path.join(REPO, "workspace", "roundtable", "lib", "replay.py")
VIS = os.path.join(D, "visible.jsonl")

KINDS = {
    "close_above": lambda b, p: b["c"] > p,
    "close_below": lambda b, p: b["c"] < p,
    "touch_above": lambda b, p: b["h"] >= p,
    "touch_below": lambda b, p: b["l"] <= p,
}


def nbars():
    with open(VIS) as f:
        return sum(1 for _ in f)


def last_bar():
    with open(VIS) as f:
        return json.loads(f.readlines()[-1])


def step(rid):
    """One bar. FAILS LOUDLY - the first version returned stdout+stderr and let the
    caller filter it for interesting lines, so when the harness path was wrong by
    one directory every step failed silently and the watcher 'halted' on the bar it
    had started from. A step that does not advance the tape is not a quiet event."""
    before = nbars()
    r = subprocess.run([sys.executable, HARNESS, "next", "--id", rid, "--n", "1"],
                       capture_output=True, text=True, cwd=REPO)
    if r.returncode != 0:
        sys.exit(f"harness step FAILED rc={r.returncode}\n{r.stdout}\n{r.stderr}")
    if nbars() != before + 1:
        sys.exit(f"harness step did not advance the tape "
                 f"({before} -> {nbars()} bars). Refusing to evaluate conditions "
                 f"against a bar that was already visible.\n{r.stdout}\n{r.stderr}")
    return r.stdout + r.stderr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", default="R1")
    ap.add_argument("--budget", type=int, default=50)
    ap.add_argument("--cond", action="append", default=[])
    a = ap.parse_args()

    conds = []
    for c in a.cond:
        kind, price, side = c.split(":")
        if kind not in KINDS:
            sys.exit(f"unknown condition kind {kind!r}; known: {', '.join(KINDS)}")
        conds.append((kind, float(price), side.upper()))
    if not conds:
        sys.exit("no --cond given; watch.py exists to halt on a condition")

    if not os.path.exists(HARNESS):
        sys.exit(f"harness not found at {HARNESS} - check the path arithmetic")
    print(f"watching from bar {nbars()-1}, budget {a.budget} bars, "
          f"{len(conds)} condition(s):")
    for k, p, s in conds:
        print(f"   {k} {p} -> {s}")

    for n in range(a.budget):
        out = step(a.id)
        # the harness prints its own FILLED/CLOSED lines - surface them verbatim
        for line in out.splitlines():
            if any(t in line for t in ("FILLED", "CLOSED", "REFUSED", "absorbing",
                                       "FORBIDDEN", "Traceback", "Error")):
                print(f"   harness: {line.strip()}")
        b = last_bar()
        i = nbars() - 1
        for kind, price, side in conds:
            if KINDS[kind](b, price):
                print(f"\n>>> HALT at bar {i}  {b['ts']}")
                print(f"    o {b['o']} h {b['h']} l {b['l']} c {b['c']} v {int(b['v'])}")
                print(f"    fired: {kind} {price}  ->  {side}")
                print(f"    cursor is on this bar; `order` now fills at the NEXT open.")
                print(f"    RE-CHECK before ordering: the 0.5-ATR floor, the R:R at the")
                print(f"    actual fill (a gap below 1.5 voids the plan), rule 5's")
                print(f"    15:00-16:00 window, and bars left to the 16:00 flat.")
                return 0
    print(f"\nbudget spent, no condition fired. cursor at bar {nbars()-1} "
          f"({last_bar()['ts']}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
