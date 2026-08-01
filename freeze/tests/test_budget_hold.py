# -*- coding: utf-8 -*-
"""The freeze manifest's readiness may not outrun the programme's balance.

2026-08-01.  `freeze/BUDGET_TABLE.json` recomputes the programme's spend from
the ledgers and `remaining_measured_usd` is negative.  Item 12 of the freeze
list *is* the 预算表, and it is `blocked` today for reasons that have nothing to
do with the money -- three ⟨…⟩ placeholders that are fillable in an afternoon.
Without a hold that reads the NUMBER, filling them would flip item 12 to `ready`
and the manifest would publish a ready budget for an overdrawn programme.

Half of these are negative controls, because the whole content of a hold is that
it can be seen not to fire.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

FREEZE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FREEZE))

import build_manifest as bm  # noqa: E402


def _table(tmp_path: Path, remaining) -> Path:
    path = tmp_path / "BUDGET_TABLE.json"
    path.write_text(json.dumps({"balance": {
        "ceiling_usd": 214.9,
        "programme_measured_usd": round(214.9 - remaining, 4),
        "remaining_measured_usd": remaining,
        "remaining_nominal_usd": remaining,
    }}), encoding="utf-8", newline="\n")
    return path


def _entries(status="ready"):
    return [{"n": 12, "name": "预算表", "status": status},
            {"n": 13, "name": "每格重复数 ⟨n⟩", "status": "ready"}]


def test_a_negative_balance_overrides_a_declared_ready(tmp_path):
    state = bm.budget_state(_table(tmp_path, -35.1687))
    rows = _entries("ready")
    assert bm.apply_budget_hold(rows, state) == [12]
    assert rows[0]["status"] == "blocked"
    assert rows[0]["budget_hold"]["declared_status"] == "ready"


def test_negative_control_a_positive_balance_holds_nothing(tmp_path):
    """A hold that always fires is a hardcoded `blocked`, not a hold."""
    state = bm.budget_state(_table(tmp_path, 12.34))
    rows = _entries("ready")
    assert bm.apply_budget_hold(rows, state) == []
    assert rows[0]["status"] == "ready"
    assert "budget_hold" not in rows[0]


def test_negative_control_exactly_zero_is_not_over_ceiling(tmp_path):
    """The boundary is `< 0` and it is checked, not assumed."""
    state = bm.budget_state(_table(tmp_path, 0.0))
    assert state["over_ceiling"] is False
    assert bm.apply_budget_hold(_entries("ready"), state) == []


def test_negative_control_only_the_named_items_are_held(tmp_path):
    state = bm.budget_state(_table(tmp_path, -1.0))
    rows = _entries("ready")
    bm.apply_budget_hold(rows, state)
    assert rows[1]["status"] == "ready"
    assert "budget_hold" not in rows[1]


def test_a_missing_budget_table_is_absence_not_zero(tmp_path):
    state = bm.budget_state(tmp_path / "not_here.json")
    assert state["present"] is False
    assert state["over_ceiling"] is None
    assert bm.apply_budget_hold(_entries("ready"), state) == []
    assert "ABSENCE, not zero" in state["reading"]


def test_the_verdict_sentence_quotes_the_number_rather_than_describing_it(tmp_path):
    state = bm.budget_state(_table(tmp_path, -35.1687))
    sentence = bm._budget_sentence(state, [12])
    assert "-35.1687" in sentence
    assert "214.9" in sentence
    assert "NEGATIVE" in sentence
    assert "owner" in sentence          # the ruling on the money is not ours


def test_the_published_manifest_carries_the_hold_today():
    """The real artefact, not a fixture: this is what a reader will open."""
    manifest = json.loads((FREEZE / "MANIFEST.json").read_text(encoding="utf-8"))
    budget = manifest["budget"]
    assert budget["over_ceiling"] is True, (
        "if this ever goes False, the programme came back under its ceiling and "
        "this assertion is the thing to update -- deliberately noisy")
    assert budget["remaining_measured_usd"] < 0
    assert manifest["verdict"]["budget_held_items"] == [12]
    item12 = [e for e in manifest["entries"] if e["n"] == 12][0]
    assert item12["status"] == "blocked"
    assert item12["budget_hold"]["held"] is True
    assert manifest["verdict"]["freeze_ready"] is False


def test_the_frozen_number_is_labelled_a_floor_not_the_figure():
    """`verify.sh` [15b] is red for a moved balance, so this table is stale.

    The manifest must not present a stale overspend as *the* overspend.
    """
    manifest = json.loads((FREEZE / "MANIFEST.json").read_text(encoding="utf-8"))
    assert "FLOOR" in manifest["budget"]["reading"]
    assert "15b" in manifest["budget"]["reading"]


def test_selftest_controls_all_pass():
    proc = subprocess.run([sys.executable, str(FREEZE / "build_manifest.py"),
                           "--selftest"], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.strip().splitlines()[-1] == "8/8"


def test_the_hold_is_derived_and_not_a_word_in_the_note():
    """The reason item 12 is blocked on the money is computed, not typed.

    If someone fills PENDING_FIVE's three ⟨…⟩ and flips ITEMS[12]["status"] to
    `ready`, the published status must still be `blocked`.  That is the whole
    point of the hold and it is asserted rather than trusted.
    """
    declared = [i for i in bm.ITEMS if i["n"] == 12][0]
    assert "预算" in declared["name"]
    rows = _entries("ready")
    bm.apply_budget_hold(rows, bm.budget_state())
    assert rows[0]["status"] == "blocked"
