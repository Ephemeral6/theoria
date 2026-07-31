"""The referee's copy: rules, invariants, solvability, reversibility.

Every world ships this, and it is the thing that makes the catalogue usable as a
scoring target rather than just as a pile of traces.  Three properties are worth
stating because they are easy to lose:

* **the rules come from the same code that runs the world.**  A mechanism's
  `truth_rules` names each rule with the exact string its `Outcome.rule` carries,
  and `check_invariants` runs every declared invariant over the *whole* reachable
  set.  A ground truth that disagrees with the world therefore fails at build
  time rather than at scoring time;
* **invariants are exercised, not asserted.**  An invariant with no callable
  `check` is recorded as prose and reported as unverified — the distinction is
  kept in the JSON so a reader can tell which is which;
* **the reversibility stamp is measured.**  `core/reversibility.py` derives, per
  rule, how many times one trajectory can witness it.  That is A0′'s criterion
  (`cold-start-a0/prime/A0P_REPORT.md` §1) applied as an outgoing inspection.

Split as in cold-start-a0: the trace is everything a discovery pipeline may
read; `ground_truth.json` and `GROUND_TRUTH.md` are scoring only.
"""

import json
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import reversibility as rev
from . import solvability
from .spec import WorldSpec
from .types import ACTIONS, AGENT, FLOOR, WALL
from .world import GridWorld

# Two rules belong to `GridWorld.explain` itself rather than to any mechanism.
BASE_RULES: List[Dict[str, Any]] = [
    {"name": "walk",
     "when": "act=D and the target cell is inside the grid, is not a wall, and no "
             "mechanism claims it",
     "then": "the agent moves one cell in direction D",
     "reversible": "conditional — reversible on open floor, not across a one-way edge"},
    {"name": "blocked_by_wall",
     "when": "act=D and the target cell is outside the grid or is a wall",
     "then": "nothing changes",
     "reversible": True},
]


def rule_table(world: GridWorld) -> List[Dict[str, Any]]:
    out = list(BASE_RULES)
    for mechanism in world.mechanisms:
        out.extend(mechanism.truth_rules(world.spec, world.mine(mechanism)))
    return out


def invariant_table(world: GridWorld) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = [
        {"name": "agent_unique",
         "statement": "exactly one cell shows colour %d at all times" % AGENT,
         "check": lambda w, s: sum(row.count(AGENT) for row in w.render(s)) == 1},
        {"name": "grid_shape",
         "statement": "every frame is %d x %d" % (world.spec.height, world.spec.width),
         "check": lambda w, s: (len(w.render(s)) == w.spec.height
                                and all(len(r) == w.spec.width for r in w.render(s)))},
    ]
    for mechanism in world.mechanisms:
        out.extend(mechanism.invariants(world.spec, world.mine(mechanism)))
    return out


def check_invariants(world: GridWorld,
                     states: Optional[Sequence] = None) -> List[Dict[str, Any]]:
    states = list(world.reachable()) if states is None else list(states)
    results: List[Dict[str, Any]] = []
    for inv in invariant_table(world):
        check = inv.get("check")
        row = {"name": inv["name"], "statement": inv["statement"]}
        if check is None:
            row["verified"] = False
            row["note"] = "prose only — not checkable on a single state"
            results.append(row)
            continue
        violations = []
        for state in states:
            try:
                ok = bool(check(world, state))
            except Exception as exc:
                ok = False
                violations.append({"state": list(state.key()), "error": repr(exc)})
                break
            if not ok:
                violations.append({"state": list(state.key())})
                if len(violations) >= 3:
                    break
        row["verified"] = True
        row["states_checked"] = len(states)
        row["holds"] = not violations
        if violations:
            row["violations"] = violations
        results.append(row)
    return results


