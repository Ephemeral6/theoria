"""Hand a deadlock theorem to a planner that has no pruning hook.

`fd_adapter.search` takes a `prune` callable and Fast Downward does not -- the
adapter says so in `choose_tier` clause 3, and it is a fact about the backend
rather than a gap in the adapter.  So the question "does a proved deadlock speed
up *the planner*", which is what Theoria 1.9 actually promises, cannot be asked
of the FD rungs by the route the bundled rung uses.

It can be asked by a different route: put the theorem in the task.

## The compilation, and why it preserves the answer

A theorem says: pattern `P` is closed under the action set, and no state
containing `P` is a goal.  Therefore every state containing `P` is dead.

The compilation forbids exactly the transitions that *enter* `P` -- an action is
blocked when its effect would produce a state containing every atom of `P`.  What
that removes from the state space is a set of states from which no goal is
reachable, so:

* every plan of the original task survives (a plan never enters a dead state, or
  it would never reach the goal);
* every plan of the compiled task is a plan of the original (the compiled action
  set is a subset of the original one, with the same effects);

hence plan existence and **optimal plan length are unchanged**.  Same guarantee
as the pruner, arrived at by editing the task instead of the search.

## What is guarded, and the assumption that is checked rather than assumed

The theorems this rig proves are conjunctions of ground `at(box, cell)` atoms --
the carver restricts its candidate atoms to the predicates the goal mentions, and
in sokoban the goal is about box positions.  `push` is the only schema that adds
`at`, so it is the only one guarded.  Those facts are **checked** in
`guardable()`, which raises rather than emitting a domain whose guard does not
match the theorems it claims to carry.

Two directions of mismatch, and only one of them is cheap.  A guard that misses a
transition costs the dividend and nothing else.  A guard that blocks a transition
the theorem does not condemn destroys optimality -- and the pair guard reads the
**pre-state**, so a pattern naming one box twice does exactly that.  An earlier
draft of this module contemplated only the first direction and let the second
through; `guardable()` clause 3 is that hole closed.

## The safety net

Nothing here is trusted.  `bench/dividend.py` validates every plan the compiled
task produces against the **original** domain, using the rig's own independent
replay validator, and asserts the length matches the unguarded optimal rung's.
A guard that is too strong shows up as a longer plan or no plan at all; a guard
that is too weak shows up as no dividend, which is a disappointment rather than a
falsehood.  See `dividend.py` for where those two checks are made.

## The cost side of the ledger

The guard is not free and the artifacts do not pretend it is.  `deadpair` is a
4-ary static predicate, so the problem file grows quadratically in the number of
pair theorems, and the universal precondition makes FD's translator do
noticeably more work.  Both the translator's time and its task-size figure are
recorded, so "the search expanded fewer nodes" and "the run got faster" stay
separate claims.
"""

import os
import re
from typing import Dict, List, Optional, Sequence, Tuple

from engines.deadlock_carver.carve import Theorem
from engines.fd_adapter.pddl import Domain, Problem

# Three guards, because the obvious way of writing the second one does not fit
# through the optimal rungs and the way that does costs something.
#
# **singleton** is `fixtures/data/sokoban_domain.pddl` with one static predicate
# and one negative precondition added to `push`: a box may not be pushed onto a
# cell proved dead for it.  That is still STRIPS, so every rung accepts it.
#
# **full** adds the pair guard -- "there is no other box sitting where it would
# complete a dead pair with the position I am about to create" -- as a
# universally quantified negated conjunction, hence `:adl`.  FD's `normalize.py`
# turns any `forall` precondition into an **axiom**, and `astar(lmcut())` and
# `astar(ipdb())` both refuse a task with axioms (`This configuration does not
# support axioms!`, driver exit 34).  `astar(blind())` accepts it.
#
# **indexed** is the same pair guard with the quantifier removed -- see
# `indexed_domain()`.  Pure STRIPS, no axioms, and the optimal rungs take it.
# It exists because an adversarial review of this run built it to refute the
# claim that pair deadlocks could not reach those rungs at all.  They can.  What
# they cost is the finding that replaced the claim: FD compiles a negative
# precondition on a fluent into one operator copy per other value of that
# variable, the task grows about an order of magnitude, and `lmcut` comes out
# *slower* with the pair theorems than without them.
_MOVE = """
  (:action move
    :parameters (?from - cell ?to - cell ?d - dir)
    :precondition (and (at-player ?from) (clear ?to) (adj ?from ?to ?d))
    :effect (and (at-player ?to) (not (at-player ?from))
                 (clear ?from) (not (clear ?to))))
"""

