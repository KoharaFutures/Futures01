#!/usr/bin/env python3
"""E2_randomwalk.py - is MES 60m a random walk at this timeframe?

AGENT E2, REPLAY desk, closed-market window.

WHAT THIS IS FOR
  Every measurement on this desk returns null: the stand-down counterfactual is
  indistinguishable from arbitrary bars across 36 geometries, detected S/R levels
  are indistinguishable from random price lines, and the mechanised thesis-5
  pattern sits at ~zero expectancy. The untested explanation is that the SERIES
  has no exploitable linear structure at 60 minutes, which would explain every
  null at once. This script tests that directly.

  Four tests on log returns of closes, each run on the real series AND on
  matched synthetic nulls so the reader can see what "no structure" looks like
  at n = 1684:
    1. ACF of returns, lags 1-24, +-1.96/sqrt(n) bands; ACF of |returns| too.
    2. Lo-MacKinlay variance ratio, q = 2,4,8,12,24, heteroskedasticity-ROBUST
       statistic (z2) reported alongside the homoskedastic one (z1).
    3. Runs test on the sign of returns.
    4. Hurst exponent by corrected R/S and by DFA-1.

  THE CONTROL IS THE POINT. A test that cannot separate the real series from a
  simulated random walk of the same length has measured its own power, not the
  market. Two nulls are used:
    - GAUSSIAN RW: iid normal, mean and sd matched to the real returns, seeded.
    - PERMUTATION: the actual return series shuffled. This keeps the real
      marginal distribution exactly (fat tails, tick granularity, the zero
      returns) and destroys only the serial dependence. It is the stricter null
      for the runs and Hurst tests, which are sensitive to the marginal.

  Both nulls are run once at a stated seed for a headline "here is one draw",
  and then REPS times to get empirical null bands for every statistic.

READS ONLY
  visible.jsonl, in R1's own lane, retrospective over bars the cursor has
  already passed. Does not touch data/archive/, csv/, replay.py or state.json.
  Does not run the harness or advance any cursor. Writes nothing but stdout.

CONVENTIONS
  - returns are log returns of CLOSES: r_t = ln(c_t / c_{t-1}), n = 1684.
  - the tape has 23 bars per day, not 24: there is no 17:00 ET bar. The return
    from a 16:00 close to the next 18:00 close therefore spans the 2-hour
    session break. Those ~72 boundary returns are kept in the headline (they
    are returns the desk actually holds through) and a robustness pass reports
    the ACF and VR with them dropped.
  - exact-zero returns exist (tick granularity on a quiet overnight bar). The
    runs test drops them, standard practice, and the count is reported.

TRIAL COUNT: declared in the "TRIALS" block at the end of the run. This script
  reports many statistics and the multiplicity is stated rather than buried.
"""

import functools
import json
import math
import os
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
VISIBLE = os.path.join(HERE, os.pardir, "visible.jsonl")

SEED = 1685            # stated seed, == the visible bar count, no other meaning
REPS = 4000            # replications for the empirical null bands
MAXLAG = 24
QS = (2, 4, 8, 12, 24)
BLOCK_MIN, BLOCK_MAX = 16, 256   # R/S and DFA window range


# ---------------------------------------------------------------- data

def load_closes():
    rows = [json.loads(l) for l in open(VISIBLE)]
    closes = np.array([r["c"] for r in rows], dtype=float)
    hours = np.array([int(r["ts"][11:13]) for r in rows])
    return rows, closes, hours


def logret(closes):
    return np.diff(np.log(closes))


# ---------------------------------------------------------------- 1. ACF

def acf(x, maxlag):
    """Sample autocorrelation, lags 1..maxlag. Denominator is the full-sample
    variance (the standard 1/n biased-but-consistent estimator, which is what
    the +-1.96/sqrt(n) band is derived for)."""
    x = x - x.mean()
    n = len(x)
    denom = np.dot(x, x)
    return np.array([np.dot(x[lag:], x[:-lag]) / denom for lag in range(1, maxlag + 1)])


