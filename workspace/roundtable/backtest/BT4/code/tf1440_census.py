"""Census: which stored results in this repository ran on a 1440m frame?

R4-M3 established that `align_bucket` ignores `minutes` above 1440, so
`FRAMES[1440] = [1440, 7200]` is the daily series twice. The mechanism is
settled; the consequence is not, and the consequence is a count of rows.

The definition used here, stated because it is the load-bearing choice:
a stored row "ran on a 1440m frame" iff it carries a timeframe field whose
value is 1440. Every harness in this repo resolves its frame from a
`FRAMES`-shaped map keyed on that value and keeps only strategies whose
`primary_tf` equals the key, so tf=1440 implies the frame [1440, 7200]
(verified per-harness in the burst note, not assumed here).

Walks every JSON/JSONL under the result stores, recursively, and tallies
every dict that carries a timeframe-ish key. Dependency-free, no network.
"""
import json
import os
import sys
from collections import Counter, defaultdict

TF_KEYS = ("tf", "timeframe", "primary_tf", "tf_min", "exec_tf", "minutes")
ROOTS = ("workspace", "scan_reports", "reports", "research", "docs", "desk")
SKIP_DIRS = {"__pycache__", ".git", "roundtable"}


def walk(obj, hits, path=""):
    """Recursively tally every dict carrying a timeframe key."""
    if isinstance(obj, dict):
        for k in TF_KEYS:
            if k in obj and isinstance(obj[k], (int, float)) and obj[k] is not None:
                hits[(path, k)][int(obj[k])] += 1
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                walk(v, hits, path + "/" + k if len(path) < 60 else path)
    elif isinstance(obj, list):
        for v in obj[:200000]:
            if isinstance(v, (dict, list)):
                walk(v, hits, path + "[]")


def scan_file(fp):
    hits = defaultdict(Counter)
    try:
        if fp.endswith(".jsonl"):
            with open(fp) as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        walk(json.loads(line), hits)
        else:
            walk(json.load(open(fp)), hits)
    except (ValueError, OSError):
        return None
    return hits


def main() -> int:
    only_1440 = "--all" not in sys.argv
    total = Counter()
    per_file = {}
    for root in ROOTS:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fn in filenames:
                if not (fn.endswith(".json") or fn.endswith(".jsonl")):
                    continue
                fp = os.path.join(dirpath, fn)
                hits = scan_file(fp)
                if not hits:
                    continue
                agg = Counter()
                for (_p, _k), c in hits.items():
                    agg.update(c)
                if only_1440 and not (agg.get(1440) or agg.get(7200)):
                    continue
                per_file[fp] = agg
                total.update(agg)
    for fp in sorted(per_file):
        agg = per_file[fp]
        print(f"{agg.get(1440, 0):>7} @1440  {agg.get(7200, 0):>5} @7200   "
              f"(all tf values: {dict(sorted(agg.items()))})  {fp}")
    print()
    print("files touching 1440/7200:", len(per_file))
    print("total records @1440:", total.get(1440, 0), " @7200:", total.get(7200, 0))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
