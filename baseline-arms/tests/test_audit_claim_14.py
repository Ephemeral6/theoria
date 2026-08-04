"""A33 -- the recount of registration #14, and the two ways it must fail.

The positive tests pin every number the corrected wording publishes.  The two
negative samples are the reason the module exists, and they are written first
in the ticket for the same reason: a checker that only confirms the conclusion
it was built around is not a checker.

  * **Backfill.** Take one of the seven runs whose completion count is ABSENT
    and hand it a `levels_completed: 0`.  The checker must go red and name that
    run.  Turning an absent value into a zero is precisely the error being
    corrected; a checker that absorbed it would be committing the error one
    layer down.
  * **A budget that clears the baseline.** Introduce a run budgeted at 100
    actions against g50t's level-1 baseline of 78.  The partition must move it
    out of `budget_below_level_1_baseline` and report it separately.  If a run
    that *could* have won still lands in the "was not budgeted to win" bucket,
    the partition is not computing anything -- it is reciting §4's conclusion.

The synthetic trees are built from copies of the real `run.json` files, so the
partition is exercised against the real record plus one perturbation, not
against a toy.
"""

import json
import os
import shutil

import pytest

from harness import audit_claim_14 as a33

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.path.join(HERE, "runs")

# The API's own level-1 baselines, injected so the negative samples do not each
# pay for a full probe-log scan.  Values are audit_zero's, recomputed in the
# `test_injected_baselines_match_the_api` test below rather than trusted.
BASELINES = {"ar25-0c556536": 32, "g50t-5849a774": 78,
             "sk48-d8078629": 61, "tn36-ef4dde99": 32}


@pytest.fixture(scope="module")
def real():
    """One recount of the committed tree, shared by every assertion below.

    Module-scoped on purpose: the probe-log scan behind it is the single
    most expensive read in this territory.
    """
    return a33.recount()


def test_an_unmutated_clone_is_green(tmp_path):
    """The control for both negative samples.

    Without this, `assert problems` proves nothing: a clone that was already
    red would satisfy it no matter what the mutation did.
    """
    runs_dir = _clone_runs(tmp_path)
    assert a33.adjudicate(_recount(runs_dir), runs_dir) == []


def _clone_runs(tmp_path):
    """A runs/ tree holding every real run.json and the manifest, nothing else.

    Only the JSON is copied -- the run directories also hold large artefacts
    that nothing here reads.
    """
    dest = tmp_path / "runs"
    dest.mkdir()
    shutil.copy(os.path.join(RUNS, "MANIFEST.json"), dest / "MANIFEST.json")
    for name in sorted(os.listdir(RUNS)):
        src = os.path.join(RUNS, name, "run.json")
        if os.path.exists(src):
            (dest / name).mkdir()
            shutil.copy(src, dest / name / "run.json")
    return str(dest)


def _recount(runs_dir):
    """Recount a synthetic tree against the REAL scorecard observations.

    Not `obs=[]`.  An earlier draft passed an empty list, which made
    `adjudicate()` return two problems (the score column collapses to
    `{absent: 8, unobtainable: 35}`) *before any mutation was applied* -- so
    every `assert problems` below passed vacuously and "goes red" was never
    actually demonstrated.  `test_an_unmutated_clone_is_green` is the control
    that keeps that from coming back.
    """
    return a33.recount(runs_dir, level_1_baselines=dict(BASELINES),
                       obs=a33.observations())


# ---------------------------------------------------------------- positives

def test_forty_six_is_entries_and_forty_three_is_runs(real):
    s1 = real["section_1_46_is_entries_not_runs"]
    assert s1["run_json_files_on_disk"] == 46
    assert s1["manifest_total"] == 46
    assert s1["runs"] == 43
    assert s1["by_kind"] == {"excluded": 1, "fetch": 1, "migration": 1, "run": 43}
    # The three that never played a game, named rather than counted.
    assert {r["id"] for r in s1["not_runs"]} == {
        "s1-full-run-not-archived",
        "fetch-schema-traces-path-a",
        "migration-ledger-v0-to-v1.0",
    }
    assert s1["manifest_agrees_with_disk"] is True


