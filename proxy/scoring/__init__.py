"""The scoring layer: one frozen scorer, shared by every arm.

`Theoria.md`'s standing discipline for the three arms is "同壳" -- one outer
loop, one ledger format, one scorer -- because otherwise a difference in the
numbers cannot be attributed to a difference in the arms. This package is the
scorer half of that.

Three properties, each structural rather than promised:

  * **Frozen.** `frozen.json` records the sha256 of each scorer's source.
    `verify_frozen()` recomputes it and `score_run()` refuses to score when it
    disagrees. A scorer that could be edited between two arms' runs is not a
    shared scorer, it is two scorers with one name.
  * **Named in the artefact.** The scorer's id, version and source hash go into
    `run_start` and into `run.json`, so a number can always be traced to the
    rule that produced it.
  * **Registered, not hard-wired.** `REGISTRY` takes more than one scorer. The
    upstream `score_trajectories.py` is not vendored (D-016); if it ever is, it
    registers here under its own id and old runs keep their old attribution
    instead of being silently re-scored.

Scoring is a *derived* quantity and follows the rule §5 of `LEDGER_FORMAT.md`
sets for derived quantities: it is not written into the ledger. It lands in
`proxy/var/scores/<run_id>.json` and in `run.json`. What does go into the
ledger is the failure: a reconciliation that disagrees, or one that could not
be performed at all, is an `incident` record -- which is what Phase 1 asks for
in the first place.

    python -m proxy.scoring --run-id r-...
    python -m proxy.scoring --all
"""

import argparse
import hashlib
import json
import os
import sys
from typing import Any, Callable, Dict, List, Optional

from ..ledger import Ledger, RunLedger, read_ledger
from ..paths import LEDGER_PATH, VAR_DIR
from . import arc_v1

HERE = os.path.dirname(os.path.abspath(__file__))
FROZEN_PATH = os.path.join(HERE, "frozen.json")
SCORES_DIR = os.path.join(VAR_DIR, "scores")

#: id -> the module implementing it. A scorer is anything with `SCORER_ID`,
#: `VERSION` and `score(records) -> dict`.
REGISTRY: Dict[str, Any] = {arc_v1.SCORER_ID: arc_v1}

DEFAULT_SCORER = arc_v1.SCORER_ID


class ScorerDriftError(RuntimeError):
    """The scorer's source no longer hashes to its freeze record.

    Raised instead of scoring. Scoring anyway would attach a number produced by
    one rule to a run recorded under another, and the two would be
    indistinguishable afterwards.
    """


def _sha256_file(path: str) -> str:
    """Hash the source with newlines normalised to LF.

    `proxy/.gitattributes` already pins LF, so on a correct checkout this is
    the same as hashing the raw bytes. Normalising anyway means a machine whose
    git is misconfigured reports *drift in the scoring rule* only when the rule
    actually changed, instead of failing every run over a line ending. The
    freeze is about the rule, not about the file's transport encoding.
    """
    with open(path, "rb") as fh:
        blob = fh.read().replace(b"\r\n", b"\n")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def load_frozen(path: str = FROZEN_PATH) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def fingerprint(scorer_id: str = DEFAULT_SCORER,
                frozen_path: str = FROZEN_PATH) -> Dict[str, Any]:
    """What goes into `run_start` and `run.json`: which scorer, which version,
    which bytes."""
    frozen = load_frozen(frozen_path).get("scorers", {}).get(scorer_id)
    if frozen is None:
        raise KeyError("no freeze record for scorer %r in %s"
                       % (scorer_id, frozen_path))
    module = REGISTRY[scorer_id]
    return {"id": scorer_id, "version": module.VERSION,
            "sha256": frozen["sha256"], "frozen_at": frozen["frozen_at"],
            "source": frozen["source"]}


def verify_frozen(scorer_id: str = DEFAULT_SCORER,
                  frozen_path: str = FROZEN_PATH) -> Dict[str, Any]:
    """Recompute the scorer's source hash and compare it to the freeze record.

    Returns the fingerprint; raises `ScorerDriftError` on disagreement.
    """
    frozen = load_frozen(frozen_path)
    record = frozen.get("scorers", {}).get(scorer_id)
    if record is None:
        raise KeyError("no freeze record for scorer %r" % scorer_id)
    source = os.path.join(os.path.dirname(os.path.abspath(frozen_path)),
                          os.path.basename(record["source"]))
    actual = _sha256_file(source)
    if actual != record["sha256"]:
        raise ScorerDriftError(
            "%s hashes to %s but its freeze record says %s. The frozen scorer "
            "has been edited in place. Runs already scored used the old rule "
            "and cannot be compared with runs scored under the new one -- "
            "register a new scorer_id instead of editing this file."
            % (record["source"], actual, record["sha256"]))
    return {"id": scorer_id, "version": REGISTRY[scorer_id].VERSION,
            "sha256": actual, "frozen_at": record["frozen_at"],
            "source": record["source"]}


