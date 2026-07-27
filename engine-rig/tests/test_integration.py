"""M8 acceptance: all six engines run, and the whole candidate stream validates."""

import json
import os

import pytest

from common.candidates import ENGINES, KINDS, emit, make_candidate
from common.jsonio import read_jsonl
from tools import run_all as runner
from tools.validate_candidates import validate_file, validate_row, validate_rows


@pytest.fixture(autouse=True)
def clean_environment():
    """run_all toggles env vars; do not let that leak between tests."""
    saved = {
        key: os.environ.get(key)
        for key in ("THEORIA_FIXED_TIME", "THEORIA_DETERMINISTIC_IDS")
    }
    yield
    for key, value in saved.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture(scope="module")
def full_run(tmp_path_factory):
    out = str(tmp_path_factory.mktemp("m8") / "candidates.jsonl")
    summary = runner.run_all(out_path=out, deterministic=True)
    return summary, out


# ------------------------------------------------------------ the whole run

def test_every_engine_runs_without_crashing(full_run):
    summary, _ = full_run
    assert sorted(summary["by_engine"]) == sorted(ENGINES)


def test_every_candidate_kind_is_exercised(full_run):
    summary, _ = full_run
    assert sorted(summary["by_kind"]) == sorted(KINDS)


def test_the_whole_stream_satisfies_the_frozen_schema(full_run):
    summary, out = full_run
    assert summary["errors"] == []
    assert validate_file(out) == []


def test_the_stream_is_not_empty_and_every_row_is_a_candidate(full_run):
    _, out = full_run
    rows = read_jsonl(out)
    assert len(rows) >= 20
    assert all(row["status"] == "candidate" for row in rows)


def test_no_engine_adjudicates_anything(full_run):
    """status is never anything but 'candidate' -- adjudication is not this sprint."""
    _, out = full_run
    with open(out, "r", encoding="utf-8") as fh:
        assert '"status":"candidate"' in fh.read().replace(", ", ",")


def test_each_line_is_one_json_object(full_run):
    _, out = full_run
    with open(out, "r", encoding="utf-8") as fh:
        for line in fh:
            assert isinstance(json.loads(line), dict)


def test_the_headline_results_survive_the_integration_path(full_run):
    """The engines' acceptance results, re-read off the emitted stream."""
    _, out = full_run
    rows = read_jsonl(out)
    by_engine = {}
    for row in rows:
        by_engine.setdefault(row["engine"], []).append(row)

    segmentation = by_engine["mdl_segmenter"][0]["payload"]
    assert segmentation["mdl"]["ratio"] <= 0.5

    rules = {r["payload"]["name"]: r for r in by_engine["cegis_miner"]}
    assert rules["teleport"]["evidence"]["coverage"] == "1/1"
    k, n = (int(x) for x in rules["push"]["evidence"]["coverage"].split("/"))
    assert k == n > 20

    laws = [r["payload"] for r in by_engine["zero_space"]]
    globals_ = [law for law in laws if law["scope"] == "global"]
    assert len(globals_) == 1 and globals_[0]["rendering"] == "(#R) mod 2 = 0"

    certificate = [
        r["payload"] for r in by_engine["lp_potential"] if r["kind"] == "invariant"
    ][0]
    assert certificate["conditions"] == {
        "inv_init": True,
        "inv_closed": True,
        "goal_break": True,
    }

    assert by_engine["fd_adapter"][0]["payload"]["length"] == 5
    assert by_engine["probe_frontier"][0]["payload"]["action"] == "UP"


# --------------------------------------------------------------- append-only

def test_writing_again_appends_and_never_rewrites(tmp_path):
    out = str(tmp_path / "candidates.jsonl")
    first = [
        make_candidate("zero_space", "invariant", {"n": i}, [i], "1/1",
                       timestamp="2026-07-27T00:00:00Z")
        for i in range(3)
    ]
    emit(out, first)
    with open(out, "rb") as fh:
        before = fh.readlines()

    emit(out, [make_candidate("fd_adapter", "plan", {"n": 99}, [0], "1/1",
                              timestamp="2026-07-27T00:00:00Z")])
    with open(out, "rb") as fh:
        after = fh.readlines()

    assert after[: len(before)] == before          # nothing already written moved
    assert len(after) == len(before) + 1
    assert validate_file(out) == []


def test_a_second_full_run_only_adds_lines(tmp_path):
    out = str(tmp_path / "candidates.jsonl")
    first = runner.run_all(out_path=out, deterministic=True)
    with open(out, "rb") as fh:
        before = fh.readlines()
    second = runner.run_all(out_path=out, deterministic=True)
    with open(out, "rb") as fh:
        after = fh.readlines()

    assert after[: len(before)] == before
    assert second["candidates"] == 2 * first["candidates"]
    assert validate_file(out) == []


