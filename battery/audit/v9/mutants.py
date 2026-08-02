"""Mutants — the attack surface of the V9 defences, deliberately wider than
the tests that pin them.

`PREREG_V9.md` §3 R2: a defence that would move a metric back into the main
table must carry **more attack variants than tests**, and the variants must
reach past the tested condition.  The counting rule is fixed and unflattering
to me: *tests* = pytest items collected from
`battery/tests/test_v9_defences.py`; *mutants* = `mutant_*` builders in this
module.  A parametrised test that walks every mutant would make the two equal
and the discipline vacuous, so the sweep here is checked by **one** aggregate
test — the mutants explore, the tests pin a narrow property.

That is C11's lesson, which cost this project a night: eighteen mutants against
eighteen tests is not a mutation suite, it is the tests written twice.

Each mutant declares what it expects, and the expectation is part of the
evidence rather than a convenience:

* `refused=True`  — the defence must reject this record.
* `refused=False` — the defence must **not** reject it.  These are the mutants
  that matter most.  A defence that refuses everything is not a defence, it is
  a metric that has been switched off, and the cheapest way to fake process 4
  is to make every metric unanswerable.  Roughly a third of the mutants below
  are legitimate records sitting exactly on the boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

from battery.model import (Beat, Call, Clause, Concept, Repair, Run, Step,
                           Theory, Truth)


@dataclass(frozen=True)
class Mutant:
    """One probe at a defence's boundary."""

    defence: str          # D1 | D2 | D3
    metric_id: str
    name: str
    build: Callable[[], Run]
    refused: bool         # must the metric refuse this record?
    note: str


def _theory(**kwargs) -> Theory:
    return Theory(**kwargs)


# --- D1 · a share may not exceed one --------------------------------------

def mutant_D1_K1_exact() -> Mutant:
    return Mutant("D1", "K1", "K1-agree-equals-pairs",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              theory=Theory(replay_pairs=40, replay_agree=40)),
                  False, "a perfect replay is legitimate and must still score")


def mutant_D1_K1_over_by_one() -> Mutant:
    return Mutant("D1", "K1", "K1-agree-over-by-one",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              theory=Theory(replay_pairs=40, replay_agree=41)),
                  True, "one more agreement than pair; the smallest lie")


def mutant_D1_K1_wild() -> Mutant:
    return Mutant("D1", "K1", "K1-agree-sevenfold",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              theory=Theory(replay_pairs=1, replay_agree=7)),
                  True, "the blind attack's exact record: a share of 7.0")


def mutant_D1_K1_negative() -> Mutant:
    return Mutant("D1", "K1", "K1-agree-negative",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              theory=Theory(replay_pairs=40, replay_agree=-5)),
                  True, "the other end, which no attacker tried")


def mutant_D1_K2_over() -> Mutant:
    return Mutant("D1", "K2", "K2-agree-over",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              theory=Theory(held_out_pairs=3, held_out_agree=9,
                                            held_out_frame="exhaustive")),
                  True, "K2 carries the same ratio and nobody attacked it here")


def mutant_D1_K2_exact() -> Mutant:
    return Mutant("D1", "K2", "K2-agree-exact",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              theory=Theory(held_out_pairs=3, held_out_agree=3,
                                            held_out_frame="3 gaps")),
                  False, "A0's real shape; must survive the defence")


def mutant_D1_K4_over() -> Mutant:
    return Mutant("D1", "K4", "K4-coverage-over",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              theory=Theory(clauses=[
                                  Clause(name="c", kind="rule",
                                         coverage_num=9, coverage_den=3)])),
                  True, "nine witnesses out of three")


def mutant_D1_K4_mixed() -> Mutant:
    return Mutant("D1", "K4", "K4-one-bad-among-many",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              theory=Theory(clauses=[
                                  Clause(name="ok%d" % i, kind="rule",
                                         coverage_num=1, coverage_den=2)
                                  for i in range(20)] + [
                                  Clause(name="bad", kind="rule",
                                         coverage_num=5, coverage_den=1)])),
                  True, "one broken clause hidden in twenty sound ones")


def mutant_D1_K4_exact() -> Mutant:
    return Mutant("D1", "K4", "K4-fully-covered",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              theory=Theory(clauses=[
                                  Clause(name="c%d" % i, kind="rule",
                                         coverage_num=4, coverage_den=4)
                                  for i in range(5)])),
                  False, "complete coverage is legitimate")


def mutant_D1_K8_over() -> Mutant:
    return Mutant("D1", "K8", "K8-executable-over",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              theory=Theory(probes_designed=1,
                                            probes_executable=1000)),
                  True, "a share of one thousand")


def mutant_D1_K8_exact() -> Mutant:
    return Mutant("D1", "K8", "K8-all-executable",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              theory=Theory(probes_designed=9,
                                            probes_executable=9)),
                  False, "every probe runnable is the good case")


def _repair(**kwargs) -> Repair:
    base = dict(episode_id="e0", strategy="patch", changed_clause="c",
                repair_actions=4, baseline_actions=40)
    base.update(kwargs)
    return Repair(**base)


