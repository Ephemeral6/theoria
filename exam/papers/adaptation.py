"""Question type 3 — change one rule of the world, and measure the repair.

Theoria.md 1.11 asks for one line of it: 「改一条规则,多快适应回来」.
`a0-spike/pipeline/adapt.py` answers that line once, by hand, in a script, and
its docstring names the three quantities worth measuring — detection latency,
repair cost, and collateral invalidation.  This module mechanises that script
into an exam: it enumerates variant worlds programmatically, derives each one's
ground truth by construction and computation over `a0-spike/world/sokoban2.py`,
and sets sixty items whose answers the examinee has to earn from observations.

**Collateral is the item that matters and it is weighted accordingly.**  Sixty
of the paper's 144 points sit on it.  The reason is the one `adapt.py` gives:
detection and repair are engineering, but a theorem that silently becomes false
is the failure this whole architecture exists to prevent.  `theorem
unsolvable_mismatch [depends: push2]` is not decoration — two of the six
variants here flip that theorem's verdict outright, and a framework that skipped
the dependency step would go on confidently declaring a now-winnable level
impossible while every one of its own replay checks still passed.  The rubric
therefore raises `silently_wrong` as a labelled flag and `axes()` reports it as
its own integer, because an examinee can keep the old verdict on both flipped
variants and still show a respectable percentage, and the percentage is the
number that would hide it.

Four design calls, each with the simpler option that was rejected.

**Variants are enumerated, not listed.**  `Rules` is a frozen dataclass whose
three fields are three rules of the world (`sokoban2.py` says so in as many
words), so the variant family is the product of a small grid over those fields
plus a short allowlist of compositions.  A hand-written list would have been
half the code and would also have quietly encoded the author's idea of which
changes are interesting; the grid does not, and it turned up the composition
that matters most here — see the next paragraph.

**Truth comes from the world, never from the examinee and never from a table.**
Every quantity is computed: first divergence by replaying the old theory against
the variant world along the deterministic exploration, falsified rules by
classifying every configuration on which the base and variant transition
functions disagree, claim survival by checking the invariants over the whole
configuration space and the theorem by breadth-first search, repair cost and
exactness by actually re-mining and then testing on a board the evidence never
visited.  The one place a table appears is the opaque variant id, and it lives
in `Paper.notes`, i.e. in the truth file only.

**The paper never names the changed rule.**  Variants are `v-a0-01` … `v-a0-06`
in an order fixed by a digest, and the sheet carries observations: level
geometry, and per episode a list of `[action, figure cell, box cell]` after each
action.  What the sheet does *not* carry is the changed field, the transparent
variant name, the first-divergence index, or the names of the claims — every one
of those is a declared leak probe on every item.  The answer alphabets an
examinee needs are in `exam/grading/rubrics_adaptation.py`, which is public by
construction (the sheet carries its digest) and contains no variant table.

**One variant is undetectable on the base level, and that is the point.**
`adapt.py::detection_across_levels` records why: a guard weakening is invisible
until you stand somewhere the old and the new guard disagree, and `match` can
make that configuration unreachable — every wall on it sits on an even-parity
cell while the cell a sliding box crosses always has odd parity (THEORIZE_LOG
T-9).  So one variant runs the base level's entire exploration, 341 actions,
without the old theory being wrong once, and is caught on `crossing_UP` at
action 6.  "Detected at step N" is a wrong answer there; "never here, and here
is where it does show" is the right one, and the `detect` rubric pays nothing
for the plausible version.

The composition grid found a second trap without being asked to.  One variant
changes two fields — the box travels one cell *and* the crossing rule is
dropped — and is **observationally identical** to changing only the travel
distance, because at a travel distance of one cell there are no crossed cells
for the crossing rule to govern.  Its `describe` truth is therefore the
one-label answer, verified mechanically by comparing full transition tables over
every registered level, and an examinee that names both changes is claiming
something no observation can support.

**Substitution, recorded because it is load-bearing.**  `adapt.py` predicts with
the executable form compiled from `a0-spike/theory/theory.dsl` by
`gen_exec.compile_module`.  That path is broken in this checkout and not by
anything here: the theory-compiler track's parser has moved to grammar v0.2 and
refuses a manual with no `semantics:` section, which the A0 manual predates, so
every test in `a0-spike/tests/test_a0.py` currently errors on the import.  The
A0 manual is that track's file and this exam does not edit it.  The old theory's
predictions are therefore taken from `sokoban2.step` under the *base* rules,
which is what the compiled manual computes — the manual was certified exact
against the base world, and its five guards are the base transition function
written out.  `exam/tests/test_adaptation.py` checks that equivalence against the
compiled module whenever the compiler can parse the manual, and skips with the
reason when it cannot, so the substitution is verified rather than asserted the
day the other track lands its fix.

**What the caps cost.**  Streams are capped at 640 observations per level.  The
cap bites on two streams only (921 and 920 actions, both on the shortest-travel
variants), and both diverge inside the first 60 actions, so no cap ever hides a
divergence; `build()` asserts that rather than trusting it.  The one place
completeness is required — the level where the truth is "never" — is 341 actions
and is embedded whole, because "no divergence in the first 640 of 341" is a
sentence with nothing in it.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, replace
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..guard import assert_synthetic_world, provenance
from ..model import ExamError, Item, Paper, sha256_text
from ..grading.rubrics_adaptation import (CHANGE_LABELS, CLAIMS, MANUAL_RULES,
                                          OLD_VERDICT)

HERE = os.path.dirname(os.path.abspath(__file__))
EXAM = os.path.dirname(HERE)
REPO = os.path.dirname(EXAM)
A0_ROOT = os.path.join(REPO, "a0-spike")
ENGINE_RIG = os.path.join(REPO, "engine-rig")
for _path in (A0_ROOT, ENGINE_RIG):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from pipeline import explore, stages                       # noqa: E402
from world import levels, sokoban2                         # noqa: E402
from world.sokoban2 import DELTA, DIRECTIONS, Level, Rules, State   # noqa: E402

PAPER_ID = "p15-adaptation-a0"
QUESTION_TYPE = "adaptation"

#: The base world is `a0`; every variant of it is `a0-prime`.  Both are in
#: `exam.guard.SYNTHETIC_WORLDS`; neither is in either pile.
BASE_WORLD_ID = "a0"
WORLD_ID = "a0-prime"

#: Exploration density, matching `adapt.py`.  Raising it lengthens every stream
#: without changing a single truth, so it is pinned rather than tuned.
PER_CLASS = 4

#: Observations embedded per (variant, level).  See the module docstring for
#: what the cap costs.
STREAM_CAP = 640

#: The board the repaired theory is tested on.  Its obstruction layout appears
#: in no evidence level, so "exact here" is a claim about states the miner never
#: saw -- which is the only kind of exactness worth scoring (Theoria.md 1.11:
#: 重放是对过去的预测,背题也能满分).
HELDOUT_WALLS: Tuple[Tuple[int, int], ...] = ((1, 1), (2, 4), (4, 4), (5, 2))

BASE_RULES = Rules()
_FIELDS: Tuple[str, ...] = ("push_distance", "require_crossing_free",
                            "walls_block_player")

#: One non-base value per field, in a fixed order.  Two for the travel distance
#: because shorter and longer are different worlds: one kills the conservation
#: law and flips the theorem, the other kills the law and leaves the theorem's
#: statement standing.  An exam with only one of them cannot tell "the proof
#: broke" from "the conclusion broke".
_VARIANT_GRID: Dict[str, Tuple[Any, ...]] = {
    "push_distance": (1, 3),
    "require_crossing_free": (False,),
    "walls_block_player": (False,),
}

#: Compositions, allowlisted with their reason.  Not the full product: most of
#: the twelve cells of the product are two independent changes sitting next to
#: each other, which measures nothing the singles do not.  These two do not.
_COMPOSITIONS: Tuple[Tuple[Dict[str, Any], str], ...] = (
    ({"push_distance": 3, "require_crossing_free": False},
     "two cells are crossed and the crossing rule is gone, so the guard change "
     "is observable rather than vacuous -- the only cell of the product where "
     "both changes have witnesses in the same transition"),
    ({"push_distance": 1, "require_crossing_free": False},
     "the same pair with the travel distance shortened instead, which makes the "
     "crossing rule govern nothing at all: this variant is observationally "
     "identical to the single change and its describe truth says so"),
)

#: Which manual rule each registered claim hangs off.  The theorem's edge is
#: read from its own `[depends: ...]` annotation; the invariants carry no such
#: annotation in v0.1 of the manual, so their edge is computed instead -- an
#: invariant over the box's position depends on exactly the rules that move the
#: box, and which rules those are is a question about the base world that
#: `_box_moving_rules()` answers by running it.
_THEOREM_CLAIM = "unsolvable_mismatch"


# ------------------------------------------------------------ the world side

def _evidence_levels() -> Tuple[Level, ...]:
    """The five levels the A0 loop mines from.

    `mismatch` is deliberately not among them: it differs from `match` only in
    where the target sits, and the target does not enter `sokoban2.step`, so its
    transitions are `match`'s transitions and a stream from it would be a
    duplicate dressed as evidence.
    """
    return levels.EVIDENCE_LEVELS


def _variant_level(level: Level, rules: Rules) -> Level:
    return replace(level, rules=rules)


def _cells(level: Level) -> List[Tuple[int, int]]:
    return [(r, c) for r in range(level.height) for c in range(level.width)
            if (r, c) not in level.walls]


def _configurations(level: Level) -> List[State]:
    """Every legal (figure, box) placement on a level, in a fixed order.

    Reachability is not consulted on purpose.  A rule of the manual is a claim
    about the domain, so whether it is false is a question about the whole
    configuration space; whether anyone would ever *notice* is the separate
    question the detect items ask, and keeping them separate is what lets one
    variant be wrong everywhere and detectable nowhere on the base level.
    """
    cells = _cells(level)
    return [State(player=p, box=b) for p in cells for b in cells if p != b]


def _classify(level: Level, state: State, action: str) -> str:
    """Which of the manual's five rules governs this transition *in this world*.

    A pure function of the world's own rule data -- it reads `level.rules`, not
    the manual -- so it can be applied to the base world and to a variant and
    the two answers compared.  That comparison is how "which rules did the
    change falsify" is computed without anyone writing down a mapping.
    """
    rules = level.rules
    dr, dc = DELTA[action]
    target = (state.player[0] + dr, state.player[1] + dc)
    if not sokoban2.in_bounds(level, target):
        return "blocked_wall"
    if sokoban2.is_wall(level, target) and rules.walls_block_player:
        return "blocked_wall"
    if target != state.box:
        return "walk"
    distance = rules.push_distance
    landing = (state.box[0] + dr * distance, state.box[1] + dc * distance)
    crossed = [(state.box[0] + dr * k, state.box[1] + dc * k)
               for k in range(1, distance)]

    def obstructed(cell: Tuple[int, int]) -> bool:
        return (not sokoban2.in_bounds(level, cell)) or sokoban2.is_wall(level, cell)

    if rules.require_crossing_free and any(obstructed(c) for c in crossed):
        return "blocked_box_crossing"
    if obstructed(landing):
        return "blocked_box_landing"
    return "push2"


def _transition_signature(rules: Rules) -> Tuple[Any, ...]:
    """The variant's whole transition function, over every registered level."""
    out: List[Any] = []
    for base in (levels.MATCH, levels.MISMATCH) + levels.CROSSING_LEVELS:
        level = _variant_level(base, rules)
        for state in _configurations(base):
            for action in DIRECTIONS:
                nxt, _event = sokoban2.step(level, state, action)
                out.append((nxt.player, nxt.box))
    return tuple(out)


