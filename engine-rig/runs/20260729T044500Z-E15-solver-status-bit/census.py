"""E15 item 2 -- re-issue the 639, so the rate is readable off the engine's product.

    python -m runs.20260729T044500Z-E15-solver-status-bit.census        # (not importable: dotted dir)
    python runs/20260729T044500Z-E15-solver-status-bit/census.py

E11 measured `lp_potential`'s incompleteness at **639 / 2189 = 29.2 %** of truly
unreachable `jumpgraph` worlds.  The number is right and it is not being
re-litigated here.  What is being fixed is *how* it was obtained: E11's reviewer
had to rebuild the LP and read HiGHS's status themselves, because the engine
collapsed status 1/2/3/4 into one silent `None`.  A figure a reader can only
believe by re-deriving it does not belong in a paper.

So every classification below is the **engine's own word** -- `LpOutcome.status`,
straight from `engines.lp_potential.decide` -- and nothing in `census.jsonl` is
computed by re-solving the LP outside the engine.  The two things the harness
does own are the ground truth (an independent forward BFS over `spec.triples`,
never the generator's `solvable` flag) and the world draw.

The wider-box columns are also the engine, called again with a different `bound`.
That is not a second opinion about the same question: `bound` is part of the
question, and `LpOutcome` now carries it.
"""

import json
import os
import sys
import time
from collections import Counter, deque
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE_RIG = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ENGINE_RIG)
for path in (ENGINE_RIG, REPO):
    if path not in sys.path:
        sys.path.insert(0, path)

from engines import lp_potential                                   # noqa: E402
from engines.lp_potential import potential                         # noqa: E402
from fuzzlab import prng                                           # noqa: E402
from fuzzlab.worlds import jumpgraph                               # noqa: E402

CAMPAIGN_SEED = 0x00005EEDC1E4F002
FAMILY = "jumpgraph"
N_WORLDS = 3000
WIDER_BOUNDS = (100, 10 ** 4, 10 ** 6)


def reachable(initial, triples):
    """Forward BFS, written here and driven by `spec.triples`.

    `spec.triples` rather than `graph["edges"]`: the engine's move list is built
    from `edges`, so an oracle reading `edges` shares a failure with the subject.
    E11 made the same choice for the same reason.
    """
    seen = {initial}
    queue = deque([initial])
    while queue:
        state = queue.popleft()
        for src, over, dst in triples:
            if state[src] == "1" and state[over] == "1" and state[dst] == "0":
                cells = list(state)
                cells[src] = cells[over] = "0"
                cells[dst] = "1"
                nxt = "".join(cells)
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
    return seen


def exact_pagoda_holds(weights, triples, initial, goals, margin=1):
    """Re-check a weight vector in exact rationals, from the spec's triples.

    Used only on the one world that becomes feasible in a wider box -- the
    positive result E11 verified by hand.  A solver's word is not evidence for a
    claim; this is.
    """
    w = [Fraction(x) for x in weights]

    def potential_of(state):
        return sum((w[i] for i, cell in enumerate(state) if cell == "1"),
                   Fraction(0))

    start = potential_of(initial)
    inv_closed = all(w[d] - w[s] - w[o] <= 0 for s, o, d in triples)
    goal_break = all(potential_of(g) - start >= Fraction(margin) for g in goals)
    return {
        "inv_closed": inv_closed,
        "goal_break": goal_break,
        "initial_potential": str(start),
        "goal_gaps": [str(potential_of(g) - start) for g in goals],
        "holds": inv_closed and goal_break,
    }


