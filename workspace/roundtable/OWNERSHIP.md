# File ownership — one writer per file, always

## Why this is a manifest and not a chmod

Every agent in this container runs as **root** (verified: `id -u` → 0), and root bypasses mode
bits — a `chmod 444` file is still writable by anyone here. So ownership cannot be enforced by
the filesystem. It is enforced two other ways, both of which actually work:

1. **Structurally: no file in this tree ever has two writers.** Agents share by *creating new
   files* and by *reading* each other's, never by editing a file someone else owns. A message bus
   of one-file-per-message has no write contention by construction. This is the real guarantee.
2. **By audit at the commit boundary.** `check_ownership.py` maps every changed path to its owner
   and fails if a file was touched by anyone but. The parent session runs it before every commit
   and reverts violations. Nothing reaches the branch without passing.

## The map

| path | sole writer | everyone else |
|---|---|---|
| `BRIEF.md`, `THROTTLE.md`, `LEDGER.md`, `OWNERSHIP.md`, `PIPELINE.md`, `check_ownership.py` | **parent session** | read |
| `discovery/AVENUES.md` | **discovery** | read |
| `discovery/MAIN_TASKS.md` | **discovery** | read |
| `discovery/bursts/*.md` | **discovery** | read |
| `manager/BOARD.md` | **manager** | read |
| `manager/ADJUDICATIONS.md` | **manager** | read |
| `DIVISION.md` | **manager** | read |
| `OPEN_QUESTIONS.md` | **manager** (routes) | append via `msgs/` instead — but see the exception below |
| `research/R4_*`, `R5_*`, `R6_*` | **R4 / R5 / R6** | read |
| `discovery2/*` | **DISC2** | read |
| `discovery/claims/<who>-*.md` | **whoever created it**, once | read |
| `lib/*` | **parent** | read, and import |
| `workspace/studies/DEFECTS.md` | **parent** writes; **manager** allocates the ids | read |
| `workspace/studies/*`, `workspace/chrono/*` | **parent** | read |
| `research/<agent>/SCOPE.md` | **that researcher** | read |
| `research/<agent>/findings.md` | **that researcher** | read |
| `research/<agent>/REQUESTS.md` | **that researcher** | read |
| `research/R1_*.md`, `R2_*.md`, `R3_*.md` (round-1 flat files) | **that researcher** | read |
| `research/<id>/REQUESTS.md` | **that researcher** | read |
| `backtest/<bt>/ALGOS.md` | **that backtester** | read |
| `backtest/<bt>/VERIFY.md` | **that backtester** | read |
| `backtest/<bt>/REQUESTS.md` | **that backtester** | read |
| `backtest/<bt>/bursts/*.md` | **that backtester** | read |
| `backtest/<bt>/code/*` | **that backtester** | read, and run |
| `backtest/BT4/*`, `BT5/*`, `BT6/*` | **BT4 / BT5 / BT6** | read |
| `tests/test_bt<n>_*.py` (repo tests) | **that backtester** | read, and run |
| `tests/test_ef<n>_*.py` (repo tests) | **that edge-finder** | read, and run |
| `msgs/NN_from_to_topic.md` | **whoever created it**, once | read only, forever |

## Read is universal. Write is exclusive. Asking is how you cross the line.

**Every agent may read every file in this tree, always, without asking.** Ownership restricts
writing only. There is no private working file here and nothing is hidden from a teammate —
`AVENUES.md`, another track's `findings.md`, a backtester's code, the manager's board, the
parent's ledger, every posted message. **Read before you ask**, every time: the answer is usually
already written down, and a question whose answer was on disk costs the owner a turn for nothing.

When reading is genuinely not enough — you need the owner's *intent*, a judgement they did not
record, a reason behind a choice, or you believe their file is wrong — **ask them**:

```
msgs/NN_<you>_<owner>_<topic>.md
```

State what you read, what you could not determine from it, and what you would do with the answer.
The owner replies with their own message, `msgs/NN_<owner>_<you>_re-<topic>.md`. Both files are
write-once and each has exactly one writer, so the conversation never contends.

**Never edit another agent's file, not even to correct a plain error.** Especially then: a silent
cross-edit is how two agents come to hold different beliefs about what a file says, and neither
can tell which of them is stale. Post the correction as a message and let the owner apply it.

## The three rules every agent follows

1. **Write only under the paths this table gives you.** If you need something changed in a file
   you do not own, write a message into `msgs/` asking its owner. Do not edit it yourself, even
   to fix an obvious error — especially then, because a silent cross-edit is how two agents come
   to disagree about what a file says.
2. **`msgs/` files are write-once.** Create yours, never touch another's. Sequence numbers are
   zero-padded and monotonic; if you race someone for a number, take the next one.
3. **`csv/` is read-only for everyone, including the parent session. Never delete or edit any
   file under it, no matter what.** `data/archive/` is append-only.

## The one live exception, and why it is written down

Round 1's dispatch prompts told R1, R2 and R3 to append boundary disputes and cross-track
questions **directly** to `OPEN_QUESTIONS.md`. The map above says the manager is its sole writer.
Both cannot be true, and the map is the one I intend to keep — so this is a defect in the round-1
dispatch, not in the map.

It was caught by `check_ownership.py` rather than by review, which is the audit doing its job on
its first real commit.

