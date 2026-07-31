"""Two threat models, and the question of which one V9 actually measured.

`battery/audit/v9/` demoted 37 of 38 metrics and withheld the 38th, so the
main table is empty and E2 -- a Phase 4 primary endpoint -- has nothing under
it. `STATUS.md` reports that as a finding. This module asks whether it is one.

**The suspicion, stated so it can be wrong.** A blind attacker in V9 writes a
zero-argument builder that returns a `Run` dataclass. That is: the attacker
*is* the recorder. Every battery metric is a total function of a `Run`, so if
the attacker authors the `Run`, "can this metric be pushed past a threshold"
reduces to "is the threshold attainable by any record at all" -- which is a
property of the threshold, not of the metric. A universal demotion is what a
tautology looks like from the outside, and 37/38 is very close to universal.

**W-12 already named the distinction** and said the paper must keep it: "一条
臂能不能自己走到那个分数, 和 生产者/适配器 写下那个值, 是两件事, 而电池对两者
一视同仁地信任." V9 scored both as gaming. This module separates them:

* **T-REC** -- the recorder is adversarial. The attacker writes the ledger.
  Under T-REC every metric over a self-reported record is gameable, and that
  is a theorem about passive instruments, not a measurement of any metric.
  V9 ran under T-REC.
* **T-ARM** -- the recorder is honest, the arm is adversarial. The arm chooses
  actions, prompts and when to stop; the harness stamps indices, prices and
  ordering. An attack only counts here if the `Run` it lays out is one a real
  harness *could have emitted while an arm played*.

Narrowing a threat model is exactly how an audit gets laundered, so the
narrowing is not allowed to be an opinion:

1. **Every invariant is validated against the real corpus before it may
   judge anything.** `validate()` runs each candidate over every `Run` the
   battery can load. An invariant that any real run violates is **dropped**,
   with the counterexample recorded in the artefact. A rule that would call
   real recorded play "impossible" is not a description of the recorder.
2. **The narrowing must be seen to say yes as well as no.** If T-ARM cleared
   every attack it would be a whitewash, and `assert_not_vacuous()` refuses
   that outcome: at least one attack must survive the filter *and still land*.
   The test suite asserts both directions.
3. **T-ARM does not promote anything.** `PREREG_V9.md` R1 -- V9 demotes, V9
   never promotes -- binds this file too. Nothing here changes `tier_of`.
   A metric with no arm-reachable attack left is reported as exactly that, and
   the route back to the main table is still process 1 (discrimination).

    python -m battery.audit.threat          # writes the tracked artefact
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from battery.model import Run

HERE = os.path.dirname(os.path.abspath(__file__))
BATTERY = os.path.dirname(HERE)
REPO = os.path.dirname(BATTERY)

DEFAULT_OUT = os.path.join(BATTERY, "artifacts_live", "threat_model.json")


# --------------------------------------------------------------------------
# The recorder's guarantees, as predicates.
#
# Each returns None when the run satisfies the invariant, or a short string
# naming the violation. They are written about the *harness*, never about the
# arm: "the arm played badly" must never be a violation, or T-ARM would be
# filtering out honest incompetence, which is precisely the behaviour E2 is
# supposed to be able to see.
# --------------------------------------------------------------------------

def _i_calls_imply_steps(run: Run) -> Optional[str]:
    if run.calls and not run.steps:
        return ("%d model call(s) and 0 steps: a harness bills a decision it "
                "then executes" % len(run.calls))
    return None


def _i_turn_indexes_a_step(run: Run) -> Optional[str]:
    n = len(run.steps)
    for call in run.calls:
        if call.turn is None:
            continue
        if call.turn < 0 or call.turn >= n:
            return ("call %d declares turn=%s with %d step(s): the turn index "
                    "is stamped from the decision being taken"
                    % (call.idx, call.turn, n))
    return None


def _i_distinct_turns_le_steps(run: Run) -> Optional[str]:
    turns = {c.turn for c in run.calls if c.turn is not None}
    if turns and len(turns) > len(run.steps):
        return ("%d distinct turn label(s) over %d step(s)"
                % (len(turns), len(run.steps)))
    return None


def _i_turn_follows_call_order(run: Run) -> Optional[str]:
    seen = -1
    for call in sorted(run.calls, key=lambda c: c.idx):
        if call.turn is None:
            continue
        if call.turn < seen:
            return ("turn labels fall as call order rises (call %d -> turn "
                    "%d after turn %d): the recorder appends"
                    % (call.idx, call.turn, seen))
        seen = call.turn
    return None


def _i_step_idx_unique(run: Run) -> Optional[str]:
    idxs = [s.idx for s in run.steps]
    if len(idxs) != len(set(idxs)):
        return "step indices repeat: the recorder appends one row per step"
    return None


def _i_pricing_all_or_nothing(run: Run) -> Optional[str]:
    priced = [c for c in run.calls if c.cost_usd is not None]
    if priced and len(priced) != len(run.calls):
        return ("%d of %d calls carry no price: a billing logger that drops "
                "out mid-run is a broken recorder, not an arm"
                % (len(run.calls) - len(priced), len(run.calls)))
    return None


def _i_call_step_idx_in_range(run: Run) -> Optional[str]:
    known = {s.idx for s in run.steps}
    for call in run.calls:
        if call.step_idx is not None and call.step_idx not in known:
            return ("call %d points at step_idx=%s, which the run does not "
                    "record" % (call.idx, call.step_idx))
    return None


def _i_theory_implies_play(run: Run) -> Optional[str]:
    if run.theory is not None and not run.steps:
        return "a manual with no recorded step behind it"
    return None


def _i_concept_first_seen_in_range(run: Run) -> Optional[str]:
    if run.theory is None:
        return None
    n = len(run.steps)
    for concept in run.theory.concepts:
        if concept.first_seen_step is None:
            continue
        if concept.first_seen_step < 0 or concept.first_seen_step >= n:
            return ("concept %r first_seen_step=%s with %d step(s)"
                    % (concept.name, concept.first_seen_step, n))
    return None


def _i_coverage_is_a_fraction(run: Run) -> Optional[str]:
    if run.theory is None:
        return None
    for clause in run.theory.clauses:
        num, den = clause.coverage_num, clause.coverage_den
        if num is None or den is None:
            continue
        if den <= 0 or num > den or num < 0:
            return ("clause %r declares coverage %s/%s"
                    % (clause.name, num, den))
    return None


#: id -> (one-line statement of what the recorder guarantees, predicate)
CANDIDATE_INVARIANTS: Dict[str, Tuple[str, Callable[[Run], Optional[str]]]] = {
    "I1": ("a billed model call belongs to a step the arm then took",
           _i_calls_imply_steps),
    "I2": ("a call's turn label indexes a step the run records",
           _i_turn_indexes_a_step),
    "I3": ("there are no more distinct turns than there are steps",
           _i_distinct_turns_le_steps),
    "I4": ("turn labels do not fall as call order rises",
           _i_turn_follows_call_order),
    "I5": ("step indices are unique -- the recorder appends",
           _i_step_idx_unique),
    "I6": ("a run is priced completely or not at all",
           _i_pricing_all_or_nothing),
    "I7": ("a call's step_idx points at a step the run records",
           _i_call_step_idx_in_range),
    "I8": ("a manual is written by an arm that played",
           _i_theory_implies_play),
    "I9": ("a concept's first sighting indexes a step the run records",
           _i_concept_first_seen_in_range),
    "I10": ("declared clause coverage is a fraction of its own denominator",
            _i_coverage_is_a_fraction),
}


# --------------------------------------------------------------------------
# Validation against the real corpus -- the part that keeps this honest.
# --------------------------------------------------------------------------

def real_runs() -> List[Run]:
    """Every `Run` the battery can load on this tree, live legs included.

    Deliberately tolerant: an absent optional source (the untracked shards,
    the upstream Schema traces) yields fewer runs rather than an exception,
    and the count goes into the artefact so a thin corpus is visible instead
    of quietly weakening the validation.
    """
    import sys
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from battery.guard import load_piles
    from battery.run_battery import collect_runs

    piles = load_piles()
    return list(collect_runs(piles))


def validate(runs: Sequence[Run]) -> Dict[str, object]:
    """Keep only the invariants no real run violates.

    An invariant a real recorded run breaks is a false description of the
    recorder, and using it to dismiss an attack would be dismissing the attack
    for resembling reality. Dropped ones are reported with the run that
    dropped them, so the corpus can overrule the author.
    """
    kept: List[str] = []
    dropped: List[Dict[str, str]] = []
    for inv_id in sorted(CANDIDATE_INVARIANTS, key=_num):
        statement, predicate = CANDIDATE_INVARIANTS[inv_id]
        counterexample = None
        for run in runs:
            try:
                violation = predicate(run)
            except Exception as exc:                       # pragma: no cover
                violation = "predicate raised %s" % type(exc).__name__
            if violation:
                counterexample = {"run_id": run.run_id, "arm": run.arm,
                                  "source": run.source, "violation": violation}
                break
        if counterexample is None:
            kept.append(inv_id)
        else:
            dropped.append({"invariant": inv_id, "statement": statement,
                            **counterexample})
    return {"kept": kept, "dropped": dropped, "n_real_runs": len(runs)}


def _num(inv_id: str) -> int:
    return int(inv_id[1:])


def violations(run: Run, kept: Sequence[str]) -> List[Dict[str, str]]:
    """Every validated invariant this run breaks."""
    out: List[Dict[str, str]] = []
    for inv_id in sorted(kept, key=_num):
        statement, predicate = CANDIDATE_INVARIANTS[inv_id]
        try:
            violation = predicate(run)
        except Exception as exc:                           # pragma: no cover
            violation = "predicate raised %s" % type(exc).__name__
        if violation:
            out.append({"invariant": inv_id, "statement": statement,
                        "violation": violation})
    return out


def reachability(run: Run, kept: Sequence[str]) -> str:
    """`arm-reachable` if an honest recorder could have emitted this run."""
    return "recorder-only" if violations(run, kept) else "arm-reachable"


# --------------------------------------------------------------------------
# Re-adjudication under T-ARM.
# --------------------------------------------------------------------------

def build(out_of_scope: bool = False) -> Dict[str, object]:
    """The whole comparison: V9 under T-REC, the same attacks under T-ARM."""
    import sys
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from battery.audit.v9.verdict import collect_attacks, judge
    from battery.metrics import REGISTRY

    runs = real_runs()
    validation = validate(runs)
    kept = validation["kept"]

    attacks: Dict[str, List[Dict[str, object]]] = {}
    for metric_id, group in collect_attacks().items():
        rows: List[Dict[str, object]] = []
        for attack in group:
            verdict = judge(attack)
            run = attack.build()
            broken = violations(run, kept)
            rows.append({
                "attack": attack.name,
                "t_rec_landed": bool(verdict.get("succeeded")),
                "value": verdict.get("value"),
                "target": verdict.get("target"),
                "reachability": "recorder-only" if broken else "arm-reachable",
                "breaks": [b["invariant"] for b in broken],
                "breaks_detail": broken,
                # T-ARM: a landed attack only counts if an honest recorder
                # could have produced the record it needed.
                "t_arm_landed": bool(verdict.get("succeeded")) and not broken,
                "claim": verdict.get("claim"),
            })
        attacks[metric_id] = sorted(rows, key=lambda r: r["attack"])

    metrics: Dict[str, Dict[str, object]] = {}
    for metric_id in sorted(REGISTRY):
        rows = attacks.get(metric_id, [])
        t_rec = [r for r in rows if r["t_rec_landed"]]
        t_arm = [r for r in rows if r["t_arm_landed"]]
        metrics[metric_id] = {
            "n_attacks": len(rows),
            "t_rec_landed": sorted(r["attack"] for r in t_rec),
            "t_arm_landed": sorted(r["attack"] for r in t_arm),
            "narrowed_away": sorted(r["attack"] for r in t_rec
                                    if not r["t_arm_landed"]),
            "attacks": rows,
        }

    survives_t_arm = sorted(m for m in metrics
                            if metrics[m]["n_attacks"]
                            and not metrics[m]["t_arm_landed"])
    gameable_t_rec = sorted(m for m in metrics if metrics[m]["t_rec_landed"])
    gameable_t_arm = sorted(m for m in metrics if metrics[m]["t_arm_landed"])

    total_attacks = sum(len(v) for v in attacks.values())
    landed_rec = sum(len(metrics[m]["t_rec_landed"]) for m in metrics)
    landed_arm = sum(len(metrics[m]["t_arm_landed"]) for m in metrics)

    return {
        "what": ("V9's blind attacks re-judged under a narrower threat model. "
                 "T-REC (V9's own): the attacker writes the ledger. T-ARM: "
                 "the recorder is honest and only the arm is adversarial, so "
                 "an attack counts only if an honest harness could have "
                 "emitted the record. The invariants defining 'could have' "
                 "are validated against every real run first; one a real run "
                 "breaks is dropped, with the counterexample. Nothing here "
                 "promotes a metric -- PREREG_V9 R1 binds this file too."),
        "prereg_r1": ("T-ARM does not move any tier. `battery.audit.gaming."
                      "tier_of` is untouched; the route back to the main "
                      "table is process 1, not process 4."),
        "invariants": {k: v[0] for k, v in sorted(
            CANDIDATE_INVARIANTS.items(), key=lambda kv: _num(kv[0]))},
        "validation": validation,
        "n_attacks": total_attacks,
        "n_landed_t_rec": landed_rec,
        "n_landed_t_arm": landed_arm,
        "gameable_under_t_rec": gameable_t_rec,
        "gameable_under_t_arm": gameable_t_arm,
        "no_arm_reachable_attack_left": survives_t_arm,
        "metrics": metrics,
    }


def assert_not_vacuous(doc: Dict[str, object]) -> None:
    """Refuse a narrowing that cleared everything, or that cleared nothing.

    Both degenerate outcomes are failures of the instrument rather than
    findings about the metrics: a filter that clears every attack has replaced
    the audit with an opinion, and one that clears none has not narrowed
    anything and should not be published as a narrowing.
    """
    if int(doc["n_landed_t_arm"]) <= 0:
        raise ValueError(
            "T-ARM cleared every attack (%d/%d landed): a filter that never "
            "says yes is a whitewash, not a threat model"
            % (doc["n_landed_t_arm"], doc["n_landed_t_rec"]))
    if int(doc["n_landed_t_arm"]) >= int(doc["n_landed_t_rec"]):
        raise ValueError(
            "T-ARM removed nothing (%d of %d attacks still land): this is not "
            "a narrowing and must not be published as one"
            % (doc["n_landed_t_arm"], doc["n_landed_t_rec"]))


def serialise(doc: Dict[str, object]) -> str:
    return json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write(out_path: str = DEFAULT_OUT) -> str:
    from battery.audit.live_tiers import refuse_frozen_destination
    resolved = refuse_frozen_destination(out_path)
    doc = build()
    assert_not_vacuous(doc)
    os.makedirs(os.path.dirname(resolved), exist_ok=True)
    with open(resolved, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(serialise(doc))
    return resolved


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="re-judge the V9 attacks under a narrowed threat model")
    parser.add_argument("--out", default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    try:
        path = write(args.out)
    except ValueError as exc:
        print("REFUSED: %s" % exc)
        return 2
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
