"""The endpoint-2 layer, and the two things it must never stop doing.

Every test here is written so that it can fail: each one was run against a
deliberately broken version of the code it pins, and the break is named in the
docstring.  A regression test whose red has never been seen is a test whose
green means nothing.
"""

from __future__ import annotations

import pytest

from exam import endpoint as ep
from exam import prereg
from exam.grading.mark import mark
from exam.grading.registry import digest
from exam.papers import module_for
from exam.tools import endpoint_verdict as ev


@pytest.fixture(scope="module")
def paper_and_key():
    module = module_for("verdict")
    paper = module.build()
    return module, paper, paper.key(digest())


def _judge(mode, paper_and_key):
    module, paper, key_doc = paper_and_key
    answers = module.reference_answers(paper, key_doc, mode)
    from exam.model import Submission
    submission = Submission(examinee_id="t-%s" % mode, paper_id=paper.paper_id,
                            answers=answers,
                            capabilities=() if mode == "null" else ("answers",))
    report = mark(key_doc, submission, axes_fn=getattr(module, "axes", None))
    return ep.judge(report, key_doc)


# ------------------------------------------------------- the conversion

def test_conversion_fills_both_denominators_to_the_class_size(paper_and_key):
    """弃权计错 means tp+fn and tn+fp are the class sizes, on every examinee.

    Broken by having `abstain_as_wrong` return the cell unchanged: the abstainer
    then keeps `n_positive` 0 and this assertion fails on the first mode.
    """
    for mode in ("oracle", "null", "abstainer", "memoriser", "bluffer", "denier"):
        record = _judge(mode, paper_and_key)["record"]
        cell = record["converted"]["overall"]
        assert cell["tp"] + cell["fn"] == 9, mode
        assert cell["tn"] + cell["fp"] == 8, mode


def test_neither_rate_is_ever_undefined_after_conversion(paper_and_key):
    """`None < S_min` is not false, it is undefined -- launch_blockers 9.15.

    This is the property that gives the specificity floor a total order.  An
    arm that abstains on every solvable item used to leave `specificity` at
    `None`, and the floor could not be applied to it at all.
    """
    for mode in ("null", "abstainer"):
        ruling = _judge(mode, paper_and_key)["ruling"]
        assert ruling["specificity"] is not None, mode
        assert ruling["sensitivity"] is not None, mode
        assert ruling["specificity"] == 0.0


def test_the_marker_still_reports_what_it_observed(paper_and_key):
    """The conversion is a layer, not an edit: D-EX-015 stands underneath it.

    The observed rates must survive beside the converted ones, or the finding
    that an abstention is not a wrong answer has been overwritten by the
    endpoint's ruling that, for *this* endpoint, it counts as one.
    """
    record = _judge("abstainer", paper_and_key)["record"]
    cell = record["converted"]["overall"]
    assert cell["observed_sensitivity"] is None
    assert cell["observed_specificity"] is None
    assert cell["sensitivity"] == 0.0 and cell["specificity"] == 0.0
    assert record["observed"]["overall"]["sensitivity"] is None


def test_a_cell_missing_an_escape_counter_is_refused():
    """A conversion that silently skipped an escape would restore the defect.

    Broken by defaulting the missing key to 0: this raises nothing and an
    unreadable answer quietly leaves the denominator again.
    """
    cell = {"tp": 1, "fp": 0, "tn": 1, "fn": 0,
            "abstained_on_positive": 0, "abstained_on_negative": 0,
            "unanswered_on_positive": 0, "unanswered_on_negative": 0}
    with pytest.raises(KeyError):
        ep.abstain_as_wrong(cell)


def test_a_declared_class_size_that_disagrees_is_an_error():
    """If the arithmetic does not land on the class size, an item was lost."""
    cell = {"tp": 1, "fp": 0, "tn": 1, "fn": 0, "n_positive": 5, "n_negative": 1,
            "abstained_on_positive": 0, "abstained_on_negative": 0,
            "unanswered_on_positive": 0, "unanswered_on_negative": 0,
            "unclassified_on_positive": 0, "unclassified_on_negative": 0}
    with pytest.raises(AssertionError):
        ep.abstain_as_wrong(cell)


def test_balanced_accuracy_is_never_one_sided():
    """A BA that fell back to whichever half existed is the number to refuse."""
    assert ep.balanced_accuracy({"sensitivity": 1.0, "specificity": None}) is None
    assert ep.balanced_accuracy({"sensitivity": None, "specificity": 1.0}) is None
    assert ep.balanced_accuracy({"sensitivity": 1.0, "specificity": 0.0}) == 0.5


