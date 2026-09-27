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

Filename stays `NN_<from>_<to>_<topic>.md`, zero-padded and monotonic; if you race someone for a
number, take the next one. **A message with no `RE:` line is malformed** — `check_refs.py`
fails the commit on it.

## Say the id, not the description

When you write about another agent's work, name the id. "R1's finding about delta" is ambiguous
across four findings; **R1-D4** is not. When you disagree with something, quote the id you are
disagreeing with and the path you read it at, so the owner can tell whether you read the current
version or a stale one.
