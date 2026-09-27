# The pipeline — discovery, scoping, sectioned research

This replaces round 1's shape. In round 1 the manager mapped 53 families itself, up front, and
handed each researcher six fixed deliverables. That is top-down: the manager did the discovering,
and a researcher could only fill in boxes someone else had already drawn.

The pipeline below inverts the two ends. **Discovery is its own agent**, and **scoping belongs to
the researcher who has to do the work.**

```
   DISCOVERY  --------- main task ---------->  MANAGER  ---- "what do you need?" ---->  RESEARCH
   short bursts                                task board                              scopes itself
   AVENUES.md ledger                           sections                                     |
        ^                                          ^                                        |
        |                                          |                                        |
        +--- never re-explores a closed avenue     +------ "add a sub-task" <----------------+
                                                            mid-research request
```

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

## 4. What the parent session does

Relays (no agent can call another), dispatches every agent so the limit gate is never bypassed,
records burn in `LEDGER.md`, runs `check_ownership.py` before every commit, and commits and pushes.

The manager is told not to spawn agents: only the parent can read `rate_limit_info`, so only the
parent can safely decide that a round may fire. See `THROTTLE.md`.

## 5. Round 1's output is not discarded

Three researchers ran under the old shape and their files are on the branch. Under this pipeline
that output becomes **discovery's starting ledger** — 53 families already mapped is 53 avenues
discovery must not re-explore. Its first burst begins by reading round 1 into `AVENUES.md` with
verdicts, which is exactly the anti-re-exploration mechanism working on real ground.
