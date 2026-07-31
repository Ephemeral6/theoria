"""probe -- design the experiment that splits the frontier, predict first, then act.

`Theoria.md` 1.10(d): probe targets the thinnest-evidenced clause and the
action whose outcome most divides the surviving hypotheses; the prediction is
written **before** the action is taken; the result goes to `probes.jsonl`; a
refutation goes back to theorize. 1.10(b) adds the part that matters online:
probe value is entropy per unit cost, and **the path costs API actions**, so
the value function must price them.

The frontier here is built by ablation, which is the form a frontier takes
once a manual exists. The hypotheses are:

* `manual` -- what the manual predicts;
* `manual_without_<rule>` -- what it would predict if that one rule did not
  fire. The generated predictor exposes `fired(state, action)`, so this is an
  exact ablation and not a guess;
* `inert` -- nothing changes. This is the hypothesis A0's R-05 needed and could
  never test: a rule that is *missing* rather than wrong predicts "nothing
  happens", and only an experiment separates that from "the rule fired".

An action on which every hypothesis agrees has entropy zero and buys nothing;
`probe_frontier` says so and the arm does not spend an action on it.
"""

import json
import os
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import _bootstrap                                     # noqa: F401  (sys.path)

from world.frames import grid_hash


class ProbeRecord(dict):
    pass


def _observation(grid) -> str:
    return grid_hash(grid) or "none"


def build_hypotheses(namespace: Dict[str, Any]):
    """One hypothesis per ablation, plus the manual and the inert reading."""
    from engines.probe_frontier import Hypothesis     # noqa: PLC0415

    render = namespace["render"]
    step = namespace["step"]
    fired = namespace.get("fired")
    rules = list(namespace.get("RULES") or [])

    def manual_predict(state, action):
        try:
            return _observation(render(step(state, action)))
        except Exception:                              # noqa: BLE001
            return "error"

    def inert_predict(state, action):
        return _observation(render(state))

    hypotheses = [
        Hypothesis(id="manual", predict=manual_predict,
                   description="the manual as written"),
        Hypothesis(id="inert", predict=inert_predict,
                   description="this action does nothing in this state"),
    ]

    if fired is not None:
        # `RULES` is a list of (name, guard_fn, effect_fn, objects) tuples.
        #
        # Ablate by SCHEMA, not by ground rule. `forall ?p in Ring` grounds to
        # one rule per instance -- `shift__Ring_r8c14`, `shift__Ring_r8c15`, …
        # -- and ablating each separately would make seventy near-identical
        # hypotheses, seventy times the work, to answer a question nobody
        # asked. The manual's claim is the schema; "does `shift` fire at all"
        # is the hypothesis worth an action, so all of a schema's ground rules
        # are suppressed together.
        schemas: Dict[str, List[str]] = {}
        for entry in rules:
            name = entry[0] if isinstance(entry, (tuple, list)) else str(entry)
            schemas.setdefault(name.split("__")[0], []).append(name)

        for base, members in sorted(schemas.items()):
            group = frozenset(members)

            def ablated(state, action, _group=group):
                try:
                    if _group & set(fired(state, action) or []):
                        return _observation(render(state))
                    return _observation(render(step(state, action)))
                except Exception:                      # noqa: BLE001
                    return "error"
            hypotheses.append(Hypothesis(
                id="without_%s" % base, predict=ablated,
                description=("the manual with rule %r removed (%d ground "
                             "instance%s)" % (base, len(members),
                                              "" if len(members) == 1 else "s"))))
    return hypotheses


def design(namespace: Dict[str, Any], state: Any, actions: Sequence[Any], *,
           costs: Optional[Dict[Any, float]] = None,
           out_path: Optional[str] = None,
           transitions: Optional[Sequence[int]] = None,
           coverage: Optional[str] = None) -> Dict[str, Any]:
    """Rank the available actions by bits-per-action. Zero model calls."""
    from engines import probe_frontier                # noqa: PLC0415

    hypotheses = build_hypotheses(namespace)
    best, ranked = probe_frontier.run(
        hypotheses, state, list(actions),
        costs=costs or {a: 1.0 for a in actions},
        transitions=list(transitions or []),
        coverage=coverage or "0/0",
        out_path=out_path)

    return {
        "n_hypotheses": len(hypotheses),
        "hypotheses": [{"id": h.id, "description": h.description}
                       for h in hypotheses],
        "best": best.as_json() if best is not None else None,
        "ranking": [value.as_json() for value in ranked],
        "verdict": ("no action separates any two hypotheses in this state -- "
                    "the manual and every ablation of it predict the same thing "
                    "everywhere, so no experiment here is worth an action"
                    if best is None else
                    "action %s splits %d hypotheses into %d classes for %.1f bits"
                    % (best.action, len(hypotheses), best.n_classes, best.entropy)),
    }


class ProbeLog:
    """`probes.jsonl`: design, prediction, observation, verdict -- in that order.

    The order is the discipline. A prediction written after the observation is
    not a prediction, so `record_design` is called before the action is sent and
    `record_result` afterwards, and the two halves carry the same `probe_id`.
    """

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.n = 0
        self.open: Dict[str, Dict[str, Any]] = {}

    def _write(self, row: Dict[str, Any]) -> None:
        with open(self.path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(row, sort_keys=True, default=str))
            fh.write("\n")

    def record_design(self, *, action: Any, design_report: Dict[str, Any],
                      predictions: Dict[str, str], step_idx: int,
                      rationale: str = "") -> str:
        self.n += 1
        probe_id = "P-%02d" % self.n
        row = {"probe_id": probe_id, "phase": "design", "step_idx": step_idx,
               "action": action, "rationale": rationale,
               "predictions": predictions, "design": design_report}
        self.open[probe_id] = row
        self._write(row)
        return probe_id

    def record_result(self, probe_id: str, *, observed: str,
                      status: int, n_frames: int) -> Dict[str, Any]:
        design_row = self.open.pop(probe_id, {})
        predictions = design_row.get("predictions") or {}
        survived = sorted(h for h, p in predictions.items() if p == observed)
        refuted = sorted(h for h, p in predictions.items() if p != observed)
        row = {"probe_id": probe_id, "phase": "result", "status": status,
               "observed": observed, "n_frames": n_frames,
               "survived": survived, "refuted": refuted,
               "manual_survived": "manual" in survived,
               "verdict": ("the manual predicted this transition"
                           if "manual" in survived else
                           "THE MANUAL WAS WRONG: it predicted %r, the world "
                           "answered %r" % (predictions.get("manual"), observed))}
        self._write(row)
        return row

    def record_unrunnable(self, *, reason: str, design_report: Dict[str, Any],
                          step_idx: int) -> str:
        """A probe that cannot be run is a finding; a probe quietly dropped is
        a lie (cold-start-a2, P-3)."""
        self.n += 1
        probe_id = "P-%02d" % self.n
        row = {"probe_id": probe_id, "phase": "unrunnable", "step_idx": step_idx,
               "reason": reason, "design": design_report}
        self._write(row)
        return probe_id
