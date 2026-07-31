"""The referee: five numbers per direction, and the divergence list.

Run from the worktree root:

    python -m crosscheck.judge.score              # both directions
    python -m crosscheck.judge.score s_on_c       # one

Each direction is scored on

1. **replay** -- the visitor's predictor against every frame of every episode the
   bridge served it. The cheap layer, and the one a manual can pass while being
   wrong; reported because failing it is disqualifying, not because passing it
   proves anything.
2. **held-out** -- the same predictor against the world over every state the
   level can represent, and separately over the reachable ones.
3. **rule recovery** -- per mechanism of the incumbent manual, measured
   behaviourally (see `native.native_firing`).
4. **plan** -- the visitor's actions executed in the true world; its
   `unsolvable` verdicts against ground truth.
5. **divergence** -- visitor vs. incumbent over the same sweep, and the subset
   where both are wrong.

The incumbent is scored on exactly the same sweep, because a visitor's accuracy
is only interpretable next to what the author of the world achieved on it.
"""

import argparse
import importlib.util
import json
import os
import sys
from typing import Any, Callable, Dict, List, Optional, Sequence

from a2_crosscheck.bridge import open_world
from a2_crosscheck.judge import native, sweep, truth

Frame = List[List[int]]

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CROSSCHECK = os.path.join(HERE, "crosscheck")

DIRECTIONS = {
    "s_on_c": {"visitor": "a0-spike", "world": "C", "host": "cold-start-a0"},
    "c_on_s": {"visitor": "cold-start-a0", "world": "S", "host": "a0-spike"},
}


# ------------------------------------------------------------------- loading

