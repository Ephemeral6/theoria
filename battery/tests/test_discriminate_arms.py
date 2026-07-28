"""Process 1 on the specified gradient: CC vs Schema, paired by game.

These run on hand-built `Run` objects rather than on the real material, for
the reason `test_determinism.py` gives about the live ledger and for one more:
the upstream Schema payload is gitignored, so a test that needed it would pass
on this machine and fail on a reader's.
"""

import pytest

from battery.audit.discriminate import (
    CONTROL_ARMS, HIGH_ARM, LOW_ARM, discriminate_arms,
)
from battery.metrics import REGISTRY, Value
from battery.model import Run

GAMES = ["ar25-0c556536", "g50t-5849a774", "sk48-d8078629", "tn36-ef4dde99"]


def run_for(arm, game, n=0):
    return Run(run_id="%s-%s-%d" % (arm, game, n), arm=arm, source="t",
               game_id=game, pile="dev", intent="solve")


def values_for(runs, per_run):
    """`per_run` maps run_id -> value, for every registered metric."""
    out = {}
    for run in runs:
        got = per_run.get(run.run_id)
        out[run.run_id] = {
            mid: (Value(mid, got, "ok") if got is not None
                  else Value(mid, None, "not-applicable", "test"))
            for mid in REGISTRY
        }
    return out


def build(high_by_game, low_by_game):
    runs, per_run = [], {}
    for game, value in sorted(high_by_game.items()):
        run = run_for(HIGH_ARM, game)
        runs.append(run)
        per_run[run.run_id] = value
    for game, value in sorted(low_by_game.items()):
        run = run_for(LOW_ARM, game)
        runs.append(run)
        per_run[run.run_id] = value
    return runs, values_for(runs, per_run)


def entry(result, metric_id="X1"):
    return result["metrics"][metric_id]


# ------------------------------------------------------------------ the pass

def test_a_clean_separation_in_the_declared_direction_discriminates():
    """X2 declares `higher`; the Schema side scoring higher on all four games
    is the shape process 1 is looking for."""
    runs, values = build({g: 0.9 for g in GAMES}, {g: 0.1 for g in GAMES})
    got = entry(discriminate_arms(runs, values), "X2")
    assert got["n_paired_games"] == 4
    assert got["cliffs_delta"] == 1.0
    assert got["agrees_with_declared_direction"] is True
    # Four paired games cannot reach p<0.05 however clean the split is, and
    # the verdict has to say so rather than claim a result.
    assert got["verdict"] == "underpowered"
    assert got["sign_test"]["min_attainable_p"] == pytest.approx(0.125)


def test_a_clean_separation_against_the_declared_direction_is_flagged():
    runs, values = build({g: 0.1 for g in GAMES}, {g: 0.9 for g in GAMES})
    got = entry(discriminate_arms(runs, values), "X2")
    assert got["agrees_with_declared_direction"] is False
    assert "opposite direction" in got["warning"]


def test_lower_is_better_metrics_are_scored_by_their_declared_direction():
    """X1 declares `lower`, so the stronger arm scoring *less* agrees."""
    assert REGISTRY["X1"].direction == "lower"
    runs, values = build({g: 0.1 for g in GAMES}, {g: 0.9 for g in GAMES})
    got = entry(discriminate_arms(runs, values), "X1")
    assert got["cliffs_delta"] == -1.0
    assert got["agrees_with_declared_direction"] is True
    assert "warning" not in got


def test_one_shared_game_is_no_data_not_no_effect():
    """The distinction the whole verdict vocabulary exists for: `no-data`
    says the material cannot answer, `no-effect` says it did and said no."""
    runs, values = build({GAMES[0]: 0.9}, {GAMES[1]: 0.1})
    got = entry(discriminate_arms(runs, values), "X2")
    assert got["verdict"] == "no-data"
    assert got["n_paired_games"] == 0
    assert got["n_high_games"] == 1 and got["n_low_games"] == 1


def test_identical_values_report_no_effect():
    runs, values = build({g: 0.5 for g in GAMES}, {g: 0.5 for g in GAMES})
    got = entry(discriminate_arms(runs, values), "X2")
    assert got["cliffs_delta"] == 0.0
    assert got["verdict"] == "no-effect"


def test_neutral_metrics_are_never_ranked():
    neutral = [m for m in REGISTRY if REGISTRY[m].direction == "neutral"]
    assert neutral, "the registry should carry diagnostics"
    runs, values = build({g: 0.9 for g in GAMES}, {g: 0.1 for g in GAMES})
    result = discriminate_arms(runs, values)
    for mid in neutral:
        assert result["metrics"][mid]["verdict"] == "not-ranked"


# ------------------------------------------------- the control-arm exclusion

def test_a_theoria_run_cannot_enter_the_validation_material():
    """The one way this pass could be corrupted. `Theoria.md`: 验证只用对照
    两臂，与 Theoria 无关."""
    runs, values = build({g: 0.9 for g in GAMES}, {g: 0.1 for g in GAMES})
    clean = discriminate_arms(runs, values)

    intruder = Run(run_id="theoria-x", arm="theoria_a2", source="t",
                   game_id=GAMES[0], pile="dev", intent="solve")
    runs.append(intruder)
    values[intruder.run_id] = {mid: Value(mid, 0.0, "ok") for mid in REGISTRY}

    assert discriminate_arms(runs, values) == clean
    assert "theoria_a2" not in discriminate_arms(runs, values)["arms_present"]


def test_control_arms_contains_no_theoria_arm():
    assert CONTROL_ARMS == (LOW_ARM, HIGH_ARM)
    assert not any("theoria" in arm for arm in CONTROL_ARMS)


# ---------------------------------------------------------------- provenance

def test_availability_is_reported_rather_than_assumed():
    """v0 and v1 had no Schema arm at all. A reader has to be able to tell
    which of those two worlds an artefact was computed in."""
    runs, values = build({}, {g: 0.1 for g in GAMES})
    result = discriminate_arms(runs, values)
    assert result["available"] is False
    assert result["arms_present"] == [LOW_ARM]


def test_every_run_carries_the_confounds_it_was_computed_under():
    runs, values = build({g: 0.9 for g in GAMES}, {g: 0.1 for g in GAMES})
    result = discriminate_arms(runs, values)
    joined = " ".join(result["confounds"])
    # The three that must never be dropped: harness bundling, upstream-not-ours,
    # and the licence.
    assert "harness" in joined
    assert "复现值" in joined
    assert "licence" in joined


def test_the_pass_is_deterministic_over_input_order():
    runs, values = build({g: 0.9 for g in GAMES}, {g: 0.1 for g in GAMES})
    first = discriminate_arms(runs, values)
    second = discriminate_arms(list(reversed(runs)), values)
    assert first == second
