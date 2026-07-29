"""Run every pre-registered held-out split and write `results.json`.

    python -m heldout.run --out runs/<id>/results.json

Deterministic and free of wall-clock: two runs produce byte-identical output,
which is one of the pre-registered validity criteria.  Exit codes follow the rig
convention that "checked and wrong" and "could not check" must not collapse into
one value:

    0  the run is valid -- whatever the hit rates say
    1  a pre-registered validity criterion failed (harness gate, non-determinism)
    3  the run could not be carried out at all
"""

import argparse
import dataclasses
import json
import sys
from collections import Counter
from typing import Any, Dict, List

from heldout import lp_potential_heldout as lph
from heldout import parityworld, peg
from heldout import zero_space_heldout as zsh


def _pct(hits: int, total: int) -> str:
    return "n/a" if not total else "%.1f" % (100.0 * hits / total)


def zero_space_section() -> Dict[str, Any]:
    worlds = parityworld.corpus()

    gate_failures = [w.world_id for w in worlds if not zsh.fit_matches_engine(w)]

    outcomes: List[zsh.SplitOutcome] = []
    for world in worlds:
        outcomes.append(zsh.run_s1(world))
        outcomes.extend(zsh.run_s2(world))

    tally: Dict[str, Counter] = {}
    misses: List[Dict[str, Any]] = []
    for outcome in outcomes:
        for law in outcome.laws:
            for bucket in (outcome.split_name, "%s/%s" % (outcome.split_name, law.scope)):
                counter = tally.setdefault(bucket, Counter())
                counter["laws"] += 1
                counter["delta_hit"] += int(law.delta_hit)
                counter["value_hit"] += int(law.value_hit)
            if not law.delta_hit:
                misses.append({
                    "world": outcome.world_id,
                    "split": outcome.split_name,
                    "variant": outcome.variant,
                    "scope": law.scope,
                    "support": law.support,
                    "value": law.value,
                    "witness": law.first_delta_witness,
                    "train_rank": outcome.train_rank,
                    "full_rank": outcome.full_rank,
                })

    rank_loss = Counter()
    for outcome in outcomes:
        rank_loss["%s" % outcome.split_name] += int(outcome.train_rank < outcome.full_rank)
        rank_loss["%s/splits" % outcome.split_name] += 1

    return {
        "corpus": {
            "family": "parityworld",
            "worlds": len(worlds),
            "n_cells": list(parityworld.N_CELLS),
            "widths": list(parityworld.WIDTHS),
            "transitions_per_world": parityworld.N_TRANSITIONS,
        },
        "gate_fit_matches_engine": {"failures": gate_failures,
                                    "checked": len(worlds)},
        "splits": {k: dict(v) for k, v in sorted(tally.items())},
        "rank_loss": dict(rank_loss),
        "misses": misses[:200],
        "misses_total": len(misses),
    }


def lp_potential_section() -> Dict[str, Any]:
    gate_ok, gate_problems = peg.matches_fixture_peg4()

    baselines: List[lph.BaselineCase] = []
    cases: List[lph.HeldOutCase] = []
    n_instances = 0
    for n in lph.N_POSITIONS:
        for goal_index in range(1, n - 1):
            goal = "".join("1" if i == goal_index else "0" for i in range(n))
            graph = peg.graph(n, goal)
            geometries = peg.geometries(graph)
            for instance in lph.instances(n, graph, goal):
                n_instances += 1
                baselines.append(lph.baseline(instance, graph))
                for geometry in geometries:
                    cases.append(lph.held_out_case(instance, graph, geometry))

    certificates = [c for c in cases if c.outcome == "certificate"]
    inv_hits = [c for c in certificates if c.heldout_inv_closed]
    false_certs = [c for c in certificates if c.claim_true is False]
    ungated = [c for c in certificates if not c.gate_withholds]
    caught_by_arithmetic = [c for c in certificates if c.gate_raising_moves]

    base_certs = [b for b in baselines if b.outcome == "certificate"]
    base_false = [b for b in base_certs if b.claim_true is False]
    base_violations = [b for b in base_certs if (b.admissibility_violations or 0) > 0]
    heldout_violations = [c for c in certificates
                          if (c.admissibility_violations or 0) > 0]

    def witness(case) -> Dict[str, Any]:
        return {k: v for k, v in dataclasses.asdict(case).items() if v not in (None, [], {})}

    return {
        "corpus": {"family": "pegN", "n_positions": list(lph.N_POSITIONS),
                   "instances": n_instances, "held_out_cases": len(cases)},
        "gate_matches_fixture_peg4": {"ok": gate_ok, "problems": gate_problems},
        "baseline_complete_graph": {
            "instances": len(baselines),
            "certificates": len(base_certs),
            "silent": sum(1 for b in baselines if b.outcome == "silent"),
            "errors": sum(1 for b in baselines if b.outcome == "error"),
            "false_certificates": len(base_false),
            "states_tested_L2": sum(b.admissibility_tested or 0 for b in base_certs),
            "admissibility_violations_L2": sum(b.admissibility_violations or 0
                                               for b in base_certs),
            "instances_with_violations": len(base_violations),
        },
        "held_out_L1": {
            "cases": len(cases),
            "certificates": len(certificates),
            "silent": sum(1 for c in cases if c.outcome == "silent"),
            "errors": sum(1 for c in cases if c.outcome == "error"),
            "heldout_inv_closed_hits": len(inv_hits),
            "heldout_inv_closed_rate_pct": _pct(len(inv_hits), len(certificates)),
            "false_certificates": len(false_certs),
            "false_certificate_rate_pct": _pct(len(false_certs), len(certificates)),
            "emit_gate_withheld": len(certificates) - len(ungated),
            "emit_gate_let_through": len(ungated),
            "caught_by_raised_potential_too": len(caught_by_arithmetic),
            "heldout_admissibility_violations": sum(
                c.admissibility_violations or 0 for c in certificates),
            "cases_with_admissibility_violations": len(heldout_violations),
        },
        "witnesses": {
            "false_certificates": [witness(c) for c in false_certs[:20]],
            "inv_closed_misses": [witness(c) for c in certificates
                                  if not c.heldout_inv_closed][:20],
            "admissibility_violations": [witness(c) for c in heldout_violations[:20]],
            "emit_gate_let_through": [witness(c) for c in ungated[:20]],
        },
    }


