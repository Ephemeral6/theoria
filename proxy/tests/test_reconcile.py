"""Reconciliation, re-keyed -- and the negative samples that prove it can fail.

The obligation this replaces could not be discharged. `LEDGER_FORMAT.md` §3
required the score derived from `env_step` records to equal the scorecard's, and
a live ARC command response carries no `score` field at all (INC-TA-002). A rule
nobody can satisfy leaves the gate permanently red, or -- worse and quieter --
gets skipped, and this repository has a name for both.

**The negative samples are the point of this file.** A rule that has never been
seen to fail is `check_with_no_failing_path`: a green light with nothing behind
it. So every leg of the new key gets its own red, per record *and* per run:

    actions        a duplicated step_idx        a scorecard action count that lies
    cost           a price table that moved     a declared model_call count that lies
    score_per_run  a scorecard score that contradicts its own levels

and the two quantities that are deliberately **not** compared get tests too,
because "we decided not to check this" is a claim that can also rot:

    turns             is ABSENT, does not vote, and names what would close it
    score_per_step    is surfaced, labelled not-cross-verified, and does not vote
                      -- proved by editing it and watching the verdict not move
"""

import json
import os
from typing import Any, Dict, List, Optional

import pytest

from proxy.cost import PriceTable
from proxy.ledger import Ledger, RunLedger, read_ledger
from proxy.reconcile import (RECONCILIATION_KEY, reconcile_run,
                             scorecard_score)

GAME = "ar25-0c556536"
RUN = "r-a10"


def _card(actions: int = 2, levels: int = 0, score: float = 0.0,
          level_count: int = 8) -> Dict[str, Any]:
    """The live `environments[]` shape, filled so the frozen scorer's battery
    has no complaint that is not the one under test."""
    return {"card_id": "c1",
            "environments": [{"actions": actions, "completed": False,
                              "id": GAME, "level_count": level_count,
                              "levels_completed": levels, "resets": 0,
                              "runs": [{"actions": actions,
                                        "levels_completed": levels,
                                        "guid": "g", "state": "NOT_FINISHED"}],
                              "score": score}],
            "opaque": {}, "score": score, "tags": [], "tags_scores": [],
            "total_actions": actions, "total_environments": 1,
            "total_environments_completed": 0, "total_levels": level_count,
            "total_levels_completed": levels}


def write_run(path: str, *, card: Optional[Dict[str, Any]] = None,
              model_calls: int = 2, actions: int = 2) -> None:
    """One canonical run, written through the real writer.

    Built through `RunLedger` rather than by hand because RED-40's fix means a
    hand-built stream no longer reconciles at all -- so a hand-built negative
    sample would go red for the wrong reason and prove nothing.
    """
    table = PriceTable.load()
    run = RunLedger(Ledger(path), RUN, "mock_arm", game_id=GAME)
    run.run_start(game_id=GAME, card_id="c1")
    run.env_step(GAME, {"name": "RESET", "id": None, "data": None},
                 frames=[[[0]]], card_id="c1", guid="g", levels_completed=0,
                 response={"win_levels": 8}, http={"status": 200})
    for i in range(actions):
        run.env_step(GAME, {"name": "ACTION1", "id": 1, "data": None},
                     frames=[[[i + 1]]], card_id="c1", guid="g",
                     levels_completed=0, response={"win_levels": 8},
                     http={"status": 200})
    for i in range(model_calls):
        run.model_call("anthropic", "mock-model-1", request={"m": i},
                       response={"r": i},
                       usage={"input_tokens": 10, "output_tokens": 5},
                       pricing_ref=table.reference(), step_idx=i,
                       http={"status": 200})
    run.run_end(outcome="done", steps=actions, model_calls=model_calls,
                scorecard=_card(actions=actions) if card is None else card)


def forge(src: str, dst: str, mutate) -> str:
    """Copy a ledger, letting `mutate` rewrite records on the way through.

    The chain's `prev` links are left stale on purpose: `verify_chain` is what
    catches an edited line, and the question here is whether *reconciliation*
    catches the arithmetic. A negative sample that is caught by the wrong
    mechanism does not test the mechanism it was written for.
    """
    with open(src, encoding="utf-8") as fh, \
            open(dst, "w", encoding="utf-8", newline="") as out:
        for line in fh:
            record = json.loads(line)
            record = mutate(record) or record
            out.write(json.dumps(record, sort_keys=True) + "\n")
    return dst


