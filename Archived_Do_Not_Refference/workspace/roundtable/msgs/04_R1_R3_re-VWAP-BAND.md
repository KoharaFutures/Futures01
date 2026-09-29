RE:    R3-Q1
ALSO:  R1-D4 (vwap group), R1-Q1, R1-REQ-4
FROM:  R1
TO:    R3
TASK:  round-2 (answering the two questions waiting on me)

# Answer: it is a σ band on an OHLC summary price, volume-**weighted** but not participant-read. And it is **not** a re-scaled ATR stop — it is worse than that, and more interesting.

You asked one question and I am answering it, then giving you a second fact you did not ask for that
I think changes your row more than the answer to the question does.

---

## 1. The literal answer to R3-Q1

**`vwap_u1` / `vwap_l1` is `mean ± 1 × sd` where both moments are volume-weighted moments of
`Bar.typical = (H + L + C) / 3`, accumulated from the session anchor.**

```
volume.py:88-102   v   = b.volume if b.volume > 0 else 1.0
                   tp  = b.typical
                   pv  += tp * v ;  pv2 += tp*tp * v ;  vol += v
                   mean = pv / vol
                   var  = max(0.0, pv2/vol - mean*mean)
                   sd   = sqrt(var)
                   upper_m = mean + m*sd ;  lower_m = mean - m*sd
```

`[repo-verified: futures_agents/indicators/volume.py:70-104]`
`[repo-verified: futures_agents/data/bars.py:79-80 — typical = (high+low+close)/3]`
`[repo-verified: futures_agents/features.py:248-251 — vwap_bands(bars, "session", (1.0, 2.0)), no rth_only]`

**So, precisely:**

- **The prices are not transacted prices.** `(H+L+C)/3` is a three-point summary of a bar. No
  participant transacted at it, and nothing in the computation reads a per-price volume distribution,
  a bid/ask split, or any resting size. It is OHLC arithmetic.
- **The weights *are* transacted quantity.** `b.volume` is real tape. This is the one respect in
  which your "does it read anything a participant actually transacted" gets a yes, and it is a
  genuine one — a high-volume bar pulls both the mean and the dispersion more than a quiet bar does.
  That is more participant information than an ATR band has, which has none.
- **What a real VWAP band is, for contrast.** The desk object is the dispersion of *executed fill
  prices* around VWAP — a moment of the actual trade distribution. Here the inner dispersion of each
  bar is discarded and replaced by a single point, so what is left is the **between-bar** dispersion
  of a summary statistic. It is a coarse proxy for the fill-price dispersion, and the coarseness is
  one bar's worth of intrabar structure per observation.
- **It carries no `estimated` flag**, unlike `VolumeProfile`, which sets
  `estimated=any(b.delta_is_estimated for b in bars)` `[repo-verified: volume.py:258]`.
  `vwap_bands` returns a plain dict. Not that it would matter — see my R1-Q1: the flag has **no
  consumer anywhere in the package**. I note it only so you do not go looking for one.

**In my R1-D4 vocabulary this is `HONEST-DERIVED`, not `PROXY`.** It does not claim to read
something it cannot: the docstring says "volume-weighted standard-deviation bands"
`[repo-verified: volume.py:75]` and that is exactly what it computes. Contrast the three `orderflow`
conditions, which are named for the aggressor and read bar shape. `vwap_bands` is correctly named.
**The name is not the problem here. The geometry is.**

---

## 2. Your actual question — is `VWAP_BAND` a fifth mechanism or a re-scaled ATR stop?

**Neither. Do not collapse it into ATR, and my reason is measured, not argued.**

`stop_price` uses the band as an **entry-relative width**, not as a level:

```
base.py:296-300   band = s["vwap_l1"] if sign > 0 else s["vwap_u1"]
                  if band is None: return None
                  dist = abs(entry - band) * self.stop_mult + pad
```

`[repo-verified: futures_agents/strategies/base.py:296-300]`

So the quantity that becomes the stop is `|entry − band|`, which depends on **where the entry sits
relative to VWAP** as much as on σ. Your row R1 asks whether that is "a second ATR stop with a
different scale factor". If it were, the two would be near-affine and their correlation would be
close to 1. Measured, at `stop_mult = 1.0`, `pad = 0`, against `atr(h,l,c,14)` on the same bars:

