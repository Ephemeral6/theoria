"""Small non-parametric statistics, hand-rolled for determinism.

Everything here is exact rational or simple float arithmetic on tiny samples,
so it produces the same bits on every machine. That matters more than the
convenience of scipy: the battery's artefacts have to be byte-reproducible, and
a BLAS-backed routine is not a promise anyone can keep across platforms.

Non-parametric throughout, on purpose. With four games per arm there is no
distributional assumption anyone could defend, and `Theoria.md` Phase 4 already
fixes the confirmatory tests as the sign test and Wilcoxon.
"""

from __future__ import annotations

from math import comb
from typing import Dict, List, Optional, Sequence, Tuple


def ranks(xs: Sequence[float]) -> List[float]:
    """Ranks with averaged ties."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    out = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        average = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = average
        i = j + 1
    return out


def pearson(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 0 or syy <= 0:
        return None          # a constant series correlates with nothing
    return sxy / (sxx * syy) ** 0.5


def spearman(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    if len(xs) < 3:
        return None
    return pearson(ranks(xs), ranks(ys))


def cliffs_delta(highs: Sequence[float],
                 lows: Sequence[float]) -> Optional[float]:
    """P(high > low) - P(high < low), in [-1, 1].

    Chosen over Cohen's d because it assumes nothing about the distribution and
    is meaningful at n=4, where a standard deviation is barely an opinion.
    """
    if not highs or not lows:
        return None
    greater = sum(1 for h in highs for l in lows if h > l)
    lesser = sum(1 for h in highs for l in lows if h < l)
    return (greater - lesser) / (len(highs) * len(lows))


def magnitude(delta: Optional[float]) -> str:
    """Romano et al.'s thresholds, the usual reading of Cliff's delta."""
    if delta is None:
        return "none"
    a = abs(delta)
    if a < 0.147:
        return "negligible"
    if a < 0.33:
        return "small"
    if a < 0.474:
        return "medium"
    return "large"


def mann_whitney(a: Sequence[float], b: Sequence[float]) -> Dict[str, object]:
    """Exact two-sided Mann-Whitney U over two *unpaired* groups.

    The sign test cannot be used for the arm contrast: `bare_cc` plays ARC
    games and the offline Theoria arms play self-built worlds, so there is no
    game to pair on.  This is the unpaired substitute, and it is exact rather
    than normal-approximated because the samples here are tiny (n=2 on the
    Theoria side) and a normal approximation at n=2 is a decoration.

    Exactness is by dynamic programming over the rank-sum distribution: the
    number of ways to choose `len(a)` ranks out of `n` summing to each value.
    Integer arithmetic throughout, so the p-value is byte-identical everywhere.

    `min_attainable_p` is reported for the same reason `sign_test` reports it —
    with 2 against 17 the smallest attainable two-sided p is 0.0117, and with
    2 against 2 it is 0.667, which no amount of separation can improve on.

    **Ties are counted, not corrected for.**  The exact null distribution below
    assumes distinct values; with ties the p-value is conservative in an
    unquantified direction, so `ties` is returned and a caller with ties should
    read the effect size instead.
    """
    n1, n2 = len(a), len(b)
    if n1 == 0 or n2 == 0:
        return {"n1": n1, "n2": n2, "u": None, "p_value": None,
                "min_attainable_p": None, "ties": 0}

    greater = sum(1 for x in a for y in b if x > y)
    lesser = sum(1 for x in a for y in b if x < y)
    ties = n1 * n2 - greater - lesser
    # U with the usual half-credit for ties, kept as a float only at the end.
    u = greater + ties / 2.0

    total = n1 + n2
    # counts[k][s] = ways to pick k of the first i ranks summing to s.
    # Rank sums for a group of n1 range over [n1(n1+1)/2, n1(2*total-n1+1)/2].
    max_sum = n1 * (2 * total - n1 + 1) // 2
    counts = [[0] * (max_sum + 1) for _ in range(n1 + 1)]
    counts[0][0] = 1
    for rank in range(1, total + 1):
        for k in range(min(rank, n1), 0, -1):
            row, prev = counts[k], counts[k - 1]
            for s in range(max_sum, rank - 1, -1):
                if prev[s - rank]:
                    row[s] += prev[s - rank]

    ways = comb(total, n1)
    min_rank_sum = n1 * (n1 + 1) // 2
    # U = rank_sum(a) - min_rank_sum, so the null over U is the null over
    # rank sums, shifted.
    dist = counts[n1]
    at_or_below = sum(dist[min_rank_sum:min_rank_sum + int(u) + 1])
    at_or_above = sum(dist[min_rank_sum + int(u + 0.999999):])
    tail = min(at_or_below, at_or_above)
    p = min(1.0, 2.0 * tail / ways)
    return {
        "n1": n1, "n2": n2, "u": round(u, 9), "ties": ties,
        "p_value": round(p, 9),
        "min_attainable_p": round(min(1.0, 2.0 / ways), 9),
    }


def sign_test(pairs: Sequence[Tuple[float, float]]) -> Dict[str, object]:
    """Exact two-sided sign test over (high, low) pairs.

    Also reports `min_attainable_p` — the smallest two-sided p this many
    non-tied pairs could ever produce. With four games no metric can reach
    0.05 no matter how cleanly it separates, and a battery that did not say so
    would be inviting its reader to over-read a p of 0.125.
    """
    wins = sum(1 for h, l in pairs if h > l)
    losses = sum(1 for h, l in pairs if h < l)
    ties = len(pairs) - wins - losses
    n = wins + losses
    if n == 0:
        return {"n": 0, "wins": wins, "losses": losses, "ties": ties,
                "p_value": None, "min_attainable_p": None}
    k = min(wins, losses)
    tail = sum(comb(n, i) for i in range(k + 1))
    p = min(1.0, 2.0 * tail / (2 ** n))
    return {
        "n": n, "wins": wins, "losses": losses, "ties": ties,
        "p_value": round(p, 9),
        "min_attainable_p": round(min(1.0, 2.0 / (2 ** n)), 9),
    }
