"""plan → commit: the last two beats of the inner loop.

`theory.pddl` goes to `engine-rig/fd_adapter`, which returns a length-optimal
plan (Fast Downward when it is installed, the bundled grounded-STRIPS BFS
otherwise — both optimal for unit costs). Then two independent checks, in this
order, because they answer different questions:

* **does the manual agree?** — replay the plan through `theory.py`. If the
  planner and the manual disagree about what a plan does, the four co-derived
  forms have drifted apart and the PDDL is lying.
* **does the world agree?** — execute the same plan against `world/a0_world.py`,
  frame by frame. This is `commit`: the plan is scripted, the machine grades it,
  and a mismatch is an execution anomaly that sends the manual back to theorize.

`SAT` is not the interesting branch. `UNSAT` is: it triggers the certificate
obligation (constraint 6 — a bare UNSAT is not an answer), which is M5.
"""

import json
import os
import sys
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from common.candidates import emit, make_candidate  # noqa: E402
from engines import fd_adapter  # noqa: E402

from certify.replay import ACTION_NAMES, load_theory  # noqa: E402
from world import a0_world  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# PDDL action names carry their direction as a suffix; the manual's rule names
# are the source of both, so the mapping is a rename and nothing more.
WORLD_ACTION = {"up": "UP", "down": "DOWN", "left": "LEFT", "right": "RIGHT"}


def _direction_of(action_text: str) -> str:
    head = action_text.strip("()").split()[0]
    for direction in WORLD_ACTION:
        if head.endswith("-" + direction):
            return direction
    raise ValueError("cannot read a direction off %r" % action_text)


def run_plan(out_dir: str, spec, out_path: Optional[str] = None,
             timestamp: Optional[str] = None, world=None,
             report_name: Optional[str] = None) -> Dict[str, object]:
    """`world` defaults to the A0 world built from `spec`; A0′ passes its own."""
    domain = os.path.join(out_dir, "domain.pddl")
    instance = os.path.join(out_dir, "problem.pddl")
    theory = load_theory(os.path.join(out_dir, "theory.py"))

    try:
        plan = fd_adapter.solve(domain, instance, prefer="stub")
    except RuntimeError as exc:
        # The adapter raises rather than returning None when the search closes
        # the space without reaching the goal.  That is UNSAT, not a crash.
        if "no plan exists" not in str(exc):
            raise
        plan = None
    report: Dict[str, object] = {
        "domain": os.path.relpath(domain, ROOT),
        "problem": os.path.relpath(instance, ROOT),
        "backend": getattr(plan, "backend", None) if plan else None,
        "status": "UNSAT" if plan is None else "SAT",
    }
    report["_name"] = report_name
    if plan is None:
        report["note"] = ("no plan exists under this manual — constraint 6 forbids "
                          "stopping here; a certificate is owed")
        _write(report)
        return report

    directions = [_direction_of(a) for a in plan.actions]
    report["length"] = plan.length
    report["actions"] = list(plan.actions)
    report["directions"] = directions

    # --- does the manual agree? -----------------------------------------
    state = theory.initial_state()
    for direction in directions:
        state = theory.step(state, ("push", "Cart", direction))
    report["manual_reaches_goal"] = bool(theory.is_goal(state))

    # --- does the world agree? (commit) ---------------------------------
    world = world or a0_world.A0World(spec)
    wstate = world.initial()
    mismatches = []
    mstate = theory.initial_state()
    for i, direction in enumerate(directions):
        wstate = world.step(wstate, WORLD_ACTION[direction])
        mstate = theory.step(mstate, ("push", "Cart", direction))
        if world.render(wstate) != theory.render(mstate):
            mismatches.append({"step": i, "action": WORLD_ACTION[direction]})
    report["world_reaches_goal"] = bool(world.is_win(wstate))
    report["execution_mismatches"] = mismatches
    report["green"] = (
        report["manual_reaches_goal"] and report["world_reaches_goal"]
        and not mismatches
    )

    if out_path:
        emit(out_path, [make_candidate(
            engine="fd_adapter",
            kind="plan",
            payload={
                "domain": "a0",
                "problem": os.path.basename(instance),
                "backend": plan.backend,
                "search": "bfs",
                "optimal": True,
                "length": plan.length,
                "actions": list(plan.actions),
            },
            transitions=list(range(plan.length)),
            coverage="%d/%d" % (plan.length, plan.length),
            timestamp=timestamp,
        )])
    _write(report)
    return report


def _write(report: Dict[str, object]) -> None:
    name = (report.get("_name")
            or os.path.basename(os.path.dirname(str(report["problem"])))
            or "plan")
    out = os.path.join(ROOT, "artifacts", "plan_%s.json" % name)
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")


def main() -> int:
    out_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        ROOT, "theory", "generated")
    variant = sys.argv[2] if len(sys.argv) > 2 else "base"
    spec = a0_world.BASE if variant == "base" else a0_world.NO_BUTTON
    report = run_plan(out_dir, spec,
                      out_path=os.path.join(ROOT, "artifacts", "candidates.jsonl"))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("green") or report["status"] == "UNSAT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
