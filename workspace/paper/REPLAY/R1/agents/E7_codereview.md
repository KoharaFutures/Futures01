# E7 — correctness review of the REPLAY desk's own tooling

Scope: `view.py`, `levels.py`, `scenario.py`, `missed.py`, `watch.py`, `mode.py`, and the five
agent scripts `agents/A_grid.py`, `agents/C_merge.py`, `agents/C_regime.py`, `agents/C_shape.py`,
`agents/D_discretion.py`. Read-only. Nothing fixed, nothing committed, no cursor advanced.
Numbers below come from running the pure readers (`levels.py`, `view.py`, `scenario.py`,
`C_regime.py`, `A_grid.py`) and from scratch instrumentation; `missed.py` was **not** run because
it rewrites `missed.jsonl`, so its figures are read off the shipped `missed.jsonl` instead.

**34 findings: 5 critical, 8 major, 10 moderate, 11 minor/latent.**
Each is tagged **NUMBER** (it changes a published figure) or **LABEL** (the arithmetic is right,
the description is not). The brief's four known defects were all of the second kind shading into
the first; so are most of these.

---

## CRITICAL

### C1. `scenario.py:59-60` — the map's headline odds are constants no shipped code can regenerate  **NUMBER**

`P1_BOUNCE, P1_BREAK = 0.457, 0.543` are published as measured ("fresh swing extreme n=162
bounce 45.7% break 54.3%", docstring line 17) and drive the per-level advice
`(BREAK is the majority case)`.

`levels.py study()` line 141 is `if touches < 2: continue`. **The 1-touch bucket cannot be
produced by the shipped code at all.** Whatever measured n=162 was a transient edit that is not
in the lane.

Worse, the control cannot produce it either: `levels.py:136` draws
`rng.choice([2, 2, 3, 4])` — the random lines are **never** 1-touch. Instrumented over today's
tape: 1-touch candidates dropped by the `touches < 2` filter — **detected 18,895 (58.7% of all
candidates), random 0 (0.0%).** So the docstring's claim that the fresh-extreme break rate is
"the largest deviation from the random control anywhere in the study, about 9 points below it"
compares a **1-touch treatment against a 2+-touch control**. It is the sample/control asymmetry
of defect 4, sitting under the study's one positive result.

Today's map (run just now) shows four levels. **All four are 1-touch.** Every odds line printed
in the live scenario map today comes from these two unreproducible constants.

### C2. `missed.py:54-60` `session_end()` — silently rolls the exit into the *next* session on truncated days  **NUMBER**

`session_end` scans forward for the first ET hour `"16"`. Three ET dates in `visible.jsonl` have
no 16:00 bar: **2024-11-29** and **2024-12-24** (bars 09:00-12:00 only) and **2025-01-09**
(00:00-09:00, then 18:00). On those days the scan runs past the end of the day, past the
maintenance halt, and in two cases past a weekend.

- **30 control bars** have a `session_end` more than 22 bars forward; **max span 38 bars.**
- Stand-down **bar 874** (`2024-11-27T19:00`) exits at **`2024-12-02T16:00`** — 32 bars and five
  calendar days later, across Thanksgiving and the weekend. `missed.jsonl` publishes that row as
  `"best_r": 2.0, "exit_reason": "TARGET"`. A "2R I missed" that is in fact a five-day hold.

The same function, verbatim, is in `A_grid.py:79-91` and `C_regime.py:105-109`, so the geometry
sweep and the pattern sweep carry it too. The brief asked what happens "when the search runs past
the end of the tape" — that case is handled (returns `None` → PENDING). The unhandled case is the
search running past the end of the *day*.

### C3. `C_regime.py:293` — the placebo z omits the real arm's sampling error entirely  **NUMBER**

```python
z = (real - st.mean(trials))/st.pstdev(trials)
```

`pstdev(trials)` is the spread of 40 *placebo trial means*. That is the standard error of one arm.
The real arm is treated as having zero variance.

| tier | n | real mean | per-trade sd | real SE | placebo trial-mean sd | reported z | correct z |
|---|---|---|---|---|---|---|---|
| A | 444 | +0.0247R | 1.313 | 0.0623 | 0.056 | **+0.72** | **+0.48** |
| B | 92 | −0.0900R | 1.236 | 0.1288 | 0.112 | (same form) | ~0.66× as large |

The label "placebo-sd" is literally accurate about the denominator, but the line above it reads
`difference +0.040R = +0.72 placebo-sd` and that is what gets quoted. Magnitude overstated ~1.5×
on both tiers.

### C4. `C_regime.py:278-289` — the placebo is filtered differently from the treatment  **NUMBER**

`filt()` (line 155) rejects three things: (a) fill hour 15/16, (b) stop below 0.5×ATR,
(c) bars 1146-1158, the known roll-merge. **The placebo applies only (a).**

- **11 of the 13 corrupted roll-merge bars are inside the placebo draw range.** Those bars have an
  84-point mean range against a stop sized from a normal ATR — near-certain −1R. The treatment
  excludes them by name; the control draws them.
- The placebo draws entry bars **uniformly over the clock**, while real signals cluster in RTH:

| | 07 ET | 09 ET | 10 ET | 12 ET | each hour |
|---|---|---|---|---|---|
| Tier B real fills | 10% | 10% | **17%** | 10% | — |
| placebo pool | — | — | — | — | **5% flat** |

Both asymmetries push the placebo mean down, i.e. both flatter the real arm. The comment at 271-272
claims "Same side mix, same stop sizes, same engine, random entry bars" — the side mix and stop
sizes are matched; the *eligibility filter* and the *time-of-day distribution* are not.

### C5. `missed.py:233` — `ARMED` is keyed by decision bar, tested against fill bar; the class is empty  **LABEL**

```python
ARMED = {414, 429, 607, 612, 1515, 1535, 1538, 1502}   # from NOTES.md, by fill bar
...
kind = "ARMED" if f in ARMED else ...
```

`f = c["visible_bars"]`, and `visible_bars == bar_index + 1` for all 45 callouts (verified) — `f`
is the **fill** bar, one past the decision bar. `ARMED` holds decision-bar indices (NOTES calls
them "bar 414", "bar 429"), and in any case none of `{414,429,607,612,1502,1515,1535,1538}` nor
their successors appear in the stand-down fill-bar list.

Shipped `missed.jsonl`: **`UNNAMED 20, NONE 13, REVERSAL 9, ARMED 0`.** The docstring calls ARMED
"A genuine process failure; the fix is cadence" — the one taxonomy class that would trigger a
process change cannot be emitted. The R figures are unaffected; the classification is.

---

## MAJOR

### M6. `levels.py:143,149` — the per-horizon dedupe fires for the control and never for the treatment  **NUMBER**

```python
key = round(L / max(band, 0.25))          # band = BAND_ATR * atr(i-1), changes every bar
if i - active.get(key, -99) < HORIZON: continue   # "one test per level per horizon"
```

A stable real level divided by a *moving* band maps to a different key on almost every bar, so it
never collides with itself. Random lines are fresh draws each bar and collide by chance.
Instrumented on today's tape:

| arm | candidate level-bars | dropped by `touches<2` | tests | **suppressed by the dedupe** |
|---|---|---|---|---|
| DETECTED | 32,195 | 18,895 (58.7%) | 176 | **0** |
| RANDOM | 16,320 | 0 (0.0%) | 205 | **18** |

"One test per level per horizon" is a rule the control obeys and the treatment does not. It sets
the published n (176 vs 205) and therefore both arms' rates.

### M7. `missed.py:97-100` `is_pivot` — a bar that is both a window low and a window high is silently reported LOW  **NUMBER**

```python
if abs(lo - f) <= tol: return "LOW"
if abs(hi - f) <= tol: return "HIGH"
```

With `tol=1` in a 7-bar window, **66 of 1685 bars (3.9%) satisfy both**, and all 66 return `"LOW"`
purely from statement order. The tag is not cosmetic: at lines 223 and 226-227 it selects the trade
*direction* for the published "trade-with-the-turn" figure. Shipped `missed.jsonl` tags
`HIGH 11 / LOW 5 / None 26`.

### M8. `missed.py:218-231` — the "with the turn" statistic is hindsight, and unlike its sibling arm it is not labelled so  **LABEL**

`is_pivot(f)` inspects bars `f-3 .. f+3` (line 91). The docstring is honest that it looks forward.
The brief asked whether it is ever used for a decision — it is used for one: line 226 picks the
trade side from it.

```python
piv_al = [(e["long"][0] if e["pivot"] == "LOW" else e["short"][0]) for c, e in piv]
```

The "BEST of both" arm is shouted down as HINDSIGHT at lines 194 and 203-209. This arm is the same
species and gets no such label. Its **difference against `ct_piv`** is defensible — the control is
selected the same way — but the standalone mean printed at line 229 is not a tradeable number.

### M9. Every simulator fills the stop exactly at the stop price, even through a gap  **NUMBER**

`missed.py:76-79`, `A_grid.py:105-107`, `C_regime.py:119`, `levels.py:118` all return a flat
`-1.0` when `b["l"] <= stop`. A loss is *always* exactly −1R, whatever the gap.

This is the one risk the desk's own `scenario.py` builds an entire fourth branch around
("GAPPED THROUGH — resolved at a price nobody could have transacted"), citing SERIES_AUDIT's
`open[i+1] != close[i]` on 57-80% of MES 60m boundaries. Entry slippage is modelled (one tick);
exit slippage is not. Every published loss is understated, and `both_lose` at line 211 (`best <=
-1.0`) is therefore an exact-equality test in disguise.

### M10. The 16:00-labelled bar is held through and used as the exit — one hour past the desk's own flat deadline  **NUMBER**

The tape is open-labelled and **hour 17 is absent entirely** (the 17:00-18:00 maintenance halt), so
the bar labelled `16:00` spans **16:00-17:00 ET**. NOTES line 37 confirms: "Bar 21 is the 16:00 bar
and the harness flags it `<-- FORBIDDEN WINDOW`", and `watch.py:113` names "rule 5's 15:00-16:00
window" as the last tradeable hour.

`missed.py:73,82`, `A_grid.py:100,109` and `C_regime.py:117,121` all run `for j in range(f, end+1)`
and exit at `rows[end]["c"]` — the **17:00 ET** print. Every simulated trade gets one extra
post-deadline hour to reach its stop or target.

`C_regime.py` contradicts itself inside one file: line 157 refuses to **enter** on a 16:00 bar as
forbidden, lines 117-121 **hold through** that same bar.

Measured impact on the control (recomputed, not run through `missed.py`):

| | n | always LONG | always SHORT | BEST | ≥1.5R (best) |
|---|---|---|---|---|---|
| as shipped (holds through 16:00) | 1659 | +0.0147R | −0.0211R | +0.9469R | 57.2% |
| flat at 16:00 ET (last bar 15:00) | 1587 | +0.0105R | −0.0175R | +0.9669R | 58.9% |

40 of 3318 direction-trades change exit reason (1.2%). Second-order but real, and it wants an
owner's ruling on "flat at the 16:00 ET close" rather than a code guess — the same ambiguity
`mode.py`'s docstring already raises about `CLOSE_H`.

Separately, 3 of 43 stand-down fill bars (**90, 974, 1563**) *are* 16:00 forbidden bars, and 72
control bars are. Their trade opens and closes inside one forbidden bar; `missed.jsonl` publishes
them at +0.146R, +0.421R, +0.051R, all `SESSION_CLOSE`.

### M11. `scenario.py:58` — `TICK = 0.25` declared and never read; the map publishes untransactable prices and an overstated R:R  **NUMBER**

`grep -n TICK scenario.py` → declared at line 58, **zero further occurrences.** This is defect 3's
exact family, in the module that produces the desk's pre-planned geometry.

Today's output prints stops and targets at `6162.59`, `6136.07`, `6157.29`, `6150.21`, `6171.43`,
`6126.66`, `6153.18` — none on the 0.25 grid, none transactable on MES. And no entry slippage tick
is applied, unlike `levels.py:113`, `missed.py:70` and `C_regime.py:115` which all add one.

At the engine's own fill rule, today's printed **"R:R 2.00"** is really **1.92** (bounce arm) and
**1.90** (break arm). The module's own gap paragraph warns "below 1.5 voids the plan" — measured
against a baseline already ~5% optimistic.

### M12. `A_grid.py:186-193` — defect 4 is re-implemented, and the corrected version is computed and never read  **LATENT**

```python
def arms(sample, parity_by_enum):
    if parity_by_enum:   fl = [... for i, e in enumerate(sample)]    # list position
    else:                fl = [... if e["f"] % 2 == 0 ...]           # bar index
    fl_bar = [(e["long"] if e["f"] % 2 == 0 else e["short"]) for e in sample]
...
a_sd = arms(sdn, False)   # bar index
a_ct = arms(ctl, True)    # enumerate position
```

That is defect 4 verbatim. `flip_bar` — the symmetric version — is computed for both arms at
line 191 and **nothing reads it**; `ARMS` uses the key `"flip"`.

To the author's credit, lines 341-350 check this and the run prints
`max |mean(enumerate-parity) - mean(bar-index-parity)| over 12 cells = 0.0000`. The reasoning is
sound: `CTRL_BARS = range(20, len(rows))` filtered only at the tail, so the bars are contiguous
from an **even** index and the two parities coincide exactly. **No current number changes.**

But the guard is an accident of the literal `20`. Change it to 21, or let `session_end` return
`None` for a bar mid-tape (which C2 shows is one data quirk away), and the asymmetry becomes live
and silent. And the note at line 349 — "missed.py uses enumerate index for the control" — is now
**factually wrong**: `missed.py:182` was fixed.

### M13. `A_grid.py:324-337` — the promised self-check is FAILING right now, and the run continues  **LABEL**

The docstring promises: "Cell (1.0, 2.0) is asserted against missed.py's published figures at the
bottom of the run as a cross-check." Today's run:

```
always LONG    mine +0.253/+0.015 z +1.08   published +0.211/-0.009 z +0.99   MISMATCH
always SHORT   mine +0.060/-0.021 z +0.38   published +0.085/-0.003 z +0.41   MISMATCH
coin flip      mine +0.149/-0.012 z +0.73   published +0.177/-0.011 z +0.85   MISMATCH
n_sd 42 (published 41)   n_ct 1659 (published 1613)
baseline reproduction: FAIL
```

`pub` hardcodes a shorter tape. The word FAIL is printed ~200 lines *below* the twelve tables it
was meant to validate, with no non-zero exit code and no flag in the header. A reader who scrolls
to the grid and stops sees nothing wrong.

---

## MODERATE

### D14. `view.py:35-37` — the printed range window is not the window the table shows  **NUMBER**

The table prints the last `sessions` **ET dates**; the line under it prints the extremes of
`rows[-sessions*22:]`, i.e. `sessions × 22` **bars**.

| | span | low | high |
|---|---|---|---|
| the 8 ET dates in the table | 161 bars, from 2025-01-14 | 5842.25 | 6156.0 |
| what the line actually prints | 176 bars, from 2025-01-13T08:00 | **5813.0** | 6156.0 |

**5813.0 does not occur anywhere in the eight dates shown.** This is the orientation figure read
before every decision.

Related: `days` is keyed on `ts[:10]`, the ET calendar date, while the desk's cycle is 18:00→16:00.
So each row's `o` is the **00:00 ET bar's open** — mid-cycle — not a session open, and `bars 6`
appears for a Sunday evening alongside `bars 23` for a full date.

### D15. `watch.py:105-106` — two conditions on one bar: the side is decided by argv order  **NUMBER**

```python
for kind, price, side in conds:
    if KINDS[kind](b, price): ... return 0
```

With `touch_above:X:LONG` and `touch_below:Y:SHORT` both armed — the documented two-sided usage —
a wide bar satisfies both. The watcher halts on whichever was typed first and prints a single
definite `fired: ... -> SIDE`. It cannot know which came first intrabar. It should refuse and say
so, not pick. `close_above`/`close_below` cannot both fire, so this is specific to `touch_*`.

### D16. `watch.py:39-42` — inconsistent inclusivity between condition kinds  **NUMBER**

`close_above` is strict `>`, `close_below` strict `<`; `touch_above` is `>=`, `touch_below` `<=`.
On a 0.25 tick grid with tick-aligned armed levels, a bar closing *exactly* at the price does not
fire `close_above`. Silent non-fire, reported as "budget spent, no condition fired".

### D17. `watch.py:85` — no sanity check that the condition price is anywhere near the tape  **NUMBER**

`float(price)` and nothing else. A mistyped price produces a clean, plausible
`budget spent, no condition fired. cursor at bar N` after burning the entire budget of cursor
advances — which are irreversible. This is exactly the defect-2 shape: a broken input rendered as
a tidy negative result.

### D18. `watch.py:100-101` — the defect-2 output filter is still a filter  **LABEL**

`step()` now exits on `rc != 0` and on a non-advancing tape, which closes the hole that was found.
But the display is still an allow-list: `FILLED, CLOSED, REFUSED, absorbing, FORBIDDEN, Traceback,
Error`. A harness line saying an order was rejected, a stop expired, a position was already open,
or anything with a lowercase `error:` is still dropped — on a step that *did* advance, so the two
new guards do not catch it. The fix addressed the return code and the bar count, not the filter.

### D19. `C_merge.py:57` — docstring says "needs no tuned fraction"; the code has two magic numbers  **LABEL**

The docstring's whole argument is that condition (b) "is the discriminator and it needs no tuned
fraction." The hit criterion is `if g >= 20.0 and s >= 2.0:` — two hardcoded absolute thresholds,
inline, not module constants, not mentioned in the docstring, not justified anywhere.

### D20. `C_regime.py:248-251` — Tier B's stated de-duplication is not what the code does  **NUMBER**

Stated rule (b), line 236: "FIRST retest after a given break episode only (level+break
de-duplicated), so one shelf cannot contribute seven signals."

