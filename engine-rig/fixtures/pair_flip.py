"""Fixture B - the Pair-Flip world.

Eight cells in a row, each one permanently either Red or Blue (never empty).
`flip_pair(i, j)` inverts both cells at once; (i, j) is drawn from a fixed set of
adjacent pairs.

Ground truth: (#Red) mod 2 is invariant.  Each flip either turns RR into BB
(-2 red), BB into RR (+2 red), or swaps an RB/BR pair (0 red) -- every case
preserves parity.  This is the invariant zero_space has to recover on GF(2).

The first 7 actions walk through every adjacent pair once, so the observed
difference vectors span the whole even-weight subspace and the recovered null
space is exactly the span of the all-ones vector.  Without that guarantee a
random draw could miss a pair and yield a larger (still correct, but weaker)
invariant space -- see DECISIONS.md D-003.

Serialisation: one JSON object per line,
`{"state": ["R","B",...], "action": {"op":"flip_pair","i":<int>,"j":<int>}}`,
final line has `"action": null`.
"""

import os
from typing import Dict, List, Optional, Tuple

from common.jsonio import write_json, write_jsonl
from common.rng import SplitMix64

N_CELLS = 8
COLORS = ("R", "B")
PAIRS: Tuple[Tuple[int, int], ...] = tuple((i, i + 1) for i in range(N_CELLS - 1))
INITIAL: Tuple[str, ...] = ("R", "B", "R", "R", "B", "B", "R", "B")
SEED = 0x5EED5
N_ACTIONS = 40

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TRAJ_PATH = os.path.join(DATA_DIR, "pair_flip.jsonl")
TRUTH_PATH = os.path.join(DATA_DIR, "pair_flip_truth.json")


def flip(color: str) -> str:
    return "B" if color == "R" else "R"


def step(state: Tuple[str, ...], pair: Tuple[int, int]) -> Tuple[str, ...]:
    i, j = pair
    out = list(state)
    out[i] = flip(out[i])
    out[j] = flip(out[j])
    return tuple(out)


def red_count(state: Tuple[str, ...]) -> int:
    return sum(1 for c in state if c == "R")


def build_actions() -> List[Tuple[int, int]]:
    rng = SplitMix64(SEED)
    actions = list(PAIRS)                       # every pair witnessed once
    while len(actions) < N_ACTIONS:
        actions.append(PAIRS[rng.below(len(PAIRS))])
    return actions[:N_ACTIONS]


def generate() -> Dict[str, object]:
    actions = build_actions()
    state = INITIAL
    states = [state]
    for pair in actions:
        state = step(state, pair)
        states.append(state)

    parities = {red_count(s) % 2 for s in states}
    if len(parities) != 1:
        raise AssertionError("red parity is not invariant: %r" % (parities,))
    if set(actions) != set(PAIRS):
        raise AssertionError("not every adjacent pair is witnessed")

    rows = []
    for t, s in enumerate(states):
        action: Optional[Dict[str, object]] = None
        if t < len(actions):
            i, j = actions[t]
            action = {"op": "flip_pair", "i": i, "j": j}
        rows.append({"state": list(s), "action": action})

    truth = {
        "n_cells": N_CELLS,
        "colors": list(COLORS),
        "pairs": [list(p) for p in PAIRS],
        "initial": list(INITIAL),
        "seed": SEED,
        "n_actions": len(actions),
        "actions": [list(a) for a in actions],
        "red_counts": [red_count(s) for s in states],
        "red_parity": red_count(INITIAL) % 2,
        "invariant": "(#Red) mod 2 = %d" % (red_count(INITIAL) % 2),
    }
    return {"rows": rows, "truth": truth}


def write(traj_path: str = TRAJ_PATH, truth_path: str = TRUTH_PATH) -> Dict[str, object]:
    out = generate()
    write_jsonl(traj_path, out["rows"])          # type: ignore[arg-type]
    write_json(truth_path, out["truth"])
    return out


if __name__ == "__main__":  # pragma: no cover
    result = write()
    print("pair_flip: %d states -> %s" % (len(result["rows"]), TRAJ_PATH))
