"""分层移交测试 — the layered handover paper (Theoria.md 1.11, 题型 2).

> 全新实例、无历史无上下文,分两档交付——只交说明书,或说明书 + 玩法书。
> 新读者打平作者 = 理解在文档里;两档之差 = 战略知识的价值。
> 凡有交付物的臂都考——Schema 交裸 world_model.py…CC 无物可交记零。

This module is the machinery, not the experiment.  It builds the paper, emits
the two delivery bundles, and computes the author baseline.  The fresh readers
are spawned elsewhere; **nothing here calls a model and nothing here opens a
socket**.

--------------------------------------------------------------------------
The three question families, and why these three
--------------------------------------------------------------------------

*step semantics* asks what one action does.  It is the floor: a reader who
cannot single-step the world has not received a manual, whatever else the
bundle contains.  Eleven items cover all five rules of the A0 manual, including
both ways a push can fail — the cell the Box would **cross** being blocked and
the cell it would **land on** being blocked.  That pair is not padding: it is
the exact distinction `a0-spike`'s own theory got wrong for 1,966 transitions
(README finding 5), because in the level it was mined from the crossing case is
*unreachable*.  A handover that does not test it is testing a level.

*which names are level data* is the family that separates understanding from
pattern-matching.  A reader who saw one instance and generalised from it will
believe the walls, the target and the starting cells are facts about the world.
A reader who understood the manual will notice that the manual never mentions a
wall, a target cell or a starting position anywhere — it speaks only of `free`,
`ahead`, `beyond` and parity — and will conclude that those are supplied from
outside.  Twelve names, seven supplied by the instance and five fixed by the
world.

*optimal action* is where the playbook is supposed to pay.  Truth comes from the
world's own BFS oracle (`world.sokoban2.solve_bfs`), and the accepted answer is
**any** action that lies on some shortest solution.  Marking against the single
plan BFS happened to return would fail a reader for disagreeing with a loop
order; the truth therefore carries the whole optimal set, and the test suite
re-derives that set by brute force so it cannot silently narrow.

--------------------------------------------------------------------------
What the bundles contain, and what was taken out
--------------------------------------------------------------------------

Both tiers are self-contained: the text is **copied in**, never referenced by
repository path, because a fresh reader has no repository.  Provenance (source
path plus sha256) is recorded in each bundle's `MANIFEST.json` so that "is this
really the deliverable?" stays checkable.

`tier1_manual/` carries the manual and nothing else:

  * `MANUAL.dsl`  — `a0-spike/theory/theory.dsl` verbatim, LF-normalised.  This
    is the form Theoria 1.8 hands to the third reader ("全新的 agent,读源文件
    本体"), so it is handed over unedited, adjudication comments and all.
  * `MANUAL.md`   — a deterministic rendering of that source produced by
    `render_manual()` below.  No model is in that path and none may be
    (1.8: 不过 LLM,不许润色).  The track's own `gen_markdown` could not be
    used: its parser now refuses a manual with no `semantics:` section, and the
    A0 manual predates that section — see `_AUTHOR_BASELINE_NOTE`.

`tier2_manual_playbook/` carries the same two files plus `PLAYBOOK.dsl` and
`PLAYBOOK.md`: deadlock patterns, a search heuristic, move ordering, and what
the conservation law is *for*.  `a0-spike` shipped no playbook file — only
`theory/theory.dsl` — so the strategic tier was assembled from the findings that
directory does record (README findings 1 and 5, the parity law of `laws:`, and
the `[depends: push2]` edge that `pipeline/adapt.py` measures).  That assembly
is stated here rather than hidden: the tier-2 bundle is *this exam's* rendering
of A0's strategy, and a future A0 that emits a real playbook should replace it.

**Three things were deliberately kept out of both bundles**, because each would
have turned a question into a lookup:

  1. *Every worked example.*  No bundle file contains a concrete state, a
     concrete action, or a step-by-step trace.  A single worked push on a
     concrete board would answer four step-semantics items outright.  The
     playbook's deadlock patterns are therefore stated over `Box.pos` and
     `target` symbolically and mention no coordinate anywhere.
  2. *Every level.*  No walls, no board size, no target cell, no starting
     positions.  Beyond the leak, naming one level is precisely the mistake the
     level-data family is testing for; a bundle that shipped a level would teach
     the reader to treat that level's furniture as world law.
  3. *The words that name the answer.*  `level_data`, `world_law`, "varies per
     level", "fixed across levels" appear in no manual or playbook file.  They
     appear only in `READER_BRIEF.md`, where they are the answer *alphabet* —
     which every examinee must have, and which gives nothing away because it
     labels no name.  `exam/tests/test_handover.py` asserts both halves.

--------------------------------------------------------------------------
One defect of the deliverable, found while building this and kept
--------------------------------------------------------------------------

The A0 manual writes its conservation laws with a constant from one particular
board baked in:

    invariant box_row_parity (Box.pos.row) mod 2 = 1  [status: proven]

The *conservation* is a law of this world; the `1` is a fact about the board
that manual was mined on, and on any board whose Box starts on an even row the
sentence is false as written.  All three invariants are written this way.

Two things follow, and neither is worked around.  The bundles carry the laws
verbatim, defect included, because a handover test that quietly repaired the
deliverable would be examining a document nobody shipped.  And the vocabulary
family splits the two apart into `box_row_parity` (the conservation — a world
law) and `box_row_parity_value` (the `= 1` — supplied by the board), so a reader
who noticed can say so and a reader who did not is measured rather than merely
confused.  Expect the tier-2 reader to have a small edge on that one item: the
playbook states the parity test in relative terms — compare the Box's parity
with the target's — and that phrasing points at the answer.  It is one point of
forty-six, and it is a real difference between the tiers rather than a leak, but
it should be discounted when the tier delta is read.

--------------------------------------------------------------------------
The author baseline
--------------------------------------------------------------------------

「新读者打平作者」 needs an author to draw level with, and the honest author is
not the human who wrote the manual — it is **the manual itself**, executed.
`author_answers()` answers the whole sheet from the deliverable's compiled
executable form and from nothing else:

  * step semantics — run the compiled `step` and report which rule fired;
  * optimal action — breadth-first search over that same compiled `step`
    (this is what the A0 planner does; the world's oracle is never consulted);
  * level data vs world law — instantiate the deliverable twice, once per level,
    and compare a stated observable per name.  A name whose observable must be
    rebound to move the deliverable to another instance is supplied by the
    instance; a name whose observable is untouched is fixed by the world.  The
    criterion *is* the question, mechanised.

The resulting score is stored in the **truth** file (`Paper.notes`), never on
the sheet — an examinee who could see the author's answers would be sitting a
different exam.

--------------------------------------------------------------------------
Leakage
--------------------------------------------------------------------------

Every item declares two probes: the answer written in the published grammar and
the answer serialised as JSON, which are the two forms in which a builder
accidentally leaves an answer lying around.  What is *not* used as a probe is a
bare token of an answer alphabet — `walk`, `LEFT`, `world_law`.  Those appear on
every clean sheet by necessity (the reader is told the alphabet), so probing for
them would report a hit on a paper with nothing wrong with it and train the
reader to ignore the tool, exactly as `leakage.probe_hits` refuses probes under
three characters for the same reason.

The bundles are checked with the same probe set as the sheet, because a bundle
is handed to the examinee just as the sheet is; a leak does not care which file
it travelled in.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import sys
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..guard import assert_synthetic_world, provenance
from ..model import (Item, ItemScore, Paper, Submission, canonical, sha256,
                     sha256_text)
from ..grading.rubrics_handover import (ACTIONS, NAME_CLASSES, RULE_NAMES,
                                        RUBRICS)

PAPER_ID = "p15-handover-a0"
QUESTION_TYPE = "handover"
WORLD_ID = "a0"

HERE = os.path.dirname(os.path.abspath(__file__))
EXAM = os.path.dirname(HERE)
REPO = os.path.dirname(EXAM)
A0 = os.path.join(REPO, "a0-spike")

MANUAL_SOURCE = os.path.join(A0, "theory", "theory.dsl")
EXEC_SOURCE = os.path.join(A0, "artifacts", "theory_exec.py")
GEN_EXEC_SOURCE = os.path.join(A0, "pipeline", "gen_exec.py")

#: Where `emit_bundles` writes by default.
BUNDLES_DIR = os.path.join(EXAM, "handover_bundles")

TIER1 = "tier1_manual"
TIER2 = "tier2_manual_playbook"
TIERS: Tuple[str, ...] = (TIER1, TIER2)

#: An arm may only be asked a handover question if it has something to hand
#: over.  Declaring this capability is the arm's claim that it does.
HANDOVER_CAPABILITY = "handover_bundle"

FAMILY_STEP = "step_semantics"
FAMILY_NAMES = "level_data_vs_world_law"
FAMILY_OPTIMAL = "optimal_action"
FAMILIES: Tuple[str, ...] = (FAMILY_STEP, FAMILY_NAMES, FAMILY_OPTIMAL)

POINTS = {FAMILY_STEP: 2.0, FAMILY_NAMES: 1.0, FAMILY_OPTIMAL: 2.0}


class HandoverError(RuntimeError):
    pass


class UnrenderableManual(HandoverError):
    """The manual uses a clause this renderer cannot put into words.

    Same discipline as `a0-spike/pipeline/gen_exec.py`: anything not understood
    is a hard error, never a silent omission.  A rendering that quietly dropped
    a guard would hand the reader a *different, weaker* world and the handover
    score would measure the drop.
    """


# =========================================================================
# the world, loaded without polluting sys.path
# =========================================================================

def _load_isolated(name: str, path: str) -> Any:
    """Import a file under a private module name.

    `a0-spike/world/sokoban2.py` would otherwise have to be reached through the
    top-level package name `world`, and putting `a0-spike` on `sys.path` inside
    an exam module would change what every *other* paper in the same process
    imports.  A guardrail that has side effects on its neighbours is not one.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise HandoverError("cannot load %s from %s" % (name, path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_SOKOBAN: Any = None


def world() -> Any:
    """The A0 ground truth.  Read-only, and only ever used to build truths."""
    global _SOKOBAN
    if _SOKOBAN is None:
        _SOKOBAN = _load_isolated(
            "exam._a0_sokoban2", os.path.join(A0, "world", "sokoban2.py"))
    return _SOKOBAN


# =========================================================================
# the levels
# =========================================================================

@dataclass(frozen=True)
class LevelSpec:
    """One fresh A0 instance.

    Fresh is the requirement (「全新实例」): none of these is `match`,
    `mismatch` or any of the four `crossing_*` levels the A0 run was built on,
    so a reader who somehow saw that run gains nothing.  The *world* is the same
    world — same rules, same push distance — which is the whole point: the
    manual is supposed to travel.
    """

    level_id: str
    height: int
    width: int
    walls: Tuple[Tuple[int, int], ...]
    target: Tuple[int, int]
    start_player: Tuple[int, int]
    start_box: Tuple[int, int]

    def sheet_block(self) -> Dict[str, Any]:
        """What the examinee is told about the geometry.  No start state: each
        item supplies its own, so a reader cannot answer by recalling one."""
        return {"level_id": self.level_id, "height": self.height,
                "width": self.width,
                "walls": [list(w) for w in self.walls],
                "target": list(self.target)}


LEVELS: Tuple[LevelSpec, ...] = (
    LevelSpec("corridor", 5, 7, ((1, 1), (1, 5), (3, 1), (3, 5)),
              target=(2, 1), start_player=(2, 4), start_box=(2, 3)),
    LevelSpec("pinch", 6, 6, ((0, 3), (2, 2), (3, 4), (4, 1)),
              target=(5, 5), start_player=(1, 4), start_box=(3, 5)),
    LevelSpec("yard", 7, 6, ((1, 2), (2, 4), (4, 2), (5, 4), (3, 0)),
              target=(5, 1), start_player=(1, 0), start_box=(3, 1)),
)

LEVEL_OF: Dict[str, LevelSpec] = {lv.level_id: lv for lv in LEVELS}


def _level(spec: LevelSpec, player: Tuple[int, int],
           box: Tuple[int, int]) -> Any:
    sk = world()
    return sk.Level(name=spec.level_id, height=spec.height, width=spec.width,
                    walls=spec.walls, player=player, box=box,
                    target=spec.target)


def ascii_board(spec: LevelSpec, player: Tuple[int, int],
                box: Tuple[int, int]) -> List[str]:
    """The geometry as a picture, because a wall list is unreadable at a glance.

    Precedence P > B > # > T > `.` is stated in the legend rather than left to
    be inferred: an ambiguous picture would make a step-semantics item a
    question about rendering.
    """
    rows = []
    for r in range(spec.height):
        line = []
        for c in range(spec.width):
            cell = (r, c)
            if cell == player:
                line.append("P")
            elif cell == box:
                line.append("B")
            elif cell in spec.walls:
                line.append("#")
            elif cell == spec.target:
                line.append("T")
            else:
                line.append(".")
        rows.append("".join(line))
    return rows


BOARD_LEGEND = ("P=Player  B=Box  #=wall  T=target cell  .=empty. "
                "Row 0 is the top row, column 0 the left column. "
                "If two of these share a cell the earlier letter is drawn, so "
                "the target is still the cell named in `target` even when it is "
                "not visible.")


# =========================================================================
# family 1 -- step semantics
# =========================================================================

#: (level_id, player, box, action).  Eleven transitions covering all five rules,
#: with both push failures and both kinds of obstruction (interior wall and
#: board edge) represented.  Written out rather than sampled: a randomly drawn
#: set is a different exam every time the seed moves, and 1.11's rubric-freezing
#: only means something if the paper is frozen too.
_STEP_CASES: Tuple[Tuple[str, Tuple[int, int], Tuple[int, int], str], ...] = (
    ("corridor", (2, 4), (2, 2), "UP"),        # walk, box irrelevant
    ("yard", (0, 0), (3, 3), "DOWN"),          # walk
    ("corridor", (2, 4), (2, 3), "LEFT"),      # push: two cells, pusher follows
    ("pinch", (0, 1), (1, 1), "DOWN"),         # push
    ("corridor", (2, 5), (0, 0), "UP"),        # wall ahead of the Player
    ("yard", (0, 2), (4, 4), "DOWN"),          # wall ahead of the Player
    ("corridor", (1, 3), (1, 2), "LEFT"),      # Box blocked on the crossed cell
    ("pinch", (2, 4), (2, 3), "LEFT"),         # Box blocked on the crossed cell
    ("corridor", (3, 4), (3, 3), "LEFT"),      # Box blocked on the landing cell
    ("pinch", (3, 3), (2, 3), "UP"),           # Box blocked on the landing cell
    ("corridor", (2, 2), (2, 1), "LEFT"),      # landing cell is off the board
)


def _which_rule(spec: LevelSpec, player: Tuple[int, int],
                box: Tuple[int, int], action: str) -> str:
    """Name the manual's rule that covers this transition.

    Derived from the *world*, not from the theory: the truth of a handover item
    is what the world does, and the rule name is the manual's word for it.  The
    five guards are mutually exclusive and total (a0-spike constraint 9), so
    exactly one branch below can be taken.
    """
    sk = world()
    state = sk.State(player=player, box=box)
    level = _level(spec, player, box)
    dr, dc = sk.DELTA[action]
    ahead = (player[0] + dr, player[1] + dc)
    if ahead != box:
        return "walk" if sk.free(level, ahead, state) else "blocked_wall"
    crossed = (box[0] + dr, box[1] + dc)
    landing = (box[0] + 2 * dr, box[1] + 2 * dc)
    if not sk.free(level, crossed, state):
        return "blocked_box_crossing"
    if not sk.free(level, landing, state):
        return "blocked_box_landing"
    return "push2"


def _step_truth(spec: LevelSpec, player: Tuple[int, int],
                box: Tuple[int, int], action: str) -> Dict[str, Any]:
    sk = world()
    nxt, _event = sk.step(_level(spec, player, box),
                          sk.State(player=player, box=box), action)
    return {"next_player": list(nxt.player), "next_box": list(nxt.box),
            "rule": _which_rule(spec, player, box, action)}


def step_answer_text(truth: Dict[str, Any]) -> str:
    return "player=(%d,%d); box=(%d,%d); rule=%s" % (
        truth["next_player"][0], truth["next_player"][1],
        truth["next_box"][0], truth["next_box"][1], truth["rule"])


# =========================================================================
# family 2 -- which names are level data
# =========================================================================

@dataclass(frozen=True)
class NameEntry:
    """One name of the manual's vocabulary, its definition, and its class.

    `observable` names the function used to answer this item *mechanically* from
    the deliverable — see `author_answers`.  It is recorded on the entry rather
    than buried in the baseline code so that the criterion the author baseline
    uses is visible next to the truth it is being compared against.
    """

    name: str
    definition: str
    cls: str
    observable: str


#: Twelve names, seven supplied by the board and five fixed by the world.
#:
#: The names and the definitions are length-matched on purpose.  A definition
#: that reads longer for one class than the other is a positional signal:
#: `leakage.positional_report` measures exactly that, and an examinee that never
#: read the manual could score above chance by answering "the long ones are the
#: laws".  `exam/tests/test_handover.py` asserts the two class means stay within
#: a few percent of each other, so the balance cannot rot silently when a
#: definition is reworded.
_VOCABULARY: Tuple[NameEntry, ...] = (
    NameEntry("wall_cells",
              "the cells of the board that are walls, whichever cells those are",
              "level_data", "walls"),
    NameEntry("target_cell",
              "the cell the Box must end up on for the goal clause to hold",
              "level_data", "target"),
    NameEntry("board_shape",
              "how many rows the board has and how many columns it has",
              "level_data", "board_shape"),
    NameEntry("box_start",
              "the cell the Box occupies before any action has been taken",
              "level_data", "box_start"),
    NameEntry("player_start",
              "the cell the Player occupies before any action has been taken",
              "level_data", "player_start"),
    NameEntry("reachable_box_cells",
              "the cells the Box can be made to occupy by some sequence of "
              "actions",
              "level_data", "reachable_box_cells"),
    NameEntry("push_distance",
              "how many cells the Box travels along when it is being pushed",
              "world_law", "push_distance"),
    NameEntry("walk_distance",
              "how many cells the Player travels along when it is walking",
              "world_law", "player_step_distance"),
    NameEntry("crossing_rule",
              "that a push needs the crossed cell free as well as the landing "
              "cell",
              "world_law", "crossing_requirement"),
    NameEntry("box_row_parity",
              "that `Box.pos.row mod 2` never changes, whatever is done",
              "world_law", "box_row_parity"),
    # The sharpest item on the paper, and it exists because the deliverable
    # has a defect.  The manual's laws section writes
    # `invariant box_row_parity (Box.pos.row) mod 2 = 1`: a conservation law
    # with the *value* from one particular board baked into it.  The
    # conservation is a world law; the 1 is not, and on any board whose Box
    # starts on an even row the manual's own sentence is false as written.
    # Splitting the two into separate items measures whether the reader noticed,
    # instead of leaving them to trip over it silently.
    NameEntry("box_row_parity_value",
              "that `Box.pos.row mod 2` is 1, the way the laws section spells "
              "it out",
              "level_data", "box_row_parity_value"),
    NameEntry("goal_form",
              "that the goal is the Box standing on the target cell, whichever "
              "cell that is",
              "world_law", "goal_form"),
)

#: name -> the observable the author baseline reads for it.  Kept separate from
#: the name so that rewording a vocabulary entry cannot silently change which
#: property of the deliverable is being measured.
_OBSERVABLE_OF: Dict[str, str] = {e.name: e.observable for e in _VOCABULARY}


def _shuffled(keys: Sequence[str]) -> List[int]:
    """A fixed, answer-independent order for a family's items.

    Neither the natural order (which groups the answers) nor a strict
    alternation (which makes the item index predict the answer) is acceptable to
    `leakage.positional_report`.  Ordering by the sha256 of a key that does not
    mention the answer gives a fixed permutation uncorrelated with it, with no
    seed to move and no RNG in the build.
    """
    return sorted(range(len(keys)),
                  key=lambda i: (hashlib.sha256(keys[i].encode("utf-8"))
                                 .hexdigest(), i))


# =========================================================================
# family 3 -- optimal action
# =========================================================================

#: (level_id, player, box).  Chosen so that no single action is optimal in more
#: than half of them: with four actions and set-valued truth, a reader who
#: answers the same direction every time should not look competent.  Three have
#: a unique optimal action and three have two, which is what makes "accept the
#: whole optimal set" a rule with teeth rather than a slogan.
_OPTIMAL_CASES: Tuple[Tuple[str, Tuple[int, int], Tuple[int, int]], ...] = (
    ("corridor", (0, 6), (2, 3)),
    ("corridor", (2, 6), (2, 3)),
    ("corridor", (3, 0), (2, 3)),
    ("pinch", (2, 1), (5, 3)),
    ("pinch", (2, 3), (1, 5)),
    ("yard", (0, 3), (1, 1)),
)


def _plan_length(spec: LevelSpec, player: Tuple[int, int],
                 box: Tuple[int, int]) -> Optional[int]:
    plan = world().solve_bfs(_level(spec, player, box))
    return None if plan is None else len(plan)


def optimal_actions(spec: LevelSpec, player: Tuple[int, int],
                    box: Tuple[int, int]) -> List[str]:
    """Every action lying on some shortest solution from this state.

    An action qualifies when it is not blocked and the shortest solution from
    where it leaves us is exactly one shorter.  That is the definition of "on an
    optimal path", and it is deliberately computed from the oracle's *distance*
    rather than from the plan the oracle returned: `solve_bfs` breaks ties by
    the order of `DIRECTIONS`, and a reader who picks the other tie is right.
    """
    sk = world()
    here = _plan_length(spec, player, box)
    if here is None or here == 0:
        raise HandoverError(
            "optimal-action item needs a solvable state with at least one "
            "action left to take; %s %s/%s has none"
            % (spec.level_id, player, box))
    out = []
    for action in sk.DIRECTIONS:
        nxt, event = sk.step(_level(spec, player, box),
                             sk.State(player=player, box=box), action)
        if event == sk.BLOCKED:
            continue
        there = _plan_length(spec, nxt.player, nxt.box)
        if there is not None and there == here - 1:
            out.append(action)
    if not out:
        raise HandoverError("no optimal action out of a solvable state -- the "
                            "oracle contradicts itself")
    return out


# =========================================================================
# the paper
# =========================================================================

INSTRUCTIONS = """\
You are a fresh reader of one framework's deliverable. You have been given a
bundle of documents and this sheet, and nothing else: no repository, no source
code beyond what the bundle contains, no history of earlier play, no
conversation. Everything you need is either in the bundle or in the item.

The world is a grid world. The bundle tells you how it behaves. This sheet tells
you, per item, the geometry of one board and (where relevant) where the Player
and the Box are standing.

Three kinds of question appear, distinguished by each item's `kind` field.

  kind = "step_semantics"
      One action is taken from the given situation. Say what the situation is
      afterwards and which rule of the manual accounts for it.
      Answer grammar, exactly:
          player=(row,col); box=(row,col); rule=<name>
      All three fields, in any order, separated by semicolons. `<name>` must be
      one of: %(rules)s

  kind = "name_class"
      A name is defined for you. Say whether it is something each board supplies
      (answer `level_data`) or something the world fixes once for every board
      (answer `world_law`).
      Answer grammar, exactly one word: %(classes)s

  kind = "optimal_action"
      Name one action that begins a shortest sequence putting the Box on the
      target cell. Where several actions do, any of them is accepted.
      Answer grammar, exactly one word: %(actions)s

Any item may instead be answered `abstain`. An abstention scores nothing and is
recorded as an abstention, not as a wrong answer; a guess is recorded as a wrong
answer. An answer that is not a sentence of the grammar above scores nothing and
the parse failure is recorded.

Submit a single JSON object mapping every item_id on this sheet to its answer
string. %(legend)s""" % {
    "rules": " | ".join(RULE_NAMES),
    "classes": " | ".join(NAME_CLASSES),
    "actions": " | ".join(ACTIONS),
    "legend": BOARD_LEGEND,
}


def _probes(item_id: str, canonical_answer: str,
            truth: Dict[str, Any]) -> Tuple[str, ...]:
    """The two forms in which an answer accidentally ends up on a sheet.

    Not probed: a bare token of the answer alphabet.  `walk`, `LEFT` and
    `world_law` are printed in the instructions above because the reader has to
    be told the alphabet, so probing for them would raise on a clean paper.
    `leakage.probe_hits` refuses sub-three-character probes for exactly this
    reason; a published alphabet token is the same failure with more letters.
    """
    return ("%s => %s" % (item_id, canonical_answer), canonical(truth))


def _step_items() -> List[Item]:
    keys = ["%s|%s|%s|%s" % (lv, p, b, a) for lv, p, b, a in _STEP_CASES]
    items = []
    for n, index in enumerate(_shuffled(keys), start=1):
        level_id, player, box, action = _STEP_CASES[index]
        spec = LEVEL_OF[level_id]
        truth = _step_truth(spec, player, box, action)
        item_id = "hv-step-%02d" % n
        items.append(Item(
            item_id=item_id,
            rubric_id="handover.step_semantics",
            points=POINTS[FAMILY_STEP],
            paper={
                "kind": "step_semantics",
                "level": spec.sheet_block(),
                "board": ascii_board(spec, player, box),
                "state": {"player": list(player), "box": list(box)},
                "action": action,
                "prompt": ("The Player takes the action %s. Give the situation "
                           "after the action and the rule that accounts for it."
                           % action),
            },
            truth=truth,
            leak_probes=_probes(item_id, step_answer_text(truth), truth),
            tags=(FAMILY_STEP, "level:" + level_id),
        ))
    return items


def _name_items() -> List[Item]:
    keys = [entry.name for entry in _VOCABULARY]
    items = []
    for n, index in enumerate(_shuffled(keys), start=1):
        entry = _VOCABULARY[index]
        truth = {"class": entry.cls}
        item_id = "hv-name-%02d" % n
        items.append(Item(
            item_id=item_id,
            rubric_id="handover.name_class",
            points=POINTS[FAMILY_NAMES],
            paper={
                "kind": "name_class",
                "name": entry.name,
                "definition": entry.definition,
                "prompt": ("Is `%s` supplied by each individual board, or fixed "
                           "by the world for every board?" % entry.name),
            },
            truth=truth,
            leak_probes=_probes(item_id, "%s => %s" % (entry.name, entry.cls),
                                truth),
            tags=(FAMILY_NAMES,),
        ))
    return items


def _optimal_items() -> List[Item]:
    keys = ["%s|%s|%s" % (lv, p, b) for lv, p, b in _OPTIMAL_CASES]
    items = []
    for n, index in enumerate(_shuffled(keys), start=1):
        level_id, player, box = _OPTIMAL_CASES[index]
        spec = LEVEL_OF[level_id]
        actions = optimal_actions(spec, player, box)
        truth = {"optimal_actions": actions,
                 "distance": _plan_length(spec, player, box)}
        item_id = "hv-opt-%02d" % n
        items.append(Item(
            item_id=item_id,
            rubric_id="handover.optimal_action",
            points=POINTS[FAMILY_OPTIMAL],
            paper={
                "kind": "optimal_action",
                "level": spec.sheet_block(),
                "board": ascii_board(spec, player, box),
                "state": {"player": list(player), "box": list(box)},
                "prompt": ("Name one action that begins a shortest sequence of "
                           "actions ending with the Box on the target cell."),
            },
            truth=truth,
            leak_probes=_probes(item_id, "/".join(actions), truth),
            tags=(FAMILY_OPTIMAL, "level:" + level_id),
        ))
    return items


def build() -> Paper:
    """Deterministic.  No wall clock, no RNG, no network, no model."""
    assert_synthetic_world(WORLD_ID)
    items = _step_items() + _name_items() + _optimal_items()
    paper = Paper(
        paper_id=PAPER_ID,
        question_type=QUESTION_TYPE,
        instructions=INSTRUCTIONS,
        items=items,
        world={"world_id": WORLD_ID, **provenance()},
        notes={},
    )
    paper.notes = {
        "families": {
            FAMILY_STEP: {"n": len(_STEP_CASES),
                          "points_each": POINTS[FAMILY_STEP]},
            FAMILY_NAMES: {"n": len(_VOCABULARY),
                           "points_each": POINTS[FAMILY_NAMES]},
            FAMILY_OPTIMAL: {"n": len(_OPTIMAL_CASES),
                             "points_each": POINTS[FAMILY_OPTIMAL]},
        },
        "levels": {lv.level_id: {"height": lv.height, "width": lv.width,
                                 "walls": [list(w) for w in lv.walls],
                                 "target": list(lv.target),
                                 "start_player": list(lv.start_player),
                                 "start_box": list(lv.start_box)}
                   for lv in LEVELS},
        "rule_coverage": _rule_coverage(items),
        "tiers": list(TIERS),
        "author_baseline": author_baseline(paper),
    }
    return paper


def _rule_coverage(items: Sequence[Item]) -> Dict[str, int]:
    """Which of the five rules each step item exercises.

    Lives in the truth file and not in `Item.tags`, because tags are printed on
    the sheet (`Item.sheet_side`) -- a tag naming the rule would be the answer,
    written next to the question.
    """
    counts = {name: 0 for name in RULE_NAMES}
    for item in items:
        if item.rubric_id == "handover.step_semantics":
            counts[item.truth["rule"]] += 1
    return counts


# =========================================================================
# the deliverable, executed -- the author baseline
# =========================================================================

_AUTHOR_BASELINE_NOTE = (
    "The author is the manual, executed. `pipeline.gen_exec.compile_module` is "
    "tried first, so that the baseline runs a form compiled from theory.dsl at "
    "this moment; when it raises, the checked-in compiled form "
    "a0-spike/artifacts/theory_exec.py is loaded instead and its three "
    "geometry constants are rebound per level. Both paths execute the same "
    "deliverable and neither consults the world's oracle or the answer key."
)


def _exec_form(spec: LevelSpec) -> Tuple[Dict[str, Any], str, Optional[str]]:
    """The deliverable, instantiated for one level.

    Returns (namespace, how, why_not_compiled).  `how` is `"compiled"` when the
    manual was recompiled here and `"checked-in"` when the shipped compiled form
    was reused; the difference is recorded rather than smoothed over, because a
    baseline that silently fell back to an artefact on disk would stop being a
    statement about the manual.
    """
    dsl = read_manual_source()
    try:
        gen_exec = _load_isolated("exam._a0_gen_exec", GEN_EXEC_SOURCE)
        namespace = gen_exec.compile_module(dsl, spec.height, spec.width,
                                            list(spec.walls))
        return namespace, "compiled", None
    except Exception as exc:                      # noqa: BLE001 -- see docstring
        why = "%s: %s" % (type(exc).__name__, str(exc).split("\n")[0])

    with open(EXEC_SOURCE, "r", encoding="utf-8") as fh:
        source = fh.read()
    namespace: Dict[str, Any] = {}
    exec(compile(source, EXEC_SOURCE, "exec"), namespace)   # noqa: S102
    namespace["GRID_HEIGHT"] = spec.height
    namespace["GRID_WIDTH"] = spec.width
    namespace["WALLS"] = frozenset(spec.walls)
    namespace["__source__"] = source
    return namespace, "checked-in", why


def _author_step(namespace: Dict[str, Any], player: Tuple[int, int],
                 box: Tuple[int, int],
                 action: str) -> Tuple[Tuple[int, int], Tuple[int, int], str]:
    """One step of the compiled manual, plus the name of the rule that fired.

    The compiled `step` does not report which rule fired, so the rules are run
    the same way it runs them.  Constraint 9 says exactly one fires, and this
    demands exactly one -- including in the case the shipped `step` tolerates,
    where two rules fire and happen to agree on the successor.  A successor two
    rules agree on is still a successor with two names, and naming the rule is
    half of what a step-semantics item asks for.
    """
    from dataclasses import replace

    state_cls = namespace["State"]
    fired = []
    for name, rule in namespace["RULES"]:
        trial = replace(state_cls(player=player, box=box))
        if rule(trial, action):
            fired.append((name, (trial.player, trial.box)))
    if len(fired) != 1:
        raise HandoverError(
            "the compiled manual fired %d rules for %s from %s/%s (%s); the "
            "manual promises exactly one"
            % (len(fired), action, player, box, [n for n, _ in fired]))
    name, (next_player, next_box) = fired[0]
    return next_player, next_box, name


def _author_plan_length(namespace: Dict[str, Any], spec: LevelSpec,
                        player: Tuple[int, int],
                        box: Tuple[int, int]) -> Optional[int]:
    """Breadth-first search over the *compiled manual*, not over the world.

    This is what A0's planner does, and it is the only search the author is
    allowed: a baseline that planned with `world.sokoban2` would be scoring the
    world against itself and would tell us nothing about the deliverable.
    """
    if box == spec.target:
        return 0
    start = (player, box)
    seen = {start}
    queue = deque([(start, 0)])
    while queue:
        (here_player, here_box), depth = queue.popleft()
        for action in ("UP", "DOWN", "LEFT", "RIGHT"):
            nxt_player, nxt_box, _ = _author_step(namespace, here_player,
                                                  here_box, action)
            if (nxt_player, nxt_box) == (here_player, here_box):
                continue
            if (nxt_player, nxt_box) in seen:
                continue
            if nxt_box == spec.target:
                return depth + 1
            seen.add((nxt_player, nxt_box))
            queue.append(((nxt_player, nxt_box), depth + 1))
    return None


def _author_optimal(namespace: Dict[str, Any], spec: LevelSpec,
                    player: Tuple[int, int], box: Tuple[int, int]) -> str:
    here = _author_plan_length(namespace, spec, player, box)
    if here is None or here == 0:
        return "abstain"
    for action in ("UP", "DOWN", "LEFT", "RIGHT"):
        nxt_player, nxt_box, _ = _author_step(namespace, player, box, action)
        if (nxt_player, nxt_box) == (player, box):
            continue
        there = _author_plan_length(namespace, spec, nxt_player, nxt_box)
        if there is not None and there == here - 1:
            return action
    return "abstain"


_PUSH_DISTANCE = re.compile(
    r"state\.box\s*=\s*_step_from\(state\.box,\s*direction,\s*(\d+)\)")
_WALK_DISTANCE = re.compile(
    r"def _rule_walk\b.*?state\.player\s*=\s*_step_from\(state\.player,"
    r"\s*direction,\s*(\d+)\)", re.S)
_PUSH_GUARD = re.compile(r"def _rule_push2\b.*?if not \((.*?)\):", re.S)
_GOAL_CLAUSE = re.compile(r"^\s*goal\s+(.+?)\s*$", re.M)


def _reachable_boxes(namespace: Dict[str, Any], spec: LevelSpec) -> List[Any]:
    seen = {(spec.start_player, spec.start_box)}
    boxes = {spec.start_box}
    queue = deque([(spec.start_player, spec.start_box)])
    while queue:
        player, box = queue.popleft()
        for action in ("UP", "DOWN", "LEFT", "RIGHT"):
            nxt = _author_step(namespace, player, box, action)[:2]
            if nxt in seen:
                continue
            seen.add(nxt)
            boxes.add(nxt[1])
            queue.append(nxt)
    return sorted(boxes)


def _observe(name: str, namespace: Dict[str, Any],
             spec: LevelSpec) -> str:
    """What the deliverable says about one name, instantiated for one level.

    Every branch is a lookup into the deliverable -- the compiled source text,
    a constant of the compiled form, the manual's own goal clause, or the
    behaviour of the compiled `step`.  None of them reads `LevelSpec` except
    where the name is *about* the instance, which is the point: the comparison
    across two levels is what answers the question, not this function.
    """
    source = namespace["__source__"]
    if name == "walls":
        return canonical(sorted(list(w) for w in namespace["WALLS"]))
    if name == "board_shape":
        return canonical([namespace["GRID_HEIGHT"], namespace["GRID_WIDTH"]])
    if name == "target":
        return canonical(list(spec.target))
    if name == "box_start":
        return canonical(list(spec.start_box))
    if name == "player_start":
        return canonical(list(spec.start_player))
    if name == "reachable_box_cells":
        return canonical([list(c) for c in _reachable_boxes(namespace, spec)])
    if name == "push_distance":
        match = _PUSH_DISTANCE.search(source)
        if not match:
            raise HandoverError("the compiled manual does not slide the Box")
        return match.group(1)
    if name == "player_step_distance":
        match = _WALK_DISTANCE.search(source)
        if not match:
            raise HandoverError("the compiled manual does not walk the Player")
        return match.group(1)
    if name == "crossing_requirement":
        match = _PUSH_GUARD.search(source)
        if not match:
            raise HandoverError("the compiled manual has no push guard")
        return " ".join(match.group(1).split())
    if name == "box_row_parity":
        rows = {cell[0] % 2 for cell in _reachable_boxes(namespace, spec)}
        return "conserved" if len(rows) == 1 else "broken"
    if name == "box_row_parity_value":
        rows = sorted({cell[0] % 2
                       for cell in _reachable_boxes(namespace, spec)})
        return canonical(rows)
    if name == "goal_form":
        clauses = _GOAL_CLAUSE.findall(read_manual_source())
        if not clauses:
            raise HandoverError("the manual states no goal")
        return canonical(sorted(" ".join(c.split()) for c in clauses))
    raise HandoverError("no observable defined for %r" % name)


def author_answers(paper: Paper) -> Dict[str, str]:
    """Answer the whole sheet from the deliverable alone.

    The level-data family is answered by the only criterion that is actually
    mechanical: instantiate the deliverable for two different boards and compare
    the observable.  Something that had to be rebound to move the deliverable to
    another board is supplied by the board; something untouched is fixed by the
    world.  No branch here reads `NameEntry.cls`.
    """
    instances: Dict[str, Dict[str, Any]] = {}
    how = {}
    for spec in LEVELS:
        namespace, kind, _why = _exec_form(spec)
        instances[spec.level_id] = namespace
        how[spec.level_id] = kind

    probe_levels = sorted(LEVEL_OF)[:2]
    answers: Dict[str, str] = {}
    for item in paper.items:
        kind = item.paper["kind"]
        if kind == "step_semantics":
            spec = LEVEL_OF[item.paper["level"]["level_id"]]
            player = tuple(item.paper["state"]["player"])
            box = tuple(item.paper["state"]["box"])
            nxt_player, nxt_box, rule = _author_step(
                instances[spec.level_id], player, box, item.paper["action"])
            answers[item.item_id] = ("player=(%d,%d); box=(%d,%d); rule=%s"
                                     % (nxt_player[0], nxt_player[1],
                                        nxt_box[0], nxt_box[1], rule))
        elif kind == "optimal_action":
            spec = LEVEL_OF[item.paper["level"]["level_id"]]
            answers[item.item_id] = _author_optimal(
                instances[spec.level_id], spec,
                tuple(item.paper["state"]["player"]),
                tuple(item.paper["state"]["box"]))
        elif kind == "name_class":
            observable = _OBSERVABLE_OF[item.paper["name"]]
            seen = {_observe(observable, instances[lid], LEVEL_OF[lid])
                    for lid in probe_levels}
            answers[item.item_id] = ("world_law" if len(seen) == 1
                                     else "level_data")
        else:
            raise HandoverError("unknown item kind %r" % kind)
    return answers


_RUBRIC_OF = {rubric.rubric_id: rubric for rubric in RUBRICS}


def score_locally(paper: Paper,
                  answers: Dict[str, Any]) -> Dict[str, Any]:
    """Mark against this module's own rubrics, bypassing the registry.

    `exam.grading.registry` imports all four question types' rubric modules and
    the other three are being written concurrently; a baseline that could not be
    computed until every sibling landed would block the build for a reason that
    has nothing to do with handover.  The rubrics applied here are the same
    objects the registry would hand back for these three ids.
    """
    scores: List[ItemScore] = []
    for item in paper.items:
        if item.item_id not in answers:
            scores.append(ItemScore(item.item_id, item.rubric_id, 0.0,
                                    item.points, "unanswered",
                                    {"why": "no answer submitted"}))
            continue
        scores.append(_RUBRIC_OF[item.rubric_id].grade(
            answers[item.item_id], item.truth, item))
    awarded = round(sum(s.awarded for s in scores), 6)
    possible = round(sum(s.possible for s in scores), 6)
    by_family: Dict[str, Dict[str, float]] = {}
    tag_of = {item.item_id: item.tags for item in paper.items}
    for score in scores:
        for family in FAMILIES:
            if family in tag_of.get(score.item_id, ()):
                bucket = by_family.setdefault(
                    family, {"awarded": 0.0, "possible": 0.0, "n": 0})
                bucket["awarded"] += score.awarded
                bucket["possible"] += score.possible
                bucket["n"] += 1
    for family, bucket in by_family.items():
        bucket["fraction"] = (round(bucket["awarded"] / bucket["possible"], 6)
                              if bucket["possible"] else 0.0)
        bucket["awarded"] = round(bucket["awarded"], 6)
        bucket["possible"] = round(bucket["possible"], 6)
    return {
        "awarded": awarded, "possible": possible,
        "fraction": round(awarded / possible, 6) if possible else 0.0,
        "by_family": dict(sorted(by_family.items())),
        "wrong": sorted(s.item_id for s in scores if s.verdict == "wrong"),
    }


def author_baseline(paper: Paper) -> Dict[str, Any]:
    """The author's score, computed and stored in the truth file.

    Never on the sheet.  A reader who could see how the author answered would be
    sitting a comprehension test with the answers attached, and the delta
    「新读者打平作者」 would measure nothing.
    """
    _namespace, how, why = _exec_form(LEVELS[0])
    answers = author_answers(paper)
    result = score_locally(paper, answers)
    result["form"] = how
    result["compile_refusal"] = why
    result["note"] = _AUTHOR_BASELINE_NOTE
    return result


# =========================================================================
# the manual, rendered
# =========================================================================

def read_manual_source() -> str:
    with open(MANUAL_SOURCE, "r", encoding="utf-8") as fh:
        return fh.read().replace("\r\n", "\n")


_GUARD_PHRASES: Dict[str, Optional[str]] = {
    "act=move(Player, dir)": None,
    "free(ahead(Player, dir))":
        "the cell one step from the Player in direction d is free",
    "not free(ahead(Player, dir))":
        "the cell one step from the Player in direction d is NOT free",
    "Box.pos = ahead(Player, dir)":
        "the Box is standing on the cell one step from the Player in direction d",
    "not Box.pos = ahead(Player, dir)":
        "the Box is NOT standing on the cell one step from the Player in "
        "direction d",
    "free(ahead(Box, dir))":
        "the cell one step from the Box in direction d -- the cell the Box would "
        "cross -- is free",
    "not free(ahead(Box, dir))":
        "the cell one step from the Box in direction d -- the cell the Box would "
        "cross -- is NOT free",
    "free(beyond(Box, dir))":
        "the cell two steps from the Box in direction d -- the cell the Box would "
        "land on -- is free",
    "not free(beyond(Box, dir))":
        "the cell two steps from the Box in direction d -- the cell the Box would "
        "land on -- is NOT free",
}

_EVENT_PHRASES: Dict[str, str] = {
    "moved(Player, dir)":
        "the Player moves one cell in direction d. Nothing else changes.",
    "slid(Box, dir)":
        "the Box slides two cells in direction d, and the Player advances one "
        "cell -- onto the cell the Box has just left.",
    "stayed(Player)":
        "nothing moves. The situation after the action is identical to the "
        "situation before it.",
}

_RULE_LINE = re.compile(r"^\s*rule\s+(\w+)", re.M)
_WHEN_LINE = re.compile(r"^\s*when\s+(.+?)\s+then\s+(.+?)\s*$", re.M)
_INVARIANT = re.compile(r"^\s*invariant\s+(\w+)\s+(.+?)\s*\[status:\s*(\w+)\]",
                        re.M)
_THEOREM = re.compile(r'^\s*theorem\s+(\w+)\s+"(.+?)"', re.M)
_OBJECT = re.compile(r"^\s*object\s+(\w+)\s*\{\s*(.+?)\s*\}", re.M)

#: Primitive vocabulary the manual uses but does not define.  Taken from the
#: manual's own compiled executable form (one of the four co-derived forms), not
#: invented here: `_free`, `_on_board` and `DELTA` in
#: a0-spike/artifacts/theory_exec.py.  Without it the bundle is unanswerable --
#: `free` and `ahead` carry the whole content of every guard -- and that the v0.1
#: manual does not define its own primitives is a real limit of the deliverable,
#: recorded here rather than papered over.
_PRIMITIVES = """\
## The words the rules are built from

These are the primitives the rules above use. They are not restated in the
manual's source; they are read off the manual's compiled executable form, which
is one of the forms the manual compiles to.

- A **cell** is written `(row, col)`. Row 0 is the top row and column 0 the
  left column.
- A **direction** `d` is one of UP, DOWN, LEFT, RIGHT. UP subtracts one from
  the row, DOWN adds one to the row, LEFT subtracts one from the column,
  RIGHT adds one to the column.
- **one step from X in direction d** is X's cell moved once by d;
  **two steps from X in direction d** is X's cell moved twice by d.
- A cell is **free** when all three of these hold: it is on the board, it is
  not a wall, and the Box is not standing on it. The Player never makes a cell
  un-free: the Player does not block anything, including itself.
- An action is always a move by the Player in one direction. There is no other
  kind of action.
"""


def render_manual(dsl_text: str) -> str:
    """theory.dsl -> English, by table lookup, deterministically.

    A pretty-printer, in the sense Theoria 1.8 means: same input, same bytes,
    no model in the path, no polishing.  Every guard clause and every event has
    to be in `_GUARD_PHRASES` / `_EVENT_PHRASES` or this raises -- the same
    refusal `gen_exec` makes, and for the same reason.  A renderer that quietly
    dropped an unrecognised guard would hand the reader a weaker world and the
    handover score would silently measure the difference.
    """
    lines: List[str] = ["# The manual for this world",
                        "",
                        "A deterministic rendering of the manual's source file "
                        "(`MANUAL.dsl` in this bundle). It adds nothing; where "
                        "it says more than the source, it is reading the "
                        "source's compiled form and says so.",
                        ""]

    lines += ["## What there is", ""]
    if re.search(r"^\s*board\s*$", dsl_text, re.M):
        lines.append("- A **board**: a rectangular grid of cells that does not "
                     "change while the game is played.")
    for name, fields in _OBJECT.findall(dsl_text):
        lines.append("- A **%s**, which has one property: %s."
                     % (name, ", ".join(f.strip() for f in fields.split(","))))
    lines.append("")

    lines += ["## What can happen", "",
              "Three kinds of change, and no others: something **moved** one "
              "cell, something **slid** (further than one cell), or something "
              "**stayed** where it was.", ""]

    lines += ["## How things change", ""]
    rule_names = _RULE_LINE.findall(dsl_text)
    bodies = _WHEN_LINE.findall(dsl_text)
    if len(rule_names) != len(bodies):
        raise UnrenderableManual(
            "the manual has %d rule headers and %d `when ... then` bodies; a "
            "rendering that guessed which belongs to which would be inventing "
            "the manual" % (len(rule_names), len(bodies)))
    for name, (guard, event) in zip(rule_names, bodies):
        clauses = [c.strip() for c in guard.split(" and ")]
        phrases = []
        for clause in clauses:
            if clause not in _GUARD_PHRASES:
                raise UnrenderableManual(
                    "no rendering for the guard clause %r" % clause)
            phrase = _GUARD_PHRASES[clause]
            if phrase is not None:
                phrases.append(phrase)
        event = event.strip()
        if event not in _EVENT_PHRASES:
            raise UnrenderableManual("no rendering for the event %r" % event)
        lines.append("**%s**" % name)
        lines.append("")
        lines.append("When the Player is told to move in direction d, and")
        for phrase in phrases:
            lines.append("  - %s," % phrase)
        lines.append("")
        lines.append("then %s" % _EVENT_PHRASES[event])
        lines.append("")

    lines += ["Exactly one of these rules applies to any situation and any "
              "action, so there is never a question of which one to use.", ""]

    lines += ["## When the game is won", ""]
    for clause in _GOAL_CLAUSE.findall(dsl_text):
        lines.append("- The game is won when %s."
                     % clause.replace("Box.pos = target",
                                      "the Box is standing on the target cell"))
    lines.append("")

    lines += ["## What is always true", ""]
    for name, expr, status in _INVARIANT.findall(dsl_text):
        lines.append("- **%s** (%s): `%s` holds before the first action and "
                     "after every action, whatever actions are taken."
                     % (name, status, " ".join(expr.split())))
    for name, text in _THEOREM.findall(dsl_text):
        lines.append("- **%s**: %s" % (name, text))
    lines.append("")

    lines.append(_PRIMITIVES)
    return "\n".join(lines).rstrip() + "\n"


# =========================================================================
# the playbook
# =========================================================================

PLAYBOOK_DSL = """\
# ============================================================================
# A0 玩法书 — the strategic tier of the layered handover
#
# Four sentence forms and no others (constraint 10, CONTRACTS/dsl_grammar_v0.1):
# ordering, pruning, heuristics, preferences. There is deliberately no way to
# write a solution down here. A playbook that stored answers would turn the
# handover into passing notes rather than passing understanding.
#
# Every entry cites the manual clause it rests on, so that changing that clause
# invalidates the entry.
# ============================================================================

# Check the conservation law before searching at all. The law decides some
# boards outright, and it decides them in one arithmetic step; a search that
# runs first is a search that may run forever on a board that was already
# settled. Rests on: invariant box_row_parity, invariant box_col_parity.
order parity_check_before_search [proof: lean]

# The board is decided, and impossible, when the Box's row parity or its column
# parity differs from the target's. Nothing the Player does can change either.
# Rests on: invariant box_row_parity, invariant box_col_parity, rule push2.
prune parity(Box.pos) != parity(target) => dead [proof: lean]

# A Box that cannot be pushed in any direction will never move again: every rule
# that moves the Box needs the Player standing behind it and both cells ahead of
# it free. Rests on: rule push2, rule blocked_box_crossing,
# rule blocked_box_landing.
prune no_direction_admits_a_push(Box.pos) => dead [proof: none]

# A lower bound on the number of pushes still needed: each push moves the Box
# two cells along one axis, so at best it takes half the remaining row distance
# plus half the remaining column distance. Rests on: rule push2.
heuristic pushes_remaining(Box.pos, target) [admissible: none]

# The empirical tier is EMPTY, and that is a finding rather than an omission.
# A `prefer` entry must carry a win rate or a node count (constraint 5), and no
# such measurement exists for this world yet. Writing one down without it would
# be inventing evidence. The tier stays open.
"""

PLAYBOOK_MD = """\
# The playbook for this world

The manual says what the world does. This says how to win in it, and — more
usefully — how to avoid work.

Nothing here is a solution to any particular board. The playbook deliberately
contains no board, no position and no sequence of actions: those are outputs of
planning, not contents of a book.

## What the conservation law is for

The manual records that the Box's row parity and its column parity never change.
That is a fact about the world; here is what to do with it.

**Decide before you search.** Compare the Box's row parity with the target's row
parity, and the Box's column parity with the target's column parity. If either
disagrees, the board is impossible — not "no plan was found", but *there is no
plan*, and the reason fits on one line. Searching such a board is wasted effort
in the best case and unbounded effort in the worst.

**Shrink the search when you do search.** Even when the parities agree, the law
says the Box can only ever stand on cells matching its own row parity and its
own column parity. Three quarters of the board is unreachable for the Box before
a single action is considered. Any search that expands nodes placing the Box on
those cells is expanding nodes that cannot exist.

**The certificate is the explanation.** When a board is refused, the refusal is
checkable by anyone with the manual: this parity, that parity, they differ, the
law forbids the crossing. That is a different kind of answer from "my search
finished and found nothing", and it is the answer this framework is for.

## Deadlocks

A deadlock is a situation that is not yet lost by the goal condition but from
which the goal can no longer be reached. They are the daily business of this
world, far more common than a whole board being impossible.

**The Box is frozen.** The Box moves only when the Player stands directly behind
it *and* the cell it would cross *and* the cell it would land on are both free.
If, in every one of the four directions, at least one of those three conditions
can never be met, the Box will never move again. If it is not already on the
target, the board is lost.

**The two-cell slide makes edges wider than they look.** Because the Box travels
two cells, it cannot be pushed toward a wall that sits one *or* two cells away
in that direction — one cell away blocks the crossing, two cells away blocks the
landing. A Box that would be pushable in an ordinary one-cell world can be
immovable here. Reason about the pair of cells, never about the next cell alone.

**The Player is not a wall but the Box is.** The Box blocks the Player's walking;
the Player blocks nothing. So the Player can always be routed anywhere the walls
allow, provided the route does not pass through the Box — which is exactly the
constraint that makes some pushes unreachable even when the Box could accept
them.

## Choosing an action

**Count pushes, then count walking.** Each push closes two cells of the gap
between the Box and the target along one axis. So the number of pushes still
needed is at least half the remaining row distance plus half the remaining
column distance. This is a lower bound and can be used to order candidates; it
is not proven admissible for the total number of actions, because the walking
between pushes is not counted.

**Plan the pushes, then plan the walking.** The Box's route is the hard part and
the Player's route is almost always the easy part: the Player is unobstructed
except by walls and by the Box itself. Work out which sequence of pushes brings
the Box to the target — respecting both parities and the deadlocks above — and
only then work out how to get the Player behind the Box each time.

**Getting behind the Box costs actions, and turning around costs the most.**
Pushing the Box in a direction requires the Player to be on the cell immediately
opposite that direction. Continuing a push in the direction already being pushed
is free — the Player is already in place, having followed the Box. Changing the
push direction means walking around the Box, and the Box is in the way while you
do it. A route that pushes along one axis and then the other is usually cheaper
than one that alternates.

**Only pushes are irreversible.** Walking can always be undone. A push may not
be: whether the Box can be pushed back depends on whether the Player can get to
the far side of it and on what is behind it there. Treat every push as a
commitment and check the deadlock conditions before making it, not after.

## Where this book came from, and what it does not have

Every claim above is derived from clauses of the manual, and the derivation is
short in each case. That is the pre-registered prediction of the layered
handover: a reader given only the manual should be able to reconstruct this
book, and should end up at the same place after paying the search cost this book
saves. If that turns out to be false, this book contains something the manual
does not, and finding out what would be the interesting result.

There is no empirical tier — no "this move ordering wins 7 times in 10" — because
no such measurement exists for this world. An entry of that kind without the
count behind it would be invented evidence.
"""


# =========================================================================
# the bundles
# =========================================================================

_TIER_BRIEF_HEADER = {
    TIER1: (
        "You have been given **the manual only**. There is no playbook in this "
        "bundle and there is not supposed to be one: this tier measures what a "
        "description of the world alone is worth. If you want a strategy, you "
        "will have to derive it."
    ),
    TIER2: (
        "You have been given **the manual and the playbook**. The manual "
        "describes the world; the playbook describes how to win in it, "
        "including which situations are hopeless and why. This tier measures "
        "what the strategic book adds on top of the description."
    ),
}


def _reader_brief(tier: str, files: Sequence[str]) -> str:
    listing = "\n".join(
        "- `%s` — %s" % (name, _FILE_BLURB[name]) for name in files
        if name in _FILE_BLURB)
    return """\
# Reader brief — %(tier)s

## Who you are

You are a fresh reader. You have never seen this world, you have no record of
anyone playing it, no source code beyond this bundle, and no earlier
conversation about it. Everything you are entitled to use is in this bundle and
on the question sheet you were handed with it. If something is not in one of
those two places, you do not know it — say `abstain` rather than guess it.

## What you have been given

%(header)s

Files in this bundle:

%(listing)s

## What to do

Read the bundle. Then answer every item on the question sheet. The sheet is a
JSON document; each item has an `item_id`, a `kind`, and whatever board
geometry and situation that item needs.

## How the sheet describes a board

An item that needs a board carries a `level` block giving the board's `height`,
its `width`, the list of `walls` and the `target` cell, and a `board` field
holding the same thing drawn as rows of characters. The lists are authoritative;
the drawing is there to be read at a glance.

%(legend)s

An item that needs a situation carries a `state` block with the Player's cell
and the Box's cell. Take the situation from `state`, not from any earlier item:
each item stands alone.

## How to write your answers

Produce **one JSON object**. Its keys are the `item_id` values from the sheet —
every one of them, none omitted, none invented. Its values are answer strings in
the grammars below. Nothing else: no commentary, no reasoning, no extra keys.

    {
      "<item_id>": "<answer string>",
      ...
    }

### `kind` = `step_semantics`

    player=(row,col); box=(row,col); rule=<name>

Exactly three fields. Separate them with semicolons. The order does not matter.
Case does not matter for the field names. `row` and `col` are integers.
`<name>` must be one of:

%(rules)s

`player` is where the Player stands after the action, `box` is where the Box
stands after the action, and `rule` is the rule that accounts for what happened.
If nothing moved, `player` and `box` are where they already were.

### `kind` = `name_class`

One word, exactly one of:

%(classes)s

Answer `level_data` if the item's name is something each individual board
supplies. Answer `world_law` if it is something the world fixes once and for
all, the same on every board.

### `kind` = `optimal_action`

One word, exactly one of:

%(actions)s

Name an action that begins a shortest sequence of actions ending with the Box on
the target cell. If several actions begin some shortest sequence, any of them is
accepted; you do not need to find them all.

### Any item

Instead of an answer you may write:

    abstain

An abstention scores nothing and is recorded as an abstention. A guess that
turns out wrong is recorded as a wrong answer. If you cannot work an item out
from this bundle, abstaining is the honest response and it is treated as one.

### Format example

This example uses an item id that is not on your sheet and a situation that
cannot occur; it shows the shape and nothing else.

    {
      "example-item-id-not-on-your-sheet": "player=(9,9); box=(9,9); rule=walk",
      "another-example-id": "world_law",
      "a-third-example-id": "abstain"
    }

## How you will be marked

By a fixed rule, published before your answers existed, applied mechanically. An
answer outside the grammars above scores zero and the parse failure is recorded;
it is not interpreted charitably. A step-semantics answer must have all three
fields right — two out of three scores zero.
""" % {
        "tier": tier,
        "header": _TIER_BRIEF_HEADER[tier],
        "listing": listing,
        "legend": BOARD_LEGEND,
        "rules": "\n".join("  - `%s`" % r for r in RULE_NAMES),
        "classes": "\n".join("  - `%s`" % c for c in NAME_CLASSES),
        "actions": "\n".join("  - `%s`" % a for a in ACTIONS),
    }


_FILE_BLURB = {
    "MANUAL.dsl": "the manual, in the form its author wrote it",
    "MANUAL.md": "the same manual rendered into English, mechanically",
    "PLAYBOOK.dsl": "the playbook, in the form its author wrote it",
    "PLAYBOOK.md": "the same playbook rendered into English",
}


def bundle_files(tier: str) -> Dict[str, str]:
    """The content of one tier, as {filename: text}.  Pure, deterministic."""
    if tier not in TIERS:
        raise HandoverError("no such tier %r; the two tiers are %s"
                            % (tier, list(TIERS)))
    dsl = read_manual_source()
    files: Dict[str, str] = {
        "MANUAL.dsl": dsl,
        "MANUAL.md": render_manual(dsl),
    }
    if tier == TIER2:
        files["PLAYBOOK.dsl"] = PLAYBOOK_DSL
        files["PLAYBOOK.md"] = PLAYBOOK_MD
    files["READER_BRIEF.md"] = _reader_brief(tier, sorted(files))
    return files


#: Files whose text is *evidence* handed to the reader.  The brief is excluded:
#: it is the answer alphabet, which every examinee must have.
CONTENT_FILES = ("MANUAL.dsl", "MANUAL.md", "PLAYBOOK.dsl", "PLAYBOOK.md")


def bundle_text(tier: str, content_only: bool = False) -> str:
    """Every byte a reader of this tier receives, concatenated."""
    files = bundle_files(tier)
    names = [n for n in sorted(files)
             if not content_only or n in CONTENT_FILES]
    return "\n".join("=== %s ===\n%s" % (n, files[n]) for n in names)


def emit_bundles(dest: Optional[str] = None) -> Dict[str, Any]:
    """Write both tiers.  Byte-identical on every call; returns the digests.

    The manifest records where each copied file came from and the sha256 of the
    source it was copied from, so "is this bundle really the deliverable?" is a
    question with an answer.  A bundle that only said "the manual" would be a
    claim; this is a check.
    """
    root = dest or BUNDLES_DIR
    out: Dict[str, Any] = {}
    manual_source_digest = sha256_text(read_manual_source())
    for tier in TIERS:
        files = bundle_files(tier)
        tier_dir = os.path.join(root, tier)
        os.makedirs(tier_dir, exist_ok=True)
        digests = {}
        for name in sorted(files):
            path = os.path.join(tier_dir, name)
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(files[name])
            digests[name] = sha256_text(files[name])
        bundle_digest = sha256([[n, digests[n]] for n in sorted(digests)])
        manifest = {
            "bundle": tier,
            "paper_id": PAPER_ID,
            "world_id": WORLD_ID,
            "bundle_digest": bundle_digest,
            "files": dict(sorted(digests.items())),
            "provenance": {
                "MANUAL.dsl": {
                    "copied_from": "a0-spike/theory/theory.dsl",
                    "source_sha256": manual_source_digest,
                    "edits": "line endings normalised to LF; nothing else",
                },
                "MANUAL.md": {
                    "generated_by": "exam.papers.handover.render_manual",
                    "of": "MANUAL.dsl",
                    "model_calls": 0,
                },
                "PLAYBOOK.dsl": {
                    "written_for": "this exam",
                    "why": "a0-spike ships no playbook file; the strategic tier "
                           "is assembled from its recorded findings",
                },
                "PLAYBOOK.md": {
                    "written_for": "this exam",
                    "why": "see PLAYBOOK.dsl",
                },
                "READER_BRIEF.md": {
                    "generated_by": "exam.papers.handover._reader_brief",
                },
            },
        }
        manifest_path = os.path.join(tier_dir, "MANIFEST.json")
        with open(manifest_path, "w", encoding="utf-8", newline="\n") as fh:
            import json
            json.dump(manifest, fh, indent=2, sort_keys=True,
                      ensure_ascii=False)
            fh.write("\n")
        out[tier] = {"path": tier_dir, "digest": bundle_digest,
                     "files": dict(sorted(digests.items()))}
    return out


# =========================================================================
# the calibration examinees
# =========================================================================

CALIBRATION_MODES = ("oracle", "null", "memoriser", "bluffer")

#: What the memoriser plays on every optimal-action item.  It is the opening of
#: the A0 run's own solution to `match` -- the one plan it has seen -- replayed
#: regardless of the board in front of it.  That is the whole failure mode: a
#: memoriser does not know it is looking at a different board.
_MEMORISED_ACTION = "LEFT"


def _canonical_answer(item: Item) -> str:
    kind = item.paper["kind"]
    if kind == "step_semantics":
        return step_answer_text(item.truth)
    if kind == "name_class":
        return item.truth["class"]
    if kind == "optimal_action":
        return item.truth["optimal_actions"][0]
    raise HandoverError("unknown item kind %r" % kind)


def reference_answers(paper: Paper, key_doc: Dict[str, Any],
                      mode: str) -> Dict[str, Any]:
    """The four calibration examinees of `exam.papers.CALIBRATION_MODES`.

    `null` submits nothing.  It doubles as the CC arm: 「CC 无物可交记零」, and a
    zero the marker derives from an empty submission is worth more than a zero
    written into a table.  `no_deliverable_submission()` wraps it with the
    missing capability so the *reason* for the zero is in the report too.

    `memoriser` is the reader this paper exists to catch.  It answers every
    step-semantics item correctly -- those are drilled by the manual's rules and
    a reader who memorised one worked board can reproduce them -- and then calls
    every name a world law, because everything it ever saw was true of the one
    board it saw.  If the paper cannot separate it from `oracle`, the paper is
    not testing comprehension.

    `bluffer` answers each family with that family's commonest answer, which is
    the score to beat before any reader's number means anything.
    """
    if mode not in CALIBRATION_MODES:
        raise HandoverError("unknown calibration mode %r; the four are %s"
                            % (mode, list(CALIBRATION_MODES)))
    if mode == "null":
        return {}

    truth_of = {entry["item_id"]: entry["truth"]
                for entry in key_doc.get("items", [])}

    if mode == "oracle":
        return {item.item_id: _canonical_answer(item) for item in paper.items}

    if mode == "memoriser":
        answers = {}
        for item in paper.items:
            kind = item.paper["kind"]
            if kind == "step_semantics":
                answers[item.item_id] = step_answer_text(
                    truth_of[item.item_id])
            elif kind == "name_class":
                answers[item.item_id] = "world_law"
            else:
                answers[item.item_id] = _MEMORISED_ACTION
        return answers

    # bluffer: the modal answer of each family, ties broken lexically so the
    # examinee is a function of the paper and not of dict ordering.
    modal: Dict[str, str] = {}
    for family, kind in ((FAMILY_STEP, "step_semantics"),
                         (FAMILY_NAMES, "name_class"),
                         (FAMILY_OPTIMAL, "optimal_action")):
        tally: Dict[str, int] = {}
        for item in paper.items:
            if item.paper["kind"] != kind:
                continue
            if kind == "optimal_action":
                for action in item.truth["optimal_actions"]:
                    tally[action] = tally.get(action, 0) + 1
            else:
                answer = _canonical_answer(item)
                tally[answer] = tally.get(answer, 0) + 1
        modal[kind] = sorted(tally.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    return {item.item_id: modal[item.paper["kind"]] for item in paper.items}


def no_deliverable_submission(examinee_id: str = "cc-bare") -> Submission:
    """An arm with nothing to hand over.

    Not a hardcoded zero: a real submission, with no bundle capability and no
    answers, marked by the same marker as everyone else.  It scores zero because
    there is nothing in it, which is the finding Theoria 1.11 wants recorded --
    and `axes` says *why* it is zero rather than leaving the number bare.
    """
    return Submission(examinee_id=examinee_id, paper_id=PAPER_ID, answers={},
                      capabilities=(),
                      meta={"tier": None,
                            "why": "this arm produces no deliverable; there is "
                                   "nothing to hand a fresh reader"})


def submission(examinee_id: str, tier: str, answers: Dict[str, Any],
               **meta: Any) -> Submission:
    """A reader's submission for one tier, with the capability it implies."""
    if tier not in TIERS:
        raise HandoverError("no such tier %r" % tier)
    return Submission(examinee_id=examinee_id, paper_id=PAPER_ID,
                      answers=answers,
                      capabilities=(HANDOVER_CAPABILITY,),
                      meta={"tier": tier, **meta})


# =========================================================================
# the axes
# =========================================================================

def axes(report: Any, key_doc: Dict[str, Any],
         submission: Submission) -> Dict[str, Any]:
    """The three numbers Theoria 1.11 asks this question type for.

    `reader_minus_author` is 「新读者打平作者」: the fresh reader's fraction minus
    the fraction the deliverable's own executable form scores on the same sheet.
    Zero means the understanding is in the document rather than in the head of
    whoever wrote it.

    `tier2_minus_tier1` is 「两档之差」, and it needs *two* readers.  One report
    describes one reader, so this function cannot compute the difference from
    what it is given; it reports the difference only when the harness has
    supplied the sibling tier's fraction in `submission.meta`, and otherwise
    returns `None` with the reason.  A number invented from one tier would be
    the difference between a reader and nothing.

    `no_deliverable` is the CC arm's zero, derived.  It takes *two* facts, not
    one: the submission declares no bundle capability **and** it contains no
    answers.  Keying it on the capability alone would be tidier and wrong, for
    two reasons.  An examinee that answered plainly had something to read,
    whatever it declared — answers are evidence of a deliverable and a
    declaration is only a claim about one.  And the calibration fakes of
    `exam.grading.calibration` are not arms at all; labelling `oracle` as an arm
    with nothing to hand over would put a false finding in every calibration
    report.  A submission that answers without declaring the capability is
    reported under `capability_unclaimed` instead: its score stands on its
    answers, but it cannot be quoted as a handover arm until the two claims are
    reconciled.
    """
    has_bundle = HANDOVER_CAPABILITY in tuple(submission.capabilities)
    baseline = key_doc.get("notes", {}).get("author_baseline", {})
    author_fraction = baseline.get("fraction")
    handed_over_nothing = not has_bundle and not submission.answers

    out: Dict[str, Any] = {
        "tier": submission.meta.get("tier"),
        "fraction": report.fraction,
        "author_baseline_fraction": author_fraction,
        "author_baseline_form": baseline.get("form"),
        "no_deliverable": handed_over_nothing,
        "answers_submitted": len(submission.answers),
    }

    if handed_over_nothing:
        out["no_deliverable_reason"] = (
            "the submission declares no %r capability and carries no answers, "
            "so there was no bundle to hand a fresh reader. The zero is by "
            "construction, not by failure to answer: Theoria.md 1.11, "
            "CC 无物可交记零." % HANDOVER_CAPABILITY)
    elif not has_bundle:
        out["capability_unclaimed"] = (
            "%d answers were submitted by an examinee that declares no %r "
            "capability. The mark stands on the answers, but the examinee "
            "cannot be reported as a handover arm until it says what it handed "
            "over." % (len(submission.answers), HANDOVER_CAPABILITY))

    if author_fraction is None:
        out["reader_minus_author"] = None
        out["reader_minus_author_note"] = (
            "the truth file carries no author baseline, so there is nothing to "
            "draw level with")
    else:
        out["reader_minus_author"] = round(report.fraction - author_fraction, 6)

    paired = submission.meta.get("paired_tier_fraction")
    tier = submission.meta.get("tier")
    if tier == TIER2 and isinstance(paired, (int, float)):
        out["tier2_minus_tier1"] = round(report.fraction - float(paired), 6)
    elif tier == TIER1 and isinstance(paired, (int, float)):
        out["tier2_minus_tier1"] = round(float(paired) - report.fraction, 6)
    else:
        out["tier2_minus_tier1"] = None
        out["tier2_minus_tier1_note"] = (
            "a tier difference needs both tiers. Mark the sibling tier and pass "
            "its fraction as submission.meta['paired_tier_fraction'], or use "
            "exam.papers.handover.tier_delta(report_tier1, report_tier2).")
    return out


def tier_delta(report_tier1: Any, report_tier2: Any,
               key_doc: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """「两档之差 = 战略知识的价值」, computed from the two reports it needs.

    Reported per family as well as overall, because the prediction is not that
    the playbook helps everywhere.  It should buy almost nothing on step
    semantics -- the manual alone determines every transition -- and most of what
    it buys should land on the optimal-action family.  A delta spread evenly
    across all three families would mean the tiers differ in some way other than
    strategy, and that is worth knowing before the number is quoted.
    """
    tag_of = {entry["item_id"]: tuple(entry.get("tags", ()))
              for entry in (key_doc or {}).get("items", [])}
    if not tag_of:
        tag_of = {}

    def _families(report: Any) -> Dict[str, float]:
        out: Dict[str, float] = {}
        buckets: Dict[str, List[Any]] = {}
        for score in report.scores:
            for tag in tag_of.get(score.item_id, ()):
                if tag in FAMILIES:
                    buckets.setdefault(tag, []).append(score)
        for family, group in buckets.items():
            possible = sum(s.possible for s in group)
            out[family] = (round(sum(s.awarded for s in group) / possible, 6)
                           if possible else 0.0)
        return out

    one, two = _families(report_tier1), _families(report_tier2)
    return {
        "tier1_fraction": report_tier1.fraction,
        "tier2_fraction": report_tier2.fraction,
        "tier2_minus_tier1": round(report_tier2.fraction
                                   - report_tier1.fraction, 6),
        "by_family": {f: round(two.get(f, 0.0) - one.get(f, 0.0), 6)
                      for f in sorted(set(one) | set(two))},
        "prediction": (
            "Theoria.md 1.11 pre-registers that the manual-only reader can "
            "re-derive the playbook and eventually draw level, paying the "
            "search cost the playbook caches. A large and persistent delta on "
            "optimal_action, with none on step_semantics, is the shape that "
            "prediction expects."),
    }
