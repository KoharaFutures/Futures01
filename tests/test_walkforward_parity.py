"""DATA_HUB/tools/walkforward.py must reproduce the REPLAY harness exactly.

REPLAY R1 took two real trades through `workspace/roundtable/lib/replay.py`. The engine,
fed the same two orders, must return the same R (+1.8949, +1.8540, both TARGET). Its
legacy-placebo mode must reproduce the harness placebo, including the -0.0671R instant
scratch that exposes finding F1 (the harness placebo reused absolute stop/target prices).
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "DATA_HUB" / "tools"))


def test_engine_reproduces_replay_r1_trades():
    wf = pytest.importorskip("walkforward")
    sp = wf.R.spec("MES")
    bars = wf.R.source_bars("MES", 60)
    if len(bars) < 1500:
        pytest.skip("MES 60m archive too short")
    fx = {452: {"side": "SHORT", "stop": 5804.0, "target": 5768.0},
          1339: {"side": "SHORT", "stop": 5985.5, "target": 5950.0}}
    res = wf.run(bars, "MES", None, wf.Ctx(bars, "MES", 60), sp, end=1500, legacy_placebo=True, fixture=fx)
    assert [(t["r"], t["reason"]) for t in res["trades"]] == [(1.8949, "TARGET"), (1.854, "TARGET")]
    assert all(t["placebo"]["LONG"] == -0.0671 for t in res["trades"])


def test_view_blocks_lookahead():
    wf = pytest.importorskip("walkforward")
    v = wf.View([{"c": 1}, {"c": 2}, {"c": 3}], 1)
    assert v[1]["c"] == 2
    with pytest.raises(IndexError):
        v[2]
    with pytest.raises(IndexError):
        v[0:3]
