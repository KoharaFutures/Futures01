# R2 — Wall A implementation spec

**Owner:** researcher R2. **Opened:** 2026-09-27 (round 2). Appended to as work proceeds.
**Implements:** the Wall A finding in `workspace/roundtable/research/R2_expressibility_wall.md` §1-§2.
**Status:** complete enough to hand to a developer. Gaps I could not close are in §9, named.

Marking per BRIEF.md rule 3: `[repo-verified: path:line]` / `[measured: command → result]` /
`[general knowledge]`. **Every line number in this file was re-verified in round 2**; §0.2 lists the
places round 1's citations had drifted by one to four lines, so a developer following round 1's
table alone would have patched the wrong line in two spots.

---

## 0. What this file is, and what it is not

### 0.1 Scope

Wall A is **one `FeatureSnapshot` per symbol** — a condition can see one symbol's path and nothing
beside it. This file turns edits A1-A8 into instructions. It does **not** cover Wall B (one
instrument per position); `R2_expressibility_wall.md` §3 prices that separately and the build-order
conclusion is unchanged: Wall A first.

Wall A buys **relational signals on one traded leg**. After it, the engine still trades exactly one
contract, `BacktestEngine.spec` is still one `ContractSpec`, and R is still one notional contract.
That restriction is what keeps the change to eight additive edits, and A7 exists to state it.

**The whole change is additive and keyword-only.** That is not a style preference, it is the
budget:
`[measured: grep -rn "build_symbol_frame" --include=*.py . | grep -v __pycache__ | wc -l → 144]` and
`[measured: grep -rn "SymbolFrame(" --include=*.py . | grep -v __pycache__ | grep -v "def \|class " | wc -l → 19]`.
163 construction sites. A positional parameter, a renamed field or a changed `ConditionFn` is a
163-site refactor; a keyword-only default is zero sites.

**`ConditionFn` at `[repo-verified: futures_agents/strategies/base.py:87]`
`ConditionFn = Callable[[FeatureSnapshot, int], ConditionResult]` does not change.** All 79
conditions keep working untouched. This is the load-bearing property of the design.

### 0.2 Line-number corrections to round 1 — read this before patching

Round 1's edit table cited a handful of lines that are off. Verified in round 2:

| round 1 said | actually | what it is |
|---|---|---|
| `features.py:687` — the wall's docstring | **`features.py:686`** | `"""Everything known about one symbol at one instant, across all timeframes."""` |
| `features.py:690` — `symbol: str` scalar | **`features.py:688`** | the scalar symbol field |
| `features.py:795` (`SymbolFrame.__init__` at :798) | **:795 class, :798 `__init__`** — correct | no change |
| `base.py:118-120` — the cache key | **`base.py:121`** | `key = (self.name, tf)` |
| `engine.py:284` — the per-bar cache | **`engine.py:288`** | `cache: Dict[Tuple[str, int], ConditionResult] = {}` |
| (not cited in round 1) | **`base.py:613`** | `"|".join(sorted(c.label for c in self.conditions))` inside `strategy_id` — **this is the line that makes §7 work** |

`[repo-verified: all six re-read with awk NR ranges in round 2]`. BT2's `event_gate.py` docstring
inherited round 1's `base.py:120` and `engine.py:284` from me; the cited mechanism is right, the two
numbers are 121 and 288.

### 0.3 The three invariants the whole change rests on

Everything below is in service of these. If an implementation satisfies all three it is correct even
if it differs from my code sketches; if it violates any one, it is wrong no matter how closely it
follows them.

- **I1 — Backwards-only.** The partner bar visible at primary bar *i* is the last partner bar whose
  `end_ts <= bars[i].end_ts`. Never the nearest, never interpolated, never forward-filled from a
  bar that had not closed. `-1` when none has.
- **I2 — Empty is a legal answer and it means decline.** A partner slot may be absent. A condition
  that cannot find its partner returns `ConditionResult.no()`. It must never substitute a default, a
  last-known value, or the primary symbol's own reading.
- **I3 — Distinguishable identity.** Two partner bindings of one condition must differ in
  `Condition.label`, in the per-bar cache key, and therefore in `Strategy.strategy_id`. A binding
  that is invisible to any of the three is a silent-wrong-answer defect, not a missing feature.

### 0.4 The six families Wall A unlocks, and the two it is **not sufficient** for

Required by the manager's ADJ-1 covering message
`[repo-verified: workspace/roundtable/msgs/11_manager_R2_wall-a-and-axis-c.md, "One thing the Wall A
spec must carry"]`: *"a reader will otherwise read 6 as six testable families."* The manager is right
and the correction belongs here rather than only in the catalogue entry, because the spec is what a
developer reads.

**"Unlocked" means the architectural blocker is removed. It does not mean testable.** Two of the six
have a second, independent constraint that Wall A cannot touch, because it is not a code constraint.

| family | what Wall A unlocks | partner data on disk | **is Wall A sufficient?** |
|---|---|---|---|
| **II-9** correlation regime | rolling-correlation regime as a filter | any on-disk pair | **Yes.** The cheapest Wall-A unlock in Class II: correlation regime *is* the mechanism, and two aligned price series are the whole data requirement |
| **II-5** inter-market | gold-vs-equity, gold-vs-crude conditioning | `MGC_1d`×`SPY_1d` **2,507** (longest aligned pair in the repo); `MGC_1h`×`MCL_1h` **4,636** | **Yes for the version the data supports.** **No** for the canonical rates-vs-equity and dollar-vs-metals versions: no ZN, no DX, no FX series exists — that is a **data** gap, not an architecture one |
| **II-8** lead-lag | cross-contract structural lead-lag | ES/NQ/MES/MNQ/SPY/QQQ | **Yes for the structural version only.** The real (sub-second) version is **INEXPRESSIBLE-DATA at any architecture**: 1m is the finest bar here, so a sub-second lag is unmeasurable *in principle*. And D14/D41: these are one complex, so a result is a microstructure statement and cross-leg agreement is **not** corroboration |
| **II-3** basis | futures rich/cheap vs ETF as a signal | `MES_1d`×`SPY_1d` **1,855**; `MNQ_1d`×`QQQ_1d` **1,855** | **Yes as a rich/cheap signal, at daily** (§9.1). **No** as index arb: no financing rate, no dividend stream, no borrow cost, no tick data — and an ETF has its own NAV premium and creation/redemption mechanics, so the proxy is not the mechanism |
| **II-6** statarb | ratio z-score as a signal | `MES_1h`×`MGC_1h` **4,986** | **Yes for a one-legged, labelled-as-such signal.** **No** as a market-neutral pairs *trade* — that needs **Wall B**. A one-legged "the ratio is stretched, buy the cheap leg" carries the leg's own variance; report its Sharpe as an outright's or the number will be read as a spread's |
| **II-7** cross-sectional momentum | a rank filter over the symbol universe | the four micros | **NO, and no amount of Wall A fixes it.** |

**II-7 is the one to state loudly, because it is the one a reader will over-count.** Its binding
constraint is **universe size**, which is quantitative, not architectural:
`[measured: ls csv/raw/ → 11 distinct symbols]`, of which **3 are D40-excluded** (`MZC`/`MZS`/`MZW`
splice more than one contract month) and **2 are ETFs** that must never be costed as traded (§7), and
`[repo-verified: futures_agents/config.py:107-125]` `MES`/`MNQ`/`ES`/`NQ` all share one
`correlation_group`. **So the effective cross-section is ≈2** (an index complex and a metal), against a
canonical version that ranks 40-60 markets. Wall A would let the rank be *computed*. It would not make
the rank *informative*, and a 2-wide cross-section has no cross-section. The manager's ADJ-1 accepts
this framing as written: II-7's constraint is one *"the class definition does not capture and no code
change here fixes"*.

**Honest total, then.** Wall A removes the architectural blocker on **six** families. Of those,
**one (II-9) is unreservedly testable**, **four (II-5, II-8, II-3, II-6) are testable in a named
degraded form with a named caveat that must travel with any result**, and **one (II-7) remains
untestable for a reason Wall A does not address**. The nine-after-a-vendor-fetch figure is subject to
the same distinction and I have not re-audited it here, because the fetch is a board decision and
`R2_expressibility_wall.md` §4 already records that "reachable by the code" is not "verified to have
history".

---

## 1. A1 — `FeatureSnapshot` gains a partner map

**File:** `futures_agents/features.py`. **Anchor:** dataclass at `:684-685`, docstring `:686`, last
field `in_news_blackout: bool = False` at `:712`, first method `def tf` at `:714`.
`[repo-verified: futures_agents/features.py:684-715]`

### Signature before

```python
@dataclass
class FeatureSnapshot:
    """Everything known about one symbol at one instant, across all timeframes."""

    symbol: str
    ...
    in_news_blackout: bool = False          # :712 — last field

    def tf(self, timeframe: int) -> Optional[TFSnapshot]:   # :714
```

### Signature after