@pytest.fixture()
def clean(tmp_path) -> str:
    path = str(tmp_path / "ledger.jsonl")
    write_run(path)
    return path


def incidents(path: str) -> List[Dict[str, Any]]:
    return [r for r in read_ledger(path, strict=False) if r.get("event") == "incident"]


# -- the positive control --------------------------------------------------

def test_a_clean_run_reconciles_and_every_leg_agrees(clean):
    report = reconcile_run(RUN, clean, write_incident=False)
    assert report["verdict"] == "PASS", report
    assert report["reconciliation_key"] == list(RECONCILIATION_KEY)
    for leg in RECONCILIATION_KEY:
        assert report["legs"][leg]["verdict"] == "AGREE", (leg, report["legs"][leg])
    # Without this the reds below could be reds about something else.


def test_the_key_is_the_three_legs_that_are_actually_recordable():
    assert RECONCILIATION_KEY == ("actions", "cost", "score_per_run")
    assert "turns" not in RECONCILIATION_KEY, (
        "turns is not in the ledger; a leg over a field that does not exist "
        "cannot fail, and a leg that cannot fail is not a check")


# -- leg 1: actions ---------------------------------------------------------

def test_red_a_duplicated_step_idx_makes_the_action_count_disagree(clean, tmp_path):
    """Per record. One `env_step` is one ARC command, so a repeated index is
    either two records for one action or one action recorded twice."""
    seen = {"done": False}

    def mutate(record):
        if record.get("event") == "env_step" and record["step_idx"] == 2 \
                and not seen["done"]:
            seen["done"] = True
            record["step_idx"] = 1
        return record

    path = forge(clean, str(tmp_path / "dup.jsonl"), mutate)
    assert seen["done"], "the sample did not actually mutate anything"

    report = reconcile_run(RUN, path, write_incident=True)
    assert report["verdict"] == "FAIL", report
    assert report["legs"]["actions"]["verdict"] == "DISAGREE"
    assert report["legs"]["actions"]["duplicate_step_idx"] == [1]
    assert any("A-1" in p for p in report["problems"])
    assert incidents(path)[-1]["kind"] == "score_mismatch"
    assert "actions" in incidents(path)[-1]["failing_legs"]


def test_red_a_scorecard_action_count_that_lies_makes_the_leg_disagree(tmp_path):
    """Per run. The card says it billed nine actions; the ledger holds two
    successful non-RESET commands."""
    path = str(tmp_path / "ledger.jsonl")
    write_run(path, card=_card(actions=9))

    report = reconcile_run(RUN, path, write_incident=False)
    assert report["verdict"] == "FAIL", report
    assert report["legs"]["actions"]["verdict"] == "DISAGREE"
    assert report["legs"]["actions"]["card_total_actions_check"] == "FAIL"
    assert any("A-2" in p for p in report["problems"])


def test_the_action_leg_is_the_thing_that_went_red_and_not_the_others(tmp_path):
    """A red that takes the whole report with it teaches nothing about which
    quantity disagreed."""
    path = str(tmp_path / "ledger.jsonl")
    write_run(path, card=_card(actions=9))
    legs = reconcile_run(RUN, path, write_incident=False)["legs"]
    assert legs["cost"]["verdict"] == "AGREE"
    assert legs["score_per_run"]["verdict"] == "AGREE", (
        "S-1 is the card's action count; it belongs to one leg, or a reader "
        "cannot tell which quantity was wrong")


# -- leg 2: cost ------------------------------------------------------------

def test_red_a_price_table_that_moved_makes_the_cost_leg_disagree(clean, tmp_path):
    """Per record. No dollar figure is in the ledger (§5) -- what is recorded is
    `usage` plus the hash of the table in force. If that hash no longer matches
    the table on disk, the bill is not recomputable, and nothing else in the
    repository would notice."""
    def mutate(record):
        if record.get("event") == "model_call" and record.get("call_idx") == 0:
            record["pricing_ref"] = dict(record["pricing_ref"],
                                         sha256="sha256:" + "0" * 64)
        return record

    path = forge(clean, str(tmp_path / "drift.jsonl"), mutate)
    report = reconcile_run(RUN, path, write_incident=True)

    assert report["verdict"] == "FAIL", report
    assert report["legs"]["cost"]["verdict"] == "DISAGREE"
    assert report["legs"]["cost"]["price_table_drift"][0]["call_idx"] == 0
    assert any("C-1" in p for p in report["problems"])
    assert "cost" in incidents(path)[-1]["failing_legs"]
    assert report["legs"]["actions"]["verdict"] == "AGREE", (
        "the cost leg went red on its own")


