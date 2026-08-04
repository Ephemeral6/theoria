"""How many level boundaries does this repository's record actually contain?

A27's fourth question, answered by counting rather than by remembering. The
answer decides how much the detector added in this ticket is worth: a detector
whose positives are all synthetic has to say so, and the only way to know is to
read every ledger.

    python measure_boundaries.py            # writes MEASUREMENT.json

Reads, and only reads:

* every `*.jsonl` under `<arm>/runs/` for `theoria-arm`, `baseline-arms` and
  `ablation-arm` -- `env_step` rows for the envelope counter and the state
  string, `env_meta` rows for scorecards recovered from close responses;
* nothing else. No network, no API, no model, no working-tree opinion.

Two things it is careful about.

**Envelope rows are not all alike.** A non-200 command carries no
`levels_completed` at all, and `None` is not `0`: the two are counted
separately, because "the field was absent" and "the field said zero" are
different facts and collapsing them is exactly the error this ticket is about.

**A scorecard is found in two places.** `armtools/backfill.py` looks for close
responses in the ledger; `armtools/archive.py` looks in `run.json`'s summary.
This reads both shapes -- any object carrying an `environments` list -- so the
count is of documents, not of the tool that happened to write them.
"""

import json
import os
import sys
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ARM)

ARMS = ("theoria-arm", "baseline-arms", "ablation-arm")


def _rows(path: str):
    try:
        fh = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return
    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except ValueError:
                continue


def _walk(root: str) -> List[str]:
    out = []
    for base, _dirs, names in os.walk(root):
        for name in sorted(names):
            if name.endswith(".jsonl"):
                out.append(os.path.join(base, name))
    return sorted(out)


def _cards_in(record: Any) -> List[Dict[str, Any]]:
    """Every scorecard-shaped object inside one ledger record."""
    found = []
    if not isinstance(record, dict):
        return found
    for value in record.values():
        if isinstance(value, dict) and isinstance(value.get("environments"), list):
            found.append(value)
    return found


def measure() -> Dict[str, Any]:
    env_rows = 0
    counter_present = 0
    counter_absent = 0
    max_counter = 0
    states: Dict[str, int] = {}
    cards = 0
    max_card_levels = 0
    max_card_score = 0.0
    nonzero_level_scores = 0
    max_level_actions_sum = 0
    baselines: Dict[str, Dict[Any, Any]] = {}
    boundaries: List[Dict[str, Any]] = []
    files = 0

    for arm in ARMS:
        root = os.path.join(REPO, arm, "runs")
        if not os.path.isdir(root):
            continue
        for path in _walk(root):
            files += 1
            rel = os.path.relpath(path, REPO).replace(os.sep, "/")
            for record in _rows(path):
                if record.get("event") == "env_step":
                    env_rows += 1
                    completed = record.get("levels_completed")
                    if completed is None:
                        counter_absent += 1
                    else:
                        counter_present += 1
                        try:
                            completed = int(completed)
                        except (TypeError, ValueError):
                            completed = 0
                        max_counter = max(max_counter, completed)
                        if completed > 0:
                            boundaries.append(
                                {"file": rel, "levels_completed": completed,
                                 "state": record.get("state")})
                    state = record.get("state")
                    key = state if state is not None else "<absent>"
                    states[key] = states.get(key, 0) + 1

                for card in _cards_in(record):
                    cards += 1
                    max_card_levels = max(
                        max_card_levels, int(card.get("total_levels_completed") or 0))
                    try:
                        max_card_score = max(max_card_score,
                                             float(card.get("score") or 0.0))
                    except (TypeError, ValueError):
                        pass
                    for env in card.get("environments") or []:
                        if not isinstance(env, dict):
                            continue
                        for run in env.get("runs") or []:
                            if not isinstance(run, dict):
                                continue
                            scores = run.get("level_scores") or []
                            if any(float(s or 0) for s in scores):
                                nonzero_level_scores += 1
                            actions = run.get("level_actions") or []
                            if actions:
                                max_level_actions_sum = max(
                                    max_level_actions_sum,
                                    sum(int(a or 0) for a in actions))
                            baseline = run.get("level_baseline_actions")
                            if baseline and env.get("id"):
                                vector = tuple(int(b or 0) for b in baseline)
                                baselines.setdefault(env["id"], {})
                                baselines[env["id"]].setdefault(vector, set())
                                baselines[env["id"]][vector].add(rel)

    # Which baseline vectors were seen against more than one game. A roster is
    # a property of the game, so a vector shared across game ids is not a
    # roster -- it is whatever answered the request. See the `mock` note below.
    by_vector: Dict[Any, set] = {}
    for game, vectors in baselines.items():
        for vector in vectors:
            by_vector.setdefault(vector, set()).add(game)
    shared = {vector: sorted(games) for vector, games in by_vector.items()
              if len(games) > 1}

    baselines_out = {
        game: {"vectors": [{"vector": list(vector),
                            "files": sorted(files_)[:8],
                            "file_count": len(files_)}
                           for vector, files_ in sorted(vectors.items())]}
        for game, vectors in sorted(baselines.items())}

    return {
        "arms_scanned": list(ARMS),
        "baseline_vectors_seen_against_more_than_one_game": {
            ",".join(str(n) for n in vector): games
            for vector, games in sorted(shared.items())},
        "baseline_provenance_note": (
            "`level_baseline_actions` is a per-game roster, so one vector "
            "cannot belong to two games. Any vector listed above therefore "
            "came from something that is not the game -- in this archive that "
            "is `proxy/mock`, which answers [8, 8, 8] with `level_count: 3` "
            "for whatever id it is handed. A `reach` report built on it would "
            "compare a leg against a reference cost of 8 when the real g50t "
            "level 1 is 78, so `ScoreWatch` carries the leg's `offline` flag "
            "and labels the number rather than leaving it to the reader."),
        "jsonl_files_scanned": files,
        "env_step_rows": env_rows,
        "env_step_rows_carrying_the_counter": counter_present,
        "env_step_rows_with_the_counter_absent": counter_absent,
        "max_levels_completed_on_any_envelope": max_counter,
        "envelope_state_histogram": dict(sorted(states.items())),
        "scorecards_found": cards,
        "max_total_levels_completed_on_any_scorecard": max_card_levels,
        "max_score_on_any_scorecard": max_card_score,
        "scorecards_with_any_nonzero_level_score": nonzero_level_scores,
        "max_sum_level_actions_on_one_run_row": max_level_actions_sum,
        "level_baseline_actions_by_game": baselines_out,
        "boundaries_found": boundaries,
        "verdict": (
            "no level boundary exists anywhere in this arm's, the baseline "
            "arms' or the ablation arm's recorded ARC traffic. The detector "
            "added by A27 is therefore untested on a real positive; every "
            "positive in tests/test_scoreboard.py is synthetic."
            if not boundaries and max_card_levels == 0 else
            "AT LEAST ONE BOUNDARY IS ON RECORD -- re-read the synthetic "
            "positives in tests/test_scoreboard.py against it."),
    }


def main() -> int:
    payload = measure()
    path = os.path.join(HERE, "MEASUREMENT.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print(json.dumps(payload, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
