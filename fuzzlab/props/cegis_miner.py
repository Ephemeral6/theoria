"""`cegis_miner` — four invariants, evaluated directly rather than via bitmasks.

The engine reasons in integer bitmasks over transition indices. Every check here
re-derives the same facts by calling `atoms.evaluate` on each `(state, action)`
and comparing sets, so a bug in the mask bookkeeping — the most likely place for
one — cannot hide behind the bookkeeping that produced it.

Two scope limits, taken from the engine's own documented contract, because
asserting past either would file a bug against a promise never made:

* **completeness is bounded by `rule.frontier_max_size`, which is not always 3.**
  `mine` sets `size = min(max(len(cegis_guard), 1), max_frontier_size)`, so a
  rule whose CEGIS guard came out at one literal has its frontier enumerated at
  size 1 and two-literal minimal guards are legitimately absent. The invariant
  is completeness *up to that rule's own bound*;
* **`NoSeparatingGuard` is a documented outcome, not a defect.** It is what the
  engine raises when the fixed five-predicate vocabulary cannot separate a
  positive from a negative — coarse vocabulary, or contradictory evidence. It is
  recorded as `skipped` with the reason rather than as a violation or an
  unexpected raise, so the campaign's counts stay honest about how many worlds
  were actually judged.

| invariant | claim under test |
|---|---|
| `frontier_guards_are_consistent` | every frontier guard fires on exactly the rule's support — covers every positive, excludes every negative |
| `frontier_is_complete_to_size` | every minimal consistent guard within the rule's own size bound is in the frontier |
| `applicable_equals_support` | a consistent rule's applicable set is its support, so `coverage` is n/n |
| `guards_partition_the_evidence` | the ground rules are mutually exclusive and explain every transition |
"""

import itertools
from typing import Any, Dict, List, Sequence, Set, Tuple

from fuzzlab import rig  # noqa: F401  (path bootstrap)
from fuzzlab.props import finding

from engines import cegis_miner as engine  # noqa: E402
from engines.cegis_miner import atoms as atom_mod  # noqa: E402
from engines.cegis_miner.miner import NoSeparatingGuard  # noqa: E402
from engines import mdl_segmenter  # noqa: E402

FAMILY = "gridworld"
ENGINE = "cegis_miner"

# The exhaustive subset sweep in `frontier_is_complete_to_size` is
# C(|vocabulary|, size).  Beyond this the property records a `skipped` rather
# than sampling — a partial sweep reported as a pass claims coverage it does not
# have.
COMBINATION_BUDGET = 400_000


class Unminable(Exception):
    """The segmentation narrates something `transitions_from_segmentation` refuses.

    Not a defect. `transitions_from_segmentation` raises `ValueError` by design
    when a transition narrates anything other than a single `move` or nothing —
    it mines the mover's rule and an `appear`/`vanish`/`recolor` is not one.
    """


def _mine(world: Any):
    """Mine the mover's rules, trying both segmentation operators before giving up.

    The colour-agnostic operator is tried first because it is the engine's
    default. It merges the mover with an obstacle the moment they touch, and the
    merged component narrates as `vanish` + `appear` rather than `move` — the
    touching-objects gap the A0 family has reported upstream twice. Once
    `gridworld` started producing reachable obstacles at all (see
    `worlds/gridworld.py:_place_obstacles`), that stopped being rare: it fired on
    179 of 500 worlds in the first full campaign.

    `split_by_color=True` is the operator that exists for exactly this, so it is
    tried second and the one that worked is recorded. Where neither can produce a
    move/none narration the property records a **`skipped`** with the reason,
    not a `raised`: a documented refusal counted as an unexplained exception
    makes the campaign's own health look worse than it is, and — worse — hides
    how many worlds actually got judged.
    """
    background = world.spec_json().get("background", 0)
    errors = []
    for split in (False, True):
        seg = mdl_segmenter.segment_trajectory(world.frames, background=background,
                                               split_by_color=split)
        try:
            transitions = engine.transitions_from_segmentation(
                world.frames, world.action_list, seg, background=background)
        except ValueError as exc:
            errors.append("split_by_color=%s: %s" % (split, exc))
            continue
        return engine.mine(transitions), transitions, split
    raise Unminable("; ".join(errors))


