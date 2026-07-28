"""The family generator: ASCII art in, `WorldSpec` out, plus the catalogue of 20.

A world is written as a picture and a legend.  That is not a convenience — it is
what makes the catalogue a *family* rather than twenty hand-built modules.  The
picture fixes the geometry; the legend fixes what each glyph means; and because
the legend is a parameter, the same picture with one legend entry changed is a
**variant pair** — two worlds identical in every respect except one rule.  Those
pairs are the raw material an exam needs (`worldgen/USAGE.md`), and they are
free here rather than laboriously constructed.

Palette assignment is automatic and per world.  ARC has ten colours and this
library has seven families, so no global assignment exists; `palette_for` draws
the colour keys a world actually needs out of `POOL` in a fixed canonical order
and fails loudly if a world needs more than seven.  A downstream reader must
therefore learn the mapping from the trace instead of memorising it, which is
the situation on ARC and is cheaper to build in than to retrofit.

```bash
python -m worldgen.generate            # build every world into worldgen/out/worlds/
python -m worldgen.generate t1-push-open t1-push-corridor
```
"""

import argparse
import json
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .core.spec import Entity, WorldSpec, validate
from .core.types import POOL, Cell
from .mechanisms import FAMILIES        # noqa: F401  — importing registers every family

# Colour keys each entity kind needs, beyond the reserved floor/wall/agent.
# `cycler` is special: it needs one key per phase, so its list is trimmed to the
# largest `k` any cycler in the world actually uses.
COLOR_KEYS: Dict[str, Tuple[str, ...]] = {
    "block": ("block",),
    "switch": ("switch", "switch_on"),
    "door": ("door",),
    "portal": ("portal",),
    "token": ("token",),
    "lock": ("lock",),
    "fragile": ("fragile", "collapsed"),
    "cycler": ("cycler", "cycler_1", "cycler_2", "cycler_3"),
}

# Fixed order, so that two worlds containing the same kinds get the same colours
# and a human comparing two GROUND_TRUTH.md files is not reading noise.
CANONICAL = ("block", "switch", "switch_on", "door", "portal", "token", "lock",
             "fragile", "collapsed", "cycler", "cycler_1", "cycler_2", "cycler_3")

KIND_FAMILY = {
    "block": "push",
    "switch": "switch_door", "door": "switch_door",
    "portal": "portal",
    "token": "count_lock", "lock": "count_lock",
    "fragile": "consumable",
    "cycler": "color_cycle",
}


def palette_for(entities: Sequence[Entity]) -> Tuple[Tuple[str, int], ...]:
    kinds = {e.kind for e in entities}
    needed: List[str] = []
    for kind in sorted(kinds):
        keys = COLOR_KEYS[kind]
        if kind == "cycler":
            k = max(int(e.prop("k", 3)) for e in entities if e.kind == "cycler")
            keys = keys[:k]
        needed.extend(keys)
    ordered = [key for key in CANONICAL if key in set(needed)]
    if len(ordered) > len(POOL):
        raise ValueError("world needs %d colours, the pool has %d: %r"
                         % (len(ordered), len(POOL), ordered))
    return tuple(sorted(zip(ordered, POOL)))


