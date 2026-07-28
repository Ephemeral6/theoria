"""Generate the rule sets and certificates under `recheck/cases/`.

Written rather than hand-typed because a 148-entry neighbour table typed by
hand is a transcription bug waiting to be blamed on the rechecker.  The
generator is data-driven: the boards are literals, everything else follows from
them.  Output is byte-stable -- `python -m recheck.build_cases --check` fails if
a committed case has drifted from what the generator says it should be.

Four worlds:

* **peg4** -- Fixture C, two starts.  `0111` is the unsolvable configuration
  `ic3_pdr` returns an invariant for (STATUS.md, M9); `1101` is the solvable one
  it correctly refuses, and is here so a forged invariant has somewhere to fail.
* **a2-holed** -- the A2 exhibit's manual: the 9x9 pushing world with the
  teleport rule deleted.  This is the rule set the Lean file
  `cold-start-a2/theory/generated_holed/theory.lean` proves `unsolvable` over,
  axiom-free.
* **a2-world** -- the same world *with* the teleport rule, i.e. A2's control
  manual, which its 18-action refutation established is the world's own rule
  set.  The two files differ by one rule and one event, exactly as
  `theory.dsl` and `theory_holed.dsl` do.
* **sokoban** -- Fixture D's `ringstuck` and `open4far`, multi-valued rather
  than grounded-STRIPS, so the deadlock patterns `deadlock_carver` emits can be
  rechecked against rules nobody grounded for them.

The boards are transcribed from the fixtures and from
`cold-start-a2/theory/generated_holed/theory.py`.  Transcription is the risk, so
it is checked twice and neither check is this file: `tests/test_recheck_a2.py`
replays A2's own recorded 18-action refutation episode through the generated
`a2-world` rules frame by frame, and compares the generated `a2-holed`
transition relation against the 592-line `step` table inside the Lean file Lean
itself accepted.
"""

import argparse
import hashlib
import json
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

from recheck.ruleset import canonical_text

CASES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cases")

RULESET_SCHEMA = "engine-rig/recheck/ruleset-v1"
CERTIFICATE_SCHEMA = "engine-rig/recheck/certificate-v1"

Cell = Tuple[int, int]


def cell_name(cell: Cell) -> str:
    return "%d,%d" % cell


def lit(value) -> list:
    return ["lit", value]


def var(name: str) -> list:
    return ["var", name]


def eq(left, right) -> list:
    return ["=", left, right]


def dump(path: str, payload: dict) -> str:
    text = serialise(payload)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return text


# ============================================================== peg solitaire

PEG_N = 4
PEG_GOAL = "0100"


def peg_moves() -> List[Tuple[int, int, int]]:
    """Every jump the geometry allows, as (src, over, dst)."""
    out = []
    for i in range(PEG_N):
        for step in (1, -1):
            over, dst = i + step, i + 2 * step
            if 0 <= dst < PEG_N:
                out.append((i, over, dst))
    return sorted(out, key=lambda m: (m[0], m[2]))


def peg_ruleset(start: str) -> dict:
    moves = peg_moves()
    return {
        "schema": RULESET_SCHEMA,
        "name": "peg4-%s" % start,
        "comment": "Fixture C, 1D peg solitaire on four positions, started at "
                   "%s. A move jumps a peg over a neighbouring peg into an "
                   "empty hole and removes the jumped peg." % start,
        "provenance": {
            "world": "engine-rig/fixtures/peg4.py",
            "goal": "exactly one peg, at position 1 (state %s)" % PEG_GOAL,
            "hand_verified": "peg4.py's docstring: 1110, 0111 and 1011 are "
                             "unsolvable; 1101 solves in 2 moves",
        },
        "variables": [
            {"name": "pos%d" % i, "domain": [0, 1],
             "comment": "1 if position %d holds a peg" % i}
            for i in range(PEG_N)
        ],
        "actions": ["jump(%d,%d,%d)" % move for move in moves],
        "init": {"pos%d" % i: int(start[i]) for i in range(PEG_N)},
        "goal": ["and"] + [
            eq(var("pos%d" % i), lit(int(PEG_GOAL[i]))) for i in range(PEG_N)
        ],
        "rules": [
            {
                "name": "jump_%d_%d_%d" % move,
                "action": "jump(%d,%d,%d)" % move,
                "guard": ["and",
                          eq(var("pos%d" % move[0]), lit(1)),
                          eq(var("pos%d" % move[1]), lit(1)),
                          eq(var("pos%d" % move[2]), lit(0))],
                "effects": {
                    "pos%d" % move[0]: lit(0),
                    "pos%d" % move[1]: lit(0),
                    "pos%d" % move[2]: lit(1),
                },
            }
            for move in moves
        ],
    }


