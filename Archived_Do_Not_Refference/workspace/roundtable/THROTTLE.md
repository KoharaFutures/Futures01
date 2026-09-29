# The session-limit throttle — who actually holds it

**The manager agent cannot see the session limit.** Its toolset is Read, Glob, Grep, Bash,
Write, Edit, TodoWrite, Agent — no MCP tools. `rate_limit_info` is only readable through
`mcp__Claude_Code_Remote__get_session`, which only the parent session can call. So the parent
session holds the gate and checks it before dispatching every round. The manager plans rounds;
it does not decide when they fire.

## What the limit actually is, as measured on 2026-09-27

```
rateLimitType : ccr_promotional
status        : allowed
isUsingOverage: false
resetsAt      : 2026-11-05T08:00:00Z   -- 943 hours / 39 days away
context_usage : 110,050 / 1,000,000 tokens  (11%)
```

**This is not a five-hour rolling window.** It was `five_hour` two days ago; it is now a
promotional window that does not refresh until 5 November. So "pause until the limit refreshes"
is not a throttle — it is a 39-day stop. Gating on it that way would end the research, not
protect it.

## The gate actually used

Three checks before each dispatch, in order of how hard they bite:

1. **`rate_limit_info.status` != "allowed"** → stop dispatching immediately. This is the real
   signal, and it is authoritative.
2. **Context window ≥ 85% of `max_tokens`** → stop dispatching and let compaction run first.
   This is the ceiling that has actually disrupted this session (it hit 77% and compacted), and
   unlike the promotional window it *does* recover. 850,000 tokens is the dispatch cutoff.
3. **Burn rate per round vs. what remains.** Measured from cumulative `usage` deltas between
   rounds, recorded in `LEDGER.md`. If a round's burn would take context past the cutoff, the
   round is split instead of launched whole.

At the cutoff the parent session does not idle: it banks every deliverable to disk, commits,
and reports. Research already written is never lost to a limit, which is the point of rule 1
in `BRIEF.md`.