def load_visitor(direction: str) -> Optional[Any]:
    path = os.path.join(CROSSCHECK, direction, "predictor.py")
    if not os.path.isfile(path):
        return None
    spec = importlib.util.spec_from_file_location("_cc_visitor_%s" % direction, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_json(direction: str, name: str) -> Optional[Any]:
    path = os.path.join(CROSSCHECK, direction, name)
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


# -------------------------------------------------------------------- replay

def score_replay(world_id: str, visitor: Any,
                 episodes: Sequence[Any]) -> Dict[str, Any]:
    """Full-history replay of the bridge's own episodes through the manual."""
    frames_checked = 0
    failures: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    for index, episode in enumerate(episodes):
        frame = [list(row) for row in episode.frames[0]]
        for t, action in enumerate(episode.actions):
            try:
                frame = visitor.step_frame(episode.level_id, frame, action)
            except Exception as exc:
                errors.append({"episode": index, "t": t,
                               "error": "%s: %s" % (type(exc).__name__,
                                                    str(exc)[:160])})
                break
            frames_checked += 1
            observed = [list(row) for row in episode.frames[t + 1]]
            if [list(r) for r in frame] != observed:
                failures.append({"episode": index, "level": episode.level_id,
                                 "t": t, "action": action})
                break
    return {
        "episodes": len(episodes),
        "frames_checked": frames_checked,
        "n_failures": len(failures),
        "failures": failures[:20],
        "n_errors": len(errors),
        "errors": errors[:20],
        "replay_exact": not failures and not errors,
    }


# ------------------------------------------------------------- rule recovery

def score_rule_recovery(world_id: str, predictor: Callable[..., Frame],
                        levels: Sequence[str]) -> Dict[str, Any]:
    per_rule: Dict[str, Dict[str, int]] = {}
    for level_id in levels:
        for frame in truth.representable_frames(world_id, level_id):
            for action in truth.actions_of(world_id):
                fired = native.native_firing(world_id, level_id, frame, action)
                if not fired:
                    continue
                actual = truth.truth_step_frame(world_id, level_id, frame, action)
                try:
                    predicted = predictor(level_id, frame, action)
                    agrees = [list(r) for r in predicted] == [list(r) for r in actual]
                except Exception:
                    agrees = False
                for name in fired:
                    entry = per_rule.setdefault(name, {"cases": 0, "correct": 0})
                    entry["cases"] += 1
                    entry["correct"] += int(agrees)
    for entry in per_rule.values():
        entry["accuracy"] = (round(entry["correct"] / entry["cases"], 6)
                             if entry["cases"] else None)
        entry["recovered"] = entry["cases"] > 0 and entry["correct"] == entry["cases"]
    recovered = [n for n, e in per_rule.items() if e["recovered"]]
    return {
        "mechanisms": len(per_rule),
        "recovered": len(recovered),
        "recovery_rate": (round(len(recovered) / len(per_rule), 6)
                          if per_rule else None),
        "per_rule": dict(sorted(per_rule.items())),
        "missed": sorted(n for n in per_rule if n not in recovered),
    }


# ---------------------------------------------------------------------- plan

def score_plan(world_id: str, plan: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for level_id in truth.TASK_LEVELS_OF[world_id]:
        fact = truth.solvable(world_id, level_id)
        entry: Dict[str, Any] = {
            "truth_solvable": fact["solvable"],
            "truth_optimal_length": fact["optimal_length"],
        }
        claim = (plan or {}).get(level_id)
        if claim is None:
            entry.update({"claimed": None, "verdict_agrees": None})
            out[level_id] = entry
            continue
        verdict = str(claim.get("verdict", "")).lower()
        entry["claimed"] = verdict
        entry["reason"] = claim.get("reason")
        entry["verdict_agrees"] = (
            (verdict == "solved") == bool(fact["solvable"])
        )
        if verdict == "solved":
            actions = list(claim.get("actions") or [])
            run = truth.execute(world_id, level_id, actions)
            entry.update({
                "plan_length": run["length"],
                "won": run["won"],
                "won_at": run["won_at"],
                "optimal": run["won"] and run["won_at"] == fact["optimal_length"],
            })
        else:
            entry["gave_a_reason"] = bool(str(claim.get("reason") or "").strip())
        out[level_id] = entry
    return out


# ------------------------------------------------------------------ the whole

def score_direction(direction: str, max_records: int = 60) -> Dict[str, Any]:
    meta = DIRECTIONS[direction]
    world_id = meta["world"]
    report: Dict[str, Any] = {"direction": direction, **meta}

    visitor = load_visitor(direction)
    report["visitor_present"] = visitor is not None

    predictors: Dict[str, Callable[..., Frame]] = {
        "incumbent": lambda lid, f, a, w=world_id: native.native_step_frame(w, lid, f, a),
    }
    if visitor is not None:
        predictors["visitor"] = lambda lid, f, a: visitor.step_frame(lid, f, a)

    report["sweep"] = sweep.sweep_world(world_id, predictors,
                                        max_records=max_records)
    report["incumbent_source"] = native.SOURCE[world_id]

    if visitor is not None:
        episodes = replay_episodes(direction)
        report["replay"] = score_replay(world_id, visitor, episodes)
        report["rule_recovery"] = score_rule_recovery(
            world_id, predictors["visitor"], truth.LEVELS_OF[world_id])
        report["incumbent_rule_recovery"] = score_rule_recovery(
            world_id, predictors["incumbent"], truth.LEVELS_OF[world_id])
        report["plan"] = score_plan(world_id, load_json(direction, "plan.json"))
    return report


def replay_episodes(direction: str) -> List[Any]:
    """Re-serve the episodes the visitor recorded, so replay is on its evidence.

    A direction that saved `episodes.json` (a list of `{level_id, actions}`) is
    replayed on exactly what it saw. Otherwise the referee falls back to a fixed
    sweep of short prefixes, which is weaker evidence and is labelled as such.
    """
    world_id = DIRECTIONS[direction]["world"]
    world = open_world(world_id)
    recorded = load_json(direction, "episodes.json")
    episodes = []
    if recorded:
        for item in recorded:
            episodes.append(world.rollout(item["level_id"], item["actions"]))
        return episodes
    for level_id in truth.LEVELS_OF[world_id]:
        for action in truth.actions_of(world_id):
            episodes.append(world.rollout(level_id, [action] * 6))
    return episodes


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directions", nargs="*", default=None,
                        choices=sorted(DIRECTIONS) + [[]], help="default: both")
    parser.add_argument("--out", default=None, help="write JSON here")
    parser.add_argument("--max-records", type=int, default=60)
    args = parser.parse_args(argv)

    chosen = args.directions or sorted(DIRECTIONS)
    report = {d: score_direction(d, max_records=args.max_records) for d in chosen}

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(report, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")

    for direction, entry in sorted(report.items()):
        print("=" * 72)
        print("%s -- %s's pipeline on world %s" %
              (direction, entry["visitor"], entry["world"]))
        if not entry["visitor_present"]:
            print("  no predictor.py yet; incumbent-only sweep")
        for scope in ("representable", "reachable"):
            totals = entry["sweep"]["totals"][scope]
            print("  %-14s %5d cases" % (scope, totals["cases"]))
            for name, stats in sorted(totals["per_predictor"].items()):
                print("      %-10s correct %5d  wrong %4d  refused %4d  acc %.4f"
                      % (name, stats["correct"], stats["wrong"],
                         stats["refused"], stats["accuracy"] or 0.0))
            print("      disagreements %d   both-wrong %d"
                  % (totals["n_disagreements"], totals["n_joint_errors"]))
        if entry.get("replay"):
            r = entry["replay"]
            print("  replay         %d frames, exact=%s"
                  % (r["frames_checked"], r["replay_exact"]))
        if entry.get("rule_recovery"):
            rr = entry["rule_recovery"]
            print("  rule recovery  %d/%d mechanisms  missed=%s"
                  % (rr["recovered"], rr["mechanisms"], rr["missed"] or "none"))
        for level_id, p in sorted((entry.get("plan") or {}).items()):
            print("  plan %-9s claimed=%s truth_solvable=%s agrees=%s won=%s"
                  % (level_id, p.get("claimed"), p["truth_solvable"],
                     p.get("verdict_agrees"), p.get("won")))
    if args.out:
        print("\n  report -> %s" % args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
