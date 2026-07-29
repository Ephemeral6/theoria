"""Tests for the marker's self-test, and for the leak it found.

Two things are under test here and they pull in opposite directions.

The **self-test** is machinery, so these tests are hostile to it: a mutant that
cannot be made to fail is not a mutant, so each one is shown failing against a
marker broken on purpose, not merely passing against the real one.  The
fault-injection matrix gets the same treatment — the seams are checked to be
seams, and the restoration is checked, because a fault-injection suite that
leaks a patched marker into the next test poisons everything after it.

The **leak** is a fact about a shipped rubric, so those tests pin the exact
behaviour that shipped: an illegible answer used to be read as the substantive
claim `never`, which is ground truth on the one undetectable variant, so a
submission containing nothing collected that item in full.  Regression tests
here name the item and the amount (D-EX-011's discipline: pin the leak that
shipped, not a paraphrase of it).
"""

from __future__ import annotations

import os
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam.grading import mark as mark_mod                           # noqa: E402
from exam.grading import selftest as st                             # noqa: E402
from exam.grading.calibration import calibrate_one                  # noqa: E402
from exam.grading.confusion_matrix import (collisions,               # noqa: E402
                                           per_class_confusion,
                                           render_matrix, verdict_matrix)
from exam.grading.registry import digest                            # noqa: E402
from exam.grading.rubrics_adaptation import (UNREADABLE,          # noqa: E402
                                             _read_claim, _read_level_claim)
from exam.model import ItemScore                                    # noqa: E402
from exam.papers import module_for                                  # noqa: E402

ALL_TYPES = ("heldout", "handover", "adaptation", "verdict")


# ------------------------------------------------------- the mutants themselves

@pytest.mark.parametrize("question_type", ALL_TYPES)
def test_every_mutant_passes_on_the_real_marker(question_type):
    result = st.mutant_battery(question_type)
    assert result["failures"] == [], result["failures"]
    assert result["oracle_fraction"] == 1.0
    assert set(result["checks"]) == set(st.PRE_REGISTERED)


@pytest.mark.parametrize("question_type", ALL_TYPES)
def test_every_mutant_states_what_it_pre_registered(question_type):
    """A check whose expectation is not written down is a check nobody can
    argue with afterwards."""
    for name, entry in st.mutant_battery(question_type)["checks"].items():
        assert entry["pre_registered"] == st.PRE_REGISTERED[name]
        assert len(entry["pre_registered"]) > 40


def test_drop_exact_predicts_the_score_before_it_is_marked():
    result = st.mutant_battery("verdict")["checks"]["drop_exact"]
    assert result["predicted_awarded"] == result["observed_awarded"]
    assert result["dropped_all_unanswered"] is True
    assert result["n_dropped"] >= 2


def test_partial_credit_check_declares_itself_inapplicable_rather_than_passing():
    """D-EX-011: an optional check is a check that does not run.  Where there
    is nothing to degrade the check has to say so, not report a pass."""
    quiet = st.mutant_battery("heldout")["checks"]["partial_credit_survives"]
    assert quiet["applicable"] is False
    assert quiet["n_degraded"] == 0
    loud = st.mutant_battery("verdict")["checks"]["partial_credit_survives"]
    assert loud["applicable"] is True
    assert loud["n_strictly_partial"] > 0


# --------------------------------------------- the mutants have to be breakable

def test_a_marker_that_pays_for_silence_fails_drop_exact():
    def fake_unanswered(item, why="no answer submitted"):
        return ItemScore(item.item_id, item.rubric_id, item.points, item.points,
                         "correct", {"injected": True})

    with st._patched(mark_mod, "unanswered", fake_unanswered):
        result = st.mutant_battery("verdict")
    assert not result["checks"]["drop_exact"]["passed"]


def test_a_marker_that_accepts_anything_fails_transplant_and_garbage():
    with _fault("accepts_anything"):
        result = st.mutant_battery("verdict")
    assert not result["checks"]["transplant"]["passed"]
    assert not result["checks"]["garbage"]["passed"]


