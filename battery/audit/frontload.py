"""E2L — the front-load index on the step axis, and the audit of it.

`Theoria.md:319` defines the front-load index as 前 k% 回合花掉的成本占比, and
`freeze/STATS_RULES.md` makes the paired difference on it one of Phase 4's
three primary endpoints. The battery's `E2` implements it with the turn axis
taken from `Call.turn` -- a label the harness writes -- and V9's blind attack
`batched-turn-label` reads 0.973 out of a bill that never front-loads at all,
purely by stamping thirty equal calls `turn=0`.

E2L changes exactly one thing: **the axis**. Cost is attributed to the step the
call was made at, and the head is the first quarter of the steps the arm
actually took. A turn label is a batching convention; a step ordinal is the
environment answering.

Everything in `PREREG_E2L.md` §1--§2 is implemented here and nothing else is.
The five refusal conditions matter more than the number: `G4` in particular
refuses to fall back to call order when the axis cannot be rebuilt, which is
the fallback that lets E2 be decided by a missing field.

This module deliberately does **not** register E2L in `battery.metrics`. A
metric in the registry is a metric in the recompute, the spectrum and the
freeze record, and E2L has not passed process 1 -- `PREREG_E2L.md` §0 says it
starts at the beginning. It lives here, is computed here, and is published
beside E2 rather than instead of it.

    python -m battery.audit.frontload        # writes the tracked artefact
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Optional, Tuple

from battery.metrics.economy import _cost_through
from battery.model import Call, Run, Step

HERE = os.path.dirname(os.path.abspath(__file__))
BATTERY = os.path.dirname(HERE)
REPO = os.path.dirname(BATTERY)

DEFAULT_OUT = os.path.join(BATTERY, "artifacts_live", "frontload_e2l.json")
LIVE_ROOT = os.path.join(REPO, "theoria-arm", "runs")

#: PREREG_E2L §1
FRONTLOAD_K = 0.25
#: PREREG_E2L §2 G3 -- E2's own early-exit floor, unchanged.
MIN_STEPS_FOR_SHAPE = 8
#: PREREG_E2L §2 G5 -- distinct new states after the head.
MIN_POST_HEAD_STATES = 2
#: PREREG_E2L §3 -- bounded [0,1], direction higher, so PREREG_V9 §1.2 gives
#: 0.95. Written here so an attack can be judged without a second table.
TARGET = 0.95
DIRECTION = "higher"


class Reading(Dict[str, object]):
    """A status/value pair shaped like `battery.metrics.Value`, kept local."""


def _reading(status: str, value: Optional[float], reason: str,
             **support: Any) -> Dict[str, object]:
    row: Dict[str, object] = {"metric": "E2L", "status": status,
                              "value": value, "reason": reason}
    if support:
        row["support"] = dict(sorted(support.items()))
    return row


def frontload_step_index(run: Run) -> Dict[str, object]:
    """E2L for one run. `PREREG_E2L.md` §1--§2, in order.

    The gates are checked in the pre-registered order and each one returns
    rather than degrading to a number. `unsound` means the record cannot
    support the question; `thin` means the run cannot. Neither is a low score,
    and V9 S1 counts both as the battery declining to answer.
    """
    calls = sorted(run.calls, key=lambda c: c.idx)
    if not calls:
        return _reading("not-applicable", None,
                        "no model calls: the economy family has no material")

    # G1 -- V9-D3. An unpriced call is not a free one.
    missing = sum(1 for c in calls if c.cost_usd is None)
    if missing:
        return _reading("unsound", None,
                        "%d of %d model calls carry no price; the shape of a "
                        "bill cannot be read from a partial bill"
                        % (missing, len(calls)))

    total = sum(float(c.cost_usd or 0.0) for c in calls)
    # G2
    if total <= 0:
        return _reading("thin", None, "total cost is zero")

    steps = sorted(run.steps, key=lambda s: s.idx)
    n_steps = len(steps)
    # G3
    if n_steps < MIN_STEPS_FOR_SHAPE:
        return _reading("thin", None,
                        "fewer than %d steps; a short run is trivially "
                        "front-loaded" % MIN_STEPS_FOR_SHAPE)

    # G4 -- the axis, or nothing. No fallback to call order.
    unanchored = [c.idx for c in calls
                  if c.step_idx is None and float(c.cost_usd or 0.0) > 0]
    if unanchored:
        return _reading("unsound", None,
                        "%d priced call(s) carry no step_idx; the step axis "
                        "cannot be rebuilt and E2L does not fall back to "
                        "call order -- that fallback is how a missing label "
                        "decides the value" % len(unanchored),
                        unanchored_calls=len(unanchored))

    order = {s.idx: i for i, s in enumerate(steps)}
    per_step = [0.0] * n_steps
    for call in calls:
        position = order.get(call.step_idx)
        if position is None:
            return _reading("unsound", None,
                            "call %d is billed at step_idx=%s, which the run "
                            "does not record" % (call.idx, call.step_idx))
        per_step[position] += float(call.cost_usd or 0.0)

    head_mark = n_steps * FRONTLOAD_K
    head = _cost_through(per_step, head_mark)

    # G5 -- the coasting has to go somewhere.
    head_steps = int(head_mark)
    before = {s.state_key for s in steps[:head_steps] if s.state_key}
    after = {s.state_key for s in steps[head_steps:] if s.state_key}
    new_after = after - before
    if len(new_after) < MIN_POST_HEAD_STATES:
        return _reading("thin", None,
                        "%d new state(s) reached after the head; paying up "
                        "front and then not moving is not front-loading, it "
                        "is stopping" % len(new_after),
                        new_states_after_head=len(new_after),
                        steps=n_steps)

    return _reading("ok", head / total,
                    "share of cost billed in the first %.0f%% of steps"
                    % (FRONTLOAD_K * 100),
                    steps=n_steps,
                    head_steps=round(head_mark, 9),
                    billed_calls=len(calls),
                    new_states_after_head=len(new_after),
                    total_usd=round(total, 9))


def meets_target(value: Optional[float]) -> bool:
    """S2 for E2L. `higher`, bounded, so PREREG_V9 §1.2 gives >= 0.95."""
    return value is not None and value >= TARGET


# --------------------------------------------------------------------------
# Probes -- the attacks written against my own narrowing.
#
# `audit/threat.py` reports that E2 has no arm-reachable attack left. That
# clearance is suspicious on its face: every economy attack in V9 was written
# with `steps=[]`, because the attacker only needed calls to move the metric.
# Attaching steps is pure layout, which the poverty certificate permits, so
# the clearance may be an artefact of how six attackers happened to write
# their builders rather than a fact about E2.
#
# These builders test that. They must be judged by the same machinery: the
# poverty certificate (`v9/check.py`), the validated invariants
# (`audit/threat.py`), and the pre-registered target. If they land, T-ARM does
# not clear E2 and the report has to say so.
# --------------------------------------------------------------------------

def build_E2_batched_turn_label_coherent() -> Run:
    """`batched-turn-label`, repaired so an honest recorder could emit it.

    Forty steps, forty calls, every call anchored to the step it was made at,
    turn labels non-decreasing and inside the step range, every call priced.
    The only thing carried over from the original attack is the batching
    convention: the first thirty calls are all labelled `turn=0`.
    """
    return Run(
        run_id="tarm-E2-batched-coherent", arm="attacker", source="tarm-probe",
        steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i)
               for i in range(40)],
        calls=[Call(idx=i, step_idx=i, turn=(0 if i < 30 else i - 29),
                    cost_usd=(1.0 if i < 30 else 0.1), input_tokens=5000)
               for i in range(40)])


def build_E2_first_turn_bill_coherent() -> Run:
    """`first-turn-bill`, repaired the same way.

    Forty steps, the whole bill on the first one, thirty-nine free steps
    after it. Under T-ARM this is not a lie by the recorder -- it is a
    perfectly ordinary shape for a harness that bills one large system prompt
    and then runs a cheap loop.
    """
    return Run(
        run_id="tarm-E2-first-turn-coherent", arm="attacker",
        source="tarm-probe",
        steps=[Step(idx=i, action="a%d" % i, state_key="s%d" % i)
               for i in range(40)],
        calls=[Call(idx=i, step_idx=i, turn=i,
                    cost_usd=(1.0 if i == 0 else 0.0), input_tokens=1000)
               for i in range(40)])


def build_E2_first_turn_bill_frozen_world() -> Run:
    """The same bill, but the arm never moves after paying.

    G5's target case: pay everything up front, then press one button forever.
    Kept as a probe rather than a test fixture because a defence has to be
    seen refusing something it was not written against, and this is the shape
    `PREREG_E2L.md` §2 names.
    """
    return Run(
        run_id="tarm-E2-frozen-world", arm="attacker", source="tarm-probe",
        steps=[Step(idx=i, action="noop", state_key="s0") for i in range(40)],
        calls=[Call(idx=i, step_idx=i, turn=i,
                    cost_usd=(1.0 if i == 0 else 0.0), input_tokens=1000)
               for i in range(40)])


PROBES: Tuple[Tuple[str, Any, str], ...] = (
    ("batched-turn-label-coherent", build_E2_batched_turn_label_coherent,
     "thirty equal calls labelled turn=0, but every one of them anchored to "
     "a real step: the batching convention survives, the impossible record "
     "does not"),
    ("first-turn-bill-coherent", build_E2_first_turn_bill_coherent,
     "the whole bill on step 0 of 40, the rest free and still moving"),
    ("first-turn-bill-frozen-world", build_E2_first_turn_bill_frozen_world,
     "the whole bill on step 0 of 40, and then one button pressed forever"),
)


def probe_table() -> List[Dict[str, object]]:
    """Judge every probe against E2 and E2L, with certificate and invariants.

    Nothing is taken on this module's word: the value comes from the live
    metric, the certificate from `v9/check.py`, the reachability from the
    corpus-validated invariants in `audit/threat.py`.
    """
    import sys
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from battery.audit.threat import reachability, validate, violations
    from battery.audit.v9 import prereg
    from battery.audit.v9.check import certificate
    from battery.audit.threat import real_runs
    from battery.metrics import evaluate

    kept = validate(real_runs())["kept"]

    rows: List[Dict[str, object]] = []
    for name, builder, note in PROBES:
        run = builder()
        cert = certificate(builder)
        broken = violations(run, kept)
        e2 = evaluate(run)["E2"]
        e2l = frontload_step_index(run)
        rows.append({
            "probe": name,
            "note": note,
            "poverty_certified": bool(cert["ok"]),
            "certificate_violations": cert["violations"],
            "reachability": reachability(run, kept),
            "breaks": [b["invariant"] for b in broken],
            "E2": {"status": e2.status, "value": e2.value,
                   "target": prereg.target_for("E2"),
                   "S2_reached_target": bool(
                       e2.value is not None and e2.value >= 0.95)},
            "E2L": {"status": e2l["status"], "value": e2l["value"],
                    "reason": e2l["reason"], "target": TARGET,
                    "S2_reached_target": meets_target(e2l["value"])},
            # S1 ∧ S2 ∧ S3 ∧ S4, all four, per PREREG_E2L §3.
            "lands_on_E2": bool(
                e2.ok and e2.value is not None and e2.value >= 0.95
                and cert["ok"] and not broken),
            "lands_on_E2L": bool(
                e2l["status"] == "ok" and meets_target(e2l["value"])
                and cert["ok"] and not broken),
        })
    return rows


# --------------------------------------------------------------------------
# The live legs.
# --------------------------------------------------------------------------

def _leg_curves(path: str) -> Optional[Dict[str, Any]]:
    curves = os.path.join(path, "curves.json")
    if not os.path.isfile(curves):
        return None
    with open(curves, encoding="utf-8") as fh:
        return json.load(fh)


def leg_reading(slug: str, path: str) -> Dict[str, object]:
    """E2L on one live leg, read off the archive's own turn/step join.

    Deliberately **not** routed through `battery/adapters/theoria_live.py`.
    That adapter sets `Call.step_idx = None` on every call, and populating it
    would move `P2`'s live reading too (`battery/metrics/planning.py:50` reads
    the same field) -- a side effect that belongs to its own ticket, and
    `PREREG_E2L.md` §5 says so. So the axis is rebuilt here from `curves.json`
    rows, and the join's own confidence label travels with the number instead
    of being dropped.
    """
    curves = _leg_curves(path)
    if curves is None:
        return {"leg": slug, "status": "not-applicable",
                "reason": "no curves.json"}

    rows = curves.get("rows") or []
    priced = [r for r in rows if float(r.get("usd") or 0.0) > 0]
    total = sum(float(r.get("usd") or 0.0) for r in rows)
    anchored = [r for r in priced if r.get("step_idx") is not None]

    base: Dict[str, object] = {
        "leg": slug,
        "game_id": curves.get("game_id"),
        "join_confidence": curves.get("join_confidence"),
        "turn_rows": len(rows),
        "priced_rows": len(priced),
        "anchored_priced_rows": len(anchored),
        "total_usd": round(total, 9),
    }

    if total <= 0:                                              # G2
        return {**base, "status": "thin", "value": None,
                "reason": "total cost is zero"}
    if len(anchored) != len(priced):                            # G4
        return {**base, "status": "unsound", "value": None,
                "reason": "%d of %d priced turn(s) carry no step_idx"
                          % (len(priced) - len(anchored), len(priced))}

    # The step axis: the archive records a step ordinal only where a decision
    # was taken, so the axis length is the last recorded ordinal, which is the
    # number of environment actions the leg got through.
    last = max(int(r["step_idx"]) for r in anchored)
    n_steps = last + 1
    if n_steps < MIN_STEPS_FOR_SHAPE:                           # G3
        return {**base, "status": "thin", "value": None, "steps": n_steps,
                "reason": "fewer than %d steps" % MIN_STEPS_FOR_SHAPE}

    per_step = [0.0] * n_steps
    for row in anchored:
        per_step[int(row["step_idx"])] += float(row.get("usd") or 0.0)

    head_mark = n_steps * FRONTLOAD_K
    head = _cost_through(per_step, head_mark)

    # Axis sensitivity, carried with the number rather than left in a
    # footnote. `n_steps` is a lower bound -- the archive stamps an ordinal
    # only where a decision was taken -- so a reading of 0.0 is only as solid
    # as the gap between the leg's real action count and the axis length at
    # which the head would first reach the first priced step.
    first_priced = min(int(r["step_idx"]) for r in anchored)
    actions = sum(int(r.get("actions_taken") or 0) for r in rows)
    break_even = first_priced / FRONTLOAD_K

    return {**base, "status": "ok", "value": head / total, "steps": n_steps,
            "head_steps": round(head_mark, 9),
            "first_priced_step": first_priced,
            "actions_taken": actions,
            "axis_break_even_steps": break_even,
            "axis_margin_steps": break_even - actions,
            "reason": "share of cost billed in the first 25%% of %d step(s)"
                      % n_steps}


def live_legs(root: str = LIVE_ROOT, slugs: Optional[List[str]] = None
              ) -> List[Dict[str, object]]:
    """Every carried live leg with a `curves.json`, in slug order."""
    if slugs is None:
        slugs = sorted(d for d in os.listdir(root)
                       if os.path.isfile(os.path.join(root, d, "curves.json")))
    return [leg_reading(s, os.path.join(root, s)) for s in slugs]


def paired_material(readings: List[Dict[str, object]]) -> Dict[str, object]:
    """Process 1's question: how many paired games does E2L have?

    `freeze/STATS_RULES.md` makes the endpoint a **paired difference**,
    Theoria minus a control arm, per game. Legs from one arm produce no pairs
    however many of them there are, and `audit/stats.py`'s floor
    (`2/2**n <= 0.05` needs n >= 6) is unreachable at n = 0 regardless.
    """
    ok = [r for r in readings if r.get("status") == "ok"]
    games = sorted({str(r.get("game_id")) for r in ok if r.get("game_id")})
    return {
        "evaluable_legs": [r["leg"] for r in ok],
        "n_evaluable": len(ok),
        "arms": ["theoria"],
        "control_arm_legs": 0,
        "n_paired_games": 0,
        "games_with_an_evaluable_leg": games,
        "min_attainable_p": None,
        "verdict": ("no-data: the endpoint is a paired difference and there "
                    "is no control arm on any of these games, so the number "
                    "of pairs is 0 and no amount of Theoria-side replication "
                    "changes it"),
    }


def build() -> Dict[str, object]:
    readings = live_legs()
    probes = probe_table()
    return {
        "what": ("E2L -- the front-load index on the step axis, defined in "
                 "PREREG_E2L.md before any of these numbers existed. "
                 "Published beside E2, not instead of it: E2L has not passed "
                 "process 1 and is not in `battery.metrics.REGISTRY`."),
        "definition": ("share of a run's total model cost billed in the first "
                       "%.0f%% of its steps, interpolated at the boundary; "
                       "cost is attributed to `Call.step_idx`, never to "
                       "`Call.turn`" % (FRONTLOAD_K * 100)),
        "target": TARGET,
        "direction": DIRECTION,
        "gates": {
            "G1": "any unpriced call -> unsound (V9-D3)",
            "G2": "total cost <= 0 -> thin",
            "G3": "fewer than %d steps -> thin" % MIN_STEPS_FOR_SHAPE,
            "G4": ("any priced call without a step_idx -> unsound; no "
                   "fallback to call order"),
            "G5": ("fewer than %d new states after the head -> thin"
                   % MIN_POST_HEAD_STATES),
        },
        "probes": probes,
        "n_probes_landing_on_E2": sum(1 for p in probes if p["lands_on_E2"]),
        "n_probes_landing_on_E2L": sum(1 for p in probes if p["lands_on_E2L"]),
        "live_legs": readings,
        "process_1_material": paired_material(readings),
    }


def serialise(doc: Dict[str, object]) -> str:
    return json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write(out_path: str = DEFAULT_OUT) -> str:
    from battery.audit.live_tiers import refuse_frozen_destination
    resolved = refuse_frozen_destination(out_path)
    doc = build()
    os.makedirs(os.path.dirname(resolved), exist_ok=True)
    with open(resolved, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(serialise(doc))
    return resolved


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="compute and publish E2L")
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
