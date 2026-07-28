"""The control arm, and the objection it exists to answer.

*The person who carried the books to level 2 wrote them for level 1, and
already knew the answer.*  These tests are the answer: a manual induced blind
from level 2's own evidence contains every clause level 1's manual contains,
and the two arms converged on the same laws and the same semantics without
either seeing the other.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import pytest  # noqa: E402

import _bootstrap  # noqa: F401,E402

ARTIFACTS = os.path.join(HERE, "artifacts")
THEORY = os.path.join(HERE, "theory")


def _agreement(state="as_written"):
    """One of the two comparisons in `domain_agreement.json`.

    `as_written` is the blind manual before it was told anything about the
    toolchain, and it is the one that measures **convergence** — two arms,
    disjoint evidence, no contact.  `after_conformance` is the same manual
    after being made to ground its rules and rename its objects; its higher
    agreement is partly the tool's doing and is not evidence of convergence.
    Tests about convergence must use the first.
    """
    path = os.path.join(ARTIFACTS, "domain_agreement.json")
    if not os.path.exists(path):
        pytest.skip("run `python -m a3pipeline.agreement` first")
    report = json.load(open(path, encoding="utf-8"))
    if state not in report:
        pytest.skip("%s comparison absent" % state)
    return report[state]


def _bill(arm):
    path = os.path.join(ARTIFACTS, "bill_%s.json" % arm)
    if not os.path.exists(path):
        pytest.skip("bill_%s.json absent — run `python run_all.py`" % arm)
    return json.load(open(path, encoding="utf-8"))


# ------------------------------------------------------ the two arms converged

def test_every_level_1_clause_is_in_the_blindly_induced_manual():
    """The objection's answer.  Not "similar" — every clause, by meaning."""
    result = _agreement()
    assert result["canonical_only_in_left"] == [], (
        "level 1's manual claims something the blind arm did not reach: %s"
        % result["canonical_only_in_left"])
    assert result["canonical_agreed"] == result["canonical_rules_left"]
    assert result["canonical_rules_left"] > 0


def test_the_two_arms_agree_on_the_laws_and_the_semantics():
    result = _agreement()
    assert result["canonical_laws_only_left"] == []
    assert result["canonical_laws_only_right"] == []
    assert len(result["canonical_laws_agreed"]) >= 2
    assert result["semantics_agree"] is True


def test_neither_arm_put_a_goal_section_in_its_domain():
    """Both independently kept level data out of the travelling file."""
    assert _agreement()["neither_has_a_goal_section"] is True


def test_neither_domain_contains_a_coordinate():
    """The miner offered `!at(3,1)` to both arms.  Neither took one.

    Comments are stripped before the check, and that is a deliberate choice
    rather than a loophole: level 1's manual *discusses* the coordinates it
    rejected — the four displacement vectors, `!at(3,1)` itself — and a rule
    that forbade mentioning them would forbid recording the adjudication.  What
    must not contain a coordinate is the part the compiler reads.
    """
    import re
    for name in ("domain.dsl", "domain_l2_scratch.dsl"):
        path = os.path.join(THEORY, name)
        if not os.path.exists(path):
            pytest.skip("%s absent" % name)
        for lineno, line in enumerate(open(path, encoding="utf-8"), 1):
            body = line.split("#")[0]
            assert not re.search(r"\(\s*\d+\s*,\s*\d+\s*\)", body), (
                "%s:%d has a coordinate in the domain: %s"
                % (name, lineno, line.strip()))


def test_most_of_a_manual_is_convention_not_content():
    """The gap between the strict and the canonical comparison is the point.

    Two manuals that agree completely about the world agreed on *nothing*
    textually.  If this ever stops being true the quotient in
    `a3pipeline/agreement.py` has become a no-op and the agreement result would
    no longer be evidence of anything.
    """
    result = _agreement("as_written")
    assert result["strict_agreement"] < result["canonical_agreement"]
    assert result["roles_left"] != result["roles_right"], (
        "the two arms happened to choose the same object names, so this run "
        "does not exercise the renaming quotient")


def test_the_blind_arm_over_generalised_and_level_1_did_not():
    """The disagreement is one-sided, and the report says which side.

    The blind manual has clauses level 1's does not; level 1's has none the
    blind manual lacks.  If that ever reverses, level 1's manual is claiming
    something its own evidence did not license and §4 is wrong.
    """
    result = _agreement()
    assert result["canonical_only_in_left"] == []


# ----------------------------------------------------------------- the bill

def test_the_control_arm_paid_for_what_the_transfer_arm_got_free():
    scratch = _bill("l2_from_scratch")["counts"]
    transfer = _bill("l2_transfer")["counts"]
    for line in ("world_frames", "world_actions", "engine_stages",
                 "candidates_adjudicated", "theorize_rounds",
                 "dsl_clauses_written"):
        assert scratch[line] > transfer[line], line


def test_the_two_level_2_arms_are_comparable():
    """Same level, same supplied constants — only the books differ."""
    scratch = _bill("l2_from_scratch")
    transfer = _bill("l2_transfer")
    assert scratch["level"] == transfer["level"]
    assert scratch["carries_books"] is False
    assert transfer["carries_books"] is True


def test_the_control_arm_also_won():
    """A control arm that failed would not be a control arm."""
    path = os.path.join(ARTIFACTS, "arm_l2_from_scratch.json")
    if not os.path.exists(path):
        pytest.skip("run `python run_all.py` first")
    arm = json.load(open(path, encoding="utf-8"))
    assert arm["outcome"] == "win", arm["outcome"]
    assert arm["certify_cheap"]["green"] is True


def test_the_grounding_round_is_on_the_control_arms_bill():
    """R-09's cost is charged, not absorbed.

    The blind manual's first version did not compile — `gen_python_a0` cannot
    take a `?dir`-lifted rule — and grounding it cost a theorize round.  That
    round belongs to the arm that did not carry the books.
    """
    assert _bill("l2_from_scratch")["counts"]["theorize_rounds"] >= 2


def test_the_failed_lifted_manual_is_kept():
    """Evidence for R-09, confirmed from a second and blind direction."""
    kept = os.path.join(ARTIFACTS, "finding_r09_blind",
                        "domain_l2_scratch_lifted.dsl")
    assert os.path.exists(kept)
    text = open(kept, encoding="utf-8").read()
    assert "forall" in text, "the preserved manual is not the lifted one"


def test_conformance_raised_agreement_and_the_report_does_not_hide_it():
    """The two comparisons must both survive, and differ.

    After the toolchain rounds the blind manual uses the same object names and
    the same ground form, so its *strict* agreement with level 1's rises
    sharply.  That rise is the tool's doing, not the evidence's.  Quoting only
    the post-conformance number would overstate the convergence result, so both
    are kept and this test fails if the pair ever collapses to one.
    """
    before = _agreement("as_written")
    after = _agreement("after_conformance")
    assert before["strict_agreement"] < after["strict_agreement"], (
        "conformance did not raise strict agreement — has the preserved "
        "pre-conformance manual been overwritten?")
    # ...and the *canonical* comparison, which is the one about the world,
    # should be unmoved by a rename.
    assert before["canonical_agreement"] == after["canonical_agreement"]
    assert before["canonical_only_in_left"] == after["canonical_only_in_left"]
