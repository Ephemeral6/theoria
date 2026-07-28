"""The recheck itself: three conditions, verified by enumeration, plus a second
opinion that shares nothing with them.

The three conditions are the Lean skeleton of Theoria 1.10(a), unchanged:

    inv_init    the claim holds where the world starts
    inv_closed  it survives every rule, from every state satisfying it
    goal_break  no state satisfying it is a goal state

Everything here is deliberately dumb.  There is no fixpoint, no frame stack, no
generalisation -- just a loop over the product of the declared domains.  A
checker clever enough to be wrong in the same way as the engine would be no
check at all, and the engines that produced these certificates were the clever
ones.  `ic3_pdr` and `deadlock_carver` are not imported, here or anywhere in
this package.

**The second opinion.**  Every world this rechecker can hold is small enough to
exhaust, so after the three conditions it also runs a plain breadth-first search
and asks the question the certificate was hired to answer without one: is a goal
state reachable at all?  That is not how certificates are meant to be checked --
the whole point of a certificate is that it is cheaper than the search -- and at
any real scale it would be unavailable.  It is here because it catches the one
thing the three conditions cannot: a certificate that is impeccable about a rule
set that is not the world.  When the two disagree in the direction that should
be impossible -- conditions green, goal reachable -- the verdict is
`INCONSISTENT` and the report says so in those words, because that combination
means this file has a bug, not that the certificate is good.
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from recheck.certificate import Certificate, CertificateError
from recheck.expr import ExprError
from recheck.ruleset import RuleSet, RuleSetError

ACCEPT = "ACCEPT"
REJECT = "REJECT"
INCONSISTENT = "INCONSISTENT"

MAX_WITNESSES = 6


@dataclass
class Verdict:
    verdict: str
    reasons: List[str] = field(default_factory=list)
    conditions: Dict[str, bool] = field(default_factory=dict)
    ruleset_conditions: Dict[str, bool] = field(default_factory=dict)
    witnesses: Dict[str, List[str]] = field(default_factory=dict)
    search: Dict[str, object] = field(default_factory=dict)
    stats: Dict[str, object] = field(default_factory=dict)
    ruleset_summary: Dict[str, object] = field(default_factory=dict)
    certificate_summary: Dict[str, object] = field(default_factory=dict)

    @property
    def accepted(self) -> bool:
        return self.verdict == ACCEPT

    def as_json(self) -> Dict[str, object]:
        return {
            "verdict": self.verdict,
            "reasons": list(self.reasons),
            "conditions": dict(sorted(self.conditions.items())),
            "ruleset_conditions": dict(sorted(self.ruleset_conditions.items())),
            "counterexamples": {k: list(v) for k, v in sorted(self.witnesses.items())},
            "second_opinion": dict(sorted(self.search.items())),
            "stats": dict(sorted(self.stats.items())),
            "ruleset": dict(sorted(self.ruleset_summary.items())),
            "certificate": dict(sorted(self.certificate_summary.items())),
            "method": "exhaustive enumeration over the product of the declared "
                      "domains; the transition relation is derived from the rules, "
                      "never read",
        }

    def report(self) -> str:
        lines = ["%-12s %s" % (self.verdict, self.certificate_summary.get("name", "?"))]
        lines.append("  rule set   %s (%s states, %s rules)"
                     % (self.ruleset_summary.get("name"),
                        self.ruleset_summary.get("n_states"),
                        self.ruleset_summary.get("n_rules")))
        lines.append("  claim      %s" % self.certificate_summary.get("claim"))
        lines.append("  predicate  %s" % self.certificate_summary.get("predicate"))
        for name, value in sorted(self.ruleset_conditions.items()):
            lines.append("  rules  %-20s %s" % (name, "ok" if value else "FAILED"))
        for name, value in sorted(self.conditions.items()):
            lines.append("  cert   %-20s %s" % (name, "ok" if value else "FAILED"))
        for name, found in sorted(self.witnesses.items()):
            for witness in found:
                lines.append("    %s: %s" % (name, witness))
        if self.search:
            lines.append("  second opinion: %s" % self.search.get("says"))
            plan = self.search.get("witness_plan")
            if plan:
                lines.append("    plan (%d actions): %s"
                             % (len(plan), " ".join(str(p) for p in plan)))
        for reason in self.reasons:
            lines.append("  -> %s" % reason)
        return "\n".join(lines)


def _binding_ok(certificate: Certificate, ruleset: RuleSet) -> Optional[str]:
    binds = certificate.binds_ruleset
    if not binds:
        return None
    name = binds.get("name")
    if name is not None and name != ruleset.name:
        return ("the certificate is bound to rule set %r but was checked against "
                "%r" % (name, ruleset.name))
    digest = binds.get("sha256")
    if digest and ruleset.sha256 and digest != ruleset.sha256:
        return ("the certificate is bound to rule set sha256 %s but this file "
                "hashes to %s" % (digest[:16], ruleset.sha256[:16]))
    return None


def _bfs(ruleset: RuleSet, states: Sequence[tuple], rows, sources: Sequence[int],
         is_goal: Sequence[bool]) -> Tuple[bool, Optional[List[str]], Optional[int], int]:
    """Reach a goal from any source?  Returns (found, plan, source, n_visited)."""
    origin: Dict[int, Tuple[int, str]] = {}
    seen = set(sources)
    root: Dict[int, int] = {i: i for i in sources}
    queue = deque(sources)
    for index in sources:
        if is_goal[index]:
            return True, [], index, len(seen)
    while queue:
        index = queue.popleft()
        for a, action in enumerate(ruleset.actions):
            target = rows[index][a]
            if target < 0 or target in seen:
                continue
            seen.add(target)
            origin[target] = (index, action)
            root[target] = root[index]
            if is_goal[target]:
                plan: List[str] = []
                cursor = target
                while cursor in origin:
                    cursor, label = origin[cursor]
                    plan.append(label)
                plan.reverse()
                return True, plan, root[target], len(seen)
            queue.append(target)
    return False, None, None, len(seen)


def shortest_plan(ruleset: RuleSet) -> Optional[List[str]]:
    """A shortest action sequence from init to a goal, or None if there is none.

    Exposed for the anchors: a rule set whose stated optimum is 6 and whose
    derived relation says 7 has been mistranscribed, and that is worth finding
    out from the fixture rather than from a verdict.
    """
    states = ruleset.states()
    rows = ruleset.transitions()
    inside = [ruleset.constraint(state) for state in states]
    is_goal = [inside[i] and ruleset.goal(state) for i, state in enumerate(states)]
    index_of = {state: i for i, state in enumerate(states)}
    sources = [index_of[state] for state in ruleset.init]
    found, plan, _source, _visited = _bfs(ruleset, states, rows, sources, is_goal)
    return plan if found else None


def recheck(ruleset: RuleSet, certificate: Certificate,
            max_witnesses: int = MAX_WITNESSES) -> Verdict:
    """Re-derive the three conditions from the rule set and the certificate."""
    verdict = Verdict(verdict=ACCEPT)
    verdict.ruleset_summary = ruleset.summary()
    verdict.certificate_summary = certificate.summary()

    binding = _binding_ok(certificate, ruleset)
    if binding is not None:
        verdict.verdict = REJECT
        verdict.reasons.append(binding)
        verdict.conditions["ruleset_binding"] = False
        return verdict
    if certificate.binds_ruleset:
        verdict.conditions["ruleset_binding"] = True

    # The rule set's own dues, before the certificate is looked at.  A world
    # whose step is not single-valued cannot support any certificate, and
    # saying so here keeps that failure from being reported as the
    # certificate's.
    try:
        obligations = ruleset.obligations(max_witnesses=max_witnesses)
    except (ExprError, RuleSetError) as exc:
        verdict.verdict = REJECT
        verdict.ruleset_conditions["rules_evaluate"] = False
        verdict.reasons.append(
            "the rule set does not evaluate: %s. A world description that "
            "raises is refused, never treated as though the offending state "
            "did not exist." % exc)
        return verdict
    verdict.ruleset_conditions = dict(obligations.conditions)
    for name, found in obligations.witnesses.items():
        verdict.witnesses[name] = list(found)
    if not obligations.holds:
        verdict.verdict = REJECT
        verdict.reasons.append(
            "the rule set does not discharge its own obligations, so nothing "
            "can be certified against it")
        return verdict

    try:
        predicate = certificate.compile(ruleset)
    except CertificateError as exc:
        verdict.verdict = REJECT
        verdict.reasons.append(str(exc))
        verdict.conditions["predicate_wellformed"] = False
        return verdict
    verdict.conditions["predicate_wellformed"] = True

    states = ruleset.states()
    try:
        rows = ruleset.transitions()
        inside = [ruleset.constraint(state) for state in states]
        is_goal = [inside[i] and ruleset.goal(state) for i, state in enumerate(states)]
    except (ExprError, RuleSetError) as exc:         # pragma: no cover - obligations catch it
        verdict.verdict = REJECT
        verdict.ruleset_conditions["rules_evaluate"] = False
        verdict.reasons.append("the rule set does not evaluate: %s" % exc)
        return verdict

    # Evaluated state by state so that a predicate which raises on one state is
    # a rejection with that state named, not a traceback out of the tool.
    satisfies: List[bool] = []
    for state in states:
        try:
            satisfies.append(predicate(state))
        except ExprError as exc:
            verdict.verdict = REJECT
            verdict.conditions["predicate_wellformed"] = False
            verdict.witnesses["predicate_wellformed"] = [
                "%s: %s" % (ruleset.render_state(state), exc)]
            verdict.reasons.append(
                "the predicate does not evaluate to a boolean on every state, "
                "so there is no set of states for it to denote")
            return verdict
    index_of = {state: i for i, state in enumerate(states)}

    region = [i for i in range(len(states)) if satisfies[i] and inside[i]]

    closed_bad: List[str] = []
    for i in region:
        for a, action in enumerate(ruleset.actions):
            target = rows[i][a]
            if target < 0 or not satisfies[target]:
                if len(closed_bad) < max_witnesses:
                    closed_bad.append(
                        "%s -%s-> %s escapes"
                        % (ruleset.render_state(states[i]), action,
                           ruleset.render_state(states[target]) if target >= 0
                           else "<off-domain>"))

    goal_bad = [ruleset.render_state(states[i]) for i in range(len(states))
                if is_goal[i] and satisfies[i]][:max_witnesses]

    if certificate.kind == "inductive_invariant":
        init_bad = [ruleset.render_state(state) for state in ruleset.init
                    if not satisfies[index_of[state]]]
        verdict.conditions["inv_init"] = not init_bad
        verdict.conditions["inv_closed"] = not closed_bad
        verdict.conditions["goal_break"] = not goal_bad
        if init_bad:
            verdict.witnesses["inv_init"] = init_bad[:max_witnesses]
        sources = [index_of[state] for state in ruleset.init]
    else:
        verdict.conditions["region_nonempty"] = bool(region)
        verdict.conditions["region_closed"] = not closed_bad
        verdict.conditions["goal_break"] = not goal_bad
        if not region:
            verdict.witnesses["region_nonempty"] = [
                "no state in the declared space satisfies the pattern; a region "
                "with no members is closed and goal-free for free, and licenses "
                "nothing about any state the world can be in"
            ]
        sources = list(region)

    if closed_bad:
        key = "inv_closed" if certificate.kind == "inductive_invariant" else "region_closed"
        verdict.witnesses[key] = closed_bad
    if goal_bad:
        verdict.witnesses["goal_break"] = goal_bad

    verdict.stats = {
        "n_states": len(states),
        "n_wellformed": sum(1 for flag in inside if flag),
        "n_satisfying": len(region),
        "n_goal_states": sum(1 for flag in is_goal if flag),
        "n_transitions": len(states) * len(ruleset.actions),
    }

    # --------------------------------------------------- the second opinion
    if sources:
        found, plan, source, visited = _bfs(ruleset, states, rows, sources, is_goal)
    else:
        found, plan, source, visited = False, None, None, 0
    verdict.search = {
        "method": "breadth-first search over the same derived relation, sharing "
                  "nothing with the three conditions above",
        "from": ("the initial state" if certificate.kind == "inductive_invariant"
                 else "every state satisfying the pattern"),
        "n_sources": len(sources),
        "n_reached": visited,
        "goal_reachable": bool(found),
        "says": ("a goal state IS reachable -- the claim is false of this rule set"
                 if found else
                 "no goal state is reachable -- the claim is true of this rule set"),
    }
    if found:
        verdict.search["witness_plan"] = plan
        if source is not None:
            verdict.search["witness_source"] = ruleset.render_state(states[source])

    conditions_pass = all(verdict.conditions.values())
    if conditions_pass and found:
        verdict.verdict = INCONSISTENT
        verdict.reasons.append(
            "the three conditions hold and yet a goal state is reachable. That "
            "combination is impossible if this checker is correct, so it is "
            "reported as a defect in the checker, never as an accepted "
            "certificate.")
        return verdict
    if not conditions_pass:
        verdict.verdict = REJECT
        failed = sorted(name for name, ok in verdict.conditions.items() if not ok)
        verdict.reasons.append("failed: %s" % ", ".join(failed))
        if found:
            verdict.reasons.append(
                "and the claim itself is false of this rule set: the second "
                "opinion reached a goal state in %d actions"
                % (len(plan) if plan is not None else 0))
        else:
            verdict.reasons.append(
                "the claim may still be true -- the second opinion found no "
                "reachable goal -- but this certificate does not establish it")
        return verdict

    verdict.reasons.append(
        "all three conditions hold over %d states, and an independent search "
        "agrees the goal is unreachable" % verdict.stats["n_states"])
    return verdict
