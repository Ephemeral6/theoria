"""题型 1 — held-out prediction, set in the A0 world.

Theoria.md 1.11: 「预测没见过的转移(held-out)——注意与重放的区别:重放是对过去的
预测,背题也能满分;held-out 才考规则本身」.  Everything in this module exists to
make that sentence measurable rather than quotable.

**The paper is two papers.**  Half the items are transitions the theory was
allowed to learn from (`replay`); half are transitions it was not (`heldout`).
The headline number is not either score, it is the **gap** — replay minus
held-out.  A rule-learner has a gap near zero.  A memoriser has a gap near its
whole score.  Reporting only the held-out fraction would confuse a memoriser
with a bad theorist, and reporting only replay would confuse it with a good one.

**The split rule, stated so it can be checked.**  Let

    E = { (frame_before, action) -> frame_after }

be every transition witnessed by `explore.evidence_set(level, per_class=4)` on
the five A0 evidence levels (`match` plus the four `crossing_*` levels) — that
is, the exact evidence a0-spike's own theory was mined from, not a fresh sample
invented here.  Let U be every *well-formed* board configuration of those five
levels crossed with the four actions: player and box on distinct non-wall cells
in bounds, 39,960 transitions in all.  Then

    replay items  are drawn from  E
    held-out items are drawn from U \\ E, keyed on (frame_before, action)

The key is the rendered frame and the action, nothing else.  It has to be: the
frame is what an examinee is shown, so "has this examinee seen this transition"
must be decidable from what it was shown.  Keying on internal coordinates would
let a memoriser that re-encodes states claim it had never seen something it had.
Frames are unique per level here (each level has a different number of wall
cells), so the key does not collide across geometries.

Selection is **pure enumeration** — no wall clock, no RNG, not even a seeded one.
Candidates are ordered by a sha256 of their own contents and taken round-robin
across the five levels, so the sample is spread over the board and over the
geometries instead of being the top-left corner of `match`.  A seeded RNG would
have done the same job, and would also have been one library upgrade away from
producing a different paper; a hash of the item cannot drift.

**Stratified on purpose, and the distortion is published.**  The natural class
mix of U is 74.8% `move`, 15.5% `blocked_edge`, 8.0% `blocked_wall`, 0.94%
`push`, 0.36% `blocked_landing` and 0.12% `blocked_crossing`.  A paper sampled
naturally would be three-quarters "the player walks one cell", which measures
almost nothing, and would contain a `blocked_crossing` item about once in every
830.  a0-spike's T-9 is precisely the story of a theory that was exact on 1,966
replayed transitions and wrong about `blocked_crossing`, so a paper that cannot
see that class cannot see the finding that motivates the whole item type.
`QUOTA` therefore over-samples it a hundredfold (104x as built, and `push` 43x),
and `notes["stratification"]`
carries the natural frequencies next to the quotas so a reader can undo the
weighting rather than be misled by it.

The quotas are **identical for the two splits**.  That is not symmetry for its
own sake: `Item.tags` rides on the sheet, so an examinee can see whether an item
is `replay` or `heldout`.  If the class mixes differed, that tag would be a hint
about the answer ("held-out items are mostly refusals, so guess 'nothing
happened' more often there").  Matched quotas make the tag carry exactly zero
information about the answer, which is cheaper than hiding it.

**Answers are frames, not coordinates.**  a0-spike's `certify*` replays through
the compiled manual and compares *rendered frames*, because a theory that tracks
the right positions and draws them wrong is still wrong (README, "certify runs
through the compiled manual").  Same here: the item shows the frame before, the
truth holds the frame after, and the rubric is whole-frame exact.

**What a do-nothing answer is worth is published, not hidden.**  Four of the six
classes have "the frame does not change" as their answer, so an examinee that
always returns the input frame scores `notes["unchanged_frame_share"]` — 45% as
built.  That number cannot be driven to zero without deleting the classes that
carry the guards, so the paper states its own bluffer ceiling instead of
pretending to be immune.  `axes()` reports it beside every score.

**`blocked_both` is excluded.**  124 configurations of U have *both* the crossed
cell and the landing cell blocked.  They are dropped rather than folded into
another class: the evidence set contains no witness of them at all, so they could
not be class-matched across the two splits, and lumping them into
`blocked_crossing` would inflate the rare class with items whose answer is
over-determined.  The count is recorded in `notes`.

**Imports.**  `pipeline.stages` and `pipeline.gen_exec` are deliberately *not*
imported even though `pipeline/adapt.py` takes all three.  They drag in
`engine-rig` and the theory-compiler parser respectively, and this paper needs
only rendered frames; an exam that fails to build because a generator changed
would be reporting on the generator.  a0-spike is appended to `sys.path` rather
than prepended, because its top-level packages are called `world` and `pipeline`
and prepending would let them shadow anything the exam imports later.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from ..guard import assert_synthetic_world, provenance
from ..model import Item, Paper, canonical, sha256_text

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # exam/
REPO = os.path.dirname(HERE)
A0_DIR = os.path.join(REPO, "a0-spike")
if A0_DIR not in sys.path:
    sys.path.append(A0_DIR)

from world import levels, sokoban2        # noqa: E402
from pipeline import explore              # noqa: E402

PAPER_ID = "p15-heldout-a0"
QUESTION_TYPE = "heldout"
WORLD_ID = "a0"
RUBRIC_ID = "heldout.frame_exact"

#: Fed to `explore.evidence_set`.  4 is a0-spike's own setting (`pipeline/adapt.py`
#: and `run_a0`); changing it would build the paper against evidence no theory in
#: this repository was ever mined from.
EVIDENCE_PER_CLASS = 4

#: Salts.  Two different ones so the sampling order and the presentation order
#: are independent -- if they shared a salt, "picked first" and "printed first"
#: would be the same fact and position would carry information about the sample.
_SAMPLE_SALT = "p15-heldout-a0/sample/"
_ORDER_SALT = "p15-heldout-a0/order/"

MOVE = "move"
PUSH = "push"
BLOCKED_WALL = "blocked_wall"
BLOCKED_EDGE = "blocked_edge"
BLOCKED_CROSSING = "blocked_crossing"
BLOCKED_LANDING = "blocked_landing"
BLOCKED_BOTH = "blocked_both"           # enumerated, then excluded -- see docstring

#: Frozen order.  Reordering changes nothing about the marks and everything about
#: whether two reports can be diffed, so it is pinned rather than sorted at use.
EVENT_CLASSES: Tuple[str, ...] = (
    MOVE, PUSH, BLOCKED_WALL, BLOCKED_EDGE, BLOCKED_CROSSING, BLOCKED_LANDING,
)

#: Items per class, per split.  `push` dominates because it is the only class
#: whose answer depends on the rule that carries A0's content -- the two-cell
#: slide -- and because every wrong theory a0-spike actually produced (push1,
#: push3, nocross, the under-guarded first pass) is wrong *here* and nowhere
#: else.  The two refusals that discriminate guards get five each rather than
#: four so that a by-tag fraction over them is not a coin flip.  `move` is held
#: down to six: it is 75% of the world and 0% of the difficulty.
QUOTA: Dict[str, int] = {
    MOVE: 6,
    PUSH: 16,
    BLOCKED_WALL: 4,
    BLOCKED_EDGE: 4,
    BLOCKED_CROSSING: 5,
    BLOCKED_LANDING: 5,
}

Frame = List[List[int]]
Cell = Tuple[int, int]

LEGEND = {"empty": sokoban2.EMPTY, "player": sokoban2.PLAYER,
          "box": sokoban2.BOX, "wall": sokoban2.WALL}

INSTRUCTIONS = (
    "A0 is a sokoban variant. Each item gives the geometry of a board, the "
    "rendered frame before an action, and the action. Predict the rendered "
    "frame after that action.\n\n"
    "Cell codes are in `legend`. Walls never move. Exactly one player and "
    "exactly one box are on every board. The four actions are UP, DOWN, LEFT, "
    "RIGHT.\n\n"
    "Answer with the frame after, as a list of rows of integers, either bare or "
    "under the key `frame_after` -- so either [[0, 2], [4, 0]] or "
    "{ \"frame_after\": [[0, 2], [4, 0]] } is accepted. Marking is whole-frame "
    "exact: a frame with one cell wrong scores the same as a frame with all of "
    "them wrong, because a theory that draws the world nearly right is a theory "
    "that has not been shown to draw it right.\n\n"
    "If your theory has no rule covering an item, answer { \"abstain\": true }. "
    "That scores nothing, and it is recorded as an abstention rather than as a "
    "wrong answer; guessing costs you nothing here, so the distinction is for "
    "the reader of your report, not for your total.\n\n"
    "The `tags` field says whether the transition occurred in the evidence you "
    "were given (`replay`) or did not (`heldout`). The two halves have the same "
    "mix of situations, so the tag tells you nothing about the answer."
)


# ------------------------------------------------------------------ the world

def _levels() -> Tuple[Any, ...]:
    """The five evidence levels, in a pinned order.

    `levels.EVIDENCE_LEVELS` is already `(MATCH,) + CROSSING_LEVELS` and
    `CROSSING_LEVELS` is built from a sorted dict, so this is stable; it is
    re-stated here so that a change upstream shows up as a changed paper digest
    rather than as a silently different sample.
    """
    return tuple(levels.EVIDENCE_LEVELS)


def _walls_of(level: Any) -> List[List[int]]:
    return [list(cell) for cell in sorted(level.walls)]


def _frame(level: Any, state: Any) -> Frame:
    return sokoban2.render(level, state)


def _free_cells(level: Any) -> List[Cell]:
    return [(r, c) for r in range(level.height) for c in range(level.width)
            if (r, c) not in level.walls]


def classify(level: Any, state: Any, action: str) -> str:
    """The ground-truth event class of one transition.

    Finer than `sokoban2.step`'s three labels, and the extra distinctions are the
    ones that cost a0-spike evidence to learn.  `step` lumps every refusal into
    `BLOCKED`; but "a wall in front of the player", "the board edge in front of
    the player", "the cell the box would cross is blocked" and "the cell the box
    would land on is blocked" are four different guards, and T-9 is the record of
    the third one surviving 1,966 exact replays undetected.  A paper that reports
    one `blocked` percentage cannot show that.

    The order of the tests mirrors `sokoban2.step` exactly, including that the
    crossed cell is checked before the landing cell, so `blocked_crossing` names
    the reason the world actually refused rather than a reason we prefer.
    """
    delta = sokoban2.DELTA[action]
    target = (state.player[0] + delta[0], state.player[1] + delta[1])
    if not sokoban2.in_bounds(level, target):
        return BLOCKED_EDGE
    if sokoban2.is_wall(level, target):
        return BLOCKED_WALL
    if target != state.box:
        return MOVE
    crossed = (state.box[0] + delta[0], state.box[1] + delta[1])
    landing = (state.box[0] + 2 * delta[0], state.box[1] + 2 * delta[1])

    def clear(cell: Cell) -> bool:
        return sokoban2.in_bounds(level, cell) and not sokoban2.is_wall(level, cell)

    crossed_ok, landing_ok = clear(crossed), clear(landing)
    if crossed_ok and landing_ok:
        return PUSH
    if not crossed_ok and landing_ok:
        return BLOCKED_CROSSING
    if crossed_ok and not landing_ok:
        return BLOCKED_LANDING
    return BLOCKED_BOTH


# --------------------------------------------------------------- transitions

class _Candidate:
    """One transition, everything the item needs, nothing it does not."""

    __slots__ = ("level_name", "level", "state", "action", "before", "after",
                 "next_state", "event")

    def __init__(self, level: Any, state: Any, action: str) -> None:
        self.level = level
        self.level_name = level.name
        self.state = state
        self.action = action
        self.event = classify(level, state, action)
        nxt, _ = sokoban2.step(level, state, action)
        self.next_state = nxt
        self.before = _frame(level, state)
        self.after = _frame(level, nxt)

    @property
    def key(self) -> str:
        return transition_key(self.before, self.action)

    def order_key(self, salt: str) -> str:
        return sha256_text(salt + canonical(
            [self.level_name, list(self.state.player), list(self.state.box),
             self.action]))


def transition_key(frame_before: Sequence[Sequence[int]], action: str) -> str:
    """The identity of a transition *as an examinee can see it*.

    Frame plus action, canonically serialised.  Deliberately not (level, player,
    box, action): the whole question is whether this examinee has seen this
    transition, and the only thing it was ever shown is the frame.
    """
    return canonical([[list(row) for row in frame_before], action])


_EVIDENCE: Optional[Dict[str, Frame]] = None
_UNIVERSE: Optional[List[_Candidate]] = None


def evidence_index() -> Dict[str, Frame]:
    """`transition_key -> frame_after` for every transition in the evidence set.

    This is the memoriser's entire mind, and it is also what makes the split
    checkable from outside: a test can rebuild this from `explore` and
    `sokoban2` alone and assert that no held-out item's key is in it, without
    taking the builder's word for anything.
    """
    global _EVIDENCE
    if _EVIDENCE is None:
        index: Dict[str, Frame] = {}
        for level in _levels():
            evidence = explore.evidence_set(level, per_class=EVIDENCE_PER_CLASS)
            for run in evidence["episodes"]:          # type: ignore[index]
                state = sokoban2.initial_state(level)
                for action in run["actions"]:
                    before = _frame(level, state)
                    state, _ = sokoban2.step(level, state, action)
                    index.setdefault(transition_key(before, action),
                                     _frame(level, state))
        _EVIDENCE = index
    return _EVIDENCE


def _universe() -> List[_Candidate]:
    """Every well-formed (state, action) of the five levels.

    Well-formed = player and box on distinct non-wall cells in bounds.  This is
    a0-spike's own held-out sweep (README: "39,960 states across 5 levels"),
    reused rather than re-invented so that the exam and the spike are talking
    about the same set.
    """
    global _UNIVERSE
    if _UNIVERSE is None:
        out: List[_Candidate] = []
        for level in _levels():
            cells = _free_cells(level)
            for player in cells:
                for box in cells:
                    if player == box:
                        continue
                    state = sokoban2.State(player=player, box=box)
                    for action in sokoban2.DIRECTIONS:
                        out.append(_Candidate(level, state, action))
        _UNIVERSE = out
    return _UNIVERSE


def _split_pools() -> Tuple[Dict[str, List[_Candidate]], Dict[str, List[_Candidate]],
                            Dict[str, int], int]:
    """(replay pool, heldout pool, natural class counts, blocked_both dropped)."""
    seen = evidence_index()
    replay: Dict[str, List[_Candidate]] = {c: [] for c in EVENT_CLASSES}
    heldout: Dict[str, List[_Candidate]] = {c: [] for c in EVENT_CLASSES}
    natural: Dict[str, int] = {}
    dropped = 0
    for cand in _universe():
        natural[cand.event] = natural.get(cand.event, 0) + 1
        if cand.event == BLOCKED_BOTH:
            dropped += 1
            continue
        (replay if cand.key in seen else heldout)[cand.event].append(cand)
    return replay, heldout, natural, dropped


def _round_robin(candidates: Sequence[_Candidate], quota: int) -> List[_Candidate]:
    """Take `quota` candidates, spread across levels, deterministically.

    Taking the hash-ordered head of the whole pool would be deterministic too,
    and would also happily return five items from `match` and none from the
    `crossing_*` levels -- which is the exact blindness T-9 is about.  So the
    pool is bucketed by level and drained one level at a time.
    """
    by_level: Dict[str, List[_Candidate]] = {}
    for cand in candidates:
        by_level.setdefault(cand.level_name, []).append(cand)
    for group in by_level.values():
        group.sort(key=lambda c: c.order_key(_SAMPLE_SALT))
    names = sorted(by_level)
    out: List[_Candidate] = []
    depth = 0
    while len(out) < quota:
        progressed = False
        for name in names:
            group = by_level[name]
            if depth < len(group):
                out.append(group[depth])
                progressed = True
                if len(out) == quota:
                    break
        if not progressed:
            break
        depth += 1
    return out


# ---------------------------------------------------------------- item making

def _probes(cand: _Candidate, split: str, before_frames: Iterable[str]
            ) -> Tuple[List[str], bool]:
    """What would give this item's answer away, as exact strings.

    Three of the four probes are key-qualified -- `"frame_after":[[...` and so on
    -- so they fire only when the truth object itself has been copied into the
    paper, which is the leak that actually happens.  They cannot false-positive:
    inside the sheet's own prose those characters are escaped, so `\\"frame_after\\"`
    does not match `"frame_after"`.

    The fourth is the bare serialised after-frame, which is the strong probe: it
    fires even if a leak arrives under some innocent field name.  It has to be
    dropped for two kinds of item.  For every refusal the after-frame *is* the
    before-frame, so it is in the sheet by construction and the probe would
    report a leak on a clean paper.  And a `move` or `push` can land on a frame
    that is some *other* item's starting frame, which is a coincidence and not a
    leak -- an examinee cannot tell which of eighty frames is its answer.  Both
    cases are counted in `notes["probes"]` rather than passed over in silence:
    the number of items whose strongest probe had to be withdrawn is exactly the
    number a reader should be suspicious about.
    """
    after = canonical(cand.after)
    probes = [
        '"frame_after":' + after,
        '"event":"%s"' % cand.event,
        '"split":"%s"' % split,
        canonical({"box": list(cand.next_state.box),
                   "player": list(cand.next_state.player)}),
    ]
    bare_ok = after not in set(before_frames)
    if bare_ok:
        probes.append(after)
    return probes, bare_ok


def build() -> Paper:
    """Deterministic.  Two calls produce byte-identical sheets."""
    assert_synthetic_world(WORLD_ID)

    replay_pool, heldout_pool, natural, dropped_both = _split_pools()

    chosen: List[Tuple[str, _Candidate]] = []
    shortfalls: Dict[str, Dict[str, int]] = {}
    for event in EVENT_CLASSES:
        quota = QUOTA[event]
        for split, pool in (("replay", replay_pool), ("heldout", heldout_pool)):
            picked = _round_robin(pool[event], quota)
            if len(picked) < quota:
                # Refuse rather than quietly shrink a class.  An unmatched quota
                # breaks the one property that makes the `replay`/`heldout` tag
                # safe to print on the sheet, and a paper that silently drops the
                # rare class is the failure this item type exists to catch.
                shortfalls[event] = {"split_%s_available" % split: len(pool[event]),
                                     "quota": quota}
                continue
            chosen.extend((split, cand) for cand in picked)
    if shortfalls:
        raise RuntimeError(
            "the A0 evidence set no longer supports matched quotas: %s. Lower "
            "QUOTA for the affected class or raise EVIDENCE_PER_CLASS, but do "
            "not let the two splits differ in class mix -- that turns the tag on "
            "the sheet into a hint." % canonical(shortfalls))

    # Presentation order: a hash of the candidate under a salt unrelated to the
    # sampling salt, so neither position nor item_id correlates with the answer.
    # `leakage.positional_report` is run over this in the test suite rather than
    # trusted.
    chosen.sort(key=lambda pair: (sha256_text(_ORDER_SALT + pair[0]
                                              + pair[1].order_key(_SAMPLE_SALT))))

    before_frames = {canonical(cand.before) for _, cand in chosen}

    items: List[Item] = []
    bare_probe_dropped = 0
    for position, (split, cand) in enumerate(chosen):
        probes, bare_ok = _probes(cand, split, before_frames)
        if not bare_ok:
            bare_probe_dropped += 1
        items.append(Item(
            item_id="%s-%03d" % ("a0h", position),
            rubric_id=RUBRIC_ID,
            points=1.0,
            paper={
                "level": {"height": cand.level.height, "width": cand.level.width,
                          "walls": _walls_of(cand.level)},
                "frame_before": cand.before,
                "action": cand.action,
                "legend": dict(LEGEND),
            },
            truth={
                "frame_after": cand.after,
                "event": cand.event,
                "player_after": list(cand.next_state.player),
                "box_after": list(cand.next_state.box),
                "level_name": cand.level_name,
                "split": split,
            },
            leak_probes=tuple(probes),
            tags=(split,),
        ))

    unchanged = sum(1 for _, cand in chosen if cand.before == cand.after)
    total_natural = sum(natural.values())

    notes = {
        "split_rule": (
            "replay items are transitions in E = explore.evidence_set(level, "
            "per_class=%d) pooled over levels.EVIDENCE_LEVELS; held-out items "
            "are well-formed (state, action) pairs of the same five levels whose "
            "(frame_before, action) key is NOT in E. Selection is pure "
            "enumeration ordered by sha256 of the candidate, round-robin over "
            "levels; there is no RNG and no wall clock."
            % EVIDENCE_PER_CLASS),
        "evidence": {
            "levels": [lv.name for lv in _levels()],
            "per_class": EVIDENCE_PER_CLASS,
            "unique_transitions": len(evidence_index()),
        },
        "universe": {
            "well_formed_transitions": total_natural,
            "definition": ("player and box on distinct non-wall in-bounds cells, "
                           "times four actions"),
        },
        "stratification": {
            "quota_per_split": dict(QUOTA),
            "natural_counts": dict(sorted(natural.items())),
            "natural_share": {k: round(v / total_natural, 6)
                              for k, v in sorted(natural.items())},
            "oversampling_factor": {
                event: round((QUOTA[event] / sum(QUOTA.values()))
                             / (natural[event] / total_natural), 3)
                for event in EVENT_CLASSES if natural.get(event)},
            "why": ("the natural mix is three-quarters `move` and under half a "
                    "percent `blocked_crossing`; a naturally sampled paper of "
                    "this size would contain no witness of the class T-9 says "
                    "only held-out testing can catch."),
            "matched_across_splits": True,
        },
        "excluded": {
            "blocked_both": dropped_both,
            "why": ("both the crossed and the landing cell blocked: no witness in "
                    "the evidence set, so the class cannot be matched across the "
                    "two splits, and folding it into blocked_crossing would pad "
                    "the rare class with over-determined items."),
        },
        "unchanged_frame_share": round(unchanged / len(items), 6),
        "unchanged_frame_note": (
            "the score of an examinee that always returns the input frame. "
            "Published because it cannot be made small without deleting the "
            "classes that carry the guards."),
        "probes": {
            "bare_after_frame_withdrawn": bare_probe_dropped,
            "why": ("the bare after-frame probe is vacuous for a refusal (the "
                    "answer is the input) and would false-positive where one "
                    "item's answer is another item's starting frame; the "
                    "key-qualified probes are declared for every item."),
        },
        "rare_class": BLOCKED_CROSSING,
    }

    return Paper(
        paper_id=PAPER_ID,
        question_type=QUESTION_TYPE,
        instructions=INSTRUCTIONS,
        items=items,
        # The description used to read "sokoban in which a push slides the box
        # two cells". That sentence is the rule the examinee is being tested on
        # -- a cheater subagent given the sheet alone went from 47.5% (generic
        # sokoban prior, one-cell push) to essentially full marks on the
        # strength of it. A held-out paper that publishes the mechanic is not a
        # held-out paper. The world block now says which world it is and
        # nothing about how it behaves.
        world={"world_id": WORLD_ID,
               "description": ("A0: a self-built grid world with a figure and a "
                               "movable object. Ground truth fully known, in "
                               "neither pile. Its dynamics are what this paper "
                               "asks about and are deliberately not stated here."),
               **provenance()},
        notes=notes,
    )


# ------------------------------------------------------- calibration examinees

def _grid(frame: Sequence[Sequence[int]]) -> Frame:
    return [list(row) for row in frame]


def _naive_successor(before: Frame, action: str) -> Optional[Frame]:
    """The memoriser's fallback theory: push one cell, and no guards at all.

    Not an arbitrary wrong answer.  This is a0-spike's `push1` variant crossed
    with its `ghost` variant -- the two mis-theories the spike actually produced
    and measured -- so the memoriser's held-out failures are the failures a real
    under-evidenced theory makes, not noise.  It walks onto walls, slides the box
    into the cell it should have been blocked by, and gets ordinary moves right,
    which is exactly why replay-only certification cannot tell it from the truth.

    Returns None where the naive rule would put the player off the board: there
    is no frame to draw, and the memoriser abstains rather than invent one.  That
    is the single place its ignorance is legible to itself.
    """
    height, width = len(before), len(before[0])
    walls, player, box = [], None, None
    for r, row in enumerate(before):
        for c, value in enumerate(row):
            if value == sokoban2.WALL:
                walls.append((r, c))
            elif value == sokoban2.PLAYER:
                player = (r, c)
            elif value == sokoban2.BOX:
                box = (r, c)
    if player is None or box is None:
        return None

    dr, dc = sokoban2.DELTA[action]
    target = (player[0] + dr, player[1] + dc)
    if not (0 <= target[0] < height and 0 <= target[1] < width):
        return None
    if target == box:
        landing = (box[0] + dr, box[1] + dc)
        if not (0 <= landing[0] < height and 0 <= landing[1] < width):
            return None
        box = landing

    grid = [[sokoban2.EMPTY] * width for _ in range(height)]
    for (r, c) in walls:
        grid[r][c] = sokoban2.WALL
    grid[box[0]][box[1]] = sokoban2.BOX
    grid[target[0]][target[1]] = sokoban2.PLAYER
    return grid


def reference_answers(paper: Paper, key_doc: Optional[Dict[str, Any]] = None,
                      mode: str = "oracle") -> Dict[str, Any]:
    """The four calibration examinees of `exam.papers.CALIBRATION_MODES`.

    `memoriser` is the one this paper is built for.  It answers from a table of
    the evidence transitions keyed exactly as the split was made, so it is
    perfect on `replay` by construction; everywhere else it falls back to a
    plausible under-evidenced theory.  It does not score zero on held-out and no
    honest construction would make it: a sixth of the held-out items are ordinary
    moves, and any theory at all gets those right.  The measurement is the gap,
    not the floor.
    """
    truth_of: Dict[str, Dict[str, Any]] = {}
    if key_doc is not None:
        truth_of = {entry["item_id"]: entry["truth"] for entry in key_doc["items"]}
    else:
        truth_of = {item.item_id: item.truth for item in paper.items}

    if mode == "null":
        # Not `{item_id: None}`: an examinee that submits nothing is `unanswered`,
        # which the marker keeps distinct from `wrong` on purpose.
        return {}

    if mode == "oracle":
        return {item.item_id: {"frame_after": _grid(truth_of[item.item_id]["frame_after"])}
                for item in paper.items}

    if mode == "bluffer":
        # Bare grids rather than the dict form, so the rubric's acceptance of both
        # shapes is exercised by a calibration run instead of asserted in prose.
        return {item.item_id: _grid(item.paper["frame_before"])
                for item in paper.items}

    if mode == "memoriser":
        seen = evidence_index()
        out: Dict[str, Any] = {}
        for item in paper.items:
            before = item.paper["frame_before"]
            action = item.paper["action"]
            recalled = seen.get(transition_key(before, action))
            if recalled is not None:
                out[item.item_id] = {"frame_after": _grid(recalled)}
                continue
            guess = _naive_successor(_grid(before), action)
            out[item.item_id] = ({"abstain": True} if guess is None
                                 else {"frame_after": guess})
        return out

    raise KeyError("unknown calibration mode %r" % mode)


# ------------------------------------------------------------------- the axes

def _bucket(scores: Sequence[Any]) -> Dict[str, Any]:
    got = sum(s.awarded for s in scores)
    can = sum(s.possible for s in scores)
    return {"n": len(scores), "awarded": round(got, 6), "possible": round(can, 6),
            "fraction": round(got / can, 6) if can else 0.0}


def axes(report: Any, key_doc: Dict[str, Any], submission: Any) -> Dict[str, Any]:
    """The gap, and the breakdown that stops the gap from being a single number.

    `gap_replay_minus_heldout` is the headline.  It is the quantity Theoria.md
    1.11 is pointing at when it says 背题也能满分: a memoriser scores full marks
    on replay and collapses on held-out, so the difference is the part of a score
    that memory can account for.  Zero gap is the good result, and it is only
    meaningful next to the held-out score itself -- an examinee that scores 12%
    on both has a gap of zero and knows nothing, which is why both are reported
    and neither is reported alone.

    `by_split_event` is the T-9 view.  a0-spike's under-guarded `push2` was exact
    on every replayed transition and wrong on `blocked_crossing`; in this table
    that theory shows up as a single cell at zero while every other cell is full,
    and in a single percentage it shows up as 97%.
    """
    truth_of = {entry["item_id"]: entry["truth"] for entry in key_doc["items"]}

    by_split: Dict[str, List[Any]] = {}
    by_event: Dict[str, List[Any]] = {}
    by_both: Dict[str, List[Any]] = {}
    unchanged_answer = 0
    for score in report.scores:
        truth = truth_of.get(score.item_id, {})
        split = truth.get("split", "unknown")
        event = truth.get("event", "unknown")
        by_split.setdefault(split, []).append(score)
        by_event.setdefault(event, []).append(score)
        by_both.setdefault("%s/%s" % (split, event), []).append(score)
        if event not in (MOVE, PUSH):
            unchanged_answer += 1

    splits = {name: _bucket(group) for name, group in sorted(by_split.items())}
    replay = splits.get("replay", {}).get("fraction")
    heldout = splits.get("heldout", {}).get("fraction")
    gap = (round(replay - heldout, 6)
           if replay is not None and heldout is not None else None)

    rare = {name: _bucket(group) for name, group in sorted(by_both.items())
            if name.endswith("/" + BLOCKED_CROSSING)}

    total = len(report.scores)
    return {
        "by_split": splits,
        "gap_replay_minus_heldout": gap,
        "gap_note": ("replay minus held-out. A rule-learner is near zero; a "
                     "memoriser is near its own replay score. Read it beside "
                     "by_split.heldout.fraction, never instead of it."),
        "by_event": {name: _bucket(group) for name, group in sorted(by_event.items())},
        "by_split_event": {name: _bucket(group)
                           for name, group in sorted(by_both.items())},
        "rare_class": BLOCKED_CROSSING,
        "rare_class_scores": rare,
        "unchanged_frame_share": round(unchanged_answer / total, 6) if total else 0.0,
        "unchanged_frame_note": ("what an examinee scores by always returning the "
                                 "input frame -- the bluffer's ceiling on this "
                                 "paper, published rather than assumed small."),
        "abstained": sum(1 for s in report.scores if s.verdict == "abstained"),
        "unanswered": sum(1 for s in report.scores if s.verdict == "unanswered"),
    }