def _falsified_rules(rules: Rules) -> List[str]:
    """Manual rules the change falsifies, computed from disagreements.

    At every configuration where the base and the variant disagree, two rules
    are implicated: the one the old manual applies there, and the one that
    governs the transition now.  Both go in.  Taking only the first would miss
    exactly the interesting case -- weakening a guard makes a *blocked* rule fire
    where a *push* rule should, and the push rule is the one the theorem depends
    on.  `adapt.py` reaches the same answer by hand-labelling each variant with a
    `changed_rule`; this derives it.
    """
    hit = set()
    for base in (levels.MATCH, levels.MISMATCH) + levels.CROSSING_LEVELS:
        old = _variant_level(base, BASE_RULES)
        new = _variant_level(base, rules)
        for state in _configurations(base):
            for action in DIRECTIONS:
                a, _ = sokoban2.step(old, state, action)
                b, _ = sokoban2.step(new, state, action)
                if (a.player, a.box) != (b.player, b.box):
                    hit.add(_classify(old, state, action))
                    hit.add(_classify(new, state, action))
    return sorted(hit)


def _box_moving_rules() -> List[str]:
    """Rules that move the box in the base world.  The invariants' dependency."""
    hit = set()
    for base in (levels.MATCH,) + levels.CROSSING_LEVELS:
        level = _variant_level(base, BASE_RULES)
        for state in _configurations(base):
            for action in DIRECTIONS:
                nxt, _ = sokoban2.step(level, state, action)
                if nxt.box != state.box:
                    hit.add(_classify(level, state, action))
    return sorted(hit)


