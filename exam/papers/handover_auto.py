"""The layered handover test, automated, and with somewhere left to fail.

Theoria.md 1.11 asks for a fresh instance -- no history, no context -- handed a
deliverable in two tiers: the manual alone, or the manual and the playbook.  The
difference between the tiers is what strategic knowledge is worth.

P-15 built that apparatus and ran it once.  Both tiers scored 46/46, so the
difference was zero and the zero meant nothing: a saturated sheet cannot show a
gap.  `exam/STATUS.md` records it as open weakness 1.  This module is the second
sheet, built to leave room, and the driver `exam.tools.run_handover_auto` is what
makes the run repeatable rather than a session someone once did by hand.

**Four changes, each aimed at one way the first sheet was blind.**

1. *Boards a reader has to search.*  The three P-15 boards had shortest
   solutions of a handful of actions.  Six of these have 14 to 25, which is past
   the point where a reader can see the answer, and the sheet asks for the length
   of that solution as well as its first action -- half the marks each.  A reader
   who has understood the world but not finished the search now scores half,
   where before it scored full.

   **Two have 11, and that is a cost V26 paid knowingly.**  Closing the
   level-multiplicity leak required a *solvable* state on each of `stile` and
   `cairn`, and 11 is the longest either board admits -- searched exhaustively
   over every (player, box) pair on both, so it is a ceiling and not a lazy pick.
   Those two boards are 6 rows; they do not reach 14.  So the sheet gained its two
   easiest items at the moment its recorded failure was saturation, and the honest
   summary is that this repair traded a little headroom for the removal of a
   channel that answered 8 items out of 8.  Whoever next widens this family should
   add hard items on `warren`/`flume`/`kiln` -- two per level, to keep
   `test_level_multiplicity_is_uniform` satisfied.

2. *Two boards with no solution at all*, and they fail for different reasons.
   `stile` is settled by arithmetic: the Box's column parity differs from the
   target's, and the manual's own `invariant box_col_parity` decides it without
   any search.  `cairn` is not: every parity the manual states matches, and the
   board is dead because the Box stands where no direction admits a push, which
   is a fact about geometry that only the *playbook* writes down
   (`prune no_direction_admits_a_push(Box.pos) => dead`).  If the playbook is
   worth anything on this sheet, `cairn` is where it shows.

3. *The fourth question family, which had no rubric at all.*  1.11 lists 「这条
   规则为什么成立」 beside the other three.  It is asked here as a citation: a
   claim, a fixed list of the manual's clauses, and the instruction to name the
   subset the claim's truth depends on.  Machine-marked, set-valued, and a
   spurious citation costs what a correct one earns -- see
   `exam.grading.rubrics_handover_auto`.

4. *One question the marker settles by computing, not by comparing.*  The A0
   manual ships `invariant box_row_parity (Box.pos.row) mod 2 = 1` marked
   `proven`, and that sentence is false on most boards of its own world -- P-15
   found it three times independently and deliberately did not repair it.  The
   sheet asks for a situation where it fails, and the rubric recomputes the claim
   there.  This is the one item whose marking cannot drift: there is no stored
   answer to loosen.

**What is deliberately unchanged.**  The bundle *builder*.  Tier 1 is
`MANUAL.dsl` and `MANUAL.md`, tier 2 adds the two playbook files, assembled by
P-15's own `handover.bundle_files`.  Re-cutting the bundle at the same time as
re-cutting the sheet would leave two changes and no attribution.

It is the builder and not the bytes: `a0-spike/theory/theory.dsl` has since
migrated to grammar v0.2 and grown a `semantics:` section, so tier 1 here is the
deliverable *as it stands*, not the snapshot in `exam/handover_bundles/`.  That
is the right choice -- a handover test examines what would be handed over today
-- but it means this run's tier-1 bundle is not byte-comparable with P-15's, and
no score here should be differenced against a P-15 score.  Two further
consequences are recorded rather than repaired: `render_manual` predates the new
section and silently omits it from `MANUAL.md`, so the `.dsl` is strictly more
informative than the `.md`; and the new comments cite repository paths, which
`exam/runs/.../BLINDING.md` lists as a residual pointer out of the bundle.

The P-15 reader brief is *not* shipped -- it publishes the old answer grammar,
and a brief that contradicts the sheet is a trap rather than a bundle.

**What this sheet still does not measure.**  Cost.  1.11's pre-registered
prediction is that the manual-only reader draws level *and pays for it in
search*; `plan_len` is a proxy for having done the search, not a measurement of
what it cost.  P-15's open weakness 2 stands.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..guard import assert_synthetic_world, provenance
from ..model import Item, Paper, Submission, canonical
from ..grading.rubrics_handover_auto import CITABLE, NO_ACTION, PUBLISHED
from . import handover as H

PAPER_ID = "v11-handover-a0"
QUESTION_TYPE = "handover"
WORLD_ID = "a0"
PROMPT_ID = "V11-handover-auto"

#: The two tiers, reusing P-15's bundles byte for byte.
TIER1 = H.TIER1
TIER2 = H.TIER2
TIERS: Tuple[str, ...] = H.TIERS

HANDOVER_CAPABILITY = H.HANDOVER_CAPABILITY

FAMILY_STEP = "step_semantics"
FAMILY_NAMES = "level_data_vs_world_law"
FAMILY_OPTIMAL = "optimal_action"
FAMILY_WHY = "rule_justification"
FAMILIES: Tuple[str, ...] = (FAMILY_STEP, FAMILY_NAMES, FAMILY_OPTIMAL,
                             FAMILY_WHY)

POINTS = {FAMILY_STEP: 2.0, FAMILY_NAMES: 1.0, FAMILY_OPTIMAL: 2.0,
          FAMILY_WHY: 3.0}


# =========================================================================
# the boards
# =========================================================================

#: Five fresh boards.  None is an A0 run level and none is a P-15 level, so a
#: reader who somehow saw either gains nothing; the *world* is the same world,
#: which is the whole point of a handover test.
#:
#: `stile` and `cairn` carry no solution.  They are here in a pair on purpose:
#: one is decided by the manual's arithmetic and one is not, and a delta that
#: lands on `cairn` alone is the shape 1.11's prediction expects.
LEVELS: Tuple[H.LevelSpec, ...] = (
    H.LevelSpec("warren", 8, 8,
                ((1, 1), (1, 2), (1, 5), (2, 4), (2, 7), (3, 7)),
                target=(4, 2), start_player=(6, 7), start_box=(2, 6)),
    H.LevelSpec("flume", 8, 8,
                ((1, 7), (2, 1), (2, 7), (4, 2), (4, 4), (6, 2), (6, 3), (6, 5)),
                target=(7, 5), start_player=(3, 1), start_box=(5, 5)),
    H.LevelSpec("kiln", 7, 7,
                ((2, 5), (3, 0), (4, 3), (4, 4), (5, 3), (6, 1)),
                target=(3, 5), start_player=(0, 5), start_box=(3, 1)),
    H.LevelSpec("stile", 6, 7,
                ((1, 2), (2, 3), (3, 1), (4, 1), (5, 5)),
                target=(4, 4), start_player=(2, 0), start_box=(0, 5)),
    H.LevelSpec("cairn", 6, 6,
                ((0, 2), (2, 3), (2, 4), (3, 3), (3, 4), (4, 5), (5, 4)),
                target=(2, 1), start_player=(1, 5), start_box=(0, 5)),
)

LEVEL_OF: Dict[str, H.LevelSpec] = {lv.level_id: lv for lv in LEVELS}


# =========================================================================
# family 1 -- step semantics
# =========================================================================

#: (level_id, player, box, action).  Seven transitions, all five rules covered,
#: written out rather than sampled for the reason P-15 gives: a sampled set is a
#: different exam every time the seed moves, and freezing the rubric only means
#: something if the paper is frozen too.
_STEP_CASES: Tuple[Tuple[str, Tuple[int, int], Tuple[int, int], str], ...] = (
    ("warren", (0, 0), (5, 3), "RIGHT"),      # walk, Box nowhere near
    ("flume", (3, 1), (5, 5), "DOWN"),        # walk
    ("warren", (0, 0), (1, 0), "DOWN"),       # push: Box slides two, Player one
    ("kiln", (0, 1), (0, 2), "RIGHT"),        # push
    ("kiln", (3, 1), (5, 5), "LEFT"),         # wall ahead of the Player
    ("cairn", (0, 4), (0, 5), "RIGHT"),       # crossed cell is off the board
    ("warren", (0, 2), (0, 1), "LEFT"),       # landing cell is off the board
)


# =========================================================================
# family 2 -- which names are level data
# =========================================================================

#: Ten names.  Definitions are written as *pointers* into the manual wherever a
#: pointer exists -- `exam/STATUS.md` open weakness 9 records that P-15's
#: descriptive definitions let a cheater classify eleven of twelve names with no
#: manual at all, because the English gave it away.  A pointer says where the
#: name lives, not what kind of thing it is.
#:
#: `target` is the item this family exists for.  It is written in the manual's
#: own `goal:` clause, so "does it appear in the manual" answers it wrongly; it
#: is supplied per board, so reading the manual answers it correctly.
_VOCABULARY: Tuple[Tuple[str, str, str], ...] = (
    ("push2", "a name introduced in the manual's `rules:` section", "world_law"),
    ("blocked_box_landing",
     "a name introduced in the manual's `rules:` section", "world_law"),
    ("slid", "a name introduced in the manual's `events:` section", "world_law"),
    ("box_col_parity",
     "a name introduced in the manual's `laws:` section", "world_law"),
    ("beyond",
     "a name used inside rule guards, applied to an object and a direction",
     "world_law"),
    ("free",
     "a name used inside rule guards, applied to a cell", "world_law"),
    ("target",
     "the name written in the manual's `goal:` clause", "level_data"),
    ("walls",
     "the cells of one board that are not on the board's floor", "level_data"),
    ("height", "the number of rows a board has", "level_data"),
    ("start_box",
     "the cell the Box occupies before any action is taken", "level_data"),
)


# =========================================================================
# family 3 -- optimal action, and the length of the plan
# =========================================================================

#: (level_id, player, box).  Eight solvable states with shortest solutions of 11
#: to 25 actions, and the two dead boards.  No direction is the answer to more
#: than four of the ten, so answering one direction throughout is not a
#: strategy.
#:
#: **Every level appears exactly twice, and that is load-bearing rather than
#: tidy.** V25's pooled private-marker cut found a real leak here: the first eight
#: cases put `warren`/`flume`/`kiln` on two items each and `stile`/`cairn` on one
#: each, and `stile`/`cairn` were exactly the two dead boards -- so "does my
#: `level:` name occur only once *among the `optimal_action` items*" predicted
#: `solvable` 8 of 8, at an exact false-positive rate of 0.0357.  An examinee never
#: had to reason about a board to produce the `action=none; plan_len=none` those two
#: items existed to ask for.  The last two entries close it by giving each dead
#: board a *solvable* state as well, which makes level-name multiplicity uniform
#: and so predictive of nothing.  Adding a case here without keeping every level's
#: count equal reopens the channel; `test_level_multiplicity_is_uniform` fails if
#: it does.
#:
#: The scope matters and is easy to get wrong: `level:` tags ride the
#: `step_semantics` items too, so the *whole-sheet* version of the rule was 7 of 8
#: (it called `cairn` solvable).  The 8-of-8 rule is the family-scoped one, which is
#: also the scope the gate groups by.  Repaired and ruled on in
#: `runs/20260729T2215Z-V26-handover-leak-ruling/RULING.md`.
#:
#: Measured side effect, worth keeping: it also closed the *board-size* channel.
#: `stile` (6x7) and `cairn` (6x6) are the two smallest boards, and before the
#: repair they were also the only dead ones, so "smallest board => dead" was 2 of
#: 2.  Each now carries one dead and one solvable state, so that rule is 2 of 4.
_OPTIMAL_CASES: Tuple[Tuple[str, Tuple[int, int], Tuple[int, int]], ...] = (
    ("warren", (6, 7), (2, 6)),
    ("warren", (0, 0), (4, 6)),
    ("flume", (3, 1), (5, 5)),
    ("flume", (0, 0), (3, 3)),
    ("kiln", (0, 5), (3, 1)),
    ("kiln", (6, 6), (1, 3)),
    ("stile", (2, 0), (0, 5)),          # dead: column parity, the manual settles it
    ("cairn", (1, 5), (0, 5)),          # dead: no push admitted, only the playbook
    ("stile", (5, 0), (2, 4)),          # solvable in 11; balances `stile`
    ("cairn", (3, 5), (4, 1)),          # solvable in 11; balances `cairn`
)


def optimal_truth(spec: H.LevelSpec, player: Tuple[int, int],
                  box: Tuple[int, int]) -> Dict[str, Any]:
    """The whole accepted set, plus the length, plus whether there is one.

    Unlike `handover.optimal_actions` this does not raise on a dead board: a
    board with no solution is a question here rather than a build error, and the
    accepted answer on it is `none` for both fields.
    """
    length = H._plan_length(spec, player, box)
    if length is None:
        return {"solvable": False, "optimal_actions": [], "plan_len": None}
    if length == 0:
        raise H.HandoverError(
            "%s %s/%s is already won; an optimal-action item needs a state with "
            "at least one action left to take" % (spec.level_id, player, box))
    return {"solvable": True,
            "optimal_actions": H.optimal_actions(spec, player, box),
            "plan_len": length}


# =========================================================================
# family 4 -- why does this hold
# =========================================================================

#: (key, claim, candidates, rests_on, why).
#:
#: `rests_on` is the set of clauses whose **effect** -- the `then` half -- the
#: claim's truth uses.  That criterion is printed on the sheet, and it is the
#: reason `blocked_wall` is not cited for the parity claims: as written, its
#: effect moves nothing, so the claim does not depend on what it does.  Without
#: a criterion this family would be an argument about taste, and a rubric that
#: can be argued with after the answers arrive is not frozen.
#:
#: `why` is recorded in the truth file, not on the sheet.  A key that cannot say
#: why it is the key is a key nobody can check.
_WHY_CASES: Tuple[Tuple[str, str, Tuple[str, ...], Tuple[str, ...], str], ...] = (
    ("colparity",
     "Whatever the Player is told to do, the column the Box stands in keeps "
     "the parity it had before the action (odd stays odd, even stays even).",
     ("walk", "push2", "blocked_wall", "blocked_box_crossing",
      "blocked_box_landing"),
     ("push2",),
     "push2 is the only clause whose effect moves the Box, and it moves it two "
     "cells along one axis, so a column index changes by 0 or 2. The other four "
     "clauses move the Player or nothing; the claim does not depend on what they "
     "do."),

    ("mismatch",
     "On a board whose target cell has a different column parity from the cell "
     "the Box starts on, the game can never be won.",
     ("walk", "push2", "blocked_wall", "blocked_box_crossing",
      "blocked_box_landing", "goal_box_on_target"),
     ("push2", "goal_box_on_target"),
     "Two clauses and no more: push2 conserves the Box's column parity, and the "
     "goal clause is what makes winning mean the Box standing on the target. "
     "Drop either and the claim fails -- with a one-cell push the parity is not "
     "conserved; with a different victory condition the parity is irrelevant."),

    ("bump",
     "A Player standing beside a wall, with no Box between, told to move into "
     "that wall, is in exactly the situation it was in before.",
     ("walk", "push2", "blocked_wall", "blocked_box_crossing",
      "blocked_box_landing"),
     ("blocked_wall",),
     "This is blocked_wall's guard and blocked_wall's effect, and nothing "
     "else's: the guard names a cell ahead that is not free and no Box on it."),

    ("total",
     "For every situation and every action there is at least one clause of the "
     "manual that says what happens.",
     ("walk", "push2", "blocked_wall", "blocked_box_crossing",
      "blocked_box_landing", "goal_box_on_target"),
     ("walk", "push2", "blocked_wall", "blocked_box_crossing",
      "blocked_box_landing"),
     "Totality is a property of the five rules together -- remove any one and "
     "some situation is left unaccounted for. The goal clause says when the "
     "game is won, not what happens, so it carries no part of this claim."),

    ("frozen",
     "If the Box stands where no direction admits a push -- for every direction "
     "either the cell the Box would cross or the cell it would land on is not "
     "free, or the cell the Player would have to stand on is off the board or a "
     "wall -- then the Box will never move again, whatever the Player does.",
     ("walk", "push2", "blocked_wall", "blocked_box_crossing",
      "blocked_box_landing"),
     ("push2",),
     "Only push2's effect moves the Box, and the condition in the claim is "
     "exactly the negation of push2's guard, quantified over all four "
     "directions. The two blocked_box_* clauses describe the same situations but "
     "their effect is that nothing moves, so the claim does not rest on them."),
)


# =========================================================================
# family 4b -- refute a sentence the manual marks proven
# =========================================================================

_COUNTEREXAMPLE_CLAIM = "box_row_mod2_eq_1"

_COUNTEREXAMPLE_TEXT = (
    "The manual's `laws:` section contains the line\n"
    "    invariant box_row_parity (Box.pos.row) mod 2 = 1 [status: proven]\n"
    "which asserts that the row the Box stands in is always odd. Name a "
    "situation, on one of the boards listed in this item, at which that "
    "assertion is false. A situation is legal when both cells are on the board, "
    "neither is a wall, and the Player is not standing on the Box.")


def _counterexample_boards() -> List[Dict[str, Any]]:
    """The geometry the rubric needs to recompute the claim.

    It travels in the item's `truth` so that the rubric stays a pure function of
    (answer, truth, item) -- a marker that reads the world off disk is a marker
    whose result depends on the working directory.

    A *list*, with the board id in value position and the geometry under field
    names the sheet does not use.  Keyed by board id it shared eight key names
    with the sheet and `leakage.structural_hits` refused the paper, correctly:
    the same key on both sides is how a truth field turns into a sheet field
    without anyone noticing.
    """
    return [{"id": lv.level_id, "rows": lv.height, "cols": lv.width,
             "blocked": [list(w) for w in lv.walls]}
            for lv in LEVELS]


# =========================================================================
# the sheet's own instructions
# =========================================================================

INSTRUCTIONS = """\
You are a fresh reader of one framework's deliverable. You have been given a
bundle of documents and this sheet, and nothing else: no repository, no source
code beyond what the bundle contains, no record of anyone playing this world, no
earlier conversation. Everything you are entitled to use is in the bundle or in
the item itself.

