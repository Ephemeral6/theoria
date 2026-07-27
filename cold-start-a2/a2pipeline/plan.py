"""plan → commit, and the UNSAT branch that owes a certificate.

`theory.pddl` goes to `engine-rig/fd_adapter`, which returns a length-optimal
plan (Fast Downward when installed, the bundled grounded-STRIPS BFS otherwise;
both optimal for unit costs).  Then two independent checks, in this order,
because they answer different questions:

* **does the manual agree?** — replay the plan through `theory.py`.  A
  disagreement between planner and manual means the four co-derived forms have
  drifted and the PDDL is lying.
* **does the world agree?** — execute the same plan against `a2world`, frame by
  frame.  This is `commit`.

A2 rewrites A0's `plan_stage` instead of importing it for one reason: A0's
writes its report into A0's own `artifacts/`, and this track does not write
there.  The logic is A0's; the destination is A2's.

`SAT` is the boring branch.  `UNSAT` is the one A2 is built around — it triggers
the certificate obligation (constraint 6: a bare UNSAT is not an answer), and in
the holed manual's case that certificate is a theorem which is **false of the
world**.  The planner is not wrong.  The manual is.
"""

import json
import os
import sys
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from common.candidates import emit, make_candidate  # noqa: E402
from engines import fd_adapter  # noqa: E402

from certify.replay import load_theory  # noqa: E402  (cold-start-a0, read-only)

from a2world import a2_world  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, "artifacts")

WORLD_ACTION = {"up": "UP", "down": "DOWN", "left": "LEFT", "right": "RIGHT"}


def _direction_of(action_text: str) -> str:
    head = action_text.strip("()").split()[0]
    for direction in WORLD_ACTION:
        if head.endswith("-" + direction):
            return direction
    raise ValueError("cannot read a direction off %r" % action_text)


def run_plan(out_dir: str, name: str, spec=a2_world.BASE,
             candidates_path: Optional[str] = None,
             timestamp: Optional[str] = None) -> Dict[str, object]:
    # `common.candidates.emit` opens in "a" mode — the contract's append-only
    # rule, enforced structurally.  Append-only holds *within* a run; a rerun
    # starts the stream over, or the file grows a duplicate row every time and
    # the artefacts stop being byte-reproducible.  Same convention as A0's
    # engines_stage.
    if candidates_path and os.path.exists(candidates_path):
        os.remove(candidates_path)

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
        "name": name,
        "domain": os.path.relpath(domain, ROOT),
        "problem": os.path.relpath(instance, ROOT),
        "backend": getattr(plan, "backend", None) if plan else None,
        "status": "UNSAT" if plan is None else "SAT",
    }
    if plan is None:
        report["note"] = ("no plan exists under this manual — constraint 6 forbids "
                          "stopping here; a certificate is owed")
        _write(report, name)
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

    # --- does the world agree?  (commit) --------------------------------
    world = a2_world.A2World(spec)
    wstate = world.initial()
    mstate = theory.initial_state()
    mismatches = []
    for i, direction in enumerate(directions):
        wstate = world.step(wstate, WORLD_ACTION[direction])
        mstate = theory.step(mstate, ("push", "Cart", direction))
        if world.render(wstate) != theory.render(mstate):
            mismatches.append({"step": i, "action": WORLD_ACTION[direction]})
    report["world_reaches_goal"] = bool(world.is_win(wstate))
    report["execution_mismatches"] = mismatches
    report["green"] = (report["manual_reaches_goal"]
                       and report["world_reaches_goal"] and not mismatches)

    if candidates_path:
        emit(candidates_path, [make_candidate(
            engine="fd_adapter",
            kind="plan",
            payload={
                "domain": "a2",
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
    _write(report, name)
    return report


def _write(report: Dict[str, object], name: str) -> None:
    out = os.path.join(ARTIFACTS, "plan_%s.json" % name)
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")


def main() -> int:
    os.environ.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
    os.environ.setdefault("THEORIA_FIXED_TIME", "2026-07-28T00:00:00Z")
    target = sys.argv[1] if len(sys.argv) > 1 else "generated"
    report = run_plan(os.path.join(ROOT, "theory", target), target,
                      candidates_path=os.path.join(ARTIFACTS, "candidates.jsonl"))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("green") or report["status"] == "UNSAT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