_EFFECT = """
    :effect (and (at-player ?from) (not (at-player ?p)) (clear ?p)
                 (at ?b ?to) (not (at ?b ?from))
                 (not (clear ?to)) (not (clear ?from)))))
"""

_HEADER_TEMPLATE = """;; Sokoban with the deadlock theorems compiled in (%(kind)s guard).
;; Generated by bench/compile_theorems.py -- do not edit by hand.
;;
;; Identical to fixtures/data/sokoban_domain.pddl except that `push` may not
;; create a state matching a proved dead pattern.  `dead1` and `deadpair` are
;; static -- no action adds or deletes them -- so they cost grounding, not search.
(define (domain %(name)s)
  (:requirements %(requirements)s)
  (:types cell box dir)
  (:predicates
    (at-player ?c - cell)
    (at ?b - box ?c - cell)
    (clear ?c - cell)
    (adj ?from - cell ?to - cell ?d - dir)
    (dead1 ?b - box ?c - cell)
    (deadpair ?b1 - box ?c1 - cell ?b2 - box ?c2 - cell)%(extra)s)
"""


def _header(kind: str, requirements: str, extra: Sequence[str] = ()) -> str:
    """The domain preamble. `extra` adds predicate declarations inside the block.

    Inside, not after: PDDL allows one `:predicates` section, and appending a
    second one is the kind of thing a parser reports three layers away from the
    line that caused it.
    """
    return _HEADER_TEMPLATE % {
        "kind": kind, "name": "sokoban-guarded", "requirements": requirements,
        "extra": "".join("\n    %s" % line for line in extra),
    }


SINGLETON_DOMAIN = (
    _header("singleton", ":strips :typing :negative-preconditions")
    + _MOVE
    + """
  (:action push
    :parameters (?p - cell ?from - cell ?to - cell ?b - box ?d - dir)
    :precondition (and (at-player ?p) (at ?b ?from) (clear ?to)
                       (adj ?p ?from ?d) (adj ?from ?to ?d)
                       (not (dead1 ?b ?to)))"""
    + _EFFECT
)

FULL_DOMAIN = (
    _header("full", ":adl :typing")
    + _MOVE
    + """
  (:action push
    :parameters (?p - cell ?from - cell ?to - cell ?b - box ?d - dir)
    :precondition (and (at-player ?p) (at ?b ?from) (clear ?to)
                       (adj ?p ?from ?d) (adj ?from ?to ?d)
                       (not (dead1 ?b ?to))
                       (forall (?ob - box ?oc - cell)
                         (or (not (deadpair ?b ?to ?ob ?oc))
                             (not (at ?ob ?oc)))))"""
    + _EFFECT
)

