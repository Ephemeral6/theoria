"""题型 1, set in a generated world — held-out prediction, twenty times over.

`exam/papers/heldout.py` sets this question in A0. This module sets the same
question in any world the factory has built, and the difference is not that
there are more boards: it is that three things the A0 paper had to *construct*
are now *measured*.

  * **The event class.** A0's paper carries a hand-written six-way classifier
    that re-derives each transition and decides which case it looked like. Here
    `GridWorld.explain()` returns the next state and the rule name from one code
    path, so the label and the world cannot disagree. The class of bug A0 could
    only test for is gone.
  * **The evidence set.** A0's paper calls the explorer to regenerate what the
    arm was shown. Here the trace *is* the published artefact — the same file a
    reader gets — so "already seen" is a fact about a file rather than a
    reconstruction that has to stay in step with one.
  * **The quota.** A0 fixes six classes at hand-tuned counts. That number cannot
    survive contact with twenty worlds whose rule sets differ in name, count and
    frequency: `t1-walk-maze` fires two rules, `t2-switch-push` and
    `t3-full-house` fire six. So the quota is **derived per world** from what the
    world can actually support, and a world that cannot support the matched
    quota is refused with its counts rather than shrunk.

THE MATCHED QUOTA IS THE WHOLE DESIGN, AND IT IS WHY WORLDS GET REFUSED

Every item carries a `replay` or `heldout` tag, and the tag is printed on the
sheet. That is only safe if the tag carries no information about the answer —
which requires the two splits to have *identical rule mixes*. If a rule can fill
its replay quota but not its held-out quota, dropping it from one side turns the
tag into a hint, and the paper would be measuring whether an examinee noticed the
hint.

So a rule qualifies only when it has `per_class` transitions inside the published
trace **and** `per_class` outside it. Both halves matter, and the second is A0's
own recorded failure: a rule witnessed exactly once has no second witness to hold
out, which is the A0′ criterion the factory now stamps every world with.

Measured across the catalogue at `per_class=2`, **all twenty worlds qualify**,
with between 2 and 6 usable rules each. That is a fact about the factory, not
about this module: the worlds ship with reversibility stamps precisely so that
rules have re-witnessable transitions.

WHAT IS ON THE SHEET, AND WHAT IS NOT

The sheet is built from `spec.json` and `raw_trace.jsonl` only — the two files
the factory licenses to anyone. `ground_truth.json` is scoring-only and reaches
`Item.truth` alone. There is a test for that, because the split is the only
thing standing between the catalogue and a rigged evaluation, and an exam is
exactly the consumer that could quietly break it.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..guard import assert_synthetic_world
from ..model import ExamError, Item, Paper, canonical, sha256_text
from . import worldgen_port as port

QUESTION_TYPE = "heldout"
RUBRIC_ID = "heldout.frame_exact"

#: Items per rule per split. Two is the smallest number that can distinguish a
#: rule an examinee has learned from one it got right once.
DEFAULT_PER_CLASS = 2

#: Ceiling on items per paper, so that a twenty-world matrix stays runnable.
#: A world with six usable rules produces 24 items at `per_class=2`.
MAX_ITEMS = 96

_SAMPLE_SALT = "v2-heldout-sample"
_ORDER_SALT = "v2-heldout-order"


def paper_id_for(world_id: str) -> str:
    return "v2-heldout-%s" % world_id


# -- candidate enumeration ---------------------------------------------------

def _candidates(world_id: str) -> Tuple[Dict[str, List[Dict[str, Any]]],
                                        Dict[str, List[Dict[str, Any]]]]:
    """Every reachable transition, split by whether the trace published it.

    Enumeration, not sampling: `GridWorld.transitions()` walks the reachable
    relation in a deterministic order, and the choice of which candidates become
    items is a hash under a salt. There is no RNG and no wall clock, so two
    builds produce byte-identical sheets.
    """
    world = port.open_world(world_id)
    index = port.evidence_index(world_id)
    replay: Dict[str, List[Dict[str, Any]]] = {}
    heldout: Dict[str, List[Dict[str, Any]]] = {}

    for state, action, after, rule in world.transitions():
        before_frame = world.render(state)
        after_frame = world.render(after)
        key = port.transition_key(before_frame, action)
        candidate = {
            "before": before_frame,
            "after": after_frame,
            "action": action,
            "rule": rule,
            "key": key,
        }
        bucket = replay if key in index else heldout
        bucket.setdefault(rule, []).append(candidate)
    return replay, heldout


def _pick(pool: Sequence[Dict[str, Any]], count: int) -> List[Dict[str, Any]]:
    """The `count` candidates whose salted hash sorts first. Deterministic."""
    ordered = sorted(pool, key=lambda c: sha256_text(_SAMPLE_SALT + c["key"]))
    return ordered[:count]


def plan(world_id: str, per_class: int = DEFAULT_PER_CLASS) -> Dict[str, Any]:
    """What this world can carry, before anything is built.

    Separate from `build_for` so a matrix driver can ask twenty worlds what they
    support and report the answer, rather than catching twenty exceptions.
    """
    replay, heldout = _candidates(world_id)
    rules = sorted(set(replay) | set(heldout))
    usable = [r for r in rules
              if len(replay.get(r, ())) >= per_class
              and len(heldout.get(r, ())) >= per_class]
    blocked = {
        r: {"in_trace": len(replay.get(r, ())),
            "held_out": len(heldout.get(r, ())),
            "why": ("the trace witnessed it fewer than %d times -- the A0' "
                    "failure mode: no second witness to hold out" % per_class)
            if len(replay.get(r, ())) < per_class else
            "every reachable transition of this rule is already in the trace"}
        for r in rules if r not in usable}
    return {
        "world_id": world_id,
        "per_class": per_class,
        "usable_rules": usable,
        "blocked_rules": dict(sorted(blocked.items())),
        "items": len(usable) * per_class * 2,
        "feasible": len(usable) >= 2,
    }


# -- the paper ---------------------------------------------------------------

def build_for(world_id: str, per_class: int = DEFAULT_PER_CLASS) -> Paper:
    """Deterministic. Two calls produce byte-identical sheets."""
    assert_synthetic_world(world_id)
    shape = plan(world_id, per_class)
    if not shape["feasible"]:
        raise ExamError(
            "%s cannot carry a matched-quota held-out paper at per_class=%d: "
            "usable rules %s, blocked %s. Refusing rather than shrinking a "
            "class -- an unmatched quota turns the replay/heldout tag on the "
            "sheet into a hint about the answer."
            % (world_id, per_class, shape["usable_rules"],
               canonical(shape["blocked_rules"])))
    if shape["items"] > MAX_ITEMS:
        per_class = max(1, MAX_ITEMS // (2 * len(shape["usable_rules"])))
        shape = plan(world_id, per_class)

    world = port.open_world(world_id)
    replay, heldout = _candidates(world_id)
    legend = port.palette(world)
    cells = port.legal_cells(world)

    chosen: List[Tuple[str, Dict[str, Any]]] = []
    for rule in shape["usable_rules"]:
        for split, pool in (("replay", replay), ("heldout", heldout)):
            chosen.extend((split, cand) for cand in _pick(pool[rule], per_class))

    # Presentation order under a salt unrelated to the sampling salt, so neither
    # position nor item_id correlates with the answer.
    chosen.sort(key=lambda pair: sha256_text(_ORDER_SALT + pair[0]
                                             + pair[1]["key"]))

    items: List[Item] = []
    for position, (split, cand) in enumerate(chosen):
        items.append(Item(
            item_id="%s-%03d" % (world_id, position),
            rubric_id=RUBRIC_ID,
            points=1.0,
            paper={
                "frame_before": cand["before"],
                "action": cand["action"],
                "legend": dict(legend),
                "grid": [len(cand["before"]), len(cand["before"][0])],
            },
            truth={
                "frame_after": cand["after"],
                "rule": cand["rule"],
                "split": split,
                # The palette, so the marker knows what a well-formed frame of
                # this world looks like. A0's rubric hardcoded four values and
                # would reject every generated frame as malformed -- which reads
                # on a report as an examinee that cannot format an answer.
                "legal_cells": list(cells),
            },
            leak_probes=(cand["rule"],),
            tags=(split, "rule:%s" % cand["rule"]),
        ))

    unchanged = sum(1 for _, cand in chosen if cand["before"] == cand["after"])
    row = port.summary(world_id)
    return Paper(
        paper_id=paper_id_for(world_id),
        question_type=QUESTION_TYPE,
        instructions=(
            "You are shown a frame and one action. Predict the frame that "
            "follows, as a list of rows of integers. The legend names each "
            "colour. Answer with the grid itself or with "
            "{\"frame_after\": [[...]]}; answer {\"abstain\": true} if you "
            "cannot tell. There is no partial credit: the frame matches cell "
            "for cell or it does not."),
        items=items,
        world={
            "world_id": world_id,
            "tier": row.get("tier"),
            "families": list(row.get("families", [])),
            "grid": row.get("grid"),
            # Deliberately not the rule table, the solvability, or the coverage:
            # those are scoring-only files, and two of them would answer items.
        },
        notes={
            "split_rule": (
                "replay items are transitions whose (rendered frame, action) key "
                "appears in the world's published raw_trace.jsonl; held-out items "
                "are reachable transitions whose key does not. Selection is "
                "enumeration of the reachable relation ordered by sha256 under a "
                "salt; no RNG, no wall clock."),
            "quota": {
                "per_rule_per_split": per_class,
                # Counts, not names. The rule names are the answer vocabulary of
                # the `by_rule` axis, and a sheet that lists them hands the
                # examinee the alphabet it is being asked to discover. The
                # mapping lives in the truth file only -- the same discipline
                # the A0 adaptation paper uses for its variant ids.
                "classes": len(shape["usable_rules"]),
                "matched": True,
                "why": ("identical rule mixes on both sides, so the replay / "
                        "heldout tag printed on the sheet carries no information "
                        "about the answer"),
            },
            "classes_not_examined": len(shape["blocked_rules"]),
            "unchanged_frame_share": round(unchanged / len(items), 6) if items else 0.0,
            "sheet_sources": list(port.OPEN_FILES),
        },
    )


# -- the four fake examinees -------------------------------------------------

def reference_answers(paper: Paper, key_doc: Optional[Dict[str, Any]] = None,
                      mode: str = "oracle") -> Dict[str, Any]:
    """Answers with known scores, for calibrating the marker before it marks.

    `oracle` and `null` are exact by construction and are the two that matter:
    a marker that rejects ground truth depresses every real score, and one that
    pays for silence inflates every one of them.

    `memoriser` and `bluffer` are the diagnostic pair, and on this paper they
    are the same theory told two ways -- which is the point. The memoriser has
    the trace and nothing else: perfect where the answer was published, and
    "nothing happens" everywhere else. The bluffer says "nothing happens"
    everywhere. Their difference **is** `gap_replay_minus_heldout`, so if the
    gap ever came out near zero on a world, the paper would be failing to hold
    anything out.
    """
    if mode == "null":
        return {}

    truth_by_item: Dict[str, Dict[str, Any]] = {}
    if key_doc:
        for entry in key_doc.get("items", []):
            truth_by_item[entry["item_id"]] = entry.get("truth", {})

    answers: Dict[str, Any] = {}
    for item in paper.items:
        before = item.paper["frame_before"]
        truth = truth_by_item.get(item.item_id, item.truth or {})
        if mode == "oracle":
            answers[item.item_id] = truth.get("frame_after")
        elif mode == "bluffer":
            answers[item.item_id] = before
        elif mode == "memoriser":
            # It replays what the trace published and predicts stasis elsewhere.
            # It reads `split` from the key, which is exactly the shortcut a
            # real memoriser has: it does not *know* the split, it knows whether
            # the transition is in the file it memorised, which is the same set.
            answers[item.item_id] = (truth.get("frame_after")
                                     if truth.get("split") == "replay" else before)
        else:
            raise ExamError("unknown calibration mode %r" % mode)
    return answers


# -- axes --------------------------------------------------------------------

def axes(report: Any, key_doc: Dict[str, Any], submission: Any) -> Dict[str, Any]:
    """The measurements the score alone cannot carry.

    `gap_replay_minus_heldout` is the headline and the reason this question type
    exists: 重放是对过去的预测，背题也能满分. A rule-learner is near zero. A
    memoriser is near one.
    """
    truth_by_item = {entry["item_id"]: entry.get("truth", {})
                     for entry in key_doc.get("items", [])}
    split_totals: Dict[str, List[float]] = {"replay": [], "heldout": []}
    rule_totals: Dict[str, Dict[str, List[float]]] = {}

    for score in report.scores:
        truth = truth_by_item.get(score.item_id, {})
        split = truth.get("split")
        rule = truth.get("rule")
        fraction = (score.awarded / score.possible) if score.possible else 0.0
        if split in split_totals:
            split_totals[split].append(fraction)
        if rule:
            rule_totals.setdefault(rule, {"replay": [], "heldout": []})
            if split in rule_totals[rule]:
                rule_totals[rule][split].append(fraction)

    def mean(values: Sequence[float]) -> float:
        return round(sum(values) / len(values), 6) if values else 0.0

    replay = mean(split_totals["replay"])
    heldout = mean(split_totals["heldout"])
    unchanged = sum(1 for entry in key_doc.get("items", [])
                    if entry.get("truth", {}).get("frame_after") is not None)
    return {
        "replay": replay,
        "heldout": heldout,
        "gap_replay_minus_heldout": round(replay - heldout, 6),
        "by_rule": {rule: {"replay": mean(v["replay"]),
                           "heldout": mean(v["heldout"]),
                           "gap": round(mean(v["replay"]) - mean(v["heldout"]), 6)}
                    for rule, v in sorted(rule_totals.items())},
        "abstained": sum(1 for s in report.scores if s.verdict == "abstained"),
        "unanswered": sum(1 for s in report.scores if s.verdict == "unanswered"),
        "items": unchanged,
    }
