"""A `worldgen` world as a boolean `System`, and the gate that proves it is that world.

Axis C asks whether *composing mechanisms* costs IC3 anything once state-space
size is held fixed.  `worldgen/` supplies the worlds -- twenty of them, one to
three mechanism families each, fully deterministic, with an independent
reachability oracle of its own.  This module is the adapter, and it is where all
of the axis's honesty problems live.

**The multi-valued / boolean gap, stated up front.**  `worldgen.core.types.State`
is `(agent: Cell, vars: Tuple[int, ...])` and those ints are *multi-valued*: a
`consumable` tile is 0/1/2, a `color_cycle` phase is anything in `range(k)`.
`engines.ic3_pdr` is boolean and nothing else.  So the world has to be re-encoded
before IC3 can see it, and the encoding this module uses is:

    one bit per floor cell        `at_r3c4`   -- one-hot, exactly one is true
    one bit per two-valued slot   `token_r1c3`, `switch_r4c1`
    one bit per value of a wider  `fragile_r3c7_is0/1/2`, `cycler_r3c2_is0/1/2`
    slot                             -- one-hot within the slot

**And here is the caveat the whole axis has to carry.**  `System.states` is an
explicitly enumerated tuple, not the 2^n product of the bit vector, and this
module hands IC3 only the **declared product**: every floor cell crossed with
every in-domain value of every slot.  For `t3-latch-maze` that is 1680 states out
of a 2^46 bit space.  Everything outside it -- an agent one-hot with two bits set,
a `fragile` tile that is both intact and collapsed -- simply does not exist as far
as the search is concerned.

That means **the invariant IC3 returns is inductive over the declared subspace
and over nothing else**.  It is not a theorem about the 2^46 bit space, and a
reader who forgets that will over-read it.  Structurally this is exactly the
`shrunken-domain` forgery `recheck/` exists to catch: a certificate that looks
strong because the domain it quantifies over was quietly made small.  The
difference between this and a forgery is that the shrink is *declared*, is
*named in every row* (`n_states`, `declared_product`), and is *forced* -- the
alternative is a one-hot relaxation over 2^46 states that no enumerating oracle
can walk.  It is a caveat, not a defence: axis C's rows measure IC3 on the
well-formed subspace of a composed world, and that is the claim they support.

**The gate.**  Before IC3 runs, `transcription_mismatches` asserts that the
adapter's transition relation equals `GridWorld.transitions()` edge for edge on
the reachable set -- same labels, same successors, both directions.  It also
asserts the encode/decode round trip is the identity on every declared state,
that every reachable state is inside the declared subspace, and that the chosen
bad set is disjoint from the reachable set according to `GridWorld.reachable()`.
A world that fails any of it is verdict `adapter-mismatch`, never `timeout` and
never a capability claim.

**What the gate is, and what it is not.**  It is *not* a second transcription of
`worldgen`'s rules the way `harness._independent_moves` is a second transcription
of the peg rule -- writing one would mean re-implementing `gravity.settle`,
portal landing and `consumable`'s three-state tile, which is the expensive
worldgen-to-ruleset transcriber this axis explicitly does not build.  What it is
is a proof that the *encoding* is a faithful, bijective, edge-preserving image of
the world on the reachable set.  That is the failure mode that actually threatens
this axis: get `consumable`'s domain wrong at 2 values instead of 3 and every
ARMED state falls outside the declared subspace, edges vanish, and IC3 returns a
fast invariant about a world that is not the world.  The gate catches exactly
that, and says so rather than claiming more.

**Choosing the bad set.**  19 of the 20 worlds are solvable, so asking IC3 "can
the agent reach the goal" returns a `Counterexample` -- a cheap breadth-first
walk that measures nothing about invariant scaling.  `System.bad` is any subset
of the declared space, so this module picks one that is genuinely unreachable and
separated by a **mechanism** rather than by a wall:

* `t1-switch-latch` -- *the agent stands on the goal cell with the latch unset*.
  The only opening in the divider is a door on the latch's net, and a latch never
  clears, so the conjunction is unreachable and the reason is one-way state.
* every world with a `lock` -- *the agent stands on the lock cell with fewer than
  k tokens collected*.  `walk_through_lock` is the only route onto the cell and
  the collected count is monotone, so again the separation is the mechanism.

Both are checked, not asserted: the gate confirms the bad set is disjoint from
`GridWorld.reachable()`, and confirms every agent cell it mentions *is* somewhere
the agent can stand in some reachable state -- which is what makes it a
mechanism cut rather than the walled-off pocket that 8 of the 20 worlds would
otherwise offer, whose invariant is the trivial "the agent is never there".

`push` and `gravity` are refused outright (`UnsupportedWorld`).  Both relocate
entities by writing encoded cells into other mechanisms' slots, so their slot
domain is the floor set rather than a small constant and the declared product
stops being small.  The six worlds axis C walks avoid both without losing a
composition step.
"""

