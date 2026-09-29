# The pipeline — discovery, scoping, sectioned research

This replaces round 1's shape. In round 1 the manager mapped 53 families itself, up front, and
handed each researcher six fixed deliverables. That is top-down: the manager did the discovering,
and a researcher could only fill in boxes someone else had already drawn.

The pipeline below inverts the two ends. **Discovery is its own agent**, and **scoping belongs to
the researcher who has to do the work.**

```
  DISCOVERY ------ main task ------> MANAGER ---- "what do you need?" ----> RESEARCH  <--+
  short bursts                      task board                            scopes        |
  AVENUES.md ledger                 sections, one at a time                itself        |
       ^                               ^   ^                                  |          |
       |                               |   |                                  |       findings
       +-- never re-explores           |   +---- "add a sub-task" <------------+          |
           a closed avenue             |   |         mid-research request                |
                                       |   |                                             |
                                       |   +---- "add a sub-task" <---------+            |
                                       |             from the bench          |           |
                                       |                                 BACKTESTER -----+
                                       +--- board carries both -------->  short bursts
                                                                          codes ALGO-k
                                                                          asks: faithful?
```

Three pairs run this way: **R1+BT1, R2+BT2, R3+BT3.** Both halves of a pair can put work on the
manager's board, and a backtester's questions go to its own researcher, never to another's.

## 1. Discovery — breadth, in short bursts

**Owns:** `discovery/AVENUES.md`, `discovery/MAIN_TASKS.md`, `discovery/bursts/*.md`.

Discovery works at **altitude**. It is looking for *whole avenues* — a family, a mechanism, a
literature, a market structure — not for the mechanics of any one strategy. Depth is somebody
else's job, and handing depth to discovery is what collapses this pipeline back into round 1.

**Short bursts are a requirement, not a style note.** One burst is one narrow sweep with a stated
question, a stated stopping point, and a written result. A burst that wanders into implementation
detail has failed even if what it found is interesting — it should have logged that as a lead and
stopped. Each burst writes `discovery/bursts/NN_<slug>.md`.

**`AVENUES.md` is the memory that stops re-exploration**, and it is the single most important file
discovery owns. Every burst **reads it in full before starting** and **appends to it before
finishing**. Each avenue carries a verdict:

| verdict | meaning | may a later burst revisit? |
|---|---|---|
| `CLOSED-EMPTY` | explored, nothing there | **no** — not without a new reason, stated |
| `CLOSED-FOUND` | explored, produced a main task | no — the main task carries it now |
| `OPEN-PARTIAL` | explored to a stated depth, more remains | yes, from the recorded stopping point |
| `DEFERRED` | out of reach for a named reason (no data, no primitive) | only if that reason changes |

An avenue with no verdict is a bug in the ledger. If a burst finds itself re-covering ground,
that is the ledger's failure to record, and fixing the entry is part of the burst.

**A main task** is discovery's output, appended to `MAIN_TASKS.md`. It is one avenue judged worth
depth, stated at altitude: what the avenue is, why it plausibly matters here, what it would take
to know, and what discovery deliberately did *not* investigate. Discovery does not decompose it.
Decomposing is the researcher's job, next.

## 2. Manager — the board, and the question it must ask

**Owns:** `manager/BOARD.md`, `manager/ADJUDICATIONS.md`, `DIVISION.md`, `OPEN_QUESTIONS.md`.

The manager reads a main task and **does not decompose it either.** Its first move is to ask the
researcher: *what sub-task breakdown do you need to research this, and at what granularity?*

This is the inversion that matters. The researcher will discover that the main task needs five
sub-tasks, or two, or that it needs a prerequisite nobody anticipated. The manager cannot know
that in advance, and round 1 is the evidence — it pre-registered expectations precisely because
it knew its own guesses were guesses.

Once the researcher's scope comes back, the manager:
- turns it into **sections** on `BOARD.md`, in dependency order,
- dispatches **one section at a time**, never the whole main task,
- adjudicates boundary disputes into `ADJUDICATIONS.md`,
- and **accepts mid-research sub-task requests** (below) rather than deferring them to a round.

A section is the unit of work. Sections exist so a main task can be paused, resumed, split across
limit windows, or abandoned partway without losing what was already learned.

## 3. Research — scopes itself, then requests more as it learns

**Owns:** `research/<id>/SCOPE.md`, `research/<id>/findings.md`, `research/<id>/REQUESTS.md`.

Two distinct modes, and a researcher is always told which one it is in:

**Mode SCOPE.** Given a main task, produce `SCOPE.md`: the sub-tasks this actually needs, each
with what it would answer, what it needs to read or run, roughly how big it is, and what depends
on what. **Do no research yet.** An honest scope that says "this main task is three sub-tasks and
one of them is impossible without X" is the deliverable.

**Mode SECTION.** Given one section, research it, append to `findings.md` as you go, and finish.

**The mid-research request is the point of the whole design.** Research turns up things the scope
could not have anticipated — a prerequisite, a confound, a better question, a family next door
that turns out to be the real subject. When that happens, append to `REQUESTS.md`:

```
## REQ-<n> <one line>
- **Arose in:** section <id>, doing <what>
- **The ask:** add a sub-task to main task <id> that ...
- **Why it cannot wait / why it can:** ...
- **What it blocks:** nothing | section <id> | the main task's conclusion
- **My estimate of its size:** small | medium | large
```