def mutant_D1_K12_short_requirement() -> Mutant:
    return Mutant("D1", "K12", "K12-six-of-one",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              repairs=[_repair(beats_required=1, beats=[
                                  Beat(tag="t%d" % i, name="b", closed=True)
                                  for i in range(6)])]),
                  True, "six closed beats against a declared requirement of 1")


def mutant_D1_K12_honest_six() -> Mutant:
    return Mutant("D1", "K12", "K12-six-of-six",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              repairs=[_repair(beats_required=6, beats=[
                                  Beat(tag="L%d" % i, name="b", closed=True)
                                  for i in range(6)])]),
                  False, "a complete honest loop must still score 1.0")


def mutant_D1_K12_partial() -> Mutant:
    return Mutant("D1", "K12", "K12-four-of-six",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              repairs=[_repair(beats_required=6, beats=[
                                  Beat(tag="L%d" % i, name="b", closed=i < 4)
                                  for i in range(6)])]),
                  False, "a partial loop is the metric's whole point")


def mutant_D1_M6_over() -> Mutant:
    return Mutant("D1", "M6", "M6-collateral-over",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              repairs=[_repair(invalidated_theorems=1000,
                                               theorems_before=1)]),
                  True, "a `share` of one thousand")


def mutant_D1_M6_exact() -> Mutant:
    return Mutant("D1", "M6", "M6-total-collateral",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              repairs=[_repair(invalidated_theorems=7,
                                               theorems_before=7)]),
                  False, "a repair that invalidated everything is real")


def mutant_D1_M6_hidden() -> Mutant:
    return Mutant("D1", "M6", "M6-one-bad-episode",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              repairs=[_repair(episode_id="a",
                                               invalidated_theorems=1,
                                               theorems_before=4),
                                       _repair(episode_id="b",
                                               invalidated_theorems=9,
                                               theorems_before=2)]),
                  True, "averaging hides the impossible episode")


# --- D2 · a delay may not run backwards -----------------------------------

def _truth(mechs) -> Truth:
    return Truth(mechanisms=mechs)


def mutant_D2_M1_zero() -> Mutant:
    return Mutant("D2", "M1", "M1-used-on-sight",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              truth=_truth({"g": {"first_seen": 7,
                                                  "first_used": 7}})),
                  False, "instant uptake is legitimate, if unlikely")


def mutant_D2_M1_minus_one() -> Mutant:
    return Mutant("D2", "M1", "M1-off-by-one",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              truth=_truth({"g": {"first_seen": 7,
                                                  "first_used": 6}})),
                  True, "an origin mismatch of one, the realistic bug")


def mutant_D2_M1_precognition() -> Mutant:
    return Mutant("D2", "M1", "M1-precognition",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              truth=_truth({"g": {"first_seen": 1000,
                                                  "first_used": 0}})),
                  True, "the blind attack's record: a delay of -1000")


def mutant_D2_M1_one_bad() -> Mutant:
    return Mutant("D2", "M1", "M1-one-bad-among-twenty",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              truth=_truth(dict(
                                  [("g%d" % i, {"first_seen": i,
                                                "first_used": i + 3})
                                   for i in range(20)]
                                  + [("bad", {"first_seen": 50,
                                              "first_used": 0})]))),
                  True, "one negative delay dragging a mean of twenty")


def mutant_D2_M4_zero() -> Mutant:
    return Mutant("D2", "M4", "M4-instant-detection",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              repairs=[_repair(detected=True,
                                               detection_actions=0)]),
                  False, "a rule that breaks on the first action is real")


def mutant_D2_M4_negative() -> Mutant:
    return Mutant("D2", "M4", "M4-negative-detection",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              repairs=[_repair(detected=True,
                                               detection_actions=-500)]),
                  True, "detection before injection")


def mutant_D2_M4_via_notes() -> Mutant:
    return Mutant("D2", "M4", "M4-negative-through-notes",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              repairs=[_repair(
                                  detected=False,
                                  notes={"earliest_detection": -3})]),
                  True, "the notes path outranks `detected`; it needs the "
                        "same guard, and no attacker probed it")


def mutant_D2_M4_large_honest() -> Mutant:
    return Mutant("D2", "M4", "M4-slow-but-honest",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              repairs=[_repair(detected=True,
                                               detection_actions=9000)]),
                  False, "a very late detection is a bad arm, not a bad record")


# --- D3 · an unpriced call is not a free one ------------------------------

def _call(idx: int, price, turn=None, tokens=1000) -> Call:
    return Call(idx=idx, input_tokens=tokens, cost_usd=price, turn=turn,
                prompt_chars=tokens * 4)