def _theorem_dependencies(dsl_text: str) -> Dict[str, List[str]]:
    """The `[depends: ...]` edges of the manual, read out of the manual.

    Uses `adapt.py::dependent_theorems` in reverse: ask it, for each rule name,
    which theorems name it.  Reusing that function rather than re-parsing keeps
    the exam honest about which edges exist -- including its own hard-won fix for
    the bracket that holds several `key: value` pairs.
    """
    from pipeline import adapt          # imported here: see the module docstring
    out: Dict[str, List[str]] = {}
    for rule in MANUAL_RULES:
        for theorem in adapt.dependent_theorems(dsl_text, rule):
            out.setdefault(theorem, []).append(rule)
    return {k: sorted(set(v)) for k, v in out.items()}


def _invariant_holds(rules: Rules, projection: str) -> bool:
    """Is the parity invariant still closed under every transition?

    Checked over the whole configuration space rather than over a trajectory:
    an invariant that survives the walk we happened to take is not an invariant,
    it is a coincidence with a good alibi.
    """
    for base in (levels.MATCH, levels.MISMATCH) + levels.CROSSING_LEVELS:
        level = _variant_level(base, rules)
        for state in _configurations(base):
            for action in DIRECTIONS:
                nxt, _ = sokoban2.step(level, state, action)
                before, after = state.box, nxt.box
                if projection == "row":
                    ok = before[0] % 2 == after[0] % 2
                elif projection == "col":
                    ok = before[1] % 2 == after[1] % 2
                else:
                    ok = (before[0] + before[1]) % 2 == (after[0] + after[1]) % 2
                if not ok:
                    return False
    return True


# ------------------------------------------------------------- the old theory

def _old_theory_step(level: Level, state: State, action: str) -> State:
    """What the manual predicts here.

    The manual's five guards spell out the base transition function, so the base
    transition function is what it predicts.  See the module docstring for why
    this is not read off the compiled form, and `test_adaptation.py` for the
    check that closes the gap when the compiler can be run.
    """
    nxt, _event = sokoban2.step(_variant_level(level, BASE_RULES), state, action)
    return nxt


def _stream(level: Level) -> List[Dict[str, Any]]:
    """The deterministic exploration of a variant level, as episodes.

    Same walk `adapt.py::detection_latency` takes: `plan_episodes` in
    breadth-first order, each episode resetting to the initial state.  The index
    an examinee is asked for counts actions across the whole stream, 1-based, so
    it is the position in the concatenation of these episodes.
    """
    episodes = []
    for episode in explore.plan_episodes(level, per_class=PER_CLASS):
        state = sokoban2.initial_state(level)
        observations = []
        for action in episode.actions:
            state, _event = sokoban2.step(level, state, action)
            observations.append([action, list(state.player), list(state.box)])
        episodes.append({"start": [list(level.player), list(level.box)],
                         "obs": observations})
    return episodes


def _first_divergence(level: Level, episodes: Sequence[Dict[str, Any]]
                      ) -> Optional[int]:
    """1-based index of the first action on which the old theory is wrong."""
    seen = 0
    for episode in episodes:
        state = sokoban2.initial_state(level)
        predicted = state
        for action, _player, _box in [(o[0], o[1], o[2]) for o in episode["obs"]]:
            actual, _ = sokoban2.step(level, state, action)
            predicted = _old_theory_step(level, predicted, action)
            seen += 1
            if (predicted.player, predicted.box) != (actual.player, actual.box):
                return seen
            state = actual
    return None


def _truncate(episodes: Sequence[Dict[str, Any]], cap: int
              ) -> Tuple[List[Dict[str, Any]], int, bool]:
    """Keep at most `cap` observations, whole ones only.  Returns (eps, n, done)."""
    kept: List[Dict[str, Any]] = []
    budget = cap
    total = sum(len(e["obs"]) for e in episodes)
    for episode in episodes:
        if budget <= 0:
            break
        take = episode["obs"][:budget]
        budget -= len(take)
        kept.append({"start": episode["start"], "obs": take})
    return kept, min(total, cap), total <= cap


# ------------------------------------------------------------------- repair

def _heldout_level(rules: Rules) -> Level:
    return Level(name="heldout", height=levels.HEIGHT, width=levels.WIDTH,
                 walls=HELDOUT_WALLS, player=(0, 0), box=(3, 3),
                 target=(3, 1), rules=rules)


