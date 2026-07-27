"""Run all eight engines end to end and validate the candidate stream they produce.

This was M8 (six engines); M9 adds the deadlock carver, IC3/PDR, and the
planner-backed probe layer.  Every engine proposes into one append-only
`candidates.jsonl`, and the whole file is then checked against the frozen
contract.

    python -m tools.run_all                    # writes out/candidates.jsonl
    python -m tools.run_all --deterministic    # frozen ids and timestamps
    python -m tools.run_all --out somewhere.jsonl --force

The two engines added after the contract was frozen emit under the enum member
whose work they extend and name themselves in `payload.producer` -- so the
`engine` histogram below still shows six names.  See DECISIONS.md D-018.
"""

import argparse
import os
import sys
from typing import Any, Dict, List, Optional

from common.jsonio import read_json, read_jsonl
from engines import (
    cegis_miner,
    deadlock_carver,
    fd_adapter,
    ic3_pdr,
    lp_potential,
    mdl_segmenter,
    probe_frontier,
    zero_space,
)
from engines.fd_adapter.pddl import parse_domain, parse_problem
from engines.probe_frontier import scenario as probe_scenario
from engines.probe_frontier import sokoban_probe
from fixtures import cart_world, pair_flip, peg4, sokoban
from tools.validate_candidates import validate_file

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(HERE, "out", "candidates.jsonl")

# The reference stream checked into the repository. Regenerate with:
#   python -m tools.run_all --out artifacts/candidates.jsonl --deterministic --force
ARTIFACT_PATH = os.path.join(HERE, "artifacts", "candidates.jsonl")
FIXED_TIME = "2026-07-27T00:00:00Z"

UNSOLVABLE_CONFIG = "1110"

# The configuration the LP is infeasible on (D-014) -- IC3's reason to exist.
NO_PAGODA_CONFIG = "0111"


def _deterministic_mode(enabled: bool) -> None:
    if enabled:
        os.environ["THEORIA_FIXED_TIME"] = FIXED_TIME
        os.environ["THEORIA_DETERMINISTIC_IDS"] = "1"
    else:
        os.environ.pop("THEORIA_FIXED_TIME", None)
        os.environ.pop("THEORIA_DETERMINISTIC_IDS", None)