def build() -> Dict[str, Any]:
    return {
        "prompt_id": "E17-held-out-validation",
        "preregistration": "PREREGISTRATION.md",
        "zero_space": zero_space_section(),
        "lp_potential": lp_potential_section(),
    }


def summarise(report: Dict[str, Any]) -> List[str]:
    zs = report["zero_space"]
    lp = report["lp_potential"]
    lines = ["zero_space -- %d %s worlds, %d transitions each"
             % (zs["corpus"]["worlds"], zs["corpus"]["family"],
                zs["corpus"]["transitions_per_world"]),
             "  gate fit==analyse: %d/%d worlds ok"
             % (zs["gate_fit_matches_engine"]["checked"]
                - len(zs["gate_fit_matches_engine"]["failures"]),
                zs["gate_fit_matches_engine"]["checked"])]
    for name in sorted(zs["splits"]):
        row = zs["splits"][name]
        lines.append("  %-22s laws=%-6d delta_hit=%s%%  value_hit=%s%%"
                     % (name, row["laws"], _pct(row["delta_hit"], row["laws"]),
                        _pct(row["value_hit"], row["laws"])))
    lines.append("  delta misses total: %d" % zs["misses_total"])
    lines.append("lp_potential -- %d pegN instances, %d held-out cases"
                 % (lp["corpus"]["instances"], lp["corpus"]["held_out_cases"]))
    lines.append("  gate graph==fixture peg4: %s" % lp["gate_matches_fixture_peg4"]["ok"])
    b, h = lp["baseline_complete_graph"], lp["held_out_L1"]
    lines.append("  baseline: %d certs, %d silent, %d false; L2 %d/%d states violate h<=d"
                 % (b["certificates"], b["silent"], b["false_certificates"],
                    b["admissibility_violations_L2"], b["states_tested_L2"]))
    lines.append("  held-out: %d certs (%d silent), inv_closed hit %s%%, false certs %d (%s%%)"
                 % (h["certificates"], h["silent"], h["heldout_inv_closed_rate_pct"],
                    h["false_certificates"], h["false_certificate_rate_pct"]))
    lines.append("  emit gate: withheld %d, let through %d; raised-potential caught %d"
                 % (h["emit_gate_withheld"], h["emit_gate_let_through"],
                    h["caught_by_raised_potential_too"]))
    return lines


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    try:
        report = build()
    except Exception as exc:                      # noqa: BLE001 -- see docstring
        print("heldout: COULD NOT RUN: %r" % (exc,), file=sys.stderr)
        return 3

    text = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)

    for line in summarise(report):
        print(line)

    invalid = []
    if report["zero_space"]["gate_fit_matches_engine"]["failures"]:
        invalid.append("the fit drifted from zerospace.analyse")
    if not report["lp_potential"]["gate_matches_fixture_peg4"]["ok"]:
        invalid.append("the pegN generator disagrees with Fixture C")
    if invalid:
        print("heldout: RUN INVALID -- %s" % "; ".join(invalid), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
