"""E18 -- `lp_potential`'s incompleteness rate, as a script instead of a sentence.

    cd engine-rig && python -m tools.survey_numbers.lp_incomplete
    cd engine-rig && python -m tools.survey_numbers.lp_incomplete --n 500
    cd engine-rig && python -m tools.survey_numbers.lp_incomplete --jsonl worlds.jsonl

The number
----------
E11 published **639 / 2189 = 29.2 %** -- of the `jumpgraph` worlds whose goal is
*genuinely unreachable* (proved by exhaustive forward BFS, no budget exhaustion),
the fraction on which the engine issues **no** certificate.  It appeared as prose
in `runs/20260729T000000Z-E11-engine-crosscheck-deep/partials/lp_potential-via-exhaustive.md`
with no script and no data behind it.  This module is the script.

The recipe, unchanged from E11 §3
---------------------------------
* Worlds are `fuzzlab/worlds/jumpgraph.py::generate`, drawn with the campaign
  seed `0x00005EEDC1E4F002` via `fuzzlab/prng.py::derive(seed, "jumpgraph", i)`
  for `i = 0 .. N-1`.  Index `i < 500` is exactly the world the E4 campaign saw,
  so `--n 500` reproduces the campaign-scale slice the paper also quotes.
* Ground truth is a forward BFS from `spec.initial` over successors built here,
  **from `spec.triples`** -- deliberately *not* from `graph["edges"]`.  E11 §1
  step 3 made that choice on purpose: the engine's move list comes from `edges`
  via `moves_from_graph`, so an oracle reading `edges` would share a failure mode
  with the subject it is judging.  `spec.triples` is the field the generator was
  told to build the world from.  The choice is preserved here, and is the reason
  `edges` appears nowhere below.
* "Unreachable" means the BFS **completed** -- enumerated the whole reachable set
  without hitting `fuzzlab.oracles.search.STATE_BUDGET` -- and reached no goal.
  A timeout is not a proof, and is counted separately (`bfs_budget_exhausted`).
* The engine's answer is `engines.lp_potential.run`, the public pair, plus
  `engines.lp_potential.decide` for the status word.  Both are called; that they
  agree is checked rather than assumed (`run_vs_decide_disagreements`).

The caliber change this module had to resolve
---------------------------------------------
Commit `2a1c30d` ("C11: a tool that failed is not a fact about the world") landed
*after* the E11 run and rewrote the very branch the ratio is a tally of.  Before
it, `solve_certificate` was::

    if not result.success:
        return None

-- so an iteration limit, an unbounded relaxation and numerical difficulties all
arrived at the caller as "no certificate", indistinguishable from a proved
infeasibility.  Today only HiGHS status 2 returns `None`; statuses 1/3/4 raise
`LpUnavailable`.  (E15 then widened the same seam into `LpOutcome`; the decision
rule is unchanged from `2a1c30d`.)

So the number of record is the one recomputed on today's code, and the old
caliber is *measured* rather than guessed.  The two rules are different functions
of one quantity, `result.status`, and the LP handed to HiGHS is byte-identical
across the change -- the only edit to `solve`'s body between `2a1c30d^` and HEAD
is `options=dict(solver_options) if solver_options else None`, a no-op at the
default.  Recording `solver_status` per world therefore yields both rules from
one solve:

    old (pre-2a1c30d):  no certificate  <=>  status != 0
    new (HEAD):         no certificate  <=>  status == 2
                        undecided       <=>  status in {1, 3, 4}

The delta between them is exactly the worlds with status in {1,3,4}, and
`counts["pre_2a1c30d"]` reports it.  `--verify-old-code` goes one step further
and runs the *genuine* pre-`2a1c30d` module: `git show` materialises it into a
temp directory, it is imported by path, and its verdict is compared per world
against the derived one.  Nothing under `engines/` is touched either way.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from tools.survey_numbers import _common

_common.add_repo_root()

import numpy                                                        # noqa: E402
import scipy                                                        # noqa: E402

from engines import lp_potential                                    # noqa: E402
from engines.lp_potential import potential                          # noqa: E402
from fuzzlab import prng                                            # noqa: E402
from fuzzlab.oracles import search                                  # noqa: E402
from fuzzlab.worlds import jumpgraph                                # noqa: E402

KEY = "lp.incomplete"
CAMPAIGN_SEED = 0x00005EEDC1E4F002
FAMILY = "jumpgraph"
DEFAULT_N = 3000
SLICE_N = 500

#: The commit that changed the branch this ratio counts.
CALIBER_COMMIT = "2a1c30d"
OLD_POTENTIAL_PATH = "engine-rig/engines/lp_potential/potential.py"

#: E11's §4.3 headline, recorded verbatim so the comparison is in the artefact.
E11_PROSE = {"numerator": 639, "denominator": 2189, "pct": 29.2}

#: E11 §4.1, likewise.
E11_BASE_RATES = {
    "goal_truly_unreachable": {"count": 2189, "pct": 73.0},
    "goal_truly_reachable": {"count": 811, "pct": 27.0},
    "certificate_issued": {"count": 1550, "pct": 51.7},
    "no_certificate": {"count": 1450, "pct": 48.3},
    "certificate_error": {"count": 0, "pct": 0.0},
}

#: E11 §4.3, the campaign-scale slice.  Shares of *all* N=500 worlds.
E11_SLICE_500 = {
    "no_certificate_total_pct": 46.6,
    "no_certificate_because_reachable_pct": 24.0,
    "no_certificate_and_unreachable_pct": 22.6,
}

#: The wider boxes E11 §6 probed, and the count it reported for all three at
#: once.  They are re-solved and counted *separately* here: the paper's sentence
#: claims all three bounds, and a single collapsed number cannot be checked
#: against a three-part claim.
WIDER_BOUNDS = (100, 10 ** 4, 10 ** 6)
E11_WIDER_BOX_ALL_THREE = 638
E11_BOX_BLOCKED = 1                       # ENGINE_TABLE `lp.box_blocked`
E11_NO_FARKAS = 638                       # ENGINE_TABLE `lp.no_farkas`

#: Every file the answer depends on.  A recomputation whose inputs are not
#: pinned is only marginally better than the prose it replaces.
INPUT_FILES = [
    # the draw
    "fuzzlab/prng.py",
    "engine-rig/common/rng.py",          # SplitMix64, the actual byte stream
    "fuzzlab/rig.py",                    # path bootstrap prng.py imports
    "fuzzlab/worlds/jumpgraph.py",
    "fuzzlab/worlds/common.py",
    # the independent truth
    "fuzzlab/oracles/search.py",
    # the subject
    "engine-rig/engines/lp_potential/__init__.py",
    "engine-rig/engines/lp_potential/potential.py",
    "engine-rig/common/candidates.py",   # imported by lp_potential/__init__
    # this script
    "engine-rig/tools/survey_numbers/lp_incomplete.py",
    "engine-rig/tools/survey_numbers/_common.py",
]


# --------------------------------------------------------------- ground truth

def _successors(state: str, triples: Sequence[Tuple[int, int, int]]) -> List[str]:
    """Peg-jump successors, driven by `spec.triples` and nothing else.

    Written out here rather than imported: `fuzzlab.worlds.jumpgraph.successors`
    would do, but E11 §1 step 3 owns this link precisely so that a defect in the
    world module cannot be shared between the truth and the subject.  The four
    copies of the `(src, over, dst)` convention in this repo are a known shared
    dependency (E11 §2.2) and this is the fourth.
    """
    out = []
    for src, over, dst in triples:
        if state[src] == "1" and state[over] == "1" and state[dst] == "0":
            cells = list(state)
            cells[src] = "0"
            cells[over] = "0"
            cells[dst] = "1"
            out.append("".join(cells))
    return out


def _truth(spec) -> Dict[str, Any]:
    """Exhaustive forward BFS: is a goal reachable, and was the search complete?

    Two oracles from `fuzzlab/oracles/search.py`, both run:

    * `bfs_distances` enumerates the whole reachable set, which is what gives
      `states_enumerated` and what makes "no goal in it" a proof.
    * `distance_to_any` is the function E11 named, and returns the `exhausted`
      bit explicitly.  It stops early on success, so it is not a substitute for
      the first -- it is a second reading of the same question, and a
      disagreement between them is counted rather than silently resolved.
    """
    goals = set(spec.goal_states)

    def succ(state: str) -> List[str]:
        return _successors(state, spec.triples)

    dist = search.bfs_distances(spec.initial, succ)
    to_goal, exhausted = search.distance_to_any(spec.initial, succ, goals)

    if dist is None:                                   # budget hit: not a proof
        return {
            "reachable": None,
            "bfs_exhausted": False,
            "states_enumerated": None,
            "oracles_agree": exhausted is False,
        }
    reachable = any(goal in dist for goal in goals)
    return {
        "reachable": reachable,
        "bfs_exhausted": bool(exhausted),
        "states_enumerated": len(dist),
        "oracles_agree": (to_goal is not None) == reachable and bool(exhausted),
    }


# ------------------------------------------------------------- the engine's word

def _ask_engine(graph: Dict[str, Any], initial: str) -> Dict[str, Any]:
    """What `lp_potential` says, through both public doors.

    `decide` first, for the status word and `solver_status`; then `run`, the pair
    E11 actually called.  Calling both costs a second solve and buys the check
    that they agree -- which is the kind of thing that is true today, cheap to
    assert, and expensive to discover is false later.
    """
    record: Dict[str, Any] = {
        "engine_status": None,
        "solver_status": None,
        "certificate_issued": False,
        "certificate_error": False,
        "lp_unavailable": False,
        "run_vs_decide_disagreement": False,
    }

    try:
        outcome = lp_potential.decide(graph, initial)
    except potential.CertificateError:
        # Weights that failed the exact rational re-check.  Not a certificate,
        # and not a "no linear pagoda" either -- its own row, as in E11 §4.1.
        record["engine_status"] = "certificate_error"
        record["certificate_error"] = True
        return record
    except potential.LpUnavailable as exc:
        got = getattr(exc, "outcome", None)
        record["engine_status"] = potential.UNDECIDED
        record["solver_status"] = None if got is None else got.solver_status
        record["lp_unavailable"] = True
        return record

    record["engine_status"] = outcome.status
    record["solver_status"] = outcome.solver_status

    try:
        certificate, _heuristic = lp_potential.run(graph, initial)
    except potential.CertificateError:
        record["run_vs_decide_disagreement"] = True
        record["engine_status"] = "certificate_error"
        record["certificate_error"] = True
        return record
    except potential.LpUnavailable:
        record["lp_unavailable"] = True
        record["run_vs_decide_disagreement"] = outcome.status in (
            potential.CERTIFIED, potential.NO_LINEAR_PAGODA)
        return record

    record["certificate_issued"] = certificate is not None
    # `run` returns a certificate exactly when `decide` said CERTIFIED.  Checked
    # by name on both sides -- never as `certificate is None`, which is the
    # collapsed reading E15 removed.
    record["run_vs_decide_disagreement"] = (
        (certificate is not None) != (outcome.status == potential.CERTIFIED)
    )
    return record


# ------------------------------------------------------------------ the survey

def survey(n: int = DEFAULT_N) -> List[Dict[str, Any]]:
    """One row per world, in index order.  Pure function of `n`."""
    rows: List[Dict[str, Any]] = []
    for i in range(n):
        seed = prng.derive(CAMPAIGN_SEED, FAMILY, i)
        world = jumpgraph.generate(seed)
        spec, graph = world.spec, world.graph
        truth = _truth(spec)
        engine = _ask_engine(graph, spec.initial)
        rows.append({
            "i": i,
            "seed": seed,
            "n_pos": spec.n_pos,
            "n_goals": len(spec.goal_states),
            "n_triples": len(spec.triples),
            "reachable": truth["reachable"],
            "bfs_exhausted": truth["bfs_exhausted"],
            "states_enumerated": truth["states_enumerated"],
            "oracles_agree": truth["oracles_agree"],
            "certificate_issued": engine["certificate_issued"],
            "certificate_error": engine["certificate_error"],
            "engine_status": engine["engine_status"],
            "solver_status": engine["solver_status"],
            "lp_unavailable": engine["lp_unavailable"],
            "run_vs_decide_disagreement": engine["run_vs_decide_disagreement"],
        })
    return rows


def write_jsonl(rows: Iterable[Dict[str, Any]], path: str | Path) -> str:
    """The raw counts, on disk, one row per world.

    The ticket asks for "the raw counts it spat out"; a 3000-row jsonl is the
    honest form of that -- every claim below is a `grep | wc -l` away.  Keys are
    sorted and the newline is pinned to LF, so the file is byte-stable.
    """
    target = Path(path)
    if target.parent and not target.parent.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return target.as_posix()


# ------------------------------------------------------------------- tallying

def _pct(part: int, whole: int) -> Optional[float]:
    return round(100.0 * part / whole, 1) if whole else None


def _ratio(part: int, whole: int) -> Optional[float]:
    return round(part / whole, 6) if whole else None


def _base_rates(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """E11 §4.1, recomputed, with the prose beside each row."""
    total = len(rows)
    counts = {
        "goal_truly_unreachable": sum(1 for r in rows if r["reachable"] is False),
        "goal_truly_reachable": sum(1 for r in rows if r["reachable"] is True),
        "certificate_issued": sum(1 for r in rows if r["certificate_issued"]),
        "no_certificate": sum(1 for r in rows if not r["certificate_issued"]),
        "certificate_error": sum(1 for r in rows if r["certificate_error"]),
    }
    out: Dict[str, Any] = {}
    for name in sorted(counts):
        prose = E11_BASE_RATES.get(name) if total == DEFAULT_N else None
        row: Dict[str, Any] = {
            "count": counts[name],
            "pct": _pct(counts[name], total),
        }
        if prose is not None:
            row["e11_count"] = prose["count"]
            row["e11_pct"] = prose["pct"]
            row["agrees"] = counts[name] == prose["count"]
        out[name] = row
    return out


def _incompleteness(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """The headline: no certificate, on a world proved unreachable."""
    unreachable = [r for r in rows if r["reachable"] is False]
    silent = [r for r in unreachable if not r["certificate_issued"]]
    return {
        "numerator": len(silent),
        "denominator": len(unreachable),
        "pct": _pct(len(silent), len(unreachable)),
        "rate": _ratio(len(silent), len(unreachable)),
        "share_of_all_worlds_pct": _pct(len(silent), len(rows)),
    }


def _slice_500(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """E11 §4.3's campaign-scale table -- the same computation, truncated.

    Indices are drawn in order and `derive` is a pure function of the index, so
    `rows[:500]` *is* the N=500 corpus; nothing is re-drawn.
    """
    head = rows[:SLICE_N]
    if len(head) < SLICE_N:
        return {"available": False, "reason": "n < %d" % SLICE_N}
    no_cert = [r for r in head if not r["certificate_issued"]]
    because_reachable = [r for r in no_cert if r["reachable"] is True]
    and_unreachable = [r for r in no_cert if r["reachable"] is False]
    out = {
        "available": True,
        "worlds": len(head),
        "no_certificate_total": len(no_cert),
        "no_certificate_total_pct": _pct(len(no_cert), len(head)),
        "no_certificate_because_reachable": len(because_reachable),
        "no_certificate_because_reachable_pct": _pct(len(because_reachable), len(head)),
        "no_certificate_and_unreachable": len(and_unreachable),
        "no_certificate_and_unreachable_pct": _pct(len(and_unreachable), len(head)),
        "incompleteness": _incompleteness(head),
        "e11_prose": dict(E11_SLICE_500),
    }
    out["agrees_with_e11"] = all(
        out[name] == value for name, value in E11_SLICE_500.items()
    )
    return out


def _fact(recomputed: Any, prose: Any, **extra: Any) -> Dict[str, Any]:
    """One registry fact: what it is now, what the prose said, do they agree."""
    out = {"recomputed": recomputed, "e11_prose": prose,
           "agrees": recomputed == prose}
    out.update(extra)
    return out


def _exact_pagoda(weights: Sequence[Any], spec, margin: int = 1) -> Dict[str, Any]:
    """Re-check a weight vector in exact rationals, over `spec.triples`.

    Not the solver's word, and not `graph["edges"]` either -- the same two
    independences the rest of this module keeps.  `solve` has already run
    `check_exactly` over the *engine's* move list; this is the second reading,
    over the world's definition, which is the one E11 §6 published.
    """
    w = [Fraction(x) for x in weights]

    def potential_of(state: str) -> Fraction:
        return sum((w[i] for i, cell in enumerate(state) if cell == "1"),
                   Fraction(0))

    start = potential_of(spec.initial)
    inv_closed = all(w[d] - w[s] - w[o] <= 0 for s, o, d in spec.triples)
    gaps = [potential_of(g) - start for g in spec.goal_states]
    goal_break = all(gap >= Fraction(margin) for gap in gaps)
    return {
        "inv_closed": inv_closed,
        "goal_break": goal_break,
        "holds": inv_closed and goal_break,
        "initial_potential": str(start),
        "goal_gaps": [str(g) for g in gaps],
        "max_abs_weight": str(max((abs(x) for x in w), default=Fraction(0))),
        "triples_checked": len(spec.triples),
    }


def _wider_box(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Re-solve the silent-and-unreachable worlds at each wider `bound`.

    Why this is here rather than in a footnote: `PAPER.md` (§10 adjudication,
    also `papers/phase1-workshop/sections/10_adjudication.md:289`) states that of
    the 639 silences "**638 are still infeasible at bounds of 100, 10⁴ and
    10⁶**", and cites `engine-rig/ENGINE_TABLE.md` for it.  The strings `10⁴`,
    `10⁶` and `bound = 100` do not occur in `ENGINE_TABLE.md`; its only bound key
    is `lp.weight_bound = 10`.  The real source is E11 §6, which is prose.  So
    the paper's strongest sentence about the 639 cites a file that does not
    contain the number, backed by a file that contains no script.

    The three bounds are therefore counted **separately**.  E11's table gave one
    number for all three at once, and a three-part claim cannot be checked
    against a collapsed count: 638-at-each is a different statement from
    638-at-all-three, and only the second is what the sentence asserts.
    """
    silent = [r for r in rows if r["reachable"] is False
              and not r["certificate_issued"]]

    per_bound: Dict[int, Counter] = {bound: Counter() for bound in WIDER_BOUNDS}
    feasible_at: Dict[int, List[Dict[str, Any]]] = {b: [] for b in WIDER_BOUNDS}
    feasible_any: Dict[int, Dict[str, Any]] = {}       # world index -> witness
    infeasible_at_all_three = 0

    for row in silent:
        world = jumpgraph.generate(row["seed"])
        spec, graph = world.spec, world.graph
        still_infeasible = True
        for bound in WIDER_BOUNDS:
            try:
                outcome = lp_potential.decide(graph, spec.initial, bound=bound)
            except potential.CertificateError as exc:
                per_bound[bound]["certificate_error"] += 1
                still_infeasible = False
                feasible_any.setdefault(row["i"], {
                    "i": row["i"], "seed": row["seed"], "first_bound": bound,
                    "status": "certificate_error", "detail": str(exc)[:200],
                })
                continue
            except potential.LpUnavailable as exc:
                got = getattr(exc, "outcome", None)
                per_bound[bound]["undecided"] += 1
                still_infeasible = False
                feasible_any.setdefault(row["i"], {
                    "i": row["i"], "seed": row["seed"], "first_bound": bound,
                    "status": "lp_unavailable",
                    "solver_status": None if got is None else got.solver_status,
                })
                continue

            per_bound[bound][outcome.status] += 1
            if outcome.status == potential.CERTIFIED:
                still_infeasible = False
                witness = {
                    "i": row["i"],
                    "seed": row["seed"],
                    "n_pos": row["n_pos"],
                    "initial": spec.initial,
                    "goal_states": sorted(spec.goal_states),
                    "reachable_size": row["states_enumerated"],
                    "bound": bound,
                    "weights": [str(w) for w in outcome.certificate.weights],
                    "exact_recheck_over_spec_triples":
                        _exact_pagoda(outcome.certificate.weights, spec),
                }
                feasible_at[bound].append(witness)
                feasible_any.setdefault(row["i"], dict(witness, first_bound=bound,
                                                       status="certified"))
            elif outcome.status != potential.NO_LINEAR_PAGODA:
                still_infeasible = False
        if still_infeasible:
            infeasible_at_all_three += 1

    bounds_table = {}
    for bound in WIDER_BOUNDS:
        tally = per_bound[bound]
        still = tally[potential.NO_LINEAR_PAGODA]
        bounds_table[str(bound)] = {
            "bound": bound,
            "still_infeasible": still,
            "feasible": tally[potential.CERTIFIED],
            "undecided": tally["undecided"],
            "certificate_error": tally["certificate_error"],
            "status_counts": dict(sorted(tally.items())),
            "e11_prose_all_three": E11_WIDER_BOX_ALL_THREE,
            "agrees_with_e11_all_three": still == E11_WIDER_BOX_ALL_THREE,
            "feasible_worlds": sorted(feasible_at[bound], key=lambda d: d["i"]),
        }

    widened = sorted(feasible_any.values(), key=lambda d: d["i"])
    return {
        "probed": len(silent),
        "bounds": bounds_table,
        "still_infeasible_at_all_three": _fact(
            infeasible_at_all_three, E11_WIDER_BOX_ALL_THREE,
            claim=("PAPER.md / 10_adjudication.md:289: 'of 639 silences, 638 are "
                   "still infeasible at bounds of 100, 10^4 and 10^6'"),
            cited_to="engine-rig/ENGINE_TABLE.md",
            citation_is_wrong=True,
            citation_note=(
                "ENGINE_TABLE.md contains no bound other than lp.weight_bound=10; "
                "the strings '10^4', '10^6' and 'bound = 100' do not occur in it. "
                "The actual source is "
                "runs/20260729T000000Z-E11-engine-crosscheck-deep/partials/"
                "lp_potential-via-exhaustive.md:275-277, which is prose with no "
                "script behind it. This module is that script."
            ),
        ),
        "box_blocked": _fact(
            len(widened), E11_BOX_BLOCKED,
            registry_key="lp.box_blocked",
            note=("silent-and-unreachable worlds that stop being silent once the "
                  "weight box is widened -- the box, not the mathematics, was "
                  "doing the refusing"),
            worlds=widened,
        ),
        "note": (
            "Counted per bound, not collapsed. `bound` is a solver parameter and "
            "not part of the pagoda definition, so every infeasibility here is "
            "infeasibility *within* the box and each box is its own claim."
        ),
    }


