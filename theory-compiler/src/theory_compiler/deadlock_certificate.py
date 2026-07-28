"""Reading a `deadlock_carver` conditional-unsolvability certificate.

The third certificate schema this compiler consumes, and the first that is not a
statement about a level as a whole. `lp_potential` and `ic3_pdr` both answer
"can the goal be reached from `s₀`". This one answers a different question, and
Theoria 1.9 is explicit about why it is the more useful one in the wild: whole
levels are rarely unsolvable, and dead regions are everywhere. Each dead region
is a small unsolvability theorem with a condition attached.

    <pattern>  AND  not-goal   =>   dead

Two obligations, and neither is taken on the producer's word:

| obligation | what is recomputed here |
|---|---|
| **closure** | from every well-formed state containing the pattern, every legal action leads to a state containing it |
| **excludes the goal** | no well-formed state containing the pattern is a goal state |

**Why "well-formed" and not "reachable".** The producer's claim is about
reachable states, and re-checking it on the reachable set only would make the
closure obligation circular in exactly the way `ic3_certificate` refuses: the
set you are closed under would be the set you computed by being closed. So the
obligations are recomputed over the whole *well-formed* state space — every
tuple that puts each thing in one cell and no two things in the same one, 3360
of them on this fixture against 3352 reachable. Well-formedness is not a
convenience: it is the content of the producer's h² mutex fixpoint, arrived at
from the other side (see `strips_encoding`), and closure genuinely fails without
it.

**The pattern is the only thing this reader takes from the certificate.** The
task — cells, ground actions, preconditions, effects, goal — is parsed and
grounded on this side by `strips.py`. A certificate that supplied its own action
set would be closed under an action set of its own choosing, which is the same
hazard `ic3_certificate` names when it refuses a `moves` field. What the
certificate's *bookkeeping* is good for is cross-checking: if our grounding and
theirs disagree about how many ground actions the task has, or about which ones
delete a pattern atom, then one of us has the wrong task and neither result
means anything. `cross_check` raises on any such disagreement.

**A pattern nothing satisfies is refused.** `recheck` requires a well-formed
witness. A conditional theorem with an unsatisfiable condition passes every
obligation, prints an empty axiom set, and says nothing — a failure mode this
repository has already met once, from the other direction, and does not intend
to meet again.
"""

from __future__ import annotations

import json
from typing import Dict, List, Optional, Sequence, Tuple

from .certificate import CertificateError
from .strips import Atom, GroundAction, StripsTask
from .strips_encoding import PositionalEncoding, State

SCHEMA = "deadlock_carver/conditional_unsolvability_certificate@1"

CLOSURE_FORMS = ("no_deleting_action", "deleting_actions_blocked")


class DeadlockCertificate:
    """A pattern of ground atoms, claimed dead wherever it holds."""

    def __init__(self, claim: str, domain: str, problem: str,
                 pattern: Sequence[Atom], closure: str, n_deleting_actions: int,
                 blocked_actions: Sequence[Dict], goal_conflict: Optional[Dict],
                 coverage: str, produced_by: str, provenance: str, path: str = ""):
        self.claim = claim
        self.domain = domain
        self.problem = problem
        self.pattern: Tuple[Atom, ...] = tuple(sorted(pattern))
        self.closure = closure
        self.n_deleting_actions = n_deleting_actions
        self.blocked_actions = [dict(b) for b in blocked_actions]
        self.goal_conflict = dict(goal_conflict) if goal_conflict else None
        self.coverage = coverage
        self.produced_by = produced_by
        self.provenance = provenance
        self.path = path

    @property
    def pattern_text(self) -> str:
        """Rendered here, from `pattern`. The document's own rendering is checked
        against this one and a disagreement is fatal — a human-readable line that
        does not match the machine-readable one is worse than no line."""
        return " AND ".join(str(a) for a in self.pattern)

    def deleting_actions(self, task: StripsTask) -> List[GroundAction]:
        """The ground actions whose delete list touches the pattern.

        These are the ones the closure obligation has to dispose of, and the
        producer reports how many it found. Counting them here independently is
        the cheapest disagreement detector there is.
        """
        return [a for a in task.actions if set(a.dele) & set(self.pattern)]


# --------------------------------------------------------------------- loading

