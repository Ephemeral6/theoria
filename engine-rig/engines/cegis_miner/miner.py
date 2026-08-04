"""cegis_miner -- counterexample-guided synthesis of guards, over an exact ledger.

The ledger is the verifier: zero noise, so a rule is right exactly when it fires
on every transition with its effect and on no other.  The loop is the classic
one -- propose the most general guard, ask the ledger for a counterexample,
strengthen with the cheapest literal that kills the counterexample while keeping
every positive, repeat -- and it terminates because each round strictly shrinks
the set of transitions the guard admits.

What comes out is not a point guess but a **frontier**: every minimal guard
consistent with the evidence, ordered by description length.  On Fixture A that
matters twice over --

  * `free`, `in_bounds` and `clear` are indistinguishable on a one-object board,
    so all three survive into the frontier;
  * the single teleport transition is equally well explained by "it was on that
    cell" and by "the wall was in the way and it was not on any other cell",

which is precisely the input `probe_frontier` is built to consume.

**One unseparable effect class must not cost the frontier for the others.**
`synthesize` raises `NoSeparatingGuard` when no literal in the vocabulary tells
a group of transitions apart from the rest -- a true report, and it stays a
raise, because at the level of one effect class there is nothing to return.
`mine` groups transitions by (action, effect) and used to let that raise escape,
which threw away every rule for the track including the classes that were
perfectly separable.  `on_unseparable="record"` keeps the frontier for the
groups that have one and files the rest under `MiningResult.unseparable` with
the reason, so the output says which part of the world the vocabulary can and
cannot name.  The default is still `"raise"`: this widening is opt-in, and on
every existing fixture the two modes produce byte-identical results because no
group is unseparable there.  See DECISIONS.md D-E20-002.
"""

import itertools
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from engines.cegis_miner.atoms import (
    Atom,
    State,
    atom_masks,
    atom_order_key,
    build_vocabulary,
    guard_cost,
    guard_order_key,
)

DELTA = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}
DIR_VAR = "?dir"

# Frontier enumeration is exhaustive up to this many literals; anything deeper is
# reported as truncated rather than silently dropped.
MAX_FRONTIER_SIZE = 3


class NoSeparatingGuard(Exception):
    """The vocabulary cannot separate an effect class from the rest of the ledger."""


@dataclass(frozen=True)
class Effect:
    type: str                                  # move | none
    dy: int = 0
    dx: int = 0
    to: Optional[Tuple[int, int]] = None       # only when every witness agrees
    direction: Optional[str] = None            # set on lifted rules: move(?dir)

    def as_json(self) -> Dict[str, object]:
        out: Dict[str, object] = {"type": self.type}
        if self.type != "move":
            return out
        if self.direction is not None:
            out["direction"] = self.direction
            return out
        out["dy"] = self.dy
        out["dx"] = self.dx
        if self.to is not None:
            out["to"] = list(self.to)
        return out

    def key(self) -> Tuple:
        return (self.type, self.dy, self.dx)


@dataclass
class Transition:
    index: int
    state: State
    action: str
    effect: Effect


@dataclass
class Rule:
    name: str
    action: str
    effect: Effect
    guard: List[Atom]
    frontier: List[List[Atom]]
    frontier_max_size: int
    frontier_truncated: bool
    support: List[int]
    applicable: List[int]
    cegis_trace: List[Dict[str, object]]
    cegis_guard: List[Atom] = field(default_factory=list)
    cegis_added: List[Atom] = field(default_factory=list)
    lifted_from: List[str] = field(default_factory=list)

    @property
    def coverage(self) -> str:
        return "%d/%d" % (len(self.support), len(self.applicable))

    def guard_names(self) -> List[str]:
        return sorted(atom.name for atom in self.guard)

    def as_json(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "action": self.action,
            "guard": self.guard_names(),
            "guard_cost_bits": guard_cost(self.guard),
            "effect": self.effect.as_json(),
            "frontier": [sorted(a.name for a in g) for g in self.frontier],
            "frontier_size": len(self.frontier),
            "frontier_max_size": self.frontier_max_size,
            "frontier_truncated": self.frontier_truncated,
            "cegis_guard": sorted(a.name for a in self.cegis_guard),
            "cegis_iterations": len(self.cegis_trace),
            "cegis_trace": self.cegis_trace,
            "lifted_from": self.lifted_from,
        }


# ------------------------------------------------------------------- CEGIS

def _mask_of(guard: Sequence[Atom], masks: Dict[Atom, int], universe: int) -> int:
    mask = universe
    for atom in guard:
        mask &= masks[atom]
    return mask


def _lowest_set_bit(mask: int) -> int:
    return (mask & -mask).bit_length() - 1


