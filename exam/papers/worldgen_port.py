"""The world factory, seen from the exam side.

`C1-worldgen` ships twenty worlds, each with its own ground truth. This module
is the only place `exam/` knows how to open one, so that a paper module can be
written against a world rather than against a directory layout.

WHAT THIS BUYS, AND WHY IT IS NOT JUST PLUMBING

The hand-built A0 papers had to write their own event classifier -- six named
classes, derived by re-deriving the transition and asking which of them it looked
like (`heldout.classify`). A generated world does not need one: `GridWorld.explain`
returns the next state **and the name of the rule that produced it**, from the
same code path that produced the state. The classifier and the world can
therefore no longer disagree, which is a class of bug the A0 paper could only
test for.

That is the general shape of the port. Where A0 needed a reconstruction, the
factory has a measurement:

| the A0 paper reconstructs | the factory measured |
|---|---|
| the event class of a transition | `GridWorld.explain` -> rule name |
| which transitions the evidence set saw | `raw_trace.jsonl`, the published discovery input |
| the well-formed universe (a Cartesian product) | `GridWorld.reachable()` |
| solvability, by search | `ground_truth.json["solvability"]`, with a certificate |
| the legend | `ground_truth.json["palette"]` |

THE READ LICENCE IS THE POINT, NOT A FORMALITY

`worldgen/build.py` publishes a split: `raw_trace.jsonl` and `spec.json` are
readable by anyone, and `ground_truth.json` / `coverage.json` /
`reversibility.json` are **scoring only**. That split is the only thing standing
between the catalogue and a rigged evaluation, and an exam is exactly the
consumer that could quietly break it -- an item's *paper* side must be buildable
from the open files alone, while its *truth* side may use everything.

So this module keeps the two apart by construction rather than by care:
`open_world()` returns what may go on a sheet; `scoring_truth()` is a separate
call with a name that says what it is, and the paper modules that use it put its
output only in `Item.truth`. There is a test that the sheet of every generated
paper is reproducible from the open files alone.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))      # exam/
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from worldgen.core.spec import WorldSpec                        # noqa: E402
from worldgen.core.trace import read_trace                      # noqa: E402
from worldgen.core.types import ACTIONS, State                  # noqa: E402
from worldgen.core.world import GridWorld                       # noqa: E402

WORLDS_DIR = os.path.join(REPO, "worldgen", "out", "worlds")
INDEX_PATH = os.path.join(WORLDS_DIR, "INDEX.json")

#: Files a paper's *sheet* may be built from. Anything else is scoring-only.
OPEN_FILES = ("spec.json", "raw_trace.jsonl")
SCORING_FILES = ("ground_truth.json", "coverage.json", "reversibility.json",
                 "GROUND_TRUTH.md")


class WorldNotBuilt(RuntimeError):
    """The factory has not produced this world. A real state, not a bug."""


def _read_json(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def roster() -> List[Dict[str, Any]]:
    """Every built world's summary row, in the factory's own order."""
    if not os.path.exists(INDEX_PATH):
        return []
    return list(_read_json(INDEX_PATH).get("worlds", []))


def world_ids() -> Tuple[str, ...]:
    return tuple(str(row["world_id"]) for row in roster() if row.get("world_id"))


def summary(world_id: str) -> Dict[str, Any]:
    """The roster row: tier, families, sizes, coverage, reversibility."""
    for row in roster():
        if row.get("world_id") == world_id:
            return dict(row)
    raise WorldNotBuilt("%r is not in %s" % (world_id, INDEX_PATH))


def world_dir(world_id: str) -> str:
    path = os.path.join(WORLDS_DIR, world_id)
    if not os.path.isdir(path):
        raise WorldNotBuilt(
            "%s does not exist. Run `python -m worldgen.build` first; an exam "
            "set in a world that was never built would be scored against files "
            "that are not there." % path)
    return path


# -- the open half -----------------------------------------------------------

def open_world(world_id: str) -> GridWorld:
    """The live world, rebuilt from the *open* `spec.json`.

    Not from the catalogue in `worldgen.generate`, deliberately. The shipped
    spec is what a reader of the artefacts has; rebuilding from the in-process
    catalogue would let a paper depend on something an examinee's world does not
    contain, and the difference would only show up if the two ever diverged --
    which is exactly when it would matter.
    """
    spec = WorldSpec.from_json(_read_json(os.path.join(world_dir(world_id),
                                                       "spec.json")))
    return GridWorld(spec)


def trace(world_id: str) -> Tuple[List[List[List[int]]], List[Optional[str]],
                                  List[bool]]:
    """The published discovery input: `(frames, actions, wins)`."""
    return read_trace(os.path.join(world_dir(world_id), "raw_trace.jsonl"))


def evidence_index(world_id: str) -> Dict[str, List[List[int]]]:
    """`(frame_before, action) -> frame_after`, over the published trace only.

    This is the exam's definition of "what the examinee has already been shown",
    and it has to be computed from the trace rather than from the world, because
    the trace is what was published. A world's reachable set is much larger than
    its trace: `t3-full-house` has 2,654 reachable states and a 421-line trace.
    That gap is where held-out items come from.
    """
    frames, actions, _ = trace(world_id)
    index: Dict[str, List[List[int]]] = {}
    for position, action in enumerate(actions):
        if action is None or position + 1 >= len(frames):
            continue
        index[transition_key(frames[position], action)] = frames[position + 1]
    return index


def transition_key(frame: Sequence[Sequence[int]], action: str) -> str:
    """The identity of a transition *as the examinee can see it*.

    Rendered frame plus action, not internal state plus action. An examinee sees
    frames; if two distinct internal states render identically then they are the
    same question, and treating them as two would let a "held-out" item be one
    the trace already answered. `ground_truth.json["frame_determines_state"]`
    records whether that collapse actually happens in a given world, and
    `frame_ambiguous()` below surfaces it rather than assuming it away.
    """
    return json.dumps([frame, action], sort_keys=True, separators=(",", ":"))


def palette(world: GridWorld) -> Dict[str, int]:
    """Colour by name, from the spec's own legend plus the fixed three.

    Open information: `spec.json` carries `colors`, and the floor/wall/agent
    values are constants of the renderer.
    """
    from worldgen.core.types import AGENT, FLOOR, WALL
    legend = {"floor": FLOOR, "wall": WALL, "agent": AGENT}
    legend.update({str(k): int(v) for k, v in dict(world.spec.colors).items()})
    return dict(sorted(legend.items()))


def legal_cells(world: GridWorld) -> Tuple[int, ...]:
    """Every value this world's renderer can emit.

    Handed to the marker on the truth side: the A0 rubric hardcoded `{0,2,4,8}`,
    which rejects every frame from every generated world as malformed -- and a
    malformed-answer verdict reads on a report as an examinee that cannot format
    JSON, not as a rubric that was pointed at the wrong world.
    """
    return tuple(sorted(set(palette(world).values())))


# -- the scoring half --------------------------------------------------------

def scoring_truth(world_id: str) -> Dict[str, Any]:
    """`ground_truth.json`. **Scoring only** -- never put this on a sheet."""
    return _read_json(os.path.join(world_dir(world_id), "ground_truth.json"))


def coverage(world_id: str) -> Dict[str, Any]:
    """`coverage.json`. Scoring only."""
    return _read_json(os.path.join(world_dir(world_id), "coverage.json"))


def reversibility(world_id: str) -> Dict[str, Any]:
    """`reversibility.json`. Scoring only -- the A0' stamp."""
    return _read_json(os.path.join(world_dir(world_id), "reversibility.json"))