Code dedupes on exact `round(L, 2)` price + side within 48 bars. Two pivots 0.25 apart on the same
shelf are *different levels* and both survive. The break episode (`s["brk"]`) is not part of the
key at all, despite "level+break de-duplicated". Sets Tier B's n and mean.

### D21. `D_discretion.py:56` — the "liquidity" filter partly measures the clock  **NUMBER**

`"liquid signal bar (v >= 50k)": lambda s: rows[s["i"]]["v"] >= 50_000`

NOTES' own Contradiction 3 establishes that the zero-volume bars are "**A missing volume field, not
an absence of trades**", with 56 of 60 in the 18:00 ET hour. The filter rejects those as illiquid,
so part of what it measures is time-of-day, not liquidity — and the module's conclusion is about
whether *discretion* adds anything.

### D22. `D_discretion.py:54-60, 99-104` — post-hoc filters, and the reader instruction overstates what a positive z means  **LABEL**

The three filters are drawn from the desk's own wording about its two real trades (bar 1502's
"crossed 5845.0 four times in six bars", the trades' "lower highs and lower lows"), then scored on
the same signal population, and line 96-98 reports whether bars 452 and 1337 survive them.

Line 100-101 tells the reader: "A positive z means the discretion separates winners from losers
WITHIN the pattern's own population — the filters are doing work." For filters selected from the
outcomes, it does not. The closing hedge ("this cannot prove the filters work") is weaker than the
claim it follows.

