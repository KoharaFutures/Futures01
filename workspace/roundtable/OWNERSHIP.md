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
| `research/<agent>/SCOPE.md` | **that researcher** | read |
| `research/<agent>/findings.md` | **that researcher** | read |
| `research/<agent>/REQUESTS.md` | **that researcher** | read |
| `research/R1_*.md`, `R2_*.md`, `R3_*.md` (round-1 flat files) | **that researcher** | read |
| `msgs/NN_from_to_topic.md` | **whoever created it**, once | read only, forever |

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
