"""Reconciliation, re-keyed to quantities the ledger actually records.

This module used to open by quoting `LEDGER_FORMAT.md` §3 -- "the score derived
from `env_step` records must equal the score the API's scorecard reports" -- and
then discharging it by comparing `max(env_step.score)` against the card. On the
live ARC API that obligation cannot be discharged, and the reason is recorded:
**a command response carries no `score` field at all**. Its key set is
`action_input, available_actions, frame, full_reset, game_id, guid,
levels_completed, state, win_levels` (`theoria-arm/INCIDENTS.md` INC-TA-002,
confirmed against 196 successful command responses in
`arc-recon/data/recon_ledger.jsonl`, none of which carries one; the canon says
the same at `LEDGER_FORMAT.md` §3). So `env_step.score` is `null` on every live
record and the ledger side of that comparison has no numbers in it.

An obligation nobody can satisfy is worse than no obligation: it leaves the gate
permanently red, or -- the failure mode this repository catalogues as
`check_with_no_failing_path` -- quietly skipped, with nobody able to say which.

## What is reconciled now, and what each leg is worth

Three legs, and the *scope* of each is the point. Two of them were already true
and are not weakened; one is new.

  ``actions``      **recorded.** One `env_step` per ARC command, `step_idx`
                   monotonic from the RESET at 0 (§3). Checked two ways that
                   can each disagree on their own: the sequence against itself
                   (duplicates, gaps, non-integers), and the scorecard's
                   `total_actions` against the count of successful non-RESET
                   commands (the frozen scorer's S-1).

  ``cost``         **derivable, deliberately not recorded.** §5 and
                   `canon.BANNED_SPELLINGS` refuse every dollar-shaped field,
                   because an append-only file that recorded a price would be
                   wrong the day the price changed. What *is* recorded is
                   `usage` verbatim plus a `pricing_ref` naming the table and
                   its hash, and that pair is what makes the bill reproducible.
                   So the leg checks reproducibility, not a dollar figure: the
                   named table must exist and must still hash to the value the
                   record pinned, and the run's declared `model_calls` must
                   equal the model_call records on disk.

  ``score_per_run`` **recorded on the scorecard, and cross-verifiable.** This is
                   the leg that a broader reading of INC-TA-002 would have
                   thrown away. The gap is per-*step* score, not per-*run*
                   score: `POST /api/scorecard/close` does return `score`, and
                   32 real closed cards in
                   `proxy/tests/fixtures/scorecard_corpus.json` carry one. The
                   frozen scorer's battery is run here rather than
                   reimplemented, because two implementations of one obligation
                   drift and the drift is invisible until they disagree about a
                   real run.

## Two things this deliberately refuses to compare

``turns`` -- **the field does not exist.** `battery/INPUT_FORMAT.md` gap 5: "No
turn index distinct from `step_idx`. Still open upstream." theoria-arm keeps its
turn axis outside the ledger in `turns.json` and rejoins it structurally, with
an explicit `join_confidence` because the join is not exact; ablation-arm's turn
count lives in `run_report.json`; baseline-arms has no turn count at any level.
A comparison over a field that is not in the file would be a check with no
failing path wearing the costume of a check with one. It is reported as
`gaps.turns`, it does **not** vote on the verdict -- a format gap is not a
defect in the run being reconciled, and making it vote would rebuild the
permanently-red signal this module exists to take down -- and it names what
would close it: §8 bumps `v` for a changed meaning or a new *required* field, so
an *optional* `turn_idx` on `env_step` and `model_call` can be added at v1.0.
`canon.py`'s `prev` is the precedent.

``score_per_step`` -- **arm-self-reported, not cross-verified.** Surfaced, never
silently dropped, under a field name that says so rather than a comment that
does. Whatever wrote the record is the only witness to it.

## Verdicts

  PASS         every leg that votes agreed
  FAIL         a leg disagreed -- an incident, written as a §6 `incident`
  INCOMPLETE   nothing disagreed but a voting leg had no evidence to work with
  EMPTY        no `env_step` records for this run at all

`INCOMPLETE` is not `PASS`. baseline-arms lost 22 of 23 scorecards to a
transient 404 and the loss was silent, so the obligation was quietly not being
performed; a reconciler that answered "nothing to compare" with `PASS` would
reproduce exactly that.

    python -m proxy.reconcile --run-id r-...
    python -m proxy.reconcile --all
"""