### D23. Stale hardcoded numbers quoted as current — and one self-contradiction  **NUMBER**

| where | claims | today |
|---|---|---|
| `scenario.py` docstring:18 | retested n=175, bounce 53.7% | n=176, 53.4% |
| `scenario.py` docstring:19 | random n=200, bounce 55.0% | n=205, 54.1% |
| `scenario.py:59` `P_BOUNCE/P_CTRL` | 0.537 / 0.550 | 0.534 / 0.541 |
| `scenario.py` docstring:31 | break arm **+0.045R at z +1.17** | +0.074R, z +1.34 |
| `scenario.py` docstring:49 | break arm **+0.063R ... z +1.13** | +0.074R, z +1.34 |
| `D_discretion.py` docstring:4 | "91 tradeable firings at −0.113R" | Tier B n=92, −0.090R |
| `A_grid.py:329-335` `pub` | n_sd 41, n_ct 1613 | 42, 1659 (see M13) |

**Lines 31 and 49 of `scenario.py` report the same statistic at two different values in the same
docstring** (+0.045R z+1.17 vs +0.063R z+1.13). At least one was already wrong when written.
Nothing in `scenario.py` recomputes any of these; they drift silently as the tape grows.

---

## MINOR / LATENT

- **N24. `view.py:97`** — `i = j` runs even when the max-jump test *rejects* a run, so the whole
  candidate window is skipped rather than re-anchored at `i+1`; a real merge beginning inside a
  rejected window would never be examined. **Latent only:** today just bars 1446-1449 are skipped
  and no merge hides there — I ran both variants and the output is identical. Also
  `while i < len(rows) - k` leaves a **k-bar blind spot at the right edge** — which is precisely
  where a live roll would first appear.
