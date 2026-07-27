"""Generate the frozen synthetic ledger the tests run against.

    python -m battery.tests.make_fixture

Synthetic on purpose, for three reasons:

* `baseline-arms/ledger.jsonl` is append-only and another session may be
  writing to it right now, so a test pinned to the live file would fail for
  reasons that have nothing to do with the battery;
* it belongs to another track, and copying it here would fork someone else's
  data;
* a hand-built fixture can contain the shapes that matter and are rare in real
  data -- a failed step, a run with no model calls, a run too short to support
  a trend, a deliberately front-loaded cost curve.

The generator is seeded and byte-stable: regenerating over an unchanged
generator produces an identical file. Only development-pile game ids appear.
"""

from __future__ import annotations

import json
import os
import random
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURE = os.path.join(HERE, "fixtures", "ledger_fixture.jsonl")

SEED = 20260728
GAMES = ["ar25-0c556536", "g50t-5849a774", "sk48-d8078629", "tn36-ef4dde99"]
# Weakest rung first; the fixture encodes a capability gradient so the
# discrimination pass has something with a known answer to be tested against.
LADDER = [
    ("claude-haiku-4-5-20251001", 0.55, 1.9),
    ("claude-sonnet-5", 0.30, 1.4),
    ("claude-opus-5", 0.12, 1.0),
]
TURNS = 16


def _frame(rng: random.Random, token: int) -> List[List[List[int]]]:
    """A 4x4 grid standing in for an observation. `token` fixes its identity,
    so a repeated token is a genuinely revisited state."""
    rng_local = random.Random(token)
    return [[[rng_local.randrange(4) for _ in range(4)] for _ in range(4)]]


def build() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for game in GAMES:
        for model, revisit_p, cost_tail in LADDER:
            rng = random.Random("%s|%s|%d" % (game, model, SEED))
            run_id = "bare_cc-%s-%s-fixture" % (game.split("-")[0], model)
            visited: List[int] = []
            for turn in range(TURNS):
                # A weaker rung revisits more often -- the gradient the
                # discrimination pass is supposed to detect.
                if visited and rng.random() < revisit_p:
                    token = rng.choice(visited)
                else:
                    token = rng.randrange(10_000)
                    visited.append(token)

                failed = rng.random() < 0.08
                step: Dict[str, Any] = {
                    "action": {"id": rng.randrange(1, 8), "data": None},
                    "arm": "bare_cc",
                    "frame": None if failed else _frame(rng, token),
                    "game_id": game,
                    "model": model,
                    "run_id": run_id,
                    "step_idx": turn,
                    "timestamp": "2026-07-28T00:%02d:00Z" % turn,
                }
                if failed:
                    step.update({"failed": True, "http_status": 500,
                                 "reason": "synthetic failure"})
                else:
                    step.update({"available_actions": [1, 2, 3, 4],
                                 "frames_returned": 1,
                                 "levels_completed": 0,
                                 "state": "NOT_FINISHED",
                                 "win_levels": 8})
                rows.append(step)

                # Cost decays for the stronger rungs: a front-loaded bill.
                weight = cost_tail ** (turn / TURNS)
                rows.append({
                    "duration_ms": 1000 + turn * 10,
                    "game_id": game,
                    "is_error": False,
                    "model": model,
                    "provider": "synthetic",
                    "run_id": run_id,
                    "step_idx": turn,
                    "timestamp": "2026-07-28T00:%02d:30Z" % turn,
                    "total_cost_usd": round(0.05 / weight, 8),
                    "usage": {
                        "cache_read_input_tokens": 1000 + turn * 400,
                        "input_tokens": 200,
                        "output_tokens": 300 + turn * 5,
                    },
                })
    return rows


def write(path: str = FIXTURE) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for row in build():
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=True))
            fh.write("\n")
    return path


if __name__ == "__main__":
    print(write())
