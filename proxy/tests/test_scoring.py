"""The frozen scorer, and the corpus that calibrated it.

Every check here has a companion that makes it go red (D-014): a check never
observed to fail is not evidence that anything passed.
"""

import copy
import hashlib
import json
import os

import pytest

from proxy.ledger import frame_hash
from proxy import scoring
from proxy.scoring import arc_v1

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
CORPUS = os.path.join(FIXTURES, "scorecard_corpus.json")


@pytest.fixture(scope="module")
def corpus():
    with open(CORPUS, encoding="utf-8") as fh:
        return json.load(fh)


# -- the freeze ------------------------------------------------------------

def test_the_scorer_hashes_to_its_freeze_record():
    fingerprint = scoring.verify_frozen()
    assert fingerprint["id"] == "arc_v1"
    assert fingerprint["sha256"].startswith("sha256:")


def test_an_edited_scorer_refuses_to_score(tmp_path):
    """The negative control. A freeze that has never been seen to fire is a
    comment."""
    frozen = copy.deepcopy(scoring.load_frozen())
    frozen["scorers"]["arc_v1"]["sha256"] = "sha256:" + "0" * 64
    path = str(tmp_path / "frozen.json")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        json.dump(frozen, fh)
    # the source lives beside the freeze record, so point it at the real one
    import shutil
    shutil.copy(os.path.join(os.path.dirname(arc_v1.__file__), "arc_v1.py"),
                str(tmp_path / "arc_v1.py"))

    with pytest.raises(scoring.ScorerDriftError, match="edited in place"):
        scoring.verify_frozen(frozen_path=path)


def test_the_freeze_record_names_the_source_it_hashes():
    record = scoring.load_frozen()["scorers"]["arc_v1"]
    assert record["source"].endswith("arc_v1.py")
    blob = open(os.path.join(os.path.dirname(arc_v1.__file__), "arc_v1.py"),
                "rb").read().replace(b"\r\n", b"\n")
    assert record["sha256"] == "sha256:" + hashlib.sha256(blob).hexdigest()


# -- the calibration, against 32 real scorecards ---------------------------

def test_total_actions_equals_successful_non_reset_commands(corpus):
    """The calibration constant, checked against every card we hold.

    baseline-arms reported this on four samples and asked that it not be used
    past its evidence. This is the same claim on 32.
    """
    disagreements = [
        (e["run_id"], e["scorecard"]["total_actions"], e["ledger"]["actions_ok"])
        for e in corpus["entries"]
        if e["scorecard"]["total_actions"] != e["ledger"]["actions_ok"]
    ]
    assert not disagreements, disagreements
    assert len(corpus["entries"]) >= 31


def test_failed_commands_really_were_present_and_still_unbilled(corpus):
    """Without failures in the corpus the previous test would be vacuous: it
    would show only that a run with no failures is billed for none of them."""
    with_failures = [e for e in corpus["entries"] if e["ledger"]["actions_failed"]]
    assert len(with_failures) >= 20
    assert sum(e["ledger"]["actions_failed"] for e in with_failures) >= 100


def test_the_corpus_is_development_pile_only(corpus):
    """A fixture that quietly carried a sealed game would poison the exam."""
    from proxy.guard import SealedPileGuard
    guard = SealedPileGuard()
    for entry in corpus["entries"]:
        for env in entry["scorecard"]["environments"]:
            assert guard.classify(env["id"]) == "dev", env["id"]


def test_every_real_card_reads_as_the_live_shape(corpus):
    for entry in corpus["entries"]:
        card = arc_v1.CardView(entry["scorecard"])
        assert card.shape == "arc_live"
        assert card.total_actions == entry["scorecard"]["total_actions"]
        assert not card.aggregate_errors, card.aggregate_errors


