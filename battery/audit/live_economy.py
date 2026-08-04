"""经济族 · the shape of the bill, read on the live Theoria arm's legs.

`battery/audit/live_arm.py` evaluates all 38 registered metrics on the live
arm's committed leg archives and writes `artifacts_live/live_arm_readings.json`
— the reading of record.  This module is its economy-family companion, and it
exists for one reason: **the economy family is the only one whose answer
depends on an axis the battery does not own.**

E1, E4, E5, E6 and E7 are computed per *billed call* or per *step*, so the
adapter's extraction is the whole of their input.  E2 (front-load index) and
E3 (convergence point) are computed per *turn* — per decision — and the live
arm's ledger carries no turn index.  `adapters/theoria_live._turn_map` therefore
reads the archive's own join, and when it cannot, `model.Run.turn_costs()`
falls back to one-call-per-turn.  That fallback is documented and is not a
defect; what *is* a hazard is that a fallback axis and an exact axis produce
E2/E3 values that look identical in a table.  Phase 4 names the front-load
index a primary endpoint.  An endpoint whose axis is a silent fallback is an
endpoint nobody can audit.

**So this file does three things, and deliberately not a fourth.**

1. **Reconciles the money three ways** — the proxy ledger's `model_call`
   rows, the archive's `bill_shape.json` (per-call, carrying `call_idx`,
   `turn` and `usd`), and A8's `curves.json` (per-turn) — and reports every
   disagreement with both numbers.  A join that does not add up is named, not
   averaged.
2. **Re-evaluates the frozen economy metric bodies on the archive's exact
   axis**, obtained by copying `bill_shape.json`'s `call_idx -> turn` onto the
   adapter's own `Call` objects.  This is a *sensitivity check on the axis*,
   not a second reading: the metric functions are the frozen ones, imported,
   and the join is read from the producer's artefact rather than re-derived
   here.  `theoria_live`'s docstring is explicit that a second implementation
   of the turn join would be a second unlabelled definition of E2's input;
   copying a published `turn` field is not that.
3. **Records absence with its reason, per leg and per metric, and never as a
   zero** — `theme.ABSENCE`'s two structural states (`not-applicable`,
   `insufficient-data`) plus the battery's `unsound`, carried verbatim from
   the metric that returned them.  A leg that made no billed model call has no
   bill and therefore no bill *shape*; writing 0.0 there would say it was
   cheap.

The fourth thing — settling a prediction, moving a tier, entering a
discrimination verdict — is refused for exactly the reasons `live_arm.py`
records: `PREDICTIONS.md` is frozen prefix-and-whole under BATTERY_V1
`freeze:prereg`, `PREREG_V9.md` §5 forbids rewriting the committed artefacts,
and process 1's gradient (CC vs Schema) does not contain this arm.  These are
readings.

The artefact is byte-reproducible for a fixed tree — no timestamp, no absolute
path, sorted keys — and pins the sha256 of every input file it read, so
`battery/verify.py`'s rung 8 turns red the moment the committed companion
stops matching an in-process recompute.

    python -m battery.audit.live_economy            # writes the tracked default
    python -m battery.audit.live_economy --out P    # anywhere except artifacts/
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))          # battery/audit
BATTERY = os.path.dirname(HERE)                            # battery
REPO = os.path.dirname(BATTERY)

#: The tracked default output. `battery/freeze.py` lists it under READINGS.
DEFAULT_OUT = os.path.join(BATTERY, "artifacts_live", "live_economy.json")

#: The five economy metrics, in registry order. Read from the registry rather
#: than restated, in `_economy_ids()`; this tuple is only the fallback order
#: for a registry that somehow carries none of them, which is a bug, not a
#: configuration.
ECONOMY_FAMILY = "economy"

#: Files this artefact digests. `bill_shape.json` is the one `live_arm.py`
#: does not read, and it is the reason this module exists.
_INPUT_FILES = ("ledger.jsonl", "bill_shape.json", "curves.json",
                "turn_series.json")

#: Money reconciles or it does not. A cent is far coarser than any rounding
#: these producers do (they round to 6 dp), so a difference above this is a
#: real difference and not a float artefact.
USD_TOLERANCE = 1e-06


def _read_json(path: str) -> Optional[Any]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _sha256(path: str) -> str:
    """LF-normalised digest, `battery.freeze`'s own hash — one definition."""
    import sys
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from battery.freeze import sha256_file
    return sha256_file(path)


