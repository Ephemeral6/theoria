"""The canon validator, checked against inputs it must reject.

A validator that has only ever been run on conforming input is a validator
nobody has tested. Every check gets a line crafted to break it, and the file
that ships is checked at the end.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness import validate_canon as vc                             # noqa: E402


def good_env_step(**over):
    frames = [[[0, 1], [1, 0]]]
    rec = {
        "v": "1.0", "event": "env_step", "seq": 1,
        "ts": "2026-07-27T18:21:28.000Z", "run_id": "r1", "arm": "bare_cc",
        "game_id": "ar25-0c556536", "card_id": "c1", "guid": "g1", "step_idx": 1,
        "action": {"name": "ACTION2", "id": 2, "data": None},
        "frames": frames, "frame_hash": vc.sha256_of(frames), "n_frames": 1,
        "state": "NOT_FINISHED", "score": None, "levels_completed": 0,
        "level": 0, "level_boundary": False, "variant": None,
        "guard": {"decision": "allow"},
        "http": {"method": "POST", "path": "/api/cmd/ACTION2", "status": 200,
                 "elapsed_ms": None, "request_sha256": None, "attempts": 1},
    }
    rec.update(over)
    return rec


def good_model_call(**over):
    rec = {
        "v": "1.0", "event": "model_call", "seq": 1,
        "ts": "2026-07-27T18:21:28.000Z", "run_id": "r1", "arm": "bare_cc",
        "call_idx": 0, "provider": "anthropic-claude-code-cli",
        "model": "claude-haiku-4-5-20251001", "request": None, "response": None,
        "usage": {"input_tokens": 10}, "pricing_ref": None, "step_idx": 1,
        "http": {"method": None, "path": None, "status": None,
                 "elapsed_ms": 8428, "stream": None, "attempts": 1},
    }
    rec.update(over)
    return rec


def line(rec):
    return vc.canonical(rec) + "\n"


def problems(rec, strict=False):
    return vc.validate_line(line(rec), 1, strict)


def write(tmp_path, records, name="l.jsonl"):
    path = str(tmp_path / name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for r in records:
            fh.write(vc.canonical(r) + "\n")
    return path


# ------------------------------------------------------------- accepts good
def test_a_conforming_env_step_passes():
    assert problems(good_env_step()) == []


def test_a_conforming_model_call_passes():
    assert problems(good_model_call()) == []


def test_honest_nulls_are_not_errors():
    """A lift is full of them and LEDGER_FORMAT section 7 blesses that. Only
    --strict objects."""
    rec = good_env_step(guid=None, card_id=None, score=None)
    assert problems(rec) == []
    assert problems(rec, strict=True)


# ------------------------------------------------------------- byte form
def test_a_non_canonical_line_is_rejected():
    rec = good_env_step()
    pretty = json.dumps(rec, sort_keys=True, ensure_ascii=True) + "\n"  # default separators
    found = vc.validate_line(pretty, 1, False)
    assert any("byte-canonical" in p for p in found)


def test_unsorted_keys_are_rejected():
    raw = '{"v":"1.0","event":"env_step"}\n'      # v sorts after event
    assert any("byte-canonical" in p for p in vc.validate_line(raw, 1, False))


def test_keys_unsorted_at_depth_are_rejected():
    """sort_keys applies recursively; a nested object out of order is just as
    non-canonical as a top-level one, and far easier to miss."""
    raw = '{"arm":"bare_cc","event":"env_step","http":{"status":200,"method":"POST"}}\n'
    assert any("byte-canonical" in p for p in vc.validate_line(raw, 1, False))


def test_a_carriage_return_is_rejected():
    assert any("carriage return" in p
               for p in vc.validate_line(vc.canonical(good_env_step()) + "\r\n",
                                         1, False))


def test_a_line_that_is_not_json_is_rejected():
    assert any("not JSON" in p for p in vc.validate_line("{ truncated\n", 1, False))


# -------------------------------------------------------------- envelope
def test_an_unknown_version_is_rejected():
    assert any("not '1.0'" in p or "v is" in p
               for p in problems(good_env_step(v="1.1")))


def test_an_unknown_event_is_rejected():
    assert any("event" in p for p in problems(good_env_step(event="frobnicate")))


def test_an_unknown_arm_is_rejected():
    assert any("arm" in p for p in problems(good_env_step(arm="rogue_arm")))


def test_a_second_resolution_ts_is_rejected():
    """The format says millisecond precision; the lift renders .000 rather than
    dropping the field."""
    assert any("millisecond" in p
               for p in problems(good_env_step(ts="2026-07-27T18:21:28Z")))


def test_a_missing_required_field_is_rejected():
    rec = good_env_step()
    del rec["frame_hash"]
    assert any("frame_hash" in p for p in problems(rec))


# ---------------------------------------------------------- derived fields
def test_a_wrong_frame_hash_is_caught():
    assert any("frame_hash does not match" in p
               for p in problems(good_env_step(frame_hash="sha256:" + "0" * 64)))


def test_a_wrong_n_frames_is_caught():
    assert any("n_frames" in p for p in problems(good_env_step(n_frames=7)))


def test_null_frames_must_have_zero_count_and_no_hash():
    found = problems(good_env_step(frames=None, n_frames=1,
                                   frame_hash="sha256:" + "0" * 64))
    assert any("n_frames" in p for p in found)
    assert any("frame_hash is set" in p for p in found)


def test_a_denied_step_carrying_frames_is_caught():
    assert any("denied step" in p
               for p in problems(good_env_step(guard={"decision": "deny"})))


def test_a_reset_with_an_action_id_is_caught():
    assert any("RESET carries" in p
               for p in problems(good_env_step(
                   action={"name": "RESET", "id": 3, "data": None})))


def test_a_non_command_path_on_an_env_step_is_caught():
    """A request carrying no game command is env_meta, never env_step."""
    rec = good_env_step()
    rec["http"]["path"] = "/api/scorecard/close"
    assert any("not a command path" in p for p in problems(rec))


# -------------------------------------------------------- the prohibitions
def test_any_cost_shaped_key_in_a_model_call_is_rejected():
    """Bluntly, on purpose: proxy/ledger.py's own guard checks only the literal
    keys `cost` and `cost_usd`, which is how v0's `total_cost_usd` slipped past
    it in the first place."""
    for key in ("cost", "cost_usd", "total_cost_usd", "usd_cost"):
        rec = good_model_call(**{key: 0.08})
        assert any("no dollar figure" in p for p in problems(rec)), key


def test_a_cost_key_nested_deep_is_still_rejected():
    rec = good_model_call(lift={"note": "x", "cost_usd": 0.08})
    assert any("no dollar figure" in p for p in problems(rec))


def test_a_credential_header_key_is_rejected():
    for key in ("Authorization", "X-API-Key", "x-api-key"):
        rec = good_env_step(http={"headers": {key: "<redacted>"}})
        assert any("credential header" in p for p in problems(rec)), key


def test_a_sealed_game_id_fails_the_file(tmp_path):
    path = write(tmp_path, [good_env_step(game_id="ls20-9607627b")])
    result = vc.validate_file(path)
    assert not result["ok"]
    assert any("SEALED-PILE CONTACT" in p for p in result["problems"])


# ------------------------------------------------------------ file-level
def test_seq_must_be_dense_from_one(tmp_path):
    path = write(tmp_path, [good_env_step(seq=1), good_env_step(seq=3)])
    assert any("dense" in p for p in vc.validate_file(path)["problems"])


def test_ts_must_not_go_backwards(tmp_path):
    path = write(tmp_path, [good_env_step(seq=1, ts="2026-07-27T18:00:02.000Z"),
                            good_env_step(seq=2, ts="2026-07-27T18:00:01.000Z")])
    assert any("non-decreasing" in p for p in vc.validate_file(path)["problems"])


def test_the_level_carry_rule_is_enforced(tmp_path):
    """proxy/reconcile.py recomputes this and calls a disagreement an incident."""
    a = good_env_step(seq=1, levels_completed=0, level=0)
    b = good_env_step(seq=2, levels_completed=1, level=1, level_boundary=False)
    path = write(tmp_path, [a, b])
    assert any("level_boundary" in p for p in vc.validate_file(path)["problems"])


def test_a_carried_level_across_a_failed_step_is_accepted(tmp_path):
    a = good_env_step(seq=1, levels_completed=2, level=2)
    b = good_env_step(seq=2, levels_completed=None, level=2, frames=None,
                      n_frames=0, frame_hash=None)
    c = good_env_step(seq=3, levels_completed=2, level=2)
    path = write(tmp_path, [a, b, c])
    assert vc.validate_file(path)["ok"], vc.validate_file(path)["problems"]


# ---------------------------------------------------- the shipped artefact
def test_the_migrated_ledger_conforms():
    from harness import migrate_ledger as ml
    path = os.path.join(ml.MIGRATIONS_DIR, "ledger-v0-to-v1.0",
                        "ledger.canon.jsonl")
    if not os.path.exists(path):
        pytest.skip("the migration has not been run")
    result = vc.validate_file(path)
    assert result["ok"], result["problems"][:10]
    assert result["records"] == 560


def test_the_migrated_ledger_does_not_pass_strict_and_that_is_correct():
    """--strict is for a stream a live proxy wrote. A lift's nulls are recorded
    gaps, and a lift that passed strict would mean the migrator invented values."""
    from harness import migrate_ledger as ml
    path = os.path.join(ml.MIGRATIONS_DIR, "ledger-v0-to-v1.0",
                        "ledger.canon.jsonl")
    if not os.path.exists(path):
        pytest.skip("the migration has not been run")
    assert not vc.validate_file(path, strict=True)["ok"]
