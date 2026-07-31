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
  for `i = 0 .. N-1`.  The E4 campaign drew the same family from the same seed in
  the same index order, so `rows[:500]` is the campaign's prefix rather than a
  fresh draw -- but only the first **60** indices are checkable against a
  committed seed table.  `fuzzlab/out/campaign.json` is now a 60-world run
  (`worlds_per_engine: 60`) and `fuzzlab/out/seeds.jsonl` holds 60 jumpgraph
  rows, all 60 of which equal `derive(seed, "jumpgraph", i)` for `i = 0..59`.
  The 500-world artefact survives at
  `fuzzlab/runs/20260728T161127Z-V13-audit-the-published-surface/partials/campaign.500w.json`;
  indices 60..499 are reproduced by the same pure function but have no committed
  seed row to check them against.
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

The numerator is a status word, not a missing object
----------------------------------------------------
A world is in the numerator when the engine returned **`no_linear_pagoda`** --
HiGHS status 2, a statement about the configuration.  It is *not* `certificate is
None`, which is also true when HiGHS hit its iteration limit, went unbounded or
broke down numerically, and true again when weights failed exact re-checking.
Those outcomes are counted **apart** and published in
`counts.incompleteness.set_apart`; none of them can enter the ratio.  This is the
rule commit `2a1c30d` exists to enforce ("a tool that failed is not a fact about
the world", D-024), and an earlier version of this module broke it inside the
audit written to check it.  On this corpus the two readings coincide exactly --
`lp_unavailable = 0`, `certificate_error = 0` -- so the published 639 is
unmoved; the point is that it now cannot move for the wrong reason.

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
of one quantity, `result.status`, and **the LP handed to HiGHS is unchanged
across the change**: `moves_from_graph`, `_occupancy`, `check_exactly`, `Move`,
`Certificate.holds` and the constraint-matrix construction are byte-identical
between `2a1c30d^` and HEAD, and the added `options=dict(solver_options) if
solver_options else None` is `None` at the default, which is scipy's own default.
What did change is the whole post-`linprog` branch -- the status table, the
`LpOutcome` return, the `success`-vs-`status` contradiction check -- i.e. the
*classification* of one solve, not the solve.  Recording `solver_status` per
world therefore yields both rules from one solve:

    old (pre-2a1c30d):  no certificate  <=>  status != 0
    new (HEAD):         no certificate  <=>  status == 2
                        undecided       <=>  status in {1, 3, 4}

The delta between them is exactly the worlds with status in {1,3,4}, and
`counts["pre_2a1c30d"]` reports it.  `--verify-old-code` goes one step further
and runs the *genuine* pre-`2a1c30d` module: `git show` materialises it into a
temp directory, it is imported by path, and its verdict is compared per world
against the derived one.  Nothing under `engines/` is touched either way, and the
temp directory is removed before the function returns.

The exact upgrade
-----------------
`counts.no_pagoda_exact` re-decides the same 639 worlds with an exact rational
Phase-1 simplex (Bland's rule, `Fraction` throughout, **no weight box at all**)
and, where the system is infeasible, emits the **Farkas multiplier vector** that
proves it.  A Phase-1 optimum > 0 in exact arithmetic *is* an infeasibility
proof, so those worlds stop resting on a solver's floating-point word.  The
resulting statement is strictly stronger than the paper's: no linear pagoda
exists at *any* weight magnitude, not merely within `|w| <= 10^6`.
`lp.no_farkas` is left exactly as it was -- the paper's claim is about the
bounded case and has to stay checkable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
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
#: once.  They are re-solved at each bound here as a **solver-consistency
#: check**, not because three separate answers were owed: the constraint system
#: is homogeneous apart from the goal margin and the box only widens, so a `w`
#: feasible at `|w| <= B` is feasible at every `B' > B` and infeasibility at
#: 10^6 entails infeasibility at 10^4 and at 100.  Three equal counts are forced
#: unless HiGHS is inconsistent with itself; E11's single number was not a defect.
WIDER_BOUNDS = (100, 10 ** 4, 10 ** 6)
E11_WIDER_BOX_ALL_THREE = 638
E11_BOX_BLOCKED = 1                       # ENGINE_TABLE `lp.box_blocked`
E11_NO_FARKAS = 638                       # ENGINE_TABLE `lp.no_farkas`

#: How many certified / reachable worlds the exact simplex re-decides as
#: controls.  First-N in index order, so the sample is a pure function of the run.
EXACT_CONTROL_SAMPLE = 60

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
        record["engine_status"] = potential.UNDECIDED if got is None else got.status
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


# ------------------------------------------------------- the numerator predicate

def _is_no_linear_pagoda(row: Dict[str, Any]) -> bool:
    """The one predicate the ratio may be built on.

    `engine_status == "no_linear_pagoda"` is HiGHS status 2: the LP was *proved*
    infeasible inside the box.  Every other silence -- `budget`, `unbounded`,
    `numerical`, `undecided`, `certificate_error` -- is a fact about the solver
    and is counted somewhere else.  `not certificate_issued` is the collapsed
    reading `2a1c30d` removed from the engine, and it must not reappear here.
    """
    return row.get("engine_status") == potential.NO_LINEAR_PAGODA


def _old_rule_no_certificate(row: Dict[str, Any]) -> bool:
    """What pre-`2a1c30d` `solve_certificate` would have returned `None` for.

    `if not result.success: return None`, and `success` is exactly
    `status == 0`.  A `CertificateError` raised there too, so it is not a
    `None`.  `solver_status is None` means the solve did not even get far enough
    to report one, which the old code also reached as "no certificate".
    """
    if row.get("certificate_error"):
        return False
    return row.get("solver_status") != 0


def _set_apart(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Every outcome that is a fact about HiGHS rather than about the world."""
    apart = [r for r in rows
             if not _is_no_linear_pagoda(r)
             and r.get("engine_status") != potential.CERTIFIED]
    return {
        "total": len(apart),
        "certificate_error": sum(1 for r in apart if r["certificate_error"]),
        "lp_unavailable": sum(1 for r in apart if r["lp_unavailable"]),
        "by_engine_status": dict(sorted(
            Counter(str(r["engine_status"]) for r in apart).items())),
        "world_indices": sorted(r["i"] for r in apart)[:50],
        "rule": (
            "budget / unbounded / numerical / undecided / certificate_error. "
            "None of these may enter the incompleteness numerator: a tool that "
            "failed is not a fact about the world (D-024, commit %s)."
            % CALIBER_COMMIT
        ),
    }


# ------------------------------------------------------------------- tallying

def _pct(part: int, whole: int) -> Optional[float]:
    return round(100.0 * part / whole, 1) if whole else None


def _ratio(part: int, whole: int) -> Optional[float]:
    return round(part / whole, 6) if whole else None


def _base_rates(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """E11 §4.1, recomputed, with the prose beside each row.

    `no_certificate` is kept as E11 defined it -- the engine handed back no
    certificate object -- because that is the row E11 published.  `no_linear_pagoda`
    is the same question asked of the status word, and the two are reported side
    by side precisely so a reader can see whether they coincide.  On this corpus
    they do; that is a fact about these 3000 solves, not an identity.
    """
    total = len(rows)
    counts = {
        "goal_truly_unreachable": sum(1 for r in rows if r["reachable"] is False),
        "goal_truly_reachable": sum(1 for r in rows if r["reachable"] is True),
        "certificate_issued": sum(1 for r in rows if r["certificate_issued"]),
        "no_certificate": sum(1 for r in rows if not r["certificate_issued"]),
        "certificate_error": sum(1 for r in rows if r["certificate_error"]),
        # not E11 rows: the status-word reading of the same two questions
        "no_linear_pagoda": sum(1 for r in rows if _is_no_linear_pagoda(r)),
        "solver_did_not_decide": sum(
            1 for r in rows
            if not _is_no_linear_pagoda(r)
            and r["engine_status"] != potential.CERTIFIED),
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
    """The headline: the engine returned `no_linear_pagoda` on an unreachable world.

    Built on the status word, never on `certificate is None`.  Undecided solves
    and exact-recheck failures are reported in `set_apart` and are not in the
    numerator; they are also not silently in the *denominator's* favour, since
    the denominator is "goal genuinely unreachable" and says nothing about the
    solver at all.
    """
    unreachable = [r for r in rows if r["reachable"] is False]
    silent = [r for r in unreachable if _is_no_linear_pagoda(r)]
    certified = [r for r in unreachable
                 if r["engine_status"] == potential.CERTIFIED]
    apart = _set_apart(unreachable)
    return {
        "numerator": len(silent),
        "denominator": len(unreachable),
        "pct": _pct(len(silent), len(unreachable)),
        "rate": _ratio(len(silent), len(unreachable)),
        "share_of_all_worlds_pct": _pct(len(silent), len(rows)),
        "numerator_predicate": (
            "engine_status == 'no_linear_pagoda' (HiGHS status 2) AND the goal is "
            "unreachable by exhaustive BFS -- NOT `certificate is None`"
        ),
        "certified": len(certified),
        "set_apart": apart,
        "accounted": len(silent) + len(certified) + apart["total"] == len(unreachable),
        "collapsed_reading_would_be": sum(
            1 for r in unreachable if not r["certificate_issued"]),
        "collapsed_reading_note": (
            "`not certificate_issued` over the same worlds. Equal to the "
            "numerator only while no solve is undecided; it is published so the "
            "gap is visible the first time they part."
        ),
    }


def _slice_500(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """E11 §4.3's campaign-scale table -- the same computation, truncated.

    Indices are drawn in order and `derive` is a pure function of the index, so
    `rows[:500]` *is* the N=500 corpus; nothing is re-drawn.  The three
    `no_certificate_*` shares are E11's own rows and keep E11's predicate (no
    certificate object came back); `incompleteness` below them is the status-word
    reading.
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


def _fact(recomputed: Any, prose: Any, scope_note: Optional[str] = None,
          **extra: Any) -> Dict[str, Any]:
    """One registry fact: what it is now, what the prose said, do they agree.

    `scope_note` is the guard the module applies wherever a comparison against
    E11's N=3000 prose would otherwise publish a bare `false` at another `--n`.
    A `false` that means "different corpus" is worse than no answer, so out of
    scope `agrees` is `null` and the reason travels with it.
    """
    out = {"recomputed": recomputed, "e11_prose": prose,
           "agrees": None if scope_note else recomputed == prose}
    if scope_note:
        out["scope"] = scope_note
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


# ------------------------------------------------- exact rational feasibility

_QZERO = Fraction(0)
_QONE = Fraction(1)


def pagoda_system(spec, margin: int = 1) -> Tuple[List[List[Fraction]],
                                                  List[Fraction]]:
    """`{w in Q^n : A w <= b}` -- the pagoda conditions, with **no weight box**.

    Row order is fixed and published, because a Farkas multiplier vector is only
    checkable against a stated row order:

    * rows `0 .. len(spec.triples)-1`: `w_dst - w_src - w_over <= 0`, one per
      triple, in `spec.triples` order (the tuple is already sorted by the
      generator);
    * the remaining rows: `pot(initial) - pot(goal) <= -margin`, one per goal, in
      `sorted(spec.goal_states)` order.

    `margin` is a free scale.  Every row is homogeneous in `w` except the goal
    rows' right-hand side, so a solution with any positive margin rescales to one
    with margin 1 -- which is why "no box" and "margin = 1" together lose nothing.
    """
    n = spec.n_pos
    matrix: List[List[Fraction]] = []
    rhs: List[Fraction] = []
    for src, over, dst in spec.triples:
        row = [_QZERO] * n
        row[dst] += _QONE
        row[src] -= _QONE
        row[over] -= _QONE
        matrix.append(row)
        rhs.append(_QZERO)
    start = [_QONE if cell == "1" else _QZERO for cell in spec.initial]
    for goal in sorted(spec.goal_states):
        occupied = [_QONE if cell == "1" else _QZERO for cell in goal]
        matrix.append([start[i] - occupied[i] for i in range(n)])
        rhs.append(Fraction(-margin))
    return matrix, rhs


def phase1(matrix: Sequence[Sequence[Fraction]], rhs: Sequence[Fraction]):
    """Exact Phase-1 simplex for `{x free : A x <= b}`.  Bland's rule throughout.

    Returns `(feasible, x_or_None, farkas_or_None)`.

    `x = u - v` with `u, v >= 0`, one slack per row, one artificial per row, rows
    negated where `b_i < 0` so every right-hand side is non-negative, minimising
    the sum of the artificials.  Bland's rule means no cycling and -- since every
    number is a `Fraction` -- no tolerance anywhere, so "optimum > 0" is exact.

    **Where the certificate comes from.**  The objective row carries the reduced
    costs `d_j = c_j - y^T A_j` for the current dual `y`.  For artificial column
    `i`, `A_j = e_i` and `c_j = 1`, so `y_i = 1 - d_{art_i}` reads straight off
    it.  Dual feasibility on the slack column of row `i` gives `sign_i * y_i <=
    0`, and on the `u_j` / `v_j` pair gives `sum_i y_i sign_i A_ij = 0`.  Setting
    `lambda_i = -sign_i * y_i` therefore yields

        lambda >= 0,   lambda^T A = 0,   lambda^T b = -optimum < 0

    which is exactly Farkas' lemma's certificate that `A x <= b` has no solution.
    It is returned rather than described, and `check_farkas` re-checks it from
    `A` and `b` alone.
    """
    m = len(matrix)
    n = len(matrix[0]) if m else 0
    ncols = 2 * n + m + m                       # u, v, slack, artificial
    tab: List[List[Fraction]] = []
    basis: List[int] = []
    signs: List[int] = []
    for i in range(m):
        sign = -1 if rhs[i] < 0 else 1
        signs.append(sign)
        scale = Fraction(sign)
        row = [_QZERO] * (ncols + 1)
        for j in range(n):
            row[j] = scale * matrix[i][j]
            row[n + j] = -scale * matrix[i][j]
        row[2 * n + i] = scale                  # slack
        row[2 * n + m + i] = _QONE              # artificial
        row[ncols] = scale * rhs[i]
        tab.append(row)
        basis.append(2 * n + m + i)

    obj = [_QZERO] * (ncols + 1)
    for i in range(m):
        for j in range(ncols + 1):
            obj[j] -= tab[i][j]
    for i in range(m):
        obj[2 * n + m + i] += _QONE             # artificials priced out

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
        if leave < 0:                            # pragma: no cover -- impossible
            raise RuntimeError(
                "phase-1 objective unbounded below, which cannot happen: the sum "
                "of non-negative artificials is bounded below by 0"
            )
        piv = tab[leave][enter]
        tab[leave] = [v / piv for v in tab[leave]]
        for i in range(m):
            if i != leave and tab[i][enter] != 0:
                factor = tab[i][enter]
                tab[i] = [a - factor * b for a, b in zip(tab[i], tab[leave])]
        if obj[enter] != 0:
            factor = obj[enter]
            obj = [a - factor * b for a, b in zip(obj, tab[leave])]
        basis[leave] = enter

    optimum = -obj[ncols]
    if optimum != 0:
        farkas = [Fraction(signs[i]) * (obj[2 * n + m + i] - _QONE)
                  for i in range(m)]
        return False, None, farkas
    x = [_QZERO] * (2 * n)
    for i in range(m):
        if basis[i] < 2 * n:
            x[basis[i]] = tab[i][ncols]
    return True, [x[j] - x[n + j] for j in range(n)], None


def primitive_integers(vector: Sequence[Fraction]) -> List[int]:
    """Scale a rational vector to the smallest integer vector of the same ray.

    A Farkas certificate is a ray -- any positive multiple proves the same thing
    -- so the published form is normalised.  That makes it small, canonical and
    comparable across runs instead of carrying whatever denominators the pivot
    sequence happened to leave behind.
    """
    denominator = 1
    for value in vector:
        denominator = denominator * value.denominator // math.gcd(
            denominator, value.denominator)
    scaled = [int(value * denominator) for value in vector]
    common = 0
    for value in scaled:
        common = math.gcd(common, abs(value))
    if common > 1:
        scaled = [value // common for value in scaled]
    return scaled


def check_farkas(multipliers: Sequence[int],
                 matrix: Sequence[Sequence[Fraction]],
                 rhs: Sequence[Fraction]) -> Dict[str, Any]:
    """Re-derive the proof from `A`, `b` and the multipliers, and nothing else.

    `lambda >= 0`, `lambda^T A = 0`, `lambda^T b < 0`.  Given those three, any
    `x` with `A x <= b` would give `0 = (lambda^T A) x = lambda^T (A x) <=
    lambda^T b < 0`.  So the system has no solution -- over the rationals and
    over the reals, at any weight magnitude, with no tolerance and no solver in
    the argument.
    """
    n = len(matrix[0]) if matrix else 0
    combination = [sum((multipliers[i] * matrix[i][j] for i in range(len(matrix))),
                       _QZERO) for j in range(n)]
    product = sum((multipliers[i] * rhs[i] for i in range(len(matrix))), _QZERO)
    nonnegative = all(value >= 0 for value in multipliers)
    zero_combination = all(value == 0 for value in combination)
    return {
        "multipliers_nonnegative": nonnegative,
        "combination_is_zero": zero_combination,
        "rhs_is_negative": product < 0,
        "lambda_dot_b": str(product),
        "valid": nonnegative and zero_combination and product < 0,
    }


def decide_exactly(spec, margin: int = 1) -> Dict[str, Any]:
    """Does *any* linear pagoda exist for this world?  Exactly, and unboxed.

    One of two answers, both of them checkable without trusting this function:
    a rational weight vector re-verified by `_exact_pagoda`, or a Farkas
    multiplier vector re-verified by `check_farkas`.
    """
    matrix, rhs = pagoda_system(spec, margin=margin)
    feasible, weights, farkas = phase1(matrix, rhs)
    if feasible:
        recheck = _exact_pagoda(weights, spec, margin=margin)
        return {
            "feasible": True,
            "weights": [str(w) for w in weights],
            "exact_recheck_over_spec_triples": recheck,
            "max_abs_weight": recheck["max_abs_weight"],
        }
    multipliers = primitive_integers(farkas)
    return {
        "feasible": False,
        "farkas_multipliers": multipliers,
        "verification": check_farkas(multipliers, matrix, rhs),
        "rows": len(matrix),
        "invariant_rows": len(spec.triples),
        "goal_rows": len(matrix) - len(spec.triples),
    }


def _engine_rows_match_spec(graph: Dict[str, Any], spec) -> bool:
    """Is the LP the engine solves the same system the exact simplex refutes?

    The engine builds its move list with `moves_from_graph(graph)`, over
    `graph["edges"]`; `pagoda_system` builds its rows from `spec.triples`.  The
    exact infeasibility proof only transfers to the engine's claim if the two
    describe the same constraint set, so the identity is checked per world
    rather than argued once.  Same for the goal set.
    """
    engine_moves = {(m.src, m.over, m.dst)
                    for m in potential.moves_from_graph(graph)}
    if engine_moves != {tuple(t) for t in spec.triples}:
        return False
    return sorted(graph["goal_states"]) == sorted(spec.goal_states)


def _no_pagoda_exact(rows: Sequence[Dict[str, Any]],
                     wider: Optional[Dict[str, Any]] = None,
                     controls: int = EXACT_CONTROL_SAMPLE) -> Dict[str, Any]:
    """`no_pagoda_exact`: the 639, re-decided in exact rationals with no box.

    This is the upgrade `lp.no_farkas` was waiting for.  E11 §7 and the paper's
    limitation at `10_adjudication.md:294` both say the 638 rest on
    `scipy.optimize.linprog` reporting HiGHS status 2 in floating point, with no
    exact rational infeasibility certificate produced.  One is produced here, per
    world, and re-checked from the constraint matrix alone.

    Two things this is **not**:

    * It is not `lp.no_farkas`.  That count is the paper's claim about the
      bounded case and stays exactly where it was, so the paper stays checkable.
    * It is not a claim about the engine's box.  It is the stronger statement --
      no linear pagoda exists at any weight magnitude -- which *entails* the
      boxed one but is not what E11 measured.

    Controls, because a decision procedure that always says "infeasible" would
    reproduce the headline perfectly: the first `controls` certified worlds must
    come back exactly feasible, and the first `controls` worlds whose goal is
    genuinely *reachable* must come back exactly infeasible (no pagoda can exist
    when the goal is reachable -- the potential would have to rise).
    """
    silent = [r for r in rows if r["reachable"] is False and _is_no_linear_pagoda(r)]
    certified_control = [r for r in rows
                         if r["engine_status"] == potential.CERTIFIED][:controls]
    reachable_control = [r for r in rows if r["reachable"] is True][:controls]

    certificates: List[Dict[str, Any]] = []
    witnesses: List[Dict[str, Any]] = []
    unverified: List[Dict[str, Any]] = []
    contradictions: List[Dict[str, Any]] = []
    system_mismatch: List[int] = []

    for row in silent:
        world = jumpgraph.generate(row["seed"])
        spec, graph = world.spec, world.graph
        if not _engine_rows_match_spec(graph, spec):
            system_mismatch.append(row["i"])
        verdict = decide_exactly(spec)
        if verdict["feasible"]:
            # HiGHS said no_linear_pagoda at |w| <= 10 and unboxed exact
            # arithmetic finds a pagoda.  That is the engine's documented
            # incompleteness, not a contradiction -- unless the witness fits
            # inside the box the engine actually searched, which would mean one
            # of the two is wrong.
            in_box = Fraction(verdict["max_abs_weight"]) <= 10
            witness = {
                "i": row["i"], "seed": row["seed"],
                "weights": verdict["weights"],
                "max_abs_weight": verdict["max_abs_weight"],
                "inside_engine_default_box": in_box,
                "reading": ("the box, not the mathematics, was refusing: a "
                            "pagoda exists but every one of them has a weight "
                            "of magnitude > 10"),
                "exact_recheck_over_spec_triples":
                    verdict["exact_recheck_over_spec_triples"],
            }
            witnesses.append(witness)
            if in_box:
                contradictions.append(dict(witness, contradiction=(
                    "HiGHS reported the LP infeasible at bound=10 and an exact "
                    "witness with |w| <= 10 exists; one of the two is wrong")))
            continue
        entry = {
            "i": row["i"],
            "seed": row["seed"],
            "farkas_multipliers": verdict["farkas_multipliers"],
            "rows": verdict["rows"],
            "invariant_rows": verdict["invariant_rows"],
            "goal_rows": verdict["goal_rows"],
            "lambda_dot_b": verdict["verification"]["lambda_dot_b"],
            "verified": verdict["verification"]["valid"],
        }
        certificates.append(entry)
        if not verdict["verification"]["valid"]:
            unverified.append(dict(entry, verification=verdict["verification"]))

    def _control(sample: Sequence[Dict[str, Any]], expect_feasible: bool,
                 why: str) -> Dict[str, Any]:
        failures = []
        for row in sample:
            spec = jumpgraph.generate(row["seed"]).spec
            verdict = decide_exactly(spec)
            ok = verdict["feasible"] is expect_feasible
            if ok and expect_feasible:
                ok = verdict["exact_recheck_over_spec_triples"]["holds"]
            if ok and not expect_feasible:
                ok = verdict["verification"]["valid"]
            if not ok:
                failures.append({"i": row["i"], "seed": row["seed"],
                                 "feasible": verdict["feasible"]})
        return {
            "worlds": len(sample),
            "selection": "first %d in index order (%d requested)"
                         % (len(sample), controls),
            "expected": "exactly feasible" if expect_feasible
                        else "exactly infeasible",
            "why": why,
            "failures": failures,
            "passed": not failures and bool(sample),
        }

    ids = "\n".join(str(entry["i"]) for entry in certificates)
    feasible_ids = sorted(w["i"] for w in witnesses)
    cross_check: Dict[str, Any] = {
        "checked": wider is not None,
        "why": (
            "Two independent routes to the same one world: the wider-box sweep "
            "finds it CERTIFIED at bound=100, and the exact unboxed simplex "
            "finds a rational pagoda for it. They are computed from different "
            "code (HiGHS over graph['edges'] vs an exact simplex over "
            "spec.triples), so agreeing on the id set is a real check."
        ),
    }
    if wider is not None:
        box_blocked_ids = sorted(w["i"] for w in wider["box_blocked"]["worlds"])
        cross_check.update({
            "box_blocked_world_ids": box_blocked_ids,
            "exactly_feasible_world_ids": feasible_ids,
            "identical": box_blocked_ids == feasible_ids,
        })
    return {
        "recomputed": len(certificates),
        "probed": len(silent),
        "exactly_infeasible_unbounded": len(certificates),
        "exactly_feasible_unbounded": len(witnesses),
        "farkas_certificates_verified": sum(
            1 for entry in certificates if entry["verified"]),
        "farkas_certificates_unverified": unverified,
        "contradictions_with_highs": contradictions,
        "agrees_with_box_blocked": cross_check,
        "engine_system_differs_from_spec_triples": system_mismatch,
        "controls": {
            "certified_worlds": _control(
                certified_control, True,
                "the engine issued a certificate, so a pagoda demonstrably "
                "exists; an exact 'infeasible' here would falsify the simplex"),
            "reachable_worlds": _control(
                reachable_control, False,
                "the goal is reachable by BFS, so no pagoda can exist -- the "
                "potential would have to rise along the path; an exact "
                "'feasible' here would falsify the simplex's soundness"),
        },
        "certificate_world_ids_sha256": hashlib.sha256(
            ids.encode("utf-8")).hexdigest(),
        # The proofs themselves, one per world, in index order.  A count of
        # certificates is not a certificate: without the multipliers a reader is
        # back to trusting a script instead of trusting a solver, which is the
        # trade this whole section exists to refuse.
        "certificates": certificates,
        "feasible_witnesses": witnesses,
        "row_order": (
            "Multipliers are indexed by the rows of pagoda_system(spec): first "
            "one row per triple in spec.triples order (w_dst - w_src - w_over "
            "<= 0), then one row per goal in sorted(spec.goal_states) order "
            "(pot(initial) - pot(goal) <= -1). They are normalised to the "
            "smallest non-negative integer vector on the same ray."
        ),
        "method": (
            "Exact rational Phase-1 simplex (Bland's rule, fractions.Fraction "
            "throughout, no floating point) over {w : A w <= b} built from "
            "spec.triples and spec.goal_states with margin 1 and NO weight box. "
            "A Phase-1 optimum > 0 is an infeasibility proof; the objective row "
            "at that optimum yields the Farkas multipliers, which are normalised "
            "to primitive integers and re-checked against A and b by "
            "check_farkas(). See tools/survey_numbers/lp_incomplete.py::phase1."
        ),
        "claim": (
            "For each of the %d worlds listed in `certificates`, the published "
            "multipliers lambda satisfy lambda >= 0, lambda^T A = 0 and "
            "lambda^T b < 0, so no weight vector w over the rationals or the "
            "reals satisfies the pagoda conditions -- at ANY weight magnitude, "
            "not merely within |w| <= 10^6. This is strictly stronger than the "
            "paper's sentence and it is a proof rather than a solver's report."
            % len(certificates)
        ),
        "relation_to_no_farkas": (
            "lp.no_farkas = %d is left untouched: it is the paper's count of "
            "worlds whose infeasibility rested on HiGHS alone, and the paper has "
            "to stay checkable against it. What changes is the epistemic status "
            "of those worlds, recorded here as a separate number rather than by "
            "overwriting theirs." % E11_NO_FARKAS
        ),
        "margin_is_free": (
            "Every row is homogeneous in w except the goal rows' right-hand "
            "side, so a pagoda with any positive margin rescales to one with "
            "margin 1. Fixing margin = 1 loses no solutions."
        ),
    }


def _wider_box(rows: Sequence[Dict[str, Any]],
               scope_note: Optional[str] = None) -> Dict[str, Any]:
    """Re-solve the silent-and-unreachable worlds at each wider `bound`.

    Why this is here rather than in a footnote: `PAPER.md` §10.5 (also
    `papers/phase1-workshop/sections/10_adjudication.md:289`) states that of the
    639 silences "**638 are still infeasible at bounds of 100, 10⁴ and 10⁶**".
    That sentence carries no citation of its own -- it attributes itself to "A
    reviewer rebuilt the LP independently and re-derived it" -- and
    `ENGINE_TABLE.md` has **no registry key** for the triple.  Its `lp.*` keys
    are `incomplete`, `incomplete_of_all`, `no_farkas`, `box_blocked` and
    `weight_bound = 10`; none of them is "still infeasible at 100 / 10⁴ / 10⁶".
    So before E18 those three numbers were in the paper with no registry entry
    and no script behind them -- **unregistered**, which is a smaller finding
    than a miscitation and is the accurate one.  This function is the script.

    **What re-running each bound buys, and what it does not.**  It is a
    solver-consistency check, not three separate claims being settled.  The
    system is homogeneous apart from the goal margin and the box only widens, so
    a `w` feasible at `|w| <= B` is feasible at every `B' > B`, and infeasibility
    at 10⁶ entails infeasibility at 10⁴ and at 100.  Three equal counts are
    therefore *forced* unless HiGHS contradicts itself between bounds -- which is
    worth measuring, and is what this measures.  E11 reporting one number for all
    three was not a defect.

    **Only a genuine feasible result may say the box was the problem.**
    `box_blocked` is documented as "the box, not the mathematics, was doing the
    refusing", and a solve that *failed* at a wider bound establishes nothing of
    the kind.  Failures go to `solve_failed` and are visible there; an earlier
    version of this function fed them into `box_blocked` and thence subtracted
    them from `lp.no_farkas`, which is the exact defect `2a1c30d` exists to
    remove, reappearing in the audit.
    """
    silent = [r for r in rows if r["reachable"] is False and _is_no_linear_pagoda(r)]

    per_bound: Dict[int, Counter] = {bound: Counter() for bound in WIDER_BOUNDS}
    feasible_at: Dict[int, List[Dict[str, Any]]] = {b: [] for b in WIDER_BOUNDS}
    feasible_any: Dict[int, Dict[str, Any]] = {}       # world index -> witness
    failed_any: Dict[int, Dict[str, Any]] = {}         # world index -> failure
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
                failed_any.setdefault(row["i"], {
                    "i": row["i"], "seed": row["seed"], "first_bound": bound,
                    "failure": "certificate_error", "detail": str(exc)[:200],
                })
                continue
            except potential.LpUnavailable as exc:
                got = getattr(exc, "outcome", None)
                per_bound[bound]["lp_unavailable_raised"] += 1
                still_infeasible = False
                failed_any.setdefault(row["i"], {
                    "i": row["i"], "seed": row["seed"], "first_bound": bound,
                    "failure": "lp_unavailable",
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
                # budget / unbounded / numerical / undecided -- returned, not
                # raised.  A non-answer, and it goes with the other non-answers.
                still_infeasible = False
                failed_any.setdefault(row["i"], {
                    "i": row["i"], "seed": row["seed"], "first_bound": bound,
                    "failure": outcome.status,
                    "solver_status": outcome.solver_status,
                })
        if still_infeasible:
            infeasible_at_all_three += 1

    undecided_words = (potential.BUDGET, potential.UNBOUNDED,
                       potential.NUMERICAL, potential.UNDECIDED)
    bounds_table = {}
    for bound in WIDER_BOUNDS:
        tally = per_bound[bound]
        still = tally[potential.NO_LINEAR_PAGODA]
        undecided = sum(tally[word] for word in undecided_words)
        raised = tally["lp_unavailable_raised"]
        errors = tally["certificate_error"]
        bounds_table[str(bound)] = {
            "bound": bound,
            "probed": len(silent),
            "still_infeasible": still,
            "feasible": tally[potential.CERTIFIED],
            # `decide` RETURNS budget/unbounded/numerical rather than raising, so
            # reading one key named "undecided" off the tally reported 0 while
            # the status counts said otherwise.  Both paths are summed here and
            # `accounted` proves nothing fell between them.
            "undecided_returned": undecided,
            "lp_unavailable_raised": raised,
            "certificate_error": errors,
            "solve_failed": undecided + raised + errors,
            "status_counts": dict(sorted(tally.items())),
            "accounted": (still + tally[potential.CERTIFIED]
                          + undecided + raised + errors) == len(silent),
            "e11_prose_all_three": E11_WIDER_BOX_ALL_THREE,
            "agrees_with_e11_all_three": (
                None if scope_note else still == E11_WIDER_BOX_ALL_THREE),
            "feasible_worlds": sorted(feasible_at[bound], key=lambda d: d["i"]),
        }
        if scope_note:
            bounds_table[str(bound)]["scope"] = scope_note

    widened = sorted(feasible_any.values(), key=lambda d: d["i"])
    failed = sorted(failed_any.values(), key=lambda d: d["i"])
    return {
        "probed": len(silent),
        "bounds": bounds_table,
        "still_infeasible_at_all_three": _fact(
            infeasible_at_all_three, E11_WIDER_BOX_ALL_THREE, scope_note,
            claim=("PAPER.md §10.5 / 10_adjudication.md:289: 'of 639 silences, "
                   "638 are still infeasible at bounds of 100, 10^4 and 10^6'"),
            registry_key=None,
            registry_note=(
                "ENGINE_TABLE.md has no key for this triple. Its lp.* keys are "
                "incomplete, incomplete_of_all, no_farkas, box_blocked and "
                "weight_bound=10; the strings '10^4', '10^6' and 'bound = 100' "
                "do not occur in it. The sentence cites no artefact of its own "
                "-- it attributes itself to a reviewer's re-derivation, whose "
                "write-up is "
                "runs/20260729T000000Z-E11-engine-crosscheck-deep/partials/"
                "lp_potential-via-exhaustive.md:275-277, prose with no script. "
                "So the number was unregistered and unscripted, not miscited. "
                "This module is the script; the registry key is still missing."
            ),
            counted_per_bound_because=(
                "solver consistency, not three claims: infeasibility at 10^6 "
                "already entails infeasibility at 10^4 and 100, so unequal "
                "counts across bounds would mean HiGHS disagreed with itself."
            ),
        ),
        "box_blocked": _fact(
            len(widened), E11_BOX_BLOCKED, scope_note,
            registry_key="lp.box_blocked",
            note=("silent-and-unreachable worlds on which a wider box yields a "
                  "genuine CERTIFIED outcome -- the box, not the mathematics, "
                  "was doing the refusing. Only status 0 counts: a failed solve "
                  "at a wider bound is not a rescued world."),
            worlds=widened,
        ),
        "solve_failed": {
            "count": len(failed),
            "worlds": failed,
            "note": (
                "Solves that did not decide at some wider bound. Kept out of "
                "box_blocked and out of the no_farkas subtraction, and reported "
                "here instead. Zero on this corpus; the branch exists so that a "
                "future solver failure is loud rather than laundered."
            ),
        },
        "note": (
            "Counted per bound as a consistency check on the solver. `bound` is "
            "a solver parameter and not part of the pagoda definition, so every "
            "infeasibility here is infeasibility *within* the box; "
            "counts.no_pagoda_exact removes the box entirely."
        ),
    }


def _no_farkas(rows: Sequence[Dict[str, Any]],
               wider: Dict[str, Any],
               exact: Optional[Dict[str, Any]] = None,
               scope_note: Optional[str] = None) -> Dict[str, Any]:
    """`lp.no_farkas` = 638: the silences that rest on HiGHS and nothing else.

    E11 §7: "For the 638 worlds I call genuinely incomplete, the evidence is
    `linprog` returning status 2 in floating point ... I did not produce an exact
    rational infeasibility certificate (Farkas dual)".  It is the 639 minus the
    one the widened box rescues -- the one *positive* result E11 verified
    exactly.  Everything left was, at the time, a solver's verdict.

    The count is unchanged and deliberately so: the paper's limitation at
    `10_adjudication.md:294` is a claim about what E11 produced, and rewriting
    the number would make the paper uncheckable.  What *has* changed is that
    `counts.no_pagoda_exact` now supplies the missing artefact -- an exact
    rational Farkas certificate per world -- so the gap this number names is
    closed elsewhere rather than edited away here.
    """
    silent_unreachable = sum(1 for r in rows
                             if r["reachable"] is False and _is_no_linear_pagoda(r))
    rescued = wider["box_blocked"]["recomputed"]
    extra: Dict[str, Any] = {
        "registry_key": "lp.no_farkas",
        "derivation": "silent-and-unreachable (%d) minus rescued-by-a-genuine-"
                      "CERTIFIED-at-a-wider-box (%d)" % (silent_unreachable, rescued),
        "farkas_duals_produced_by_e11": 0,
        "evidence": ("scipy.optimize.linprog reporting HiGHS status 2 in floating "
                     "point at |w_i| <= 10. E11 computed no exact rational "
                     "infeasibility certificate for any of them, which is what "
                     "the paper's limitation records."),
    }
    if exact is not None:
        extra["superseded_epistemically_by"] = {
            "count": "counts.no_pagoda_exact",
            "verified_certificates": exact["farkas_certificates_verified"],
            "what_it_adds": (
                "%d of these worlds now carry an exact rational Farkas "
                "certificate, re-checkable from the constraint matrix alone, and "
                "with no weight box at all. The count above is unchanged because "
                "it is the paper's claim; the epistemic status is no longer 'a "
                "solver's claim, not a proof'."
                % exact["farkas_certificates_verified"]),
        }
    return _fact(silent_unreachable - rescued, E11_NO_FARKAS, scope_note, **extra)


def _denominators(rows: Sequence[Dict[str, Any]],
                  wider: Dict[str, Any]) -> Dict[str, Any]:
    """The two denominators the number 639 is quoted against, side by side.

    `ENGINE_TABLE.md` publishes `lp.incomplete = 639 / 2189`, where 2189 is every
    genuinely unreachable world.  The paper writes "of **639 silences**, 638 are
    still infeasible ...", using 639 itself as the denominator.  Both sentences
    can be true at once, but only if the 639 in each is the same set of worlds.

    What this function can and cannot establish is written into the output rather
    than implied, because an earlier version published `same_set_of_worlds: true`
    off a subset test on a one-element list -- a predicate that also returns true
    for the empty list and that `_wider_box` guarantees by construction, since it
    selects its `silent` set with the identical predicate used here.  It could
    not fail.  It has been removed rather than repaired: no set-identity check is
    *possible* from inside this module, which computes one 639 and quotes it
    twice.

    The reading hazard below is a different matter and stands: the engine is
    silent on 1450 worlds, not 639.
    """
    unreachable = [r for r in rows if r["reachable"] is False]
    all_silences = [r for r in rows if not r["certificate_issued"]]
    silent_unreachable = [r for r in unreachable if _is_no_linear_pagoda(r)]
    silent_reachable = [r for r in all_silences if r["reachable"] is True]

    numerator_ids = sorted(r["i"] for r in silent_unreachable)
    ids_blob = "\n".join(str(i) for i in numerator_ids)

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
        "set_identity": {
            "checked_here": False,
            "established": (
                "There is one computed set: the %d worlds that are goal-"
                "unreachable by exhaustive BFS and on which the engine returned "
                "no_linear_pagoda. Both published sentences are evaluated "
                "against that one set -- the registry's %d / %d and the paper's "
                "'of %d silences' -- so within this artefact they refer to the "
                "same worlds by construction."
                % (len(silent_unreachable), len(silent_unreachable),
                   len(unreachable), len(silent_unreachable))),
            "not_established": (
                "That this set is E11 §6's set. E11 published a count and no "
                "world list, so there are no ids to compare against and no check "
                "inside this module can perform that comparison. It is an open "
                "gap, not a passed test. A previous version reported "
                "`same_set_of_worlds: true` from a tautology; the field is gone."),
            "numerator_world_ids_sha256": hashlib.sha256(
                ids_blob.encode("utf-8")).hexdigest(),
            "numerator_world_ids_sha256_note": (
                "sha256 of the sorted decimal indices joined by '\\n'. Published "
                "so that any future recomputation -- or any artefact that does "
                "list its worlds -- can be compared against this run, which is "
                "the check that was missing."),
        },
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

    Both numerators are counted **directly**, each from its own predicate over
    the same rows.  The previous version computed `old = new + extra` and
    double-counted, because the `extra` worlds -- undecided and unreachable --
    were already inside `new` under the collapsed predicate.  Deriving one count
    from the other is what made that possible; they are independent tallies now.
    """
    unreachable = [r for r in rows if r["reachable"] is False]
    differ = [r for r in rows
              if _old_rule_no_certificate(r) != _is_no_linear_pagoda(r)]

    new = _incompleteness(rows)
    old_numerator = sum(1 for r in unreachable if _old_rule_no_certificate(r))
    old_pct = _pct(old_numerator, new["denominator"])
    return {
        "commit": CALIBER_COMMIT,
        "what_changed": (
            "`if not result.success: return None` became `only HiGHS status 2 "
            "returns None; 1/3/4 raise LpUnavailable`. The LP handed to HiGHS is "
            "unchanged: moves_from_graph, _occupancy, check_exactly, Move, "
            "Certificate.holds and the constraint-matrix construction are "
            "byte-identical between 2a1c30d^ and HEAD, and the added "
            "`options=dict(solver_options) if solver_options else None` is None "
            "at the default, which is scipy's own default. What did change is "
            "the whole post-linprog branch -- the status table, the LpOutcome "
            "return and the success/status contradiction check -- i.e. the "
            "classification of one solve, not the solve."
        ),
        "old_rule_predicate": "solver_status != 0 and not certificate_error",
        "new_rule_predicate": "engine_status == 'no_linear_pagoda'",
        "counted": "each numerator from its own predicate over the same rows; "
                   "neither is derived from the other",
        "solver_status_histogram": dict(sorted(
            Counter("null" if r["solver_status"] is None else str(r["solver_status"])
                    for r in rows).items())),
        "worlds_where_the_rules_differ": len(differ),
        "of_those_truly_unreachable": sum(1 for r in differ
                                          if r["reachable"] is False),
        "old_rule_numerator": old_numerator,
        "old_rule_denominator": new["denominator"],
        "old_rule_pct": old_pct,
        "delta_numerator": old_numerator - new["numerator"],
        "delta_pct": round((old_pct or 0.0) - (new["pct"] or 0.0), 1),
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

def _load_old_potential(directory: str) -> Tuple[Any, str]:
    """Materialise `2a1c30d^:.../potential.py` in `directory` and import it.

    Scratch only: nothing under `engines/` is written or shadowed, and the module
    is loaded by path under a private name so it cannot be picked up by an
    ordinary import.  It has no engine-local imports (math, dataclasses,
    fractions, typing, numpy, scipy), which is what makes this cheap.  The
    caller owns `directory` and removes it.
    """
    import importlib.util

    rev = "%s^:%s" % (CALIBER_COMMIT, OLD_POTENTIAL_PATH)
    source = subprocess.run(
        ["git", "show", rev],
        cwd=str(_common.repo_root()), capture_output=True, check=True,
    ).stdout
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
    absent the reason is reported rather than swallowed.  The scratch directory
    is removed on every path, including the failing ones -- it used to leak one
    per invocation.
    """
    directory = tempfile.mkdtemp(prefix="e18-old-lp-")
    try:
        try:
            old, path = _load_old_potential(directory)
        except Exception as exc:                        # pragma: no cover
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
            "scratch_path_kind": "tempfile.mkdtemp (not under engines/), removed "
                                 "before this function returns",
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
    finally:
        shutil.rmtree(directory, ignore_errors=True)


# -------------------------------------------------------------------- compute

def compute(n: int = DEFAULT_N, verify_old_code: bool = False,
            jsonl_path: Optional[str] = None,
            wider_box: bool = True,
            exact: bool = True) -> Dict[str, Any]:
    """Recompute `lp.incomplete` and its dependants, in `result` shape.

    Five registry-adjacent facts, not one, because a parallel census found that
    of the 87 E11-sourced facts only two reach the paper body and both are this
    engine's:

    * `lp.incomplete`     = 639 / 2189 -- the headline (`value`)
    * `lp.no_farkas`      = 638 -- the paper's Farkas-dual limitation
    * the bound triple    -- "638 still infeasible at 100, 10^4, 10^6", which has
                             no `ENGINE_TABLE.md` registry key at all
    * both denominators the number 639 is quoted against
    * `no_pagoda_exact`   -- new: the same 638, proved infeasible in exact
                             rationals with no weight box, one Farkas certificate
                             per world
    """
    rows = survey(n)
    if jsonl_path:
        write_jsonl(rows, jsonl_path)

    # One guard, applied everywhere a comparison against E11's N=3000 prose
    # happens.  A bare `false` at `--n 500` means "different corpus", not
    # "different answer", and publishing it is the hazard this note removes.
    scope_note = None if n == DEFAULT_N else (
        "E11's prose is an N=%d number; this run is N=%d, so `agrees` is null "
        "-- a different corpus, not a different answer. The N=%d comparison "
        "that IS meaningful lives in counts.slice_500.agrees_with_e11."
        % (DEFAULT_N, n, SLICE_N)
    )

    incompleteness = _incompleteness(rows)
    verified = _verify_old_code(rows) if verify_old_code else None
    caliber = _caliber(rows, verified)
    wider = _wider_box(rows, scope_note) if wider_box else None
    exact_result = _no_pagoda_exact(rows, wider) if exact else None

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
            "is only meaningful at the default N=%d (this run: N=%d). The same "
            "guard is applied to counts.wider_box and counts.no_farkas."
            % (DEFAULT_N, n)
        ),
        "e11_prose_in_scope": n == DEFAULT_N,
        "base_rates": _base_rates(rows),
        "incompleteness": incompleteness,
        "slice_500": _slice_500(rows),
        "pre_2a1c30d": caliber,
        # --- the paper-body facts that hang off the same 639 ---
        "wider_box": wider if wider is not None else {
            "ran": False,
            "reason": "wider_box=False; the bound triple was not recomputed",
        },
        "no_farkas": _no_farkas(rows, wider, exact_result, scope_note)
        if wider is not None else {
            "recomputed": None,
            "e11_prose": E11_NO_FARKAS,
            "agrees": None,
            "reason": "needs the wider-box sweep; run with wider_box=True",
        },
        "no_pagoda_exact": exact_result if exact_result is not None else {
            "ran": False,
            "reason": "exact=False; the exact rational re-decision was skipped",
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
            "certificate_errors": sum(1 for r in rows if r["certificate_error"]),
            "solver_did_not_decide": sum(
                1 for r in rows
                if not _is_no_linear_pagoda(r)
                and r["engine_status"] != potential.CERTIFIED),
            "reachability_undetermined": sum(1 for r in rows if r["reachable"] is None),
            "unreachable_worlds_unaccounted": (
                0 if incompleteness["accounted"] else 1),
            "wider_box_solves_that_failed": (
                None if wider is None else wider["solve_failed"]["count"]),
            "exact_farkas_certificates_unverified": (
                None if exact_result is None
                else len(exact_result["farkas_certificates_unverified"])),
            "exact_contradictions_with_highs": (
                None if exact_result is None
                else len(exact_result["contradictions_with_highs"])),
            "exact_disagrees_with_box_blocked": (
                None if exact_result is None
                or not exact_result["agrees_with_box_blocked"]["checked"]
                else int(not exact_result["agrees_with_box_blocked"]["identical"])),
            "exact_engine_system_mismatches": (
                None if exact_result is None
                else len(exact_result["engine_system_differs_from_spec_triples"])),
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
            "on what fraction does lp_potential return no_linear_pagoda?"
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
            "their agreement checked. Numerator = unreachable worlds whose status "
            "word is 'no_linear_pagoda' (HiGHS status 2) -- not 'certificate is "
            "None', which is also true of an undecided solve; every undecided "
            "outcome is counted apart in counts.incompleteness.set_apart. "
            "Denominator = unreachable worlds."
            % (DEFAULT_N - 1)
        ),
        caveats=[
            "NUMERATOR PREDICATE (changed 2026-07-30): the ratio counts the "
            "status word `no_linear_pagoda`, not `certificate is None`. The "
            "earlier version of this module used the collapsed predicate that "
            "2a1c30d exists to remove, so a HiGHS iteration limit would have "
            "been published as a fact about the world -- inside the audit "
            "written to check that very rule. On this corpus the two readings "
            "coincide exactly (lp_unavailable = %d, certificate_error = %d), so "
            "the published %d is unmoved; counts.incompleteness."
            "collapsed_reading_would_be = %d records that they still agree."
            % (counts["integrity"]["lp_unavailable"],
               counts["integrity"]["certificate_errors"],
               incompleteness["numerator"],
               incompleteness["collapsed_reading_would_be"]),
            "CALIBER (%s): the code path that produced E11's 29.2%% was rewritten "
            "after the E11 run. `if not result.success: return None` became `only "
            "HiGHS status 2 returns None; statuses 1/3/4 raise LpUnavailable`, and "
            "E15 (99204472, d2b75c26, af884509) then widened the same seam into "
            "LpOutcome without changing the decision rule. The number above is "
            "measured on today's code and is the number of record. "
            "counts.pre_2a1c30d measures the old rule from the same solver "
            "statuses, each numerator counted from its own predicate rather than "
            "derived from the other: old %s/%s = %s%%, new %s/%s = %s%%, delta "
            "%+d world(s) in the numerator. HiGHS returned status 1/3/4 on %d of "
            "%d worlds, which is the only place the two rules can differ.%s"
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
            "engine's verdict. scipy %s, numpy %s, Python %d.%d.%d. E11 ran scipy "
            "1.17.1, numpy 2.4.4, Python 3.13.13; a HiGHS behaviour change would "
            "move this number. It would no longer be invisible from inside this "
            "script -- counts.no_pagoda_exact re-decides the same worlds without "
            "a solver at all -- but the *engine's* verdict, and therefore "
            "lp.incomplete itself, still rests on HiGHS alone."
            % (scipy.__version__, numpy.__version__, *sys.version_info[:3]),
            "SHARED DEPENDENCY: fuzzlab.worlds.jumpgraph.generate produces both "
            "the truth and the engine's input (E11 §2.1). A generator that only "
            "emitted easy geometries would flatter both sides.",
            "SHARED DEPENDENCY: the (src, over, dst) peg-jump convention is "
            "hard-coded in Move.delta, jumpgraph.apply, fuzzlab/props and in "
            "_successors here -- four copies of one rule (E11 §2.2). If the "
            "convention is wrong they are all wrong together.",
            "SCOPE: n_pos <= 9 (jumpgraph.MAX_POSITIONS), so <= 512 states per "
            "world and the exhaustive BFS is what buys the truth. The "
            "silence-vs-n_pos trend is decreasing over 4..9; extrapolating past 9 "
            "is unjustified in either direction.",
            "The E11 partial's own numbers were independently reproduced by the "
            "E15 census (runs/20260729T044500Z-E15-solver-status-bit/SUMMARY.json) "
            "on post-2a1c30d code, and again by the 2026-07-30 adversarial "
            "recount in runs/20260730T120000Z-E18/adversarial/"
            "independent_recount.json, which flipped every methodological choice "
            "(BFS over graph['edges'] and over moves_from_graph rather than "
            "spec.triples; its own BFS rather than fuzzlab.oracles.search) and "
            "got 2189/811/1550/1450/639 with zero disagreements. This module is a "
            "third, differently-plumbed reading, not a copy of either.",
            "BYTE-STABILITY: `run_all.py` writes these files with newline='\\n' "
            "and ensure_ascii=False, and they are byte-identical across reruns. "
            "The CLI in this module's header writes to stdout instead, where "
            "Windows text mode inserts CRLF and json.dump escapes non-ASCII, so "
            "`python -m tools.survey_numbers.lp_incomplete > f` and run_all "
            "produce byte-different files with identical content. Compare via "
            "run_all, or parse before diffing.",
        ] + ([] if wider is None else [
            "UNREGISTERED, NOT MISCITED (finding, not a caveat about this run): "
            "PAPER.md §10.5 and papers/phase1-workshop/sections/"
            "10_adjudication.md:289 state that of the 639 silences '638 are still "
            "infeasible at bounds of 100, 10^4 and 10^6'. ENGINE_TABLE.md has no "
            "registry key for that triple -- its lp.* keys are incomplete, "
            "incomplete_of_all, no_farkas, box_blocked and weight_bound=10 -- and "
            "the sentence cites no artefact of its own, attributing itself to a "
            "reviewer's re-derivation whose write-up is prose (the E11 partial, "
            "lines 275-277). So before E18 the three numbers were in the paper "
            "with no registry entry and no script. (An earlier version of this "
            "module called this a BAD CITATION, reading the parenthetical "
            "'(engine-rig/ENGINE_TABLE.md)' as attached to the bound sentence. It "
            "is attached to the item heading -- lp_potential's 29.2 %% "
            "incompleteness rate -- which ENGINE_TABLE.md does publish verbatim "
            "as lp.incomplete. §10.5 uses that heading-plus-artefact form for "
            "every entry. The miscitation claim was wrong and is withdrawn.) The "
            "claim itself recomputes exactly (%s): %s."
            % (wider["still_infeasible_at_all_three"]["recomputed"],
               ", ".join("bound=%s -> %d still infeasible"
                         % (t["bound"], t["still_infeasible"])
                         for t in sorted(wider["bounds"].values(),
                                         key=lambda d: d["bound"]))),
            "ONE CLAIM, NOT THREE: the per-bound sweep is a solver-consistency "
            "check, not three separate questions being settled. The constraint "
            "system is homogeneous apart from the goal margin and the box only "
            "widens, so a w feasible at |w| <= B is feasible at every larger B, "
            "and infeasibility at 10^6 entails it at 10^4 and at 100. Equal "
            "counts across the three bounds are forced unless HiGHS contradicts "
            "itself. E11 reporting one number for all three was not a defect, and "
            "an earlier version of this module implying otherwise was over-"
            "claiming.",
            "DENOMINATOR: 639 is quoted against two different denominators. "
            "ENGINE_TABLE's lp.incomplete is 639/2189 (2189 = genuinely "
            "unreachable worlds); the paper's 'of 639 silences' reuses the "
            "numerator as a denominator. Both sentences are true of the one set "
            "this module computes, and counts.denominators_for_639.set_identity "
            "says exactly that -- and says that whether this set is E11 §6's set "
            "is NOT checked, because E11 published no world list. The engine is "
            "silent on 1450 worlds, not 639; the other 811 silences are reachable "
            "worlds the engine correctly declines to certify. A reader who reads "
            "639 as the silence count is off by 2.3x.",
            "BOX-BLOCKED IS STATUS 0 ONLY (changed 2026-07-30): a solve that "
            "*fails* at a wider bound no longer enters lp.box_blocked and is no "
            "longer subtracted from lp.no_farkas. Failures are reported in "
            "counts.wider_box.solve_failed (%d on this corpus). The earlier "
            "version counted an LpUnavailable or a CertificateError at bound=10^6 "
            "as 'the box was doing the refusing', which is the same collapse "
            "2a1c30d removed from the engine; CertificateError was the live risk, "
            "since Fraction(float(v)).limit_denominator(1000) on weights near "
            "10^6 fails exact re-checking far more readily than at |w| <= 10."
            % wider["solve_failed"]["count"],
        ]) + ([] if exact_result is None else [
            "EXACT, AND STRONGER THAN THE PAPER: counts.no_pagoda_exact re-decides "
            "the %d numerator worlds with an exact rational Phase-1 simplex "
            "(Bland's rule, Fraction throughout, NO weight box) and emits a "
            "Farkas multiplier vector per infeasible world, re-checked from the "
            "constraint matrix alone. Result: %d exactly infeasible with %d "
            "verified certificates, %d exactly feasible. For those %d worlds, "
            "'no linear pagoda exists' is now a proof and holds at ANY weight "
            "magnitude, not merely within |w| <= 10^6. lp.no_farkas = %s is "
            "deliberately NOT overwritten: it is the paper's count of what E11 "
            "left unproved, and the paper has to stay checkable against it. "
            "Controls: %d certified worlds must come back exactly feasible (%s) "
            "and %d reachable worlds must come back exactly infeasible (%s), the "
            "second being the soundness direction."
            % (exact_result["probed"],
               exact_result["exactly_infeasible_unbounded"],
               exact_result["farkas_certificates_verified"],
               exact_result["exactly_feasible_unbounded"],
               exact_result["exactly_infeasible_unbounded"],
               E11_NO_FARKAS,
               exact_result["controls"]["certified_worlds"]["worlds"],
               "passed" if exact_result["controls"]["certified_worlds"]["passed"]
               else "FAILED",
               exact_result["controls"]["reachable_worlds"]["worlds"],
               "passed" if exact_result["controls"]["reachable_worlds"]["passed"]
               else "FAILED"),
            "EXACT vs HiGHS: the %d world(s) the exact simplex finds feasible are "
            "not a contradiction of the engine. HiGHS searched |w| <= 10 and the "
            "witness needs a weight of magnitude %s, so both are right and the "
            "gap is the engine's documented incompleteness. A contradiction "
            "would be an exact witness that fits inside the box; there are %d of "
            "those. The same world set comes back from the wider-box sweep as "
            "lp.box_blocked, computed by different code over a different move "
            "list: identical = %s."
            % (exact_result["exactly_feasible_unbounded"],
               ", ".join(w["max_abs_weight"]
                         for w in exact_result["feasible_witnesses"]) or "n/a",
               len(exact_result["contradictions_with_highs"]),
               exact_result["agrees_with_box_blocked"].get("identical")),
            "EXACT: WHAT IT DOES NOT COVER. The exact system is built from "
            "spec.triples and spec.goal_states; the engine's LP is built from "
            "graph['edges'] via moves_from_graph. The two are checked for "
            "identity per world (integrity.exact_engine_system_mismatches = %s), "
            "so the proof transfers -- but it is a check on this corpus, not a "
            "theorem about the generator. The exact simplex also decides only the "
            "unboxed question: it can prove no pagoda exists at any magnitude, "
            "and it says nothing about which bound the engine should use."
            % counts["integrity"]["exact_engine_system_mismatches"],
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
    parser.add_argument(
        "--no-exact", action="store_true",
        help="skip counts.no_pagoda_exact (the exact rational Phase-1 simplex). "
             "It is ON by default and costs about half the run; the default path "
             "-- and therefore verify.py rung 4 -- exercises it.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = _parse_args(argv)
    _common.main(lambda: compute(
        n=args.n,
        verify_old_code=args.verify_old_code,
        jsonl_path=args.jsonl,
        exact=not args.no_exact,
    ))


if __name__ == "__main__":
    main()