def test_red_a_declared_model_call_count_that_lies_makes_the_cost_leg_disagree(
        clean, tmp_path):
    """Per run. The cost axis is a sum over `model_call` records, so a run that
    declares a different number of them has declared a different bill."""
    def mutate(record):
        if record.get("event") == "run_end":
            record["model_calls"] = 7
        return record

    path = forge(clean, str(tmp_path / "miscount.jsonl"), mutate)
    report = reconcile_run(RUN, path, write_incident=False)

    assert report["verdict"] == "FAIL", report
    assert report["legs"]["cost"]["verdict"] == "DISAGREE"
    assert report["legs"]["cost"]["declared_model_calls"] == 7
    assert report["legs"]["cost"]["model_calls"] == 2
    assert any("C-2" in p for p in report["problems"])


def test_a_bill_that_cannot_be_derived_is_INCOMPLETE_and_not_PASS(clean, tmp_path):
    """A price table that is not on disk is not a disagreement -- but it is not
    agreement either, and the distinction is the whole reason this module was
    rewritten."""
    def mutate(record):
        if record.get("event") == "model_call":
            record["pricing_ref"] = {"table": "pricing_that_never_existed",
                                     "sha256": "sha256:" + "0" * 64}
        return record

    path = forge(clean, str(tmp_path / "notable.jsonl"), mutate)
    report = reconcile_run(RUN, path, write_incident=False)

    assert report["verdict"] == "INCOMPLETE", report
    assert report["verdict"] != "PASS"
    assert report["legs"]["cost"]["verdict"] == "INCOMPLETE"
    assert report["problems"] is None, "nothing disagreed; there was nothing to compare"


def test_a_run_with_no_model_calls_says_so_rather_than_agreeing(tmp_path):
    path = str(tmp_path / "nocalls.jsonl")
    write_run(path, model_calls=0)
    leg = reconcile_run(RUN, path, write_incident=False)["legs"]["cost"]
    assert leg["verdict"] == "NOT_APPLICABLE"
    assert leg["model_calls"] == 0


def test_no_dollar_figure_is_read_out_of_the_ledger(clean):
    """The leg derives the bill; it never reads one. §5, and `canon.py` refuses
    the spellings, so a cost field in the file would be a canon violation
    before it were a reconciliation one."""
    blob = open(clean, encoding="utf-8").read()
    for spelling in ("cost_usd", "total_cost_usd", "price_usd"):
        assert spelling not in blob
    leg = reconcile_run(RUN, clean, write_incident=False)["legs"]["cost"]
    assert leg["recorded"] is False and leg["derivable"] is True
    assert leg["usd_total"] is not None


# -- leg 3: score, per run, which survives INC-TA-002 -----------------------

def test_red_a_scorecard_score_that_contradicts_its_levels_goes_red(tmp_path):
    """Per run. The per-*step* score is not cross-verifiable; the per-*run*
    score is, because `POST /api/scorecard/close` does return one. Scoping the
    INC-TA-002 label to the whole quantity would have thrown this check away."""
    path = str(tmp_path / "ledger.jsonl")
    card = _card(actions=2)
    card["score"] = 0.9
    card["environments"][0]["score"] = 0.9      # levels_completed stays 0
    write_run(path, card=card)

    report = reconcile_run(RUN, path, write_incident=False)
    assert report["verdict"] == "FAIL", report
    assert report["legs"]["score_per_run"]["verdict"] == "DISAGREE"
    assert report["legs"]["score_per_run"]["cross_verified"] is True
    assert any("S-3" in p for p in report["problems"])


def test_the_per_run_score_is_reported_as_cross_verified(clean):
    leg = reconcile_run(RUN, clean, write_incident=False)["legs"]["score_per_run"]
    assert leg["cross_verified"] is True
    assert leg["recorded"] is True
    assert "scorecard/close" in leg["source"]


