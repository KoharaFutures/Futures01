# ID registry — the single place any reference resolves

Seven agents are now working at once and they refer to each other's work constantly. An
ambiguous reference does not announce itself: it silently sends an agent to the wrong finding,
and the mistake surfaces later as a disagreement nobody can trace.

**This file is authoritative for what an ID means.** If a reference cannot be resolved here, it
is malformed — ask its issuer rather than guessing.

## The collision that already happened

Round 1 let each agent number its own questions in a shared file, and three agents reached for
the same numbers independently:

| as written | issuer → addressee | subject | **canonical id** |
|---|---|---|---|
| Q1 | R1 → manager | the `estimated` flag is set and never read | **R1-Q1** |
| Q2 | R1 → manager | did zero-trade `openinterest` strategies enter the 2,975,629 denominator | **R1-Q2** |
| Q3 | R1 → R2 | every MEDIUM/LOW `ECON_RULES` entry is invisible to all three `news` conditions | **R1-Q3** |
| Q4 | R2 → manager | Class II is mis-cut: II-10 and II-11 need no second observable | **R2-Q1** |
| Q5 | R2 → R1 | answering R1-Q3, plus a correction back | **R2-Q2** |
| **Q2** | **R3 → R1** | is `StopKind.VWAP_BAND` an ATR band in disguise | **R3-Q1** |
| **Q3** | **R3 → manager** | refutes DIVISION §6's "≤2" pre-registration for R3-D5 | **R3-Q2** |

So **"Q2" and "Q3" each name two different questions.** `OPEN_QUESTIONS.md` is the manager's
file and is not renumbered here — renumbering would break every citation already written into
five research files. The canonical column above is how they are referred to from now on, and a
bare `Q2` is a malformed reference.

## The naming rule, for everything from here

**`<ISSUER>-<KIND>-<n>`.** The issuer prefix is what makes an id unique, so it is never dropped,
not even inside the issuer's own file.

| kind | pattern | example | authoritative file |
|---|---|---|---|
| main task | `MAIN-<nn>` | `MAIN-01` | `discovery/MAIN_TASKS.md` |
| section of a main task | `MAIN-<nn>/S<n>` | `MAIN-01/S2` | `manager/BOARD.md` |
| avenue | `<class>-<n>` / `X-<n>` | `I-12`, `X-4` | `discovery/AVENUES.md` |
| discovery lead | `DISC-LEAD-<nn>` | `DISC-LEAD-05` | `discovery/AVENUES.md` |
| research finding | `<R>-<tag>` | `R1-D4`, `R3-A-1` | `research/<R>_*.md` |
| family verdict | `<class>-<n>` in a `<R>` file | `II-10` in `R2_relational.md` | that researcher's file |
| algorithm | `<BT>-ALGO-<n>` | `BT1-ALGO-1` | `backtest/<BT>/ALGOS.md` |
| question | `<issuer>-Q<n>` | `R3-Q1` | `OPEN_QUESTIONS.md` |
| sub-task request | `<issuer>-REQ-<n>` | `BT2-REQ-1` | that agent's `REQUESTS.md` |
| defect | `D<n>` (programme-wide) | `D38` | `workspace/studies/DEFECTS.md` |

`BT1-ALGO-1` and `BT2-ALGO-1` are different algorithms. That is the point of the prefix.

**Only the manager allocates `D<n>` numbers and `MAIN-<nn>/S<n>` sections.** Only discovery
allocates `MAIN-<nn>`. Everything else you allocate yourself inside your own prefix, so no two
agents can ever race for the same id.

## Harness component ids, allocated by the parent on 2026-09-27

`EF1-H<n>` was added as a kind because EF2 and EF3 both needed to cite EF1's harness and had
nothing to name. EF1 was mid-flight and had not published any, and **three messages were written
with prose in a `RE:` header as a result** — a gap in this registry, not a failure by those agents.
So the canonical ids are fixed here:

| id | component |
|---|---|
| `EF1-H1` | `session_window.classify_bar` — the bar classifier (`ON_BOUNDARY` / `IN_WINDOW` / `INTERIOR`) |
| `EF1-H2` | `SessionWindowEngine` — the engine wrapping it |
| `EF1-H3` | `violations()` — the invariant auditor |
| `EF7-H1..` | EF7's independent reimplementation, ids allocated by EF7 |
| `EF3-H1` | EF3's own local engine, built rather than blocking |

