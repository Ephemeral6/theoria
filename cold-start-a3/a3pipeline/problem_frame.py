"""The **problem** half of the domain/problem split, by two different routes.

`theory/domain.dsl` is the domain: it has no coordinate in it.  Everything that
is true of *one* level — the grid, the board map, where the objects start, what
`exit_a` and `exit_b` name, which cell wins — is a `compile.problem.Problem`,
and this module builds one.

**The two entry points are the experiment.**  They differ in exactly one thing:
how much of the world the caller had to look at.

| | `from_trace` | `from_frame` |
|---|---|---|
| input | a whole `*_sweep.jsonl` (333 frames, 332 actions) | one `*_frame0.json` (1 frame, 0 actions) |
| board / objects / arena | derived, by A0's `problem.derive` | derived, from the single frame |
| `goal_cell`, `exit_a`, `exit_b` | **supplied** | **supplied** |
| what the arm paid | a full sweep of the level | one look at it |

C3's claim is that the second column is enough once the books have been
written, so the second column has to be *audited*, not asserted.  Both entry
points return `(Problem, provenance)`, and `provenance["fields"]` says, per
`Problem` field, whether the value was derived or handed over.  That dict is
what `A3_REPORT` prints, so the size of the concession is a number in a table.

**The concession, stated plainly.**  Three values are supplied on both routes:

* `goal_cell` — the goal cell is not rendered in any frame (`a3world/a3_world.py`
  on D-A3-002), so no amount of looking recovers it.  PDDL puts the goal in the
  problem file; so does A3.
* `exit_a` / `exit_b` — a portal's exit is plain floor and looks like plain
  floor (D-A3-003), so it is not in the pixels either.  The `landmark`
  declarations in the domain name them; the problem instance says where.
* the object-colour map — which colours are objects rather than scenery.  This
  is the manual's `word_table`, not level data, and it is the *same* map on both
  routes, so it does not separate them.  It is recorded anyway.

`from_trace` could in principle derive `goal_cell` (A0's `derive` reads it off
the frames where the trace's `win` flag is set) and could *not* derive the two
landmarks (A0 infers `portal_exit` only when there is exactly one jump
destination, and A3 has two — trap T1).  Both facts are recorded in
`provenance["also_derivable"]` rather than exploited: if the two routes were
allowed to supply different things, `compare_problems` would be comparing two
different questions.

**Sanity requirement.**  For level 2, `from_frame(l2_frame0.json)` must return a
`Problem` equal in every field to `from_trace(l2_sweep.jsonl)`.  That is the
whole justification for the transfer arm reading one frame: not "close enough",
but the same object.  `compare_problems` reports the per-field verdict and
`tests/` asserts it.

Credit: `from_trace` is a thin wrapper over `cold-start-a0`'s
`compile.problem.derive`, unmodified, with `name_by_color` supplied because A0's
default map is `{7: "Button", 5: "Door", 6: "Cart"}` and A3's object is a
`Switch`.  `from_frame` re-derives A0's algorithm for the one-frame case; the
algorithm is A0's and the credit is A0's.
"""

import json
import os
import sys
from collections import Counter
from dataclasses import replace
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from compile import problem as problem_mod  # noqa: E402  (cold-start-a0, read-only)
from compile.problem import ObjectInstance, Problem  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

Cell = Tuple[int, int]

#: The manual's `word_table`, as a colour map.  Both routes get the same one —
#: see the module docstring on why that is not a thumb on the scale.  Colours 7
#: and 8 are the same object in two polarities (`Switch` up / down), which is
#: why the map is not injective; A0's `NAME_BY_COLOR` could not express that
#: because A0's Button was a latch and never came back up.
OBJECT_COLOURS: Dict[int, str] = {5: "Door", 6: "Cart", 7: "Switch", 8: "Switch"}

