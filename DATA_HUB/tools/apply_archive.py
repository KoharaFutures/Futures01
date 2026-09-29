#!/usr/bin/env python3
"""Move ARCHIVE rows of the sweep manifests into Archived_Do_Not_Refference/ and index them.

Each manifest is a TSV with header `path  decision  reason  summary`. Every ARCHIVE path is
moved with `git mv` to Archived_Do_Not_Refference/<same relative path>, so provenance stays
readable, and Archived_Do_Not_Refference/ARCHIVE_INDEX.md is (re)written listing every
archived path with its one-line summary - that index is how agents learn what is in the
archive WITHOUT opening it.

    python3 DATA_HUB/tools/apply_archive.py DATA_HUB/sources/*_manifest.tsv --dry-run
    python3 DATA_HUB/tools/apply_archive.py DATA_HUB/sources/*_manifest.tsv

Idempotent: a path already moved is indexed again from the manifest and skipped.
Nested rows are handled: if a directory is archived, rows for files inside it are only indexed.
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
ARCH = "Archived_Do_Not_Refference"
HEADER = """# Archived_Do_Not_Refference — index

**Agents: do not open, search or re-analyse anything in this folder.** Every item here was
reviewed during the 2026-09-29 consolidation; its findings are already folded into
`DATA_HUB/` (start at `DATA_HUB/README.md`). The one-line summaries below tell you what each
item contained so you never need to re-explore it. If you believe something here is needed,
say so to the owner instead of reading it.

Paths are the ORIGINAL repo paths; the file now lives at `Archived_Do_Not_Refference/<path>`.

| original path | what it contained | why archived |
|---|---|---|
"""


def read_rows(paths):
    rows = []
    for p in paths:
        with open(p, newline="") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                if r.get("path") and r.get("decision", "").strip().upper() == "ARCHIVE":
                    r["path"] = r["path"].strip().rstrip("/")
                    if any(ch in r["path"] for ch in "*?["):
                        hits = sorted(str(q.relative_to(ROOT)) for q in ROOT.glob(r["path"]))
                        hits += sorted(str(q.relative_to(ROOT / ARCH)) for q in (ROOT / ARCH).glob(r["path"]))
                        rows += [dict(r, path=h) for h in dict.fromkeys(hits)]
                    else:
                        rows.append(r)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifests", nargs="+")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--extra", nargs="*", default=[], help="extra 'path|summary|reason' rows")
    a = ap.parse_args()
    rows = read_rows(a.manifests)
    for e in a.extra:
        p, summ, why = (e.split("|") + ["", ""])[:3]
        rows.append(dict(path=p.rstrip("/"), summary=summ, reason=why))
    seen, uniq = set(), []
    for r in sorted(rows, key=lambda r: r["path"]):
        if r["path"] not in seen:
            seen.add(r["path"])
            uniq.append(r)
    moved = skipped = missing = 0
    done_dirs: list[str] = []
    for r in uniq:
        p = r["path"]
        if any(p.startswith(d + "/") for d in done_dirs):
            continue                       # inside a directory already moved
        src, dst = ROOT / p, ROOT / ARCH / p
        if not src.exists():
            if dst.exists():
                skipped += 1
            else:
                missing += 1
                print(f"missing: {p}", file=sys.stderr)
            if src.is_dir() or dst.is_dir():
                done_dirs.append(p)
            continue
        if src.is_dir():
            done_dirs.append(p)
        if a.dry_run:
            print(f"would move {p}")
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            tracked = subprocess.run(["git", "ls-files", "--error-unmatch", p], cwd=ROOT,
                                     capture_output=True).returncode == 0 or src.is_dir()
            cmd = ["git", "mv", "-k", p, str(pathlib.Path(ARCH) / p)] if tracked else None
            if cmd:
                subprocess.run(cmd, cwd=ROOT, check=True)
            if src.exists():               # untracked leftovers (e.g. ignored files) move by rename
                src.rename(dst) if not dst.exists() else None
        moved += 1
    idx = [HEADER.rstrip("\n")]
    for r in uniq:
        s = (r.get("summary") or "").replace("|", "/").strip()
        w = (r.get("reason") or "").replace("|", "/").strip()
        idx.append(f"| `{r['path']}` | {s} | {w} |")
    if not a.dry_run:
        (ROOT / ARCH).mkdir(exist_ok=True)
        (ROOT / ARCH / "ARCHIVE_INDEX.md").write_text("\n".join(idx) + "\n")
    print(f"moved {moved}, already archived {skipped}, missing {missing}, indexed {len(uniq)}")


if __name__ == "__main__":
    main()