The world is a grid world. The bundle says how it behaves. Each item that needs
one carries the geometry of a board and, where relevant, where the Player and
the Box are standing. Take the situation from the item, never from an earlier
item: every item stands alone.

%(legend)s

Four kinds of question appear, distinguished by each item's `kind` field.

  kind = "step_semantics"
      One action is taken from the given situation. Say what the situation is
      afterwards and which clause of the manual accounts for it.
      Answer grammar, exactly:
          player=(row,col); box=(row,col); rule=<name>
      All three fields, in any order, separated by semicolons. `<name>` is one
      of: %(rules)s
      All three fields must be right; two out of three scores nothing.

  kind = "name_class"
      A name is pointed at. Say whether it is something each individual board
      supplies (`level_data`) or something the world fixes once for every board
      (`world_law`). Whether the name appears in the manual is not the question.
      Answer grammar, exactly one word: %(classes)s

  kind = "optimal_action"
      Answer grammar, exactly:
          action=<A>; plan_len=<n>
      `<A>` names an action that begins a shortest sequence of actions ending
      with the Box on the target cell, and `<n>` is how many actions that
      shortest sequence contains. Where several actions begin some shortest
      sequence, any one of them is accepted; you do not have to find them all.
      `<A>` is one of: %(actions)s
      If the Box can never reach the target from the situation given, answer
      `action=none; plan_len=none`. The two halves are marked separately and are
      worth half the item each.

  kind = "rule_justification"
      A claim about this world is stated, together with a list of the manual's
      clauses. Name every listed clause the claim's truth depends on, and no
      others.
      Answer grammar, exactly:
          rests_on=<clause>+<clause>+...
      Depends on means: the claim's truth uses **what that clause does** -- the
      `then` half of it, the change it makes. A clause whose effect changes
      nothing the claim is about does not belong in your answer, even if a
      differently written clause in its place would have broken the claim. Order
      does not matter and a repeated name is counted once.
      Every clause you name that belongs earns; every clause you name that does
      not belong costs the same amount. Naming all of them is not a strategy.
      The full set is worth the whole item.

  kind = "counterexample"
      A sentence from the manual is quoted and you are asked for a situation at
      which it is false.
      Answer grammar, exactly:
          level=<board id>; player=(row,col); box=(row,col)
      The board id must be one of the boards the item lists. The situation must
      be legal on that board. It is marked by recomputing the quoted sentence at
      the situation you name.

