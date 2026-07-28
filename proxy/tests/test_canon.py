"""The canon guard: what the writer refuses, and what the reader refuses.

F-16 ruled `proxy/LEDGER_FORMAT.md` the canon. A canon that cannot refuse is a
style guide, so each test here is one refusal -- and, following D-014, several
of them also show the refusal firing on the exact record a well-meaning caller
would have written.
"""

import json

import pytest

from proxy import canon
from proxy.ledger import Ledger, RunLedger
from proxy.tools.validate_ledger import validate_records


def _run(tmp_path):
    return RunLedger(Ledger(str(tmp_path / "l.jsonl")), "r1", "probe",
                     game_id="ar25-0c556536")


# -- the closed shapes -----------------------------------------------------

def test_an_undefined_field_on_env_step_is_refused(tmp_path):
    run = _run(tmp_path)
    with pytest.raises(canon.NonCanonicalField, match="field set is closed"):
        run.env_step("g", {"name": "ACTION1", "id": 1, "data": None},
                     frames=[[[0]]], my_own_idea=42)


def test_an_undefined_field_on_model_call_is_refused(tmp_path):
    run = _run(tmp_path)
    with pytest.raises(canon.NonCanonicalField, match="field set is closed"):
        run.model_call("anthropic", "m", usage={}, latency_bucket="fast")


def test_an_auxiliary_payload_stays_open(tmp_path):
    """§6 deliberately leaves auxiliary payloads loose: a run_start carries
    whatever a run needs to describe itself. Closing them would be a different
    decision, and it is not this one."""
    run = _run(tmp_path)
    record = run.run_start(game_id="g", anything_at_all={"deep": [1, 2]})
    assert record["anything_at_all"] == {"deep": [1, 2]}


def test_an_auxiliary_still_needs_its_required_keys(tmp_path):
    run = _run(tmp_path)
    with pytest.raises(canon.NonCanonicalField, match="must carry"):
        run.run_end(steps=3)                        # no `outcome`


def test_a_caller_may_not_set_an_envelope_field(tmp_path):
    ledger = Ledger(str(tmp_path / "l.jsonl"))
    with pytest.raises(canon.NonCanonicalField, match="envelope field"):
        ledger.append("env_meta", "r1", "probe", http={}, seq=999)


# -- the v0 spellings ------------------------------------------------------

@pytest.mark.parametrize("field,hint", [
    ("frame", "frames"),
    ("timestamp", "ts"),
    ("frames_returned", "n_frames"),
    ("win_levels", "levels_completed"),
    ("http_status", "http.status"),
    ("http_tries", "http.attempts"),
    ("duration_ms", "http.elapsed_ms"),
])
def test_a_v0_spelling_is_refused_and_names_its_replacement(tmp_path, field, hint):
    run = _run(tmp_path)
    with pytest.raises(canon.NonCanonicalField) as exc:
        run.env_step("g", {"name": "ACTION1", "id": 1, "data": None},
                     frames=[[[0]]], **{field: 1})
    message = str(exc.value)
    assert "not canonical" in message and hint in message
    assert "upgrade_ledger" in message          # the refusal points at the fix


def test_reason_is_refused_on_a_step_but_natural_on_an_auxiliary(tmp_path):
    run = _run(tmp_path)
    with pytest.raises(canon.NonCanonicalField):
        run.env_step("g", {"name": "ACTION1", "id": 1, "data": None},
                     frames=[[[0]]], reason="because")
    record = run.guard_block(rule="sealed_pile", path="/api/cmd/RESET",
                             reason="because")
    assert record["reason"] == "because"


# -- the type checks that stop a plausible wrong number --------------------

def test_a_bare_frame_written_where_a_list_belongs_is_refused(tmp_path):
    """The v0 harness wrote `frame` as one frame. One command has been observed
    returning seven, so this is an observation silently lost."""
    run = _run(tmp_path)
    with pytest.raises(canon.NonCanonicalField, match="must be a list"):
        run.env_step("g", {"name": "ACTION1", "id": 1, "data": None},
                     frames={"not": "a list"})


def test_a_boolean_score_is_not_an_int(tmp_path):
    run = _run(tmp_path)
    with pytest.raises(canon.NonCanonicalField, match="sums as 1"):
        run.env_step("g", {"name": "ACTION1", "id": 1, "data": None},
                     frames=[[[0]]], score=True)


