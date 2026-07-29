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
from .world import FORBIDDEN_RULE, GridWorld

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


#: The opening every rule in this library writes when it is conditioned on the
#: action.  `guard_rules` rewrites exactly this prefix and nothing else, and
#: `tests/test_mutate.py` requires the rewrite to reach every rule that has it —
#: a partial rewrite is worse than none, because it leaves the table looking
#: uniformly correct while half of it is stale.
ACTION_PREFIX = "act=D and "


def base_rules(world: GridWorld) -> List[Dict[str, Any]]:
    """`BASE_RULES`, plus `action_forbidden` where a world forbids a command."""
    if not world.forbidden:
        return list(BASE_RULES)
    named = " or ".join("`%s`" % a for a in sorted(world.forbidden))
    return list(BASE_RULES) + [{
        "name": FORBIDDEN_RULE,
        "when": "act=D and D is %s" % named,
        "then": "nothing changes — the command is refused before the grid is "
                "consulted, so the refusal is indistinguishable from a world in "
                "which that direction never does anything",
        "reversible": True,
    }]


def guard_rules(world: GridWorld,
                rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Condition every action-triggered rule on the world's forbidden command.

    A world that refuses a command before consulting the grid makes **no** rule
    unconditional in the direction it refuses — not `walk`, not
    `blocked_by_wall`, and not `advance_cycler` or `walk_through_door` either.
    An earlier version of this rewrote only the two rules in `BASE_RULES`, on
    the grounds that they were the ones this module owns, and the result was a
    `ground_truth.json` that contradicted itself: on `v-eb4c5810` at agent
    `(3,4)` with the cycler shut, `act=UP` satisfies the antecedent of both
    `action_forbidden` ("nothing changes") and `advance_cycler` ("the phase
    becomes (phase+1) mod k"), and only the first is true.

    `rule_correspondence` compares rule *names* against `Outcome.rule` tags and
    is blind to prose, so nothing caught it. It is caught now by
    `test_no_rule_claims_a_transition_a_forbidden_action_prevents`, which
    evaluates the antecedents rather than reading them.
    """
    if not world.forbidden:
        return rules
    named = " or ".join("`%s`" % a for a in sorted(world.forbidden))
    guarded = "act=D, D is not %s, and " % named
    out: List[Dict[str, Any]] = []
    for rule in rules:
        row = dict(rule)
        when = row.get("when", "")
        if rule["name"] != FORBIDDEN_RULE and when.startswith(ACTION_PREFIX):
            row["when"] = guarded + when[len(ACTION_PREFIX):]
        out.append(row)
    return out


def rule_table(world: GridWorld) -> List[Dict[str, Any]]:
    out = base_rules(world)
    for mechanism in world.mechanisms:
        out.extend(mechanism.truth_rules(world.spec, world.mine(mechanism)))
    return guard_rules(world, out)


def fired_rules(world: GridWorld) -> List[str]:
    """Every `Outcome.rule` tag that actually occurs on the reachable graph."""
    return sorted({rule for _s, _a, _n, rule in world.transitions()})


def rule_correspondence(world: GridWorld) -> Dict[str, Any]:
    """Does the declared rule table match the tags the world actually emits?

    The module docstring claims the rules "come from the same code that runs the
    world". That was aspirational: `truth_rules` is prose living in the mechanism
    modules and only `name` was ever tied to `Outcome.rule` — **by convention,
    with nothing checking either direction**. So 12 of 20 worlds shipped
    declaring rules that never fire, and `GROUND_TRUTH.md` printed `unreachable`
    for three of them (`fall`, `up_is_inert`, `door_mirrors_net`) that are not
    `Outcome.rule` tags at all: they describe the `settle` cascade, which never
    names a rule. A reader had no way to tell "impossible by design" from
    "impossible by bug" — and one of those `unreachable` entries, `teleport_twoway`,
    was a bug.

    This closes the loop in both directions:

    * a declared rule that is neither `cascade: True` nor ever fired is
      **`declared_never_fires`** — either the world cannot reach it (say it, with
      `cascade`) or the mechanism is broken (fix it);
    * a tag the world emits that nobody declared is **`fired_undeclared`** — a
      mechanism shipping an effect that is missing from the referee's copy.

    Two exemptions, and each is a claim rather than an excuse.

    **`cascade: True`** says "this fires inside `settle`". `settle` is the only
    place a rule can act without naming itself, so a cascade rule is unwitnessable
    *as a tag* by construction — that is a fact about where it acts, not evidence
    it cannot happen.

    **`clause: True`** marks a guard clause: the negative branch of some positive
    rule (`blocked_portal_exit` is the branch of `teleport_*` where the landing is
    not available). A clause may be dormant in a world whose geometry never
    presents the case, and that is ordinary. A **primary** rule that never fires
    is not ordinary and fails the build — which is the check that would have
    caught `teleport_twoway`, dormant in every world that contained it because
    the landing test used the wrong predicate, while `reversibility.json` recorded
    it as `unreachable` with a clean `reversibility_score: 1.0`.

    Dormant clauses are still *reported*, per world, so the distinction stays
    visible to a reader instead of being silently forgiven.
    """
    declared = rule_table(world)
    names = [r["name"] for r in declared]
    cascade = {r["name"] for r in declared if r.get("cascade")}
    clause = {r["name"] for r in declared if r.get("clause")}
    fired = set(fired_rules(world))
    duplicates = sorted({n for n in names if names.count(n) > 1})
    dormant = set(names) - fired - cascade
    primary_never = sorted(dormant - clause)
    undeclared = sorted(fired - set(names))
    return {
        "declared": sorted(set(names)),
        "declared_duplicates": duplicates,
        "cascade": sorted(cascade),
        "fired": sorted(fired),
        "dormant_clauses": sorted(dormant & clause),
        "declared_never_fires": primary_never,
        "fired_undeclared": undeclared,
        "agrees": not primary_never and not undeclared and not duplicates,
    }


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


def frame_determines_state(world: GridWorld,
                           states: Optional[Sequence] = None) -> Dict[str, Any]:
    """Do two distinct reachable states ever render to the same frame?

    The property everything else in this library assumes. A reader gets frames
    and nothing else; if two states look alike and behave differently, no manual
    can be right about the world and no accuracy number means anything — the
    world is not learnable from its own trace, and it would look like a *miner*
    failure when the miner reported that no guard separates two transitions.

    It is worth checking rather than arguing because the argument is fragile and
    was already wrong once: `consumable` renders ARMED identically to INTACT and
    justifies it by "the agent is standing on it", which held only while
    `interact` was the sole route onto a tile. A gravity drop or a teleport onto
    an intact tile would have broken it, and the naive repair for the two-way
    portal defect would have introduced exactly that.
    """
    states = list(world.reachable()) if states is None else list(states)
    seen: Dict[Any, Any] = {}
    collisions = []
    for state in states:
        key = tuple(tuple(row) for row in world.render(state))
        other = seen.get(key)
        if other is not None and other != state.key():
            collisions.append({"a": list(other), "b": list(state.key())})
            if len(collisions) >= 3:
                break
        seen[key] = state.key()
    return {
        "states": len(states),
        "distinct_frames": len(seen),
        "injective": not collisions,
        "collisions": collisions,
    }


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
        "rule_correspondence": rule_correspondence(world),
        "frame_determines_state": frame_determines_state(world),
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

    corr = truth.get("rule_correspondence", {})
    lines += ["", "## Rules", "",
              "`max` is the largest number of times **one trajectory** can witness "
              "the rule; `-1` means unboundedly often. A rule with `max = 1` is the "
              "A0 failure mode — one witness, no second one obtainable.", "",
              "A rule marked **cascade** fires inside `settle`, after the rule that "
              "caused it, and therefore never carries an `Outcome.rule` tag of its "
              "own. It has no `max` because there is no tagged transition to count — "
              "that is a property of where it acts, not evidence that it cannot "
              "happen. Any *non*-cascade rule reading `never fires` is a defect, and "
              "the build refuses to ship one.", "",
              "| name | when | then | claimed reversible | max |", "|---|---|---|---|---|"]
    measured = truth["reversibility"]["rules"]
    cascade = set(corr.get("cascade", ()))
    for rule in truth["rules"]:
        seen = measured.get(rule["name"])
        if rule["name"] in cascade:
            stamp_cell = "_cascade — untagged by construction_"
        elif seen is None:
            stamp_cell = "**never fires**"
        else:
            stamp_cell = str(seen["max_witnesses"])
        lines.append("| `%s` | %s | %s | %s | %s |" % (
            rule["name"], rule["when"], rule["then"], rule.get("reversible", "—"),
            stamp_cell))
    if corr and not corr.get("agrees", True):
        lines += ["", "**Rule table disagrees with the world.**"]
        for key in ("declared_never_fires", "fired_undeclared", "declared_duplicates"):
            if corr.get(key):
                lines.append("* `%s`: %s"
                             % (key, ", ".join("`%s`" % n for n in corr[key])))

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
