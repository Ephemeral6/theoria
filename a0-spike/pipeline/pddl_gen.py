"""Compile the A0 level into PDDL -- the planning form of the same theory.

This is the "same theory, several forms" obligation in miniature: the rules the
miner induced and the rules encoded here have to be the same rules, or planning
is answering a question about a different world. `walk` and `push2` below are
transcriptions of the mined guards:

    walk   act==D and ahead_free(D)
    push2  act==D and ahead_is_box(D) and box_beyond_free(D)

`adj` is static -- no action adds or deletes it -- so the grounder's static
filtering reduces `push2` from |cells|^4 instances to the collinear quadruples
that actually exist. Without that the 7x7 board grounds to millions.
"""

from typing import Dict, List, Sequence, Tuple

Cell = Tuple[int, int]

DIRECTION_VECTORS: Dict[str, Cell] = {
    "up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1),
}

DOMAIN = """;; A0 sokoban-2: a push slides the box two cells.
;; Transcribed from the mined rules; see pipeline/stages.py for their provenance.
(define (domain sokoban2)
  (:requirements :strips :typing :negative-preconditions)
  (:types cell dir)
  (:predicates
    (player-at ?c - cell)
    (box-at ?c - cell)
    (wall ?c - cell)
    (adj ?from - cell ?to - cell ?d - dir))

  ;; walk: act==D and ahead_free(D)
  (:action walk
    :parameters (?from - cell ?to - cell ?d - dir)
    :precondition (and (player-at ?from) (adj ?from ?to ?d)
                       (not (wall ?to)) (not (box-at ?to)))
    :effect (and (player-at ?to) (not (player-at ?from))))

  ;; push2: act==D and ahead_is_box(D) and box_beyond_free(D)
  ;; the box crosses ?over and lands on ?land; the player takes its old cell
  (:action push2
    :parameters (?p - cell ?b - cell ?over - cell ?land - cell ?d - dir)
    :precondition (and (player-at ?p) (adj ?p ?b ?d) (box-at ?b)
                       (adj ?b ?over ?d) (adj ?over ?land ?d)
                       (not (wall ?over)) (not (wall ?land)))
    :effect (and (box-at ?land) (not (box-at ?b))
                 (player-at ?b) (not (player-at ?p)))))
"""


def cell_name(cell: Cell) -> str:
    return "c%d_%d" % cell


def generate_problem(name: str, height: int, width: int, walls: Sequence[Cell],
                     player: Cell, box: Cell, target: Cell) -> str:
    cells = [(r, c) for r in range(height) for c in range(width)]
    lines: List[str] = []
    lines.append("(define (problem %s)" % name)
    lines.append("  (:domain sokoban2)")
    lines.append("  (:objects")
    lines.append("    " + " ".join(cell_name(c) for c in cells) + " - cell")
    lines.append("    " + " ".join(sorted(DIRECTION_VECTORS)) + " - dir)")
    lines.append("  (:init")
    for direction, (dr, dc) in sorted(DIRECTION_VECTORS.items()):
        for (r, c) in cells:
            nxt = (r + dr, c + dc)
            if 0 <= nxt[0] < height and 0 <= nxt[1] < width:
                lines.append("    (adj %s %s %s)" % (cell_name((r, c)), cell_name(nxt), direction))
    for wall in sorted(walls):
        lines.append("    (wall %s)" % cell_name(wall))
    lines.append("    (player-at %s)" % cell_name(player))
    lines.append("    (box-at %s)" % cell_name(box))
    lines.append("  )")
    lines.append("  (:goal (box-at %s)))" % cell_name(target))
    return "\n".join(lines) + "\n"


def write_files(directory: str, name: str, height: int, width: int,
                walls: Sequence[Cell], player: Cell, box: Cell,
                target: Cell) -> Tuple[str, str]:
    import os

    os.makedirs(directory, exist_ok=True)
    domain_path = os.path.join(directory, "domain.pddl")
    problem_path = os.path.join(directory, "problem_%s.pddl" % name)
    with open(domain_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(DOMAIN)
    with open(problem_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(generate_problem(name, height, width, walls, player, box, target))
    return domain_path, problem_path
