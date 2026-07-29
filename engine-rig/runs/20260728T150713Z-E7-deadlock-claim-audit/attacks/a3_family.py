"""Attack 3 -- is `far` simply the wrong instance family?

E2 measured one construction (`open4far`, scaled) and one unsolvable one
(`ringstuck`, scaled).  If the theorems ever pay on an admissible heuristic, the
cheapest way to find out is to look at a lot of geometries rather than to argue
about one.

Two halves:

* `HAND` -- geometries picked because they stress something `far` does not:
  interior walls, 1-wide corridors, three and four boxes, tight goals, and
  instances that are unsolvable for an *interaction* reason rather than because a
  box sits in a corner.  The last group matters most: FD's translator settles
  `ringstuck` by relaxed reachability and never searches, so those rows in E2 are
  vacuous.  An interaction deadlock is invisible to the delete relaxation, so the
  planner has to search, and that is where a proved pair deadlock could pay.
* a randomised sweep over small boards with random interior walls, box counts and
  goals, so the answer does not depend on which geometries occurred to me.

Levels are written in ASCII:  `#` wall, `.` floor, `@` player, digits `1..9` a
box's start, letters `a..i` the matching box's goal (`a` goes with `1`).  A cell
that is both is written with the digit and listed in `also_goal`.
"""

import os
import random
import sys
import textwrap
import traceback
from typing import Dict, List, Optional, Tuple

from lens import brief, dump, measure_level          # noqa: E402
from fixtures import sokoban                         # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work", "a3")
LOGS = os.path.join(HERE, "logs", "a3")

DIGITS = "123456789"
LETTERS = "abcdefghi"


def parse(name: str, art: str) -> sokoban.Level:
    # `dedent` first, and then refuse any space that survives.  Without it the
    # source indentation becomes *floor*, which quietly bolts a disconnected
    # strip of open cells onto the left of every board -- it happened, the
    # instances were still well-formed sokoban and the numbers were still real,
    # but the picture in the write-up was not the instance that was measured.
    rows = [line for line in textwrap.dedent(art.strip("\n")).splitlines() if line]
    if any(" " in row for row in rows):
        raise ValueError("%s: a space survived dedent; the art is misaligned" % name)
    width = max(len(r) for r in rows)
    rows = [r.ljust(width, "#") for r in rows]
    grid: List[str] = []
    player = None
    boxes: Dict[str, Tuple[int, int]] = {}
    goals: Dict[str, Tuple[int, int]] = {}
    for r, line in enumerate(rows):
        out = []
        for c, ch in enumerate(line):
            if ch == "#":
                out.append("#")
                continue
            out.append(".")
            if ch == "@":
                player = (r, c)
            elif ch in DIGITS:
                boxes["b%s" % ch] = (r, c)
            elif ch in LETTERS:
                goals["b%s" % DIGITS[LETTERS.index(ch)]] = (r, c)
        grid.append("".join(out))
    if player is None:
        raise ValueError("%s: no @" % name)
    if set(boxes) != set(goals):
        raise ValueError("%s: boxes %s goals %s" % (name, sorted(boxes), sorted(goals)))
    return sokoban.Level(
        name=name, grid=tuple(grid), player=player,
        boxes=tuple(sorted(boxes.items())), goals=tuple(sorted(goals.items())),
        optimum=None, path="",
    )


# --------------------------------------------------------------------- by hand

