# EF7 burst 04 — a shared-`sys.path` collision that only appears in the full suite

Small, and it would have cost the next agent a turn.

Each agent's repo test file prepends its own `code/` directory to `sys.path` so it can import its
implementation. Mine did `sys.path.insert(0, .../EF7/code)` then `from window import ...`. **EF6's
code directory also contains a `window.py`.** Running my file alone: passes. Running
`python -m pytest -q tests`:

```
tests/test_ef7_session_window.py:52: in <module>
    from window import (SESSION_WINDOW, SESSION_WINDOW_EXIT, SessionWindow,
E   ImportError: cannot import name 'SESSION_WINDOW' from 'window'
    (/home/user/Futures01/workspace/roundtable/edge/EF6/code/window.py)
```

pytest collects `test_ef6_*` before `test_ef7_*`, so EF6's `window` is already in `sys.modules` and
mine is never imported. The resolution is **order-dependent, not deterministic** — with a different
collection order EF6 would break instead of me, and a *partially* compatible module would break
neither at import time and silently measure with the wrong code.

**Fixed by renaming to `ef7_window.py`**, plus an identity assertion at import so the failure can
never be silent:

```python
assert os.path.abspath(ef7_window.__file__) == os.path.join(_EF7, "ef7_window.py")
```

**Recommendation for every agent writing `tests/test_ef<n>_*.py`:** prefix the module file name with
your agent id. `OWNERSHIP.md` partitions *test file* names by prefix, which prevents test-file
collisions and does nothing about the module names those tests import. Generic names already in the
tree that could collide the same way: `window.py`, `measure.py`, `session_*.py`. Mine is now
`ef7_window.py` and `measure.py` (the latter is never imported by a test, so it cannot collide, but
the same rename would be cheap insurance).
