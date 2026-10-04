# LTA_EXPORT: handoff to KoharaFutures/KMOD-LTA-FUTURES

From session `session_01FsjMu3FuXfDBstj3dv52X7` (Futures01, branch `claude/zealous-sagan-n7jnmn`), 2026-10-04.
This folder is the standalone **LTA-Concepts** tree: copy its contents to the root of the new repo as-is.
It doesn't import anything from Futures01 (`desk/lta_common.py` replaces those dependencies).

## Files

| path | what |
|---|---|
| `README.md`, `CLAUDE.md`, `requirements.txt`, `.gitignore`, `.gitattributes` | repo front page, agent rules, deps (yfinance, pillow), ignores (`*.pdf`, `desk/live/`, state) |
| `study/README.md` | study area + tracker (8 sections, book pages) |
| `study/CONCEPTS_DIGEST.md` | full paraphrased digest of the book with page cites (`[pN]` = original-PDF page; book page = N − 10) |
| `study/notes/README.md` | template for per-section notes (none written yet) |
| `desk/` | the LTA Concept Callouts paper desk: `lta_common.py`, `lta_levels.py`, `macro.py`, `callout.py`, `ledger.py`, `scan.py`, `fetch.py`, `card_png.py`, `cycle.sh`, `desk.sh`, `desk_loop.sh`, `CHARTER.md`, `README.md`, `cot_inputs.example.json` |
| `desk/callouts.jsonl`, `desk/resolutions.jsonl` | the paper record: 4 callouts posted 2026-10-02, all resolved (1 win +2R, 3 losses; net −$152.79) |
| `desk/cards/*.png` | the 8 PNG cards for those callouts and outcomes |
| `.claude/agents/lta-concept-callouts.md` | agent definition |

Checked standalone on 2026-10-04: `bash desk/desk.sh MGC MNQ` fetched bars, built the level maps and the macro
layer, and resolved the ledger. `desk/scan.py` exits 3 (dormant) on weekends.

## Left out on purpose

- **The book PDF, in every version.** It's copyrighted and Futures01 is public. All of these exist only in the
  Futures01 session's container scratchpad:
  - `LTA_Concepts.pdf`: original, 314 pages, rebuilt from the owner's split zip
  - `LTA_Concepts_blank_front.pdf`, `_blank_v2.pdf`, `_v3.pdf` (290 pages): superseded intermediate steps
  - **`LTA_Concepts_v4.pdf`: the latest, 304 pages.** The owner already has it as a 3-part zip
    (`LTA_Concepts_v4.z01/.z02/.zip`). The owner should upload it to the private repo themselves.
  - `parts/00_Intro.pdf … 09_Glossary.pdf`: the original split into sections for reading
- How v4 was made from the original (pypdf, no script kept): delete pages 2–8 and 11–27 (front matter
  and the Introduction), giving 290 pages; then insert 14 blank pages after the cover, so PDF page = printed
  book page (TOC on p16–17, Chapter 1 on p18, glossary on p294–303).
- **Not exported, because they're regenerated or local:** `desk/live/` (fetched bars), `desk/levels/`, `desk/state.json`,
  `desk/scan_events.jsonl`, `__pycache__`.

## Loops, routines, sessions

- **Nothing is running.** The 2-minute session cron was deleted, the background `desk_loop.sh` hit its
  2-hour limit and was not restarted, and there are no account routines for this desk.
- The notifier session `session_017k1DRebVjkHZtE1R2kcZZ5` ("LTA Concept Callouts — main") is **archived**.
- To run the scan in the new repo, start `bash desk/desk_loop.sh` in the background. It's silent until exit 10, then you send
  the `CARD` PNGs. A background tool run is capped at 2 hours, so an hourly keepalive is needed. The owner
  asked for no notification spam.

## Pending

- The owner's decision whether to delete the LTA copies from Futures01 (`LTA_Concepts/`, `workspace/paper/LTA/`,
  `.claude/agents/lta-concept-callouts.md`). **Nothing has been deleted.**
- Open question for the owner: add a minimum stop width (the 02:32 MES callout had a 2-point stop sized to 9 contracts).
- COT layer: `desk/cot_inputs.json` needs the owner's weekly reads (cftc.gov is blocked in these containers).
- Section-by-section study with the owner hasn't started. Section I is next (book pp. 18–70).
- Pre-registered tests LTA-H1…H5 (`desk/CHARTER.md` §5) haven't been run.