HAND = {
    # A 1-wide passage between two halves, with a box on each side that has to
    # end up on the other.  The delete relaxation never deletes `clear`, so it
    # does not notice that the two boxes are in each other's way.
    "swap-passage": """
    #######
    #.....#
    #.1.b.#
    ##.#.##
    #.a.2.#
    #..@..#
    #######
    """,
    # The same board with a disconnected 4-wide strip of open cells bolted on.
    # This is not a decoration: the first run of this sweep produced it by
    # accident (the parser read the source indentation as floor), it is the
    # instance the first `swap-passage` numbers were measured on, and it is kept
    # so those numbers stay reproducible next to the clean board's.
    "swap-passage-strip": """
    ....#######
    ....#.....#
    ....#.1.b.#
    ....##.#.##
    ....#.a.2.#
    ....#..@..#
    ....#######
    ....#######
    """,
    # Same idea, one room, a pillar in the middle.
    "pillar": """
    ######
    #..1b#
    #.##.#
    #a2..#
    #.@..#
    ######
    """,
    # Two rooms joined by a single door cell, and the two boxes have to trade
    # rooms through it.
    "door-swap": """
    ########
    #..#...#
    #.1..2.#
    #.b#a..#
    #..#..@#
    ########
    """,
    # Three boxes in an open room, each goal on the far side of the others.
    "three-far": """
    #######
    #.....#
    #.1.2.#
    #..3..#
    #.b.c.#
    #.a.@.#
    #######
    """,
    # Four boxes, tight room -- the pair deadlocks multiply.
    "four-tight": """
    #######
    #.....#
    #.1.2.#
    #.ab..#
    #.dc..#
    #.4.3@#
    #######
    """,
    # A wall stub in the interior: cells beside it are dead for a box without
    # being board corners, so the theorem set is not just the four corners.
    "stub-wall": """
    #######
    #.....#
    #.1##.#
    #..#..#
    #.a...#
    #..@..#
    #######
    """,
    # Corridors meeting at a T.  A box in a 1-wide corridor can be pushed along
    # it and never turned, so most of the board is dead for a box.
    "tee": """
    #######
    #..a..#
    ###.###
    ###1###
    #.....#
    ###@###
    #######
    """,
    # A room whose goal cells sit behind the boxes that have to reach them.
    "behind": """
    ######
    #....#
    #.12.#
    #.ba.#
    #.@..#
    ######
    """,
    # An 8x8 open room, two boxes, goals swapped -- `far8` with the player
    # starting in the middle rather than the corner, to move the search's shape.
    "far8-midplayer": """
    ##########
    #........#
    #.1......#
    #..2.....#
    #...@....#
    #........#
    #........#
    #.b......#
    #a.......#
    ##########
    """,
    # Three boxes on a bigger board -- more room for the search to wander into a
    # dead region before an admissible heuristic notices.
    "three-far8": """
    ##########
    #........#
    #.1.2....#
    #...3....#
    #........#
    #........#
    #..b.c...#
    #a.......#
    #.......@#
    ##########
    """,
}


# ------------------------------------------------------------------- at random

def random_level(rng: random.Random, index: int) -> Optional[sokoban.Level]:
    side = rng.choice((4, 4, 5, 5, 6))
    n_walls = rng.choice((0, 1, 1, 2, 2, 3, 4))
    n_boxes = rng.choice((2, 2, 2, 3, 3, 4))
    cells = [(r, c) for r in range(1, side + 1) for c in range(1, side + 1)]
    walls = set(rng.sample(cells, min(n_walls, len(cells) - 2 * n_boxes - 1)))
    floor = [cell for cell in cells if cell not in walls]
    if len(floor) < 2 * n_boxes + 1:
        return None
    grid = ["#" * (side + 2)]
    for r in range(1, side + 1):
        grid.append("#" + "".join(
            "#" if (r, c) in walls else "." for c in range(1, side + 1)) + "#")
    grid.append("#" * (side + 2))

    picks = rng.sample(floor, 2 * n_boxes + 1)
    player = picks[0]
    boxes = tuple(("b%d" % (i + 1), picks[1 + i]) for i in range(n_boxes))
    goals = tuple(("b%d" % (i + 1), picks[1 + n_boxes + i]) for i in range(n_boxes))
    return sokoban.Level(name="rnd%04d" % index, grid=tuple(grid), player=player,
                         boxes=boxes, goals=goals, optimum=None, path="")


# ------------------------------------------------------------------- the sweep

def dividends(entry) -> List[Tuple[str, str, int, int]]:
    out = []
    for r in entry.get("rows", ()):
        if "skipped" in r:
            continue
        b, a = r["before"]["expanded"], r["after"]["expanded"]
        if b is None or a is None or r["after"]["error"] or r["before"]["error"]:
            continue
        out.append((r["guard"], r["rung"], b, a))
    return out


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "hand"
    guards = ("singleton", "indexed")
    results = []
    hits = []

    if which == "hand":
        levels = [parse(name, art) for name, art in sorted(HAND.items())]
        out_path = os.path.join(HERE, "a3_hand.json")
    else:
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        seed = int(sys.argv[3]) if len(sys.argv) > 3 else 20260728
        rng = random.Random(seed)
        levels = []
        index = 0
        while len(levels) < count:
            level = random_level(rng, index)
            index += 1
            if level is not None:
                levels.append(level)
        out_path = os.path.join(HERE, "a3_random.json")

    for level in levels:
        try:
            entry = measure_level(level, os.path.join(WORK, level.name), LOGS,
                                  guards=guards, timeout=600, repeats=1)
        except Exception as exc:
            print("== %s  FAILED: %s" % (level.name, exc))
            traceback.print_exc()
            results.append({"instance": level.name, "failed": str(exc)})
            continue
        entry["art"] = list(level.grid)
        brief(entry)
        results.append(entry)
        for guard, rung, before, after in dividends(entry):
            if rung != "blind" and after < before:
                hits.append((level.name, guard, rung, before, after))
                print("   *** HIT %s %s %s: %d -> %d" % (level.name, guard, rung, before, after))
        dump({"results": results, "hits": hits}, out_path)

    print()
    print("HITS on an admissible heuristic (%d):" % len(hits))
    for hit in hits:
        print("   %s" % (hit,))


if __name__ == "__main__":
    main()
