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

**Probe economics (`ProbeEconomy`, default off).** That `entropy > 0` floor is
the only thing standing between the loop and an unbounded probe bill, and the
four live legs of 2026-07-31 measured what it lets through. 56 probes designed,
52 completed, and the frontier never shrank once -- not a single monotone drop
in hypothesis count across any leg, because the frontier is rebuilt by ablation
from the current manual on every turn and a refutation is thrown away the
moment it is written down. Worse, 47 of the 52 landed **off the frontier**: the
observed hash matched no hypothesis at all, not the manual, not `inert`, not
any ablation. An observation with no posterior support is not a split of the
frontier; it is evidence the frontier does not contain the truth, and the
0.54--1.00 "bits" priced at design time were never realisable. On top of that,
18 of the 56 were byte-identical repeats -- same action, same partition --
because a greedy argmax over a frontier that never changes returns the same
argmax forever.

So `ProbeEconomy` prices the four things the measurement found, and nothing
else. It carries refutations forward so the frontier can actually shrink; it
refuses an experiment whose (action, partition) signature has already been
fired, which under determinism cannot buy a bit the first firing did not; it
retires the probe class after N consecutive off-frontier results; and it caps
firings per *generation*, where a generation is the hypothesis-id set itself --
so theorize, and only theorize, re-opens probing. That is the honest economy: a
probe is worth an action when the theory has changed since the last one.

`enabled=False` is the default and reproduces the old behaviour exactly.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

import _bootstrap                                     # noqa: F401  (sys.path)

from world.frames import grid_hash


class ProbeRecord(dict):
    pass


def _observation(grid) -> str:
    return grid_hash(grid) or "none"


@dataclass(frozen=True)
class ProbeEconomyConfig:
    """The switch. Every default here is the pre-change behaviour.

    `enabled=False` makes `ProbeEconomy` a pass-through: `filter_hypotheses`
    returns its argument and `gate` always allows. A round turns exactly this
    on by flipping `enabled`, and nothing else in the arm moves.
    """

    #: The master switch. False == 2026-07-31 behaviour, byte for byte.
    enabled: bool = False

    #: Carry refutations forward, so the frontier can shrink. Measured need:
    #: zero monotone drops in 56 probes.
    carry_refutations: bool = True

    #: Refuse an experiment whose (action, partition) signature already fired.
    #: Measured need: 18/56 = 32.1% of probes were exact repeats.
    suppress_repeats: bool = True

    #: Retire the probe class after this many consecutive off-frontier
    #: results. 0 disables. Measured need: 47/52 = 90.4% off-frontier, and in
    #: r3 the very first probe was off-frontier and 27 more followed.
    off_frontier_stop: int = 3

    #: Cap firings per generation (a generation == one hypothesis-id set).
    #: 0 disables. Backstop above every observed distinct-experiment count.
    max_per_generation: int = 4

    #: Refuse a probe splitting fewer than this many bits. Default 0.0, which
    #: is a deliberate no-op: every one of the 56 measured probes scored
    #: 0.5436--1.0000 bits, so no floor would have cut a probe the other three
    #: rules do not already cut. The knob exists because the next game may
    #: differ; it is set where the measurement leaves it, not where it would
    #: look busy.
    min_bits: float = 0.0

    @classmethod
    def from_env(cls, env: Optional[Dict[str, str]] = None
                 ) -> "ProbeEconomyConfig":
        """`THEORIA_PROBE_ECONOMY=1` turns it on; absent or 0 leaves it off.

        Anything unrecognised is off. A misspelt switch must not silently
        enable a framework change that a round is trying to measure.
        """
        env = os.environ if env is None else env
        raw = str(env.get("THEORIA_PROBE_ECONOMY", "")).strip().lower()
        on = raw in ("1", "true", "yes", "on")
        if not on:
            return cls()
        kwargs: Dict[str, Any] = {"enabled": True}
        for name, cast in (("PROBE_OFF_FRONTIER_STOP", int),
                           ("PROBE_MAX_PER_GENERATION", int),
                           ("PROBE_MIN_BITS", float)):
            value = env.get("THEORIA_" + name)
            if value not in (None, ""):
                try:
                    kwargs[name.lower().replace("probe_", "", 1)] = cast(value)
                except ValueError:
                    pass
        return cls(**kwargs)


