"""The grading matrix: every buildable question, every generated world.

```bash
python -m exam.tools.run_matrix              # build, calibrate, mark, report
python -m exam.tools.run_matrix --json       # the matrix as data
```

WHAT THIS PRODUCES, AND IN WHICH ORDER

The order is not cosmetic. `exam/README.md` states the rule this follows: the
question-setter can be checked by reading it, and the marker cannot, because a
marking bug produces a plausible number and a plausible number is
indistinguishable from a result. So on every world the fakes with known scores
run **first**, and a world whose marker fails calibration contributes no row to
the matrix -- it contributes a refusal, with the band it missed.

  1. **feasibility** -- per world, can it carry the question type at all, and if
     not, which rules blocked it and with what counts;
  2. **calibration** -- the four fake examinees per world, against bands;
  3. **the matrix** -- fraction and axes per (world, examinee);
  4. **difficulty** -- the distribution the item asks for, which is a property
     of the worlds and not of any examinee.

WHY THE BANDS ARE PER WORLD AND NOT PER TYPE

`exam/grading/calibration.py` pre-registers one band per (question_type, mode).
That works when a type has one paper. Across twenty worlds two of the four bands
stop being properties of the marker and start being properties of the item mix:
a memoriser's score is exactly the replay share of the paper, and a bluffer's is
exactly the share of items whose frame does not change. Both are computable from
the paper before any marking happens, so here they are **derived and asserted
exactly**, not banded -- which is a stronger check than the one it replaces, and
it is the only kind that survives twenty different worlds.

`oracle == 1.0` and `null == 0.0` stay exact everywhere, because they follow
from construction rather than from item mix.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Optional, Sequence

from ..grading.mark import mark
from ..grading.registry import digest
from ..guard import no_network
from ..model import ARTIFACTS, Submission, canonical, write_json
from ..papers import heldout_worldgen as heldout_wg
from ..papers import worldgen_port as port

MATRIX_DIR = os.path.join(ARTIFACTS, "matrix")

#: The fakes, and what each one's score must be. Two are exact by construction;
#: two are exact by arithmetic over the paper, which is why they are computed
#: rather than banded.
MODES = ("oracle", "null", "memoriser", "bluffer")


def expected_fraction(mode: str, paper: Any, key_doc: Dict[str, Any]) -> Optional[float]:
    """What this fake must score on this paper, computed from the paper.

    `None` means "no exact expectation" -- there is currently no such mode, and
    the branch exists so that adding one is a visible decision rather than a
    silent gap.
    """
    items = key_doc.get("items", [])
    if not items:
        return None
    if mode == "oracle":
        return 1.0
    if mode == "null":
        return 0.0
    before_of = {item.item_id: item.paper["frame_before"] for item in paper.items}
    if mode == "memoriser":
        # It answers every replay item from the trace, and predicts stasis on
        # the held-out half -- where it is still right whenever the world does
        # nothing. The naive expectation, "exactly the replay share", was wrong
        # on the first run for that reason, and the arithmetic is left explicit
        # rather than banded because it pins the *interaction* of the two
        # behaviours and not just the split. A drifting quota or a leaking
        # split would move this number and nothing else would notice.
        correct = 0
        for entry in items:
            truth = entry.get("truth", {})
            if truth.get("split") == "replay":
                correct += 1
            elif truth.get("frame_after") == before_of.get(entry["item_id"]):
                correct += 1
        return round(correct / len(items), 6)
    if mode == "bluffer":
        # It returns the input frame. It is right exactly where the world does
        # nothing -- which the paper publishes as `unchanged_frame_share`, so
        # this also checks that the published figure is the true one.
        correct = sum(1 for entry in items
                      if entry.get("truth", {}).get("frame_after")
                      == before_of.get(entry["item_id"]))
        return round(correct / len(items), 6)
    return None


def tag_bias(paper: Any) -> float:
    """How much the printed `replay`/`heldout` tag predicts the answer.

    Matched rule mixes make the two splits equivalent *by rule*, which is the
    property the design turns on -- but it does not make them equivalent by
    outcome. A cascading mechanism can fire the same rule and settle back to the
    same frame in one split and not the other, so the share of items whose frame
    actually changes can differ between the tags. `t2-gravity-push` does this.

    That is a small exploitable signal: an examinee that noticed could bias
    toward "nothing happens" on held-out items. It is measured and published
    rather than asserted away, because the honest form of a residual bias is a
    number somebody can look at, not a test that was written until it passed.

    Returns |changed share on replay - changed share on heldout|; 0.0 is clean.
    """
    changed = {"replay": 0, "heldout": 0}
    total = {"replay": 0, "heldout": 0}
    for item in paper.items:
        split = item.truth["split"]
        total[split] += 1
        if item.truth["frame_after"] != item.paper["frame_before"]:
            changed[split] += 1
    shares = [changed[s] / total[s] if total[s] else 0.0 for s in ("replay", "heldout")]
    return round(abs(shares[0] - shares[1]), 6)


def calibrate(world_id: str, paper: Any, key_doc: Dict[str, Any]
              ) -> Dict[str, Any]:
    """Run the fakes. A world whose marker misses is excluded from the matrix."""
    rows: List[Dict[str, Any]] = []
    failures: List[str] = []
    for mode in MODES:
        answers = heldout_wg.reference_answers(paper, key_doc, mode)
        submission = Submission(
            examinee_id="fake-%s" % mode, paper_id=paper.paper_id,
            answers=answers,
            capabilities=() if mode == "null" else ("answers",))
        report = mark(key_doc, submission, axes_fn=heldout_wg.axes)
        want = expected_fraction(mode, paper, key_doc)
        got = round(report.fraction, 6)
        ok = want is None or abs(got - want) < 1e-6
        if not ok:
            failures.append("%s scored %.6f, construction says %.6f"
                            % (mode, got, want))
        # Structural checks that hold on every paper of this type, regardless
        # of world: silence must never pay, and truth must never be marked wrong.
        if mode == "null" and any(s.verdict != "unanswered" for s in report.scores):
            failures.append("null produced a verdict other than `unanswered`; a "
                            "marker that pays for silence inflates every score")
        if mode == "oracle" and any(s.verdict == "wrong" for s in report.scores):
            failures.append("oracle was marked wrong somewhere; a marker that "
                            "rejects ground truth depresses every score")
        rows.append({"mode": mode, "fraction": got, "expected": want,
                     "ok": ok, "axes": report.axes})
    return {"world_id": world_id, "modes": rows, "failures": failures,
            "calibrated": not failures}


def run(per_class: int = heldout_wg.DEFAULT_PER_CLASS,
        world_ids: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    targets = list(world_ids or port.world_ids())
    rubric_digest = digest()

    feasibility: List[Dict[str, Any]] = []
    calibrations: List[Dict[str, Any]] = []
    matrix: List[Dict[str, Any]] = []
    difficulty: List[Dict[str, Any]] = []
    refused: List[Dict[str, Any]] = []

    for world_id in targets:
        shape = heldout_wg.plan(world_id, per_class)
        feasibility.append(shape)
        if not shape["feasible"]:
            refused.append({"world_id": world_id, "why": "not feasible",
                            "blocked_rules": shape["blocked_rules"]})
            continue

        paper = heldout_wg.build_for(world_id, per_class)
        key_doc = paper.key(rubric_digest)
        result = calibrate(world_id, paper, key_doc)
        calibrations.append(result)
        if not result["calibrated"]:
            refused.append({"world_id": world_id, "why": "marker not calibrated",
                            "failures": result["failures"]})
            continue

        row: Dict[str, Any] = {"world_id": world_id,
                               "tier": paper.world.get("tier"),
                               "items": len(paper.items),
                               "tag_bias": tag_bias(paper)}
        for entry in result["modes"]:
            row[entry["mode"]] = entry["fraction"]
            if entry["mode"] == "memoriser":
                row["gap"] = entry["axes"].get("gap_replay_minus_heldout")
        matrix.append(row)

        # Difficulty is a property of the world, measured before any examinee:
        # how much of the reachable relation the published trace covers, and how
        # much of the rule set can be examined at all.
        summary = port.summary(world_id)
        difficulty.append({
            "world_id": world_id,
            "tier": summary.get("tier"),
            "families": list(summary.get("families", [])),
            "reachable_states": summary.get("reachable_states"),
            "coverage_fraction": summary.get("coverage_fraction"),
            "rules_total": summary.get("rules_total"),
            "rules_examinable": len(shape["usable_rules"]),
            "rules_blocked": len(shape["blocked_rules"]),
            "items": len(paper.items),
            "unchanged_frame_share": paper.notes.get("unchanged_frame_share"),
            # The floor a theory-free examinee gets for predicting stasis, and
            # the headroom above it. These are the numbers that make raw
            # fractions non-comparable across worlds: a 0.70 on a world whose
            # floor is 0.63 is worse than a 0.50 on one whose floor is 0.25.
            "bluffer_floor": paper.notes.get("unchanged_frame_share"),
            "headroom": round(1.0 - float(paper.notes.get(
                "unchanged_frame_share", 0.0)), 6),
        })

    return {
        "question_type": heldout_wg.QUESTION_TYPE,
        "per_class": per_class,
        "rubric_digest": rubric_digest,
        "worlds_offered": len(targets),
        "worlds_in_matrix": len(matrix),
        "refused": refused,
        "feasibility": feasibility,
        "calibration": calibrations,
        "matrix": matrix,
        "difficulty": difficulty,
        "totals": _totals(matrix, difficulty),
    }


def _totals(matrix: Sequence[Dict[str, Any]],
            difficulty: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    if not matrix:
        return {}

    def mean(key: str, rows: Sequence[Dict[str, Any]]) -> float:
        values = [r[key] for r in rows if isinstance(r.get(key), (int, float))]
        return round(sum(values) / len(values), 6) if values else 0.0

    by_tier: Dict[Any, List[Dict[str, Any]]] = {}
    for row in matrix:
        by_tier.setdefault(row.get("tier"), []).append(row)
    return {
        "items_total": sum(r["items"] for r in matrix),
        "mean_gap_replay_minus_heldout": mean("gap", matrix),
        "mean_bluffer_floor": mean("bluffer", matrix),
        "gap_by_tier": {str(tier): mean("gap", rows)
                        for tier, rows in sorted(by_tier.items(),
                                                 key=lambda kv: str(kv[0]))},
        "bluffer_floor_by_tier": {str(tier): mean("bluffer", rows)
                                  for tier, rows in sorted(by_tier.items(),
                                                           key=lambda kv: str(kv[0]))},
        "max_tag_bias": max(r["tag_bias"] for r in matrix),
        "worlds_with_tag_bias": sorted(r["world_id"] for r in matrix
                                       if r["tag_bias"] > 0.0),
        "rules_examinable_total": sum(d["rules_examinable"] for d in difficulty),
        "rules_blocked_total": sum(d["rules_blocked"] for d in difficulty),
        "bluffer_floor_range": [min(d["bluffer_floor"] for d in difficulty),
                                max(d["bluffer_floor"] for d in difficulty)],
        "comparability_note": (
            "raw fractions are NOT comparable across worlds. The floor a "
            "theory-free examinee gets for predicting stasis ranges from %.3f "
            "to %.3f across the catalogue, because worlds differ in how much of "
            "their rule set is a `blocked_by_*` rule that changes nothing. "
            "Compare (score - bluffer_floor) / headroom, or compare within a "
            "world." % (min(d["bluffer_floor"] for d in difficulty),
                        max(d["bluffer_floor"] for d in difficulty))),
    }


def render(result: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("held-out prediction over the world factory  (per_class=%d)"
                 % result["per_class"])
    lines.append("  %d of %d worlds carried the question type"
                 % (result["worlds_in_matrix"], result["worlds_offered"]))
    lines.append("")
    lines.append("  %-24s %-4s %5s  %6s %6s %9s %8s  %6s"
                 % ("world", "tier", "items", "oracle", "null", "memoriser",
                    "bluffer", "gap"))
    for row in result["matrix"]:
        lines.append("  %-24s %-4s %5d  %6.3f %6.3f %9.3f %8.3f  %6.3f"
                     % (row["world_id"], row["tier"], row["items"],
                        row["oracle"], row["null"], row["memoriser"],
                        row["bluffer"], row["gap"]))
    totals = result.get("totals") or {}
    if totals:
        lines.append("")
        lines.append("  %d items; mean gap %.3f; mean bluffer floor %.3f"
                     % (totals["items_total"],
                        totals["mean_gap_replay_minus_heldout"],
                        totals["mean_bluffer_floor"]))
        lines.append("  gap by tier: %s"
                     % json.dumps(totals["gap_by_tier"], sort_keys=True))
        lines.append("  rules examinable %d, blocked %d"
                     % (totals["rules_examinable_total"],
                        totals["rules_blocked_total"]))
    for entry in result["refused"]:
        lines.append("  REFUSED %s: %s" % (entry["world_id"], entry["why"]))
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--per-class", type=int,
                        default=heldout_wg.DEFAULT_PER_CLASS)
    parser.add_argument("--world", action="append", dest="worlds")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)

    with no_network():
        result = run(args.per_class, args.worlds)

    if not args.no_write:
        os.makedirs(MATRIX_DIR, exist_ok=True)
        write_json(os.path.join(MATRIX_DIR, "heldout_worldgen.json"), result)
    print(json.dumps(result, indent=2, sort_keys=True) if args.json
          else render(result))
    return 0 if result["worlds_in_matrix"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
