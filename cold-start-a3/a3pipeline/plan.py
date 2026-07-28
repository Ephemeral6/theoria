"""plan — hand the compiled PDDL to `fd_adapter` and check the manual agrees.

The pair `<out_dir>/{domain,problem}.pddl` goes to `engine-rig`'s `fd_adapter`,
which returns a length-optimal plan (Fast Downward when installed, the bundled
grounded-STRIPS BFS otherwise; both optimal for unit costs).  Then one check,
and it is deliberately not the interesting one:

* **does the manual agree with itself?** — replay the plan through the *same
  instance's* `theory.py`.  A disagreement between the planning form and the
  executable form means the four co-derived forms have drifted, and the PDDL is
  lying about the manual it was generated from.

What this module does **not** do is execute the plan against the world.  That
is `commit`, it belongs to a different beat, and putting it here would mean
`a3pipeline.plan` importing `a3world` — which would make the transfer arm's
sealing claim ("the arm's driver imports no world module") depend on which
functions it happens to call rather than on what it imports.  A2's `plan.py`
does both in one function because A2 had no sealed arm to protect.

**Copied from `cold-start-a2/a2pipeline/plan.py`, not imported.**  A2's
`run_plan` takes `out_dir` as an *input* directory and then writes its report
to `cold-start-a2/artifacts/plan_<name>.json` unconditionally
(`a2pipeline/plan.py:138-141`) — another experiment's tree, regardless of what
the caller asked for.  A2 itself copied A0's `plan_stage` for the same reason
and said so.  The logic is A2's and A0's; the destination is A3's.
"""

import json
import os
import sys
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from common.candidates import emit, make_candidate  # noqa: E402  (engine-rig)
from engines import fd_adapter  # noqa: E402

from certify.replay import load_theory  # noqa: E402  (cold-start-a0, read-only)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, "artifacts")

FIXED_TIME = "2026-07-28T00:00:00Z"

WORLD_ACTION = {"up": "UP", "down": "DOWN", "left": "LEFT", "right": "RIGHT"}


def _direction_of(action_text: str) -> str:
    """Read the direction off a grounded PDDL action's name.

    By suffix, because `gen_pddl_a0` names every action `rule.name.replace("_",
    "-")` and the manual's rules are all `<mechanism>_<direction>`.  That
    convention is load-bearing and undeclared anywhere upstream, so a rule named
    otherwise raises here rather than being mapped to a guess.
    """
    head = action_text.strip("()").split()[0]
    for direction in WORLD_ACTION:
        if head.endswith("-" + direction):
            return direction
    raise ValueError("cannot read a direction off %r" % action_text)


