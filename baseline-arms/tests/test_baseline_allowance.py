"""A28b -- the allowance column, and the negative controls that make it a test.

A28 asked whether any baseline run was allowed enough actions to complete
level 1, read `budget` out of `runs/bare_cc-*/run.json`, and answered "no, on
any game". This module asserts the answer the whole archive gives, which is a
different one, and asserts the three ways the checker could be wrong:

  * it could recite A28's conclusion instead of computing it -- so a mock game
    whose allowance clears its baseline must come back `capability_tested` or
    `abort_artefact`, never `budget_artefact`;
  * it could turn an absent allowance into a zero -- so an observed run with no
    allowance anywhere must be counted as absent and must not drag the maximum
    down;
  * it could accept "spent as many actions as the baseline" as capability
    evidence -- which is A28's error pointing the other way, and would make
    `tn36` (32 actions against a 32-action baseline, NOT_FINISHED) look like a
    tested game.

And one positive control on the rule reconstruction: a checker that can only
ever answer "today's rule would not have fired" is not checking the rule, so a
synthetic episode with ten back-to-back failures must come back True.

Offline. No network, no spend.
"""

from __future__ import annotations

import pytest

from harness import audit_zero, bare_cc, baseline_allowance

pytestmark = pytest.mark.filterwarnings("ignore")

DEV_PILE = ("ar25-0c556536", "g50t-5849a774", "sk48-d8078629", "tn36-ef4dde99")


@pytest.fixture(scope="module")
def res():
    return baseline_allowance.analyse()


# ---------------------------------------------------------------- the finding

def test_the_s1_campaign_allowed_more_than_the_level_1_baseline_on_every_game(res):
    """The fact that overturns A28's headline.

    `harness/campaign.py` sets each game's action budget to the sum of its
    official level baselines and hands each episode what is left of it. On all
    four development-pile games that number is larger -- by an order of
    magnitude on three of them -- than the level-1 baseline the arm had to beat.
    """
    for game in DEV_PILE:
        d = res["per_game"][game]
        assert d["allowance_covers_level_1"], (
            "%s: max allowance %s is below its level-1 baseline %d"
            % (game, d["allowance_max"], d["level_1_baseline"]))
        assert d["allowance_max"] >= d["level_1_baseline"]
        assert d["runs_allowed_at_least_level_1"] >= 12, (
            "%s: the S1 episodes are missing from the allowance table" % game)


def test_no_game_is_a_budget_artefact(res):
    """The sentence the paper must not print. If this test ever goes red the
    finding has changed and the wording in `BASELINE_COLUMN.md` is stale.
    """
    verdicts = {g: res["per_game"][g]["verdict"] for g in DEV_PILE}
    assert "budget_artefact" not in verdicts.values(), verdicts


def test_the_runs_that_had_the_actions_were_stopped_by_a_rule_that_no_longer_exists(res):
    """47 of 48 S1 episodes recorded `api_unusable` under a stop rule that
    counted *scattered* failures against an absolute ten. D-016 replaced it with
    a consecutive-failure abort and a budget-scaled grind cap. Reconstructed
    from the ledger's per-step `failed` flags, the longest back-to-back failure
    run anywhere in that campaign is far short of the current threshold, and no
    episode reaches the grind cap at a 317-1070 action budget.
    """
    sr = res["stop_rule"]
    assert sr["s1_episodes"] == 48
    assert sr["s1_episodes_with_a_ledger_failure_shape"] == 48, (
        "an S1 episode lost its ledger; the rule claim is no longer checkable")
    assert sr["s1_episodes_whose_recorded_outcome_was_api_unusable"] == 47
    assert sr["s1_longest_consecutive_failure_run_anywhere"] < bare_cc.CONSECUTIVE_FAILURE_ABORT
    assert sr["s1_episodes_that_would_abort_under_current_rules"] == 0


def test_exactly_one_run_in_the_whole_arm_ended_because_the_game_ended(res):
    """Everything else stopped because the harness stopped it. That single
    episode -- ar25, 67 successful actions against a 32-action level-1 baseline,
    terminal `game_over` -- is the arm's entire stock of capability evidence.
    """
    terminal = [rid for g in DEV_PILE
                for rid in res["per_game"][g]["terminal_game_end_at_or_over_level_1"]]
    assert terminal == ["bare_cc-ar25-claude-haiku-4-5-20251001-76390591"], terminal
    assert res["per_game"]["ar25-0c556536"]["verdict"] == "capability_tested"
    for game in ("g50t-5849a774", "sk48-d8078629", "tn36-ef4dde99"):
        assert res["per_game"][game]["verdict"] == "abort_artefact", game


def test_absence_is_counted_and_named_not_folded_into_a_zero(res):
    """Two observed run_ids have no allowance in any of the three sources. They
    are listed by name and excluded from the allowance maxima; nothing in the
    table renders them as an allowance of 0.
    """
    a = res["absence"]
    assert a["observed_run_ids"] >= 57
    assert a["observed_run_ids_with_no_allowance_anywhere"] == len(
        a["run_ids_with_no_allowance_anywhere"])
    assert a["observed_run_ids_with_a_recorded_allowance"] + \
        a["observed_run_ids_with_no_allowance_anywhere"] == a["observed_run_ids"]
    for g in DEV_PILE:
        assert res["per_game"][g]["allowance_max"] > 0