def test_a_marker_that_truncates_partial_credit_fails_only_the_new_check():
    """The fault that nothing on master caught, and the check added for it.

    It is asserted as *only* this check because that is the finding: every band
    in `calibration.EXPECTED` for the informative fakes is `Band(0.0, x)`,
    bounded above and open below, so a marker that depresses scores satisfies
    all of them.
    """
    with _fault("truncates_partial"):
        result = st.mutant_battery("verdict")
        calibration = calibrate_one("verdict")
    assert not result["checks"]["partial_credit_survives"]["passed"]
    assert calibration["calibrated"] is True, (
        "if the bands now catch this, the finding has changed and the comment "
        "above needs rewriting -- not this assertion loosening")
    others = [n for n, e in result["checks"].items()
              if n != "partial_credit_survives" and not e["passed"]]
    assert others == []


def test_an_order_dependent_marker_fails_the_key_order_mutant():
    with _fault("order_dependent"):
        result = st.mutant_battery("verdict")
    assert not result["checks"]["key_order"]["passed"]


def _fault(name):
    """Apply a named fault from `selftest.FAULTS` as a context manager."""
    import contextlib

    @contextlib.contextmanager
    def applied():
        with contextlib.ExitStack() as stack:
            for target, attr, value in st.FAULTS[name]():
                stack.enter_context(st._patched(target, attr, value))
            yield
    return applied()


def test_injected_faults_are_fully_restored():
    """A fault that leaks out of its context poisons every test after it."""
    before = (mark_mod.rubric, mark_mod.unanswered, mark_mod.confusion)
    for name in st.FAULTS:
        with _fault(name):
            pass
    assert (mark_mod.rubric, mark_mod.unanswered, mark_mod.confusion) == before
    assert calibrate_one("verdict")["calibrated"] is True


def test_the_fault_matrix_runs_on_a_clean_baseline_and_catches_everything():
    """Slow: eight faults x every check.  It is the whole point of the module."""
    matrix = st.fault_matrix(("verdict",), cap=3)
    assert matrix["baseline_clean"] is True, matrix["baseline_noise"]
    assert set(matrix["faults"]) == set(st.FAULTS)
    for name, row in matrix["faults"].items():
        if name == "blends_the_pair":
            assert "calibration" in row["caught_by"]
        assert row["caught"], (
            "nothing catches %s (%s). That is a hole in the checks, not a "
            "reason to delete the fault." % (name, row["what_it_does"]))


# -------------------------------------------------------- the protocol digest

def test_the_protocol_digest_covers_the_marker_and_the_bands():
    modules = st.protocol_module_digests()
    assert set(modules) == set(st.PROTOCOL_MODULES)
    assert "exam.grading.calibration" in modules
    assert "exam.grading.mark" in modules
    assert st.protocol_digest() == st.protocol_digest()
    assert st.protocol_digest() != digest()


def test_a_widened_band_changes_the_protocol_digest(monkeypatch):
    """STATUS open weakness 3: the rubric digest does not cover the bands, so a
    quiet widening was invisible.  This is what makes it visible."""
    import inspect

    from exam.grading import calibration

    before = st.protocol_digest()
    real = inspect.getsource

    def patched(obj):
        if obj is calibration:
            return real(obj) + "\n# a quietly widened band\n"
        return real(obj)

    monkeypatch.setattr(inspect, "getsource", patched)
    assert st.protocol_digest() != before


# --------------------------------------------------- the confusion matrix split

def test_an_empty_denominator_is_undefined_and_not_zero():
    matrix = verdict_matrix()
    small = matrix["examinees"]["oracle"]["split"]["by_class"]["small_unsolvable"]
    assert small["n_negative"] == 0
    assert small["specificity"] is None
    assert "empty" in small["specificity_undefined_because"]
    assert small["sensitivity"] == 1.0