def main():
    started = time.time()
    rows = []
    for index in range(N_WORLDS):
        seed = prng.derive(CAMPAIGN_SEED, FAMILY, index)
        world = jumpgraph.generate(seed)
        spec, graph = world.spec, world.graph
        reach = reachable(spec.initial, spec.triples)
        truly_unreachable = not any(g in reach for g in spec.goal_states)

        row = {
            "index": index,
            "seed": seed,
            "n_pos": spec.n_pos,
            "n_triples": len(spec.triples),
            "n_goals": len(spec.goal_states),
            "initial": spec.initial,
            "goal_states": list(spec.goal_states),
            "reachable_size": len(reach),
            # harness-owned truth
            "goal_truly_unreachable": truly_unreachable,
            "generator_solvable_flag": spec.solvable,
        }

        try:
            outcome = lp_potential.decide(graph, spec.initial)
        except potential.CertificateError as exc:
            row["engine"] = {"status": "certificate_error", "detail": str(exc)}
            row["silent"] = True
            rows.append(row)
            continue

        # The engine's own payload, verbatim.  This is the whole point of the
        # item: the classification is read, not reconstructed.
        row["engine"] = outcome.as_json()
        # Branch on the status *word*, never on `certificate is None`.  The two
        # agree on this corpus (0 undecided outcomes), and that is precisely why
        # writing the second one would be undetectable here and wrong the first
        # time HiGHS hits an iteration limit -- E15's whole complaint.
        row["silent"] = outcome.status != potential.CERTIFIED

        if row["silent"] and truly_unreachable:
            widened = []
            for bound in WIDER_BOUNDS:
                wider = lp_potential.decide(graph, spec.initial, bound=bound)
                entry = {"bound": bound, "status": wider.status,
                         "solver_status": wider.solver_status}
                if wider.certificate is not None:
                    weights = [float(x) for x in wider.certificate.weights]
                    entry["weights"] = [str(x) for x in wider.certificate.weights]
                    entry["exact_recheck"] = exact_pagoda_holds(
                        wider.certificate.weights, spec.triples,
                        spec.initial, spec.goal_states,
                    )
                    entry["max_abs_weight"] = max(abs(x) for x in weights)
                widened.append(entry)
            row["wider_box"] = widened

        rows.append(row)

    out = os.path.join(HERE, "census.jsonl")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")

    summary = summarise(rows)
    with open(os.path.join(HERE, "SUMMARY.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    # Timing goes to stdout, never into the artifact: `SUMMARY.json` has to be
    # byte-reproducible for a fixed seed (CLAUDE.md), and a wall-clock field
    # makes every re-run differ for a reason that says nothing about the corpus.
    print("wall_seconds: %.1f" % (time.time() - started))


def summarise(rows):
    """Every count below is a tally of the engine's own `status` strings."""
    status = Counter(row["engine"]["status"] for row in rows)
    unreachable = [r for r in rows if r["goal_truly_unreachable"]]
    silent_unreachable = [r for r in unreachable if r["silent"]]

    wider = [r for r in silent_unreachable if r.get("wider_box")]
    feasible_wider = [
        r for r in wider
        if any(e["status"] == potential.CERTIFIED for e in r["wider_box"])
    ]
    return {
        "campaign_seed": "0x%016X" % CAMPAIGN_SEED,
        "family": FAMILY,
        "worlds": len(rows),
        "status_counts": dict(sorted(status.items())),
        "certificate_issued": status[potential.CERTIFIED],
        "no_certificate": len(rows) - status[potential.CERTIFIED],
        "goal_truly_unreachable": len(unreachable),
        "goal_truly_reachable": len(rows) - len(unreachable),
        "silent_and_truly_unreachable": len(silent_unreachable),
        "incompleteness_rate": (
            round(len(silent_unreachable) / len(unreachable), 6)
            if unreachable else None
        ),
        "incompleteness_rate_pct": (
            round(100.0 * len(silent_unreachable) / len(unreachable), 1)
            if unreachable else None
        ),
        "silence_by_status": dict(sorted(Counter(
            r["engine"]["status"] for r in silent_unreachable).items())),
        "undecided_outcomes": sum(
            1 for r in rows if not r["engine"].get("decided", False)
            and r["engine"]["status"] != potential.CERTIFIED
        ),
        "wider_box_probed": len(wider),
        "wider_box_feasible": len(feasible_wider),
        "wider_box_feasible_worlds": [
            {"index": r["index"], "seed": r["seed"], "n_pos": r["n_pos"],
             "initial": r["initial"], "goal_states": r["goal_states"],
             "reachable_size": r["reachable_size"],
             "first_feasible": next(
                 e for e in r["wider_box"] if e["status"] == potential.CERTIFIED)}
            for r in feasible_wider
        ],
        "certificate_errors": status["certificate_error"],
        "note": (
            "status_counts is a tally of LpOutcome.status as the engine emitted "
            "it. Nothing here re-solves the LP outside the engine."
        ),
    }


if __name__ == "__main__":
    main()
