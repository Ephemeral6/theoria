"""Controlled variant pairs: one world, one rule-level edit, a new known truth.

The factory builds independent worlds.  An exam that asks *"the rules changed —
how fast did you notice, what did it cost to fix, what else did it invalidate"*
cannot use independent worlds: it needs the **same** world with **one** rule
moved, and it needs a machine-readable statement of what moved, because all
three of those quantities are measured against the edit rather than against the
world.  `exam/runs/…-V2-exam-on-worldgen/GAPS.md` is where that came from — three
of the exam's four question types are blocked on this file existing.

```bash
python -m worldgen.mutate                 # build every mutant + the descriptors
python -m worldgen.mutate --list          # the edit corpus, without building
python -m worldgen.mutate --knobs         # the declared semantic knobs
```

## The knob layer, and what was actually missing

GAPS.md diagnosed the blockage as "semantics live in mechanism classes'
`interact()` bodies; push distance is one cell because `mechanisms/push.py` says
so in code, not because a parameter says so."  That is exactly true of push and
mostly false of everything else: `switch.mode`, `door.polarity`, `lock.k`,
`cycler.open_phase`, `cycler.phase0`, `portal.mode` and `portal.dest` are all
read out of `Entity.props` at the decision point, every time.  What was missing
was not a parameterisation but a **declaration** of one — nothing said which
props are semantic knobs, what their domains are, or which mechanism reads them,
so nothing could enumerate the legal edits.

`KNOBS` below is that declaration, and `tests/test_mutate_knobs.py` refuses to
let it be prose: every declared knob has to demonstrably change the transition
function of a world that carries it.  A knob table nothing checks is a comment.

Exactly one knob is genuinely new — `flags["forbidden_action"]`, read by
`GridWorld.explain` before the grid is consulted — because forbidding a command
is the one edit in the item's list that no entity prop can express.  It is
absent from all twenty catalogue worlds, so their artefacts are byte-identical
either side of it.

## What a mutant ships, and where

`worldgen/out/worlds/<variant_id>/`, the same six files as any other world and
under the same read licence, because that is the only directory
`exam/papers/worldgen_port.py` knows how to open.  Mutants are **not** members
of `generate.CATALOGUE` — several are deliberately unsolvable and the catalogue
ships exactly one unsolvability certificate — but `build.py` builds them
alongside it and judges them with the same `gate_failures` and the same
byte-for-byte determinism check.

Four of the five gates apply verbatim; `solvability_intent_failures` reads
`spec.intended_solvable`, which a mutant leaves blank on purpose, so that one
check moved to `mutation_gate_failures` and reads `Edit.intended_solvable`
instead.  Two gates were added: the edit-family claim, and that moved
solvability claim.

**They are not rows in `INDEX.json`**, and that is a correction rather than a
preference.  `exam/guard.py` admits a generated id iff it is a row there, so
putting them in was the obvious move; it also breaks five tests in `exam/`,
which asserts the roster is exactly twenty and offers every row to a paper
builder that cannot build one on a three-state world.  Admission is `exam/`'s
decision, in `exam/`'s territory.  The mutants' roster is `MUTATIONS.json →
roster`, in `INDEX.json`'s exact shape.

**Ids are opaque and the spec tells no story — and that is less protection than
it sounds, so here is exactly how much.**  `variant_of`, `variant_delta`, `notes`
and `seed` are blank on a mutant even though every other world in the factory
fills them in, and the id is `v-<digest>` rather than a phrase, because W-1540
already shipped a leak of that shape: the ids `t2-unsolvable-nodoor` and
`t1-walk-maze` put *unsolvable* and *walk*, both live answers, in front of the
examinee.  `intended_solvable` is blank too — it is the answer to a verdict item
and `GridWorld` never reads it.

What that does **not** buy, because `exam/papers/worldgen_port.py` reconstructs
the world from `spec.json` and so the file has to be complete:

* `entities[].props` carries `mode`, `polarity`, `k`, `dest`, `open_phase` —
  most of the rule set, in words;
* the base's `spec.json` is open too, and a mutant is refused if it changes the
  layout, the start or the goal, so **the geometry identifies the base and a
  two-file diff is the edit, in plaintext.**

There is no version of `spec.json` that both hides that and lets `open_world()`
work. The protection here is against the *id* and the *labels* leaking, which
is what leaked before; it is not a claim that an examinee handed both specs
cannot read off the answer, and a paper that hands over both has not been given
one by this file. `MUTATIONS.json` — scoring-only — is where the linkage is
stated rather than merely inferable.

## The three quantities the exam grades on

**检测延迟 — exact.**  BFS over the *product* graph, pairs
`(state_base, state_mutant)` driven by the same action from the two initial
states, stopping at the first pair whose **rendered frames or win bits** differ.
The depth is the fewest actions any prober needs before the change is
observable at all; `0` means the very first frame gives it away.  Diverged pairs
are not expanded, so the search stays inside the synchronised region and the
number is a minimum over every strategy rather than over one walk.  `null` with
`complete: true` is the strong statement — **observationally equivalent on the
whole reachable graph** — and `exam.papers.adaptation.build()` refuses to ship a
paper in which no variant is undetectable, so the corpus has to contain one.
Per-stream latencies (the base world's own `raw_trace.jsonl`, the base world's
optimal plan) are reported alongside with their length and completeness, because
a stream that ended is not a change that never showed.

**连带作废 — exact, given a dependency graph that had to be built.**  Rules
falsified in both directions (the rule that used to govern the transition and
the one that governs it now — taking only the first misses the interesting
case); base invariants that fail on the mutant's reachable set; the solvability
verdict and whether it flipped.  `claims_to_reexamine` needs a claim→rule
dependency graph, which GAPS.md names as the missing artefact and which
`ground_truth.json` does not have.  `claim_dependencies` computes one — see that
function for what is measured and what is stated.

**修复成本 — partial, and it says so.**  The honest number needs a miner that can
represent mechanism state, which lives in `engine-rig` and does not exist yet
(GAPS.md: "a repair score against a miner that cannot represent the state is not
a measurement").  What ships is what this territory owns: how many observations
diverge, how many distinct rule-pair classes they fall into, and a greedy budget
— the walk length in the *mutated* world that witnesses every class at least
once.  `miner_measured` is emitted as `null` next to the name of its blocker
rather than omitted or approximated into looking like a measurement.
"""

import argparse
import hashlib
import json
import os
import shutil
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Set, Tuple

from .core import reversibility as rev, solvability, truth
from .core.explorer import shortest_paths
from .core.spec import Entity, WorldSpec, validate
from .core.trace import read_trace
from .core.types import ACTIONS, Cell, State
from .core.world import GridWorld
from .generate import BY_ID

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "worlds")

#: Cap on the synchronised product search.  Reached only if a mutant tracks its
#: base through a very large graph; recorded as `complete: false` rather than
#: silently returning "undetectable", which is the one wrong answer this search
#: can give.
PRODUCT_LIMIT = 200_000

EDIT_FAMILIES: Tuple[str, ...] = (
    "forbid_action",
    "change_guard",
    "reversible_to_irreversible",
    "move_portal_exit",
)


# ===================================================================== knobs

@dataclass(frozen=True)
class Knob:
    """One declared semantic parameter: what reads it, and what it may become.

    `reads` is a file reference rather than prose because the claim being made
    is falsifiable — the named line is where the mechanism branches on this
    value, and if it stops doing so the knob is dead and the test says so.
    """

    scope: str                 # "entity" or "world"
    kind: str                  # entity kind, or "" for a world-level knob
    prop: str
    mechanism: str
    domain: str                # human-readable; `values` when it is enumerable
    values: Tuple[Any, ...]
    governs: str               # what changing it changes, in one line
    reads: str
    #: Non-empty when no world in *this* catalogue can exercise the knob, with
    #: the reason.  An exemption rather than a hole: `tests/test_mutate.py`
    #: turns each one into its own assertion, so the reason is checked and not
    #: merely offered.  A knob that could be exercised and is not would be a
    #: knob nothing has ever demonstrated is read.
    unexercisable: str = ""

    def as_json(self) -> Dict[str, Any]:
        return {
            "scope": self.scope, "kind": self.kind, "prop": self.prop,
            "mechanism": self.mechanism, "domain": self.domain,
            "values": list(self.values), "governs": self.governs,
            "reads": self.reads, "unexercisable": self.unexercisable,
        }


