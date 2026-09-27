# EF2 / Burst 13 — the 240m half of my cell is WITHDRAWN. Recorded, not deleted.

**Ruling (coordinator, 2026-09-27):** the window is 22 h = 1,320 min and
`1320 = 2³·3·5·11`, so **5/15/30/60/120 divide it evenly and 240 gives 5.5**. A four-hour bar cannot
align with a twenty-two-hour window. That is arithmetic, not an implementation limit, and no harness fix
reaches it. **EF2's cell is therefore MGC and MCL at 60m only.**

I am recording every 240m number I measured rather than deleting it, so nobody re-derives it, and
recording precisely which construct is withdrawn.

## What is withdrawn

**`primary_tf = 240` is withdrawn.** Two of my four cells go with it:

| cell | status |
|---|---|
| `f60__p60` — frame (60,), primary 60 | **LIVE** |
| `f60_240__p60` — frame (60,240), primary 60, confirm (240,) | **LIVE** |
| `f240__p240` — frame (240,), primary 240 | **WITHDRAWN** |
| `f60_240__p240` — frame (60,240), primary 240 | **WITHDRAWN** |

**`f60_240__p60` survives and matters.** Its `primary_tf` is 60, its base grid is 60m, and 240m enters
only as a *confirmation* timeframe read out of the snapshot — the position is opened, held and flattened
entirely on the 60m clock, which divides 1,320 exactly 22 times. It is also **the only cell in my whole
assignment where MULTI_TIMEFRAME can be tested at all** (burst 03: its two required SIGNALs are VOID at
the frame's top timeframe, so a 60m-only frame cannot express it either).

## What the 240m work measured, kept for the record

1. **`STRADDLE` bars, the mechanism EF6's divisibility argument predicts.** 586 of 3,052 MGC 240m bars
   and 563 of 2,990 MCL 240m bars — **19.2% and 18.8%** — contain 16:00 or 18:00 strictly inside them.
   At 60m there are **zero** on either symbol (burst 05). The 240m ET grid is 00/04/08/12/16/20: the
   12:00 bar closes exactly at 16:00 and the 16:00 bar spans 16:00→20:00, two forbidden hours then two
   legal ones. **This is the same fact as `1320 % 240 = 220`, measured on the tape.**
2. **The VOID census at 240m, which is the strongest per-timeframe result I have.** 12 of 79 conditions
   VOID on MGC and 10 on MCL, against 3–7 at 60m. All six `profile` conditions VOID at 240m on both
   symbols — the 4 SIGNALs *and* the 2 FILTERs, which is what makes it reach eight strategy groups and
   not just VOLUME_PROFILE. `VOLUME_PROFILE` and `MULTI_TIMEFRAME` both have **zero** surviving arms at
   240m. **48.7% (MGC) and 42.4% (MCL) of 240m candidate arms were structurally incapable of trading**,
   against 8.5–19.6% at 60m.
3. **`session_extreme_sweep` is LIVE at 240m and VOID at 60m** — 1,891 MGC / 1,705 MCL fires, of which
   1,414 / 1,600 inside RTH, against 200 / 107 fires and **zero** inside RTH at 60m. R1's D-L4
   ("structurally dead inside every strategy the combinator can build") is true at 60m under
   `rth_only=True` and false at 240m. EF6 independently measured 1,652–2,134 at 240m. **This is the
   clearest single instance in the corpus of why `VOID` had to be a per-(symbol, timeframe) verdict**,
   and it survives the withdrawal as a finding about the vocabulary even though the cell does not.
4. **The gap-fill tail, which is worst at 240m on MCL.** Median 1.08 R on the tightest ATR stop, 26.8%
   over 2 R, 7.3% over 5 R, max 12.97 R (burst 12). MGC 60m's median is 0.07 R. Four cells, four
   different answers.
5. **D45 stop collapse at 240m:** `VWAP_BAND` → fixed-tick on 12.4% (MGC) and 24.6% (MCL) of bars;
   `STRUCTURE` on 1.7% and 3.7%. Lower than the 60m rates (19.2% / 37.2% and 3.8% / 7.5%), so the 60m
   cell is the more affected one and the withdrawal does not remove the D45 problem.
6. **Flat reachability at 240m:** 9 of 602 MGC cycles and 14 of 596 MCL cycles had no bar the rule could
   act on. EF1's post-fix saturation reports `1b = 9` on MGC 240m — **exact agreement with my count**.

## One fact I am recording without contesting the ruling

EF6's own statement of the divisibility rule is about the **base** grid: *"never make 240m or 1440m the
base of a frame under this rule — use 60m or 120m as the base and read 240m/1440m out of the snapshot. A
row with `primary_tf = 240` on a **240m base** is not a row under this programme's rule."* Every EF2
240m cell used a **60m base** (burst 01, fixed before any of this), and EF1's post-fix saturation run at
240m reports **`viol = 0` under the strict audit with no carve-out**, `over = 0`, and `maxhold = 960m`
against a 1,080m cap.

So on the evidence a 240m *thesis* on a 60m base ran compliantly. What it did **not** do is reach the
window's own ceiling: **16 hours, not 22**, because the flat lands on the `[12:00,16:00)` bucket and the
`[16:00,20:00)` bucket is `IN_WINDOW` and vetoed, so the earliest re-entry is 20:00. **That 16-vs-22
shortfall is exactly the 5.5-windows misalignment expressed in hold time**, and it is a real reason to
drop the cell rather than a technicality: a 240m swing row would be reported under a 22-hour rule while
only ever being able to use 16 of them, and 5.5 bars of runway is not a swing thesis.

**I am not asking for the ruling to be revisited and I have not acted against it.** If the board ever
wants the distinction, the testable form is: *`primary_tf = 240` on a 60m base is window-compliant but
hold-capped at 16 h; `primary_tf = 240` on a 240m base is not compliant at all.* Both halves are
measured above.

## What the withdrawal costs, stated so the loss is visible

- **MULTI_TIMEFRAME is now testable in exactly one cell** (`f60_240__p60`) instead of one of four. It was
  never testable at 240m.
- **VOLUME_PROFILE is now fully testable**, because every cell that killed it was a 240m cell.
- **The "does multi-timeframe alignment improve outcomes" question narrows** from a 4-cell comparison to
  the single paired contrast `f60__p60` vs `f60_240__p60` with the rule set held fixed — which is
  `EF2-HYP-2`, and which is *cleaner* than the 4-cell version because both arms now share a base grid,
  a primary timeframe and a hold ceiling.
- **`EF2-HYP-3` (the two 240m cells differ only by `_default_regime_tf`) is withdrawn with the cells.**
  It was the only clean single-variable test I had of frame composition, and it is gone. Recorded as a
  loss, not quietly dropped.
- **`EF2-HYP-4` (60m vs 240m) is withdrawn.** There is no second timeframe left to compare against.
