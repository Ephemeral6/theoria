"""Mutation testing against the DELIVERED harness's own self-checks.

Every mutant is applied by monkeypatching at run time; no delivered file is
edited.  For each mutant we ask three questions:

  1. does `heldout/run.py` notice (either of its two pre-registered gates, or the
     bare `except Exception` that exits 3)?
  2. do the headline numbers move -- i.e. would a reader see anything?
  3. is the mutant inside `heldout/`?  If so `python -m pytest` cannot possibly
     catch it: no file under `tests/` imports the package (verified by grep).

The lp_potential mutants run on a reduced corpus (n in {4,5}) so that twelve
mutants finish; the baseline is recomputed at the same scale, so the comparison
is like for like.
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from engines.zero_space import gf2, zerospace
from engines.lp_potential.potential import (
    CertificateError, LpUnavailable, Move, heuristic_from, solve_certificate,
)
from engines import lp_potential
from heldout import parityworld, peg, split as hsplit
from heldout import zero_space_heldout as zsh
from heldout import lp_potential_heldout as lph

LP_N = (4, 5)

_orig = {
    "split.random_transition_split": hsplit.random_transition_split,
    "split.leave_one_operation_out": hsplit.leave_one_operation_out,
    "zsh.fit": zsh.fit,
    "zsh.fit_matches_engine": zsh.fit_matches_engine,
    "zsh.score": zsh.score,
    "peg.graph_minus_geometry": peg.graph_minus_geometry,
    "peg.matches_fixture_peg4": peg.matches_fixture_peg4,
    "lph._admissibility_on_heldout": lph._admissibility_on_heldout,
    "parityworld.build": parityworld.build,
    "lph.held_out_case": lph.held_out_case,
}


def restore():
    hsplit.random_transition_split = _orig["split.random_transition_split"]
    hsplit.leave_one_operation_out = _orig["split.leave_one_operation_out"]
    zsh.fit = _orig["zsh.fit"]
    zsh.fit_matches_engine = _orig["zsh.fit_matches_engine"]
    zsh.score = _orig["zsh.score"]
    peg.graph_minus_geometry = _orig["peg.graph_minus_geometry"]
    peg.matches_fixture_peg4 = _orig["peg.matches_fixture_peg4"]
    lph._admissibility_on_heldout = _orig["lph._admissibility_on_heldout"]
    parityworld.build = _orig["parityworld.build"]
    lph.held_out_case = _orig["lph.held_out_case"]


# ------------------------------------------------------------------ measuring

def zs_measure():
    """Reproduces run.zero_space_section()'s headline numbers and its gate."""
    try:
        worlds = parityworld.corpus()
    except Exception as exc:                       # run.py's `except Exception`
        return {"EXIT": 3, "why": repr(exc)}
    gate_failures = [w.world_id for w in worlds if not zsh.fit_matches_engine(w)]
    tally = Counter()
    for w in worlds:
        try:
            tr, ho = hsplit.random_transition_split(len(w.actions), w.seed)
            o = zsh.run_s1(w)
        except Exception as exc:
            return {"EXIT": 3, "why": repr(exc)}
        for law in o.laws:
            tally["S1/%s/laws" % law.scope] += 1
            tally["S1/%s/hit" % law.scope] += int(law.delta_hit)
        for o in zsh.run_s2(w):
            for law in o.laws:
                tally["S2/%s/laws" % law.scope] += 1
                tally["S2/%s/hit" % law.scope] += int(law.delta_hit)

    def r(p):
        return ("n/a" if not tally[p + "/laws"]
                else "%.1f" % (100.0 * tally[p + "/hit"] / tally[p + "/laws"]))

    return {"EXIT": 1 if gate_failures else 0,
            "gate_failures": len(gate_failures),
            "S1_global": r("S1/global"), "S2_global": r("S2/global"),
            "S2_local": r("S2/cell_local"),
            "S2_global_laws": tally["S2/global/laws"]}