KNOBS: Tuple[Knob, ...] = (
    Knob("entity", "switch", "mode", "switch_door",
         "toggle | latch", ("toggle", "latch"),
         "whether the bit can be cleared again, i.e. whether the mechanism is "
         "reversible at all",
         "worldgen/mechanisms/switch_door.py:132"),
    Knob("entity", "door", "polarity", "switch_door",
         "open_when_on | open_when_off", ("open_when_on", "open_when_off"),
         "the guard relating the door's passability to its net's aggregate bit",
         "worldgen/mechanisms/switch_door.py:91"),
    Knob("entity", "door", "net", "switch_door",
         "any label; a net with no switch on it is never on", (),
         "which switches drive this door",
         "worldgen/mechanisms/switch_door.py:89"),
    Knob("entity", "switch", "net", "switch_door",
         "any label", (),
         "which doors this switch drives",
         "worldgen/mechanisms/switch_door.py:84"),
    Knob("entity", "lock", "k", "count_lock",
         "1..(number of tokens in the world)", (),
         "the threshold guard: how many tokens must be collected before the "
         "lock is passable",
         "worldgen/mechanisms/count_lock.py:63"),
    Knob("entity", "cycler", "open_phase", "color_cycle",
         "0..k-1", (),
         "which phase of the cycle is the passable one",
         "worldgen/mechanisms/color_cycle.py:72"),
    Knob("entity", "cycler", "phase0", "color_cycle",
         "0..k-1", (),
         "the starting phase, hence `(open_phase - phase0) % k` — the number of "
         "advances available before the gate is open and the rule stops firing",
         "worldgen/mechanisms/color_cycle.py:76"),
    Knob("entity", "portal", "mode", "portal",
         "oneway | twoway | paired", ("oneway", "twoway", "paired"),
         "where the mouth delivers the agent, and whether the effect mentions "
         "the direction of travel",
         "worldgen/mechanisms/portal.py:98"),
    Knob("entity", "portal", "dest", "portal",
         "any floor cell", (),
         "the exit of a one-way portal",
         "worldgen/mechanisms/portal.py:101"),
    Knob("entity", "portal", "pair", "portal",
         "any label; exactly two mouths must carry each", (),
         "which mouth is the exit of which",
         "worldgen/mechanisms/portal.py:74",
         unexercisable="every catalogue world has exactly one pair, so the only "
                       "edit the validator admits is relabelling both mouths — "
                       "a gauge transformation that provably changes nothing. "
                       "Re-pairing needs a world with four mouths, which the "
                       "factory does not build. The exit of a paired portal is "
                       "moved here by `move_entity` on the partner mouth instead."),
    Knob("world", "", "forbidden_action", "-",
         "UP | DOWN | LEFT | RIGHT", ACTIONS,
         "one command the world refuses outright, before the grid is consulted",
         "worldgen/core/world.py:FORBIDDEN_RULE"),
)

#: The knobs whose edit is a *guard* change — a condition under which an
#: existing rule fires — as opposed to a change of destination or of
#: reversibility.  Used to check a mutation's declared `edit_family` against
#: what its operators actually touch.
GUARD_KNOBS: FrozenSet[Tuple[str, str]] = frozenset({
    ("door", "polarity"), ("door", "net"), ("switch", "net"),
    ("lock", "k"), ("cycler", "open_phase"), ("cycler", "phase0"),
})

PORTAL_EXIT_KNOBS: FrozenSet[Tuple[str, str]] = frozenset({
    ("portal", "dest"), ("portal", "pair"),
})


def knob_for(kind: str, prop: str) -> Optional[Knob]:
    for knob in KNOBS:
        if knob.kind == kind and knob.prop == prop:
            return knob
    return None


# ================================================================= operators

class MutationError(ValueError):
    """A mutation that does not describe a legal edit of its base."""


def _find_entity(spec: WorldSpec, kind: str, cell: Cell) -> int:
    for index, entity in enumerate(spec.entities):
        if entity.kind == kind and entity.cell == tuple(cell):
            return index
    raise MutationError("%s: no %s at %r" % (spec.world_id, kind, tuple(cell)))


def _apply_one(spec: WorldSpec, op: Dict[str, Any]) -> WorldSpec:
    """One operator, applied to a spec.  The base is never mutated in place.

    Every operator states the value it expects to find as well as the one it
    writes.  An edit whose `from` is stale is refused rather than applied: a
    silent no-op mutation would ship as a variant pair with an empty diff and
    every metric computed off it would read as "the change was undetectable",
    which is the one answer this corpus must never fabricate.
    """
    kind = op["op"]

    if kind == "forbid_action":
        action = op["action"]
        if action not in ACTIONS:
            raise MutationError("forbid_action %r is not an action" % action)
        if spec.flag("forbidden_action") is not None:
            raise MutationError("%s already forbids an action" % spec.world_id)
        flags = dict(spec.flags)
        flags["forbidden_action"] = action
        return _replace(spec, flags=tuple(sorted(flags.items())))

    if kind == "set_prop":
        index = _find_entity(spec, op["kind"], op["cell"])
        entity = spec.entities[index]
        prop = op["prop"]
        if knob_for(entity.kind, prop) is None:
            raise MutationError("%s.%s is not a declared knob (see KNOBS)"
                                % (entity.kind, prop))
        current = entity.prop(prop)
        if _norm(current) != _norm(op["from"]):
            raise MutationError(
                "%s: %s at %r has %s=%r, the operator expected %r"
                % (spec.world_id, entity.kind, entity.cell, prop, current,
                   op["from"]))
        if _norm(op["from"]) == _norm(op["to"]):
            raise MutationError(
                "%s: %s at %r would set %s=%r, which it already is — the "
                "docstring's no-op is refused here rather than described"
                % (spec.world_id, entity.kind, entity.cell, prop, op["to"]))
        props = {k: v for k, v in entity.props}
        if op["to"] is None:
            props.pop(prop, None)
        else:
            props[prop] = op["to"]
        entities = list(spec.entities)
        entities[index] = Entity.make(entity.kind, entity.cell, **props)
        return _replace(spec, entities=tuple(entities))

    if kind == "move_entity":
        index = _find_entity(spec, op["kind"], op["from"])
        entity = spec.entities[index]
        target = (int(op["to"][0]), int(op["to"][1]))
        if target == entity.cell:
            raise MutationError("%s: %s is already at %r"
                                % (spec.world_id, op["kind"], target))
        if entity.kind != "portal":
            # `set_prop` is checked against `KNOBS`; this was not, so it could
            # relocate a token or a block — a change of the picture, which is
            # what `Edit.spec`'s geometry guard exists to refuse and does not
            # cover because the layout is untouched.
            raise MutationError(
                "%s: move_entity is declared only for portal mouths, whose "
                "partner *is* the exit; moving a %s is a geometry edit"
                % (spec.world_id, entity.kind))
        entities = list(spec.entities)
        entities[index] = Entity(kind=entity.kind, cell=target, props=entity.props)
        return _replace(spec, entities=tuple(entities))

    raise MutationError("unknown operator %r" % kind)


def _norm(value: Any) -> Any:
    """Compare a prop value the way JSON round-tripping leaves it."""
    if isinstance(value, (list, tuple)):
        return tuple(_norm(v) for v in value)
    return value


def _replace(spec: WorldSpec, **changes: Any) -> WorldSpec:
    return WorldSpec(
        world_id=changes.get("world_id", spec.world_id),
        layout=changes.get("layout", spec.layout),
        agent_start=changes.get("agent_start", spec.agent_start),
        goal=changes.get("goal", spec.goal),
        entities=changes.get("entities", spec.entities),
        colors=changes.get("colors", spec.colors),
        families=changes.get("families", spec.families),
        flags=changes.get("flags", spec.flags),
        tier=changes.get("tier", spec.tier),
        seed=changes.get("seed", spec.seed),
        variant_of=changes.get("variant_of", spec.variant_of),
        variant_delta=changes.get("variant_delta", spec.variant_delta),
        notes=changes.get("notes", spec.notes),
        intended_solvable=changes.get("intended_solvable", spec.intended_solvable),
    )


