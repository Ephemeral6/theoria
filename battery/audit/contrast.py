"""The arm contrast — bare CC against the offline Theoria arms.

**This is not process 1, and it must never be filed as process 1.**

`Theoria.md` Phase 2 is explicit about the discipline this module sits outside
of:

    1. 区分力：每个候选指标必须在已知能力梯度上拉开差距（CC vs Schema，效应量
       入册）...  验证只用对照两臂，与 Theoria 无关，防止电池被设计成给自己脸上
       贴金。

*Validation uses the control arms only, and has nothing to do with Theoria* —
precisely so that the instrument cannot be tuned into flattering the framework
it exists to test. `audit/discriminate.py` is that pass and it stays
control-only.

This module computes the thing that pass is forbidden to compute: how the
metrics actually separate `bare_cc` from the Theoria arms. That is a *result*,
reported as one, and the two must not be allowed to blur together — a metric
that "discriminates" here has demonstrated nothing about its own validity, and
citing it as validation would be exactly the self-congratulation the discipline
was written to prevent. `run_battery` writes the two to different artefacts and
`METRICS.md`'s 验证材料 column records, per metric, which material its
*validation* rests on. Nothing from here appears in that column.

Three properties of this contrast are structural, not fixable, and are attached
to every entry rather than left in prose:

* **It is unpaired.** `bare_cc` plays ARC games; the offline Theoria arms play
  self-built worlds. There is no game to pair on, so the sign test that
  `discriminate.py` uses does not apply and an exact Mann-Whitney stands in.
* **Arm is confounded with world.** Every difference found here is a difference
  between (arm A on world A) and (arm B on world B). No amount of data
  separates the two, because no Theoria arm has yet played an ARC game. This is
  the single biggest reason the numbers below are weaker than they look.
* **The two sides are largely complementary.** `bare_cc` has no books, so the
  epistemic family cannot score it; the offline Theoria arms have no model
  calls, so the economy family cannot score them. Most metrics therefore have
  data on exactly one side and no contrast at all exists for them. That
  emptiness is the finding, and `overlap` reports it per metric rather than
  quietly returning nothing.

Unpaired testing buys nominal power the paired test could not reach — 2 against
17 attains p = 0.0117 where four paired games could not beat 0.125. That is
power bought by discarding the control, and it is reported next to
`min_attainable_p` so nobody reads it as an improvement.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from battery.audit.stats import cliffs_delta, magnitude, mann_whitney
from battery.metrics import REGISTRY, Value
from battery.model import Run

MEDIUM_EFFECT = 0.33

# The one honest use of this pass. Metric definitions are validated on the
# control arms; this exists to say what the instrument reads when it is finally
# pointed at both kinds of arm, and to make the *coverage* asymmetry visible.
NOT_VALIDATION = (
    "Theoria.md Phase 2 process 1 validates metrics on the control arms only "
    "(CC vs Schema). This contrast includes Theoria arms and is therefore a "
    "result, not a validation. No entry here licenses a metric for use."
)


def _values_for(runs: Sequence[Run], values: Dict[str, Dict[str, Value]],
                metric_id: str) -> List[float]:
    out: List[float] = []
    for run in sorted(runs, key=lambda r: r.run_id):
        value = values[run.run_id][metric_id]
        if value.ok and value.value is not None:
            out.append(value.value)
    return out


def _worlds(runs: Sequence[Run]) -> List[str]:
    return sorted({r.game_id or r.source for r in runs})


def contrast(runs: Sequence[Run], values: Dict[str, Dict[str, Value]], *,
             control_arm: str = "bare_cc",
             theory_prefix: str = "theoria") -> Dict[str, object]:
    """Effect size and an exact unpaired test, control arm vs Theoria arms.

    Returns one entry per metric. `overlap` is the first thing to read: a
    metric with data on only one side has no contrast, and saying so is more
    informative than any statistic computed around it.
    """
    control = [r for r in runs if r.arm == control_arm]
    theory = [r for r in runs if r.arm.startswith(theory_prefix)]

    results: Dict[str, object] = {}
    for metric_id in sorted(REGISTRY):
        card = REGISTRY[metric_id]
        theory_vals = _values_for(theory, values, metric_id)
        control_vals = _values_for(control, values, metric_id)

        entry: Dict[str, object] = {
            "family": card.family,
            "direction": card.direction,
            "n_theoria": len(theory_vals),
            "n_bare_cc": len(control_vals),
        }

        if not theory_vals or not control_vals:
            side = ("theoria" if control_vals else
                    control_arm if theory_vals else "neither")
            entry["overlap"] = False
            entry["verdict"] = "no-contrast"
            entry["note"] = (
                "scored on %s only; the two arms are structurally "
                "complementary on this metric, so no contrast exists to "
                "compute" % side)
            results[metric_id] = entry
            continue

        entry["overlap"] = True
        delta = cliffs_delta(theory_vals, control_vals)
        test = mann_whitney(theory_vals, control_vals)

        # "Higher is more capable" means the Theoria arm scoring higher agrees
        # with the declared direction; a `lower` metric agrees when it scores
        # lower. Same convention as `discriminate.py`, so the two artefacts can
        # be read side by side without re-deriving it.
        expected = 1.0 if card.direction == "higher" else -1.0
        signed = (delta or 0.0) * expected

        entry.update({
            "cliffs_delta": None if delta is None else round(delta, 9),
            "magnitude": magnitude(delta),
            "mann_whitney": test,
            "theoria_median": round(_median(theory_vals), 9),
            "bare_cc_median": round(_median(control_vals), 9),
            # The confound, attached to the number rather than filed under it.
            "worlds_theoria": _worlds(theory),
            "worlds_bare_cc": _worlds(control),
            "confounded_by_world": True,
        })

        if card.direction == "neutral":
            entry["verdict"] = "not-ranked"
            entry["note"] = ("diagnostic metric; it describes a run, it does "
                             "not rank one")
        elif abs(delta or 0.0) < MEDIUM_EFFECT:
            entry["verdict"] = "no-effect"
            entry["note"] = "effect below the medium threshold (|d| < 0.33)"
        else:
            entry["verdict"] = ("separates" if signed > 0
                                else "separates-against")
            entry["note"] = (
                "the arms separate on this metric, %s the declared direction. "
                "Arm and world are confounded: every Theoria run here is on a "
                "self-built world and every %s run is on an ARC game, so this "
                "is not attributable to the arm."
                % ("in" if signed > 0 else "against", control_arm))

        results[metric_id] = entry

    overlapping = sorted(m for m in results if results[m].get("overlap"))
    return {
        "status": NOT_VALIDATION,
        "design": "unpaired; no game is shared between the arms",
        "test": "exact two-sided Mann-Whitney (no normal approximation)",
        "control_arm": control_arm,
        "theoria_arms": sorted({r.arm for r in theory}),
        "n_control_runs": len(control),
        "n_theoria_runs": len(theory),
        "metrics_with_overlap": overlapping,
        "n_metrics_with_overlap": len(overlapping),
        "n_metrics": len(results),
        "coverage_note": (
            "%d of %d metrics have data on both sides. The rest are "
            "structurally one-sided: an arm with no books cannot be scored on "
            "the epistemic family, and an arm with no model calls cannot be "
            "scored on the economy family. This is why Theoria.md specified "
            "CC vs Schema -- a replay-level model is the only arm that "
            "overlaps both."
            % (len(overlapping), len(results))),
        "metrics": results,
    }


def _median(xs: Sequence[float]) -> float:
    ordered = sorted(xs)
    n = len(ordered)
    if n % 2:
        return ordered[n // 2]
    return (ordered[n // 2 - 1] + ordered[n // 2]) / 2.0
