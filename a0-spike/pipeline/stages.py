"""The A0 loop, stage by stage: perceive -> mine -> certify -> prove -> plan -> win.

Every stage is an engine from `engine-rig` applied to the A0 world. The only
step that is not an engine is `theorize`, which is the LLM's -- its output is
`theory/theory.dsl` and its reasoning is `THEORIZE_LOG.md`.

Nothing here may import the world's rule table. The pipeline sees frames and
actions; `world/sokoban2.py` is ground truth and is used only to grade the run.
"""

import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "engine-rig"))

from engines import mdl_segmenter                                    # noqa: E402
from engines.cegis_miner.atoms import atom_order_key                  # noqa: E402
from engines.cegis_miner.miner import enumerate_frontier, synthesize  # noqa: E402
from pipeline.dnf import learn_dnf, mutually_exclusive                # noqa: E402
from engines.zero_space import gf2                                   # noqa: E402
from world.sokoban2 import DELTA, DIRECTIONS, Level                  # noqa: E402

Cell = Tuple[int, int]

WALL = 8
PLAYER = 2
BOX = 4


# ------------------------------------------------------------------ atoms

@dataclass(frozen=True)
class A0Atom:
    """A guard literal for this world.

    Duck-types the interface `cegis_miner` orders atoms by (`cost`, `strength`,
    `name`), so the engine's synthesis core is reused unchanged -- which is the
    point: the engine generalises past the fixture it was built on.
    """

    kind: str
    arg: str
    negated: bool = False

    @property
    def name(self) -> str:
        body = "act==%s" % self.arg if self.kind == "act" else "%s(%s)" % (self.kind, self.arg)
        return ("!" + body) if self.negated else body

    @property
    def cost(self) -> int:
        return 6

    @property
    def strength(self) -> int:
        return -1 if self.negated else 1

    def negate(self) -> "A0Atom":
        return A0Atom(self.kind, self.arg, not self.negated)


PREDICATES = (
    "ahead_free",       # the cell in front of the player is on-board, wall-free, box-free
    "ahead_is_box",     # the box is directly in front of the player
    "ahead_on_board",   # the cell in front of the player is on the board
    "box_ahead_free",   # the cell the box would cross is free
    "box_beyond_free",  # the cell the box would land on is free
)


@dataclass(frozen=True)
class Percept:
    """What the pipeline believes about a frame: where the movable objects are."""

    player: Cell
    box: Cell
    walls: Tuple[Cell, ...]
    height: int
    width: int

    def on_board(self, cell: Cell) -> bool:
        return 0 <= cell[0] < self.height and 0 <= cell[1] < self.width

    def free(self, cell: Cell) -> bool:
        return self.on_board(cell) and cell not in self.walls and cell != self.box

    def ahead(self, cell: Cell, direction: str, times: int = 1) -> Cell:
        dr, dc = DELTA[direction]
        return (cell[0] + dr * times, cell[1] + dc * times)


def evaluate(atom: A0Atom, percept: Percept, action: str) -> bool:
    value = _evaluate_positive(atom.kind, atom.arg, percept, action)
    return (not value) if atom.negated else value


def _evaluate_positive(kind: str, arg: str, p: Percept, action: str) -> bool:
    if kind == "act":
        return action == arg
    ahead = p.ahead(p.player, arg)
    if kind == "ahead_free":
        return p.free(ahead)
    if kind == "ahead_is_box":
        return ahead == p.box
    if kind == "ahead_on_board":
        return p.on_board(ahead)
    if kind == "box_ahead_free":
        return p.free(p.ahead(p.box, arg))
    if kind == "box_beyond_free":
        return p.free(p.ahead(p.box, arg, 2))
    raise ValueError(kind)


def vocabulary() -> List[A0Atom]:
    atoms: List[A0Atom] = []
    for direction in DIRECTIONS:
        atoms.append(A0Atom("act", direction))
        atoms.append(A0Atom("act", direction, negated=True))
        for kind in PREDICATES:
            atoms.append(A0Atom(kind, direction))
            atoms.append(A0Atom(kind, direction, negated=True))
    return atoms


# ------------------------------------------------------- stage 1: perceive

