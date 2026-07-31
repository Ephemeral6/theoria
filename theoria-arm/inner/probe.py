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

**The other end of that sentence, and what it cost.** An action on which every
hypothesis is *wrong* also buys nothing, and until the 2026-07-31 legs the arm
had no way to say so. Those four legs designed 56 probes and completed 52, and
the record is unambiguous about all three ways an action was wasted:

* **The answer was outside the frontier, 47 times in 52.** Every resolved probe
  on two of the legs came back `survived: []` -- 28/28 on
  `20260731T1430Z-...-r3`, 16/16 on `20260731T1500Z-...-l1`. The world's answer
  matched no hypothesis at all: not the manual, not any ablation of it, not
  even `inert` ("nothing happens"). A posterior over an empty set is not a
  posterior, so the *realised* information gain of each of those probes was
  zero bits, while the design report went on advertising 0.54--1.0 expected
  bits.
* **The same question was bought twice, 18 times in 56.** A greedy argmax over
  a frontier that never changes returns the same argmax forever: r3 ran P-25
  and P-27 as byte-identical designs, and P-26 and P-28 likewise.
* **The frontier never shrank once.** Not a single monotone drop in hypothesis
  count across any leg, because the frontier is rebuilt by ablation from the
  current manual on every turn and a refutation is thrown away the moment it is
  written down.

The first two are now *measured* rather than inferred, and the measurement is
what the loop refuses on. `entropy_bits` in the design is **disagreement among
the hypotheses**; `information_gain_bits` in the result is **what the answer
actually eliminated**; `frontier_vacuous` names the case where the frontier did
not contain the world; and `fingerprint` names an experiment by its action and
by what every hypothesis predicted, so a repeat is recognisable on sight. The
two bit-counts travel together in every result row so nobody can read the first
as the second again, and `inner/loop.py` spends no action on a probe whose
streak, fingerprint or budget says the answer is already in hand.

**The third is what `ProbeEconomy` is for, and it is default off.** Refusing to
re-ask a question is free; *changing the frontier* is a framework change, so it
ships behind a switch a round can turn on (`THEORIA_PROBE_ECONOMY=1`) and
measure against a leg that left it off. Enabled, the economy carries a probe's
refutations forward within a **generation** -- a generation being the
hypothesis-id set itself, so theorize, and only theorize, re-opens the
questions -- and hands `design` the frontier that is actually still standing
rather than the whole ablation set again. It also refuses a frontier that has
collapsed to one hypothesis, which only becomes reachable once the frontier can
shrink at all, and carries a bits floor whose default of 0.0 is a deliberate
no-op (every one of the 56 measured probes scored 0.5436--1.0000 bits, so no
floor would have cut one the streak and fingerprint rules do not already cut).