import itertools
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


def _ensure_importable() -> None:
    """Put `engine-rig/` and the repo root on `sys.path`.

    `worldgen/` is a sibling of `engine-rig/` at the repo root and is another
    track's territory: it is imported, never edited.  Computed from `__file__`
    so that nothing here depends on where the checkout lives -- an absolute path
    must not reach an artefact.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    engine_rig = os.path.dirname(here)
    repo_root = os.path.dirname(engine_rig)
    for path in (engine_rig, repo_root):
        if path not in sys.path:
            sys.path.insert(0, path)


_ensure_importable()

from engines.ic3_pdr.system import State as BoolState          # noqa: E402
from engines.ic3_pdr.system import System                       # noqa: E402
from worldgen.core import solvability                           # noqa: E402
from worldgen.core.spec import Entity, WorldSpec                 # noqa: E402
from worldgen.core.types import ACTIONS, Cell                    # noqa: E402
from worldgen.core.types import State as WorldState              # noqa: E402
from worldgen.core.world import GridWorld                        # noqa: E402
from worldgen.generate import BY_ID                              # noqa: E402


class UnsupportedWorld(Exception):
    """This world cannot be given a small declared product, so it is refused.

    Raised rather than approximated.  A world whose slot domain is "every floor
    cell" (`push`, and `gravity` which moves other families' entities) would blow
    the declared product up by |floor| per movable, and a silently truncated
    domain is precisely the `adapter-mismatch` this package exists to make
    impossible.
    """


class EncodingError(Exception):
    """A state does not fit the declared encoding.  The gate reports it."""


# The families this adapter can encode, and the domain of one slot of each.  A
# family absent from here is refused, so adding one to `worldgen/` cannot
# silently produce a wrong declared product.
UNSUPPORTED_FAMILIES: Tuple[str, ...] = ("push", "gravity")

#: family -> the entity kind that carries the family's state vector.  `None`
#: means the family holds no state at all (`portal` is a pure function of the
#: spec, which is why it costs a composition step and no state space).
STATEFUL_KIND: Dict[str, Optional[str]] = {
    "switch_door": "switch",     # doors hold no state; they mirror their net
    "count_lock": "token",       # locks hold no state; they read the count
    "consumable": "fragile",
    "color_cycle": "cycler",
    "portal": None,
}


def _domain_of(kind: str, entity: Entity) -> Tuple[int, ...]:
    if kind == "switch":
        return (0, 1)                                  # off / on
    if kind == "token":
        return (0, 1)                                  # uncollected / collected
    if kind == "fragile":
        return (0, 1, 2)                               # INTACT / ARMED / COLLAPSED
    if kind == "cycler":
        return tuple(range(int(entity.prop("k", 3))))  # phase
    raise UnsupportedWorld("no declared domain for entity kind %r" % kind)


# ------------------------------------------------------------------- the layout

@dataclass(frozen=True)
class Slot:
    """One entry of `worldgen`'s flat `State.vars`, and the bits that encode it."""

    name: str
    family: str
    kind: str
    cell: Cell
    index: int                      # position in `State.vars`
    domain: Tuple[int, ...]
    bits: Tuple[int, ...]           # boolean variable indices
    onehot: bool                    # False: one bit, true iff the value is 1

    def as_json(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "family": self.family,
            "kind": self.kind,
            "cell": list(self.cell),
            "index": self.index,
            "domain": list(self.domain),
            "bits": list(self.bits),
            "onehot": self.onehot,
        }


def cell_name(cell: Cell) -> str:
    return "at_r%dc%d" % cell