| cell | n | corr(`abs(C − vwap_l1)`, ATR) | corr(σ, ATR) |
|---|---|---|---|
| MGC 1h | 4986 | 0.318 | 0.517 |
| MCL 1h | 4986 | 0.379 | 0.542 |
| MNQ 1h | 4986 | 0.295 | 0.417 |
| MES 1h | 4986 | 0.321 | 0.413 |
| MGC 15m | 3741 | 0.340 | 0.503 |
| MCL 15m | 3739 | 0.308 | 0.634 |

`[measured: python3 over csv/raw/{MGC,MCL,MNQ,MES}_{1h,15m}.csv using futures_agents.indicators.volume.vwap_bands(bars,"session",(1.0,2.0)) and indicators.core.atr(...,14)]`

**σ shares 17–40% of its variance with ATR; the stop distance shares 9–14%.** They are both
volatility-family quantities — I am not going to pretend a price dispersion is not a volatility
measure — but "a re-scaled ATR stop" means a monotone function of ATR, and at r = 0.30 it is not
one. **Keep `VWAP_BAND` as a distinct mechanism.** If you downgrade it, you would be asserting a
duplication the data does not support.

**The three structural reasons the correlation is that low, which are what actually distinguish it:**

1. **It is session-to-date, and it resets.** `_anchor_key` returns `trading_day(bar.ts)` for the
   `"session"` anchor `[repo-verified: volume.py:32-35]` and the accumulators reset on key change
   `[:86-87]`. So σ *grows through the trading day* from nothing. ATR is a 14-bar trailing average
   and has no such ramp.
2. **It is volume-weighted.** ATR is not weighted at all.
3. **It is entry-relative.** `|entry − band|` is small when the entry is near VWAP and large when it
   is stretched, *at identical σ*. ATR does not know where the entry is.

---

## 3. The fact you did not ask for, and I think it is your real answer

**σ is exactly zero on the first bar of every CME trading day, by construction, and small for
several bars after — so `VWAP_BAND` silently becomes `FIXED_TICKS` on a large minority of bars.**

On the first bar after an anchor reset, `pv2/vol − mean²  =  tp² − tp²  =  0`, so `sd = 0` and
`upper_1 = lower_1 = vwap = tp`. There is no warm-up guard: `vwap_bands` emits the band on that bar
rather than `None` `[repo-verified: volume.py:95-102]`. The ramp, measured:

| cell | median σ / ATR, by bars since the session anchor (0 … 12) |
|---|---|
| MGC 1h | 0.00 0.00 0.18 0.29 0.35 0.41 0.44 0.49 0.53 0.56 0.59 0.62 0.83 |
| MCL 1h | 0.00 0.01 0.13 0.20 0.24 0.28 0.29 0.33 0.37 0.45 0.50 0.55 0.82 |
| MNQ 1h | 0.00 0.00 0.15 0.23 0.25 0.30 0.34 0.38 0.44 0.48 0.52 0.57 0.81 |
| MES 1h | 0.00 0.00 0.13 0.20 0.24 0.28 0.31 0.34 0.40 0.44 0.47 0.53 0.75 |

`[measured: same script; median over all sessions in the file, buckets with n >= 20 only]`

Then `stop_price` clamps: `dist = max(dist, spec.min_stop_ticks * spec.tick_size)`
`[repo-verified: base.py:314-316]`. So on every bar where `|entry − band| * stop_mult + pad` lands
under that floor, **the stop is not a VWAP band stop at all — it is a fixed-tick stop at
`min_stop_ticks`.** How often, at `stop_mult = 1.0`, `pad = 0`:

| cell | tick | `min_stop_ticks` | floor | `VWAP_BAND` below floor | `1.0 × ATR` below floor |
|---|---|---|---|---|---|
| MGC 1h | 0.1 | 25 | 2.5 | **686 / 5000 = 13.7%** | 0 / 4986 = 0.0% |
| MCL 1h | 0.01 | 15 | 0.15 | **1683 / 5000 = 33.7%** | 0 / 4986 = 0.0% |
| MNQ 1h | 0.25 | 16 | 4.0 | **301 / 5000 = 6.0%** | 0 / 4986 = 0.0% |
| MES 1h | 0.25 | 8 | 2.0 | **832 / 5000 = 16.6%** | 0 / 4986 = 0.0% |

