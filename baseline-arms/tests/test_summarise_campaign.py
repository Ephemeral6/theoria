"""The envelope table, and the two defects that bite when a second game lands.

Until P-12 the envelope had one game in it, which is exactly the shape in which
a per-game collapse and a missing degraded row are invisible. These tests exist
because nine more cells are about to be appended.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness import adjudications, summarise_campaign as sc                # noqa: E402

HAIKU = "claude-haiku-4-5-20251001"


def cell(game, rid, ok=14, failed=10, cost=0.8, outcome="budget_exhausted",
         model=HAIKU, **over):
    c = {"game_id": game, "run_id": rid, "model": model, "outcome": outcome,
         "budget": 30, "repeat": 1, "actions_ok": ok, "actions_failed": failed,
         "cost_usd": cost, "model_calls": ok + failed,
         "http_calls_gameplay": 140, "output_tokens": 40000,
         "cache_read_tokens": 600000, "cache_creation_tokens": 250000,
         "levels_completed": 0, "wall_seconds": 1100.0,
         "started": "2026-07-27T18:21:28Z", "ended": "2026-07-27T18:39:05Z"}
    c.update(over)
    return c


def three(game, prefix, oks=(11, 14, 19)):
    return [cell(game, "%s-%d" % (prefix, i), ok=v, repeat=i + 1)
            for i, v in enumerate(oks)]


def rule(tmp_path, run_ids):
    path = str(tmp_path / "adj.jsonl")
    adjudications.append({
        "kind": "degraded", "finding": "F-15", "authority": "monitor",
        "recorded_at": "2026-07-28T00:00:00Z", "recorded_by": "test",
        "game_id": "ar25-0c556536", "run_ids": list(run_ids), "scope": ["G4"],
        "reason": "ruled degraded", "evidence": ["a citation"]}, path=path)
    return path


# --------------------------------------------------------------- the collapse
def test_two_tiers_for_one_game_raise_rather_than_lose_cells():
    """Grouping is per (game, model); the result is keyed per game. Before P-12
    the second tier silently overwrote the first."""
    cells = three("g50t-5849a774", "a") + \
        [cell("g50t-5849a774", "b-1", model="claude-opus-5")]
    with pytest.raises(ValueError) as exc:
        sc.by_game(cells)
    assert "two model tiers" in str(exc.value)


def test_one_tier_across_several_games_is_fine():
    cells = three("g50t-5849a774", "a") + three("sk48-d8078629", "b")
    per_game = sc.by_game(cells)
    assert set(per_game) == {"g50t-5849a774", "sk48-d8078629"}
    assert all(g["repeats"] == 3 for g in per_game.values())


# ------------------------------------------------------------- degraded rows
def test_a_fully_adjudicated_game_is_marked_degraded(tmp_path, monkeypatch):
    cells = three("ar25-0c556536", "ar")
    monkeypatch.setattr(adjudications, "ADJUDICATIONS_PATH",
                        rule(tmp_path, [c["run_id"] for c in cells]))
    per_game = sc.by_game(cells)
    assert per_game["ar25-0c556536"]["degraded"]["finding"] == "F-15"
    assert per_game["ar25-0c556536"]["degraded"]["evidence"]


def test_a_partly_adjudicated_game_is_not_degraded(tmp_path, monkeypatch):
    """A ruling over one of three cells leaves two that are still evidence.
    Dropping the game whole would discard them."""
    cells = three("ar25-0c556536", "ar")
    monkeypatch.setattr(adjudications, "ADJUDICATIONS_PATH",
                        rule(tmp_path, [cells[0]["run_id"]]))
    assert sc.by_game(cells)["ar25-0c556536"]["degraded"] is None


def test_an_unruled_game_is_never_degraded(tmp_path, monkeypatch):
    monkeypatch.setattr(adjudications, "ADJUDICATIONS_PATH",
                        str(tmp_path / "empty.jsonl"))
    cells = three("g50t-5849a774", "g", oks=(0, 0, 0))
    for c in cells:
        c["outcome"] = "api_unusable"
    assert sc.by_game(cells)["g50t-5849a774"]["degraded"] is None


# ------------------------------------------------------- the envelope itself
def test_a_degraded_game_is_excluded_from_the_pooled_cv(tmp_path, monkeypatch):
    ar = three("ar25-0c556536", "ar", oks=(11, 14, 19))
    g50 = three("g50t-5849a774", "g", oks=(20, 21, 22))
    monkeypatch.setattr(adjudications, "ADJUDICATIONS_PATH",
                        rule(tmp_path, [c["run_id"] for c in ar]))
    per_game = sc.by_game(ar + g50)
    env = sc.envelope(per_game)
    assert env["_excluded_games"] == ["ar25-0c556536"]
    assert env["actions_ok"]["games_with_estimate"] == 1
    # the kept game's cv alone
    assert env["actions_ok"]["cv_median"] == \
        per_game["g50t-5849a774"]["metrics"]["actions_ok"]["cv"]


def test_the_cost_of_excluding_is_reported_not_asserted(tmp_path, monkeypatch):
    """Both numbers are printed, so a reader can see what the exclusion did."""
    ar = three("ar25-0c556536", "ar", oks=(11, 14, 19))
    g50 = three("g50t-5849a774", "g", oks=(20, 21, 22))
    monkeypatch.setattr(adjudications, "ADJUDICATIONS_PATH",
                        rule(tmp_path, [c["run_id"] for c in ar]))
    env = sc.envelope(sc.by_game(ar + g50))
    kept = env["actions_ok"]["cv_median"]
    both = env["actions_ok"]["cv_median_including_degraded"]
    assert both is not None and both != kept


def test_a_degraded_game_keeps_its_own_row_and_its_numbers(tmp_path, monkeypatch):
    """The money was spent and the measurements happened. Excluded from the
    aggregate is not the same as deleted."""
    ar = three("ar25-0c556536", "ar", oks=(11, 14, 19))
    monkeypatch.setattr(adjudications, "ADJUDICATIONS_PATH",
                        rule(tmp_path, [c["run_id"] for c in ar]))
    row = sc.by_game(ar)["ar25-0c556536"]
    assert row["repeats"] == 3
    assert row["metrics"]["actions_ok"]["mean"] == pytest.approx(14.6667, abs=1e-3)
    assert row["metrics"]["actions_ok"]["cv"] is not None


def test_with_every_game_degraded_the_envelope_is_empty_not_wrong(tmp_path,
                                                                  monkeypatch):
    ar = three("ar25-0c556536", "ar")
    monkeypatch.setattr(adjudications, "ADJUDICATIONS_PATH",
                        rule(tmp_path, [c["run_id"] for c in ar]))
    env = sc.envelope(sc.by_game(ar))
    assert env["actions_ok"]["games_with_estimate"] == 0
    assert env["actions_ok"]["cv_median"] is None
    assert env["actions_ok"]["cv_median_including_degraded"] is not None


# ---------------------------------------------------------------- arithmetic
def test_spread_is_the_sample_sd():
    row = sc.spread([11.0, 14.0, 19.0])
    assert row["n"] == 3
    assert row["mean"] == pytest.approx(14.6667, abs=1e-3)
    assert row["sd"] == pytest.approx(4.0415, abs=1e-3)        # n-1, not n
    assert row["cv"] == pytest.approx(0.2756, abs=1e-3)
    assert row["sem_at_n"]["1"] == row["sd"]
    assert row["sem_at_n"]["3"] == pytest.approx(row["sd"] / 3 ** 0.5, abs=1e-3)


def test_one_sample_has_no_spread():
    row = sc.spread([14.0])
    assert row["sd"] is None and row["cv"] is None
    assert "sem_at_n" not in row


def test_an_all_zero_metric_has_no_cv_rather_than_a_division_error():
    row = sc.spread([0.0, 0.0, 0.0])
    assert row["mean"] == 0.0 and row["sd"] == 0.0 and row["cv"] is None


# ------------------------------------------------------ the live envelope run
def test_the_live_summary_runs_and_marks_ar25_degraded(capsys):
    assert sc.main([]) == 0
    out = capsys.readouterr().out
    assert "ar25-0c556536" in out
    assert "DEGRADED" in out
    assert "F-15" in out
    assert "excluded as degraded" in out



# ------------------------------------------------------------- re-run mixing
def test_a_re_run_game_is_flagged_not_silently_pooled(tmp_path, monkeypatch):
    """Appending is the only write path, so re-running a game's three repeats
    gives six cells. They all count -- for a variance envelope a failed episode
    is a sample, not a mistake -- but the over-count has to be visible."""
    monkeypatch.setattr(adjudications, "ADJUDICATIONS_PATH",
                        str(tmp_path / "none.jsonl"))
    cells = three("g50t-5849a774", "a") + three("g50t-5849a774", "b")
    entry = sc.by_game(cells)["g50t-5849a774"]
    assert entry["repeats"] == 6
    assert entry["repeats_expected"] == 3
    assert entry["over_expected_repeats"]
    assert entry["metrics"]["actions_ok"]["n"] == 6      # all of them count


def test_a_game_at_protocol_repeats_is_not_flagged(tmp_path, monkeypatch):
    monkeypatch.setattr(adjudications, "ADJUDICATIONS_PATH",
                        str(tmp_path / "none.jsonl"))
    entry = sc.by_game(three("g50t-5849a774", "a"))["g50t-5849a774"]
    assert entry["over_expected_repeats"] is None
