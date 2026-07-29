"""A8 -- the false-positive rate of the token check under a null, by group size.

MIN_LABELLED was widened from `0.6 * n_items` to 4, so a derived label set can
now cover as few as 4 items and `_metadata_hits_within` scores any kind-group of
4 or more.  At n=4 and n=5 a *random* token -- one carrying no information at
all -- fires the check surprisingly often, because `rate` is quantised to k/n
and `tolerance = 0.90` forces rate == 1.0, which small n reaches by accident.

Null model: answers assigned at random from a two-symbol alphabet; a single
token carried by a uniformly random non-empty proper subset of the items.  No
relationship whatsoever between the two.  Count how often `_token_hits_within`
reports a hit.
"""
import itertools
import os
import sys
from collections import Counter
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))

TOL = 0.90


def fires(answers, holders):
    """Exact replica of the accept condition in _token_hits_within."""
    n = len(answers)
    if len(holders) < 2 or len(holders) == n:
        return False
    floor = Counter(answers).most_common(1)[0][1] / n
    w = Counter(answers[i] for i in holders)
    wo = Counter(answers[i] for i in range(n) if i not in holders)
    rate = (w.most_common(1)[0][1] + wo.most_common(1)[0][1]) / n
    return rate > TOL and rate > floor + 1e-9


print("Exhaustive enumeration over ALL answer vectors x ALL token subsets")
print("(two-symbol alphabet, both symbols present -- the check needs that):")
print()
print("  n   subsets_scored   fired   P(false positive | random token)")
for n in range(4, 11):
    tot = fired = 0
    for bits in itertools.product("ab", repeat=n):
        if len(set(bits)) < 2:
            continue
        for k in range(2, n):
            for holders in itertools.combinations(range(n), k):
                tot += 1
                if fires(list(bits), set(holders)):
                    fired += 1
    print("  %-3d %-16d %-7d %.4f" % (n, tot, fired, fired / tot))

print()
print("Same, conditioned on a balanced-ish answer vector (the realistic case):")
print("  n   split   subsets   fired   P")
for n, a in ((4, 2), (5, 3), (6, 3), (8, 4), (8, 6), (12, 6)):
    answers = ["a"] * a + ["b"] * (n - a)
    tot = fired = 0
    for k in range(2, n):
        for holders in itertools.combinations(range(n), k):
            tot += 1
            if fires(answers, set(holders)):
                fired += 1
    print("  %-3d %-7s %-9d %-7d %.4f" % (n, "%d/%d" % (a, n - a), tot, fired,
                                          fired / tot))

print()
print("Interpretation: a `tags` field carrying t independent tokens gets t")
print("independent chances.  At n=4, 2/2, TWO of the six possible 2-item")
print("tokens fire -- 1 in 3 for 2-item tokens, 1 in 5 over all scored subsets.")
print("The real papers' smallest scored groups (see a2): v11 `why` n=5,")
print("v11 `plan_len` n=6, p15-adaptation `label`/`verdict` n=6.")
