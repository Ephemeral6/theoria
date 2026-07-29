"""Sokoban without `clear`: the same world, encoded with a negative precondition.

The claim's `relaxation_dead` set is computed by `audit.claim.relaxed_reachable_goal`
over a domain whose only "this cell is free" fact is the **positive** fluent
`clear`.  That matters more than it looks:

  * a positive `clear` precondition survives into the delete relaxation, so a
    cell that is not clear in the state stays un-clear until the *player* leaves
    it -- which is why the relaxation on this encoding is strong enough to see
    box-against-box blocking at all;
  * `audit.claim.relaxed_reachable_goal` **ignores negative preconditions**
    (its docstring says the domain has none, and it is right about that domain).

So the honest question is whether the equality is a property of sokoban or a
property of this encoding of sokoban.  This module writes the same world with
`occupied` and `(not (occupied ?c))`, which is logically the complement of
`clear` and gives a *bit-for-bit isomorphic* state space and transition
relation -- and then the same three sets are measured again.

Nothing here is imported by the rig.
"""

import os
from typing import List

from fixtures import sokoban

DOMAIN = """;; Sokoban, re-encoded with `occupied` and a negative precondition.
;; Written by attacks/noclear.py for the E7 adversarial review -- not a fixture.
;;
;; `occupied ?c` is the exact complement of the committed domain's `clear ?c`,
;; so the grounded transition relation is isomorphic to it: the same states, the
;; same actions, the same plans.  What differs is only where the "free cell"
;; requirement sits -- in a negative precondition rather than a positive one.
(define (domain sokoban-nc)
  (:requirements :strips :typing :negative-preconditions)
  (:types cell box dir)
  (:predicates
    (at-player ?c - cell)
    (at ?b - box ?c - cell)
    (occupied ?c - cell)
    (adj ?from - cell ?to - cell ?d - dir))

  (:action move
    :parameters (?from - cell ?to - cell ?d - dir)
    :precondition (and (at-player ?from) (not (occupied ?to)) (adj ?from ?to ?d))
    :effect (and (at-player ?to) (not (at-player ?from))
                 (occupied ?to) (not (occupied ?from))))

  (:action push
    :parameters (?p - cell ?from - cell ?to - cell ?b - box ?d - dir)
    :precondition (and (at-player ?p) (at ?b ?from) (not (occupied ?to))
                       (adj ?p ?from ?d) (adj ?from ?to ?d))
    :effect (and (at-player ?from) (not (at-player ?p)) (not (occupied ?p))
                 (at ?b ?to) (not (at ?b ?from))
                 (occupied ?to) (occupied ?from))))
"""


def problem_text(level: sokoban.Level) -> str:
    """`level.problem_text()`, with `clear` replaced by its complement."""
    cells = level.floors()
    names = [level.cell_name(cell) for cell in cells]
    occupied = level.occupied()

    adjacency = []
    for cell in cells:
        for direction in sokoban.DIRECTIONS:
            target = level.neighbour(cell, direction)
            if target is not None:
                adjacency.append(
                    "    (adj %s %s %s)"
                    % (level.cell_name(cell), level.cell_name(target), direction)
                )

    init = ["    (at-player %s)" % level.cell_name(level.player)]
    init += ["    (at %s %s)" % (name, level.cell_name(cell))
             for name, cell in sorted(level.boxes)]
    init += ["    (occupied %s)" % level.cell_name(cell) for cell in cells
             if cell in occupied]

    goal = " ".join("(at %s %s)" % (name, level.cell_name(cell))
                    for name, cell in sorted(level.goals))
    picture = "\n".join(";;   " + row for row in level.grid)
    return (
        ";; Sokoban level %s, `occupied` encoding. attacks/noclear.py -- not a fixture.\n"
        ";;\n%s\n;;\n"
        "(define (problem sokoban-nc-%s)\n"
        "  (:domain sokoban-nc)\n"
        "  (:objects\n"
        "    %s - cell\n"
        "    %s - box\n"
        "    %s - dir)\n"
        "  (:init\n%s\n%s)\n"
        "  (:goal (and %s)))\n"
        % (level.name, picture, level.name,
           " ".join(names), " ".join(level.box_names()),
           " ".join(sokoban.DIRECTIONS),
           "\n".join(init), "\n".join(adjacency), goal)
    )


def write_domain(directory: str) -> str:
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, "sokoban_nc_domain.pddl")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(DOMAIN)
    return path


class NcLevel(sokoban.Level):
    """A `Level` whose `problem_text` renders the `occupied` encoding.

    Subclassed rather than parameterised so every consumer in `attacks/` --
    including `audit.claim._problem_with_initial`, which is handed the rendered
    text -- keeps working unchanged.
    """

    def problem_text(self) -> str:                       # type: ignore[override]
        return problem_text(self)


def as_nc(level: sokoban.Level) -> "NcLevel":
    return NcLevel(name=level.name + "-nc", grid=level.grid, player=level.player,
                   boxes=level.boxes, goals=level.goals, optimum=None, path="")