def run_plan(out_dir: str, name: str, meter=None,
             candidates_path: Optional[str] = None,
             timestamp: Optional[str] = None) -> Dict[str, object]:
    """Plan `<out_dir>`'s PDDL pair, replay it through `<out_dir>/theory.py`.

    **UNSAT arrives as an exception, and is matched as a substring.**
    `fd_adapter.solve` raises `RuntimeError("no plan exists for %s" %
    problem.name)` when the search closes the space without reaching the goal
    (`engine-rig/engines/fd_adapter/__init__.py:121-122`).  That is a result,
    not a crash, so it is caught — but the only handle on it is
    `"no plan exists" in str(exc)`, a **string match on an unversioned message
    in another component**.  Anything else re-raises.  If that message is ever
    reworded, this module stops distinguishing "unsolvable" from "the planner
    fell over", and the failure would look like a fact about the manual.  The
    alternative, `solve_parsed`, returns `(None, result)` instead — but its
    "unsolvable is a result" promise holds on the bundled BFS path only, so
    swapping to it would trade a known string coupling for a silent difference
    in behaviour between backends.  Recorded rather than fixed.

    Reports go to `artifacts/plan_<name>.json` under **this** tree.
    """
    # `common.candidates.emit` opens in "a" mode — the contract's append-only
    # rule, enforced structurally (trap T9).  Append-only holds *within* a run;
    # a rerun starts the stream over, or the file grows a duplicate row every
    # time and the artefacts stop being byte-reproducible.
    if candidates_path and os.path.exists(candidates_path):
        os.remove(candidates_path)

    domain = os.path.join(out_dir, "domain.pddl")
    instance = os.path.join(out_dir, "problem.pddl")
    theory = load_theory(os.path.join(out_dir, "theory.py"))

    try:
        plan = fd_adapter.solve(domain, instance, prefer="stub")
    except RuntimeError as exc:
        if "no plan exists" not in str(exc):
            raise
        plan = None

    report: Dict[str, object] = {
        "name": name,
        "domain": os.path.relpath(domain, ROOT).replace(os.sep, "/"),
        "problem": os.path.relpath(instance, ROOT).replace(os.sep, "/"),
        "backend": getattr(plan, "backend", None) if plan else None,
        "status": "UNSAT" if plan is None else "SAT",
    }

    if meter is not None:
        meter.charge("plan_runs", 1, "fd_adapter.solve on %s" % name)

    if plan is None:
        report["note"] = ("no plan exists under this manual — constraint 6 "
                          "forbids stopping here; a certificate is owed")
        _write(report, name)
        return report

    directions = [_direction_of(a) for a in plan.actions]
    report["length"] = plan.length
    report["actions"] = list(plan.actions)
    report["directions"] = directions
    report["world_actions"] = [WORLD_ACTION[d] for d in directions]

    # --- does the manual agree with itself? ---------------------------------
    # The plan is replayed through the executable form, cell by cell, and the
    # trail is kept.  A plan that reaches the goal by a route the manual does
    # not take would still report `manual_reaches_goal`, so the trail is what
    # makes the agreement inspectable rather than merely asserted.
    state = theory.initial_state()
    trail = [list(state.Cart_pos)]
    for direction in directions:
        state = theory.step(state, ("push", "Cart", direction))
        trail.append(list(state.Cart_pos))
    report["manual_trail"] = trail
    report["manual_reaches_goal"] = bool(theory.is_goal(state))
    report["manual_final_cell"] = list(state.Cart_pos)
    report["green"] = bool(report["manual_reaches_goal"])

    if candidates_path:
        emit(candidates_path, [make_candidate(
            engine="fd_adapter",
            kind="plan",
            payload={
                "domain": "a3",
                "problem": os.path.basename(instance),
                "backend": plan.backend,
                "search": "bfs",
                "optimal": True,
                "length": plan.length,
                "actions": list(plan.actions),
            },
            transitions=list(range(plan.length)),
            coverage="%d/%d" % (plan.length, plan.length),
            timestamp=timestamp or FIXED_TIME,
        )])

    if meter is not None:
        meter.mark_first_plan()

    _write(report, name)
    return report


def _write(report: Dict[str, object], name: str) -> str:
    os.makedirs(ARTIFACTS, exist_ok=True)
    out = os.path.join(ARTIFACTS, "plan_%s.json" % name)
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return out


def brief(report: Dict[str, object]) -> str:
    if report["status"] == "UNSAT":
        return "UNSAT  (%s)" % report.get("note", "")
    return "%-5s length %d, backend %s, manual reaches goal: %s" % (
        "GREEN" if report.get("green") else "RED",
        report["length"], report["backend"], report["manual_reaches_goal"])


def main() -> int:
    os.environ.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
    os.environ.setdefault("THEORIA_FIXED_TIME", FIXED_TIME)
    target = sys.argv[1] if len(sys.argv) > 1 else "generated_l1"
    report = run_plan(
        os.path.join(ROOT, "theory", target), target,
        candidates_path=os.path.join(ARTIFACTS, "candidates_plan_%s.jsonl"
                                     % target))
    print(json.dumps(report, indent=2, sort_keys=True))
    # UNSAT is not a failure here: it triggers the certificate obligation.
    return 0 if report.get("green") or report["status"] == "UNSAT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
