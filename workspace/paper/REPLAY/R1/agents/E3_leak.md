# E3 — Look-ahead leak audit (dedicated)

Scope: every `why` field in `callouts.jsonl` (45 rows) and every price-bearing line of
`NOTES.md` (1,456 lines), checked against `visible.jsonl` (1,685 bars).
Nothing else was read. No harness run, no cursor advanced.

---

## HEADLINE

**Category-(a) look-ahead breaches found: 0.**

Zero new breaches, and **zero in `callouts.jsonl` at all** — the decision record itself is clean.
The one known breach (`5987.5`) is **not** a look-ahead into an unseen bar: it is a *hindsight
mis-attribution*, and the price was already visible when the sentence was written. Details in §4.
The audit is therefore **clean on the mechanical rule** and **dirty on one narrative attribution**,
which is a materially different (and less severe) finding than the original description suggested.

**`as_of` reconciles for all 45 callouts.** `as_of == visible.jsonl[visible_bars-1].ts` in every
row, and `bar_index == visible_bars - 1` in every row. **Zero harness-level problems.**

---

## 1. Method

1. **Extraction.** Regex `(?<![\d.])(\d{4}(,\d{3})?(\.\d+)?)(?![\d])` over each `why` and each
   NOTES line, keeping values in `[5600, 6300]`. This deliberately admits some non-prices
   (round numbers, dollar figures) and excludes by construction the classes the brief warned
   about: ATR values, z-scores, R multiples, bar counts, volumes, date fragments — all fall
   outside the band. Yield: **429 price mentions in `callouts.jsonl`**, **249 in `NOTES.md`**.
2. **First occurrence.** Built a map `price -> first bar index where it appears as o/h/l/c`.
3. **Two-stage flagging**, because "does not print" is far weaker evidence than "could not be known":
   - **Stage 1 (non-print):** first occurrence is `>= visible_bars`, or the price never appears.
   - **Stage 2 (outside envelope):** the price is above the running max high or below the running
     min low of bars `0 … N-1`. Stage 2 is the *hard* test — a price inside the envelope may simply
     be a tick the tape jumped over or a level quoted to the whole point, whereas a price outside
     the envelope is information the desk provably did not have.
4. **Attribution checks** (independent of 1-3, to catch a leaked claim whose *number* happens to
   print early): grammatically anchored patterns tying a price to a named bar
   (`bar N's high of X`, `bar N closed X`, `bar N rallied to X`, `X at bar N`, …) or a named
   session date (`12/27's low X`, `1/03 closed X`), each verified against that bar's/day's
   actual o/h/l/c, plus a check that the bar index is `< visible_bars`.

### Classification rule (stated explicitly, as asked)

A flagged price is **category (a) — a leak** only if **all three** hold:

- **(i) Grammatical stance is observational.** The price is the object of a verb of observation or
  a named tape feature: *rallied to / fell to / printed / traded / closed / topped at / touched /
  its low / its high / a three-touch shelf / rejected at*. Contrast **category (b)**, where the
  price is the object of a verb of choice or arithmetic: *stop / target / entry / fill / trigger /
  threshold / buffer / say X / 2R target / planned*.
- **(ii) It is a legal MES print.** Tick size is 0.25, so any value ending `.83`, `.86`, `.93`,
  `.13`, `.14`, `.17`, `.64` **cannot** be a tape print and is necessarily computed — automatic (b).
- **(iii) It is not a rounding of a visible value.** A zone quoted to the whole point
  (`5918-5927`, `5736-5754`) is checked against the actual extremes of the bars it describes;
  if it rounds a visible extreme it is not a leak.

A chosen stop or target **need never appear in the tape at all** — that is normal and not a finding.

---

## 2. Results — `callouts.jsonl`

| test | count |
|---|---|
| in-range price mentions | 429 |
| Stage 1 flags (never print / print at-or-after `visible_bars`) | 23 |
| Stage 2 flags (**outside** the visible price envelope) | **2** |
| **category (a) — leaks** | **0** |

### The 2 outside-envelope prices — both category (b)