def _mine(rules: Rules, level_names: Sequence[str]) -> Tuple[int, List[Any]]:
    """Run the stated evidence protocol and mine.  Returns (actions, rules)."""
    by_name = {level.name: level for level in _evidence_levels()}
    transitions: List[Any] = []
    actions = 0
    for name in level_names:
        level = _variant_level(by_name[name], rules)
        evidence = explore.evidence_set(level, per_class=PER_CLASS)
        actions += int(evidence["action_budget_spent"])
        transitions.extend(stages.transitions_from_episodes(evidence["episodes"]))
    return actions, stages.mine(transitions)


def _heldout_exactness(rules: Rules, mined: Sequence[Any]) -> Tuple[int, int]:
    """(mispredictions, checks) on a board the evidence never visited."""
    level = _heldout_level(rules)
    walls = tuple(sorted(HELDOUT_WALLS))
    bad = checks = 0
    for state in _configurations(level):
        percept = stages.Percept(player=state.player, box=state.box, walls=walls,
                                 height=level.height, width=level.width)
        for action in DIRECTIONS:
            nxt, _ = sokoban2.step(level, state, action)
            truth = ((nxt.player[0] - state.player[0],
                      nxt.player[1] - state.player[1]),
                     (nxt.box[0] - state.box[0], nxt.box[1] - state.box[1]))
            checks += 1
            if stages.predict(mined, percept, action) != truth:
                bad += 1
    return bad, checks


# ------------------------------------------------------------- the variants

@dataclass(frozen=True)
class _Variant:
    vid: str                       # opaque, the only name the sheet sees
    tag: str                       # transparent, truth file only
    rules: Rules
    changed: Dict[str, Any]
    reason: str
    labels: List[str]              # minimal change labels (describe truth)
    minimal_tag: str
    falsified: List[str]
    reexamine: List[str]
    now_false: List[str]
    verdict: str
    streams: Dict[str, List[Dict[str, Any]]]
    stream_meta: Dict[str, Dict[str, Any]]
    divergence: Dict[str, Optional[int]]


_LABEL_OF: Dict[Tuple[str, Any], str] = {
    ("push_distance", 1): "chg-box-travel-1",
    ("push_distance", 3): "chg-box-travel-3",
    ("require_crossing_free", False): "chg-box-crosses-blocked",
    ("walls_block_player", False): "chg-actor-enters-blocked",
}


def _assignments() -> List[Tuple[Dict[str, Any], str]]:
    """The variant family, enumerated.  Singles first, then compositions."""
    out: List[Tuple[Dict[str, Any], str]] = []
    for field in _FIELDS:
        for value in _VARIANT_GRID[field]:
            out.append(({field: value},
                        "one field of Rules, taken from the grid"))
    out.extend(_COMPOSITIONS)
    seen = set()
    for changed, _reason in out:
        key = tuple(sorted(changed.items()))
        if key in seen:
            raise ExamError("the variant grid produced %r twice" % (changed,))
        seen.add(key)
    return out


def _rules_from(changed: Dict[str, Any]) -> Rules:
    return replace(BASE_RULES, **changed)


def _minimal_assignment(changed: Dict[str, Any],
                        signatures: Dict[Tuple[Any, ...], List[Dict[str, Any]]]
                        ) -> Dict[str, Any]:
    """The fewest field changes that produce this exact transition function.

    A variant can flip two fields and be indistinguishable from one that flips
    one, and an examinee watching frames has no way to tell them apart -- so the
    truth for "what changed" has to be the minimal explanation or the exam is
    marking an unanswerable question.  Computed, not asserted: full transition
    tables over every registered level are compared.
    """
    group = signatures[_transition_signature(_rules_from(changed))]
    fewest = min(len(a) for a in group)
    candidates = [a for a in group if len(a) == fewest]
    if len(candidates) != 1:
        raise ExamError(
            "%r has %d minimal explanations (%r); the describe item would have "
            "no single right answer" % (changed, len(candidates), candidates))
    return candidates[0]


def _labels_for(changed: Dict[str, Any]) -> List[str]:
    labels = []
    for field in _FIELDS:
        if field in changed:
            labels.append(_LABEL_OF[(field, changed[field])])
    return sorted(labels)


def _tag_for(changed: Dict[str, Any]) -> str:
    return _rules_from(changed).label()


def _variants() -> List[_Variant]:
    assignments = _assignments()

    # Every point in the full product, grouped by transition function.  The
    # product is 12 cells; grouping it is what makes "observationally identical"
    # a computed fact rather than a claim.
    signatures: Dict[Tuple[Any, ...], List[Dict[str, Any]]] = {}
    for distance in (1, 2, 3):
        for crossing in (True, False):
            for blocking in (True, False):
                changed = {}
                if distance != BASE_RULES.push_distance:
                    changed["push_distance"] = distance
                if crossing != BASE_RULES.require_crossing_free:
                    changed["require_crossing_free"] = crossing
                if blocking != BASE_RULES.walls_block_player:
                    changed["walls_block_player"] = blocking
                rules = Rules(push_distance=distance,
                              require_crossing_free=crossing,
                              walls_block_player=blocking)
                signatures.setdefault(_transition_signature(rules), []).append(changed)

    dsl_text = open(os.path.join(A0_ROOT, "theory", "theory.dsl"),
                    encoding="utf-8").read()
    theorem_edges = _theorem_dependencies(dsl_text)
    invariant_edges = _box_moving_rules()

    ordered = sorted(assignments, key=lambda a: sha256_text(PAPER_ID + "|" + _tag_for(a[0])))

    built: List[_Variant] = []
    for position, (changed, reason) in enumerate(ordered, start=1):
        rules = _rules_from(changed)
        minimal = _minimal_assignment(changed, signatures)
        falsified = _falsified_rules(rules)

        reexamine = []
        for claim in CLAIMS:
            edges = (theorem_edges.get(claim) if claim == _THEOREM_CLAIM
                     else invariant_edges)
            if edges is None:
                raise ExamError("claim %r has no dependency edge; a claim whose "
                                "dependencies are unknown cannot be re-examined"
                                % claim)
            if set(edges) & set(falsified):
                reexamine.append(claim)

        now_false = []
        for claim, projection in (("box_row_parity", "row"),
                                  ("box_col_parity", "col"),
                                  ("box_parity", "sum")):
            if not _invariant_holds(rules, projection):
                now_false.append(claim)
        mismatch = _variant_level(levels.MISMATCH, rules)
        winnable = sokoban2.solve_bfs(mismatch) is not None
        if winnable:
            now_false.append(_THEOREM_CLAIM)

        streams: Dict[str, List[Dict[str, Any]]] = {}
        meta: Dict[str, Dict[str, Any]] = {}
        divergence: Dict[str, Optional[int]] = {}
        for base in _evidence_levels():
            level = _variant_level(base, rules)
            full = _stream(level)
            index = _first_divergence(level, full)
            kept, n_actions, complete = _truncate(full, STREAM_CAP)
            if index is not None and index > n_actions:
                raise ExamError(
                    "the %s stream on %s is capped at %d actions but the old "
                    "theory is not caught out until action %d -- the cap would "
                    "hide the answer" % (_tag_for(changed), base.name,
                                         n_actions, index))
            if index is None and not complete:
                raise ExamError(
                    "the %s stream on %s says 'never' over a truncated stream; "
                    "that is not a finding, it is a missing tail"
                    % (_tag_for(changed), base.name))
            streams[base.name] = kept
            meta[base.name] = {"n_actions": n_actions, "complete": complete,
                               "cap": STREAM_CAP}
            divergence[base.name] = index

        built.append(_Variant(
            vid="v-a0-%02d" % position,
            tag=_tag_for(changed),
            rules=rules,
            changed=dict(sorted(changed.items())),
            reason=reason,
            labels=_labels_for(minimal),
            minimal_tag=_tag_for(minimal),
            falsified=falsified,
            reexamine=sorted(reexamine),
            now_false=sorted(now_false),
            verdict="solvable" if winnable else "unsolvable",
            streams=streams,
            stream_meta=meta,
            divergence=divergence,
        ))
    return built