- **N25. `levels.py:99`** — `resolve` starts at `j = i` and can in principle resolve on the decision
  bar itself. Safe only because `BAND_ATR (0.25) < BREAK_ATR / BOUNCE_ATR (0.40)`. An unstated
  inequality among three constants, with no assertion.
- **N25b. `levels.py` — `NEITHER` is 0.0% of 176 and 0.0% of 205.** With `BOUNCE_ATR ==
  BREAK_ATR == 0.40` over 24 bars, `resolve` degenerates to a symmetric first-passage race that
  essentially always resolves. So the published "bounce 53.4% / break 46.6%" *is* a coin-flip
  first-passage statistic — which is the mechanical reason it equals the random control — and
  `scenario.py`'s whole "if NEITHER" branch describes an outcome measured at zero.
- **N26. `missed.py:75` / `A_grid.py:100`** — `mfe` is updated *before* the stop check inside the
  same bar, so a stopped-out trade is credited with the full extreme of its exit bar. Inflates the
  published MFE column only.
- **N27. `missed.py:181-183`** — bar **1613 appears twice** in the stand-down sample (two callouts
  share `visible_bars: 1613`); confirmed in `missed.jsonl`. Double-weighted in every sample mean.
- **N28. `missed.py:124-133`** — rows dropped by `evaluate()` returning `None` are counted neither
  in `res` nor in `pending`, so the header's "N scored, M pending" need not sum to `len(stand)`.
  It does today (43 = 42 + 1).