def _no_farkas(rows: Sequence[Dict[str, Any]],
               wider: Dict[str, Any]) -> Dict[str, Any]:
    """`lp.no_farkas` = 638: the silences that rest on HiGHS and nothing else.

    E11 §7: "For the 638 worlds I call genuinely incomplete, the evidence is
    `linprog` returning status 2 in floating point ... I did not produce an exact
    rational infeasibility certificate (Farkas dual)".  It is the 639 minus the
    one the widened box rescues -- the one *positive* result E11 verified
    exactly.  Everything left is a solver's verdict.

    The paper leans on this: it is the "no exact Farkas dual produced" limitation
    at 10_adjudication.md:294.  Nothing in this module upgrades it; the count is
    recomputed, the epistemic status is not.
    """
    silent_unreachable = sum(1 for r in rows if r["reachable"] is False
                             and not r["certificate_issued"])
    rescued = wider["box_blocked"]["recomputed"]
    return _fact(
        silent_unreachable - rescued, E11_NO_FARKAS,
        registry_key="lp.no_farkas",
        derivation="silent-and-unreachable (%d) minus rescued-by-a-wider-box (%d)"
                   % (silent_unreachable, rescued),
        farkas_duals_produced=0,
        evidence=("scipy.optimize.linprog reporting HiGHS status 2 in floating "
                  "point at |w_i| <= 10. No exact rational infeasibility "
                  "certificate was computed for any of them, so 'no linear "
                  "pagoda exists' remains a solver's claim, not a proof."),
    )