def peg_ic3_certificate() -> dict:
    """`ic3_pdr`'s answer on 0111, transcribed clause by clause.

    STATUS.md, M9: `I(s) = (!pos1 | pos2) & (pos1 | !pos2)`.  Written here as
    the two clauses rather than as `pos1 == pos2`, so that what is rechecked is
    the shape the engine actually emitted.
    """
    return {
        "schema": CERTIFICATE_SCHEMA,
        "name": "peg4-0111-ic3-invariant",
        "kind": "inductive_invariant",
        "claim": "unsolvable",
        "produced_by": "engines/ic3_pdr (M9)",
        "comment": "(!pos1 | pos2) & (pos1 | !pos2) -- positions 1 and 2 always "
                   "hold the same thing.",
        "ruleset": {"name": "peg4-0111"},
        "predicate": ["and",
                      ["or", eq(var("pos1"), lit(0)), eq(var("pos2"), lit(1))],
                      ["or", eq(var("pos1"), lit(1)), eq(var("pos2"), lit(0))]],
    }


# ==================================================================== A2

# Transcribed from cold-start-a2/theory/generated_holed/theory.py (BOARD).
A2_BOARD: Tuple[Tuple[int, ...], ...] = (
    (1, 1, 1, 1, 1, 1, 1, 1, 1),
    (1, 0, 1, 0, 0, 1, 0, 0, 1),
    (1, 0, 0, 0, 0, 1, 0, 0, 1),
    (1, 0, 0, 0, 0, 1, 0, 0, 1),
    (1, 0, 0, 0, 0, 1, 0, 0, 1),
    (1, 0, 0, 0, 0, 1, 0, 0, 1),
    (1, 1, 0, 0, 0, 1, 0, 0, 1),
    (1, 0, 1, 1, 3, 1, 0, 0, 1),
    (1, 1, 1, 1, 1, 1, 1, 1, 1),
)

A2_DIRECTIONS: Dict[str, Cell] = {
    "up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1),
}
A2_BUTTON = (1, 1)
A2_BUTTON_COLOUR = 7
A2_BUTTON_PRESSED = 8
A2_CART_COLOUR = 6
A2_CART_START = (5, 1)
A2_DOOR = (6, 4)
A2_DOOR_COLOUR = 5
A2_GOAL = (2, 7)
A2_PORTAL_EXIT = (7, 6)
A2_PORTAL_COLOUR = 3
A2_BACKGROUND = 0


def a2_arena() -> List[Cell]:
    return [(r, c) for r in range(9) for c in range(9) if A2_BOARD[r][c] == A2_BACKGROUND]


