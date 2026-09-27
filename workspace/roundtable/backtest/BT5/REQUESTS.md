# BT5 — sub-task requests

`PIPELINE.md` §3 shape. Filed as they arose; work continued rather than stalling on them.

---

## BT5-REQ-1 `python -m pytest -q tests` cannot collect the suite at all

- **Arose in:** BT5 burst 01, running the full suite before finishing as `OWNERSHIP.md`'s
  backtester-test allowance requires.
- **The ask:** route a fix for a module-name collision that currently makes the repo's own test suite
  **uncollectable**, and decide whose it is. Not mine to fix — it is EF6's and EF7's ground.
- **What it is.** `tests/test_ef7_session_window.py:52` does
  `from window import SESSION_WINDOW, SESSION_WINDOW_EXIT, SessionWindow, ...` and receives
  `workspace/roundtable/edge/EF6/code/window.py` instead of `EF7/code/window.py`, because **both
  edge-finders own a file called `code/window.py`** and both insert their own directory into
  `sys.path` at import time. The first insertion wins for the whole process, and `sys.modules` caches
  it, so which module `EF7`'s test gets depends on collection order rather than on its own
  `sys.path.insert`.
  ```
  [measured: python3 -m pytest -q tests
     -> ImportError: cannot import name 'SESSION_WINDOW' from 'window'
        (/home/user/Futures01/workspace/roundtable/edge/EF6/code/window.py)
        Interrupted: 1 error during collection]
  [measured: python3 -m pytest -q tests --ignore=tests/test_ef7_session_window.py
     -> 932 passed in 272.48s]
  ```
- **Why it cannot wait.** A collection error is not one failing test: pytest **interrupts the whole
  run**, so *no* agent can currently discharge "run the full suite before finishing". It is also the
  exact class of failure this repository keeps cataloguing — silent, and with a signature
  (`ImportError` naming the *other* agent's file) that reads like a bug in the importing agent's own
  code. `OWNERSHIP.md`'s per-agent `tests/test_ef<n>_*.py` prefix rule was designed to stop test files
  colliding and it works; **there is no equivalent rule for the `code/` modules those tests import**,
  which is the hole.
- **What it blocks:** every agent's "full suite" obligation. Nothing in BT5's own measurement.
- **My estimate of its size:** small. The narrow fix is one import line in one agent's own test
  (import by file path via `importlib.util.spec_from_file_location`, or a per-agent module prefix such
  as `ef7_window.py`). The general fix is a one-line addition to `OWNERSHIP.md`'s rules:
  **a module under `<agent>/code/` that a repo test imports must carry that agent's prefix in its
  filename.** I did not touch either file.

---

## BT5-REQ-2 record the 60m/240m per-bar activity dispersion and the zero-volume hourly bars

- **Arose in:** BT5 burst 01, measuring the premise of `MAIN-01`'s mechanism on the grid the published
  findings live on.
- **The ask:** two substrate facts about the **frozen `csv/raw` snapshot** belong on the record where
  substrate claims live, and neither is in a file I own.
  1. **Per-bar activity dispersion at 60m/240m is 5.9×–29.4× (p90/p10)** — the same order as the "~30×"
     figure `MAIN-01` was built on, which was a 1-minute measurement on a *different instrument*
     (`data/MGC_1m.csv`, Oanda CFD). So the inequality the mechanism needs is **not** a sub-hourly
     artefact; it is present at the timeframes every `scan_reports/` result was measured at.
  2. **3.55–3.95% of `csv/raw` hourly bars have `volume == 0`** (177–196 bars per symbol), against the
     0.1% R5 measured at 1 minute on `data/archive/` `[repo-verified: research/R5_SCOPE.md:130-133]`.
     **593 of `geo_trades.json`'s 21,954 trades were decided on a zero-volume signal bar.** Any
     volume-clock or dollar-clock construction stalls on such a bar, and `relative_volume` returns
     `None` there `[repo-verified: futures_agents/indicators/volume.py:280]`, so a
     `relative_volume`-gated condition is structurally unevaluable on ~3.7% of hourly bars — which is
     the `VOID`-adjacent distinction `BRIEF.md` added vocabulary for.
  `[measured: python3 workspace/roundtable/backtest/BT5/code/s2.py → s2_report.json.dispersion,
  s2_report.json.coverage]`
- **Why it can wait:** nothing is blocked. But `MGR-T6` is the task that verifies store equivalence
  **per timeframe**, and ADJ-16c already extended it to 1m for exactly this reason; (2) is the same
  shape of fact one timeframe up, and (1) bears on how `MAIN-01`'s closure should be read.
- **What it blocks:** nothing.
- **My estimate of its size:** small — it is two measured numbers, already measured. The judgement of
  where they belong is the manager's.