@dataclass(frozen=True)
class Layout:
    """The bijection between `worldgen`'s `State` and a boolean vector."""

    world_id: str
    families: Tuple[str, ...]
    cells: Tuple[Cell, ...]            # floor cells, sorted
    slots: Tuple[Slot, ...]            # sorted by `index`
    variables: Tuple[str, ...]

    # ------------------------------------------------------------ sizes
    @property
    def declared_product(self) -> int:
        total = len(self.cells)
        for slot in self.slots:
            total *= len(slot.domain)
        return total

    @property
    def n_variables(self) -> int:
        return len(self.variables)

    def cell_index(self, cell: Cell) -> int:
        try:
            return self.cells.index(cell)
        except ValueError:
            raise EncodingError("cell %r is not a floor cell of %s"
                                % (cell, self.world_id))

    # --------------------------------------------------------- the bijection
    def encode(self, state: WorldState) -> BoolState:
        bits = [False] * len(self.variables)
        bits[self.cell_index(state.agent)] = True
        if len(state.vars) != len(self.slots):
            raise EncodingError(
                "%s: state has %d vars, the layout declares %d slots"
                % (self.world_id, len(state.vars), len(self.slots))
            )
        for slot in self.slots:
            value = state.vars[slot.index]
            if value not in slot.domain:
                raise EncodingError(
                    "%s: slot %s holds %r, outside its declared domain %r"
                    % (self.world_id, slot.name, value, slot.domain)
                )
            if slot.onehot:
                bits[slot.bits[slot.domain.index(value)]] = True
            elif value == 1:
                bits[slot.bits[0]] = True
        return tuple(bits)

    def decode(self, bits: BoolState) -> WorldState:
        if len(bits) != len(self.variables):
            raise EncodingError("%s: %d bits, the layout declares %d variables"
                                % (self.world_id, len(bits), len(self.variables)))
        hot = [i for i in range(len(self.cells)) if bits[i]]
        if len(hot) != 1:
            raise EncodingError("%s: %d agent bits are set, expected exactly 1"
                                % (self.world_id, len(hot)))
        values: List[int] = []
        for slot in self.slots:
            if slot.onehot:
                on = [v for v, bit in zip(slot.domain, slot.bits) if bits[bit]]
                if len(on) != 1:
                    raise EncodingError(
                        "%s: slot %s has %d bits set, expected exactly 1"
                        % (self.world_id, slot.name, len(on))
                    )
                values.append(on[0])
            else:
                values.append(1 if bits[slot.bits[0]] else 0)
        return WorldState(agent=self.cells[hot[0]], vars=tuple(values))

    # -------------------------------------------------------------- helpers
    def slots_of_kind(self, kind: str) -> Tuple[Slot, ...]:
        return tuple(slot for slot in self.slots if slot.kind == kind)

    def declared(self) -> Tuple[WorldState, ...]:
        """Every well-formed state: floor cells crossed with every slot domain.

        Sorted, because every downstream loop is sorted and `System.states` has
        to be reproducible byte for byte (`engines.ic3_pdr.system.peg_system`
        sorts for the same reason).
        """
        # Materialised, not left as the iterator `product` returns: the
        # comprehension below walks it once per cell, and an exhausted iterator
        # silently yields a declared set of one cell's worth of states.
        combos = list(itertools.product(*[slot.domain for slot in self.slots]))
        out = [
            WorldState(agent=cell, vars=tuple(combo))
            for cell in self.cells
            for combo in combos
        ]
        return tuple(sorted(out, key=lambda s: s.key()))

    def as_json(self) -> Dict[str, Any]:
        return {
            "world_id": self.world_id,
            "families": list(self.families),
            "n_floor_cells": len(self.cells),
            "n_variables": self.n_variables,
            "declared_product": self.declared_product,
            "slots": [slot.as_json() for slot in self.slots],
        }