def test_the_split_separates_the_memoriser_from_ground_truth():
    """The argument for splitting the pair, as a measurement rather than a claim.

    Pooled, the memoriser is numerically identical to the oracle -- sensitivity
    1.0 and specificity 1.0 -- while scoring 0.5882.  It abstains on all four
    large-space items, and abstentions stay out of the denominator, so the
    pooled rate is computed over the classes it happens to be good at.  Only the
    split and the coverage figure show it.
    """
    matrix = verdict_matrix()
    oracle = matrix["examinees"]["oracle"]
    memoriser = matrix["examinees"]["memoriser"]

    assert oracle["pooled"]["sensitivity"] == memoriser["pooled"]["sensitivity"] == 1.0
    assert oracle["pooled"]["specificity"] == memoriser["pooled"]["specificity"] == 1.0
    assert memoriser["fraction"] < oracle["fraction"]

    large = memoriser["split"]["by_class"]["large_unsolvable"]
    assert large["n_positive"] == 4
    assert large["abstained_on_positive"] == 4
    assert large["sensitivity"] is None
    assert large["coverage_positive"] == 0.0

    small = memoriser["split"]["by_class"]["small_unsolvable"]
    assert small["sensitivity"] == 1.0
    assert small["coverage_positive"] == 1.0


def test_the_bluffer_signature_survives_the_split():
    matrix = verdict_matrix()
    bluffer = matrix["examinees"]["bluffer"]["split"]
    assert bluffer["overall"]["sensitivity"] == 1.0
    assert bluffer["overall"]["specificity"] == 0.0
    assert bluffer["by_class"]["solvable_hard"]["specificity"] == 0.0
    assert bluffer["by_class"]["solvable_hard"]["coverage_negative"] == 1.0


def test_the_rendered_matrix_prints_coverage_and_never_prints_a_fake_zero():
    text = render_matrix(verdict_matrix())
    assert "1.000 (5/9)" in text          # the memoriser's pooled sensitivity
    assert "--" in text
    assert "empty denominator, not a zero" in text
    for line in text.splitlines():
        if line.startswith("| `oracle`"):
            # class (i) and (ii) have no solvable items: those cells must be
            # blank, never 0.000, or the oracle would look like it had failed.
            assert line.count("0.000") == 0


def test_all_three_verdict_classes_are_present_with_a_constructive_spec():
    """Ask (2) of the item, verified rather than rebuilt.

    The paper already carries every class, and the class lives on the truth
    side only -- so this test says both things at once: the classes are there,
    and they are not on the sheet.
    """
    module = module_for("verdict")
    paper = module.build()
    key_doc = paper.key(digest())
    by_class = {}
    for entry in key_doc["items"]:
        by_class.setdefault(entry["truth"]["class"], []).append(entry)
    assert set(by_class) == {"small_unsolvable", "large_unsolvable", "solvable_hard"}
    for klass, entries in by_class.items():
        assert entries, klass
        for entry in entries:
            assert entry["truth"].get("spec"), (klass, entry["item_id"])
    for item in paper.items:
        assert "class" not in item.paper


# ------------------------------- the leak the self-test found, pinned exactly

def test_an_illegible_answer_is_not_read_as_the_claim_never():
    """The defect V4 found, named at the function that had it.

    `_read_claim` had two outcomes where it needed three, so everything it
    could not parse became "did not claim a detection" and the caller wrote
    that down as `never`.
    """
    for illegible in (st.GARBAGE, "", {}, None, [], 3.5):
        assert _read_claim(illegible) == UNREADABLE, illegible

    # the four legible spellings of "never", which must keep working
    assert _read_claim("never") == (True, False, None)
    assert _read_claim(False) == (True, False, None)
    assert _read_claim({"detected": False}) == (True, False, None)
    assert _read_claim({"index": None}) == (True, False, None)
    # and a real claim
    assert _read_claim(18) == (True, True, 18)
    assert _read_claim({"detected": True, "index": 18}) == (True, True, 18)


def test_a_level_the_examinee_never_mentioned_is_not_a_claim_of_never():
    assert _read_level_claim({}, "match") == UNREADABLE
    assert _read_level_claim({"other": 3}, "match") == UNREADABLE
    # present-with-null is the spelling the reference answers use, and it is a
    # claim: the examinee named the level and declined to give it an index.
    assert _read_level_claim({"match": None}, "match") == (True, False, None)
    assert _read_level_claim({"match": 6}, "match") == (True, True, 6)


