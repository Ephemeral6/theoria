"""Attack 5: answer the paper from sheet.json alone.

Three examinees, each strictly weaker than the last in what it is allowed to
look at.  None of them ever runs a search, and none of them ever consults truth.

  * `position`   -- item ORDER only.  Nothing else on the sheet is read.
  * `shape`      -- the operator shape only (op name, list lengths). No board.
  * `no_grid`    -- operator shape + board.start / board.goal.  Never reads
                    `board.grid`, i.e. never learns where a single wall is.

They are marked by the drill's own `mark()` against the drill's own paper.
"""
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)

import inspect
from exam import drill_certificates as certs
from exam.grading.confusion_matrix import per_class_confusion
from exam.model import Paper, Submission, sha256_text
from exam.tools.sealed_drill import (PAPER_ID, QUESTION_TYPE, PROMPT_ID, FAKES,
                                     build_items, fake_answers, grade, mark,
                                     _sheet_side)
from exam import guard

OUT = tempfile.mkdtemp(prefix="v6-adv-")
items, findings = build_items(os.path.join(OUT, "variant_specs"), OUT)
paper = Paper(paper_id=PAPER_ID, question_type=QUESTION_TYPE,
              instructions=_sheet_side.__doc__ or "", items=items,
              world=guard.provenance(),
              notes={"classes": sorted({f["class"] for f in findings}),
                     "prompt_id": PROMPT_ID})
rubric_digest = "drill:" + sha256_text(
    inspect.getsource(grade) + inspect.getsource(certs))[:32]
sheet = paper.sheet(rubric_digest=rubric_digest)
key = paper.key(rubric_digest=rubric_digest)

DELTA = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}


def effective(ops):
    forbidden = {o["action"] for o in ops if o["op"] == "forbid_action"}
    remap = {o["from"]: o["to"] for o in ops if o["op"] == "remap_action"}
    return {c: (None if c in forbidden else remap.get(c, c))
            for c in ("UP", "DOWN", "LEFT", "RIGHT")}


def cheat_position(sheet):
    """Item order only. Odd-numbered items (1-based) are unsolvable."""
    out = {}
    for i, it in enumerate(sheet["items"], 1):
        out[it["item_id"]] = {"claim": "unsolvable" if i % 2 else "solvable"}
    return out


def cheat_shape(sheet):
    """Operator shape only. Never reads the board."""
    out = {}
    for it in sheet["items"]:
        ops = it["wrapper_edit"]
        kinds = [o["op"] for o in ops]
        if "win_tighten" in kinds:
            claim = "unsolvable"
        elif "observation_loss" in kinds:
            n = max(len(o["cells"]) for o in ops if o["op"] == "observation_loss")
            claim = "unsolvable" if n >= 2 else "solvable"
        else:
            claim = "solvable"
        out[it["item_id"]] = {"claim": claim}
    return out


def cheat_no_grid(sheet):
    """Operator shape + the two coordinates. `board.grid` is never touched."""
    out = {}
    for it in sheet["items"]:
        ops = it["wrapper_edit"]
        kinds = [o["op"] for o in ops]
        sr, sc = it["board"]["start"]
        gr, gc = it["board"]["goal"]
        live = effective(ops)
        answer = None
        # (1) an axis invariant, straight off the alphabet + two coordinates
        for name, axis, s, g in (("agent_row", 0, sr, gr), ("agent_col", 1, sc, gc)):
            if g == s:
                continue
            need = 1 if g > s else -1
            if not any(a is not None and
                       ((DELTA[a][axis] > 0) - (DELTA[a][axis] < 0)) == need
                       for a in live.values()):
                answer = {"claim": "unsolvable",
                          "certificate": {"kind": "invariant", "invariant": name,
                                          "initial_value": s, "goal_value": g}}
                break
        # (2) a counting bound, ditto
        if answer is None:
            limits = sorted(o["limit"] for o in ops if o["op"] == "step_limit")
            man = abs(gr - sr) + abs(gc - sc)
            if limits and man > limits[0]:
                answer = {"claim": "unsolvable",
                          "certificate": {"kind": "counting", "bound": man,
                                          "limit": limits[0]}}
        # (3) pure shape guesses
        if answer is None and "win_tighten" in kinds:
            answer = {"claim": "unsolvable"}
        if answer is None and "observation_loss" in kinds:
            n = max(len(o["cells"]) for o in ops if o["op"] == "observation_loss")
            if n >= 2:
                answer = {"claim": "unsolvable"}
        # (4) otherwise: solvable, with the naive L-shaped route derived from
        #     the two coordinates. No wall is ever consulted.
        if answer is None:
            path = ["DOWN"] * max(0, gr - sr) + ["UP"] * max(0, sr - gr) \
                 + ["RIGHT"] * max(0, gc - sc) + ["LEFT"] * max(0, sc - gc)
            answer = {"claim": "solvable", "witness": path}
        out[it["item_id"]] = answer
    return out


