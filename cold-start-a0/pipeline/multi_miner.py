"""Multi-track CEGIS driver.

`cegis_miner.mine` groups transitions by `(action, effect)` for a *single* track
and mines a guard per group.  A0 has three tracks and its interesting law relates
two of them, so this module does the grouping and the bookkeeping while the
synthesis itself stays upstream: `cegis_miner.synthesize` and
`cegis_miner.enumerate_frontier` are called verbatim, on masks over the extended
vocabulary in `atoms_a0`.  Both functions are generic over the atom type -- they
touch only the mask table and `atom_order_key` -- so this is reuse, not a fork.

What the driver adds:

  * one effect stream per track, read off `mdl_segmenter`'s narration
    (`move` / `recolor` / `vanish` / `appear` / `none`);
  * lifting for `none` rules as well as `move` rules (upstream lifts moves only);
  * a `frontier` on every rule, including the one-witness rules, which is the
    whole point of the exercise: the theorize step downstream has to consume a
    frontier, not a point guess.
"""

import itertools
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from engines.cegis_miner.miner import enumerate_frontier, synthesize

from pipeline.atoms_a0 import (
    DELTA, DIRECTIONS, Atom, Obs, atom_masks, build_vocabulary,
)

DIR_VAR = "?dir"
MAX_FRONTIER_SIZE = 3


def guard_cost(guard: Sequence[Atom]) -> int:
    return sum(a.cost for a in guard)


def guard_strength(guard: Sequence[Atom]) -> int:
    return sum(a.strength for a in guard)


def guard_order_key(guard: Sequence[Atom]):
    return (guard_cost(guard), len(guard), -guard_strength(guard),
            tuple(sorted(a.name for a in guard)))


@dataclass(frozen=True)
class Effect:
    """What the segmenter said happened to one track in one transition."""

    type: str                                   # move | recolor | vanish | appear | none
    dy: int = 0
    dx: int = 0
    to_color: Optional[int] = None
    direction: Optional[str] = None             # set on lifted rules

    def key(self) -> Tuple:
        return (self.type, self.dy, self.dx, self.to_color)

    def as_json(self) -> Dict[str, object]:
        out: Dict[str, object] = {"type": self.type}
        if self.type == "move":
            if self.direction is not None:
                out["direction"] = self.direction
            else:
                out["dy"], out["dx"] = self.dy, self.dx
        if self.type == "recolor":
            out["to"] = self.to_color
        return out

    def rendering(self) -> str:
        if self.type == "none":
            return "nothing happens"
        if self.type == "move":
            if self.direction is not None:
                return "moves one cell in direction %s" % self.direction
            return "moves by (%d,%d)" % (self.dy, self.dx)
        if self.type == "recolor":
            return "recolours to %s" % self.to_color
        return self.type


@dataclass
class Transition:
    index: int
    obs: Obs
    action: str
    effects: Dict[str, Effect]                  # track -> effect


@dataclass
class Rule:
    name: str
    track: str
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
    lifted_from: List[str] = field(default_factory=list)

    @property
    def coverage(self) -> str:
        return "%d/%d" % (len(self.support), len(self.applicable))

    def as_json(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "track": self.track,
            "action": self.action,
            "guard": sorted(a.name for a in self.guard),
            "guard_cost_bits": guard_cost(self.guard),
            "effect": self.effect.as_json(),
            "effect_rendering": self.effect.rendering(),
            "frontier": [sorted(a.name for a in g) for g in self.frontier],
            "frontier_size": len(self.frontier),
            "frontier_max_size": self.frontier_max_size,
            "frontier_truncated": self.frontier_truncated,
            "cegis_guard": sorted(a.name for a in self.cegis_guard),
            "cegis_iterations": len(self.cegis_trace),
            "cegis_trace": self.cegis_trace,
            "lifted_from": self.lifted_from,
            "vocabulary": "a0_relational_v1",
            "driver": "cold-start-a0/pipeline/multi_miner",
        }


# ------------------------------------------------------------------ narration

