"""The exam, set in the world factory's output.

The tests that matter most here are the two the port could plausibly get wrong
in a way no score would reveal:

  * **the read licence** -- `ground_truth.json` is scoring-only, and an exam is
    exactly the consumer that could quietly put it on a sheet. A leak here does
    not fail; it produces a *higher* score, which is indistinguishable from a
    better examinee.
  * **the matched quota** -- every item's `replay`/`heldout` tag is printed on
    the sheet, and that is only safe if the two splits have identical rule
    mixes. An unmatched quota turns the tag into a hint, and an examinee that
    reads the hint looks like one that learned the rules.

    cd . && python -m pytest exam/tests/test_worldgen_papers.py -q
"""

from __future__ import annotations

import json

import pytest

from exam.grading.mark import mark
from exam.grading.registry import digest
from exam.guard import (UnknownGameError, assert_synthetic_world,
                        generated_worlds, no_network)
from exam.model import ExamError, Submission, canonical
from exam.papers import heldout_worldgen as hw
from exam.papers import worldgen_port as port
from exam.tools import run_matrix

WORLDS = port.world_ids()
SAMPLE = ("t1-push-open", "t2-switch-push", "t3-full-house")


def test_the_factory_has_been_built():
    """Every other test here is vacuous if it has not."""
    assert len(WORLDS) == 20


# -- the read licence --------------------------------------------------------

def _scoring_only_values(world_id):
    """Numbers and strings that appear only in the scoring-only files."""
    truth = port.scoring_truth(world_id)
    values = set()
    for rule in truth.get("rules", []):
        values.add(rule.get("when", ""))
        values.add(rule.get("then", ""))
        values.add(rule.get("reversible", ""))
    solvability = truth.get("solvability", {})
    if solvability.get("optimal_plan"):
        values.add(" ".join(solvability["optimal_plan"]))
    for invariant in truth.get("invariants", []):
        values.add(invariant.get("statement", ""))
    return {v for v in values if isinstance(v, str) and len(v) > 12}


@pytest.mark.parametrize("world_id", SAMPLE)
def test_the_sheet_carries_no_scoring_only_text(world_id):
    """The split is the only thing standing between the catalogue and a rigged
    evaluation, and the rule table would answer items outright."""
    paper = hw.build_for(world_id)
    sheet = canonical(paper.sheet(digest()))
    for value in _scoring_only_values(world_id):
        assert value not in sheet, (world_id, value[:60])


@pytest.mark.parametrize("world_id", SAMPLE)
def test_the_sheet_names_no_rule_the_open_files_do_not_already_name(world_id):
    """Rule names are the answer vocabulary of the `by_rule` axis, so the sheet
    must not introduce them.

    "Introduce" is the operative word, and the first version of this test missed
    it: a *family* name from `spec.json` can equal a rule name -- `push` is both
    -- and `spec.json` is licensed open, so the examinee already has it. Removing
    it from the sheet would protect nothing while pretending to. What must not
    appear is a rule name the open files do not already give away."""
    paper = hw.build_for(world_id)
    sheet = canonical(paper.sheet(digest()))
    open_text = canonical(json.load(
        open(port.world_dir(world_id) + "/spec.json", encoding="utf-8")))
    for rule in {item.truth["rule"] for item in paper.items}:
        if '"%s"' % rule in open_text:
            continue                       # already the examinee's, by licence
        assert '"%s"' % rule not in sheet, (world_id, rule)


@pytest.mark.parametrize("world_id", SAMPLE)
def test_the_truth_side_does_carry_the_rule(world_id):
    """The negative control: a check that passes because nothing is there at
    all would pass the two above as well."""
    paper = hw.build_for(world_id)
    assert all(item.truth.get("rule") for item in paper.items)


# -- the matched quota -------------------------------------------------------

@pytest.mark.parametrize("world_id", WORLDS)
def test_every_world_has_matched_rule_mixes(world_id):
    paper = hw.build_for(world_id)
    replay, heldout = {}, {}
    for item in paper.items:
        bucket = replay if item.truth["split"] == "replay" else heldout
        bucket[item.truth["rule"]] = bucket.get(item.truth["rule"], 0) + 1
    assert replay == heldout, world_id


@pytest.mark.parametrize("world_id", WORLDS)
def test_the_tag_is_close_to_uninformative_and_the_residue_is_published(world_id):
    """Matched rule mixes make the splits equivalent *by rule*. They do not make
    them equivalent by outcome: a cascading mechanism can fire the same rule and
    settle back to the same frame in one split and not the other, so the share
    of items whose frame changes can differ slightly between the tags.

    The first version of this test asserted exact equality and `t2-gravity-push`
    failed it. Asserting equality would have meant either dropping that world or
    widening until it passed; instead the residue is measured, bounded, and put
    on the matrix where somebody can look at it."""
    paper = hw.build_for(world_id)
    bias = run_matrix.tag_bias(paper)
    assert bias <= 0.25, (world_id, bias)


def test_a_world_that_cannot_match_its_quota_is_refused(monkeypatch):
    """Refusing beats shrinking: a paper that silently drops its rare class is
    the failure this question type exists to catch."""
    monkeypatch.setattr(hw, "plan", lambda world_id, per_class=2: {
        "world_id": world_id, "per_class": per_class, "usable_rules": ["walk"],
        "blocked_rules": {"push": {"in_trace": 1, "held_out": 0}},
        "items": 2, "feasible": False})
    with pytest.raises(ExamError) as exc:
        hw.build_for("t1-push-open")
    assert "hint" in str(exc.value)