def ljung_box(r, maxlag):
    """Ljung-Box Q and its chi2(maxlag) p-value - the joint test across lags,
    which is the right way to ask 'any linear structure at all' once."""
    n = len(r)
    a = acf(r, maxlag)
    q = n * (n + 2) * np.sum(a ** 2 / (n - np.arange(1, maxlag + 1)))
    return q, stats.chi2.sf(q, maxlag)


# ---------------------------------------------------------------- 2. variance ratio

def variance_ratio(r, q):
    """Lo-MacKinlay (1988) overlapping variance ratio.

    Returns (VR, z1 homoskedastic, z2 heteroskedasticity-robust).

    sigma_a^2 : unbiased 1-period variance.
    sigma_c^2 : overlapping q-period variance with the Lo-MacKinlay
                m = q(n-q+1)(1 - q/n) denominator.
    z1        : uses psi(q) = 2(2q-1)(q-1)/(3q), valid only under iid+homosk.
    z2        : uses psi*(q) = sum_j (2(q-j)/q)^2 delta_j, valid under
                heteroskedasticity, which financial returns certainly have.
                z2 is the statistic to read; z1 is shown to expose how much
                volatility clustering alone would have inflated it.
    """
    n = len(r)
    mu = r.mean()
    sigma_a = np.sum((r - mu) ** 2) / (n - 1)

    # overlapping q-sums via cumulative sum
    cs = np.concatenate(([0.0], np.cumsum(r)))
    qsums = cs[q:] - cs[:-q]              # length n - q + 1
    m = q * (n - q + 1) * (1.0 - q / n)
    sigma_c = np.sum((qsums - q * mu) ** 2) / m

    vr = sigma_c / sigma_a

    psi_homo = 2.0 * (2 * q - 1) * (q - 1) / (3.0 * q)
    z1 = math.sqrt(n) * (vr - 1.0) / math.sqrt(psi_homo)

    # robust: delta_j
    e = r - mu
    e2 = e ** 2
    s2 = np.sum(e2)
    psi_rob = 0.0
    for j in range(1, q):
        # Lo-MacKinlay delta_j; the leading n is what makes delta_j -> 1 under
        # homoskedastic iid, so that psi*(q) reduces to psi(q). Omitting it
        # deflates psi* by a factor of n and inflates z2 by sqrt(n).
        delta_j = n * np.sum(e2[j:] * e2[:-j]) / (s2 ** 2)
        psi_rob += (2.0 * (q - j) / q) ** 2 * delta_j
    z2 = math.sqrt(n) * (vr - 1.0) / math.sqrt(psi_rob) if psi_rob > 0 else float("nan")

    return vr, z1, z2


# ---------------------------------------------------------------- 3. runs test

def runs_test(r):
    """Wald-Wolfowitz runs test on the sign of returns. Exact-zero returns are
    dropped (they have no sign); the count is returned so it is visible."""
    s = np.sign(r)
    nz = int(np.sum(s == 0))
    s = s[s != 0]
    n1 = int(np.sum(s > 0))
    n2 = int(np.sum(s < 0))
    n = n1 + n2
    runs = 1 + int(np.sum(s[1:] != s[:-1]))
    exp = 2.0 * n1 * n2 / n + 1.0
    var = 2.0 * n1 * n2 * (2.0 * n1 * n2 - n) / (n ** 2 * (n - 1.0))
    z = (runs - exp) / math.sqrt(var)
    return dict(runs=runs, exp=exp, sd=math.sqrt(var), z=z, n1=n1, n2=n2, zeros=nz)


# ---------------------------------------------------------------- 4. Hurst