- **N29. `mode.py:29`** — `(now or datetime.now(ET)).astimezone(ET)`: a **naive** datetime is
  interpreted as *system local*. This container is UTC, so any caller passing a naive ET wall time
  silently gets a posture shifted by 4-5 hours. `__main__` passes an aware value, so nothing is
  wrong today; a scheduler or wake-up hook passing `datetime(2026,9,28,17,15)` would be.
- **N29b. `mode.py:56-61`** — the transition printer does wall-clock `timedelta` arithmetic across
  DST; on a spring-forward it will emit times in the nonexistent hour. Display only.
- **N30. `C_regime.py:304`** — prints `{2}` as the desk-trade count without consulting line 263's own
  membership check; **line 313** hardcodes `[("MID","DOWN"), ("LO","DOWN")]` as "BOTH DESK TRADES'
  CELLS" rather than reading `regs[452]` / `regs[1337]`; **lines 316-318** call `st.mean([])`
  unguarded if a cell empties.
- **N31. `C_regime.py:159`** — `1146 <= s["i"] <= 1158` is a magic literal copied from `view.py`'s
  detector *output*, not derived from the detector. If bar indices ever shift, it silently excludes
  the wrong bars.
- **N32. `C_shape.py:46`** — `RTH = lambda h: 9 <= h <= 16` includes hour 16, the post-close
  forbidden bar, and starts at 09:00 though RTH opens 09:30. The published "zero-volume bars inside
  RTH 09:00-16:00 ET" count and the table's `RTH?` column both inherit it.
