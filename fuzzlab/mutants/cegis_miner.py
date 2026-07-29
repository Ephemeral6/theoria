"""`cegis_miner` mutants — fifteen defects, aimed one at a time.

The seam is `props/cegis_miner.py:_mine`, and it is the *only* engine call the
property module makes: all six invariants open with `result, transitions, _split
= _mine(world)` and everything else they do is re-derivation — by
`atoms.evaluate` for the four guard invariants, and by `oracles/motion.py` for
the two V-13 ones. So one seam covers the whole module, and no invariant reaches
the engine around it.

Three structural facts about this engine decide what a mutant here can be, and
each of them changes what a survivor means:

* **The seam returns a triple**, `(MiningResult, transitions, split)`, so a
  `corrupt` receives a tuple and edits the `MiningResult` inside it. Nothing here
  shadows a method, so `mut.touched` is never needed — every mutant below edits a
  dataclass field and the inert check sees it in the `repr`.

* **`skipped` is decided before the mutant exists.** `NoSeparatingGuard` and
  `Unminable` are raised *inside* `_mine`, i.e. inside `original(*args)`, so
  `corrupt` is never called and the driver's `record` stays empty — the world is
  counted `inert` and leaves the denominator. That is the right accounting, and
  it means **no mutant on this seam can move the skipped rate**: the skipped
  worlds are worlds this measurement never reached, not worlds the battery let
  through. The consequence to keep in view is that the campaign's detection power
  is only ever measured on the minable residue.

* **Rule guards are copies, not aliases, after `deepcopy`.** `mine` sets
  `rule.guard = list(best)` where `best is frontier[0]`, so in the engine's own
  output those two share atoms. `applied()` deep-copies before corrupting, which
  splits them — editing `rule.guard` leaves `rule.frontier[0]` alone. That is
  what makes `cm-weaken-ground-guard` narrow enough to name one invariant, and it
  is a property of the harness rather than of the engine, so it is written down.

## Pre-registered predictions beyond `expect_kill`

`expect_kill` can only name invariants that exist. Three mutants below are
predicted, *before the run*, to survive anyway, because the invariant whose job
they fall under declines to look:

* `cm-empty-frontier` — `frontier_is_complete_to_size` opens with
  `if rule.frontier_truncated or not rule.frontier: continue`, so a rule whose
  frontier is empty is exempt from the completeness check by construction, and
  `frontier_guards_are_consistent` is vacuous over an empty list.
* `cm-truncation-alibi` — the same `continue`, reached by the other branch: an
  engine that sets its own truncation flag exculpates itself.
* `cm-shrink-lifted-support` — every invariant iterates `result.rules`, never
  `result.all_rules`, while `cegis_miner.candidates()` publishes `all_rules`.

If those three die, the prediction was wrong and the report says so.

## V-13: the effect mutants, and why none of them is a tautology

Six mutants were added in V-13 for the two new invariants
(`effects_agree_with_the_evidence`, `rules_fire_on_the_action_they_name`). The
adversarial pass on V-10 caught `cm-weaken-ground-guard` choosing its injection
point with `_fires_on(weaker) > support` — *the very predicate* the invariant it
was aimed at evaluates — so that its death was a restatement of its own search
condition. That criticism is on file and these six are written against it:

* **the target is chosen structurally, never by the invariant's criterion.**
  "the first ground rule whose effect is a move", "the first lifted rule",
  "the first rule carrying a destination". No mutant below calls
  `oracles/motion.py`, and none asks whether the value it is about to write
  would trip anything;
* **the lie's falsity is guaranteed by the engine's own semantics, not by the
  oracle.** Negating a non-zero displacement, or filing a rule under a direction
  none of its witnesses took, is false whatever the pixels say — which is
  exactly what makes it a *defect* under `mutants/__init__.py`'s rule that a
  mutant must contradict a claim the engine actually makes. A mutant whose
  falsity had to be established by the oracle would be the tautology;
* **the negative control is registered.** `cm-drop-effect-destination` is
  pre-declared a survivor: `effects_agree_with_the_evidence` checks `effect.to`
  only where the engine states one, so withholding a destination it could have
  stated is a real gap and the mutant measures it instead of the prose claiming
  it. An invariant that killed that one too would be over-reaching, and the
  report would say so.

What ultimately licenses the kills is the **baseline**: on the clean tree
`effects_agree_with_the_evidence` returns nothing on every world it judges, so
the oracle and the engine already agree there, and the mutant is the only thing
that changed.
"""