def _blocks(n, lo, hi):
    """Roughly log-spaced window sizes between lo and hi."""
    out = []
    k = lo
    while k <= min(hi, n // 4):
        out.append(int(k))
        k *= 1.4
    return sorted(set(out))


def hurst_rs(r, lo=BLOCK_MIN, hi=BLOCK_MAX, corrected=True):
    """Hurst by rescaled range, log-log slope of E[R/S] against window size.

    If corrected, each window's log(R/S) has the Anis-Lloyd-Peters expected
    value under independence subtracted before the regression, and 0.5 is added
    back to the slope. UNCORRECTED R/S on a series this short is biased UPWARD:
    the finite-sample E[R/S] under pure independence sits above the sqrt(pi n/2)
    asymptote, so genuinely iid data returns H ~ 0.55-0.60 rather than 0.50.
    The synthetic controls measure that bias directly, which is the only
    trustworthy way to read a short-series Hurst number.
    """
    n = len(r)
    ks = _blocks(n, lo, hi)
    xs, ys = [], []
    for k in ks:
        nb = n // k
        vals = []
        for b in range(nb):
            seg = r[b * k:(b + 1) * k]
            z = np.cumsum(seg - seg.mean())
            rng = z.max() - z.min()
            sd = seg.std(ddof=1)
            if sd > 0 and rng > 0:
                vals.append(rng / sd)
        if not vals:
            continue
        rs = float(np.mean(vals))
        y = math.log(rs)
        if corrected:
            y -= math.log(anis_lloyd(k))
        xs.append(math.log(k))
        ys.append(y)
    slope = np.polyfit(xs, ys, 1)[0]
    return slope + 0.5 if corrected else slope


@functools.lru_cache(maxsize=None)
def anis_lloyd(k):
    """Anis-Lloyd (1976) / Peters expected R/S for an independent series of
    length k - the finite-sample null value the raw statistic must be measured
    against."""
    if k > 340:
        front = 1.0 / math.sqrt(k * math.pi / 2.0)
    else:
        front = math.gamma((k - 1) / 2.0) / (math.sqrt(math.pi) * math.gamma(k / 2.0))
    tail = sum(math.sqrt((k - i) / i) for i in range(1, k))
    return front * tail


def hurst_dfa(r, lo=BLOCK_MIN, hi=BLOCK_MAX):
    """Detrended fluctuation analysis, order 1. Slope of log F(k) on log k;
    for the integrated series this estimates H directly. DFA is less
    finite-sample biased than raw R/S but still noisy at n ~ 1700, and the
    controls quantify that noise."""
    y = np.cumsum(r - r.mean())
    n = len(y)
    ks = _blocks(n, lo, hi)
    xs, ys = [], []
    for k in ks:
        nb = n // k
        if nb < 4:
            continue
        resid2 = []
        t = np.arange(k, dtype=float)
        for b in range(nb):
            seg = y[b * k:(b + 1) * k]
            c = np.polyfit(t, seg, 1)
            resid2.append(np.mean((seg - np.polyval(c, t)) ** 2))
        f = math.sqrt(float(np.mean(resid2)))
        if f > 0:
            xs.append(math.log(k))
            ys.append(math.log(f))
    return np.polyfit(xs, ys, 1)[0]


# ---------------------------------------------------------------- battery

def battery(r):
    """All four tests on one return series -> flat dict of statistics."""
    out = {}
    a = acf(r, MAXLAG)
    aa = acf(np.abs(r), MAXLAG)
    for i in range(MAXLAG):
        out[f"acf{i+1}"] = a[i]
        out[f"aacf{i+1}"] = aa[i]
    out["acf_maxabs"] = float(np.max(np.abs(a)))
    out["aacf_mean1_24"] = float(np.mean(aa))
    q, p = ljung_box(r, MAXLAG)
    out["lb_q"], out["lb_p"] = q, p
    qa, pa = ljung_box(np.abs(r), MAXLAG)
    out["lb_abs_q"], out["lb_abs_p"] = qa, pa
    for q_ in QS:
        vr, z1, z2 = variance_ratio(r, q_)
        out[f"vr{q_}"], out[f"vrz1_{q_}"], out[f"vrz2_{q_}"] = vr, z1, z2
    rt = runs_test(r)
    out["runs"] = rt["runs"]
    out["runs_z"] = rt["z"]
    out["hurst_rs"] = hurst_rs(r, corrected=True)
    out["hurst_rs_raw"] = hurst_rs(r, corrected=False)
    out["hurst_dfa"] = hurst_dfa(r)
    return out


def pct_rank(value, dist):
    """Two-sided empirical p: fraction of null draws at least as extreme as the
    observed value, measured about the null's own median."""
    dist = np.asarray(dist)
    med = np.median(dist)
    return float(np.mean(np.abs(dist - med) >= abs(value - med)))


def band(dist):
    d = np.asarray(dist)
    return np.percentile(d, 2.5), np.median(d), np.percentile(d, 97.5)


# ---------------------------------------------------------------- main

def main():
    rows, closes, hours = load_closes()
    r = logret(closes)
    n = len(r)
    mu, sd = r.mean(), r.std(ddof=1)

    print("=" * 78)
    print("E2 - IS MES 60m A RANDOM WALK? tests on log returns of closes")
    print("=" * 78)
    print(f"bars {len(closes)}  returns n = {n}")
    print(f"first {rows[0]['ts']}   last {rows[-1]['ts']}")
    print(f"mean {mu:+.8f}  sd {sd:.8f}  ({sd*100:.4f}% per 60m bar)")
    print(f"annualised-ish sd (x sqrt(23*252)) = {sd*math.sqrt(23*252)*100:.1f}%")
    print(f"total log drift {np.sum(r):+.5f}  ({closes[0]:.2f} -> {closes[-1]:.2f})")
    print(f"skew {stats.skew(r):+.3f}  excess kurtosis {stats.kurtosis(r):+.3f}")
    print(f"exact-zero returns: {int(np.sum(r == 0))}")
    print(f"mean |return| in points: {np.mean(np.abs(np.diff(closes))):.3f}")
    band_95 = 1.96 / math.sqrt(n)
    print(f"\nACF 95% band +-1.96/sqrt(n) = +-{band_95:.4f}")

    # ---- observed
    obs = battery(r)

    # ---- nulls
    rng = np.random.default_rng(SEED)
    # headline single draws
    gauss_one = rng.normal(mu, sd, n)
    perm_one = rng.permutation(r)
    obs_g1 = battery(gauss_one)
    obs_p1 = battery(perm_one)

    keys = [k for k in obs if isinstance(obs[k], float) or isinstance(obs[k], int)]
    dist_g = {k: [] for k in keys}
    dist_p = {k: [] for k in keys}
    rng2 = np.random.default_rng(SEED + 1)
    for _ in range(REPS):
        bg = battery(rng2.normal(mu, sd, n))
        bp = battery(rng2.permutation(r))
        for k in keys:
            dist_g[k].append(bg[k])
            dist_p[k].append(bp[k])

    # ---------------- 1. ACF
    print("\n" + "=" * 78)
    print("1. AUTOCORRELATION, lags 1-24")
    print("=" * 78)
    print("   'sig' = |rho| exceeds the +-1.96/sqrt(n) band. 'Gnull 95%' is the")
    print(f"   2.5-97.5 pct of the same statistic over {REPS} Gaussian RW draws.")
    print(f"\n{'lag':>4} {'rho(r)':>9} {'sig':>4} {'Gnull 95%':>20} "
          f"{'rho(|r|)':>10} {'sig':>4}")
    n_sig_r = n_sig_a = 0
    for i in range(1, MAXLAG + 1):
        rr, ra = obs[f"acf{i}"], obs[f"aacf{i}"]
        lo, _, hi = band(dist_g[f"acf{i}"])
        s1 = "*" if abs(rr) > band_95 else ""
        s2 = "*" if abs(ra) > band_95 else ""
        n_sig_r += bool(s1)
        n_sig_a += bool(s2)
        print(f"{i:>4} {rr:>+9.4f} {s1:>4} [{lo:>+8.4f},{hi:>+8.4f}] "
              f"{ra:>+10.4f} {s2:>4}")
    print(f"\nreturn-ACF lags outside band: {n_sig_r}/24  "
          f"(expected under null at alpha=.05: 1.2)")
    print(f"abs-ACF    lags outside band: {n_sig_a}/24")
    print(f"max |rho(r)| over 24 lags = {obs['acf_maxabs']:.4f}   "
          f"Gaussian-null 95% max = {band(dist_g['acf_maxabs'])[2]:.4f}  "
          f"emp p = {pct_rank(obs['acf_maxabs'], dist_g['acf_maxabs']):.3f}")
    print(f"mean rho(|r|) lags 1-24   = {obs['aacf_mean1_24']:+.4f}  "
          f"Gaussian-null 95% = [{band(dist_g['aacf_mean1_24'])[0]:+.4f},"
          f"{band(dist_g['aacf_mean1_24'])[2]:+.4f}]  "
          f"emp p = {pct_rank(obs['aacf_mean1_24'], dist_g['aacf_mean1_24']):.4f}")
    print(f"\nLjung-Box Q(24) returns : {obs['lb_q']:8.2f}  p = {obs['lb_p']:.4f}")
    print(f"Ljung-Box Q(24) |return|: {obs['lb_abs_q']:8.2f}  p = {obs['lb_abs_p']:.3e}")
    print(f"  control, one Gaussian draw, returns Q(24) = {obs_g1['lb_q']:.2f} "
          f"p = {obs_g1['lb_p']:.4f};  |r| Q(24) = {obs_g1['lb_abs_q']:.2f} "
          f"p = {obs_g1['lb_abs_p']:.4f}")
    print(f"  control, one permutation, |r| Q(24) = {obs_p1['lb_abs_q']:.2f} "
          f"p = {obs_p1['lb_abs_p']:.4f}")

    # ---------------- 2. VR
    print("\n" + "=" * 78)
    print("2. LO-MacKINLAY VARIANCE RATIO  (z2 = heteroskedasticity-ROBUST,")
    print("   the statistic to read; z1 = homoskedastic, shown for contrast)")
    print("=" * 78)
    print(f"{'q':>4} {'VR':>8} {'z1':>8} {'z2 rob':>8} {'p(z2)':>8} "
          f"{'Gauss-null VR 95%':>24} {'emp p':>7}")
    for q_ in QS:
        vr, z1, z2 = obs[f"vr{q_}"], obs[f"vrz1_{q_}"], obs[f"vrz2_{q_}"]
        lo, med, hi = band(dist_g[f"vr{q_}"])
        p2 = 2 * stats.norm.sf(abs(z2))
        ep = pct_rank(vr, dist_g[f"vr{q_}"])
        print(f"{q_:>4} {vr:>8.4f} {z1:>+8.3f} {z2:>+8.3f} {p2:>8.3f} "
              f"[{lo:>7.4f},{hi:>7.4f}] {ep:>7.3f}")
    print("\n  same table, ONE Gaussian RW draw (seed %d) - what null looks like:" % SEED)
    for q_ in QS:
        print(f"{q_:>4} {obs_g1[f'vr{q_}']:>8.4f} {obs_g1[f'vrz1_{q_}']:>+8.3f} "
              f"{obs_g1[f'vrz2_{q_}']:>+8.3f}")
    print("\n  same table, ONE permutation of the real returns:")
    for q_ in QS:
        print(f"{q_:>4} {obs_p1[f'vr{q_}']:>8.4f} {obs_p1[f'vrz1_{q_}']:>+8.3f} "
              f"{obs_p1[f'vrz2_{q_}']:>+8.3f}")

    # ---------------- 3. runs
    print("\n" + "=" * 78)
    print("3. RUNS TEST on the sign of returns")
    print("=" * 78)
    rt = runs_test(r)
    print(f"up {rt['n1']}  down {rt['n2']}  exact zeros dropped {rt['zeros']}")
    print(f"observed runs {rt['runs']}   expected under independence "
          f"{rt['exp']:.1f}  sd {rt['sd']:.1f}")
    print(f"z = {rt['z']:+.3f}   p = {2*stats.norm.sf(abs(rt['z'])):.3f}")
    lo, med, hi = band(dist_p["runs"])
    print(f"permutation null runs 95% = [{lo:.0f},{hi:.0f}] median {med:.0f}  "
          f"emp p = {pct_rank(rt['runs'], dist_p['runs']):.3f}")
    print(f"control, one Gaussian draw: runs z = {obs_g1['runs_z']:+.3f}")
    print(f"control, one permutation  : runs z = {obs_p1['runs_z']:+.3f}")
    print("  a positive z means MORE runs than independence predicts, i.e. sign")
    print("  alternation / mean reversion; negative means sign persistence.")

    # ---------------- 4. Hurst
    print("\n" + "=" * 78)
    print("4. HURST EXPONENT")
    print("=" * 78)
    for label, key in (("R/S, Anis-Lloyd corrected", "hurst_rs"),
                       ("R/S, UNCORRECTED (biased up)", "hurst_rs_raw"),
                       ("DFA-1", "hurst_dfa")):
        lo, med, hi = band(dist_g[key])
        lop, medp, hip = band(dist_p[key])
        print(f"{label:<30} observed {obs[key]:.4f}")
        print(f"{'':<30} Gaussian-RW null: median {med:.4f} 95% [{lo:.4f},{hi:.4f}]"
              f"  emp p = {pct_rank(obs[key], dist_g[key]):.3f}")
        print(f"{'':<30} permutation null: median {medp:.4f} 95% [{lop:.4f},{hip:.4f}]"
              f"  emp p = {pct_rank(obs[key], dist_p[key]):.3f}")
        print(f"{'':<30} one draw: gauss {obs_g1[key]:.4f}  perm {obs_p1[key]:.4f}")
    print("\n  BIAS DIRECTION: the uncorrected R/S null median above is the whole")
    print("  point - a series KNOWN to be an exact random walk returns H well")
    print("  above 0.50 at this length. Short-series raw R/S is biased UPWARD.")
    print("  Any H > 0.5 here must be read against that median, not against 0.5.")

    # ---------------- 5. power / MDE
    print("\n" + "=" * 78)
    print("5. WHAT THIS SAMPLE COULD HAVE DETECTED (bounding the null)")
    print("=" * 78)
    crit = 1.96 / math.sqrt(n)
    mde80 = (1.96 + 0.8416) / math.sqrt(n)
    mde50 = 1.96 / math.sqrt(n)
    bonf = stats.norm.isf(0.05 / (2 * MAXLAG)) / math.sqrt(n)
    print(f"n = {n}, alpha = 0.05 two-sided, single pre-specified lag:")
    print(f"  significance threshold      |rho| > {crit:.4f}")
    print(f"  min detectable at 50% power |rho| = {mde50:.4f}")
    print(f"  min detectable at 80% power |rho| = {mde80:.4f}")
    print(f"  Bonferroni over 24 lags     |rho| > {bonf:.4f}")
    mean_abs_pts = float(np.mean(np.abs(np.diff(closes))))
    for rho in (crit, mde80):
        edge = rho * mean_abs_pts
        print(f"  an AR(1) with |rho| = {rho:.4f} predicts {rho**2*100:.3f}% of return")
        print(f"    variance; conditional edge ~ {edge:.4f} pts/bar "
              f"(= ${edge*5:.3f}/contract) against a round-turn cost of ~1.04 pts")
        print(f"    (2.69/5.0 commission + 1 tick each way) -> {edge/1.04:.3f}x cost")

    # ---------------- 6. robustness: drop session-break returns
    print("\n" + "=" * 78)
    print("6. ROBUSTNESS - drop returns spanning the session break (no 17:00 bar)")
    print("=" * 78)
    keep = hours[1:] != 18          # return INTO an 18:00 bar spans the break
    r_nb = r[keep]
    print(f"dropped {int(np.sum(~keep))} boundary returns, n = {len(r_nb)}")
    a_nb = acf(r_nb, MAXLAG)
    b_nb = 1.96 / math.sqrt(len(r_nb))
    print(f"lag-1 rho {a_nb[0]:+.4f} (band +-{b_nb:.4f})   "
          f"max|rho| 1-24 {np.max(np.abs(a_nb)):.4f}   "
          f"lags outside band {int(np.sum(np.abs(a_nb) > b_nb))}/24")
    qn, pn = ljung_box(r_nb, MAXLAG)
    print(f"Ljung-Box Q(24) = {qn:.2f} p = {pn:.4f}")
    for q_ in QS:
        vr, z1, z2 = variance_ratio(r_nb, q_)
        print(f"  VR({q_:>2}) = {vr:.4f}  z2 = {z2:+.3f}")

    # ---------------- 7. volatility predictability, quantified
    print("\n" + "=" * 78)
    print("7. VOLATILITY PREDICTABILITY - present, but directionless")
    print("=" * 78)
    ar = np.abs(r)
    sl, ic, rv, pv, se = stats.linregress(ar[:-1], ar[1:])
    print(f"regress |r_t| on |r_(t-1)|: slope {sl:+.4f} (se {se:.4f}) "
          f"R^2 {rv**2:.4f} p {pv:.3e}")
    sl2, ic2, rv2, pv2, se2 = stats.linregress(ar[:-1], r[1:])
    print(f"regress  r_t  on |r_(t-1)|: slope {sl2:+.6f} (se {se2:.6f}) "
          f"R^2 {rv2**2:.6f} p {pv2:.3f}")
    print("  the first says yesterday's move size predicts today's SIZE.")
    print("  the second says it does not predict today's SIGN. Volatility")
    print("  predictability sets stop distance and position size. It does not")
    print("  tell you which way to face, so it cannot rescue a directional edge.")
    sgn = np.sign(r)
    nzm = sgn != 0
    s1 = sgn[:-1][nzm[:-1] & nzm[1:]]
    s2 = sgn[1:][nzm[:-1] & nzm[1:]]
    same = float(np.mean(s1 == s2))
    print(f"\n  P(next bar same sign as this bar) = {same:.4f} on "
          f"{len(s1)} pairs; band +-{1.96*math.sqrt(0.25/len(s1)):.4f} around 0.50")

    # ---------------- trials
    print("\n" + "=" * 78)
    print("TRIALS - my own multiplicity, declared")
    print("=" * 78)
    print(f"  return ACF lags           24")
    print(f"  abs-return ACF lags       24")
    print(f"  Ljung-Box                  2  (returns, |returns|)")
    print(f"  variance ratio             5  q = {QS} (z2 read; z1 reported)")
    print(f"  runs                       1")
    print(f"  Hurst                      3  (R/S corrected, R/S raw, DFA-1)")
    print(f"  robustness pass            6  (lag-1 + LB + 5 VR, break dropped)")
    print(f"  volatility regressions     2")
    print(f"  ---------------------------")
    print(f"  TOTAL                     67 statistics on the real series.")
    print(f"  At alpha = .05 that is ~3.4 expected false positives. Nothing")
    print(f"  below is claimed as a finding unless it clears the empirical null")
    print(f"  band from {REPS} matched draws, which is multiplicity-free by")
    print(f"  construction for the max-|rho| and mean-rho(|r|) summaries.")
    print(f"\n  seed {SEED} (Gaussian draws and permutations), REPS {REPS}")


if __name__ == "__main__":
    main()