import argparse
import json
import sys
from collections import Counter
from typing import Any, Dict, List, Optional

from .ledger import Ledger, RunLedger, read_ledger
from .paths import LEDGER_PATH
from .scoring import score_records
from .scoring.arc_v1 import CardView, _as_int

#: The legs that vote on the run's verdict, in report order. `turns` is
#: deliberately not among them -- see the module docstring.
RECONCILIATION_KEY = ("actions", "cost", "score_per_run")

#: Why the per-step score is surfaced but never compared. Kept as a constant so
#: the report, the tests and `LEDGER_FORMAT.md` quote one sentence.
STEP_SCORE_NOT_CROSS_VERIFIABLE = (
    "arm-self-reported and NOT cross-verified: a live ARC command response "
    "carries no `score` field (INC-TA-002; LEDGER_FORMAT.md 3), so on live "
    "traffic this is null and nothing outside the writing arm witnesses it. "
    "The per-run score on the scorecard is a different quantity and IS "
    "cross-verified -- see legs.score_per_run.")

#: Why the turn count is named rather than compared.
TURNS_ABSENT = (
    "not reconcilable: no turn index exists in the ledger. "
    "battery/INPUT_FORMAT.md gap 5 -- 'No turn index distinct from step_idx. "
    "Still open upstream.' theoria-arm holds its turn axis outside the ledger "
    "in turns.json and rejoins it with a stated join_confidence; ablation-arm's "
    "count is in run_report.json; baseline-arms has none at any level. "
    "Comparing a field that is not in the file would be a check with no "
    "failing path.")

TURNS_REMEDY = (
    "add an OPTIONAL `turn_idx` to env_step and model_call. LEDGER_FORMAT.md 8 "
    "bumps `v` for a changed meaning or a new REQUIRED field, and an optional "
    "one is neither -- `prev` (canon.ENVELOPE) is the precedent. Until an arm "
    "writes it, this leg stays ABSENT and does not vote.")


def scorecard_view(scorecard: Any, game_id: Optional[str] = None) -> CardView:
    """Read a scorecard, whatever shape it came back in.

    There is exactly one scorecard reader in this package and it lives in the
    frozen scorer. `proxy/STATUS.md` used to note that this module "handles two
    shapes and will need a third if the real one differs" -- it did differ, and
    two readers drifting apart is precisely how a reconciliation obligation
    turns into a reconciliation ritual. So this delegates.
    """
    return CardView(scorecard, game_id=game_id)


def scorecard_score(scorecard: Any) -> Optional[float]:
    """The card's own score, or None. Kept as a name because callers outside
    this module use it."""
    return scorecard_view(scorecard).score


def _check_verdict(scored: Dict[str, Any], check_id: str) -> Optional[str]:
    for check in scored["checks"]:
        if check["id"] == check_id:
            return check["verdict"]
    return None


def _leg(verdict: str, **detail: Any) -> Dict[str, Any]:
    record = {"verdict": verdict, "votes": True}
    record.update(detail)
    return record


# -- the legs ---------------------------------------------------------------