# ------------------------------------------------------------ coverage

def test_coverage_is_read_before_the_conversion(paper_and_key):
    """Converted coverage is 1.0 by construction and would say nothing.

    The memoriser answered 0 of 4 class (ii) items.  Read after the conversion
    it would look like full coverage of a class it never touched, and the floor
    that catches it would never fire.
    """
    record = _judge("memoriser", paper_and_key)["record"]
    assert record["coverage_observed"]["large_unsolvable"]["coverage_positive"] == 0.0
    assert record["coverage_observed"]["large_unsolvable"]["answered_positive"] == 0
    # ... while its converted pair is perfectly readable, which is the trap.
    assert record["converted"]["overall"]["sensitivity"] > 0.5


# ---------------------------------------------------------- adjudication

def test_the_controls_are_judged_as_pre_registered():
    """`launch_blockers` 9.16's two, plus four more, in one assertion."""
    assert prereg.check_controls() == []


def test_the_gate_can_say_yes(paper_and_key):
    """A gate that has only ever refused is indistinguishable from a stub."""
    assert _judge("oracle", paper_and_key)["ruling"]["credited"] is True


def test_memoriser_is_inconclusive_and_not_refuted(paper_and_key):
    """Silence is not refutation -- the direction is the ruling of 9.16.

    Broken by routing the coverage breach to 不成立: this fails, and so does
    the pre-registered control table.
    """
    ruling = _judge("memoriser", paper_and_key)["ruling"]
    assert ruling["verdict"] == ep.VERDICT_INCONCLUSIVE
    assert not ruling["credited"]


def test_both_constants_land_on_exactly_one_half(paper_and_key):
    """The argument for the BA floor, as an assertion rather than a sentence."""
    bluffer = _judge("bluffer", paper_and_key)["ruling"]
    denier = _judge("denier", paper_and_key)["ruling"]
    assert (bluffer["sensitivity"], bluffer["specificity"]) == (1.0, 0.0)
    assert (denier["sensitivity"], denier["specificity"]) == (0.0, 1.0)
    assert bluffer["balanced_accuracy"] == denier["balanced_accuracy"] == 0.5
    assert not bluffer["credited"] and not denier["credited"]


def test_specificity_floor_is_checked_before_ba(paper_and_key):
    """§2.2 makes it a veto *no matter how high BA is*, so order matters.

    `overclaimer` has BA 0.6875, above the floor, and specificity 0.375, below
    it.  If the BA test ran first it would be credited.
    """
    ruling = _judge("overclaimer", paper_and_key)["ruling"]
    assert ruling["balanced_accuracy"] > ep.BA_FLOOR
    assert ruling["verdict"] == ep.VERDICT_REFUTED
    assert "specificity" in ruling["reasons"][0]


def test_every_floor_catches_something_on_its_own():
    """Leave-one-out, recomputed. A floor nothing needs is decoration.

    This is the test that found the defect it now pins: with only `bluffer`,
    `abstainer` and `null` on the sheet, removing `S_min` changed no verdict at
    all, because all three also fail the BA floor.
    """
    loo = prereg.floor_leave_one_out()
    assert loo["all_floors"] == []
    for floor, claim in prereg.FLOOR_CLAIMS.items():
        credited = loo["without_%s" % floor]
        assert credited == claim["catches_alone"], (
            "removing %s credits %s; FLOOR_CLAIMS says %s"
            % (floor, credited, claim["catches_alone"]))
        assert credited, "%s catches nothing on its own" % floor


# ------------------------------------------------------------- the CLI

def test_exit_codes_are_the_answer():
    """The launch gate's contract is exit 0 / non-zero, on two targets."""
    assert ev.main(["--examinee", "oracle"]) == ev.EXIT_CREDITED
    assert ev.main(["--examinee", "bluffer"]) == ev.EXIT_REFUTED
    assert ev.main(["--examinee", "memoriser"]) == ev.EXIT_INCONCLUSIVE
    assert ev.EXIT_INCONCLUSIVE != 0, (
        "不可结论 must fail the launch gate's positive-target contract, or an "
        "arm that answered nothing clears a blocker")


def test_the_control_transcripts_are_on_disk(tmp_path):
    """9.15's `negative_target_exists` was `false`; a blocker with no target
    cannot be cleared by anyone, so the transcripts ship."""
    written = ev.emit_controls(str(tmp_path))
    assert len(written) == len(ev.CONTROLS)
    from exam.model import Submission, read_json
    for path in written:
        doc = read_json(path)
        submission = Submission.from_json(doc)
        assert submission.paper_id == "p15-verdict-a2"