| callout | `visible_bars` | price | visible range at that bar | stance |
|---|---|---|---|---|
| `R1-00012-b000442` | 442 | 5700 | 5725.25 – 5927.0 | *"SHORT if a bar CLOSES below 5730.0 … **target 5700**"* — chosen target, stated **before** the bars |
| `R1-00018-b000606` | 606 | 6061.0 | 5724.25 – 6053.25 | *"LONG if a bar closes above 6032.5 … **target 6061.0**"* — chosen target, stated before the bars |

Both are forward-looking targets in pre-registered ARMED plans. A target above the highest price
yet seen is what a breakout target *is*. Not leaks.

### How the other 21 Stage-1 flags were disposed of

- **12 are non-tick computed geometry** (`R1-00041`, `R1-00042`, `R1-00043`): 6044.93, 6006.14,
  6037.17, 6026.83, 6057.86, 6049.13, 6041.87, 6063.64. Rule (ii) — none can be a print.
- **6 are chosen stops or targets** on tick boundaries: 5758.0 (`R1-00012`, the `why` itself calls
  it *"a BUFFER rather than a structural level"*), 6019.0 / 5992.0 (`R1-00018`/`R1-00019` coil stop
  and target), 6050.5 (`R1-00026`, *"stop below 6052.0 at say 6050.5"* — the words "say" and
  "stop"), 6110.75 (`R1-00030`, *"short of the 6110.75 **target**"*), 5830.25 (`R1-00038`,
  *"the **2R target** at 5830.25"*).
- **1 is a harness fill price** (`R1-00015`, 5791.75): *"the fill was 5791.75 against bar 453's
  open of 5792.0, so the harness took its tick of slippage."* A fill = open − 1 tick, so it is an
  arithmetic product and need not print.
- **2 are whole-point zone boundaries that round a visible extreme** (rule iii):
  - `R1-00005`, *"the second failed push at **5918**-5927"*. Exact 5918 first prints at bar 713,
    but before bar 202 the two pushes are bar 135 (high **5918.5**) and bars 197/198 (highs
    5919.75 / **5927.0**). 5918 is 5918.5 quoted to the point; both pushes are visible. Not a leak.

## 3. Results — `NOTES.md` prose

Each line was given the **end** bar of its enclosing burst section as its visible limit
(Burst 1→40, 2→402, 3→506, 4→714, 5→924, 6→1190, 7→1393, 8→1563, 9→1563, 10→1618, 11→1635,
12/Corrections→1635, Consolidation→1685). That is the *permissive* limit — prose written mid-burst
gets the benefit of the doubt — so any flag surviving it is robust.

| test | count |
|---|---|
| in-range price mentions | 249 |
| Stage 1 flags | 12 |
| Stage 2 flags (outside envelope) | 1 |
| **category (a) — leaks** | **0** |

- **L64, 5814, outside envelope:** *"a 2R target (**~5814** on an 11-point stop)"* — explicitly a
  computed 2R target, and written with a tilde. Category (b).
- **L35, "chop 5769–5788 through the morning":** bars 13-18 actually ran **5766.75 – 5788.5**.
  5788 rounds 5788.5. Visible. Not a leak.
- **L40, "Bars 23–31 base in 5736–5754":** bars 23-31 actually ran **5736.0 – 5754.75**.
  5754 rounds 5754.75. Visible. Not a leak.
- **The remaining 9** are the same chosen/derived values already dispositioned in §2
  (5791.75 fill ×2, 6110.75 target, 5830.25 2R target, and the non-tick geometry 6037.17,
  6049.13 ×2, 6041.87, 6063.64).

## 4. The known `5987.5` case, re-characterised — and it is not a look-ahead

Established from the tape:

- `5987.5` first prints at **bar 1392** (`2025-01-05T23:00`, close). Also 1563, 1582.
- `5985.75` prints at 544, 802, **1386**, 1389, 1390, 1561.
- The bar-1340 trade is `R1-00033-b001340`: SHORT 5973.25, stop 5985.5, target 5950.0, TARGET, +1.854R.