def test_no_run_json_has_ever_carried_a_score_key(real):
    s2 = real["section_2_score_is_absent_not_zero"]
    assert s2["runs_persisting_a_score_field"] == 0
    assert s2["runs_persisting_a_score_field_ids"] == []


def test_the_completion_count_is_zero_thirty_six_times_and_absent_seven(real):
    s2 = real["section_2_score_is_absent_not_zero"]
    # The key assertion of the whole ticket: "absent" is its own bucket and is
    # not folded into the zeros.
    assert s2["completion_counts"] == {"0": 36, "absent": 7}
    assert s2["runs_with_a_summary"] == 36


def test_the_score_column_recovers_twenty_and_admits_twenty_three_holes(real):
    s2 = real["section_2_score_is_absent_not_zero"]
    assert s2["score_column"] == {"absent": 8, "recorded": 20, "unobtainable": 15}
    assert sum(s2["score_column"].values()) == 43
    assert s2["distinct_recorded_scores"] == [0.0]
    assert s2["max_recorded_score"] == 0.0


def test_fourteen_dead_runs_are_not_evidence_of_playing_and_losing(real):
    s3 = real["section_3_seven_have_no_count_and_fourteen_never_played"]
    assert s3["dead_runs"] == 14
    assert s3["manifest_dead_runs"] == 14
    assert s3["runs_without_a_summary"] == 7
    # 43 = 22 played + 14 dead + 7 with no summary at all.
    assert s3["runs_that_played_and_lost"] == 22
    assert s3["runs_that_played_and_lost"] + s3["dead_runs"] \
        + s3["runs_without_a_summary"] == 43


def test_no_budget_reached_its_games_level_1_baseline(real):
    s4 = real["section_4_no_budget_reached_the_level_1_baseline"]
    assert s4["budgets"] == {"20": 14, "30": 22, "absent": 7}
    assert s4["max_actions_ok"] == 30
    assert s4["total_actions_ok"] == 573
    assert s4["budget_below_level_1_baseline"] == 36
    assert s4["budget_at_or_above_level_1_baseline"] == 0
    assert s4["budget_unattributable"] == 7


def test_forty_three_means_archived_runs_not_runs(real):
    """The correction must not create the next '46'."""
    s4 = real["section_4_no_budget_reached_the_level_1_baseline"]
    assert s4["archived_run_dirs"] == 43
    assert s4["distinct_run_ids_in_scorecard_bodies"] == 57
    assert s4["run_ids_with_a_scorecard_but_no_archived_run_json"] == 37
    # Two independently-sourced counts landing on the same 80 the paper uses.
    assert s4["distinct_run_ids_known"] == 80


def test_cards_did_pass_a_level_1_baseline_so_the_strong_wording_is_wrong(real):
    """Layer two must contradict layer one, and be printed doing it."""
    reach = real["section_4_no_budget_reached_the_level_1_baseline"]["card_level_reach"]
    assert reach["ar25-0c556536"]["cards_reaching_the_baseline"] == 4
    assert reach["tn36-ef4dde99"]["cards_reaching_the_baseline"] == 2
    # ...and on g50t, the game whose 78 registration #14 quotes, none did.
    assert reach["g50t-5849a774"]["cards_reaching_the_baseline"] == 0
    assert reach["g50t-5849a774"]["best_card_actions"] == 73


def test_injected_baselines_match_what_the_api_reported(real):
    """The constant this file injects is not allowed to drift from the record."""
    assert real["section_4_no_budget_reached_the_level_1_baseline"][
        "level_1_baselines"] == BASELINES


def test_the_committed_tree_is_green(real):
    assert a33.adjudicate(real) == []


# --------------------------------------------------- negative sample one
#
# An absent completion count backfilled as zero.