**Resolution:** round 1's appends stand. They are genuine findings and destroying them to satisfy
a convention would be the wrong trade. The commit that carries them passes
`--allow workspace/roundtable/OPEN_QUESTIONS.md`, so the exception is declared on the command
line and recorded in the commit message instead of being a silent hole in the audit.

**From the pipeline onward:** a researcher with a question for another track or for the manager
writes `msgs/NN_<from>_<to>_<topic>.md` — write-once, no contention — and the manager consolidates
into `OPEN_QUESTIONS.md`. Every dispatch prompt after round 1 says this. If you are a researcher
reading this file and your prompt told you to edit `OPEN_QUESTIONS.md` directly, your prompt is
stale: post a message instead and say so in your report.

## A second narrow allowance: backtesters may add repo regression tests

BT1 raised this and it is right. Its standing role brief gives it `tests/`, while its dispatch
restricted it to `backtest/BT1/**`; it followed the dispatch and put its 33 checks in
`code/test_absorption.py`. The consequence is that **no regression test for D38 exists in the
repo's own `tests/`**, which is where it belongs and where it would stop the next agent losing a
burst to the same silent-zeroing defect.

So each backtester may also write `tests/test_bt<n>_*.py` — its own prefix, so two backtesters
cannot collide, and narrow enough that it cannot touch another agent's tests or the existing
suite. Run the full suite before finishing: a new test that breaks the other 817 is worse than
no test.

## Two discovery agents, one memory — the claim protocol

`AVENUES.md` exists so no avenue is explored twice. That makes it the one file two discovery
agents would both want to write, and one-writer-per-file forbids it. Partitioning the ledger
alone does not solve it either: two agents could still sweep the same avenue simultaneously and
each write it up in its own half.

So exploration is **claimed before it starts**, and a claim is a new file, which cannot contend:

```
discovery/claims/<DISC>-<avenue-id>.md      e.g.  discovery/claims/DISC2-X-4.md
```

The file states the avenue, the question, and the time claimed. **Before any sweep, a discovery
agent lists `discovery/claims/` and reads both ledgers.** If a claim already exists for that
avenue, pick another — do not negotiate, do not wait, and do not sweep it anyway because the other
agent's angle looks different. If you genuinely believe the avenue needs a second pass from another
direction, that is a message to the claim's owner and a note for the manager, not a second claim.

**Ledgers:** DISC1 owns `discovery/AVENUES.md` and `discovery/MAIN_TASKS.md`. DISC2 owns
`discovery2/AVENUES.md` and `discovery2/MAIN_TASKS.md`. Neither is the whole ledger, so **both must
be read before either is written** — an agent that reads only its own half has no memory of the
other's closures, which is the failure the ledger exists to prevent.

**Main task numbering:** DISC1 allocates odd (`MAIN-01`, `MAIN-03`, …), DISC2 even (`MAIN-02`,
`MAIN-04`, …). Disjoint by construction, so the two cannot race for a number the way the message
counter did.

## Standing role directories are shared, not private — a hazard, found 2026-09-27

Several agent types carry a standing role brief that points at a directory named after the *role*:
`workspace/developer/`, `workspace/manager/`, `workspace/strategy_research/`. EF1 wrote its
validation output to `workspace/developer/ef1_validation_swing_60m.json`, following its role brief
rather than its dispatch — the same conflict BT1 raised earlier about `tests/`.

**The output was fine. The location is a collision zone.** At the time this was found, **six live
agents were of type `developer`** — EF1, EF7, BT3, BT4, BT5, BT6 — so all six share that one
directory. `workspace/developer/out/test_report.json` and `log/activity.log` can be silently
overwritten by any of them, which is precisely the one-writer rule this file exists to enforce.

Worse, **the audit could not see it**: `check_ownership.py` scanned only `workspace/roundtable/`
and `tests/`. A write outside those was invisible. The scan now covers all of `workspace/`, and
these directories are reported as `shared-role` — never failed, because the role briefs legitimately
use them, but always flagged.

**So: if it is durable, it belongs in your own lane.** `workspace/roundtable/edge/EF1/`,
`backtest/BT4/`, `research/R4_*` — those are yours alone and nothing else writes them. Treat a role
directory as scratch that another agent may clobber between your writing it and anyone reading it.

## The one file where allocation and authorship differ

`workspace/studies/DEFECTS.md` is the programme-wide register. **The manager allocates every
`D<n>`; the parent writes the entry.** Nowhere else in this tree does one agent decide an id and
another write the text, and the split is deliberate:

- **Only the manager allocates**, because a `D<n>` is a scarce shared name and two agents reaching
  for "the next free number" is precisely how the question-numbering collided (see `REGISTRY.md`).
  Board rule `R-9` follows from this: an agent wanting a number **describes the defect** and does
  not name a number.
- **Only the parent writes**, because the register is read by every agent and by every future
  session, and because an entry needs its mechanism verified rather than relayed. Entries carry a
  provenance mark: `[verified here]` where the parent read the code and reproduced the behaviour,
  `[agent-measured]` where an agent's figures are being recorded.

This file was unmapped until 2026-09-27 and only surfaced when the audit's scan was widened from
`workspace/roundtable/` to all of `workspace/` — the same widening that exposed the shared role
directories. An unmapped file in a tree whose whole premise is one-writer-per-file is a gap in the
premise, not a detail.
