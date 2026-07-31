"""The v0 -> v1.0 migrator, and the bit-exact replay spot check.

`LEDGER_FORMAT.md` §7 specified `upgrade_ledger.py` long before it existed and
`proxy/STATUS.md` carried the gap. These are its tests. The v0 records here are
copied field-for-field from `baseline-arms/out/shards/ledger.ar25.jsonl`; that
track's files are read, never written.
"""

import json

import pytest

from proxy.ledger import frame_hash, read_ledger
from proxy.tools.replay_spotcheck import (sessions_from_canon,
                                          sessions_from_recon, spotcheck)
from proxy.tools.upgrade_ledger import UnknownDialect, lift, upgrade_file
from proxy.tools.validate_ledger import validate_records

RUN = "bare_cc-ar25-claude-haiku-4-5-20251001-247c595a"
GAME = "ar25-0c556536"

V0_RESET = {
    "action": "RESET", "arm": "bare_cc", "available_actions": [1, 2, 3, 4, 5, 6, 7],
    "frame": [[[9, 9], [9, 9]]], "game_id": GAME, "levels_completed": 0,
    "model": "claude-haiku-4-5-20251001", "run_id": RUN, "state": "NOT_FINISHED",
    "step_idx": 0, "timestamp": "2026-07-27T18:23:14Z", "win_levels": 8,
}

V0_STEP = {
    "action": {"data": None, "id": 1}, "arm": "bare_cc",
    "available_actions": [1, 2, 3, 4, 5, 6, 7], "frame": [[[9, 8], [9, 9]]],
    "frames_returned": 1, "game_id": GAME, "http_tries": 3, "levels_completed": 0,
    "model": "claude-haiku-4-5-20251001", "run_id": RUN, "state": "NOT_FINISHED",
    "step_idx": 1, "timestamp": "2026-07-27T18:23:17Z", "win_levels": 8,
}

V0_FAILED = {
    "action": {"data": None, "id": 3}, "arm": "bare_cc", "failed": True,
    "frame": None, "game_id": GAME, "http_status": 400, "http_tries": 12,
    "model": "claude-haiku-4-5-20251001", "reason": "game %s not found" % GAME,
    "run_id": RUN, "step_idx": 3, "timestamp": "2026-07-27T18:24:58Z",
}

V0_MODEL = {
    "attempt": 1, "duration_ms": 11871, "game_id": GAME, "is_error": False,
    "model": "claude-haiku-4-5-20251001", "prompt_chars": 5005,
    "provider": "anthropic-claude-code-cli", "run_id": RUN, "step_idx": 1,
    "timestamp": "2026-07-27T18:23:14Z", "total_cost_usd": 0.0243132,
    "usage": {"input_tokens": 10, "output_tokens": 609,
              "cache_read_input_tokens": 17742},
}


def test_a_lifted_stream_validates_as_canon():
    lifted = lift([V0_RESET, V0_MODEL, V0_STEP, V0_FAILED], source="fixture")
    assert validate_records(lifted) == []


def test_the_frame_becomes_a_list_and_is_hashed():
    lifted = lift([V0_RESET], source="fixture")
    step = [r for r in lifted if r["event"] == "env_step"][0]
    assert step["frames"] == V0_RESET["frame"]
    assert step["n_frames"] == 1
    assert step["frame_hash"] == frame_hash(V0_RESET["frame"])


def test_win_levels_survives_into_the_response():
    """It is the only place the environment says how many levels a game has,
    and canon has nowhere else to put it."""
    lifted = lift([V0_RESET], source="fixture")
    step = [r for r in lifted if r["event"] == "env_step"][0]
    assert step["response"]["win_levels"] == 8
    assert step["response"]["available_actions"] == [1, 2, 3, 4, 5, 6, 7]


def test_a_failed_step_keeps_its_status_and_its_reason():
    lifted = lift([V0_RESET, V0_FAILED], source="fixture")
    failed = [r for r in lifted if r["event"] == "env_step"][-1]
    assert failed["frames"] is None and failed["n_frames"] == 0
    assert failed["http"]["status"] == 400
    assert failed["http"]["attempts"] == 12
    assert "not found" in failed["http"]["error"]
    # v0's single `failed` flag conflated a server refusal with a guard
    # refusal; the guard did not refuse this one.
    assert failed["guard"] == {"decision": "allow"}