```python
@dataclass
class FeatureSnapshot:
    """Everything known about one symbol at one instant, across all timeframes,
    plus a read-only view of any PARTNER symbols attached to the frame.

    The partner view is what makes a relational condition possible without
    changing ``ConditionFn``: a second series rides inside the object every
    condition already receives. Three properties are load-bearing and each has a
    test in ``tests/test_features.py``:

    * a partner snapshot is never fresher than this one (backwards-only, I1);
    * a partner may be ABSENT, and absent means the condition declines (I2);
    * partner snapshots are one level deep — ``snap.partner(x).partners`` is
      always empty, so there is no recursion and no cycle.
    """

    symbol: str
    ...
    in_news_blackout: bool = False
    #: symbol -> that symbol's snapshot at the last bar of ITS OWN series that
    #: had closed at or before this bar's close. Empty when the frame carries no
    #: partners, and a key is ABSENT (not None-valued) when that partner had no
    #: closed bar yet. Absent is the signal to decline; see I2.
    partners: Dict[str, "FeatureSnapshot"] = field(default_factory=dict)

    def partner(self, symbol: str) -> Optional["FeatureSnapshot"]:
        """The partner snapshot for ``symbol``, or None when unavailable.

        None covers three different situations deliberately, because a condition
        must treat all three the same way — decline:
        the frame has no such partner; the partner had no closed bar yet; the
        partner's own snapshot could not be built.
        """
        return self.partners.get(symbol.upper())
```

**Case convention:** keys are upper-cased on insert (A4) and on lookup, because
`[repo-verified: futures_agents/data/bars.py:165]` `BarSeries.__init__` does `self.symbol =
symbol.upper()` and `[repo-verified: futures_agents/features.py:801]` `SymbolFrame` takes
`base.symbol` verbatim. A condition written `snap.partner("spy")` must not silently miss.

**What it does.** Gives a condition one lookup through which a second symbol's full
`FeatureSnapshot` — all its timeframes, its regime, its session levels — is reachable.

**What breaks if skipped.** Nothing compiles differently and nothing is unlocked. This is the
field the other seven edits populate and read; without it the change does not exist.

**How to test.**
- `test_partner_defaults_to_empty`: build any frame the old way, `snapshot(0).partners == {}`.
  This is the no-regression test for all 163 construction sites.
- `test_partner_lookup_is_case_insensitive`: `snap.partner("spy") is snap.partner("SPY")`.
- `test_partner_snapshot_is_one_level_deep`: for every partner *p* of every snapshot in a
  partnered frame, `p.partners == {}`.
- `test_to_dict_unchanged_by_default`: `[repo-verified: futures_agents/features.py:772-792]`
  `FeatureSnapshot.to_dict` enumerates fields explicitly and so will **not** serialise `partners`
  unless someone adds it. Leave it out (keeps every stored JSON shape byte-identical) and assert
  the key is absent, so the omission is a decision on the record rather than an oversight.

---

## 2. A2 — `SymbolFrame` accepts partner frames

**File:** `futures_agents/features.py`. **Anchor:** `class SymbolFrame` `:795`, `__init__` `:798-800`,
existing finer-timeframe guard `:805-807`, construction tail `:814-818`.
`[repo-verified: futures_agents/features.py:795-818]`

### Signature before

```python
def __init__(self, base: BarSeries, timeframes: Sequence[int],
             spec: Optional[ContractSpec] = None, *,
             regime_timeframe: Optional[int] = None):
```

### Signature after

```python
def __init__(self, base: BarSeries, timeframes: Sequence[int],
             spec: Optional[ContractSpec] = None, *,
             regime_timeframe: Optional[int] = None,
             partners: Sequence["SymbolFrame"] = (),
             allow_coarser_partners: bool = False):
```

Both new parameters are **keyword-only** (they sit after the existing `*`) and both default to the
current behaviour, so all 163 sites are untouched.

### Body, appended after `:818` (`self._news = self._build_news_proximity()`)

```python
        self.partners: Dict[str, "SymbolFrame"] = {}
        for pf in partners:
            if pf.symbol == self.symbol:
                raise ValueError(
                    f"{self.symbol}: cannot be its own partner")
            if pf.partners:
                raise ValueError(
                    f"{self.symbol}: partner {pf.symbol} itself carries partners; "
                    "partner frames must be built without partners so the snapshot "
                    "graph stays one level deep")
            if pf.symbol in self.partners:
                raise ValueError(
                    f"{self.symbol}: partner {pf.symbol} supplied twice")
            if pf.base.minutes > self.base.minutes and not allow_coarser_partners:
                raise ValueError(
                    f"{self.symbol}: partner {pf.symbol} base is "
                    f"{pf.base.minutes}m, coarser than this frame's "
                    f"{self.base.minutes}m. This is SAFE but statistically "
                    "misleading: one partner reading would repeat across "
                    f"{pf.base.minutes // max(1, self.base.minutes)} primary bars, "
                    "inflating the effective sample. Pass "
                    "allow_coarser_partners=True to accept it deliberately.")
            self.partners[pf.symbol] = pf
        self._palign = self._build_partner_alignment()
```

### Round-1 self-correction, recorded

`R2_expressibility_wall.md` §2 A2 said: *"Reject a partner whose `base.minutes` is coarser than
`self.base.minutes` (the mirror of the existing guard at `features.py:808-810`)."* **That framing was
wrong and I am correcting it here.**

- It is not a mirror of the existing guard. The existing guard `[repo-verified:
  futures_agents/features.py:805-807]` rejects a timeframe *finer* than the source because that
  timeframe **cannot be constructed** — the data does not exist. A coarser partner can be
  constructed and is read backwards-only, so it **does not leak**.
- The real hazard is statistical, not causal. A daily partner against an hourly primary repeats one
  reading across ~7-24 primary bars. Every bar then carries the same partner value, the R series
  acquires block autocorrelation, and a t-statistic computed as if the observations were independent
  is inflated. That is the D28 failure mode (`T.ab` inflating z ~3.3x) arriving through the data
  rather than through the test.
- So: **reject by default with a message that says why, and provide `allow_coarser_partners=True`.**
  A caller who opts in has recorded the decision at the call site, and any measurement using it owes
  a block-aware test — which is exactly what BT3's `block_vs_iid.py` exists to supply
  `[repo-verified: workspace/roundtable/backtest/BT3/code/block_vs_iid.py exists]`.

A partner *finer* than the primary needs no guard at all: backwards-only selection at the primary
bar's close makes it safe and it is strictly more informative.

**What it does.** Attaches partner frames to a frame and validates the three ways an attachment can
be malformed (self, nested, duplicate) plus the one way it can be misleading (coarser).

**What breaks if skipped.** There is nowhere to put a partner, so A3/A4 have nothing to align.
Worse, if a developer skips only the `pf.partners` check, `snapshot` recurses: a frame with a
partner that has a partner builds a snapshot tree whose depth is the chain length and whose cost is
multiplicative. With a cycle (A partners B, B partners A) it does not terminate.

**How to test.**
- `test_self_partner_rejected`, `test_nested_partner_rejected`, `test_duplicate_partner_rejected`:
  each raises `ValueError`.
- `test_coarser_partner_rejected_by_default_and_allowed_on_opt_in`: `MGC_1h` primary with `SPY_1d`
  partner raises; same call with `allow_coarser_partners=True` succeeds.
- `test_finer_partner_accepted`: `MGC_1d` primary with `SPY_1h` partner succeeds with no flag.
- `test_partner_free_construction_is_byte_identical`: build `MGC_1h` with and without the new
  keywords and assert `snapshot(i).to_dict()` is equal for a sample of *i*. This is the regression
  guard for the 163 sites.

---

## 3. A3 — `_build_partner_alignment`, the causality-critical edit

**File:** `futures_agents/features.py`, new method. **Model it on:**
`[repo-verified: futures_agents/features.py:828-847]` `_build_alignment`, whose docstring at
`:829-831` states the invariant verbatim: *"base bar index -> index of the last COMPLETED bar on
each timeframe. `-1` means no bar on that timeframe had closed yet."*

**This is the edit that decides whether Wall A adds a capability or a look-ahead bias.** Everything
else is plumbing.

### Signature

```python
    def _build_partner_alignment(self) -> Dict[str, List[int]]:
        """partner symbol -> (base bar index -> index of the last CLOSED partner bar).

        The same invariant as :meth:`_build_alignment` with the axis swapped from
        timeframe to instrument, and for the same reason. ``-1`` means no bar of
        that partner had closed yet at this base bar, and a condition seeing -1
        must decline rather than guess.

        Comparison is on ``end_ts`` (``bars.py:51``: ``ts + minutes``), never on
        ``ts``, because ``ts`` is the bar's OPEN (``bars.py:37``). Selecting on
        the open would admit a partner bar that had begun but not finished — the
        precise definition of look-ahead on this axis, and worth a sentence
        because the two fields differ by one bar length and the bug is invisible
        in any single spot-check.

        NOT ``bisect`` over a timestamp list, and NOT "nearest": a two-pointer
        forward scan, so the pointer can only ever advance. That makes it
        structurally impossible for a later base bar to see an earlier partner
        bar, and structurally impossible for any base bar to see a partner bar
        from its future.
        """
        out: Dict[str, List[int]] = {}
        base_bars = self.base.bars
        for sym, pf in self.partners.items():
            p_bars = pf.base.bars
            ptr: List[int] = []
            k = -1
            j = 0
            for b in base_bars:
                end = b.end_ts
                while j < len(p_bars) and p_bars[j].end_ts <= end:
                    k = j
                    j += 1
                ptr.append(k)
            out[sym] = ptr
        return out
```

It is `_build_alignment`'s loop with `self.frames.items()` → `self.partners.items()` and
`frame.series.bars` → `pf.base.bars`. **Deliberately so.** The invariant is already tested on the
timeframe axis; copying the algorithm rather than writing a new one means the two axes cannot drift
apart, and a reviewer who has accepted `_build_alignment` has accepted this.

### A public accessor beside `tf_index`

