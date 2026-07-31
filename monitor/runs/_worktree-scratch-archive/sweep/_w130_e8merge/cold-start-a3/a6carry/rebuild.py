"""The **problem rebuilder**, in a form that is not about A3's world.

A3's `a3pipeline/problem_frame.from_frame` is the algorithm this generalises, and
the generalisation is exactly three constants:

| A3 held it as | carrypack holds it as |
|---|---|
| `OBJECT_COLOURS = {5: "Door", 6: "Cart", 7: "Switch", 8: "Switch"}` | `requires.objects[].colours` |
| `landmarks={"exit_a": …, "exit_b": …}` | `requires.landmarks`, valued by the caller |
| `goal_cell` supplied, always | `requires.supplied_constants` |

Everything else is the same derivation and it is A0's: the board is the frame
with the object cells blanked, the arena is what the board leaves at background,
and the background comes off the border.  Credit for the algorithm is A0's and
for the one-frame restatement is A3's; what is new here is that the module holds
no colour, no name and no coordinate of its own.

## The preflight is the point

`from_frame` in A3 could not fail informatively.  Hand it a frame with no Switch
in it and it builds a `Problem` with no Switch; `gen_python_a0.initial_state`
then omits the field, the dataclass default `(0, 0)` takes over, and the manual
predicts a Switch in the top-left corner of a level that does not have one.  The
cheap layer does catch that — as `render_mismatch` at t=0, i.e. as evidence that
the *manual* is wrong.

So `preflight` runs first and returns a verdict, and `rebuild_from_frame` raises
`RebuildRefusal` on a red one **before** a problem instance exists.  The
distinction it draws is the one that matters online:

* a declared **object** that is not on the frame is a **refusal** — the manual is
  about a world this level is not;
* a **guard colour** that is not on the frame is a **note** — the level simply
  does not present that mechanism, the rules guarding on it lie dormant, and
  that is the ordinary case when a domain covers more than one level.

The second is what "the domain travels" looks like from underneath, so it must
not be an error; the first is what a *wrong* carried domain looks like on frame
0, so it must not be a warning.
"""

import json
import os
import sys
from collections import Counter
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from compile.problem import ObjectInstance, Problem  # noqa: E402  (cold-start-a0)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

Cell = Tuple[int, int]

#: Every field of `compile.problem.Problem`, in declaration order.  Written out
#: rather than taken from `dataclasses.fields` so a field added upstream shows up
#: as a test failure here instead of being silently unaudited.  A3's list,
#: unchanged — the audit is the same audit.
PROBLEM_FIELDS = (
    "name", "height", "width", "background", "board", "objects",
    "goal_cell", "landmarks", "arena",
)


class RebuildRefusal(Exception):
    """The frame does not present the world the carried domain is about.

    Carries the preflight verdict so a caller can report *which* check failed
    without re-running it.
    """

    def __init__(self, verdict: Dict[str, object]):
        self.verdict = verdict
        super().__init__("; ".join(verdict["refusals"]) or "rebuild refused")


# --------------------------------------------------------------- frame reading