def from_art(world_id: str, art: Sequence[str], legend: Dict[str, Any],
             *, tier: int = 1, seed: int = 0, notes: str = "",
             variant_of: Optional[str] = None, variant_delta: str = "",
             gravity: bool = False, extra_families: Sequence[str] = (),
             intended_solvable: Optional[bool] = True) -> WorldSpec:
    """Parse a picture.

    `legend` maps a glyph to one of:

    * `"agent"` / `"goal"` — the start and the objective (both plain floor);
    * `("mark", name)` — a floor cell whose position other entries refer to by
      name (a one-way portal's destination, for instance);
    * `(kind, {**props})` — an entity.  A `props` value of the form
      `("@", name)` is resolved to the cell of the mark called `name`, which is
      how a picture stays a picture instead of degenerating into coordinates.

    `.` and `#` need no legend entry.
    """
    art = [row.rstrip("\n") for row in art if row.strip("\n") != ""]
    width = len(art[0])
    if any(len(row) != width for row in art):
        raise ValueError("%s: art rows differ in width" % world_id)

    marks: Dict[str, Cell] = {}
    agent: Optional[Cell] = None
    goal: Optional[Cell] = None
    placements: List[Tuple[str, Cell, Dict[str, Any]]] = []
    layout: List[str] = []

    for r, row in enumerate(art):
        line = []
        for c, glyph in enumerate(row):
            cell = (r, c)
            if glyph == "#":
                line.append("#")
                continue
            line.append(".")
            if glyph == ".":
                continue
            entry = legend.get(glyph)
            if entry is None:
                raise ValueError("%s: glyph %r has no legend entry" % (world_id, glyph))
            if entry == "agent":
                agent = cell
            elif entry == "goal":
                goal = cell
            elif isinstance(entry, tuple) and entry[0] == "mark":
                marks[entry[1]] = cell
            else:
                kind, props = entry
                placements.append((kind, cell, dict(props)))
        layout.append("".join(line))

    if agent is None or goal is None:
        raise ValueError("%s: art must contain an agent and a goal" % world_id)

    entities: List[Entity] = []
    for kind, cell, props in placements:
        resolved = {}
        for key, value in props.items():
            if isinstance(value, tuple) and len(value) == 2 and value[0] == "@":
                if value[1] not in marks:
                    raise ValueError("%s: mark %r is never placed" % (world_id, value[1]))
                resolved[key] = list(marks[value[1]])
            else:
                resolved[key] = value
        entities.append(Entity.make(kind, cell, **resolved))

    families = sorted({KIND_FAMILY[e.kind] for e in entities} | set(extra_families)
                      | ({"gravity"} if gravity else set()))
    spec = WorldSpec(
        world_id=world_id,
        layout=tuple(layout),
        agent_start=agent,
        goal=goal,
        entities=tuple(entities),
        colors=palette_for(entities),
        families=tuple(families),
        flags=(("gravity", True),) if gravity else (),
        tier=tier,
        seed=seed,
        variant_of=variant_of,
        variant_delta=variant_delta,
        notes=notes,
        intended_solvable=intended_solvable,
    )
    validate(spec)
    return spec


# ===================================================================== worlds
#
# Twenty worlds in three complexity tiers.  Four of them are **variant pairs** —
# the same picture with one legend entry changed — and one is unsolvable.  The
# pairs are the point: `t1-push-open` and `t1-push-corridor` differ only in
# geometry and their `push` rule differs in how often a trajectory can witness
# it, which is A0′'s finding reduced to two files a reader can diff.

A = "agent"
G = "goal"