- **N33. `D_discretion.py:20, 24-27`** — `os.chdir(D)` mutates process CWD globally; `sys.stdout =
  open(os.devnull, "w")` has no `try/finally`, so anything printed before an exception in
  `exec_module` is lost (the traceback itself still reaches stderr) and the handle leaks.
- **N34. `scenario.py:68-70`** — `contracts = int(ACCOUNT_RISK // (risk * POINT_VALUE))` can be `0`
  with **no flag**: a plan that cannot be sized prints `0c $0` and looks takeable. And
  `ok = risk >= 0.5 * a` is **structurally unreachable** — the two geometries hardcode risk at
  1.00×ATR and 0.80×ATR, both always ≥ 0.5×ATR, so the advertised `<<< REFUSED ... (rule 4)` path
  can never print. Rule-4 compliance is displayed as checked and is not checkable.
  Also `d = abs(L - px)` printed as `{d:+.2f}pt away`, so levels *below* price show a `+`.
- **N34b. `C_regime.py:287`** — `for _try in range(30): ... if res: rs.append(res[0]); break`. If all
  30 draws fail, that pool member contributes nothing to the trial and nothing says so; the trial
  mean is then over fewer trades than `len(pool)`.

---

## CLEAN, per file

**Priority 1 — look-ahead leaks. None found that feeds a decision.** Verified programmatically:

- `levels.py levels_at(i)` — `for j in range(max(K, i-LOOKBACK), i-K)` gives `j_max = i-K-1`, and
  the widest window `rows[j-K : j+K+1]` touches exactly `i-1`. **Correct**: a k-bar fractal pivot
  at j is known only from j+k, and nothing at or beyond the decision bar is read. Called as
  `levels_at(i, atr(i-1))` in `study()` — clean.
- `scenario.py report(i)` calls `levels_at(i+1, LV.atr(i))`, which touches **bar i and no further** —
  correct for a decision made at bar i's *close*. Not a leak. Worth noting only that it is one bar
  *looser* than the information set `levels.py`'s own study used (`atr(i-1)`, `levels_at(i)`), so the
  live map can display a level the study that validated it would not have counted.
- `missed.py atr()` and `A_grid.py atr()` use `rows[max(0,i-n):i+1]` and are called as `atr(f-1)` —
  the decision bar, one before the fill. Clean, and the comment at `missed.py:112` is accurate.
- `C_regime.pivots_known_at(i)` is clean and slightly stricter than `levels.py` (adds a strict
  extremum test). `C_regime.pct_rank` is trailing-only.
- `view.py atr()` is a trailing-tail display value over the last 14 TRs. No leak.
- `missed.py is_pivot()` does look forward, as documented — see **M8** for the one place that
  matters.

**Priority 2 — declared-but-unread constants.** Every module-level constant was traced.
`levels.py` (K, LOOKBACK, TOL_ATR, BAND_ATR, BREAK_ATR, BOUNCE_ATR, HORIZON, STOP_ATR, RR, TICK) —
**all read, all where their names imply.** `missed.py` (TICK, STOP_ATR, RR, PIVOT_K) — all read;
STOP_ATR is genuinely wired in now at line 115. `mode.py` (CLOSE_H, OPEN_H, PRE_OPEN_MIN),
`A_grid.py` (TICK, STOPS, TARGETS, DIAG_STOPS), `C_regime.py` (TICK, RR, K, LOOKBACK, HORIZON,
STOP_FLOOR) — all read. **Two failures: `scenario.py`'s `TICK` (M11) and `A_grid.py`'s `flip_bar`
(M12).**

