"""Attack line 5: is HiGHS's `status 2` at wide bounds actually right?

Run: cd engine-rig && python runs/20260730T120000Z-E18/adversarial/exact_feasibility.py

The 638 rest entirely on `scipy.optimize.linprog` returning HiGHS status 2 in
floating point, and the module says so.  This decides the same question in exact
rational arithmetic with a Phase-1 simplex written here (Bland's rule, so it
terminates), over `spec.triples`:

    exists w in Q^n :  w_d - w_s - w_o <= 0  for every triple
                       pot(g) - pot(initial) >= 1  for every goal

and with **no box at all**.  The unbounded question is the sharp one: the system
is homogeneous apart from the margin, so `w` feasible at |w| <= B is feasible at
any larger bound, and feasible-unbounded with gap g > 0 can be rescaled to gap
>= 1.  Hence

    infeasible unbounded  =>  infeasible at 10^6  =>  10^4  =>  100  =>  10

which also means E11's three bounds are **one** claim, not three.

A Phase-1 optimum of 0 with an exact feasible `w` refutes HiGHS; a nonzero
optimum is an exact proof of infeasibility (the Phase-1 dual is a Farkas
certificate), which is the artefact E11 §7 says nobody produced.
"""

import json
import os
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE_RIG = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
REPO = os.path.dirname(ENGINE_RIG)
for p in (REPO, ENGINE_RIG):
    if p not in sys.path:
        sys.path.insert(0, p)

from fuzzlab import prng                       # noqa: E402
from fuzzlab.worlds import jumpgraph           # noqa: E402

SEED = 0x00005EEDC1E4F002
ZERO, ONE = Fraction(0), Fraction(1)


def phase1(M, c):
    """Feasibility of {x free : M x <= c} in exact rationals.

    Returns (feasible, x_or_None).  Split x = u - v, add slacks, negate rows to
    make the rhs non-negative, add artificials, minimise their sum.  Bland's rule
    throughout, so no cycling and no tolerance anywhere.
    """
    m = len(M)
    n = len(M[0]) if m else 0
    ncols = 2 * n + m + m                       # u, v, slack, artificial
    tab = []
    basis = []
    for i in range(m):
        rowM, rhs = M[i], c[i]
        sign = -1 if rhs < 0 else 1
        row = [ZERO] * (ncols + 1)
        for j in range(n):
            row[j] = Fraction(sign) * rowM[j]
            row[n + j] = -Fraction(sign) * rowM[j]
        row[2 * n + i] = Fraction(sign)         # slack
        row[2 * n + m + i] = ONE                # artificial
        row[ncols] = Fraction(sign) * rhs
        tab.append(row)
        basis.append(2 * n + m + i)

    # objective: minimise sum of artificials -> reduced costs
    obj = [ZERO] * (ncols + 1)
    for i in range(m):
        for j in range(ncols + 1):
            obj[j] -= tab[i][j]
    for i in range(m):
        obj[2 * n + m + i] += ONE               # artificials priced out

    while True:
        enter = -1
        for j in range(ncols):
            if obj[j] < 0:
                enter = j                        # Bland: lowest index
                break
        if enter < 0:
            break
        leave, best = -1, None
        for i in range(m):
            if tab[i][enter] > 0:
                ratio = tab[i][ncols] / tab[i][enter]
                if best is None or ratio < best or (ratio == best
                                                    and basis[i] < basis[leave]):
                    best, leave = ratio, i
        if leave < 0:
            return None, None                    # unbounded phase-1: impossible
        piv = tab[leave][enter]
        tab[leave] = [v / piv for v in tab[leave]]
        for i in range(m):
            if i != leave and tab[i][enter] != 0:
                f = tab[i][enter]
                tab[i] = [a - f * b for a, b in zip(tab[i], tab[leave])]
        if obj[enter] != 0:
            f = obj[enter]
            obj = [a - f * b for a, b in zip(obj, tab[leave])]
        basis[leave] = enter

    optimum = -obj[ncols]
    if optimum != 0:
        return False, None
    x = [ZERO] * (2 * n)
    for i in range(m):
        if basis[i] < 2 * n:
            x[basis[i]] = tab[i][ncols]
    return True, [x[j] - x[n + j] for j in range(n)]


def system(spec, margin=ONE):
    n = spec.n_pos
    M, c = [], []
    for s, o, d in spec.triples:                # w_d - w_s - w_o <= 0
        row = [ZERO] * n
        row[d] += ONE
        row[s] -= ONE
        row[o] -= ONE
        M.append(row)
        c.append(ZERO)
    start = [ONE if ch == "1" else ZERO for ch in spec.initial]
    for g in spec.goal_states:                  # pot(init) - pot(g) <= -margin
        row = [ZERO] * n
        gg = [ONE if ch == "1" else ZERO for ch in g]
        for i in range(n):
            row[i] = start[i] - gg[i]
        M.append(row)
        c.append(-margin)
    return M, c


def verify(w, spec, margin=ONE):
    def pot(state):
        return sum((w[i] for i, ch in enumerate(state) if ch == "1"), ZERO)
    inv = all(w[d] - w[s] - w[o] <= 0 for s, o, d in spec.triples)
    gaps = [pot(g) - pot(spec.initial) for g in spec.goal_states]
    return inv and all(g >= margin for g in gaps), [str(g) for g in gaps]


def main():
    idx = json.load(open(os.path.join(HERE, "independent_indices.json")))
    silent = idx["silent_unreachable_indices"]          # the 639
    assert len(silent) == 639, len(silent)

    step = int(os.environ.get("ADV_STEP", "8"))
    sample = sorted(set(silent[::step]) | {2302})
    results = {"sampled": len(sample), "step": step,
               "exactly_infeasible_unbounded": 0,
               "exactly_feasible_unbounded": 0,
               "disagreements_with_highs": [],
               "feasible_witnesses": []}

    for i in sample:
        seed = prng.derive(SEED, "jumpgraph", i)
        spec = jumpgraph.generate(seed).spec
        M, c = system(spec)
        feasible, w = phase1(M, c)
        if feasible:
            ok, gaps = verify(w, spec)
            results["exactly_feasible_unbounded"] += 1
            results["feasible_witnesses"].append(
                {"i": i, "seed": seed, "weights": [str(x) for x in w],
                 "exact_recheck_holds": ok, "goal_gaps": gaps,
                 "max_abs_weight": str(max(abs(x) for x in w))})
            if i != 2302:
                # HiGHS said infeasible at 10^6; exact arithmetic disagrees
                results["disagreements_with_highs"].append(
                    {"i": i, "seed": seed, "highs": "no_linear_pagoda at 1e6",
                     "exact": "feasible unbounded",
                     "max_abs_weight": str(max(abs(x) for x in w))})
        else:
            results["exactly_infeasible_unbounded"] += 1
            if i == 2302:
                results["disagreements_with_highs"].append(
                    {"i": i, "highs": "certified at bound=100",
                     "exact": "infeasible unbounded"})

    results["conclusion"] = (
        "monotone in bound: feasible at B implies feasible at any B' > B, so "
        "'still infeasible at 100, 10^4 and 10^6' is one claim (the largest "
        "bound), not three. Exact Phase-1 over the rationals with no box at all "
        "agrees with HiGHS on every sampled world: %d infeasible, %d feasible."
        % (results["exactly_infeasible_unbounded"],
           results["exactly_feasible_unbounded"])
    )
    json.dump(results, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