def _catalogue() -> List[WorldSpec]:
    out: List[WorldSpec] = []

    # ---------------------------------------------------------------- tier 1
    out.append(from_art("t1-walk-maze", [
        "#########",
        "#A..#...#",
        "#.#.#.#.#",
        "#.#...#.#",
        "#.#####.#",
        "#......G#",
        "#########",
    ], {"A": A, "G": G}, tier=1, seed=101,
        notes="No mechanism at all: `walk` and `blocked_by_wall` only. The floor "
              "of the catalogue, and the control every other world is read against."))

    push_art = [
        "#######",
        "#..#..#",
        "#.AB.G#",
        "#..#..#",
        "#######",
    ]
    out.append(from_art("t1-push-open", push_art, {
        "A": A, "G": G, "B": ("block", {}),
    }, tier=1, seed=102,
        notes="A block in the only gap of a divider, with room on both sides. The "
              "agent can walk round and shove it back, so `push` is witnessable "
              "unboundedly often."))

    out.append(from_art("t1-push-corridor", [
        "######",
        "#A.B.#",
        "#.####",
        "#...G#",
        "######",
    ], {"A": A, "G": G, "B": ("block", {})}, tier=1, seed=103,
        variant_of="t1-push-open",
        variant_delta="same mechanism, dead-end corridor instead of an open room",
        notes="The block can be shoved exactly once before it meets the wall, and "
              "the agent can never reach its far side. Identical rule, one witness. "
              "This is the A0 vs A0′ contrast with the mechanism held fixed and only "
              "the geometry moved."))

    # The divider at column 4 is load-bearing and was not, in the first cut of
    # this catalogue: the door sat in an open room with floor above and below it,
    # so all three worlds built on this art were winnable **without ever touching
    # the switch** and the headline mechanic was decorative.  `D` is now the only
    # opening in the wall, which is what makes `t2-unsolvable-nodoor` — the same
    # art with the switch deleted — actually unsolvable.
    #
    # `E` is a second door on the same net, next to the switch, and it is there to
    # give one world in the catalogue a reachable `blocked_toggle_would_shut_door`:
    # standing on `E` and pressing `S` would shut a door under the agent.  Without
    # it that branch is dormant everywhere and the family never witnesses it.
    switch_art = [
        "#######",
        "#.A.#.#",
        "#...#.#",
        "#...D.#",
        "#SE.#G#",
        "#######",
    ]
    switch_doors = {
        "D": ("door", {"net": "a", "polarity": "open_when_on"}),
        "E": ("door", {"net": "a", "polarity": "open_when_on"}),
    }
    out.append(from_art("t1-switch-toggle", switch_art, dict({
        "A": A, "G": G,
        "S": ("switch", {"mode": "toggle", "net": "a"}),
    }, **switch_doors), tier=1, seed=104,
        notes="A0′'s central mechanic on its own. The switch is re-witnessable from "
              "all four directions and both ways, and it is load-bearing: the door "
              "is the only gap in the divider, so the goal is unreachable until it "
              "is thrown."))

    out.append(from_art("t1-switch-latch", switch_art, dict({
        "A": A, "G": G,
        "S": ("switch", {"mode": "latch", "net": "a"}),
    }, **switch_doors), tier=1, seed=105,
        variant_of="t1-switch-toggle",
        variant_delta="the switch is a latch: it sets once and never clears",
        notes="Byte-identical geometry to `t1-switch-toggle`; only `mode` differs. "
              "This is A0's Button against A0′'s Switch, isolated."))

    out.append(from_art("t1-portal-oneway", [
        "#########",
        "#A......#",
        "#.#####.#",
        "#.#x..#.#",
        "#.#.###.#",
        "#P#.#.#G#",
        "#...#...#",
        "#########",
    ], {"A": A, "G": G, "x": ("mark", "dest"),
        "P": ("portal", {"mode": "oneway", "dest": ("@", "dest")})},
        tier=1, seed=106,
        notes="One mouth, one destination, no way back except on foot. The rule is "
              "re-witnessable because the agent can walk back round to the mouth — "
              "the *route* is one-way, the *rule* is not, and the stamp distinguishes "
              "them."))

    out.append(from_art("t1-cycler-gate", [
        "#######",
        "#.....#",
        "#.A.C.#",
        "#.....#",
        "#....G#",
        "#######",
    ], {"A": A, "G": G, "C": ("cycler", {"k": 3, "open_phase": 2})},
        tier=1, seed=107,
        notes="A gate that has to be pushed twice to open and stays open. Fully "
              "reversible: keep pushing and the phase comes back round. The cheapest "
              "world in the catalogue for which the naive 'colour means state' "
              "reading is right."))

    out.append(from_art("t1-tokens-lock", [
        "#########",
        "#A.T.T..#",
        "#.#####.#",
        "#T..L..G#",
        "#########",
    ], {"A": A, "G": G, "T": ("token", {}), "L": ("lock", {"k": 3})},
        tier=1, seed=108,
        notes="Collect three, then the lock opens. Monotone by construction: every "
              "`collect_token` has exactly one witness, and the lock never re-closes."))

    out.append(from_art("t1-fragile-bridge", [
        "#######",
        "#A.F.G#",
        "#.#.#.#",
        "#..F..#",
        "#######",
    ], {"A": A, "G": G, "F": ("fragile", {})},
        tier=1, seed=109,
        notes="Two one-shot crossings and two routes. Cross the wrong one and the "
              "other still gets you there; cross both and you are stranded. The "
              "collapse lands one frame *after* the agent leaves, which is the "
              "inductively interesting bit."))

    # ---------------------------------------------------------------- tier 2
    out.append(from_art("t2-switch-push", [
        "#########",
        "#A......#",
        "#.#####.#",
        "#.B.D..G#",
        "#.#####.#",
        "#S......#",
        "#########",
    ], {"A": A, "G": G, "B": ("block", {}),
        "S": ("switch", {"mode": "toggle", "net": "a"}),
        "D": ("door", {"net": "a", "polarity": "open_when_on"})},
        tier=2, seed=201,
        notes="Two families that interact through geometry only: the block can be "
              "parked in front of the door, which is a configuration no single-family "
              "world can produce."))

    portal_art = [
        "#########",
        "#A...#..#",
        "#.####..#",
        "#P..##..#",
        "#.###..Q#",
        "#.....#G#",
        "#########",
    ]
    out.append(from_art("t2-portal-pair", portal_art, {
        "A": A, "G": G,
        "P": ("portal", {"mode": "twoway", "pair": "p"}),
        "Q": ("portal", {"mode": "twoway", "pair": "p"}),
    }, tier=2, seed=202,
        notes="Two mouths, same colour, and nothing in the palette says they are "
              "linked — the pairing has to be induced from behaviour."))

    out.append(from_art("t2-portal-paired", portal_art, {
        "A": A, "G": G,
        "P": ("portal", {"mode": "paired", "pair": "p"}),
        "Q": ("portal", {"mode": "paired", "pair": "p"}),
    }, tier=2, seed=203,
        variant_of="t2-portal-pair",
        variant_delta="`paired` instead of `twoway`: the agent exits *through* the "
                      "partner, so the landing cell depends on the direction of travel",
        notes="The variant that makes direction observable. A miner that has not "
              "lifted `?dir` cannot state this rule in fewer than four clauses."))

    out.append(from_art("t2-gravity-push", [
        "#########",
        "#A......#",
        "###.#####",
        "#....B..#",
        "#.#######",
        "#......G#",
        "#########",
    ], {"A": A, "G": G, "B": ("block", {})},
        tier=2, seed=204, gravity=True,
        notes="Ledges and a shaft. `UP` is inert here — the agent moves and gravity "
              "settles it straight back — and descending a ledge cannot be undone, "
              "so the reachable graph is genuinely layered rather than a big "
              "reversible blob."))

    out.append(from_art("t2-lock-fragile", [
        "#########",
        "#A.T.T#G#",
        "#.###.#.#",
        "#T..#.#F#",
        "#.#.#.#.#",
        "#...#.L.#",
        "#########",
    ], {"A": A, "G": G, "T": ("token", {}), "L": ("lock", {"k": 3}),
        "F": ("fragile", {})},
        tier=2, seed=205,
        notes="Both irreversible families at once. Nearly every rule here has a "
              "single witness, which makes it the worst case for a pipeline that "
              "leans on repetition — and therefore the one worth running."))

    out.append(from_art("t2-cycler-lock", [
        "#########",
        "#A..T..T#",
        "#.#####.#",
        "#.C.L..G#",
        "#########",
    ], {"A": A, "G": G, "C": ("cycler", {"k": 2, "open_phase": 1}),
        "T": ("token", {}), "L": ("lock", {"k": 2})},
        tier=2, seed=206,
        notes="One reversible gate and one monotone one, side by side, so the "
              "reversibility stamp has to separate them within a single world."))

    out.append(from_art("t2-unsolvable-nodoor", [
        "#######",
        "#.A.#.#",
        "#...#.#",
        "#...D.#",
        "#.E.#G#",
        "#######",
    ], {"A": A, "G": G, **switch_doors},
        tier=2, seed=207, intended_solvable=False,
        variant_of="t1-switch-toggle",
        variant_delta="the switch is deleted, so the door's net has no driver",
        notes="cold-start-a0's unsolvable variant, generalised: a door on an empty "
              "net never opens. Ships an exhaustive-reachability certificate and "
              "names the entity whose removal would flip it."))

    # ---------------------------------------------------------------- tier 3
    out.append(from_art("t3-full-house", [
        "##########",
        "#A...#...#",
        "#.#..#.#.#",
        "#.#B.D.#.#",
        "#.#..#.#.#",
        "#P#..#.#Q#",
        "#S.......#",
        "#.......G#",
        "##########",
    ], {"A": A, "G": G, "B": ("block", {}),
        "S": ("switch", {"mode": "toggle", "net": "a"}),
        "D": ("door", {"net": "a", "polarity": "open_when_on"}),
        "P": ("portal", {"mode": "twoway", "pair": "p"}),
        "Q": ("portal", {"mode": "twoway", "pair": "p"})},
        tier=3, seed=301,
        notes="Push, switch-door and a two-way portal in one grid. Three families is "
              "where the vocabulary a segmenter has to invent stops being obvious."))

    out.append(from_art("t3-gravity-fragile", [
        "#########",
        "#A......#",
        "###F#####",
        "#...B...#",
        "#####F###",
        "#......G#",
        "#########",
    ], {"A": A, "G": G, "B": ("block", {}), "F": ("fragile", {})},
        tier=3, seed=302, gravity=True,
        notes="Gravity, a shovable block and two one-shot floors. Every descent is "
              "one-way and every crossing is one-shot, so the reachable graph is "
              "close to a DAG — the extreme opposite of `t1-cycler-gate`."))

    out.append(from_art("t3-cycler-portal-lock", [
        "##########",
        "#A..T#..T#",
        "#.##.#.#.#",
        "#.C..#.#.#",
        "#.##.#.#.#",
        "#P..L#..Q#",
        "#.......G#",
        "##########",
    ], {"A": A, "G": G, "C": ("cycler", {"k": 3, "open_phase": 1}),
        "T": ("token", {}), "L": ("lock", {"k": 2}),
        "P": ("portal", {"mode": "twoway", "pair": "p"}),
        "Q": ("portal", {"mode": "twoway", "pair": "p"})},
        tier=3, seed=303,
        notes="A reversible gate, a monotone lock and a teleport, so that a single "
              "world contains one rule of each reversibility class."))

    out.append(from_art("t3-latch-maze", [
        "##########",
        "#A..T#..F#",
        "#.##.#.#.#",
        "#..S.#.#.#",
        "#.##.#.#.#",
        "#T.#D#T.L#",
        "#.......G#",
        "##########",
    ], {"A": A, "G": G, "T": ("token", {}), "L": ("lock", {"k": 3}),
        "F": ("fragile", {}),
        "S": ("switch", {"mode": "latch", "net": "a"}),
        "D": ("door", {"net": "a", "polarity": "open_when_on"})},
        tier=3, seed=304,
        notes="The hardest world in the catalogue for an inductive pipeline: a latch, "
              "three tokens, a lock and a one-shot floor, so almost nothing can be "
              "seen twice. Built as the standing counter-example to any claim that "
              "coverage is what a manual needs."))

    return out


CATALOGUE: Tuple[WorldSpec, ...] = tuple(_catalogue())
BY_ID: Dict[str, WorldSpec] = {s.world_id: s for s in CATALOGUE}


def write_catalogue(dirname: str) -> List[str]:
    os.makedirs(dirname, exist_ok=True)
    written = []
    for spec in CATALOGUE:
        path = os.path.join(dirname, spec.world_id + ".json")
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(spec.dumps())
        written.append(path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("worlds", nargs="*", help="world ids; default all")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    write_catalogue(os.path.join(here, "catalog"))
    print("catalogue: %d worlds" % len(CATALOGUE))
    for spec in CATALOGUE:
        if args.worlds and spec.world_id not in args.worlds:
            continue
        print("  %-24s tier=%d families=%s" % (spec.world_id, spec.tier,
                                               ",".join(spec.families) or "-"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
