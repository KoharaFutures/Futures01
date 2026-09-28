# E4 - what the 22-hour session rule costs

tape: 1685 bars, 2024-10-06T19:00 .. 2025-01-23T23:00 ET, hourly, labelled by bar START
16:00 ET bars in tape: 72    17:00 bars: 0 (maintenance halt)
geometry: 1.0 ATR stop, 2.0R target, ATR14 at the decision bar, fill next bar's open +/- 0.25, stop wins the tie
population: both directions at every bar f in [15, 1565] at which ALL regimes resolve in-tape
TRIALS: 3102  (1551 bars x 2 directions)   of which ROLLED 72, clean 3030

## short sessions and cycles with no 16:00 bar

dates with bars: 91    16:00 ET bars: 72
dates carrying a day session but NO 16:00 bar -> TRUNCATED SESSIONS: 3
  2024-11-29   4 bars  09:30..12:30 ET
  2024-12-24   4 bars  09:30..12:30 ET
  2025-01-09  16 bars  00:00..23:00 ET
dates holding only evening bars (18:00-23:00) - the opening leg of the next
cycle, nothing missing: 16 (Sundays and the Friday-evening-free
weekday pattern of this tape)

These are abbreviated sessions: 2024-11-29 (day after Thanksgiving) and
2024-12-24 (Christmas Eve) run on a 30-minute-offset grid 09:30..12:30 and stop
at the 13:00 ET early close; 2025-01-09 (Carter day of mourning) stops at 09:00
ET and reopens at 18:00. Dates entirely absent from the tape (2024-11-28,
2024-12-25, 2025-01-20) are full holidays and form no cycle at all.

HANDLING. A cycle with no 16:00 bar has nothing to flatten at. Following the
desk's existing session_end() convention the flat rolls to the NEXT 16:00, so
the position is held well past 22 hours. Those trials are tagged ROLLED, and
every number below is given both ways. ROLLED trials: 72 of 3102 (2.3%), from these flat bars:
  flat bar 905 2024-12-02T16:00  n= 20  hold to flat up to 118h
  flat bar 1277 2024-12-26T16:00  n= 20  hold to flat up to 70h
  flat bar 1494 2025-01-10T16:00  n= 32  hold to flat up to 46h

## regimes - ALL TRIALS (rolled included)