def run_all(out_path: str = DEFAULT_OUT, deterministic: bool = False) -> Dict[str, Any]:
    """Run every engine against its fixture, appending proposals to `out_path`."""
    _deterministic_mode(deterministic)
    steps: List[Dict[str, Any]] = []

    def note(engine: str, detail: str) -> None:
        steps.append({"engine": engine, "detail": detail})

    # 1 & 2 -- Fixture A: segment, then mine rules off the segmentation.
    rows = read_jsonl(cart_world.TRAJ_PATH)
    frames = [row["frame"] for row in rows]
    actions = [row["action"] for row in rows]

    seg = mdl_segmenter.run(frames, background=0, out_path=out_path)
    note(
        "mdl_segmenter",
        "%d object(s), %d events, %d vs %d bits (ratio %.3f)"
        % (
            len(seg.tracks),
            len(seg.events),
            seg.script_bits,
            seg.baseline_bits,
            seg.compression_ratio,
        ),
    )

    transitions = cegis_miner.transitions_from_segmentation(frames, actions, seg)
    mined = cegis_miner.run(transitions, out_path=out_path)
    push, teleport = mined.by_name("push"), mined.by_name("teleport")
    note(
        "cegis_miner",
        "%d rules; push cov %s, teleport cov %s; guards exclusive=%s, total=%s"
        % (
            len(mined.all_rules),
            push.coverage if push else "-",
            teleport.coverage if teleport else "-",
            mined.guards_are_mutually_exclusive(),
            mined.explains_every_transition(),
        ),
    )

    # 3 -- Fixture B: conservation laws.
    pair_rows = read_jsonl(pair_flip.TRAJ_PATH)
    states = [row["state"] for row in pair_rows]
    laws = zero_space.run(states, ["R", "B"], out_path=out_path)
    note(
        "zero_space",
        "null space dim %d; global law: %s"
        % (laws.dimension, laws.global_laws()[0].rendering()),
    )

    # 4 -- Fixture C: pagoda certificate plus the heuristic it doubles as.
    graph = read_json(peg4.GRAPH_PATH)
    certificate, heuristic = lp_potential.run(graph, UNSOLVABLE_CONFIG, out_path=out_path)
    if certificate is None:
        raise RuntimeError("no certificate for %s" % UNSOLVABLE_CONFIG)
    note(
        "lp_potential",
        "w=%s certifies %s unsolvable; conditions %s"
        % (
            [str(w) for w in certificate.weights],
            UNSOLVABLE_CONFIG,
            certificate.conditions,
        ),
    )

    # 5 -- the planner adapter, on its own PDDL instance.
    plan = fd_adapter.run(out_path=out_path)
    note("fd_adapter", "%s plan of length %d" % (plan.backend, plan.length))

    # 6 -- the probe designer, on the hand-made frontier.
    bundle = probe_scenario.build()
    best, ranked = probe_frontier.run(
        bundle["hypotheses"],
        bundle["state"],
        bundle["actions"],
        transitions=list(range(len(bundle["evidence"]))),
        coverage="%d/%d" % (len(bundle["hypotheses"]), len(bundle["hypotheses"])),
        state_rendering=bundle["state"].render(),
        out_path=out_path,
    )
    if best is None:
        raise RuntimeError("the probe scenario produced no discriminating action")
    note("probe_frontier", "probe %s worth %.3f bits" % (best.action, best.entropy))

    # 7 -- Fixture D: conditional mini unsolvability theorems, and what they buy.
    with open(sokoban.DOMAIN_PATH, "r", encoding="utf-8") as fh:
        soko_domain = parse_domain(fh.read())
    with open(sokoban.OPEN4FAR.path, "r", encoding="utf-8") as fh:
        soko_problem = parse_problem(fh.read())
    task, theorems, report = deadlock_carver.run(
        soko_domain, soko_problem, out_path=out_path
    )
    if not theorems or report is None or not report.same_answer:
        raise RuntimeError("the deadlock carver proved nothing, or changed the answer")
    note(
        "deadlock_carver",
        "%d theorem(s) (%d corner, %d wall-pair); %d -> %d expansions (%.1f%% fewer), "
        "plan length %s either way"
        % (
            len(theorems),
            sum(1 for t in theorems if t.size == 1),
            sum(1 for t in theorems if t.size == 2),
            report.baseline.expansions, report.pruned.expansions,
            100.0 * (1.0 - report.ratio), report.pruned.length,
        ),
    )

    # 8 -- Fixture C again, on the configuration the LP cannot certify.
    peg_system = ic3_pdr.peg_system(graph, NO_PAGODA_CONFIG)
    verdict, checked = ic3_pdr.run(peg_system, out_path=out_path)
    if not isinstance(verdict, ic3_pdr.Invariant):
        raise RuntimeError("IC3 failed to certify %s" % NO_PAGODA_CONFIG)
    note(
        "ic3_pdr",
        "%s: LP infeasible, IC3 invariant I(s) = %s; conditions %s"
        % (
            NO_PAGODA_CONFIG,
            peg_system.render_cnf(verdict.clauses),
            checked.conditions,
        ),
    )

    # 9 -- probes priced by the planner, on the ring level.
    with open(sokoban.RING.path, "r", encoding="utf-8") as fh:
        ring_problem = parse_problem(fh.read())
    bundle = sokoban_probe.build()
    designed = probe_frontier.run_with_planner(
        bundle["hypotheses"], bundle["configurations"], soko_domain, ring_problem,
        prune=deadlock_carver.pruner(deadlock_carver.carve(
            deadlock_carver.Task.build(soko_domain, ring_problem)
        )),
        transitions=list(range(len(bundle["evidence"]))),
        out_path=out_path,
    )
    executable = [p for p in designed if p.tier == probe_frontier.EXECUTABLE]
    unreachable = [p for p in designed if p.reach.status == probe_frontier.UNREACHABLE]
    note(
        "probe_frontier+fd",
        "%d executable (%s), %d unreachable (%s)"
        % (
            len(executable),
            ", ".join(
                "%s %s: %.3f bits / cost %g"
                % (p.configuration.name, p.best.action, p.entropy, p.cost)
                for p in executable
            ) or "-",
            len(unreachable),
            ", ".join(p.configuration.name for p in unreachable) or "-",
        ),
    )

    written = read_jsonl(out_path)
    errors = validate_file(out_path)
    by_engine: Dict[str, int] = {}
    by_kind: Dict[str, int] = {}
    for row in written:
        by_engine[row["engine"]] = by_engine.get(row["engine"], 0) + 1
        by_kind[row["kind"]] = by_kind.get(row["kind"], 0) + 1

    return {
        "out_path": out_path,
        "steps": steps,
        "candidates": len(written),
        "by_engine": by_engine,
        "by_kind": by_kind,
        "errors": errors,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=DEFAULT_OUT, help="candidates.jsonl to append to")
    parser.add_argument("--deterministic", action="store_true",
                        help="freeze ids and timestamps so runs are byte-identical")
    parser.add_argument("--force", action="store_true",
                        help="remove an existing output file first")
    args = parser.parse_args(argv)

    if os.path.exists(args.out):
        if not args.force:
            print(
                "refusing to append to the existing %s -- pass --force to start fresh, "
                "or --out <path>" % args.out
            )
            return 2
        os.remove(args.out)

    summary = run_all(out_path=args.out, deterministic=args.deterministic)

    print("engine-rig integration run")
    print("-" * 72)
    for step in summary["steps"]:
        print("  %-15s %s" % (step["engine"], step["detail"]))
    print("-" * 72)
    print("  candidates: %d -> %s" % (summary["candidates"], summary["out_path"]))
    print("  by engine : %s" % dict(sorted(summary["by_engine"].items())))
    print("  by kind   : %s" % dict(sorted(summary["by_kind"].items())))
    if summary["errors"]:
        print("  SCHEMA    : FAIL (%d errors)" % len(summary["errors"]))
        for error in summary["errors"][:20]:
            print("     " + error)
        return 1
    print("  SCHEMA    : OK -- every line satisfies CONTRACTS/candidates_schema.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