# ================================================================== the corpus

@dataclass(frozen=True)
class Edit:
    """One declared mutation of one built world.

    `edit_family` is a claim, not a label: `check_family` compares it against
    what the operators touch and, for `reversible_to_irreversible`, against the
    *measured* reversibility stamp of the two worlds.  `intended_solvable` is a
    claim in exactly the sense `WorldSpec.intended_solvable` is, and the build
    gate that already checks it for the twenty checks it here too.

    `transparent_name` and `justification` are scoring-only.  They never reach a
    `spec.json`.
    """

    base: str
    edit_family: str
    operators: Tuple[Dict[str, Any], ...]
    transparent_name: str
    justification: str
    intended_solvable: Optional[bool] = None

    @property
    def variant_id(self) -> str:
        """An opaque handle.  Digest of the base and the operators, so it is
        stable under re-ordering of the corpus and carries no word from the
        answer alphabet — see the module docstring on W-1540's leak."""
        payload = json.dumps({"base": self.base, "operators": list(self.operators)},
                             sort_keys=True, separators=(",", ":"))
        return "v-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]

    def spec(self) -> WorldSpec:
        base = BY_ID[self.base]
        spec = base
        for op in self.operators:
            spec = _apply_one(spec, op)
        spec = _replace(
            spec,
            world_id=self.variant_id,
            # Blank on purpose.  `spec.json` is an open file; a `variant_delta`
            # reading "the switch is now a latch" is the answer to the item.
            variant_of=None, variant_delta="", notes="",
            # And `None` on purpose.  `intended_solvable` is a designer's label
            # with no functional role — `GridWorld` never reads it — and it is
            # the literal answer to a verdict item, sitting in an open file.  So
            # the claim does not travel in the spec: it lives in
            # `Edit.intended_solvable` and is checked by `mutation_gate_failures`
            # against the exhaustive decision, which is the same check
            # `build.py`'s `solvability_intent_failures` gate makes for the
            # twenty, with the answer moved out of the examinee's reach.
            intended_solvable=None,
            # Cleared for the same reason and it was not, in the first draft:
            # `seed` is copied verbatim from the base by every other field's
            # default, it has no meaning for a mutant (nothing here is random),
            # and it is **unique across the twenty**, so matching it against the
            # open catalogue specs identified the base of all fifteen mutants
            # exactly. Found by an adversarial review, not by me.
            seed=0,
        )
        validate(spec)
        if spec.colors != base.colors:
            # A palette shift would make every frame differ for a reason that has
            # nothing to do with the rule, and the detection latency measured off
            # it would be 0 for every such mutant — a number about the generator,
            # not about the edit.
            raise MutationError(
                "%s: the edit changes the palette (%r -> %r); a controlled pair "
                "must keep the legend fixed" % (self.variant_id, base.colors,
                                                spec.colors))
        if spec.layout != base.layout or spec.agent_start != base.agent_start \
                or spec.goal != base.goal:
            raise MutationError("%s: the edit changes the geometry, not a rule"
                                % self.variant_id)
        return spec


