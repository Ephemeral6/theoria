"""判决题 -- three classes of verdict question, set in the A2 world family.

Theoria.md 1.11 does not ask "can it tell solvable from unsolvable".  It asks
three separate questions and insists on scoring sensitivity and specificity
together:

  (i)   **small space, unsolvable.**  Exhaustive search is feasible here, so a
        complete searcher stops correctly too -- and may stop correctly *for the
        wrong reason*, because a missing edge also makes a search terminate.
        What is examined is therefore the reason.  Every class (i) item on this
        paper has its state space actually enumerated at build time, and the
        count and the cap are written into the truth file, so "exhaustive search
        is feasible here" is a measured number rather than an adjective.
  (ii)  **large space, unsolvable.**  Enumeration is out of reach and only
        invariant reasoning answers.  The bound is *demonstrated*, not asserted:
        each class (ii) level admits, by construction, a family of 2^m distinct
        reachable states obtained by dipping into any subset of m alcoves and
        returning to the corridor, and the arithmetic is recorded.  m is chosen
        by the level, not by us -- the builder computes the largest m the step
        budget allows and refuses to ship an item whose bound is below 10^12.
  (iii) **solvable but hard.**  The false-positive trap.  The truth carries a
        witness plan that was *computed and replayed*, not asserted, and the
        items are weighted (3 points against 2) so that a `bluffer` who answers
        "unsolvable" everywhere has perfect sensitivity, zero specificity, and a
        bad score.  That calibration is asserted in the tests; it is the thing
        that proves the rubric is not scoring confidence.

**This is the dress rehearsal Phase 4 needs.**  Theoria.md Phase 4 has a timing
problem it solves by ordering: constructing a justified unsolvable variant of a
sealed game requires understanding that game, and understanding it breaks the
seal -- so the main table runs first, and only afterwards may the exam subset be
studied.  What is frozen *now*, before any of that, is the operator library and
the procedure.  Every item here is emitted as a `proxy.variants` spec, validated
by constructing `proxy.variants.Variant` over it, and hashed; the four wrapper
operators used (`forbid_action`, `remap_action`, `step_limit`,
`observation_loss`, plus `win_tighten` on one control item) are the whole legal
set.  When a sealed game is finally opened, the only new work is the per-game
justification -- the format, the validator, the certificate grammar, the rubric
and the calibration are already fixed and already exercised.

**Leakage.**  This question type gives itself away more easily than the other
three, because the class name *is* the answer for two of the three classes.  So:
item ids are opaque digests, the class never appears on the sheet (not in the
id, not in the tags -- `Item.sheet_side` publishes tags), the per-class
breakdown is computed in `axes()` from the truth side, and the item order is a
deterministic shuffle over the item ids so that answer does not correlate with
position.  The variant specs carry `claim` and `justification` and are therefore
truth-side artefacts: nothing on the sheet names a spec file or a variant id.
The same board appears six times under different operators -- twice unsolvable,
four times solvable -- so board identity carries no signal either.

**The world.**  A2's geometry and semantics (`cold-start-a2/a2world/a2_world.py`):
a pushing world, a button that opens a door in the same transition, a teleport
with exactly one firing context, and a right room that column c5 seals off.  The
family adds one thing A2 does not have -- latching switches in alcoves off a
corridor -- for one reason: it is the cheapest construction that makes the state
space provably enormous while leaving the *goal's* reachability decided by
geometry alone, so the truth of a class (ii) item still follows from the
construction and never from a search.  `cold-start-a2` deliberately does not
carry the DC22 game id and neither does this paper.
"""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .. import guard
from ..grading.mark import confusion
from ..grading.rubrics_verdict import (
    ACTIONS, DELTA, MAX_ENUMERATION, OPPOSITE, Level, check_certificate,
    enumerate_states, relaxed_distance, replay,
)
from ..model import ARTIFACTS, HERE, Item, Paper, canonical, sha256_text, write_json

PAPER_ID = "p15-verdict-a2"
QUESTION_TYPE = "verdict"
WORLD_ID = "a2"
RUBRIC_ID = "verdict.a2.claim_and_certificate"

SPEC_DIR = os.path.join(ARTIFACTS, "variant_specs")
REPO_ROOT = os.path.dirname(HERE)

#: A class (ii) item whose demonstrated bound is under this is not a class (ii)
#: item, it is a class (i) item with a big board.  `build()` refuses to ship one.
LARGE_SPACE_THRESHOLD = 10 ** 12

#: A board is "small" if a human can hold it; the split is what `memoriser` is
#: measured against.  Recorded in the truth, never on the sheet.
SMALL_BOARD_MAX_HEIGHT = 12
SMALL_BOARD_MAX_WIDTH = 24

#: Uniform, and it has to stay uniform.
#:
#: These were 2.0 and 3.0, weighting the solvable items so that a bluffer who
#: answers "unsolvable" everywhere scored badly.  A cheater subagent handed the
#: sheet alone read the class straight off `points` -- 17/17, the whole claim
#: half of the paper, with no reasoning about any board -- because `points` is
#: on the sheet (`Item.sheet_side`) and every solvable item carried 3.0.
#:
#: The anti-bluffer property did not need the weights: there are 9 unsolvable
#: items and 8 solvable ones, and half of every item's marks are the reason,
#: which a bluffer never earns.  It scores 9 of 34 either way.  The weighting
#: bought nothing and leaked everything.
POINTS_UNSOLVABLE = 2.0
POINTS_SOLVABLE = 2.0

CART_COLOUR = 6          # A2's palette: the cart is colour 6, so an
                         # observation_loss keyed on 6 means "the cart is here".

MARKERS = {
    "#": "wall", ".": "floor", "S": "the cart's start", "G": "the goal cell",
    "B": "button (pressing it opens the door, in the same transition; the cart "
         "does not move)",
    "D": "door (impassable until the button is pressed)",
    "P": "teleport entry (entering it moves the cart to X; the cart never rests "
         "on P)",
    "X": "teleport exit",
    "s": "latching switch (stepping on it latches it, for good)",
    "!": "hazard: the episode is declared lost on the frame in which the cart "
         "stands here",
}


# ============================================================ level builders

def _level(level_id: str, rows: Sequence[str], start: Tuple[int, int],
           goal: Tuple[int, int], **extra: Any) -> Dict[str, Any]:
    doc: Dict[str, Any] = {
        "level_id": level_id,
        "rows": list(rows),
        "start": list(start),
        "goal": list(goal),
        "button": None,
        "door": None,
        "portal": None,
        "portal_dest": None,
        "switches": [],
        "require_all_switches": False,
        "forbidden": [],
        "remap": {},
        "step_limit": None,
        "lost_cells": [],
        "win_score_required": 1,
    }
    doc.update(extra)
    return doc


def a2_echo() -> Dict[str, Any]:
    """A2's own 9x9 board, marker for marker.

    Column 5 is solid wall from r1 to r7, so the right room touches nothing; the
    teleport at (7,4) is its only entrance and (7,4) is enterable only from the
    door cell (6,4), going down.  Both facts are load-bearing: the first makes a
    forbidden DOWN unsolvable and provably so, the second makes the shortest
    honest solution eighteen commands long.
    """
    rows = [
        "#########",
        "#B#..#..#",
        "#....#.G#",
        "#....#..#",
        "#....#..#",
        "#S...#..#",
        "##..D#..#",
        "#.##P#X.#",
        "#########",
    ]
    return _level("atrium", rows, (5, 1), (2, 7),
                  button=[1, 1], door=[6, 4], portal=[7, 4], portal_dest=[7, 6])


def updraft() -> Dict[str, Any]:
    """Goal strictly above the start, and no teleport anywhere on the board.

    Built so that removing UP leaves a monotone row -- the simplest closed
    invariant there is, and the one whose closure check costs four subtractions
    rather than a search.
    """
    rows = [
        "#########",
        "#.....G.#",
        "#.#####.#",
        "#.......#",
        "#.#####.#",
        "#...S...#",
        "#########",
    ]
    return _level("updraft", rows, (5, 4), (1, 6))


def cistern() -> Dict[str, Any]:
    """Two halves joined by exactly one floor cell, (3,5).

    A cut set of size one.  Deliberately a *single* cell, so a submitted cut set
    that names two cells because it did not look is refused for naming a
    non-hazard.
    """
    rows = [
        "###########",
        "#....#....#",
        "#....#....#",
        "#S.......G#",
        "#....#....#",
        "#....#....#",
        "###########",
    ]
    return _level("cistern", rows, (3, 1), (3, 9))


def quarry() -> Dict[str, Any]:
    """The goal room is walled off by static geometry alone.

    Nothing the wrapper does can change that, which is the point: the item's
    operator is a pure relabelling, and an examinee that reasons about the
    operator instead of the board gets it wrong.
    """
    rows = [
        "#########",
        "#S......#",
        "#.......#",
        "#########",
        "#......G#",
        "#.......#",
        "#########",
    ]
    return _level("quarry", rows, (1, 1), (4, 7))