`[repo-verified: futures_agents/features.py:921-926]` `tf_index(base_index, timeframe)` clamps its
index and raises `KeyError` for an unknown timeframe. The partner accessor must clamp the same way
but must **not** raise for an unknown partner — an unknown partner is I2's "decline", and raising
would be swallowed into `ConditionResult.no()` by
`[repo-verified: futures_agents/strategies/base.py:131-133]` anyway, only after being counted as an
error in `CONDITION_ERRORS`, which would make a legitimately partnerless configuration look like a
broken condition. That is the D38-shaped confusion running in reverse.

```python
    def partner_index(self, base_index: int, symbol: str) -> int:
        """Index of the newest CLOSED bar of ``symbol`` at ``base_index``.

        ``-1`` when none had closed. Also ``-1``, not an exception, when
        ``symbol`` is not a partner of this frame: "no partner" and "partner not
        started yet" are the same instruction to a condition (decline), and
        raising here would be swallowed by ``Condition.evaluate`` and tallied in
        ``CONDITION_ERRORS``, making a correct configuration look broken.
        """
        ptr = self._palign.get(symbol.upper())
        if ptr is None or not ptr:
            return -1
        return ptr[min(max(0, base_index), len(ptr) - 1)]
```

### The two ways to get this wrong, both of which produce plausible numbers

1. **`ts` instead of `end_ts`.** Off by exactly one partner bar length, always in the leaking
   direction. On `MGC_1h` × `MCL_1h` that is a one-hour peek. It will not fail any sanity check: the
   series still looks aligned, the bar counts are unchanged, and the strategy's equity curve simply
   gets better. **This is the single highest-value assertion in the whole test plan.**
2. **`bisect` on nearest.** `bisect_left` on a timestamp list followed by "take index *j*" rather
   than *j−1* selects the partner bar that *starts* at or after the primary bar's close. Same leak,
   arrived at differently. The two-pointer form above cannot express it.

### How to test — five tests, and the first two are copies of existing ones

`[repo-verified: tests/test_features.py:36,91]` the repo already encodes this invariant on the
timeframe axis as `test_no_aligned_bar_ends_after_the_base_bar_it_is_aligned_to` and
`test_aligned_bar_contains_no_base_bar_that_had_not_closed`. The partner tests are those two with
the axis swapped.

- **T3.1 `test_no_partner_bar_ends_after_the_base_bar_it_is_aligned_to`** — for every base bar *i*
  and every partner *p*, with `k = frame.partner_index(i, p)`, assert `k == -1 or
  p_bars[k].end_ts <= base_bars[i].end_ts`. Sweep every bar, not a sample. This is the test that
  catches failure mode 1.
- **T3.2 `test_partner_index_is_the_LAST_such_bar`** — additionally assert `k + 1 == len(p_bars) or
  p_bars[k+1].end_ts > base_bars[i].end_ts`. T3.1 alone passes for `k = 0` forever; this one pins
  it to the newest.
- **T3.3 `test_partner_index_is_monotone_nondecreasing`** — `partner_index(i, p) <=
  partner_index(i+1, p)` for all *i*. Cheap, and it is the property a `bisect`-on-nearest
  implementation violates first.
- **T3.4 `test_partner_index_is_minus_one_before_the_partner_starts`** — construct a primary whose
  first bars precede the partner's first bar and assert `-1` there. Real instance available:
  `[measured: round-1 R2-D0 spans]` `csv/raw/MGC_1d.csv` starts 2016-09-26 and `csv/raw/MES_1d.csv`
  starts 2019-05-03, so `MGC_1d` with partner `MES_1d` has ~650 leading bars that must read `-1`.
  Do not synthesise this case; the on-disk one is better because it also proves the loader path.
- **T3.5 `test_appending_a_future_partner_bar_never_changes_a_historical_index`** — build the
  alignment, append a bar to the partner series, rebuild, assert the prefix is identical. The
  general anti-leak property, and the same shape as the test BT2 wrote for its event clock
  (`test_appending_a_bar_never_changes_a_historical_reading`,
  `[repo-verified: workspace/roundtable/backtest/BT2/code/event_clock.py:33-38 docstring]`).

**What breaks if skipped.** There is no safe way to pick a partner bar, so either partners are
unusable or somebody picks one ad hoc at the call site — and the ad hoc pick will be `nearest`,
because that is what a reasonable person writes when they have not been told otherwise. Every number
produced downstream is then contaminated by an amount nobody can bound after the fact.

---

## 4. A4 — `snapshot()` populates the partner map

**File:** `futures_agents/features.py:1004-1035`. `[repo-verified: futures_agents/features.py:1004-1035]`

### Signature

Unchanged: `def snapshot(self, base_index: int) -> Optional[FeatureSnapshot]`. Only the
constructor call at `:1022-1035` grows one argument.

### Body

Insert before the `return FeatureSnapshot(` at `:1022`:

```python
        partners: Dict[str, FeatureSnapshot] = {}
        for sym in self.partners:
            k = self.partner_index(i, sym)
            if k < 0:
                continue                      # I2: absent, not None-valued
            psnap = self.partners[sym].snapshot(k)
            if psnap is not None:
                partners[sym] = psnap
```

and add `partners=partners,` to the constructor call.

**Note the `i`, not `base_index`.** `[repo-verified: futures_agents/features.py:1009]` `snapshot`
clamps `i = min(max(0, base_index), len(bars) - 1)` and then uses `i` for every other field
(`self._session_state[i]`, `self._news[i]`, `self.regime_at(i)`). Using the unclamped `base_index`
for the partner lookup while everything else uses `i` would desynchronise the partner from the rest
of the snapshot at the two ends of the series. `partner_index` clamps too, so the bug would be
silent.

**Absent, not `None`-valued.** `continue` rather than `partners[sym] = None`. `A1`'s `partner()`
returns `.get()`, so both read the same from a condition's side, but keeping `None` out of the dict
means `snap.partners` is always a map of real snapshots and `len(snap.partners)` is a truthful count
of what was observable on this bar — which is the diagnostic a developer will actually reach for when
a relational strategy reports zero trades.

**Cost.** `[repo-verified: futures_agents/backtest/engine.py:310-312]` `run_many` builds the
snapshot lazily and **at most once per bar** (`if snap is None: snap = self.frame.snapshot(i)`),
shared across every strategy. So one partner costs one extra `snapshot()` per bar in total, not per
strategy. Eager population is therefore the right default and the measured overhead should be
roughly linear in partner count. **Do not make this lazy in the first version.** A lazy accessor
must close over a fixed index; if it closes over anything the loop later advances, the condition
reads a partner bar from the future and I1 is defeated by the optimisation. If profiling later
demands laziness, it must close over an integer captured at snapshot-build time, and T3.5 must be
re-run against the lazy path.

**What breaks if skipped.** `FeatureSnapshot.partners` stays empty forever and every relational
condition declines on every bar — a strategy that reports zero trades and looks like a data problem.
This is D38's exact signature (a feature that appears to work and silently measures nothing), so if
A4 is skipped the failure is maximally expensive to diagnose.

**How to test.**
- **T4.1** `test_snapshot_partner_matches_partner_index`: for a sample of *i*, `snap.partner(p).ts ==
  p_bars[frame.partner_index(i, p)].ts`.
- **T4.2** `test_partner_snapshot_never_carries_a_future_timestamp`: `snap.partner(p).ts +
  timedelta(minutes=p_base_minutes) <= snap.ts + timedelta(minutes=base_minutes)` for every bar.
  This is T3.1 restated at the snapshot level — worth having both, because A4 is where an index/`i`
  mix-up would break the chain that T3.1 alone cannot see.
- **T4.3** `test_partner_absent_before_partner_series_starts`: on the `MGC_1d` × `MES_1d` pair of
  T3.4, `snap.partner("MES") is None` for the leading bars and not None afterwards.
- **T4.4** `test_clamped_index_keeps_partner_in_step`: `snapshot(-5)` and `snapshot(0)` agree on the
  partner; `snapshot(len+5)` and `snapshot(len-1)` agree.

---

## 5. A5 — `Condition` gains `partner`, `bind_partner()` and a partner-rendering `label`

**File:** `futures_agents/strategies/base.py`. **Anchor:** `@dataclass(frozen=True) class Condition`
`:90-91`, fields `:94-102`, `bind` `:104-106`, `label` `:153-155`.
`[repo-verified: futures_agents/strategies/base.py:90-106,153-155]`

### Signature before

```python
@dataclass(frozen=True)
class Condition:
    name: str
    group: str
    fn: ConditionFn
    kind: ConditionKind = ConditionKind.SIGNAL
    description: str = ""
    timeframe: Optional[int] = None          # :100
    warmup_bars: int = 50                    # :102

    def bind(self, timeframe: int) -> "Condition":                 # :104
        """Return a copy of this condition pinned to a specific timeframe."""
        return replace(self, timeframe=timeframe)

    @property
    def label(self) -> str:                                        # :153-155
        return f"{self.name}@{tf_label(self.timeframe)}" if self.timeframe else self.name
```

### Signature after