def lp_measure():
    try:
        gate_ok, _ = peg.matches_fixture_peg4()
    except Exception as exc:
        return {"EXIT": 3, "why": repr(exc)}
    certs = inv = false = letthrough = silent = 0
    viol = 0
    try:
        for n in LP_N:
            for gi in range(1, n - 1):
                goal = "".join("1" if i == gi else "0" for i in range(n))
                full = peg.graph(n, goal)
                gs = peg.geometries(full)
                for inst in lph.instances(n, full, goal):
                    for g in gs:
                        c = lph.held_out_case(inst, full, g)
                        if c.outcome == "silent":
                            silent += 1
                            continue
                        if c.outcome != "certificate":
                            continue
                        certs += 1
                        inv += int(bool(c.heldout_inv_closed))
                        false += int(c.claim_true is False)
                        letthrough += int(not c.gate_withholds)
                        viol += c.admissibility_violations or 0
    except Exception as exc:
        return {"EXIT": 3, "why": repr(exc)}
    return {"EXIT": 0 if gate_ok else 1, "fixture_gate_ok": gate_ok,
            "certs": certs, "silent": silent,
            "inv_rate": "n/a" if not certs else "%.1f" % (100.0 * inv / certs),
            "false": false, "gate_let_through": letthrough,
            "heldout_violations": viol}


# ------------------------------------------------------------------- mutants

def m_split_overlap():
    """M1: train and test overlap by 12 transitions; the asserts are gone too."""
    def bad(n_transitions, world_seed):
        order = hsplit.shuffled(range(n_transitions), world_seed ^ hsplit.SPLIT_SALT)
        cut = (n_transitions * 7) // 10
        return sorted(order[:cut]), sorted(order[cut - 12:])
    hsplit.random_transition_split = bad


def m_fit_leaks_all():
    """M2: `fit` ignores `train` entirely and fits on every transition."""
    real = _orig["zsh.fit"]
    def bad(encoded, features, train):
        return real(encoded, features, range(len(encoded) - 1))
    zsh.fit = bad


def m_fit_leaks_one():
    """M3: `fit` sneaks the first held-out difference into the training set."""
    real = _orig["zsh.fit"]
    def bad(encoded, features, train):
        train = list(train)
        missing = [t for t in range(len(encoded) - 1) if t not in train]
        return real(encoded, features, train + missing[:1])
    zsh.fit = bad


def m_score_checks_train():
    """M4: the re-check iterates the TRAIN transitions instead of the held-out ones."""
    real = _orig["zsh.score"]
    def bad(world, train, heldout, split_name, variant=""):
        return real(world, train, list(train), split_name, variant)
    zsh.score = bad


def m_gate_always_true():
    """M5: `fit_matches_engine` always passes."""
    zsh.fit_matches_engine = lambda world: True


def m_loo_leaks():
    """M6: leave-one-operation-out trains on everything, asserts removed."""
    def bad(actions, operation):
        return list(range(len(actions))), [t for t, a in enumerate(actions)
                                           if a == operation]
    hsplit.leave_one_operation_out = bad


def m_no_coverage():
    """M7: parityworld.build drops the 'every operation is witnessed' guarantee."""
    from common.rng import SplitMix64
    from heldout.parityworld import COLORS, ParityWorld, apply, operations_for
    def bad(n_cells, width, seed, n_transitions=parityworld.N_TRANSITIONS):
        ops = operations_for(n_cells, width)
        rng = SplitMix64(seed)
        initial = tuple(COLORS[rng.below(2)] for _ in range(n_cells))
        actions = [rng.below(len(ops)) for _ in range(n_transitions)]
        state = initial
        states = [state]
        for a in actions:
            state = apply(state, ops[a])
            states.append(state)
        return ParityWorld(world_id="pw-n%d-k%d-s%08x" % (n_cells, width, seed),
                           n_cells=n_cells, width=width, seed=seed,
                           operations=ops, actions=actions, states=states)
    parityworld.build = bad


def m_op_never_witnessed():
    """M8: an operation is never witnessed (build's own assertion should fire)."""
    real = _orig["parityworld.build"]
    def bad(n_cells, width, seed, n_transitions=parityworld.N_TRANSITIONS):
        w = real(n_cells, width, seed, n_transitions)
        w.actions = [0 if a == len(w.operations) - 1 else a for a in w.actions]
        if set(w.actions) != set(range(len(w.operations))):
            raise AssertionError("not every operation is witnessed in %s" % (seed,))
        return w
    parityworld.build = bad


def m_geometry_not_deleted():
    """M9: graph_minus_geometry keeps the edges it claims to delete."""
    peg.graph_minus_geometry = lambda g, positions: dict(g)


def m_fixture_gate_true():
    """M10: the Fixture C gate always passes."""
    peg.matches_fixture_peg4 = lambda: (True, [])


