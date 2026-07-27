"""Process 1 — discriminative power on a known capability gradient.

`Theoria.md`: *每个候选指标必须在已知能力梯度上拉开差距(CC vs Schema，效应量
入册)——分不开已知差异的指标，没资格测未知差异。* And the validation must use
the control arms only, never Theoria, so the battery cannot be tuned into
flattering the framework it is meant to test.

**The specified gradient does not exist.** `baseline-arms/SCHEMA_LOCATE.md`
establishes that the Schema harness was never released, so there is no
`schema_repro` arm to contrast `bare_cc` against and there may never be one.

v0 substitutes the **model ladder inside `bare_cc`** — haiku-4.5 < sonnet-5 <
opus-5, same harness, same prompt, same games. It is a weaker gradient and
`DECISIONS.md` D-B-004 says why; the two properties that matter are that it is
a capability ordering fixed independently of this battery, and that it contains
no Theoria arm.

Runs are paired by `game_id`, because `Theoria.md` Phase 4 already fixes
cross-game pairing as the confirmatory design and a metric validated under a
different design would not transfer.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from battery.audit.stats import cliffs_delta, magnitude, sign_test
from battery.metrics import REGISTRY, Value
from battery.model import Run

# The substitute gradient, weakest first.  Fixed here rather than discovered
# from the data, so no ordering can be chosen after the effect sizes are seen.
MODEL_LADDER: Tuple[str, ...] = (
    "claude-haiku-4-5-20251001",
    "claude-sonnet-5",
    "claude-opus-5",
)

MEDIUM_EFFECT = 0.33      # Cliff's delta; below this a metric is not separating


def _rung(model: Optional[str]) -> Optional[int]:
    if model is None:
        return None
    return MODEL_LADDER.index(model) if model in MODEL_LADDER else None


def _per_game_mean(runs: Sequence[Run], values: Dict[str, Dict[str, Value]],
                   metric_id: str, rung: int) -> Dict[str, float]:
    """One number per game per rung, so a game with two runs is not counted
    twice and cannot dominate a four-game sign test."""
    buckets: Dict[str, List[float]] = {}
    for run in runs:
        if _rung(run.model) != rung or run.game_id is None:
            continue
        value = values[run.run_id][metric_id]
        if value.ok and value.value is not None:
            buckets.setdefault(run.game_id, []).append(value.value)
    return {gid: sum(vs) / len(vs) for gid, vs in sorted(buckets.items())}


def discriminate(runs: Sequence[Run],
                 values: Dict[str, Dict[str, Value]],
                 *, arm: str = "bare_cc") -> Dict[str, object]:
    """Effect size and paired sign test for every metric, top rung vs bottom.

    Returns a verdict per metric.  `underpowered` is reported separately from
    `no-effect`: the first says the data cannot answer, the second says it did
    and the answer was no.  Collapsing them is how a thin pilot gets read as
    evidence of absence.
    """
    control = [r for r in runs if r.arm == arm and _rung(r.model) is not None]
    low, high = 0, len(MODEL_LADDER) - 1

    results: Dict[str, object] = {}
    for metric_id in sorted(REGISTRY):
        card = REGISTRY[metric_id]
        highs = _per_game_mean(control, values, metric_id, high)
        lows = _per_game_mean(control, values, metric_id, low)
        shared = sorted(set(highs) & set(lows))

        entry: Dict[str, object] = {
            "family": card.family,
            "direction": card.direction,
            "n_paired_games": len(shared),
            "games": shared,
        }

        if card.direction == "neutral":
            entry["verdict"] = "not-ranked"
            entry["note"] = "diagnostic metric; it describes a run, it does " \
                            "not rank one"
            results[metric_id] = entry
            continue

        if len(shared) < 2:
            entry["verdict"] = "no-data"
            entry["note"] = ("the ladder's top and bottom rungs share %d "
                             "game(s); nothing to pair" % len(shared))
            results[metric_id] = entry
            continue

        pairs = [(highs[g], lows[g]) for g in shared]
        delta = cliffs_delta([highs[g] for g in shared],
                             [lows[g] for g in shared])
        test = sign_test(pairs)

        # A metric declaring "lower is better" separates the ladder correctly
        # when the *more capable* rung scores lower, i.e. a negative delta.
        expected_sign = 1.0 if card.direction == "higher" else -1.0
        signed = (delta or 0.0) * expected_sign

        entry.update({
            "cliffs_delta": None if delta is None else round(delta, 9),
            "magnitude": magnitude(delta),
            "agrees_with_declared_direction": signed > 0,
            "sign_test": test,
        })

        # A large, clean effect pointing the *wrong* way is the single most
        # informative thing this pass can find, and it must not be buried under
        # "underpowered" -- a metric whose declared direction is backwards is
        # broken regardless of how many games back it.
        if abs(delta or 0.0) >= 0.474 and signed < 0:
            entry["warning"] = (
                "separates the ladder strongly (|d| = %.3f) but in the "
                "opposite direction to the one declared. Either the "
                "definition is measuring something else, or the declared "
                "direction is wrong. Do not use until resolved."
                % abs(delta or 0.0))

        if test["p_value"] is not None and test["min_attainable_p"] > 0.05:
            entry["verdict"] = "underpowered"
            entry["note"] = (
                "%d paired games cannot reach p<0.05 however cleanly the "
                "metric separates (smallest attainable two-sided p is %.4f). "
                "The effect size stands; the test does not."
                % (test["n"], test["min_attainable_p"]))
        elif abs(delta or 0.0) < MEDIUM_EFFECT:
            entry["verdict"] = "no-effect"
            entry["note"] = "effect below the medium threshold (|d| < 0.33)"
        elif signed < 0:
            entry["verdict"] = "wrong-direction"
            entry["note"] = ("the metric separates the ladder, but backwards "
                             "from its declared direction -- either the "
                             "definition or the declaration is wrong")
        else:
            entry["verdict"] = "discriminating"

        results[metric_id] = entry

    return {
        "gradient": "model ladder within %s (substitute; see module docstring)"
                    % arm,
        "ladder": list(MODEL_LADDER),
        "control_runs": len(control),
        "metrics": results,
    }


def power_note(n_games: int) -> str:
    """How many paired games the confirmatory test would actually need."""
    needed = 1
    while 2.0 / (2 ** needed) > 0.05:
        needed += 1
    return ("a two-sided sign test needs %d non-tied paired games to be able "
            "to reach p<0.05 at all; the pilot has %d"
            % (needed, n_games))
