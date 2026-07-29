"""P-22: the decision arithmetic the three primary endpoints need pinned."""
from math import comb
N = 21  # sealed games = pairing units

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

print("C. U3 RATE -- Clopper-Pearson 95% CI for x of 21 (one-sample, no comparator)")
try:
    from scipy.stats import beta
    def cp(x, n=N, a=0.05):
        lo = 0.0 if x == 0 else beta.ppf(a/2, x, n-x+1)
        hi = 1.0 if x == n else beta.ppf(1-a/2, x+1, n-x)
        return lo, hi
    for x in (0, 5, 8, 11, 14, 17, 21):
        lo, hi = cp(x)
        print(f"   {x:2d}/21 = {x/N:.3f}   95% CI [{lo:.3f}, {hi:.3f}]")
except ImportError:
    print("   scipy unavailable")
print("   => 11/21 (a bare majority) has CI lower bound ~0.32 -- it does NOT")
print("      exclude 'fewer than half'.  A floor of 11 is the weakest defensible")
print("      reading of C1's word 稳定; 14/21 is the first x whose CI lower bound")
print("      clears 0.45.\n")

print("D. WHAT n DOES AND DOES NOT BUY")
print("   pairs available for the test = 21, for every n.  n adds no df.")
print("   within-cell SE shrinks by 1/sqrt(n): n=2 -> 0.707x.")
print("   n=2 doubles cost for a 29% SE reduction on the CONTINUOUS endpoint only;")
print("   on the two rate endpoints it converts Bernoulli -> 3-level ordinal.")
print("   The real argument for n=2 is episode mortality, not variance (see")
print("   envelope_stats.py section 6: 47/48 infrastructure-terminated).")
