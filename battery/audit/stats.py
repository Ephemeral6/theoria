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