def test_an_action_missing_a_key_is_refused(tmp_path):
    run = _run(tmp_path)
    with pytest.raises(canon.NonCanonicalField, match="action must be exactly"):
        run.env_step("g", {"name": "ACTION1", "id": 1}, frames=[[[0]]])


def test_a_guard_decision_is_required_on_every_step(tmp_path):
    run = _run(tmp_path)
    with pytest.raises(canon.NonCanonicalField, match="refusal is a record"):
        run.env_step("g", {"name": "ACTION1", "id": 1, "data": None},
                     frames=[[[0]]], guard={"verdict": "fine"})


def test_usage_must_be_an_object(tmp_path):
    run = _run(tmp_path)
    with pytest.raises(canon.NonCanonicalField, match="copied through"):
        run.model_call("anthropic", "m", usage=["input", 10])


# -- model_call carries the game the battery asked for ---------------------

def test_a_model_call_carries_its_game_without_being_asked(tmp_path):
    run = _run(tmp_path)
    record = run.model_call("anthropic", "claude-opus-5", usage={})
    assert record["game_id"] == "ar25-0c556536"


# -- the reader side -------------------------------------------------------

def test_the_validator_catches_a_forged_frame_hash():
    record = {"v": "1.0", "event": "env_step", "seq": 1, "ts": "2026-01-01T00:00:00.000Z",
              "run_id": "r", "arm": "probe", "game_id": "g", "card_id": None,
              "guid": None, "step_idx": 0,
              "action": {"name": "RESET", "id": None, "data": None},
              "frames": [[[0]]], "n_frames": 1,
              "frame_hash": "sha256:" + "0" * 64,
              "state": None, "score": None, "levels_completed": 0,
              "level": 0, "level_boundary": False, "variant": None,
              "guard": {"decision": "allow"}, "response": None,
              "http": {"status": 200}}
    problems = validate_records([record])
    assert any(p["kind"] == "frame_hash_mismatch" for p in problems)


def test_the_validator_catches_a_duplicated_seq():
    base = {"v": "1.0", "event": "env_meta", "ts": "2026-01-01T00:00:00.000Z",
            "run_id": "r", "arm": "probe", "http": {}}
    problems = validate_records([dict(base, seq=1), dict(base, seq=1)])
    assert any(p["kind"] == "duplicate_seq" for p in problems)


def test_the_validator_catches_a_level_field_that_does_not_recompute():
    step = {"v": "1.0", "event": "env_step", "seq": 1, "ts": "2026-01-01T00:00:00.000Z",
            "run_id": "r", "arm": "probe", "game_id": "g", "card_id": None,
            "guid": None, "step_idx": 0,
            "action": {"name": "RESET", "id": None, "data": None},
            "frames": None, "n_frames": 0, "frame_hash": None,
            "state": None, "score": None, "levels_completed": 0,
            "level": 5, "level_boundary": False, "variant": None,
            "guard": {"decision": "allow"}, "response": None,
            "http": {"status": 200}}
    problems = validate_records([step])
    assert any(p["kind"] == "level_does_not_recompute" for p in problems)


def test_the_validator_accepts_what_the_writer_produced(tmp_path):
    """The two directions have to agree, or the canon is two canons."""
    from proxy.ledger import read_ledger
    path = str(tmp_path / "l.jsonl")
    run = RunLedger(Ledger(path), "r1", "probe", game_id="ar25-0c556536")
    run.run_start(game_id="ar25-0c556536")
    run.env_step("ar25-0c556536", {"name": "RESET", "id": None, "data": None},
                 frames=[[[0]]], levels_completed=0)
    run.env_step("ar25-0c556536", {"name": "ACTION1", "id": 1, "data": None},
                 frames=[[[1]], [[2]]], levels_completed=1)
    run.model_call("anthropic", "claude-opus-5", usage={"input_tokens": 1})
    run.run_end(outcome="done")
    assert validate_records(read_ledger(path)) == []


def test_describe_is_the_registry_as_data():
    described = canon.describe()
    assert described["ledger_version"] == "1.0"
    assert "frames" in described["closed_shapes"]["env_step"]["fields"]
    assert "frame" in described["banned_spellings"]
    json.dumps(described)                          # it has to be publishable