def build_layout(world_id: str) -> Tuple[GridWorld, Layout]:
    """The world and its encoding.  Cheap: no transition relation is built."""
    if world_id not in BY_ID:
        raise KeyError("no worldgen world %r" % world_id)
    spec: WorldSpec = BY_ID[world_id]
    world = GridWorld(spec)

    families = tuple(m.name for m in world.mechanisms)
    for name in families:
        if name in UNSUPPORTED_FAMILIES:
            raise UnsupportedWorld(
                "%s uses %r, whose slot domain is the floor set rather than a "
                "small constant -- the declared product would not stay small and "
                "a truncated domain is exactly the adapter-mismatch this module "
                "refuses to risk" % (world_id, name)
            )

    cells: Tuple[Cell, ...] = tuple(sorted(
        (r, c)
        for r in range(spec.height)
        for c in range(spec.width)
        if not spec.is_wall((r, c))
    ))

    variables: List[str] = [cell_name(cell) for cell in cells]
    slots: List[Slot] = []
    for mechanism in world.mechanisms:
        base, length = world.slices[mechanism.name]
        kind = STATEFUL_KIND.get(mechanism.name)
        mine = tuple(e for e in world.entities_of[mechanism.name]
                     if kind is not None and e.kind == kind)
        if len(mine) != length:
            # `n_vars` is the world's own answer; disagreeing with it means this
            # module's model of the family has drifted from `worldgen`'s.  Loud,
            # because a silent disagreement is a wrong declared product.
            raise UnsupportedWorld(
                "%s: %s declares %d state slot(s) but this adapter finds %d "
                "%r entities -- the adapter's model of the family has drifted"
                % (world_id, mechanism.name, length, len(mine), kind)
            )
        for offset, entity in enumerate(mine):
            domain = _domain_of(entity.kind, entity)
            name = "%s_r%dc%d" % (entity.kind, entity.cell[0], entity.cell[1])
            onehot = len(domain) > 2
            if onehot:
                bits = tuple(len(variables) + i for i in range(len(domain)))
                variables.extend("%s_is%d" % (name, value) for value in domain)
            else:
                bits = (len(variables),)
                variables.append(name)
            slots.append(Slot(name=name, family=mechanism.name, kind=entity.kind,
                              cell=entity.cell, index=base + offset,
                              domain=domain, bits=bits, onehot=onehot))

    slots.sort(key=lambda s: s.index)
    total_vars = sum(length for _base, length in world.slices.values())
    if total_vars != len(slots):
        raise UnsupportedWorld(
            "%s: the world's state vector is %d long, the adapter declares %d "
            "slots" % (world_id, total_vars, len(slots))
        )

    return world, Layout(world_id=world_id, families=families, cells=cells,
                         slots=tuple(slots), variables=tuple(variables))


# ------------------------------------------------------------------- bad sets

@dataclass(frozen=True)
class BadSet:
    """The property IC3 is asked to prove, chosen so that proving it means something."""

    key: str
    statement: str
    separated_by: str                 # the mechanism family that does the separating
    cells: Tuple[Cell, ...]           # agent cells the set mentions
    predicate: Callable[[WorldState], bool] = field(compare=False,
                                                   default=lambda s: False)

    def as_json(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "statement": self.statement,
            "separated_by": self.separated_by,
            "cells": [list(cell) for cell in self.cells],
        }


def _only(entities: Sequence[Entity], kind: str, world_id: str) -> Entity:
    found = [e for e in entities if e.kind == kind]
    if len(found) != 1:
        raise UnsupportedWorld("%s: expected exactly one %r, found %d"
                               % (world_id, kind, len(found)))
    return found[0]


def _lock_bad(world: GridWorld, layout: Layout) -> BadSet:
    """*The agent stands on the lock with fewer than k tokens collected.*

    Unreachable because `walk_through_lock` is the only route onto the cell and
    it demands the count, and because the count is monotone -- so this is a
    statement about `count_lock`'s one-way frontier, not about geometry.  The
    lock cell itself *is* reachable (with the count met), which is what the gate
    checks and what distinguishes this from a walled-off pocket.
    """
    spec = world.spec
    lock = _only(spec.entities, "lock", spec.world_id)
    k = int(lock.prop("k", 1))
    tokens = layout.slots_of_kind("token")
    cell = lock.cell

    def predicate(state: WorldState) -> bool:
        if state.agent != cell:
            return False
        return sum(1 for slot in tokens if state.vars[slot.index]) < k

    return BadSet(
        key="agent-on-lock-below-count",
        statement="the agent stands on the lock at r%dc%d while fewer than %d of "
                  "the %d tokens are collected" % (cell[0], cell[1], k, len(tokens)),
        separated_by="count_lock",
        cells=(cell,),
        predicate=predicate,
    )


