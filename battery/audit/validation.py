"""What material each metric's validation actually rests on.

`METRICS.md` gained a 验证材料 column in v1, and the point of it is to stop a
reader from having to guess. A metric with a definition, a direction and a
tier looks equally authoritative whether it was checked against twenty runs or
zero, and v0's table gave no way to tell those apart.

**The column is computed, not declared.** A hand-written provenance note is a
claim about the code; this is derived from the recompute itself, so it cannot
drift away from what actually happened and cannot be quietly improved.

The distinction it enforces is `Theoria.md` Phase 2 process 1:

    验证只用对照两臂，与 Theoria 无关。

*Validation uses the control arms only.* So a run on a Theoria arm can make a
metric **computable** without making it **validated**, and the two are reported
in different fields:

* `validation_runs` — control-arm runs only. This is the number that licenses
  a metric to be used for an ordering claim.
* `computed_runs` — every run the metric produced a value on, control or not.
  Useful, and not evidence of anything about the metric.

A metric with `validation_runs = 0` has never been checked against a known
capability gradient at all. It may still be perfectly sound; it has simply not
been shown to separate anything, and `Theoria.md` is blunt about what that
means: 分不开已知差异的指标，没资格测未知差异.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from battery.metrics import REGISTRY, Value
from battery.model import Run

# Arms whose runs count as validation material for process 1. Theoria arms are
# deliberately absent and must stay absent -- that exclusion is the whole
# mechanism by which the battery cannot be tuned to flatter the framework.
CONTROL_ARMS = ("bare_cc", "schema_repro")


def _label(run: Run) -> str:
    """A short, stable name for the material a run belongs to."""
    if run.game_id:
        campaign = run.campaign or "unlabelled"
        return "%s/%s/%s" % (run.arm, campaign, run.game_id)
    return "%s/%s" % (run.arm, run.source)


def material(runs: Sequence[Run], values: Dict[str, Dict[str, Value]],
             discrimination: Optional[Dict[str, object]] = None,
             ) -> Dict[str, object]:
    """Per metric: what it was computed on, and what validates it."""
    controls = [r for r in runs if r.arm in CONTROL_ARMS]
    verdicts = ((discrimination or {}).get("metrics") or {})

    rows: Dict[str, object] = {}
    for metric_id in sorted(REGISTRY):
        computed: List[str] = []
        validating: List[str] = []
        games = set()
        for run in sorted(runs, key=lambda r: r.run_id):
            value = values[run.run_id][metric_id]
            if not (value.ok and value.value is not None):
                continue
            computed.append(run.run_id)
            if run.arm in CONTROL_ARMS:
                validating.append(run.run_id)
                if run.game_id:
                    games.add(run.game_id)

        sources = sorted({_label(r) for r in runs
                          if values[r.run_id][metric_id].ok})
        control_sources = sorted({_label(r) for r in controls
                                  if values[r.run_id][metric_id].ok})
        entry = verdicts.get(metric_id) or {}

        rows[metric_id] = {
            "computed_runs": len(computed),
            "validation_runs": len(validating),
            "validation_games": sorted(games),
            "sources": sources,
            "control_sources": control_sources,
            "process1_verdict": entry.get("verdict", "not-run"),
            "n_paired_games": entry.get("n_paired_games", 0),
            "summary": _summary(len(validating), sorted(games),
                                control_sources, entry.get("verdict")),
        }

    unvalidated = sorted(m for m in rows if not rows[m]["validation_runs"])
    return {
        "rule": ("validation material is control arms only (Theoria.md "
                 "Phase 2 process 1); Theoria runs make a metric computable, "
                 "not validated"),
        "control_arms": list(CONTROL_ARMS),
        "n_unvalidated": len(unvalidated),
        "unvalidated": unvalidated,
        "metrics": rows,
    }


def _summary(n_validation: int, games: Sequence[str],
             control_sources: Sequence[str],
             verdict: Optional[str]) -> str:
    """The one-line form that goes in `METRICS.md`'s 验证材料 column."""
    if not n_validation:
        return "none — never computed on a control arm"
    campaigns = sorted({s.split("/")[1] for s in control_sources
                        if len(s.split("/")) > 2})
    where = ", ".join(campaigns) if campaigns else "control"
    return "%d control run%s over %d game%s (%s); process 1: %s" % (
        n_validation, "" if n_validation == 1 else "s",
        len(games), "" if len(games) == 1 else "s", where,
        verdict or "not-run")