```python
@dataclass(frozen=True)
class Condition:
    name: str
    group: str
    fn: ConditionFn
    kind: ConditionKind = ConditionKind.SIGNAL
    description: str = ""
    timeframe: Optional[int] = None
    warmup_bars: int = 50
    #: Partner symbol this condition is bound to, or None for the traded symbol.
    #:
    #: Two modes, and which one applies is decided by ``partner_mode``:
    #:  * REDIRECT — evaluate ``fn`` against the PARTNER's snapshot. Any of the
    #:    79 existing conditions becomes an inter-market read with no new code.
    #:  * RELATIONAL — evaluate ``fn`` against the PRIMARY snapshot; ``fn``
    #:    reads the partner itself via ``snap.partner(...)``. Needed whenever the
    #:    answer depends on BOTH series (a ratio, a correlation, a spread).
    partner: Optional[str] = None
    partner_mode: str = "REDIRECT"           # "REDIRECT" | "RELATIONAL"

    def bind(self, timeframe: int) -> "Condition":
        """Return a copy of this condition pinned to a specific timeframe."""
        return replace(self, timeframe=timeframe)

    def bind_partner(self, symbol: str, *, mode: str = "REDIRECT") -> "Condition":
        """Return a copy of this condition bound to a partner symbol.

        Mirrors :meth:`bind` exactly, including returning a new frozen instance
        rather than mutating, so a condition in the shared ``CONDITIONS``
        registry can be bound by one strategy without affecting any other.
        """
        if mode not in ("REDIRECT", "RELATIONAL"):
            raise ValueError(f"{self.name}: unknown partner_mode {mode!r}")
        return replace(self, partner=symbol.upper(), partner_mode=mode)

    @property
    def label(self) -> str:
        """Human-readable identity. **Also the hash input** — see base.py:613.

        ``partner`` MUST appear here. ``Strategy.strategy_id`` builds its content
        hash from ``sorted(c.label ...)`` (base.py:613), so a field that ``label``
        omits is invisible to the strategy's identity. That is D43 exactly, and
        this is the third place in this file where it could happen.
        """
        base = f"{self.name}@{tf_label(self.timeframe)}" if self.timeframe else self.name
        if self.partner:
            base = f"{base}:{self.partner}"
            if self.partner_mode != "REDIRECT":
                base = f"{base}#{self.partner_mode[:3]}"
        return base
```

`Condition` is `[repo-verified: futures_agents/strategies/base.py:90]` `@dataclass(frozen=True)`, so
`dataclasses.replace` is already the idiom `bind` uses at `:106` and `bind_partner` is a two-line
extension of a pattern that exists.

**Label format `name@tf:PARTNER`.** Safe to extend:
`[measured: grep -rn "split(\"@\")\|split('@')" --include=*.py . | grep -v __pycache__ → no match]`
— nothing in the repository parses a condition label by splitting on `@`, so adding a `:PARTNER`
suffix cannot break a consumer. The `#RED`/`#REL` suffix is emitted only for the non-default mode so
existing labels of unbound conditions are byte-identical.

### The REDIRECT dispatch, and the one line a developer will get wrong

REDIRECT lives in `Condition.evaluate` (A6), and the trap is the `tfs` guard.
`[repo-verified: futures_agents/strategies/base.py:125-126]`:

```python
        if snap.tf(tf) is None:
            res = ConditionResult.no()
```

Under REDIRECT that guard must be applied to **the redirected snapshot**, not the primary. Written
against the primary, a condition redirected to a partner whose frame lacks timeframe `tf` sails past
the guard and calls `fn(partner_snap, tf)`; `fn` then does `_s(snap, tf)` → `None` → most conditions
return `no()` correctly, but a condition that indexes without checking raises `KeyError`, which
`[repo-verified: futures_agents/strategies/base.py:131-133]` swallows into `no()` while incrementing
`CONDITION_ERRORS`. The result is a condition that reports zero trigger rate *and* an error tally,
with no way to tell "this partner has no 240m frame" from "this condition is broken". Apply the
guard to the snapshot `fn` will actually receive and the message is unambiguous.

**Consequence for A2, stated so it is not discovered later:** a REDIRECT binding requires the
partner frame to carry the timeframe the condition is evaluated on. The cheapest discipline is to
build partner frames with the same `timeframes` list as the primary. This is **not** enforced in A2
— a partner frame legitimately might not be able to carry a finer timeframe than its own base
(`[repo-verified: futures_agents/features.py:805-807]` raises), e.g. `SPY` is 5m-finest
`[measured: round-1 R2-D0 → SPY/QQQ finest = 5m]` so a 1m REDIRECT binding to SPY is impossible in
principle. Let it decline and say why in the detail string; do not raise at construction, because a
strategy may legitimately hold a 1m condition on the primary and a 60m one on the partner.

**What breaks if skipped.** Without `partner` there is no way to say which series a condition reads
— and without the `label` change, D43 recurs: two bindings of one condition hash to one
`strategy_id` (§7).

**How to test.**
- **T5.1** `test_bind_partner_returns_a_new_condition`: `c.bind_partner("SPY") is not c` and
  `c.partner is None` afterwards (registry not mutated).
- **T5.2** `test_label_renders_partner`: `CONDITIONS["regime_trending"].bind(1440).bind_partner("SPY").label
  == "regime_trending@1D:SPY"`.
- **T5.3** `test_label_unchanged_for_unbound_conditions`: for all 79 conditions in `CONDITIONS`, the
  label is byte-identical to before the change. Guards every stored `strategy_id` in
  `performance_db` against silent invalidation.
- **T5.4** `test_bind_partner_rejects_unknown_mode`.

---

## 6. A6 — the cache key, which is mandatory

**File:** `futures_agents/strategies/base.py:108-149` (`Condition.evaluate`), key at **`:121`**;
type hints at `:109`, `:653`; and `futures_agents/backtest/engine.py:288`.
`[repo-verified: futures_agents/strategies/base.py:108-121,653; futures_agents/backtest/engine.py:288]`

### Signature before

```python
    def evaluate(self, snap: FeatureSnapshot, default_tf: int,
                 cache: Optional[Dict[Tuple[str, int], ConditionResult]] = None
                 ) -> ConditionResult:
        ...
        tf = self.timeframe or default_tf
        key = (self.name, tf)                    # :121
```

and `[repo-verified: futures_agents/backtest/engine.py:288]`
`cache: Dict[Tuple[str, int], ConditionResult] = {}`,
and `[repo-verified: futures_agents/strategies/base.py:652-654]` `Strategy.evaluate`'s same hint.

### Signature after

```python
CondCacheKey = Tuple[str, int, Optional[str], str]      # (name, tf, partner, mode)

    def evaluate(self, snap: FeatureSnapshot, default_tf: int,
                 cache: Optional[Dict[CondCacheKey, ConditionResult]] = None
                 ) -> ConditionResult:
        ...
        tf = self.timeframe or default_tf
        key = (self.name, tf, self.partner, self.partner_mode)
        if cache is not None:
            hit = cache.get(key)
            if hit is not None:
                return hit
        target = snap if self.partner is None or self.partner_mode == "RELATIONAL" \
                 else snap.partner(self.partner)
        if target is None:
            # I2: the partner had no closed bar at this primary bar. Decline.
            res = ConditionResult.no()
        elif target.tf(tf) is None:
            res = ConditionResult.no()
        else:
            try:
                res = self.fn(target, tf)
            except (...):                         # unchanged tuple, :130-133
                ...
```

Three type hints move together: `base.py:109`, `base.py:653`, `engine.py:288`. A `Tuple[str, int]`
hint left behind is only a type error, not a runtime one — but leaving it makes the next reader
believe the key is still two-wide, which is how the defect comes back.

### Why this is not optional — the failure it prevents, restated precisely