#: The corpus.  Four families, at least two instances each, and the instances
#: are chosen for spread on the quantity the exam grades: three visible in the
#: first frame, one that cannot be seen at all, the rest between 1 and 8 actions,
#: and four that flip the solvability verdict — one to solvable and three to
#: unsolvable.  Every number in that sentence is `MUTATIONS.json → totals`, not
#: a design intention; where the two came apart, the intention lost and the
#: `justification` says so.
MUTATIONS: Tuple[Edit, ...] = (
    # ------------------------------------------------------- forbid_action
    Edit(
        base="t1-walk-maze", edit_family="forbid_action",
        operators=({"op": "forbid_action", "action": "UP"},),
        transparent_name="t1-walk-maze::forbid(UP)",
        justification="The control world, so the edit is isolated from every "
                      "mechanism: nothing but movement exists here, and the "
                      "maze's only route to the goal descends. Refusing UP "
                      "cannot be seen until the agent stands somewhere UP would "
                      "have moved it, which is not the start cell.",
        intended_solvable=True),
    Edit(
        base="t1-walk-maze", edit_family="forbid_action",
        operators=({"op": "forbid_action", "action": "DOWN"},),
        transparent_name="t1-walk-maze::forbid(DOWN)",
        justification="The same board and the same family as the edit above, "
                      "one action along, and the verdict flips: the goal sits "
                      "on the bottom row and every route to it descends, so "
                      "refusing DOWN makes the world unwinnable. Two mutants of "
                      "one base whose boards are indistinguishable and whose "
                      "answers are opposite — GAPS.md asks for exactly this "
                      "shape, so that board identity carries no signal.",
        intended_solvable=False),
    Edit(
        base="t1-cycler-gate", edit_family="forbid_action",
        operators=({"op": "forbid_action", "action": "UP"},),
        transparent_name="t1-cycler-gate::forbid(UP)",
        justification="An open room: the goal sits below and right of the "
                      "start, so UP is never on a shortest path and the "
                      "optimal length is 5 either way. `costs nothing` would be "
                      "the wrong summary and a draft used it — the same "
                      "descriptor records the corpus's largest `divergent_share` "
                      "(0.25), the reachable set falling 58 → 41, and a "
                      "divergence class that exists in the base and can never "
                      "be witnessed in the mutant at all. An edit can leave the "
                      "objective untouched and still be most of what there is "
                      "to learn about the world.",
        intended_solvable=True),

    # -------------------------------------------------------- change_guard
    Edit(
        base="t2-unsolvable-nodoor", edit_family="change_guard",
        operators=({"op": "set_prop", "kind": "door", "cell": (3, 4),
                    "prop": "polarity", "from": "open_when_on",
                    "to": "open_when_off"},
                   {"op": "set_prop", "kind": "door", "cell": (4, 2),
                    "prop": "polarity", "from": "open_when_on",
                    "to": "open_when_off"}),
        transparent_name="t2-unsolvable-nodoor::door.polarity=open_when_off",
        justification="The same guard inverted on both of the world's doors — "
                      "two operators, because the world has two doors and "
                      "inverting one would leave a pair that differ in a rule "
                      "nobody edited. On a net that has no switch on it: "
                      "The net is off forever, so the doors that never opened "
                      "are now never shut, and the world whose entire purpose "
                      "was to ship an unsolvability certificate becomes "
                      "solvable. Visible in the first frame — the doors are "
                      "simply absent — which is the low end of the detection "
                      "range.",
        intended_solvable=True),
    Edit(
        base="t1-tokens-lock", edit_family="change_guard",
        operators=({"op": "set_prop", "kind": "lock", "cell": (3, 4),
                    "prop": "k", "from": 3, "to": 2},),
        transparent_name="t1-tokens-lock::lock.k=2",
        justification="The threshold guard, moved by one. What gives it away is "
                      "not bumping the lock but the lock **disappearing**: a "
                      "lock is drawn while it is shut and not drawn once the "
                      "count reaches k, so at the second token the two worlds' "
                      "frames differ from across the board — measured "
                      "`earliest_actions: 4`, on a straight walk that never "
                      "goes near the lock's row. (An earlier version of this "
                      "sentence claimed the opposite, that the edit stayed "
                      "invisible until the agent stood next to the lock; an "
                      "adversarial review replayed the witness and refuted it. "
                      "The variant is still worth carrying — it is a guard "
                      "whose value no frame states — but it is not the "
                      "late-detection instance it was chosen to be.)",
        intended_solvable=True),
    Edit(
        base="t3-cycler-portal-lock", edit_family="change_guard",
        operators=({"op": "set_prop", "kind": "cycler", "cell": (3, 2),
                    "prop": "open_phase", "from": 1, "to": 2},),
        transparent_name="t3-cycler-portal-lock::cycler.open_phase=2",
        justification="Which colour is the passable one, moved one step round "
                      "the cycle. The gate now needs two bumps instead of one, "
                      "so the colour a reader learned to walk into is the "
                      "colour that now refuses — a guard change that inverts a "
                      "learned association rather than deleting it.",
        intended_solvable=True),
    Edit(
        base="t1-switch-toggle", edit_family="change_guard",
        operators=({"op": "set_prop", "kind": "door", "cell": (3, 4),
                    "prop": "net", "from": "a", "to": "b"},),
        transparent_name="t1-switch-toggle::door(3,4).net=b",
        justification="The guard that says *which* switch a door answers to. "
                      "The door in the divider now listens to a net no switch "
                      "drives, so it never opens and the world is unwinnable — "
                      "while the second door, still on net `a`, keeps opening "
                      "and shutting exactly as before. Nothing in any frame "
                      "distinguishes the two boards until the switch is thrown, "
                      "which is what makes this the solvable/unsolvable "
                      "near-twin a verdict paper needs.",
        intended_solvable=False),
    Edit(
        base="t1-switch-latch", edit_family="change_guard",
        operators=({"op": "set_prop", "kind": "door", "cell": (3, 4),
                    "prop": "net", "from": "a", "to": "b"},),
        transparent_name="t1-switch-latch::door(3,4).net=b",
        justification="The same guard edit on the latch half of the catalogue's "
                      "existing variant pair, so the corpus carries the "
                      "unsolvable twin of both switch worlds and an examinee "
                      "cannot infer the verdict from the switch's mode.",
        intended_solvable=False),
    Edit(
        base="t2-switch-push", edit_family="change_guard",
        operators=({"op": "set_prop", "kind": "switch", "cell": (5, 1),
                    "prop": "net", "from": "a", "to": "b"},
                   {"op": "set_prop", "kind": "door", "cell": (3, 4),
                    "prop": "net", "from": "a", "to": "b"}),
        transparent_name="t2-switch-push::net a->b (relabel, both ends)",
        justification="A net is a label and both ends of it moved. State it "
                      "precisely, because a draft of this sentence said 'the "
                      "rule table genuinely changed' and `truth.rule_table` "
                      "returns byte-identical tables for the two: what changed "
                      "is the **world description** — which label the guard "
                      "`door_mirrors_net` reads — and nothing else, not the "
                      "table, not the transition function, not any frame. "
                      "`net` is a real knob and `v-707a64ad` proves it by "
                      "moving one end of the same one and making a world "
                      "unwinnable; this is the one edit of it with no "
                      "observable content. That is what an undetectable "
                      "variant has to be. A paper with none of them rewards "
                      "claiming a detection, and an examinee reporting a "
                      "latency for a change it cannot have observed would score "
                      "like one that measured — which is the constraint "
                      "`exam.papers.adaptation.build()` enforces on the A0 "
                      "paper, met here in advance rather than discovered when "
                      "somebody writes the worldgen one.",
        intended_solvable=True),

    # ------------------------------------------ reversible_to_irreversible
    Edit(
        base="t2-switch-push", edit_family="reversible_to_irreversible",
        operators=({"op": "set_prop", "kind": "switch", "cell": (5, 1),
                    "prop": "mode", "from": "toggle", "to": "latch"},),
        transparent_name="t2-switch-push::switch.mode=latch",
        justification="A0′'s central comparison, applied to a world that also "
                      "contains a block: the switch sets once and never "
                      "clears, so `toggle_switch` is replaced by a rule with "
                      "exactly one witness in the life of the world.",
        intended_solvable=True),
    Edit(
        base="t3-full-house", edit_family="reversible_to_irreversible",
        operators=({"op": "set_prop", "kind": "switch", "cell": (6, 1),
                    "prop": "mode", "from": "toggle", "to": "latch"},),
        transparent_name="t3-full-house::switch.mode=latch",
        justification="The same edit inside three interacting families and the "
                      "largest world in the catalogue, 2654 states. What it "
                      "buys over `v-efe43df1` is **detection latency, not "
                      "collateral**: the two have identical collateral blocks "
                      "(same three rules falsified, same claim added, same "
                      "single claim to re-examine, and the reachable set does "
                      "not shrink — nothing becomes unreachable when the door "
                      "stops re-shutting), while the earliest witness is 8 "
                      "actions against 5, the longest in the corpus. A draft of "
                      "this said 'every claim about reaching cells behind it "
                      "changes with it'; the descriptor says one claim does.",
        intended_solvable=True),
    Edit(
        base="t1-cycler-gate", edit_family="reversible_to_irreversible",
        operators=({"op": "set_prop", "kind": "cycler", "cell": (2, 4),
                    "prop": "phase0", "from": None, "to": 1},),
        transparent_name="t1-cycler-gate::cycler.phase0=1",
        justification="`mechanisms/color_cycle.py` names this configuration in "
                      "advance: a cycler starting one step short of its open "
                      "phase fires `advance_cycler` once and never again, "
                      "because passing through does not advance the phase. The "
                      "group is still of order k and destroys nothing, and the "
                      "rule still becomes single-witness — the two axes coming "
                      "apart, produced deliberately. Note what the descriptor "
                      "measures and this sentence must not overstate: the "
                      "transition function is **unchanged**. Nothing is "
                      "falsified and there is nothing to repair; what moved is "
                      "where the world starts, and the consequence is that a "
                      "trajectory can no longer obtain the second witness. "
                      "`changes.transition_function` is false here and true for "
                      "the other two in this family, which is the distinction "
                      "an adaptation item has to keep.",
        intended_solvable=True),

    # ---------------------------------------------------- move_portal_exit
    Edit(
        base="t1-portal-oneway", edit_family="move_portal_exit",
        operators=({"op": "set_prop", "kind": "portal", "cell": (5, 1),
                    "prop": "dest", "from": (3, 3), "to": (3, 5)},),
        transparent_name="t1-portal-oneway::portal.dest=(3,5)",
        justification="The exit moved two cells inside the same pocket. A "
                      "one-way portal's destination is unmarked floor, so no "
                      "frame anywhere in the world differs until the mouth is "
                      "entered, and the whole detection latency is the walk to "
                      "the mouth. Nothing about the edit is visible before that "
                      "and everything about it is visible at that step.",
        intended_solvable=True),
    Edit(
        base="t1-portal-oneway", edit_family="move_portal_exit",
        operators=({"op": "set_prop", "kind": "portal", "cell": (5, 1),
                    "prop": "dest", "from": (3, 3), "to": (6, 2)},),
        transparent_name="t1-portal-oneway::portal.dest=(6,2)",
        justification="The exit moved out of the pocket and next to the mouth, "
                      "so the teleport becomes a one-cell hop. It was chosen to "
                      "isolate *how far* the exit moved from *whether* it "
                      "moved, and on the published numbers **it does not**: "
                      "this variant and the one above agree on every field — "
                      "earliest_actions 4, one rule falsified, 2 divergent "
                      "observations, budget 4, 26 reachable states, optimal "
                      "length 10. The latency is the walk to the mouth and the "
                      "walk is the same. The two differ only in *where the "
                      "agent lands*, which is in `divergence_examples` and in "
                      "nothing the descriptor summarises. Kept, because a pair "
                      "that is identical on the summary and different in the "
                      "witness is itself a thing a scoring pass should not "
                      "confuse; not kept as the contrast it was meant to be.",
        intended_solvable=True),
    Edit(
        base="t2-portal-pair", edit_family="move_portal_exit",
        operators=({"op": "move_entity", "kind": "portal",
                    "from": (4, 7), "to": (5, 5)},),
        transparent_name="t2-portal-pair::mouth(4,7)->(5,5)",
        justification="The other kind of exit move: for a two-way pair the "
                      "exit *is* the partner mouth, and a mouth is drawn. This "
                      "one gives itself away in the first frame, which is what "
                      "makes it the control against the two invisible ones "
                      "above — same family, opposite end of the detection range.",
        intended_solvable=True),
)

MUTANT_BY_ID: Dict[str, Edit] = {e.variant_id: e for e in MUTATIONS}