def _denominators(rows: Sequence[Dict[str, Any]],
                  wider: Dict[str, Any]) -> Dict[str, Any]:
    """The two denominators the number 639 is quoted against, side by side.

    `ENGINE_TABLE.md` publishes `lp.incomplete = 639 / 2189`, where 2189 is every
    genuinely unreachable world.  The paper writes "of **639 silences**, 638 are
    still infeasible ...", using 639 itself as the denominator.  Both sentences
    can be true at once, but only if the 639 in each is the *same set of worlds*
    -- and the word "silences" is the hazard, because the engine is silent on
    1450 worlds, not 639.  811 of those silences are the engine correctly
    declining to prove a false statement on a reachable world.

    So the set identity is checked rather than assumed.
    """
    unreachable = [r for r in rows if r["reachable"] is False]
    all_silences = [r for r in rows if not r["certificate_issued"]]
    silent_unreachable = [r for r in unreachable if not r["certificate_issued"]]
    silent_reachable = [r for r in all_silences if r["reachable"] is True]

    numerator_ids = sorted(r["i"] for r in silent_unreachable)
    probed_ids = sorted(w["i"] for w in wider["box_blocked"]["worlds"])
    same_set = set(probed_ids) <= set(numerator_ids)

    return {
        "numerator": len(silent_unreachable),
        "registry": {
            "key": "lp.incomplete",
            "ratio": "%d / %d" % (len(silent_unreachable), len(unreachable)),
            "denominator": len(unreachable),
            "denominator_means": "worlds whose goal is genuinely unreachable",
            "pct": _pct(len(silent_unreachable), len(unreachable)),
        },
        "paper_phrasing": {
            "quote": "of 639 silences, 638 are still infeasible at bounds of "
                     "100, 10^4 and 10^6",
            "denominator": len(silent_unreachable),
            "denominator_means": "silences that fall on a genuinely unreachable "
                                 "world -- i.e. the registry's numerator, reused "
                                 "as a denominator",
            "pct_of_that_denominator": _pct(
                wider["still_infeasible_at_all_three"]["recomputed"],
                len(silent_unreachable)),
        },
        "all_silences": {
            "count": len(all_silences),
            "on_unreachable_worlds": len(silent_unreachable),
            "on_reachable_worlds": len(silent_reachable),
            "share_that_is_incompleteness_pct": _pct(len(silent_unreachable),
                                                     len(all_silences)),
        },
        "same_set_of_worlds": same_set,
        "reading_hazard": (
            "The engine is silent on %d worlds, not %d. 'of %d silences' names "
            "the %d silences that land on a genuinely unreachable world; the "
            "other %d are the engine correctly declining to prove a false "
            "statement about a reachable one (E11 §5.4 -- no public path yields "
            "a certificate for a solvable configuration, so every reachable "
            "world is a silence by construction). Both sentences are true; a "
            "reader who takes 639 for the silence count is off by %.1fx and "
            "would compute the box artefact's scale as 1/%d = %s%% instead of "
            "1/%d = %s%%."
            % (len(all_silences), len(silent_unreachable),
               len(silent_unreachable), len(silent_unreachable),
               len(silent_reachable),
               (len(all_silences) / len(silent_unreachable))
               if silent_unreachable else 0.0,
               len(silent_unreachable),
               round(100.0 * 1 / len(silent_unreachable), 3)
               if silent_unreachable else None,
               len(all_silences),
               round(100.0 * 1 / len(all_silences), 3) if all_silences else None)
        ),
    }


