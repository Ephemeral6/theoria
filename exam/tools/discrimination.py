"""Per-item discrimination: which questions separate anybody, and which are free.

```bash
python -m exam.tools.discrimination                    # all worlds, write artefact
python -m exam.tools.discrimination --world t1-push-open --no-write
python -m exam.tools.discrimination --per-world-dir <dir>   # one JSON per world
```

WHY THIS EXISTS SEPARATELY FROM `run_matrix`

`run_matrix` reports, per world, what each fake examinee *scored*. A fraction is
an average, and an average hides the thing a question-setter most needs to know:
**a question every examinee gets right measures nothing.** A paper can post a
respectable mean gap while a majority of its items are unanswerable-by-nobody --
free marks handed to an examinee with no theory at all. The published
`bluffer_floor` already says how *many* such marks exist per world; it does not
say *which* items they are, which rules produce them, or whether the residue that
remains is large enough to rank anyone.

WHAT COUNTS AS ZERO DISCRIMINATION, AND WHY `null` IS NOT A VOTER

Three of the four calibration fakes are informative here:

* `oracle`    -- answers from ground truth. Must be correct on every item.
* `memoriser` -- replays the published trace, predicts stasis elsewhere.
* `bluffer`   -- returns the input frame on every item, holding no theory at all.

`null` submits nothing, so it is `unanswered` on every item by construction. It
cannot distinguish two items any more than a blank page can, and including it
would make every item look as though it discriminated *something*. It stays in
the calibration (silence must never pay) and out of this count.

An item is **zero-discrimination** when those three agree -- when the item's
outcome is the same regardless of which of them sat the paper:

* `free`      -- all three correct. The bluffer already has it. Any examinee who
                 writes down the frame in front of them scores this mark, so it
                 ranks nobody. This is the dominant class and it is the finding.
* `dead`      -- all three wrong, *oracle included*. Nobody can score it, so it
                 also ranks nobody -- but an item the ground truth itself fails
                 is a **marker defect**, not a difficulty. Reported separately
                 and loudly for that reason; `run_matrix`'s calibration would
                 already have refused the world, so a non-zero count here means
                 the two instruments disagree and one of them is broken.

And it discriminates when they do not agree:

* `memorised` -- memoriser and oracle correct, bluffer wrong. Separates an
                 examinee who read the trace from one who did not. Weak: it
                 rewards recall, not theory.
* `theory`    -- oracle alone correct. The only class that asks for a world
                 model. This is the count that should be quoted as the paper's
                 real size, and on most worlds it is far below the item count.

`free + dead` is the zero-discrimination share. `theory` is the informative
residue. Both are per world, per rule and per split, because a paper can be
healthy in aggregate and degenerate on the one rule somebody cares about.

WHAT THIS IS NOT

It is not a claim about human or model examinees; three synthetic answer
strategies are not a population. An item this file calls `theory` is one that
those three strategies do not settle -- a fourth strategy nobody has written
could settle it for free, and the taxonomy would not notice. That is the same
limit `exam/grading/selftest.py` records for its own fault list: a matrix can
say the failures it enumerates are caught, and nothing about the ones nobody
thought to write down.

WHAT IT TURNED OUT TO BE, WHICH IS LESS THAN THE ABOVE PROMISES

That caveat was written as a hypothetical and is not one. Twenty independent
examiners, one per world, each tried to build a cheap examinee that beats its
world's paper without a world model. Most of them succeeded within a session, and
a single eight-line grid prior -- step one cell unless the target is a wall --
scores **1.000 on twelve of the twenty worlds** and takes **109 of the 139
frame-changing items** across the catalogue. Measured against that fourth
strategy, the informative residue this file reports as 69 items falls to **16**,
and to **zero on fourteen of the twenty worlds**.

That prior is not theory-free either, and the honest version of the number says
so: strip `legend["agent"]` from the sheet it reads and it scores **0.4110**,
which is the bluffer floor to four figures. Every point it earns above the floor
is bought with the sheet's naming of the agent and the wall -- an object ontology,
handed over. So the residue above is measured against *legend plus eight lines*,
not against a reader who brought nothing.

Two exact identities, both checked over all 236 items rather than argued:

* **`class` is a function of `(split, frame_changes)`, with zero violations.**
  Given how the voters are defined -- the memoriser replays the trace and
  otherwise predicts stasis, the bluffer always predicts stasis -- an item is
  `free` iff its frame does not change, `memorised` iff it changes and is in the
  trace, and `theory` iff it changes and is held out. So this file does not
  measure difficulty. It measures "held out, and something moved", which is two
  fields the paper already carries, one of them printed on the sheet.
* **A rule whose consequent is "nothing changes" is barren a priori**, in every
  world, at every quota: its ground truth *is* the bluffer's answer, so no
  sampling can make it discriminate. The catalogue has **seven** such rules over
  the full reachable relation -- the four this file reports at `per_class=2`
  (`blocked_by_wall`, `blocked_by_block`, `blocked_by_door`, `latch_already_set`)
  plus `blocked_by_lock`, `blocked_by_collapsed` and
  `blocked_toggle_would_shut_door`. **Which of them reach a paper is a property
  of the quota, not of the rule table**: the barren set is five at `per_class=1`,
  four at 2, two at 3 and one at 4. Barrenness is derivable without running
  anything; membership of the reported set is not, and an earlier draft of this
  docstring conflated the two.

  A gap this leaves open: barrenness is computed **by rule tag**, so a stasis
  transition filed under a non-stasis rule is invisible here. `up_is_inert` on
  `t2-gravity-push` is exactly that -- a cascade rule whose transitions carry the
  `walk` tag, which is why `walk` is the one rule in the catalogue producing both
  changing and non-changing items and is never reported as partly barren.

So the honest description is: **this is a consistency check that earns its keep
through `dead` and `anomaly`, plus a restatement of the bluffer floor per rule and
per split.** `theory` should be read as an upper bound on the informative residue,
never as its size. The fix is a fourth voter implementing the grid prior, which
would collapse `theory` to something worth quoting; it is left undone here rather
than done badly, because a voter that is itself a world model would need its own
argument for why it is the *right* baseline, and that argument is not this run's.

`exam/tests/test_discrimination.py` pins the first identity with a test that is
designed to **fail** when a genuinely independent voter is added, so the fix
cannot land quietly.
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, List, Optional, Sequence

from ..grading.mark import mark
from ..grading.registry import digest
from ..guard import no_network
from ..model import ARTIFACTS, Submission, write_json
from ..papers import heldout_worldgen as heldout_wg
from ..papers import worldgen_port as port

MATRIX_DIR = os.path.join(ARTIFACTS, "matrix")

#: The voters. `null` is deliberately absent -- see the module docstring.
VOTERS = ("oracle", "memoriser", "bluffer")

#: The classes, ordered from least to most informative. `dead` is not a
#: difficulty tier; it is a defect, and it sorts first so it cannot be skimmed
#: past in a rendered table.
CLASSES = ("dead", "free", "memorised", "theory")


def _classify(correct: Dict[str, bool]) -> str:
    """One item's class from the three voters' outcomes.

    Only four of the eight possible outcome triples are reachable if the
    strategies behave as documented -- a bluffer that is right where the oracle
    is wrong, for instance, would mean the marker accepts an answer the ground
    truth does not produce. Those are not silently folded into a neighbouring
    class: they come back as `anomaly:<triple>` so that an impossible
    combination is visible as itself rather than as a plausible number.
    """
    o, m, b = correct["oracle"], correct["memoriser"], correct["bluffer"]
    if o and m and b:
        return "free"
    if not o and not m and not b:
        return "dead"
    if o and m and not b:
        return "memorised"
    if o and not m and not b:
        return "theory"
    return "anomaly:oracle=%s,memoriser=%s,bluffer=%s" % (o, m, b)


def profile_world(world_id: str, per_class: int = heldout_wg.DEFAULT_PER_CLASS
                  ) -> Dict[str, Any]:
    """Every item of one world, with the class each falls into."""
    shape = heldout_wg.plan(world_id, per_class)
    if not shape["feasible"]:
        return {"world_id": world_id, "feasible": False,
                "blocked_rules": shape["blocked_rules"], "items": []}

    paper = heldout_wg.build_for(world_id, per_class)
    key_doc = paper.key(digest())

    verdicts: Dict[str, Dict[str, str]] = {}
    for mode in VOTERS:
        answers = heldout_wg.reference_answers(paper, key_doc, mode)
        report = mark(key_doc, Submission(
            examinee_id="fake-%s" % mode, paper_id=paper.paper_id,
            answers=answers, capabilities=("answers",)),
            axes_fn=heldout_wg.axes)
        for score in report.scores:
            verdicts.setdefault(score.item_id, {})[mode] = score.verdict

    truth_of = {item.item_id: item.truth for item in paper.items}
    before_of = {item.item_id: item.paper["frame_before"] for item in paper.items}

    items: List[Dict[str, Any]] = []
    for item_id in sorted(verdicts):
        truth = truth_of[item_id]
        correct = {mode: verdicts[item_id][mode] == "correct" for mode in VOTERS}
        items.append({
            "item_id": item_id,
            "rule": truth.get("rule"),
            "split": truth.get("split"),
            "frame_changes": truth.get("frame_after") != before_of[item_id],
            "verdicts": dict(verdicts[item_id]),
            "class": _classify(correct),
        })

    return {"world_id": world_id, "feasible": True,
            "tier": paper.world.get("tier"),
            "per_class": per_class,
            "paper_id": paper.paper_id,
            "rubric_digest": key_doc.get("rubric_digest"),
            "n_items": len(items),
            "items": items,
            "by_class": _counts(items, "class"),
            "by_rule": _cross(items, "rule"),
            "by_split": _cross(items, "split"),
            "summary": _world_summary(items)}


def _counts(items: Sequence[Dict[str, Any]], field: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for item in items:
        out[str(item[field])] = out.get(str(item[field]), 0) + 1
    return dict(sorted(out.items()))


def _cross(items: Sequence[Dict[str, Any]], field: str) -> Dict[str, Dict[str, int]]:
    out: Dict[str, Dict[str, int]] = {}
    for item in items:
        bucket = out.setdefault(str(item[field]), {})
        bucket[item["class"]] = bucket.get(item["class"], 0) + 1
    return {k: dict(sorted(v.items())) for k, v in sorted(out.items())}


def _world_summary(items: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    n = len(items)
    counts = _counts(items, "class")
    free = counts.get("free", 0)
    dead = counts.get("dead", 0)
    theory = counts.get("theory", 0)
    memorised = counts.get("memorised", 0)
    anomalies = sorted(k for k in counts if k.startswith("anomaly:"))
    zero = free + dead
    # A rule is dead weight when not one of its items separates anybody. It is
    # reported by name because "this world is 60% free" is actionable only if
    # you know which mechanism to fix.
    by_rule = _cross(items, "rule")
    barren = sorted(rule for rule, klasses in by_rule.items()
                    if not (klasses.get("theory", 0) or klasses.get("memorised", 0)))
    return {
        "n_items": n,
        "free": free, "dead": dead, "memorised": memorised, "theory": theory,
        "anomalies": anomalies,
        "zero_discrimination": zero,
        "zero_discrimination_share": round(zero / n, 6) if n else 0.0,
        "theory_items": theory,
        "theory_share": round(theory / n, 6) if n else 0.0,
        # The number a reader should carry instead of the item count: how many
        # questions on this paper actually require a world model.
        "effective_size": theory,
        "barren_rules": barren,
    }


def run(per_class: int = heldout_wg.DEFAULT_PER_CLASS,
        world_ids: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    targets = list(world_ids or port.world_ids())
    worlds = [profile_world(world_id, per_class) for world_id in targets]
    carried = [w for w in worlds if w["feasible"]]
    return {
        "question_type": heldout_wg.QUESTION_TYPE,
        "per_class": per_class,
        "rubric_digest": digest(),
        "worlds_offered": len(targets),
        "worlds_profiled": len(carried),
        "worlds": worlds,
        "totals": _totals(carried),
    }


def _totals(worlds: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    if not worlds:
        return {}
    items = [item for w in worlds for item in w["items"]]
    n = len(items)
    counts = _counts(items, "class")
    free = counts.get("free", 0)
    dead = counts.get("dead", 0)
    theory = counts.get("theory", 0)
    memorised = counts.get("memorised", 0)
    anomalies = sorted(k for k in counts if k.startswith("anomaly:"))
    shares = [(w["world_id"], w["summary"]["theory_share"]) for w in worlds]
    zero_worlds = sorted(world_id for world_id, share in shares if share == 0.0)
    return {
        "items_total": n,
        "free": free, "dead": dead, "memorised": memorised, "theory": theory,
        "anomalies": anomalies,
        "zero_discrimination_total": free + dead,
        "zero_discrimination_share": round((free + dead) / n, 6) if n else 0.0,
        "theory_share": round(theory / n, 6) if n else 0.0,
        "worlds_with_no_theory_item": zero_worlds,
        "theory_share_range": [min(s for _, s in shares),
                               max(s for _, s in shares)],
        "least_informative_worlds": [w for w, _ in sorted(shares,
                                                          key=lambda kv: kv[1])[:5]],
        "barren_rules_total": sorted({rule for w in worlds
                                      for rule in w["summary"]["barren_rules"]}),
        "reading_note": (
            "`items` is not the size of the paper. %d of %d items are settled "
            "identically by an oracle, a memoriser and a theory-free bluffer, "
            "so they rank nobody; %d ask for a world model. Quote the second "
            "number." % (free + dead, n, theory)),
    }


def render(result: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("per-item discrimination over the world factory  (per_class=%d)"
                 % result["per_class"])
    lines.append("  %d of %d worlds profiled"
                 % (result["worlds_profiled"], result["worlds_offered"]))
    lines.append("")
    lines.append("  %-24s %-4s %5s  %5s %5s %10s %7s  %8s"
                 % ("world", "tier", "items", "dead", "free", "memorised",
                    "theory", "theory%"))
    for world in result["worlds"]:
        if not world["feasible"]:
            lines.append("  %-24s  NOT FEASIBLE" % world["world_id"])
            continue
        s = world["summary"]
        lines.append("  %-24s %-4s %5d  %5d %5d %10d %7d  %7.3f"
                     % (world["world_id"], world["tier"], s["n_items"],
                        s["dead"], s["free"], s["memorised"], s["theory"],
                        s["theory_share"]))
    totals = result.get("totals") or {}
    if totals:
        lines.append("")
        lines.append("  %d items: %d free, %d dead, %d memorised, %d theory"
                     % (totals["items_total"], totals["free"], totals["dead"],
                        totals["memorised"], totals["theory"]))
        lines.append("  zero discrimination %.3f of all items"
                     % totals["zero_discrimination_share"])
        if totals["worlds_with_no_theory_item"]:
            lines.append("  WORLDS THAT RANK NOBODY: %s"
                         % ", ".join(totals["worlds_with_no_theory_item"]))
        if totals["anomalies"]:
            lines.append("  ANOMALIES: %s" % ", ".join(totals["anomalies"]))
        if totals["barren_rules_total"]:
            # "at this quota", not "anywhere": the catalogue has seven
            # 100%-stasis rules and which of them reach a paper depends on
            # per_class (five at 1, four at 2, two at 3, one at 4).
            lines.append("  rules producing no informative item on any world "
                         "at per_class=%d: %s"
                         % (result["per_class"],
                            ", ".join(totals["barren_rules_total"])))
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--per-class", type=int,
                        default=heldout_wg.DEFAULT_PER_CLASS)
    parser.add_argument("--world", action="append", dest="worlds")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--per-world-dir", default=None,
                        help="also write one JSON per world into this directory")
    args = parser.parse_args(argv)

    with no_network():
        result = run(args.per_class, args.worlds)

    if not args.no_write:
        os.makedirs(MATRIX_DIR, exist_ok=True)
        write_json(os.path.join(MATRIX_DIR, "discrimination_worldgen.json"), result)
    if args.per_world_dir:
        os.makedirs(args.per_world_dir, exist_ok=True)
        for world in result["worlds"]:
            write_json(os.path.join(args.per_world_dir,
                                    "%s.json" % world["world_id"]), world)
    print(json.dumps(result, indent=2, sort_keys=True) if args.json
          else render(result))
    # A world that ranks nobody is a result, not an error. An anomaly and a
    # `dead` item are both errors: the first means two instruments that must
    # agree do not, the second means the marker rejected its own ground truth.
    # `dead` was missing from this condition in the first version, which made
    # the docstring's "reported loudly" a promise the CLI did not keep -- a gate
    # that says a thing is a defect and then exits clean is not a gate.
    totals = result.get("totals", {})
    return 1 if (totals.get("anomalies") or totals.get("dead")
                 or not result["worlds_profiled"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