def _latch_bad(world: GridWorld, layout: Layout) -> BadSet:
    """*The agent stands on the goal cell with the latch still unset.*

    The only gap in the divider is a door on the latch's net and a latch never
    clears, so the conjunction cannot occur.  The goal cell is reachable (with
    the latch set), so the cut is the mechanism and not the wall.
    """
    spec = world.spec
    switches = [e for e in spec.entities
                if e.kind == "switch" and e.prop("mode", "toggle") == "latch"]
    if len(switches) != 1:
        raise UnsupportedWorld("%s: expected exactly one latch switch, found %d"
                               % (spec.world_id, len(switches)))
    slot = next(s for s in layout.slots if s.cell == switches[0].cell
                and s.kind == "switch")
    cell = spec.goal

    def predicate(state: WorldState) -> bool:
        return state.agent == cell and state.vars[slot.index] == 0

    return BadSet(
        key="agent-at-goal-latch-unset",
        statement="the agent stands on the goal at r%dc%d while the latch at "
                  "r%dc%d is still 0" % (cell[0], cell[1],
                                         switches[0].cell[0], switches[0].cell[1]),
        separated_by="switch_door",
        cells=(cell,),
        predicate=predicate,
    )


#: world id -> the bad-set builder.  Explicit rather than inferred: which
#: unreachable set is worth proving is a judgement, and a table is the honest
#: place to record a judgement.
BAD_SETS: Dict[str, Callable[[GridWorld, Layout], BadSet]] = {
    "t1-switch-latch": _latch_bad,
    "t1-tokens-lock": _lock_bad,
    "t2-cycler-lock": _lock_bad,
    "t2-lock-fragile": _lock_bad,
    "t3-cycler-portal-lock": _lock_bad,
    "t3-latch-maze": _lock_bad,
}


# -------------------------------------------------------------------- the system

@dataclass(frozen=True)
class WorldSystem(System):
    """`System`, plus everything the gate and the renderer need to stay honest.

    The extra fields are `compare=False` so that two systems built from the same
    world still compare on the data IC3 actually searches.
    """

    layout: Optional[Layout] = field(default=None, compare=False)
    world: Optional[GridWorld] = field(default=None, compare=False)
    bad_set: Optional[BadSet] = field(default=None, compare=False)

    def render_state(self, state: BoolState) -> str:
        """`r4c5|switch_r4c1=1` -- the world's own vocabulary, not 46 bits."""
        if self.layout is None:
            return System.render_state(self, state)
        try:
            decoded = self.layout.decode(state)
        except EncodingError:
            return System.render_state(self, state)
        parts = ["r%dc%d" % decoded.agent]
        parts.extend("%s=%d" % (slot.name, decoded.vars[slot.index])
                     for slot in self.layout.slots)
        return "|".join(parts)


def move_label(action: str, rule: str) -> str:
    """`DOWN:collect_token` -- the action and the ground-truth rule that fired.

    The rule tag rides in the label so the gate compares rules as well as
    successors, and so a counterexample renders as the world's own vocabulary.
    """
    return "%s:%s" % (action, rule)


def build_system(world_id: str) -> WorldSystem:
    """The declared subspace of `world_id`, as `engines.ic3_pdr` wants it.

    The relation is taken over the whole declared product, not the reachable
    part, for the reason `peg_system` gives: an inductive invariant has to be
    closed under moves from every state satisfying it, and restricting the
    relation to the reachable part makes the closure check quietly circular.
    """
    world, layout = build_layout(world_id)
    declared = layout.declared()

    states = tuple(sorted(layout.encode(state) for state in declared))
    transitions: Dict[BoolState, Tuple[Tuple[str, BoolState], ...]] = {}
    for state in declared:
        moves = []
        for action in ACTIONS:
            nxt, rule = world.explain(state, action)
            moves.append((move_label(action, rule), layout.encode(nxt)))
        transitions[layout.encode(state)] = tuple(sorted(moves))

    bad_set = BAD_SETS[world_id](world, layout)
    bad = tuple(sorted(layout.encode(state) for state in declared
                       if bad_set.predicate(state)))

    return WorldSystem(
        name=world_id,
        variables=layout.variables,
        states=states,
        init=(layout.encode(world.initial()),),
        bad=bad,
        transitions=transitions,
        layout=layout,
        world=world,
        bad_set=bad_set,
    )


# ----------------------------------------------------------------------- the gate

