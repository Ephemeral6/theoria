"""Process 3 — de-redundancy.

`Theoria.md`: *相关性聚类，一族留代表——二十个互相相关的数字不是二十个发现.*

Spearman rather than Pearson: these metrics are ratios, counts and shares on
wildly different scales, and monotone agreement is what "says the same thing"
actually means here.

Clustering is single-linkage at |rho| >= 0.9 — transitive by construction, so
the result does not depend on the order metrics arrive in. That determinism is
worth more than a cleverer algorithm: two runs of the battery must produce the
same clusters, and an agglomerative method with a tie-break would not promise
that.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from battery.audit.stats import spearman
from battery.metrics import REGISTRY, Value

THRESHOLD = 0.9
MIN_SHARED = 4      # fewer than four shared runs and a correlation is noise


def _series(values: Dict[str, Dict[str, Value]],
            metric_id: str) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for run_id in sorted(values):
        value = values[run_id].get(metric_id)
        if value is not None and value.ok and value.value is not None:
            out[run_id] = value.value
    return out


def correlations(values: Dict[str, Dict[str, Value]]
                 ) -> Dict[Tuple[str, str], Optional[float]]:
    series = {mid: _series(values, mid) for mid in sorted(REGISTRY)}
    out: Dict[Tuple[str, str], Optional[float]] = {}
    ids = sorted(REGISTRY)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            shared = sorted(set(series[a]) & set(series[b]))
            if len(shared) < MIN_SHARED:
                out[(a, b)] = None
                continue
            out[(a, b)] = spearman([series[a][k] for k in shared],
                                   [series[b][k] for k in shared])
    return out


def cluster(values: Dict[str, Dict[str, Value]]) -> Dict[str, object]:
    """Group metrics that say the same thing and nominate one representative.

    The representative is the metric with the most usable data, ties broken by
    id. Coverage, not elegance: a cluster's representative has to be the one
    most likely to have a number when it matters, and any tie-break that
    consulted the *values* would let the choice be made after seeing them.
    """
    ids = sorted(REGISTRY)
    parent = {mid: mid for mid in ids}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            # Always point at the lexicographically smaller root, so the
            # forest's shape does not depend on iteration order.
            lo, hi = sorted((ra, rb))
            parent[hi] = lo

    rho = correlations(values)
    strong: List[Dict[str, object]] = []
    for (a, b), value in sorted(rho.items()):
        if value is not None and abs(value) >= THRESHOLD:
            union(a, b)
            strong.append({"a": a, "b": b, "rho": round(value, 9)})

    groups: Dict[str, List[str]] = {}
    for mid in ids:
        groups.setdefault(find(mid), []).append(mid)

    coverage = {mid: len(_series(values, mid)) for mid in ids}
    clusters = []
    for root in sorted(groups):
        members = sorted(groups[root])
        representative = sorted(
            members, key=lambda m: (-coverage[m], m))[0]
        clusters.append({
            "members": members,
            "representative": representative,
            "families": sorted({REGISTRY[m].family for m in members}),
            "coverage": {m: coverage[m] for m in members},
        })

    # The basis, not just the verdict.  A cluster assignment is an assertion
    # about every pair that did *not* cluster as much as about the pairs that
    # did, and "these two metrics say the same thing" is not checkable from a
    # list of clusters alone.  Every pair is emitted with its rho and the
    # number of runs the correlation was computed over, so a reader can see
    # which non-clusterings were decisions and which were simply absences --
    # on thin data most pairs share too few runs to correlate at all, and a
    # matrix full of `null` is a very different fact from a matrix full of
    # small correlations.
    pairs = []
    measured = 0
    for (a, b), value in sorted(rho.items()):
        shared = len(set(_series(values, a)) & set(_series(values, b)))
        if value is not None:
            measured += 1
        pairs.append({
            "a": a, "b": b,
            "rho": None if value is None else round(value, 9),
            "shared_runs": shared,
            "reason": (None if value is not None
                       else "fewer than %d shared runs" % MIN_SHARED),
        })

    families: Dict[str, List[str]] = {}
    for mid in ids:
        families.setdefault(REGISTRY[mid].family, []).append(mid)

    return {
        "threshold": THRESHOLD,
        "min_shared_runs": MIN_SHARED,
        "method": ("Spearman rank correlation; single-linkage clustering at "
                   "|rho| >= %.1f, transitive by construction so the result "
                   "does not depend on the order metrics arrive in"
                   % THRESHOLD),
        "n_clusters": len(clusters),
        "n_metrics": len(ids),
        "n_pairs": len(pairs),
        "n_pairs_measured": measured,
        "n_pairs_unmeasurable": len(pairs) - measured,
        "coverage_note": (
            "%d of %d metric pairs share enough runs to correlate at all. A "
            "cluster count near the metric count reflects thin data, not "
            "twenty independent findings."
            % (measured, len(pairs))),
        "strong_pairs": strong,
        "clusters": clusters,
        "representatives": sorted(c["representative"] for c in clusters),
        "by_family": {f: sorted(ms) for f, ms in sorted(families.items())},
        "matrix": pairs,
    }