def a2_ruleset(with_teleport: bool) -> dict:
    arena = a2_arena()
    neighbours = []
    for cell in arena:
        for name in sorted(A2_DIRECTIONS):
            dr, dc = A2_DIRECTIONS[name]
            neighbours.append([cell_name(cell), name, cell_name((cell[0] + dr, cell[1] + dc))])

    board_entries = [[cell_name(cell), 0] for cell in arena]
    board_entries += [
        [cell_name((r, c)), A2_BOARD[r][c]]
        for r in range(9) for c in range(9)
        if A2_BOARD[r][c] not in (0, 1)
    ]

    # `rendered` is `theory.py`'s render() read back off the frame, in the same
    # draw order: board, then Button, then Cart, then Door, so the later drawing
    # wins.  The guards below read colours and never the state directly, which
    # is what the manual's own `colored(...)` / `free(...)` mean.
    rendered = ["if",
                ["and", eq(["param", "x"], lit(cell_name(A2_DOOR))),
                 eq(var("door"), lit("yes"))],
                lit(A2_DOOR_COLOUR),
                ["if", eq(["param", "x"], var("cart")),
                 lit(A2_CART_COLOUR),
                 ["if", eq(["param", "x"], lit(cell_name(A2_BUTTON))),
                  var("button"),
                  ["table", "board", ["param", "x"]]]]]

    def push(direction: str) -> dict:
        target = ["table", "nb", var("cart"), lit(direction)]
        return {
            "name": "push_%s" % direction,
            "action": direction,
            "guard": ["call", "free", target],
            "effects": {"cart": target},
            "owns": ["cart"],
        }

    rules = [push(d) for d in ("up", "down", "left", "right")]
    if with_teleport:
        rules.append({
            "name": "teleport_down",
            "action": "down",
            "comment": "when act=push(Cart, down) and colored(below(Cart), 3) "
                       "then jumped(Cart, portal_exit)",
            "guard": eq(["call", "rendered",
                         ["table", "nb", var("cart"), lit("down")]],
                        lit(A2_PORTAL_COLOUR)),
            "effects": {"cart": lit(cell_name(A2_PORTAL_EXIT))},
            "owns": ["cart"],
        })
    rules.append({
        "name": "press_up",
        "action": "up",
        "guard": eq(["call", "rendered", ["table", "nb", var("cart"), lit("up")]],
                    lit(A2_BUTTON_COLOUR)),
        "effects": {"button": lit(A2_BUTTON_PRESSED)},
        "owns": ["button"],
    })
    rules.append({
        "name": "door_opens_up",
        "action": "up",
        "guard": eq(["call", "rendered", ["table", "nb", var("cart"), lit("up")]],
                    lit(A2_BUTTON_COLOUR)),
        "effects": {"door": lit("no")},
        "owns": ["door"],
    })

    name = "a2-world" if with_teleport else "a2-holed"
    return {
        "schema": RULESET_SCHEMA,
        "name": name,
        "comment": (
            "A2's 9x9 pushing world, %s the teleport rule. %s"
            % ("with" if with_teleport else "WITHOUT",
               "This is the control manual, which A2's 18-action refutation "
               "established is the world's own rule set."
               if with_teleport else
               "This is the exhibit: the manual whose `unsolvable` theorem is "
               "true of itself and false of the world.")
        ),
        "provenance": {
            "manual": "cold-start-a2/theory/%s"
                      % ("theory.dsl" if with_teleport else "theory_holed.dsl"),
            "compiled_form": "cold-start-a2/theory/%s/theory.py"
                             % ("generated" if with_teleport else "generated_holed"),
            "board": "transcribed from that file's BOARD literal",
            "difference": "a2-world adds exactly the rule `teleport_down`",
        },
        "variables": [
            {"name": "button", "domain": [A2_BUTTON_COLOUR, A2_BUTTON_PRESSED],
             "comment": "the Button's colour; 8 once pressed"},
            {"name": "cart", "domain": [cell_name(cell) for cell in arena],
             "comment": "the Cart's cell, over the %d background cells" % len(arena)},
            {"name": "door", "domain": ["no", "yes"],
             "comment": "whether the Door is still present at %s" % cell_name(A2_DOOR)},
        ],
        "actions": ["down", "left", "right", "up"],
        "tables": {
            "board": {
                "arity": 1,
                "comment": "the board's own colours; every cell not listed is "
                           "wall (1), which is what the BOARD literal says",
                "default": 1,
                "entries": sorted(board_entries),
            },
            "nb": {
                "arity": 2,
                "comment": "the neighbour of a Cart cell in a direction",
                "entries": sorted(neighbours),
            },
        },
        "defs": [
            {
                "name": "rendered",
                "params": ["x"],
                "comment": "the colour a frame shows at cell x -- board, then "
                           "Button, then Cart, then Door, last drawn wins",
                "body": rendered,
            },
            {
                "name": "free",
                "params": ["x"],
                "body": eq(["call", "rendered", ["param", "x"]], lit(A2_BACKGROUND)),
            },
        ],
        "init": {
            "button": A2_BUTTON_COLOUR,
            "cart": cell_name(A2_CART_START),
            "door": "yes",
        },
        "goal": eq(var("cart"), lit(cell_name(A2_GOAL))),
        "rules": rules,
    }


# Pagoda weight, transcribed from generated_holed/theory.lean, `def w`.
A2_WEIGHT_ZERO_CELLS: Tuple[Cell, ...] = (
    (1, 3), (1, 4),
    (2, 1), (2, 2), (2, 3), (2, 4),
    (3, 1), (3, 2), (3, 3), (3, 4),
    (4, 1), (4, 2), (4, 3), (4, 4),
    (5, 1), (5, 2), (5, 3), (5, 4),
    (6, 2), (6, 3), (6, 4),
)