# ------------------------------------------------------------------- items

def _level_block(level: Level) -> Dict[str, Any]:
    return {"name": level.name, "height": level.height, "width": level.width,
            "walls": [list(w) for w in sorted(level.walls)],
            "start_figure": list(level.player), "start_box": list(level.box),
            "target": list(level.target)}


#: Strings whose appearance in the sheet would hand an item over.  Declared for
#: every item, not only the ones where they are plausible: `exam.leakage` treats
#: an item that cannot say what would give its answer away as unchecked rather
#: than clean, and a probe list that varies by family invites the argument that
#: the family with fewer probes was the one nobody thought about.
_STANDING_PROBES: Tuple[str, ...] = tuple(sorted(
    set(_FIELDS)                          # the fields a variant flips
    | set(MANUAL_RULES)                   # the manual's rule names
    | set(CLAIMS)                         # the claim names
    | set(CHANGE_LABELS)                  # the change-label alphabet
    | {"solvable", "unsolvable"}          # the verdict alphabet
))


def _probes(variant: _Variant, extra: Sequence[str] = ()) -> List[str]:
    # The transparent name and the minimal explanation's name: the whole item is
    # in either of them.  The first-divergence indices are probed in the JSON
    # shape a leaked debug field would take -- the bare integer is not probed,
    # because two-digit numbers occur inside every sha256 on the sheet and a
    # probe that fires on a clean paper teaches the reader to ignore the tool.
    out = set(_STANDING_PROBES)
    out.add(variant.tag)
    out.add(variant.minimal_tag)
    out.update(str(e) for e in extra)
    return sorted(p for p in out if len(p) >= 3)


def _index_probes(variant: _Variant, level_name: Optional[str] = None) -> List[str]:
    names = [level_name] if level_name else list(variant.divergence)
    out = []
    for name in names:
        index = variant.divergence[name]
        if index is None:
            out.append('"detected":false')
            out.append("never_detected_here")
        else:
            out.append('"index":%d' % index)
            out.append("first_divergence=%d" % index)
    return out


def _detect_items(variant: _Variant) -> List[Item]:
    items = []
    for base in _evidence_levels():
        name = base.name
        level = _variant_level(base, variant.rules)
        items.append(Item(
            item_id="%s.detect.%s" % (variant.vid, name),
            rubric_id="adapt.detect.v1",
            points=1.0,
            paper={
                "kind": "detect",
                "world": WORLD_ID,
                "variant": variant.vid,
                "level": _level_block(level),
                "stream": variant.stream_meta[name],
                "episodes": variant.streams[name],
                "ask": ("Replay the manual named in `world.base_manual` against "
                        "this stream. At which observation is its prediction "
                        "first wrong? Answer {\"detected\": bool, \"index\": "
                        "int|null}; the index counts actions across the whole "
                        "stream, 1-based, episodes concatenated in the order "
                        "given. Answer {\"detected\": false} if the manual is "
                        "never wrong here."),
                "note": ("Each episode restarts from `start`; every entry of "
                         "`obs` is [action, figure cell, box cell] after that "
                         "action. The full frame is recoverable from the level "
                         "geometry and these two cells -- perception is not what "
                         "this paper measures."),
            },
            truth={"detected": variant.divergence[name] is not None,
                   "index": variant.divergence[name],
                   "level": name},
            leak_probes=_probes(variant, _index_probes(variant, name)),
            tags=("detect", "single_level", variant.vid),
        ))
    return items


def _cross_item(variant: _Variant) -> Item:
    evidence = ["%s.detect.%s" % (variant.vid, b.name) for b in _evidence_levels()]
    return Item(
        item_id="%s.detect.across" % variant.vid,
        rubric_id="adapt.detect_cross.v1",
        points=3.0,
        paper={
            "kind": "detect_across_levels",
            "world": WORLD_ID,
            "variant": variant.vid,
            "evidence_items": evidence,
            "ask": ("Give the first-divergence index for every level, as "
                    "{\"per_level\": {level: int|null}}. A null means the manual "
                    "is never caught out on that level, over the whole stream "
                    "given for it. Where you look decides whether you notice at "
                    "all; a level that never notices is an answer, not a gap."),
            "note": "The streams are the ones embedded in `evidence_items`.",
        },
        truth={"per_level": dict(sorted(variant.divergence.items()))},
        leak_probes=_probes(variant, _index_probes(variant)),
        tags=("detect", "across_levels", variant.vid),
    )


