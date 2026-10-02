# Why the 2-minute cadence is a cron, not `desk_loop.sh`

**Stated disagreement with the hourly keepalive routine, recorded as that routine asks.**

The keepalive says: *"Never create your own crons, `send_later` chains or `/loop`. One loop
plus this keepalive is the whole mechanism."* This desk is now run by a 2-minute cron
instead. The reason, and the evidence:

1. **The owner asked for an update every 2 minutes, twice, in their own words.** A live
   instruction from the owner outranks a stored routine prompt. `CHARTER.md` remains the
   authority on *what* the desk trades; this note only concerns *how often it reports*.

2. **`desk_loop.sh` reports to nobody.** It runs `desk_check.py` in the background and only
   surfaces anything when it exits 10. Between exits the owner sees silence, so a 2-minute
   background check satisfied the letter of "check every 2 minutes" and none of the intent.

3. **A background loop does not survive a worker restart.** Observed twice on 2026-10-01:
   a 58.4-minute outage ending 20:56 ET, and a 39.3-minute outage ending 21:39 ET. Both
   times the process was simply gone. The hourly keepalive bounds such a gap at ~1 hour,
   which is wider than Friday's 08:00-12:00 ET entry window can afford. A cron is driven by
   the harness, not by a process inside the container, so it survives restarts.

4. **Double-reporting is avoided by role, not by count.** `cycle.sh` is still the only thing
   that runs the desk, holds the archive append-only, asserts the prior and commits.
   `report.py` is strictly read-only: it writes nothing and commits nothing, so it cannot
   race the loop's pushes or post a second version of the same event.

`desk_loop.sh` is kept working and its dormant sleep is now the check interval rather than
600s, so it is correct if anyone starts it. It is simply not the mechanism in use. If the
owner wants the keepalive's single-loop design restored, stop the cron and start the loop —
both are one command, and nothing else about the desk changes.

## 2026-10-02 — background-only: this desk notifies nobody

The owner split the job: **this desk runs silently in the background; a separate main
agent reads its output and does the notifying.** The 2-minute cron that posted a line
per tick is deleted — it was reporting "nothing changed" every two minutes, which is
exactly the spam the split is meant to end.

Running mechanism now:

    LVNFIB_BACKGROUND=1 bash workspace/paper/LVNFIB/desk_loop.sh

`desk_loop.sh` runs `cycle.sh` every 120 s. `LVNFIB_BACKGROUND=1` changes one thing:
on exit 10 (attention) the loop appends to `attention.jsonl` and KEEPS CYCLING rather
than exiting. Without it the desk would stop on the first resolution and stay stopped
until the hourly keepalive noticed — up to an hour of missed cycles, which inside an
08:00-12:00 ET entry window is the difference between catching a trigger and not.

### Where the notifying agent should read

Everything is pushed to `claude/intelligent-feynman-ongyjw` on every cycle:

| file | what it carries |
|---|---|
| `callouts.jsonl` | append-only; every callout with its levels, sizing, gate notes, source bar |
| `resolutions.jsonl` | append-only outcomes: `outcome`, `r`, `contracts`, `pnl_usd`, `exit_bar` |
| `attention.jsonl` | one line per exit-10 cycle, so a poller can find them without diffing |
| `state.json` | equity, peak, max drawdown, closed count |
| `desk_events.jsonl` | one line per cycle, woken or not — use it to tell a live desk from a dead one |

Cards are **not** in git (`cards/` is gitignored, ~215 KB each). Render on demand:

    python3 workspace/paper/LVNFIB/card_png.py <callout_id>

### What the notifying agent must not get wrong

- **Only MGC arm A can risk the account.** Everything else is `contracts: 0`; a
  resolution with `pnl_usd: 0.0` did not make or lose money and must not be presented
  as a trade result.
- **Win rate and payoff travel together.** A no-fill has no `r` and belongs in no average.
- **No price from these logs is current.** Every callout carries `as_of_bar`; quote it.
- **Nothing here clears its luck bar.** Arm A's prior is n=24 +0.2379R t +1.027,
  win 50.0% at payoff 1.58, against a 2.327 bar. It is a forward test, not an edge.