import dataclasses
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from fuzzlab import mutants as mut
from fuzzlab import rig  # noqa: F401  (path bootstrap)
from fuzzlab.worlds.gridworld import DELTA

from engines.cegis_miner import atoms as atom_mod  # noqa: E402

ENGINE = "cegis_miner"
SEAM = "_mine"


def _unpack(result: Any) -> Tuple[Any, Sequence[Any]]:
    """The seam's `(MiningResult, transitions, split)`, minus the split."""
    mining, transitions, _split = result
    return mining, transitions


def _fires_on(guard: Sequence[Any], transitions: Sequence[Any]) -> Set[int]:
    """Which transitions a guard admits, by direct evaluation.

    Deliberately re-implemented rather than imported from
    `props/cegis_miner.py`: a mutant that decides whether it applied by calling
    the property's own helper would go inert exactly when the property is blind,
    which is the one correlation this measurement cannot afford.
    """
    return {t.index for t in transitions
            if all(atom_mod.evaluate(a, t.state, t.action) for a in guard)}


# ------------------------------------------------------------------ mutations

def _frontier_guard_inconsistent(result: Any, args: Tuple[Any, ...],
                                 kwargs: Dict[str, Any]) -> Any:
    mining, transitions = _unpack(result)
    vocabulary = atom_mod.build_vocabulary([t.state for t in transitions])
    for rule in mining.rules:
        support = set(rule.support)
        for atom in vocabulary:
            if _fires_on([atom], transitions) != support:
                rule.frontier = rule.frontier + [[atom]]
                return result
    raise mut.inert("every atom in the vocabulary fires on exactly the support "
                    "of every rule; no inconsistent guard exists to smuggle in")


def _drop_frontier_guard(result: Any, args: Tuple[Any, ...],
                         kwargs: Dict[str, Any]) -> Any:
    mining, _transitions = _unpack(result)
    for rule in mining.rules:
        if not rule.frontier_truncated and len(rule.frontier) >= 2:
            rule.frontier = rule.frontier[:-1]
            return result
    raise mut.inert("no untruncated rule has two frontier guards; dropping the "
                    "only one would empty the frontier, which is a different "
                    "mutant (cm-empty-frontier)")


def _empty_frontier(result: Any, args: Tuple[Any, ...],
                    kwargs: Dict[str, Any]) -> Any:
    mining, _transitions = _unpack(result)
    for rule in mining.rules:
        if rule.frontier:
            rule.frontier = []
            return result
    raise mut.inert("no rule has a frontier to erase")


def _truncation_alibi(result: Any, args: Tuple[Any, ...],
                      kwargs: Dict[str, Any]) -> Any:
    mining, _transitions = _unpack(result)
    for rule in mining.rules:
        if not rule.frontier_truncated and len(rule.frontier) >= 2:
            rule.frontier = rule.frontier[:-1]
            rule.frontier_truncated = True
            return result
    raise mut.inert("no untruncated rule has two frontier guards to hide one of")


def _inflate_applicable(result: Any, args: Tuple[Any, ...],
                        kwargs: Dict[str, Any]) -> Any:
    mining, transitions = _unpack(result)
    for rule in mining.rules:
        outside = [t.index for t in transitions if t.index not in set(rule.applicable)]
        if outside:
            rule.applicable = sorted(set(rule.applicable) | {outside[0]})
            return result
    raise mut.inert("every rule already applies to every transition; there is no "
                    "index left to over-claim")