def test_the_timestamp_is_the_original_not_the_migration_time():
    lifted = lift([V0_RESET], source="fixture")
    step = [r for r in lifted if r["event"] == "env_step"][0]
    assert step["ts"] == "2026-07-27T18:23:14.000Z"


def test_cost_does_not_survive_as_a_field_but_the_number_is_not_lost():
    lifted = lift([V0_MODEL], source="fixture")
    call = [r for r in lifted if r["event"] == "model_call"][0]
    assert "total_cost_usd" not in call and "cost_usd" not in call
    start = [r for r in lifted if r["event"] == "run_start"][0]
    assert start["lifted"]["dropped"]["total_cost_usd_v0"] == pytest.approx(0.0243132)
    assert "pricing_ref" in start["lifted"]["dropped"]["_note"]


def test_the_holes_v0_left_are_named_rather_than_papered_over():
    lifted = lift([V0_MODEL], source="fixture")
    call = [r for r in lifted if r["event"] == "model_call"][0]
    assert call["request"] is None and call["response"] is None
    start = [r for r in lifted if r["event"] == "run_start"][0]
    assert "model_call.request" in start["lifted"]["holes"]


def test_provenance_lands_on_the_run_start():
    lifted = lift([V0_RESET], source="some/path.jsonl", source_sha256="sha256:ab")
    start = [r for r in lifted if r["event"] == "run_start"][0]
    assert start["lifted"]["lifted_from"] == "baseline-arms/v0"
    assert start["lifted"]["source"] == "some/path.jsonl"
    assert start["lifted"]["source_sha256"] == "sha256:ab"
    assert start["lifted"]["migrator_version"]


def test_a_run_without_a_scorecard_says_so_rather_than_inventing_one():
    lifted = lift([V0_RESET], source="fixture")
    end = [r for r in lifted if r["event"] == "run_end"][0]
    assert end["scorecard"] is None
    assert "UNDETERMINED" in end["_note"]


def test_a_scorecard_can_be_attached_and_then_the_run_reconciles():
    from proxy import scoring
    card = {"card_id": "c1",
            "environments": [{"actions": 1, "completed": False, "id": GAME,
                              "level_count": 8, "levels_completed": 0,
                              "resets": 0,
                              "runs": [{"actions": 1, "levels_completed": 0,
                                        "guid": "g", "state": "NOT_FINISHED"}],
                              "score": 0.0}],
            "opaque": {"run_id": RUN}, "score": 0.0, "tags": [],
            "tags_scores": [], "total_actions": 1, "total_environments": 1,
            "total_environments_completed": 0, "total_levels": 8,
            "total_levels_completed": 0}
    lifted = lift([V0_RESET, V0_STEP, V0_FAILED], source="fixture",
                  scorecards={RUN: card})
    report = scoring.score_records(lifted)
    # one RESET, one successful action, one 400 -> the card billed exactly one
    assert report["ledger"]["actions_ok"] == 1
    assert report["ledger"]["actions_failed"] == 1
    assert report["verdict"] == "PASS", report["checks"]


def test_the_migrator_refuses_a_record_it_does_not_understand():
    with pytest.raises(UnknownDialect):
        lift([{"run_id": "r", "something": "else"}], source="fixture")


def test_the_migrator_refuses_to_double_lift():
    lifted = lift([V0_RESET], source="fixture")
    with pytest.raises(UnknownDialect, match="already v1.0"):
        lift(lifted, source="fixture")


def test_the_original_file_is_not_touched(tmp_path):
    src = tmp_path / "v0.jsonl"
    with open(str(src), "w", encoding="utf-8", newline="") as fh:
        for record in (V0_RESET, V0_STEP):
            fh.write(json.dumps(record, sort_keys=True) + "\n")
    before = open(str(src), "rb").read()

    report = upgrade_file(str(src), str(tmp_path / "canon.jsonl"))
    assert open(str(src), "rb").read() == before
    assert report["records_in"] == 2 and report["records_out"] == 4
    assert validate_records(read_ledger(str(tmp_path / "canon.jsonl"))) == []