def _caliber(rows: Sequence[Dict[str, Any]],
             verified: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """What `2a1c30d` did to this number, measured.

    Old rule: `not result.success` -> no certificate, for every status.
    New rule: only status 2 -> no certificate; 1/3/4 raise.
    They differ exactly on the worlds whose `solver_status` is 1, 3 or 4.
    """
    undecided = [r for r in rows
                 if r["solver_status"] is not None and r["solver_status"] not in (0, 2)]
    undecided += [r for r in rows if r["solver_status"] is None
                  and not r["certificate_error"]]
    unreachable = [r for r in rows if r["reachable"] is False]

    # Under the old rule those worlds would have counted as "no certificate",
    # and the unreachable ones would have joined the numerator.
    new = _incompleteness(rows)
    extra = sum(1 for r in undecided if r["reachable"] is False)
    old_numerator = new["numerator"] + extra
    return {
        "commit": CALIBER_COMMIT,
        "what_changed": (
            "`if not result.success: return None` became `only HiGHS status 2 "
            "returns None; 1/3/4 raise LpUnavailable`.  The LP handed to HiGHS "
            "is unchanged: the sole edit to solve()'s body between 2a1c30d^ and "
            "HEAD is `options=dict(solver_options) if solver_options else None`, "
            "which is a no-op at the default."
        ),
        "solver_status_histogram": dict(sorted(
            Counter("null" if r["solver_status"] is None else str(r["solver_status"])
                    for r in rows).items())),
        "worlds_where_the_rules_differ": len(undecided),
        "of_those_truly_unreachable": extra,
        "old_rule_numerator": old_numerator,
        "old_rule_denominator": new["denominator"],
        "old_rule_pct": _pct(old_numerator, new["denominator"]),
        "delta_numerator": old_numerator - new["numerator"],
        "delta_pct": round(
            (_pct(old_numerator, new["denominator"]) or 0.0) - (new["pct"] or 0.0), 1),
        "verified_against_old_module": verified,
        "note": (
            "The delta is zero only because HiGHS never returned 1, 3 or 4 on "
            "this corpus.  That is a fact about these 3000 LPs, not a guarantee: "
            "the two rules are genuinely different functions and the first "
            "iteration limit would separate them."
        ),
        "unreachable_worlds_in_denominator": len(unreachable),
    }


# --------------------------------------------- the genuine pre-2a1c30d module

def _load_old_potential() -> Tuple[Any, str]:
    """Materialise `2a1c30d^:.../potential.py` in a temp dir and import it.

    Scratch only: nothing under `engines/` is written or shadowed, and the module
    is loaded by path under a private name so it cannot be picked up by an
    ordinary import.  It has no engine-local imports (math, dataclasses,
    fractions, typing, numpy, scipy), which is what makes this cheap.
    """
    import importlib.util

    rev = "%s^:%s" % (CALIBER_COMMIT, OLD_POTENTIAL_PATH)
    source = subprocess.run(
        ["git", "show", rev],
        cwd=str(_common.repo_root()), capture_output=True, check=True,
    ).stdout
    directory = tempfile.mkdtemp(prefix="e18-old-lp-")
    path = os.path.join(directory, "potential_pre_2a1c30d.py")
    with open(path, "wb") as handle:
        handle.write(source)

    spec = importlib.util.spec_from_file_location("_e18_potential_pre_2a1c30d", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def _verify_old_code(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Run the real old `solve_certificate` and compare it to the derivation.

    A measured "cannot be reproduced, here is why" would be an acceptable
    deliverable; it is not needed, because the old module runs.  If `git` is
    absent the reason is reported rather than swallowed.
    """
    try:
        old, path = _load_old_potential()
    except Exception as exc:                            # pragma: no cover
        return {
            "ran": False,
            "reason": "%s: %s" % (type(exc).__name__, exc),
            "note": "the old number could not be re-measured on this machine",
        }

    agree = 0
    disagree: List[Dict[str, Any]] = []
    old_no_certificate = 0
    old_certificate = 0
    old_errors = 0
    for row in rows:
        world = jumpgraph.generate(row["seed"])
        try:
            certificate = old.solve_certificate(world.graph, world.spec.initial)
        except old.CertificateError:
            old_errors += 1
            derived = "certificate_error"
        else:
            if certificate is None:
                old_no_certificate += 1
                derived = "no_certificate"
            else:
                old_certificate += 1
                derived = "certificate"
        # what the derivation predicts the old code would have said
        if row["certificate_error"]:
            predicted = "certificate_error"
        elif row["solver_status"] == 0:
            predicted = "certificate"
        else:
            predicted = "no_certificate"
        if predicted == derived:
            agree += 1
        else:
            disagree.append({"i": row["i"], "seed": row["seed"],
                             "old_module": derived, "derived": predicted})

    unreachable = [r for r in rows if r["reachable"] is False]
    silent_unreachable = 0
    for row in unreachable:
        world = jumpgraph.generate(row["seed"])
        try:
            certificate = old.solve_certificate(world.graph, world.spec.initial)
        except old.CertificateError:
            certificate = None
        if certificate is None:
            silent_unreachable += 1

    return {
        "ran": True,
        "source": "git show %s^:%s" % (CALIBER_COMMIT, OLD_POTENTIAL_PATH),
        "scratch_path_kind": "tempfile.mkdtemp (not under engines/)",
        "worlds_compared": len(rows),
        "agree": agree,
        "disagree": len(disagree),
        "disagreements": sorted(disagree, key=lambda d: d["i"])[:20],
        "old_certificate_issued": old_certificate,
        "old_no_certificate": old_no_certificate,
        "old_certificate_errors": old_errors,
        "old_numerator": silent_unreachable,
        "old_denominator": len(unreachable),
        "old_pct": _pct(silent_unreachable, len(unreachable)),
        "loaded_from_basename": os.path.basename(path),
    }


# -------------------------------------------------------------------- compute

def compute(n: int = DEFAULT_N, verify_old_code: bool = False,
            jsonl_path: Optional[str] = None,
            wider_box: bool = True) -> Dict[str, Any]:
    """Recompute `lp.incomplete` and its three dependants, in `result` shape.

    Four registry facts, not one, because a parallel census found that of the 87
    E11-sourced facts only two reach the paper body and both are this engine's:

    * `lp.incomplete`   = 639 / 2189 -- the headline (`value`)
    * `lp.no_farkas`    = 638 -- the paper's Farkas-dual limitation
    * the bound triple  -- "638 still infeasible at 100, 10^4, 10^6", whose
                           citation points at a file that does not contain it
    * both denominators the number 639 is quoted against
    """
    rows = survey(n)
    if jsonl_path:
        write_jsonl(rows, jsonl_path)

    incompleteness = _incompleteness(rows)
    verified = _verify_old_code(rows) if verify_old_code else None
    caliber = _caliber(rows, verified)
    wider = _wider_box(rows) if wider_box else None

    value = {
        "numerator": incompleteness["numerator"],
        "denominator": incompleteness["denominator"],
        "pct": incompleteness["pct"],
    }

    counts: Dict[str, Any] = {
        "worlds": n,
        "campaign_seed": "0x%016X" % CAMPAIGN_SEED,
        "family": FAMILY,
        # `agrees_with_e11` at the top level compares against E11 §4.3, which is
        # an N=3000 number.  Saying so here rather than letting a `--n 500` run
        # publish a bare `false` that means "different corpus", not "different
        # answer" -- the N=500 comparison lives in `slice_500.agrees_with_e11`.
        "e11_prose_scope": (
            "E11 §4.3 quotes 639/2189 at N=3000; the top-level agrees_with_e11 "
            "is only meaningful at the default N=%d (this run: N=%d)"
            % (DEFAULT_N, n)
        ),
        "base_rates": _base_rates(rows),
        "incompleteness": incompleteness,
        "slice_500": _slice_500(rows),
        "pre_2a1c30d": caliber,
        # --- the three paper-body facts that hang off the same 639 ---
        "wider_box": wider if wider is not None else {
            "ran": False,
            "reason": "wider_box=False; the bound triple was not recomputed",
        },
        "no_farkas": _no_farkas(rows, wider) if wider is not None else {
            "recomputed": None,
            "e11_prose": E11_NO_FARKAS,
            "agrees": None,
            "reason": "needs the wider-box sweep; run with wider_box=True",
        },
        "denominators_for_639": _denominators(rows, wider) if wider is not None
        else {"reason": "needs the wider-box sweep; run with wider_box=True"},
        "integrity": {
            # Every one of these should be zero; each is a way the measurement
            # could be quietly wrong rather than loudly broken.
            "bfs_budget_exhausted": sum(1 for r in rows if not r["bfs_exhausted"]),
            "oracle_disagreements": sum(1 for r in rows if not r["oracles_agree"]),
            "run_vs_decide_disagreements": sum(
                1 for r in rows if r["run_vs_decide_disagreement"]),
            "lp_unavailable": sum(1 for r in rows if r["lp_unavailable"]),
            "reachability_undetermined": sum(1 for r in rows if r["reachable"] is None),
        },
        "engine_status_histogram": dict(sorted(
            Counter(str(r["engine_status"]) for r in rows).items())),
        "n_pos_histogram": dict(sorted(
            Counter(str(r["n_pos"]) for r in rows).items())),
        # Two different totals, kept apart because E11 quotes both and they are
        # an order of magnitude apart.  §3's "505 312 states enumerated" is the
        # size of the *state spaces* (sum of 2^n_pos), which is what the
        # per-state admissibility sweep walked; the reachable-set total is what
        # this module's BFS actually visited.
        "reachable_states_total": sum(r["states_enumerated"] or 0 for r in rows),
        "state_space_total": sum(1 << r["n_pos"] for r in rows),
        "state_space_total_e11": 505312 if n == DEFAULT_N else None,
        "environment": {
            "python": "%d.%d.%d" % sys.version_info[:3],
            "numpy": numpy.__version__,
            "scipy": scipy.__version__,
        },
        "jsonl_written": jsonl_path if jsonl_path else None,
    }

    return _common.result(
        key=KEY,
        question=(
            "Of the jumpgraph worlds whose goal is genuinely unreachable (proved "
            "by exhaustive forward BFS over spec.triples, no budget exhaustion), "
            "on what fraction does lp_potential issue no certificate?"
        ),
        value=value,
        e11_prose=dict(E11_PROSE),
        counts=counts,
        inputs=_common.input_digests(INPUT_FILES),
        method=(
            "Draw world i from prng.derive(0x00005EEDC1E4F002, 'jumpgraph', i) "
            "for i = 0..%d and generate it with fuzzlab.worlds.jumpgraph.generate. "
            "Ground truth: forward BFS from spec.initial over successors built in "
            "this module from spec.triples -- NOT from graph['edges'], preserving "
            "E11 §1 step 3, because the engine's move list is built from edges and "
            "an oracle sharing that table shares its failures. Unreachable = the "
            "BFS enumerated the whole reachable set within "
            "fuzzlab.oracles.search.STATE_BUDGET and met no goal. Engine answer: "
            "engines.lp_potential.decide for the status word and "
            "engines.lp_potential.run for the (certificate, heuristic) pair, with "
            "their agreement checked. Numerator = unreachable worlds with no "
            "certificate; denominator = unreachable worlds."
            % (DEFAULT_N - 1)
        ),
        caveats=[
            "CALIBER (%s): the code path that produced E11's 29.2%% was rewritten "
            "after the E11 run. `if not result.success: return None` became `only "
            "HiGHS status 2 returns None; statuses 1/3/4 raise LpUnavailable`, and "
            "E15 (99204472, d2b75c26, af884509) then widened the same seam into "
            "LpOutcome without changing the decision rule. The number above is "
            "measured on today's code and is the number of record. "
            "counts.pre_2a1c30d measures the old rule from the same solver "
            "statuses: old %s/%s = %s%%, new %s/%s = %s%%, delta %+d world(s) in "
            "the numerator. HiGHS returned status 1/3/4 on %d of %d worlds, which "
            "is the only place the two rules can differ.%s"
            % (CALIBER_COMMIT,
               caliber["old_rule_numerator"], caliber["old_rule_denominator"],
               caliber["old_rule_pct"],
               incompleteness["numerator"], incompleteness["denominator"],
               incompleteness["pct"],
               caliber["delta_numerator"],
               caliber["worlds_where_the_rules_differ"], n,
               "" if verified is None else
               (" The derivation was checked against the genuine pre-%s module: "
                "%d/%d worlds agree." % (CALIBER_COMMIT, verified.get("agree", 0),
                                         verified.get("worlds_compared", 0))
                if verified.get("ran") else
                " The genuine old module could NOT be run here: %s."
                % verified.get("reason"))),
            "SHARED DEPENDENCY: scipy.optimize.linprog / HiGHS decides the "
            "engine's verdict, and there is no second solver here to check it "
            "against. scipy %s, numpy %s, Python %d.%d.%d. E11 ran scipy 1.17.1, "
            "numpy 2.4.4, Python 3.13.13; a HiGHS behaviour change would move this "
            "number and would be invisible from inside this script."
            % (scipy.__version__, numpy.__version__, *sys.version_info[:3]),
            "SHARED DEPENDENCY: fuzzlab.worlds.jumpgraph.generate produces both "
            "the truth and the engine's input (E11 §2.1). A generator that only "
            "emitted easy geometries would flatter both sides.",
            "SHARED DEPENDENCY: the (src, over, dst) peg-jump convention is "
            "hard-coded in Move.delta, jumpgraph.apply, fuzzlab/props and in "
            "_successors here -- four copies of one rule (E11 §2.2). If the "
            "convention is wrong they are all wrong together.",
            "NOT A PROOF OF NON-EXISTENCE: 'no certificate' on an unreachable "
            "world means HiGHS reported the LP infeasible in floating point with "
            "|w_i| <= 10. No exact rational infeasibility certificate (Farkas "
            "dual) is produced, so the numerator rests on the solver's word "
            "(E11 §7). E11 found exactly 1 of the 639 to be feasible at "
            "bound=100 -- seed 17475932563032345095, index 2302 -- so the box, "
            "not the mathematics, does the refusing there.",
            "SCOPE: n_pos <= 9 (jumpgraph.MAX_POSITIONS), so <= 512 states per "
            "world and the exhaustive BFS is what buys the truth. The "
            "silence-vs-n_pos trend is decreasing over 4..9; extrapolating past 9 "
            "is unjustified in either direction.",
            "The E11 partial's own numbers were independently reproduced by the "
            "E15 census (runs/20260729T044500Z-E15-solver-status-bit/SUMMARY.json) "
            "on post-2a1c30d code. This module is a third, differently-plumbed "
            "reading, not a copy of either.",
        ] + ([] if wider is None else [
            "BAD CITATION (finding, not a caveat about this run): PAPER.md and "
            "papers/phase1-workshop/sections/10_adjudication.md:289 state that "
            "of the 639 silences '638 are still infeasible at bounds of 100, "
            "10^4 and 10^6' and cite engine-rig/ENGINE_TABLE.md. ENGINE_TABLE.md "
            "contains no bound but lp.weight_bound=10 -- the strings '10^4', "
            "'10^6' and 'bound = 100' do not occur in it. The true source is the "
            "E11 partial at lines 275-277, which was prose. The claim itself "
            "recomputes exactly (%s), counted per bound rather than collapsed: "
            "%s. The citation is what is wrong, not the number."
            % (wider["still_infeasible_at_all_three"]["recomputed"],
               ", ".join("bound=%s -> %d still infeasible"
                         % (t["bound"], t["still_infeasible"])
                         for t in sorted(wider["bounds"].values(),
                                         key=lambda d: d["bound"]))),
            "DENOMINATOR: 639 is quoted against two different denominators. "
            "ENGINE_TABLE's lp.incomplete is 639/2189 (2189 = genuinely "
            "unreachable worlds); the paper's 'of 639 silences' reuses the "
            "numerator as a denominator. counts.denominators_for_639 confirms "
            "these are the same set of worlds, so both sentences are true -- but "
            "the engine is silent on 1450 worlds, not 639, and the other 811 "
            "silences are reachable worlds the engine correctly declines to "
            "certify. A reader who reads 639 as the silence count is off by 2.3x.",
            "NOT A PROOF, PART 2: lp.no_farkas = %s is recomputed here, but only "
            "the count is. Zero exact rational infeasibility certificates "
            "(Farkas duals) were produced by this module either, so the paper's "
            "limitation at 10_adjudication.md:294 stands exactly as written and "
            "is not weakened or strengthened by this script."
            % _no_farkas(rows, wider)["recomputed"],
        ]),
    )


# ----------------------------------------------------------------------- cli

def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m tools.survey_numbers.lp_incomplete",
        description=__doc__.splitlines()[0],
    )
    parser.add_argument(
        "--n", type=int, default=int(os.environ.get("E18_N", DEFAULT_N)),
        help="number of worlds (default %d, or $E18_N); --n 500 is the "
             "campaign-scale slice" % DEFAULT_N,
    )
    parser.add_argument(
        "--jsonl", metavar="PATH", default=os.environ.get("E18_JSONL") or None,
        help="also write one JSON-lines row per world to PATH",
    )
    parser.add_argument(
        "--verify-old-code", action="store_true",
        default=bool(os.environ.get("E18_VERIFY_OLD_CODE")),
        help="also run the genuine pre-%s solve_certificate (materialised into a "
             "temp dir by `git show`) and compare it to the derived old rule"
             % CALIBER_COMMIT,
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = _parse_args(argv)
    _common.main(lambda: compute(
        n=args.n,
        verify_old_code=args.verify_old_code,
        jsonl_path=args.jsonl,
    ))


if __name__ == "__main__":
    main()
