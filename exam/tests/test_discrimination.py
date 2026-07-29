"""The per-item discrimination profiler.

The tests that matter here are not "does it run". They are the three ways this
instrument could produce a plausible number that is wrong: it could disagree with
the marker it is built on, it could call an item informative when the ground truth
itself fails, or it could quietly become a relabelling of a field the paper already
prints and be read as new evidence anyway. The last one is a real property of the
current design and is asserted rather than hidden -- see
`test_the_class_is_a_function_of_split_and_frame_change`.
"""

from __future__ import annotations

import pytest

from exam.grading.registry import digest
from exam.papers import heldout_worldgen as hw
from exam.papers import worldgen_port as port
from exam.tools import discrimination as disc

SAMPLE = ("t1-walk-maze", "t2-gravity-push", "t3-cycler-portal-lock")


@pytest.mark.parametrize("world_id", SAMPLE)
def test_every_item_lands_in_a_declared_class(world_id):
    profile = disc.profile_world(world_id)
    assert profile["feasible"]
    for item in profile["items"]:
        assert item["class"] in disc.CLASSES, item


@pytest.mark.parametrize("world_id", SAMPLE)
def test_free_items_do_not_change_the_frame_and_theory_items_do(world_id):
    """The taxonomy's load-bearing promise, checked against the frames rather
    than against the verdicts that produced the labels."""
    profile = disc.profile_world(world_id)
    for item in profile["items"]:
        if item["class"] == "free":
            assert not item["frame_changes"], item["item_id"]
        if item["class"] in ("theory", "memorised"):
            assert item["frame_changes"], item["item_id"]


def test_no_world_reports_a_dead_item_or_an_anomaly():
    """`dead` means the oracle failed and `anomaly` means two instruments that
    must agree do not. Either is a defect, not a difficulty, and neither is
    tolerable at any count -- so this asserts zero over the whole catalogue
    rather than sampling."""
    result = disc.run()
    totals = result["totals"]
    assert totals["dead"] == 0, "the marker rejected its own ground truth"
    assert totals["anomalies"] == [], totals["anomalies"]


def test_the_profile_agrees_with_run_matrix_on_which_worlds_are_feasible():
    """Two drivers build the same papers by different routes. If they ever
    disagree about which worlds carry the question type, one of them is lying and
    the numbers from both become unquotable."""
    from exam.tools import run_matrix
    profiled = {w["world_id"] for w in disc.run()["worlds"] if w["feasible"]}
    matrix = {row["world_id"] for row in run_matrix.run()["matrix"]}
    assert profiled == matrix


@pytest.mark.parametrize("world_id", SAMPLE)
def test_free_equals_unchanged_frame_share(world_id):
    """`free` is counted per item from three marked submissions;
    `unchanged_frame_share` is counted builder-side from the frames. Two code
    paths to the same quantity, so a drift means one is broken.

    Renamed from `..._reproduces_the_published_bluffer_floor`, which oversold it:
    `run_matrix` sets `bluffer_floor` **to** `unchanged_frame_share`, so the old
    name implied a comparison against a marked bluffer that this test never
    makes. The next test does make it.
    """
    profile = disc.profile_world(world_id)
    paper = hw.build_for(world_id)
    share = profile["summary"]["free"] / profile["summary"]["n_items"]
    assert share == pytest.approx(float(paper.notes["unchanged_frame_share"]))


@pytest.mark.parametrize("world_id", SAMPLE)
def test_a_marked_bluffer_actually_scores_the_free_share(world_id):
    """The comparison the previous test only appears to make: run the bluffer
    through `mark()` and check its fraction is the free share. This is what
    would catch a marker that paid the bluffer on an item whose frame changes."""
    from exam.grading.mark import mark
    from exam.model import Submission
    profile = disc.profile_world(world_id)
    paper = hw.build_for(world_id)
    key_doc = paper.key(digest())
    report = mark(key_doc, Submission(
        examinee_id="fake-bluffer", paper_id=paper.paper_id,
        answers=hw.reference_answers(paper, key_doc, "bluffer"),
        capabilities=("answers",)), axes_fn=hw.axes)
    assert report.fraction == pytest.approx(
        profile["summary"]["free"] / profile["summary"]["n_items"])


def test_the_class_is_the_named_function_of_split_and_frame_change():
    """The identity, asserted as the *specific* mapping and over the whole
    catalogue rather than a sample.

    The first version of this test checked only well-definedness on three
    worlds -- it would have passed if every item were classified `free`. It is
    the published claim (236 items, 20 worlds, one named mapping), so it is now
    the tested claim.
    """
    expected = {("replay", False): "free", ("heldout", False): "free",
                ("replay", True): "memorised", ("heldout", True): "theory"}
    seen = set()
    for world in disc.run()["worlds"]:
        for item in world["items"]:
            key = (item["split"], item["frame_changes"])
            assert item["class"] == expected[key], (world["world_id"], item)
            seen.add(key)
    assert seen == set(expected), "a cell of the identity went untested"


@pytest.mark.parametrize("world_id", SAMPLE)
def test_the_class_is_a_function_of_split_and_frame_change(world_id):
    """**A caveat with a test on it, because prose caveats get skimmed.**

    Given how the three voters are defined, an item's class is determined by
    `(split, frame_changes)` -- both fields the profile already carries, one of
    them printed on the sheet. So `theory` does not measure difficulty: it means
    "held out, and something moved". Several independent examiners confirmed the
    practical consequence by writing a fourth strategy, a generic grid prior, that
    takes most of the `theory` residue on most worlds.

    This test exists so that adding a genuinely independent voter -- which is the
    fix -- **breaks it loudly**, rather than silently improving a number nobody
    was watching. If you are here because this test failed, that is the good case:
    delete it and quote the new residue.
    """
    profile = disc.profile_world(world_id)
    seen = {}
    for item in profile["items"]:
        key = (item["split"], item["frame_changes"])
        if key in seen:
            assert seen[key] == item["class"], (
                "the class is no longer a function of (split, frame_changes) on "
                "%s -- a voter that is not one of the original three must have "
                "been added. Retire this test and requote `effective_size`."
                % world_id)
        seen[key] = item["class"]


def test_the_profile_is_deterministic():
    a = disc.profile_world("t1-walk-maze")
    b = disc.profile_world("t1-walk-maze")
    assert a == b


def test_an_infeasible_world_is_refused_rather_than_shrunk():
    """`profile_world` must not invent a paper for a world that cannot carry one;
    `plan()` already refuses and the profiler has to inherit that refusal."""
    shape = hw.plan("t1-walk-maze", per_class=99)
    assert not shape["feasible"]
    profile = disc.profile_world("t1-walk-maze", per_class=99)
    assert profile["feasible"] is False
    assert profile["items"] == []
    assert profile["blocked_rules"]


def test_the_catalogue_is_covered():
    """A profile over a subset would understate the free share; the totals are
    quoted catalogue-wide, so the run has to be catalogue-wide."""
    result = disc.run()
    assert result["worlds_offered"] == len(port.world_ids())
    assert result["worlds_profiled"] == result["worlds_offered"]
    assert result["rubric_digest"] == digest()