# -- the two quantities that are deliberately not compared ------------------

def test_turns_is_named_as_absent_does_not_vote_and_says_what_would_fix_it(clean):
    """The requirement is not dropped and not faked. Both would be defects, and
    the second one is the defect this rewrite exists to remove."""
    report = reconcile_run(RUN, clean, write_incident=False)
    turns = report["gaps"]["turns"]
    assert turns["verdict"] == "ABSENT"
    assert turns["votes"] is False
    assert turns["recorded"] is False and turns["derivable"] is False
    assert "INPUT_FORMAT.md gap 5" in turns["detail"]
    assert "turn_idx" in turns["what_would_close_it"]
    # And it does not colour the verdict, because a missing field is a gap in
    # the format, not a defect in this run.
    assert report["verdict"] == "PASS"


def test_the_per_step_score_is_surfaced_and_labelled_not_cross_verified(clean):
    report = reconcile_run(RUN, clean, write_incident=False)
    gap = report["gaps"]["score_per_step"]
    assert gap["verdict"] == "NOT_CROSS_VERIFIABLE"
    assert gap["cross_verified"] is False
    assert gap["votes"] is False
    assert "INC-TA-002" in gap["detail"]
    # Surfaced, not dropped: under the old key for callers, and under a name
    # that states its own status for readers.
    assert "ledger_score" in report
    assert report["step_score_self_reported_not_cross_verified"] == report["ledger_score"]


def test_editing_the_per_step_score_alone_does_not_move_the_verdict(clean, tmp_path):
    """The honesty test for the label. If rewriting a self-reported number
    changed the verdict, it would not be self-reported -- something would be
    checking it, and the label would be a lie in the other direction."""
    def mutate(record):
        if record.get("event") == "env_step":
            record["score"] = 41
        return record

    path = forge(clean, str(tmp_path / "selfreport.jsonl"), mutate)
    before = reconcile_run(RUN, clean, write_incident=False)
    after = reconcile_run(RUN, path, write_incident=False)

    assert before["verdict"] == after["verdict"] == "PASS"
    assert after["step_score_self_reported_not_cross_verified"] == 41
    assert after["gaps"]["score_per_step"]["value"] == 41, (
        "the unverifiable number is still reported -- the label is on it, not "
        "instead of it")


# -- the contract shape callers depend on ----------------------------------

def test_the_verdict_vocabulary_separates_no_evidence_from_agreement(tmp_path):
    path = str(tmp_path / "empty.jsonl")
    open(path, "w", encoding="utf-8").close()
    report = reconcile_run("r-nothing", path, write_incident=False)
    assert report["verdict"] == "EMPTY"
    assert report["verdict"] != "PASS"


def test_the_report_keeps_the_keys_its_callers_read(clean):
    """`test_e2e` and `test_redteam` read these by name and are not this
    module's to edit; re-keying the obligation must not re-key the report."""
    report = reconcile_run(RUN, clean, write_incident=False)
    for key in ("run_id", "verdict", "problems", "steps", "ledger_health",
                "ledger_score", "ledger_levels_completed", "level_boundaries",
                "scorecard_score", "scorecard_shape",
                "scorecard_levels_completed", "scorer", "scorer_verdict",
                "level_field_errors"):
        assert key in report, key
    assert scorecard_score(None) is None


def test_every_leg_of_the_key_has_a_proven_failing_path():
    """The meta-assertion. Each name below is covered by a red above; this test
    fails if a leg is added to the key without one, which is how
    `check_with_no_failing_path` gets in.
    """
    proven = {"actions": (test_red_a_duplicated_step_idx_makes_the_action_count_disagree,
                          test_red_a_scorecard_action_count_that_lies_makes_the_leg_disagree),
              "cost": (test_red_a_price_table_that_moved_makes_the_cost_leg_disagree,
                       test_red_a_declared_model_call_count_that_lies_makes_the_cost_leg_disagree),
              "score_per_run": (test_red_a_scorecard_score_that_contradicts_its_levels_goes_red,)}
    assert set(proven) == set(RECONCILIATION_KEY)
    for leg, tests in proven.items():
        assert tests, leg
