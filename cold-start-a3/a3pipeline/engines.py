"""M2/M3 — segmentation, rule mining, conservation laws, probe design.

A3 writes no engine.  This module is a driver: it points
`cold-start-a0`'s `pipeline.engines_stage.run_stage` at an A3 trace and an A3
output path, and that stage in turn drives `engine-rig`'s `mdl_segmenter`,
the multi-track CEGIS miner, `zero_space` and `probe_frontier`.

Two arms call it and one deliberately does not:

  * `l1_sweep.jsonl`  -> `candidates_l1.jsonl`      (the L1 cold start)
  * `l2_sweep.jsonl`  -> `candidates_l2_scratch.jsonl` (the control arm)
  * the transfer arm calls nothing here at all.  Not "calls it and ignores the
    result" — the arm's driver does not import this module, and
    `tests/test_sealing.py` checks that, because "no rules were re-mined" is
    the claim under test and a promise is not evidence.

`emit` is append-only by contract (`engine-rig/common/candidates.py`), which
holds *within* a run and not across them, so the target is deleted first or the
stream grows a duplicate row per run and stops being byte-reproducible.  A2
learned this the same way and its note is copied here rather than paraphrased.
"""

import json
import os
import sys
from typing import Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from pipeline.engines_stage import run_stage  # noqa: E402  (cold-start-a0, read-only)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, "artifacts")

FIXED_TIME = "2026-07-28T00:00:00Z"

RUNS = (
    ("l1", "l1_sweep.jsonl",
     "the level-1 cold start: its entire evidence"),
    ("l2_scratch", "l2_sweep.jsonl",
     "the from-scratch control arm on level 2, carrying nothing"),
)


def run(tag: str, trace_name: str, note: str,
        meter=None) -> Dict[str, object]:
    trace = os.path.join(ARTIFACTS, trace_name)
    out = os.path.join(ARTIFACTS, "candidates_%s.jsonl" % tag)
    report_path = os.path.join(ARTIFACTS, "engines_report_%s.json" % tag)

    if os.path.exists(out):
        os.remove(out)      # append-only within a run, not across runs

    report = run_stage(trace, out, report_path, timestamp=FIXED_TIME)
    report["note"] = note
    with open(report_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")

    if meter is not None:
        meter.charge("engine_stages", 1, "run_stage on %s" % trace_name)

    return report


def brief(report: Dict[str, object]) -> str:
    seg = report["segmentation"]
    mining = report["mining"]
    return (
        "%d frames, %d transitions | tracks %d (operator %s) | rules %d, "
        "exclusive=%s, total=%s | zero_space laws %d | probes %d"
        % (report["frames"], report["transitions"], len(seg["tracks"]),
           seg["operator"], len(mining["rules"]), mining["mutually_exclusive"],
           mining["explains_every_transition"],
           len(report["zero_space"]["global_laws"]), len(report["probes"]))
    )


def main() -> int:
    os.environ.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
    os.environ.setdefault("THEORIA_FIXED_TIME", FIXED_TIME)
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for tag, trace_name, note in RUNS:
        if only and tag != only:
            continue
        report = run(tag, trace_name, note)
        print("%-12s %s" % (tag, brief(report)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
