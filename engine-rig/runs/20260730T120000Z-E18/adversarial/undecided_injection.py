"""Attack lines 3 and 5: what the module does when HiGHS *does* return 1/3/4.

Run: cd engine-rig && python runs/20260730T120000Z-E18/adversarial/undecided_injection.py

On this corpus the solver-status histogram is {0: 1550, 2: 1450}, so every branch
that handles an undecided solve is dead code and none of it has ever executed.
This probe executes it, three ways:

A. Synthetic rows fed to `_incompleteness` and `_caliber`.  No solver involved --
   the rows are exactly the shape `survey()` emits.
B. A real HiGHS iteration limit, driven through `potential.solve` with
   `solver_options={"maxiter": 1}`, so the status word is genuinely produced by
   the solver rather than asserted.
C. The same real undecided outcome injected into `_wider_box`, to see whether a
   solve that *failed* at a wider bound is counted as a world the box was
   blocking -- which is the thing 2a1c30d exists to prevent.
"""

import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE_RIG = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
REPO = os.path.dirname(ENGINE_RIG)
for p in (REPO, ENGINE_RIG):
    if p not in sys.path:
        sys.path.insert(0, p)

from tools.survey_numbers import lp_incomplete as L    # noqa: E402
from engines import lp_potential                       # noqa: E402
from engines.lp_potential import potential             # noqa: E402
from fuzzlab import prng                               # noqa: E402
from fuzzlab.worlds import jumpgraph                   # noqa: E402


def row(i, *, reachable, certificate_issued, solver_status,
        engine_status, certificate_error=False):
    return {
        "i": i, "seed": 1000 + i, "n_pos": 5, "n_goals": 1, "n_triples": 5,
        "reachable": reachable, "bfs_exhausted": True, "states_enumerated": 4,
        "oracles_agree": True,
        "certificate_issued": certificate_issued,
        "certificate_error": certificate_error,
        "engine_status": engine_status,
        "solver_status": solver_status,
        "lp_unavailable": engine_status == potential.UNDECIDED,
        "run_vs_decide_disagreement": False,
    }


def part_a():
    """Ten unreachable worlds: 4 certified, 3 status-2, 3 status-1 (budget)."""
    rows = []
    rows += [row(i, reachable=False, certificate_issued=True, solver_status=0,
                 engine_status=potential.CERTIFIED) for i in range(4)]
    rows += [row(4 + i, reachable=False, certificate_issued=False, solver_status=2,
                 engine_status=potential.NO_LINEAR_PAGODA) for i in range(3)]
    # the three that have never happened: HiGHS hit its iteration limit.
    rows += [row(7 + i, reachable=False, certificate_issued=False, solver_status=1,
                 engine_status=potential.BUDGET) for i in range(3)]

    inc = L._incompleteness(rows)
    cal = L._caliber(rows, None)
    return {
        "corpus": "10 unreachable worlds: 4 certified(st 0), 3 infeasible(st 2), "
                  "3 iteration-limit(st 1)",
        "truth": {
            "old_rule_numerator (status != 0)": 6,
            "new_rule_numerator (status == 2 only)": 3,
            "correct_delta": 3,
        },
        "module_says": {
            "_incompleteness.numerator": inc["numerator"],
            "_caliber.old_rule_numerator": cal["old_rule_numerator"],
            "_caliber.worlds_where_the_rules_differ":
                cal["worlds_where_the_rules_differ"],
            "_caliber.delta_numerator": cal["delta_numerator"],
        },
        "verdict": {
            "new_numerator_wrongly_includes_undecided":
                inc["numerator"] != 3,
            "old_numerator_double_counts": cal["old_rule_numerator"] != 6,
            "old_numerator_overshoot": cal["old_rule_numerator"] - 6,
        },
        "note": (
            "_incompleteness counts `not certificate_issued`, the collapsed "
            "two-valued predicate; a status-1 world therefore lands in the "
            "'engine is silent because no linear pagoda exists' numerator. "
            "_caliber then adds the same worlds again as `extra`."
        ),
    }


def _real_undecided():
    """Drive HiGHS into a genuine non-{0,2} status and report the outcome."""
    out = []
    for i in range(40):
        seed = prng.derive(L.CAMPAIGN_SEED, "jumpgraph", i)
        w = jumpgraph.generate(seed)
        for maxiter in (0, 1):
            try:
                o = potential.solve(w.graph, w.spec.initial,
                                    solver_options={"maxiter": maxiter})
                status, ss, exc = o.status, o.solver_status, None
            except potential.LpUnavailable as e:
                got = getattr(e, "outcome", None)
                status = "raised LpUnavailable"
                ss = None if got is None else got.solver_status
                exc = str(e)[:160]
            except potential.CertificateError as e:
                status, ss, exc = "CertificateError", None, str(e)[:160]
            if ss not in (0, 2):
                out.append({"i": i, "maxiter": maxiter, "status": status,
                            "solver_status": ss, "exception": exc})
        if len(out) >= 3:
            break
    return out