# -- what a paper needs to know before it tries to set questions -------------

def rule_names(world: GridWorld) -> Tuple[str, ...]:
    """Every rule name `explain()` can return for this world.

    Derived by walking the reachable transition relation rather than read from
    the ground truth, so it is available on the open side and so it names the
    rules that actually *fire* -- a declared rule that never fires cannot carry
    an item.
    """
    seen = set()
    for _state, _action, _after, rule in world.transitions():
        seen.add(rule)
    return tuple(sorted(seen))


def firing_counts(world: GridWorld) -> Dict[str, int]:
    """How many reachable transitions each rule accounts for."""
    counts: Dict[str, int] = {}
    for _state, _action, _after, rule in world.transitions():
        counts[rule] = counts.get(rule, 0) + 1
    return dict(sorted(counts.items()))


def frame_ambiguous(world_id: str) -> bool:
    """Do two distinct states of this world render to the same frame?

    If they do, a frame-keyed evidence index conflates them, and an item drawn
    from one is partly answered by the trace's visit to the other. The factory
    measures this per world; the exam reads the measurement instead of assuming.
    """
    truth = scoring_truth(world_id)
    return not bool(truth.get("frame_determines_state", {}).get("injective", True))


def feasibility(world_id: str, per_class: int = 2) -> Dict[str, Any]:
    """Can this world carry a matched-quota held-out paper, and if not, why not?

    Answered before anything is built, and answered per rule, because the
    matched-quota property is the one that makes the `replay`/`heldout` tag safe
    to print on a sheet -- and on a small world it is simply unobtainable. The
    honest failure is "this world cannot carry this question type", stated with
    the counts, not a paper that quietly drops its rare class.

    A rule qualifies when it has `per_class` transitions inside the trace **and**
    `per_class` outside it. Both halves are needed: a rule the trace witnessed
    once has no second witness to hold out (which is A0's own failure mode,
    recorded as the A0' criterion), and a rule the trace never witnessed has no
    replay control.
    """
    world = open_world(world_id)
    index = evidence_index(world_id)
    inside: Dict[str, int] = {}
    outside: Dict[str, int] = {}
    for state, action, _after, rule in world.transitions():
        key = transition_key(world.render(state), action)
        bucket = inside if key in index else outside
        bucket[rule] = bucket.get(rule, 0) + 1

    rules = sorted(set(inside) | set(outside))
    usable = [r for r in rules
              if inside.get(r, 0) >= per_class and outside.get(r, 0) >= per_class]
    blocked = {r: {"in_trace": inside.get(r, 0), "held_out": outside.get(r, 0)}
               for r in rules if r not in usable}
    return {
        "world_id": world_id,
        "per_class": per_class,
        "rules": rules,
        "usable_rules": usable,
        "blocked_rules": dict(sorted(blocked.items())),
        "feasible": len(usable) >= 2,
        "why_not": (None if len(usable) >= 2 else
                    "only %d rule(s) have %d transitions both inside and "
                    "outside the published trace; a matched-quota paper needs "
                    "at least 2, or the replay/heldout tag becomes a hint"
                    % (len(usable), per_class)),
        "frame_ambiguous": frame_ambiguous(world_id),
        "transitions_in_trace": sum(inside.values()),
        "transitions_held_out": sum(outside.values()),
    }


def survey(per_class: int = 2) -> List[Dict[str, Any]]:
    """Feasibility across the whole catalogue. This is the difficulty map."""
    return [feasibility(world_id, per_class) for world_id in world_ids()]