def indexed_domain(max_arity: int) -> str:
    """The pair guard without a `forall`, and therefore without axioms.

    The `full` guard's universal precondition is what FD's `normalize.py` turns
    into an axiom, and the axiom is what `astar(lmcut())` and `astar(ipdb())`
    refuse.  Nothing about *pair deadlocks* requires quantification, though --
    only the fact that a pattern's partner set has a size the schema does not
    know.  Give the schema that size and the quantifier disappears:

    * a static `npair<k> ?b ?to` says "(box, cell) has exactly k dead partners";
    * static `deadpair<i> ?b ?to ?ob ?oc` names the i-th of them;
    * one `push-pair<k>` schema per arity binds k partner pairs through those
      statics and adds one ground `(not (at ?ob_i ?oc_i))` per partner.

    The statics are functional in `(?b, ?to, i)`, so grounding binds the extra
    parameters uniquely and the ground action count is unchanged.  Requirements
    stay `:strips :typing :negative-preconditions`.

    Exactly one `npair<k>` holds per `(box, cell)`, so exactly one schema applies
    to any push -- including `push-pair0` for the pairs with no dead partners,
    which is why that fact has to be emitted for *every* (box, cell) rather than
    only for the interesting ones.  Omitting it does not weaken the guard, it
    blocks the push entirely.

    This encoding was found by an adversarial review of this run, which built it
    to refute the claim that pair deadlocks "cannot reach" the admissible rungs.
    It does reach them.  What it costs is in `DIVIDEND.md`: FD compiles a
    negative precondition on a fluent into one operator copy per other value of
    that variable, so the task grows about an order of magnitude and the optimal
    rungs come out *slower*.  That is a measurement, and it replaces a prediction.
    """
    extra = ["(npair%d ?b - box ?c - cell)" % k for k in range(max_arity + 1)]
    extra += [
        "(deadpair%d ?b - box ?c - cell ?ob - box ?oc - cell)" % index
        for index in range(1, max_arity + 1)
    ]
    parts = [
        _header("indexed", ":strips :typing :negative-preconditions", extra),
        _MOVE,
    ]

    for arity in range(max_arity + 1):
        params = "".join(
            " ?ob%d - box ?oc%d - cell" % (index, index)
            for index in range(1, arity + 1)
        )
        binds = "".join(
            "\n                       (deadpair%d ?b ?to ?ob%d ?oc%d)"
            % (index, index, index)
            for index in range(1, arity + 1)
        )
        excludes = "".join(
            "\n                       (not (at ?ob%d ?oc%d))" % (index, index)
            for index in range(1, arity + 1)
        )
        parts.append(
            """
  (:action push-pair%d
    :parameters (?p - cell ?from - cell ?to - cell ?b - box ?d - dir%s)
    :precondition (and (at-player ?p) (at ?b ?from) (clear ?to)
                       (adj ?p ?from ?d) (adj ?from ?to ?d)
                       (not (dead1 ?b ?to))
                       (npair%d ?b ?to)%s%s)"""
            % (arity, params, arity, binds, excludes)
            + _EFFECT.rstrip()[:-1]      # drop the domain's closing paren
        )
    parts.append(")\n")
    return "".join(parts)


def indexed_partners(theorems: Sequence[Theorem]) -> Dict[Tuple[str, str], List[Tuple[str, str]]]:
    """`(box, cell)` -> its dead partners, both orders, in a fixed order."""
    partners: Dict[Tuple[str, str], List[Tuple[str, str]]] = {}
    for theorem in theorems:
        if theorem.size != 2:
            continue
        (_, b1, c1), (_, b2, c2) = theorem.pattern
        partners.setdefault((b1, c1), []).append((b2, c2))
        partners.setdefault((b2, c2), []).append((b1, c1))
    return {key: sorted(set(value)) for key, value in sorted(partners.items())}


def indexed_facts(theorems: Sequence[Theorem], boxes: Sequence[str],
                  cells: Sequence[str]) -> List[str]:
    """`npair<k>` for every (box, cell), and `deadpair<i>` for the partners."""
    partners = indexed_partners(theorems)
    facts = []
    for box in sorted(boxes):
        for cell in sorted(cells):
            found = partners.get((box, cell), [])
            facts.append("(npair%d %s %s)" % (len(found), box, cell))
            for index, (other_box, other_cell) in enumerate(found, start=1):
                facts.append(
                    "(deadpair%d %s %s %s %s)"
                    % (index, box, cell, other_box, other_cell)
                )
    return facts


def indexed_arity(theorems: Sequence[Theorem]) -> int:
    partners = indexed_partners(theorems)
    return max((len(value) for value in partners.values()), default=0)


GUARDS = {"singleton": SINGLETON_DOMAIN, "full": FULL_DOMAIN, "indexed": None}

GUARD_PREDICATE = "at"                   # the predicate the theorems talk about
GUARD_SCHEMA = "push"                    # the only schema that adds it


class NotGuardable(RuntimeError):
    """A theorem this compilation cannot express, stated rather than skipped."""