def meander() -> Dict[str, Any]:
    """A serpentine corridor: one route, about a hundred commands long.

    Solvable, and long enough that a depth-limited or budgeted searcher gives up
    and reports failure.  "It gave up" and "there is nothing to find" are the
    two things class (iii) exists to separate.
    """
    height, width = 11, 21
    rows: List[str] = ["#" * width]
    for r in range(1, height - 1):
        if r % 2 == 1:
            rows.append("#" + "." * (width - 2) + "#")
        else:
            opening = width - 2 if (r // 2) % 2 == 1 else 1
            row = ["#"] * width
            row[opening] = "."
            rows.append("".join(row))
    rows.append("#" * width)
    grid = [list(r) for r in rows]
    grid[1][1] = "S"
    grid[height - 2][width - 2] = "G"
    return _level("meander", ["".join(r) for r in grid], (1, 1),
                  (height - 2, width - 2))


def comb_open(level_id: str, corridor_len: int, start_col: int,
              goal_col: int) -> Dict[str, Any]:
    """Corridor with a latching switch above and below every column.

    The switches are what make the state space enormous, and they make it
    enormous *provably*: dip into any subset of them and come back, and you are
    at the corridor's far end with exactly that subset latched.  Distinct
    subsets are distinct states, so the reachable set is at least 2^m.  They gate
    nothing about the geometry, so the goal's reachability is still decided by
    walls and by the operator -- which is what keeps a class (ii) truth
    constructive.
    """
    width = corridor_len + 2
    border = "#" * width
    upper = "#" + "s" * corridor_len + "#"
    lower = "#" + "s" * corridor_len + "#"
    corridor = list("#" + "." * corridor_len + "#")
    corridor[start_col] = "S"
    corridor[goal_col] = "G"
    rows = [border, upper, "".join(corridor), lower, border]
    switches = ([[1, c] for c in range(1, corridor_len + 1)]
                + [[3, c] for c in range(1, corridor_len + 1)])
    return _level(level_id, rows, (2, start_col), (2, goal_col),
                  switches=switches, require_all_switches=True)


def comb_room(level_id: str, corridor_len: int,
              bridge_col: Optional[int]) -> Dict[str, Any]:
    """The same comb, plus a two-row goal room under a separator.

    `bridge_col=None` seals the room with static wall; a bridge column makes the
    separator a single floor cell, which is then either the hazard that severs
    the level or the cell a witness plan walks across.  Same board, opposite
    answers, one operator apart.
    """
    width = corridor_len + 2
    border = "#" * width
    upper = "#" + "s" * corridor_len + "#"
    lower = "#" + "s" * corridor_len + "#"
    corridor = list("#" + "." * corridor_len + "#")
    corridor[1] = "S"
    separator = list("#" * width)
    if bridge_col is not None:
        separator[bridge_col] = "."
    room_top = list("#" + "." * corridor_len + "#")
    room_top[corridor_len] = "G"
    room_bottom = "#" + "." * corridor_len + "#"
    rows = [border, upper, "".join(corridor), lower, "".join(separator),
            "".join(room_top), room_bottom, border]
    switches = ([[1, c] for c in range(1, corridor_len + 1)]
                + [[3, c] for c in range(1, corridor_len + 1)])
    return _level(level_id, rows, (2, 1), (5, corridor_len),
                  switches=switches, require_all_switches=True)


# =========================================================== level surgery

def variant_of(base: Dict[str, Any], level_id: str, **ops: Any) -> Dict[str, Any]:
    """Apply wrapper operators to a base level, producing the level the examinee
    is actually shown.  The base is never mutated."""
    doc = json.loads(json.dumps(base, sort_keys=True))
    doc["level_id"] = level_id
    doc.update(ops)
    return doc


# ======================================================= planning & bounds

def _passable(level: Level, cell: Tuple[int, int]) -> bool:
    return level.passable(cell) and cell not in level.lost_cells


def position_paths(level: Level, src: Tuple[int, int]) -> Dict[Tuple[int, int],
                                                               List[str]]:
    """Shortest command sequences from `src` to every cell, in command space.

    Exact only for levels with no button, door or portal -- which is every comb
    level, and `waypoint_plan` asserts it.  Command space rather than world-
    action space so that `remap_action` needs no translation anywhere: the plan
    that comes out is the plan the arm sends.
    """
    paths: Dict[Tuple[int, int], List[str]] = {src: []}
    frontier = [src]
    while frontier:
        nxt_frontier: List[Tuple[int, int]] = []
        for cell in frontier:
            for command in level.commands():
                moved, _ = level.step(cell, False, level.world_action(command))
                if moved in paths or not _passable(level, moved):
                    continue
                paths[moved] = paths[cell] + [command]
                nxt_frontier.append(moved)
        frontier = nxt_frontier
    return paths


def waypoint_plan(level: Level) -> Optional[List[str]]:
    """Visit every switch, then the goal.  Chained shortest hops.

    Not optimal and not meant to be -- a class (iii) witness has to *exist* and
    be replayable, and a shorter one would make the item easier, not more
    honest.
    """
    if level.button is not None or level.door is not None or level.portal is not None:
        raise ValueError("waypoint planning assumes a comb level: no button, "
                         "door or portal, so position determines the successor")
    waypoints = sorted(level.switches, key=lambda c: (c[1], c[0]))
    waypoints.append(level.goal)
    plan: List[str] = []
    here = level.start
    for target in waypoints:
        if target == here:
            continue
        paths = position_paths(level, here)
        if target not in paths:
            return None
        plan.extend(paths[target])
        here = target
    return plan


def subset_lower_bound(level: Level) -> Dict[str, Any]:
    """A demonstrated lower bound on the reachable state count: 2^m.

    The construction, and it is the whole justification:

      * a switch `s` is *dippable* from corridor cell `c` when one available
        command moves the cart c -> s and another moves it back s -> c;
      * take the dippable switches in order of their corridor cell's distance
        from the start; visiting the first m of them costs at most
        dist(c_m) + 2m commands, because the corridor cells lie along one path
        and each dip is out-and-back;
      * for every one of the 2^m subsets, dipping into exactly that subset and
        stopping at c_m leaves the cart in the same place with a different latch
        mask.  Distinct masks are distinct states.

    So the reachable set has at least 2^m elements, with m the largest prefix
    the step budget affords.  No search anywhere, which is the point: a bound
    that had to be searched for would be a bound we could not state about a
    board we cannot search.
    """
    reach = position_paths(level, level.start)
    candidates: List[Tuple[int, Tuple[int, int]]] = []
    for switch in level.switches:
        if switch in level.lost_cells or not level.passable(switch):
            continue
        best: Optional[int] = None
        for command in level.commands():
            action = level.world_action(command)
            dr, dc = DELTA[action]
            source = (switch[0] - dr, switch[1] - dc)
            if source == switch or not _passable(level, source):
                continue
            if source not in reach:
                continue
            back = OPPOSITE[action]
            if back not in level.effective_actions():
                continue
            landed, _ = level.step(source, False, action)
            if landed != switch:
                continue
            returned, _ = level.step(switch, False, back)
            if returned != source:
                continue
            distance = len(reach[source])
            best = distance if best is None else min(best, distance)
        if best is not None:
            candidates.append((best, switch))
    candidates.sort(key=lambda pair: (pair[0], pair[1]))

    m = 0
    for index, (distance, _switch) in enumerate(candidates, start=1):
        cost = distance + 2 * index
        if level.step_limit is not None and cost > level.step_limit:
            break
        m = index

    # The premise the construction rests on, checked rather than assumed.
    #
    # "Dip into any subset and come back" is only realisable for *arbitrary*
    # subsets if the m dip sources lie on one contiguous lane the cart can walk
    # along without latching anything it did not choose and without dying. The
    # code checked each dip in isolation and never checked the travel between
    # them, so on a corridor whose own cells are switches the reachable masks
    # are the m prefixes rather than the 2^m subsets -- and `subset_lower_bound`
    # returned 2^60 for a level with 1,830 reachable states. Worse, `comb_open`
    # plus an `observation_loss` on the corridor -- a shipped constructor and a
    # shipped operator -- produced 2^60 against a true 29,791, and `_large_space`
    # stamped `exhaustive_feasible: False` on it. Repro in this run's
    # `verify_checker_claims.py`. D-EX-021.
    #
    # The second premise, and it is a different one: the m dips must move m
    # *independent* latch bits. `Level.switch_index` (rubrics_verdict.py) is
    # keyed on the cell, so two entries naming the same cell share one bit and
    # the 2^m family counts masks the level cannot hold. Measured: a `comb_open`
    # whose `switches` list repeats one cell 60 times yielded 2^60 = 1.15e18
    # against a true 359 reachable states, and neither the lane premise nor
    # `LARGE_SPACE_THRESHOLD` refused it -- only `Level.wellformed_problems()`
    # did, from `_self_check` at the very end of `build()`, long after
    # `_large_space` had written the false record. A bound must defend its own
    # premise where it is claimed, not rely on a check three call frames away.
    # Gated on `candidates[:m]` rather than on `level.switches`, because a
    # duplicate that never enters the prefix never enters the bound: a repeated
    # entry naming a wall is skipped above and the bound over the real alcoves
    # stays sound. Repro in this run's `repro_duplicate_switch.py`. D-EX-028.
    chosen = [switch for _d, switch in candidates[:m]]
    sources = [_dip_source(level, reach, switch) for switch in chosen]
    problems = _lane_problems(level, [s for s in sources if s is not None])
    if m and len(set(chosen)) != m:
        problems.append(
            "the first %d dips name only %d distinct cells; duplicates share "
            "one latch bit, so 2^%d counts latch masks the level cannot hold"
            % (m, len(set(chosen)), m))
    if m and (len(sources) != m or problems):
        raise AssertionError(
            "%s: the 2^m family is not demonstrated on this board -- %s. The "
            "bound counts each dip in isolation; it is only a bound when the "
            "dip sources lie on one switch-free, hazard-free lane, because "
            "otherwise walking between two dips latches switches the subset did "
            "not choose and the 2^m states are not distinct reachable states."
            % (level.level_id, "; ".join(problems) or "a dip source vanished"))
    return {
        "m": m,
        "dippable_switches": len(candidates),
        "lower_bound": 2 ** m,
        "arithmetic": (
            "%d switches are dippable out-and-back from the corridor; the step "
            "budget (%s) affords the first %d of them at a cost of dist + 2m "
            "commands; each of the 2^%d subsets ends at the same cell with a "
            "different latch mask, so the reachable set has at least 2^%d = %d "
            "states." % (len(candidates),
                         "unbounded" if level.step_limit is None
                         else str(level.step_limit), m, m, m, 2 ** m)),
    }


def _dip_source(level: Level, reach: Dict[Tuple[int, int], List[str]],
                switch: Tuple[int, int]) -> Optional[Tuple[int, int]]:
    """The corridor cell the bound's construction dips into `switch` from.

    Same rule `subset_lower_bound` uses to decide a switch is dippable, kept in
    step with it by reading the same `reach`.  Returned so the lane the cart
    walks between dips can be checked, which is the premise the bound was
    asserting rather than testing.
    """
    best: Optional[Tuple[int, Tuple[int, int]]] = None
    for command in level.commands():
        action = level.world_action(command)
        dr, dc = DELTA[action]
        source = (switch[0] - dr, switch[1] - dc)
        if source == switch or not _passable(level, source) or source not in reach:
            continue
        back = OPPOSITE[action]
        if back not in level.effective_actions():
            continue
        landed, _ = level.step(source, False, action)
        if landed != switch:
            continue
        returned, _ = level.step(switch, False, back)
        if returned != source:
            continue
        distance = len(reach[source])
        if best is None or distance < best[0]:
            best = (distance, source)
    return None if best is None else best[1]


def _lane_problems(level: Level,
                   sources: Sequence[Tuple[int, int]]) -> List[str]:
    """Is there one lane along which every dip can be taken independently?

    The 2^m family is realisable for *arbitrary* subsets only if the cart can
    travel from one dip source to the next without latching anything the subset
    did not choose and without dying.  One contiguous, switch-free, hazard-free
    row or column is the sufficient condition, and it is the one the comb
    construction actually provides.  Anything else and the reachable masks are
    not the 2^m subsets -- on a corridor whose own cells are switches they are
    the m prefixes, which is m+1 masks rather than 2^m.
    """
    problems: List[str] = []
    if not sources:
        return problems
    rows = {cell[0] for cell in sources}
    cols = {cell[1] for cell in sources}
    if len(rows) == 1:
        row = next(iter(rows))
        lane = [(row, c) for c in range(min(cols), max(cols) + 1)]
    elif len(cols) == 1:
        col = next(iter(cols))
        lane = [(r, col) for r in range(min(rows), max(rows) + 1)]
    else:
        return ["the dip sources do not lie on one row or one column (rows %s, "
                "columns %s), so travelling between two dips is not a straight "
                "walk and may latch switches the subset did not choose"
                % (sorted(rows), sorted(cols))]
    for cell in lane:
        if not _passable(level, cell):
            problems.append("the lane cell %s is not walkable" % (list(cell),))
        elif cell in level.switch_index:
            problems.append("the lane cell %s is itself a latching switch, so "
                            "walking past it latches a switch the subset did "
                            "not choose" % (list(cell),))
    return problems[:4]


def _witness_by_search(level_doc: Dict[str, Any]) -> Tuple[Optional[List[str]], str]:
    """A witness found by breadth-first search over the whole state space.

    Legitimate -- a plan that replays and wins proves solvability however it was
    found -- but it is *not* an answer that follows from the construction, and
    the paper's premise is 由构造即知答案. So the key records which of the two
    this was, and `_self_check` refuses an item that does not say. D-EX-023.
    """
    return enumerate_states(Level(level_doc), cap=MAX_ENUMERATION)["solution"], "search"


def _witness_by_construction(level_doc: Dict[str, Any]) -> Tuple[Optional[List[str]], str]:
    """A witness built from the board's shape by `waypoint_plan`, no search."""
    return waypoint_plan(Level(level_doc)), "construction"


def positional_states(level: Level) -> int:
    """How many `(cart, button pressed)` states are actually reachable.

    The quotient a competent solver searches, as against the raw product space
    `enumerate_states` walks.  On a comb level latching is monotone and gates no
    geometry, so every non-full latch mask at a position behaves alike and this
    is the space that decides the question.

    It is recorded on every item because the difference between the two numbers
    is the honest content of class (ii): `lower_bound` says a *naive* enumerator
    cannot finish, and this says what an enumerator that quotients has to do
    instead.  The paper used to publish only the first and let the rubric tell
    an examinee that had searched the second that its search was impossible.
    D-EX-022.
    """
    start = (level.start, False)
    seen = {start}
    frontier = [start]
    while frontier:
        nxt_frontier: List[Tuple[Tuple[int, int], bool]] = []
        for cart, pressed in frontier:
            for command in level.commands():
                state = level.step(cart, pressed, level.world_action(command))
                if state[0] in level.lost_cells or state in seen:
                    continue
                seen.add(state)
                nxt_frontier.append(state)
        frontier = nxt_frontier
    return len(seen)


# ============================================================ spec emission

def _spec(variant_id: str, base_level: str, claim: str, justification: str,
          operators: List[Dict[str, Any]], notes: str) -> Dict[str, Any]:
    return {
        "variant_id": variant_id,
        "base_game": WORLD_ID,
        "base_level": base_level,
        "claim": claim,
        "justification": justification,
        "operators": operators,
        "notes": notes,
    }


def _emit_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Write one spec and validate it the only way that counts: by constructing
    `proxy.variants.Variant` over it.

    The import is read-only and reaches into the other track's module on
    purpose.  A spec validated by our own copy of the rules would prove that our
    copy agrees with itself; a spec `Variant.load` refuses is not a question,
    and only `Variant` can say so.  Round-tripped through the file as well, so
    that what is hashed is what is on disk.
    """
    from proxy.variants import Variant   # noqa: E402  (read-only, other track)

    Variant(spec)                       # refuses here if the spec is malformed
    path = os.path.join(SPEC_DIR, "%s.json" % spec["variant_id"])
    write_json(path, spec)
    loaded = Variant.load(path)
    with open(path, "r", encoding="utf-8", newline="") as handle:
        text = handle.read()
    return {
        "variant_id": loaded.variant_id,
        "spec_sha256": loaded.sha256,
        "spec_file": os.path.relpath(path, REPO_ROOT).replace(os.sep, "/"),
        "spec_file_sha256": sha256_text(text),
        "operators": [op["op"] for op in loaded.operators],
    }


# ============================================================ item assembly

def _opaque_id(key: str) -> str:
    return "vq-" + hashlib.sha256(("%s|%s" % (PAPER_ID, key)).encode("utf-8")).hexdigest()[:10]


def _board_size_class(level_doc: Dict[str, Any]) -> str:
    rows = level_doc["rows"]
    if len(rows) <= SMALL_BOARD_MAX_HEIGHT and len(rows[0]) <= SMALL_BOARD_MAX_WIDTH:
        return "small"
    return "large"


def _render(level_doc: Dict[str, Any]) -> List[str]:
    grid = [list(row) for row in level_doc["rows"]]
    for r, c in level_doc.get("lost_cells", ()):
        grid[r][c] = "!"
    return ["".join(row) for row in grid]


def _paper_side(level_doc: Dict[str, Any]) -> Dict[str, Any]:
    level = Level(level_doc)
    legend = {ch: MARKERS[ch] for ch in sorted(set("".join(_render(level_doc))))
              if ch in MARKERS}
    return {
        "kind": "verdict",
        "world": WORLD_ID,
        "level_id": level_doc["level_id"],
        "objective": "drive the cart onto G",
        "board": {"grid": _render(level_doc), "legend": legend},
        "commands": list(level.commands()),
        "relabelled": dict(sorted(level.remap.items())),
        "budget": level.step_limit,
        "hazards": [list(c) for c in sorted(level.lost_cells)],
        "win_requires": {
            "cart_on_goal": True,
            "all_switches_latched": bool(level.require_all_switches and level.switches),
            "score_at_least": level.win_score_required,
        },
        "question": ("Is this level solvable? Answer `solvable` or `unsolvable`, "
                     "and justify it as the instructions require."),
    }


def _make_item(key: str, level_doc: Dict[str, Any], klass: str, claim: str,
               certificate: Optional[Dict[str, Any]], witness: Optional[List[str]],
               state_space: Dict[str, Any],
               spec_record: Dict[str, Any], justification: str,
               points: float, witness_source: Optional[str] = None) -> Item:
    item_id = _opaque_id(key)
    # "Could this examinee have enumerated the space it says it enumerated?"
    #
    # This run briefly derived it from `positional_states`, the `(cart, button)`
    # quotient, on the argument that latching is monotone and gates no geometry
    # so the quotient decides the question. **That argument is false and the
    # change was withdrawn.** The quotient ignores `step_limit` outright, and it
    # carries no latch state at all -- so on a `require_all_switches` board where
    # one switch has been made unreachable, the quotient says the goal is
    # reachable and the level is unsolvable. Both counterexamples use a shipped
    # constructor and a shipped operator; the reproduction is in this run's
    # `verify_review_claims.py`. Deriving credibility from an unsound abstraction
    # replaced "a true statement was called false" with "a false statement is
    # called true", and the second one *pays*. D-EX-022, withdrawn.
    #
    # So it is the real thing again: an examinee could have enumerated this level
    # exactly when a forward enumeration of the level's own state space finishes,
    # which `_small_space` establishes by running one and `_large_space` refuses
    # by demonstrating a 2^m lower bound.
    search_credible = bool(state_space["naive_enumeration_feasible"])
    truth: Dict[str, Any] = {
        "claim": claim,
        "class": klass,
        "level_blob": canonical(level_doc),
        "certificate_blob": canonical(certificate) if certificate else None,
        "witness": list(witness) if witness else None,
        "witness_length": len(witness) if witness else None,
        # Where the key's own answer came from. `README` said "a computed
        # witness plan" and `verdict.py` said "computed and replayed, not
        # asserted", and neither word separates a breadth-first search from a
        # construction. On a paper whose premise is 由构造即知答案, the key has
        # to say which of the two produced it. D-EX-023.
        "witness_source": witness_source,
        "spec": spec_record,
        "state_space": state_space,
        "search_credible": search_credible,
        "board_size_class": _board_size_class(level_doc),
        "weights": {"verdict": 0.5, "justification": 0.5},
        "note": justification,
    }
    probes = [
        spec_record["variant_id"],
        spec_record["spec_sha256"],
        justification[:80],
        klass,
    ]
    if certificate:
        probes.append(canonical(certificate))
    if witness:
        probes.append(" ".join(witness))
    return Item(
        item_id=item_id,
        rubric_id=RUBRIC_ID,
        points=points,
        paper=_paper_side(level_doc),
        truth=truth,
        leak_probes=tuple(probes),
        # Tags travel on the sheet (`Item.sheet_side`), so they say nothing a
        # reader could turn into an answer. The class breakdown is an axis,
        # computed from the truth side.
        tags=("verdict", "a2-family"),
    )


def _small_space(level_doc: Dict[str, Any]) -> Dict[str, Any]:
    """Enumerate, and record the cap alongside the count.

    A count that quietly hit its cap is not an enumeration, and "exhaustive
    search is feasible here" is the premise of the whole of class (i).
    """
    result = enumerate_states(Level(level_doc), cap=MAX_ENUMERATION)
    if result["truncated"]:
        raise AssertionError(
            "%s did not finish enumerating under the cap of %d; it is not a "
            "small-space item" % (level_doc["level_id"], MAX_ENUMERATION))
    return {
        # Renamed from `exhaustive_feasible`: the claim this field can carry is
        # about the *naive* method -- forward enumeration over the full
        # (cart, button, latch mask) state -- and not about exhaustive search in
        # general. On the class (ii) side the old name was flatly false; see
        # `_large_space` and D-EX-028. Renamed on both sides so the two records
        # keep saying the same thing about the same method.
        "naive_enumeration_feasible": True,
        "enumeration_attempted": True,
        "enumerated": result["states"],
        "cap": result["cap"],
        "truncated": False,
        "lower_bound": result["states"],
        "positional_states": positional_states(Level(level_doc)),
        "arithmetic": ("forward enumeration in command space terminated at %d "
                       "states, under the cap of %d" % (result["states"], result["cap"])),
    }


def _large_space(level_doc: Dict[str, Any]) -> Dict[str, Any]:
    bound = subset_lower_bound(Level(level_doc))
    if bound["lower_bound"] < LARGE_SPACE_THRESHOLD:
        raise AssertionError(
            "%s demonstrates only %d reachable states, under the %d required of "
            "a class (ii) item; enumeration is not out of reach and the question "
            "does not test what it claims to"
            % (level_doc["level_id"], bound["lower_bound"], LARGE_SPACE_THRESHOLD))
    quotient = positional_states(Level(level_doc))
    return {
        # NOT `exhaustive_feasible`. The old name claimed no exhaustive method
        # is feasible here, and that is false: every shipped class (ii) item is
        # settled by an exhaustive computation over at most 600 nodes in at most
        # 5 ms, against these bounds of 1e18-1e36. What is true is the narrower
        # statement -- the *naive* method, forward enumeration over the full
        # (cart, button, latch mask) state, which is the method class (i) is
        # graded on, cannot terminate here. D-EX-028.
        "naive_enumeration_feasible": False,
        # The previous record said `"truncated": False` next to
        # `"enumerated": None`, which is literally true only because no
        # enumeration was ever attempted and reads exactly like one that ran and
        # came back clean. `truncated` is null when nothing was run, and the
        # flag below says so outright rather than leaving it to be inferred.
        "enumeration_attempted": False,
        "enumerated": None,
        "truncated": None,
        "cap": MAX_ENUMERATION,
        "enumeration_refused_because": (
            "the construction exhibits 2^%d = %d distinct reachable states, "
            "past the cap of %d, so a forward enumeration under this cap cannot "
            "terminate. Derived from the bound rather than timed, because a "
            "timeout would not carry the claim (engine-rig D-024) and because "
            "running it on every build costs seconds for a result the bound "
            "already fixes. The enumerator is nonetheless run against every "
            "class (ii) level in the suite, by "
            "`test_class_ii_levels_actually_truncate_the_enumerator`, so the "
            "derivation's premise is checked rather than trusted."
            % (bound["m"], bound["lower_bound"], MAX_ENUMERATION)),
        "lower_bound": bound["lower_bound"],
        "m": bound["m"],
        "dippable_switches": bound["dippable_switches"],
        "positional_states": quotient,
        "arithmetic": bound["arithmetic"],
        # Recorded as a measurement, and explicitly NOT as a search space.
        # D-EX-022 tried to derive `search_credible` from this number and was
        # withdrawn; the note says why, so the next reader does not repeat it.
        "quotient_note": (
            "%d reachable (cart, button) states. This is a measurement, not a "
            "search space: the quotient is NOT a sound abstraction of this "
            "level. It ignores `step_limit` entirely, and it carries no latch "
            "state, so on a require_all_switches board it can report the goal "
            "reachable when the level is unsolvable. `lower_bound` remains the "
            "honest statement of what a *naive* complete search must cover. "
            "D-EX-028 amends what that unsoundness licenses: it is one-sided. "
            "An over-approximation yields false `solvable`, never false "
            "`unsolvable`, so a goal in a different component IS a sound "
            "unsolvability proof -- which is why this item's own answer key is "
            "allowed to be computed that way, and why the search barrier here "
            "is apparent rather than real."
            % quotient),
    }


# ==================================================================== build

INSTRUCTIONS = """You are handed a level of a self-built pushing world (the A2 family) after a
wrapper has been applied to it. Decide whether it is solvable, and justify it.

THE WORLD
  The cart moves one cell per command in the command's direction. A wall or the
  board edge blocks it and nothing moves. Stepping into B presses the button:
  the button latches and the door D vanishes in the SAME transition, and the
  cart does not move. D is impassable until then. Entering P teleports the cart
  to X; the cart never rests on P. Stepping onto s latches that switch for good.
  You win on the frame where the cart is on G (and, where the item says so, all
  switches are latched, and the score clears the stated threshold).

THE WRAPPER
  Each item states its own: which commands survive (`commands`), which commands
  are relabelled before they reach the world (`relabelled`), the command budget
  (`budget`, null for none), and the hazard cells (`hazards`, drawn as `!`) on
  which the episode is declared lost.

YOUR ANSWER, per item
  {"claim": "unsolvable", "certificate": {...}}   -- see the grammar below
  {"claim": "unsolvable", "reason": "exhaustive_search"}
  {"claim": "solvable",   "witness": ["UP", "RIGHT", ...]}
  {"claim": "abstain"}

  Half the points are the claim. The other half are the reason, and the reason
  is checked: a certificate is verified against the board, a witness plan is
  replayed. A correct claim with an unverifiable reason scores the claim only.
  "exhaustive_search" is paid at 0.4 of the reason where the space is small
  enough for that to be true, and at nothing where it is not.

THE CERTIFICATE GRAMMAR (closed -- an unlisted kind or an extra field is refused)

  {"kind": "invariant", "invariant": NAME, "initial_value": V, "goal_value": W}
      NAME is "cart_row", "cart_col" or "cart_region".
      cart_row / cart_col: V and W are the start's and goal's row / column. The
        checker verifies that every surviving command has a row (column) delta
        of a single sign -- teleport jumps included -- and that the goal is on
        the wrong side.
      cart_region: V and W are the connected components' canonical
        representatives, written [row, col] -- the lexicographically smallest
        cell of the component, in the graph that joins two cells whenever some
        surviving command steps between them (teleport edges included, doors
        treated as open, switch state ignored).

  {"kind": "cut_set", "cells": [[r, c], ...]}
      Every listed cell must be a declared hazard, and deleting all of them must
      disconnect the goal from the start in that same graph.

  {"kind": "counting", "bound": N, "limit": M}
      M is the item's budget; N is a lower bound on the commands required. The
      checker recomputes its own lower bound and refuses N above it, and refuses
      the argument unless M < N.
"""


def build() -> Paper:
    """Deterministic. Two calls produce byte-identical sheets and specs."""
    guard.assert_synthetic_world(WORLD_ID)
    os.makedirs(SPEC_DIR, exist_ok=True)

    items: List[Item] = []
    base_atrium = a2_echo()

    # ---------------------------------------------------- class (i): small
    # Exhaustive search is feasible on every one of these, and the enumeration
    # is run to prove it. The question is the reason.

    # (i-a) the teleport's only entrance is a DOWN command; remove DOWN and the
    #       right room is an island. A complete searcher stops here too.
    lvl = variant_of(base_atrium, "atrium", forbidden=["DOWN"])
    spec = _emit_spec(_spec(
        "a2var-i1-atrium-nodown", "atrium", "unsolvable",
        "Column 5 of the atrium board is solid wall from r1 to r7, so the right "
        "room touches the left room nowhere; its only entrance is the teleport "
        "at (7,4), and (7,4) is enterable only from the door cell (6,4) by a "
        "DOWN command -- its other three neighbours are wall. Forbidding DOWN "
        "therefore deletes the single edge joining the two rooms, and the cart's "
        "connected component is closed under every surviving command. The goal "
        "(2,7) lies in the other component. This follows from the board and the "
        "operator; no play is required to know it.",
        [{"op": "forbid_action", "action": "DOWN"}],
        "The forbidden command is never forwarded, so the arm observes an "
        "unchanged frame -- the wrapper-legal way to remove an action."))
    items.append(_make_item(
        "i1", lvl, "small_unsolvable", "unsolvable",
        {"kind": "invariant", "invariant": "cart_region",
         "initial_value": _region_rep(lvl, "start"),
         "goal_value": _region_rep(lvl, "goal")},
        None, _small_space(lvl), spec,
        "forbidding DOWN deletes the teleport's only entering edge, so the right "
        "room is a separate component of the board", POINTS_UNSOLVABLE))

    # (i-b) the closed invariant is one subtraction: no surviving command raises
    #       the cart.
    lvl = variant_of(updraft(), "updraft", forbidden=["UP"])
    spec = _emit_spec(_spec(
        "a2var-i2-updraft-noup", "updraft", "unsolvable",
        "The updraft board carries no teleport, so every command displaces the "
        "cart by one of the four unit vectors or by nothing at all. With UP "
        "forbidden the surviving displacements have row components 0, +1 and 0, "
        "so the cart's row never decreases. It starts at row 5 and the goal is "
        "at row 1. The argument is four subtractions over the action alphabet "
        "and does not look at the state space at all.",
        [{"op": "forbid_action", "action": "UP"}],
        "A monotone potential is the cheapest closed invariant this operator "
        "library can construct, and it is the one that scales."))
    items.append(_make_item(
        "i2", lvl, "small_unsolvable", "unsolvable",
        {"kind": "invariant", "invariant": "cart_row",
         "initial_value": 5, "goal_value": 1},
        None, _small_space(lvl), spec,
        "with UP forbidden the cart's row is non-decreasing and the goal is "
        "above the start", POINTS_UNSOLVABLE))

    # (i-c) a cut set of size one.
    lvl = variant_of(cistern(), "cistern", lost_cells=[[3, 5]])
    spec = _emit_spec(_spec(
        "a2var-i3-cistern-cut", "cistern", "unsolvable",
        "The cistern board's two halves are joined by exactly one floor cell, "
        "(3,5): column 5 is wall at every other row. Every path from the start "
        "(3,1) to the goal (3,9) therefore occupies (3,5) at the end of some "
        "command -- there is no teleport and no slide on this board, so a cell "
        "cannot be crossed without being stood on. Declaring a loss there makes "
        "every such path terminate before it arrives.",
        [{"op": "observation_loss", "cells": [[3, 5]], "value": CART_COLOUR}],
        "Value 6 is the cart's colour in A2's palette, so the predicate reads "
        "'the cart is standing on this cell' in the frame the arm acts on."))
    items.append(_make_item(
        "i3", lvl, "small_unsolvable", "unsolvable",
        {"kind": "cut_set", "cells": [[3, 5]]},
        None, _small_space(lvl), spec,
        "(3,5) is the only cell joining the cistern's halves and the wrapper "
        "declares a loss on it", POINTS_UNSOLVABLE))

    # (i-d) arithmetic, not search.
    atrium_distance = relaxed_distance(Level(base_atrium), (5, 1), (2, 7))
    budget = atrium_distance - 4
    lvl = variant_of(base_atrium, "atrium", step_limit=budget)
    spec = _emit_spec(_spec(
        "a2var-i4-atrium-budget", "atrium", "unsolvable",
        "Counting settles it. One command displaces the cart by at most one "
        "edge of the board's adjacency graph -- a blocked move and a button "
        "press displace it by none, and the teleport is a single edge from "
        "(6,4) to (7,6). In that graph the goal (2,7) is %d edges from the start "
        "(5,1), so at least %d commands are needed under any policy whatsoever. "
        "The budget is %d. The bound is deliberately loose: it ignores the door, "
        "the button and the order of anything, so it survives every relabelling."
        % (atrium_distance, atrium_distance, budget),
        [{"op": "step_limit", "limit": budget}],
        "The real shortest solution is longer still (the button detour), which "
        "is why a loose bound is the honest one to state."))
    items.append(_make_item(
        "i4", lvl, "small_unsolvable", "unsolvable",
        {"kind": "counting", "bound": atrium_distance, "limit": budget},
        None, _small_space(lvl), spec,
        "the relaxed board admits no path to the goal shorter than %d commands "
        "and the budget is %d" % (atrium_distance, budget), POINTS_UNSOLVABLE))

    # (i-e) the operator is a red herring; the wall does the work.
    lvl = variant_of(quarry(), "quarry",
                     remap={"LEFT": "RIGHT", "RIGHT": "LEFT"})
    spec = _emit_spec(_spec(
        "a2var-i5-quarry-swap", "quarry", "unsolvable",
        "The quarry board's goal room is enclosed by static wall on all four "
        "sides: row 3 is solid, row 6 is solid, and columns 0 and 8 are the "
        "border. No wrapper operator can open a wall, and relabelling LEFT and "
        "RIGHT is a bijection on the alphabet, so the set of reachable cells is "
        "exactly the base game's. The start (1,1) and the goal (4,7) lie in "
        "different connected components of the board, and did before the "
        "operator was applied.",
        [{"op": "remap_action", "from": "LEFT", "to": "RIGHT"},
         {"op": "remap_action", "from": "RIGHT", "to": "LEFT"}],
        "An item whose operator is irrelevant is a control: it catches an "
        "examinee that reasons about the wrapper instead of the board."))
    items.append(_make_item(
        "i5", lvl, "small_unsolvable", "unsolvable",
        {"kind": "invariant", "invariant": "cart_region",
         "initial_value": _region_rep(lvl, "start"),
         "goal_value": _region_rep(lvl, "goal")},
        None, _small_space(lvl), spec,
        "the quarry's goal room is sealed by static wall and a relabelling "
        "cannot open it", POINTS_UNSOLVABLE))

    # -------------------------------------------------- class (ii): large
    # Enumeration is out of reach and the bound says by how much. The truth is
    # still constructive: a wall, a severed corridor, an arithmetic budget.

    comb = comb_room("gantry", 60, None)
    lvl = variant_of(comb, "gantry", remap={"LEFT": "RIGHT", "RIGHT": "LEFT"})
    spec = _emit_spec(_spec(
        "a2var-ii1-gantry-sealed", "gantry", "unsolvable",
        "The gantry board's goal room (rows 5-6) sits under a separator row "
        "that is solid wall across its whole width, and is bounded by the "
        "border everywhere else, so it is a connected component of the board on "
        "its own. Relabelling LEFT and RIGHT is a bijection on the alphabet and "
        "cannot add an edge. The 120 latching switches make the state space "
        "astronomically large, which is exactly why the answer has to come from "
        "the partition rather than from a search: nothing about the switches "
        "touches the separator.",
        [{"op": "remap_action", "from": "LEFT", "to": "RIGHT"},
         {"op": "remap_action", "from": "RIGHT", "to": "LEFT"}],
        "The large-space twin of the quarry item: same argument, a state space "
        "no enumeration will reach."))
    items.append(_make_item(
        "ii1", lvl, "large_unsolvable", "unsolvable",
        {"kind": "invariant", "invariant": "cart_region",
         "initial_value": _region_rep(lvl, "start"),
         "goal_value": _region_rep(lvl, "goal")},
        None, _large_space(lvl), spec,
        "the gantry's goal room is a component of its own behind a solid "
        "separator row", POINTS_UNSOLVABLE))

    comb_bridge = comb_room("lattice", 60, 2)
    lvl = variant_of(comb_bridge, "lattice", lost_cells=[[4, 2]])
    spec = _emit_spec(_spec(
        "a2var-ii2-lattice-bridge", "lattice", "unsolvable",
        "The lattice board's separator row is solid except at (4,2), so that "
        "single cell is the only join between the corridor half and the goal "
        "room. There is no teleport on this board, so the cell cannot be "
        "crossed without being occupied at the end of a command. Declaring a "
        "loss on (4,2) severs the only join; the goal room becomes unreachable "
        "however the 120 switches are set, since no switch alters the geometry.",
        [{"op": "observation_loss", "cells": [[4, 2]], "value": CART_COLOUR}],
        "A cut set of size one over a state space of at least 2^120: the class "
        "(i) argument, on a board where the class (i) method cannot run."))
    items.append(_make_item(
        "ii2", lvl, "large_unsolvable", "unsolvable",
        {"kind": "cut_set", "cells": [[4, 2]]},
        None, _large_space(lvl), spec,
        "(4,2) is the lattice's only bridge to the goal room and the wrapper "
        "declares a loss on it", POINTS_UNSOLVABLE))

    long_comb = comb_open("spindle", 200, 1, 200)
    spindle_distance = relaxed_distance(Level(long_comb), (2, 1), (2, 200))
    spindle_budget = 150
    lvl = variant_of(long_comb, "spindle", step_limit=spindle_budget)
    spec = _emit_spec(_spec(
        "a2var-ii3-spindle-budget", "spindle", "unsolvable",
        "The spindle's corridor is 200 cells long, the cart starts at (2,1) and "
        "the goal is at (2,200). One command moves the cart at most one edge, "
        "and the board has no teleport, so at least %d commands are needed. The "
        "budget is %d. The 400 switches do not enter the argument at all, which "
        "is the point: they put the reachable set past 10^18 states, so the "
        "verdict cannot come from enumeration, while the counting argument "
        "needs only the corridor's length."
        % (spindle_distance, spindle_budget),
        [{"op": "step_limit", "limit": spindle_budget}],
        "The budget also caps how much of the switch space is reachable, so the "
        "recorded bound is computed against the budget rather than against the "
        "switch count."))
    items.append(_make_item(
        "ii3", lvl, "large_unsolvable", "unsolvable",
        {"kind": "counting", "bound": spindle_distance, "limit": spindle_budget},
        None, _large_space(lvl), spec,
        "the spindle's goal is %d commands away at best and the budget is %d"
        % (spindle_distance, spindle_budget), POINTS_UNSOLVABLE))

    drift = comb_open("orchard", 60, 2, 1)
    lvl = variant_of(drift, "orchard", forbidden=["LEFT"])
    spec = _emit_spec(_spec(
        "a2var-ii4-orchard-noleft", "orchard", "unsolvable",
        "The orchard board has no teleport, so every command displaces the cart "
        "by a unit vector or by nothing. With LEFT forbidden the surviving "
        "displacements have column components 0, 0 and +1, so the cart's column "
        "never decreases. It starts at column 2 and the goal is at column 1. "
        "The 118 switches still reachable from the start keep the naive state "
        "space past 10^35, so this verdict is not available to a plain forward "
        "enumeration; the monotone column costs three subtractions. (118 is "
        "reachable, not strictly-to-the-right: two of them, (1,2) and (3,2), "
        "sit directly above and below the start's own column. Strictly to the "
        "right there are 116, and 2^116 is 8.3e34, which would not clear "
        "10^35 -- the looser phrasing was worth one order of magnitude and is "
        "not used.)",
        [{"op": "forbid_action", "action": "LEFT"}],
        "The large-space twin of the updraft item, on the other axis."))
    items.append(_make_item(
        "ii4", lvl, "large_unsolvable", "unsolvable",
        {"kind": "invariant", "invariant": "cart_col",
         "initial_value": 2, "goal_value": 1},
        None, _large_space(lvl), spec,
        "with LEFT forbidden the orchard cart's column is non-decreasing and "
        "the goal is to its left", POINTS_UNSOLVABLE))

    # ------------------------------------------- class (iii): the trap
    # Solvable, and each one is the near-twin of an unsolvable item above. A
    # framework with a taste for unsolvability proofs is caught exactly here.

    lvl = variant_of(meander(), "meander",
                     remap={"LEFT": "RIGHT", "RIGHT": "LEFT"})
    witness, witness_source = _witness_by_search(lvl)
    spec = _emit_spec(_spec(
        "a2var-iii1-meander-swap", "meander", "solvable",
        "Relabelling is a bijection on the action alphabet, so it cannot change "
        "what is achievable: apply the swap to every command of a winning "
        "sequence in the base game and the wrapped game runs through exactly the "
        "same states. The meander's single serpentine route is about a hundred "
        "commands long, which is the whole difficulty -- a searcher that gives "
        "up at a shallow depth reports failure here, and failure to find is not "
        "a proof of absence.",
        [{"op": "remap_action", "from": "LEFT", "to": "RIGHT"},
         {"op": "remap_action", "from": "RIGHT", "to": "LEFT"}],
        "A long solution is the cheapest false-positive trap the operator "
        "library can build."))
    items.append(_make_item(
        "iii1", lvl, "solvable_hard", "solvable", None, witness,
        _small_space(lvl), spec,
        "the meander is one long corridor and a relabelling does not shorten or "
        "sever it", POINTS_SOLVABLE, witness_source=witness_source))

    lvl = variant_of(base_atrium, "atrium", step_limit=60)
    witness, witness_source = _witness_by_search(lvl)
    spec = _emit_spec(_spec(
        "a2var-iii2-atrium-roomy", "atrium", "solvable",
        "A step limit is only an obstacle when it falls below what the level "
        "needs. The atrium's shortest winning sequence is eighteen commands -- "
        "up to the button, back down, across to the door, down through the "
        "teleport, up the right room and onto the goal -- and the budget here is "
        "60. The wrapper therefore removes nothing: every winning sequence of "
        "the base game is still a winning sequence.",
        [{"op": "step_limit", "limit": 60}],
        "The near-twin of the budgeted unsolvable item on the same board. The "
        "operator is identical in kind; only the arithmetic differs."))
    items.append(_make_item(
        "iii2", lvl, "solvable_hard", "solvable", None, witness,
        _small_space(lvl), spec,
        "the atrium needs eighteen commands and the budget is sixty",
        POINTS_SOLVABLE, witness_source=witness_source))

    lvl = variant_of(base_atrium, "atrium", lost_cells=[[1, 3], [1, 4], [3, 3]])
    witness, witness_source = _witness_by_search(lvl)
    spec = _emit_spec(_spec(
        "a2var-iii3-atrium-offpath", "atrium", "solvable",
        "The three declared hazards (1,3), (1,4) and (3,3) sit in the middle of "
        "the left room, and none of them lies on THIS route: up column 1 to "
        "press the button, back down column 1, right along rows 5 and 6 to the "
        "door, through the teleport and up column 6. That route is 18 commands, "
        "it avoids all three cells, and exhibiting it settles the question -- a "
        "surviving route is a proof of solvability all by itself. Note what is "
        "deliberately NOT claimed: the hazards are not off *every* minimal "
        "route. (3,3) lies on 72 of the atrium's 204 shortest winning "
        "sequences, and 132 of them avoid all three cells.",
        [{"op": "observation_loss", "cells": [[1, 3], [1, 4], [3, 3]],
          "value": CART_COLOUR}],
        "The near-twin of the cistern cut: same operator, cells that do not cut."))
    items.append(_make_item(
        "iii3", lvl, "solvable_hard", "solvable", None, witness,
        _small_space(lvl), spec,
        "the atrium's three hazards sit off every minimal route and do not "
        "disconnect the board", POINTS_SOLVABLE, witness_source=witness_source))

    lvl = variant_of(base_atrium, "atrium", forbidden=["LEFT"])
    witness, witness_source = _witness_by_search(lvl)
    spec = _emit_spec(_spec(
        "a2var-iii4-atrium-noleft", "atrium", "solvable",
        "The atrium's route never moves the cart leftwards: it goes up column 1 "
        "to the button, back down column 1, rightwards along the lower rows to "
        "the door, down through the teleport into (7,6), and up column 6 to the "
        "goal at (2,7) by a final rightward step. Forbidding LEFT therefore "
        "removes a command the winning sequence does not contain, and the "
        "sequence still wins.",
        [{"op": "forbid_action", "action": "LEFT"}],
        "The near-twin of the forbidden-DOWN item on the same board: the same "
        "operator, an action the solution does not need."))
    items.append(_make_item(
        "iii4", lvl, "solvable_hard", "solvable", None, witness,
        _small_space(lvl), spec,
        "the atrium's winning sequence contains no LEFT command", POINTS_SOLVABLE, witness_source=witness_source))

    lvl = variant_of(base_atrium, "atrium", win_score_required=1)
    witness, witness_source = _witness_by_search(lvl)
    spec = _emit_spec(_spec(
        "a2var-iii5-atrium-tighten", "atrium", "solvable",
        "The level awards one point on victory and the tightened win test asks "
        "for at least one, so the test is satisfied by exactly the frames that "
        "satisfied it before. A tightened victory condition that a winning "
        "frame already meets changes nothing about which sequences win; it is "
        "the boundary case of the operator, and it is on the paper so that an "
        "examinee cannot read 'win_tighten' as a synonym for 'unsolvable'.",
        [{"op": "win_tighten", "require": {"kind": "score_at_least", "value": 1}}],
        "The fifth wrapper operator, exercised at its no-op boundary. There is "
        "no unsolvable win_tighten item because an A2-family level has a single "
        "binary victory test, so any threshold above one would be unsolvable "
        "for a reason no certificate in the grammar states."))
    items.append(_make_item(
        "iii5", lvl, "solvable_hard", "solvable", None, witness,
        _small_space(lvl), spec,
        "the tightened win test asks for a score the winning frame already "
        "carries", POINTS_SOLVABLE, witness_source=witness_source))

    # The three large solvable items: the same boards as class (ii), one
    # operator away from unsolvable. This is where a framework that has learned
    # "big comb board -> unsolvable" is caught.
    lvl = variant_of(comb_room("lattice", 60, 2), "lattice",
                     lost_cells=[[6, 10], [6, 20], [6, 30]])
    witness, witness_source = _witness_by_construction(lvl)
    spec = _emit_spec(_spec(
        "a2var-iii6-lattice-safe", "lattice", "solvable",
        "The three declared hazards all sit in row 6, the goal room's back row, "
        "while the bridge at (4,2), the goal at (5,60) and the whole of row 5 "
        "are untouched. Deleting the three cells leaves the corridor, the "
        "switch rows, the bridge and row 5 connected, so a plan exists that "
        "dips into all 120 switches from the corridor, crosses the bridge and "
        "walks row 5 to the goal without ever standing on a hazard. The plan is "
        "long, which is the difficulty, not the verdict.",
        [{"op": "observation_loss", "cells": [[6, 10], [6, 20], [6, 30]],
          "value": CART_COLOUR}],
        "The near-twin of the severed lattice: same board, same operator, cells "
        "that are not the bridge."))
    items.append(_make_item(
        "iii6", lvl, "solvable_hard", "solvable", None, witness,
        _large_space(lvl), spec,
        "the lattice's hazards are in the goal room's back row and the bridge "
        "at (4,2) is untouched", POINTS_SOLVABLE, witness_source=witness_source))

    base_room = comb_room("lattice", 60, 2)
    plan = waypoint_plan(Level(base_room))
    assert plan is not None
    roomy_budget = len(plan) + 40
    lvl = variant_of(base_room, "lattice", step_limit=roomy_budget)
    witness, witness_source = _witness_by_construction(lvl)
    spec = _emit_spec(_spec(
        "a2var-iii7-lattice-roomy", "lattice", "solvable",
        "A plan that visits every switch and then the goal is constructed "
        "directly from the board's shape, with no search: take the switches in "
        "column order and chain shortest hops between them, then cross the "
        "bridge at (4,2) and walk row 5 to the goal. The plan that construction "
        "yields costs %d commands and the budget is %d, so the budget is not an "
        "obstacle and the level's 2^120 states are irrelevant to saying so. The "
        "cost is stated for the plan actually shipped in the key rather than "
        "for the tidier corridor sweep it is easy to describe -- that one runs "
        "along row 2 and costs 418, also inside the budget, but it is not this "
        "item's witness and quoting its number here would be quoting an "
        "arithmetic that belongs to a different plan."
        % (len(plan), roomy_budget),
        [{"op": "step_limit", "limit": roomy_budget}],
        "The near-twin of the spindle's budget item: the same operator, "
        "arithmetic that goes the other way."))
    items.append(_make_item(
        "iii7", lvl, "solvable_hard", "solvable", None, witness,
        _large_space(lvl), spec,
        "a constructed sweep visits every lattice switch and reaches the goal "
        "in %d commands, inside the budget of %d" % (len(plan), roomy_budget),
        POINTS_SOLVABLE, witness_source=witness_source))

    lvl = variant_of(comb_room("lattice", 60, 2), "lattice",
                     remap={"LEFT": "RIGHT", "RIGHT": "LEFT"})
    witness, witness_source = _witness_by_construction(lvl)
    spec = _emit_spec(_spec(
        "a2var-iii8-lattice-swap", "lattice", "solvable",
        "Relabelling LEFT and RIGHT is a bijection on the alphabet and its own "
        "inverse, so it maps winning sequences to winning sequences one for "
        "one. So it is enough that the base level is solvable, and it is: this "
        "board requires every one of its 120 switches latched AS WELL AS the "
        "cart on the goal, and the corridor sweep that dips into all 120 from "
        "row 2 and then crosses the open bridge at (4,2) does both. Reaching "
        "the goal is not winning here -- the 62-command walk straight to the "
        "goal loses -- which is why the switches are named rather than left "
        "implicit. The board is the same board as the sealed gantry item, which "
        "is the trap: the separator row is what decides these, not the size of "
        "the state space.",
        [{"op": "remap_action", "from": "LEFT", "to": "RIGHT"},
         {"op": "remap_action", "from": "RIGHT", "to": "LEFT"}],
        "Same operator as the sealed gantry item, opposite answer."))
    items.append(_make_item(
        "iii8", lvl, "solvable_hard", "solvable", None, witness,
        _large_space(lvl), spec,
        "the lattice's bridge is open and a relabelling preserves solvability",
        POINTS_SOLVABLE, witness_source=witness_source))

    # ------------------------------------------------------------- shuffle
    # Deterministic, and keyed on the item id rather than on anything about the
    # item, so that answer cannot correlate with position. `exam.leakage`'s
    # positional report is what checks this rather than takes our word.
    items.sort(key=lambda it: hashlib.sha256(
        ("%s|order" % it.item_id).encode("utf-8")).hexdigest())

    _self_check(items)

    return Paper(
        paper_id=PAPER_ID,
        question_type=QUESTION_TYPE,
        instructions=INSTRUCTIONS,
        items=items,
        world=guard.provenance(),
        notes={
            "world": WORLD_ID,
            "family": "A2 (cold-start-a2/a2world) plus latching switches",
            "classes": {
                "small_unsolvable": "exhaustive search feasible; the question "
                                    "is the reason, not the verdict",
                # Was "enumeration out of reach; only invariant reasoning
                # answers". The second clause is withdrawn: it is a universal
                # over all methods that no experiment can establish, and it is
                # false as stated, since these boards are settled by an
                # exhaustive walk of a 300-node relaxed graph. D-EX-028.
                "large_unsolvable": "naive enumeration out of reach; the item "
                                    "is scored on selecting a method that is "
                                    "not naive enumeration",
                "solvable_hard": "the false-positive trap",
            },
            "large_space_threshold": LARGE_SPACE_THRESHOLD,
            "enumeration_cap": MAX_ENUMERATION,
            "specs": sorted(i.truth["spec"]["variant_id"] for i in items),
            "spec_digests": {i.truth["spec"]["variant_id"]:
                             i.truth["spec"]["spec_sha256"] for i in items},
            "operators_exercised": sorted({
                op for i in items for op in _ops_of(i)}),
            "phase4_note": (
                "The operator library and this whole procedure are frozen here, "
                "in a self-built world. Theoria.md Phase 4 orders the sealed "
                "campaign so that the exam subset is studied only after the main "
                "table has run; when that moment comes the only new work is the "
                "per-game justification."),
        },
    )


def _ops_of(item: Item) -> List[str]:
    """Read the operators off the emitted spec rather than off the level.

    The spec is the artefact Phase 4 freezes and `proxy.variants.Variant` is
    what validated it; re-deriving the list from the level's fields would be a
    second opinion that can disagree with the first, and `win_tighten` at its
    no-op boundary is exactly where it would.
    """
    return list(item.truth["spec"]["operators"])


def _region_rep(level_doc: Dict[str, Any], which: str) -> List[int]:
    """The canonical representative of the start's or the goal's component.

    Computed with the rubric's own code, so the reference certificate cannot
    drift away from the checker that will mark it.
    """
    from ..grading.rubrics_verdict import components, relaxed_edges

    level = Level(level_doc)
    rep = components(relaxed_edges(level))
    cell = level.start if which == "start" else level.goal
    return list(rep[cell])


def _self_check(items: Sequence[Item]) -> None:
    """Refuse to ship a paper whose own answers do not hold up.

    Three things, all of which have been wrong in a draft of this file at least
    once: a reference certificate the checker rejects, a witness plan that does
    not win, and a claim that disagrees with the emitted spec.  An exam whose
    key is unverified measures the key.
    """
    for item in items:
        truth = item.truth
        level = Level(json.loads(truth["level_blob"]))
        # The level's own fields first. `Level.step` and the checker's graph now
        # share one transition function, so a malformed level can no longer make
        # the checker unsound -- but it can still make the level a different
        # world from the one the justification describes, and in Phase 4 these
        # are transcribed from a game rather than written here. D-EX-020.
        problems = level.wellformed_problems()
        if problems:
            raise AssertionError("%s (%s): the level is malformed -- %s"
                                 % (item.item_id, truth["spec"]["variant_id"],
                                    "; ".join(problems)))
        if truth["claim"] == "solvable" and not truth.get("witness_source"):
            raise AssertionError(
                "%s: a solvable item must record whether its witness came from "
                "a search or from a construction. The paper's premise is that "
                "the answer follows from the construction; a key that will not "
                "say how its own answer was obtained cannot be checked against "
                "that premise." % item.item_id)
        if truth["certificate_blob"]:
            result = check_certificate(json.loads(truth["certificate_blob"]), level)
            if not result["ok"]:
                raise AssertionError("%s: reference certificate refused -- %s"
                                     % (item.item_id, result["why"]))
        if truth["claim"] == "solvable":
            if not truth["witness"]:
                raise AssertionError("%s: a solvable item without a witness plan "
                                     "is an assertion" % item.item_id)
            outcome = replay(level, truth["witness"])
            if not outcome["win"]:
                raise AssertionError("%s: witness plan does not win (%s)"
                                     % (item.item_id, outcome["status"]))
        elif truth["witness"] is not None:
            raise AssertionError("%s: an unsolvable item carries a witness"
                                 % item.item_id)


# ====================================================== reference examinees

def reference_answers(paper: Paper, key_doc: Optional[Dict[str, Any]] = None,
                      mode: str = "oracle") -> Dict[str, Any]:
    """The four calibration examinees of `exam.papers.CALIBRATION_MODES`.

    `bluffer` is the one that matters: it says "unsolvable" to everything, with
    no certificate, and the tests assert it scores sensitivity 1.0, specificity
    0.0 and under a quarter of the paper.  That triple is the calibration that
    proves the rubric is scoring reasoning rather than confidence -- Theoria.md
    1.11's "灵敏度与特异度一起打分", made into an assertion.
    """
    truths = _truths(paper, key_doc)
    if mode == "null":
        return {}
    if mode == "bluffer":
        return {item_id: {"claim": "unsolvable"} for item_id in truths}

    answers: Dict[str, Any] = {}
    for item_id, truth in truths.items():
        if mode == "memoriser" and truth["board_size_class"] != "small":
            continue
        answer: Dict[str, Any] = {"claim": truth["claim"]}
        if truth["certificate_blob"]:
            answer["certificate"] = json.loads(truth["certificate_blob"])
        if truth["witness"]:
            answer["witness"] = list(truth["witness"])
        answers[item_id] = answer
    return answers


def _truths(paper: Paper, key_doc: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if key_doc is not None:
        return {entry["item_id"]: entry["truth"] for entry in key_doc["items"]}
    return {item.item_id: item.truth for item in paper.items}


# ==================================================================== axes

def axes(report: Any, key_doc: Dict[str, Any], submission: Any) -> Dict[str, Any]:
    """Sensitivity and specificity together, plus the reason breakdown.

    Both, always.  Theoria.md 1.11 is explicit that a verdict paper reporting
    accuracy alone is measuring the wrong thing -- a framework that answers
    "unsolvable" to every question has perfect sensitivity and is worthless --
    and the reason breakdown is the other half of the same complaint: class (i)
    exists because a right verdict can be reached by a method that does not
    transfer, and a paper that reports only accuracy cannot see that at all.
    """
    truth_of = {entry["item_id"]: entry["truth"] for entry in key_doc["items"]}
    detail_of = {score.item_id: score.detail for score in report.scores}

    by_class: Dict[str, Dict[str, float]] = {}
    by_board: Dict[str, Dict[str, float]] = {}
    reasons: Dict[str, int] = {}
    for score in report.scores:
        truth = truth_of.get(score.item_id, {})
        for bucket, key in ((by_class, truth.get("class", "?")),
                            (by_board, truth.get("board_size_class", "?"))):
            row = bucket.setdefault(key, {"n": 0, "awarded": 0.0, "possible": 0.0})
            row["n"] += 1
            row["awarded"] += score.awarded
            row["possible"] += score.possible
        reason = detail_of.get(score.item_id, {}).get("reason")
        if score.verdict == "unanswered":
            reason = "unanswered"
        reasons[reason or "none"] = reasons.get(reason or "none", 0) + 1

    for bucket in (by_class, by_board):
        for row in bucket.values():
            row["awarded"] = round(row["awarded"], 6)
            row["possible"] = round(row["possible"], 6)
            row["fraction"] = (round(row["awarded"] / row["possible"], 6)
                               if row["possible"] else 0.0)

    n_certified = reasons.get("certificate", 0)
    n_unsolvable_right = sum(
        1 for s in report.scores
        if s.verdict == "correct" and truth_of.get(s.item_id, {}).get("claim") == "unsolvable")

    # The pair, per board-size stratum. The class taxonomy is one-to-one with
    # the answer -- classes (i) and (ii) hold only unsolvable items and class
    # (iii) only solvable ones -- so no class cell can hold both rates and the
    # pair exists only pooled, which is the reading D-EX-015 shows cannot
    # separate ground truth from a reader who never saw a board.
    # `board_size_class` cross-cuts the answer (small 5/5, large 4/3) and splits
    # on the very distinction classes (i) and (ii) were invented to draw.
    # D-EX-024.
    from ..grading.confusion_matrix import per_class_confusion

    return {
        "confusion": confusion(report, key_doc, positive="unsolvable"),
        "confusion_by_board_size": per_class_confusion(
            report, key_doc, positive="unsolvable")["by_board_size"],
        "reason_quality": {
            "counts": dict(sorted(reasons.items())),
            "certified_share_of_correct_unsolvable": (
                round(n_certified / n_unsolvable_right, 6) if n_unsolvable_right else None),
            "note": ("A right 'unsolvable' backed by a certificate and a right "
                     "'unsolvable' backed by 'I searched everything' are the "
                     "same verdict and not the same answer. Theoria.md 1.11 "
                     "class (i) is about precisely this gap."),
        },
        "by_class": dict(sorted(by_class.items())),
        "by_board_size": dict(sorted(by_board.items())),
    }