def effects_from_segmentation(seg, track_ids: Sequence[str], t: int) -> Dict[str, Effect]:
    """Read one transition's events off the segmenter, one Effect per track."""
    out = {tid: Effect(type="none") for tid in track_ids}
    for event in seg.events_at(t):
        if event.track not in out:
            continue
        if event.type == "move":
            out[event.track] = Effect(
                type="move", dy=int(event.params["dy"]), dx=int(event.params["dx"])
            )
        elif event.type == "recolor":
            to = event.params.get("to") or []
            out[event.track] = Effect(
                type="recolor", to_color=int(to[0]) if to else None
            )
        else:
            out[event.track] = Effect(type=event.type)
    return out


def mover_track(seg) -> str:
    """The track that moves most -- a structural handle, not a name."""
    counts: Dict[str, int] = {t.track_id: 0 for t in seg.tracks}
    for event in seg.events:
        if event.type == "move":
            counts[event.track] = counts.get(event.track, 0) + 1
    return max(sorted(counts), key=lambda tid: (counts[tid], tid))


def build_transitions(frames, layer, actions, seg, background: int = 0) -> List[Transition]:
    """`frames` are the full frames (guards need the walls); `layer` is the
    object layer the segmenter was run on (track colours are read off it)."""
    mover = mover_track(seg)
    track_ids = [t.track_id for t in seg.tracks]
    shape = tuple(next(t for t in seg.tracks if t.track_id == mover).shape)
    out: List[Transition] = []
    for t in range(len(frames) - 1):
        action = actions[t]
        if action is None:
            break
        obs = Obs(
            frame=tuple(tuple(row) for row in frames[t]),
            mover_anchor=seg_anchor(seg, mover, t),
            mover_shape=shape,
            anchors={tid: seg_anchor(seg, tid, t) for tid in track_ids},
            colors={tid: seg_color(seg, layer, tid, t) for tid in track_ids},
            background=background,
        )
        out.append(
            Transition(index=t, obs=obs, action=action,
                       effects=effects_from_segmentation(seg, track_ids, t))
        )
    return out


def seg_anchor(seg, track_id: str, t: int):
    track = next(x for x in seg.tracks if x.track_id == track_id)
    anchor = track.anchors[t] if t < len(track.anchors) else None
    return tuple(anchor) if anchor is not None else None


def seg_color(seg, layer, track_id: str, t: int) -> Optional[int]:
    """The track's uniform colour in frame t, read off its own mask."""
    track = next(x for x in seg.tracks if x.track_id == track_id)
    mask = track.masks[t] if t < len(track.masks) else None
    if not mask:
        return None
    values = {layer[t][r][c] for r, c in mask}
    return values.pop() if len(values) == 1 else None


# ----------------------------------------------------------------- structure

def structural_name(track: str, action: str, effect: Effect,
                    guard: Sequence[Atom]) -> str:
    """Derived from the rule's shape, never from its meaning (Theoria 1.10b)."""
    if effect.type == "none":
        return "%s_still_%s" % (track, action)
    if effect.type == "move":
        step = abs(effect.dy) + abs(effect.dx)
        if step == 1 and (effect.dy, effect.dx) == DELTA.get(action):
            return "%s_step_%s" % (track, action)
        return "%s_jump_%s" % (track, action)
    if effect.type == "recolor":
        return "%s_recolor%s_%s" % (track, effect.to_color, action)
    return "%s_%s_%s" % (track, effect.type, action)


def _normalise(rule: Rule) -> Optional[Tuple]:
    """Rule shape with the concrete direction replaced by a variable."""
    if rule.action not in DELTA:
        return None
    if rule.effect.type == "move":
        if (rule.effect.dy, rule.effect.dx) != DELTA[rule.action]:
            return None
        shape = "move(%s)" % DIR_VAR
    elif rule.effect.type == "none":
        shape = "none"
    else:
        return None
    guard = tuple(sorted(a.substitute_direction(rule.action).name for a in rule.guard))
    return (rule.track, guard, shape)