def synthesize(positives: int, universe: int, masks: Dict[Atom, int]
               ) -> Tuple[List[Atom], List[Dict[str, object]], List[Atom]]:
    """CEGIS: refine the most general guard until no counterexample remains.

    Returns the (minimised) guard, the counterexample trace, and every literal
    the loop added before minimisation -- the third value is what makes the
    refinement itself auditable rather than just its result.
    """
    negatives = universe & ~positives
    guard: List[Atom] = []
    trace: List[Dict[str, object]] = []
    added: List[Atom] = []
    consistent = [a for a in masks if positives & ~masks[a] == 0]  # true on every positive

    while True:
        current = _mask_of(guard, masks, universe)
        counter = current & negatives
        if not counter:
            break
        cex = _lowest_set_bit(counter)
        options = [a for a in consistent if not (masks[a] >> cex) & 1]
        if not options:
            raise NoSeparatingGuard(
                "no literal separates transition %d from the positives" % cex
            )
        pick = min(options, key=atom_order_key)
        guard.append(pick)
        added.append(pick)
        trace.append(
            {
                "iteration": len(trace),
                "counterexample": cex,
                "added": pick.name,
                "admitted_before": bin(current).count("1"),
            }
        )

    # Drop literals the others already imply -- CEGIS adds greedily, in order.
    for atom in sorted(guard, key=atom_order_key, reverse=True):
        reduced = [a for a in guard if a != atom]
        if not (_mask_of(reduced, masks, universe) & negatives):
            guard = reduced
    return sorted(guard, key=atom_order_key), trace, added


def enumerate_frontier(positives: int, universe: int, masks: Dict[Atom, int],
                       max_size: int) -> List[List[Atom]]:
    """Every minimal-by-inclusion guard of at most `max_size` literals."""
    negatives = universe & ~positives
    consistent = sorted(
        (a for a in masks if positives & ~masks[a] == 0), key=atom_order_key
    )
    found: List[List[Atom]] = []
    for size in range(1, max_size + 1):
        for combo in itertools.combinations(consistent, size):
            if any(set(g) <= set(combo) for g in found):
                continue                                  # not minimal
            if not (_mask_of(combo, masks, universe) & negatives):
                found.append(list(combo))
    found.sort(key=guard_order_key)
    return found


# ------------------------------------------------------------------- naming

def structural_name(action: str, effect: Effect, guard: Sequence[Atom]) -> str:
    """A name derived from the rule's *shape*, never from its meaning.

    Naming a concept is the LLM's job (Theoria 1.10b, division of labour rule 1);
    the engine only needs a stable structural handle so that proposals can be
    referred to.  This is a lookup on the rule's form, and nothing else.
    """
    if effect.type == "none":
        return "blocked_%s" % action
    step = abs(effect.dy) + abs(effect.dx)
    if step == 1 and (effect.dy, effect.dx) == DELTA.get(action):
        return "push_%s" % action
    if step > 1 and any(a.kind == "at" and not a.negated for a in guard):
        return "teleport"
    return "move_%s" % action


# -------------------------------------------------------------------- lifting

def _normalise(rule: Rule) -> Optional[Tuple]:
    """Rule shape with the concrete direction replaced by a variable."""
    if rule.effect.type != "move" or (rule.effect.dy, rule.effect.dx) != DELTA.get(rule.action):
        return None
    guard = tuple(sorted(a.substitute_direction(rule.action).name for a in rule.guard))
    return (guard, "move(%s)" % DIR_VAR)


def lift(rules: Sequence[Rule]) -> List[Rule]:
    """Collapse per-direction rules that are alpha-equivalent under `?dir`."""
    groups: Dict[Tuple, List[Rule]] = {}
    for rule in rules:
        shape = _normalise(rule)
        if shape is not None:
            groups.setdefault(shape, []).append(rule)

    lifted: List[Rule] = []
    for shape, members in sorted(groups.items()):
        if len(members) < 2:
            continue
        members = sorted(members, key=lambda r: r.action)
        template = members[0]
        guard = [a.substitute_direction(template.action) for a in template.guard]
        frontier = [
            [a.substitute_direction(template.action) for a in g] for g in template.frontier
        ]
        support = sorted(i for m in members for i in m.support)
        applicable = sorted(i for m in members for i in m.applicable)
        name = structural_name(template.action, template.effect, template.guard)
        name = name.rsplit("_", 1)[0] if name.startswith(("push_", "move_")) else name
        lifted.append(
            Rule(
                name=name,
                action=DIR_VAR,
                effect=Effect(type="move", direction=DIR_VAR),
                guard=guard,
                frontier=frontier,
                frontier_max_size=template.frontier_max_size,
                frontier_truncated=any(m.frontier_truncated for m in members),
                support=support,
                applicable=applicable,
                cegis_trace=[],
                lifted_from=[m.name for m in members],
            )
        )
    return lifted


# --------------------------------------------------------------------- driver