@pytest.mark.parametrize("world_id", SAMPLE)
def test_a_blocked_rule_says_why_it_is_blocked(world_id):
    shape = hw.plan(world_id, per_class=2)
    for rule, detail in shape["blocked_rules"].items():
        assert detail["why"], rule
        assert detail["in_trace"] < 2 or detail["held_out"] < 2


# -- determinism -------------------------------------------------------------

@pytest.mark.parametrize("world_id", SAMPLE)
def test_two_builds_are_byte_identical(world_id):
    first = canonical(hw.build_for(world_id).sheet(digest()))
    second = canonical(hw.build_for(world_id).sheet(digest()))
    assert first == second


@pytest.mark.parametrize("world_id", SAMPLE)
def test_the_world_is_rebuilt_from_the_published_spec(world_id):
    """Not from the in-process catalogue: a paper must depend only on what a
    reader of the artefacts has."""
    world = port.open_world(world_id)
    assert world.spec.world_id == world_id
    assert world.render(world.initial()) == port.trace(world_id)[0][0]


# -- the guard ---------------------------------------------------------------

def test_a_generated_world_is_admitted_by_the_roster_not_by_a_list():
    assert assert_synthetic_world("t1-push-open") == "generated"
    assert set(generated_worlds()) == set(WORLDS)


def test_an_id_that_is_not_in_the_roster_is_still_refused():
    with pytest.raises(UnknownGameError):
        assert_synthetic_world("t9-not-a-world")


def test_the_roster_is_kept_off_the_sheet():
    """Publishing it leaked answer vocabulary on the first run: the ids
    `t2-unsolvable-nodoor` and `t1-walk-maze` put `unsolvable` and `walk` --
    both live answers on the adaptation paper -- in front of the examinee. The
    exam's own leak probes caught it."""
    from exam.guard import provenance
    blob = canonical(provenance())
    assert "t2-unsolvable-nodoor" not in blob
    assert isinstance(provenance()["generated_worlds_available"], int)


# -- the marker, before it marks anything ------------------------------------

@pytest.mark.parametrize("world_id", WORLDS)
def test_the_marker_is_calibrated_on_every_world(world_id):
    """Exact, not banded. Two of the four expectations are computed from the
    paper, which survives twenty different item mixes where a pre-registered
    band would not."""
    paper = hw.build_for(world_id)
    result = run_matrix.calibrate(world_id, paper, paper.key(digest()))
    assert result["calibrated"], result["failures"]


@pytest.mark.parametrize("world_id", SAMPLE)
def test_the_oracle_scores_exactly_one_and_the_null_exactly_zero(world_id):
    paper = hw.build_for(world_id)
    key_doc = paper.key(digest())
    for mode, want in (("oracle", 1.0), ("null", 0.0)):
        answers = hw.reference_answers(paper, key_doc, mode)
        report = mark(key_doc, Submission("fake-%s" % mode, paper.paper_id,
                                          answers,
                                          () if mode == "null" else ("answers",)),
                      axes_fn=hw.axes)
        assert abs(report.fraction - want) < 1e-9, (world_id, mode)


@pytest.mark.parametrize("world_id", SAMPLE)
def test_the_memoriser_shows_the_gap_the_question_type_exists_to_measure(world_id):
    """重放是对过去的预测，背题也能满分. If the gap were near zero the paper
    would not be holding anything out."""
    paper = hw.build_for(world_id)
    key_doc = paper.key(digest())
    answers = hw.reference_answers(paper, key_doc, "memoriser")
    report = mark(key_doc, Submission("fake-memoriser", paper.paper_id, answers,
                                      ("answers",)), axes_fn=hw.axes)
    assert report.axes["replay"] == 1.0
    assert report.axes["gap_replay_minus_heldout"] > 0.2, world_id


@pytest.mark.parametrize("world_id", SAMPLE)
def test_the_palette_reaches_the_marker(world_id):
    """A0's rubric hardcodes {0,2,4,8}. Without the palette on the truth side
    every generated frame is rejected as malformed -- which reads on a report as
    an examinee that cannot format an answer, not as a misaimed rubric."""
    from exam.grading.rubrics_heldout import grade_frame_exact
    paper = hw.build_for(world_id)
    item = paper.items[0]
    score = grade_frame_exact(item.truth["frame_after"], item.truth, item)
    assert score.verdict == "correct", (world_id, score.detail)


def test_without_the_palette_the_same_frame_is_rejected():
    """The negative control for the test above."""
    from exam.grading.rubrics_heldout import grade_frame_exact
    paper = hw.build_for("t1-push-open")
    item = paper.items[0]
    stripped = {k: v for k, v in item.truth.items() if k != "legal_cells"}
    score = grade_frame_exact(item.truth["frame_after"], stripped, item)
    assert score.verdict == "wrong"
    assert "well-formed" in score.detail["why"]


# -- the matrix --------------------------------------------------------------

def test_the_matrix_covers_every_world_and_says_so():
    with no_network():
        result = run_matrix.run(per_class=2)
    assert result["worlds_offered"] == 20
    assert result["worlds_in_matrix"] == 20
    assert result["refused"] == []
    assert result["totals"]["items_total"] > 200


def test_the_matrix_reports_that_scores_are_not_comparable_across_worlds():
    """The finding, kept as a test so a later change cannot quietly drop it: the
    stasis floor ranges widely across the catalogue, so a raw fraction says as
    much about the world as about the examinee."""
    with no_network():
        result = run_matrix.run(per_class=2)
    low, high = result["totals"]["bluffer_floor_range"]
    assert high - low > 0.2
    assert "NOT comparable" in result["totals"]["comparability_note"]
