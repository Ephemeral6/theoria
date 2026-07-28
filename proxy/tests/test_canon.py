"""The canon guard: what the writer refuses, and what the reader refuses.

F-16 ruled `proxy/LEDGER_FORMAT.md` the canon. A canon that cannot refuse is a
style guide, so each test here is one refusal -- and, following D-014, several
of them also show the refusal firing on the exact record a well-meaning caller
would have written.
"""

import json
import warnings

import pytest

from proxy import canon
from proxy.ledger import Ledger, RunLedger, read_ledger
from proxy.tools.validate_ledger import validate_records


def _run(tmp_path):
    return RunLedger(Ledger(str(tmp_path / "l.jsonl")), "r1", "probe",
                     game_id="ar25-0c556536")


# -- the two shapes: additive-safe, not closed ------------------------------
#
# These two used to assert a refusal. S9 turned the refusal into a warning,
# because the refusal cost $2.695 and a discarded reply the first time it met a
# field it had not been told about (INC-TA-006). What each one asserts now is
# the pair of things that make that safe: the record survives, and nobody has
# to notice on their own that it happened.

def test_an_undefined_field_on_env_step_is_kept_and_warned_about(tmp_path):
    run = _run(tmp_path)
    with pytest.warns(canon.UnknownField, match="my_own_idea"):
        record = run.env_step("g", {"name": "ACTION1", "id": 1, "data": None},
                              frames=[[[0]]], my_own_idea=42)
    assert record["my_own_idea"] == 42
    assert run.unknown_fields == {"env_step.my_own_idea": 1}


def test_an_undefined_field_on_model_call_is_kept_and_warned_about(tmp_path):
    run = _run(tmp_path)
    with pytest.warns(canon.UnknownField, match="latency_bucket"):
        record = run.model_call("anthropic", "m", usage={},
                                latency_bucket="fast")
    assert record["latency_bucket"] == "fast"
    assert run.unknown_fields == {"model_call.latency_bucket": 1}


def test_the_warning_says_what_to_do_about_it(tmp_path):
    """A warning nobody can act on is a warning everybody filters out."""
    run = _run(tmp_path)
    with pytest.warns(canon.UnknownField) as caught:
        run.model_call("anthropic", "m", usage={}, latency_bucket="fast")
    message = str(caught[0].message)
    assert "MODEL_CALL_FIELDS" in message        # where to add it
    assert "CONTRACT_CHANGES.md" in message      # and under what procedure
    assert "kept" in message                     # and that nothing was lost


def test_the_five_p8_fields_are_canonical_now(tmp_path):
    """INC-TA-006 exactly: `ModelDesk` sends these five, and before S9 the
    writer refused the record after the provider had been paid. They are §4
    fields now, so they do not even warn."""
    run = _run(tmp_path)
    with warnings.catch_warnings():
        warnings.simplefilter("error")           # any warning fails this test
        record = run.model_call(
            "anthropic", "claude-opus-5", usage={"input_tokens": 1},
            beat="theorize", label="sk48-rev01", transport="claude-code-cli",
            proxied=False, proxy_gap="model_proxy strips Authorization")
    assert record["beat"] == "theorize"
    assert record["proxied"] is False
    assert run.unknown_fields == {}
    assert validate_records(read_ledger(str(tmp_path / "l.jsonl"))) == []


def test_constraint_8_is_checkable_from_the_ledger(tmp_path):
    """Why `beat` is worth a field rather than a note in a prose report:
    Theoria.md constraint 8 says the large model appears at theorize and at
    probe design and nowhere else, and this is the query that decides it."""
    run = _run(tmp_path)
    for beat in ("theorize", "probe_design", "theorize", "certify"):
        run.model_call("anthropic", "m", usage={}, beat=beat)
    records = read_ledger(str(tmp_path / "l.jsonl"))
    spent_at = sorted({r["beat"] for r in records if r["event"] == "model_call"})
    assert spent_at == ["certify", "probe_design", "theorize"]   # `certify` is the violation


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


def test_an_unknown_field_is_a_notice_and_not_a_verdict(tmp_path):
    """The read-side half of S9. A stream carrying a field this reader has not
    been told about is still a valid stream; refusing it is the same mistake
    the writer used to make, one direction over -- and it lands on the frozen
    scorer, which calls the validator from S-12."""
    path = str(tmp_path / "l.jsonl")
    run = RunLedger(Ledger(path), "r1", "probe", game_id="ar25-0c556536")
    with pytest.warns(canon.UnknownField):
        run.model_call("anthropic", "m", usage={}, from_the_future="hello")
    records = read_ledger(path)

    notices = []
    problems = validate_records(records, notices=notices)
    assert problems == []                                  # verdict unaffected
    assert [n["fields"] for n in notices] == [["from_the_future"]]
    assert notices[0]["kind"] == "unknown_field"


def test_a_banned_spelling_is_still_refused_on_read_and_write(tmp_path):
    """Additive-safe is not permissive. What the closure was protecting --
    drift between two spellings of one thing, and a dollar figure in an
    append-only file -- is protected by the ban list, which did not move."""
    run = _run(tmp_path)
    with pytest.raises(canon.NonCanonicalField, match="not canonical"):
        run.model_call("anthropic", "m", usage={}, total_cost_usd=2.695)

    forged = {"v": "1.0", "event": "model_call", "seq": 1, "arm": "probe",
              "ts": "2026-01-01T00:00:00.000Z", "run_id": "r", "call_idx": 0,
              "provider": "anthropic", "model": "m", "request": {},
              "response": {}, "usage": {}, "http": {}, "cost_usd": 2.695}
    assert any(p["kind"] == "non_canonical" for p in validate_records([forged]))