regime                                  n    meanR     sd    win%  TIME n   TIME%  meanR|TIME
------------------------------------------------------------------------------------------
A  FLAT16 (owner's rule)             3102  -0.0099   1.33  35.3%     369  11.9%     +0.2424
B  HOLD, no time exit, cap 48 bars   3102  -0.0068   1.41  33.1%       0   0.0%           -
B  HOLD, no time exit, cap 120 bars  3102  -0.0068   1.41  33.1%       0   0.0%           -
C  FLAT16x2 (one extra cycle)        3102  -0.0063   1.41  33.1%       3   0.1%     -0.5547

## regimes - CLEAN ONLY (rolled excluded)

regime                                  n    meanR     sd    win%  TIME n   TIME%  meanR|TIME
------------------------------------------------------------------------------------------
A  FLAT16 (owner's rule)             3030  -0.0200   1.33  35.0%     369  12.2%     +0.2424
B  HOLD, no time exit, cap 48 bars   3030  -0.0168   1.41  32.8%       0   0.0%           -
B  HOLD, no time exit, cap 120 bars  3030  -0.0168   1.41  32.8%       0   0.0%           -
C  FLAT16x2 (one extra cycle)        3030  -0.0164   1.41  32.8%       3   0.1%     -0.5547

## HEADLINE - the paired price of the forced flat

Positive d = the forced flat EARNS that much R per trade versus the
alternative; negative d = it COSTS that much. Same trials, same fills, so the
difference is paired. z(trial) is the naive per-trial z and is OPTIMISTIC
(overlapping windows, two directions per bar). z(sess) clusters on the flat
bar, z(week) on the ISO week - quote z(week).

all trials:
  comparison                       n  d R/trade  z(trial)  z(sess)  z(week)
  ----------------------------------------------------------------------------
  FLAT16 vs HOLD cap 48         3102    -0.0031     -0.37    -0.25    -0.48   (clusters 68/15)
  FLAT16 vs HOLD cap 120        3102    -0.0031     -0.37    -0.25    -0.48   (clusters 68/15)
  FLAT16 vs FLAT16x2            3102    -0.0035     -0.42    -0.30    -0.53   (clusters 68/15)

clean only:
  comparison                       n  d R/trade  z(trial)  z(sess)  z(week)
  ----------------------------------------------------------------------------
  FLAT16 vs HOLD cap 48         3030    -0.0032     -0.37    -0.36    -0.47   (clusters 68/15)
  FLAT16 vs HOLD cap 120        3030    -0.0032     -0.37    -0.36    -0.47   (clusters 68/15)
  FLAT16 vs FLAT16x2            3030    -0.0036     -0.42    -0.41    -0.52   (clusters 68/15)

two-sample Welch z as well, for comparability with the desk's other reports
(missed.py uses the unpaired form) - clean trials:
  A vs B48    Welch z -0.09
  A vs B120   Welch z -0.09
  A vs C      Welch z -0.10

### the bound, which is the useful part of a null

Week-clustered 95% intervals on the paired difference (clean trials). A null
is only worth anything if it comes with what it excludes:
  FLAT16 vs HOLD cap 48  d -0.0032R   95% CI [-0.0221, +0.0158]R per trade
  FLAT16 vs HOLD cap 120 d -0.0032R   95% CI [-0.0221, +0.0158]R per trade
  FLAT16 vs FLAT16x2     d -0.0036R   95% CI [-0.0223, +0.0151]R per trade

So on this tape the rule is worth somewhere between 0.016R SAVED and
0.022R SPENT per trade. At any trade rate this desk will ever run
that is not a number anyone can feel, and the interval is tight enough to rule
out the rule quietly bleeding tenths of an R, which was the thing worth
checking.

## where the difference comes from

all trials: regime A exits by TIME on 369/3102 = 11.9% of trials, mean +0.2424R.
   those same trials under B48  : mean +0.2683R  (STOP 213, TARGET 156)   -> lift +0.0259R on 11.9% of trials = +0.0031R/trade
   those same trials under B120 : mean +0.2683R  (STOP 213, TARGET 156)   -> lift +0.0259R on 11.9% of trials = +0.0031R/trade
   those same trials under C    : mean +0.2719R  (STOP 210, TARGET 156, TIME 3)   -> lift +0.0295R on 11.9% of trials = +0.0035R/trade

clean only: regime A exits by TIME on 369/3030 = 12.2% of trials, mean +0.2424R.
   those same trials under B48  : mean +0.2683R  (STOP 213, TARGET 156)   -> lift +0.0259R on 12.2% of trials = +0.0032R/trade
   those same trials under B120 : mean +0.2683R  (STOP 213, TARGET 156)   -> lift +0.0259R on 12.2% of trials = +0.0032R/trade
   those same trials under C    : mean +0.2719R  (STOP 210, TARGET 156, TIME 3)   -> lift +0.0295R on 12.2% of trials = +0.0036R/trade

Trials that already resolve by stop or target before the flat are IDENTICAL in
all regimes by construction, so the whole of any difference lives in the
TIME-exited slice. The per-trade figure is the lift on that slice times its
share - which is the arithmetic printed above, and it reconciles with the
headline table.

THE MAXIMUM HORIZON IS NOT BINDING. Every clean trial resolves by stop or
target well inside 48 bars: longest resolution 39 bars, mean 6.6 bars.
So B48 and B120 are the same experiment on this tape and give identical
numbers; the 120-bar arm is reported only to show the cap is slack. 'No time
exit' is therefore a genuine hold-to-resolution, not a second time exit in
disguise.

### was the flat cutting winners short, or losers loose?

Split regime A's TIME exits by whether the trade was in profit at the flat.
This is the shape the owner would feel: a rule that scratches winners is a
different complaint from one that rescues losers.

at the flat                n   A meanR  B120 meanR     lift  z(week)  resolution under B120
----------------------------------------------------------------------------------------------
in profit (R > 0)        224   +0.6070     +0.7143  +0.1073    -0.67  STOP 96, TARGET 128
under water (R <= 0)     145   -0.3208     -0.4207  -0.0998     0.25  STOP 117, TARGET 28

### sanity check: did truncating the population at f_max bias regime A?

regime A over EVERY bar with a 16:00 ahead (no B/C resolvability filter):
  n=3328  mean -0.0026R  vs the common population's -0.0099R  (Welch z +0.22)
  the common population drops the last 119 bars of the tape (113 bars, 6.8% of trials).
  The truncated and full populations agree; the common-population requirement
  costs coverage, not comparability.

## RUNWAY AT ENTRY - the deliverable

runway = bars available to the trade, counted from the FILL bar through the
flat bar inclusive. A fill landing on the 16:00 bar itself has runway 1: it is
filled at that bar's open and flattened at that bar's close. The decision bar
is f-1, so an agent standing at the decision bar sees runway+1 bars ahead.
Rolled trials have no meaningful runway and are excluded from this section.

runway        n |  A meanR  A win%  TIMEn   TIME%  A R|TIME | B120 meanR |  d=A-B120  z(sess)  z(week)
-------------------------------------------------------------------------------------------------------
1-2         268 |  -0.0336  46.3%    212  79.1%   +0.1227 |    -0.0485 |   +0.0149     0.24    -0.03
3-6         536 |  -0.0166  38.4%    127  23.7%   +0.4813 |    +0.0019 |   -0.0184    -0.84    -0.70
7-12        794 |  -0.0249  32.6%      5   0.6%   +0.8456 |    -0.0252 |   +0.0003     0.10     0.36
13+        1432 |  -0.0160  33.0%     25   1.7%   -0.0768 |    -0.0133 |   -0.0027    -0.45    -0.54

Note the TIME% column, which is the mechanical content of the rule: the forced
flat only BINDS on trades that have not already resolved. It binds on most
short-runway trades and on almost none with real runway, so the rule's whole
footprint is concentrated in the 1-6 bar band - and the R|TIME cells for the
7-12 and 13+ buckets rest on the handful of trials in the TIMEn column and
should not be read as estimates of anything.

same buckets, regime C (one extra cycle) and B48:
runway        n   C meanR     d=A-C  z(week)    B48 meanR   d=A-B48  z(week)
--------------------------------------------------------------------------------
1-2         268   -0.0452   +0.0117    -0.07      -0.0485   +0.0149    -0.03
3-6         536   +0.0027   -0.0193    -0.73      +0.0019   -0.0184    -0.70
7-12        794   -0.0252   +0.0003     0.36      -0.0252   +0.0003     0.36
13+        1432   -0.0133   -0.0027    -0.54      -0.0133   -0.0027    -0.54

### does runway itself predict anything? (the desk's real question)

The desk has declined trades for 'not enough runway'. That is a claim about
regime A's own returns: short-runway entries should do WORSE under the owner's
rule than long-runway ones. Each bucket against all the other buckets, same
regime, unpaired (different trials), Welch z:

runway        n   A meanR  rest meanR  Welch z    B120 meanR      rest  Welch z
------------------------------------------------------------------------------------
1-2         268   -0.0336     -0.0187    -0.30       -0.0485   -0.0138    -0.39
3-6         536   -0.0166     -0.0207     0.07       +0.0019   -0.0209     0.34
7-12        794   -0.0249     -0.0182    -0.12       -0.0252   -0.0139    -0.19
13+        1432   -0.0160     -0.0236     0.16       -0.0133   -0.0200     0.13

per-runway-bar detail under the owner's rule (regime A), clean trials:
 runway     n   A meanR    win%   TIME%  B120 meanR
----------------------------------------------------
      1   134   -0.0544  46.3%  94.0%     +0.0075
      2   134   -0.0127  46.3%  64.2%     -0.1045
      3   134   -0.0681  40.3%  41.8%     +0.0075
      4   134   +0.0170  41.0%  31.3%     +0.0075
      5   134   -0.0251  37.3%  14.9%     -0.0373
      6   134   +0.0100  35.1%   6.7%     +0.0299
      7   134   -0.0245  32.8%   0.7%     -0.0373
      8   132   +0.0909  36.4%   0.0%     +0.0909
      9   132   -0.0238  32.6%   1.5%     -0.0227
     10   132   -0.0515  31.8%   0.8%     -0.0455
     11   132   -0.0455  31.8%   0.0%     -0.0455
     12   132   -0.0951  30.3%   0.8%     -0.0909
     13   132   -0.0083  33.3%   1.5%     +0.0000
     14   132   +0.0572  35.6%   0.8%     +0.0682
     15   132   +0.0502  34.8%   0.8%     +0.0455
     16   132   +0.0377  34.8%   0.8%     +0.0455
     17   132   +0.0604  35.6%   1.5%     +0.0682
     18   128   +0.0020  33.6%   1.6%     +0.0078
     19   128   -0.0446  32.0%   1.6%     -0.0391
     20   128   -0.0842  30.5%   3.1%     -0.0859
     21   128   -0.0856  30.5%   3.9%     -0.0859
     22   130   -0.1486  28.5%   3.1%     -0.1462
     23   130   -0.0188  33.1%   0.8%     -0.0308

## sensitivities

WHICH MINUTE THE FLAT LANDS ON. The bar whose ts hour is '16' spans
16:00-17:00 ET, so flattening at that bar's CLOSE is an exit at 17:00 ET.
Re-running regime A exiting at that bar's OPEN instead - flat at 16:00 ET on
the nose - gives mean -0.0199R vs -0.0200R: paired d +0.0001R, paired z +0.03.
The last hour of the cycle is worth that much and no more, so the ambiguity in
what 'flat at 16:00' means does not move the headline either way.

LONG   only: A -0.0525R  B120 -0.0515R  d -0.0010R  z(week) -0.15
SHORT  only: A +0.0125R  B120 +0.0178R  d -0.0053R  z(week) -0.27

first half of tape  : n=1515  A +0.0086R  d(A-B120) +0.0026R  z(week) +0.38
second half         : n=1515  A -0.0486R  d(A-B120) -0.0090R  z(week) -0.46

unresolved at the cap (regime B still open at H bars, clean trials):
  H=48      0/3030 = 0.00% still open, (none)
  H=120     0/3030 = 0.00% still open, (none)

## what this does NOT say

1. The population is EVERY bar in both directions. Its base rate is about
   -0.020R - a no-edge population, as it must be
   for arbitrary entries with a symmetric bracket. This prices the flat on
   ARBITRARY entries. It does not price the flat on a strategy whose edge is
   specifically multi-day follow-through; such a strategy would have to be
   shown to exist first, and no arm on this desk has shown one.
2. Regime B holds through maintenance halts and weekends with no gap-risk
   charge beyond the modelled stop, and a gap through the stop books exactly
   -1.0R here. That flatters holding. The measured cost of the flat is
   therefore an UPPER bound on what releasing the rule would earn.
3. One tape, 91 session dates, ~3.5 months, one instrument. Fifteen ISO weeks
   is fifteen clusters; that is what the conservative z is built on.
4. The rule has purposes this cannot measure: overnight headline risk, margin,
   and the operator being asleep. A finding that it costs nothing in R is an
   argument for KEEPING it, since its non-R benefits then come free.

## bottom line

THE FORCED FLAT COSTS 0.0032R PER TRADE  (week-clustered z -0.47, n=3030 trials).
95% interval: anywhere from 0.0158R SAVED to 0.0221R
SPENT per trade. Indistinguishable from zero, and bounded well inside a
fortieth of an R either way.

It binds on 12% of trades - the other 88% resolve at stop or target
before 16:00 and are byte-identical under every regime. Where it does bind it
scratches winners (0.107R forgone on 224 of 3030 trials)
and rescues losers (0.100R saved on 145 of 3030), and
those two very nearly cancel. Allowing one extra cycle (regime C) changes
nothing either: the flat almost never binds twice.

Runway at entry does NOT predict returns. Every bucket sits within 0.02R of
the rest of the population under the owner's rule (|Welch z| <= 0.30), and the
paired cost of the flat is flat across buckets too (|z(week)| <= 0.70). The
desk's 'not enough runway' refusals are not supported by the tape: a two-bar
entry is not a measurably worse instrument than a twenty-bar entry. What
runway does change is MECHANICS, not expectancy - with 1-2 bars the flat
decides 79% of outcomes and with 7+ bars it decides under 2% - so a
short-runway trade is mostly a bet on the flat print rather than on the
bracket. If the desk wants to keep declining them, the honest reason is that
the bracket is not the thing being tested, not that the expectancy is worse.