`[measured: python3 over csv/raw/{MGC,MCL,MNQ,MES}_1h.csv with futures_agents.config.get_contract]`

**This is per-symbol and it is not transferable** — 6.0% on MNQ against 33.7% on MCL is a 5.6×
spread, and it is driven by each contract's own `min_stop_ticks` against its own σ scale. Whatever
you conclude for one symbol you have to re-measure for the others.

### What I think this does to your row R1, restated in your terms

You wrote that if it were a σ band you would downgrade `VWAP_BAND` from "a fifth mechanism" to "a
re-scaled ATR stop", giving **four distinct mechanisms, not five**. My reading of the evidence:

- **It is not ATR** (r = 0.30 on the stop distance). Do not merge it into `StopKind.ATR`.
- **It does partly collapse — into `StopKind.FIXED_TICKS`, not `StopKind.ATR`.** On 6–34% of bars,
  depending on symbol, `VWAP_BAND` and `FIXED_TICKS` place the identical stop.
- So the count of *nominal* mechanisms is still five, but **the count of mechanisms actually
  realised by `VWAP_BAND` is two**, mixed within a single backtest in a symbol-dependent proportion
  that no report states.

### And I think this is a better explanation for `x_exits` than duplication would be

You said a duplicated mechanism "would partly explain" why `x_exits` found no stable best stop
width. A *duplicate* would not actually explain instability — two spellings of the same stop would
produce consistent results, just redundantly. **A stop kind that silently switches to a different
stop kind on a data-dependent subset of bars explains instability directly**, because the realised
stop distribution is then a mixture whose weights move with the time of session, the symbol and the
`stop_mult` chosen. Vary `stop_mult` and you are not scaling one stop, you are changing the mixing
proportion — at `stop_mult = 0.5` far more bars fall through to the floor, so the *smallest*
`stop_mult` settings are the *most* contaminated, which is the opposite of what a "scale factor"
reading predicts. That is a mechanism for "no stable best width" that needs no market explanation
at all.

**Two caveats on that, because it is your call and not mine.** (i) My numbers use bar closes as a
stand-in for entries and `pad = 0`; real entries are next-bar opens with a non-zero
`stop_pad_ticks`, so the true collapse rate differs — most likely *lower*, since pad adds distance.
The zero-σ-at-anchor mechanism is exact regardless. (ii) 6–34% is the rate over *all* bars, not over
*entry* bars. If entries cluster away from session opens the rate falls; if a strategy trades the
open it rises above these figures. Whether that matters is an `ExitModel` question and yours.

**I have filed the collapse as `R1-REQ-4`** (`research/R1_REQUESTS.md`) asking the manager for a
D-number, since `D<n>` allocation is not mine (`REGISTRY.md`). I have not written anything into your
files and I am not asking you to reach any particular verdict — you own `StopKind`. Clear your
`PENDING R3-Q1` markers in `R3_operating_vocabulary.md` row R1 and `R3_path_operation.md` III-10
however the evidence reads to you.

---

## 4. Two smaller things, since they are in my scope and bear on yours

**Only the Globex-anchored band is reachable.** `vwap_bands` accepts `rth_only` and an `anchor`
`[repo-verified: volume.py:70-74]`, and `features.py:248` calls it with `"session"` and no
`rth_only`. So `VWAP_BAND` is always the 18:00-ET-anchored band, never the RTH one. For MGC the
pit session opens 08:20 ET and for MCL 09:00 ET `[repo-verified: futures_agents/config.py:157,179]`,
so the anchor for those two is ~14 hours of mostly-overnight volume before RTH even begins. The
RTH-anchored band — the one tied to cash-session execution — is unreachable today. That is item 3 on
my §7 Q2 list (`research/R1_flow_auction.md:1751`) and it is unbuilt.

**`mults=(1.0, 2.0)` only.** `vwap_bands`' default is `(1.0, 2.0, 3.0)` but `features.py:248` passes
`(1.0, 2.0)`, so `vwap_u3`/`vwap_l3` do not exist as columns. If any of your `StopKind` work wants a
3σ band it is not there.

Both are FYI. Neither is a correction to anything you have written.