Then **keep working on the current section.** Do not stall on the request and do not silently
widen your section to cover it — silent widening is how a section stops being resumable. The
manager routes it, and either adds it to the board or says why not.

## 4. Backtesters — one paired to each researcher

**BT1 ↔ R1, BT2 ↔ R2, BT3 ↔ R3.** Each backtester owns `backtest/<id>/ALGOS.md`,
`VERIFY.md`, `REQUESTS.md`, `bursts/*.md` and `code/*`.

A backtester turns its researcher's findings into **running code**, and its defining constraint is
that it is **not searching for a winner**. This repository has already spent ~3,000,000 evaluations
searching for winners and found none that clears its own threshold. A backtester that starts
hunting profitable variants is re-running that programme with fewer controls, and its output would
be worth less than nothing because it would look new.

What it is doing instead: **making a researched idea executable and then finding out what it
actually does.** A faithful implementation that measures nothing is a complete success. An
implementation that measures something, with a placebo beside it, is a bigger one.

```
R<n> findings.md  ──read──>  BT<n> codes ALGO-k  ──"is this faithful?"──>  R<n>
                                    ^                                       │
                                    └────────── verdict, then correct ───────┘
                                                (loop until FAITHFUL)
```

### The fidelity loop, which is the point of the pairing

A backtester reads findings; it does not receive them pre-digested. Reading is lossy, so **before
trusting any number an algorithm produces, the backtester asks its researcher whether the code
means what the research said.** Not "does this look right" — a specific, answerable question.

Each algorithm gets an entry in `ALGOS.md` and a numbered question in `VERIFY.md`:

```
## ALGO-<k> <name>
- **Implements:** <finding id> from research/<id>/findings.md
- **Code:** backtest/<id>/code/<file>.py:<lines>
- **My reading of the finding:** <what you believe it claims, in your own words>
- **Where I had to choose:** <every place the finding was silent and you decided>
- **Fidelity:** UNVERIFIED | ASKED | FAITHFUL | DIVERGENT(<how>)
```

The **"where I had to choose"** field carries most of the value. A finding never fully specifies
an implementation — which bar, inclusive or exclusive, what happens on a tie, what happens when the
window is short. Those silent choices are where an implementation quietly stops being the thing
that was researched, and writing them down is what makes the researcher's answer possible.

Ask via `msgs/NN_BT<n>_R<n>_verify-ALGO-<k>.md`. The researcher replies
`msgs/NN_R<n>_BT<n>_re-verify-ALGO-<k>.md` with **FAITHFUL**, or **DIVERGENT** and what is wrong.
On DIVERGENT: fix the code, then ask again. Do not argue the finding — if you think the finding
itself is wrong, that is a `REQUESTS.md` entry for the manager, not a fidelity dispute.

**Never report a number from an UNVERIFIED algorithm.** An unverified result is not a weak result,
it is an unknown quantity: nobody can say what was measured.

### Short bursts, here too

One burst is **one algorithm, or one fidelity cycle, or one measurement** — then write it down and
stop. Never code three algorithms before asking about any of them: a wrong assumption in the first
propagates silently into the rest, and you will have spent three bursts to learn one thing.

Each burst writes `backtest/<id>/bursts/NN_<slug>.md`: what you did, what you chose, what you
asked, where you stopped.

### What a backtester may run, and what it must report with any number

Unlike round 1, backtesters **may** run backtests — that is the job. With three obligations:

1. **A placebo beside every result.** Run the algorithm's own exits, filters and sizing with the
   signal layer replaced (random bars count-matched, or timestamp-shuffled). `placebo_shift` leaks
   and is a conservative control only — see D42. A result without a control is not reportable.
2. **State the search size and the deflation threshold.** Searching *n* variants buys roughly
   `sqrt(2·ln n)` free t-units. If you tried six parameterisations, say six. The programme-wide
   figure is `free_t = 5.46` and the largest t ever found here is 3.923.
3. **Never route a comparative claim through `T.ab`** — it inflates z roughly 3.3× (D28). Use a
   paired test that accounts for the correlation, and name the test you used.

Read `workspace/studies/DEFECTS.md` before trusting any library function. D38 in particular:
`toolkit.measure_custom` silently zeroes custom conditions because it never calls
`register_frame` — if you write a custom condition and it appears to do nothing, that is why.

### Sub-task requests

Same channel as a researcher: append to your own `REQUESTS.md` in the PIPELINE §3 shape and keep
working. A backtester's requests tend to be the most concrete in the pipeline, because code either
runs or does not — "this needs a primitive the engine has no field for" is discovered by trying.

## 5. What the parent session does

Relays (no agent can call another), dispatches every agent so the limit gate is never bypassed,
records burn in `LEDGER.md`, runs `check_ownership.py` before every commit, and commits and pushes.

The manager is told not to spawn agents: only the parent can read `rate_limit_info`, so only the
parent can safely decide that a round may fire. See `THROTTLE.md`.

## 6. Round 1's output is not discarded

Three researchers ran under the old shape and their files are on the branch. Under this pipeline
that output becomes **discovery's starting ledger** — 53 families already mapped is 53 avenues
discovery must not re-explore. Its first burst begins by reading round 1 into `AVENUES.md` with
verdicts, which is exactly the anti-re-exploration mechanism working on real ground.