def test_no_card_in_the_corpus_pins_down_the_partial_credit_formula(corpus):
    """The reason `arc_v1` publishes the API's number instead of recomputing
    one. If this ever fails, a level was completed and the formula becomes
    knowable -- which is a reason to revisit the scorer, not to delete the
    test."""
    assert all(e["scorecard"]["score"] == 0.0 for e in corpus["entries"])
    assert all(e["ledger"]["levels_completed"] == 0 for e in corpus["entries"])


# -- the reconciliation battery -------------------------------------------

def _run(steps, scorecard, run_id="r-test"):
    records = []
    for i, step in enumerate(steps):
        record = {"v": "1.0", "event": "env_step", "seq": i + 1,
                  "ts": "2026-07-28T00:00:%02d.000Z" % i,
                  "run_id": run_id, "arm": "probe", "game_id": "ar25-0c556536",
                  "card_id": "card-1", "step_idx": i,
                  "action": {"name": step.get("name", "ACTION1"),
                             "id": 1, "data": None},
                  "frames": [[[0]]], "n_frames": 1,
                  "frame_hash": frame_hash([[[0]]]),
                  "state": "NOT_FINISHED", "score": None,
                  "levels_completed": step.get("levels_completed", 0),
                  "level": 0, "level_boundary": False,
                  "variant": None, "guard": {"decision": step.get("guard", "allow")},
                  "response": {"win_levels": 8},
                  "http": {"status": step.get("status", 200)}}
        records.append(record)
    records.append({"v": "1.0", "event": "run_end", "seq": len(records) + 1,
                    "ts": "2026-07-28T00:01:00.000Z", "run_id": run_id,
                    "arm": "probe",
                    "outcome": "done", "scorecard": scorecard})
    return records


def _card(total_actions=2, levels_completed=0, score=0.0, level_count=8,
          card_id="card-1", game_id="ar25-0c556536"):
    return {"card_id": card_id,
            "environments": [{"actions": total_actions, "completed": False,
                              "id": game_id, "level_count": level_count,
                              "levels_completed": levels_completed, "resets": 0,
                              "runs": [{"actions": total_actions,
                                        "levels_completed": levels_completed,
                                        "guid": "g", "state": "NOT_FINISHED"}],
                              "score": score}],
            "opaque": {}, "score": score, "tags": [], "tags_scores": [],
            "total_actions": total_actions, "total_environments": 1,
            "total_environments_completed": 0, "total_levels": level_count,
            "total_levels_completed": levels_completed}


def test_a_clean_run_passes():
    records = _run([{"name": "RESET"}, {}, {}], _card(total_actions=2))
    report = scoring.score_records(records)
    assert report["verdict"] == "PASS", report["checks"]


def test_a_billed_action_count_that_disagrees_fails():
    records = _run([{"name": "RESET"}, {}, {}], _card(total_actions=7))
    report = scoring.score_records(records)
    assert report["verdict"] == "FAIL"
    assert "S-1" in report["failed_checks"]


def test_a_refused_step_is_not_a_billed_action():
    """A guard denial is a full record with no frames. It must not count
    towards the actions the API billed -- it never reached the API."""
    records = _run([{"name": "RESET"}, {}, {"guard": "deny", "status": 403}],
                   _card(total_actions=1))
    report = scoring.score_records(records)
    assert report["verdict"] == "PASS", report["checks"]
    assert report["ledger"]["actions_refused"] == 1


def test_a_failed_400_is_not_a_billed_action():
    records = _run([{"name": "RESET"}, {}, {"status": 400}], _card(total_actions=1))
    report = scoring.score_records(records)
    assert report["verdict"] == "PASS", report["checks"]
    assert report["ledger"]["actions_failed"] == 1


def test_a_missing_scorecard_is_undetermined_not_pass():
    """baseline-arms lost 22 of 23 scorecards to a transient 404 and the loss
    was silent. Silence is the failure mode this exists to break."""
    records = _run([{"name": "RESET"}, {}], None)
    report = scoring.score_records(records)
    assert report["verdict"] == "UNDETERMINED"
    assert "S-0" in report["undetermined_checks"]


