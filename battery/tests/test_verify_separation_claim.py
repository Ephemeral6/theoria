"""Negative controls for `verify.py`'s fourth rung.

The rung exists because a cell whose maximum attainable score was zero was
carried elsewhere as 60% while rungs 1-3 stayed green. A gate written in
response to that failure is worth exactly as much as its ability to go red, so
every check in it gets a mutant here that it must catch.

`test_the_gate_is_not_vacuous` is the one that matters: it asserts the honest
tree passes *and* that six separate corruptions of it fail. A gate that only
ever passed would look identical in CI to one that works.
"""

import json
import os

import pytest

from battery import verify

HERE = os.path.dirname(os.path.abspath(__file__))
REAL = os.path.dirname(HERE)


def _tree(tmp_path, *, artefact=None, metrics_md=None, status_md=None):
    """A miniature battery directory the rung can be pointed at.

    Built from the real committed files and then mutated, rather than written
    from scratch: a fixture that shares no text with the artefacts would let
    the gate pass on prose the real documents do not contain.
    """
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir(exist_ok=True)

    if artefact is None:
        with open(os.path.join(REAL, "artifacts",
                               "discrimination_arms.json"), encoding="utf-8") as fh:
            artefact = json.load(fh)
    with open(artifacts / "discrimination_arms.json", "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(artefact, fh)

    for name, override in (("METRICS.md", metrics_md),
                           ("STATUS.md", status_md)):
        if override is None:
            with open(os.path.join(REAL, name), encoding="utf-8") as fh:
                override = fh.read()
        with open(tmp_path / name, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(override)
    return tmp_path


def _run(monkeypatch, tree):
    monkeypatch.setattr(verify, "HERE", str(tree))
    monkeypatch.setattr(verify, "SHIPPED", str(tree / "artifacts"))
    problems = []
    verify.rung_separation_claim(problems)
    return problems


def _committed(name):
    with open(os.path.join(REAL, name), encoding="utf-8") as fh:
        return fh.read()


def _artefact():
    with open(os.path.join(REAL, "artifacts", "discrimination_arms.json"),
              encoding="utf-8") as fh:
        return json.load(fh)


def test_the_committed_tree_passes(tmp_path, monkeypatch):
    assert _run(monkeypatch, _tree(tmp_path)) == []


def test_a_hand_edited_headline_is_caught(tmp_path, monkeypatch):
    """METRICS.md is generated, so the generator cannot see this happen."""
    doctored = _committed("METRICS.md").replace(
        "**0 of 38 metrics separate", "**7 of 38 metrics separate")
    problems = _run(monkeypatch, _tree(tmp_path, metrics_md=doctored))
    assert any("headline" in p for p in problems), problems


def test_dropping_the_ceiling_paragraph_is_caught(tmp_path, monkeypatch):
    """A bare zero reads as `the metrics failed`; the ceiling is why it isn't."""
    doctored = _committed("METRICS.md").replace(
        "unreachable for every metric", "not currently observed for any metric")
    problems = _run(monkeypatch, _tree(tmp_path, metrics_md=doctored))
    assert any("too small to attain" in p for p in problems), problems


def test_a_status_that_never_states_the_count_is_caught(tmp_path, monkeypatch):
    """The whole W-13 section deleted -- STATUS.md stops making the claim."""
    body = _committed("STATUS.md")
    start = body.index("### W-13")
    end = body.index("\n---", start)
    problems = _run(monkeypatch, _tree(tmp_path, status_md=body[:start] + body[end:]))
    assert any("separation count" in p for p in problems), problems


def test_a_status_that_states_the_wrong_count_is_caught(tmp_path, monkeypatch):
    """The 60% failure in miniature: prose that disagrees with the artefact."""
    doctored = _committed("STATUS.md").replace(
        verify.STATUS_CLAIM % (38, 0), verify.STATUS_CLAIM % (38, 6))
    problems = _run(monkeypatch, _tree(tmp_path, status_md=doctored))
    assert any("separation count" in p for p in problems), problems


def test_the_status_check_is_not_satisfied_by_a_stray_digit(tmp_path,
                                                            monkeypatch):
    """The defect this gate's own negative control found.

    The first draft looked for `str(n_separating)` anywhere in the W-13
    section. `0` occurs in `0.125`, in `80 run`, in half the prose in the file,
    so the check passed on documents that never stated the count. Pinned as a
    test because the cheap version reads as equivalent and is not.
    """
    doctored = _committed("STATUS.md").replace(
        verify.STATUS_CLAIM % (38, 0),
        "分离力见产物；p 底 0.125，对照臂 80 run，38 条指标")
    problems = _run(monkeypatch, _tree(tmp_path, status_md=doctored))
    assert any("separation count" in p for p in problems), problems


def test_a_separating_verdict_that_the_arithmetic_forbids_is_caught(
        tmp_path, monkeypatch):
    """The contradiction the 60% report would have been, in artefact form.

    Four paired games cannot reach p<0.05, so `discriminating` here is not an
    optimistic reading of thin data -- it is impossible, and a gate that let it
    through would be the same gate that let the 60% through.
    """
    doc = _artefact()
    doc["metrics"]["E4"]["verdict"] = "discriminating"
    problems = _run(monkeypatch, _tree(tmp_path, artefact=doc))
    assert any("arithmetic contradiction" in p for p in problems), problems


def test_the_ceiling_claim_goes_stale_when_the_pile_grows(tmp_path,
                                                          monkeypatch):
    """The flip. This is the direction a one-sided gate would miss.

    The moment a metric collects enough *non-tied* pairs for p<0.05 to be
    attainable, the ceiling paragraph stops being true and the zero starts
    meaning something else. Nothing else in the repo would notice.
    """
    doc = _artefact()
    doc["metrics"]["E4"]["sign_test"]["n"] = verify.docs_sign_test_games_needed()
    problems = _run(monkeypatch, _tree(tmp_path, artefact=doc))
    assert any("stale" in p for p in problems), problems


def test_paired_games_alone_do_not_trip_the_flip(tmp_path, monkeypatch):
    """The false positive an adversarial review found in the first draft.

    `2 / 2**n` is a function of the sign test's non-tied `n`, not of
    `n_paired_games`, and the two already differ here -- P3, X2 and X3 pair
    four games and score three. A pile that grew to exactly the threshold while
    every metric lost one pair to a tie leaves the floor at 0.0625: still above
    0.05, so `discriminating` is still unreachable and the ceiling paragraph is
    still **true**. The first draft keyed on paired games and went red anyway,
    demanding that a correct sentence be rewritten.
    """
    needed = verify.docs_sign_test_games_needed()
    doc = _artefact()
    for entry in doc["metrics"].values():
        if entry.get("sign_test"):
            entry["n_paired_games"] = needed
            entry["sign_test"]["n"] = needed - 1      # one tie each
            entry["sign_test"]["ties"] = 1
    assert _run(monkeypatch, _tree(tmp_path, artefact=doc)) == []


def test_a_missing_artefact_is_red_rather_than_skipped(tmp_path, monkeypatch):
    """`verify` has been broken before by a check that could not run."""
    tree = _tree(tmp_path)
    os.remove(tree / "artifacts" / "discrimination_arms.json")
    problems = _run(monkeypatch, tree)
    assert any("is absent" in p for p in problems), problems


def test_an_empty_artefact_is_red_rather_than_green(tmp_path, monkeypatch):
    """Zero metrics judged trivially satisfies `no metric separated`."""
    problems = _run(monkeypatch, _tree(tmp_path, artefact={"metrics": {}}))
    assert any("judges no metrics" in p for p in problems), problems


@pytest.mark.parametrize("alpha,expected", [
    (0.05, 6), (0.0625, 5), (0.125, 4), (0.01, 8),
])
def test_the_threshold_is_derived_from_the_test_not_restated(alpha, expected):
    """`2 / 2**n <= alpha`, the same formula `audit/stats.py` uses.

    Pinned at several alphas so the gate cannot silently acquire a hard-coded
    6 that happens to be right today.
    """
    from battery.docs import _sign_test_games_needed
    assert _sign_test_games_needed(alpha) == expected


def test_the_threshold_agrees_with_the_statistic_it_claims_to_follow():
    """The cross-check: derived number vs the real `sign_test`."""
    from battery.audit.stats import sign_test
    from battery.docs import _sign_test_games_needed

    needed = _sign_test_games_needed()
    perfect = [(1.0, 0.0)] * needed
    assert sign_test(perfect)["min_attainable_p"] <= 0.05
    assert sign_test(perfect[:-1])["min_attainable_p"] > 0.05