def test_deterministic_runs_are_byte_identical(tmp_path):
    first = str(tmp_path / "a.jsonl")
    second = str(tmp_path / "b.jsonl")
    runner.run_all(out_path=first, deterministic=True)
    runner.run_all(out_path=second, deterministic=True)
    with open(first, "rb") as fh_a, open(second, "rb") as fh_b:
        assert fh_a.read() == fh_b.read()


def test_deterministic_ids_are_still_distinct(full_run):
    _, out = full_run
    ids = [row["id"] for row in read_jsonl(out)]
    assert len(set(ids)) == len(ids)


def test_default_mode_uses_real_uuids_and_a_real_timestamp(tmp_path):
    out = str(tmp_path / "candidates.jsonl")
    runner.run_all(out_path=out, deterministic=False)
    rows = read_jsonl(out)
    assert validate_file(out) == []
    assert len({row["id"] for row in rows}) == len(rows)
    assert not any(row["timestamp"] == runner.FIXED_TIME for row in rows)


# ------------------------------------------------------------- the validator

def _valid_row():
    return {
        "id": "b3f1a3a0-0000-4000-8000-000000000000",
        "engine": "zero_space",
        "kind": "invariant",
        "payload": {"a": 1},
        "evidence": {"transitions": [0, 1], "coverage": "2/2"},
        "status": "candidate",
        "timestamp": "2026-07-27T00:00:00Z",
    }


def test_the_validator_accepts_a_well_formed_row():
    assert validate_row(_valid_row()) == []


@pytest.mark.parametrize(
    "mutate,fragment",
    [
        (lambda r: r.pop("payload"), "missing key 'payload'"),
        (lambda r: r.update(extra=1), "unexpected key 'extra'"),
        (lambda r: r.update(id="not-a-uuid"), "id is not a uuid"),
        (lambda r: r.update(engine="mystery_engine"), "engine not in the frozen enum"),
        (lambda r: r.update(kind="vibes"), "kind not in the frozen enum"),
        (lambda r: r.update(payload=[1, 2]), "payload is not an object"),
        (lambda r: r.update(status="accepted"), "status must be 'candidate'"),
        (lambda r: r.update(status="rejected"), "status must be 'candidate'"),
        (lambda r: r.update(timestamp="yesterday"), "timestamp is not ISO8601"),
        (lambda r: r.update(evidence={"transitions": [0], "coverage": "lots"}),
         "coverage must be"),
        (lambda r: r.update(evidence={"transitions": [0], "coverage": "3/2"}),
         "coverage k > n"),
        (lambda r: r.update(evidence={"transitions": ["x"], "coverage": "1/1"}),
         "transitions must be a list of ints"),
        (lambda r: r.update(evidence={"transitions": [0], "coverage": "1/1", "why": "?"}),
         "unexpected evidence key"),
        (lambda r: r.update(evidence="none"), "evidence is not an object"),
    ],
)
def test_the_validator_rejects_malformed_rows(mutate, fragment):
    row = _valid_row()
    mutate(row)
    errors = validate_row(row)
    assert any(fragment in error for error in errors), errors


def test_the_validator_reports_bad_json_and_blank_lines(tmp_path):
    path = str(tmp_path / "broken.jsonl")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(_valid_row()) + "\n")
        fh.write("\n")
        fh.write("{not json}\n")
    errors = validate_file(path)
    assert any("blank line" in e for e in errors)
    assert any("not valid JSON" in e for e in errors)


def test_the_writer_refuses_unknown_engines_and_kinds():
    with pytest.raises(ValueError):
        make_candidate("not_an_engine", "invariant", {}, [], "1/1")
    with pytest.raises(ValueError):
        make_candidate("zero_space", "not_a_kind", {}, [], "1/1")


def test_validate_rows_reports_the_offending_row_index():
    rows = [_valid_row(), _valid_row()]
    rows[1]["status"] = "accepted"
    errors = validate_rows(rows)
    assert len(errors) == 1
    assert errors[0].startswith("row 1")


# ------------------------------------------------------------------- the CLI

def test_the_cli_refuses_to_append_to_an_existing_file(tmp_path, capsys):
    out = str(tmp_path / "candidates.jsonl")
    assert runner.main(["--out", out, "--deterministic"]) == 0
    assert runner.main(["--out", out, "--deterministic"]) == 2
    assert "refusing to append" in capsys.readouterr().out
    assert runner.main(["--out", out, "--deterministic", "--force"]) == 0


def test_the_cli_reports_success_and_the_counts(tmp_path, capsys):
    out = str(tmp_path / "candidates.jsonl")
    assert runner.main(["--out", out, "--deterministic"]) == 0
    printed = capsys.readouterr().out
    assert "SCHEMA    : OK" in printed
    for engine in ENGINES:
        assert engine in printed