def test_the_warning_can_never_become_the_refusal_it_replaced(tmp_path):
    """The trap this whole change walks into if nobody looks.

    A warning is an exception whenever the ambient filter says `error` --
    `python -W error`, `PYTHONWARNINGS=error`, a hardened CI runner, a
    `simplefilter("error")` left on by something earlier in the process. Raised
    inside the writer, that is INC-TA-006 rebuilt out of the warning that was
    supposed to replace it: same lost record, same paid call, same
    `except Exception` recording "the desk failed".
    """
    path = str(tmp_path / "l.jsonl")
    run = RunLedger(Ledger(path), "r1", "theoria", game_id="g")
    with warnings.catch_warnings():
        warnings.simplefilter("error")           # the hostile ambient filter
        record = run.model_call("anthropic", "m", usage={}, mystery=1)
    assert record["mystery"] == 1
    assert len(read_ledger(path)) == 1           # it reached disk
    assert run.unknown_fields == {"model_call.mystery": 1}   # and was noticed


def test_an_unknown_field_on_a_model_call_is_still_pattern_scrubbed(tmp_path):
    """The one hole additive-safety could have opened, closed on the way in.

    `model_call` is exempt from the key-shape pass because §4 requires
    `request` and `response` verbatim and a long run of alphanumerics there is
    ordinary model output (RED-15). A field the format has never heard of
    carries no such requirement -- and before S9 it could not reach disk at
    all, so treating it as exempt would be a *new* route for a credential the
    vault has never been told about."""
    path = str(tmp_path / "l.jsonl")
    run = RunLedger(Ledger(path), "r1", "theoria", game_id="g")
    keyish = "sk-ant-api03-" + "A" * 44
    with pytest.warns(canon.UnknownField):
        record = run.model_call(
            "anthropic", "m", usage={},
            request={"prompt": keyish},          # verbatim, by §4
            side_channel=keyish)                 # not by §4; scrubbed
    assert record["request"]["prompt"] == keyish
    assert keyish not in record["side_channel"]


def test_an_unknown_field_is_not_a_back_door_for_a_banned_one(tmp_path):
    """§5's "no dollar figure is ever written to the ledger" is a property of
    the *file* (RED-42). Additive-safety opened a second route into it: before
    S9 an unlisted field could not reach disk at all, so a price could only
    hide inside a block §4 requires verbatim. Now it could ride in on a field
    nobody has heard of, at any depth."""
    run = _run(tmp_path)
    with pytest.raises(canon.NonCanonicalField, match="back door"):
        run.model_call("anthropic", "m", usage={},
                       billing={"line_items": [{"cost_usd": 2.695}]})

    # And the pre-existing one-level scan on `usage` now goes to the bottom:
    # "one level" was never the property, it was as deep as the first attack.
    with pytest.raises(canon.NonCanonicalField, match="property of the file"):
        run.model_call("anthropic", "m",
                       usage={"detail": {"breakdown": {"cost_usd": 2.695}}})


def test_what_the_ban_list_still_does_not_catch(tmp_path):
    """Stated as a test so it cannot be mistaken for a guarantee.

    The ban is on a list of *names*. `usd_spent` is not on it, so it is
    written -- and this is not new: auxiliary payloads have always been open,
    so `run_end(usd_spent=...)` was always writable and §5 was never a semantic
    price detector. What *is* new is that the two shapes now behave like the
    auxiliaries. The fix for a name you want refused is to add it to
    `BANNED_SPELLINGS`, which CONTRACT_CHANGES.md §2 classes as a tightening
    and therefore announces."""
    run = _run(tmp_path)
    with pytest.warns(canon.UnknownField):
        record = run.model_call("anthropic", "m", usage={}, usd_spent=2.695)
    assert record["usd_spent"] == 2.695


@pytest.mark.parametrize("field,value,match", [
    ("proxied", "false", "truthiness"),
    ("proxied", 1, "must be a bool"),
    ("beat", 42, "group key"),
    ("transport", ["cli"], "must be a string"),
    ("proxy_gap", {"x": 1}, "must be a string"),
])
def test_the_five_fields_are_typed_where_a_wrong_type_would_mislead(
        tmp_path, field, value, match):
    """Documented with types in §4 and enforced with none would be worse than
    not documenting them. `bool("false")` is `True`, so an arm-written record
    would read as proxy-observed -- the completeness property one size larger
    than it is, which is precisely what `proxied` exists to prevent."""
    run = _run(tmp_path)
    with pytest.raises(canon.NonCanonicalField, match=match):
        run.model_call("anthropic", "m", usage={}, **{field: value})


def test_describe_is_the_registry_as_data():
    described = canon.describe()
    assert described["ledger_version"] == "1.0"
    assert described["additive_safe"] is True
    assert "frames" in described["shapes"]["env_step"]["fields"]
    assert "beat" in described["shapes"]["model_call"]["fields"]
    assert "frame" in described["banned_spellings"]
    # The old spelling is deprecated, not deleted: `describe()` is published
    # for readers this package cannot enumerate, and dropping a key from a
    # published surface is the tightening CONTRACT_CHANGES.md C-003 is about.
    assert described["closed_shapes"] == described["shapes"]
    json.dumps(described)                          # it has to be publishable
