"""P-22: the decision arithmetic the three primary endpoints need pinned.

`N` was `21` -- the sealed pile -- until 2026-07-29.  That is the wrong
denominator for a confirmatory statistic: F-11 quarantined two games after
INC-BA-001, so a held-out claim may name **19**, and `claim_set.json`'s own
rule requires every one of those statistics to be reported a second time over
the **12** games with no disclosed exposure, with the weaker result governing.

The count is now read from `freeze/tiers.py`, which reads the claim set, so
this script cannot drift away from the roster the way the hand-written manifest
drifted away from the tree.
"""
import os
import sys
from math import comb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
from tiers import tiers as _tiers  # noqa: E402

_T = _tiers()
N = _T["claim"]["n"]            # 19 -- the primary denominator
N_CLEAN = _T["clean"]["n"]      # 12 -- the sensitivity tier, and it governs
N_SEALED = _T["sealed"]["n"]    # 21 -- descriptive only

def sign_p(k):            # exact two-sided sign test, k discordant all one way
    return 2 * 0.5 ** k

print("A. SIGN TEST -- discordant pairs needed, unadjusted vs Bonferroni(3)")
print(f"{'k':>3} {'two-sided p':>12}  {'<0.05':>6} {'<0.0167':>8}")
for k in range(4, 10):
    p = sign_p(k)
    print(f"{k:3d} {p:12.5f}  {'YES' if p<0.05 else '.':>6} {'YES' if p<0.05/3 else '.':>8}")
print("=> unadjusted needs k>=6; Bonferroni/Holm at family alpha=0.05 needs k>=7.")
print("   Multiplicity control costs exactly ONE sealed game.  Cheap; take it.\n")

print("B. WILCOXON SIGNED-RANK -- floor on achievable p (all differences same sign)")
print("   min two-sided p with m nonzero pairs = 2 / 2^m")
for m in (5, 6, 7, 10, 21):
    print(f"   m={m:2d}: {2/2**m:.3e}")
print("   => with 21 untied pairs Wilcoxon is not resolution-limited; the sign")
print("      test is.  Use Wilcoxon as primary, sign test as the tie-robust backup.\n")

print("C. U3 RATE -- Clopper-Pearson 95% CI, reported over BOTH tiers")
print(f"   primary tier n={N} (claim set); sensitivity tier n={N_CLEAN} (clean).")
print(f"   n={N_SEALED} (whole sealed pile) is descriptive only and carries no claim.")
try:
    from scipy.stats import beta
    def cp(x, n=N, a=0.05):
        lo = 0.0 if x == 0 else beta.ppf(a/2, x, n-x+1)
        hi = 1.0 if x == n else beta.ppf(1-a/2, x+1, n-x)
        return lo, hi
    def first_x_clearing(floor, n):
        for x in range(0, n + 1):
            if cp(x, n)[0] >= floor:
                return x
        return None

    # The x values were hardcoded to the old denominator.  After the 19/12
    # correction this loop printed `21/21 = 1.105` -- a rate above one, which
    # is what a stale constant looks like when it fails loudly instead of
    # quietly.  Derived from n now, and so are the floors below: the previous
    # version asserted "11 is the weakest defensible floor, 14 clears 0.45" in
    # a print statement, which is a result copied into prose next to the code
    # that computes it.
    for tier_name, n in (("claim", N), ("clean", N_CLEAN)):
        print(f"   tier={tier_name} (n={n})")
        for x in sorted({0, n // 4, n // 2, (n * 2) // 3, (n * 3) // 4, n}):
            lo, hi = cp(x, n)
            print(f"     {x:2d}/{n:<2d} = {x/n:.3f}   95% CI [{lo:.3f}, {hi:.3f}]")
        bare = (n // 2) + 1
        lo_bare, _ = cp(bare, n)
        x45 = first_x_clearing(0.45, n)
        print(f"     => bare majority {bare}/{n} has CI lower bound {lo_bare:.2f};"
              f" it does NOT exclude 'fewer than half'.")
        print(f"        weakest defensible floor for C1's word 'stable' = {bare}/{n};"
              f" first x clearing 0.45 = {x45}/{n}.")
    print("   Both tiers are reported; where they disagree the weaker governs.\n")
except ImportError:
    print("   scipy unavailable\n")

print("D. WHAT n DOES AND DOES NOT BUY")
print(f"   pairs available for the test = {N}, for every n.  n adds no df.")
print("   within-cell SE shrinks by 1/sqrt(n): n=2 -> 0.707x.")
print("   n=2 doubles cost for a 29% SE reduction on the CONTINUOUS endpoint only;")
print("   on the two rate endpoints it converts Bernoulli -> 3-level ordinal.")
print("   The real argument for n=2 is episode mortality, not variance (see")
print("   envelope_stats.py section 6: 47/48 infrastructure-terminated).")
