"""Negative controls for `contamination.py`'s exit code.

    cd arc-recon && python -m pytest test_contamination_gate.py

`verify.sh:53` grades this module by its exit code and nothing else. The exit
code used to be `0 if check["matches"] else 1` -- the `piles.json` hash, one of
five things this module knows. Sealed games ADDRESSED in a ledger and games in
NEEDS ADJUDICATION were computed, printed, and dropped. So the human reading the
table was told the truth and the machine holding the gate was told "clean", and
only the machine's answer gates anything.

Every check here has a negative control and a positive control. The positive
controls matter more than usual: this gate now has five ways to go red, and a
gate that goes red on a healthy tree is one somebody switches off.

**Nothing here writes to `data/`.** Each test replays the real artefacts into
pytest's `tmp_path`, appends its plant, and repoints the module's path
constants. `main()` is called without `--json` so `claim_set.json` is never
touched.
"""

import json
import os

import pytest

import contamination


# --------------------------------------------------------------- the fixtures


def _replay_log(tmp_path, monkeypatch, *extra_rows):
    """Replay the real contamination log, append rows, repoint the reader.

    Additive rather than synthetic: the plant is judged against the real
    register, so a test cannot pass by constructing a universe in which the
    thing it plants is the only fact.
    """
    path = tmp_path / "contamination_log.jsonl"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for entry in contamination.entries():
            fh.write(json.dumps(entry, sort_keys=True) + "\n")
        for row in extra_rows:
            fh.write((row if isinstance(row, str)
                      else json.dumps(row, sort_keys=True)) + "\n")
    monkeypatch.setattr(contamination, "LOG_PATH", str(path))
    return path


def _a_retained_sealed_game() -> str:
    """A sealed game currently in the claim set, so a plant against it moves it."""
    summary = contamination.claim_set()
    assert summary["claim_set"], "no sealed game is in the claim set; cannot plant"
    return summary["claim_set"][0]


def _replay_ledger(tmp_path, monkeypatch, name="recon_ledger.jsonl", *, lines=None):
    """Repoint the primary ledger at a temp copy; `lines` overrides the content."""
    data = tmp_path / name
    real = os.path.join(contamination.DATA_DIR, "recon_ledger.jsonl")
    if lines is None:
        data.write_text(open(real, encoding="utf-8").read(), encoding="utf-8")
    else:
        data.write_bytes(lines if isinstance(lines, bytes) else lines.encode())
    monkeypatch.setattr(contamination, "DATA_DIR", str(tmp_path))
    return data


# -------------------------------------------------------- the positive control


def test_the_real_tree_is_green(capsys):
    """Without this, every red below could be a stuck instrument.

    It also pins the thing the work order is careful about: `quarantined` and
    `retained_with_sensitivity_analysis` are **settled disclosures**, not
    unresolved defects. Both are non-empty on this tree today, and neither may
    turn the gate red -- a gate that fires on the system working correctly is a
    gate that gets switched off.
    """
    summary = contamination.claim_set()
    assert summary["quarantined"], "the fixture premise changed: nothing is quarantined"
    assert summary["retained_with_sensitivity_analysis"]

    verdict = contamination.gate()
    assert verdict["red"] is False, verdict["reasons"]
    assert contamination.main([]) == 0
    assert "GATE: green" in capsys.readouterr().out


# ---------------------------------------------- needs adjudication reaches out


def test_an_unrecognised_claim_state_turns_the_gate_red(tmp_path, monkeypatch):
    """A typo in `claims` used to be printed under NEEDS ADJUDICATION and then
    dropped from the exit code."""
    game = _a_retained_sealed_game()
    _replay_log(tmp_path, monkeypatch,
                {"game_id": game, "level": "filename_only",
                 "claims": "quarantined",  # not a member of CLAIM_STATES
                 "note": "S23 negative control", "t": "2026-07-29T00:00:00Z"})

    summary = contamination.claim_set()
    assert game in summary["needs_adjudication"]
    assert game not in summary["clean"]

    verdict = contamination.gate()
    assert verdict["red"] is True
    assert any("NEED ADJUDICATION" in r for r in verdict["reasons"]), verdict["reasons"]
    assert contamination.main([]) == 1, "it printed the finding and exited clean"