@dataclass
class MiningResult:
    rules: List[Rule]
    lifted: List[Rule]
    transitions: List[Transition]
    unseparable: List[Dict[str, object]] = field(default_factory=list)
    #: the action alphabet the guard vocabulary was built over, and how much of
    #: it the evidence could actually see.  Recorded on every result so that a
    #: vocabulary blind to the world's actions is visible without rerunning.
    vocabulary: Dict[str, object] = field(default_factory=dict)

    @property
    def all_rules(self) -> List[Rule]:
        return self.rules + self.lifted

    def by_name(self, name: str) -> Optional[Rule]:
        for rule in self.all_rules:
            if rule.name == name:
                return rule
        return None

    def guards_are_mutually_exclusive(self) -> bool:
        """Constraint 9 rehearsal: no transition is claimed by two ground rules."""
        seen = 0
        for rule in self.rules:
            mask = 0
            for i in rule.applicable:
                mask |= 1 << i
            if seen & mask:
                return False
            seen |= mask
        return True

    def explains_every_transition(self) -> bool:
        covered = {i for rule in self.rules for i in rule.applicable}
        return covered == {t.index for t in self.transitions}


def mine(transitions: Sequence[Transition],
         max_frontier_size: int = MAX_FRONTIER_SIZE,
         on_unseparable: str = "raise",
         action_alphabet: Optional[Sequence[str]] = None) -> MiningResult:
    """Mine the frontier of every effect class the vocabulary can separate.

    `on_unseparable` is `"raise"` (the default, and the behaviour this engine has
    always had) or `"record"`, which files the unseparable classes on the result
    and keeps the frontier for the rest.

    `action_alphabet` widens the `act` atoms beyond the compass.  Passing it is
    how a world whose actions are not UP/DOWN/LEFT/RIGHT gets a vocabulary that
    can see which action was taken; the default `None` reads the alphabet off
    the transitions themselves when it is not the compass, and is a no-op when
    it is.
    """
    if on_unseparable not in ("raise", "record"):
        raise ValueError("on_unseparable must be 'raise' or 'record', not %r" % on_unseparable)
    states = [t.state for t in transitions]
    actions = [t.action for t in transitions]
    observed = sorted(set(actions))
    alphabet = sorted(set(action_alphabet)) if action_alphabet is not None else observed
    vocabulary = build_vocabulary(states, alphabet)
    masks = atom_masks(vocabulary, states, actions)
    universe = (1 << len(transitions)) - 1

    groups: Dict[Tuple, List[Transition]] = {}
    for transition in transitions:
        groups.setdefault((transition.action, transition.effect.key()), []).append(transition)

    rules: List[Rule] = []
    unseparable: List[Dict[str, object]] = []
    for key in sorted(groups):
        members = groups[key]
        positives = 0
        for transition in members:
            positives |= 1 << transition.index
        try:
            guard, trace, added = synthesize(positives, universe, masks)
        except NoSeparatingGuard as exc:
            if on_unseparable == "raise":
                raise
            # Absence is recorded as absence: this effect class has no guard in
            # this vocabulary, which is evidence about the vocabulary and a
            # probe target, not a reason to lose the classes that do have one.
            unseparable.append({
                "action": members[0].action,
                "effect": members[0].effect.as_json(),
                "support": sorted(t.index for t in members),
                "reason": str(exc),
            })
            continue
        size = min(max(len(guard), 1), max_frontier_size)
        frontier = enumerate_frontier(positives, universe, masks, size)
        truncated = len(guard) > max_frontier_size
        best = frontier[0] if frontier else guard
        action = members[0].action
        # Keep a concrete destination only when every witness agrees on it;
        # otherwise the rule would advertise one transition's landing cell as if
        # it were the effect of all of them.
        destinations = {t.effect.to for t in members}
        effect = Effect(
            type=members[0].effect.type,
            dy=members[0].effect.dy,
            dx=members[0].effect.dx,
            to=destinations.pop() if len(destinations) == 1 else None,
        )
        applicable = _mask_of(best, masks, universe)
        rules.append(
            Rule(
                name=structural_name(action, effect, best),
                action=action,
                effect=effect,
                guard=list(best),
                frontier=frontier,
                frontier_max_size=size,
                frontier_truncated=truncated,
                support=sorted(t.index for t in members),
                applicable=[i for i in range(len(transitions)) if (applicable >> i) & 1],
                cegis_trace=trace,
                cegis_guard=guard,
                cegis_added=added,
            )
        )

    rules.sort(key=lambda r: (r.name, r.action))
    blind = sorted(a.name for a in vocabulary
                   if masks[a] == 0 or masks[a] == universe)
    return MiningResult(
        rules=rules,
        lifted=lift(rules),
        transitions=list(transitions),
        unseparable=unseparable,
        vocabulary={
            "action_alphabet": alphabet,
            "actions_observed": observed,
            "n_atoms": len(vocabulary),
            "n_constant_atoms": len(blind),
            "n_discriminating_atoms": len(vocabulary) - len(blind),
            "act_atoms_are_all_constant": all(
                masks[a] in (0, universe) for a in vocabulary if a.kind == "act"
            ),
        },
    )