def _priced_run(prices, steps=6) -> Run:
    # `turn=i` is one call per turn, stated rather than inferred.  These are D3
    # mutants -- price completeness -- and not one of them is about the turn
    # axis, so the axis has to be present and uninteresting for the price gate
    # to be what is under test.  Through S46 `turn_costs()` manufactured this
    # same labelling from the call's position; now that the fallback is gone,
    # the fixture says out loud what it always meant.
    return Run(run_id="m", arm="m", source="v9",
               steps=[Step(idx=i, action="a", state_key="s%d" % i)
                      for i in range(steps)],
               calls=[_call(i, p, turn=i) for i, p in enumerate(prices)])


def mutant_D3_all_priced() -> Mutant:
    return Mutant("D3", "E1", "E1-fully-priced",
                  lambda: _priced_run([0.5] * 12),
                  False, "an ordinary complete bill")


def mutant_D3_explicit_zero() -> Mutant:
    return Mutant("D3", "E1", "E1-explicit-zero",
                  lambda: _priced_run([0.5] * 11 + [0.0]),
                  False, "a call that genuinely cost nothing is priced at "
                         "zero and must not be confused with an unpriced one")


def mutant_D3_one_missing() -> Mutant:
    return Mutant("D3", "E1", "E1-one-unpriced",
                  lambda: _priced_run([0.5] * 11 + [None]),
                  True, "a single gap; the smallest form of the attack")


def mutant_D3_head_missing() -> Mutant:
    return Mutant("D3", "E1", "E1-unpriced-head",
                  lambda: _priced_run([None] * 6 + [0.5] * 6),
                  True, "gaps at the front, which flatter E3 instead of E2")


def mutant_D3_tail_only_priced() -> Mutant:
    return Mutant("D3", "E1", "E1-only-first-priced",
                  lambda: _priced_run([1.0] + [None] * 199, steps=200),
                  True, "the blind attack's record: 1 of 200 priced")


def mutant_D3_E2_unpriced_tail() -> Mutant:
    return Mutant("D3", "E2", "E2-unpriced-tail",
                  lambda: _priced_run([1.0, 1.0, 1.0] + [None] * 37),
                  True, "the shape attack; E2 read 1.0 before the defence")


def mutant_D3_E2_priced_flat() -> Mutant:
    return Mutant("D3", "E2", "E2-flat-and-complete",
                  lambda: _priced_run([1.0] * 40),
                  False, "a flat complete bill must still score 0.25")


def mutant_D3_E3_padded() -> Mutant:
    return Mutant("D3", "E3", "E3-padded-unpriced",
                  lambda: _priced_run([1.0, 1.0] + [None] * 398, steps=20),
                  True, "400 turns, 2 priced; E3 read 0.005")


def mutant_D3_E3_zero_padded() -> Mutant:
    return Mutant("D3", "E3", "E3-padded-with-real-zeros",
                  lambda: _priced_run([1.0, 1.0] + [0.0] * 98),
                  False, "the same shape, honestly priced: still computable, "
                         "and this is the case the defence must NOT catch")


def mutant_D3_E5_unpriced() -> Mutant:
    return Mutant("D3", "E5", "E5-unpriced-calls",
                  lambda: _priced_run([1.0] + [None] * 499, steps=400),
                  True, "cost per action collapses when calls are free")


def mutant_D3_E5_priced() -> Mutant:
    return Mutant("D3", "E5", "E5-priced",
                  lambda: _priced_run([0.01] * 20, steps=400),
                  False, "a cheap arm is not an unpriced one")


def mutant_D3_turn_labelled() -> Mutant:
    return Mutant("D3", "E2", "E2-unpriced-under-one-turn-label",
                  lambda: Run(run_id="m", arm="m", source="v9",
                              steps=[Step(idx=i, action="a",
                                          state_key="s%d" % i)
                                     for i in range(6)],
                              calls=[_call(i, 1.0 if i < 4 else None,
                                           turn=0 if i < 30 else i)
                                     for i in range(40)]),
                  True, "the batching attack and the pricing attack combined; "
                        "neither attacker tried the pair")


def all_mutants() -> List[Mutant]:
    """Every `mutant_*` builder in this module, discovered by name."""
    out: List[Mutant] = []
    for name in sorted(globals()):
        if not name.startswith("mutant_"):
            continue
        value = globals()[name]
        if callable(value):
            out.append(value())
    return out


def sweep() -> List[Dict[str, object]]:
    """Run every mutant through the live metric and report what happened."""
    from battery.metrics import evaluate

    rows: List[Dict[str, object]] = []
    for mutant in all_mutants():
        value = evaluate(mutant.build())[mutant.metric_id]
        refused = (not value.ok) or value.value is None
        rows.append({
            "defence": mutant.defence,
            "metric": mutant.metric_id,
            "name": mutant.name,
            "expected_refusal": mutant.refused,
            "refused": refused,
            "status": value.status,
            "value": value.value,
            "reason": value.reason,
            "agrees": refused == mutant.refused,
            "note": mutant.note,
        })
    return rows


def counts() -> Dict[str, int]:
    out: Dict[str, int] = {}
    for mutant in all_mutants():
        out[mutant.defence] = out.get(mutant.defence, 0) + 1
    out["total"] = len(all_mutants())
    return out