Any item may instead be answered `abstain`. An abstention scores nothing and is
recorded as an abstention, not as a wrong answer; a guess that turns out wrong is
recorded as a wrong answer. An answer that is not a sentence of the grammar above
scores nothing and the parse failure is recorded. `abstain` and `none` are not
the same word: `none` is a claim about the world, `abstain` is a claim about you.

Submit a single JSON object whose keys are exactly the `item_id` values on this
sheet -- every one of them, none omitted, none invented -- and whose values are
answer strings. Nothing else: no commentary, no reasoning, no extra keys.\
""" % {
    "rules": " | ".join(PUBLISHED["rule_names"]),
    "classes": " | ".join(PUBLISHED["name_classes"]),
    "actions": " | ".join(PUBLISHED["actions"]),
    "legend": H.BOARD_LEGEND,
}


# =========================================================================
# the items
# =========================================================================

def _probes(item_id: str, canonical_answer: str,
            truth: Dict[str, Any]) -> Tuple[str, ...]:
    return ("%s => %s" % (item_id, canonical_answer), canonical(truth))


def _step_items() -> List[Item]:
    keys = ["%s|%s|%s|%s" % (lv, p, b, a) for lv, p, b, a in _STEP_CASES]
    items = []
    for n, index in enumerate(H._shuffled(keys), start=1):
        level_id, player, box, action = _STEP_CASES[index]
        spec = LEVEL_OF[level_id]
        truth = H._step_truth(spec, player, box, action)
        item_id = "v11-step-%02d" % n
        items.append(Item(
            item_id=item_id,
            rubric_id="handover_auto.step_semantics",
            points=POINTS[FAMILY_STEP],
            paper={
                "kind": "step_semantics",
                "level": spec.sheet_block(),
                "board": H.ascii_board(spec, player, box),
                "state": {"player": list(player), "box": list(box)},
                "action": action,
                "prompt": ("The Player takes the action %s. Give the situation "
                           "after the action and the clause that accounts for "
                           "it." % action),
            },
            truth=truth,
            leak_probes=_probes(item_id, H.step_answer_text(truth), truth),
            tags=(FAMILY_STEP, "level:" + level_id),
        ))
    return items


def _name_items() -> List[Item]:
    keys = [name for name, _d, _c in _VOCABULARY]
    items = []
    for n, index in enumerate(H._shuffled(keys), start=1):
        name, definition, cls = _VOCABULARY[index]
        truth = {"class": cls}
        item_id = "v11-name-%02d" % n
        items.append(Item(
            item_id=item_id,
            rubric_id="handover_auto.name_class",
            points=POINTS[FAMILY_NAMES],
            paper={
                "kind": "name_class",
                "name": name,
                "definition": definition,
                "prompt": ("Is `%s` supplied by each individual board, or fixed "
                           "by the world for every board?" % name),
            },
            truth=truth,
            leak_probes=_probes(item_id, "%s => %s" % (name, cls), truth),
            tags=(FAMILY_NAMES,),
        ))
    return items


def _optimal_items() -> List[Item]:
    keys = ["%s|%s|%s" % (lv, p, b) for lv, p, b in _OPTIMAL_CASES]
    items = []
    for n, index in enumerate(H._shuffled(keys), start=1):
        level_id, player, box = _OPTIMAL_CASES[index]
        spec = LEVEL_OF[level_id]
        truth = optimal_truth(spec, player, box)
        item_id = "v11-opt-%02d" % n
        items.append(Item(
            item_id=item_id,
            rubric_id="handover_auto.optimal_action",
            points=POINTS[FAMILY_OPTIMAL],
            paper={
                "kind": "optimal_action",
                "level": spec.sheet_block(),
                "board": H.ascii_board(spec, player, box),
                "state": {"player": list(player), "box": list(box)},
                "prompt": ("Name an action that begins a shortest sequence of "
                           "actions ending with the Box on the target cell, and "
                           "the length of that shortest sequence. If there is "
                           "no such sequence, answer "
                           "`action=none; plan_len=none`."),
            },
            truth=truth,
            leak_probes=_probes(
                item_id,
                "/".join(truth["optimal_actions"]) or NO_ACTION, truth),
            # No `dead`/`solvable` tag.  The first build carried one, and tags
            # are printed on the sheet: it told the reader, in one word, the
            # answer to the sharpest item on the paper.  `leakage.metadata_hits`
            # did not catch it because it buckets on the whole `tags` value,
            # which the `level:` token makes unique per item -- so the bucket
            # holding the leak had one member and was skipped as an identifier.
            # The dead/solvable split is recoverable from the key, where it
            # belongs; `test_no_single_tag_token_predicts_an_answer` is the
            # check that would have caught it.
            tags=(FAMILY_OPTIMAL, "level:" + level_id),
        ))
    return items


def _why_items() -> List[Item]:
    keys = [key for key, _c, _cand, _r, _w in _WHY_CASES]
    items = []
    for n, index in enumerate(H._shuffled(keys), start=1):
        key, claim, candidates, rests_on, why = _WHY_CASES[index]
        truth = {"rests_on": sorted(rests_on), "why": why}
        item_id = "v11-why-%02d" % n
        items.append(Item(
            item_id=item_id,
            rubric_id="handover_auto.rule_justification",
            points=POINTS[FAMILY_WHY],
            paper={
                "kind": "rule_justification",
                "claim": claim,
                "candidates": list(candidates),
                "prompt": ("Which of the listed clauses does this claim's truth "
                           "depend on? Name every one that does and no others."),
            },
            truth=truth,
            leak_probes=_probes(item_id, "+".join(sorted(rests_on)),
                                {"rests_on": sorted(rests_on)}),
            tags=(FAMILY_WHY, "why:" + key),
        ))
    return items


def _counterexample_item() -> Item:
    truth = {"claim": _COUNTEREXAMPLE_CLAIM,
             "legal_boards": _counterexample_boards()}
    item_id = "v11-why-ce-01"
    return Item(
        item_id=item_id,
        rubric_id="handover_auto.counterexample",
        points=POINTS[FAMILY_WHY],
        paper={
            "kind": "counterexample",
            "quoted": _COUNTEREXAMPLE_TEXT,
            "candidate_boards": {
                lv.level_id: {"height": lv.height, "width": lv.width,
                              "walls": [list(w) for w in lv.walls],
                              "board": H.ascii_board(lv, lv.start_player,
                                                     lv.start_box)}
                for lv in LEVELS},
            "prompt": ("Give a legal situation on one of these boards at which "
                       "the quoted sentence is false."),
        },
        truth=truth,
        leak_probes=("v11-why-ce-01 => box row even",),
        tags=(FAMILY_WHY, "counterexample"),
    )


def build() -> Paper:
    """Deterministic.  No wall clock, no RNG, no network, no model."""
    assert_synthetic_world(WORLD_ID)
    items = (_step_items() + _name_items() + _optimal_items() + _why_items()
             + [_counterexample_item()])
    paper = Paper(
        paper_id=PAPER_ID,
        question_type=QUESTION_TYPE,
        instructions=INSTRUCTIONS,
        items=items,
        world={"world_id": WORLD_ID, **provenance()},
    )
    paper.notes = {
        "prompt_id": PROMPT_ID,
        "families": {
            FAMILY_STEP: {"n": len(_STEP_CASES),
                          "points_each": POINTS[FAMILY_STEP]},
            FAMILY_NAMES: {"n": len(_VOCABULARY),
                           "points_each": POINTS[FAMILY_NAMES]},
            FAMILY_OPTIMAL: {"n": len(_OPTIMAL_CASES),
                             "points_each": POINTS[FAMILY_OPTIMAL]},
            FAMILY_WHY: {"n": len(_WHY_CASES) + 1,
                         "points_each": POINTS[FAMILY_WHY]},
        },
        "levels": {lv.level_id: {"height": lv.height, "width": lv.width,
                                 "walls": [list(w) for w in lv.walls],
                                 "target": list(lv.target),
                                 "start_player": list(lv.start_player),
                                 "start_box": list(lv.start_box)}
                   for lv in LEVELS},
        "rule_coverage": _rule_coverage(items),
        "tiers": list(TIERS),
        "citable_clauses": list(CITABLE),
        "prediction": PREDICTION,
    }
    return paper


def _rule_coverage(items: Sequence[Item]) -> Dict[str, int]:
    counts = {name: 0 for name in PUBLISHED["rule_names"]}
    for item in items:
        if item.rubric_id == "handover_auto.step_semantics":
            counts[item.truth["rule"]] += 1
    return counts


#: Written before any examinee was spawned, and stored in the truth file so that
#: it cannot be rewritten to match the result.  It is a prediction, which means
#: it is allowed to be wrong; what it is not allowed to be is retrofitted.
PREDICTION = {
    "registered": "before the first examinee ran; see the run's BLINDING.md",
    "overall": ("tier 2 (manual + playbook) scores at least as high as tier 1 "
                "(manual only). The prediction of Theoria.md 1.11 is that tier 1 "
                "can re-derive the playbook and draw level, so a delta near zero "
                "is a confirmation and not a null result -- provided the sheet "
                "is not saturated, which is what the harder boards are for."),
    "where_the_delta_should_land": (
        "optimal_action, and inside it on the two dead boards. `cairn` is the "
        "sharpest: every parity law the manual states matches there, so the "
        "manual alone cannot settle it by arithmetic, while the playbook writes "
        "the deadlock prune down. `stile` is settled by the manual's own "
        "invariant and should show no tier difference."),
    "where_it_should_not": (
        "step_semantics and name_class. The manual alone determines every "
        "transition and every classification; a delta there would mean the tiers "
        "differ in some way other than strategy, and that would have to be "
        "explained before any number here is quoted."),
    "saturation_guard": (
        "if either tier scores above 0.95 overall the sheet has saturated again "
        "and the delta carries no information, whatever its sign."),
}


# =========================================================================
# the bundles and the prompt handed to a reader
# =========================================================================

READER_BRIEF = """\
# Reader brief