@pytest.mark.parametrize("nothing", [st.GARBAGE, "", {}, None])
def test_a_submission_of_nothing_scores_nothing_on_every_paper(nothing):
    """The regression, at the amount that shipped.

    Before the fix this scored 1.600 of 144 on `adaptation`, all of it on the
    two `v-a0-03.detect` items -- the one variant that is undetectable on its
    base level, where `never` is the truth.  The other three papers scored
    0.000, which is why nothing had ever caught it.
    """
    for question_type in ALL_TYPES:
        module, paper, key_doc, oracle = st._oracle_setup(question_type)
        answers = {item_id: nothing for item_id in oracle}
        report = st._mark(key_doc, answers, "nothing",
                          getattr(module, "axes", None))
        assert report.awarded == 0.0, (question_type, nothing, report.awarded)


# ---- negative control: an UNFIXED defect, pinned so it cannot change quietly

@pytest.mark.xfail(strict=True, reason=(
    "UNFIXED DEFECT, pinned deliberately: rubrics_adaptation._read_set uses the "
    "whole answer as the value of every set-valued key when the answer is not a "
    "dict, so a bare [] asserts the empty set for rules_falsified, "
    "claims_to_reexamine and claims_now_false at once and is paid 6.500 of 144 "
    "on adapt.collateral.v1. NOT fixed here: _read_set is on the marking path "
    "for V4's published calibration numbers, so changing its semantics moves "
    "them and needs its own item. Written up in "
    "exam/runs/20260728T151000Z-V7-exam-stress-fanout/ADVERSARIAL.md (claim 4) "
    "and FINDINGS.md section 4b. strict=True on purpose: the day _read_set is "
    "fixed this XPASSes, the suite goes red, and whoever fixed it is forced to "
    "re-derive the artefacts that quote the old number."))
def test_the_bare_empty_list_is_not_paid_on_the_adaptation_paper():
    """`[]` is illegible, and the marker says so itself -- on the other rubric.

    `test_an_illegible_answer_is_not_read_as_the_claim_never` above lists `[]`
    among the tokens `_read_claim` must call UNREADABLE, and it does.  Thirty
    lines further down, `test_a_submission_of_nothing_scores_nothing_on_every_paper`
    is parametrised `[GARBAGE, "", {}, None]` -- and `[]` is conspicuously
    absent from that list.  The one token the two tests disagree about is the
    one the collateral rubric pays for.  This test is the missing parameter,
    written separately rather than added to the list so that the xfail marks the
    defect and not the other four tokens, which are all correctly worth nothing.
    """
    for question_type in ALL_TYPES:
        module, paper, key_doc, oracle = st._oracle_setup(question_type)
        report = st._mark(key_doc, {item_id: [] for item_id in oracle},
                          "empty-list", getattr(module, "axes", None))
        assert report.awarded == 0.0, (question_type, report.awarded)


def test_the_undetectable_variant_no_longer_pays_an_empty_submission():
    module, paper, key_doc, oracle = st._oracle_setup("adaptation")
    report = st._mark(key_doc, {i: {} for i in oracle}, "empty",
                      getattr(module, "axes", None))
    by_id = {s.item_id: s for s in report.scores}
    match = by_id["v-a0-03.detect.match"]
    assert match.awarded == 0.0
    assert match.detail["said"] == "unreadable"
    across = by_id["v-a0-03.detect.across"]
    assert across.awarded == 0.0
    assert across.detail["said"] == "unreadable"
    assert len(across.detail["unreadable_on"]) == 5
    assert across.detail["claimed_never_on"] == []