def transcription_mismatches(system: WorldSystem,
                             n: Optional[int] = None,
                             initial: Optional[str] = None,
                             goal_states: Optional[Sequence[str]] = None,
                             limit: int = 8) -> List[str]:
    """Is this `System` the world it claims to transcribe?  Re-derived, not trusted.

    Signature-compatible with `harness.transcription_mismatches` so the harness's
    own runner can call it in place of the peg one.  An empty list is the gate
    passing; anything else is verdict `adapter-mismatch`, which is escalated and
    never tabulated as a boundary.

    Nine checks, in the order a failure is cheapest to read:

    1. the bit-vector width matches the spec that crossed the process boundary;
    2. the declared state set is the declared product, deduplicated and sorted;
    3. `encode(decode(b)) == b` for every declared state -- the encoding is a
       bijection, so no two world states collide on one bit vector;
    4. every state of `GridWorld.reachable()` is inside the declared subspace;
    5. the initial state is `GridWorld.initial()`, and renders as the spec says;
    6. **edge for edge**: for every reachable state, the adapter's labelled
       successor list equals `GridWorld.transitions()`'s, both directions, rule
       tags included;
    7. the bad set is non-empty and renders as the spec says;
    8. the bad set is disjoint from the reachable set -- checked against
       `GridWorld.reachable()`, an oracle neither IC3 nor this module shares;
    9. every agent cell the bad set mentions is somewhere the agent *can* stand
       in some reachable state, so the separation is a mechanism and not a wall.

    **Scope, said out loud.**  Check 6 covers edges leaving *reachable* states,
    because `GridWorld.transitions()` is the independent oracle and it walks the
    reachable set.  Edges leaving the declared-but-unreachable remainder are not
    independently re-derived here: the adapter builds them with the same
    `GridWorld.explain` call the oracle would use, so comparing them would only
    confirm that a function equals itself.  They still matter -- the invariant
    has to be closed over the whole declared subspace -- and what backs them is
    checks 3 and 4, which say the remainder is well-formed and that the encoding
    is a bijection, plus `engines.ic3_pdr.check.verify`, which re-walks every
    declared state's successors from scratch.
    """
    problems: List[str] = []
    layout = system.layout
    world = system.world
    if layout is None or world is None:
        return ["the System carries no layout or world, so it cannot be checked "
                "against the world it claims to transcribe"]

    def note(text: str) -> bool:
        problems.append(text)
        return len(problems) >= limit

    # 1 --------------------------------------------------------------- width
    if n is not None and n != len(system.variables):
        note("variable count: the spec says %d, the System has %d"
             % (n, len(system.variables)))

    # 2 ------------------------------------------------------- declared product
    expected = layout.declared_product
    if len(system.states) != expected:
        note("declared state set: %d states, the declared product is %d"
             % (len(system.states), expected))
    if len(set(system.states)) != len(system.states):
        note("declared state set: %d states but only %d distinct -- the encoding "
             "is not injective" % (len(system.states), len(set(system.states))))
    if list(system.states) != sorted(system.states):
        note("declared state set is not sorted, so the artefact is not reproducible")

    # 3 ------------------------------------------------------------ round trip
    for state in system.states:
        try:
            if layout.encode(layout.decode(state)) != state:
                if note("round trip: %s does not encode back to itself"
                        % System.render_state(system, state)):
                    return problems[:limit]
                break
        except EncodingError as exc:
            if note("round trip: %s -- %s"
                    % (System.render_state(system, state), exc)):
                return problems[:limit]
            break

    # 4/6 ------------------------------------------------------ the real world
    reachable = world.reachable()
    declared = set(system.states)
    outside = []
    for state in reachable:
        try:
            encoded = layout.encode(state)
        except EncodingError as exc:
            outside.append(str(exc))
            continue
        if encoded not in declared:
            outside.append("reachable state %r is outside the declared subspace"
                           % (state.key(),))
    if outside:
        if note("reachable set is not contained in the declared subspace (%d "
                "state(s)): %s" % (len(outside), "; ".join(outside[:3]))):
            return problems[:limit]

    # 5 ---------------------------------------------------------------- init
    try:
        expected_init = layout.encode(world.initial())
    except EncodingError as exc:
        expected_init = None
        note("initial state does not encode: %s" % exc)
    if expected_init is not None and tuple(system.init) != (expected_init,):
        note("init: %r, GridWorld.initial() is %r"
             % ([system.render_state(s) for s in system.init],
                [system.render_state(expected_init)]))
    if initial is not None and system.init:
        rendered = system.render_state(system.init[0])
        if rendered != initial:
            note("init render: the spec carried %r, the System renders %r"
                 % (initial, rendered))

    # 6 ------------------------------------------------------- edge for edge
    if not outside:
        witnessed: Dict[BoolState, List[Tuple[str, BoolState]]] = {}
        for state, action, nxt, rule in world.transitions(reachable):
            witnessed.setdefault(layout.encode(state), []).append(
                (move_label(action, rule), layout.encode(nxt))
            )
        for encoded in sorted(witnessed):
            derived = list(system.moves(encoded))
            expected_moves = sorted(witnessed[encoded])
            if derived != expected_moves:
                render = system.render_state

                def show(moves):
                    return [(label, render(target)) for label, target in moves]

                if note("transitions from %s: the System has %r, GridWorld.explain "
                        "gives %r" % (render(encoded), show(derived),
                                      show(expected_moves))):
                    return problems[:limit]

    # 7/8/9 ---------------------------------------------------------- bad set
    if not system.bad:
        note("bad set is empty, so `goal_break` is vacuous and the row would "
             "measure nothing")
    if goal_states is not None:
        rendered_bad = sorted(system.render_state(s) for s in system.bad)
        if rendered_bad != sorted(goal_states):
            note("bad set: the spec carried %d state(s), the System has %d"
                 % (len(goal_states), len(system.bad)))

    reachable_bits = set()
    for state in reachable:
        try:
            reachable_bits.add(layout.encode(state))
        except EncodingError:
            pass
    overlap = [system.render_state(s) for s in system.bad if s in reachable_bits]
    if overlap:
        note("bad set is REACHABLE according to GridWorld.reachable() (%d state(s), "
             "e.g. %s) -- the property is false and the row would measure a "
             "breadth-first walk, not an invariant"
             % (len(overlap), ", ".join(overlap[:2])))

    standable = set(solvability.agent_cells(world))
    for cell in (system.bad_set.cells if system.bad_set else ()):
        if cell not in standable:
            note("bad set mentions r%dc%d, which the agent can never occupy in any "
                 "reachable state -- that is a wall separating it, not a mechanism, "
                 "and the invariant would be the trivial 'the agent is never there'"
                 % cell)

    return problems[:limit]


