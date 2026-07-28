"""Read-only bridge to the two upstream code bases the QC harness grades against.

`worldgen` may not modify `cold-start-a0` (it belongs to the theory-compiler
track) or `engine-rig`.  It may *import* them, and the QC gate in
`monitor/prompts/C1-worldgen.md` says so explicitly — "跑 cold-start-a0 的流水线
（只读 import）".  This module is the single place that arranges the import, so
that every other file in `worldgen/qc/` can be read without wondering what is on
`sys.path`.

Nothing here writes to either upstream tree.  The one thing the harness does
write near them is a candidates stream, and that goes to
`worldgen/out/qc/<world>/`, never to `cold-start-a0/artifacts/`.
"""

import os
import sys
from typing import Any

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
COLD_START_A0 = os.path.join(REPO, "cold-start-a0")
ENGINE_RIG = os.path.join(REPO, "engine-rig")


def _ensure_path() -> None:
    # engine-rig first: cold-start-a0's own modules import `engines`/`common`
    # from it, and its `_bootstrap` does the same thing.  Appending rather than
    # inserting at 0 would let a stale cwd shadow either root.
    for path in (COLD_START_A0, ENGINE_RIG):
        if not os.path.isdir(path):
            raise RuntimeError(
                "QC needs %s on disk; it is an upstream track, not vendored here" % path
            )
        if path not in sys.path:
            sys.path.insert(0, path)


_ensure_path()

# Deterministic ids and a fixed clock, exactly as cold-start-a0's own driver sets
# them (`run_all.py`).  Without these the candidate ids carry a wall clock and no
# artefact this harness writes could be byte-reproducible.
os.environ.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
os.environ.setdefault("THEORIA_FIXED_TIME", "2026-07-28T00:00:00Z")

from pipeline import atoms_a0, engines_stage, multi_miner, segment_operators  # noqa: E402
from pipeline.board import Board, extract_board, object_layer  # noqa: E402

__all__ = [
    "REPO", "COLD_START_A0", "ENGINE_RIG",
    "atoms_a0", "engines_stage", "multi_miner", "segment_operators",
    "Board", "extract_board", "object_layer",
]