**The bar-1340 decision itself is clean.** Its `why` never mentions 5987.5 or a shelf. It is built
on `5982.75` (first prints bar **1296**, 12/27 low — correct), bar 1337's high `5983.5` (first
prints bar **1337** — correct), bar 1338/1339 highs `5980.0` (correct), and a *chosen* stop 5985.5
above the rejection high. Every observational number predates the decision. No leak.

**The shelf is real, but it belongs to bar 1442, not bar 1340.** `R1-00035-b001443` builds it
correctly and legitimately: *"1/03 closed 5985.75, 1/05 closed 5987.5, 1/06's low was 5987.25 —
three touches clustered in 1.75 points."* Verified: 1/03 = bars 1370-1386, close **5985.75** ✓;
1/05 = bars 1387-1392, close **5987.5** ✓; 1/06 = bars 1393-1415, low **5987.25** ✓. All three bars
are `< 1443`. Correct, and no leak.

**The error is a transplant, not a leak.** At `R1-00037-b001503` the desk wrote *"my two winners
were at levels with a single decisive rejection: 5801 at bar 452 and a three-touch 5985.75-5987.5
shelf **at bar 1340**"*, repeated at `NOTES.md` L818. By bar 1503 the price 5987.5 **was** visible
(1392 < 1503), so **nothing unseen entered the sentence**. What happened is that the bar-1442
shelf was retroactively attached to the bar-1340 trade, which was at 5982.75. So:

- it is **not** a violation of "at `visible_bars = N`, only bars `0…N-1` were visible";
- it **is** a false precedent, and it was load-bearing: `R1-00037` cites the fabricated
  "two winners at three-touch shelves" pattern as grounds to decline the bar-1502 trigger and
  re-arm at 5868.0. A wrong claim about the past steered a live decision.

Register as **retrospective mis-attribution / self-flattering precedent**, in agent B's 27-error
class. `NOTES.md` L1304-1311 and L1422-1423 already retract it. **Reclassify it out of the
look-ahead category**, because leaving it there implies the harness's visibility guarantee failed,
and it did not.

## 5. Mechanical guarantee — independently verified

- `as_of == visible.jsonl[visible_bars - 1].ts`: **45 / 45**, zero mismatches.
- `bar_index == visible_bars - 1`: **45 / 45**.
- **Forward bar references: 0.** No `why` mentions a bar index `>= its own visible_bars`
  (all 45 rows scanned for `bar NNNN` tokens).
- **Bar/date attributions verified:** 28 tight bar attributions and 6 date attributions in
  callouts, 10 in NOTES. **One arithmetic error, no leak:** `R1-00019-b000614` says
  *"entry bar 608's **open** 6020.75"*; bar 608 is `o 6020.5 h 6020.75 l 6012.0 c 6018.5` — 6020.75
  is that bar's **high**, not its open. Bar 608 was visible (608 < 614), so this is a 0.25-point
  bookkeeping slip that slightly flatters a short entry, not look-ahead. Note it, don't escalate it.

## 6. Limitations, stated so the clean result can be trusted at the right strength

- A leaked price that *coincidentally* printed earlier in the 1,685-bar tape would pass Stage 1.
  The attribution checks in §5 cover this for the 44 claims that name a bar or a date; a bare
  claim like "the high was 5900" with no bar named is not fully decidable by this method.
- Prices written entirely in prose ("the two-thousand handle") are not captured. Spot reading
  found none.
- `journal.jsonl`, `missed.jsonl`, `NO_TRADE.jsonl` and `state.json` were **not** read — outside
  my whitelist. The `as_of` guarantee is verified for `callouts.jsonl` only.

## 7. Bottom line

The desk has a **clean leak audit** on the rule that its value rests on. The visibility guarantee
holds mechanically in all 45 rows, and 678 price mentions across the decision record and the
narrative produced **no price the desk could not have seen**. The one known defect is a narrative
transplant, already self-retracted, and should be re-filed as an attribution error rather than a
look-ahead breach.
