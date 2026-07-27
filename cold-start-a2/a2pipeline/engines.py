"""M2 — run the engines over both traces, and record what each one supports.

The stage itself is A0's (`cold-start-a0/pipeline/engines_stage.py`, imported,
never edited): board extraction, `mdl_segmenter`, the multi-track CEGIS miner,
`zero_space`, `probe_frontier`.  A2 adds no engine and changes no engine.  What
A2 adds is that it runs the identical stage **twice**, on the sweep and on its
own prefix, and diffs the proposals:

    raw_trace.jsonl      -> candidates.jsonl          (the full sweep)
    history_trace.jsonl  -> candidates_history.jsonl  (the play record)

The diff is the isomorphism argument in executable form.  If the history's run
proposes no rule whose effect is a `jumped`, then deleting `teleport_down` from
the manual is not a mutilation invented for the demo — it is exactly the manual
the evidence supports.  §1.3's "缺的那条传送规则从未触发，不欠任何一帧" stops
being a quotation and becomes a number in `engines_diff.json`.

Nothing here adjudicates.  Adjudication is M3 and it is done by hand, in
`THEORIZE_LOG.md`.
"""

import json
import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import _bootstrap  # noqa: F401,E402

from pipeline.engines_stage import run_stage  # noqa: E402  (cold-start-a0, read-only)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS = os.path.join(ROOT, "artifacts")

RUNS = (
    ("", "raw_trace.jsonl", "the full sweep, teleport included"),
    ("_history", "history_trace.jsonl", "the play record, cut at the teleport"),
)

# Run again after M8, on the evidence the probes grew.  This is the loop
# actually closing: if the miner now proposes a jump from `probed_trace.jsonl`,
# then `theory_repaired.dsl` is re-derivable from the evidence rather than
# remembered from the control manual.
PROBED = ("_probed", "probed_trace.jsonl", "the play record plus the probes")


def _rules_with_jump(candidates_path: str) -> List[Dict[str, object]]:
    """Rule proposals whose effect moves the mover further than one cell.

    Read off the proposal's own effect payload rather than off its name, so a
    miner that called the rule something else would still be counted.
    """
    out = []
    with open(candidates_path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row["kind"] != "rule_hypothesis":
                continue
            effect = row["payload"].get("effect") or {}
            if effect.get("type") != "move":
                continue
            if "dy" not in effect or "dx" not in effect:
                continue                       # the ?dir template, not a ground move
            if abs(int(effect["dy"])) + abs(int(effect["dx"])) > 1:
                out.append({"name": row["payload"].get("name"), "effect": effect,
                            "guard": sorted(row["payload"].get("guard") or []),
                            "coverage": row["evidence"]["coverage"],
                            "transitions": row["evidence"]["transitions"]})
    return out


def main() -> int:
    os.environ.setdefault("THEORIA_DETERMINISTIC_IDS", "1")
    os.environ.setdefault("THEORIA_FIXED_TIME", "2026-07-28T00:00:00Z")

    probed = "--probed" in sys.argv[1:]
    runs = (PROBED,) if probed else RUNS
    diff_path = os.path.join(ARTIFACTS,
                             "engines_diff_probed.json" if probed
                             else "engines_diff.json")

    diff: Dict[str, object] = {}
    for suffix, trace, note in runs:
        out = os.path.join(ARTIFACTS, "candidates%s.jsonl" % suffix)
        if os.path.exists(out):
            os.remove(out)           # append-only within a run, not across runs
        report = run_stage(
            os.path.join(ARTIFACTS, trace),
            out,
            os.path.join(ARTIFACTS, "engines_report%s.json" % suffix),
        )
        jumps = _rules_with_jump(out)
        diff["candidates%s.jsonl" % suffix] = {
            "trace": trace,
            "note": note,
            "frames": report["frames"],
            "transitions": report["transitions"],
            "tracks": [t["color"] for t in report["segmentation"]["tracks"]],
            "rules_proposed": [r["name"] for r in report["mining"]["rules"]],
            "rules_with_a_jump_effect": jumps,
            "explains_every_transition": report["mining"]["explains_every_transition"],
            "mutually_exclusive": report["mining"]["mutually_exclusive"],
        }
        print("[%s] %d frames, %d rules, %d with a jump effect"
              % (trace, report["frames"], len(report["mining"]["rules"]), len(jumps)))
        for rule in report["mining"]["rules"]:
            print("    %-24s %-6s %-30s %-8s %s"
                  % (rule["name"], rule["action"], json.dumps(rule["effect"]),
                     rule["coverage"], " AND ".join(rule["guard"])))

    if probed:
        grown = diff["candidates_probed.jsonl"]
        diff["verdict"] = {
            "probed_evidence_proposes_a_jump":
                bool(grown["rules_with_a_jump_effect"]),
            "reading": "the miner proposes the teleport again from the grown "
                       "evidence, so theory_repaired.dsl is re-derivable from "
                       "probed_trace.jsonl and is not a rule remembered from the "
                       "control manual",
        }
    else:
        sweep = diff["candidates.jsonl"]
        history = diff["candidates_history.jsonl"]
        diff["verdict"] = {
            "sweep_proposes_a_jump": bool(sweep["rules_with_a_jump_effect"]),
            "history_proposes_a_jump": bool(history["rules_with_a_jump_effect"]),
            "reading": "the teleport is proposed from the sweep and not from the "
                       "history; the hole in theory_holed.dsl is therefore the "
                       "manual the play record supports, not a rule removed to "
                       "order",
        }
    with open(diff_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(diff, indent=2, sort_keys=True) + "\n")
    print("verdict:", json.dumps(diff["verdict"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