def load_deadlock_certificate(path: str, task: StripsTask,
                              encoding: Optional[PositionalEncoding] = None
                              ) -> DeadlockCertificate:
    """Read, cross-check against the task, and re-derive both obligations."""
    with open(path, encoding="utf-8") as handle:
        doc = json.load(handle)

    if doc.get("schema") != SCHEMA:
        raise CertificateError(
            "expected schema %r, got %r — this reader implements one schema and "
            "will not guess at another" % (SCHEMA, doc.get("schema")))

    for key in ("domain", "problem", "pattern", "closure"):
        if key not in doc:
            raise CertificateError("certificate is missing %r" % key)

    pattern = []
    for entry in doc["pattern"]:
        if not isinstance(entry, list) or not entry:
            raise CertificateError("a pattern entry is not a `[predicate, arg...]` "
                                   "list: %r" % (entry,))
        pattern.append(Atom(str(entry[0]), tuple(str(a) for a in entry[1:])))
    if not pattern:
        raise CertificateError(
            "the pattern is empty, so it holds in every state. The theorem would "
            "then say the level is unsolvable from anywhere, including states it "
            "is solvable from.")
    if len(set(pattern)) != len(pattern):
        raise CertificateError("the pattern repeats an atom: %r"
                               % [str(a) for a in pattern])

    if doc["closure"] not in CLOSURE_FORMS:
        raise CertificateError("unknown closure form %r; this reader knows %s"
                               % (doc["closure"], list(CLOSURE_FORMS)))

    cert = DeadlockCertificate(
        claim=doc.get("claim", "conditional unsolvability"),
        domain=doc["domain"],
        problem=doc["problem"],
        pattern=pattern,
        closure=doc["closure"],
        n_deleting_actions=int(doc.get("n_deleting_actions", -1)),
        blocked_actions=doc.get("blocked_actions", []),
        goal_conflict=doc.get("goal_conflict"),
        coverage=str(doc.get("coverage", "")),
        produced_by=doc.get("produced_by", "unknown"),
        provenance=str(doc.get("provenance", {}).get("source", path)),
        path=path,
    )

    stated = doc.get("pattern_text")
    if stated is not None and stated.strip() != cert.pattern_text:
        raise CertificateError(
            "the certificate's `pattern_text` reads %r but its `pattern` renders "
            "as %r. One of the two is what a reader will believe."
            % (stated, cert.pattern_text))

    if encoding is None:
        encoding = PositionalEncoding(task)
    cross_check(cert, task)
    recheck(cert, encoding)
    return cert


# ---------------------------------------------------------------- cross-check

def cross_check(cert: DeadlockCertificate, task: StripsTask) -> None:
    """The producer's bookkeeping against ours. Disagreement is fatal.

    None of this is an obligation — the obligations are re-derived in `recheck`
    and do not consult a single field checked here. What this establishes is
    that the two sides are talking about the *same task*. A certificate that
    passed the obligations against a task other than the one it was proved on
    would be a true theorem about the wrong world.
    """
    if cert.domain != task.domain:
        raise CertificateError("certificate is about domain %r, the task is %r"
                               % (cert.domain, task.domain))
    if cert.problem != task.problem:
        raise CertificateError("certificate is about problem %r, the task is %r"
                               % (cert.problem, task.problem))

    for atom in cert.pattern:
        if atom.name not in task.fluent_predicates:
            raise CertificateError(
                "the pattern mentions %r, which is not a fluent of this task "
                "(fluents: %s). A pattern over static atoms would be a statement "
                "about the level file, not about a state."
                % (atom.name, list(task.fluent_predicates)))
        for arg in atom.args:
            task.type_of(arg)              # raises if the object is not declared

    if cert.coverage:
        try:
            examined, total = (int(x) for x in cert.coverage.split("/"))
        except ValueError:
            raise CertificateError("`coverage` is not `<examined>/<total>`: %r"
                                   % cert.coverage)
        if total != len(task.actions):
            raise CertificateError(
                "the certificate examined %d ground action(s) out of %d; this "
                "track grounds the same task to %d. The two sides do not have the "
                "same action set, so neither side's theorem is about the other's "
                "world." % (examined, total, len(task.actions)))
        if examined != total:
            raise CertificateError(
                "the certificate examined only %d of %d ground actions; a closure "
                "claim that skipped some is not a closure claim" % (examined, total))

    ours = cert.deleting_actions(task)
    if cert.n_deleting_actions >= 0 and cert.n_deleting_actions != len(ours):
        raise CertificateError(
            "the certificate reports %d ground action(s) deleting a pattern atom; "
            "this track finds %d: %s"
            % (cert.n_deleting_actions, len(ours), [str(a) for a in ours]))
    if cert.closure == "no_deleting_action" and ours:
        raise CertificateError(
            "the certificate claims no action deletes a pattern atom, but this "
            "track grounds %d that do: %s" % (len(ours), [str(a) for a in ours]))
    if cert.closure == "deleting_actions_blocked" and not ours:
        raise CertificateError(
            "the certificate claims deleting actions exist and are blocked, but "
            "this track grounds none at all")

    named = set()
    for blocked in cert.blocked_actions:
        rendering = blocked.get("action", "")
        action = task.action_named(rendering)
        if action is None:
            raise CertificateError(
                "the certificate blocks %r, which this track's grounding does not "
                "contain" % rendering)
        if action not in ours:
            raise CertificateError(
                "the certificate blocks %r, which deletes no pattern atom here"
                % rendering)
        named.add(action)
    missing = [a for a in ours if a not in named] if cert.blocked_actions else []
    if missing:
        raise CertificateError(
            "the certificate discharges %d of the %d deleting action(s); %s "
            "were left standing" % (len(named), len(ours), [str(a) for a in missing]))

    if cert.goal_conflict:
        atom_text = cert.goal_conflict.get("goal_atom")
        if atom_text and Atom.parse(atom_text) not in task.goal:
            raise CertificateError(
                "the certificate's goal conflict cites %r, which is not in this "
                "task's goal %s" % (atom_text, sorted(str(a) for a in task.goal)))