def test_backfilling_an_absent_completion_count_as_zero_goes_red(tmp_path):
    runs_dir = _clone_runs(tmp_path)
    victim = a33.NO_SUMMARY_ROSTER[0]
    path = os.path.join(runs_dir, victim, "run.json")
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    assert doc.get("summary") is None, "fixture assumption: this run has none"

    # The exact hand-edit the ticket prescribes.
    doc["summary"] = {"levels_completed": 0}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)

    rc = _recount(runs_dir)
    problems = a33.adjudicate(rc, runs_dir)

    assert problems, "a backfilled zero passed the checker"
    named = [p for p in problems if victim in p]
    assert named, ("the checker went red but did not name %s; naming the run "
                   "is the requirement, since a bare count tells nobody which "
                   "record was falsified" % victim)
    assert any("backfilled" in p for p in named)
    # And the recount itself must not have quietly moved it into the zeros.
    assert rc["section_2_score_is_absent_not_zero"]["completion_counts"] \
        == {"0": 37, "absent": 6}


def test_deleting_a_no_summary_run_also_goes_red(tmp_path):
    """The roster's other edge: an absent record disappearing entirely."""
    runs_dir = _clone_runs(tmp_path)
    victim = a33.NO_SUMMARY_ROSTER[-1]
    shutil.rmtree(os.path.join(runs_dir, victim))

    problems = a33.adjudicate(_recount(runs_dir), runs_dir)
    assert any(victim in p and "run.json is gone" in p for p in problems)


# --------------------------------------------------- negative sample two
#
# A run budgeted above the level-1 baseline must leave the "not budgeted to
# win" bucket, or the partition is only reciting the conclusion.

def _mock_adequately_budgeted_run(runs_dir, run_id="bare_cc-g50t-mock-budget-100"):
    d = os.path.join(runs_dir, run_id)
    os.mkdir(d)
    with open(os.path.join(d, "run.json"), "w", encoding="utf-8") as fh:
        json.dump({
            "arm": "bare_cc", "id": run_id, "kind": "run",
            "game_id": "g50t-5849a774", "model": "claude-opus-5",
            "budget": 100,                       # > the level-1 baseline of 78
            "outcome": "budget_exhausted",
            "summary": {"actions_ok": 100, "levels_completed": 0,
                        "cost_usd": 11.38},
        }, fh)
    return run_id


def test_a_run_budgeted_past_the_baseline_leaves_the_insufficient_bucket(tmp_path):
    runs_dir = _clone_runs(tmp_path)
    mock = _mock_adequately_budgeted_run(runs_dir)

    rc = _recount(runs_dir)
    s4 = rc["section_4_no_budget_reached_the_level_1_baseline"]

    below = {r["id"] for r in s4["budget_below_level_1_baseline_rows"]}
    above = {r["id"] for r in s4["budget_at_or_above_level_1_baseline_rows"]}

    assert mock not in below, (
        "a run budgeted 100 against a level-1 baseline of 78 was counted among "
        "the runs that were not budgeted to win -- the partition is reciting "
        "section four's conclusion instead of computing it")
    assert mock in above
    assert s4["budget_at_or_above_level_1_baseline"] == 1
    # The real 36 are untouched: the mock is listed apart, not swapped in.
    assert s4["budget_below_level_1_baseline"] == 36


def test_the_partition_stays_a_partition_when_the_mock_is_added(tmp_path):
    runs_dir = _clone_runs(tmp_path)
    _mock_adequately_budgeted_run(runs_dir)
    rc = _recount(runs_dir)
    s1 = rc["section_1_46_is_entries_not_runs"]
    s4 = rc["section_4_no_budget_reached_the_level_1_baseline"]
    assert (s4["budget_below_level_1_baseline"]
            + s4["budget_at_or_above_level_1_baseline"]
            + s4["budget_unattributable"]) == s1["runs"] == 44


def test_the_mock_makes_the_published_counts_stale_and_says_so(tmp_path):
    """Adding a run is not a defect -- but the wording no longer describes the
    tree, and the checker must say that rather than pass."""
    runs_dir = _clone_runs(tmp_path)
    _mock_adequately_budgeted_run(runs_dir)
    problems = a33.adjudicate(_recount(runs_dir), runs_dir)
    assert any("kind == 'run'" in p for p in problems)
    # ...and not because it mistook the mock for a falsified record.
    assert not any("backfilled" in p for p in problems)


