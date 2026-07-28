"""Process 1 — discriminative power on a known capability gradient.

`Theoria.md`: *每个候选指标必须在已知能力梯度上拉开差距(CC vs Schema，效应量
入册)——分不开已知差异的指标，没资格测未知差异。* And the validation must use
the control arms only, never Theoria, so the battery cannot be tuned into
flattering the framework it is meant to test.

**The specified gradient exists as of v2, and it is the primary pass.**
`baseline-arms/SCHEMA_PATH_A.md` landed the upstream Schema-harness
trajectories for the four development-pile games, so `discriminate_arms()`
below runs the contrast `Theoria.md` actually names: CC against Schema, paired
by game. v0 and v1 reported that this gradient did not exist; what did not
exist — and still does not — is a Schema arm *we ran ourselves*, which is a
different fact and is why `⟨复现值⟩` stays empty. See D-B-019.

The **model ladder inside `bare_cc`** — haiku-4.5 < sonnet-5 < opus-5, same
harness, same prompt, same games — is kept as the secondary pass. It was v0's
substitute (`DECISIONS.md` D-B-004) and it survives because it is a within-arm
gradient: it holds the harness fixed and so separates capability from
plumbing, which the cross-arm pass cannot.

Both passes pair by `game_id`, because `Theoria.md` Phase 4 already fixes
cross-game pairing as the confirmatory design and a metric validated under a
different design would not transfer.

Neither pass contains a Theoria arm. That exclusion is the whole mechanism by
which the battery cannot be tuned to flatter the framework it exists to test,
and it is enforced in `_control_only()` rather than left to the caller.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Sequence, Tuple

from battery.audit.stats import cliffs_delta, magnitude, sign_test
from battery.metrics import REGISTRY, Value
from battery.model import Run

# The specified gradient, weaker first.  `Theoria.md` fixes this ordering --
# the Schema harness is the published state of the art at 98.98 and `bare_cc`
# is a one-shot CLI baseline -- so it is not an ordering this battery chose
# after seeing anything.
LOW_ARM = "bare_cc"
HIGH_ARM = "schema_repro"

# Arms process 1 may validate on.  Must never contain a Theoria arm; the
# exclusion is what stops the battery being tuned to flatter the framework.
CONTROL_ARMS: Tuple[str, ...] = (LOW_ARM, HIGH_ARM)

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
                   metric_id: str,
                   select: Callable[[Run], bool]) -> Dict[str, float]:
    """One number per game per side, so a game with two runs is not counted
    twice and cannot dominate a four-game sign test."""
    buckets: Dict[str, List[float]] = {}
    for run in runs:
        if run.game_id is None or not select(run):
            continue
        value = values[run.run_id][metric_id]
        if value.ok and value.value is not None:
            buckets.setdefault(run.game_id, []).append(value.value)
    return {gid: sum(vs) / len(vs) for gid, vs in sorted(buckets.items())}


def _control_only(runs: Sequence[Run]) -> List[Run]:
    """Process 1 validates on control arms and nothing else.

    `Theoria.md`: 验证只用对照两臂，与 Theoria 无关. Enforced here rather than
    trusted to callers, because the one way this pass could be corrupted is by
    quietly letting a Theoria run into the material that licenses a metric.
    """
    return [r for r in runs if r.arm in CONTROL_ARMS]


def _verdict(entry: Dict[str, object], card, delta: Optional[float],
             test: Dict[str, object]) -> None:
    """Shared scoring, so both gradients are judged by identical rules.

    Written once on purpose: two passes with two subtly different thresholds
    would let a reader pick whichever one flattered a metric.
    """
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
            "separates the gradient strongly (|d| = %.3f) but in the "
            "opposite direction to the one declared. Either the definition is "
            "measuring something else, or the declared direction is wrong. "
            "Do not use until resolved." % abs(delta or 0.0))

    if test["p_value"] is not None and test["min_attainable_p"] > 0.05:
        entry["verdict"] = "underpowered"
        entry["note"] = (
            "%d paired games cannot reach p<0.05 however cleanly the metric "
            "separates (smallest attainable two-sided p is %.4f). The effect "
            "size stands; the test does not."
            % (test["n"], test["min_attainable_p"]))
    elif abs(delta or 0.0) < MEDIUM_EFFECT:
        entry["verdict"] = "no-effect"
        entry["note"] = "effect below the medium threshold (|d| < 0.33)"
    elif signed < 0:
        entry["verdict"] = "wrong-direction"
        entry["note"] = ("the metric separates the gradient, but backwards "
                         "from its declared direction -- either the "
                         "definition or the declaration is wrong")
    else:
        entry["verdict"] = "discriminating"


def discriminate_arms(runs: Sequence[Run],
                      values: Dict[str, Dict[str, Value]],
                      *, low: str = LOW_ARM,
                      high: str = HIGH_ARM) -> Dict[str, object]:
    """Process 1 on the gradient `Theoria.md` actually specifies: CC vs Schema.

    The two arms played the *same four games*, so this pass pairs by `game_id`
    and controls for the world -- which is precisely what the v1 arm contrast
    could not do, and why that contrast was filed separately and licensed
    nothing.  Here the pairing is real, so the pass is process 1.

    What it still cannot control for is the **harness**.  `bare_cc` is this
    project's one-shot CLI against the live API; the Schema side is an upstream
    agent, differently scaffolded, differently retried, run on somebody else's
    infrastructure.  A metric that separates these two arms has separated a
    capability gradient *bundled with* a plumbing gradient, and `confounds`
    records that on every entry rather than in a footnote.  It is the gradient
    the design names, and it is not a clean one; both halves are true.
    """
    control = _control_only(runs)
    known = {r.arm for r in control}
    results: Dict[str, object] = {}

    for metric_id in sorted(REGISTRY):
        card = REGISTRY[metric_id]
        highs = _per_game_mean(control, values, metric_id,
                               lambda r: r.arm == high)
        lows = _per_game_mean(control, values, metric_id,
                              lambda r: r.arm == low)
        shared = sorted(set(highs) & set(lows))

        entry: Dict[str, object] = {
            "family": card.family,
            "direction": card.direction,
            "n_paired_games": len(shared),
            "games": shared,
            "n_high_games": len(highs),
            "n_low_games": len(lows),
        }

        if card.direction == "neutral":
            entry["verdict"] = "not-ranked"
            entry["note"] = ("diagnostic metric; it describes a run, it does "
                             "not rank one")
        elif len(shared) < 2:
            entry["verdict"] = "no-data"
            entry["note"] = (
                "%s scores %d game(s) and %s scores %d; %d in common, nothing "
                "to pair" % (high, len(highs), low, len(lows), len(shared)))
        else:
            pairs = [(highs[g], lows[g]) for g in shared]
            delta = cliffs_delta([highs[g] for g in shared],
                                 [lows[g] for g in shared])
            entry["medians"] = {
                high: round(_median([highs[g] for g in shared]), 9),
                low: round(_median([lows[g] for g in shared]), 9),
            }
            _verdict(entry, card, delta, sign_test(pairs))

        results[metric_id] = entry

    return {
        "gradient": "%s (weaker) vs %s (stronger), paired by game" % (low, high),
        "specified_by": "Theoria.md Phase 2 process 1 -- CC vs Schema",
        "arms_present": sorted(known),
        "available": low in known and high in known,
        "confounds": [
            "arm and harness are bundled: the Schema side is an upstream "
            "agent on upstream infrastructure, not this project's harness "
            "running a different model. A separating metric has separated "
            "capability together with plumbing.",
            "the Schema side is upstream *released* material, not a "
            "reproduction we ran. baseline-arms/SCHEMA_PATH_A.md section 6: "
            "the score column <复现值> stays empty and this pass does not "
            "fill it.",
            "upstream declares no licence for this material "
            "(SCHEMA_LOCATE.md 2.3), so the payload is gitignored and only "
            "derived statistics appear in any artefact.",
        ],
        "control_runs": len(control),
        "metrics": results,
    }


def _median(xs: Sequence[float]) -> float:
    ordered = sorted(xs)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def discriminate(runs: Sequence[Run],
                 values: Dict[str, Dict[str, Value]],
                 *, arm: str = "bare_cc") -> Dict[str, object]:
    """Effect size and paired sign test for every metric, top rung vs bottom.

    Returns a verdict per metric.  `underpowered` is reported separately from
    `no-effect`: the first says the data cannot answer, the second says it did
    and the answer was no.  Collapsing them is how a thin pilot gets read as
    evidence of absence.
    """
    control = [r for r in _control_only(runs)
               if r.arm == arm and _rung(r.model) is not None]
    low, high = 0, len(MODEL_LADDER) - 1

    results: Dict[str, object] = {}
    for metric_id in sorted(REGISTRY):
        card = REGISTRY[metric_id]
        highs = _per_game_mean(control, values, metric_id,
                               lambda r: _rung(r.model) == high)
        lows = _per_game_mean(control, values, metric_id,
                              lambda r: _rung(r.model) == low)
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

        # A metric declaring "lower is better" separates the ladder correctly
        # when the *more capable* rung scores lower, i.e. a negative delta.
        # Scored by the same function as the cross-arm pass, so neither
        # gradient can be judged by a threshold the other does not use.
        _verdict(entry, card,
                 cliffs_delta([highs[g] for g in shared],
                              [lows[g] for g in shared]),
                 sign_test([(highs[g], lows[g]) for g in shared]))

        results[metric_id] = entry

    return {
        "gradient": "model ladder within %s (secondary; see module docstring)"
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