def a2_certificate() -> dict:
    arena = a2_arena()
    zero = set(A2_WEIGHT_ZERO_CELLS)
    assert zero <= set(arena) and len(zero) == 21
    return {
        "schema": CERTIFICATE_SCHEMA,
        "name": "a2-right-room-locked",
        "kind": "inductive_invariant",
        "claim": "unsolvable",
        "produced_by": "zero_space -> a GF(2) occupancy law, adjudicated into a "
                       "0/1 pagoda weight (cold-start-a2 THEORIZE_LOG L-03)",
        "comment": "I(s) := w(cart) = 0, the invariant Lean proves closed in "
                   "cold-start-a2/theory/generated_holed/theory.lean, axiom-free. "
                   "It is TRUE of the holed manual and FALSE of the world; "
                   "rechecking it against a2-world must reject it. This is the "
                   "one certificate here that carries no `ruleset` binding, and "
                   "the omission is the point: it is meant to be checked "
                   "against both manuals, and a binding would refuse the second "
                   "run before the invariant was ever evaluated.",
        "provenance": {
            "lean": "cold-start-a2/theory/generated_holed/theory.lean, `def w` "
                    "and `def I`",
            "lean_status": "GREEN, #print axioms unsolvable = []",
            "refuted_by": "cold-start-a2/artifacts/refutation.json -- an "
                          "18-action episode ends with win: true",
        },
        "tables": {
            "w": {
                "arity": 1,
                "comment": "0 on the 21 cells the Cart was ever observed on, 1 "
                           "everywhere else, including the goal cell",
                "default": 1,
                "entries": sorted([cell_name(cell), 0] for cell in arena if cell in zero),
            },
        },
        "predicate": eq(["table", "w", var("cart")], lit(0)),
    }


# ================================================================ sokoban

SOKOBAN_DELTA: Dict[str, Cell] = {
    "down": (1, 0), "left": (0, -1), "right": (0, 1), "up": (-1, 0),
}
SOKOBAN_DIRECTIONS = tuple(sorted(SOKOBAN_DELTA))

OPEN4_GRID = ("######", "#....#", "#....#", "#....#", "#....#", "######")
RING_GRID = ("######", "#....#", "#.##.#", "#.##.#", "#....#", "######")


def floors(grid: Sequence[str]) -> List[Cell]:
    return sorted((r, c) for r, row in enumerate(grid)
                  for c, char in enumerate(row) if char == ".")


def sokoban_ruleset(name: str, grid: Sequence[str], player: Cell,
                    boxes: Sequence[Tuple[str, Cell]],
                    goals: Sequence[Tuple[str, Cell]]) -> dict:
    cells = floors(grid)
    names = [cell_name(cell) for cell in cells]
    box_names = [box for box, _ in boxes]

    neighbours = []
    for cell in cells:
        for direction in SOKOBAN_DIRECTIONS:
            dr, dc = SOKOBAN_DELTA[direction]
            target = (cell[0] + dr, cell[1] + dc)
            if target in set(cells):
                neighbours.append([cell_name(cell), direction, cell_name(target)])

    clear_body = ["and", ["!=", ["param", "x"], lit("none")]]
    clear_body += [["!=", ["param", "x"], var(v)] for v in ["player"] + box_names]

    rules = []
    for direction in SOKOBAN_DIRECTIONS:
        target = ["table", "nb", var("player"), lit(direction)]
        rules.append({
            "name": "move_%s" % direction,
            "action": "move-%s" % direction,
            "comment": "PDDL `move`: at-player ?from, clear ?to, adj ?from ?to ?d",
            "guard": ["call", "clear", target],
            "effects": {"player": target},
            "owns": ["player"],
        })
    for direction in SOKOBAN_DIRECTIONS:
        front = ["table", "nb", var("player"), lit(direction)]
        beyond = ["table", "nb", front, lit(direction)]
        effects: Dict[str, object] = {"player": front}
        for box in box_names:
            effects[box] = ["if", eq(front, var(box)), beyond, var(box)]
        rules.append({
            "name": "push_%s" % direction,
            "action": "push-%s" % direction,
            "comment": "PDDL `push`: at-player ?p, at ?b ?from, clear ?to, "
                       "adj ?p ?from ?d, adj ?from ?to ?d",
            "guard": ["and",
                      ["or"] + [eq(front, var(box)) for box in box_names],
                      ["call", "clear", beyond]],
            "effects": effects,
            "owns": sorted(effects),
        })

    occupants = ["player"] + box_names
    distinct = ["and"]
    for i, left in enumerate(occupants):
        for right in occupants[i + 1:]:
            distinct.append(["!=", var(left), var(right)])

    return {
        "schema": RULESET_SCHEMA,
        "name": name,
        "comment": "Fixture D's sokoban level %s, as finite-domain variables "
                   "rather than grounded STRIPS." % name,
        "provenance": {
            "world": "engine-rig/fixtures/sokoban.py",
            "grid": list(grid),
            "encoding": "one variable per movable thing; the PDDL's `clear` "
                        "fluent becomes the derived predicate `clear`, and the "
                        "at-most-one-thing-per-cell fact the grounded task gets "
                        "from its mutexes becomes the declared constraint, "
                        "which this rechecker proves inductive rather than "
                        "assuming.",
        },
        "variables": (
            [{"name": "player", "domain": names}]
            + [{"name": box, "domain": names} for box in box_names]
        ),
        "actions": (
            ["move-%s" % d for d in SOKOBAN_DIRECTIONS]
            + ["push-%s" % d for d in SOKOBAN_DIRECTIONS]
        ),
        "tables": {
            "nb": {
                "arity": 2,
                "comment": "the floor neighbour, or `none` at a wall",
                "default": "none",
                "entries": sorted(neighbours),
            },
        },
        "defs": [
            {
                "name": "clear",
                "params": ["x"],
                "comment": "a real floor cell holding neither the player nor a box",
                "body": clear_body,
            },
        ],
        "constraint": distinct,
        "init": dict(
            [("player", cell_name(player))]
            + [(box, cell_name(cell)) for box, cell in boxes]
        ),
        "goal": ["and"] + [eq(var(box), lit(cell_name(cell))) for box, cell in goals],
        "rules": rules,
    }