# --------------------------------------------------------------- guards

def test_a_missing_completion_count_is_never_defaulted_to_zero():
    """`_completion_count` is where a `.get(k, 0)` would do the damage."""
    assert a33._completion_count({}) == "absent"
    assert a33._completion_count({"summary": {}}) == "absent"
    assert a33._completion_count({"summary": {"levels_completed": 0}}) == 0
    assert a33._completion_count({"spend": {"levels_completed": 3}}) == 3


def test_the_score_column_never_emits_a_number_for_a_hole(real):
    from harness import score_column
    col = score_column.build(obs=[], runs_dir=RUNS)
    # With no scorecard observations at all, nothing is recoverable -- and the
    # column must say so with `None`, never with 0.0.
    assert col["counts"].get("recorded") is None
    assert col["max_recorded_score"] is None
    assert all(r["score"] is None for r in col["rows"])
    # `never_probed` is in the list on purpose: with no observations injected,
    # a card whose archived probes are not visible either was not shown to have
    # been refused, and `unobtainable` asserts a refusal. Claiming one here
    # would be the same unearned assertion the column exists to refuse.
    assert all(r["state"] in ("unobtainable", "never_probed", "absent")
               for r in col["rows"])
    assert "recorded" not in col["counts"] and "conflicting" not in col["counts"]


# ------------------------------------------- what an adversarial pass broke
#
# Each of these is a falsification that got past an earlier draft of this
# module with the gate still green. They are tests now because "the checker
# went red on the cases I thought of" is not the claim being made.

def test_a_disagreeing_score_is_not_swallowed_by_the_maximum():
    """The worst of the four: a 5.0 in the record under a published 'max 0.0'.

    The earlier draft emitted a *list* when a run's archived bodies disagreed,
    kept the row in `recorded`, and then filtered non-floats out of the
    maximum. So the column printed the 5.0 on its own row and still reported
    `max_recorded_score: 0.0`.
    """
    from harness import score_column
    obs = list(a33.observations())
    victim = next(o for o in obs if o.get("run_id") and o.get("run_score") == 0.0)
    obs.append({**victim, "run_score": 5.0})

    col = score_column.build(obs=obs, runs_dir=RUNS)
    row = next(r for r in col["rows"] if r["run_id"] == victim["run_id"])

    assert row["state"] == "conflicting", \
        "two archived answers were reported as one answer"
    assert row["score"] is None, "a disagreed-on score was published anyway"
    assert col["counts"]["recorded"] == 19
    assert col["counts"]["conflicting"] == 1
    # ...and the published counts have moved, so the gate must notice.
    assert col["max_recorded_score"] == 0.0


def test_a_conflicting_score_makes_the_gate_red(tmp_path):
    from harness import score_column
    obs = list(a33.observations())
    victim = next(o for o in obs if o.get("run_id") and o.get("run_score") == 0.0)
    obs.append({**victim, "run_score": 5.0})
    runs_dir = _clone_runs(tmp_path)
    rc = a33.recount(runs_dir, level_1_baselines=dict(BASELINES), obs=obs)
    assert any("score column" in p for p in a33.adjudicate(rc, runs_dir))


def test_relabelling_one_dead_outcome_as_another_goes_red(tmp_path):
    """`dead_runs == 14` held while the published histogram went false."""
    runs_dir = _clone_runs(tmp_path)
    victim = next(
        os.path.join(runs_dir, d, "run.json")
        for d in sorted(os.listdir(runs_dir))
        if os.path.exists(os.path.join(runs_dir, d, "run.json"))
        and json.load(open(os.path.join(runs_dir, d, "run.json"),
                           encoding="utf-8")).get("outcome") == "model_error")
    with open(victim, encoding="utf-8") as fh:
        doc = json.load(fh)
    doc["outcome"] = "api_unusable"          # total unmoved, distribution false
    with open(victim, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)

    rc = _recount(runs_dir)
    assert rc["section_3_seven_have_no_count_and_fourteen_never_played"][
        "dead_runs"] == 14, "fixture assumption: the total does not move"
    assert any("outcome histogram" in p
               for p in a33.adjudicate(rc, runs_dir))