def test_a_materially_leaked_game_left_in_the_claim_set_turns_the_gate_red(
        tmp_path, monkeypatch):
    """Level and claim state are two independently hand-written fields."""
    game = _a_retained_sealed_game()
    _replay_log(tmp_path, monkeypatch,
                {"game_id": game, "level": contamination.MATERIAL_LEVEL,
                 "claims": "in_claim_set",
                 "note": "S23 negative control", "t": "2026-07-29T00:00:00Z"})

    summary = contamination.claim_set()
    assert game in [r["game_id"] for r in summary["retained_above_material_level"]]
    assert game in summary["needs_adjudication"]
    assert game not in summary["clean"]

    verdict = contamination.gate()
    assert verdict["red"] is True
    assert any("NEED ADJUDICATION" in r for r in verdict["reasons"]), verdict["reasons"]
    assert contamination.main([]) == 1


def test_a_quarantined_game_does_not_turn_the_gate_red(tmp_path, monkeypatch):
    """The counterpart. Registering a leak *and ruling on it* is the system
    working, and must stay green or the gate punishes honesty."""
    game = _a_retained_sealed_game()
    _replay_log(tmp_path, monkeypatch,
                {"game_id": game, "level": contamination.MATERIAL_LEVEL,
                 "claims": "quarantined_from_claims",
                 "note": "S23 positive control", "t": "2026-07-29T00:00:00Z"})

    verdict = contamination.gate()
    assert verdict["red"] is False, verdict["reasons"]
    assert contamination.main([]) == 0


# ------------------------------------------------- the register must be readable


def test_a_missing_contamination_log_turns_the_gate_red(tmp_path, monkeypatch):
    """Deleting the log was a way through this gate.

    `entries()` returned `[]`, `current_register` turned `[]` into 21 sealed
    games at `never_audited` / `in_claim_set`, and the module printed a full
    clean claim set derived from a file that is not there.
    """
    monkeypatch.setattr(contamination, "LOG_PATH", str(tmp_path / "gone.jsonl"))

    coverage = contamination.register_coverage()
    assert coverage["present"] is False and coverage["problems"]

    verdict = contamination.gate()
    assert verdict["red"] is True
    assert any("does not exist" in r for r in verdict["reasons"]), verdict["reasons"]
    assert contamination.main([]) == 1


def test_an_unparseable_register_line_turns_the_gate_red(tmp_path, monkeypatch):
    """A registration nobody can read is not a game with no registration: the
    game it names silently keeps its `never_audited` default."""
    _replay_log(tmp_path, monkeypatch, "{not json at all")

    coverage = contamination.register_coverage()
    assert any("does not parse" in p for p in coverage["problems"]), coverage

    assert contamination.gate()["red"] is True
    assert contamination.main([]) == 1


def test_an_undecodable_register_turns_the_gate_red(tmp_path, monkeypatch):
    """Non-UTF-8 bytes. `entries()` would have returned `[]` for this too."""
    path = tmp_path / "contamination_log.jsonl"
    path.write_bytes(b'{"game_id": "x", "level": "filename_only"}\n\x80\xff\n')
    monkeypatch.setattr(contamination, "LOG_PATH", str(path))

    assert contamination.register_coverage()["problems"]
    assert contamination.gate()["red"] is True
    assert contamination.main([]) == 1


def test_a_healthy_register_reports_no_problems():
    coverage = contamination.register_coverage()
    assert coverage["present"] is True
    assert coverage["problems"] == [], coverage["problems"]
    assert coverage["lines"] > 0


# ------------------------------------------------- the ledgers must be readable


def test_an_absent_primary_ledger_is_not_clean(tmp_path, monkeypatch):
    """The load-bearing sentence of the whole held-out design -- "no sealed game
    has been touched" -- used to be returned as `True` from a file that was never
    opened: `clean: not contacts` over an empty dict, printed as
    "0 calls, sealed ADDRESSED: NONE".

    `all_ledger_audit` already knew this about the *other* tracks' ledgers and
    gave this one the benefit of the doubt.
    """
    monkeypatch.setattr(contamination, "DATA_DIR", str(tmp_path))

    report = contamination.sealed_api_contacts()
    assert report["present"] is False
    assert report["clean"] is None, "an unopened ledger reported itself clean"

    verdict = contamination.gate()
    assert verdict["red"] is True
    assert any("could not be audited" in r for r in verdict["reasons"]), verdict["reasons"]
    assert contamination.main([]) == 1


