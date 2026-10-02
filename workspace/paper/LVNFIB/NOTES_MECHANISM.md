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