def score_records(records: List[Dict[str, Any]],
                  scorer_id: str = DEFAULT_SCORER,
                  frozen_path: str = FROZEN_PATH) -> Dict[str, Any]:
    """Score a run's records with a verified-frozen scorer."""
    fp = verify_frozen(scorer_id, frozen_path)
    report = REGISTRY[scorer_id].score(records)
    report["scorer"] = fp
    return report


def score_run(run_id: str, *,
              ledger_path: str = LEDGER_PATH,
              scorer_id: str = DEFAULT_SCORER,
              frozen_path: str = FROZEN_PATH,
              scores_dir: str = SCORES_DIR,
              write_incident: bool = True,
              write_artifact: bool = True) -> Dict[str, Any]:
    """Score one game as soon as it finishes, and file the result.

    `Theoria.md` Phase 1 §5: "逐局跑完即打分入库、与 scorecard 对账", and Phase 3
    forbids batching -- the order results arrive in is itself audited. So this
    is called from the runner at the end of a game, not from a sweep afterwards.
    """
    # Non-strict: one appended line with an unknown `v` must not make every
    # record before it unauditable. The rejected lines become a failed check,
    # which is louder than an exception and does not stop the other runs from
    # being scored.
    rejected: List[Dict[str, Any]] = []
    all_records = read_ledger(ledger_path, strict=False, rejected=rejected)
    records = [r for r in all_records if r.get("run_id") == run_id]
    if not records:
        raise KeyError("no records for run %r in %s" % (run_id, ledger_path))

    report = score_records(records, scorer_id, frozen_path)
    report["run_id"] = run_id
    report["arm"] = records[0].get("arm")
    # An unreadable line is a fact about the *file*, not about this run, and
    # the two must not be conflated: a poison line appended under another
    # run_id would otherwise fail every run in the file, which is a cheaper
    # attack than forging anything. It is recorded loudly and separately.
    report["ledger_health"] = {
        "unreadable_lines": len(rejected),
        "detail": rejected[:10] or None,
    }

    if write_artifact:
        os.makedirs(scores_dir, exist_ok=True)
        with open(os.path.join(scores_dir, run_id + ".json"), "w",
                  encoding="utf-8", newline="") as fh:
            json.dump(report, fh, indent=2, sort_keys=True)
            fh.write("\n")

    if write_incident and report["verdict"] != "PASS":
        arm = records[0].get("arm", "probe")
        game_id = (report.get("game_ids") or [None])[0]
        run = RunLedger(Ledger(ledger_path), run_id, arm, game_id=game_id)
        offending = [c for c in report["checks"] if c["verdict"] != "PASS"]
        kind = "score_mismatch" if report["verdict"] == "FAIL" else "score_unreconciled"
        run.incident(
            kind,
            "; ".join("%s %s: %s" % (c["id"], c["verdict"], c["claim"])
                      for c in offending),
            scorer=report["scorer"], checks=offending,
            game_id=game_id)
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
    ap.add_argument("--scorer", default=DEFAULT_SCORER)
    ap.add_argument("--no-incident", action="store_true")
    ap.add_argument("--no-artifact", action="store_true")
    ap.add_argument("--verify-only", action="store_true",
                    help="check the freeze record and print the fingerprint")
    args = ap.parse_args(argv)

    if args.verify_only:
        print(json.dumps(verify_frozen(args.scorer), indent=2, sort_keys=True))
        return 0

    targets = run_ids(args.ledger) if args.all else [args.run_id]
    if not targets or targets == [None]:
        print("give --run-id or --all")
        return 2

    reports = [score_run(rid, ledger_path=args.ledger, scorer_id=args.scorer,
                         write_incident=not args.no_incident,
                         write_artifact=not args.no_artifact)
               for rid in targets]
    print(json.dumps(reports if args.all else reports[0], indent=2, sort_keys=True))
    return 0 if all(r["verdict"] == "PASS" for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