def mutant_specs() -> List[WorldSpec]:
    """Every mutant, in digest order.

    Digest order rather than corpus order so that the roster does not group the
    families, which would tell a reader which four ids share an edit kind.
    """
    return [e.spec() for e in sorted(MUTATIONS, key=lambda e: e.variant_id)]


def spec_for(world_id: str) -> WorldSpec:
    """A catalogue world or a mutant, by id.  The lookup downstream tools want."""
    if world_id in BY_ID:
        return BY_ID[world_id]
    if world_id in MUTANT_BY_ID:
        return MUTANT_BY_ID[world_id].spec()
    raise KeyError("no world or mutant %r" % world_id)


# ============================================================ the measurements

def _frame_key(world: GridWorld, state: State) -> Tuple[Any, bool]:
    """What an observer of this world sees at this state, and nothing else.

    The win bit is part of it: `raw_trace.jsonl` carries `win` alongside the
    frame and `cold-start-a0`'s reader sees both, so a change that only moves
    the goal condition is still observable and must not read as latent.
    """
    return (tuple(tuple(row) for row in world.render(state)), world.is_win(state))


def earliest_detection(base: GridWorld, mutant: GridWorld,
                       limit: int = PRODUCT_LIMIT) -> Dict[str, Any]:
    """Fewest actions before the edit is observable, over every strategy.

    BFS over pairs `(state_base, state_mutant)` reached by the same action
    sequence from the two initial states.  A pair whose observations differ is
    the answer and is not expanded, so the search stays inside the region where
    the two worlds still agree — which is why this terminates quickly even when
    the mutant's own reachable set is large.

    `0` means the initial frames already differ.  `None` with `complete: True`
    means no action sequence at all distinguishes the two worlds.
    """
    start = (base.initial(), mutant.initial())
    if _frame_key(base, start[0]) != _frame_key(mutant, start[1]):
        return {"actions": 0, "witness": [], "complete": True,
                "pairs_explored": 1, "base_rule": None, "mutant_rule": None}

    seen: Set[Tuple[Any, Any]] = {(start[0].key(), start[1].key())}
    queue: deque = deque([(start[0], start[1], ())])
    explored = 0
    while queue:
        sb, sm, path = queue.popleft()
        explored += 1
        for action in ACTIONS:
            nb, rule_b = base.explain(sb, action)
            nm, rule_m = mutant.explain(sm, action)
            if _frame_key(base, nb) != _frame_key(mutant, nm):
                return {"actions": len(path) + 1,
                        "witness": list(path) + [action],
                        "complete": True, "pairs_explored": explored,
                        "base_rule": rule_b, "mutant_rule": rule_m}
            key = (nb.key(), nm.key())
            if key in seen:
                continue
            if len(seen) >= limit:
                return {"actions": None, "witness": None, "complete": False,
                        "pairs_explored": explored, "base_rule": None,
                        "mutant_rule": None,
                        "note": "product search hit the %d-pair cap; "
                                "`actions: null` here means *not found*, not "
                                "*does not exist*" % limit}
            seen.add(key)
            queue.append((nb, nm, path + (action,)))
    return {"actions": None, "witness": None, "complete": True,
            "pairs_explored": explored, "base_rule": None, "mutant_rule": None,
            "note": "observationally equivalent: no action sequence "
                    "distinguishes the two worlds"}


def stream_divergence(base: GridWorld, mutant: GridWorld,
                      actions: Sequence[Optional[str]]) -> Dict[str, Any]:
    """Where a *given* action stream first shows the difference.

    1-based, matching `exam/grading/rubrics_adaptation.py`'s detection index.
    `index: null` alongside `n_actions` and `complete`, because a stream that
    ran out is not the same fact as a change that cannot be seen, and the two
    have been confused before (`exam/DECISIONS.md` D-EX-014).
    """
    sb, sm = base.initial(), mutant.initial()
    if _frame_key(base, sb) != _frame_key(mutant, sm):
        return {"index": 0, "n_actions": 0, "complete": True,
                "note": "the initial frame already differs"}
    live = [a for a in actions if a is not None]
    for i, action in enumerate(live):
        sb = base.step(sb, action)
        sm = mutant.step(sm, action)
        if _frame_key(base, sb) != _frame_key(mutant, sm):
            return {"index": i + 1, "n_actions": len(live), "complete": True}
    return {"index": None, "n_actions": len(live), "complete": False,
            "note": "the stream ended without showing the difference; this is "
                    "a fact about the stream, not about the edit"}


def one_step_divergence(base: GridWorld, mutant: GridWorld,
                        states: Sequence[State]) -> Dict[str, Any]:
    """Every `(state, action)` on which the two worlds disagree, from one side.

    Both rule tags are kept per disagreement — the rule that used to govern the
    transition and the one that governs it now.  Taking only the first is the
    mistake `exam/papers/adaptation.py:261-283` documents: it misses the case
    where a new rule captures a transition an old rule used to own, which is
    precisely the interesting one.
    """
    pairs: Dict[Tuple[str, str], int] = {}
    sites: List[Dict[str, Any]] = []
    agree = 0
    for state in states:
        for action in ACTIONS:
            nb, rule_b = base.explain(state, action)
            nm, rule_m = mutant.explain(state, action)
            if nb == nm and rule_b == rule_m:
                agree += 1
                continue
            pairs[(rule_b, rule_m)] = pairs.get((rule_b, rule_m), 0) + 1
            if len(sites) < 6:
                sites.append({"agent": list(state.agent), "vars": list(state.vars),
                              "action": action, "base_rule": rule_b,
                              "mutant_rule": rule_m,
                              "same_successor": nb == nm})
    return {
        "observations": sum(pairs.values()),
        "agreeing_observations": agree,
        "rule_pairs": [{"base_rule": b, "mutant_rule": m, "count": n}
                       for (b, m), n in sorted(pairs.items())],
        "examples": sites,
    }


def greedy_witness_budget(base: GridWorld, mutant: GridWorld) -> Dict[str, Any]:
    """The walk length, *in the mutant*, that witnesses every divergent class.

    An arm that has to repair its theory lives in the mutated world, so the
    budget is spent there.  Greedy nearest-uncovered, the same loop
    `core/explorer.py` uses, which makes this an **upper** bound on the optimal
    budget; it is a *lower* bound on what a miner needs, since a miner also has
    to separate the new rule from its neighbours after witnessing it.  Both
    directions are stated because a one-sided bound reads as an estimate.

    A class that is reachable in the base and not in the mutant is reported
    rather than dropped: those are the changes that can only be inferred from
    an absence, and they are the expensive ones.

    **The walk can also stall**, and that is not the same thing. `v-eb4c5810`
    forbids `UP` in a world whose cycler phase is absorbing at `open_phase`, so
    two of its classes are individually witnessable and **jointly unreachable**:
    once the agent has bumped the gate open it can never descend to a shut
    phase again, and it can never go back up. An earlier version broke out of
    the loop and reported the truncated count as "the walk that witnesses every
    class" and as an upper bound on the optimal — a finite number that bounded
    nothing. A stall now empties `greedy_actions` and names what was left, so
    the field cannot be read as a budget when no budget exists.
    """
    classes: Dict[Tuple[str, str], List[Tuple[Any, str]]] = {}
    # Both reachable sets, not just the base's. `rules_falsified` already unions
    # them, and enumerating only the base's left `classes_total` contradicting
    # `rule_pairs_backward` in the same record — while missing precisely the
    # classes that live in the world a repairing arm actually stands in.
    surveyed = {s.key(): s for s in base.reachable()}
    surveyed.update({s.key(): s for s in mutant.reachable()})
    for _key, state in sorted(surveyed.items()):
        for action in ACTIONS:
            nb, rule_b = base.explain(state, action)
            nm, rule_m = mutant.explain(state, action)
            if nb == nm and rule_b == rule_m:
                continue
            classes.setdefault((rule_b, rule_m), []).append((state.key(), action))

    reachable_in_mutant = {s.key() for s in mutant.reachable()}
    wanted: Dict[Tuple[str, str], Set[Tuple[Any, str]]] = {}
    orphans: List[Dict[str, Any]] = []
    for key, sites in sorted(classes.items()):
        live = {s for s in sites if s[0] in reachable_in_mutant}
        if live:
            wanted[key] = live
        else:
            orphans.append({"base_rule": key[0], "mutant_rule": key[1],
                            "sites_in_base": len(sites)})

    state = mutant.initial()
    spent = 0
    stalled: List[Dict[str, Any]] = []
    while wanted:
        paths = shortest_paths(mutant, state)
        pool = [(len(paths[key]), key, action, cls)
                for cls, sites in wanted.items()
                for key, action in sorted(sites) if key in paths]
        if not pool:
            stalled = [{"base_rule": b, "mutant_rule": m}
                       for b, m in sorted(wanted)]
            break
        _cost, key, action, cls = min(pool)
        spent += len(paths[key]) + 1
        for step_action in paths[key]:
            state = mutant.step(state, step_action)
        state = mutant.step(state, action)
        wanted.pop(cls, None)

    return {
        # `None`, not the truncated count. A stalled walk has no budget and the
        # field must not offer a number that reads like one.
        "greedy_actions": None if stalled else spent,
        "greedy_actions_before_stall": spent if stalled else None,
        "stalled_on": stalled,
        "classes_total": len(classes),
        "classes_witnessable_in_mutant": len(classes) - len(orphans),
        "classes_only_in_base": orphans,
        "bound": ("no single walk witnesses every class in this world; "
                  "`greedy_actions_before_stall` is what the greedy walk spent "
                  "before it ran out of reachable sites, and bounds nothing"
                  if stalled else
                  "upper bound on the optimal witness budget (greedy); lower "
                  "bound on a miner's repair budget (witnessing is not "
                  "separating)"),
    }