def _leg_actions(steps: List[Dict[str, Any]],
                 scored: Dict[str, Any]) -> Dict[str, Any]:
    """Recorded. `step_idx` is in the file, one per ARC command."""
    raw = [record.get("step_idx") for record in steps]
    integers = [i for i in raw
                if isinstance(i, int) and not isinstance(i, bool)]
    non_integer = len(raw) - len(integers)
    duplicates = sorted(i for i, n in Counter(integers).items() if n > 1)
    dense_from_zero = sorted(integers) == list(range(len(integers)))

    disagreements: List[str] = []
    if non_integer:
        disagreements.append(
            "A-1: %d env_step record(s) carry no integer step_idx, so the "
            "action count cannot be taken from the sequence" % non_integer)
    if duplicates:
        disagreements.append(
            "A-1: step_idx %s appear(s) more than once; one env_step is one "
            "ARC command (LEDGER_FORMAT.md 3), so a repeat is two records for "
            "one action or one action recorded twice"
            % ", ".join(str(i) for i in duplicates))
    elif not dense_from_zero and integers:
        disagreements.append(
            "A-1: step_idx runs %d..%d over %d record(s); it increments once "
            "per command from the RESET at 0, so a gap is a command that "
            "happened and was not recorded"
            % (min(integers), max(integers), len(integers)))

    card_check = _check_verdict(scored, "S-1")
    if card_check == "FAIL":
        disagreements.append(
            "A-2: the scorecard's total_actions disagrees with the count of "
            "successful non-RESET commands in the ledger (frozen scorer S-1)")

    if disagreements:
        verdict = "DISAGREE"
    elif card_check == "PASS":
        verdict = "AGREE"
    else:
        # The sequence checked out against itself, but nothing outside the
        # ledger corroborated it. That is one witness, not two.
        verdict = "INCOMPLETE"

    return _leg(
        verdict,
        recorded=True,
        quantity="one env_step per ARC command; step_idx monotonic from 0",
        env_steps=len(steps),
        step_idx_span=[min(integers), max(integers)] if integers else None,
        duplicate_step_idx=duplicates or None,
        non_integer_step_idx=non_integer or None,
        card_total_actions_check=card_check,
        disagreements=disagreements or None)


