import json
import os

import pytest

from proxy import LEDGER_VERSION
from proxy.ledger import (ARMS, Ledger, RunLedger, canonical, frame_hash,
                          read_ledger)
from proxy.redact import VAULT, Vault, mask


def test_lines_are_canonical_and_newline_terminated(tmp_path):
    path = str(tmp_path / "l.jsonl")
    ledger = Ledger(path)
    ledger.append("env_meta", "r1", "probe", request={"b": 1, "a": 2}, http={})

    with open(path, "rb") as fh:
        raw = fh.read()
    assert raw.endswith(b"\n")
    line = raw.decode().strip()
    assert " " not in line.split('"request"')[0]        # no spaces after separators
    assert json.loads(line) == json.loads(canonical(json.loads(line)))


def test_seq_is_dense_and_survives_reopen(tmp_path):
    path = str(tmp_path / "l.jsonl")
    first = Ledger(path)
    for _ in range(3):
        first.append("env_meta", "r1", "probe", http={})
    second = Ledger(path)                                # a new writer, same file
    second.append("env_meta", "r1", "probe", http={})

    seqs = [r["seq"] for r in read_ledger(path)]
    assert seqs == [1, 2, 3, 4]


def test_reader_rejects_an_unknown_version(tmp_path):
    path = str(tmp_path / "l.jsonl")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps({"v": "99.0", "event": "env_step", "seq": 1}) + "\n")
    with pytest.raises(ValueError, match="ledger version"):
        read_ledger(path)


def test_unknown_event_and_arm_are_refused(tmp_path):
    ledger = Ledger(str(tmp_path / "l.jsonl"))
    with pytest.raises(ValueError, match="unknown event"):
        ledger.append("something_else", "r1", "probe")
    with pytest.raises(ValueError, match="unknown arm"):
        ledger.append("env_meta", "r1", "not_an_arm", http={})


# -- the arm vocabulary ------------------------------------------------------

def test_the_ablation_arm_has_a_name_of_its_own(tmp_path):
    """D-A21-001. Registered 2026-08-01; before that there was no name for it.

    This is a denominator fix, not a cosmetic one. `append` refuses an
    unregistered `arm` outright, so an ablation arm could not write a record at
    all -- and `ablation-arm`'s D-AB-004 resolved that by shipping under
    `arm: "theoria"`, which made two of Phase 1's three arms indistinguishable
    in the stream that is supposed to demonstrate they are the same shell.

    The record has to *validate*, not merely be accepted by the writer: a name
    the writer takes and the validator rejects would be worse than no name,
    because the failure would appear one layer downstream of the change.
    """
    from proxy.tools.validate_ledger import validate_records     # noqa: PLC0415

    path = str(tmp_path / "l.jsonl")
    run = RunLedger(Ledger(path), "r-abl", "ablation", game_id="ar25-0c556536")
    run.run_start(game_id="ar25-0c556536")
    run.env_step("ar25-0c556536", {"name": "RESET", "id": None, "data": None},
                 frames=[[[0]]], http={"status": 200})

    records = read_ledger(path)
    assert [r["arm"] for r in records] == ["ablation", "ablation"]
    assert validate_records(records) == []


@pytest.mark.parametrize("arm", sorted(ARMS))
def test_every_registered_arm_writes_a_record_the_validator_accepts(tmp_path, arm):
    """The register and the validator must agree about all of it, not just the
    name added today. A name in `ARMS` that fails validation is a trap set for
    whoever adopts it next."""
    from proxy.tools.validate_ledger import validate_records     # noqa: PLC0415

    path = str(tmp_path / "l.jsonl")
    Ledger(path).append("env_meta", "r1", arm, http={})
    assert validate_records(read_ledger(path)) == []


def test_the_spelling_d_ab_004_requested_is_not_silently_accepted(tmp_path):
    """`theoria_ablate` is the name `ablation-arm` asked for; `ablation` is the
    name that was registered, and the difference is deliberate (see `ARMS`).

    Pinned so the divergence cannot be discovered at runtime by an arm that
    switched to its own requested spelling and got a hard refusal on its first
    record. It is refused, loudly, and the message says where to register it.
    """
    ledger = Ledger(str(tmp_path / "l.jsonl"))
    with pytest.raises(ValueError, match="unknown arm"):
        ledger.append("env_meta", "r1", "theoria_ablate", http={})