def m_admissibility_skips():
    """M11: the admissibility scan skips exactly the states that would violate."""
    import math
    def bad(certificate, graph):
        heuristic = heuristic_from(certificate)
        excluded = {certificate.initial, *certificate.goal_states}
        tested = violations = 0
        first = {}
        for state in sorted(graph["distance_to_goal"]):
            d = graph["distance_to_goal"][state]
            if d is None or state in excluded:
                continue
            h = heuristic.value(state)
            if h > d:
                continue                      # <-- the mutation
            tested += 1
        return violations, tested, first
    lph._admissibility_on_heldout = bad


def m_inv_strict():
    """M12: `<=` becomes `<` in the held-out inv_closed scoring."""
    from fractions import Fraction
    real_case = _orig["lph.held_out_case"]
    def bad(instance, graph, withheld):
        c = real_case(instance, graph, withheld)
        if c.outcome == "certificate":
            w = [Fraction(x) for x in c.weights]
            c.heldout_inv_closed = Move(*withheld).delta(w) < 0
        return c
    lph.held_out_case = bad


def m_gate_reads_reduced():
    """M13: the emit-gate probe is handed the graph the LP was actually fitted on.

    Not a defect injected into the harness -- the harness's own premise made
    concrete.  A caller that only ever observed part of the geometry has only the
    reduced graph to pass.
    """
    real_case = _orig["lph.held_out_case"]
    def bad(instance, graph, withheld):
        c = real_case(instance, graph, withheld)
        if c.outcome == "certificate":
            reduced = _orig["peg.graph_minus_geometry"](graph, withheld)
            cert = solve_certificate(reduced, instance.initial,
                                     goal_states=[instance.goal])
            c.gate_withholds = (lp_potential.candidates(
                cert, heuristic_from(cert), reduced) == [])
        return c
    lph.held_out_case = bad


MUTANTS_ZS = [
    ("M1  split.random_transition_split returns overlapping train/test", m_split_overlap),
    ("M2  zsh.fit ignores `train`, fits on all 60 transitions", m_fit_leaks_all),
    ("M3  zsh.fit sneaks ONE held-out difference into the fit", m_fit_leaks_one),
    ("M4  zsh.score re-checks the TRAIN transitions", m_score_checks_train),
    ("M5  fit_matches_engine always returns True", m_gate_always_true),
    ("M6  leave_one_operation_out trains on everything", m_loo_leaks),
    ("M7  parityworld.build drops the coverage guarantee", m_no_coverage),
    ("M8  parityworld.build leaves an operation unwitnessed", m_op_never_witnessed),
]

MUTANTS_LP = [
    ("M9  peg.graph_minus_geometry deletes nothing", m_geometry_not_deleted),
    ("M10 peg.matches_fixture_peg4 always passes", m_fixture_gate_true),
    ("M11 _admissibility_on_heldout skips the violating states", m_admissibility_skips),
    ("M12 held-out inv_closed scored with `< 0` instead of `<= 0`", m_inv_strict),
    ("M13 emit gate handed the reduced graph (the caller's real evidence)", m_gate_reads_reduced),
]


def main():
    restore()
    print("== zero_space baseline ==")
    base = zs_measure()
    print("  ", base)
    for name, fn in MUTANTS_ZS:
        restore()
        fn()
        got = zs_measure()
        moved = {k: (base.get(k), got.get(k)) for k in got
                 if base.get(k) != got.get(k)}
        print("\n%s" % name)
        print("   result :", got)
        print("   moved  :", moved if moved else "NOTHING MOVED")
        print("   run.py exit code:", got["EXIT"],
              "->", "CAUGHT" if got["EXIT"] else "SURVIVES run.py")
    restore()

    print("\n== lp_potential baseline (n in %r) ==" % (LP_N,))
    lbase = lp_measure()
    print("  ", lbase)
    for name, fn in MUTANTS_LP:
        restore()
        fn()
        got = lp_measure()
        moved = {k: (lbase.get(k), got.get(k)) for k in got
                 if lbase.get(k) != got.get(k)}
        print("\n%s" % name)
        print("   result :", got)
        print("   moved  :", moved if moved else "NOTHING MOVED")
        print("   run.py exit code:", got["EXIT"],
              "->", "CAUGHT" if got["EXIT"] else "SURVIVES run.py")
    restore()


if __name__ == "__main__":
    main()