`[repo-verified: futures_agents/backtest/engine.py:288]` `run_many` allocates **one cache per bar,
shared across every strategy in the call** (`:263-265` docstring: *"All strategies share one per-bar
condition cache, so a condition used by 800 strategies is computed once per bar"*). With the key at
`(name, tf)`:

1. Strategy X holds `regime_trending` bound to partner `SPY`. It evaluates first on this bar, writes
   `("regime_trending", 1440) → yes`.
2. Strategy Y holds `regime_trending` bound to partner `MCL`. It looks up `("regime_trending",
   1440)`, hits, and returns **SPY's answer**.
3. No exception. No zero. No log line. `CONDITION_ERRORS` is empty. Y's `detail` string even reads
   plausibly. Y has tested a pair it was not configured for, and the only way to find out is to
   notice that two differently-configured strategies produced identical trade lists.

Order-dependent, so it is intermittent across sweeps — the worst kind. And it collapses a
partner-bound condition onto the *unbound* one too: `regime_trending` (traded symbol) and
`regime_trending:SPY` share `("regime_trending", 1440)`, so the plain condition can return the
partner's answer. **That is worse than the relational feature being absent**, because it silently
corrupts existing non-relational strategies that happen to share a bar with a relational one.

Same shape as D38 (`toolkit.measure_custom` silently zeroing custom conditions) and as D43
(`strategy_id` collapsing four filter fields), both of which cost this programme real measurements.

**What breaks if skipped.** The above. Ship A1-A5 and A7-A8 without A6 and the repository acquires a
new defect class rather than a new capability — and the defect is in the shared cache, so its blast
radius is every strategy in every portfolio run, not only the relational ones.

**How to test.**
- **T6.1 `test_two_partner_bindings_do_not_share_a_cache_entry`** — the regression test for the
  defect. Build a probe condition whose `fn` returns `yes(detail=snap.symbol)`; bind it to two
  partners; evaluate both against one snapshot with **one shared cache dict**; assert the two
  details differ and `len(cache) == 2`. Run this test against the *unpatched* key first and confirm
  it fails — a collision test that has never been seen to fail is not evidence.
- **T6.2 `test_unbound_and_bound_do_not_share_a_cache_entry`** — same probe, one unbound and one
  bound to `SPY`; assert the unbound answer is the primary's.
- **T6.3 `test_redirect_missing_partner_declines_without_erroring`** — bind to a symbol the frame
  does not carry; assert `not res.triggered` **and** `condition_errors() == {}`. Declining must not
  go through the exception path, or a legitimate configuration looks broken (see A3's note on
  `partner_index` returning `-1` rather than raising).
- **T6.4 `test_relational_mode_receives_the_primary_snapshot`** — probe with
  `mode="RELATIONAL"` returning `yes(detail=snap.symbol)`; assert the detail is the **primary's**
  symbol. This pins the one line of the dispatch that distinguishes the two modes.
- **T6.5 `test_cache_hit_still_works`** — evaluate the same bound condition twice with one cache and
  assert `fn` ran once (count calls). The cache must still be a cache.

---

## 7. A7 — `BacktestEngine`: the deliberate non-change

**File:** `futures_agents/backtest/engine.py`. `[repo-verified: futures_agents/backtest/engine.py:231-235]`

```python
    def __init__(self, frame: SymbolFrame, ...):
        self.frame = frame
        self.spec: ContractSpec = frame.spec          # :233
        ...
        self.costs = CostModel(self.spec)             # :235
```

**Nothing changes here, and that is the scoping decision that keeps Wall A cheap.** Partners ride
*inside* the frame (A2), so `run_backtest`
`[repo-verified: futures_agents/backtest/engine.py:548]` and `run_portfolio`
`[repo-verified: futures_agents/backtest/engine.py:554]` — both `(frame: SymbolFrame, ...)` — need no
new parameter and none of their 57 referencing files
`[measured: grep -rln "run_portfolio\|run_backtest\|BacktestEngine(" --include=*.py . | wc -l → 57, round 1]`
change.

`self.spec = frame.spec` at `:233` stays the traded contract's spec. One tick grid, one
`CostModel`, one round turn, R on one notional contract
`[repo-verified: futures_agents/backtest/engine.py:22-25 module docstring]`. **The partner is a
signal input and is never traded, never costed, never sized.**

**Two prohibitions that belong here because this is where they would be violated.**

1. **Never cost an ETF partner leg as traded.** `[repo-verified: futures_agents/config.py:235-243
   (QQQ), :244-252 (SPY); zero-cost lines at :238 and :247]` both carry
   `commission_per_side=0.0, exchange_fee_per_side=0.0`, and
   `[repo-verified: futures_agents/config.py:227-234]` the repo's own comment says this "flatters
   their backtests against the micros" and to "treat results here as a proxy read". Under Wall A
   they cannot be traded at all, which makes the prohibition structural rather than a convention —
   worth writing down precisely so that nobody relaxes it when Wall B is considered.
2. **A multi-leg position would be costed as one contract, so do not build toward one here.**
   `[repo-verified: futures_agents/backtest/engine.py:235]` `self.costs = CostModel(self.spec)` is a
   **single-spec** object. A 3:2:1 crack is six contracts across three tick grids and three round
   turns; this object would charge one. That is why Wall A keeps the traded instrument scalar (A7) and
   why any leg-ratio work is Wall B, priced separately. Stated here because `CostModel(self.spec)` is
   three lines from `self.spec = frame.spec` and is exactly where a developer "finishing the job"
   would reach.
3. **A partner-derived result is not a spread result.** A one-legged "the ratio is stretched, buy the
   cheap leg" carries the leg's own variance, not a spread's. Any ranking of a Wall-A strategy must
   say so in the same sentence as the Sharpe, or the number will be read as a market-neutral one.
   (`R2_expressibility_wall.md` §5, II-6.)

**What breaks if skipped.** Nothing — there is nothing to skip. The failure mode here is the
opposite: a developer "finishing the job" by threading partner specs into `CostModel` or making
`self.spec` a mapping. That is Wall B, it is not additive, and it turns an eight-edit change into a
structural one. If that work is wanted it is a separate decision with a separate price.

**How to test.** `test_engine_ignores_partners_for_costing`: run an identical strategy on a frame
with and without partners attached, where the strategy holds no partner-bound condition, and assert
the trade lists and `BacktestResult.to_dict()` are identical. Proves partners are inert until
something reads them.

---

## 8. A8 — the loader

**File:** `futures_agents/research/runner.py:71-75` and `futures_agents/features.py:1050-1052`.
`[repo-verified: futures_agents/research/runner.py:71-75; futures_agents/features.py:1050-1052]`

### Signatures before

```python
# runner.py:71
def _frame(symbol: str, horizon: str):
    suffix, base_min, tfs = HORIZONS[horizon]
    series = load_csv(f"csv/raw/{symbol}_{suffix}.csv", symbol, base_min)
    return series, build_symbol_frame(series, tfs), tfs

# features.py:1050
def build_symbol_frame(series: BarSeries, timeframes: Sequence[int],
                       spec: Optional[ContractSpec] = None) -> SymbolFrame:
    return SymbolFrame(series, timeframes, spec)
```

### Signatures after

```python
def _frame(symbol: str, horizon: str, *, partners: Sequence[str] = ()):
    """One symbol's frame, optionally with partner series attached.

    Partner frames are built with the SAME ``tfs`` as the primary so a REDIRECT
    binding can find its timeframe, and WITHOUT partners of their own so the
    snapshot graph stays one level deep (A2's guard enforces it).
    """
    suffix, base_min, tfs = HORIZONS[horizon]
    series = load_csv(f"csv/raw/{symbol}_{suffix}.csv", symbol, base_min)
    pframes = []
    for p in partners:
        p_series = load_csv(f"csv/raw/{p}_{suffix}.csv", p, base_min)
        p_tfs = [t for t in tfs if t >= p_series.minutes]
        pframes.append(build_symbol_frame(p_series, p_tfs))
    return series, build_symbol_frame(series, tfs, partners=pframes), tfs


def build_symbol_frame(series: BarSeries, timeframes: Sequence[int],
                       spec: Optional[ContractSpec] = None, *,
                       partners: Sequence["SymbolFrame"] = (),
                       allow_coarser_partners: bool = False) -> SymbolFrame:
    return SymbolFrame(series, timeframes, spec,
                       partners=partners,
                       allow_coarser_partners=allow_coarser_partners)
```

`build_symbol_frame`'s new parameters are keyword-only with current-behaviour defaults, so all 144
call sites are untouched.

**The `p_tfs` filter is not cosmetic.** `[repo-verified: futures_agents/features.py:805-807]`
`SymbolFrame` raises `ValueError` on a timeframe finer than its own base. `SPY`'s finest file is 5m
`[measured: round-1 R2-D0]`, so `_frame("MES", "fast", partners=("SPY",))` — whose `tfs` is
`[5, 15, 60]` — happens to work, but `HORIZONS["fast"]`'s `base_min=5` against a partner with a
coarser base would not. Filtering rather than raising lets a partner contribute the timeframes it
has. A partner ending up with an empty `p_tfs` should raise, not silently attach a frame nothing can
read.

**Naming trap, worth one line.** `_frame` interpolates `f"csv/raw/{symbol}_{suffix}.csv"`. The
`HORIZONS` suffixes are `1d/1h/15m/5m` `[repo-verified: futures_agents/research/runner.py:34-39]`,
and `MCL` has **no** `1d` file `[measured: round-1 R2-D0 → MCL daily bars = 0 in csv/raw]`. So
`_frame("MGC", "position", partners=("MCL",))` fails on a missing file, not on anything subtle. The
error should name the path.

**Cross-store warning, carried forward from round 1 because it will bite here first.**
`csv/raw` stamps are UTC and `data/archive` stamps are Eastern
`[measured: round-1 R2-D0, head -1 of each]`. A3 compares `end_ts` values directly, so mixing a
`csv/raw` primary with a `data/archive` partner without normalising the timezone shifts the
alignment by 4-5 hours in whichever direction the naive comparison falls — and because A3 is
backwards-only, half the year it would *leak*. **A8 as specified loads both series from `csv/raw`
only.** A cross-store loader is a separate edit and needs its own test that asserts both series'
first `end_ts` agree with an independently computed UTC instant.

**What breaks if skipped.** Partners can only be attached by hand-constructing `SymbolFrame`s, so
every experiment writes its own loader, and the `p_tfs` filter and the store/timezone discipline get
re-derived (or not) each time.

**How to test.**
- **T8.1** `test_frame_without_partners_is_unchanged`: `_frame("MES", "position")` returns a frame
  with `partners == {}`.
- **T8.2** `test_frame_with_partner_loads_and_aligns`: `_frame("MGC", "position",
  partners=("SPY",))` → `frame.partners.keys() == {"SPY"}` and the count of base bars with
  `partner_index(i, "SPY") >= 0` matches the independently measured intersection
  (`[measured: round-1 R2-D0 → MGC_1d × SPY_1d = 2,507 exactly aligned of 2,511/2,512]`; the
  `>= 0` count will be **larger** than 2,507 because backwards-only carries the last closed SPY bar
  through a day SPY did not print — see §9.1, and assert the relationship rather than equality).
- **T8.3** `test_missing_partner_file_names_the_path`.
- **T8.4** `test_partner_timeframes_are_filtered_not_raised`: a partner whose base is coarser than
  some of the primary's `tfs` attaches, carrying only the timeframes it can.

---

## 9. The three things round 1 left open — rulings

### 9.1 The alignment rule under mismatched sessions

**The measurement that forces the question.** `[measured: round-1 R2-D0/§6, exact timestamp
intersection]` `MES_1h` × `SPY_1h` = **1,805 of 5,000** aligned bars (36%), `MNQ_1h` × `QQQ_1h` =
**1,794**, because the futures trade ~23h and the ETF ~6.5h
`[repo-verified: futures_agents/config.py:241 (QQQ) and :250 (SPY) → globex_open="04:00",
globex_close="20:00", vs the futures default 18:00-17:00 at config.py:45-46]`. Futures × futures barely loses anything:
`MES_1h` × `MGC_1h` = **4,986 of 5,000**.

**The rule, stated precisely.**

> At primary bar *i*, a condition bound to partner *p* sees the snapshot of the **last bar of p's own
> series whose `end_ts <= bars[i].end_ts`**, regardless of how long ago that was. If no such bar
> exists, `snap.partner(p)` is **`None`** and the condition returns `ConditionResult.no()`.

Four consequences, all deliberate:

1. **There is no "no bar for the current primary bar" case in the sense the question implies.** Once
   the partner has printed its first bar, there is always a last-closed one. What varies is its
   **age**. Between 16:00 and 09:30 ET the partner reading on an hourly futures primary is the
   16:00 ETF bar, held for 17.5 hours. The inner join's 36% is a property of *simultaneity*, not of
   availability, and backwards-only alignment does not need simultaneity.
2. **`None` therefore means exactly two things**, both of which occur only at the edges: the partner
   is not attached to this frame, or the primary's bar precedes the partner's first bar. The second
   is a real, large, on-disk case — `MGC_1d` starts 2016-09-26 and `MES_1d` starts 2019-05-03
   `[measured: round-1 R2-D0]`, ~650 leading bars — which is why T3.4/T4.3 use it.
3. **It cannot leak, and the reason is structural, not probabilistic.** `end_ts` is the instant the
   partner bar's information was complete `[repo-verified: futures_agents/data/bars.py:37,51 →
   `ts` is the OPEN, `end_ts = ts + minutes`]`. The primary snapshot's decision instant is its own
   bar's close: `[repo-verified: futures_agents/features.py:1023]` `price=bar.close`, and the entry
   fills at the **next** bar's open `[repo-verified: futures_agents/backtest/engine.py:290-292 →
   "fill pending entries at this bar's open"; :346 and :355 → `entry = spec.round_to_tick(bar.open +
   sign * slip)`. BT2's `event_clock.py` docstring cites :296-300 for this; the pending-fill block is
   :290-295 and the fill price is set at :355.]` The selected partner bar satisfies `end_ts <=
   primary.end_ts <= fill instant`, so it was complete before the decision and strictly before the
   fill. **Staleness is a loss of information; it is not a leak.** The distinction matters because
   the tempting "fix" for a 17-hour-old ETF reading is to interpolate or to use the partner's
   currently-forming bar, and both of those *are* leaks.
4. **A stale partner reading is safe and statistically dangerous.** Seventeen consecutive hourly
   bars carrying one ETF close makes those bars non-independent. Two mitigations, and the spec takes
   both: A2's coarser-partner guard (§2) catches the gross case at construction, and the rule below
   handles the subtle one.

**Therefore II-3 belongs at daily, and the rule that puts it there is not "prefer daily" but a
declarable staleness bound.** Add one optional keyword to `bind_partner`:

```python
    def bind_partner(self, symbol: str, *, mode: str = "REDIRECT",
                     max_partner_age_min: Optional[float] = None) -> "Condition":