def test_the_migration_is_byte_reproducible(tmp_path):
    src = tmp_path / "v0.jsonl"
    with open(str(src), "w", encoding="utf-8", newline="") as fh:
        for record in (V0_RESET, V0_MODEL, V0_STEP):
            fh.write(json.dumps(record, sort_keys=True) + "\n")
    first = upgrade_file(str(src), str(tmp_path / "a.jsonl"))
    second = upgrade_file(str(src), str(tmp_path / "b.jsonl"))
    assert first["out_sha256"] == second["out_sha256"]


# -- the replay spot check -------------------------------------------------

def _session(hashes, actions=None):
    actions = actions or (["RESET"] + ["ACTION1"] * (len(hashes) - 1))
    return [{"step_idx": i, "action": actions[i], "frame_hash": h, "ok": h is not None}
            for i, h in enumerate(hashes)]


def test_agreeing_sessions_pass():
    report = spotcheck({"a": _session(["h0", "h1", "h2"]),
                        "b": _session(["h0", "h1", "h2"])}, GAME)
    assert report["verdict"] == "PASS"
    assert report["steps_compared"] == 3
    assert report["pairwise_comparisons"] == 3


def test_one_disagreeing_frame_fails_the_spot_check():
    """The negative control. A check never seen to fail is not evidence."""
    report = spotcheck({"a": _session(["h0", "h1"]),
                        "b": _session(["h0", "hX"])}, GAME)
    assert report["verdict"] == "FAIL"
    assert report["disagreements"][0]["position"] == 1


def test_a_session_is_truncated_at_its_first_failure():
    """A failed step returns no frame, and what follows a lost frame is a
    different history, not a divergent replay."""
    a = _session(["h0", None, "h2"])
    b = _session(["h0", "h1", "hZ"])
    report = spotcheck({"a": a, "b": b}, GAME)
    assert report["steps_compared"] == 1        # only the shared RESET survives
    assert report["verdict"] == "PASS"


def test_one_session_alone_proves_nothing():
    report = spotcheck({"a": _session(["h0", "h1"])}, GAME)
    assert report["verdict"] == "INSUFFICIENT"


def test_comparison_stops_where_the_sessions_stop_issuing_the_same_command():
    a = _session(["h0", "h1", "h2"], ["RESET", "ACTION1", "ACTION2"])
    b = _session(["h0", "h1", "hZ"], ["RESET", "ACTION1", "ACTION5"])
    report = spotcheck({"a": a, "b": b}, GAME)
    assert report["steps_compared"] == 2
    assert report["verdict"] == "PASS"


def test_the_spot_check_reads_a_canonical_ledger(tmp_path):
    from proxy.ledger import Ledger, RunLedger
    path = str(tmp_path / "l.jsonl")
    ledger = Ledger(path)
    for run_id in ("r-one", "r-two"):
        run = RunLedger(ledger, run_id, "bare_cc", game_id=GAME)
        run.env_step(GAME, {"name": "RESET", "id": None, "data": None},
                     frames=[[[1]]], http={"status": 200})
        run.env_step(GAME, {"name": "ACTION1", "id": 1, "data": None},
                     frames=[[[2]]], http={"status": 200})
    report = spotcheck(sessions_from_canon(path, GAME), GAME)
    assert report["verdict"] == "PASS"
    assert report["n_sessions"] == 2 and report["steps_compared"] == 2


# -- the recon adapter's pass splitting ------------------------------------

def _recon_row(name, note, status=200, frame=None):
    url = "https://three.arcprize.org/api/cmd/" + name
    body = None if frame is None else {"frame": frame}
    return {"url": url, "note": note, "status": status,
            "request_body": {"game_id": GAME}, "response_body": body}


def _write_recon(tmp_path, rows):
    path = str(tmp_path / "recon.jsonl")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    return path