# --------------------------------------------------- claim → rule dependencies

def _invariant_owners(world: GridWorld) -> Dict[str, str]:
    """Which mechanism declared each invariant.  `"world"` for the two in
    `core/truth.py` that belong to `GridWorld` rather than to any family.

    Raises on a name collision rather than resolving one. Attribution decides
    which rules a claim depends on, so a mechanism that shadowed a name would
    silently take over another's claim — and a mechanism shadowing
    `agent_unique` would take a world-level claim and gain the agent-brush edge
    with it. No collision exists across the twenty today; this is here so that
    the day one does, it is a stop rather than a quietly wrong graph.
    """
    owners: Dict[str, str] = {}
    for row in truth.invariant_table(world):
        owners.setdefault(row["name"], "world")
    for mechanism in world.mechanisms:
        for row in mechanism.invariants(world.spec, world.mine(mechanism)):
            previous = owners.get(row["name"])
            if previous not in (None, "world", mechanism.name):
                raise MutationError(
                    "%s: invariant %r is declared by both %s and %s; claim "
                    "attribution would be arbitrary"
                    % (world.spec.world_id, row["name"], previous, mechanism.name))
            owners[row["name"]] = mechanism.name
    return owners


def claim_dependencies(world: GridWorld) -> Dict[str, Any]:
    """Which rules each claim rests on — the graph `ground_truth.json` lacks.

    `exam/papers/adaptation.py` grades `claims_to_reexamine` through
    `adapt.dependent_theorems(dsl, rule)`, which reads `[depends: push2]`
    annotations a human wrote into A0's manual.  Nothing generated has such
    annotations, and GAPS.md names their absence as 41.7 % of the adaptation
    paper. This computes them instead of asking for them.

    Three edges, and the difference between them is the difference between
    measured and stated:

    * **measured — slice writes.** For each rule, the set of mechanisms whose
      slice of the state vector some firing of that rule changes, read off the
      reachable graph by diffing `State.vars` across the transition. An
      invariant declared by mechanism *M* depends on every rule that writes into
      *M*'s slice. Nothing is asserted here; the numbers come from the same
      `explain` that produces the states;
    * **structural — same declarer.** A claim depends on every rule its own
      mechanism declares. This edge is not decoration and its absence was a
      live defect in the first cut of this function: a **door holds no state**,
      so no rule anywhere writes `switch_door`'s slice on account of one, and
      `door_presence_tracks_net` — an invariant entirely about doors — came back
      depending on nothing that a door edit could falsify. Slice writes alone
      see the mechanisms that store something and are blind to the ones that are
      a *function* of what others store, which is half this library;
    * **stated — the agent's brush.** The agent is painted last and wins every
      overlap (`core/world.py:render`), so a rule that moves the agent can flip
      any claim that reads a frame. Every mechanism-declared invariant in this
      library reads one, and the two world-level invariants (`agent_unique`,
      `grid_shape`) count the agent itself and the grid's shape, which no rule
      can change. So mechanism-owned claims take an edge from every
      agent-moving rule and the two world-level ones do not.

    The graph is therefore an **over-approximation**, deliberately: its consumer
    is "which claims must be re-examined", and a spurious edge costs a reader
    one check while a missing one costs a wrong answer.
    """
    states = world.reachable()
    slices = world.slices
    writes: Dict[str, Set[str]] = {}
    moves: Dict[str, bool] = {}
    for state in states:
        for action in ACTIONS:
            nxt, rule = world.explain(state, action)
            moves[rule] = moves.get(rule, False) or (nxt.agent != state.agent)
            touched = writes.setdefault(rule, set())
            if nxt.vars == state.vars:
                continue
            for name, (base, length) in slices.items():
                if nxt.vars[base:base + length] != state.vars[base:base + length]:
                    touched.add(name)

    declared_by: Dict[str, Set[str]] = {"world": {r["name"] for r in
                                                  truth.base_rules(world)}}
    for mechanism in world.mechanisms:
        declared_by[mechanism.name] = {
            r["name"] for r in mechanism.truth_rules(world.spec,
                                                     world.mine(mechanism))}

    owners = _invariant_owners(world)
    depends: Dict[str, List[str]] = {}
    for claim, owner in sorted(owners.items()):
        edges = {rule for rule, names in writes.items() if owner in names}
        edges |= declared_by.get(owner, set())
        if owner != "world":
            edges |= {rule for rule, moved in moves.items() if moved}
        depends[claim] = sorted(edges)

    return {
        "claims": depends,
        "claim_owner": dict(sorted(owners.items())),
        "rules_declared_by": {m: sorted(v) for m, v in sorted(declared_by.items())},
        "rule_writes_slice_of": {r: sorted(v) for r, v in sorted(writes.items())},
        "rule_moves_agent": dict(sorted(moves.items())),
        "method": "slice writes measured on the reachable graph; the "
                  "same-declarer edge structural; the agent-brush edge stated "
                  "(see claim_dependencies.__doc__). Over-approximating on "
                  "purpose — a spurious edge costs a reader one check, a "
                  "missing one costs a wrong answer.",
    }


# ================================================================ the descriptor

def _stamp(world: GridWorld) -> Dict[str, Any]:
    return rev.audit(world, truth.rule_table(world))


