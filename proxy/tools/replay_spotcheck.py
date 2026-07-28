"""Bit-exact replay spot check, run against ledgers that already exist.

`Theoria.md`'s Phase 1 acceptance list has a line reading "复放抽检 ⟨2⟩ 局环境
侧逐比特一致" -- for a sample of games, the environment side must reproduce bit
for bit. Until now that line had no data behind it: `proxy/replay.py` performs a
real replay, but a real replay costs actions on a live scorecard, and no live
run has gone through the proxies yet.

It turns out the evidence was already on disk. `baseline-arms`'s envelope
campaign opened fourteen independent sessions on `ar25-0c556536`, and its
harness begins every session with the same fixed probe sweep -- RESET, then
ACTION1 through ACTION7 -- before the model gets to choose anything. Fourteen
sessions with an identical action prefix are fourteen replays of that prefix.
`arc-recon`'s determinism precheck ran the same opening on the same game in a
different campaign, on a different day, through a different harness.

So this tool does not replay anything. It reads sessions that already happened,
finds the longest opening on which they all issued the same commands, and
compares their frame hashes position by position. Cost: zero actions, zero
dollars, zero API calls.

## The two rules that keep it honest

  * **A session is truncated at its first failed step.** A 400 or a 500 returns
    no frame, and the next command in a session that lost one is not the same
    command as in a session that did not. Comparing across a failure would be
    comparing two different histories and calling the difference
    non-determinism.
  * **Agreement is only claimed where at least two sessions reach the
    position.** One session agreeing with itself is not evidence.

What this shows is cross-session, cross-campaign determinism of the
environment. What it does not show is that *our* proxies reproduce a run --
that needs a live replay through `proxy/replay.py`, and it is still owed.

    python -m proxy.tools.replay_spotcheck --canon out.jsonl --game ar25-0c556536
    python -m proxy.tools.replay_spotcheck --canon out.jsonl \
        --recon arc-recon/data/recon_ledger.jsonl --game ar25-0c556536 -o report.json
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

from ..ledger import frame_hash, read_ledger

#: One step of one session: what was commanded, and what came back.
Step = Dict[str, Any]


def _action_key(action: Dict[str, Any]) -> str:
    name = action.get("name")
    data = action.get("data")
    return name if data in (None, {}) else "%s(%s)" % (
        name, json.dumps(data, sort_keys=True, separators=(",", ":")))


def sessions_from_canon(path: str, game_id: str) -> Dict[str, List[Step]]:
    """Sessions from a canonical v1.0 ledger, one per `run_id`."""
    out: Dict[str, List[Step]] = {}
    for record in read_ledger(path):
        if record.get("event") != "env_step" or record.get("game_id") != game_id:
            continue
        status = (record.get("http") or {}).get("status")
        out.setdefault(record["run_id"], []).append({
            "step_idx": record.get("step_idx"),
            "action": _action_key(record.get("action") or {}),
            "frame_hash": record.get("frame_hash"),
            "ok": status == 200 and record.get("frames") is not None,
        })
    for steps in out.values():
        steps.sort(key=lambda s: s["step_idx"])
    return out


def sessions_from_recon(path: str, game_id: str) -> Dict[str, List[Step]]:
    """Sessions from `arc-recon/data/recon_ledger.jsonl`.

    A read-only adapter for an artefact that predates the canon. It is not a
    migrator and writes nothing: the precheck ledger belongs to another
    surface, and the point of consulting it is precisely that it is an
    independent record made by a different harness on a different day.

    The precheck's `note` field carries the run label (`... run-a`, `run-b`),
    which is what separates its two passes.
    """
    out: Dict[str, List[Step]] = {}
    if not os.path.exists(path):
        return out
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            url = record.get("url") or ""
            if "/api/cmd/" not in url:
                continue
            request = record.get("request_body") or {}
            if request.get("game_id") != game_id:
                continue
            note = record.get("note") or ""
            if not note.startswith("precheck "):
                continue
            # "precheck ACTION3 #2 ar25-0c556536 run-b attempt 4"
            labels = [tok for tok in note.split() if tok.startswith("run-")]
            indices = [tok for tok in note.split() if tok.startswith("#")]
            if not labels:
                continue
            label = labels[0]
            if record.get("status") != 200:
                continue
            body = record.get("response_body")
            frames = body.get("frame") if isinstance(body, dict) else None
            if frames is not None and not isinstance(frames, list):
                frames = [frames]
            name = url.rsplit("/", 1)[-1]
            # The precheck numbers its actions from #0 and does not number
            # RESET; canon puts RESET at step 0, so shift to match.
            step_idx = 0 if name == "RESET" else int(indices[0][1:]) + 1
            out.setdefault("recon/" + label, []).append({
                "step_idx": step_idx,
                "action": name,
                "frame_hash": frame_hash(frames),
                "ok": frames is not None,
            })
    for steps in out.values():
        steps.sort(key=lambda s: s["step_idx"])
    return out


def clean_prefix(steps: List[Step]) -> List[Step]:
    """Everything up to the first step that did not come back with a frame."""
    prefix: List[Step] = []
    for step in steps:
        if not step["ok"]:
            break
        prefix.append(step)
    return prefix


def spotcheck(sessions: Dict[str, List[Step]], game_id: str) -> Dict[str, Any]:
    prefixes = {name: clean_prefix(steps) for name, steps in sessions.items()}
    prefixes = {k: v for k, v in prefixes.items() if v}
    if len(prefixes) < 2:
        return {"game_id": game_id, "verdict": "INSUFFICIENT",
                "detail": "%d session(s) with a failure-free opening; agreement "
                          "needs at least two" % len(prefixes),
                "sessions": sorted(prefixes)}

    comparisons: List[Dict[str, Any]] = []
    disagreements: List[Dict[str, Any]] = []
    position = 0
    while True:
        present = {name: steps[position] for name, steps in prefixes.items()
                   if len(steps) > position}
        if len(present) < 2:
            break
        actions = {step["action"] for step in present.values()}
        if len(actions) > 1:
            # The sessions have stopped issuing the same command. Everything
            # after this point is a different experiment, not a replay.
            break
        hashes = {name: step["frame_hash"] for name, step in present.items()}
        distinct = sorted(set(hashes.values()))
        entry = {"position": position, "action": actions.pop(),
                 "sessions": len(present), "frame_hash": distinct[0],
                 "agree": len(distinct) == 1}
        if len(distinct) > 1:
            entry["distinct_hashes"] = distinct
            entry["by_session"] = hashes
            disagreements.append(entry)
        comparisons.append(entry)
        position += 1

    pairwise = sum(c["sessions"] * (c["sessions"] - 1) // 2 for c in comparisons)
    return {
        "game_id": game_id,
        "sessions": sorted(prefixes),
        "n_sessions": len(prefixes),
        "steps_compared": len(comparisons),
        "pairwise_comparisons": pairwise,
        "comparisons": comparisons,
        "disagreements": disagreements,
        "verdict": "PASS" if comparisons and not disagreements else (
            "FAIL" if disagreements else "INSUFFICIENT"),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--canon", action="append", default=[],
                    help="a canonical v1.0 ledger; may be given more than once")
    ap.add_argument("--recon", default=None,
                    help="arc-recon/data/recon_ledger.jsonl (read-only)")
    ap.add_argument("--game", required=True)
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args(argv)

    sessions: Dict[str, List[Step]] = {}
    for path in args.canon:
        sessions.update(sessions_from_canon(path, args.game))
    if args.recon:
        sessions.update(sessions_from_recon(args.recon, args.game))

    report = spotcheck(sessions, args.game)
    report["sources"] = {"canon": args.canon, "recon": args.recon}
    blob = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="") as fh:
            fh.write(blob + "\n")
    print(blob)
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