def _describe_item(variant: _Variant) -> Item:
    evidence = ["%s.detect.%s" % (variant.vid, b.name) for b in _evidence_levels()]
    return Item(
        item_id="%s.describe" % variant.vid,
        rubric_id="adapt.describe.v1",
        points=3.0,
        paper={
            "kind": "describe",
            "world": WORLD_ID,
            "variant": variant.vid,
            "evidence_items": evidence,
            "ask": ("What changed? Answer {\"labels\": [...]} using the keys of "
                    "CHANGE_LABELS in `exam/grading/rubrics_adaptation.py`. "
                    "Report the MINIMAL set consistent with every observation: a "
                    "change the evidence cannot distinguish from no change at "
                    "all must not be claimed, and naming it is marked wrong."),
            "note": "Set equality. There is no credit for a superset.",
        },
        truth={"labels": variant.labels},
        leak_probes=_probes(variant),
        tags=("describe", variant.vid),
    )


def _collateral_item(variant: _Variant) -> Item:
    evidence = ["%s.detect.%s" % (variant.vid, b.name) for b in _evidence_levels()]
    mismatch = _variant_level(levels.MISMATCH, variant.rules)
    return Item(
        item_id="%s.collateral" % variant.vid,
        rubric_id="adapt.collateral.v1",
        points=10.0,
        paper={
            "kind": "collateral",
            "world": WORLD_ID,
            "variant": variant.vid,
            "evidence_items": evidence,
            "level": _level_block(mismatch),
            "ask": ("Four answers in one object. `rules_falsified`: which rules "
                    "of the manual this change makes false, as a subset of "
                    "MANUAL_RULES. `claims_to_reexamine`: which entries of "
                    "CLAIMS the manual's dependency edges put back on the bench. "
                    "`claims_now_false`: which of them, after re-examination, "
                    "are actually false -- these two sets are not the same "
                    "question. `verdict`: the standing claim about the level "
                    "above, from VERDICTS. All three vocabularies are in "
                    "`exam/grading/rubrics_adaptation.py`."),
            "note": ("Sets are graded on equality. The verdict is graded and "
                     "reported separately from the reasons for it."),
        },
        truth={"rules_falsified": variant.falsified,
               "claims_to_reexamine": variant.reexamine,
               "claims_now_false": variant.now_false,
               "verdict": variant.verdict,
               "label": variant.verdict},
        leak_probes=_probes(variant, [variant.verdict]),
        tags=("collateral", variant.vid),
    )


def _repair_items(variant: _Variant) -> List[Item]:
    evidence = ["%s.detect.%s" % (variant.vid, b.name) for b in _evidence_levels()]
    all_levels = [b.name for b in _evidence_levels()]
    protocols = (
        ("narrow", ["match"],
         "the base level alone -- the budget an arm spends if it re-mines where "
         "it already stands"),
        ("wide", all_levels,
         "every evidence level -- the budget an arm spends if it travels to "
         "witness the rules it cannot witness at home"),
    )
    items = []
    for suffix, level_names, why in protocols:
        actions, mined = _mine(variant.rules, level_names)
        bad, checks = _heldout_exactness(variant.rules, mined)
        items.append(Item(
            item_id="%s.repair.%s" % (variant.vid, suffix),
            rubric_id="adapt.repair.v1",
            points=1.5,
            paper={
                "kind": "repair",
                "world": WORLD_ID,
                "variant": variant.vid,
                "evidence_items": evidence,
                "protocol": {
                    "levels": list(level_names),
                    "per_class": PER_CLASS,
                    "explorer": "a0-spike/pipeline/explore.py::evidence_set",
                    "miner": "a0-spike/pipeline/stages.py::mine",
                    "why": why,
                },
                "heldout": {
                    "height": levels.HEIGHT, "width": levels.WIDTH,
                    "walls": [list(w) for w in sorted(HELDOUT_WALLS)],
                    "check": ("every ordered pair of distinct clear cells "
                              "(figure, box), each of the four actions; the "
                              "re-mined theory must give the exact displacement "
                              "of both objects"),
                },
                "ask": ("Run that protocol on this variant. Answer "
                        "{\"budget_actions\": int, \"exact_on_heldout\": bool}: "
                        "how many actions it spends, and whether the theory it "
                        "yields is exact on the held-out board above."),
                "note": ("The held-out obstruction layout appears in no evidence "
                         "level. Replay exactness is not what is asked."),
            },
            truth={"budget_actions": actions,
                   "exact_on_heldout": bad == 0,
                   "heldout_mispredictions": bad,
                   "heldout_checks": checks},
            leak_probes=_probes(variant, ['"budget_actions":%d' % actions,
                                          "budget=%d" % actions]),
            tags=("repair", "budget_%s" % suffix, variant.vid),
        ))
    return items


INSTRUCTIONS = """\
Six worlds are variants of the A0 world: in each, exactly one rule has been
rewritten deterministically (Theoria.md Phase 1, layer 2 -- the world is not
rewritten, a rule is). You are not told which one. You are given observations.

For each variant, four things are asked:

  detect      replaying the old manual against these observations, at which
              action is it first wrong? Sometimes the answer is "never, not on
              this level" -- a rule can be wrong everywhere and visible nowhere,
              if the configuration where the old and the new rule disagree
              cannot be reached from where you are standing. Saying "never here,
              and here is the level where it does show" is a diagnosis. Naming a
              step number anyway is a guess, and scores nothing.

  describe    what changed, in the closed alphabet CHANGE_LABELS of
              exam/grading/rubrics_adaptation.py. Minimal sets only.

  collateral  what the change takes down: which rules of the manual are now
              false, which registered claims the dependency edges force back
              onto the bench, which of those turn out to be false once you look,
              and whether the standing verdict on the level named `mismatch`
              still holds. These are four separate answers because they are four
              separate questions, and the distance between the third and the
              fourth is the work.

  repair      run the stated re-mining protocol and report what it cost and
              whether the result is exact on a board it never saw.

The manual under examination is named in `world.base_manual`; read it there. The
answer vocabularies are in exam/grading/rubrics_adaptation.py, whose digest is on
this sheet. Nothing else about the variants is available, and nothing else is
needed.
"""