def _economy_ids() -> List[str]:
    import sys
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from battery.metrics import REGISTRY
    return sorted(mid for mid in REGISTRY
                  if REGISTRY[mid].family == ECONOMY_FAMILY)


# --------------------------------------------------------------- the axis

def exact_axis(run, leg_dir: str) -> Tuple[Optional[Any], Dict[str, Any]]:
    """The same `Run` with `Call.turn` taken from `bill_shape.json`.

    Returns `(run_or_None, note)`.  `None` is returned — with the reason —
    whenever the archive's join cannot be trusted to be *the* join for this
    leg, and the four refusals are separate on purpose:

    * no `bill_shape.json` — nothing to copy;
    * the leg records no billed model call — there is no bill, so there is no
      bill shape.  This is the r1-shaped case and it must not become a zero;
    * a billed call the join does not mention — a partial map would silently
      bucket the unmentioned calls onto a fabricated turn;
    * the join's money does not equal the ledger's — then one of the two is
      wrong about what was spent, and a shape computed over either is a shape
      of a bill nobody was sent.
    """
    doc = _read_json(os.path.join(leg_dir, "bill_shape.json"))
    if doc is None:
        return None, {"axis": "absent",
                      "reason": "the leg archives no bill_shape.json"}
    rows = (doc.get("calls") if isinstance(doc, dict) else None) or []
    if not run.calls:
        return None, {
            "axis": "not-applicable",
            "reason": ("the leg records no billed model call, so it has no "
                       "bill and no bill shape; bill_shape.json agrees (%d "
                       "call row(s)). Absence, not zero." % len(rows))}

    mapping: Dict[int, int] = {}
    priced: Dict[int, float] = {}
    for row in rows:
        if row.get("call_idx") is None or row.get("turn") is None:
            continue
        idx = int(row["call_idx"])
        mapping[idx] = int(row["turn"])
        if row.get("usd") is not None:
            priced[idx] = float(row["usd"])

    unmapped = sorted(c.idx for c in run.calls if c.idx not in mapping)
    if unmapped:
        return None, {
            "axis": "partial",
            "reason": ("bill_shape.json carries no turn for billed call(s) %s "
                       "of %d; a partial map would bucket the rest onto a "
                       "turn nobody recorded"
                       % (", ".join(str(i) for i in unmapped), len(run.calls)))}

    ledger_usd = sum(c.cost_usd or 0.0 for c in run.calls)
    join_usd = sum(priced.get(c.idx, 0.0) for c in run.calls)
    if abs(ledger_usd - join_usd) > USD_TOLERANCE:
        return None, {
            "axis": "irreconcilable",
            "reason": ("bill_shape.json totals %.6f USD over the same %d "
                       "call(s) the proxy ledger bills at %.6f USD. One of "
                       "the two is wrong about what was spent; a shape "
                       "computed over either is the shape of a bill nobody "
                       "was sent."
                       % (join_usd, len(run.calls), ledger_usd))}

    calls = [dataclasses.replace(c, turn=mapping[c.idx]) for c in run.calls]
    turns = sorted(set(mapping[c.idx] for c in run.calls))
    return dataclasses.replace(run, calls=calls), {
        "axis": "exact",
        "source": "bill_shape.json",
        "reason": None,
        "billed_calls": len(run.calls),
        "decision_turns": len(turns),
        "turn_indices": turns,
        "reconciled_usd": round(ledger_usd, 9),
    }