def guardable(domain: Domain, theorems: Sequence[Theorem]) -> None:
    """Check the two assumptions the guard rests on, and raise on either.

    1. Every theorem atom is `at(box, cell)`.  The guard tests `dead1`/`deadpair`
       on `push`'s `?b`/`?to`, so an atom about anything else would not be
       covered and the compiled task would keep a transition the theorem forbids.
    2. `push` is the only schema adding `at`.  If `move` (or anything added
       later) could add a box position, guarding `push` alone would leave a way
       into the dead region.

    All three are true of the sokoban fixture today.  None is true by definition,
    which is why they are asserted at compile time rather than believed.
    3. **No pair theorem names the same box twice.**  This one is not about
       coverage, it is about the *other* direction, and an earlier draft of this
       module missed it because its docstring only contemplated under-guarding.

       The pair guard is evaluated against the **pre-state**: it asks whether
       some other box already sits where it would complete a dead pair with the
       position about to be created.  `at(?ob,?oc)` in the precondition equals
       its value in the successor only when `?ob` is not the box being pushed --
       the pushed box still holds its *old* position while the precondition is
       read, and loses it in the successor.  So for a pattern naming one box
       twice, the guard blocks transitions that *leave* the pattern instead of
       entering it.  That is strictly stronger than the theorem, and stronger is
       the unsound direction: measured, it took `far4`'s optimal length from 11
       to 25 under a pattern no reachable state even satisfies.

       `carve()` cannot currently emit such a pattern -- two positions of one box
       are mutex, so `prove()` rejects it as describing no reachable state. That
       is a property of a *different module*, which is exactly the kind of thing
       this function exists not to take on trust. `tools/p13_fd_dividend.py`
       skips these patterns explicitly and says why; this check is that reasoning
       restored after being dropped.
    """
    for theorem in theorems:
        for atom in theorem.pattern:
            if atom[0] != GUARD_PREDICATE or len(atom) != 3:
                raise NotGuardable(
                    "theorem atom %r is not %s(box,cell); the guard would not "
                    "cover it" % (atom, GUARD_PREDICATE)
                )
        if theorem.size > 2:
            raise NotGuardable(
                "pattern of size %d; the guard expresses singletons and pairs"
                % theorem.size
            )
        if theorem.size == 2 and theorem.pattern[0][1] == theorem.pattern[1][1]:
            raise NotGuardable(
                "pair theorem %r names box %r twice; the pre-state guard would "
                "block transitions that LEAVE the pattern rather than enter it, "
                "which is the unsound direction -- see this function's docstring"
                % (theorem.rendering(), theorem.pattern[0][1])
            )

    adders = sorted(
        action.name
        for action in domain.actions
        if any(effect[0] == GUARD_PREDICATE for effect in action.add_effects)
    )
    if adders != [GUARD_SCHEMA]:
        raise NotGuardable(
            "schemas adding %s are %s; the guard only covers %r"
            % (GUARD_PREDICATE, adders, GUARD_SCHEMA)
        )


def guard_facts(theorems: Sequence[Theorem], guard: str = "full"
                ) -> Tuple[List[str], List[str]]:
    """The static facts that turn the theorems into preconditions.

    Pairs are emitted in **both** orders.  The guard fires on the box being
    pushed, and either box of a dead pair can be the one that completes it, so a
    single ordering would catch the pattern only when it is created from one
    side -- which is exactly the kind of half-guard that shows up as a smaller
    dividend rather than as an error.

    Under the `singleton` guard the pair facts are not emitted at all rather
    than emitted and ignored: `push` has no precondition reading `deadpair`
    there, so writing them would inflate the task size the artifacts report
    without changing a single transition -- a cost charged against a dividend
    that was never collected.
    """
    singles: List[str] = []
    pairs: List[str] = []
    for theorem in theorems:
        if theorem.size == 1:
            (_, box, cell), = theorem.pattern
            singles.append("(dead1 %s %s)" % (box, cell))
        elif guard == "full":
            # `indexed` carries the same pairs through `indexed_facts` instead,
            # in the numbered form its schemas bind against.
            (_, b1, c1), (_, b2, c2) = theorem.pattern
            pairs.append("(deadpair %s %s %s %s)" % (b1, c1, b2, c2))
            pairs.append("(deadpair %s %s %s %s)" % (b2, c2, b1, c1))
    return sorted(set(singles)), sorted(set(pairs))


