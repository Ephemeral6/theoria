"""G4 with adjudications in play.

The property that matters is asymmetric: a ruling may narrow G4's input and
nothing else. So most of these assert that a suspended cell still shows up in
the money, and that G4 still fires on everything nobody has ruled on.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness import adjudications, run_campaign as rc                # noqa: E402

H = 3600.0
BASE = 1_800_000_000.0


def iso(epoch):
    import time
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def cell(rid, outcome, start_h=0.0, cost=0.8, **over):
    c = {
        "run_id": rid, "game_id": "ar25-0c556536",
        "model": "claude-haiku-4-5-20251001", "budget": 30, "outcome": outcome,
        "started": iso(BASE + start_h * H), "ended": iso(BASE + (start_h + 0.3) * H),
        "actions_ok": 14, "actions_failed": 10, "cost_usd": cost,
        "http_calls_gameplay": 140, "wall_seconds": 1100,
    }
    c.update(over)
    return c


def adj(tmp_path, run_ids, name="adj.jsonl"):
    path = str(tmp_path / name)
    adjudications.append({
        "kind": "degraded", "finding": "F-15", "authority": "monitor",
        "recorded_at": iso(BASE), "recorded_by": "test",
        "game_id": "ar25-0c556536", "run_ids": list(run_ids), "scope": ["G4"],
        "reason": "ruled degraded", "evidence": ["a citation"],
    }, path=path)
    return path


def empty(tmp_path):
    return str(tmp_path / "none.jsonl")


# ----------------------------------------------------------- G4 unadjudicated
def test_two_dead_cells_trip_g4(tmp_path):
    cells = [cell("a", "api_unusable"), cell("b", "api_unusable", 0.4)]
    gate = rc.evaluate_gate(cells, adjudications_path=empty(tmp_path))
    assert any(t.startswith("G4") for t in gate["tripped"])


def test_a_live_cell_between_two_dead_ones_breaks_the_streak(tmp_path):
    cells = [cell("a", "api_unusable"), cell("b", "budget_exhausted", 0.4),
             cell("c", "api_unusable", 0.8)]
    gate = rc.evaluate_gate(cells, adjudications_path=empty(tmp_path))
    assert not any(t.startswith("G4") for t in gate["tripped"])


# ------------------------------------------------------------- G4 adjudicated
def test_adjudicated_cells_do_not_trip_g4(tmp_path):
    cells = [cell("a", "api_unusable"), cell("b", "api_unusable", 0.4),
             cell("c", "api_unusable", 0.8)]
    gate = rc.evaluate_gate(cells, adjudications_path=adj(tmp_path, ["a", "b", "c"]))
    assert not any(t.startswith("G4") for t in gate["tripped"]), gate["tripped"]
    assert gate["state"] == "green", gate["tripped"]


def test_the_suspension_is_named_in_the_gate_record(tmp_path):
    cells = [cell("a", "api_unusable"), cell("b", "api_unusable", 0.4)]
    gate = rc.evaluate_gate(cells, adjudications_path=adj(tmp_path, ["a", "b"]))
    named = {s["run_id"] for s in gate["adjudicated"]}
    assert named == {"a", "b"}
    assert all(s["clause"] == "G4" and s["finding"] == "F-15"
               for s in gate["adjudicated"])


def test_a_ruling_naming_cells_that_are_not_recorded_is_not_reported(tmp_path):
    """The gate record lists suspensions that actually bit, so a stale ruling
    does not read as a live one."""
    cells = [cell("a", "budget_exhausted")]
    gate = rc.evaluate_gate(cells, adjudications_path=adj(tmp_path, ["ghost"]))
    assert gate["adjudicated"] == []


def test_new_dead_cells_still_trip_g4_after_a_ruling(tmp_path):
    """The whole point of naming run_ids one by one: the ar25 ruling must not
    protect g50t."""
    cells = [cell("a", "api_unusable"), cell("b", "api_unusable", 0.4),
             cell("g1", "api_unusable", 9.0, game_id="g50t-5849a774"),
             cell("g2", "api_unusable", 9.4, game_id="g50t-5849a774")]
    gate = rc.evaluate_gate(cells, adjudications_path=adj(tmp_path, ["a", "b"]))
    trips = [t for t in gate["tripped"] if t.startswith("G4")]
    assert trips and "g2" in trips[0]


def test_a_suspended_cell_does_not_shield_the_cells_around_it(tmp_path):
    """A suspended cell is dropped from the sequence rather than treated as a
    live cell that breaks a streak: it is not evidence in either direction."""
    cells = [cell("a", "api_unusable"), cell("x", "api_unusable", 0.4),
             cell("b", "api_unusable", 0.8)]
    gate = rc.evaluate_gate(cells, adjudications_path=adj(tmp_path, ["x"]))
    assert any(t.startswith("G4") for t in gate["tripped"])


# -------------------------------------------- the money is never adjudicated
def test_a_suspended_cell_still_counts_against_the_campaign_cap(tmp_path):
    cells = [cell("c%d" % i, "api_unusable", i * 0.4, cost=9.0) for i in range(7)]
    path = adj(tmp_path, [c["run_id"] for c in cells])
    gate = rc.evaluate_gate(cells, adjudications_path=path)
    assert gate["totals"]["cost_usd"] == 63.0
    assert any(t.startswith("G1 ") for t in gate["tripped"]), gate["tripped"]


def test_a_suspended_cell_still_counts_against_the_tier_cap(tmp_path):
    cells = [cell("c%d" % i, "api_unusable", i * 0.4, cost=3.5) for i in range(7)]
    path = adj(tmp_path, [c["run_id"] for c in cells])
    gate = rc.evaluate_gate(cells, adjudications_path=path)
    assert any(t.startswith("G1b") for t in gate["tripped"]), gate["tripped"]


def test_a_suspended_cell_still_counts_in_the_ratios(tmp_path):
    cells = [cell("a", "api_unusable", actions_ok=2, actions_failed=30),
             cell("b", "api_unusable", 0.4, actions_ok=2, actions_failed=30)]
    gate = rc.evaluate_gate(cells, adjudications_path=adj(tmp_path, ["a", "b"]))
    assert any(t.startswith("G5") for t in gate["tripped"]), gate["tripped"]
    assert gate["totals"]["actions_failed"] == 60


def test_a_suspended_cell_still_counts_in_g7(tmp_path):
    """Sealed-pile contact is not reviewable by anybody, ever."""
    cells = [cell("a", "api_unusable", game_id="ls20-9607627b")]
    gate = rc.evaluate_gate(cells, adjudications_path=adj(tmp_path, ["a"]))
    assert any("G7" in t for t in gate["tripped"])


def test_a_suspended_cell_still_counts_in_g2(tmp_path):
    cells = [cell("a", "api_unusable", cost=99.0)]
    gate = rc.evaluate_gate(cells, adjudications_path=adj(tmp_path, ["a"]))
    assert any(t.startswith("G2") for t in gate["tripped"])


# ------------------------------------------------------- the live gate record
def test_the_live_gate_is_green_and_says_why(tmp_path):
    """The actual campaign_cells.jsonl and the actual ruling, end to end."""
    gate = rc.evaluate_gate(rc.load_cells())
    assert gate["state"] == "green", gate["tripped"]
    assert len(gate["adjudicated"]) == 3
    assert all(s["finding"] == "F-15" for s in gate["adjudicated"])
    assert gate["totals"]["cost_usd"] > 2.5      # the spend is still on the books