def deadlock_certificate(level: str, pattern: Sequence[Tuple[str, Cell]],
                         closure: str) -> dict:
    text = " AND ".join("at(%s,c%d%d)" % (box, cell[0], cell[1])
                        for box, cell in pattern)
    slug = "-".join("%s-%d%d" % (box, cell[0], cell[1]) for box, cell in pattern)
    return {
        "schema": CERTIFICATE_SCHEMA,
        "name": "%s-dead-%s" % (level, slug),
        "kind": "dead_region",
        "claim": "conditional_unsolvability",
        "produced_by": "engines/deadlock_carver (M9)",
        "comment": "%s AND not-goal => dead (closure: %s)" % (text, closure),
        "ruleset": {"name": level},
        "predicate": ["and"] + [
            eq(var(box), lit(cell_name(cell))) for box, cell in pattern
        ],
    }


RINGSTUCK_THEOREMS = (
    (("b1", (1, 1)),),
    (("b1", (1, 4)),),
)

OPEN4FAR_THEOREMS = (
    (("b1", (1, 1)),), (("b1", (1, 4)),), (("b1", (4, 1)),), (("b1", (4, 4)),),
    (("b2", (1, 1)),), (("b2", (1, 4)),), (("b2", (4, 1)),), (("b2", (4, 4)),),
    (("b1", (1, 2)), ("b2", (1, 3))),
    (("b1", (1, 3)), ("b2", (1, 2))),
    (("b1", (2, 1)), ("b2", (3, 1))),
    (("b1", (2, 4)), ("b2", (3, 4))),
    (("b1", (3, 1)), ("b2", (2, 1))),
    (("b1", (3, 4)), ("b2", (2, 4))),
    (("b1", (4, 2)), ("b2", (4, 3))),
    (("b1", (4, 3)), ("b2", (4, 2))),
)


# ================================================================== driver

def serialise(payload: dict) -> str:
    """The exact bytes `dump` writes, so a digest taken here is the file's."""
    return canonical_text(payload)


def bind(cases: Dict[str, dict]) -> Dict[str, dict]:
    """Fill in each certificate's `ruleset.sha256` from the rule set it names.

    A binding by name alone is weak: two rule sets may share a name, and the
    rechecker would pass `ruleset_binding` on either.  The digest makes the
    binding mean the file.  Certificates deliberately meant to be checked
    against more than one rule set carry no binding at all, which is a
    different statement and is left alone here.
    """
    digests = {
        payload["name"]: hashlib.sha256(serialise(payload).encode("utf-8")).hexdigest()
        for payload in cases.values()
        if payload.get("schema") == RULESET_SCHEMA
    }
    for payload in cases.values():
        binding = payload.get("ruleset")
        if payload.get("schema") != CERTIFICATE_SCHEMA or not binding:
            continue
        digest = digests.get(binding.get("name"))
        if digest is None:
            raise KeyError("certificate %r binds to an unknown rule set %r"
                           % (payload.get("name"), binding.get("name")))
        binding["sha256"] = digest
    return cases