def _leg_cost(records: List[Dict[str, Any]],
              run_end: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Derivable, and deliberately not recorded (LEDGER_FORMAT.md 5).

    No dollar figure is compared, because none is in the file. What is compared
    is whether the bill can still be *derived*: the price table each call
    pinned must exist and must still hash to the value that was pinned, and the
    run's own declared call count must match the records on disk. A record
    whose price table has moved is a record whose cost is no longer the cost
    that was incurred, and nothing else in the repository would notice.
    """
    from .cost import PriceTable

    calls = [r for r in records if r.get("event") == "model_call"]
    declared = _as_int((run_end or {}).get("model_calls"))

    if not calls and declared in (None, 0):
        return _leg("NOT_APPLICABLE",
                    recorded=False, derivable=True,
                    quantity="usage x pricing_ref, via proxy/cost.py",
                    model_calls=0,
                    note="the run made no model calls, so there is no bill to "
                         "reconcile. Not the same as a bill that reconciled.")

    tables: Dict[str, Any] = {}
    drifted: List[Dict[str, Any]] = []
    missing_ref: List[Any] = []
    unknown_table: List[str] = []
    unpriced: List[str] = []
    unmeasured: List[Any] = []
    unmeasured_keys: List[str] = []
    usd_total = 0.0
    priced_calls = 0

    for record in calls:
        ref = record.get("pricing_ref")
        if not isinstance(ref, dict) or not isinstance(ref.get("table"), str):
            missing_ref.append(record.get("call_idx"))
            continue
        name = ref["table"]
        if name not in tables:
            try:
                tables[name] = PriceTable.load(name)
            except KeyError:
                tables[name] = None
        table = tables[name]
        if table is None:
            if name not in unknown_table:
                unknown_table.append(name)
            continue
        pinned = ref.get("sha256")
        if isinstance(pinned, str) and pinned != table.sha256:
            drifted.append({"call_idx": record.get("call_idx"),
                            "table": name, "pinned": pinned,
                            "on_disk": table.sha256})
            continue
        priced = table.cost(record.get("model", "?"), record.get("usage") or {})
        if priced["usd"] is None:
            # Two different holes reach this branch and only one of them is
            # about the model. Before S29 a call whose usage block was missing
            # `output_tokens` could not get here at all -- it priced to a
            # plausible positive number -- and now that it can, filing it under
            # `unpriced` would print "model 'claude-opus-5' is not in the table
            # they name" about a model that is right there in pricing_v1.json.
            # A true finding under a false heading is how a reconciliation
            # report gets ignored.
            if priced.get("missing_usage_keys"):
                unmeasured.append(record.get("call_idx"))
                for key in priced["missing_usage_keys"]:
                    if key not in unmeasured_keys:
                        unmeasured_keys.append(key)
            elif priced["model"] not in unpriced:
                unpriced.append(priced["model"])
            continue
        usd_total += priced["usd"]
        priced_calls += 1

    disagreements: List[str] = []
    if drifted:
        disagreements.append(
            "C-1: %d model_call(s) pin a price table whose sha256 no longer "
            "matches the table on disk, so the dollars they cost are not "
            "recomputable from this file (LEDGER_FORMAT.md 4, 5): %s"
            % (len(drifted),
               "; ".join("call %s pinned %s, %s now hashes to %s"
                         % (d["call_idx"], d["pinned"], d["table"], d["on_disk"])
                         for d in drifted[:5])))
    if declared is not None and declared != len(calls):
        disagreements.append(
            "C-2: run_end declares %d model_call(s) and the ledger holds %d; "
            "the cost axis is a sum over those records, so a miscount is a "
            "miscounted bill" % (declared, len(calls)))

    incomplete: List[str] = []
    if missing_ref:
        incomplete.append("%d model_call(s) carry no pricing_ref, so no table "
                          "is named and no dollar figure is derivable"
                          % len(missing_ref))
    if unknown_table:
        incomplete.append("price table(s) %s are named but not on disk"
                          % ", ".join(repr(t) for t in unknown_table))
    if unpriced:
        incomplete.append("model(s) %s are not in the table they name"
                          % ", ".join(repr(m) for m in unpriced))
    if unmeasured:
        incomplete.append(
            "%d model_call(s) carry a priced model but no %s, so they were "
            "never measured and no dollar figure is derivable for them "
            "(call_idx %s)"
            % (len(unmeasured), " or ".join(sorted(unmeasured_keys)),
               ", ".join(str(i) for i in unmeasured[:5])))

    if disagreements:
        verdict = "DISAGREE"
    elif incomplete:
        verdict = "INCOMPLETE"
    else:
        verdict = "AGREE"

    return _leg(
        verdict,
        recorded=False, derivable=True,
        quantity="usage x pricing_ref, via proxy/cost.py",
        model_calls=len(calls),
        declared_model_calls=declared,
        priced_calls=priced_calls,
        unmeasured_calls=len(unmeasured),
        usd_total=round(usd_total, 6) if priced_calls else None,
        price_table_drift=drifted[:10] or None,
        not_derivable=incomplete or None,
        note="no dollar figure is recorded (LEDGER_FORMAT.md 5); this leg "
             "checks that the bill is still derivable from the usage and the "
             "table each call pinned",
        disagreements=disagreements or None)


def _leg_score_per_run(scored: Dict[str, Any], card: CardView,
                       level_errors: List[Dict[str, Any]],
                       boundaries: int, ledger_levels: int) -> Dict[str, Any]:
    """The per-run score, from the scorecard. Cross-verifiable, and kept.

    The premise that "the API does not return score" is true of a *command
    response* and false of a *scorecard close*. Marking this leg
    non-cross-verifiable would have discarded a check that works.
    """
    # S-1 is the card's action count and belongs to the `actions` leg. Letting
    # it disagree here too would make one arithmetic error light up two legs,
    # and a reader could not tell which quantity was actually wrong.
    disagreements = [
        "%s: %s" % (check["id"], check["claim"])
        for check in scored["checks"]
        if check["verdict"] == "FAIL" and check["id"] != "S-1"]
    if scored["verdict"] == "UNDETERMINED":
        disagreements.append(
            "the score could not be reconciled at all (%s); an obligation that "
            "cannot be discharged is not an obligation that passed"
            % ", ".join(scored["undetermined_checks"] or []))
    if boundaries != ledger_levels:
        disagreements.append("%d level boundaries but levels_completed reached %d"
                             % (boundaries, ledger_levels))
    if level_errors:
        disagreements.append("%d step(s) have level fields that do not recompute"
                             % len(level_errors))

    return _leg(
        "DISAGREE" if disagreements else "AGREE",
        recorded=True, cross_verified=True,
        quantity="the scorecard's own score, levels and totals, against the "
                 "ledger's step sequence",
        scorer=scored["scorer"], scorer_verdict=scored["verdict"],
        scorecard_score=card.score, scorecard_shape=card.shape,
        source="POST /api/scorecard/close returns `score`; 32 real closed "
               "cards in proxy/tests/fixtures/scorecard_corpus.json carry one. "
               "This is a different quantity from the per-step score.",
        disagreements=disagreements or None)


def _gap_turns() -> Dict[str, Any]:
    return {"verdict": "ABSENT", "votes": False, "recorded": False,
            "derivable": False, "detail": TURNS_ABSENT,
            "what_would_close_it": TURNS_REMEDY}


def _gap_step_score(steps: List[Dict[str, Any]],
                    ledger_score: Optional[int]) -> Dict[str, Any]:
    reported = sum(1 for r in steps if _as_int(r.get("score")) is not None)
    return {"verdict": "NOT_CROSS_VERIFIABLE", "votes": False,
            "recorded": True, "cross_verified": False,
            "value": ledger_score, "steps_reporting_a_score": reported,
            "detail": STEP_SCORE_NOT_CROSS_VERIFIABLE}


# -- the obligation ---------------------------------------------------------

def reconcile_run(run_id: str, ledger_path: str = LEDGER_PATH,
                  write_incident: bool = True) -> Dict[str, Any]:
    rejected: List[Dict[str, Any]] = []
    records = [r for r in read_ledger(ledger_path, strict=False, rejected=rejected)
               if r.get("run_id") == run_id]
    steps = sorted([r for r in records if r.get("event") == "env_step"],
                   key=lambda r: r.get("step_idx", 0))
    ends = [r for r in records if r.get("event") == "run_end"]

    if not steps:
        return {"run_id": run_id, "verdict": "EMPTY",
                "reconciliation_key": list(RECONCILIATION_KEY),
                "detail": "no env_step records for this run"}

    # -- what the ledger says ----------------------------------------------
    observed = [_as_int(r.get("levels_completed")) for r in steps]
    observed = [v for v in observed if v is not None]
    ledger_levels = observed[-1] if observed else 0
    boundaries = sum(1 for r in steps if r.get("level_boundary"))
    scored_steps = [_as_int(r.get("score")) for r in steps]
    scored_steps = [v for v in scored_steps if v is not None]
    # Kept under its old name for callers, and labelled in `gaps` for readers.
    ledger_score = max(scored_steps) if scored_steps else None

    # -- what the API's scorecard says --------------------------------------
    games = sorted({r.get("game_id") for r in steps if isinstance(r.get("game_id"), str)})
    card = scorecard_view(ends[-1].get("scorecard") if ends else None,
                          game_id=games[0] if len(games) == 1 else None)
    card_score = card.score

    # -- re-derive the derived-and-recorded fields ------------------------
    level_errors: List[Dict[str, Any]] = []
    completed = 0
    for record in steps:
        expected_level = completed
        after = record.get("levels_completed")
        after = completed if not isinstance(after, int) else after
        expected_boundary = after > completed
        completed = after
        if (record.get("level") != expected_level
                or bool(record.get("level_boundary")) != expected_boundary):
            level_errors.append({
                "step_idx": record.get("step_idx"),
                "recorded": {"level": record.get("level"),
                             "level_boundary": record.get("level_boundary")},
                "recomputed": {"level": expected_level,
                               "level_boundary": expected_boundary}})

    # The card-side obligation is the frozen scorer's battery, run here rather
    # than reimplemented here. Two implementations of one obligation drift, and
    # the drift is invisible until the day they disagree about a real run.
    scored = score_records(records)

    legs = {
        "actions": _leg_actions(steps, scored),
        "cost": _leg_cost(records, ends[-1] if ends else None),
        "score_per_run": _leg_score_per_run(scored, card, level_errors,
                                            boundaries, ledger_levels),
    }
    gaps = {"turns": _gap_turns(),
            "score_per_step": _gap_step_score(steps, ledger_score)}

    problems: List[str] = []
    for name in RECONCILIATION_KEY:
        problems.extend(legs[name].get("disagreements") or [])

    voting = [legs[name] for name in RECONCILIATION_KEY if legs[name]["votes"]]
    if problems:
        verdict = "FAIL"
    elif any(leg["verdict"] == "INCOMPLETE" for leg in voting):
        verdict = "INCOMPLETE"
    else:
        verdict = "PASS"

    report = {
        "run_id": run_id,
        "reconciliation_key": list(RECONCILIATION_KEY),
        "ledger_health": {"unreadable_lines": len(rejected),
                          "detail": rejected[:10] or None},
        "steps": len(steps),
        "legs": legs,
        "gaps": gaps,
        # Surfaced under the name it has always had, so callers do not break.
        # `gaps.score_per_step` is where the label lives; the name below is
        # kept honest by the alias beside it.
        "ledger_score": ledger_score,
        "step_score_self_reported_not_cross_verified": ledger_score,
        "ledger_levels_completed": ledger_levels,
        "level_boundaries": boundaries,
        "scorecard_score": card_score,
        "scorecard_shape": card.shape,
        "scorecard_levels_completed": card.levels_completed,
        "scorer": scored["scorer"],
        "scorer_verdict": scored["verdict"],
        "level_field_errors": level_errors[:20] or None,
        "problems": problems or None,
        "verdict": verdict,
    }

    if rejected and write_incident:
        run = RunLedger(Ledger(ledger_path), run_id, steps[0].get("arm", "probe"))
        run.incident(
            "ledger_unreadable_line",
            "%d line(s) in %s are not v1.0 records; they were skipped rather "
            "than allowed to make every run in the file unauditable"
            % (len(rejected), ledger_path),
            lines=[r["line"] for r in rejected[:20]])

    if problems and write_incident:
        arm = steps[0].get("arm", "probe")
        run = RunLedger(Ledger(ledger_path), run_id, arm)
        # `score_mismatch` is the kind LEDGER_FORMAT.md 6 names for a failed
        # reconciliation. Its name is now narrower than what it records --
        # renaming it means editing `ledger.INCIDENT_KINDS`, which this module
        # does not own -- so the detail says which leg disagreed.
        run.incident("score_mismatch", "; ".join(problems),
                     failing_legs=[name for name in RECONCILIATION_KEY
                                   if legs[name]["verdict"] == "DISAGREE"],
                     ledger_score=ledger_score, scorecard_score=card_score,
                     level_field_errors=level_errors[:20] or None)
    return report


def run_ids(ledger_path: str = LEDGER_PATH) -> List[str]:
    seen: List[str] = []
    for record in read_ledger(ledger_path):
        if record.get("event") == "env_step" and record["run_id"] not in seen:
            seen.append(record["run_id"])
    return seen


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--ledger", default=LEDGER_PATH)
    ap.add_argument("--no-incident", action="store_true",
                    help="report without appending an incident record")
    args = ap.parse_args(argv)

    targets = run_ids(args.ledger) if args.all else [args.run_id]
    if not targets or targets == [None]:
        print("give --run-id or --all")
        return 2

    reports = [reconcile_run(rid, args.ledger, write_incident=not args.no_incident)
               for rid in targets]
    print(json.dumps(reports if args.all else reports[0], indent=2, sort_keys=True))
    # INCOMPLETE exits non-zero with FAIL, and is a distinct word in the
    # report. It is not agreement, and the previous behaviour (an
    # undischargeable obligation exiting 1) is not weakened here.
    return 0 if all(r["verdict"] in ("PASS", "EMPTY") for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