def check_family(edit: Edit, base: GridWorld, mutant: GridWorld,
                 base_stamp: Dict[str, Any],
                 mutant_stamp: Dict[str, Any]) -> List[str]:
    """Is the declared `edit_family` what the operators and the numbers say?

    The same discipline `intended_solvable` is under, and for the same reason:
    the first cut of the catalogue measured solvability, printed it, and shipped
    the opposite label. A family label nothing compares against measurement is a
    caption.
    """
    problems: List[str] = []
    if edit.edit_family not in EDIT_FAMILIES:
        return ["%r is not one of %s" % (edit.edit_family, ", ".join(EDIT_FAMILIES))]

    ops = edit.operators
    touched = {(op.get("kind", ""), op.get("prop", "")) for op in ops
               if op["op"] == "set_prop"}

    if edit.edit_family == "forbid_action":
        if not all(op["op"] == "forbid_action" for op in ops):
            problems.append("declared forbid_action but an operator is not one")
    elif edit.edit_family == "move_portal_exit":
        moves_mouth = any(op["op"] == "move_entity" and op.get("kind") == "portal"
                          for op in ops)
        if not (touched & PORTAL_EXIT_KNOBS) and not moves_mouth:
            problems.append("declared move_portal_exit but no operator touches a "
                            "portal's exit (dest, pair, or the partner mouth)")
    elif edit.edit_family == "change_guard":
        if not touched or not touched <= GUARD_KNOBS:
            problems.append("declared change_guard but the operators touch %r, "
                            "which is not a subset of the guard knobs" % sorted(touched))
    elif edit.edit_family == "reversible_to_irreversible":
        # A rule that survives into the mutant and stops being re-witnessable.
        # The `.get(name, {"re_witnessable": False})` this used to be counted a
        # rule that merely **stopped existing** as one that lost
        # re-witnessability, which let a guard change wear the label:
        # `v-57cfb2b4` opens two doors permanently, `blocked_by_door` never
        # fires again, and nothing about reversibility moved. A rule that is
        # gone is gone; it is `rules_falsified`'s business, not this one's.
        lost = sorted(
            name for name, row in base_stamp["rules"].items()
            if row["re_witnessable"] and name in mutant_stamp["rules"]
            and not mutant_stamp["rules"][name]["re_witnessable"])
        gained_single = sorted(
            name for name, row in mutant_stamp["rules"].items()
            if row["single_witness"] and name not in base_stamp["rules"])
        if not lost and not gained_single:
            problems.append(
                "declared reversible_to_irreversible, but no surviving rule "
                "lost re-witnessability and no new single-witness rule appeared "
                "(base score %.4f, mutant score %.4f)"
                % (base_stamp["reversibility_score"],
                   mutant_stamp["reversibility_score"]))
    return problems


def describe(edit: Edit, base_trace_dir: str = OUT) -> Dict[str, Any]:
    """The machine-readable description of one edit.  Scoring-only."""
    base_spec = BY_ID[edit.base]
    mutant_spec = edit.spec()
    base = GridWorld(base_spec)
    mutant = GridWorld(mutant_spec)

    base_states = base.reachable()
    mutant_states = mutant.reachable()
    base_stamp = _stamp(base)
    mutant_stamp = _stamp(mutant)

    base_solve = solvability.report(base, diagnose=False)
    mutant_solve = solvability.report(mutant, diagnose=False)

    # ---------------------------------------------------------- 检测延迟
    earliest = earliest_detection(base, mutant)
    streams: Dict[str, Any] = {}
    trace_path = os.path.join(base_trace_dir, edit.base, "raw_trace.jsonl")
    if os.path.exists(trace_path):
        _frames, trace_actions, _wins = read_trace(trace_path)
        streams["base_raw_trace"] = stream_divergence(base, mutant, trace_actions)
    if base_solve.get("optimal_plan"):
        streams["base_optimal_plan"] = stream_divergence(
            base, mutant, base_solve["optimal_plan"])

    # ---------------------------------------------------------- 连带作废
    forward = one_step_divergence(base, mutant, base_states)
    backward = one_step_divergence(base, mutant, mutant_states)
    falsified = sorted({row["base_rule"] for row in forward["rule_pairs"]}
                       | {row["mutant_rule"] for row in forward["rule_pairs"]}
                       | {row["base_rule"] for row in backward["rule_pairs"]}
                       | {row["mutant_rule"] for row in backward["rule_pairs"]})

    base_inv = {row["name"]: row for row in truth.check_invariants(base, base_states)}
    mutant_inv = {row["name"]: row
                  for row in truth.check_invariants(mutant, mutant_states)}
    now_false = sorted(name for name, row in mutant_inv.items()
                       if row.get("verified") and not row.get("holds", True))
    claims_added = sorted(set(mutant_inv) - set(base_inv))
    claims_removed = sorted(set(base_inv) - set(mutant_inv))

    # Both graphs. The base's alone has no row for a claim the *edit* introduced
    # — `latch_monotone` appears in `claims_added` for both `switch.mode=latch`
    # mutants and could never enter `claims_to_reexamine` — and no node for a
    # rule tag that exists only in the mutant, which is every `action_forbidden`.
    deps = claim_dependencies(base)
    deps_mutant = claim_dependencies(mutant)
    merged: Dict[str, Set[str]] = {k: set(v) for k, v in deps["claims"].items()}
    for claim, rules in deps_mutant["claims"].items():
        merged.setdefault(claim, set()).update(rules)
    reexamine = sorted(
        claim for claim, rules in merged.items()
        if rules & set(falsified) and claim not in now_false)

    witness_changes = {}
    for name in sorted(set(base_stamp["rules"]) | set(mutant_stamp["rules"])):
        before = base_stamp["rules"].get(name)
        after = mutant_stamp["rules"].get(name)
        b = None if before is None else before["max_witnesses"]
        a = None if after is None else after["max_witnesses"]
        if b != a:
            witness_changes[name] = {"base": b, "mutant": a}

    verdict = "solvable" if mutant_solve["solvable"] else "unsolvable"
    base_verdict = "solvable" if base_solve["solvable"] else "unsolvable"

    # ---------------------------------------------------------- 修复成本
    repair = greedy_witness_budget(base, mutant)

    family_problems = check_family(edit, base, mutant, base_stamp, mutant_stamp)

    return {
        "variant_id": edit.variant_id,
        "base_world_id": edit.base,
        "edit_family": edit.edit_family,
        "edit_family_agrees": not family_problems,
        "edit_family_problems": family_problems,
        "operators": [dict(sorted(_jsonable(op).items())) for op in edit.operators],
        # Measured, and worth separating because the two are different
        # questions. `cycler.phase0` moves where the world *starts* and leaves
        # every rule alone: nothing is falsified, no repair is needed, and the
        # only thing that changed is how many times a trajectory can witness a
        # rule that still says exactly what it said. An adaptation item built on
        # it is asking something else than one built on a changed guard, and a
        # descriptor that flattened the two would let the paper conflate them.
        "changes": {
            "transition_function": bool(forward["observations"]
                                        or backward["observations"]),
            "initial_state": base.initial() != mutant.initial(),
        },
        # -------------------------------------------------- scoring-only text
        "transparent_name": edit.transparent_name,
        "justification": edit.justification,
        "leak_probes": sorted({edit.transparent_name, edit.base,
                               edit.edit_family, base_verdict, verdict}
                              | {str(op.get("prop", "")) for op in edit.operators
                                 if op.get("prop")}
                              | {str(op.get("action", "")) for op in edit.operators
                                 if op.get("action")}),
        # ------------------------------------------------------------ 检测延迟
        "detection": {
            "earliest_actions": earliest["actions"],
            "earliest_witness": earliest["witness"],
            "search_complete": earliest["complete"],
            "observationally_equivalent": (earliest["actions"] is None
                                           and earliest["complete"]),
            "first_divergent_rules": {"base": earliest["base_rule"],
                                      "mutant": earliest["mutant_rule"]},
            "pairs_explored": earliest["pairs_explored"],
            "streams": streams,
            "note": earliest.get("note"),
        },
        # ------------------------------------------------------------ 连带作废
        "collateral": {
            "rules_falsified": falsified,
            "rule_pairs_forward": forward["rule_pairs"],
            "rule_pairs_backward": backward["rule_pairs"],
            "divergence_examples": forward["examples"],
            "claims_now_false": now_false,
            "claims_to_reexamine": reexamine,
            "claims_added": claims_added,
            "claims_removed": claims_removed,
            # The dependency edges of the claims that exist only in the mutant.
            # `claim_dependencies[<base>]` at the top of this file cannot carry
            # them, and without them a claim the edit *created* would be
            # ungradeable for collateral.
            "claim_dependencies_added": {
                claim: sorted(deps_mutant["claims"][claim])
                for claim in claims_added if claim in deps_mutant["claims"]},
            "rule_witness_changes": witness_changes,
            "verdict": verdict,
            "base_verdict": base_verdict,
            "verdict_flipped": verdict != base_verdict,
            "optimal_length": {"base": base_solve.get("optimal_length"),
                               "mutant": mutant_solve.get("optimal_length")},
            "reachable_states": {"base": len(base_states),
                                 "mutant": len(mutant_states)},
            "reversibility_score": {"base": base_stamp["reversibility_score"],
                                    "mutant": mutant_stamp["reversibility_score"]},
        },
        # ------------------------------------------------------------ 修复成本
        "repair": {
            "divergent_observations": forward["observations"],
            "agreeing_observations": forward["agreeing_observations"],
            "divergent_share": round(
                forward["observations"]
                / max(1, forward["observations"] + forward["agreeing_observations"]), 6),
            "greedy_witness_budget": repair["greedy_actions"],
            "greedy_actions_before_stall": repair["greedy_actions_before_stall"],
            "stalled_on": repair["stalled_on"],
            "classes_total": repair["classes_total"],
            "classes_witnessable_in_mutant": repair["classes_witnessable_in_mutant"],
            "classes_only_in_base": repair["classes_only_in_base"],
            "bound": repair["bound"],
            "miner_measured": None,
            "miner_blocked_on": "engine-rig's miner represents a two-object "
                                "sokoban percept and cannot express mechanism "
                                "state; see exam/runs/20260728T090621Z-"
                                "V2-exam-on-worldgen/GAPS.md. A repair score "
                                "against a miner that cannot represent the "
                                "state is not a measurement, so this is null "
                                "rather than approximated.",
        },
        "artifacts": {
            "dir": "worldgen/out/worlds/%s" % edit.variant_id,
            "open": ["spec.json", "raw_trace.jsonl"],
            "scoring_only": ["ground_truth.json", "GROUND_TRUTH.md",
                             "coverage.json", "reversibility.json"],
        },
    }


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_jsonable(v) for v in value]
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


