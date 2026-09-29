"""BT6 — blast radius of R6-D1: how much of the stored corpus is a daily `vwap` result?

Three counts, deliberately separate, because they answer three different
questions and conflating them is how an audit over-retracts:

  1. **Certain.** Stored rows with `tf == 1440` whose `group == "VWAP"`.
     `vwap` is VWAP's only `required_groups` entry
     (`combinator.py:189-200`), so every such row holds a `vwap` condition by
     construction. No inference.
  2. **Possible.** Stored rows with `tf == 1440` in the nine other templates
     that offer `vwap` as an *optional* group. The stores record `group` and
     not the condition names, so membership cannot be read off disk — it is
     bounded below by 0 and above by the count, and §3 measures where in that
     range it actually lands by re-generating the population.
  3. **Unaffected.** Stored rows with `tf == 1440` in the three templates that
     cannot draw a `vwap` condition at all (BREAKOUT, MOMENTUM, SUPPLY_DEMAND).

A row "ran at 1440m" iff it carries a timeframe field equal to 1440. Every
harness here resolves its frame from a `FRAMES`-shaped map keyed on that value
and keeps only `primary_tf == tf` (R6-M1), so `tf == 1440` implies the frame
`[1440, 7200]`. The scan is structural, not semantic: it walks every dict in
every JSON/JSONL under the result stores and needs no per-harness knowledge.

Dependency-free, no network. Reads only; writes under `backtest/BT6/out/`.

Usage:
    PYTHONPATH=. python3 workspace/roundtable/backtest/BT6/code/vwap_blast_radius.py
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

OUT = os.path.join(os.path.dirname(__file__), "..", "out")

TF_KEYS = ("tf", "timeframe", "primary_tf", "tf_min", "exec_tf", "minutes")
GROUP_KEYS = ("group", "strategy_group", "grp")
COND_KEYS = ("signal_conditions", "conditions", "signals", "filter_conditions",
             "filters", "rule", "rules", "names")
ROOTS = ("workspace", "scan_reports", "reports", "research", "docs", "desk")
SKIP_DIRS = {"__pycache__", ".git", "roundtable", ".pytest_cache"}

VWAP_CONDITIONS = ("above_vwap", "vwap_band1_bounce", "vwap_band_extension",
                   "vwap_proximity", "vwap_reclaim")


def classify(group: Optional[str], requires: frozenset, offers: frozenset,
             never: frozenset) -> str:
    if group in requires:
        return "certain"
    if group in offers:
        return "possible"
    if group in never:
        return "unaffected"
    return "no_group_field"


def walk(obj, sink, group_ctx=None, tf_ctx=None):
    """Tally every dict that carries a timeframe, with the nearest group label.

    `group_ctx`/`tf_ctx` inherit downward: a cell keyed `MGC_1440m_274d` often
    records `tf` once at the top and `group` on each row beneath it, so a row
    seen alone would look timeframe-less.
    """
    if isinstance(obj, dict):
        tf = tf_ctx
        for k in TF_KEYS:
            v = obj.get(k)
            if isinstance(v, (int, float)) and v is not None and k != "exec_tf":
                tf = int(v)
                break
        grp = group_ctx
        for k in GROUP_KEYS:
            v = obj.get(k)
            if isinstance(v, str) and v.isupper():
                grp = v
                break
        conds: List[str] = []
        for k in COND_KEYS:
            v = obj.get(k)
            if isinstance(v, (list, tuple)):
                conds += [x for x in v if isinstance(x, str)]
            elif isinstance(v, str):
                conds.append(v)
        is_row = any(k in obj for k in ("exp", "expectancy", "win", "t", "n", "id"))
        if tf is not None and is_row:
            sink.append((tf, grp, tuple(sorted(set(
                c for c in conds if c in VWAP_CONDITIONS)))))
        for v in obj.values():
            if isinstance(v, (dict, list)):
                walk(v, sink, grp, tf)
    elif isinstance(obj, list):
        for v in obj:
            if isinstance(v, (dict, list)):
                walk(v, sink, group_ctx, tf_ctx)


def scan_file(fp) -> Optional[List[Tuple[int, Optional[str], Tuple[str, ...]]]]:
    sink: List[Tuple[int, Optional[str], Tuple[str, ...]]] = []
    try:
        if fp.endswith(".jsonl"):
            with open(fp) as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        walk(json.loads(line), sink)
        else:
            with open(fp) as fh:
                walk(json.load(fh), sink)
    except (ValueError, OSError, RecursionError):
        return None
    return sink


def main() -> int:
    from futures_agents.strategies.combinator import TEMPLATES

    requires = frozenset(t.group for t in TEMPLATES if "vwap" in t.required_groups)
    offers = frozenset(t.group for t in TEMPLATES
                       if "vwap" in t.optional_groups and t.group not in requires)
    never = frozenset(t.group for t in TEMPLATES
                      if t.group not in requires and t.group not in offers)
    print(f"requires `vwap`:  {sorted(requires)}")
    print(f"offers `vwap`:    {sorted(offers)}")
    print(f"cannot draw it:   {sorted(never)}")
    print()

    per_file: Dict[str, Counter] = {}
    total = Counter()
    by_group_1440 = Counter()
    named_vwap_1440 = Counter()
    files_1440: List[str] = []
    for root in ROOTS:
        full_root = os.path.join(REPO, root)
        if not os.path.isdir(full_root):
            continue
        for dirpath, dirnames, filenames in os.walk(full_root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                if not (fn.endswith(".json") or fn.endswith(".jsonl")):
                    continue
                fp = os.path.join(dirpath, fn)
                rows = scan_file(fp)
                if not rows:
                    continue
                c = Counter()
                for tf, grp, vw in rows:
                    c[tf] += 1
                    if tf == 1440:
                        klass = classify(grp, requires, offers, never)
                        by_group_1440[(grp, klass)] += 1
                        if vw:
                            named_vwap_1440[vw] += 1
                if c.get(1440):
                    rel = os.path.relpath(fp, REPO)
                    files_1440.append(rel)
                    per_file[rel] = c
                total.update(c)

    print(f"result rows found, all timeframes: {sum(total.values())}")
    print(f"  by timeframe: {dict(sorted(total.items()))}")
    print(f"\nfiles holding >=1 row at tf=1440: {len(files_1440)}")
    for rel in sorted(per_file):
        print(f"  {per_file[rel][1440]:>7} @1440   {rel}")

    print("\nrows at tf=1440, by group and vwap-reachability:")
    klass_total = Counter()
    for (grp, klass), n in sorted(by_group_1440.items(),
                                  key=lambda kv: (-kv[1], str(kv[0]))):
        print(f"  {n:>7}  {str(grp):18s} {klass}")
        klass_total[klass] += n
    print(f"\n  totals: {dict(klass_total)}")
    if named_vwap_1440:
        print("\n  rows that NAME a vwap condition explicitly at 1440m:")
        for vw, n in sorted(named_vwap_1440.items()):
            print(f"    {n:>7}  {list(vw)}")
    else:
        print("\n  no stored row at 1440m names its conditions -- the stores"
              " record `group` only, so the `possible` class cannot be resolved"
              " from disk. See the generation measurement.")

    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(OUT, "vwap_blast_radius.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump({
            "requires": sorted(requires), "offers": sorted(offers),
            "never": sorted(never),
            "rows_by_tf": {str(k): v for k, v in sorted(total.items())},
            "files_with_1440_rows": {k: per_file[k][1440] for k in sorted(per_file)},
            "rows_1440_by_group": {f"{g}|{k}": n
                                   for (g, k), n in by_group_1440.items()},
            "rows_1440_by_class": dict(klass_total),
            "rows_1440_naming_vwap_conditions": {"|".join(k): v
                                                 for k, v in named_vwap_1440.items()},
        }, fh, indent=1, sort_keys=True)
    print(f"\nwrote {os.path.relpath(dest, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
