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


def scorecard_score(scorecard: Any) -> Optional[int]:
    """Pull a score out of whatever shape the scorecard came back in.

    The mock reports a flat `score`; the live API's card aggregates per game.
    Both are handled, and an unrecognised shape returns None rather than a
    guess -- a fabricated number here would defeat the whole check.
    """
    if not isinstance(scorecard, dict):
        return None
    if isinstance(scorecard.get("score"), int):
        return scorecard["score"]
    cards = scorecard.get("cards")
    if isinstance(cards, dict):
        total = 0
        for entry in cards.values():
            scores = (entry or {}).get("scores") or []
            numeric = [s for s in scores if isinstance(s, int)]
            if numeric:
                total += max(numeric)
        return total
    return None


def reconcile_run(run_id: str, ledger_path: str = LEDGER_PATH,
                  write_incident: bool = True) -> Dict[str, Any]:
    records = [r for r in read_ledger(ledger_path) if r.get("run_id") == run_id]
    steps = sorted([r for r in records if r.get("event") == "env_step"],
                   key=lambda r: r.get("step_idx", 0))
    ends = [r for r in records if r.get("event") == "run_end"]

    if not steps:
        return {"run_id": run_id, "verdict": "EMPTY",
                "detail": "no env_step records for this run"}

    # -- score from the ledger ------------------------------------------
    observed = [r.get("levels_completed") for r in steps
                if isinstance(r.get("levels_completed"), int)]
    ledger_levels = max(observed) if observed else 0
    boundaries = sum(1 for r in steps if r.get("level_boundary"))
    scored = [r.get("score") for r in steps if isinstance(r.get("score"), int)]
    ledger_score = max(scored) if scored else None

    # -- score from the API's scorecard ----------------------------------
    card = (ends[-1].get("scorecard") if ends else None)
    card_score = scorecard_score(card)

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

    problems: List[str] = []
    if card_score is None:
        problems.append("no scorecard score could be read from run_end")
    elif ledger_score is not None and ledger_score != card_score:
        problems.append("ledger score %s != scorecard score %s"
                        % (ledger_score, card_score))
    if boundaries != ledger_levels:
        problems.append("%d level boundaries but levels_completed reached %d"
                        % (boundaries, ledger_levels))
    if level_errors:
        problems.append("%d step(s) have level fields that do not recompute"
                        % len(level_errors))

    report = {
        "run_id": run_id,
        "steps": len(steps),
        "ledger_score": ledger_score,
        "ledger_levels_completed": ledger_levels,
        "level_boundaries": boundaries,
        "scorecard_score": card_score,
        "level_field_errors": level_errors[:20] or None,
        "problems": problems or None,
        "verdict": "PASS" if not problems else "FAIL",
    }

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
