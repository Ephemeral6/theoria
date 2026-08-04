"""A28 -- the zero in the paper's left-hand column, asserted rather than narrated.

Three claims, each of which the paper depends on and none of which was
checkable before this module existed:

  1. The gameplay response has no `score` field, so a harness reading gameplay
     responses is structurally unable to report a score. The arm's zero is
     therefore *not* evidence about the score unless it came from a scorecard
     body.
  2. Every authoritative scorecard body archived by this arm carries score 0.0
     at all three nesting levels (card, environment, run) and at every level
     slot. The zero is real, not an artefact of a missed read.
  3. The zero is *not* uniformly a capability result. On two of four games no
     run ever *spent* as many actions as the level-1 baseline.

**Claim 3's original wording said "was ever allowed", and that was wrong.** This
module reads `budget` out of `runs/bare_cc-*/run.json`, which is a population of
36 runs and is not the arm's ceiling: the 48 episodes of the approved S1
baseline-parity campaign have no `runs/` directory at all
(`runs/s1-full-run-not-archived/run.json`, INC-BA-003), and their allowance --
recorded in `out/campaign/campaign_*.json` as `total_budget` -- clears the
level-1 baseline on all four games. What stopped them was a stop rule that D-016
has since replaced. See `harness/baseline_allowance.py`, its test module, and
`BASELINE_COLUMN.md`; the assertions below are kept because they are true of the
population they read, and renamed because their old names named a conclusion the
whole archive does not support.

These are regression tests over archived artefacts, not live runs. They make no
network call.
"""

from __future__ import annotations

import json
import os

import pytest

from harness import audit_zero

pytestmark = pytest.mark.filterwarnings("ignore")


@pytest.fixture(scope="module")
def obs():
    return audit_zero.scorecard_observations()


@pytest.fixture(scope="module")
def res():
    return audit_zero.analyse()


def test_the_arm_archived_authoritative_scorecard_bodies(obs):
    """Without these the whole question is unanswerable, so assert they exist.

    The count is a floor, not an equality: probe_log.jsonl is append-only and a
    later campaign may add more.
    """
    assert len(obs) >= 63, "archived scorecard bodies went missing"
    assert len({o["run_id"] for o in obs if o["run_id"]}) >= 57


def test_gameplay_responses_carry_no_score_field():
    """Claim 1. The ledger's env_step records are lifted verbatim from gameplay
    responses. If any of them had a score, `migrate_ledger.ENV_STEP_GAPS` would
    be wrong and the arm could have read a score all along.
    """
    root = audit_zero.HERE
    ledger = os.path.join(root, "ledger.jsonl")
    seen = 0
    with open(ledger, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if "state" not in rec or "levels_completed" not in rec:
                continue
            seen += 1
            assert "score" not in rec, (
                "a gameplay record carried a score field: %r" % (rec.get("run_id"),))
    assert seen > 100, "no gameplay records found; the fixture moved"


def test_every_authoritative_score_is_zero(res):
    """Claim 2. Not 'we recorded zero' -- the API said zero, at every level."""
    q2 = res["question_2_score_is_zero"]
    assert q2["observations_with_nonzero_card_score"] == 0
    assert q2["observations_with_nonzero_run_score"] == 0
    assert q2["observations_with_any_nonzero_level_score"] == 0
    assert q2["observations_with_levels_completed_gt_0"] == 0


def test_the_arm_never_persisted_the_authoritative_score(res):
    """The defect worth naming: the score exists in the probe log but no
    runs/<id>/run.json carries it, so anything built from run.json is quoting
    `levels_completed`, not the score. The two agree here -- both zero -- but
    that agreement is luck, not design.
    """
    q1 = res["question_1_score_is_read"]
    assert q1["run_dirs_persisting_a_score_field"] == 0
    assert q1["archived_run_dirs"] >= 43


def test_two_games_never_saw_a_run_spend_its_level_1_baseline(res):
    """Claim 3, restated as what it actually measures: actions *spent*.

    g50t and sk48: no run ever spent as many actions as the level-1 baseline.
    ar25 and tn36: some runs did.

    Spending the baseline is not the same as being allowed to, and it is not on
    its own capability evidence -- `tn36`'s best run spent exactly 32 against a
    32-action baseline and came back NOT_FINISHED. The verdict that separates
    the two lives in `harness/baseline_allowance.py`.
    """
    per_game = res["question_3_budget"]["per_game"]

    budget_limited = {"g50t-5849a774", "sk48-d8078629"}
    capability_tested = {"ar25-0c556536", "tn36-ef4dde99"}

    for game in budget_limited:
        d = per_game[game]
        assert d["obs_reaching_level_1_baseline"] == 0, (
            "%s now has a run at or above its level-1 baseline; the zero for "
            "this game is no longer purely a budget artefact" % game)
        assert d["best_pct_of_level_1"] < 100.0

    for game in capability_tested:
        d = per_game[game]
        assert d["obs_reaching_level_1_baseline"] > 0
        assert d["best_pct_of_level_1"] >= 100.0


def test_every_run_carrying_a_budget_key_was_capped_below_its_level_1_baseline(res):
    """True of 36 runs, and of exactly those 36.

    Budgets written into `run.json` were 20 or 30 actions; the smallest level-1
    baseline on the development pile is 32. So none of *these* runs could have
    completed level 1 within budget -- which says nothing about the 48 S1
    episodes, whose allowance is written somewhere else and is larger. The
    denominator is asserted here so the sentence cannot be quoted without it.
    """
    q3 = res["question_3_budget"]
    assert set(q3["budgets_seen"]) <= {20, 30}
    assert q3["runs_with_a_budget"] == 36
    assert q3["runs_whose_budget_is_below_level_1_baseline"] == q3["runs_with_a_budget"]

    smallest = min(d["level_1_baseline"] for d in q3["per_game"].values())
    assert max(q3["budgets_seen"]) < smallest, (
        "a configured budget now reaches a level-1 baseline; re-derive the "
        "budget-artefact claim before the paper repeats it")


def test_the_capability_evidence_is_one_model_tier_only(obs):
    """The six runs that did reach a level-1 baseline are all haiku. No opus or
    sonnet run ever got far enough for its zero to mean anything about
    capability -- which is exactly the tier the paper's headline compares.
    """
    base = audit_zero.baselines(obs)
    reached = [o for o in obs
               if base.get(o["game_id"])
               and (o["actions"] or 0) >= base[o["game_id"]][0]]
    assert reached, "no run reached a level-1 baseline"
    tiers = {("opus" if "opus" in (o["run_id"] or "") else
              "sonnet" if "sonnet" in (o["run_id"] or "") else
              "haiku") for o in reached}
    assert tiers == {"haiku"}, (
        "a non-haiku run now reaches a level-1 baseline: %s" % sorted(tiers))