def build_descriptors(root: str = OUT,
                      roster: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    edits = sorted(MUTATIONS, key=lambda e: e.variant_id)
    rows = [describe(edit, base_trace_dir=root) for edit in edits]
    bases = sorted({e.base for e in edits})
    return {
        "prompt_id": "C6-worldgen-mutate",
        "schema_version": "worldgen/mutations/v0.2",
        "read_licence": "scoring-only — this file names the edit, which is the "
                        "answer to every adaptation item built on it",
        # The mutants' roster, in `INDEX.json`'s exact shape and judged by the
        # same `build.gate_failures`. It is here and not in `INDEX.json` because
        # putting it there breaks five tests in `exam/` — see
        # `build.all_specs.__doc__`. A reader who wants the twenty-plus-fifteen
        # view concatenates two files; `exam/` admitting these ids is a one-line
        # change in `exam/guard.py`, in `exam/`'s territory.
        "roster": roster,
        "mutations": rows,
        "claim_dependencies": {
            base: claim_dependencies(GridWorld(BY_ID[base])) for base in bases
        },
        "knobs": [k.as_json() for k in KNOBS],
        "totals": {
            "mutations": len(rows),
            "bases": bases,
            "by_family": {
                family: sorted(r["variant_id"] for r in rows
                               if r["edit_family"] == family)
                for family in EDIT_FAMILIES
            },
            "edit_family_disagreements": sorted(
                r["variant_id"] for r in rows if not r["edit_family_agrees"]),
            "observationally_equivalent": sorted(
                r["variant_id"] for r in rows
                if r["detection"]["observationally_equivalent"]),
            # Published rather than buried: these are the variants for which no
            # repair budget exists at all, because no single walk in the mutated
            # world can witness every class the edit created.
            "repair_walk_stalls": sorted(r["variant_id"] for r in rows
                                         if r["repair"]["stalled_on"]),
            "verdict_flips": sorted(r["variant_id"] for r in rows
                                    if r["collateral"]["verdict_flipped"]),
            "unsolvable": sorted(r["variant_id"] for r in rows
                                 if r["collateral"]["verdict"] == "unsolvable"),
            "detection_range": sorted(
                r["detection"]["earliest_actions"] for r in rows
                if r["detection"]["earliest_actions"] is not None),
        },
    }


def prune_orphans(root: str = OUT) -> List[str]:
    """Delete `v-*` directories that no live mutation claims.

    A variant id is a **digest of its operators**, so editing an operator does
    not update a directory — it strands the old one and creates a new one beside
    it. That is not a tidiness problem: an orphan is a complete six-file world,
    published under an id nothing describes, missing from `INDEX.json` and
    therefore invisible to every gate that would have judged it. This run
    produced two within an hour of the corpus being revised, and would have
    committed both.
    """
    live = set(MUTANT_BY_ID)
    removed: List[str] = []
    if not os.path.isdir(root):
        return removed
    for name in sorted(os.listdir(root)):
        path = os.path.join(root, name)
        if not name.startswith("v-") or not os.path.isdir(path):
            continue
        if name in live:
            continue
        shutil.rmtree(path)
        removed.append(name)
    return removed


def write_descriptors(root: str = OUT,
                      roster: Optional[Dict[str, Any]] = None) -> str:
    blob = build_descriptors(root, roster=roster)
    path = os.path.join(root, "MUTATIONS.json")
    os.makedirs(root, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(blob, indent=2, sort_keys=True) + "\n")
    return path


def mutation_gate_failures(root: str = OUT) -> List[str]:
    """The mutants' own two gates, read back off the descriptor file.

    **The family claim.** A mutation's `edit_family` is a claim about what the
    edit *is*, and the catalogue has been wrong about a claim of exactly this
    kind before — `intended_solvable` exists because twenty worlds shipped with
    the label inverted. So the claim is compared against the operators and, for
    `reversible_to_irreversible`, against the two measured reversibility stamps.

    **The solvability claim.** `build.py`'s `solvability_intent_failures` gate
    reads `spec.intended_solvable`, which a mutant deliberately leaves blank so
    that its open `spec.json` does not carry the answer to a verdict item. The
    check itself is not dropped, only moved: the claim lives in
    `Edit.intended_solvable` and is compared here against the exhaustive
    reachability decision recorded in the descriptor.
    """
    path = os.path.join(root, "MUTATIONS.json")
    if not os.path.exists(path):
        return ["MUTATIONS.json was not written"]
    with open(path, encoding="utf-8") as handle:
        blob = json.load(handle)
    out: List[str] = []
    for row in blob["mutations"]:
        for problem in row["edit_family_problems"]:
            out.append("%-12s declared %-26s %s"
                       % (row["variant_id"], row["edit_family"], problem))
        claimed = MUTANT_BY_ID[row["variant_id"]].intended_solvable
        measured = row["collateral"]["verdict"] == "solvable"
        if claimed is not None and claimed != measured:
            out.append("%-12s claims intended_solvable=%r, the exhaustive "
                       "search says %r" % (row["variant_id"], claimed, measured))
    return out


# ======================================================================= cli

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="build the mutant corpus")
    parser.add_argument("--list", action="store_true",
                        help="print the corpus and exit")
    parser.add_argument("--knobs", action="store_true",
                        help="print the declared semantic knobs and exit")
    parser.add_argument("--into", default=OUT)
    args = parser.parse_args(argv)

    if args.knobs:
        for knob in KNOBS:
            print("%-8s %-8s %-16s %-12s %s"
                  % (knob.scope, knob.kind or "-", knob.prop, knob.mechanism,
                     knob.domain))
        return 0

    if args.list:
        for edit in sorted(MUTATIONS, key=lambda e: e.variant_id):
            print("%-12s %-28s %-28s %s"
                  % (edit.variant_id, edit.edit_family, edit.base,
                     edit.transparent_name))
        return 0

    from . import build as build_module            # late: build imports this one

    specs = mutant_specs()
    for spec in specs:
        row = build_module.build_world(spec, args.into)
        print("%-12s tier=%d states=%-5d cov=%-9s rev=%.2f %s"
              % (row["world_id"], row["tier"], row["reachable_states"],
                 row["coverage"], row["reversibility_score"],
                 "solvable(%s)" % row["optimal_length"] if row["solvable"]
                 else "UNSOLVABLE"))

    path = write_descriptors(args.into)
    blob = json.loads(open(path, encoding="utf-8").read())
    print()
    print(json.dumps(blob["totals"], indent=2, sort_keys=True))
    print("-> %s" % os.path.relpath(path, os.path.dirname(HERE)))
    problems = mutation_gate_failures(args.into)
    if problems:
        print()
        print("MUTATION GATE FAILED:")
        for line in problems:
            print("  " + line)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
