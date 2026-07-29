"""C-4: plan, and the UNSAT branch that owes nothing.

The full arm, `Theoria.md:230`:

    SAT → commit;**UNSAT → 触发证书义务(回 certify 昂贵层出定理)+ 针对该定理依赖
    子句的定向戳探,全过才允许定案"不可解"**。

This arm, after the cut:

    SAT → commit;UNSAT → 定案"不可解"。

That is the whole of C-4, and on the A2 exhibit it is the whole of the arm's
behaviour (DESIGN.md §9, E2).  Upstream leaves a marker exactly where this arm
stops — `cold-start-a2/artifacts/plan_holed.json` carries the note

    "no plan exists under this manual — constraint 6 forbids stopping here;
     a certificate is owed"

and this arm writes the sentence that replaces it.

Two things are deliberately *not* changed, because changing them would move the
difference off the incision:

* the planner is the same `fd_adapter` at the same rung (`prefer="stub"`, the
  bundled grounded-STRIPS BFS, length-optimal for unit costs);
* the SAT branch keeps both checks — does the manual agree, does the world agree
  — because those are replay-family checks and replay is on the kept side.

One thing worth recording rather than glossing.  `certify/fd_unsat.py` upstream
draws the distinction constraint 6 turns on: FD exit 12 is "proved no plan
exists" and exit 13 is "my search was incomplete and found nothing", and only the
first counts.  This arm has no use for that distinction — it believes the report
either way — so `unsat_evidence` records *how* the search stopped and
`distinguishes_proof_from_exhaustion: false` states the arm's own limit in its
own artefact.  Logic is `cold-start-a2/a2pipeline/plan.py`'s, rewritten here
because that module writes into A2's `artifacts/`.
"""

import json
import os
from typing import Dict, List, Optional

import _bootstrap  # noqa: F401

from engines import fd_adapter  # noqa: E402

from certify.replay import load_theory  # noqa: E402  (cold-start-a0, read-only)

WORLD_ACTION = {"up": "UP", "down": "DOWN", "left": "LEFT", "right": "RIGHT"}

SETTLED_BY_SEARCH = (
    "no plan exists under this manual.  This arm has no constraint 6: the "
    "verdict is final as it stands.  No certificate is owed, no invariant is "
    "sought, no directed probe is scheduled, and nothing is placed on the "
    "surprise bus -- so the loop does not turn.  DESIGN.md §7.3.")


def _direction_of(action_text: str) -> str:
    head = action_text.strip("()").split()[0]
    for direction in WORLD_ACTION:
        if head.endswith("-" + direction):
            return direction
    raise ValueError("cannot read a direction off %r" % action_text)


def run_plan(out_dir: str, name: str, world=None, bus=None,
             out_path: Optional[str] = None) -> Dict[str, object]:
    """Plan from `out_dir`'s PDDL; commit against `world` when one is given."""
    domain = os.path.join(out_dir, "domain.pddl")
    instance = os.path.join(out_dir, "problem.pddl")
    theory = load_theory(os.path.join(out_dir, "theory.py"))

    plan = None
    unsat_evidence = None
    try:
        plan = fd_adapter.solve(domain, instance, prefer="stub")
    except RuntimeError as exc:
        if "no plan exists" not in str(exc):
            raise
        unsat_evidence = str(exc)

    report: Dict[str, object] = {
        "name": name,
        "domain": os.path.basename(domain),
        "problem": os.path.basename(instance),
        "backend": getattr(plan, "backend", None) if plan else None,
        "status": "UNSAT" if plan is None else "SAT",
    }

    if plan is None:
        report.update({
            "verdict": "unsolvable",
            "settled": True,
            "settled_by": "search",
            "certificate": None,
            "certificate_owed": False,
            "directed_probes_scheduled": 0,
            "note": SETTLED_BY_SEARCH,
            "unsat_evidence": unsat_evidence,
            "distinguishes_proof_from_exhaustion": False,
            "full_arm_would": ("owe a certificate (constraint 6) and probe the "
                               "theorem's `depends:` clauses (constraint 7) "
                               "before settling"),
        })
        if out_path:
            _write(report, out_path)
        return report

    directions = [_direction_of(a) for a in plan.actions]
    report["length"] = plan.length
    report["actions"] = list(plan.actions)
    report["directions"] = directions
    report["settled_by"] = "witness"

    # --- does the manual agree? -----------------------------------------
    state = theory.initial_state()
    for direction in directions:
        state = theory.step(state, ("push", "Cart", direction))
    report["manual_reaches_goal"] = bool(theory.is_goal(state))

    # --- does the world agree?  (commit) --------------------------------
    if world is not None:
        wstate = world.initial()
        mstate = theory.initial_state()
        mismatches: List[Dict[str, object]] = []
        for i, direction in enumerate(directions):
            wstate = world.step(wstate, WORLD_ACTION[direction])
            mstate = theory.step(mstate, ("push", "Cart", direction))
            if world.render(wstate) != theory.render(mstate):
                mismatches.append({"step": i, "action": WORLD_ACTION[direction]})
        report["world_reaches_goal"] = bool(world.is_win(wstate))
        report["execution_mismatches"] = mismatches
        report["green"] = (report["manual_reaches_goal"]
                           and report["world_reaches_goal"] and not mismatches)
        if bus is not None:
            for mismatch in mismatches:
                bus.raise_("execution_mismatch", mismatch, beat="commit")

    if out_path:
        _write(report, out_path)
    return report


def _write(report: Dict[str, object], out_path: str) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