#: What `compile.problem.derive` needs instead.  It reads the colour off frame
#: 0 only, so the down-polarity 8 never reaches it; passing it anyway would be
#: harmless but would suggest A0's derive can handle a two-polarity object, and
#: it cannot (it would name a colour-8 frame-0 Switch `Switch` and then still
#: only ever see one colour per track).
NAME_BY_COLOR: Dict[int, str] = {5: "Door", 6: "Cart", 7: "Switch"}

#: Every field of `compile.problem.Problem`, in declaration order.  Written out
#: rather than taken from `dataclasses.fields` so that a field added upstream
#: shows up as a test failure here instead of being silently unaudited.
PROBLEM_FIELDS = (
    "name", "height", "width", "background", "board", "objects",
    "goal_cell", "landmarks", "arena",
)


# --------------------------------------------------------------- frame reading

def read_frame(frame_path: str) -> List[List[int]]:
    """One frame out of a `{"t": 0, "frame": [[...]]}` file, and nothing else.

    Deliberately not `read_trace`: the transfer arm must be unable to read a
    second frame even by accident, and the cheapest way to guarantee that is
    for the only reader on its path to return exactly one grid.
    """
    with open(frame_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    frame = payload["frame"]
    if not frame or not frame[0]:
        raise ValueError("%s holds an empty frame" % frame_path)
    width = len(frame[0])
    if any(len(row) != width for row in frame):
        raise ValueError("%s is not rectangular" % frame_path)
    return [list(row) for row in frame]


def background_from_frame(frame: Sequence[Sequence[int]]) -> int:
    """The background colour, from a single frame.

    **This is the one derivation that genuinely cannot reuse A0's.**
    `pipeline.engines_stage.background_color` counts colours over the board's
    *dynamic* cells — the cells that changed at least once — precisely because
    counting over the whole frame gets it wrong on any world with a wall border
    (its own docstring says so).  With one frame there are no dynamic cells:
    nothing has had a chance to change.  And the naive count really does fail
    here — A3's level 1 is 46 wall pixels against 35 of everything else, so
    "most common colour" would answer `1`.

    The rule used instead, and its assumption stated rather than buried:

        if every cell on the outer ring carries the same colour, that colour is
        structure, not background; the background is the commonest colour among
        the cells that are left.

    The assumption is that the level has a solid frame around it.  A3's two
    levels do, ARC grids very often do, and a level that did not would fall
    through to the plain count — which is the answer A0 would give from one
    frame anyway, so the fallback is no worse than the baseline.  Ties break on
    the smaller colour value, so the result is deterministic.

    Cost, recorded because it is a real one: on a level with no border this
    returns whatever the plain count returns, and if that is wrong every
    downstream field is wrong with it.  The `compare_problems` check against the
    trace route is what catches that, and it is why the check exists.
    """
    height, width = len(frame), len(frame[0])
    border = [frame[0][c] for c in range(width)]
    border += [frame[height - 1][c] for c in range(width)]
    border += [frame[r][0] for r in range(height)]
    border += [frame[r][width - 1] for r in range(height)]

    counts: Counter = Counter()
    excluded: Optional[int] = None
    if len(set(border)) == 1:
        excluded = border[0]
    for row in frame:
        for value in row:
            if value != excluded:
                counts[value] += 1
    if not counts:                       # a frame that is nothing but border
        counts[border[0]] = 1
    best = min(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return best[0]


# ------------------------------------------------------------------ the routes

def from_trace(trace_path: str, name: str, goal_cell: Cell,
               exit_a: Cell, exit_b: Cell) -> Tuple[Problem, Dict[str, object]]:
    """The cold-start route: derive the level from its whole sweep.

    A0's `compile.problem.derive`, unmodified, with `name_by_color` supplied.
    Two of its results are then *overwritten* by the caller's, and the
    originals are kept in the provenance so the substitution is on the record:

    * `goal_cell` — derive finds `(7, 7)` on level 1 from the `win` flags.  The
      caller's value is used anyway, because the transfer route cannot do that
      and a comparison between two routes that were asked different questions
      is not a comparison.
    * `landmarks` — derive returns `{}`.  It infers `portal_exit` only when the
      Cart has exactly one jump destination (`problem.py:118-126`); A3 has two,
      so the inference declines, silently, and a manual full of
      `jumped(Cart, exit_a)` would compile to `LANDMARKS['exit_a']` and blow up
      with a `KeyError` at the first `step` (reference trap T1).  Supplying the
      landmarks is what stops that, on **both** routes.
    """
    derived = problem_mod.derive(trace_path, name, name_by_color=NAME_BY_COLOR)
    landmarks = {"exit_a": tuple(exit_a), "exit_b": tuple(exit_b)}
    prob = replace(derived,
                   goal_cell=tuple(goal_cell),
                   landmarks=landmarks)

    frames = actions = 0
    with open(trace_path, "r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            frames += 1
            if json.loads(line).get("action") is not None:
                actions += 1

    provenance = _provenance(
        route="trace",
        source=trace_path,
        prob=prob,
        derived_tag="derived_from_trace",
        inputs_read={"frames": frames, "actions": actions},
        also_derivable={
            "goal_cell": (list(derived.goal_cell) if derived.goal_cell
                          else None),
            "goal_cell_note":
                "A0's derive reads the goal off the frames whose `win` flag is "
                "set; the supplied value is used instead so both routes answer "
                "the same question",
            "landmarks": {k: list(v) for k, v in derived.landmarks.items()},
            "landmarks_note":
                "empty: A0's derive infers a landmark only for a single jump "
                "destination and A3 has two (trap T1) — nothing was overwritten",
        },
    )
    return prob, provenance


def from_frame(frame_path: str, name: str, goal_cell: Cell,
               exit_a: Cell, exit_b: Cell) -> Tuple[Problem, Dict[str, object]]:
    """The transfer route: derive the level from **one frame**.

    No trace, no world import, no second look.  What comes out of the pixels:

    | field | how |
    |---|---|
    | `height`, `width` | the frame's shape |
    | `background` | `background_from_frame` above |
    | `board` | the frame with every object cell blanked to background |
    | `objects` | every cell whose colour is in `OBJECT_COLOURS` |
    | `arena` | every cell the board leaves at background — floor, plus the cells the objects are standing on |

    The `arena` rule is A0's, restated for one frame.  A0 takes "the board is
    silent here" to mean `values[r][c] is None or == background`; with one frame
    nothing is `None`, but a cell is silent for exactly the same reason — an
    object is standing on it, or it is floor.  The static coloured cells (the
    two portals) are *not* arena on either route, which matters: it is why the
    PDDL form needs D-A3-006 and why the Lean form must not have it.
    """
    frame = read_frame(frame_path)
    height, width = len(frame), len(frame[0])
    background = background_from_frame(frame)

    objects: List[ObjectInstance] = []
    seen: Dict[str, Cell] = {}
    for r in range(height):
        for c in range(width):
            colour = frame[r][c]
            if colour not in OBJECT_COLOURS:
                continue
            obj_name = OBJECT_COLOURS[colour]
            if obj_name in seen:
                # The word table declares one instance per name.  Two cells of
                # the same object colour is a different world, not a warning.
                raise ValueError(
                    "two cells claim to be %s: %s and %s"
                    % (obj_name, seen[obj_name], (r, c)))
            seen[obj_name] = (r, c)
            objects.append(ObjectInstance(name=obj_name, pos=(r, c),
                                          color=colour))
    objects.sort(key=lambda o: o.name)   # A0's ordering; the generators rely on it

    occupied = {o.pos for o in objects}
    board = [
        [background if (r, c) in occupied else frame[r][c]
         for c in range(width)]
        for r in range(height)
    ]
    arena = sorted((r, c) for r in range(height) for c in range(width)
                   if board[r][c] == background)

    prob = Problem(
        name=name,
        height=height,
        width=width,
        background=background,
        board=board,
        objects=objects,
        goal_cell=tuple(goal_cell),
        landmarks={"exit_a": tuple(exit_a), "exit_b": tuple(exit_b)},
        arena=arena,
    )

    provenance = _provenance(
        route="frame",
        source=frame_path,
        prob=prob,
        derived_tag="derived_from_frame",
        inputs_read={"frames": 1, "actions": 0},
        also_derivable={
            "goal_cell": None,
            "goal_cell_note":
                "the goal cell is not rendered (D-A3-002); one frame or a "
                "thousand, it is not in the pixels",
            "landmarks": {},
            "landmarks_note":
                "a portal exit is plain floor (D-A3-003); it is not in the "
                "pixels either",
        },
    )
    return prob, provenance


# ------------------------------------------------------------------ provenance

def _provenance(route: str, source: str, prob: Problem, derived_tag: str,
                inputs_read: Dict[str, int],
                also_derivable: Dict[str, object]) -> Dict[str, object]:
    """One audited row per `Problem` field, plus the counts behind it.

    `name` is `supplied` on both routes and is listed rather than dropped: a
    field nobody audits is a field nobody notices going missing.
    """
    fields = {field: derived_tag for field in PROBLEM_FIELDS}
    fields["name"] = "supplied"
    fields["goal_cell"] = "supplied"
    fields["landmarks"] = "supplied"

    derived_count = sum(1 for v in fields.values() if v == derived_tag)
    return {
        "route": route,
        "source": os.path.relpath(source, ROOT).replace(os.sep, "/"),
        "inputs_read": dict(inputs_read),
        "fields": fields,
        "derived_fields": derived_count,
        "supplied_fields": len(PROBLEM_FIELDS) - derived_count,
        "supplied_values": {
            "name": prob.name,
            "goal_cell": list(prob.goal_cell) if prob.goal_cell else None,
            "landmarks": {k: list(v) for k, v in sorted(prob.landmarks.items())},
        },
        "shared_priors": {
            "object_colour_map": {str(k): v for k, v in
                                  sorted(OBJECT_COLOURS.items())},
            "note": "the manual's word_table, identical on both routes, so it "
                    "does not separate them",
        },
        "counts": {
            "grid": [prob.height, prob.width],
            "background": prob.background,
            "objects": len(prob.objects),
            "object_names": [o.name for o in prob.objects],
            "arena_cells": len(prob.arena),
            "board_non_background_cells": sum(
                1 for row in prob.board for v in row if v != prob.background),
        },
        "also_derivable": also_derivable,
    }


# --------------------------------------------------------------- the comparison

def compare_problems(a: Problem, b: Problem) -> Dict[str, object]:
    """Per-field equality between two `Problem`s, as data.

    Not `a == b`: the dataclass compares fine, but a boolean is useless when it
    is `False`, and the whole point of the check is what it says when it fails.
    Object lists are compared as tuples so that `ObjectInstance` ordering is
    part of the verdict — the generators index objects positionally in places
    (`gen_pddl_a0` takes `next(o for o in problem.objects if o.name == "Cart")`,
    `gen_python_a0.initial_state` emits them in list order), so two problems
    with the same objects in a different order are not interchangeable.
    """
    def norm(prob: Problem, field: str):
        value = getattr(prob, field)
        if field == "objects":
            return [(o.name, tuple(o.pos), o.color, o.present) for o in value]
        if field == "landmarks":
            return {k: tuple(v) for k, v in sorted(value.items())}
        if field == "arena":
            return [tuple(c) for c in value]
        if field == "goal_cell":
            return tuple(value) if value is not None else None
        if field == "board":
            return [list(row) for row in value]
        return value

    fields: Dict[str, object] = {}
    for field in PROBLEM_FIELDS:
        left, right = norm(a, field), norm(b, field)
        row: Dict[str, object] = {"equal": left == right}
        if left != right:
            row["a"] = left
            row["b"] = right
        fields[field] = row

    differing = sorted(f for f, row in fields.items() if not row["equal"])
    return {
        "equal": not differing,
        "fields": fields,
        "differing_fields": differing,
    }


def write_provenance(path: str, payload: Dict[str, object]) -> str:
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path
