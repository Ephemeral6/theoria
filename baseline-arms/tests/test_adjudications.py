"""The adjudication channel must not be usable as a threshold dial.

Most of these tests assert that something is *refused*. That is the point: the
module exists to let an outside ruling narrow one clause's input, and the tests
are the record that it cannot be turned into anything wider.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness import adjudications                                   # noqa: E402


def _record(**over):
    rec = {
        "kind": "degraded",
        "finding": "F-15",
        "authority": "monitor",
        "recorded_at": "2026-07-28T00:00:00Z",
        "recorded_by": "P-12",
        "game_id": "ar25-0c556536",
        "run_ids": ["bare_cc-ar25-x-1"],
        "scope": ["G4"],
        "reason": "ruled degraded, not representative",
        "evidence": ["BUDGET_REPORT.md section 11.2"],
    }
    rec.update(over)
    return rec


# ------------------------------------------------------------------- shape
def test_a_well_formed_record_validates():
    assert adjudications.validate(_record()) is not None


@pytest.mark.parametrize("missing", ["kind", "finding", "authority", "run_ids",
                                     "scope", "reason", "evidence",
                                     "recorded_at", "recorded_by"])
def test_every_field_is_required(missing):
    rec = _record()
    rec.pop(missing)
    with pytest.raises(adjudications.AdjudicationError):
        adjudications.validate(rec)


def test_unknown_kind_is_refused():
    with pytest.raises(adjudications.AdjudicationError):
        adjudications.validate(_record(kind="excused"))


def test_evidence_may_not_be_empty():
    with pytest.raises(adjudications.AdjudicationError):
        adjudications.validate(_record(evidence=[]))


# -------------------------------------------------- it cannot reach a cap
@pytest.mark.parametrize("clause", ["G1", "G1b", "G2", "G3", "G5",
                                    "G6a", "G6b", "G6c", "G7"])
def test_no_clause_but_g4_can_be_suspended(clause):
    """Spend, ratios, clocks and sealed-pile contact are out of reach."""
    with pytest.raises(adjudications.AdjudicationError) as exc:
        adjudications.validate(_record(scope=[clause]))
    assert "not suspendable" in str(exc.value)


def test_g7_is_refused_even_alongside_g4():
    with pytest.raises(adjudications.AdjudicationError):
        adjudications.validate(_record(scope=["G4", "G7"]))


def test_suspendable_holds_only_g4():
    """A guard on the allowlist itself: widening it should fail this test and
    force the widener to say so in the same diff."""
    assert adjudications.SUSPENDABLE == ("G4",)


def test_suspended_returns_nothing_for_a_clause_outside_the_allowlist(tmp_path):
    path = str(tmp_path / "adj.jsonl")
    adjudications.append(_record(), path=path)
    assert adjudications.suspended("G1", path=path) == {}


# ---------------------------------------------- it cannot absorb the future
@pytest.mark.parametrize("pattern", ["bare_cc-ar25-*", "*", "cell-?", "a[0-9]"])
def test_patterns_are_refused_as_run_ids(pattern):
    with pytest.raises(adjudications.AdjudicationError) as exc:
        adjudications.validate(_record(run_ids=[pattern]))
    assert "pattern" in str(exc.value)


def test_run_ids_may_not_be_empty():
    with pytest.raises(adjudications.AdjudicationError):
        adjudications.validate(_record(run_ids=[]))


def test_duplicate_run_ids_are_refused():
    with pytest.raises(adjudications.AdjudicationError):
        adjudications.validate(_record(run_ids=["a", "a"]))


def test_a_track_may_not_adjudicate_its_own_gate():
    with pytest.raises(adjudications.AdjudicationError) as exc:
        adjudications.validate(_record(authority="baseline-arms"))
    assert "outside reviewer" in str(exc.value)


# --------------------------------------------------------------- the file
def test_append_and_load_round_trip(tmp_path):
    path = str(tmp_path / "adj.jsonl")
    adjudications.append(_record(run_ids=["a"]), path=path)
    adjudications.append(_record(run_ids=["b", "c"]), path=path)
    assert len(adjudications.load(path)) == 2
    assert set(adjudications.suspended("G4", path=path)) == {"a", "b", "c"}


def test_append_refuses_an_invalid_record_before_writing(tmp_path):
    path = str(tmp_path / "adj.jsonl")
    with pytest.raises(adjudications.AdjudicationError):
        adjudications.append(_record(scope=["G1"]), path=path)
    assert not os.path.exists(path)


def test_revocation_puts_a_cell_back(tmp_path):
    path = str(tmp_path / "adj.jsonl")
    adjudications.append(_record(run_ids=["a", "b"]), path=path)
    adjudications.append(_record(kind="revoked", run_ids=["a"],
                                 reason="ruling withdrawn"), path=path)
    assert set(adjudications.suspended("G4", path=path)) == {"b"}


def test_load_rejects_a_hand_edited_over_reaching_line(tmp_path):
    """The file is append-only text; someone can still edit it. Reading is the
    second place the allowlist is enforced, so an edited line fails loudly at
    the next gate evaluation rather than silently suspending a spend clause."""
    path = str(tmp_path / "adj.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(_record(scope=["G1"])) + "\n")
    with pytest.raises(adjudications.AdjudicationError):
        adjudications.load(path)


def test_load_of_a_missing_file_is_empty(tmp_path):
    assert adjudications.load(str(tmp_path / "nope.jsonl")) == []


# ------------------------------------------------ the record actually on disk
def test_the_recorded_f15_ruling_is_well_formed_and_narrow():
    """The live file, not a fixture."""
    records = adjudications.load()
    f15 = [r for r in records if r["finding"] == "F-15"]
    assert f15, "F-15 has not been recorded"
    for rec in f15:
        assert rec["scope"] == ["G4"]
        assert rec["authority"] == "monitor"
        assert rec["game_id"] == "ar25-0c556536"
        assert len(rec["evidence"]) >= 3
        assert "does_not_cover" in rec