def lift(rules: Sequence[Rule]) -> List[Rule]:
    """Collapse per-direction rules that are alpha-equivalent under `?dir`."""
    groups: Dict[Tuple, List[Rule]] = {}
    for rule in rules:
        shape = _normalise(rule)
        if shape is not None:
            groups.setdefault(shape, []).append(rule)

    out: List[Rule] = []
    for shape, members in sorted(groups.items()):
        if len(members) < 2:
            continue
        members = sorted(members, key=lambda r: r.action)
        template = members[0]
        guard = [a.substitute_direction(template.action) for a in template.guard]
        frontier = [
            [a.substitute_direction(template.action) for a in g]
            for g in template.frontier
        ]
        if template.effect.type == "move":
            effect = Effect(type="move", direction=DIR_VAR)
            name = "%s_step" % template.track
        else:
            effect = Effect(type="none")
            name = "%s_still" % template.track
        out.append(
            Rule(
                name=name,
                track=template.track,
                action=DIR_VAR,
                effect=effect,
                guard=guard,
                frontier=frontier,
                frontier_max_size=template.frontier_max_size,
                frontier_truncated=any(m.frontier_truncated for m in members),
                support=sorted(i for m in members for i in m.support),
                applicable=sorted(i for m in members for i in m.applicable),
                cegis_trace=[],
                lifted_from=[m.name for m in members],
            )
        )
    return out


# -------------------------------------------------------------------- driver

@dataclass
class MiningResult:
    rules: List[Rule]
    lifted: List[Rule]
    transitions: List[Transition]
    vocabulary: List[Atom]
    masks: Dict[Atom, int]
    mover: str

    @property
    def all_rules(self) -> List[Rule]:
        return self.rules + self.lifted

    def by_name(self, name: str) -> Optional[Rule]:
        for rule in self.all_rules:
            if rule.name == name:
                return rule
        return None

    def for_track(self, track: str) -> List[Rule]:
        return [r for r in self.rules if r.track == track]

    def guards_are_mutually_exclusive(self, track: str) -> bool:
        """Constraint 9, per track: no transition is claimed by two ground rules."""
        seen = 0
        for rule in self.for_track(track):
            mask = 0
            for i in rule.applicable:
                mask |= 1 << i
            if seen & mask:
                return False
            seen |= mask
        return True

    def explains_every_transition(self, track: str) -> bool:
        covered = {i for rule in self.for_track(track) for i in rule.applicable}
        return covered == {t.index for t in self.transitions}


def mine(transitions: Sequence[Transition], track_ids: Sequence[str],
         max_frontier_size: int = MAX_FRONTIER_SIZE,
         mover: str = "") -> MiningResult:
    observations = [t.obs for t in transitions]
    actions = [t.action for t in transitions]
    vocabulary = build_vocabulary(observations, list(track_ids))
    masks = atom_masks(vocabulary, observations, actions)
    universe = (1 << len(transitions)) - 1

    rules: List[Rule] = []
    for track in track_ids:
        groups: Dict[Tuple, List[Transition]] = {}
        for transition in transitions:
            key = (transition.action, transition.effects[track].key())
            groups.setdefault(key, []).append(transition)

        for key in sorted(groups, key=lambda k: (k[0], str(k[1]))):
            members = groups[key]
            positives = 0
            for transition in members:
                positives |= 1 << transition.index
            guard, trace, _added = synthesize(positives, universe, masks)
            size = min(max(len(guard), 1), max_frontier_size)
            frontier = enumerate_frontier(positives, universe, masks, size)
            frontier.sort(key=guard_order_key)
            truncated = len(guard) > max_frontier_size
            best = frontier[0] if frontier else guard
            applicable_mask = universe
            for atom in best:
                applicable_mask &= masks[atom]
            effect = members[0].effects[track]
            rules.append(
                Rule(
                    name=structural_name(track, members[0].action, effect, best),
                    track=track,
                    action=members[0].action,
                    effect=effect,
                    guard=list(best),
                    frontier=frontier,
                    frontier_max_size=size,
                    frontier_truncated=truncated,
                    support=sorted(t.index for t in members),
                    applicable=[
                        i for i in range(len(transitions))
                        if (applicable_mask >> i) & 1
                    ],
                    cegis_trace=trace,
                    cegis_guard=guard,
                )
            )

    rules.sort(key=lambda r: (r.track, r.name, r.action))
    return MiningResult(
        rules=rules,
        lifted=lift(rules),
        transitions=list(transitions),
        vocabulary=vocabulary,
        masks=masks,
        mover=mover,
    )