CHEATS = {"position": cheat_position, "shape": cheat_shape, "no_grid": cheat_no_grid}

print("reference bands from the drill itself")
print("-" * 64)
for mode in FAKES:
    sub = Submission(examinee_id="fake-%s" % mode, paper_id=PAPER_ID,
                     answers=fake_answers(mode, paper),
                     capabilities=() if mode == "null" else ("answers",))
    rep = mark(paper, sub, rubric_digest, OUT)
    print("  %-12s %.4f" % (mode, rep.fraction))

print()
print("cheap examinees that never search")
print("-" * 64)
for name, fn in CHEATS.items():
    answers = fn(sheet)                      # sheet only -- `key` is not in scope
    sub = Submission(examinee_id="cheat-%s" % name, paper_id=PAPER_ID,
                     answers=answers, capabilities=("answers",))
    rep = mark(paper, sub, rubric_digest, OUT)
    conf = per_class_confusion(rep, key, positive="unsolvable")["overall"]
    print("  %-12s %.4f  (%.1f/%.1f)  sens %s spec %s"
          % (name, rep.fraction, rep.awarded, rep.possible,
             conf["sensitivity"], conf["specificity"]))
    for s in rep.scores:
        print("       %-14s %-10s %-22s %.1f/%.1f"
              % (s.item_id, s.verdict, s.detail.get("reason"), s.awarded, s.possible))
    print()

print("=" * 64)
print("A5-B  the reason ceiling (0.95) is not a ceiling")
print("=" * 64)
# the oracle's own answers, plus one bogus cut_set on the item the drill says
# nobody -- ground truth included -- can pay the reason half for.
answers = dict(fake_answers("oracle", paper))
target = None
for item in paper.items:
    if item.truth["claim"] == "unsolvable" and item.truth["certificate"] is None:
        target = item
assert target is not None
answers[target.item_id] = {"claim": "unsolvable",
                           "certificate": {"kind": "cut_set", "cells": [[4, 1], [4, 7]]}}
sub = Submission(examinee_id="oracle-plus-bluff", paper_id=PAPER_ID,
                 answers=answers, capabilities=("answers",))
rep = mark(paper, sub, rubric_digest, OUT)
print("  item %s is %s / world %s / operators %s"
      % (target.item_id, target.truth["claim"], target.truth["world_id"],
         [o["op"] for o in target.truth["operators"]]))
print("  the drill's declared reason_ceiling is 0.95")
print("  oracle + one cut_set that has nothing to do with the operators: %.4f"
      % rep.fraction)
for s in rep.scores:
    if s.item_id == target.item_id:
        print("  that item scored %.1f/%.1f, reason=%r"
              % (s.awarded, s.possible, s.detail.get("reason")))

print()
print("=" * 64)
print("A5-C  marker robustness on hostile submissions")
print("=" * 64)
item = paper.items[0]
for label, ans in (
    ("certificate is a string", {"claim": "unsolvable", "certificate": "cut it"}),
    ("certificate is a list", {"claim": "unsolvable", "certificate": [[4, 1]]}),
    ("witness is a string", {"claim": "solvable", "witness": "DOWNDOWN"}),
    ("witness has a bogus command", {"claim": "solvable", "witness": ["BANANA"]}),
    ("witness contains RESET", {"claim": "solvable", "witness": ["RESET", "DOWN"]}),
    ("witness of 200000 commands", {"claim": "solvable", "witness": ["UP"] * 200000}),
):
    tgt = paper.items[1] if ans["claim"] == "solvable" else paper.items[0]
    try:
        sc = grade(ans, tgt, OUT)
        print("  %-28s -> %s / %r  (%.1f)" % (label, sc.verdict,
                                              sc.detail.get("reason"), sc.awarded))
    except Exception as exc:
        print("  %-28s -> RAISED %s: %s" % (label, type(exc).__name__,
                                            str(exc)[:90]))

shutil.rmtree(OUT, ignore_errors=True)