def test_cost_may_not_be_written_into_the_ledger(tmp_path):
    run = RunLedger(Ledger(str(tmp_path / "l.jsonl")), "r1", "probe")
    for banned in ("cost", "cost_usd", "total_cost_usd"):
        with pytest.raises(ValueError, match="not canonical") as exc:
            run.model_call("anthropic", "claude-opus-5", usage={}, **{banned: 0.01})
        # the refusal has to teach, or the next caller just renames the field
        assert "versioned price table" in str(exc.value)


def test_frame_hash_covers_the_whole_sequence():
    one = [[[0, 1], [1, 0]]]
    two = [[[0, 1], [1, 0]], [[1, 1], [0, 0]]]
    assert frame_hash(one) != frame_hash(two)
    assert frame_hash(one) == frame_hash([[[0, 1], [1, 0]]])
    assert frame_hash(None) is None


def test_level_boundaries_are_derived_from_the_step_sequence(tmp_path):
    run = RunLedger(Ledger(str(tmp_path / "l.jsonl")), "r1", "probe")
    completions = [0, 0, 1, 1, 2]
    for done in completions:
        run.env_step("g", {"name": "ACTION1", "id": 1, "data": None},
                     frames=[[[0]]], levels_completed=done)

    steps = read_ledger(str(tmp_path / "l.jsonl"))
    assert [s["level"] for s in steps] == [0, 0, 0, 1, 1]
    assert [s["level_boundary"] for s in steps] == [False, False, True, False, True]
    assert [s["step_idx"] for s in steps] == [0, 1, 2, 3, 4]


def test_a_denied_step_is_recorded_with_no_frames(tmp_path):
    run = RunLedger(Ledger(str(tmp_path / "l.jsonl")), "r1", "probe")
    run.env_step("sealed-game", {"name": "RESET", "id": None, "data": None},
                 frames=None, guard={"decision": "deny", "rule": "sealed_pile"})
    record = read_ledger(str(tmp_path / "l.jsonl"))[0]
    assert record["frames"] is None and record["n_frames"] == 0
    assert record["frame_hash"] is None
    assert record["guard"]["decision"] == "deny"


def test_a_secret_cannot_reach_the_file(tmp_path):
    secret = "sk-ant-abcdefghijklmnopqrstuvwxyz012345"
    VAULT.register(secret)
    run = RunLedger(Ledger(str(tmp_path / "l.jsonl")), "r1", "probe")
    run.env_meta(request={"body": "key=" + secret, "headers": {"X-API-Key": secret}},
                 http={})

    blob = open(str(tmp_path / "l.jsonl"), encoding="utf-8").read()
    assert secret not in blob
    assert "<redacted>" in blob


def test_sensitive_headers_are_blanked_whatever_the_value():
    vault = Vault()
    scrubbed = vault.scrub({"Authorization": "Bearer whatever", "Accept": "json"})
    assert scrubbed["Authorization"] == "<redacted>"
    assert scrubbed["Accept"] == "json"


def test_mask_is_safe_to_log():
    masked = mask("sk-ant-abcdefghijklmnopqrstuvwxyz")
    assert "abcdefgh" not in masked and masked.startswith("sk-a")


def test_version_constant_matches_the_written_records(tmp_path):
    ledger = Ledger(str(tmp_path / "l.jsonl"))
    record = ledger.append("env_meta", "r1", "probe", http={})
    assert record["v"] == LEDGER_VERSION


def test_ledger_has_no_rewrite_path():
    for forbidden in ("update", "rewrite", "delete", "truncate", "__setitem__"):
        assert not hasattr(Ledger, forbidden), (
            "%s would make the ledger not append-only" % forbidden)
    source = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "ledger.py"), encoding="utf-8").read()
    assert '"a"' in source and '"w"' not in source
