"""The noise-floor instrument, checked the way it asks other things to be.

`armtools/noise_floor.py` exists to answer "how far apart do two identical legs
land?", and its answer is only worth as much as its reductions are. Four things
are worth pinning:

* `columns_of` reads the scoreboard out of a campaign document, including the
  legs that failed -- a repetition that failed a leg is not a repetition with
  fewer legs.
* `stop_signature` files off the absolute paths and timestamps that make two
  identical stops read as two different ones.
* the normaliser blanks the fields it says it blanks, **and still reports a
  real difference** -- a normaliser that smoothed everything would make the
  variation audit say "identical" forever, which is the failure mode the audit
  exists to avoid.
* the desk guard says no. That is the negative control: `install_stub_desk`
  claims no real CLI can start under it, and a claim like that is worth nothing
  until it has been seen to refuse.

Nothing here runs a campaign; the repetitions themselves are minutes long and
belong in a run directory, not in the suite.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from armtools import noise_floor as nf                # noqa: E402


def _campaign(**legs) -> dict:
    """A campaign document with one played leg and one failed one."""
    return {
        "legs": [
            {"index": 1, "game_id": "g", "slug": "20260731T000000Z-leg01",
             "usd": 1.5, "actions_ok": 40, "theorize_rounds": 3,
             "levels": {"boundaries": 1},
             "surprises": {"total": 5,
                           "by_kind": {"replay_mismatch": 4,
                                       "proof_failure": 1}},
             "run_dir": legs.get("run_dir", "/nonexistent")},
            {"index": 2, "game_id": "g", "event": "leg_failed",
             "error": "boom", "usd": 2.0},
            {"game_id": "g", "event": "game_end", "reason": "spent"},
        ],
        "stopped": legs.get("stopped"),
    }


def test_columns_count_the_failed_leg_as_a_leg():
    cols = nf.columns_of(_campaign())
    assert cols["legs_played"] == 1
    assert cols["legs_failed"] == 1          # not silently dropped
    assert cols["usd"] == pytest.approx(3.5)  # the failed leg's bound counts
    assert cols["actions_ok"] == 40
    assert cols["theorize_rounds"] == 3
    assert cols["levels_boundaries"] == 1
    assert cols["surprise.replay_mismatch"] == 4
    assert cols["surprise.proof_failure"] == 1
    assert cols["surprise.total"] == 5
    # A kind that never fired is a column reading zero, not a missing key.
    for kind in nf.SURPRISE_KINDS:
        assert "surprise.%s" % kind in cols


def test_every_declared_column_is_produced():
    cols = nf.columns_of({"legs": []})
    assert set(cols) == set(nf.COLUMNS)


def test_stop_signature_erases_what_cannot_match():
    a = _campaign(stopped={"reason": "no theory.dsl carried in from "
                                     r"C:\x\theoria-arm\runs\20260731T010203Z-leg01\books"})
    b = _campaign(stopped={"reason": "no theory.dsl carried in from "
                                     r"C:\y\theoria-arm\runs\20260731T111213Z-leg01\books"})
    assert nf.stop_signature(a) == nf.stop_signature(b)
    assert nf.stop_signature({"stopped": None}) == "ran-to-completion"


def test_normaliser_blanks_the_named_fields_and_says_which():
    seen = []
    out = nf._normalise({"utc": "2026-07-31T00:00:00Z", "keep": 7,
                         "nested": {"run_id": "r-0123456789abcdef", "n": 2}},
                        seen)
    assert out["utc"] == "<volatile>"
    assert out["nested"]["run_id"] == "<volatile>"
    assert out["keep"] == 7 and out["nested"]["n"] == 2
    assert "utc" in seen and "nested.run_id" in seen


def test_normaliser_still_sees_a_real_difference():
    """The audit's own negative control.

    A normaliser aggressive enough to hide a genuine change would make every
    repetition look identical and the whole measurement would read "the
    framework is deterministic" no matter what it did. Two documents that
    differ only in volatile fields must compare equal; two that differ in a
    scoreboard number must not.
    """
    volatile = []
    same_a = nf._normalise({"utc": "A", "count": 3}, volatile)
    same_b = nf._normalise({"utc": "B", "count": 3}, volatile)
    assert nf.diff_paths(same_a, same_b) == []

    diff_a = nf._normalise({"utc": "A", "count": 3}, volatile)
    diff_b = nf._normalise({"utc": "B", "count": 4}, volatile)
    paths = nf.diff_paths(diff_a, diff_b)
    assert paths and paths[0].startswith("count")


def test_diff_paths_reports_a_length_change():
    assert nf.diff_paths([1, 2], [1, 2, 3])[0].startswith("<root> <len 2 vs 3>")


def test_the_desk_guard_refuses(monkeypatch):
    """The negative control, in the suite as well as in the run.

    `install_stub_desk(None)` installs only the raiser, which is the state the
    `--negative-control` mode runs a whole leg under. Monkeypatched so the
    replacement cannot leak into another test in the same process -- the real
    module attribute is restored on teardown.
    """
    from harness import modelcall

    monkeypatch.setattr(modelcall, "claude_bin", modelcall.claude_bin)
    nf.install_stub_desk(None)
    with pytest.raises(nf.DeskWasNotStubbed):
        modelcall.claude_bin()


def test_the_stub_desk_returns_the_canned_reply(monkeypatch, tmp_path):
    from harness import modelcall

    books = tmp_path / "books"
    books.mkdir()
    (books / "theory.dsl").write_text("theory body\n", encoding="utf-8")
    (books / "playbook.dsl").write_text("playbook body\n", encoding="utf-8")
    reply = nf.canned_reply(str(books))
    assert "=== THEORY ===" in reply and "theory body" in reply
    assert "=== PLAYBOOK ===" in reply and "playbook body" in reply
    # `inner/theorize.py:BLOCK` is the parser this reply has to satisfy; asking
    # it directly beats asserting on a regex written twice.
    from inner.theorize import BLOCK
    found = {m.group(1) for m in BLOCK.finditer(reply)}
    assert found == {"THEORY", "PLAYBOOK", "LOG"}

    monkeypatch.setattr(modelcall, "claude_bin", modelcall.claude_bin)
    monkeypatch.setattr(modelcall.ModelDesk, "_invoke",
                        modelcall.ModelDesk._invoke)
    nf.install_stub_desk(reply)
    envelope, elapsed_ms, stderr = modelcall.ModelDesk._invoke(
        object(), "a prompt", "claude-opus-5")
    assert envelope["result"] == reply
    assert envelope["total_cost_usd"] == 0.0     # never invents dollars
    assert elapsed_ms == 0 and stderr == ""


def test_summarise_flags_a_column_that_moved():
    reps = [{"index": 1, "columns": dict.fromkeys(nf.COLUMNS, 0), "stop": "s",
             "elapsed_s": 1.0, "leg_dirs_created": []},
            {"index": 2, "columns": dict(dict.fromkeys(nf.COLUMNS, 0),
                                         theorize_rounds=1), "stop": "s",
             "elapsed_s": 1.0, "leg_dirs_created": []}]
    out = nf.summarise(reps)
    assert out["moved"] == ["theorize_rounds"]
    assert out["columns"]["theorize_rounds"]["spread"] == 1
    assert out["columns"]["actions_ok"]["deterministic"] is True