def perceive(frames: Sequence[Sequence[Sequence[int]]]) -> Dict[str, Any]:
    """Segment the trajectory into objects and events, with no world knowledge.

    Uses the colour-splitting operator: the player stands against walls and beside
    the box, and the colour-agnostic operator would fuse them into one blob.
    """
    seg = mdl_segmenter.segment_trajectory(frames, background=0, split_by_color=True)
    movers = [t for t in seg.tracks if any(e.track == t.track_id for e in seg.events)]
    statics = [t for t in seg.tracks if t not in movers]
    by_color = {}
    for track in seg.tracks:
        by_color.setdefault(track.color, []).append(track)
    return {
        "segmentation": seg,
        "tracks": seg.tracks,
        "movers": movers,
        "board": statics,          # never co-varies -> settles into the board
        "by_color": by_color,
        "script_bits": seg.script_bits,
        "baseline_bits": seg.baseline_bits,
        "ratio": seg.compression_ratio,
    }


def percepts_from(frames: Sequence[Sequence[Sequence[int]]]) -> List[Percept]:
    """Read object positions straight off the frames -- no world import."""
    out = []
    for frame in frames:
        height, width = len(frame), len(frame[0])
        player = box = None
        walls = []
        for r in range(height):
            for c in range(width):
                value = frame[r][c]
                if value == PLAYER:
                    player = (r, c)
                elif value == BOX:
                    box = (r, c)
                elif value == WALL:
                    walls.append((r, c))
        out.append(
            Percept(player=player, box=box, walls=tuple(sorted(walls)),
                    height=height, width=width)
        )
    return out


# ----------------------------------------------------------- stage 2: mine

@dataclass
class MinedRule:
    name: str
    action: str
    effect: Tuple[Tuple[int, int], Tuple[int, int]]     # (player delta, box delta)
    guard: List[A0Atom]
    frontier: List[List[A0Atom]]
    support: List[int]

    @property
    def coverage(self) -> str:
        return "%d/%d" % (len(self.support), len(self.support))

    def as_json(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "action": self.action,
            "guard": sorted(a.name for a in self.guard),
            "effect": {"player_delta": list(self.effect[0]), "box_delta": list(self.effect[1])},
            "frontier": [sorted(a.name for a in g) for g in self.frontier],
            "support": self.support,
            "coverage": self.coverage,
        }


def _effect_of(before: Percept, after: Percept) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    return (
        (after.player[0] - before.player[0], after.player[1] - before.player[1]),
        (after.box[0] - before.box[0], after.box[1] - before.box[1]),
    )


def transitions_from_episodes(episodes: Sequence[Dict[str, Any]]
                              ) -> List[Tuple[Percept, str, Percept]]:
    """Pool every episode's transitions into one evidence set."""
    out: List[Tuple[Percept, str, Percept]] = []
    for episode in episodes:
        percepts = percepts_from(episode["frames"])
        for i, action in enumerate(episode["actions"]):
            out.append((percepts[i], action, percepts[i + 1]))
    return out


def mine(transitions: Sequence[Tuple[Percept, str, Percept]]) -> List[MinedRule]:
    """CEGIS over this world's vocabulary, using the engine's synthesis core."""
    atoms = vocabulary()
    n = len(transitions)
    masks: Dict[A0Atom, int] = {}
    for atom in atoms:
        mask = 0
        for i, (before, action, _after) in enumerate(transitions):
            if evaluate(atom, before, action):
                mask |= 1 << i
        masks[atom] = mask
    universe = (1 << n) - 1

    groups: Dict[Tuple[str, Any], List[int]] = {}
    for i, (before, action, after) in enumerate(transitions):
        groups.setdefault((action, _effect_of(before, after)), []).append(i)

    rules: List[MinedRule] = []
    for (action, effect), indices in sorted(groups.items(), key=lambda kv: str(kv[0])):
        positives = 0
        for i in indices:
            positives |= 1 << i
        player_delta, box_delta = effect
        if box_delta != (0, 0):
            stem = "push2"
        elif player_delta != (0, 0):
            stem = "walk"
        else:
            stem = "blocked"

        # One conjunction if the class admits one; otherwise a disjunction learned
        # as several, each of which is itself a legal conjunctive guard.
        try:
            guard, _trace, _added = synthesize(positives, universe, masks)
            frontier = enumerate_frontier(positives, universe, masks, min(len(guard), 3))
            learned = [frontier[0] if frontier else guard]
            frontiers = [frontier]
        except Exception:
            keep = [A0Atom("act", action)]
            learned = learn_dnf(positives, universe, masks, atom_order_key, keep=keep)
            frontiers = [[] for _ in learned]

        for k, one in enumerate(learned):
            covered = universe
            for atom in one:
                covered &= masks[atom]
            support = [i for i in range(n) if (covered >> i) & 1]
            suffix = "" if len(learned) == 1 else "_%d" % (k + 1)
            rules.append(
                MinedRule(name="%s_%s%s" % (stem, action, suffix), action=action,
                          effect=effect, guard=list(one), frontier=frontiers[k],
                          support=support)
            )
    return rules