def guarded_problem_text(problem_text: str, theorems: Sequence[Theorem],
                         guard: str = "full",
                         problem: Optional[Problem] = None) -> str:
    """The original problem with the guard facts spliced into `:init`.

    Splicing text rather than re-rendering the problem is deliberate: the
    original `:init` reaches Fast Downward byte for byte, so a difference in the
    measurement cannot come from this module having re-serialised the instance
    slightly differently.
    """
    singles, pairs = guard_facts(theorems, guard)
    facts = singles + pairs
    if guard == "indexed":
        boxes = [name for name, kind in problem.objects if kind == "box"]
        cells = [name for name, kind in problem.objects if kind == "cell"]
        facts = singles + indexed_facts(theorems, boxes, cells)
    marker = "(:goal"
    index = problem_text.rindex(marker)
    head, tail = problem_text[:index], problem_text[index:]

    # `:init` is the block just before `:goal`; close it, add ours, reopen nothing.
    closing = head.rindex(")")
    block = "\n    ;; deadlock theorems, compiled in by bench/compile_theorems.py\n"
    block += "\n".join("    %s" % fact for fact in facts)
    guarded_head = head[:closing] + block + "\n" + head[closing:]
    return (
        guarded_head.replace("(:domain sokoban)", "(:domain sokoban-guarded)")
        + tail
    )


def write_guarded(directory: str, name: str, problem_text: str,
                  theorems: Sequence[Theorem], guard: str = "full",
                  problem: Optional[Problem] = None) -> Tuple[str, str]:
    """Write the guarded domain and problem for one guard; returns their paths.

    `problem` is needed only by the `indexed` guard, which emits one `npair<k>`
    fact per (box, cell) and therefore has to know what the objects are.
    """
    if guard not in GUARDS:
        raise ValueError("unknown guard %r; have %s" % (guard, ", ".join(sorted(GUARDS))))
    if guard == "indexed" and problem is None:
        raise ValueError("the indexed guard needs the parsed problem for its objects")
    os.makedirs(directory, exist_ok=True)
    domain_path = os.path.join(directory, "sokoban_guarded_%s_domain.pddl" % guard)
    problem_path = os.path.join(directory, "%s_guarded_%s.pddl" % (name, guard))
    text = (indexed_domain(indexed_arity(theorems)) if guard == "indexed"
            else GUARDS[guard])
    with open(domain_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    with open(problem_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(guarded_problem_text(problem_text, theorems, guard, problem))
    return domain_path, problem_path


def guard_size(theorems: Sequence[Theorem], guard: str = "full",
               problem: Optional[Problem] = None) -> Dict[str, int]:
    """What the guard costs the problem file, before the planner sees it."""
    singles, pairs = guard_facts(theorems, guard)
    if guard == "indexed" and problem is not None:
        boxes = [name for name, kind in problem.objects if kind == "box"]
        cells = [name for name, kind in problem.objects if kind == "cell"]
        pairs = indexed_facts(theorems, boxes, cells)
    return {
        "guard": guard,
        "dead1_facts": len(singles),
        "deadpair_facts": len(pairs),
        "guard_facts_total": len(singles) + len(pairs),
        "max_pair_arity": indexed_arity(theorems) if guard == "indexed" else None,
        # How much of the proved evidence this guard can actually carry.  The
        # singleton guard leaves every pair theorem on the floor, and the table
        # has to say so next to the dividend it reports.
        "theorems_total": len(theorems),
        "theorems_expressed": (
            len(singles) if guard == "singleton" else len(theorems)
        ),
    }


_PUSH_PAIR = re.compile(r"^\(push-pair\d+\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)")


def to_original_plan(plan: Sequence[str], guard: str) -> List[str]:
    """A guarded task's plan, in the original domain's vocabulary.

    Only `indexed` needs this: it splits `push` into `push-pair<k>` schemas with
    extra parameters bound to the dead partners, so its plan steps neither name
    nor arity-match the original action set.  The mapping is mechanical -- drop
    the arity suffix, keep the first five arguments, which are `push`'s own
    parameters in `push`'s own order.

    This exists because the validator refused the plan, which is the outcome the
    validator is for.  Renaming a schema is a change to the *task*, and a
    benchmark that quietly accepted a plan written in a vocabulary the original
    domain does not have would have lost the only check standing between the
    compilation and a wrong number.
    """
    if guard != "indexed":
        return list(plan)
    out = []
    for step in plan:
        match = _PUSH_PAIR.match(step)
        out.append("(push %s)" % " ".join(match.groups()) if match else step)
    return out


def guardable_guards(theorems: Sequence[Theorem]) -> Tuple[str, ...]:
    """Which guards can carry these theorems at all.

    `singleton` is always available; the two pair guards are pointless when the
    carver produced no pair theorem, and emitting them anyway would put rows in
    the table whose "before" and "after" are the same task.
    """
    if any(theorem.size == 2 for theorem in theorems):
        return ("singleton", "full", "indexed")
    return ("singleton",)
