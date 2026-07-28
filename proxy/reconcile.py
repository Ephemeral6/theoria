"""The score reconciliation obligation.

LEDGER_FORMAT.md §3: the score derived from `env_step` records must equal the
score the API's scorecard reports, and inequality is an incident. This is not a
diagnostic that can be waved away -- if the two disagree, the ledger is not a
faithful record of the game, and every conclusion drawn from it is suspect.

It also re-derives `level` and `level_boundary` from the same records and checks
them against what was written. Those two fields are derived-and-recorded (§5),
which is only safe if the derivation is reproducible from the file itself.

    python -m proxy.reconcile --run-id r-...
    python -m proxy.reconcile --all
"""

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from .ledger import Ledger, RunLedger, read_ledger
from .paths import LEDGER_PATH
from .scoring import score_records
from .scoring.arc_v1 import CardView, _as_int


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
                "detail": "no env_step records for this run"}

    # -- score from the ledger ------------------------------------------
    observed = [_as_int(r.get("levels_completed")) for r in steps]
    observed = [v for v in observed if v is not None]
    ledger_levels = observed[-1] if observed else 0
    boundaries = sum(1 for r in steps if r.get("level_boundary"))
    scored = [_as_int(r.get("score")) for r in steps]
    scored = [v for v in scored if v is not None]
    ledger_score = max(scored) if scored else None

    # -- score from the API's scorecard ----------------------------------
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
    problems: List[str] = [
        "%s: %s" % (check["id"], check["claim"])
        for check in scored["checks"] if check["verdict"] == "FAIL"
    ]
    if scored["verdict"] == "UNDETERMINED":
        problems.append(
            "the score could not be reconciled at all (%s); an obligation that "
            "cannot be discharged is not an obligation that passed"
            % ", ".join(scored["undetermined_checks"] or []))
    if boundaries != ledger_levels:
        problems.append("%d level boundaries but levels_completed reached %d"
                        % (boundaries, ledger_levels))
    if level_errors:
        problems.append("%d step(s) have level fields that do not recompute"
                        % len(level_errors))

    report = {
        "run_id": run_id,
        "ledger_health": {"unreadable_lines": len(rejected),
                          "detail": rejected[:10] or None},
        "steps": len(steps),
        "ledger_score": ledger_score,
        "ledger_levels_completed": ledger_levels,
        "level_boundaries": boundaries,
        "scorecard_score": card_score,
        "scorecard_shape": card.shape,
        "scorecard_levels_completed": card.levels_completed,
        "scorer": scored["scorer"],
        "scorer_verdict": scored["verdict"],
        "level_field_errors": level_errors[:20] or None,
        "problems": problems or None,
        "verdict": "PASS" if not problems else "FAIL",
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
        run.incident("score_mismatch", "; ".join(problems),
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
    return 0 if all(r["verdict"] in ("PASS", "EMPTY") for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
