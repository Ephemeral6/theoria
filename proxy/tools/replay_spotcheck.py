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

## The third harness, and why the two rules were not enough

`theoria-arm`'s live legs of 2026-07-31 are canonical v1.0 ledgers written by
a harness neither of the above knew about, and this tool read exactly zero
sessions out of them: `INSUFFICIENT, 0 session(s) with a failure-free
opening`. The cause is a shape the ar25 sources never had. The arm records a
*refused* command as its own `env_step` at its own `step_idx` and then retries
under the next one, so a leg that ends with 34 frames spends 234 step
indices getting there -- and step 0 is a refusal in every leg. Truncating at
the first failed step therefore truncates at the first step.

So a third rule, off by default (`--compact-refusals`):

  * **A refusal that provably executed nothing is not a step.** Only one shape
    qualifies today (`400 SERVER_ERROR`, `game <id> not found`, no frame, and
    `n_frames: 0`), it is a closed whitelist, and anything outside it still
    truncates the session exactly as before. `refusals_compacted` in the
    report says how many rows each session lost, so a reader can see the
    compaction rather than infer it.

The whitelist is narrow on purpose, but the *direction* of the residual risk
is what makes the rule safe. Suppose a refusal did secretly execute. Then two
sessions that met different numbers of them have genuinely different
histories, and comparing them position by position produces a *disagreement*
-- a FAIL, not a false PASS. Compaction can manufacture alarm; it cannot
manufacture agreement. Every position still has to carry the same command
name in every session or the comparison stops there, and the contiguity check
now runs over the raw `step_idx` space, so a dropped row still has to be
accounted for by a refusal rather than by a hole.

    python -m proxy.tools.replay_spotcheck --canon out.jsonl --game ar25-0c556536
    python -m proxy.tools.replay_spotcheck --canon out.jsonl \
        --recon arc-recon/data/recon_ledger.jsonl --game ar25-0c556536 -o report.json
    python -m proxy.tools.replay_spotcheck --compact-refusals --game g50t-5849a774 \
        --canon theoria-arm/runs/20260731T1240Z-A3-level2-carried/ledger.jsonl \
        --canon theoria-arm/runs/20260731T1310Z-A3-level2-carried-r2/ledger.jsonl
"""

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

from ..ledger import frame_hash, read_ledger

#: One step of one session: what was commanded, and what came back.
Step = Dict[str, Any]

#: The closed whitelist of refusals that provably ran nothing upstream.
#: Keyed by the name that appears in `refusals_compacted`, so a report says
#: which shape was compacted and not merely how many rows.
#:
#: `game <id> not found` is a lookup failure: the API could not resolve the
#: game, so there was no game to apply the command to, no frame came back, and
#: `n_frames` is 0. It is also not charged -- the scorecard counts successful
#: actions only (baseline-arms' four-sample measurement, PARTNER_SYNC
#: 2026-07-28), which is a second, independent witness that nothing ran.
#:
#: Adding a shape here is a claim about upstream behaviour, not a convenience.
#: The default is still to truncate, and an unrecognised failure always does.
_GAME_NOT_FOUND = re.compile(r"^game \S+ not found$")


def non_executing_refusal(record: Dict[str, Any]) -> Optional[str]:
    """The refusal shape this row matches, or None.

    None covers both "it succeeded" and "it failed in a way we cannot claim to
    understand"; the caller treats the second as a hard truncation, which is
    the pre-existing behaviour and the safe one.
    """
    http = record.get("http") or {}
    if http.get("status") != 400:
        return None
    if record.get("frames") is not None or (record.get("n_frames") or 0) != 0:
        return None
    response = record.get("response")
    if not isinstance(response, dict) or response.get("error") != "SERVER_ERROR":
        return None
    if _GAME_NOT_FOUND.match(str(response.get("message", ""))):
        return "game-not-found"
    return None


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
            "refusal": non_executing_refusal(record),
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

    A label is not always a single session. The g50t-5849a774 precheck shows
    the other shape: several aborted passes (a successful RESET whose first
    ACTION then failed and was abandoned) and a later partial pass, all under
    the same `run-a` / `run-b` label. Folding those into one session would
    put two RESET frames at position 0 of the same history and then interleave
    two different sweeps -- a fabricated disagreement. So every *successful*
    RESET opens a new pass, and each pass is its own session: the first pass
    of a label keeps the plain `recon/<label>` name (which is what the ar25
    spot check archived, so that report stays reproducible), later passes are
    `recon/<label>#2`, `#3`, ... An aborted pass survives as a one-step
    session; that is honest -- its RESET frame really was observed, and the
    spot check only counts positions at least two sessions reach.
    """
    out: Dict[str, List[Step]] = {}
    passes: Dict[str, int] = {}
    current: Dict[str, str] = {}
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
            if name == "RESET":
                # A successful RESET opens a new pass of this label.
                passes[label] = passes.get(label, 0) + 1
                current[label] = "recon/" + label + (
                    "" if passes[label] == 1 else "#%d" % passes[label])
            session = current.get(label)
            if session is None:
                # An action with no successful RESET before it under this
                # label: no history to attach it to.
                continue
            out.setdefault(session, []).append({
                "step_idx": step_idx,
                "action": name,
                "frame_hash": frame_hash(frames),
                "ok": frames is not None,
            })
    for steps in out.values():
        steps.sort(key=lambda s: s["step_idx"])
    return out


