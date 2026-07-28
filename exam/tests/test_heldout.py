"""Acceptance tests for 题型 1 -- held-out prediction.

The tests that matter here are the ones that refuse to take the builder's word.
`exam/papers/heldout.py` says the held-out items are transitions its evidence set
does not contain; this file rebuilds that evidence set from `pipeline.explore`
and `world.sokoban2` directly, re-serialises the keys with plain `json` rather
than the builder's helper, and checks the disjointness itself.  Likewise the
answer key is not trusted: every truth frame is re-derived by reconstructing the
level from the item's own geometry and stepping the world.  A paper that asserts
its own correctness has asserted nothing.

`exam.grading.registry` imports all four rubric modules and the other three are
being written concurrently, so it may not import yet.  The rubrics under test are
therefore imported directly and applied by a local marker that mirrors
`exam.grading.mark.mark`; one test opts into the registry if it happens to be
complete and skips if it is not.  Nothing here stubs another track's file.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam import leakage                                    # noqa: E402
from exam.guard import no_network                           # noqa: E402
from exam.grading import rubrics_heldout                    # noqa: E402
from exam.model import (Item, Report, Submission,           # noqa: E402
                        canonical, unanswered)
from exam.papers import heldout                             # noqa: E402

A0_DIR = os.path.join(REPO, "a0-spike")
if A0_DIR not in sys.path:
    sys.path.append(A0_DIR)

from pipeline import explore                                # noqa: E402
from world import levels, sokoban2                          # noqa: E402

DIGEST = "test-digest"
RUBRICS = {r.rubric_id: r for r in rubrics_heldout.RUBRICS}


# ------------------------------------------------------------------ fixtures

@pytest.fixture(scope="module")
def paper():
    # Built inside the tripwire: "zero API, zero network" is meant to be a
    # property the suite would fail to report, not a sentence in a README.
    with no_network():
        return heldout.build()


@pytest.fixture(scope="module")
def key_doc(paper):
    return paper.key(DIGEST)


@pytest.fixture(scope="module")
def sheet(paper):
    return paper.sheet(DIGEST)


def _items_from_key(key_doc):
    """Exactly what `exam.grading.mark` reconstructs: the paper side is gone."""
    return [Item(item_id=e["item_id"], rubric_id=e["rubric_id"],
                 points=float(e["points"]), paper={}, truth=e["truth"],
                 tags=tuple(e["tags"]))
            for e in key_doc["items"]]


def _mark(key_doc, answers, examinee_id="cal"):
    items = _items_from_key(key_doc)
    scores = []
    for item in items:
        if item.item_id not in answers:
            scores.append(unanswered(item))
            continue
        scores.append(RUBRICS[item.rubric_id].grade(
            answers[item.item_id], item.truth, item))
    return Report(paper_id=key_doc["paper_id"], examinee_id=examinee_id,
                  question_type=key_doc["question_type"], rubric_digest=DIGEST,
                  scores=scores)


def _run(paper, key_doc, mode):
    answers = heldout.reference_answers(paper, key_doc, mode)
    submission = Submission("cal-" + mode, paper.paper_id, answers)
    report = _mark(key_doc, answers, examinee_id=submission.examinee_id)
    return report, heldout.axes(report, key_doc, submission)


# --------------------------------------------------- an independent world model

def _independent_key(frame, action):
    """The transition key, re-derived rather than imported.

    Deliberately not `heldout.transition_key`: the disjointness claim is the
    builder's, and a test that checks it with the builder's own serialiser can
    only catch a builder that contradicts itself.
    """
    return json.dumps([[list(row) for row in frame], action],
                      sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _independent_evidence():
    """Rebuild E from `explore` and the world, with no help from the paper."""
    seen = {}
    for level in levels.EVIDENCE_LEVELS:
        evidence = explore.evidence_set(level, per_class=heldout.EVIDENCE_PER_CLASS)
        for run in evidence["episodes"]:
            state = sokoban2.initial_state(level)
            for action in run["actions"]:
                before = sokoban2.render(level, state)
                state, _ = sokoban2.step(level, state, action)
                seen.setdefault(_independent_key(before, action),
                                sokoban2.render(level, state))
    return seen


def _level_from(paper_side):
    """Rebuild a `Level` from what the sheet shows, and only from that."""
    geometry = paper_side["level"]
    walls = tuple(sorted(tuple(cell) for cell in geometry["walls"]))
    return sokoban2.Level(name="from-sheet", height=geometry["height"],
                          width=geometry["width"], walls=walls,
                          player=(0, 0), box=(0, 0), target=(0, 0))


def _state_from(frame):
    player = box = None
    for r, row in enumerate(frame):
        for c, value in enumerate(row):
            if value == sokoban2.PLAYER:
                player = (r, c)
            elif value == sokoban2.BOX:
                box = (r, c)
    return sokoban2.State(player=player, box=box)


# ------------------------------------------------------------------ the tests

def test_build_is_deterministic():
    """Two builds, byte-identical sheets.

    The module memoises its evidence index and its enumeration of the universe,
    so a naive second call would reuse both and prove nothing about the build.
    The caches are cleared between the two builds on purpose: what is under test
    is that the *enumeration* is reproducible, not that a dict lookup is.
    """
    with no_network():
        first = heldout.build().sheet(DIGEST)
        heldout._EVIDENCE = None       # noqa: SLF001 -- see docstring
        heldout._UNIVERSE = None       # noqa: SLF001
        second = heldout.build().sheet(DIGEST)
    assert canonical(first) == canonical(second)
    assert first["n_items"] == second["n_items"] > 0


def test_paper_shape(paper, sheet):
    assert paper.paper_id == heldout.PAPER_ID
    assert paper.question_type == "heldout"
    assert len(paper.items) == 2 * sum(heldout.QUOTA.values())
    assert sheet["total_points"] == float(len(paper.items))
    assert paper.world["world_id"] == "a0"
    # The cut the paper was built under travels with it.
    assert paper.world["piles_sha256"]
    assert "a0" in paper.world["synthetic_worlds"]


def test_sealed_and_unknown_worlds_are_refused():
    from exam.guard import SealedPileError, UnknownGameError, assert_synthetic_world
    assert assert_synthetic_world("a0") == "synthetic"
    with pytest.raises(UnknownGameError):
        assert_synthetic_world(None)
    with pytest.raises((SealedPileError, UnknownGameError)):
        assert_synthetic_world("not-a-registered-game")


def test_leakage_check_passes(paper, sheet):
    answer_of = {item.item_id: item.truth["event"] for item in paper.items}
    report = leakage.check_paper(paper, sheet, answer_of=answer_of)
    assert report["probe_hits"] == 0
    assert report["structural_hits"] == 0
    assert report["probes_declared"] >= 4 * len(paper.items)
    # Position must not betray the answer: a hash-ordered paper alternates, a
    # paper grouped by class does not.
    assert report["positional"]["clustered_by_answer"] is False
    assert report["positional"]["order_runs"] > len(paper.items) / 2


def test_every_item_declares_usable_probes(paper):
    for item in paper.items:
        assert item.leak_probes, item.item_id
        assert all(len(p) >= 3 for p in item.leak_probes), item.item_id
        # The key-qualified probes are declared unconditionally; only the bare
        # after-frame is ever withdrawn, and the count is published.
        assert ('"frame_after":' + canonical(item.truth["frame_after"])
                in item.leak_probes)


def test_sheet_carries_no_truth_field(sheet):
    text = canonical(sheet)
    for forbidden in ('"frame_after"', '"player_after"', '"box_after"',
                      '"event"', '"level_name"', '"split"'):
        assert forbidden not in text, forbidden


def test_truth_is_what_the_world_does(paper):
    """Re-derive every answer from the item's own geometry.

    Nothing here reads `levels.py`: the level is rebuilt from the height, width
    and walls the sheet shows, and the state is read off the frame. If the key
    and the world ever disagree, the exam is grading its own bug.
    """
    for item in paper.items:
        level = _level_from(item.paper)
        state = _state_from(item.paper["frame_before"])
        nxt, _ = sokoban2.step(level, state, item.paper["action"])
        assert sokoban2.render(level, nxt) == item.truth["frame_after"], item.item_id
        assert list(nxt.player) == item.truth["player_after"]
        assert list(nxt.box) == item.truth["box_after"]
        assert heldout.classify(level, state, item.paper["action"]) \
            == item.truth["event"]


def test_heldout_items_are_absent_from_the_evidence(paper):
    """The claim the whole item type rests on, checked against E itself."""
    seen = _independent_evidence()
    assert len(seen) > 100, "the evidence set collapsed; the split means nothing"
    heldout_items = [i for i in paper.items if i.truth["split"] == "heldout"]
    assert heldout_items
    for item in heldout_items:
        key = _independent_key(item.paper["frame_before"], item.paper["action"])
        assert key not in seen, (
            "%s is tagged heldout but its (frame, action) was in the evidence"
            % item.item_id)


def test_replay_items_are_present_in_the_evidence(paper):
    """The control has to be a real control: every replay item was witnessed."""
    seen = _independent_evidence()
    replay_items = [i for i in paper.items if i.truth["split"] == "replay"]
    assert replay_items
    for item in replay_items:
        key = _independent_key(item.paper["frame_before"], item.paper["action"])
        assert key in seen, item.item_id
        assert seen[key] == item.truth["frame_after"], item.item_id


def test_every_event_class_is_represented_and_matched(paper):
    counts = {}
    for item in paper.items:
        counts[(item.truth["split"], item.truth["event"])] = counts.get(
            (item.truth["split"], item.truth["event"]), 0) + 1
    for event in heldout.EVENT_CLASSES:
        for split in ("replay", "heldout"):
            assert counts.get((split, event)) == heldout.QUOTA[event], (split, event)
    # The rare class T-9 is about must be present on both sides, or the paper
    # cannot show the thing it exists to show.
    assert counts[("heldout", heldout.BLOCKED_CROSSING)] >= 4
    assert counts[("replay", heldout.BLOCKED_CROSSING)] >= 4
    # Matched quotas are what make the split tag safe to print on the sheet.
    assert paper.notes["stratification"]["matched_across_splits"] is True


def test_heldout_covers_more_than_one_geometry(paper):
    """A held-out set drawn from one level tests a problem, not a domain."""
    for split in ("replay", "heldout"):
        names = {i.truth["level_name"] for i in paper.items
                 if i.truth["split"] == split}
        assert len(names) >= 4, (split, names)
    crossing = {i.truth["level_name"] for i in paper.items
                if i.truth["split"] == "heldout"
                and i.truth["event"] == heldout.BLOCKED_CROSSING}
    # Including `match`, where a0-spike's T-9 says the case is unreachable and
    # therefore invisible to any amount of exploring that level.
    assert "match" in crossing


def test_oracle_scores_full_marks(paper, key_doc):
    report, axes = _run(paper, key_doc, "oracle")
    assert report.fraction == 1.0
    assert axes["by_split"]["replay"]["fraction"] == 1.0
    assert axes["by_split"]["heldout"]["fraction"] == 1.0
    assert axes["gap_replay_minus_heldout"] == 0.0


def test_null_scores_zero(paper, key_doc):
    report, axes = _run(paper, key_doc, "null")
    assert report.fraction == 0.0
    assert axes["unanswered"] == len(paper.items)
    # Nothing submitted is `unanswered`, not `wrong`. The marker keeps them
    # apart because "no deliverable" is a finding.
    assert all(s.verdict == "unanswered" for s in report.scores)


def test_memoriser_shows_a_large_replay_minus_heldout_gap(paper, key_doc):
    """The calibration this paper exists for.

    背题也能满分: a memoriser is perfect on what it has seen. As built it scores
    1.00 on replay and 0.15 on held-out -- the 0.15 is the held-out `move` items,
    which any theory at all gets right, and rigging it to zero would mean
    pretending most of a world is not boring. The thresholds below are set well
    inside the measured values so the test reports a real regression rather than
    tracking noise in the fourth decimal.
    """
    report, axes = _run(paper, key_doc, "memoriser")
    replay = axes["by_split"]["replay"]["fraction"]
    heldout_frac = axes["by_split"]["heldout"]["fraction"]
    gap = axes["gap_replay_minus_heldout"]

    assert replay == 1.0, "the memoriser must be perfect on what it was shown"
    assert heldout_frac <= 0.25
    assert gap >= 0.6
    # And the gap is what separates it from every other calibration examinee:
    # a bluffer has a gap of zero at a low score, an oracle a gap of zero at a
    # high one, so the gap alone is never the whole reading.
    assert report.fraction < 1.0


def test_memoriser_fails_the_rare_class_only_on_the_heldout_side(paper, key_doc):
    """T-9 in one assertion: replay says the theory is perfect, held-out does not."""
    _, axes = _run(paper, key_doc, "memoriser")
    rare = axes["rare_class_scores"]
    assert rare["replay/" + heldout.BLOCKED_CROSSING]["fraction"] == 1.0
    assert rare["heldout/" + heldout.BLOCKED_CROSSING]["fraction"] == 0.0


def test_bluffer_scores_the_published_ceiling(paper, key_doc):
    """A confident, uniform, mostly-wrong answer -- and the paper said in advance
    what it would be worth."""
    report, axes = _run(paper, key_doc, "bluffer")
    ceiling = paper.notes["unchanged_frame_share"]
    assert report.fraction == pytest.approx(ceiling)
    assert axes["unchanged_frame_share"] == pytest.approx(ceiling)
    assert report.fraction < 0.5
    assert 1.0 - report.fraction >= 0.5
    # A bluffer's gap is zero because the two splits have the same class mix.
    # That is the point of matching the quotas: the gap responds to memory only.
    assert axes["gap_replay_minus_heldout"] == pytest.approx(0.0)


def test_calibration_ordering_is_the_expected_one(paper, key_doc):
    fractions = {mode: _run(paper, key_doc, mode)[0].fraction
                 for mode in ("oracle", "null", "memoriser", "bluffer")}
    assert fractions["oracle"] > fractions["memoriser"] > fractions["bluffer"] \
        > fractions["null"]


def test_unknown_calibration_mode_is_refused(paper, key_doc):
    with pytest.raises(KeyError):
        heldout.reference_answers(paper, key_doc, "sandbagger")


# ------------------------------------------------------------------- the rubric

def _an_item(paper):
    return paper.items[0]


def test_rubric_is_all_or_nothing(paper):
    item = _an_item(paper)
    truth = item.truth
    right = [list(row) for row in truth["frame_after"]]
    score = RUBRICS[item.rubric_id].grade({"frame_after": right}, truth, item)
    assert score.verdict == "correct" and score.awarded == item.points

    nearly = [list(row) for row in right]
    # Flip one cell to a different legal code: 48 of 49 cells right.
    for r, row in enumerate(nearly):
        for c, value in enumerate(row):
            if value == sokoban2.EMPTY:
                nearly[r][c] = sokoban2.BOX
                break
        else:
            continue
        break
    score = RUBRICS[item.rubric_id].grade(nearly, truth, item)
    assert score.verdict == "wrong"
    assert score.awarded == 0.0, "one cell wrong is wrong; no partial credit"
    assert score.detail["cells_wrong"] == 1


def test_rubric_accepts_both_answer_shapes(paper):
    item = _an_item(paper)
    bare = [list(row) for row in item.truth["frame_after"]]
    wrapped = {"frame_after": bare}
    assert RUBRICS[item.rubric_id].grade(bare, item.truth, item).verdict == "correct"
    assert RUBRICS[item.rubric_id].grade(wrapped, item.truth, item).verdict == "correct"


def test_rubric_records_abstention_separately(paper):
    item = _an_item(paper)
    score = RUBRICS[item.rubric_id].grade({"abstain": True}, item.truth, item)
    assert score.verdict == "abstained"
    assert score.awarded == 0.0


def test_rubric_refuses_malformed_frames(paper):
    item = _an_item(paper)
    for bad in ([], [[]], "UP", {"frame_after": [[1, 2], [3]]},
                [[True, False]], [[0, 2, 5]], 7):
        score = RUBRICS[item.rubric_id].grade(bad, item.truth, item)
        assert score.verdict == "wrong", bad
        assert score.awarded == 0.0


def test_rubric_is_a_pure_function_of_its_three_arguments(paper):
    """Called twice with the same arguments, it returns the same score."""
    item = _an_item(paper)
    answer = {"frame_after": [list(row) for row in item.truth["frame_after"]]}
    first = RUBRICS[item.rubric_id].grade(answer, item.truth, item)
    second = RUBRICS[item.rubric_id].grade(answer, item.truth, item)
    assert first.to_json() == second.to_json()


def test_registry_registers_this_rubric_if_it_can_be_loaded():
    """Opt-in: the registry imports all four rubric modules and the other three
    are being written concurrently. Skipping is the correct outcome until they
    land; stubbing them would not be."""
    try:
        from exam.grading import registry
        rubrics = registry.all_rubrics()
    except Exception as exc:                      # noqa: BLE001
        pytest.skip("registry not loadable yet: %s" % exc)
    assert rubrics_heldout.RUBRIC_ID in rubrics
    assert registry.digest()