def turn_cost_curve(run) -> List[Dict[str, Any]]:
    """逐回合成本曲线: per-decision cost, cumulative, and cumulative share.

    Computed from `Run.turn_costs()` — the frozen accessor E2 and E3 read —
    so the curve this artefact publishes and the curve those two metrics are
    defined over cannot drift apart.  The turn labels come from the calls'
    own `turn` field, so a curve on the exact axis is labelled with the
    archive's turn numbers rather than with 0..n.

    Empty when the axis cannot be rebuilt (S46).  That emptiness is *not*
    self-explaining — an unlabelled leg that really did spend money renders
    the same `[]` as a leg that never called a model — so `build()` writes the
    leg's `turn_axis` beside the curve and files an `absences` row carrying the
    money that is off it.  This module's third promise is "records absence with
    its reason, per leg and per metric, and never as a zero", and an empty
    curve without that row would be exactly the zero it forbids.
    """
    costs = run.turn_costs()
    # No `range(len(costs))` fallback here either: `turn_costs` only returns a
    # non-empty list on an `exact` axis, where every call carries a label, so
    # the label set and the bucket list have the same length by construction.
    labels = sorted({c.turn for c in run.calls if c.turn is not None})
    total = sum(costs)
    out: List[Dict[str, Any]] = []
    running = 0.0
    for label, cost in zip(labels, costs):
        running += cost
        out.append({
            "turn": label,
            "usd": round(cost, 9),
            "usd_cumulative": round(running, 9),
            "share_cumulative": (round(running / total, 9)
                                 if total > 0 else None),
        })
    return out


# ------------------------------------------------------- reconciliation

def reconcile(run, leg_dir: str) -> Dict[str, Any]:
    """The money, counted by all three producers, with the disagreements named.

    Three sources, and none of them is treated as authoritative here: the
    proxy ledger (what the environment proxy billed), `bill_shape.json` (the
    archive's per-call join), and `curves.json` (A8's per-turn reduction).
    Where they agree the agreement is recorded; where they do not, both
    numbers are.  Averaging them, or picking one silently, is how a
    measurement acquires an opinion.
    """
    ledger_calls = len(run.calls)
    ledger_usd = round(sum(c.cost_usd or 0.0 for c in run.calls), 9)

    out: Dict[str, Any] = {
        "ledger": {"billed_calls": ledger_calls, "usd": ledger_usd},
        "disagreements": [],
    }

    bill = _read_json(os.path.join(leg_dir, "bill_shape.json"))
    if isinstance(bill, dict):
        rows = bill.get("calls") or []
        bill_usd = round(sum(float(r.get("usd") or 0.0) for r in rows), 9)
        out["bill_shape"] = {
            "present": True,
            "billed_calls": len(rows),
            "usd": bill_usd,
            "declared_total_usd": (bill.get("totals") or {}).get("usd"),
        }
        if len(rows) != ledger_calls:
            out["disagreements"].append(
                "bill_shape.json carries %d call row(s); the proxy ledger "
                "bills %d" % (len(rows), ledger_calls))
        if abs(bill_usd - ledger_usd) > USD_TOLERANCE:
            out["disagreements"].append(
                "bill_shape.json totals %.6f USD; the proxy ledger totals "
                "%.6f USD" % (bill_usd, ledger_usd))
    else:
        out["bill_shape"] = {"present": False}
        if ledger_calls:
            out["disagreements"].append(
                "no bill_shape.json in this leg archive, and the proxy ledger "
                "bills %d call(s) -- the exact turn axis has no source here"
                % ledger_calls)

    curves = _read_json(os.path.join(leg_dir, "curves.json"))
    if isinstance(curves, dict):
        rows = curves.get("rows") or []
        curve_calls = sum(int(r.get("model_calls") or 0) for r in rows)
        curve_usd = round(sum(float(r.get("usd") or 0.0) for r in rows), 9)
        out["curves"] = {
            "present": True,
            "turn_rows": len(rows),
            "billed_calls": curve_calls,
            "usd": curve_usd,
            "join_confidence": curves.get("join_confidence"),
            "declared_total_usd": (curves.get("totals") or {}).get("usd"),
        }
        if curve_calls != ledger_calls:
            out["disagreements"].append(
                "curves.json accounts for %d billed call(s) over %d turn "
                "row(s); the proxy ledger bills %d"
                % (curve_calls, len(rows), ledger_calls))
        if abs(curve_usd - ledger_usd) > USD_TOLERANCE:
            out["disagreements"].append(
                "curves.json totals %.6f USD over its turn rows; the proxy "
                "ledger totals %.6f USD (difference %.6f)"
                % (curve_usd, ledger_usd, ledger_usd - curve_usd))
    else:
        out["curves"] = {"present": False}

    out["all_three_agree"] = not out["disagreements"]
    return out