def _world_block() -> Dict[str, Any]:
    dsl_path = os.path.join(A0_ROOT, "theory", "theory.dsl")
    with open(dsl_path, encoding="utf-8") as handle:
        dsl_text = handle.read()
    return {
        **provenance(),
        "world_id": WORLD_ID,
        "base_world_id": BASE_WORLD_ID,
        "base_manual": {"path": "a0-spike/theory/theory.dsl",
                        "sha256": sha256_text(dsl_text)},
        "answer_alphabets": "exam/grading/rubrics_adaptation.py",
        "note": ("Every variant is a deterministic rewrite of one rule of a "
                 "self-built world. No game, no API, no network."),
    }


def _shuffled(items: Sequence[Item]) -> List[Item]:
    """Deterministic, and uncorrelated with anything an examinee could exploit.

    Built in variant order, the paper would run six blocks of ten items whose
    answers move together; `exam.leakage.positional_report` measures exactly that
    and would find it. Sorting on a digest of the item id costs nothing and is
    reproducible to the byte.
    """
    return sorted(items, key=lambda i: sha256_text(PAPER_ID + "|" + i.item_id))


def build() -> Paper:
    assert_synthetic_world(BASE_WORLD_ID)
    assert_synthetic_world(WORLD_ID)

    variants = _variants()
    if not any(any(v is None for v in variant.divergence.values())
               for variant in variants):
        raise ExamError(
            "no variant in this paper is undetectable on some level. The item "
            "that separates a diagnosis from a plausible answer would be "
            "missing, and the paper would not be this question type.")
    if levels.MATCH.name not in [name for variant in variants
                                 for name, index in variant.divergence.items()
                                 if index is None]:
        raise ExamError(
            "no variant is undetectable on the base level `match`; "
            "adapt.py::detection_across_levels documents that case and the "
            "paper is built to contain it.")
    if not any(variant.verdict != OLD_VERDICT for variant in variants):
        raise ExamError(
            "no variant flips the verdict on `mismatch`. The collateral items "
            "would all reward keeping the old answer, and `silently_wrong` "
            "could never fire.")

    items: List[Item] = []
    for variant in variants:
        items.extend(_detect_items(variant))
        items.append(_cross_item(variant))
        items.append(_describe_item(variant))
        items.append(_collateral_item(variant))
        items.extend(_repair_items(variant))

    notes = {
        "variant_table": [
            {"variant": v.vid, "transparent_name": v.tag,
             "changed_fields": v.changed, "grid_reason": v.reason,
             "minimal_explanation": v.minimal_tag,
             "change_labels": v.labels,
             "rules_falsified": v.falsified,
             "claims_to_reexamine": v.reexamine,
             "claims_now_false": v.now_false,
             "mismatch_verdict": v.verdict,
             "verdict_flipped": v.verdict != OLD_VERDICT,
             "first_divergence": dict(sorted(v.divergence.items()))}
            for v in variants
        ],
        "build": {"per_class": PER_CLASS, "stream_cap": STREAM_CAP,
                  "heldout_walls": [list(w) for w in sorted(HELDOUT_WALLS)],
                  "old_theory_predictor": (
                      "sokoban2.step under base Rules; see the module docstring "
                      "for why the compiled form of theory.dsl is not used and "
                      "how the substitution is checked")},
    }

    return Paper(paper_id=PAPER_ID, question_type=QUESTION_TYPE,
                 instructions=INSTRUCTIONS, items=items,
                 world=_world_block(), notes=notes)


# ------------------------------------------------------- calibration arms

def reference_answers(paper: Paper, key_doc: Dict[str, Any], mode: str
                      ) -> Dict[str, Any]:
    """The four fake examinees of `exam.papers.CALIBRATION_MODES`.

    `memoriser` is the one to read closely. It answers as if the world had not
    changed at all -- which is what an arm that replays its history perfectly
    does when the history is all it has. It never sees a divergence, it names no
    change, it takes nothing down, and it keeps the old verdict. On this paper
    that costs it very little of the total, and it is silently wrong on both
    flipped variants; `axes()` reports the flag, not the total, for that reason.

    `bluffer` is its mirror: it always claims an immediate detection and always
    claims everything is invalidated. High recall, no precision. It must not
    score well, and in particular the collateral rubric must not pay it for
    naming the whole registry.
    """
    if mode not in ("oracle", "null", "memoriser", "bluffer"):
        raise ExamError("unknown calibration mode %r" % mode)
    if mode == "null":
        return {}

    truth_of = {e["item_id"]: e["truth"] for e in key_doc["items"]}
    kind_of = {i.item_id: i.paper.get("kind") for i in paper.items}
    level_names = [b.name for b in _evidence_levels()]

    answers: Dict[str, Any] = {}
    for item_id, truth in sorted(truth_of.items()):
        kind = kind_of.get(item_id)
        if mode == "oracle":
            if kind == "detect":
                answers[item_id] = {"detected": truth["detected"],
                                    "index": truth["index"]}
            elif kind == "detect_across_levels":
                answers[item_id] = {"per_level": dict(truth["per_level"])}
            elif kind == "describe":
                answers[item_id] = {"labels": list(truth["labels"])}
            elif kind == "collateral":
                answers[item_id] = {
                    "rules_falsified": list(truth["rules_falsified"]),
                    "claims_to_reexamine": list(truth["claims_to_reexamine"]),
                    "claims_now_false": list(truth["claims_now_false"]),
                    "verdict": truth["verdict"]}
            elif kind == "repair":
                answers[item_id] = {"budget_actions": truth["budget_actions"],
                                    "exact_on_heldout": truth["exact_on_heldout"]}
        elif mode == "memoriser":
            if kind == "detect":
                answers[item_id] = {"detected": False, "index": None}
            elif kind == "detect_across_levels":
                answers[item_id] = {"per_level": {n: None for n in level_names}}
            elif kind == "describe":
                answers[item_id] = {"labels": []}
            elif kind == "collateral":
                answers[item_id] = {"rules_falsified": [],
                                    "claims_to_reexamine": [],
                                    "claims_now_false": [],
                                    "verdict": OLD_VERDICT}
            elif kind == "repair":
                answers[item_id] = {"budget_actions": 0,
                                    "exact_on_heldout": True}
        else:   # bluffer
            if kind == "detect":
                answers[item_id] = {"detected": True, "index": 1}
            elif kind == "detect_across_levels":
                answers[item_id] = {"per_level": {n: 1 for n in level_names}}
            elif kind == "describe":
                answers[item_id] = {"labels": sorted(CHANGE_LABELS)}
            elif kind == "collateral":
                answers[item_id] = {"rules_falsified": list(MANUAL_RULES),
                                    "claims_to_reexamine": list(CLAIMS),
                                    "claims_now_false": list(CLAIMS),
                                    "verdict": "solvable"}
            elif kind == "repair":
                answers[item_id] = {"budget_actions": 1,
                                    "exact_on_heldout": True}
    return answers