def all_cases() -> Dict[str, dict]:
    cases: Dict[str, dict] = {
        # All four starts peg4.py hand-verifies, so all four literals in its
        # docstring are anchors on this encoding rather than only the two the
        # certificate needs.
        "peg4-0111.rules.json": peg_ruleset("0111"),
        "peg4-1011.rules.json": peg_ruleset("1011"),
        "peg4-1101.rules.json": peg_ruleset("1101"),
        "peg4-1110.rules.json": peg_ruleset("1110"),
        "peg4-0111-ic3.cert.json": peg_ic3_certificate(),
        "a2-holed.rules.json": a2_ruleset(with_teleport=False),
        "a2-world.rules.json": a2_ruleset(with_teleport=True),
        "a2-right-room-locked.cert.json": a2_certificate(),
        # `ring` and `open4` carry no certificate. They are here as anchors: the
        # fixture states their optima (1 and 6) on grounds this encoding shares
        # nothing with, so a transcription error in the sokoban rules shows up
        # as a wrong plan length rather than as a quietly wrong verdict.
        "sokoban-ring.rules.json": sokoban_ruleset(
            "sokoban-ring", RING_GRID, (1, 1), (("b1", (1, 2)),),
            (("b1", (1, 3)),)),
        "sokoban-open4.rules.json": sokoban_ruleset(
            "sokoban-open4", OPEN4_GRID, (4, 4),
            (("b1", (2, 2)), ("b2", (3, 3))),
            (("b1", (1, 2)), ("b2", (4, 3)))),
        "sokoban-ringstuck.rules.json": sokoban_ruleset(
            "sokoban-ringstuck", RING_GRID, (1, 1), (("b1", (1, 2)),),
            (("b1", (3, 1)),)),
        "sokoban-open4far.rules.json": sokoban_ruleset(
            "sokoban-open4far", OPEN4_GRID, (4, 4),
            (("b1", (2, 2)), ("b2", (3, 3))),
            (("b1", (4, 2)), ("b2", (1, 3)))),
    }
    for pattern in RINGSTUCK_THEOREMS:
        cert = deadlock_certificate("sokoban-ringstuck", pattern, "no_deleting_action")
        cases["%s.cert.json" % cert["name"]] = cert
    for pattern in OPEN4FAR_THEOREMS:
        closure = "no_deleting_action" if len(pattern) == 1 else "deleting_actions_blocked"
        cert = deadlock_certificate("sokoban-open4far", pattern, closure)
        cases["%s.cert.json" % cert["name"]] = cert
    return bind(cases)


def write(directory: str = CASES_DIR) -> Dict[str, str]:
    os.makedirs(directory, exist_ok=True)
    out = {}
    for filename, payload in sorted(all_cases().items()):
        out[filename] = dump(os.path.join(directory, filename), payload)
    return out


def check(directory: str = CASES_DIR) -> List[str]:
    """Filenames whose committed bytes differ from what the generator makes."""
    drifted = []
    for filename, payload in sorted(all_cases().items()):
        path = os.path.join(directory, filename)
        expected = serialise(payload)
        if not os.path.exists(path):
            drifted.append(filename + " (missing)")
            continue
        with open(path, "r", encoding="utf-8", newline="") as handle:
            if handle.read().replace("\r\n", "\n") != expected:
                drifted.append(filename)
    return drifted


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m recheck.build_cases")
    parser.add_argument("--check", action="store_true",
                        help="verify the committed cases match, write nothing")
    parser.add_argument("--dir", default=CASES_DIR)
    args = parser.parse_args(argv)

    if args.check:
        drifted = check(args.dir)
        for filename in drifted:
            print("DRIFTED %s" % filename, file=sys.stderr)
        print("%d cases, %d drifted" % (len(all_cases()), len(drifted)))
        return 1 if drifted else 0

    written = write(args.dir)
    print("%d cases written to %s" % (len(written), args.dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
