"""Ledger alignment: this arm's records are `proxy/LEDGER_FORMAT.md` v1.0.

Phase 1's 同壳 discipline (`Theoria.md:280`, `Theoria.md:290`) says every arm
writes the *same* ledger through the *same* proxies, so that differences are
attributable to the inner loop and not to the recording.  An ablation arm is an
arm, so it has to be able to land in that stream — the calibration in this ticket
is offline, but the interface has to be ready before the arm ever goes online.

**Zero API calls, zero network, zero dollars.**  `proxy.ledger`'s writer is used
directly against a path inside this arm's own run directory, exactly as
`theoria-arm` does (`runs/<slug>/ledger.jsonl`, never `proxy/var/`).  No proxy
process is started and no upstream is contacted.

One honest wrinkle, and it is registered rather than patched around
(DECISIONS D-AB-004).  `proxy.ledger.ARMS` is a frozenset:

    {"bare_cc", "schema_repro", "theoria", "probe", "replay", "mock_arm"}

There is no name in it for an ablation arm, and adding one means editing another
track's file, which every arm README in this repo forbids.  So records go out
under `arm: "theoria"` — true, in that this *is* the Theoria inner loop — and the
`run_start` record carries an `ablation` block naming the incision, the prompt
and the design document.  Auxiliary records have a closed envelope and an open
payload, so that block is legal where an extra field on `env_step` would not be.
A request to register `theoria_ablate` is on PARTNER_SYNC for the proxy track.

The offline worlds have four actions and the ARC action vocabulary has
`ACTIONn`, so the mapping is recorded in `run_start` rather than left implicit.
"""

import os
from typing import Dict, List, Optional, Sequence

import _bootstrap  # noqa: F401

from proxy.ledger import Ledger, RunLedger  # noqa: E402  (imported, never modified)

#: Offline world action -> the ARC-shaped action record.  Stated in `run_start`.
ACTION_MAP = {
    "UP": {"name": "ACTION1", "id": 1, "data": None},
    "DOWN": {"name": "ACTION2", "id": 2, "data": None},
    "LEFT": {"name": "ACTION3", "id": 3, "data": None},
    "RIGHT": {"name": "ACTION4", "id": 4, "data": None},
    "RESET": {"name": "RESET", "id": None, "data": None},
}

ARM = "theoria"

ABLATION_BLOCK = {
    "prompt_id": "P-18",
    "arm": "theoria_minus_theorem_obligations",
    "requested_arm_name": "theoria_ablate",
    "design": "ablation-arm/DESIGN.md",
    "incisions": ["C-1 no Lean form", "C-2 no expensive certify",
                  "C-3 no invariant/goal/unsolvable kwargs",
                  "C-4 naked UNSAT settles", "C-5 playbook theorem tier demoted"],
    "note": ("arm is recorded as `theoria` because proxy.ledger.ARMS has no name "
             "for an ablation arm and this track does not edit proxy/. "
             "See ablation-arm/DECISIONS.md D-AB-004."),
}


def write_episode(path: str, run_id: str, world_name: str,
                  actions: Sequence[str], frames: Sequence[List[List[int]]],
                  wins: Sequence[bool], *, outcome: str,
                  extra_start: Optional[Dict] = None,
                  extra_end: Optional[Dict] = None) -> Dict[str, object]:
    """Write one offline episode as a canonical v1.0 ledger.

    `frames[i]` is the frame *after* `actions[i]`; `frames[0]` is the RESET
    frame, so the record count is `len(actions) + 1`.
    """
    if len(frames) != len(actions) + 1:
        raise ValueError("expected one more frame than actions "
                         "(the RESET frame); got %d frames, %d actions"
                         % (len(frames), len(actions)))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if os.path.exists(path):
        os.remove(path)          # a rerun starts the stream over, as upstream does

    ledger = Ledger(path)
    run = RunLedger(ledger, run_id=run_id, arm=ARM, game_id=world_name)

    start = {
        "game_id": world_name,
        "env_base": "offline: self-built world, no HTTP",
        "model_base": "offline: zero model calls (constraint 8 holds vacuously)",
        "budget": {"api_calls": 0, "model_calls": 0, "usd": 0.0},
        "action_map": ACTION_MAP,
        "ablation": dict(ABLATION_BLOCK),
    }
    start.update(extra_start or {})
    run.run_start(**start)

    offline_http = {"method": None, "path": None, "status": None,
                    "elapsed_ms": None, "attempts": 0}
    run.env_step(world_name, ACTION_MAP["RESET"], frames=[frames[0]],
                 state="NOT_FINISHED", levels_completed=0,
                 http=dict(offline_http))
    for i, action in enumerate(actions):
        won = bool(wins[i + 1])
        run.env_step(world_name, ACTION_MAP[action], frames=[frames[i + 1]],
                     state="WIN" if won else "NOT_FINISHED",
                     levels_completed=1 if won else 0,
                     http=dict(offline_http))

    end = {"outcome": outcome, "steps": len(actions) + 1, "model_calls": 0}
    end.update(extra_end or {})
    run.run_end(**end)

    records = ledger.read()
    return {
        "path": path,
        "records": len(records),
        "format": "LEDGER_FORMAT v1.0",
        "arm": ARM,
        "run_id": run_id,
        "model_calls": 0,
        "api_calls": 0,
        "network_calls": 0,
    }