# ------------------------------------------------------------------ build

def build(runs_root: Optional[str] = None) -> Dict[str, Any]:
    """The live arm's economy family, on both axes, with absence spelled out."""
    import sys
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from battery.adapters.theoria_live import LIVE_ROOT, collect
    from battery.guard import load_piles
    from battery.metrics import REGISTRY

    root = runs_root or LIVE_ROOT
    piles = load_piles()               # raises if the cut has drifted
    runs, excluded = collect(root, piles=piles)
    ids = _economy_ids()

    legs: Dict[str, Any] = {}
    inputs: Dict[str, Any] = {}
    absences: List[Dict[str, Any]] = []
    unshaped: List[Dict[str, Any]] = []
    axis_moved: List[Dict[str, Any]] = []

    for run in runs:
        leg_dir = os.path.join(root, run.run_id)

        of_record = {mid: REGISTRY[mid].fn(run) for mid in ids}
        alt, axis_note = exact_axis(run, leg_dir)
        on_exact = ({mid: REGISTRY[mid].fn(alt) for mid in ids}
                    if alt is not None else None)

        # The curve's own absence (S46).  Deliberately *not* in `absences`:
        # that list is one row per metric and carries metric statuses, and an
        # axis is neither.  An empty `turn_cost_curve_of_record` is otherwise
        # indistinguishable from the curve of a leg that never called a model,
        # and on this arm the difference is real money -- leg
        # 20260731T231654Z-R1-sk48-b bills three calls and carries no turn
        # label on any of them.  Money that has no shape is not absent money.
        axis = run.turn_axis()
        if run.calls and not axis.usable:
            billed = sum(c.cost_usd or 0.0 for c in run.calls)
            unshaped.append({
                "leg": run.run_id,
                "axis": axis.status,
                "calls": axis.n_calls,
                "labelled_calls": axis.n_labelled,
                "unshaped_usd": round(billed, 9),
                "reason": "%d of %d call(s) carry a turn label, so the "
                          "decision axis cannot be rebuilt, the curve is "
                          "empty and E2/E3 decline; the %.6f USD billed over "
                          "those calls was spent, and is reported here rather "
                          "than left to be read off an empty curve as zero"
                          % (axis.n_labelled, axis.n_calls, billed),
            })

        for mid in ids:
            value = of_record[mid]
            if not value.ok:
                absences.append({
                    "leg": run.run_id, "metric": mid,
                    "status": value.status, "reason": value.reason,
                    "note": "absence carries its reason and is never a zero",
                })
            if on_exact is not None:
                other = on_exact[mid]
                if (other.status != value.status
                        or other.value != value.value):
                    axis_moved.append({
                        "leg": run.run_id, "metric": mid,
                        "of_record": value.as_dict(),
                        "on_exact_axis": other.as_dict(),
                    })

        legs[run.run_id] = {
            "game_id": run.game_id,
            "pile": run.pile,
            "campaign": run.campaign,
            "carried_books": bool(run.notes.get("carried_books")),
            "outcome": run.notes.get("outcome"),
            "levels_completed": run.notes.get("levels_completed"),
            "steps": len(run.steps),
            "successful_actions": len(run.ok_steps),
            "billed_calls": len(run.calls),
            "ledger_cost_usd": run.notes.get("ledger_cost_usd"),
            "adapter_turn_join": run.notes.get("turn_join"),
            # What the leg's *own* record can say about its decision axis,
            # separately from what `bill_shape.json` can rebuild for it.
            "turn_axis": {"status": axis.status, "calls": axis.n_calls,
                          "labelled_calls": axis.n_labelled},
            "exact_axis": axis_note,
            "reconciliation": reconcile(run, leg_dir),
            "turn_cost_curve_of_record": turn_cost_curve(run),
            "turn_cost_curve_exact": (turn_cost_curve(alt)
                                      if alt is not None else None),
            "economy_of_record": {mid: of_record[mid].as_dict()
                                  for mid in ids},
            "economy_on_exact_axis": ({mid: on_exact[mid].as_dict()
                                       for mid in ids}
                                      if on_exact is not None else None),
        }

        digests = {}
        for rel in _INPUT_FILES:
            path = os.path.join(leg_dir, rel.replace("/", os.sep))
            if os.path.exists(path):
                digests[rel] = _sha256(path)
        inputs[run.run_id] = digests

    # A cell can hold still while the axis under it moves: both axes return
    # `insufficient-data` below the 8-turn floor, with the same reason string,
    # from turn counts that differ. Recorded separately so the agreement above
    # is not read as two axes corroborating each other.
    turn_counts_moved = []
    for run_id in sorted(legs):
        row = legs[run_id]
        exact_curve = row["turn_cost_curve_exact"]
        if exact_curve is None:
            continue
        n_record = len(row["turn_cost_curve_of_record"])
        if n_record != len(exact_curve):
            turn_counts_moved.append({
                "leg": run_id,
                "of_record_turns": n_record,
                "exact_turns": len(exact_curve),
                "of_record_source": (row["adapter_turn_join"] or {}).get(
                    "source"),
            })

    # The progression: legs of one game in archive order. Not hardcoded to
    # r1/r2/r3 -- the slugs are UTC-prefixed, so sorting them is sorting time,
    # and a fifth leg joins its game's sequence without an edit here.
    progressions: Dict[str, Any] = {}
    for run_id in sorted(legs):
        row = legs[run_id]
        game = row["game_id"] or "unknown"
        progressions.setdefault(game, []).append({
            "leg": run_id,
            "carried_books": row["carried_books"],
            "outcome": row["outcome"],
            "levels_completed": row["levels_completed"],
            "billed_calls": row["billed_calls"],
            "decision_turns": (row["exact_axis"].get("decision_turns")
                               if row["exact_axis"].get("axis") == "exact"
                               else None),
            "successful_actions": row["successful_actions"],
            "E1_total_usd": row["economy_of_record"]["E1"],
            "E2_frontload_index": row["economy_of_record"]["E2"],
            "E3_convergence_point": row["economy_of_record"]["E3"],
            "E5_usd_per_action": row["economy_of_record"]["E5"],
        })

    measured = {
        mid: sorted(run_id for run_id in legs
                    if legs[run_id]["economy_of_record"][mid]["status"] == "ok")
        for mid in ids
    }

    return {
        "what": ("the 经济 (economy) family of the frozen battery, evaluated "
                 "on the live Theoria arm's committed leg archives on two "
                 "axes: the reading of record (battery.adapters.theoria_live, "
                 "whose turn join degrades to one-call-per-turn when the "
                 "archive publishes none) and the archive's exact "
                 "call_idx->turn join read from bill_shape.json. The metric "
                 "bodies are the frozen ones, imported; only the axis "
                 "differs. No timestamp on purpose: for a fixed tree this "
                 "file is byte-reproducible."),
        "constraint": ("readings, not confirmations -- the same constraint "
                       "battery/audit/live_arm.py records. PREDICTIONS.md is "
                       "frozen prefix-and-whole under BATTERY_V1 "
                       "freeze:prereg, PREREG_V9 §5 forbids rewriting the "
                       "committed artefacts, and process 1's gradient (CC vs "
                       "Schema) does not contain this arm. Nothing here "
                       "settles a prediction, moves a tier, or enters a "
                       "discrimination verdict."),
        "reading": ("E2 is a share of the bill spent in the first quarter of "
                    "the turn axis, interpolated, so a perfectly flat bill "
                    "scores 0.250 at every run length -- read a value near "
                    "0.25 as `no front-loading detected`, not as `a quarter "
                    "of the money`. E3 is the fraction of turns needed to "
                    "reach 90% of the bill, so 1.0 means the bill was still "
                    "climbing when the run stopped. Both require at least 8 "
                    "decision turns (battery/metrics/economy.py "
                    "MIN_TURNS_FOR_SHAPE) and both are `reference` tier under "
                    "the V9 audit, so neither may carry an ordering claim."),
        "arm": "theoria",
        "source": "theoria-arm-live",
        "runs_root": "theoria-arm/runs",
        "metrics": ids,
        "n_legs": len(legs),
        "games": sorted({row["game_id"] for row in legs.values()
                         if row["game_id"]}),
        "excluded": excluded,
        "inputs": inputs,
        "legs": legs,
        "progressions": progressions,
        "measured_by_metric": measured,
        "absences": absences,
        # Legs whose money was billed but cannot be laid on a decision axis.
        # Empty is the good state; a non-empty entry is spend that no shape
        # metric will ever account for, said out loud (S46).
        "spend_with_no_shape": unshaped,
        "axis_sensitivity": {
            "cells_that_moved": axis_moved,
            "turn_counts_that_moved": turn_counts_moved,
            "note": ("E1, E4, E5, E6 and E7 are computed per billed call or "
                     "per step and cannot move with the turn axis; only E2 "
                     "and E3 can. An empty `cells_that_moved` therefore means "
                     "the adapter's fallback axis and the archive's exact "
                     "axis agree on every computable cell -- which is a "
                     "result about this material, not a property of the code. "
                     "Read it beside `turn_counts_that_moved`: a leg whose "
                     "axis changed length but stayed under the 8-turn floor "
                     "returns the same `insufficient-data` from both axes, "
                     "and that agreement is arithmetic rather than "
                     "corroboration."),
        },
        "legs_with_axis": {
            row_axis: sorted(k for k, v in legs.items()
                             if v["exact_axis"]["axis"] == row_axis)
            for row_axis in sorted({v["exact_axis"]["axis"]
                                    for v in legs.values()})
        },
        "legs_with_disagreements": sorted(
            k for k, v in legs.items()
            if not v["reconciliation"]["all_three_agree"]),
    }


def serialise(doc: Dict[str, Any]) -> str:
    """Canonical bytes: sorted keys, two-space indent, LF, trailing newline."""
    return json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write(out_path: str = DEFAULT_OUT,
          runs_root: Optional[str] = None) -> str:
    """Build and write.  Refuses the frozen directory before touching anything.

    The refusal is `live_tiers.refuse_frozen_destination`, imported: one
    definition of "inside the frozen directory", not three.
    """
    import sys
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from battery.audit.live_tiers import refuse_frozen_destination
    resolved = refuse_frozen_destination(out_path)
    doc = build(runs_root)
    os.makedirs(os.path.dirname(resolved), exist_ok=True)
    with open(resolved, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(serialise(doc))
    return resolved


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="write the live-arm economy companion artefact")
    parser.add_argument("--out", default=DEFAULT_OUT,
                        help="destination (default: %(default)s); anything "
                             "resolving inside battery/artifacts/ is refused")
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