# --------------------------------------------------------------------- summary

def ground_truth(world_id: str) -> Dict[str, Any]:
    """`worldgen`'s own verdict on the world -- the anchor the adapter is checked against.

    `solvability.report` and `solvability.frontier` are computed by code neither
    IC3 nor this adapter shares, which is what makes them usable as evidence that
    a bad set is separated by a mechanism rather than by geometry: the frontier
    lists the cells adjacent to somewhere the agent can stand that it can never
    enter, and a bad set whose cells are *not* on it is not a walled-off pocket.
    """
    world, _layout = build_layout(world_id)
    report = solvability.report(world, diagnose=False)
    return {
        "solvable": report["solvable"],
        "reachable_states": report["reachable_states"],
        "agent_cells": report["agent_cells"],
        "optimal_length": report.get("optimal_length"),
        "separating_frontier": solvability.frontier(world),
    }


def summary(world_id: str) -> Dict[str, Any]:
    """Everything a parent process needs to build a spec, without the relation.

    Deliberately cheap: the transition relation costs |declared| x 4 calls into
    `GridWorld.explain` and the parent has no use for it -- the child builds its
    own.  What the parent does need is the shape of the row and the rendered
    initial and bad states, so that the spec crossing the process boundary can be
    checked against the System the child builds from it.
    """
    world, layout = build_layout(world_id)
    bad_set = BAD_SETS[world_id](world, layout)
    declared = layout.declared()
    system = WorldSystem(name=world_id, variables=layout.variables, states=(),
                         init=(), bad=(), transitions={}, layout=layout,
                         world=world, bad_set=bad_set)
    bad = [state for state in declared if bad_set.predicate(state)]
    return {
        "world_id": world_id,
        "families": list(layout.families),
        "n_families": len(layout.families),
        "n_floor_cells": len(layout.cells),
        "n_slots": len(layout.slots),
        "n_variables": layout.n_variables,
        "declared_product": layout.declared_product,
        "initial": system.render_state(layout.encode(world.initial())),
        "bad": bad_set.as_json(),
        "n_bad": len(bad),
        "bad_states": sorted(system.render_state(layout.encode(s)) for s in bad),
        "layout": layout.as_json(),
        "tier": world.spec.tier,
        "notes": world.spec.notes,
    }