def test_an_unparseable_ledger_line_is_not_clean(tmp_path, monkeypatch):
    _replay_ledger(tmp_path, monkeypatch,
                   lines='{"method": "GET", "url": "https://example/api/games"}\n'
                         'not json\n')

    report = contamination.sealed_api_contacts()
    assert report["unreadable"], "a line nothing could parse left no trace"
    assert report["clean"] is None

    assert contamination.gate()["red"] is True
    assert contamination.main([]) == 1


def test_an_undecodable_ledger_is_not_clean(tmp_path, monkeypatch):
    _replay_ledger(tmp_path, monkeypatch, lines=b'{"url": "x"}\n\x80\xfe\n')

    report = contamination.sealed_api_contacts()
    assert report["clean"] is None
    assert contamination.main([]) == 1


def test_a_readable_ledger_with_no_sealed_contact_is_clean(tmp_path, monkeypatch):
    """The positive control for the three above."""
    _replay_ledger(tmp_path, monkeypatch)
    report = contamination.sealed_api_contacts()
    assert report["present"] is True
    assert report["unreadable"] == []
    assert report["clean"] is True


def test_a_sealed_game_addressed_in_a_ledger_turns_the_gate_red(tmp_path, monkeypatch):
    """The strongest failure this module can find. It exited 0 on it.

    The planted record names a sealed id in a request URL, which is the module's
    own definition of contact. No API call is made; this is a synthetic line in a
    temp file.
    """
    sealed = contamination.piles()["sealed_pile"][0]
    _replay_ledger(
        tmp_path, monkeypatch,
        lines=json.dumps({"method": "POST",
                          "url": "https://three.arcprize.org/api/cmd/RESET",
                          "request_body": {"game_id": sealed}}) + "\n")

    report = contamination.sealed_api_contacts()
    assert report["clean"] is False
    assert sealed in report["sealed_games_contacted"]

    verdict = contamination.gate()
    assert verdict["red"] is True
    assert any("SEALED GAME ADDRESSED" in r for r in verdict["reasons"]), verdict["reasons"]
    assert contamination.main([]) == 1


def test_an_empty_scan_set_turns_the_gate_red(tmp_path, monkeypatch):
    """`all([])` is `True`.

    With every declared ledger renamed, the old `all_clean` computed a clean
    verdict over an empty scan set -- a green light for having read nothing.
    """
    monkeypatch.setattr(contamination, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(contamination, "OTHER_LEDGERS",
                        [str(tmp_path / "nope-a.jsonl"), str(tmp_path / "nope-b.jsonl")])

    cross = contamination.all_ledger_audit()
    assert cross["ledgers_scanned"] == 0
    assert cross["all_clean"] is True, "the premise of this test changed"

    verdict = contamination.gate()
    assert verdict["red"] is True
    assert any("covered nothing" in r for r in verdict["reasons"]), verdict["reasons"]


# ---------------------------------------------------- the hash still gates too


def test_a_cut_that_no_longer_hashes_turns_the_gate_red(tmp_path, monkeypatch):
    """The one condition the old exit code did carry. Widening must not drop it."""
    raw = json.loads(open(contamination.PILES_PATH, encoding="utf-8").read())
    raw["sha256"] = "0" * 64
    path = tmp_path / "piles.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    monkeypatch.setattr(contamination, "PILES_PATH", str(path))

    assert contamination.verify_piles_hash()["matches"] is False
    verdict = contamination.gate()
    assert verdict["red"] is True
    assert any("no longer hashes" in r for r in verdict["reasons"]), verdict["reasons"]
    assert contamination.main([]) == 1


# ------------------------------------------------------- the disclosed gap


def test_the_hand_written_scan_surface_is_reported_as_a_gap():
    """`OTHER_LEDGERS` is a hand-written list of two files and the repository
    holds more ledger-shaped files than that. Reported as a boolean rather than
    left in prose, because a caveat no consumer reads is not a disclosure. It
    does not turn the gate red: a permanently red gate is one nobody looks at.
    """
    verdict = contamination.gate()
    assert verdict["scan_surface_self_discovered"] is False
    assert verdict["red"] is False


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__]))