def _fires_on(guard: Sequence[Any], transitions: Sequence[Any]) -> Set[int]:
    """The transitions this guard admits, by direct evaluation."""
    return {t.index for t in transitions
            if all(atom_mod.evaluate(a, t.state, t.action) for a in guard)}


def _skip_no_guard(world: Any, invariant: str, exc: Exception) -> List[finding.Finding]:
    if isinstance(exc, Unminable):
        return [finding.skipped(
            ENGINE, invariant, world,
            "neither segmentation operator narrates this world as move/none — "
            "the mover's component merges with an obstacle it touches. Documented "
            "refusal by transitions_from_segmentation, and an instance of the "
            "touching-objects segmentation gap, not a mining defect.",
            error=str(exc), cause="unminable")]
    return [finding.skipped(
        ENGINE, invariant, world,
        "NoSeparatingGuard — the fixed five-predicate vocabulary cannot separate "
        "this world's evidence. Documented behaviour (miner.py, "
        "test_contradictory_evidence_is_reported_not_papered_over), not a defect.",
        error=str(exc), cause="no_separating_guard")]


# --------------------------------------------------------------- invariants

def frontier_guards_are_consistent(world: Any) -> List[finding.Finding]:
    """Every frontier guard admits exactly the rule's support."""
    try:
        result, transitions, _split = _mine(world)
    except (NoSeparatingGuard, Unminable) as exc:
        return _skip_no_guard(world, "frontier_guards_are_consistent", exc)

    out: List[finding.Finding] = []
    for rule in result.rules:
        support = set(rule.support)
        for guard in rule.frontier:
            fires = _fires_on(guard, transitions)
            if fires != support:
                out.append(finding.violated(
                    ENGINE, "frontier_guards_are_consistent", world,
                    "rule %s: frontier guard [%s] fires on %s, support is %s"
                    % (rule.name, " AND ".join(sorted(a.name for a in guard)),
                       sorted(fires), sorted(support)),
                    rule=rule.name,
                    guard=sorted(a.name for a in guard),
                    missed=sorted(support - fires),
                    spurious=sorted(fires - support)))
                return out
    return out


def frontier_is_complete_to_size(world: Any) -> List[finding.Finding]:
    """No consistent guard within the rule's own size bound is missing.

    Brute force: enumerate every subset of the vocabulary up to
    `rule.frontier_max_size`, keep the ones that fire on exactly the support, and
    check each is present in the frontier up to reordering. Minimality is handled
    by comparing sets of atoms — a non-minimal consistent guard is a superset of
    a minimal one and the engine is entitled to omit it.
    """
    try:
        result, transitions, _split = _mine(world)
    except (NoSeparatingGuard, Unminable) as exc:
        return _skip_no_guard(world, "frontier_is_complete_to_size", exc)

    vocabulary = atom_mod.build_vocabulary([t.state for t in transitions])
    out: List[finding.Finding] = []
    for rule in result.rules:
        if rule.frontier_truncated or not rule.frontier:
            continue                    # the engine says it stopped early; believe it
        size = rule.frontier_max_size
        combinations = 1
        for k in range(1, size + 1):
            combinations += _choose(len(vocabulary), k)
        if combinations > COMBINATION_BUDGET:
            out.append(finding.skipped(
                ENGINE, "frontier_is_complete_to_size", world,
                "vocabulary of %d atoms at size %d is %d subsets, over budget"
                % (len(vocabulary), size, combinations),
                rule=rule.name, vocabulary=len(vocabulary), size=size))
            continue

        support = set(rule.support)
        have = {frozenset(a.name for a in g) for g in rule.frontier}
        minimal: List[frozenset] = []
        for k in range(1, size + 1):
            for combo in itertools.combinations(vocabulary, k):
                names = frozenset(a.name for a in combo)
                if any(m < names for m in minimal):
                    continue            # a strict superset of a minimal guard
                if _fires_on(combo, transitions) == support:
                    minimal.append(names)
        for names in minimal:
            if names not in have:
                out.append(finding.violated(
                    ENGINE, "frontier_is_complete_to_size", world,
                    "rule %s: guard [%s] is consistent and within size %d but is "
                    "not in the frontier (%d entries)"
                    % (rule.name, " AND ".join(sorted(names)), size,
                       len(rule.frontier)),
                    rule=rule.name, missing=sorted(names),
                    frontier_max_size=size,
                    frontier=[sorted(a.name for a in g) for g in rule.frontier]))
                return out
    return out