# -------------------------------------------------------------- the two proofs

def recheck(cert: DeadlockCertificate, encoding: PositionalEncoding) -> None:
    """Re-derive both obligations by exhaustion. Raises on failure.

    This is the adjudication step, and it consults no field the producer filled
    in — not `closure`, not `blocked_actions`, not `mutexes`. It walks the
    well-formed state space, keeps the states the pattern accepts, and asks the
    two questions directly.
    """
    task = encoding.task
    pattern = list(cert.pattern)

    holding = [s for s in encoding.states() if encoding.holds(s, pattern)]
    if not holding:
        raise CertificateError(
            "no well-formed state satisfies the pattern %s, so the theorem's "
            "condition is never met. Every obligation below would pass and the "
            "axiom set would print empty; it would still say nothing."
            % cert.pattern_text)

    escapes = [(s, a, encoding.apply(s, a))
               for s in holding for a in task.actions
               if encoding.legal(s, a) and not encoding.holds(encoding.apply(s, a), pattern)]
    if escapes:
        state, action, after = escapes[0]
        raise CertificateError(
            "closure fails: %s satisfies the pattern, %s is legal there, and it "
            "reaches %s, which does not — %d such escape(s) over the %d "
            "well-formed state(s) the pattern accepts. A pattern you can leave is "
            "not a dead region."
            % (dict(zip(encoding.slots, state)), action,
               dict(zip(encoding.slots, after)), len(escapes), len(holding)))

    winning = [s for s in holding if encoding.is_goal(s)]
    if winning:
        raise CertificateError(
            "goal exclusion fails: %s satisfies the pattern and is a goal state "
            "(%d such). The theorem would call a win dead."
            % (dict(zip(encoding.slots, winning[0])), len(winning)))


# ------------------------------------------------------------------- reporting

def bite(cert: DeadlockCertificate, encoding: PositionalEncoding,
         reachable_states: Sequence[State]) -> Dict[str, int]:
    """How much of the level the theorem actually rules out.

    "The theorem is true" and "the theorem is worth having" are different
    statements — the producer's own README says so and reports a node account
    rather than an adjective. The consumer's version of that account is how many
    reachable states the pattern covers, and whether the level was winnable in
    the first place.
    """
    pattern = list(cert.pattern)
    covered = [s for s in reachable_states if encoding.holds(s, pattern)]
    return {
        "reachable_states": len(reachable_states),
        "reachable_states_covered": len(covered),
        "well_formed_states_covered": len([s for s in encoding.states()
                                           if encoding.holds(s, pattern)]),
        "goal_reachable": int(any(encoding.is_goal(s) for s in reachable_states)),
    }
