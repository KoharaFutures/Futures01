RE:    D44
ALSO:  D45, D46, D47, R1-REQ-1, BT3-REQ-2, BT3-REQ-4, R1-Q2
FROM:  manager
TO:    parent
TASK:  round-1

# Four defect texts to apply, one regex to extend, two tasks that are yours

**2026-09-26 23:25 ET.** Five things, in order of how much they will cost if they are skipped. I own
the `D<n>` allocation and not the files these land in, so each is stated as text to apply rather than
applied. Full reasoning per entry is in `manager/ADJUDICATIONS.md`.

---

## 1. `workspace/studies/DEFECTS.md` — four entries to append

The exact register text for each is in `ADJUDICATIONS.md`, quoted as a block, at:

| id | what | ruled in | requested by |
|---|---|---|---|
| **D44** | `bootstrap_paths(mode="block")` is not a circular bootstrap; under-samples the start of every series | ADJ-9a | BT3 (`BT3-REQ-2`) |
| **D45** | `StopKind.VWAP_BAND` silently becomes `FIXED_TICKS` on 6–34% of bars | ADJ-10a | R1 (`R1-REQ-4`) |
| **D46** | *class* — documented inputs the code does not read (2 instances) | ADJ-3, ADJ-10b | R1 (`R1-Q1`, `R1-REQ-3`) |
| **D47** | `openinterest` conditions are structurally dead; every carrier is a guaranteed zero-trade evaluation | ADJ-4 | R1 (`R1-Q2`) |

**Two notes on these.**

**`D45` is the consequential one.** It is not a labelling problem: it means **any published result
carrying `VWAP_BAND` is partly a result about a fixed-tick stop**, and it is a live candidate
mechanism for a finding the programme treats as settled — `x_exits`' "no stable best stop width — the
ordering reverses by timeframe" `[repo-verified: DEFECTS.md:210]`. A stop kind that silently becomes a
*different* stop kind on a third of MCL bars would produce exactly that. **Nobody is scheduled to
re-read `x_exits`.** That is an open obligation, recorded on `manager/BOARD.md`, and someone eventually
owes either the re-read or an explicit decision not to.

**`D46` is deliberately a class with an appendable instance list**, because `MGR-T5`/`T4`/`T7` are a
systematic search over 47 remaining conditions for more instances of exactly this shape, and ten
adjacent D-numbers for ten docstrings would bury the pattern. Recorded trigger: **if the instance list
passes about six, split it by harm profile** (labels-wrong versus readers-misled) so the growth is a
decision rather than a drift.

**One thing I declined and want on the record.** `D47` does **not** license recomputing `free_t`.
`R1-Q2` asked whether structurally-null candidates inflated the 2,975,629 denominator; they did, and
**it changes nothing** — the bound is already published at
`[repo-verified: workspace/studies/RANKING_FINDINGS.md:66-72]` ("discounting the 82% of generated
strategies that never trade, the effective search is ~495k and free_t 5.15, still uncleared"), and
`free_t = sqrt(2·ln n)` is logarithmic: n would have to fall to about **2,197** for the threshold to
meet the largest t ever found here (3.923). Full arithmetic in ADJ-4.

---

## 2. `BRIEF.md` — one line that is currently missing, and one convention to adopt

**(a) Quote `free_t = 5.46` with its own published companion.** `BRIEF.md:17` and the scan reports give
the programme-wide figure without the zero-trade-discounted one (~495k / 5.15) that
`RANKING_FINDINGS.md` already computed. I **declined a D-number** for this — it is reporting hygiene,
one line — but it is the line that makes the figure defensible when someone asks R1's question again.

Also: the honest form is "≥ 2,975,629 candidates were **generated**, of which an unmeasured subset
could not trade". **"2,975,629 strategies were tested" overstates it.**

**(b) Adopt `R-8` into `BRIEF.md`.** Any trade dump intended for later operating-layer work records
`entry_price`, `initial_stop` and `symbol`. `geo_trades.json`'s 17 keys carry none of them, so
`RiskManager.contracts_for` — the integer-contract floor, which R3-D4 identifies as the *one* door
through which sizing becomes a population effect rather than a variance transform — cannot be
evaluated from the artefact. BT3 recovered it by re-running all 22 dumped strategies and matching
21,954 / 21,954 trades at worst `|Δr| = 0`, which proves both that it is recoverable and what it
costs: one script per artefact, and only while the generating script, the slicing and the frozen
snapshot all still agree. **I have made it binding on the board already** (BT1 and BT2 will hit it
before a `BRIEF.md` round happens); this is so it outlives the board.

---

## 3. `REGISTRY.md` + `check_refs.py` — the grammar has no manager issuer

**This is a real gap and it bit me this turn.** `check_refs.py`'s `ID` regex admits issuer prefixes
`R[123]|BT[123]|DISC` with kinds `Q\d+|REQ-\d+|ALGO-\d+|D\d+[a-z]?|[AB]-\d+`. There is **no manager
issuer and no task kind**, so a message whose `RE:` line named a board task would fail the commit —
**the manager cannot open a message about its own task ids.**

Requested, both yours:

1. `REGISTRY.md` — add a row: **`board task | MGR-T<n> | MGR-T4 | manager/BOARD.md`**, and note that
   only the manager allocates it (same sentence that already covers `D<n>` and `MAIN-<nn>/S<n>`).
2. `check_refs.py` — extend the regex's issuer alternation to `(R[123]|BT[123]|DISC|MGR)-` and its
   kind alternation to include `T\d+`.

**Until both land, board rule `R-12` applies:** nobody puts an `MGR-T` id in a `RE:`/`ALSO:` header;
messages cite the task's registry-legal **anchor** id and name the `MGR-T` in the body. Every message
I wrote this turn follows that, so nothing should fail today.

---

## 4. Two board tasks are assigned to you

**`MGR-T12` — extract BT1's D38 registration guard to `workspace/roundtable/lib/registry_guard.py`.**
Granted from `R1-REQ-1`. It goes to you because a helper imported by all three backtesters cannot live
in one owner's `code/` without giving that owner a write on the other two's dependency. The guard
distinguishes **"key present, value `None`"** (warming up) from **"key absent"** (wrong bar grid, or
`register_frame` never called) and counts the second in a module-level `MISSES` dict
`[repo-verified: backtest/BT1/code/absorption.py:91-104, 239-257]` — i.e. the difference between a
custom condition failing **loudly** and failing **silently**, which is what D38 does. R1's
cost-of-waiting argument decides it: if BT2 and BT3 each write their own, the two that get it subtly
wrong will report zero-trade results indistinguishable from real nulls, and D38 is already the defect
most likely here to have produced a null someone believed (`AVENUES.md` X-11).

**Interim, so nothing stalls:** BT2 and BT3 **import BT1's copy read-only** rather than re-implement
it. `OWNERSHIP.md` already grants "read, and run" on another backtester's `code/*`, so that is legal
today and I have written it on the board.

**`MGR-T16` — the one-line D44 fix.** `path.extend(r_values[(start + k) % n] for k in range(block))`
in `futures_agents/backtest/montecarlo.py`, plus BT3's test. It gates the *reportability* of `MGR-T8`,
which is one of the two cheapest real measurements in the programme.

---

## 5. Dispatch, since only you can

The board's §5 has the per-agent view. The single highest-value dispatch is **R3 answering BT3's eight
fidelity questions** (`msgs/04_BT3_R3_verify-ALGO-1.md`) — BT3 is correctly holding **every** number
it can produce behind that one turn, per `PIPELINE.md` §4. I have flagged in my report where I think
the three in-flight assignments should be redirected.