def part_c(real):
    """Inject a real undecided outcome into `_wider_box` for one silent world."""
    # index 2302 is the one world the widened box rescues; pick a plain silent
    # world instead so the injection is not confounded with the rescue.
    target = None
    for i in range(200):
        seed = prng.derive(L.CAMPAIGN_SEED, "jumpgraph", i)
        w = jumpgraph.generate(seed)
        try:
            o = potential.solve(w.graph, w.spec.initial)
        except Exception:
            continue
        if o.status == potential.NO_LINEAR_PAGODA:
            # unreachable?
            from collections import deque
            seen = {w.spec.initial}
            q = deque([w.spec.initial])
            while q:
                s = q.popleft()
                for t in jumpgraph.successors(s, w.spec.triples):
                    if t not in seen:
                        seen.add(t)
                        q.append(t)
            if not (set(w.spec.goal_states) & seen):
                target = (i, seed, len(seen))
                break
    if target is None:
        return {"ran": False, "reason": "no silent unreachable world in first 200"}

    i, seed, reach = target
    rows = [{
        "i": i, "seed": seed, "n_pos": 0, "reachable": False,
        "certificate_issued": False, "states_enumerated": reach,
        "certificate_error": False, "solver_status": 2,
        "engine_status": potential.NO_LINEAR_PAGODA,
        "lp_unavailable": False, "run_vs_decide_disagreement": False,
    }]

    real_decide = lp_potential.decide

    def flaky_decide(graph, initial, **kw):
        if kw.get("bound") == 10 ** 6:
            raise potential.LpUnavailable(
                "injected: HiGHS hit its iteration limit",
                potential.LpOutcome(status=potential.BUDGET, solver_status=1,
                                    solver_message="injected", bound=10 ** 6,
                                    margin=1),
            )
        return real_decide(graph, initial, **kw)

    L.lp_potential.decide = flaky_decide
    try:
        wider = L._wider_box(rows)
        farkas = L._no_farkas(rows, wider)
        denom = L._denominators(rows, wider)
    finally:
        L.lp_potential.decide = real_decide

    table = {k: {kk: vv for kk, vv in v.items() if kk != "feasible_worlds"}
             for k, v in wider["bounds"].items()}
    return {
        "ran": True,
        "world": {"i": i, "seed": seed, "reachable_set": reach},
        "injection": "lp_potential.decide raises LpUnavailable(BUDGET) at bound=10**6 only",
        "bounds_table": table,
        "still_infeasible_at_all_three": wider["still_infeasible_at_all_three"]["recomputed"],
        "box_blocked_recomputed": wider["box_blocked"]["recomputed"],
        "box_blocked_worlds": wider["box_blocked"]["worlds"],
        "no_farkas_recomputed": farkas["recomputed"],
        "same_set_of_worlds": denom["same_set_of_worlds"],
        "verdict": {
            "a_failed_solve_was_counted_as_box_blocked":
                wider["box_blocked"]["recomputed"] == 1,
            "no_farkas_was_decremented_by_a_solver_failure":
                farkas["recomputed"] == 0,
            "bounds_table_undecided_field_at_1e6":
                wider["bounds"]["1000000"]["undecided"],
            "bounds_table_status_counts_at_1e6":
                wider["bounds"]["1000000"]["status_counts"],
        },
        "note": (
            "box_blocked is documented as 'silent-and-unreachable worlds that "
            "stop being silent once the weight box is widened -- the box, not "
            "the mathematics, was doing the refusing'. An LpUnavailable is not "
            "that. `_no_farkas` then subtracts it from 639."
        ),
    }


def part_d():
    """Attack line 6: is `same_set_of_worlds` a set-identity check?"""
    rows = [row(i, reachable=False, certificate_issued=False, solver_status=2,
                engine_status=potential.NO_LINEAR_PAGODA) for i in range(5)]
    # a wider-box result whose box_blocked list is EMPTY
    fake_wider = {"box_blocked": {"recomputed": 0, "worlds": []},
                  "still_infeasible_at_all_three": {"recomputed": 5}}
    d = L._denominators(rows, fake_wider)
    # and one whose box_blocked list is a world NOT in the numerator
    fake_wider2 = {"box_blocked": {"recomputed": 1,
                                   "worlds": [{"i": 99999}]},
                   "still_infeasible_at_all_three": {"recomputed": 5}}
    d2 = L._denominators(rows, fake_wider2)
    return {
        "what_the_field_compares": (
            "set(w['i'] for w in wider['box_blocked']['worlds']) <= "
            "set(r['i'] for r in silent_unreachable)"
        ),
        "with_empty_box_blocked_list": d["same_set_of_worlds"],
        "with_a_box_blocked_world_outside_the_numerator": d2["same_set_of_worlds"],
        "verdict": (
            "`same_set_of_worlds` is a subset test on the 1-element box_blocked "
            "list, not on the two 639s. It is True for the empty list, so on the "
            "real corpus it is a test that {2302} is one of the 639 -- which "
            "_wider_box guarantees by construction, since it selects `silent` "
            "with the identical predicate _denominators uses. It can never fail "
            "on real data and is therefore not evidence for claim D."
        ),
    }


def main():
    real = _real_undecided()
    out = {
        "A_synthetic_rows": part_a(),
        "B_real_iteration_limit": {
            "found": real,
            "note": ("scipy/HiGHS with maxiter=0/1 on these tiny LPs; empty list "
                     "means HiGHS refuses to be starved on this corpus, which is "
                     "itself evidence for how unreachable statuses 1/3/4 are here"),
        },
        "C_wider_box_with_an_injected_undecided": part_c(real),
        "D_same_set_of_worlds": part_d(),
    }
    json.dump(out, sys.stdout, indent=2, sort_keys=True, default=str)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
