"""V8 item (3), part b: quantify the direction the marker is generous in.

Constant answers with the strongest legal *reason* attached, plus the abstain
family, plus the marginal payoff of a bluff against silence.
"""

from __future__ import annotations

import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)

from exam.grading.mark import mark                     # noqa: E402
from exam.grading.registry import digest               # noqa: E402
from exam.model import Submission                      # noqa: E402
from exam.papers import verdict as V                   # noqa: E402
from exam.grading import rubrics_verdict as RV         # noqa: E402

paper = V.build()
key_doc = paper.key(digest())
truth_of = {e["item_id"]: e["truth"] for e in key_doc["items"]}
points_of = {e["item_id"]: float(e["points"]) for e in key_doc["items"]}
ids = [e["item_id"] for e in key_doc["items"]]
out = {}


def run(name, answers):
    sub = Submission(examinee_id=name, paper_id=paper.paper_id, answers=answers,
                     capabilities=("answers",), meta={})
    rep = mark(key_doc, sub, axes_fn=getattr(V, "axes", None))
    per_truth = {}
    for s in rep.scores:
        t = truth_of[s.item_id]["claim"]
        row = per_truth.setdefault(t, {"n": 0, "awarded": 0.0, "possible": 0.0})
        row["n"] += 1
        row["awarded"] = round(row["awarded"] + s.awarded, 6)
        row["possible"] = round(row["possible"] + s.possible, 6)
    return {"awarded": rep.awarded, "possible": rep.possible,
            "fraction": rep.fraction, "by_truth_claim": per_truth,
            "reasons": dict(sorted(rep.axes["reason_quality"]["counts"].items()))}


# --- 1. bare constant claims (the three verdict classes)
for c in ("solvable", "unsolvable", "abstain"):
    out["const_%s_bare" % c] = run("c-%s" % c, {i: {"claim": c} for i in ids})

# --- 2. every abstain token behaves the same?
out["abstain_tokens"] = {
    tok: run("c-%s" % tok, {i: {"claim": tok} for i in ids})["awarded"]
    for tok in sorted(RV._ABSTAIN)
}

# --- 3. constant "unsolvable" + "I searched everything"
out["const_unsolvable_search"] = run(
    "c-unsolv-search",
    {i: {"claim": "unsolvable", "reason": "exhaustive_search"} for i in ids})

# --- 4. constant "unsolvable" carrying the *true* certificate wherever the key
#        has one, i.e. the strongest possible impossibility bluff.
ans = {}
for i in ids:
    a = {"claim": "unsolvable"}
    blob = truth_of[i].get("certificate_blob")
    if blob:
        a["certificate"] = json.loads(blob)
    else:
        # solvable item: hand it the most plausible certificate we can build
        # from the sheet -- a cart_region invariant naming the real components.
        lvl = RV.Level(json.loads(truth_of[i]["level_blob"]))
        rep = RV.components(RV.relaxed_edges(lvl))
        a["certificate"] = {"kind": "invariant", "invariant": "cart_region",
                            "initial_value": list(rep.get(lvl.start, lvl.start)),
                            "goal_value": list(rep.get(lvl.goal, lvl.goal))}
    ans[i] = a
out["const_unsolvable_best_certificate"] = run("c-unsolv-cert", ans)

# does check_certificate ever accept on a solvable item?
accepts = []
for i in ids:
    if truth_of[i]["claim"] != "solvable":
        continue
    lvl = RV.Level(json.loads(truth_of[i]["level_blob"]))
    rep = RV.components(RV.relaxed_edges(lvl))
    tries = [
        {"kind": "invariant", "invariant": "cart_region",
         "initial_value": list(rep.get(lvl.start, lvl.start)),
         "goal_value": list(rep.get(lvl.goal, lvl.goal))},
        {"kind": "invariant", "invariant": "cart_row",
         "initial_value": lvl.start[0], "goal_value": lvl.goal[0]},
        {"kind": "invariant", "invariant": "cart_col",
         "initial_value": lvl.start[1], "goal_value": lvl.goal[1]},
        {"kind": "cut_set", "cells": [list(c) for c in sorted(lvl.lost_cells)]}
        if lvl.lost_cells else None,
        {"kind": "counting", "bound": (lvl.step_limit or 0) + 1,
         "limit": lvl.step_limit} if lvl.step_limit is not None else None,
    ]
    for cert in tries:
        if cert is None:
            continue
        r = RV.check_certificate(cert, lvl)
        if r["ok"]:
            accepts.append({"item": i, "cert": cert, "why": r["why"]})
out["certificates_accepted_on_solvable_items"] = accepts

# --- 5. constant "solvable" + the true witness wherever the key has one
ans = {}
for i in ids:
    a = {"claim": "solvable"}
    w = truth_of[i].get("witness")
    if w:
        a["witness"] = list(w)
    else:
        a["witness"] = ["UP", "DOWN", "LEFT", "RIGHT"]
    ans[i] = a
out["const_solvable_best_witness"] = run("c-solv-wit", ans)

# --- 6. the marginal payoff of a bluff against silence, per item
n_uns = sum(1 for i in ids if truth_of[i]["claim"] == "unsolvable")
n_sol = len(ids) - n_uns
out["marginal_payoff"] = {
    "items": len(ids), "n_unsolvable": n_uns, "n_solvable": n_sol,
    "pay_for_true_unsolvable_bare": 1.0,
    "pay_for_false_unsolvable": 0.0,
    "pay_for_abstain": 0.0,
    "expected_gain_of_bluffing_unsolvable_over_abstaining_per_item":
        round(n_uns / len(ids) * 1.0, 6),
    "expected_gain_of_bluffing_solvable_over_abstaining_per_item":
        round(n_sol / len(ids) * 1.0, 6),
    "downside_of_either_bluff": 0.0,
    "paper_asymmetry_points": round(n_uns * 1.0 - n_sol * 1.0, 6),
}

path = os.path.join(os.path.dirname(__file__), "asymmetry.json")
with open(path, "w", encoding="utf-8", newline="\n") as h:
    json.dump(out, h, indent=2)
    h.write("\n")
print(json.dumps(out, indent=2))