`enabled=False` is the default and reproduces the pre-economy frontier exactly.
"""

import hashlib
import json
import math
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple

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

    **Feed it the whole ablation set, not a filtered frontier.** That implicit
    pre-state only survives if the hypothesis set is held fixed: shrink the set
    and the same action from the same state hashes differently, so an
    experiment already run reads as a new one. With `ProbeEconomy` carrying
    refutations forward that is exactly what happens, and replaying the four
    legs through the merged policy measures the cost -- 9 repeats caught
    instead of 15, three more actions spent re-asking. `ProbeLog.record_design`
    therefore takes the identity set separately from the set being scored, and
    `inner/loop.py` passes the unfiltered predictions here while scoring
    survivorship on the live frontier. The identity of an experiment must not
    depend on how much of the theory the arm has already ruled out.
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


@dataclass(frozen=True)
class ProbeEconomyConfig:
    """The switch. Every default here is the pre-economy behaviour.

    `enabled=False` makes `ProbeEconomy` a pass-through: `filter_hypotheses`
    returns its argument and `gate` always allows. A round turns exactly this
    on by flipping `enabled`, and nothing else in the arm moves.

    **What is deliberately not a knob here.** Two of the four rules the
    2026-07-31 measurement asked for -- "stop after N answers that landed off
    the frontier" and "do not buy the same experiment twice" -- are *not*
    configured from this dataclass, because they are not implemented here.
    They are unconditional refusals in `inner/loop.py`, counted off the
    measurement `ProbeLog` already writes into every result row
    (`frontier_vacuous` / `vacuous_streak`, and `fingerprint` / `repeat_of`).
    Refusing to re-ask a question the record shows was already asked needs no
    permission and no A/B leg; changing the frontier the arm reasons over does,
    which is what this switch is for.
    """

    #: The master switch. False == pre-economy frontier, hypothesis for
    #: hypothesis.
    enabled: bool = False

    #: Carry refutations forward, so the frontier can shrink. Measured need:
    #: zero monotone drops in 56 probes.
    carry_refutations: bool = True

    #: Refuse a probe splitting fewer than this many bits. Default 0.0, which
    #: is a deliberate no-op: every one of the 56 measured probes scored
    #: 0.5436--1.0000 bits, so no floor would have cut a probe the streak and
    #: fingerprint rules do not already cut. The knob exists because the next
    #: game may differ; it is set where the measurement leaves it, not where it
    #: would look busy.
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
        for name, cast in (("PROBE_MIN_BITS", float),):
            value = env.get("THEORIA_" + name)
            if value not in (None, ""):
                try:
                    kwargs[name.lower().replace("probe_", "", 1)] = cast(value)
                except ValueError:
                    pass
        return cls(**kwargs)


@dataclass
class ProbeEconomy:
    """Frontier bookkeeping across probes, and the refusal that follows from it.

    Stateful on purpose. The defect the measurement found is precisely that the
    old path was stateless: every turn rebuilt the same frontier from the same
    manual, re-derived the same argmax, and spent an action re-answering a
    question already answered. `inner/loop.py` refuses the re-answering; this
    class is the other half -- it makes the frontier itself move, so the next
    argmax is a genuinely different question rather than the same one refused.
    """

    config: ProbeEconomyConfig = field(default_factory=ProbeEconomyConfig)

    #: Hypothesis ids a completed probe has already refuted, this generation.
    retired: Set[str] = field(default_factory=set)
    #: Probes fired since this generation opened. Reported, not capped -- the
    #: cap is `loop.MAX_PROBES_BETWEEN_THEORIZE`, and one cap is enough.
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
        the retirements are void: they were refutations of an older theory, and
        the questions are new questions. Returns True if this opened a new
        generation.

        Bookkeeping runs whether or not the economy is enabled, so a leg that
        left the change off still records how many generations its manual went
        through and how many probes each one bought. Only `filter_hypotheses`
        and `gate` are gated on `enabled`; counting is never a behaviour
        change.
        """
        key = frozenset(hypothesis_ids)
        if key == self._generation_key:
            return False
        self._generation_key = key
        self.generation += 1
        self.retired = set()
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

        Only the two refusals that belong to the *frontier* live here. The
        vacuous-streak stop and the repeat stop are `inner/loop.py`'s, computed
        off the record `ProbeLog` writes, and they apply whether or not this
        switch is on -- see `ProbeEconomyConfig`.

        Disabled: always allow, so the caller's own `entropy > 0` check plus
        the loop's unconditional refusals are the whole floor.
        """
        if not self.enabled:
            return True, ""
        cfg = self.config
        best = (design_report or {}).get("best") or {}
        bits = float(best.get("entropy_bits") or 0.0)

        # Only reachable once refutations are carried: the ablation frontier
        # is rebuilt whole every turn, so it can never collapse on its own.
        if n_frontier <= 1:
            return False, ("the frontier has collapsed to %d hypothesis: there "
                           "is nothing left to split" % n_frontier)

        if cfg.min_bits > 0.0 and bits < cfg.min_bits:
            return False, ("splits only %.4f bits, floor is %.4f"
                           % (bits, cfg.min_bits))

        return True, ""

    # -- results feed back -------------------------------------------------
    def record_fired(self) -> None:
        """One more action spent against the current frontier."""
        self.fired_this_generation += 1

    def observe(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Fold a probe result back into the frontier. Returns what it learnt.

        Vacuity is *read*, not recomputed. `ProbeLog.record_result` already
        decided it -- `information_gain_bits` returns 0.0 bits and
        `frontier_vacuous=True` for an empty posterior, and that is the number
        the result row carries and the loop counts its streak on. Recomputing
        `not survived` here would be a second opinion on one fact, and the two
        could drift. The fallback exists for rows written before that field did
        (the 2026-07-31 legs on disk), where an empty `survived` is the same
        statement in the older vocabulary.

        Like `note_frontier`, this runs whether or not the change is enabled.
        `filter_hypotheses` is the only place `retired` can alter behaviour, and
        it *is* gated -- so a leg that left the economy off still records in
        `probe_economy.json` exactly which hypotheses the change would have
        dropped, which is the counterfactual an A/B round wants to read.
        """
        survived = list(result.get("survived") or [])
        refuted = list(result.get("refuted") or [])
        off_frontier = (bool(result["frontier_vacuous"])
                        if "frontier_vacuous" in result else not survived)
        if not off_frontier and self.config.carry_refutations:
            # Only a probe that landed ON the frontier teaches anything about
            # which hypothesis is wrong. When nothing survived, the partition
            # itself was wrong, and "everyone is refuted" is a statement about
            # the frontier, not about its members.
            self.retired.update(i for i in refuted if i != "manual")
        return {"off_frontier": off_frontier,
                "n_survived": len(survived),
                "n_refuted": len(refuted),
                "retired_total": len(self.retired)}

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
                "min_bits": self.config.min_bits,
            },
            "generations": self.generation,
            "fired_this_generation": self.fired_this_generation,
            "probes_allowed": allowed,
            "probes_refused": refused,
            "refusal_reasons": dict(sorted(reasons.items())),
            "retired_hypotheses": sorted(self.retired),
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
    if economy is not None:
        # Generation bookkeeping runs either way; only the filtering and the
        # extra report block are gated, so a disabled economy leaves the report
        # byte-identical to one built without an economy at all.
        economy.note_frontier([h.id for h in full])
        if economy.enabled:
            hypotheses = economy.filter_hypotheses(full)
            economy_report = {
                "generation": economy.generation,
                "n_before": len(full),
                "n_after": len(hypotheses),
                "carried_refutations": sorted(economy.retired),
                "fired_this_generation": economy.fired_this_generation,
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
                      rationale: str = "",
                      identity: Optional[Dict[str, str]] = None) -> str:
        """`predictions` is what gets scored; `identity` is what names it.

        They differ only when `ProbeEconomy` has retired part of the frontier:
        then `predictions` is the live frontier (so `survived` and
        `information_gain_bits` are about hypotheses still standing) while
        `identity` is the full ablation set (so the fingerprint still means
        "this action, from this state, under this manual"). Absent, identity is
        the predictions -- which is the pre-economy call, unchanged.

        When they differ the row grows a `fingerprint_over` field naming the ids
        the hash was taken over, because a row that cannot explain its own
        fingerprint is not evidence. When they agree the field is omitted, so
        every row this arm has already written keeps its shape.
        """
        self.n += 1
        probe_id = "P-%02d" % self.n
        named_by = predictions if identity is None else identity
        mark = fingerprint(action, named_by)
        row = {"probe_id": probe_id, "phase": "design", "step_idx": step_idx,
               "action": action, "rationale": rationale,
               "fingerprint": mark,
               "repeat_of": self.asked.get(mark),
               "predictions": predictions, "design": design_report}
        if set(named_by) != set(predictions):
            # The row must be able to explain its own fingerprint. When the two
            # sets agree the hash is recomputable from `predictions` and this
            # field would be noise, so it is written only when they do not --
            # which also keeps every row the arm has ever written unchanged.
            row["fingerprint_over"] = sorted(named_by)
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