def test_the_older_reader_saw_a_strictly_smaller_population(res):
    """Why A28 concluded the opposite, stated as an assertion rather than a
    footnote: `audit_zero` counts only runs carrying a `budget` key, and no S1
    episode has a `runs/` directory at all (`runs/s1-full-run-not-archived`,
    INC-BA-003). The two tools are both right about their own populations, and
    only one of them is about the arm's ceiling.
    """
    old = audit_zero.analyse()["question_3_budget"]
    assert set(old["budgets_seen"]) <= {20, 30}
    assert old["runs_with_a_budget"] == 36
    assert res["stop_rule"]["s1_episodes"] == 48
    # the S1 allowances are larger than anything the old reader could see
    assert min(res["per_game"][g]["allowance_max"] for g in DEV_PILE) > max(old["budgets_seen"])


# ------------------------------------------------------- negative controls

def _mock_game(allowance, achieved, outcome, l1=50):
    """One game, one run, built by hand -- the classifier's inputs in the open."""
    obs = [{
        "run_id": "mock-1", "game_id": "mock-0000", "actions": achieved,
        "state": "GAME_OVER" if outcome == "game_over" else "NOT_FINISHED",
        "level_baseline_actions": [l1, 999], "level_scores": [0, 0],
        "levels_completed": 0, "card_score": 0.0, "env_score": 0.0,
        "run_score": 0.0, "resets": 0, "total_actions": achieved,
        "source": "mock", "note": None, "card_id": "mock", "level_actions": [achieved],
    }]
    recs = [{
        "run_id": "mock-1", "game_id": "mock-0000", "model": "mock",
        "allowance": allowance, "allowance_source": "mock", "regime": "mock",
        "actions_ok": achieved, "actions_failed": 0, "outcome": outcome,
    }]
    return obs, recs


def _classify(monkeypatch, obs, recs, shape=None):
    monkeypatch.setattr(baseline_allowance, "scorecard_observations", lambda: obs)
    monkeypatch.setattr(baseline_allowance, "allowance_records", lambda: recs)
    monkeypatch.setattr(baseline_allowance, "failure_shape", lambda: shape or {})
    return baseline_allowance.analyse()


def test_negative_control_a_generous_allowance_is_never_a_budget_artefact(monkeypatch):
    """If the checker only recited A28's conclusion this would still come back
    `budget_artefact`, and the checker would be worthless.
    """
    obs, recs = _mock_game(allowance=1000, achieved=12, outcome="api_unusable", l1=50)
    out = _classify(monkeypatch, obs, recs)["per_game"]["mock-0000"]
    assert out["verdict"] == "abort_artefact"
    assert out["allowance_covers_level_1"] is True


def test_negative_control_a_thin_allowance_still_is_one(monkeypatch):
    """The other half of the same control: the label must still be reachable, or
    the checker has merely been inverted.
    """
    obs, recs = _mock_game(allowance=30, achieved=30, outcome="budget_exhausted", l1=50)
    out = _classify(monkeypatch, obs, recs)["per_game"]["mock-0000"]
    assert out["verdict"] == "budget_artefact"
    assert out["allowance_covers_level_1"] is False


def test_negative_control_absent_allowance_is_absent_not_zero(monkeypatch):
    """A run observed on a scorecard with no allowance recorded anywhere must
    not be classified at all -- an allowance of `None` is not an allowance of 0,
    and a game made only of such runs has no verdict to give.
    """
    obs, recs = _mock_game(allowance=None, achieved=40, outcome="api_unusable", l1=50)
    out = _classify(monkeypatch, obs, recs)
    g = out["per_game"]["mock-0000"]
    assert g["allowance_max"] is None
    assert g["verdict"] == "no_allowance_recorded"
    assert g["allowance_covers_level_1"] is False
    assert out["absence"]["run_ids_with_no_allowance_anywhere"] == ["mock-1"]


def test_negative_control_spending_the_baseline_is_not_capability_evidence(monkeypatch):
    """A28 read `achieved >= baseline` as capability evidence. `tn36` spent
    exactly 32 actions against a 32-action baseline and came back NOT_FINISHED:
    the game did not end, the harness stopped it. That must not be labelled a
    tested game, or the paper gets a capability claim out of a truncation.
    """
    obs, recs = _mock_game(allowance=300, achieved=50, outcome="api_unusable", l1=50)
    out = _classify(monkeypatch, obs, recs)["per_game"]["mock-0000"]
    assert out["terminal_game_end_at_or_over_level_1"] == []
    assert out["verdict"] == "abort_artefact"

    obs, recs = _mock_game(allowance=300, achieved=50, outcome="game_over", l1=50)
    out = _classify(monkeypatch, obs, recs)["per_game"]["mock-0000"]
    assert out["verdict"] == "capability_tested"


def test_positive_control_the_rule_reconstruction_can_say_yes():
    """`would_abort_today` returns False on every real S1 episode. A predicate
    that cannot return True on any input is not a predicate, so drive it with a
    synthetic episode on each of the two rules.
    """
    consecutive = {"ledger_steps": 60, "failed": 10,
                   "longest_consecutive_failures": bare_cc.CONSECUTIVE_FAILURE_ABORT}
    assert baseline_allowance.would_abort_today(1000, consecutive) is True

    budget = 20
    grind = {"ledger_steps": 40, "failed": bare_cc.cumulative_failure_cap(budget),
             "longest_consecutive_failures": 2}
    assert baseline_allowance.would_abort_today(budget, grind) is True

    survives = {"ledger_steps": 60, "failed": 10, "longest_consecutive_failures": 5}
    assert baseline_allowance.would_abort_today(748, survives) is False

    assert baseline_allowance.would_abort_today(748, None) is None
    assert baseline_allowance.would_abort_today(None, survives) is None