```

and in the dispatch, after resolving `target`:

```python
        if (self.max_partner_age_min is not None and target is not snap
                and (snap.ts - target.ts).total_seconds() / 60.0
                     > self.max_partner_age_min):
            res = ConditionResult.no()          # partner too stale to speak
```

With `max_partner_age_min=None` (the default) behaviour is exactly the rule above. With it set to the
primary bar length, the condition speaks **only** where the two series genuinely overlap — the inner
join, opted into explicitly, at the cost of declining on 64% of `MES_1h` bars. That turns "should
this be daily?" from a judgement into a parameter with a measurable cost, and it must enter `label`
(§9.2) like every other behaviour-bearing field.

**My recommendation stands and is now justified rather than asserted:** run II-3 and any other
ETF-bearing family at **daily**, where `[measured: round-1 R2-D0]` `MGC_1d` × `SPY_1d` = 2,507 of
2,511 and `MES_1d` × `SPY_1d` = 1,855 of 1,859 — ~100% overlap, so staleness never exceeds one bar
and the two mitigations never bind. At daily, `max_partner_age_min` can be left `None` and the
question does not arise. **One caveat I cannot resolve without the data in front of me:** a daily
`MGC` bar and a daily `SPY` bar sharing a timestamp do not share a *content window* (gold's globex
day vs the ETF's 09:30-16:00), so the partner's content is strictly earlier than the primary's close
and the comparison is conservative — safe, but it means "same-day" is doing slightly different work
for the two series. Worth stating in any published result; not worth a code change.

### 9.2 What a partner-bound condition's `strategy_id` must include

**The mechanism, verified.** `[repo-verified: futures_agents/strategies/base.py:606-623]`
`Strategy.strategy_id` is a SHA1 over nine `parts`, and the conditions enter as
**`[repo-verified: futures_agents/strategies/base.py:613]`
`"|".join(sorted(c.label for c in self.conditions))`** (with `trigger_conditions` the same way at
`:619`). **`Condition.label` *is* the condition's identity for hashing purposes.** There is no
`Condition.identity` property.

**Therefore the requirement is exact and minimal:**

> `Condition.label` must render `partner`, `partner_mode` and `max_partner_age_min` whenever they
> differ from their defaults. Nothing else is needed, because `label` already reaches the hash.

**This is the third instance of a defect this repo has already paid for twice.**
`[repo-verified: workspace/studies/DEFECTS.md:640-653]` **D43** — `StrategyFilters.label()` omitted
`rth_only`, `days_of_week` and both minutes-since-open bounds, so *"the same rule set with
`rth_only=True`, with `rth_only=False`, with `max_minutes_since_open=90` and with
`days_of_week={MON}` all hashed to `MES-240m-107391c3583f`"*, and since
`[repo-verified: futures_agents/backtest/engine.py:277]` `run_portfolio` keys both its results dict
**and its open-position state** by `strategy_id`, running two arms in one call silently merged them.
D43 records itself as the *"second instance of the identity defect already fixed on
`ExitModel.label`"* — where `[repo-verified: futures_agents/strategies/base.py:249-267]` `identity`'s
docstring records that `R_MULTIPLE` and `ANCHOR_STRUCTURE` exits *"both rendered as
`STRUCTUREx1->1/2/3R`"* and *"one silently overwrote the other's trades"*.

**Without the label change, Wall A reproduces D43 precisely.** `regime_trending:SPY` and
`regime_trending:MCL` on one base strategy would both render `regime_trending@1D`, hash identically,
and collide in `run_portfolio`'s results dict — so one partner binding would report the other's
trades, with the A6 cache collision feeding it the other's *answers* at the same time. Two
independent silent-merge mechanisms pointing the same way. **A5's label change and A6's cache key are
one defect fixed in two places and neither is optional.**

**What the fix should look like, given the precedent.** Both prior fixes replaced a hand-written
list with `dataclasses.fields`, explicitly *"so a field added later cannot quietly reintroduce the
collision"* `[repo-verified: futures_agents/strategies/base.py:261-262, 473-476]`. **That technique
cannot be copied verbatim onto `Condition`**, because `Condition.fn` is a function object whose
`repr` contains a memory address — a `fields`-derived identity would be unstable across processes and
would break every stored `strategy_id`. So:

- **Do** extend `label` by hand for the three new fields (the minimum, and it reaches the hash).
- **Do** add the guard test that makes the hand-written list safe: **T9.2**
  `test_every_behaviour_bearing_condition_field_reaches_the_label` — enumerate
  `dataclasses.fields(Condition)`, subtract an explicitly named exclusion set
  `{"fn", "description", "group", "warmup_bars"}`, and for each remaining field construct two
  `Condition`s differing only in it and assert their labels differ. A field added later that is not
  in the exclusion set fails the test, which is the same protection `dataclasses.fields` gives the
  other two classes, obtained differently.
- `kind` is in the exclusion set deliberately: a SIGNAL and a FILTER of one name is not a
  configuration the combinator produces, and adding `kind` to the label would change all 79 existing
  labels and invalidate every stored id. Record the reasoning in the exclusion set's comment so the
  next reader does not think it was an oversight — that is exactly how D43 happened.
- `warmup_bars` is in the exclusion set **because nothing reads it**:
  `[measured: grep -rn "warmup" --include=*.py futures_agents/backtest/ futures_agents/strategies/ → only base.py:102 (the field) and library.py:40,47 (the setter)]`.
  It is declared and never consumed by the engine. That is the same shape as R1-Q1 (the `estimated`
  flag set and never read) and it is R1's lane, not mine; flagged, not pursued. If it ever *is*
  consumed it must move out of the exclusion set, and T9.2 will not catch that, so it is noted here
  instead.

**The residual gap, which the label cannot close.** `strategy_id`'s `parts`
`[repo-verified: futures_agents/strategies/base.py:612-620]` carry `self.symbol` but **nothing about
the frame's partner set**, and `BacktestResult`
`[repo-verified: futures_agents/backtest/engine.py:79,134]` records `strategy_id`, `symbol` and
`primary_tf` but no partner provenance. So a strategy holding a `:SPY` condition run against a frame
*with* SPY and against a frame *without* it produces **two different results under one
`strategy_id`** — the first trades, the second declines on every bar. And
`[repo-verified: futures_agents/storage.py:146]` `PRIMARY KEY (strategy_id, scope, regime, session)`
means the second **overwrites** the first in `performance_db`.

This is not a Wall A defect — it is Wall A making an existing gap reachable. The strategy's
definition genuinely is the same; what differs is the *environment* it was measured in, which this
schema has never had to represent because there has only ever been one environment per symbol. Two
honest options, and I am not the owner of either:

- **(a) Provenance field.** Add `partners: str` to `BacktestResult` (sorted, comma-joined, from
  `frame.partners`) and to the `strategy_performance` primary key. Correct, and a schema migration.
- **(b) Discipline.** Never run a partner-bound strategy against a frame lacking its partner, and
  assert it: a `Strategy.required_partners` property (the set of `c.partner` over all conditions) and
  an `__init__`-time check in `BacktestEngine` that `required_partners <= frame.partners.keys()`,
  raising otherwise. **Cheaper, catches the error at the boundary rather than recording it, and it
  converts a silent overwrite into a loud refusal.**

**I recommend (b) for Wall A and log (a) as a board question** (`R2-REQ-1`), because (b) is ~6 lines
inside the edits already specified and (a) touches a schema three other agents read. (b) has a real
limitation worth stating: it prevents the *accident*, but it cannot represent a deliberate
partner-present/partner-absent A/B comparison in one performance database. Anyone running that
comparison must keep the two arms in separate stores — the same workaround D43 forced on worker 2
(*"which is why worker 2 had to run its RTH arm in a separate process"*,
`[repo-verified: workspace/studies/DEFECTS.md:648-650]`).

### 9.3 New condition, or partner-bind an existing one? — and the concrete first one

**Both, and the distinction is the design.** This is why A5 carries `partner_mode`:

| mode | `fn` receives | needs a new condition? | what it expresses | families |
|---|---|---|---|---|
| **REDIRECT** | the **partner's** snapshot | **No.** All 79 work as-is. | a one-sided read of the partner: *"is the partner trending / above its EMA200 / in an expanding-volatility regime"* | II-5, II-7, II-8 |
| **RELATIONAL** | the **primary's** snapshot; `fn` reaches the partner itself | **Yes**, one per relationship | a two-sided read: a ratio, a correlation, a spread z-score | II-3, II-6, II-9 |

REDIRECT is the larger and cheaper win and it is the one round 1 did not state clearly. It converts
the existing library into a relational library at the cost of **one line** in `Condition.evaluate`
(A6's `target`), because a condition is already a pure function of `(snapshot, tf)` and a partner
snapshot is a snapshot. `[repo-verified: futures_agents/strategies/base.py:87]` — the signature that
is the wall is also what makes the redirect free.

RELATIONAL cannot be avoided for the families whose mechanism *is* the relationship. A ratio z-score
is not a property of either series. II-9 (correlation regime) is the cheapest Wall-A unlock in
Class II (`R2_expressibility_wall.md` §5) and it is RELATIONAL by necessity.

**Ship REDIRECT first, with one existing condition, and no new condition at all.** That is the
testable first step: it exercises A1-A8 end to end while holding the signal layer fixed at code
already in the repository, so anything that goes wrong is attributable to the plumbing and not to a
new indicator. A new condition in the same change would confound the two.

**The one concrete first condition:**

> **`CONDITIONS["regime_trending"].bind(1440).bind_partner("SPY")`, on an `MGC_1d` primary with a
> `SPY_1d` partner.** Label: `regime_trending@1D:SPY`.

Why this one, against the alternatives:

- **It is a FILTER**, not a SIGNAL `[measured: python3 -c "from futures_agents.strategies.library
  import CONDITIONS; print(CONDITIONS['regime_trending'].kind)" → ConditionKind.FILTER]`. A FILTER
  is a permission; it cannot manufacture a direction. A partner-bound SIGNAL lets a *second
  instrument's* trend decide the traded symbol's direction, which is a far larger claim and the wrong
  thing to put in the same change as new plumbing. `[repo-verified: futures_agents/strategies/base.py:671-674]`
  a FILTER returning `not triggered` makes `Strategy.evaluate` `return None` — no trade, never a
  reversed trade. **That is the code-level reason I2's "decline" is safe**: in both kinds, a declining
  condition can only remove trades.
- **Its `fn` is two lines and reads one field.**
  `[measured: inspect.getsource(CONDITIONS['regime_trending'].fn)]` → `r = snap.regime.regime;
  return yes(...) if r in ("TREND_UP","TREND_DOWN") else no()`. No path arithmetic, no window, no
  parameter. Under REDIRECT the answer is *"SPY's regime classifier says TREND_UP or TREND_DOWN"* —
  hand-checkable against `csv/raw/SPY_1d.csv` for any single date, which is what makes the first
  binding auditable rather than merely green.
- **It never touches `tf`.** So it isolates the partner plumbing from the timeframe plumbing. The
  `snap.tf(tf) is None` guard still applies (A6) and `SPY_1d` carries 1440, so the guard passes for
  the right reason.
- **`MGC` × `SPY` is the longest aligned pair in the repository** — `[measured: round-1 R2-D0/§6]`
  **2,507** exactly-aligned daily bars, 2016-09-26 → 2026-09-18, ten years. Nothing else in `csv/raw`
  comes close.
- **It is a genuine inter-market statement.** `[repo-verified: futures_agents/config.py:248]`
  `SPY.correlation_group == "US_EQUITY_BROAD"`; `[repo-verified: futures_agents/config.py:156]`
  `MGC.correlation_group == "PRECIOUS_METALS"` — different groups, and
  `[repo-verified: futures_agents/config.py:157]` MGC's RTH is 08:20-13:30, not the equity session. So D14/D41's "one complex, agreement is not corroboration" caveat does
  **not** bite — which it would if the first binding were `MES` with partner `SPY`. **Do not use
  `MES`×`SPY` as the first binding.** They are the same underlying: *"is SPY trending"* while trading
  MES is a noisy copy of MES's own regime, so a positive result would be uninterpretable and a null
  one uninformative. It is the most obvious pair on disk and it is the wrong one, which is exactly
  why it needs saying.
- **Mechanism, so this is a hypothesis and not a mined pattern:** gold's behaviour is conditioned on
  the equity risk regime (risk-off flows into metals; trending equities compete with a
  non-yielding asset). That is II-5's canonical conditioning version, it is the version
  `R2_expressibility_wall.md` §5 marked as having a valid on-disk proxy, and it is **not** the
  rates-vs-equity or dollar-vs-metals version, for which no series exists. State the substitution
  when reporting.

**One thing that must travel with this choice, and it makes it better rather than worse.**
`regime_trending` is on the repo's alias list: `[repo-verified: workspace/roundtable/discovery/AVENUES.md:213, avenue X-9]`
*"seven filter names are exact aliases for group membership (... `regime_trending`≡TREND,
`regime_ranging`≡MEAN_REVERSION ...), so A/B on any of them compares groups"*. The manager's round-2
board instructs citing X-9 rather than re-deriving it
`[repo-verified: workspace/roundtable/msgs/05_manager_all_round2-board.md, "Two corrections" §2]`.

