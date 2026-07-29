"""P-20 cascade probe -- one game per invocation, everything on disk as it happens.

    python -m cascade.probe --game g50t-5849a774 --run-dir <dir>
    python -m cascade.probe --game g50t-5849a774 --run-dir <dir> --dry-run

(run from `arc-recon/`.)

WHAT IT ADDS TO THE PRECHECK. The precheck hashed each response's whole `frame`
batch, so a 7-frame response and a 7-times-repeated single frame have different
hashes from each other but are indistinguishable *as a category*. This hashes
every frame in the batch separately and records, per step:

  * `frame_hashes`  -- one hash per frame, in order
  * `distinct_frames` -- how many of them are different
  * `intra_batch_changes` -- how many adjacent pairs differ
  * `first_equals_prev_last` -- whether the batch resumes from where the last
    one ended, which is what makes the batch a trajectory rather than a bag

Those four fields are the whole evidentiary difference between verdict (a) and
verdict (b), and none of them existed before.

DISCIPLINES CARRIED OVER RATHER THAN REINVENTED
  * `precheck.assert_playable` gates every game -- the sealed pile is untouchable
    and this file does not get its own opinion about that.
  * `precheck.send_command` is the retry envelope (INC-005/INC-007a): full id
    only, 40 attempts, backoff capped at 5 s, ALB pins redrawn every 5 failures.
    Short ids are never sent; INC-005's counterfeit 200s came from them.
  * The credential is read by `client.load_api_key` and never printed, never
    written, never passed anywhere but the header.
  * The ledger for this probe is its OWN file inside the run directory. P-20 may
    only add `arc-recon/cascade/`, and `data/recon_ledger.jsonl` is an existing
    tracked file -- appending to it would be an edit to something outside this
    task's territory and a merge hazard against P-11.

PREDICTIONS ARE A GATE, NOT A CUSTOM. The probe refuses to spend an action for a
game with no `predictions/<game>.md` already on disk. Writing the prediction
after seeing the frames is the failure mode this project has twice paid for
(INC-003, INC-006a: an instrument that could not fail), so the ordering is
enforced by the code rather than by intent.
"""

import argparse
import hashlib
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ARC_RECON = os.path.dirname(HERE)
sys.path.insert(0, ARC_RECON)

from client import ArcClient, load_api_key, mask          # noqa: E402
from precheck import (                                    # noqa: E402
    ACTION_ATTEMPTS,
    RESET_ATTEMPTS,
    assert_playable,
    hash_frames,
    send_command,
)

from cascade import spec                                   # noqa: E402


# -- credential -------------------------------------------------------------