def test_a_single_pass_label_keeps_its_plain_name(tmp_path):
    """The ar25 shape: one successful RESET per label. The archived ar25
    spot check named these `recon/run-a`, and that must not move."""
    path = _write_recon(tmp_path, [
        _recon_row("RESET", "precheck RESET %s run-a attempt 0" % GAME,
                   frame=[[[1]]]),
        _recon_row("ACTION1", "precheck ACTION1 #0 %s run-a attempt 0" % GAME,
                   frame=[[[2]]]),
    ])
    sessions = sessions_from_recon(path, GAME)
    assert sorted(sessions) == ["recon/run-a"]
    assert [s["action"] for s in sessions["recon/run-a"]] == ["RESET", "ACTION1"]


def test_each_successful_reset_opens_a_new_pass(tmp_path):
    """The g50t shape: aborted passes and a later partial pass share one
    label. Folding them into one session would stack two RESETs at position
    0 and interleave two sweeps -- a fabricated disagreement. Split, each
    pass is a clean replay of the opening."""
    path = _write_recon(tmp_path, [
        # pass 1: RESET succeeded, the first action then failed -- aborted.
        _recon_row("RESET", "precheck RESET %s run-a attempt 3" % GAME,
                   frame=[[[1]]]),
        _recon_row("ACTION1", "precheck ACTION1 #0 %s run-a attempt 0" % GAME,
                   status=400),
        # pass 2: a complete short sweep.
        _recon_row("RESET", "precheck RESET %s run-a attempt 0 (full id)" % GAME,
                   frame=[[[1]]]),
        _recon_row("ACTION1", "precheck ACTION1 #0 %s run-a attempt 1 (full id)" % GAME,
                   frame=[[[2]]]),
        _recon_row("ACTION2", "precheck ACTION2 #1 %s run-a attempt 0 (full id)" % GAME,
                   frame=[[[3]]]),
    ])
    sessions = sessions_from_recon(path, GAME)
    assert sorted(sessions) == ["recon/run-a", "recon/run-a#2"]
    assert [s["action"] for s in sessions["recon/run-a"]] == ["RESET"]
    assert [s["action"] for s in sessions["recon/run-a#2"]] == [
        "RESET", "ACTION1", "ACTION2"]
    # And the two passes agree at position 0, so together they are evidence.
    report = spotcheck(sessions, GAME)
    assert report["verdict"] == "PASS" and report["steps_compared"] == 1


def test_a_session_is_truncated_at_a_step_idx_hole():
    """A session whose record has holes (the g50t precheck's short-id rows
    fail the game filter, leaving step_idx 0,1,2,6,7,8) must not slide its
    later steps into the gap: the step at step_idx 6 is not the fourth
    command, and comparing it there would fabricate a disagreement."""
    from proxy.tools.replay_spotcheck import clean_prefix
    steps = _session(["h0", "h1", "h2", "h6", "h7"])
    steps[3]["step_idx"] = 6
    steps[4]["step_idx"] = 7
    assert [s["frame_hash"] for s in clean_prefix(steps)] == ["h0", "h1", "h2"]


def test_a_hole_would_otherwise_read_as_a_disagreement():
    """The negative control for the contiguity rule: with the hole collapsed
    by position, the same two honest sessions would FAIL."""
    a = _session(["h0", "h1", "h2", "h3"])
    b = _session(["h0", "h1", "h2", "hX"])   # hX really sits at step_idx 6
    b[3]["step_idx"] = 6
    report = spotcheck({"a": a, "b": b}, GAME)
    assert report["verdict"] == "PASS"
    assert report["steps_compared"] == 3


def test_an_action_with_no_successful_reset_is_dropped(tmp_path):
    """An action that no successful RESET precedes has no history to sit in.
    Attaching it anywhere would invent one."""
    path = _write_recon(tmp_path, [
        _recon_row("RESET", "precheck RESET %s run-b attempt 0" % GAME,
                   status=400),
        _recon_row("ACTION1", "precheck ACTION1 #0 %s run-b attempt 1" % GAME,
                   frame=[[[2]]]),
    ])
    assert sessions_from_recon(path, GAME) == {}