def read_frame(frame_path: str) -> List[List[int]]:
    """One frame out of a `{"t": 0, "frame": [[...]]}` file, and nothing else.

    Deliberately not a trace reader: an arm carrying books must be unable to read
    a second frame even by accident, and the cheapest way to guarantee that is
    for the only reader on its path to return exactly one grid.  A3's rule, kept.
    """
    with open(frame_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return normalise_frame(payload["frame"], frame_path)


def normalise_frame(frame: Sequence[Sequence[int]], where: str = "<frame>"
                    ) -> List[List[int]]:
    if not frame or not frame[0]:
        raise ValueError("%s holds an empty frame" % where)
    width = len(frame[0])
    if any(len(row) != width for row in frame):
        raise ValueError("%s is not rectangular" % where)
    return [list(row) for row in frame]


def background_from_frame(frame: Sequence[Sequence[int]]) -> Tuple[int, str]:
    """The background colour from a single frame, and how it was decided.

    A3's rule, restated with its verdict returned rather than implied:

        if every cell on the outer ring carries the same colour, that colour is
        structure, not background; the background is the commonest colour among
        the cells that are left.

    The assumption is a solid frame around the level.  Both `worldgen` grids have
    one (`WALL` on the whole border by construction), A3's two levels have one,
    and ARC grids very often do; a level that does not falls through to the plain
    count, which is the answer A0's one-frame baseline would give anyway.

    Returning the route as well as the answer is new here and it is not
    decoration: on the fallback path this derivation is a guess, and a
    provenance record that cannot distinguish a guess from a deduction is a
    provenance record that launders one into the other.
    """
    height, width = len(frame), len(frame[0])
    border = [frame[0][c] for c in range(width)]
    border += [frame[height - 1][c] for c in range(width)]
    border += [frame[r][0] for r in range(height)]
    border += [frame[r][width - 1] for r in range(height)]

    counts: Counter = Counter()
    excluded: Optional[int] = None
    route = "plain_count"
    if len(set(border)) == 1:
        excluded = border[0]
        route = "border_excluded"
    for row in frame:
        for value in row:
            if value != excluded:
                counts[value] += 1
    if not counts:                       # a frame that is nothing but border
        counts[border[0]] = 1
        route = "border_only"
    best = min(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return best[0], route


# ------------------------------------------------------------------- preflight

def preflight(frame: Sequence[Sequence[int]], requires: Dict[str, object],
              constants: Dict[str, Sequence[int]]) -> Dict[str, object]:
    """Can this pack be carried onto this frame at all?  Answered before acting.

    Four checks, in the order a failure is cheapest to explain:

    1. every declared object occupies **exactly one** cell of its colour set;
    2. every landmark the domain declares has a supplied coordinate, and every
       supplied coordinate is on the grid;
    3. `goal_cell` is supplied when the domain has no `goal:` section — without
       it `bind_goal` raises and three of the four backends emit a predictor that
       can never win (D-A3-004);
    4. guard colours the frame does not carry are **noted**, not refused.

    Check 1 is where a *wrong* carried domain dies for free.  Check 4 is where a
    *right* one survives a level that exercises less of it.
    """
    height, width = len(frame), len(frame[0])
    present: Counter = Counter()
    for row in frame:
        present.update(row)

    refusals: List[str] = []
    objects_found: Dict[str, Dict[str, object]] = {}

    for spec in requires.get("objects", []):
        name = str(spec["name"])
        colours = [int(c) for c in spec.get("colours", [])]
        cells = [(r, c) for r in range(height) for c in range(width)
                 if frame[r][c] in colours]
        objects_found[name] = {
            "colours": colours,
            "cells": [list(c) for c in cells],
            "count": len(cells),
        }
        if len(cells) == 1:
            continue
        if not cells:
            refusals.append(
                "%s is declared by the manual with colours %r and no cell of the "
                "frame carries any of them" % (name, colours))
        else:
            refusals.append(
                "%s is declared once and %d cells carry its colours %r (%s); "
                "carrypack v1 carries one instance per word-table name"
                % (name, len(cells), colours,
                   ", ".join(str(c) for c in cells)))

    for landmark in requires.get("landmarks", []):
        value = constants.get(landmark)
        if value is None:
            refusals.append("the manual names landmark %r and no coordinate was "
                            "supplied for it" % landmark)
        elif not (0 <= int(value[0]) < height and 0 <= int(value[1]) < width):
            refusals.append("landmark %r is supplied as %r, off a %dx%d grid"
                            % (landmark, list(value), height, width))

    if not requires.get("goal_in_domain", False):
        goal = constants.get("goal_cell")
        if goal is None:
            refusals.append(
                "the domain has no `goal:` section, so the goal cell is problem "
                "data and must be supplied (D-A3-004)")
        elif not (0 <= int(goal[0]) < height and 0 <= int(goal[1]) < width):
            refusals.append("goal_cell %r is off a %dx%d grid"
                            % (list(goal), height, width))

    guard_colours = [int(c) for c in requires.get("guard_colours", [])]
    dormant = sorted(c for c in guard_colours if present.get(c, 0) == 0)

    return {
        "green": not refusals,
        "refusals": refusals,
        "objects": objects_found,
        "grid": [height, width],
        "colours_present": {str(k): v for k, v in sorted(present.items())},
        "guard_colours": sorted(set(guard_colours)),
        "dormant_guard_colours": dormant,
        "dormant_rules": sorted(
            ctx["rule"] for ctx in requires.get("guard_contexts", [])
            if ctx.get("guard_colours")
            and any(int(c) in dormant for c in ctx["guard_colours"])),
        "note": (
            "a dormant guard colour is not a defect: the level does not present "
            "that mechanism and the rules guarding on it never fire.  A missing "
            "*object* is a refusal, because the manual is then about a world "
            "this level is not."),
    }


# ---------------------------------------------------------------- the rebuilder

def rebuild_from_frame(frame_path: str, requires: Dict[str, object],
                       constants: Dict[str, Sequence[int]], name: str
                       ) -> Tuple[Problem, Dict[str, object]]:
    """One frame + a pack's `requires` + the level constants -> a `Problem`.

    Derived from the pixels: `height`, `width`, `background`, `board`, `objects`,
    `arena`.  Supplied: `name`, `goal_cell`, `landmarks`.  The split is the same
    six-and-three A3 reported, and it is recorded field by field rather than
    described, so the size of the concession stays a number in a table.
    """
    frame = read_frame(frame_path)
    verdict = preflight(frame, requires, constants)
    if not verdict["green"]:
        raise RebuildRefusal(verdict)

    height, width = len(frame), len(frame[0])
    background, bg_route = background_from_frame(frame)

    objects: List[ObjectInstance] = []
    for spec in sorted(requires.get("objects", []), key=lambda s: s["name"]):
        name_ = str(spec["name"])
        (r, c), = [tuple(cell) for cell in verdict["objects"][name_]["cells"]]
        objects.append(ObjectInstance(name=name_, pos=(r, c), color=frame[r][c]))
    # A0's ordering; the generators index objects positionally in places, so it
    # is part of the object's identity rather than a presentation choice.
    objects.sort(key=lambda o: o.name)

    occupied = {o.pos for o in objects}
    board = [
        [background if (r, c) in occupied else frame[r][c] for c in range(width)]
        for r in range(height)
    ]
    arena = sorted((r, c) for r in range(height) for c in range(width)
                   if board[r][c] == background)

    landmarks = {lm: tuple(int(v) for v in constants[lm])
                 for lm in requires.get("landmarks", [])}
    goal = constants.get("goal_cell")

    problem = Problem(
        name=name,
        height=height,
        width=width,
        background=background,
        board=board,
        objects=objects,
        goal_cell=tuple(int(v) for v in goal) if goal is not None else None,
        landmarks=landmarks,
        arena=arena,
    )

    fields = {f: "derived_from_frame" for f in PROBLEM_FIELDS}
    fields["name"] = "supplied"
    fields["landmarks"] = "supplied" if landmarks else "n/a (the domain names none)"
    fields["goal_cell"] = ("in the domain" if requires.get("goal_in_domain")
                           else "supplied")
    derived = sum(1 for v in fields.values() if v == "derived_from_frame")

    provenance = {
        "route": "frame",
        "pack_requires_digest": {
            "objects": [o["name"] for o in requires.get("objects", [])],
            "landmarks": list(requires.get("landmarks", [])),
            "guard_colours": list(requires.get("guard_colours", [])),
        },
        "source": os.path.relpath(frame_path, ROOT).replace(os.sep, "/"),
        "inputs_read": {"frames": 1, "actions": 0},
        "fields": fields,
        "derived_fields": derived,
        "supplied_fields": len(PROBLEM_FIELDS) - derived,
        "background_route": bg_route,
        "supplied_values": {
            "name": problem.name,
            "goal_cell": list(problem.goal_cell) if problem.goal_cell else None,
            "landmarks": {k: list(v) for k, v in sorted(landmarks.items())},
        },
        "counts": {
            "grid": [height, width],
            "background": background,
            "objects": len(objects),
            "object_names": [o.name for o in objects],
            "object_cells": {o.name: list(o.pos) for o in objects},
            "arena_cells": len(arena),
            "board_non_background_cells": sum(
                1 for row in board for v in row if v != background),
        },
        "preflight": verdict,
    }
    return problem, provenance


# --------------------------------------------------------------- the comparison

def compare_problems(a: Problem, b: Problem) -> Dict[str, object]:
    """Per-field equality between two `Problem`s, as data.

    A3's `compare_problems`, generalised only in that it no longer assumes a
    landmark dictionary is non-empty.  Not `a == b`: the dataclass compares fine,
    but a boolean is useless when it is `False`, and what the check says when it
    fails is the whole reason it exists.
    """
    def norm(prob: Problem, field: str):
        value = getattr(prob, field)
        if field == "objects":
            return [(o.name, tuple(o.pos), o.color, o.present) for o in value]
        if field == "landmarks":
            return {k: tuple(v) for k, v in sorted((value or {}).items())}
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
            row["a"], row["b"] = left, right
        fields[field] = row
    differing = sorted(f for f, row in fields.items() if not row["equal"])
    return {"equal": not differing, "fields": fields,
            "differing_fields": differing}


def write_json(path: str, payload: Dict[str, object]) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True,
                                ensure_ascii=False) + "\n")
    return path