**Priority 5 — silent exception swallowing.** `grep -n except` across all ten Python files returns
**nothing**. No `try`, no `except`, no bare except, nothing swallowed anywhere. The unchecked-return
issues are N28 and N34b only.

**Priority 6 — `mode.py`.** I constructed every boundary and the schedule logic is **correct against
its own docstring**:

| time (ET) | code | docstring |
|---|---|---|
| Fri ≥ 17:00 | 3, CLOSED_WEEKEND | weekend from Fri 17:00 ✓ |
| Fri 17:30 | **3**, still weekend | ✓ — the cutback is guarded by `dow == 6`, and there is no reopen until Sunday |
| Sat, all day | 3, CLOSED_WEEKEND | ✓ |
| Sun < 17:30 | 3, CLOSED_WEEKEND | ✓ |
| Sun 17:30-17:59 | 1, PRE_OPEN | ✓ 30-min cutback |
| Sun ≥ 18:00 | 1, OPEN | ✓ |
| Mon-Thu 17:00-17:29 | 3, CLOSED_HALT | ✓ |
| Mon-Thu 17:30-17:59 | 1, PRE_OPEN | ✓ |
| Mon-Thu ≥ 18:00, Fri < 17:00 | 1, OPEN | ✓ |

`cut = 18*60 - 30 = 17:30` is right; the `dow == 6` guard on the weekend cutback is the subtle part
and it is correct. Remaining gaps are all disclosed or minor: the `CLOSE_H = 17` vs `16` question
the docstring itself raises (and NOTES line 940-942 records) — **not a defect, an open question for
the owner**; no CME holiday or early-close calendar, though the tape itself contains three such
days (see C2); plus N29 and N29b.

**`watch.py` path arithmetic is now correct.** Four `..` from
`workspace/paper/REPLAY/R1` resolves to `/home/user/Futures01`, and
`workspace/roundtable/lib/replay.py` exists there (checked by existence only, not read). `step()`
fails loudly on both a non-zero return code and a non-advancing tape. Defect 2's two halves: the
path is fixed, the loudness is fixed for the failure modes that were found, the **filter** is not
(D18).

**`C_merge.py`'s corridor logic is sound.** `lo_edge = max(lows)`, `hi_edge = min(highs)` genuinely
enforces "straddled by every bar"; the widest-gap scan is correct; and the excision test at line 98,
`if not (i+W-1 < 1140 or i > 1165): continue`, correctly skips every window that *overlaps*
1140-1165. The only complaint is D19 and the cosmetic `(0,0,0,W,0,0)` fallback at line 91 printing
`bars 0-W-1`.

**`view.py`'s roll detector is arithmetically correct where it counts.** The growth loop tests the
whole segment each step and `rows[i:j]` is the run that passed; `gaps` over `range(i+1, j)` covers
exactly the boundaries interior to that run; the placement of the max-jump test outside the growth
loop is right and the comment explaining why is right. The two defects are N24, both latent.

---

## What the desk should decide first

1. **C1** — either restore the code that produced the 1-touch bucket with a 1-touch control, or
   strike `P1_BOUNCE/P1_BREAK` and the "ONE THING WORTH KNOWING" paragraph. Right now the live map's
   only quantitative claim rests on numbers nothing can regenerate.
2. **C2** — decide what "the session containing bar f" means on a day with no 16:00 bar, and apply
   it in all three copies of `session_end`.
3. **M10** — get the owner's ruling on whether "flat at the 16:00 ET close" means the close of the
   15:00 bar or the close of the 16:00 bar. `C_regime.py` currently answers both ways at once.
4. **C3/C4** — the placebo z and the placebo filter set. These are the desk's own stated standard
   of proof.
5. **C5** — ARMED. The register has been reporting a taxonomy with one of its three classes
   structurally empty.