def test_the_fix_moved_no_calibration_number():
    """A bugfix that also re-tunes the instrument is two changes wearing one
    coat.  These are the numbers from before the fix, on master at 98593a0."""
    expected = {"heldout": {"memoriser": 0.575, "bluffer": 0.45},
                "handover": {"memoriser": 0.7174, "bluffer": 0.3261},
                "adaptation": {"memoriser": 0.1708, "bluffer": 0.1708},
                "verdict": {"memoriser": 0.5882, "bluffer": 0.2647}}
    for question_type, wanted in expected.items():
        result = calibrate_one(question_type)
        assert result["calibrated"] is True, result["failures"]
        assert result["modes"]["oracle"]["fraction"] == 1.0
        assert result["modes"]["null"]["fraction"] == 0.0
        for mode, value in wanted.items():
            assert round(result["modes"][mode]["fraction"], 4) == value, mode


# ------------------------------------- the cheater, and what the pair cannot see

def test_the_sheet_only_cheater_is_on_the_matrix_and_scores_exactly_half():
    """V4's cheater pass, pinned.

    An adversarial subagent was handed `p15-verdict-a2` alone -- no world, no
    source, no key -- and told to cheat rather than solve.  It returned all 17
    claims and got **17 of 17**, against a 9/17 majority baseline, having
    predicted 13.8 for itself.  It submitted no certificate and no witness on
    any item, so the rubric caps it at exactly half: the claim half is
    answerable from the sheet, the reason half is not.

    That cap is the paper's defence and it is worth pinning, because if a later
    edit ever lets a claim earn more than half an item, a perfect guesser
    starts outscoring a real theory that shows its work.
    """
    matrix = verdict_matrix()
    cheater = matrix["examinees"]["cheater-v4"]
    assert cheater["is_fake"] is False
    assert cheater["fraction"] == 0.5
    assert cheater["awarded"] == 17.0 and cheater["possible"] == 34.0
    pooled = cheater["split"]["overall"]
    assert pooled["tp"] == 9 and pooled["fn"] == 0
    assert pooled["tn"] == 8 and pooled["fp"] == 0


def test_the_pair_cannot_separate_ground_truth_from_a_reader_of_the_sheet():
    """The strongest argument in this file for never quoting the pair alone.

    `oracle` and `cheater-v4` agree in **every cell** of the split -- 1.000 and
    1.000 throughout, full coverage on both -- and differ only in the score.
    One derived every answer from the world; the other never saw it.
    """
    matrix = verdict_matrix()
    twins = {tuple(group) for group, _scores in collisions(matrix)}
    assert ("cheater-v4", "oracle") in twins
    oracle = matrix["examinees"]["oracle"]["split"]
    cheater = matrix["examinees"]["cheater-v4"]["split"]
    for klass in matrix["class_sizes"]:
        for rate in ("sensitivity", "specificity",
                     "coverage_positive", "coverage_negative"):
            assert (oracle["by_class"][klass][rate]
                    == cheater["by_class"][klass][rate]), (klass, rate)
    assert matrix["examinees"]["oracle"]["fraction"] == 1.0
    assert matrix["examinees"]["cheater-v4"]["fraction"] == 0.5
    assert "cannot tell apart" in render_matrix(matrix)


def test_no_sheet_names_the_genre_of_the_world_it_asks_about():
    """The leak V4's cheater found on the held-out sheet, pinned.

    `instructions` opened with "A0 is a sokoban variant" while
    `world.description` on the same sheet said the dynamics "are deliberately
    not stated here". Naming a canonical puzzle genre states them.

    The list is the genres whose names would give A0 or A2 away. It is short on
    purpose: a probe that matches everything gets switched off (leakage.py says
    so about three-character probes), and this one only has to catch the
    wording that actually shipped and its nearest neighbours.
    """
    from exam.model import canonical
    from exam.papers import BUILDERS

    genres = ("sokoban", "sokobán", "boulder dash", "rush hour", "15-puzzle",
              "sliding block", "warehouse keeper", "倉庫番")
    for question_type in BUILDERS:
        paper = module_for(question_type).build()
        text = canonical(paper.sheet(digest())).lower()
        for genre in genres:
            assert genre not in text, (
                "%s names the genre %r on the sheet. The examinee is being "
                "asked what the dynamics are; a genre name answers that from "
                "a prior instead of from the evidence."
                % (paper.paper_id, genre))