def _weaken_ground_guard(result: Any, args: Tuple[Any, ...],
                         kwargs: Dict[str, Any]) -> Any:
    mining, transitions = _unpack(result)
    for rule in mining.rules:
        support = set(rule.support)
        for i in range(len(rule.guard)):
            weaker = rule.guard[:i] + rule.guard[i + 1:]
            if _fires_on(weaker, transitions) > support:
                rule.guard = weaker
                return result
    raise mut.inert("no literal can be dropped from any ground guard without the "
                    "guard admitting exactly the same transitions -- the world "
                    "does not distinguish the weaker guard")


def _drop_rule(result: Any, args: Tuple[Any, ...],
               kwargs: Dict[str, Any]) -> Any:
    mining, transitions = _unpack(result)
    if not mining.rules or not transitions:
        raise mut.inert("no ground rule to withhold")
    mining.rules = mining.rules[1:]
    return result


def _shrink_lifted_support(result: Any, args: Tuple[Any, ...],
                           kwargs: Dict[str, Any]) -> Any:
    mining, _transitions = _unpack(result)
    for rule in mining.lifted:
        if rule.support:
            rule.support = sorted(rule.support)[1:]
            return result
    raise mut.inert("no two ground rules were alpha-equivalent under ?dir, so "
                    "this world has no lifted rule to misreport")


# ------------------------------------------------------- V-13: effect mutants
#
# Every selector below scans in a fixed order and takes the first structural
# match.  None of them evaluates the invariant's comparison, and none imports
# `fuzzlab.oracles.motion`.

def _first_move_rule(rules: Sequence[Any]) -> Optional[Any]:
    for rule in rules:
        if rule.effect.type == "move" and (rule.effect.dy, rule.effect.dx) != (0, 0):
            return rule
    return None


def _flip_effect_delta(result: Any, args: Tuple[Any, ...],
                       kwargs: Dict[str, Any]) -> Any:
    mining, _transitions = _unpack(result)
    rule = _first_move_rule(mining.rules)
    if rule is None:
        raise mut.inert("no ground rule reports a non-zero displacement, so "
                        "there is no direction to reverse")
    # `Effect` is a frozen dataclass, so the lie is told by rebinding
    # `rule.effect` (Rule is not frozen) rather than by assignment.
    rule.effect = dataclasses.replace(
        rule.effect, dy=-rule.effect.dy, dx=-rule.effect.dx,
        to=None)          # a reversed step lands nowhere the old `to` names
    return result


def _effect_none_becomes_move(result: Any, args: Tuple[Any, ...],
                              kwargs: Dict[str, Any]) -> Any:
    mining, _transitions = _unpack(result)
    for rule in mining.rules:
        if rule.effect.type == "none" and rule.action in DELTA:
            dy, dx = DELTA[rule.action]
            rule.effect = dataclasses.replace(rule.effect, type="move",
                                              dy=dy, dx=dx)
            return result
    raise mut.inert("no ground rule reports `none` for a compass action; this "
                    "world never blocked the mover")


def _drift_effect_destination(result: Any, args: Tuple[Any, ...],
                              kwargs: Dict[str, Any]) -> Any:
    mining, _transitions = _unpack(result)
    for rule in mining.rules:
        if rule.effect.to is not None:
            row, col = rule.effect.to
            rule.effect = dataclasses.replace(rule.effect, to=(row + 1, col))
            return result
    raise mut.inert("no rule carries a concrete destination: every rule's "
                    "witnesses disagreed on where the mover landed, which is "
                    "the documented condition for `to` being None")


def _drop_effect_destination(result: Any, args: Tuple[Any, ...],
                             kwargs: Dict[str, Any]) -> Any:
    mining, _transitions = _unpack(result)
    for rule in mining.rules:
        if rule.effect.to is not None:
            rule.effect = dataclasses.replace(rule.effect, to=None)
            return result
    raise mut.inert("no rule carries a destination to withhold")