def test_dropping_a_run_out_of_played_and_lost_goes_red(tmp_path):
    """`22 played and lost` was unpinned; a novel outcome silently made it 21."""
    runs_dir = _clone_runs(tmp_path)
    victim = next(
        os.path.join(runs_dir, d, "run.json")
        for d in sorted(os.listdir(runs_dir))
        if os.path.exists(os.path.join(runs_dir, d, "run.json"))
        and json.load(open(os.path.join(runs_dir, d, "run.json"),
                           encoding="utf-8")).get("outcome") == "budget_exhausted")
    with open(victim, encoding="utf-8") as fh:
        doc = json.load(fh)
    doc["outcome"] = "abandoned"
    with open(victim, "w", encoding="utf-8") as fh:
        json.dump(doc, fh)

    problems = a33.adjudicate(_recount(runs_dir), runs_dir)
    assert any("played and lost" in p for p in problems)
    assert any("no longer adds up" in p for p in problems)


def test_the_injected_observations_are_actually_used():
    """Section four silently rescanned the real corpus and ignored `obs=`."""
    rc = a33.recount(RUNS, level_1_baselines={"g50t-5849a774": 78}, obs=[
        {"run_id": "fake", "game_id": "g50t-5849a774", "actions": 999,
         "run_score": None, "level_baseline_actions": [78]}])
    reach = rc["section_4_no_budget_reached_the_level_1_baseline"]["card_level_reach"]
    assert reach["g50t-5849a774"]["observations"] == 1
    assert reach["g50t-5849a774"]["best_card_actions"] == 999


def test_a_card_with_no_recorded_refusal_is_not_called_unobtainable(tmp_path):
    """`unobtainable` asserts the API was asked and refused. Check, don't assume."""
    from harness import score_column
    runs_dir = _clone_runs(tmp_path)
    rid = "bare_cc-g50t-mock-unprobed-card"
    os.mkdir(os.path.join(runs_dir, rid))
    with open(os.path.join(runs_dir, rid, "run.json"), "w", encoding="utf-8") as fh:
        json.dump({"arm": "bare_cc", "id": rid, "kind": "run",
                   "game_id": "g50t-5849a774", "model": "claude-opus-5",
                   "budget": 30, "outcome": "budget_exhausted",
                   "summary": {"actions_ok": 30, "levels_completed": 0,
                               "card_id": "00000000-0000-0000-0000-000000000000"}},
                  fh)
    col = score_column.build(obs=a33.observations(), runs_dir=runs_dir)
    row = next(r for r in col["rows"] if r["run_id"] == rid)
    assert row["state"] == "never_probed"
    assert row["score"] is None


def test_the_cost_table_is_priced_per_cell_not_per_tier(real):
    """A tier that bought zero successful actions on a game has no price."""
    cells = real["section_4_no_budget_reached_the_level_1_baseline"][
        "cell_cost_to_reach_baseline"]
    # opus bought 0 successful actions on tn36 across 2 runs costing $1.88.
    assert cells["tn36-ef4dde99 x claude-opus-5"]["usd"] is None
    assert "0 successful actions" in cells["tn36-ef4dde99 x claude-opus-5"]["why"]
    # ...while the same tier on g50t is priced, and differs from the tn36 cell,
    # which a per-tier price could not express.
    assert cells["g50t-5849a774 x claude-opus-5"]["usd"] is not None
    haiku = {c: v["usd_per_action"] for c, v in cells.items()
             if c.endswith("claude-haiku-4-5-20251001") and v["usd"] is not None}
    assert len(set(haiku.values())) > 1, \
        "every game got the same $/action -- the table is pooled by tier again"
