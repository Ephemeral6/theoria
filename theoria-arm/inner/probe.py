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

**The other end of that sentence, added after the 2026-07-31 legs.** An action
on which every hypothesis is *wrong* also buys nothing, and the arm had no way
to say so. Across the four live legs of 2026-07-31 every single resolved probe
came back `survived: []` -- 28/28 on `20260731T1430Z-...-r3`, 16/16 on
`20260731T1500Z-...-l1`. The world's answer matched no hypothesis at all: not
the manual, not any ablation of it, not even `inert` ("nothing happens"). A
posterior over an empty set is not a posterior, so the *realised* information
gain of each of those probes was zero bits, while the design report went on
advertising 0.54--1.0 expected bits.

That gap is now measured rather than inferred. `entropy_bits` in the design is
**disagreement among the hypotheses**; `information_gain_bits` in the result is
**what the answer actually eliminated**, and `frontier_vacuous` names the case
where the frontier did not contain the world. The two numbers travel together
so nobody can read the first as the second again.
"""

import hashlib
import json
import math
import os
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import _bootstrap                                     # noqa: F401  (sys.path)

from world.frames import grid_hash


class ProbeRecord(dict):
    pass


def _observation(grid) -> str:
    return grid_hash(grid) or "none"


def fingerprint(action: Any, predictions: Dict[str, str]) -> str:
    """The identity of an experiment: the action, and what each hypothesis said.

    Two probes with the same fingerprint are the *same experiment* -- same
    action, same predicted successor for every hypothesis, therefore the same
    partition of the frontier. Running it twice cannot separate anything the
    first run did not, so the second is an action spent on a question already
    asked.

    This is not hypothetical. `20260731T1430Z-A3-level2-carried-r3` ran P-25 and
    P-27 as byte-identical designs, and P-26 and P-28 likewise: four actions,
    two experiments. The pre-state is *in* the fingerprint implicitly -- every
    prediction is computed from it -- so a genuinely new state gives a new
    fingerprint even on the same action.
    """
    payload = json.dumps({"action": action,
                          "predictions": dict(sorted(predictions.items()))},
                         sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def information_gain_bits(predictions: Dict[str, str], observed: str
                          ) -> Tuple[float, bool]:
    """What the answer eliminated, in bits, under a uniform prior.

    `n` hypotheses in, `k` survivors out, uniform prior: the posterior is
    uniform on the survivors and the gain is ``log2(n/k)``.

    * ``k == n`` -- nothing was eliminated, 0 bits. The design should have
      caught this (entropy zero) and not spent the action.
    * ``k == 0`` -- **vacuous**. Every hypothesis is refuted, the posterior is
      empty, and the arm has learned that its frontier does not contain the
      world. That is a real fact and it belongs in the record, but it is not a
      bit of information *about which hypothesis is true*, because none is. The
      gain is 0.0 and the second return value says why.

    The vacuous case is the one that mattered: reported as `log2(n/0) = inf` it
    would have looked like the most informative probe ever run.
    """
    total = len(predictions)
    if not total:
        return 0.0, False
    survivors = sum(1 for value in predictions.values() if value == observed)
    if survivors == 0:
        return 0.0, True
    return round(math.log2(total / survivors), 6), False


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
        #: fingerprint -> probe_id of the run that already asked this question.
        self.asked: Dict[str, str] = {}
        #: How many resolved probes in a row came back with an empty posterior.
        self.vacuous_streak = 0

    def _write(self, row: Dict[str, Any]) -> None:
        with open(self.path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(row, sort_keys=True, default=str))
            fh.write("\n")

    def record_design(self, *, action: Any, design_report: Dict[str, Any],
                      predictions: Dict[str, str], step_idx: int,
                      rationale: str = "") -> str:
        self.n += 1
        probe_id = "P-%02d" % self.n
        mark = fingerprint(action, predictions)
        row = {"probe_id": probe_id, "phase": "design", "step_idx": step_idx,
               "action": action, "rationale": rationale,
               "fingerprint": mark,
               "repeat_of": self.asked.get(mark),
               "predictions": predictions, "design": design_report}
        self.asked.setdefault(mark, probe_id)
        self.open[probe_id] = row
        self._write(row)
        return probe_id

    def already_asked(self, action: Any, predictions: Dict[str, str]
                      ) -> Optional[str]:
        """The `probe_id` that already ran this exact experiment, or `None`."""
        return self.asked.get(fingerprint(action, predictions))

    def record_result(self, probe_id: str, *, observed: str,
                      status: int, n_frames: int) -> Dict[str, Any]:
        design_row = self.open.pop(probe_id, {})
        predictions = design_row.get("predictions") or {}
        survived = sorted(h for h, p in predictions.items() if p == observed)
        refuted = sorted(h for h, p in predictions.items() if p != observed)
        gain, vacuous = information_gain_bits(predictions, observed)
        expected = ((design_row.get("design") or {}).get("best") or {}
                    ).get("entropy_bits")

        if vacuous:
            self.vacuous_streak += 1
        else:
            self.vacuous_streak = 0

        if vacuous:
            # The honest sentence. "THE MANUAL WAS WRONG" is true but it is the
            # least useful true thing here, and it is what the desk was told
            # 28 times in a row on r3 for $1.6 a time. The manual being wrong
            # invites a patch to the manual; the frontier being empty says the
            # patch cannot be an ablation of what is already written.
            verdict = (
                "THE FRONTIER DID NOT CONTAIN THE WORLD: all %d hypotheses "
                "were refuted, including `inert` (nothing happens) and the "
                "manual itself, which predicted %r against the world's %r. "
                "No hypothesis survives, so this probe eliminated nothing and "
                "its realised information gain is 0.0 bits against the %s bits "
                "the design expected. The manual needs a mechanism it does not "
                "currently state -- deleting one of its rules cannot reach this "
                "observation."
                % (len(predictions), predictions.get("manual"), observed,
                   "%.3f" % expected if isinstance(expected, (int, float))
                   else "unmeasured"))
        elif "manual" in survived:
            verdict = "the manual predicted this transition"
        else:
            verdict = ("THE MANUAL WAS WRONG: it predicted %r, the world "
                       "answered %r" % (predictions.get("manual"), observed))

        row = {"probe_id": probe_id, "phase": "result", "status": status,
               "observed": observed, "n_frames": n_frames,
               "survived": survived, "refuted": refuted,
               "n_hypotheses": len(predictions),
               "n_survivors": len(survived),
               "information_gain_bits": gain,
               "expected_bits": expected,
               "frontier_vacuous": vacuous,
               "vacuous_streak": self.vacuous_streak,
               "manual_survived": "manual" in survived,
               "verdict": verdict}
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