def clean_prefix(steps: List[Step],
                 compact_refusals: bool = False) -> Tuple[List[Step],
                                                          Dict[str, int]]:
    """Everything up to the first step that did not come back with a frame --
    or that does not sit at the next contiguous `step_idx`.

    The contiguity rule exists because a session can have holes: the g50t
    precheck alternated full and short game-id spellings, and the short-id
    rows fail the game filter, so its sessions arrive as step_idx 0,1,2,6,7,8.
    Comparison positions are list indices; without the rule, the step at
    step_idx 6 would be compared at position 3 against other sessions' fourth
    command -- a misalignment wearing a disagreement's clothes. Steps past a
    hole are real observations at a position this filtered history cannot
    name, so they are dropped, not shifted.

    `compact_refusals` drops rows matching `non_executing_refusal` instead of
    truncating on them. Note what does *not* change: contiguity is still
    checked against the raw `step_idx` counter, not against the length of the
    retained list. A dropped row therefore still has to be paid for by a
    refusal at that exact index; a genuine hole in the numbering is still a
    hole, and still truncates. Returns the prefix and a count per refusal
    shape, because a compaction a reader cannot see is a compaction a reader
    cannot check."""
    prefix: List[Step] = []
    compacted: Dict[str, int] = {}
    seen = 0
    for step in steps:
        if step["step_idx"] != seen:
            break
        seen += 1
        shape = step.get("refusal")
        if compact_refusals and shape and not step["ok"]:
            compacted[shape] = compacted.get(shape, 0) + 1
            continue
        if not step["ok"]:
            break
        prefix.append(step)
    return prefix, compacted


def spotcheck(sessions: Dict[str, List[Step]], game_id: str,
              compact_refusals: bool = False) -> Dict[str, Any]:
    built = {name: clean_prefix(steps, compact_refusals)
             for name, steps in sessions.items()}
    prefixes = {name: prefix for name, (prefix, _) in built.items() if prefix}
    compacted = {name: counts for name, (prefix, counts) in built.items()
                 if prefix and counts}
    # The `policy` block appears only under compaction, and deliberately so:
    # the strict path's output has to stay byte-identical to the reports
    # already archived under `proxy/runs/` (P-9's ar25 check, the closeout
    # g50t check) and hashed in their manifests. A provenance record you can
    # no longer reproduce is a provenance record you have to take on trust.
    policy = {"refusals": "compacted",
              "compactable_shapes": ["game-not-found"],
              "refusals_compacted": compacted}
    if len(prefixes) < 2:
        report = {"game_id": game_id, "verdict": "INSUFFICIENT",
                  "detail": "%d session(s) with a failure-free opening; "
                            "agreement needs at least two" % len(prefixes),
                  "sessions": sorted(prefixes)}
        if compact_refusals:
            report["policy"] = policy
        return report

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
    report = {
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
    if compact_refusals:
        report["policy"] = policy
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--canon", action="append", default=[],
                    help="a canonical v1.0 ledger; may be given more than once")
    ap.add_argument("--recon", default=None,
                    help="arc-recon/data/recon_ledger.jsonl (read-only)")
    ap.add_argument("--game", required=True)
    ap.add_argument("--compact-refusals", action="store_true",
                    help="treat a refusal that provably executed nothing "
                         "(400 SERVER_ERROR / game not found, no frame) as "
                         "not-a-step instead of truncating there. Required to "
                         "read theoria-arm ledgers, which give every retried "
                         "refusal its own step_idx")
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args(argv)

    sessions: Dict[str, List[Step]] = {}
    origin: Dict[str, str] = {}
    for path in args.canon:
        found = sessions_from_canon(path, args.game)
        origin.update({name: path for name in found})
        sessions.update(found)
    if args.recon:
        sessions.update(sessions_from_recon(args.recon, args.game))

    report = spotcheck(sessions, args.game, args.compact_refusals)
    report["sources"] = {"canon": args.canon, "recon": args.recon}
    if args.compact_refusals:
        # Which ledger each session came out of. Only under compaction, for
        # the byte-stability reason above -- and it earns its place there,
        # because compaction is the mode in which one file is one session and
        # "26 sessions" stops being the whole provenance story.
        report["session_origin"] = {name: origin[name]
                                    for name in report.get("sessions", [])
                                    if name in origin}
    blob = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="") as fh:
            fh.write(blob + "\n")
    print(blob)
    return 0 if report["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
