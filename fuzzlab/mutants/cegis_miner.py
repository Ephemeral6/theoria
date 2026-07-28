"""`cegis_miner` mutants — eight defects, aimed one at a time.

The seam is `props/cegis_miner.py:_mine`, and it is the *only* engine call the
property module makes: all four invariants open with `result, transitions, _split
= _mine(world)` and everything else they do is re-derivation by
`atoms.evaluate`. So one seam covers the whole module, and no invariant reaches
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
"""

from typing import Any, Dict, Sequence, Set, Tuple

from fuzzlab import mutants as mut
from fuzzlab import rig  # noqa: F401  (path bootstrap)

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
)
