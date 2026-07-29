"""Is the zero an artefact of `MAX_PATTERN = 2`?

`engines/deadlock_carver/carve.py` caps patterns at two atoms and says why: two
is the width h^2 mutexes can reason about.  So the measured result -- "no state
the theorems detect is missed by the delete relaxation" -- might be a fact about
the *cap* rather than about deadlock theorems.  The textbook sokoban deadlock
that needs more width is the 2x2 block of four boxes in the open, which no pair
of atoms describes.

This module runs the carver's own proof rule, `carve.prove`, at widths 3 and 4
on patterns chosen geometrically (boxes packed into a 2x2 or a 2x3 window), and
asks the same question of whatever it proves:

  * is any state a wide theorem covers **alive** in the delete relaxation?
    (that would be the counterexample the review is hunting)
  * is any state a wide theorem covers **not truly dead**?  (that would mean the
    rule does not survive the widening, which is the thing the cap protects
    against -- a finding about the carver, not about the planner)

Nothing here modifies the carver.  `prove` is called with a longer tuple, which
it already accepts.

    python -m attacks.wider four-block
    python -m attacks.wider three-b
"""

import json
import os
import sys
from collections import deque
from itertools import combinations, permutations
from typing import Dict, List, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if RIG not in sys.path:
    sys.path.insert(0, RIG)

from audit.claim import relaxed_reachable_goal                  # noqa: E402
from engines.deadlock_carver.carve import Task, carve, prove, pruner  # noqa: E402
from engines.fd_adapter import pddl, search                     # noqa: E402
from fixtures import sokoban                                    # noqa: E402

from attacks.relaxation_sweep import collect, level, load, open_rows  # noqa: E402


def levels() -> Dict[str, sokoban.Level]:
    out = {}
    # Four boxes on a 4x5 interior.  The textbook sokoban deadlock -- a 2x2
    # block of boxes in the open -- needs a width-4 pattern, and the board is
    # five columns wide rather than four because in a 4x4 interior every push
    # that would complete the centre block needs a pusher cell that is a wall,
    # so the block is not reachable and the experiment would measure nothing.
    # Here it is one push away from the initial state: player to (3,5), push b4
    # left from (3,4) onto (3,3).
    out["four-block"] = level("four-block", open_rows(4, 5), (4, 5),
                              [("b1", (2, 2)), ("b2", (2, 3)),
                               ("b3", (3, 2)), ("b4", (3, 4))],
                              [("b1", (4, 2)), ("b2", (4, 3)),
                               ("b3", (4, 4)), ("b4", (1, 4))])
    # Three boxes, a smaller board, so width 3 is cheap to enumerate.
    out["three-b"] = level("three-b", open_rows(3, 4), (3, 4),
                           [("b1", (1, 2)), ("b2", (2, 2)), ("b3", (2, 3))],
                           [("b1", (3, 3)), ("b2", (1, 4)), ("b3", (3, 1))])
    out["three-c"] = level("three-c", open_rows(4, 4), (1, 1),
                           [("b1", (2, 2)), ("b2", (2, 3)), ("b3", (3, 2))],
                           [("b1", (4, 2)), ("b2", (4, 3)), ("b3", (1, 2))])
    return out


def compact_cell_sets(cells: Sequence[Tuple[int, int]], width: int,
                      window: Tuple[int, int]) -> List[Tuple[Tuple[int, int], ...]]:
    """Cell sets that fit in a `window` bounding box -- the packed ones.

    Enumerating every width-4 subset of 16 cells is 1820 sets times every box
    assignment; restricting to packed sets is the difference between an
    experiment and an afternoon, and packed is where sokoban deadlocks live.
    """
    out = []
    for chosen in combinations(sorted(cells), width):
        rows = [r for r, _ in chosen]
        cols = [c for _, c in chosen]
        if max(rows) - min(rows) < window[0] and max(cols) - min(cols) < window[1]:
            out.append(chosen)
    return out