def applicable_equals_support(world: Any) -> List[finding.Finding]:
    """A consistent rule's applicable set is exactly its support."""
    try:
        result, _transitions, _split = _mine(world)
    except (NoSeparatingGuard, Unminable) as exc:
        return _skip_no_guard(world, "applicable_equals_support", exc)

    out: List[finding.Finding] = []
    for rule in result.rules:
        if set(rule.applicable) != set(rule.support):
            out.append(finding.violated(
                ENGINE, "applicable_equals_support", world,
                "rule %s: applicable %s != support %s, so coverage %s is "
                "not n/n" % (rule.name, sorted(rule.applicable),
                             sorted(rule.support), rule.coverage),
                rule=rule.name, applicable=sorted(rule.applicable),
                support=sorted(rule.support), coverage=rule.coverage))
    return out


def guards_partition_the_evidence(world: Any) -> List[finding.Finding]:
    """Ground rules are mutually exclusive and explain every transition.

    Recomputed by direct evaluation rather than by asking the engine's own
    `guards_are_mutually_exclusive()` / `explains_every_transition()`, which are
    near-tautological on any input `mine` accepts. Evaluating the guards makes
    the check independent of the mask bookkeeping.
    """
    try:
        result, transitions, _split = _mine(world)
    except (NoSeparatingGuard, Unminable) as exc:
        return _skip_no_guard(world, "guards_partition_the_evidence", exc)

    claimed: Dict[int, str] = {}
    out: List[finding.Finding] = []
    for rule in result.rules:
        for index in _fires_on(rule.guard, transitions):
            if index in claimed and claimed[index] != rule.name:
                out.append(finding.violated(
                    ENGINE, "guards_partition_the_evidence", world,
                    "transition %d is claimed by both %s and %s"
                    % (index, claimed[index], rule.name),
                    transition=index, rules=[claimed[index], rule.name]))
                return out
            claimed[index] = rule.name
    everything = {t.index for t in transitions}
    if set(claimed) != everything:
        out.append(finding.violated(
            ENGINE, "guards_partition_the_evidence", world,
            "%d of %d transitions are explained by no ground rule: %s"
            % (len(everything - set(claimed)), len(everything),
               sorted(everything - set(claimed))[:8]),
            unexplained=sorted(everything - set(claimed))[:8],
            n_transitions=len(everything)))
    return out


def _choose(n: int, k: int) -> int:
    out = 1
    for i in range(k):
        out = out * (n - i) // (i + 1)
    return out


INVARIANTS = {
    "frontier_guards_are_consistent": frontier_guards_are_consistent,
    "frontier_is_complete_to_size": frontier_is_complete_to_size,
    "applicable_equals_support": applicable_equals_support,
    "guards_partition_the_evidence": guards_partition_the_evidence,
}


def check(world: Any) -> List[finding.Finding]:
    return finding.run_invariants(ENGINE, world, INVARIANTS)