**The alias does not transfer to the partner-bound form, and the reason is the whole point of Wall
A.** The alias holds between *the traded symbol's own* regime and *the traded strategy's* group label.
`regime_trending@1D:SPY` reads **SPY's** regime. A second instrument's regime is not an alias for the
traded strategy's group membership under any reading, so the X-9 collapse does not apply.

That asymmetry buys a three-arm design better than any non-aliased condition would give, and it is
the design the first measurement should use:

| arm | what it is | interpretation |
|---|---|---|
| base | the host strategy alone | reference |
| base + `regime_trending@1D` (unbound) | **a known group alias** (X-9) | the control whose meaning is already settled: "does conditioning on *a* trend regime matter" — and it is a group comparison, not a condition test |
| base + `regime_trending@1D:SPY` | the partner binding | "does conditioning on *the partner's* trend regime matter" |
| base + shuffled-SPY binding | the placebo | trigger rate held, alignment destroyed |

**Prohibition that follows:** never report "the partner arm beat the unbound arm" as a relational
finding without stating that the unbound arm is an X-9 group alias. That comparison is
partner-regime versus group-membership, and the second term is not what it looks like.

**What the first binding must report, and the honest prior.** A regime filter has no distribution of
its own; its claim is that it reshapes another strategy's. So the first measurement is a **paired**
one: the same base strategy with and without `regime_trending@1d:SPY`, the same bars, plus a
placebo — the same gate with SPY's regime series **timestamp-shuffled**, which holds the gate's
trigger *rate* fixed and destroys only its alignment (`placebo_shift` leaks; see D42
`[repo-verified: workspace/studies/DEFECTS.md:620]`). And with `n=2,507` daily bars the trade count
after an RTH-and-regime-filtered daily strategy will be small; the sample-size penalty applies before
the profit factor is even looked at. **My prior is that this measures nothing**, and that is the
point: it is a plumbing test that happens to also be a real hypothesis, in that order.

**The RELATIONAL first condition, when its turn comes** — named here so the spec is complete, not for
this change: `partner_ratio_zscore(partner, window)`, II-6/II-3, whose `fn` reads
`snap.tf(tf).close` and `snap.partner(p).tf(tf).close`, holds the ratio's rolling mean and SD over
`window` bars, and declines when either side is missing. Every parameter (`partner`, `window`) must
be in the condition's `name` — BT2 has already established that idiom for a different family
(`[repo-verified: workspace/roundtable/backtest/BT2/code/event_gate.py:104-107]` `_slug` bakes every
parameter into the name for exactly the A6 reason), and copying it is cheaper than re-deriving it.

---

## 10. Test plan, consolidated