def resolve_env() -> str:
    """Find the gitignored .env. Its VALUE never leaves `load_api_key`.

    This probe runs from a worktree, and `.env` is gitignored, so it exists in
    the main checkout and not here. The candidates are paths only; nothing about
    the key itself is logged beyond `mask()`'s four-and-four handle.
    """
    repo = os.path.dirname(ARC_RECON)
    candidates = [
        os.environ.get("THEORIA_ENV") or "",
        os.path.join(repo, ".env"),
        os.path.join(os.path.dirname(repo), "theoria", ".env"),
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    raise SystemExit("no .env found; set THEORIA_ENV to its path")


# -- frame arithmetic -------------------------------------------------------

def hash_one(frame: Any) -> str:
    """Same canonicalisation as precheck.hash_frames, applied to ONE frame."""
    canonical = json.dumps(frame, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def shape_of(frame: Any) -> Optional[List[int]]:
    if not isinstance(frame, list) or not frame:
        return None
    if isinstance(frame[0], list):
        return [len(frame), len(frame[0])]
    return [len(frame)]


def analyse(frames: Any, prev_last: Optional[str]) -> Dict[str, Any]:
    """Everything about a response's frame list that the verdict turns on."""
    if not isinstance(frames, list):
        return {"n_frames": None, "batch_hash": None, "frame_hashes": None,
                "distinct_frames": None, "intra_batch_changes": None,
                "shapes": None, "first_equals_prev_last": None}
    hashes = [hash_one(f) for f in frames]
    changes = sum(1 for a, b in zip(hashes, hashes[1:]) if a != b)
    return {
        "n_frames": len(frames),
        "batch_hash": hash_frames(frames),
        "frame_hashes": hashes,
        "distinct_frames": len(set(hashes)),
        "intra_batch_changes": changes,
        "shapes": [shape_of(f) for f in frames],
        # None on the first step of a session: there is no previous batch, and
        # "no previous" must not be recorded as "did not match".
        "first_equals_prev_last": (None if prev_last is None
                                   else hashes[:1] == [prev_last]),
    }


# -- offline expectations ---------------------------------------------------

def expectations(game: str, sequence: Optional[List[Any]] = None) -> List[Optional[str]]:
    """Batch hashes for this game's leading steps, from `data/precheck.json`.

    Derived offline from a run this probe did not make, in the spirit of the
    canary: the expectation is written before the run and the run has to
    reproduce it. Positions where the precheck's action does not match this
    spec's, or where the precheck has no step at all, are `None` -- not
    silently treated as agreement. INC-003 is exactly the bug where a missing
    hash counted as a match.
    """
    path = os.path.join(ARC_RECON, "data", "precheck.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        report = json.load(fh)
    run_a = (report.get("results", {}).get(game, {}) or {}).get("run_a") or []
    sequence = sequence if sequence is not None else spec.SEQUENCES[game]
    want = ["RESET"] + ["ACTION%d" % a for a, _ in sequence]
    out: List[Optional[str]] = []
    for index, name in enumerate(want):
        if index < len(run_a) and run_a[index].get("action") == name:
            out.append(run_a[index].get("hash"))
        else:
            out.append(None)
    return out


# -- the run ----------------------------------------------------------------

def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class Recorder:
    """Append-and-flush. Context evaporating mid-run is the default assumption."""

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    def write(self, entry: Dict[str, Any]) -> None:
        line = json.dumps(entry, sort_keys=True, ensure_ascii=False) + "\n"
        with open(self.path, "a", encoding="utf-8", newline="") as fh:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())


def run(game: str, run_dir: str, dry_run: bool = False,
        which: str = "main") -> Dict[str, Any]:
    spec.check_budget()
    assert_playable(game)                      # sealed pile: refused here
    sequence = spec.SETS[which][game]
    if len(sequence) > spec.BUDGET_PER_GAME:
        raise SystemExit("budget: %s wants %d actions" % (game, len(sequence)))

    prediction = os.path.join(run_dir, "predictions", "%s.md" % game)
    if not os.path.exists(prediction) and not dry_run:
        raise SystemExit(
            "no prediction on disk for %s. Write %s before spending an action."
            % (game, prediction))

    steps_path = os.path.join(run_dir, "steps.%s.jsonl" % game)
    if os.path.exists(steps_path) and not dry_run:
        # Double-spend guard. A re-run would append a second session's steps to
        # the same file, which both overspends the budget and produces a record
        # in which two histories are indistinguishable. Point --run-dir at a new
        # directory if a second run is genuinely wanted.
        raise SystemExit("%s already exists; %s has already been run in this "
                         "run directory" % (steps_path, game))
    recorder = Recorder(steps_path)
    client = ArcClient(
        api_key=load_api_key(resolve_env()),
        ledger_path=os.path.join(run_dir, "ledger.%s.jsonl" % game),
        dry_run=dry_run,
    )
    print("[%s] %s key=%s ledger=%s"
          % (now(), game, mask(client._key), client.ledger_path))

    expected = expectations(game, sequence)
    summary: Dict[str, Any] = {
        "game_id": game, "started": now(), "prompt_id": "P-20", "set": which,
        "sequence": [[a, d] for a, d in sequence],
        "actions_executed": 0, "http_calls": 0, "steps": [],
    }
    if dry_run:
        summary["dry_run"] = True
        return summary

    card_id = client.open_scorecard(tags=["p20-cascade", game.split("-")[0]])["card_id"]
    summary["card_id"] = card_id

    status, opening, stats = send_command(
        client, "/api/cmd/RESET", {"game_id": game, "card_id": card_id},
        note="p20 RESET %s" % game, attempts=RESET_ATTEMPTS,
        delay_base=0.5, delay_cap=5.0)
    summary["http_calls"] += stats["attempts"]
    if status != 200 or not isinstance(opening, dict):
        summary["reset_failed"] = {"status": status, "attempts": stats["attempts"],
                                   "body": str(opening)[:300]}
        summary["finished"] = now()
        return summary

    guid = opening["guid"]
    summary["guid_present"] = bool(guid)       # the guid is a session bearer token
    summary["win_levels"] = opening.get("win_levels")
    summary["available_actions"] = opening.get("available_actions")

    prev_last: Optional[str] = None
    record = {"seq": 0, "t": now(), "game_id": game, "action": "RESET",
              "action_id": None, "data": None, "http_status": status,
              "attempts": stats["attempts"],
              "state": opening.get("state"),
              "levels_completed": opening.get("levels_completed"),
              "win_levels": opening.get("win_levels"),
              "available_actions": opening.get("available_actions"),
              "full_reset": opening.get("full_reset"),
              "expected_batch_hash": expected[0] if expected else None}
    record.update(analyse(opening.get("frame"), prev_last))
    record["matches_expected"] = (None if record["expected_batch_hash"] is None
                                  else record["batch_hash"] == record["expected_batch_hash"])
    recorder.write(record)
    summary["steps"].append(record)
    if record["frame_hashes"]:
        prev_last = record["frame_hashes"][-1]

    for index, (action, data) in enumerate(sequence):
        body: Dict[str, Any] = {"game_id": game, "card_id": card_id, "guid": guid}
        if data is not None:
            body.update(data)
        status, response, stats = send_command(
            client, "/api/cmd/ACTION%d" % action, body,
            note="p20 ACTION%d #%d %s" % (action, index, game),
            attempts=ACTION_ATTEMPTS, delay_cap=5.0)
        summary["http_calls"] += stats["attempts"]
        want = expected[index + 1] if index + 1 < len(expected) else None
        record = {"seq": index + 1, "t": now(), "game_id": game,
                  "action": "ACTION%d" % action, "action_id": action,
                  "data": data, "http_status": status,
                  "attempts": stats["attempts"], "expected_batch_hash": want}
        if status != 200 or not isinstance(response, dict):
            # A refusal is evidence, not an absence (LEDGER_FORMAT §3). It is
            # recorded in full and the sequence stops -- a session that lost a
            # frame is no longer the history the rest of the sequence assumes.
            record.update({"error": str(response)[:300], "n_frames": None,
                           "batch_hash": None, "frame_hashes": None,
                           "distinct_frames": None, "intra_batch_changes": None,
                           "shapes": None, "first_equals_prev_last": None,
                           "matches_expected": None})
            recorder.write(record)
            summary["steps"].append(record)
            summary["stopped_early_at"] = index + 1
            break
        summary["actions_executed"] += 1
        record.update({"state": response.get("state"),
                       "levels_completed": response.get("levels_completed"),
                       "win_levels": response.get("win_levels"),
                       "available_actions": response.get("available_actions"),
                       "full_reset": response.get("full_reset")})
        record.update(analyse(response.get("frame"), prev_last))
        record["matches_expected"] = (None if want is None
                                      else record["batch_hash"] == want)
        recorder.write(record)
        summary["steps"].append(record)
        if record["frame_hashes"]:
            prev_last = record["frame_hashes"][-1]

    summary["finished"] = now()
    summary["cookies_enabled"] = client.transport["cookies"]
    summary["cookies_held"] = client.cookies_held()      # names only (INC-008)
    multi = [s for s in summary["steps"] if (s.get("n_frames") or 0) > 1]
    summary["cascade"] = {
        "responses_with_multiple_frames": len(multi),
        "max_frames": max([s.get("n_frames") or 0 for s in summary["steps"]] or [0]),
        "multi_frame_batches_with_internal_change":
            sum(1 for s in multi if (s.get("intra_batch_changes") or 0) > 0),
        "multi_frame_batches_all_identical":
            sum(1 for s in multi if s.get("distinct_frames") == 1),
    }
    with open(os.path.join(run_dir, "summary.%s.json" % game), "w",
              encoding="utf-8", newline="") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    return summary


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", required=True, choices=sorted(spec.SEQUENCES))
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--set", dest="which", default="main",
                        choices=sorted(spec.SETS))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    summary = run(args.game, os.path.abspath(args.run_dir), args.dry_run,
                  args.which)
    print(json.dumps({k: v for k, v in summary.items() if k != "steps"},
                     indent=2, sort_keys=True))
    for step in summary.get("steps", []):
        print("  %-9s n=%-2s distinct=%-2s changes=%-2s expected=%s %s"
              % (step["action"], step.get("n_frames"), step.get("distinct_frames"),
                 step.get("intra_batch_changes"), step.get("matches_expected"),
                 step.get("error", "")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
