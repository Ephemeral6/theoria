"""Exhaustive step-equivalence between the baseline and current predictors.

Sampling: NOT a sample. The peg state vector is (pos, alive) per instance over
`N_POS` cells, so the full *representable* space is (N_POS * 2) ** n_instances
— 10,000 states for peg5, 512 for peg4. Every representable state is crossed
with every action in `ACTIONS`, and the two modules' successors (or the
exception they raise) are compared.

Representable, not reachable, on purpose: the reachable set is a few hundred
states and would never visit the guard branches ledger X-5 and the write-set
check touch. The illegal-looking states — two live pegs on one cell, a peg on a
cell another peg jumped over — are exactly where a semantic drift would show.
A BFS-reachable pass from `initial_state()` is also reported, as a sanity
cross-check that the exhaustive pass covers it.
"""
import itertools
import os
import sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")


def load(path):
    ns = {}
    with open(path, encoding="utf-8") as f:
        exec(compile(f.read(), path, "exec"), ns)
    return ns


def fields(ns):
    return [f for f in ns["State"].__dataclass_fields__]


def all_states(ns):
    """Every representable assignment, in a fixed order."""
    n = ns["N_POS"]
    doms = []
    for f in fields(ns):
        doms.append(range(n) if f.endswith("_pos") else (False, True))
    for combo in itertools.product(*doms):
        yield combo


def successor(ns, combo, action):
    st = ns["State"](*combo)
    try:
        return ("ok", ns["step"](st, action).key())
    except Exception as exc:
        return ("raise", type(exc).__name__, str(exc))


def reachable(ns):
    seen, frontier = set(), [ns["initial_state"]()]
    seen.add(frontier[0].key())
    out = [frontier[0].key()]
    while frontier:
        s = frontier.pop()
        for a in ns["ACTIONS"]:
            try:
                t = ns["step"](s, a)
            except Exception:
                continue
            if t.key() not in seen:
                seen.add(t.key())
                out.append(t.key())
                frontier.append(t)
    return sorted(out)


report = []
for label in ("peg5", "peg4"):
    b = load(os.path.join(OUT, "base", label + ".python.py"))
    c = load(os.path.join(OUT, "cur", label + ".python.py"))

    assert fields(b) == fields(c), "field order differs"
    assert b["ACTIONS"] == c["ACTIONS"], "action alphabet differs"
    assert b["SEMANTICS"] == c["SEMANTICS"], "semantics differ"

    n_states = n_pairs = n_mismatch = 0
    n_ok = n_raise = 0
    mismatches = []
    for combo in all_states(b):
        n_states += 1
        for a in b["ACTIONS"]:
            n_pairs += 1
            rb, rc = successor(b, combo, a), successor(c, combo, a)
            if rb[0] == "ok":
                n_ok += 1
            else:
                n_raise += 1
            if rb != rc:
                n_mismatch += 1
                if len(mismatches) < 10:
                    mismatches.append((combo, a, rb, rc))

    # goal / occupancy / render agreement over the same exhaustive space
    n_goal_diff = n_occ_diff = 0
    for combo in all_states(b):
        sb, sc = b["State"](*combo), c["State"](*combo)
        if b["is_goal"](sb) != c["is_goal"](sc):
            n_goal_diff += 1
        if b["occupancy"](sb) != c["occupancy"](sc):
            n_occ_diff += 1

    rb, rc = reachable(b), reachable(c)

    report.append(
        "%s: fields=%s actions=%d representable_states=%d pairs=%d\n"
        "  successors_equal=%d mismatches=%d (guard-fired-ok=%d raised=%d)\n"
        "  is_goal disagreements=%d   occupancy disagreements=%d\n"
        "  BFS-reachable from initial_state: base=%d cur=%d identical=%s"
        % (label, fields(b), len(b["ACTIONS"]), n_states, n_pairs,
           n_pairs - n_mismatch, n_mismatch, n_ok, n_raise,
           n_goal_diff, n_occ_diff, len(rb), len(rc), rb == rc))
    for m in mismatches:
        report.append("  MISMATCH state=%r action=%r base=%r cur=%r" % m)

print("\n".join(report))
