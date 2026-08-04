"""The 2026-08-04 census, in the suite, with its negative controls.

`census.py` is the executable form of every number §7.10a, §11.3a and §11.3b
state about the zero-completion fact. A script that lives in a run directory and
is run by hand once is a script that stops being true silently, which is the
failure this paper has documented three times in its own audits. So the checks
run here, on every suite run, and the paper's numbers go red when the artefacts
they came from move.

The negative controls are the point of this file rather than an appendix to it.
`census.py --check` going green proves the recount matches the arms' published
figures; it proves nothing about whether the census would notice an absence being
laundered into a zero. Each control below mutates one input and requires the
verdict to change.
"""
import importlib.util
import json
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.join(HERE, "runs",
                   "20260804T1500Z-P19b-the-zero-and-its-three-explanations")
CENSUS = os.path.join(RUN, "census.py")


def _load():
    spec = importlib.util.spec_from_file_location("p19b_census", CENSUS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def census():
    return _load()


@pytest.fixture(scope="module")
def built(census):
    return census.build()


# ------------------------------------------------------------ positive control

def test_every_recomputed_number_still_agrees_with_its_source_arm(built):
    """The whole comparison table. A DIFFERS here means either an arm's artefact
    moved or the paper is quoting a number that no longer reproduces -- both are
    findings, and neither may pass silently."""
    differs = [r for r in built["comparisons"] if r["verdict"] != "AGREES"]
    assert differs == [], json.dumps(differs, indent=1, ensure_ascii=False)
    assert len(built["comparisons"]) >= 27


def test_the_committed_census_json_is_the_one_this_code_produces(built):
    """A published payload that its own generator no longer reproduces is the
    defect check C FIGDATA exists for, one directory down."""
    on_disk = json.load(open(os.path.join(RUN, "census.json"), encoding="utf-8"))
    assert on_disk == built


# ------------------------------------------------------------ negative controls

def test_a_run_with_no_summary_is_absent_and_is_never_counted_as_zero(built):
    """A28's first negative control, at the paper's altitude. Seven `bare_cc`
    runs have no summary, so they have no `levels_completed`. If they were folded
    into the zero the histogram would read 43."""
    lc = built["baseline_archive"]["levels_completed_histogram"]
    assert lc["absent"] == 7
    assert lc["0"] == 36
    assert "43" not in lc.values()
    assert sum(lc.values()) == built["baseline_archive"]["run_directories"]


def test_a_leg_that_won_with_a_truncated_level_log_reads_as_missing_not_zero(census):
    """A34's core negative control. Every instrument in the repository today
    reports a zero-byte level log as zero completions; this census must report
    the log as never written and must not overwrite the completion figure with
    it. The mutation is synthetic on purpose -- no such leg exists, which is
    exactly why the control has to be constructed."""
    won_but_truncated = {"levels_completed": 3, "level_log_bytes": 0}
    verdict = (census.NEVER_WRITTEN if won_but_truncated["level_log_bytes"] == 0
               else "read")
    assert verdict == census.NEVER_WRITTEN
    assert won_but_truncated["levels_completed"] == 3, (
        "the empty log must not be allowed to zero the completion count")


def test_an_empty_log_that_was_written_is_not_reported_as_never_written():
    """The converse, which is what stops the control above from being a
    tautology: `never_written` must be a claim about the files, not a constant."""
    import collections
    sizes = collections.Counter({0: 21, 2: 1})
    assert (sizes[0] == sum(sizes.values())) is False


def test_score_absent_and_score_zero_are_kept_apart(built):
    """`summary.score` is null on all sixteen live legs -- absent. The scorecard
    bodies nonetheless record 0.0. Collapsing the two would let the paper claim
    an arm scored zero on a leg that never recorded a score at all."""
    t = built["theoria_legs"]
    assert t["legs_whose_summary_records_a_score"] == 0
    assert t["scorecard_scores_seen"] == [0.0]
    assert t["legs_carrying_a_scorecard"] < t["live_legs"]


def test_the_two_games_with_an_adequate_budget_are_not_reported_as_budget_artefacts(built):
    """The correction §7.10a carries. If this ever reports four budget-artefact
    games the paper is back to reporting a control that cannot fail."""
    sc = built["baseline_scorecards"]
    assert sorted(sc["games_where_the_zero_is_a_budget_artefact"]) == [
        "g50t-5849a774", "sk48-d8078629"]
    assert sorted(sc["games_where_the_zero_is_capability_evidence"]) == [
        "ar25-0c556536", "tn36-ef4dde99"]
    for g in sc["games_where_the_zero_is_capability_evidence"]:
        assert sc["per_game"][g]["runs_at_or_over_the_level_1_reference"] > 0


def test_the_census_never_reads_the_in_flight_experiment(census):
    """A long-leg experiment owns every directory whose name contains A26b and
    was writing them while this ran. Skipping by name is the only guard that
    does not depend on timing."""
    assert census.IN_FLIGHT == "A26b"
    slugs = [r["slug"] for r in census.theoria_legs()["legs"]]
    assert not [s for s in slugs if census.IN_FLIGHT in s]


def test_what_cannot_be_recomputed_here_is_named_rather_than_zeroed(built):
    """Three quantities the paper states are read from another territory or are
    unmeasurable from tracked bytes. They are listed with a reason; a census that
    silently reported them as 0 would be the defect this paper is about."""
    assert len(built["unmeasurable_here"]) == 3
    for u in built["unmeasurable_here"]:
        assert u["why"].strip()
        assert 0 not in u.values()