def ground_truth(world: GridWorld, diagnose: bool = True) -> Dict[str, Any]:
    spec = world.spec
    rules = rule_table(world)
    invariants = check_invariants(world)
    solve = solvability.report(world, diagnose=diagnose)
    stamp = rev.audit(world, rules)

    return {
        "world_id": spec.world_id,
        "spec": spec.as_json(),
        "grid": [spec.height, spec.width],
        "actions": list(ACTIONS),
        "palette": dict({"floor": FLOOR, "wall": WALL, "agent": AGENT},
                        **{k: v for k, v in spec.colors}),
        "rules": [{k: v for k, v in r.items() if k != "check"} for r in rules],
        "invariants": invariants,
        "invariants_all_hold": all(i.get("holds", True) for i in invariants),
        "solvability": solve,
        "reversibility": stamp,
    }


def to_markdown(truth: Dict[str, Any]) -> str:
    lines = [
        "# GROUND_TRUTH — `%s`" % truth["world_id"], "",
        "**Do not open while theorizing.** Scoring only.", "",
        "Grid %dx%d, actions %s, families %s."
        % (truth["grid"][0], truth["grid"][1], ", ".join("`%s`" % a for a in truth["actions"]),
           ", ".join("`%s`" % f for f in truth["spec"]["families"]) or "none"),
        "",
        "## Palette", "",
        "| name | colour |", "|---|---|",
    ]
    for name, value in sorted(truth["palette"].items()):
        lines.append("| `%s` | %d |" % (name, value))

    lines += ["", "## Rules", "",
              "`max` is the largest number of times **one trajectory** can witness "
              "the rule; `-1` means unboundedly often. A rule with `max = 1` is the "
              "A0 failure mode — one witness, no second one obtainable.", "",
              "| name | when | then | claimed reversible | max |", "|---|---|---|---|---|"]
    measured = truth["reversibility"]["rules"]
    for rule in truth["rules"]:
        seen = measured.get(rule["name"])
        lines.append("| `%s` | %s | %s | %s | %s |" % (
            rule["name"], rule["when"], rule["then"], rule.get("reversible", "—"),
            "unreachable" if seen is None else seen["max_witnesses"]))

    lines += ["", "## Invariants", ""]
    for inv in truth["invariants"]:
        if not inv.get("verified"):
            lines.append("* **%s** — %s  _(prose only, unverified)_"
                         % (inv["name"], inv["statement"]))
        else:
            lines.append("* **%s** — %s  _(checked on %d reachable states: %s)_"
                         % (inv["name"], inv["statement"], inv["states_checked"],
                            "holds" if inv["holds"] else "**VIOLATED**"))

    solve = truth["solvability"]
    lines += ["", "## Solvability", ""]
    if solve["solvable"]:
        lines.append("Solvable in %d steps: `%s`."
                     % (solve["optimal_length"], " ".join(solve["optimal_plan"])))
    else:
        cert = solve["certificate"]
        lines.append("**Unsolvable.** %s" % cert["statement"])
        blockers = cert.get("blocking_entities") or []
        if blockers:
            lines.append("")
            for row in blockers:
                lines.append("* `%s` at %r — %s" % (row["entity"]["kind"],
                                                    tuple(row["entity"]["cell"]),
                                                    row["verdict"]))

    stamp = truth["reversibility"]
    lines += ["", "## Reversibility stamp (A0′ criterion)", "",
              "%d of %d rules are re-witnessable (score %.2f)."
              % (stamp["rules_re_witnessable"], stamp["rules_total"],
                 stamp["reversibility_score"])]
    if stamp["rules_single_witness"]:
        lines.append("")
        lines.append("Single-witness rules: %s."
                     % ", ".join("`%s`" % r for r in stamp["rules_single_witness"]))
    if stamp["claim_disagreements"]:
        lines.append("")
        lines.append("**Claim disagreements:** %s."
                     % ", ".join("`%s`" % r for r in stamp["claim_disagreements"]))
    lines.append("")
    return "\n".join(lines)


def write(dirname: str, world: GridWorld, diagnose: bool = True) -> Dict[str, Any]:
    os.makedirs(dirname, exist_ok=True)
    truth = ground_truth(world, diagnose=diagnose)
    with open(os.path.join(dirname, "ground_truth.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(truth, indent=2, sort_keys=True) + "\n")
    with open(os.path.join(dirname, "GROUND_TRUTH.md"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(to_markdown(truth))
    return truth