def _signature(design_report: Dict[str, Any]) -> Optional[str]:
    """The experiment's identity: which action, and how it partitions whom.

    Not the action alone -- the same action against a different frontier is a
    different experiment, and it is the partition that says so.
    """
    best = (design_report or {}).get("best") or {}
    if not best:
        return None
    return json.dumps({"action": best.get("action"),
                       "partition": best.get("partition")},
                      sort_keys=True, default=str)


@dataclass
class ProbeEconomy:
    """Frontier bookkeeping across probes, and the refusal that follows from it.

    Stateful on purpose. The defect the measurement found is precisely that the
    old path was stateless: every turn rebuilt the same frontier, re-derived the
    same argmax, and spent an action re-answering a question already answered.
    """

    config: ProbeEconomyConfig = field(default_factory=ProbeEconomyConfig)

    #: Hypothesis ids a completed probe has already refuted, this generation.
    retired: Set[str] = field(default_factory=set)
    #: Experiment signatures already fired, this generation.
    fired: Set[str] = field(default_factory=set)
    consecutive_off_frontier: int = 0
    fired_this_generation: int = 0
    generation: int = 0
    _generation_key: Optional[frozenset] = None
    #: Every allow/refuse, with its reason. The audit trail is the evidence.
    decisions: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def enabled(self) -> bool:
        return bool(self.config.enabled)

    # -- generations -------------------------------------------------------
    def note_frontier(self, hypothesis_ids: Sequence[str]) -> bool:
        """Register the frontier the manual currently implies.

        A change in the hypothesis-id set means theorize rewrote the manual, so
        every count resets: the questions are new questions. Returns True if
        this opened a new generation.
        """
        key = frozenset(hypothesis_ids)
        if key == self._generation_key:
            return False
        self._generation_key = key
        self.generation += 1
        self.retired = set()
        self.fired = set()
        self.consecutive_off_frontier = 0
        self.fired_this_generation = 0
        return True

    # -- the frontier itself ----------------------------------------------
    def filter_hypotheses(self, hypotheses: Sequence[Any]) -> List[Any]:
        """Drop what earlier probes in this generation already refuted.

        `manual` is never dropped. It is the thing under test, and a frontier
        without it cannot report `manual_survived` -- which is the signal that
        drives theorize. When the manual is refuted the answer is a new manual,
        not a frontier that has quietly stopped mentioning it.
        """
        if not self.enabled or not self.config.carry_refutations:
            return list(hypotheses)
        kept = [h for h in hypotheses
                if h.id == "manual" or h.id not in self.retired]
        return kept or list(hypotheses)

    # -- the gate ----------------------------------------------------------
    def gate(self, design_report: Dict[str, Any], *, n_frontier: int
             ) -> Tuple[bool, str]:
        """Allow this probe, or refuse it with a reason fit for `probes.jsonl`.

        Disabled: always allow, so the caller's own `entropy > 0` check is the
        only floor, exactly as before.
        """
        if not self.enabled:
            return True, ""
        cfg = self.config
        best = (design_report or {}).get("best") or {}
        bits = float(best.get("entropy_bits") or 0.0)

        if cfg.off_frontier_stop and (
                self.consecutive_off_frontier >= cfg.off_frontier_stop):
            return False, (
                "probe class retired: %d consecutive probes landed off the "
                "frontier (no hypothesis predicted what the world did), so the "
                "frontier does not contain the truth and another probe of this "
                "shape cannot find it -- theorize, do not probe"
                % self.consecutive_off_frontier)

        if n_frontier <= 1:
            return False, ("the frontier has collapsed to %d hypothesis: there "
                           "is nothing left to split" % n_frontier)

        if cfg.max_per_generation and (
                self.fired_this_generation >= cfg.max_per_generation):
            return False, (
                "probe budget for this frontier is spent: %d probes fired "
                "since the manual last changed, cap is %d -- the frontier is "
                "unchanged, so the argmax is unchanged, so the next probe is "
                "the last one again"
                % (self.fired_this_generation, cfg.max_per_generation))

        if cfg.min_bits > 0.0 and bits < cfg.min_bits:
            return False, ("splits only %.4f bits, floor is %.4f"
                           % (bits, cfg.min_bits))

        signature = _signature(design_report)
        if cfg.suppress_repeats and signature is not None and (
                signature in self.fired):
            return False, (
                "this exact experiment has already been run: same action, same "
                "partition of the same frontier. The world is deterministic, "
                "so the answer is the answer we already have")

        return True, ""

    # -- results feed back -------------------------------------------------
    def record_fired(self, design_report: Dict[str, Any]) -> None:
        signature = _signature(design_report)
        if signature is not None:
            self.fired.add(signature)
        self.fired_this_generation += 1

    def observe(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Fold a probe result back into the frontier. Returns what it learnt."""
        survived = list(result.get("survived") or [])
        refuted = list(result.get("refuted") or [])
        off_frontier = not survived
        if off_frontier:
            self.consecutive_off_frontier += 1
        else:
            self.consecutive_off_frontier = 0
            if self.config.carry_refutations:
                # Only a probe that landed ON the frontier teaches anything
                # about which hypothesis is wrong. When nothing survived, the
                # partition itself was wrong, and "everyone is refuted" is a
                # statement about the frontier, not about its members.
                self.retired.update(i for i in refuted if i != "manual")
        return {"off_frontier": off_frontier,
                "n_survived": len(survived),
                "n_refuted": len(refuted),
                "retired_total": len(self.retired),
                "consecutive_off_frontier": self.consecutive_off_frontier}

    def note_decision(self, **fields: Any) -> None:
        self.decisions.append(dict(fields))

    def as_json(self) -> Dict[str, Any]:
        allowed = sum(1 for d in self.decisions if d.get("allowed"))
        refused = len(self.decisions) - allowed
        reasons: Dict[str, int] = {}
        for d in self.decisions:
            if not d.get("allowed"):
                key = str(d.get("reason", ""))[:60]
                reasons[key] = reasons.get(key, 0) + 1
        return {
            "enabled": self.enabled,
            "config": {
                "carry_refutations": self.config.carry_refutations,
                "suppress_repeats": self.config.suppress_repeats,
                "off_frontier_stop": self.config.off_frontier_stop,
                "max_per_generation": self.config.max_per_generation,
                "min_bits": self.config.min_bits,
            },
            "generations": self.generation,
            "probes_allowed": allowed,
            "probes_refused": refused,
            "refusal_reasons": dict(sorted(reasons.items())),
            "retired_hypotheses": sorted(self.retired),
            "consecutive_off_frontier": self.consecutive_off_frontier,
        }


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
           coverage: Optional[str] = None,
           economy: Optional[ProbeEconomy] = None) -> Dict[str, Any]:
    """Rank the available actions by bits-per-action. Zero model calls.

    With `economy` disabled or absent this is the original function: the full
    ablation frontier goes to the engine and the report says nothing new. With
    it enabled, hypotheses this generation's earlier probes already refuted are
    dropped before the engine sees them, so the frontier the report describes is
    the frontier that is actually still standing.
    """
    from engines import probe_frontier                # noqa: PLC0415

    full = build_hypotheses(namespace)
    hypotheses = list(full)
    economy_report: Optional[Dict[str, Any]] = None
    if economy is not None and economy.enabled:
        economy.note_frontier([h.id for h in full])
        hypotheses = economy.filter_hypotheses(full)
        economy_report = {
            "generation": economy.generation,
            "n_before": len(full),
            "n_after": len(hypotheses),
            "carried_refutations": sorted(economy.retired),
            "fired_this_generation": economy.fired_this_generation,
            "consecutive_off_frontier": economy.consecutive_off_frontier,
        }

    best, ranked = probe_frontier.run(
        hypotheses, state, list(actions),
        costs=costs or {a: 1.0 for a in actions},
        transitions=list(transitions or []),
        coverage=coverage or "0/0",
        out_path=out_path)

    report = {
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
    if economy_report is not None:
        report["economy"] = economy_report
    return report


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