Every test named above, in the order a developer should write them. Tests marked **red-first** must
be seen to fail before the corresponding edit lands — a collision or leak test that has never failed
is not evidence.

| # | test | edit | red-first? |
|---|---|---|---|
| T1.1 | `test_partner_defaults_to_empty` | A1 | no |
| T1.2 | `test_partner_lookup_is_case_insensitive` | A1 | no |
| T1.3 | `test_partner_snapshot_is_one_level_deep` | A1/A2 | no |
| T1.4 | `test_to_dict_unchanged_by_default` | A1 | no |
| T2.1-3 | self / nested / duplicate partner rejected | A2 | no |
| T2.4 | coarser partner rejected by default, allowed on opt-in | A2 | no |
| T2.5 | finer partner accepted | A2 | no |
| T2.6 | `test_partner_free_construction_is_byte_identical` | A2 | no |
| **T3.1** | **`test_no_partner_bar_ends_after_the_base_bar_it_is_aligned_to`** | **A3** | **yes — patch `end_ts`→`ts` and watch it fail** |
| T3.2 | `test_partner_index_is_the_LAST_such_bar` | A3 | yes |
| T3.3 | `test_partner_index_is_monotone_nondecreasing` | A3 | no |
| T3.4 | `-1` before the partner series starts (`MGC_1d`×`MES_1d`) | A3 | no |
| T3.5 | appending a future partner bar never changes history | A3 | no |
| T4.1-4 | snapshot↔index agreement, no future stamp, absent at the edges, clamping | A4 | no |
| T5.1-4 | `bind_partner` copies; label renders partner; 79 labels unchanged; bad mode raises | A5 | no |
| **T6.1** | **two partner bindings do not share a cache entry** | **A6** | **yes — the D38/D43-shaped defect** |
| **T6.2** | **unbound and bound do not share a cache entry** | **A6** | **yes** |
| T6.3 | missing partner declines with an empty `CONDITION_ERRORS` | A6 | no |
| T6.4 | RELATIONAL mode receives the primary snapshot | A6 | no |
| T6.5 | the cache is still a cache (`fn` called once) | A6 | no |
| T7.1 | engine ignores partners for costing | A7 | no |
| T8.1-4 | loader: unchanged default, aligns, names a missing path, filters timeframes | A8 | no |
| **T9.2** | **every behaviour-bearing `Condition` field reaches the label** | A5/§9.2 | **yes — add a dummy field and watch it fail** |
| T9.3 | `required_partners <= frame.partners` enforced at engine construction | §9.2(b) | no |

`[repo-verified: tests/test_features.py:36,91]` T3.1 and T3.2 are the timeframe-axis tests
`test_no_aligned_bar_ends_after_the_base_bar_it_is_aligned_to` and
`test_aligned_bar_contains_no_base_bar_that_had_not_closed` with the axis swapped. Reuse their
fixtures.

---

## 11. Anti-overfitting and bias audit **of this change**

The change itself can introduce bias, so it gets the same audit a strategy would. Stating what I
checked and what I found, not a clean bill on things I could not test.

| hazard | checked? | finding |
|---|---|---|
| **Look-ahead bias** | **Yes — the central risk.** | Two concrete vectors, both closed: `ts` instead of `end_ts` in A3 (§3, failure mode 1), and `bisect`-on-nearest (failure mode 2). Closed by the two-pointer form plus T3.1-T3.3. A third vector is created by an *optimisation*, not by the feature: a lazy partner accessor closing over a mutable index (§4). Named and prohibited in the first version. |
| **Future-data leakage** | **Yes.** | The staleness/leak distinction in §9.1(3): a 17-hour-old ETF reading is safe; interpolating or forward-filling it is not. This matters because the naive fix for the 36% hourly overlap is exactly the unsafe one. |
| **Silent-wrong-answer / repainting** | **Yes — two found, both pre-emptive.** | (i) The A6 cache collision — and its scope is worse than round 1 said: it collapses a bound condition onto the **unbound** one too, so it can corrupt existing non-relational strategies sharing a bar. (ii) The §9.2 `strategy_id` collision, which is D43's third instance. Both are D38's shape: a feature that appears to work and reports a number meaning something else. |
| **Insufficient sample size** | **Yes.** | The first binding has `n = 2,507` daily bars but a far smaller trade count after filtering. A2's coarser-partner guard and §9.1's `max_partner_age_min` both exist because a stale partner *inflates apparent* sample through block autocorrelation — the D28 failure mode arriving through the data. |
| **Understated costs / slippage** | **Yes, structurally.** | A7's prohibition 1: `[repo-verified: futures_agents/config.py:244-251,253-260]` the ETF specs carry zero commission and zero exchange fee with the repo's own warning. Under Wall A the partner is never traded, so the understatement is unreachable by construction — the strongest available form of the fix. |
| **Unrealistic fills** | **Not applicable.** | Wall A does not touch the fill path. `[repo-verified: futures_agents/backtest/engine.py:7-18]` engine rules 2-4 unchanged. The spread-fill hazard (a spread's fill is not the difference of two leg fills) belongs to Wall B. |
| **Data-mining bias** | **Yes, and it is the reason for §9.3's ordering.** | The partner axis multiplies the search space by the number of candidate partners: 11 symbols in `csv/raw` `[measured: round-1 R2-D0]` × 79 conditions × 2 modes is ~1,700 new bindings before any parameter. Naming **one** first binding, with a stated mechanism, chosen for auditability rather than for promise, is the defence. Any later sweep over partners must declare its `n` for the `sqrt(2·ln n)` deflation (PIPELINE §4). |
| **Parameter sensitivity** | **Flagged, not tested.** | `max_partner_age_min` (§9.1) and, when RELATIONAL arrives, the correlation/ratio window are the places where the parameter *is* the result. II-9's entry in `R2_expressibility_wall.md` §5 already records that a 20-day and a 120-day correlation routinely disagree in sign at turning points. |
| **Out-of-sample / walk-forward** | **Not applicable to a plumbing change; mandatory for anything it measures.** | Nothing is fitted by A1-A8. The first thing Wall A enables that *can* be fitted is a ratio hedge ratio or a correlation threshold, and estimating either in-sample and applying it in-sample is the single most common way this family manufactures an edge. |
| **Survivorship bias** | **Yes, inherited.** | Every `=F` series and `CL_1440m.jsonl` is a front-month splice with no contract-month label (round 1, R2-D4 §2). Wall A does not touch it, but a partner *chosen from* those series inherits it, and the roll steps are at seasonal frequency. Not an issue for the `MGC_1d`×`SPY_1d` first binding — both are single continuous instruments. |
| **Cross-store timezone error** | **Yes — found and fenced.** | `csv/raw` is UTC, `data/archive` is Eastern `[measured: round-1 R2-D0]`. A3 compares `end_ts` directly, so a cross-store pair mis-aligns by 4-5 hours and, being backwards-only, *leaks* for part of the year. A8 as specified loads both series from `csv/raw` only; cross-store is a separate edit with its own test (§8). |
| **Repainting indicators** | **Yes.** | No new indicator. Every partner value comes from `TimeframeFrame.snapshot` on a **closed** bar `[repo-verified: futures_agents/features.py:811 → resample(..., keep_partial=False)]`, so a partial partner bar cannot be read. |

---

## 12. Is this handable to a developer? — and what I could not pin down

**Handable.** A1-A8 each have a file, a verified line, a before/after signature, a body where the
body is where the error would be, a stated consequence of skipping, and named tests. §10 is the
order to write them in. Two edits (A3, A6) are called out as the ones that decide whether the change
is a capability or a defect.

**What I could not pin down, stated rather than papered over:**

1. **Runtime cost is reasoned, not measured.** §4's argument that partner snapshots cost one extra
   `snapshot()` per bar rests on `[repo-verified: futures_agents/backtest/engine.py:310-312]` building
   `snap` at most once per bar. I did not run a sweep to measure it — DIVISION §8 and my round-2
   brief forbid `run_portfolio`. If a partnered sweep turns out materially slower, the lazy variant
   in §4 is the answer and its hazard is named there.
2. **The `strategy_id` provenance gap (§9.2) has no owner.** I recommend option (b) and log (a) as
   `R2-REQ-1`. The schema at `[repo-verified: futures_agents/storage.py:126,146]` is read by agents
   other than me and I should not choose for them.
3. ~~`tf_label(1440)`'s exact rendering.~~ **Closed.**
   `[measured: python3 -c "from futures_agents.features import tf_label; print([tf_label(t) for t in
   (1,5,15,60,240,1440)])" → ['1m','5m','15m','1h','4h','1D']]`. The label is
   `regime_trending@1D:SPY`, capital D. Every `@1d` in an earlier draft of this file was wrong and is
   corrected; if a developer copied one, T5.2 will fail on the case.
4. **Whether `max_partner_age_min` (§9.1) is wanted at all in version one.** It is four lines and it
   turns a judgement into a parameter, which I think is right. But it is also a new parameter on the
   partner axis, and §11's data-mining row is the argument against adding parameters early. I have
   specified it as **optional with a `None` default that reproduces the plain rule**, so it can be
   shipped or dropped without touching anything else. If dropped, II-3 must be run at daily by
   convention instead of by construction, and that convention has to be written into whatever runs
   it.
5. **The content-window subtlety in §9.1's caveat.** A daily `MGC` bar and a daily `SPY` bar share a
   timestamp but not a content window. I am confident it is conservative (the partner's information
   is strictly earlier) and I could not fully characterise it without reading raw session boundaries
   bar by bar, which needs a measurement I did not run. Stated as a reporting caveat.