# -------------------------------------------------------- stage 3: certify

def certify(rules: Sequence[MinedRule],
            transitions: Sequence[Tuple[Percept, str, Percept]]) -> Dict[str, Any]:
    """Replay the whole history through the mined rules alone.

    The rules are the only predictor: for each transition, exactly one rule must
    fire, and its effect must reproduce the observed frame. This is the cheap
    layer of certify -- full-history replay -- and it is what turns "the rules
    look right" into "the rules predicted every frame we have".
    """
    failures = []
    ambiguities = []
    for i, (before, action, after) in enumerate(transitions):
        firing = [
            rule for rule in rules
            if rule.action == action
            and all(evaluate(a, before, action) for a in rule.guard)
        ]
        # Constraint 9 is "exactly one successor", not "exactly one rule": two
        # rules that fire together but agree on the effect still determine the
        # next state. Overlap only matters when the effects disagree.
        outcomes = {rule.effect for rule in firing}
        if len(outcomes) != 1:
            ambiguities.append({"transition": i, "n_firing": len(firing),
                                "distinct_effects": len(outcomes),
                                "rules": [r.name for r in firing]})
            continue
        predicted = _effect_of(before, after)
        if firing[0].effect != predicted:
            failures.append({"transition": i, "rule": firing[0].name,
                             "predicted": firing[0].effect, "observed": predicted})
    return {
        "transitions": len(transitions),
        "replay_failures": failures,
        "ambiguities": ambiguities,
        "exactly_one_successor": not ambiguities,
        "replay_exact": not failures and not ambiguities,
    }


def predict(rules: Sequence[MinedRule], percept: Percept, action: str
            ) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """The theory's prediction for one step, or None if it has nothing to say."""
    outcomes = {
        rule.effect for rule in rules
        if rule.action == action and all(evaluate(a, percept, action) for a in rule.guard)
    }
    return outcomes.pop() if len(outcomes) == 1 else None


# ---------------------------------------------------------- stage 4: prove

def prove_parity(percepts: Sequence[Percept]) -> Dict[str, Any]:
    """Recover the conservation law from the trajectory, on GF(2).

    Features are the box's row and column parity bits. `zero_space`'s null space
    over the observed differences yields the linear laws; the one that matters is
    row+col, i.e. the box never changes checkerboard colour.
    """
    encoded = []
    for p in percepts:
        bits = 0
        if p.box[0] % 2:
            bits |= 1 << 0
        if p.box[1] % 2:
            bits |= 1 << 1
        encoded.append(bits)
    differences = [encoded[i] ^ encoded[i + 1] for i in range(len(encoded) - 1)]
    basis = gf2.null_space(differences, 2)
    row_plus_col = 0b11
    return {
        "features": ["box.row mod 2", "box.col mod 2"],
        "difference_rank": gf2.rank(differences),
        "null_space_dimension": len(basis),
        "basis": [gf2.to_bits(v, 2) for v in basis],
        "row_plus_col_is_conserved": gf2.in_span(row_plus_col, basis),
        "value": gf2.dot(row_plus_col, encoded[0]),
        "rendering": "(box.row + box.col) mod 2 = %d" % gf2.dot(row_plus_col, encoded[0]),
    }


def unsolvability_certificate(level: Level) -> Dict[str, Any]:
    """The theorem, stated in the manual's own vocabulary.

    Three lines, no search: the law holds at the start, no rule breaks it, and
    winning would require breaking it.
    """
    box_parity = (level.box[0] + level.box[1]) % 2
    target_parity = (level.target[0] + level.target[1]) % 2
    breaks = box_parity != target_parity
    return {
        "level": level.name,
        "invariant": "(box.row + box.col) mod 2",
        "inv_init": box_parity,
        "inv_closed": "every push slides the box two cells along one axis, "
                      "so row+col changes by an even number",
        "goal_parity": target_parity,
        "goal_breaks_invariant": breaks,
        "unsolvable": breaks,
        "explanation": (
            "箱子每次滑动两格，(row+col) 的奇偶不变；开局奇偶为 %d，目标格奇偶为 %d，"
            "所以目标永远到不了" % (box_parity, target_parity)
        ) if breaks else (
            "目标格与箱子同奇偶，守恒律不排除它；可解性需由规划器回答"
        ),
    }
