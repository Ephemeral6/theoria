"""Adapter for the `env_step` / `model_call` ledger.

This is the format `baseline-arms/harness/ledger.py` already writes, and the
format `proxy/LEDGER_FORMAT.md` is expected to standardise (see
`battery/INPUT_FORMAT.md` for what this adapter assumes and where it will have
to move).  Two record shapes share one file and are told apart structurally:

    env_step    has `frame`
    model_call  has `usage`

Grouping is by `run_id`.  `model_call` rows carry `run_id` but no `arm`, so the
arm and model are taken from the run's `env_step` rows; a run made only of
model calls is reported rather than dropped.

**The guardrail runs here**, before a single frame is digested, because this is
the first place a sealed `game_id` could enter the battery.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, List, Optional

from battery.guard import Piles, load_piles
from battery.model import Call, Run, Step, digest


def _canonical_action(action: Any) -> str:
    """A stable string for an action of any shape.

    The live API sends `{"id": 6, "data": {"x": 32, "y": 55}}`; the A0 world
    sends `"DOWN"`.  Coordinates are part of the action's identity — clicking
    two different cells is two different actions — so they stay in the key.
    """
    if isinstance(action, str):
        return action
    if isinstance(action, dict):
        aid = action.get("id")
        data = action.get("data")
        if data:
            return "ACTION%s(%s)" % (
                aid, json.dumps(data, sort_keys=True, separators=(",", ":")))
        return "ACTION%s" % aid
    return json.dumps(action, sort_keys=True, separators=(",", ":"))


def _state_key(frame: Any) -> Optional[str]:
    """Digest the observation the next action is chosen from.

    One action can return several frames (the environment's internal ticks).
    The last one is the state the arm actually sees next, so that is the one
    that carries state identity; the count is kept separately on the step.
    """
    if not frame:
        return None
    if isinstance(frame, list) and frame and isinstance(frame[0], list):
        return digest(frame[-1])
    return digest(frame)


def _n_frames(row: Dict[str, Any]) -> Optional[int]:
    if row.get("frames_returned") is not None:
        return int(row["frames_returned"])
    frame = row.get("frame")
    if isinstance(frame, list):
        return len(frame)
    return None


def _usage_int(usage: Dict[str, Any], key: str) -> int:
    value = usage.get(key)
    return int(value) if isinstance(value, (int, float)) else 0


def parse_rows(rows: Iterable[Dict[str, Any]], *, source: str,
               piles: Optional[Piles] = None,
               default_arm: str = "unknown") -> List[Run]:
    piles = piles or load_piles()
    by_run: Dict[str, Dict[str, Any]] = {}

    for row in rows:
        run_id = row.get("run_id")
        if not run_id:
            continue
        bucket = by_run.setdefault(
            run_id, {"env": [], "model": [], "game_id": None,
                     "arm": None, "model_name": None})
        game_id = row.get("game_id")
        if game_id is not None:
            # The guardrail, at the earliest point a sealed id could enter.
            piles.assert_playable(game_id)
            bucket["game_id"] = game_id
        if "frame" in row:
            bucket["env"].append(row)
            bucket["arm"] = bucket["arm"] or row.get("arm")
            bucket["model_name"] = bucket["model_name"] or row.get("model")
        elif "usage" in row:
            bucket["model"].append(row)
            bucket["model_name"] = bucket["model_name"] or row.get("model")

    runs: List[Run] = []
    for run_id in sorted(by_run):
        bucket = by_run[run_id]
        env_rows = sorted(bucket["env"], key=lambda r: (r.get("step_idx", 0),))
        call_rows = sorted(bucket["model"],
                           key=lambda r: (r.get("step_idx") is None,
                                          r.get("step_idx", 0),
                                          r.get("timestamp", "")))

        steps: List[Step] = []
        for i, row in enumerate(env_rows):
            failed = bool(row.get("failed"))
            steps.append(Step(
                idx=i,
                action=_canonical_action(row.get("action")),
                state_key=None if failed else _state_key(row.get("frame")),
                failed=failed,
                n_frames=_n_frames(row),
                level=row.get("levels_completed"),
                won=row.get("state") == "WIN",
            ))

        calls: List[Call] = []
        for i, row in enumerate(call_rows):
            usage = row.get("usage") or {}
            calls.append(Call(
                idx=i,
                step_idx=row.get("step_idx"),
                input_tokens=_usage_int(usage, "input_tokens"),
                output_tokens=_usage_int(usage, "output_tokens"),
                cache_read_tokens=_usage_int(usage, "cache_read_input_tokens"),
                cache_creation_tokens=_usage_int(
                    usage, "cache_creation_input_tokens"),
                cost_usd=row.get("total_cost_usd"),
                duration_ms=row.get("duration_ms"),
                is_error=bool(row.get("is_error")),
            ))

        game_id = bucket["game_id"]
        runs.append(Run(
            run_id=run_id,
            arm=bucket["arm"] or default_arm,
            source=source,
            model=bucket["model_name"],
            game_id=game_id,
            pile=piles.assert_playable(game_id),
            steps=steps,
            calls=calls,
            notes={"env_rows": len(env_rows), "call_rows": len(call_rows)},
        ))
    return runs


def load_ledger_runs(path: str, *, piles: Optional[Piles] = None,
                     source: Optional[str] = None) -> List[Run]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    return parse_rows(rows, source=source or os.path.basename(path),
                      piles=piles)