def _freeze_lifted_direction(result: Any, args: Tuple[Any, ...],
                             kwargs: Dict[str, Any]) -> Any:
    mining, _transitions = _unpack(result)
    world = args[0]
    actions = world.action_list
    for rule in mining.lifted:
        witnesses = [actions[i] for i in sorted(rule.support) if i < len(actions)]
        concrete = [a for a in witnesses if a in DELTA]
        if len(set(concrete)) < 2:
            continue                # not actually parameterised on this world
        rule.effect = dataclasses.replace(rule.effect, direction=concrete[0])
        return result
    raise mut.inert("no lifted rule here collapses witnesses from two or more "
                    "directions, so pinning the variable to one of them would "
                    "not be a false statement")


def _lift_admits_a_wrong_direction(result: Any, args: Tuple[Any, ...],
                                   kwargs: Dict[str, Any]) -> Any:
    """Widen a lifted rule's support to a transition that did not move that way.

    **This is the mutant that tests what `?dir` actually means.** An adversarial
    review established that `cm-freeze-lifted-direction` does not: the engine
    never emits a concrete `effect.direction` (a census of 357 rules found only
    `{None, "?dir"}`), so that mutant only reaches
    `_claimed_delta`'s `if direction in DELTA` branch, which nothing else can
    reach. Deleting those two lines leaves it at eval=32, killed=0 — it measures
    the invariant's tolerance of a malformed field, not the semantics of the
    variable.

    The real path is `direction == "?dir"` → `DELTA[action of this witness]`, and
    it is exercised by making `lift()` collapse a member it is forbidden to
    collapse: `miner.py:_normalise` returns None unless
    `(dy, dx) == DELTA[rule.action]`, so a lifted rule's support may not contain
    a transition that stayed put. The index is taken from the first ground rule
    whose effect is `none` — a structural choice, made without consulting the
    oracle — and added to `applicable` as well, so `applicable_equals_support`
    stays quiet and the attribution is clean.
    """
    mining, _transitions = _unpack(result)
    blocked = [r for r in mining.rules if r.effect.type == "none" and r.support]
    if not blocked or not mining.lifted:
        raise mut.inert("this world has no lifted rule, or no `none` rule whose "
                        "transitions could be smuggled into one")
    index = sorted(blocked[0].support)[0]
    rule = mining.lifted[0]
    if index in rule.support:
        raise mut.inert("the lifted rule already claims that transition")
    rule.support = sorted(set(rule.support) | {index})
    rule.applicable = sorted(set(rule.applicable) | {index})
    return result


def _relabel_rule_action(result: Any, args: Tuple[Any, ...],
                         kwargs: Dict[str, Any]) -> Any:
    mining, _transitions = _unpack(result)
    for rule in mining.rules:
        if rule.action in DELTA and rule.support:
            rule.action = next(d for d in sorted(DELTA) if d != rule.action)
            return result
    raise mut.inert("no ground rule is filed under a compass action with "
                    "witnesses to contradict")


# ------------------------------------------------------------------- catalogue