## Who you are

You are a fresh reader. You have never seen this world. You have no repository,
no source code beyond the documents printed below, no record of anyone playing
it, and no earlier conversation about it. Everything you are entitled to use is
printed in this message.

**Answer from this message alone.** Do not open, search, read or execute any
file, and do not look anything up. Nothing outside this message is part of the
question, and using it would not make your answer better -- it would make this
whole exercise worthless, which is the one outcome it cannot recover from. If
something you need is not printed here, answer `abstain`.

## What you have been given

%(tier_line)s

## What to do

Read the documents. Then answer every item on the question sheet below,
following the answer grammar exactly.

## How you will be marked

By a fixed rule, written down and committed before your answers existed, applied
mechanically. An answer outside the published grammar scores zero and the parse
failure is recorded; it is not read charitably.

## Your report

After the JSON object, and only after it, add one line beginning `TOOLS:` saying
which tools you used, or `TOOLS: none`. It is not marked. It is asked because the
value of this whole exercise rests on you having answered from this message
alone, and an honest report of a slip is worth far more to us than a clean-looking
result.
"""

#: Two descriptions of two bundles, and nothing else.
#:
#: P-15's briefs said what each tier "measures" and what the playbook "adds",
#: and the tier-2 brief said the playbook covers "which situations are hopeless
#: and why".  Two of the items on this sheet are boards with no solution.  A
#: brief that tells one arm to expect hopeless boards manufactures the very
#: difference the run is trying to measure, and the manufactured part would be
#: indistinguishable from the real part afterwards.  So neither line mentions
#: the other bundle, what is being measured, or anything about the questions.
_TIER_LINE = {
    TIER1: ("**The manual.** It describes the world. There is no second "
            "document."),
    TIER2: ("**The manual and the playbook.** The manual describes the world; "
            "the playbook describes how to play it."),
}


def reader_brief(tier: str) -> str:
    if tier not in TIERS:
        raise H.HandoverError("no such tier %r; the two tiers are %s"
                              % (tier, list(TIERS)))
    return READER_BRIEF % {"tier_line": _TIER_LINE[tier]}


def bundle_text(tier: str) -> str:
    """The deliverable, and only the deliverable.

    `content_only=True` drops P-15's `READER_BRIEF.md`, which publishes the P-15
    answer grammar. Shipping a brief that contradicts this sheet would be a trap
    laid for the reader, and a wrong answer caused by a trap is not evidence
    about the deliverable.
    """
    return H.bundle_text(tier, content_only=True)


def prompt_text(tier: str, sheet: Dict[str, Any]) -> str:
    """Every byte an examinee of this tier receives.

    One string, self-contained, containing no path, no repository name, no
    branch and no mention of what is being measured.  It is handed to the
    examinee directly rather than by pointing at a directory, because a pointer
    is an invitation to look around, and looking around is exactly what a
    handover test must not permit.
    """
    import json
    return "\n\n".join([
        reader_brief(tier),
        "# The documents you were handed\n\n" + bundle_text(tier),
        "# The question sheet\n\n" + sheet["instructions"],
        "```json\n%s\n```" % json.dumps(
            {"items": [dict(i) for i in sheet["items"]]},
            indent=2, sort_keys=True, ensure_ascii=False),
    ])


# =========================================================================
# the calibration examinees
# =========================================================================

CALIBRATION_MODES: Tuple[str, ...] = ("oracle", "null", "memoriser", "bluffer")

#: What a bluffer says: one confident answer per family, chosen before the run.
_BLUFF = {
    "step_semantics": "player=(0,0); box=(0,0); rule=walk",
    "name_class": "world_law",
    "optimal_action": "action=UP; plan_len=1",
    "rule_justification": "rests_on=" + "+".join(sorted(CITABLE)),
    "counterexample": "level=warren; player=(0,0); box=(0,1)",
}


def _oracle_answer(entry: Dict[str, Any]) -> str:
    truth = entry["truth"]
    rubric_id = entry["rubric_id"]
    if rubric_id == "handover_auto.step_semantics":
        return H.step_answer_text(truth)
    if rubric_id == "handover_auto.name_class":
        return truth["class"]
    if rubric_id == "handover_auto.optimal_action":
        if not truth["solvable"]:
            return "action=none; plan_len=none"
        return "action=%s; plan_len=%d" % (truth["optimal_actions"][0],
                                           truth["plan_len"])
    if rubric_id == "handover_auto.rule_justification":
        return "rests_on=" + "+".join(sorted(truth["rests_on"]))
    if rubric_id == "handover_auto.counterexample":
        # The first legal situation with the Box on an even row, found by
        # scanning the boards the item offers. Computed, not written down: a
        # hand-written oracle answer is a place for the key and the rubric to
        # disagree quietly.
        for board in sorted(truth["legal_boards"], key=lambda b: b["id"]):
            level_id = board["id"]
            walls = {tuple(w) for w in board["blocked"]}
            cells = [(r, c) for r in range(board["rows"])
                     for c in range(board["cols"]) if (r, c) not in walls]
            for box in cells:
                if box[0] % 2 != 0:
                    continue
                for player in cells:
                    if player != box:
                        return "level=%s; player=(%d,%d); box=(%d,%d)" % (
                            level_id, player[0], player[1], box[0], box[1])
        raise H.HandoverError("no counterexample exists on the offered boards, "
                              "so the item cannot be asked")
    raise H.HandoverError("no oracle answer for rubric %r" % rubric_id)


def reference_answers(paper: Paper, key_doc: Dict[str, Any],
                      mode: str) -> Dict[str, str]:
    """The four fakes.  `oracle` must score 1.0 and `null` must score 0.0.

    They are the calibration the work order asks for in its own words: a known
    full-marks answer and a known zero-marks answer per question, used to check
    the marker *before* it marks a reader.  `memoriser` and `bluffer` are the two
    ways of scoring without understanding, and a sheet that cannot separate them
    from `oracle` is not measuring understanding.
    """
    if mode not in CALIBRATION_MODES:
        raise H.HandoverError("no such calibration mode %r; the modes are %s"
                              % (mode, list(CALIBRATION_MODES)))
    if mode == "null":
        return {}
    out: Dict[str, str] = {}
    kind_of = {i.item_id: i.paper.get("kind") for i in paper.items}
    for entry in key_doc["items"]:
        item_id = entry["item_id"]
        kind = kind_of.get(item_id)
        if mode == "oracle":
            out[item_id] = _oracle_answer(entry)
        elif mode == "bluffer":
            out[item_id] = _BLUFF[kind]
        elif mode == "memoriser":
            # Perfect on what the *bundle itself* states -- the five rules and
            # the parity laws -- and nothing else. It gets step semantics and
            # the arithmetic-dead board right, and has no answer anywhere a
            # search is required. This is the arm 1.11 warns about, and the
            # sheet has to separate it from a reader.
            if kind == "step_semantics":
                out[item_id] = _oracle_answer(entry)
            elif kind == "name_class":
                out[item_id] = "world_law"
            elif kind == "optimal_action":
                truth = entry["truth"]
                out[item_id] = ("action=none; plan_len=none"
                                if not truth["solvable"] else "abstain")
            elif kind == "rule_justification":
                out[item_id] = "rests_on=push2"
            else:
                out[item_id] = "abstain"
    return out


def submission(examinee_id: str, tier: str, answers: Dict[str, Any],
               meta: Optional[Dict[str, Any]] = None) -> Submission:
    if tier not in TIERS:
        raise H.HandoverError("no such tier %r" % tier)
    caps = ["manual"] + (["playbook"] if tier == TIER2 else [])
    return Submission(examinee_id=examinee_id, paper_id=PAPER_ID,
                      answers=answers,
                      capabilities=tuple([HANDOVER_CAPABILITY] + caps),
                      meta={"tier": tier, **(meta or {})})


#: Content words too common to carry meaning when two sentences are compared.
_STOP = frozenset("""a an and are as at be been by can cell cells does every
for from has have if in into is it its no not of on one or player that the
their then there this to when where which will with would""".split())

#: The DSL's own scaffolding.  Every playbook entry contains some of it, so
#: leaving it in would let any sentence match any entry a little, and the
#: threshold would have to rise until it caught nothing.
_SCAFFOLD = frozenset("""prune order heuristic prefer proof lean admissible
pos none""".split())


def _content_words(text: str, drop: frozenset = frozenset()) -> set:
    """Words that carry meaning, with `_` treated as a space.

    Splitting on the underscore is the whole reason this catches anything: the
    playbook writes `no_direction_admits_a_push(Box.pos)` as one identifier and
    the sheet writes "no direction admits a push" as five words. A comparison
    that kept the identifier whole would report no overlap between a sentence
    and its own restatement.
    """
    import re as _re
    return {w for w in _re.findall(r"[a-z]+", text.lower())
            if len(w) > 2 and w not in _STOP and w not in drop}


def cross_item_leak_report(paper: Paper, key_doc: Dict[str, Any], *,
                           threshold: float = 0.65) -> List[Dict[str, Any]]:
    """Does the sheet state, as a true claim, something only tier 2 is given?

    The check that did not exist when this paper was built, and whose absence
    the adversarial review called the run's decisive fault.  `leakage.py`
    compares an item's *metadata* with its own answer; nothing compared one
    item's **prose** with the content of the tier-2-only bundle.  Two
    `rule_justification` claims turned out to restate the playbook's two
    `prune` entries in English, on the tier-1 paper -- so the control arm was
    handed the treatment for the only family where a difference was predicted.

    The measure is *containment of the playbook entry*, |claim ∩ entry| over
    |entry|, and not Jaccard.  A playbook entry is six words and a sheet claim
    is thirty; Jaccard divides by the union and so scores a perfect restatement
    at 0.2, which is why the first version of this function found nothing.
    Containment asks the question that matters: has this entry been said again,
    somewhere the reader who was not given it can read?

    Returns findings rather than raising.  The two known offenders are on a
    shipped sheet that six readers have already sat; pinning them in a test is
    honest, deleting them retroactively is not.
    """
    playbook_only = [line.strip() for line in H.PLAYBOOK_DSL.splitlines()
                     if line.strip() and not line.strip().startswith("#")]
    findings: List[Dict[str, Any]] = []
    for item in paper.items:
        text = " ".join(str(v) for k, v in item.paper.items()
                        if k in ("claim", "prompt", "quoted"))
        words = _content_words(text)
        if not words:
            continue
        for entry in playbook_only:
            other = _content_words(entry, drop=_SCAFFOLD)
            if not other:
                continue
            overlap = len(words & other) / float(len(other))
            if overlap >= threshold:
                findings.append({
                    "item_id": item.item_id,
                    "playbook_entry": entry,
                    "containment": round(overlap, 4),
                    "shared": sorted(words & other),
                })
    findings.sort(key=lambda f: (f["item_id"], f["playbook_entry"]))
    return findings


def answer_labels(paper: Paper, key_doc: Dict[str, Any]) -> Dict[str, str]:
    """Short answer labels, so the leak checker's metadata test actually runs."""
    out: Dict[str, str] = {}
    for entry in key_doc["items"]:
        truth = entry["truth"]
        rid = entry["rubric_id"]
        if rid == "handover_auto.step_semantics":
            out[entry["item_id"]] = truth["rule"]
        elif rid == "handover_auto.name_class":
            out[entry["item_id"]] = truth["class"]
        elif rid == "handover_auto.optimal_action":
            out[entry["item_id"]] = ("/".join(truth["optimal_actions"])
                                     if truth["solvable"] else NO_ACTION)
        elif rid == "handover_auto.rule_justification":
            out[entry["item_id"]] = "+".join(truth["rests_on"])
    return out