def wide_theorems(task: Task, level: sokoban.Level, width: int,
                  window: Tuple[int, int]) -> List:
    boxes = level.box_names()
    if len(boxes) < width:
        return []
    cells = level.floors()
    found = []
    for cell_set in compact_cell_sets(cells, width, window):
        for chosen_boxes in permutations(boxes, width):
            pattern = tuple(("at", b, level.cell_name(c))
                            for b, c in zip(chosen_boxes, cell_set))
            theorem = prove(task, pattern)
            if theorem is not None:
                found.append(theorem)
    return found


def run(name: str) -> Dict[str, object]:
    lvl = levels()[name]
    domain, problem, _text = load(lvl)
    task = Task.build(domain, problem)
    narrow = carve(task)
    narrow_dead = pruner(narrow)

    grounded = pddl.ground_actions(domain, problem)
    actions, initial, _ok = search.strip_static(domain, problem, grounded)
    static = pddl.static_predicates(domain)
    states = collect(domain, problem, actions, initial, static, False, 200000)
    index = {s: i for i, s in enumerate(states)}

    # Truly dead, over the real relation -- needed to check the widened rule is
    # still sound before asking whether it is useful.
    backward: List[List[int]] = [[] for _ in states]
    goals = []
    for i, state in enumerate(states):
        if search.is_goal(problem, state, static):
            goals.append(i)
            continue
        for action in actions:
            if search.applicable(action, state):
                j = index.get(search.successor(action, state))
                if j is not None:
                    backward[j].append(i)
    alive = set(goals)
    queue = deque(goals)
    while queue:
        i = queue.popleft()
        for j in backward[i]:
            if j not in alive:
                alive.add(j)
                queue.append(j)
    truly_dead = {i for i in range(len(states)) if i not in alive}

    wide: List = []
    for width, window in ((3, (2, 3)), (3, (3, 2)), (4, (2, 2)), (4, (2, 3)), (4, (3, 2))):
        wide.extend(wide_theorems(task, lvl, width, window))
    seen = set()
    unique = []
    for theorem in wide:
        key = tuple(sorted(theorem.pattern))
        if key not in seen:
            seen.add(key)
            unique.append(theorem)

    narrow_set = {i for i, s in enumerate(states) if narrow_dead(s)}
    wide_only: Dict[int, List] = {}
    for i, state in enumerate(states):
        if i in narrow_set:
            continue
        covering = [t for t in unique if t.covers(state)]
        if covering:
            wide_only[i] = covering

    # The relaxation is only asked about the delta: states the widened rule
    # detects and the shipped rule does not.  That is the whole prize on offer.
    relaxed_alive = [
        i for i in sorted(wide_only)
        if relaxed_reachable_goal(actions, states[i], problem, static)
    ]
    unsound = [i for i in sorted(wide_only) if i not in truly_dead]

    out = {
        "instance": name,
        "boxes": len(lvl.boxes),
        "n_reachable": len(states),
        "n_narrow_theorems": len(narrow),
        "n_wide_theorems": len(unique),
        "wide_widths": sorted({t.size for t in unique}),
        "wide_kinds": sorted({t.kind for t in unique}),
        "n_narrow_dead": len(narrow_set),
        "n_wide_only_dead": len(wide_only),
        "n_truly_dead": len(truly_dead),
        "n_wide_only_relaxation_alive": len(relaxed_alive),
        "n_wide_only_not_truly_dead": len(unsound),
        "example_wide_theorems": [t.rendering() for t in unique[:6]],
        "counterexample_states": [sorted(states[i]) for i in relaxed_alive[:5]],
        "unsound_states": [sorted(states[i]) for i in unsound[:5]],
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return out


if __name__ == "__main__":
    names = sys.argv[1:] or ["three-b", "three-c", "four-block"]
    results = [run(n) for n in names]
    path = os.path.join(HERE, "wider.json")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(results, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("-> %s" % path)