**`EF2-H1` was allocated in error and is withdrawn.** I wrote that EF2 had built a local engine
"rather than blocking". It did not — EF2 measured flat *reachability* by importing `EF1-H1`
directly and asking, for every cycle, whether the series contains any bar the rule could act on. No
engine, no tape, exact. EF2 reported the collision itself (`EF2-03`). The id names nothing; do not
cite it.

**A `RE:` header may now name a repo path instead of an id.** Three messages in a row failed this
check because an agent needed to name something real that had no id yet, and inventing one or
writing prose were the only options. The rule exists to prevent *ambiguity*, and a path is never
ambiguous — `workspace/roundtable/edge/EF1/code/session_window.py` names exactly one thing.

**`EF1-H1` is currently defective and it gates four agents.** Measured independently and in
agreement by two agents on disjoint symbol pairs: EF3 found **43 `SPANS_WINDOW` violations, max hold
71.0 hours, 19 of 507 MES/MNQ sessions**; EF2 found **17 of 506 MGC cycles (3.36%) and 34 on MCL**,
with half of MCL's excess traced to a data gap rather than the calendar. Both used `EF1-H3`, EF1's
own auditor, so the checker is right and the engine does not match it. Cause: the flat waits to
*see* a bar at or past 16:00, and on an early-close session no such bar exists.

## EF6's deliverables, and the practice this keeps exposing

| id | component |
|---|---|
| `EF6-H1` | the placebo cohort under the session window |
| `EF6-H2` | the firing-rate prefilter |
| `EF6-H3` | the deflation threshold function, taking (n, span) |
| `EF6-H4` | the strictly-causal forward roll |

**This is the fourth message to fail the reference check for the same reason, and the cause is mine
each time.** `EF1-H1..H3`, `EF2-H1` (withdrawn), and now these: I numbered work inside a dispatch
brief — "1. The placebo cohort, 2. The firing-rate prefilter" — and never gave those items ids, so
an agent needing to cite deliverable 2 had nothing to name and wrote prose. The agents were right
and the registry was incomplete.

**Standing practice, on me:** every numbered deliverable in a brief gets an id **in the same breath
it is written**. A brief that says "build three things" and names none of them is a brief that
guarantees an unresolvable citation.

## Every message carries what it is about

A message whose subject must be inferred from its prose is how a mixup starts. So each file in
`msgs/` opens with this block, before anything else:

```
RE:    <the one id this message is primarily about>
ALSO:  <other ids it touches, or "none">
FROM:  <your agent id>
TO:    <agent id, or "manager", or "all">
TASK:  <the MAIN-nn/Sn or burst you were working when this arose, or "round-1">
```

### Filenames: per-sender sequence, because the shared counter collided

The original rule was `NN_<from>_<to>_<topic>.md` with a shared monotonic counter and "if you race
someone for a number, take the next one." **That does not work under parallelism and it failed
within the hour:** seven agents ran at once, none could see another's unwritten file, and
`msgs/` ended up with two `03`s, two `04`s and three `05`s. So "see `msgs/04`" is ambiguous — the
exact failure this registry exists to prevent, reproduced in the registry's own mechanism.

**New rule: the sequence is yours, not shared.**

```
<FROM>-<nn>_<to>_<topic>.md        e.g.  BT2-01_R2_verify-ALGO-1.md
```

`<nn>` counts only your own messages, so no two agents can collide by construction — the same
principle that makes id prefixes work. Existing duplicate-numbered files are **not renamed**
(messages are write-once and are already cited), so when referring to one, give the full filename,
never the bare number.

**A message with no `RE:` line is malformed** — `check_refs.py` fails the commit on it, and it
also now warns on any duplicate leading number among the legacy files.

## Say the id, not the description

When you write about another agent's work, name the id. "R1's finding about delta" is ambiguous
across four findings; **R1-D4** is not. When you disagree with something, quote the id you are
disagreeing with and the path you read it at, so the owner can tell whether you read the current
version or a stale one.
