# EF5 burst 03 — `D45` (`StopKind.VWAP_BAND` → `FIXED_TICKS`) re-measured for MES/MNQ at 5m/15m/30m

My dispatch named `D45` as one of four things to check in the census. R1 measured it at **1h only**
and said explicitly that the rate is per-symbol and does not transfer
(`msgs/04_R1_R3_re-VWAP-BAND.md:131-145`). It also does not transfer across timeframes, because the
mechanism is *distance from the session VWAP anchor in bars* and a 5m bar is one twelfth of a 1h bar.
So it had to be re-measured.

## The mechanism, restated exactly

`ExitModel.stop_price` for `VWAP_BAND` is `dist = |entry − band| · stop_mult + pad`
(`base.py:296-300`), then `dist = max(dist, spec.min_stop_ticks · spec.tick_size)`
(`base.py:314-316`). Whenever the first quantity lands under the floor, the realised stop is a
**fixed-tick stop at `min_stop_ticks`** and the row's declared stop mechanism is wrong.

The catalogue offers exactly one VWAP_BAND geometry — `StopKind.VWAP_BAND, stop_mult=1.0,
stop_pad_ticks=3` (`combinator.py:70-72`) — so `stop_mult = 1.0` and `pad = 3 ticks` throughout, and
the threshold is a single number per symbol:

| symbol | tick | `min_stop_ticks` | floor | pad | collapses when `|entry − band|` < |
|---|---|---|---|---|---|
| MES | 0.25 | 8 | 2.00 pt | 0.75 pt | **1.25 pt** |
| MNQ | 0.25 | 16 | 4.00 pt | 0.75 pt | **3.25 pt** |

## Measured

`[measured: EF5/code/d45_vwap_band.py → EF5/out/d45_vwap_band.json; entry approximated by the
signal bar's close, as R1 did; long uses `vwap_l1`, short uses `vwap_u1`, reported as the
direction-neutral mean of the two]`

| cell | `ALL` bars | `SESSION` bars | **`RTH` bars** | `vwap_l1/u1` is None |
|---|---|---|---|---|
| MES 5m | 14.17% | 14.61% | **5.85%** | 0 |
| MES 15m | 14.30% | 14.78% | **6.24%** | 0 |
| MES 30m | 14.76% | 15.22% | **5.82%** | 0 |
| MNQ 5m | 5.12% | 5.31% | **2.22%** | 0 |
| MNQ 15m | 4.95% | 5.10% | **1.83%** | 0 |
| MNQ 30m | 5.10% | 5.28% | **2.25%** | 0 |

## Four things this says

1. **`D45` replicates independently.** R1's 1h all-bar figures were MES **16.6%** and MNQ **6.0%** on
   `csv/raw`; mine are MES 14.2–14.8% and MNQ 4.9–5.1% on `data/archive` at 5m/15m/30m. Same
   magnitude, same 2.8× MES-over-MNQ ordering, different store, different timeframes, independent
   code. The defect is real and it is not a 1-hour artefact.
2. **The rate is roughly flat in timeframe and sharply lower under the `RTH` gate** — 5.8–6.2% (MES)
   and 1.8–2.3% (MNQ) against 14–15% / 5% over all bars. The zero-σ-at-anchor bars are the 18:00 ET
   Globex reopen bars, which `rth_only=True` excludes. So a `rth_only=True` row is *less*
   contaminated than R1's all-bar number implies, and a **`SESSION` (`rth_only=False`) row is MORE**
   contaminated — 14.6% of MES candidate bars. That direction matters for this programme specifically,
   because the session rule is what makes the overnight bars admissible in the first place.
3. **MNQ's `min_stop_ticks = 16` is doing the opposite of what it looks like.** A *larger* minimum
   stop should mean *more* collapses, and MNQ's floor is 4.00 pt against MES's 2.00 pt — yet MNQ
   collapses a third as often, because MNQ's σ scale is ~4× MES's. The two effects nearly cancel and
   the residual favours MNQ. **This is per-symbol and it is why nothing here transfers between them.**
4. **`vwap_l1`/`vwap_u1` is never None in my cell** (0 bars of 11,182 / 3,744 / 1,873, both symbols),
   so the `return None` branch of the VWAP_BAND stop never fires and never silently drops a trade.

## Consequence for the EF5 ranking, stated in advance

Any EF5 row whose exit is `StopKind.VWAP_BAND` carries a **mixed** stop mechanism, in a proportion I
now know: ~6% of MES entry bars and ~2% of MNQ entry bars in the `RTH` arm, ~15% / ~5% in the
`SESSION` arm. I will **carry `stop_kind` and this collapse fraction as columns on every reported
row** rather than describing such a row as a VWAP-band strategy. `VWAP_BAND` is 1 of 12 geometries in
the population, so this affects a bounded and stated slice — but a row that reached the top 10 partly
because ~15% of its stops were quietly a 2-point fixed stop is not the row its label says.