mut.register(
    mut.Mutant(
        id="cm-frontier-guard-inconsistent",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="every guard in the frontier fires on exactly the rule's support "
              "-- miner.py:enumerate_frontier admits a combo only if each "
              "literal is true on every positive (`positives & ~masks[a] == 0`) "
              "and the conjunction admits no negative "
              "(`_mask_of(combo) & negatives == 0`), which together force "
              "mask == positives; the module docstring calls the frontier "
              "'every minimal guard consistent with the evidence'.",
        description="append a one-literal guard, chosen from the vocabulary by "
                    "direct evaluation to fire on something other than the "
                    "support, to the first rule's frontier. The engine now "
                    "offers a guard that is false of the evidence -- and the "
                    "frontier is what probe_frontier consumes.",
        corrupt=_frontier_guard_inconsistent,
        expect_kill=("frontier_guards_are_consistent",),
    ),
    mut.Mutant(
        id="cm-drop-frontier-guard",
        engine=ENGINE, seam=SEAM, kind=mut.INCOMPLETE,
        claim="the frontier is exhaustive up to the rule's own size bound -- "
              "miner.py:enumerate_frontier is documented as 'every minimal-by-"
              "inclusion guard of at most max_size literals', and a rule that "
              "stopped short is required to say so via frontier_truncated.",
        description="drop the last (least preferred by guard_order_key) guard "
                    "from the first untruncated rule with two of them. Every "
                    "remaining guard is still true; one true alternative "
                    "explanation has been withheld, which is exactly the "
                    "ambiguity a probe is supposed to be aimed at.",
        corrupt=_drop_frontier_guard,
        expect_kill=("frontier_is_complete_to_size",),
    ),
    mut.Mutant(
        id="cm-empty-frontier",
        engine=ENGINE, seam=SEAM, kind=mut.INCOMPLETE,
        claim="a non-truncated rule always has a non-empty frontier -- "
              "miner.py:mine sets size = min(max(len(cegis_guard), 1), "
              "max_frontier_size), and cegis_guard is itself a consistent guard "
              "of that size, so enumerate_frontier cannot come back empty; "
              "`best = frontier[0] if frontier else guard` is the fallback for "
              "a case the engine does not otherwise expect.",
        description="erase the first rule's frontier entirely. The engine now "
                    "reports that no guard at all explains a rule it "
                    "nevertheless emitted a guard for.",
        corrupt=_empty_frontier,
        expect_kill=("frontier_is_complete_to_size",),
    ),
    mut.Mutant(
        id="cm-truncation-alibi",
        engine=ENGINE, seam=SEAM, kind=mut.INCOMPLETE,
        claim="frontier_truncated is an objective fact about the rule, "
              "`len(guard) > max_frontier_size` (miner.py:mine), and not a "
              "licence to omit guards from inside the bound. rule.cegis_guard "
              "is carried on the rule, so the flag is checkable against the "
              "condition that defines it.",
        description="the same withheld guard as cm-drop-frontier-guard, plus "
                    "frontier_truncated=True: an engine that hides its own "
                    "incompleteness behind its own truncation flag. Paired with "
                    "cm-drop-frontier-guard so the difference between the two "
                    "results isolates the flag as the exculpating mechanism.",
        corrupt=_truncation_alibi,
        expect_kill=("frontier_is_complete_to_size",),
    ),
    mut.Mutant(
        id="cm-inflate-applicable",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="applicable is exactly the set the chosen guard admits -- "
              "miner.py:mine computes it as `_mask_of(best, masks, universe)` "
              "with best drawn from the frontier, hence consistent, hence "
              "equal to the support; Rule.coverage publishes "
              "len(support)/len(applicable) and cegis_miner/__init__.py:"
              "candidates() writes that string into candidates.jsonl.",
        description="add one transition index the rule does not apply to. The "
                    "rule now claims to fire somewhere it does not, and its "
                    "published coverage drops from n/n to n/(n+1) -- a "
                    "candidate that looks partially confirmed when it is not.",
        corrupt=_inflate_applicable,
        expect_kill=("applicable_equals_support",),
    ),
    mut.Mutant(
        id="cm-weaken-ground-guard",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="ground rules are mutually exclusive -- "
              "MiningResult.guards_are_mutually_exclusive is documented as the "
              "'Constraint 9 rehearsal', and rule.guard is frontier[0], a guard "
              "consistent with the evidence, so it fires on its own support and "
              "nowhere else.",
        description="drop one literal from a ground rule's guard, choosing a "
                    "literal whose removal provably widens the fire set (checked "
                    "by direct evaluation, so the mutant goes inert rather than "
                    "counting a no-op as a survival). The weakened rule now "
                    "reaches into another rule's transitions.",
        corrupt=_weaken_ground_guard,
        expect_kill=("guards_partition_the_evidence",),
    ),
    mut.Mutant(
        id="cm-drop-rule",
        engine=ENGINE, seam=SEAM, kind=mut.INCOMPLETE,
        claim="the ground rules explain every transition -- miner.py:mine "
              "groups all transitions by (action, effect.key()) and emits one "
              "rule per group, so every transition is in exactly one support; "
              "MiningResult.explains_every_transition states it.",
        description="withhold the first ground rule. Its transitions are now "
                    "explained by nothing, which is the coverage half of "
                    "guards_partition_the_evidence -- the other branch from the "
                    "one cm-weaken-ground-guard aims at.",
        corrupt=_drop_rule,
        expect_kill=("guards_partition_the_evidence",),
    ),
    mut.Mutant(
        id="cm-shrink-lifted-support",
        engine=ENGINE, seam=SEAM, kind=mut.INCOMPLETE,
        claim="a lifted rule's applicable set is its support too -- "
              "miner.py:lift builds both as the union over the members it "
              "collapses, and every member has applicable == support; "
              "cegis_miner/__init__.py:candidates() emits result.all_rules, so "
              "the lifted rule and its coverage string are published exactly "
              "like a ground rule's.",
        description="drop the lowest index from a lifted rule's support, so its "
                    "published coverage becomes (n-1)/n on a rule that in fact "
                    "covers all n. Deliberately the same *kind* of defect as "
                    "cm-inflate-applicable, moved from result.rules to "
                    "result.lifted, so a difference in outcome is a difference "
                    "in scope and not in defect shape.",
        corrupt=_shrink_lifted_support,
        expect_kill=("applicable_equals_support",),
    ),

    # ------------------------------------------------------ V-13: the effect
    mut.Mutant(
        id="cm-flip-effect-delta",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="Effect.dy/.dx are the displacement the rule's own evidence "
              "shows -- miner.py:mine copies them off members[0].effect, which "
              "transitions_from_segmentation set from the segmenter's move "
              "event, and every member of the group shares effect.key() = "
              "(type, dy, dx). __init__.py:candidates() publishes them via "
              "Effect.as_json, and cold-start-a0/prime/probe_runner.py:72 reads "
              "rule_payload['effect'] to decide what a rule predicts.",
        description="negate the displacement of the first ground rule that "
                    "reports one: `push_DOWN` now claims the mover goes up. The "
                    "guards are untouched, so the rule fires in exactly the "
                    "right places and states the opposite of what happens "
                    "there -- the shape of defect the four guard invariants are "
                    "constructed to miss.",
        corrupt=_flip_effect_delta,
        expect_kill=("effects_agree_with_the_evidence",),
    ),
    mut.Mutant(
        id="cm-effect-none-becomes-move",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="Effect.type distinguishes a transition in which the object moved "
              "from one in which it did not -- transitions_from_segmentation "
              "emits Effect(type='none') exactly when the segmenter narrates no "
              "event for the track at that frame, and structural_name files the "
              "group as `blocked_<action>` on the strength of it.",
        description="turn the first `blocked_<D>` rule into a `move` by the "
                    "delta of its own action: the engine now says the mover "
                    "advances in precisely the situations where it is stopped. "
                    "This is the inverse of cm-flip-effect-delta -- there a true "
                    "motion is misdescribed, here a non-event is invented -- and "
                    "the pair separates the type field from the delta fields.",
        corrupt=_effect_none_becomes_move,
        expect_kill=("effects_agree_with_the_evidence",),
    ),
    mut.Mutant(
        id="cm-drift-effect-destination",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="Effect.to is the cell the object lands on, and is populated only "
              "when every witness agrees on it -- miner.py:mine, `destinations "
              "= {t.effect.to for t in members}` then `destinations.pop() if "
              "len(destinations) == 1 else None`, with the comment 'otherwise "
              "the rule would advertise one transition's landing cell as if it "
              "were the effect of all of them'. Published as `effect.to`.",
        description="move the destination of the first rule that states one "
                    "down by one row, leaving dy/dx alone. The displacement is "
                    "still right and the landing cell is not, so the rule is "
                    "internally inconsistent in the one direction "
                    "`frontier_*` and `applicable_equals_support` cannot see.",
        corrupt=_drift_effect_destination,
        expect_kill=("effects_agree_with_the_evidence",),
    ),
    mut.Mutant(
        id="cm-drop-effect-destination",
        engine=ENGINE, seam=SEAM, kind=mut.INCOMPLETE,
        claim="same claim as cm-drift-effect-destination. Withholding a "
              "destination every witness agreed on is a real omission: the "
              "condition miner.py:mine tests for holds, and the field is "
              "published as absent anyway.",
        description="EXPECTED SURVIVOR, pre-registered: clear `effect.to` on "
                    "the first rule that carries one. "
                    "effects_agree_with_the_evidence asserts against `to` only "
                    "where the engine states it, because `to = None` is the "
                    "engine's documented refusal to claim and asserting past a "
                    "refusal files a bug against a promise never made. So this "
                    "one is designed to live, and its survival is the measured "
                    "size of that gap rather than a sentence claiming it is "
                    "small.",
        corrupt=_drop_effect_destination,
        predicted_survivor=True,
    ),
    mut.Mutant(
        id="cm-freeze-lifted-direction",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="a lifted rule's `effect.direction` is the variable `?dir`, "
              "resolved per witness -- miner.py:lift builds Effect(type='move', "
              "direction=DIR_VAR) and _normalise admits a member only if "
              "(dy, dx) == DELTA[member.action], so the parameterised effect "
              "means 'the mover advances in the direction of the action'. "
              "Effect.as_json emits `direction` in place of dy/dx, and "
              "candidates() publishes lifted rules through all_rules.",
        description="pin the variable to the concrete direction of the lifted "
                    "rule's lowest-indexed witness. The rule now claims every "
                    "one of its transitions moved that way, which is true of "
                    "that witness and false of the members from the other "
                    "directions -- the generalisation that made the rule worth "
                    "lifting is exactly what it now gets wrong. NOTE, after "
                    "review: the engine never emits a concrete direction (357 "
                    "rules censused, `effect.direction` only ever None or "
                    "'?dir'), so this mutant reaches a branch of "
                    "_claimed_delta that nothing else reaches, and what it "
                    "measures is the invariant's handling of a malformed field "
                    "rather than the semantics of the variable. "
                    "cm-lift-admits-a-wrong-direction is the one that tests "
                    "`?dir` as the engine actually produces it.",
        corrupt=_freeze_lifted_direction,
        expect_kill=("effects_agree_with_the_evidence",),
    ),
    mut.Mutant(
        id="cm-lift-admits-a-wrong-direction",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="every member a lifted rule collapses moved in the direction of "
              "its own action -- miner.py:_normalise returns None unless "
              "`rule.effect.type == 'move' and (dy, dx) == "
              "DELTA.get(rule.action)`, and lift() groups only on shapes that "
              "survive that filter, building support as the union over members. "
              "So `move(?dir)` means `the mover advances by DELTA[the action "
              "taken]`, and a support index where nothing moved falsifies it.",
        description="add to the first lifted rule's support (and applicable, so "
                    "the attribution stays with the effect invariant) the lowest "
                    "transition index of a `blocked_<D>` rule -- a transition "
                    "where the mover did not move at all. Unlike "
                    "cm-freeze-lifted-direction this exercises the branch the "
                    "engine actually produces: `?dir` resolved per witness "
                    "against DELTA[action]. Added because a review showed the "
                    "other mutant does not reach it.",
        corrupt=_lift_admits_a_wrong_direction,
        expect_kill=("effects_agree_with_the_evidence",),
    ),
    mut.Mutant(
        id="cm-relabel-rule-action",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="Rule.action is the action every transition in the rule's support "
              "took -- miner.py:mine groups on `(transition.action, "
              "transition.effect.key())` and sets `action = members[0].action`, "
              "so the group is homogeneous in it by construction; "
              "structural_name and Rule.as_json both publish it, and it is what "
              "a manual hangs the rule off.",
        description="re-file the first ground rule under a different compass "
                    "direction, changing nothing else. Its guard still fires "
                    "where it did and its effect is still what happened; the "
                    "rule is a true statement about the world attached to the "
                    "wrong lever. Separated from the effect mutants on purpose: "
                    "for a ground rule the published dy/dx are explicit, so "
                    "effects_agree_with_the_evidence reads the same claim "
                    "before and after and only the action invariant can see it.",
        corrupt=_relabel_rule_action,
        expect_kill=("rules_fire_on_the_action_they_name",),
    ),
)
