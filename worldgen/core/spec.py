"""The declarative description of one world.  Frozen, hashable, serialisable.

A `WorldSpec` is the only input to `GridWorld`; two runs of the library that
produce equal specs produce byte-identical traces.  Everything variable about a
world lives here — layout, entity placements, per-kind colours, flags — and
nothing about a world lives in code that the spec cannot reach.  That is what
makes the family *generated* rather than hand-built: `generate.py` emits specs,
and the twenty catalogue worlds are twenty JSON files, not twenty modules.

`props` and `flags` are tuples of pairs rather than dicts because the spec has
to stay hashable and to round-trip through JSON with a stable key order.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Sequence, Tuple

from .types import Cell


def _pairs(mapping: Optional[Dict[str, Any]]) -> Tuple[Tuple[str, Any], ...]:
    if not mapping:
        return ()
    return tuple(sorted((str(k), v) for k, v in mapping.items()))


@dataclass(frozen=True)
class Entity:
    """One placed thing.  `kind` decides which mechanism owns it."""

    kind: str
    cell: Cell
    props: Tuple[Tuple[str, Any], ...] = ()

    def prop(self, name: str, default: Any = None) -> Any:
        for key, value in self.props:
            if key == name:
                return value
        return default

    def as_json(self) -> Dict[str, Any]:
        return {"kind": self.kind, "cell": list(self.cell),
                "props": {k: v for k, v in self.props}}

    @staticmethod
    def make(kind: str, cell: Cell, **props: Any) -> "Entity":
        return Entity(kind=kind, cell=tuple(cell), props=_pairs(props))


@dataclass(frozen=True)
class WorldSpec:
    world_id: str
    layout: Tuple[str, ...]            # '#' wall, '.' floor; rectangular
    agent_start: Cell
    goal: Cell
    entities: Tuple[Entity, ...] = ()
    colors: Tuple[Tuple[str, int], ...] = ()     # entity kind -> colour
    families: Tuple[str, ...] = ()               # mechanism families in play
    flags: Tuple[Tuple[str, Any], ...] = ()      # e.g. gravity
    tier: int = 1
    seed: int = 0
    variant_of: Optional[str] = None
    variant_delta: str = ""
    notes: str = ""
    # The designer's claim about whether this world can be won, checked at build
    # time against the exhaustive reachability decision.  `None` means "no claim".
    #
    # It exists because the first cut of this catalogue had the label inverted and
    # nothing noticed: `t2-unsolvable-nodoor`, the world whose entire purpose is
    # to ship an unsolvability certificate, was winnable in five steps, while two
    # worlds nobody meant to break were unsolvable because two-way portals never
    # fired.  `build.py` measured `solvable` and printed it; measuring a property
    # and never comparing it to the intent is how a catalogue ships a lie about
    # itself.
    intended_solvable: Optional[bool] = None

    # ------------------------------------------------------------- geometry
    @property
    def height(self) -> int:
        return len(self.layout)

    @property
    def width(self) -> int:
        return len(self.layout[0])

    def is_wall(self, cell: Cell) -> bool:
        return self.layout[cell[0]][cell[1]] == "#"

    def in_bounds(self, cell: Cell) -> bool:
        return 0 <= cell[0] < self.height and 0 <= cell[1] < self.width

    # ------------------------------------------------------------- lookups
    def color(self, kind: str) -> int:
        for key, value in self.colors:
            if key == kind:
                return value
        raise KeyError("world %s assigns no colour to kind %r" % (self.world_id, kind))

    def flag(self, name: str, default: Any = None) -> Any:
        for key, value in self.flags:
            if key == name:
                return value
        return default

    def of_kind(self, *kinds: str) -> Tuple[Entity, ...]:
        wanted = set(kinds)
        return tuple(e for e in self.entities if e.kind in wanted)

    def forbidden_actions(self) -> "frozenset":
        """The actions this world refuses outright, from `flags["forbidden_action"]`.

        A *world-level* semantic knob, and the only one this library has that no
        entity prop can express — every other rule-level parameter in
        `worldgen/mutate.py`'s `KNOBS` table is already a prop some mechanism
        reads.  Stored as a single action name rather than a list because the
        value has to survive `_pairs` and stay hashable, and because one
        forbidden action is the edit the exam's own `forbid_action` wrapper
        makes (`exam/papers/verdict.py`).  Absent in all twenty catalogue
        worlds, so the knob is inert for them by construction.
        """
        name = self.flag("forbidden_action")
        return frozenset() if name is None else frozenset({str(name)})

    # ---------------------------------------------------------- (de)serialise
    def as_json(self) -> Dict[str, Any]:
        return {
            "world_id": self.world_id,
            "layout": list(self.layout),
            "agent_start": list(self.agent_start),
            "goal": list(self.goal),
            "entities": [e.as_json() for e in self.entities],
            "colors": {k: v for k, v in self.colors},
            "families": list(self.families),
            "flags": {k: v for k, v in self.flags},
            "tier": self.tier,
            "seed": self.seed,
            "variant_of": self.variant_of,
            "variant_delta": self.variant_delta,
            "notes": self.notes,
            "intended_solvable": self.intended_solvable,
        }

    def dumps(self) -> str:
        return json.dumps(self.as_json(), indent=2, sort_keys=True) + "\n"

    @staticmethod
    def from_json(blob: Dict[str, Any]) -> "WorldSpec":
        return WorldSpec(
            world_id=blob["world_id"],
            layout=tuple(blob["layout"]),
            agent_start=tuple(blob["agent_start"]),
            goal=tuple(blob["goal"]),
            entities=tuple(
                Entity(kind=e["kind"], cell=tuple(e["cell"]),
                       props=_pairs(e.get("props")))
                for e in blob.get("entities", ())
            ),
            colors=tuple(sorted((k, int(v)) for k, v in blob.get("colors", {}).items())),
            families=tuple(blob.get("families", ())),
            flags=_pairs(blob.get("flags")),
            tier=int(blob.get("tier", 1)),
            seed=int(blob.get("seed", 0)),
            variant_of=blob.get("variant_of"),
            variant_delta=blob.get("variant_delta", ""),
            notes=blob.get("notes", ""),
            intended_solvable=blob.get("intended_solvable"),
        )


def validate(spec: WorldSpec) -> None:
    """Structural checks that must hold before a world is ever stepped.

    These are the invariants the rest of the library assumes rather than
    re-checks: a rectangular layout, entities on floor, at most one entity per
    cell (so mechanism dispatch order cannot change behaviour), and a colour for
    every kind present that does not collide with a reserved colour or with
    another kind.
    """
    from .types import ACTIONS, RESERVED

    forbidden = spec.flag("forbidden_action")
    if forbidden is not None and forbidden not in ACTIONS:
        raise ValueError("%s: forbidden_action %r is not one of %s"
                         % (spec.world_id, forbidden, ", ".join(ACTIONS)))

    if not spec.layout or len({len(r) for r in spec.layout}) != 1:
        raise ValueError("%s: layout is not rectangular" % spec.world_id)
    for name, cell in (("agent_start", spec.agent_start), ("goal", spec.goal)):
        if not spec.in_bounds(cell) or spec.is_wall(cell):
            raise ValueError("%s: %s %r is not a floor cell" % (spec.world_id, name, cell))

    seen: Dict[Cell, str] = {}
    for entity in spec.entities:
        if not spec.in_bounds(entity.cell) or spec.is_wall(entity.cell):
            raise ValueError("%s: %s at %r is not on floor"
                             % (spec.world_id, entity.kind, entity.cell))
        if entity.cell in seen:
            raise ValueError("%s: two entities share %r (%s, %s)"
                             % (spec.world_id, entity.cell, seen[entity.cell], entity.kind))
        seen[entity.cell] = entity.kind
    if spec.agent_start in seen:
        raise ValueError("%s: agent starts on a %s" % (spec.world_id, seen[spec.agent_start]))

    kinds = sorted({e.kind for e in spec.entities})
    assigned = {k: v for k, v in spec.colors}
    for kind in kinds:
        if kind not in assigned:
            raise ValueError("%s: kind %r has no colour" % (spec.world_id, kind))
    for kind, value in assigned.items():
        if value in RESERVED:
            raise ValueError("%s: kind %r takes reserved colour %d"
                             % (spec.world_id, kind, value))
    if len(set(assigned.values())) != len(assigned):
        raise ValueError("%s: two kinds share a colour (%r)" % (spec.world_id, assigned))