# ------------------------------------------------------------------- axes

def axes(report: Any, key_doc: Dict[str, Any], submission: Any) -> Dict[str, Any]:
    """Question-type numbers, with the one that matters kept out of the average.

    `silently_wrong` is a count, at the top level, never a percentage. It is the
    number of variants on which the examinee kept the old verdict where the
    verdict had flipped -- the failure `[depends: push2]` exists to prevent. A
    report whose fraction is 0.55 and whose `silently_wrong` is 2 has not
    half-passed; it has confidently declared two winnable levels impossible, and
    the fraction is the number that would let that pass unmentioned.

    Sensitivity and specificity on the verdict are reported together, via
    `exam.grading.mark.confusion`, because Theoria.md 1.11 insists they are a
    pair. It is fed a report restricted to the collateral items: `confusion` is
    paper-wide by design and this paper has four families, only one of which is
    a two-class question, so handing it the whole report would count every detect
    item as an abstention on the negative class and make both rates meaningless.
    """
    from ..grading.mark import confusion            # local: see mark.py's imports
    from ..model import Report

    truth_of = {e["item_id"]: e["truth"] for e in key_doc["items"]}
    tags_of = {e["item_id"]: tuple(e.get("tags", ())) for e in key_doc["items"]}

    def family(item_id: str) -> str:
        tags = tags_of.get(item_id, ())
        for name in ("detect", "describe", "collateral", "repair"):
            if name in tags:
                return name
        return "other"

    silently_wrong: List[str] = []
    flipped_items: List[str] = []
    collateral_scores = []
    parts_ok = {"rules": 0, "reexamine": 0, "false": 0, "verdict": 0}
    detect = {"n": 0, "exact": 0, "partial": 0, "missed": 0, "false_alarm": 0,
              "undetectable_items": 0, "undetectable_correct": 0}
    describe_exact = describe_n = 0
    repair_exact = repair_n = repair_budget_exact = 0

    for score in report.scores:
        truth = truth_of.get(score.item_id, {})
        group = family(score.item_id)
        if group == "collateral":
            collateral_scores.append(score)
            if truth.get("verdict") != OLD_VERDICT:
                flipped_items.append(score.item_id)
            if score.detail.get("silently_wrong"):
                silently_wrong.append(score.item_id)
            for key, ok in (score.detail.get("parts") or {}).items():
                if ok:
                    parts_ok[key] = parts_ok.get(key, 0) + 1
        elif group == "detect" and "single_level" in tags_of.get(score.item_id, ()):
            detect["n"] += 1
            fraction = float(score.detail.get("fraction", 0.0))
            if truth.get("index") is None:
                detect["undetectable_items"] += 1
                if fraction >= 1.0:
                    detect["undetectable_correct"] += 1
            if fraction >= 1.0:
                detect["exact"] += 1
            elif fraction > 0.0:
                detect["partial"] += 1
            if score.detail.get("false_alarm"):
                detect["false_alarm"] += 1
            if score.detail.get("missed"):
                detect["missed"] += 1
        elif group == "describe":
            describe_n += 1
            if score.awarded >= score.possible - 1e-9:
                describe_exact += 1
        elif group == "repair":
            repair_n += 1
            if score.detail.get("exactness_correct"):
                repair_exact += 1
            if score.detail.get("budget_fraction", 0.0) >= 1.0:
                repair_budget_exact += 1

    sub_report = Report(paper_id=report.paper_id, examinee_id=report.examinee_id,
                        question_type=report.question_type,
                        rubric_digest=report.rubric_digest,
                        scores=collateral_scores)
    sub_key = {"paper_id": key_doc["paper_id"],
               "items": [e for e in key_doc["items"]
                         if family(e["item_id"]) == "collateral"]}

    return {
        "silently_wrong": len(silently_wrong),
        "silently_wrong_items": sorted(silently_wrong),
        "verdict_flipped_items": sorted(flipped_items),
        "silently_wrong_note": (
            "variants whose verdict on `mismatch` flipped and on which the "
            "examinee kept the old one. Counted, never averaged: this is the "
            "failure the dependency annotation exists to prevent, and a "
            "percentage hides it."),
        "detect": detect,
        "describe": {"n": describe_n, "exact": describe_exact},
        "collateral_parts_correct": dict(sorted(parts_ok.items())),
        "repair": {"n": repair_n, "exactness_correct": repair_exact,
                   "budget_exact": repair_budget_exact},
        "mismatch_verdict": confusion(sub_report, sub_key, positive="solvable"),
    }