def test_a_forged_score_lands_outside_every_reading_of_it():
    records = _run([{"name": "RESET"}, {}, {}], _card(total_actions=2, score=99))
    report = scoring.score_records(records)
    assert report["verdict"] == "FAIL"
    assert "S-9" in report["failed_checks"]


def test_a_card_whose_totals_do_not_add_up_fails():
    card = _card(total_actions=2)
    card["total_actions"] = 2
    card["environments"][0]["actions"] = 5          # the sum no longer agrees
    records = _run([{"name": "RESET"}, {}, {}], card)
    report = scoring.score_records(records)
    assert report["verdict"] == "FAIL"
    assert "S-10" in report["failed_checks"]


def test_a_card_about_another_game_fails():
    records = _run([{"name": "RESET"}, {}, {}],
                   _card(total_actions=2, game_id="g50t-5849a774"))
    report = scoring.score_records(records)
    assert report["verdict"] == "FAIL"
    assert "S-4" in report["failed_checks"]


def test_a_card_the_steps_did_not_count_against_fails():
    records = _run([{"name": "RESET"}, {}, {}],
                   _card(total_actions=2, card_id="card-somebody-elses"))
    report = scoring.score_records(records)
    assert report["verdict"] == "FAIL"
    assert "S-5" in report["failed_checks"]


def test_a_level_count_disagreement_fails():
    records = _run([{"name": "RESET"}, {}, {}],
                   _card(total_actions=2, level_count=3))
    report = scoring.score_records(records)
    assert report["verdict"] == "FAIL"
    assert "S-8" in report["failed_checks"]


def test_the_level_count_comes_from_the_step_responses():
    records = _run([{"name": "RESET"}, {}, {}], _card(total_actions=2))
    report = scoring.score_records(records)
    assert report["ledger"]["level_count"] == 8
    assert report["score"]["level_count"] == 8


def test_a_second_run_end_is_a_forgery_signature():
    records = _run([{"name": "RESET"}, {}, {}], _card(total_actions=2))
    second = dict(records[-1])
    second["seq"] = 99
    second["scorecard"] = _card(total_actions=99)
    records.append(second)
    report = scoring.score_records(records)
    assert report["verdict"] == "FAIL"
    assert "S-7" in report["failed_checks"]


def test_scoring_a_run_files_an_incident_when_it_does_not_reconcile(tmp_path):
    from proxy.ledger import Ledger, read_ledger
    path = str(tmp_path / "l.jsonl")
    ledger = Ledger(path)
    for record in _run([{"name": "RESET"}, {}, {}], _card(total_actions=7)):
        fields = {k: v for k, v in record.items()
                  if k not in ("v", "event", "seq", "ts", "run_id", "arm")}
        ledger.append(record["event"], record["run_id"], record["arm"], **fields)

    report = scoring.score_run("r-test", ledger_path=path,
                               scores_dir=str(tmp_path / "scores"))
    assert report["verdict"] == "FAIL"
    incidents = [r for r in read_ledger(path) if r.get("event") == "incident"]
    assert incidents and incidents[-1]["kind"] == "score_mismatch"
    assert os.path.exists(str(tmp_path / "scores" / "r-test.json"))


def test_an_unreconcilable_run_files_its_own_kind_of_incident(tmp_path):
    from proxy.ledger import Ledger, read_ledger
    path = str(tmp_path / "l.jsonl")
    ledger = Ledger(path)
    for record in _run([{"name": "RESET"}, {}], None):
        fields = {k: v for k, v in record.items()
                  if k not in ("v", "event", "seq", "ts", "run_id", "arm")}
        ledger.append(record["event"], record["run_id"], record["arm"], **fields)

    report = scoring.score_run("r-test", ledger_path=path,
                               scores_dir=str(tmp_path / "scores"))
    assert report["verdict"] == "UNDETERMINED"
    incidents = [r for r in read_ledger(path) if r.get("event") == "incident"]
    assert incidents and incidents[-1]["kind"] == "score_unreconciled"
