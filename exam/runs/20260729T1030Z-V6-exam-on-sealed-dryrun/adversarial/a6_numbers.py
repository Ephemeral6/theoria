"""Attack 6: recompute every reported number by hand from DRILL.json / truth.json."""
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
RUN = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO)

drill = json.load(open(os.path.join(RUN, "DRILL.json"), encoding="utf-8"))
truth = json.load(open(os.path.join(RUN, "truth.json"), encoding="utf-8"))
sheet = json.load(open(os.path.join(RUN, "sheet.json"), encoding="utf-8"))

by_item = {e["item_id"]: e for e in truth["items"]}
order = [e["item_id"] for e in truth["items"]]
claims = {i: by_item[i]["truth"]["claim"] for i in order}
klass = {i: by_item[i]["truth"]["class"] for i in order}
cert = {i: by_item[i]["truth"]["certificate"] for i in order}
wit = {i: by_item[i]["truth"]["witness"] for i in order}
pts = {i: by_item[i]["points"] for i in order}

n_pos = sum(1 for i in order if claims[i] == "unsolvable")
n_neg = len(order) - n_pos
print("items=%d  unsolvable=%d  solvable=%d  points/item=%s  total=%.1f"
      % (len(order), n_pos, n_neg, sorted(set(pts.values())), sum(pts.values())))
print("classes:", {k: sum(1 for i in order if klass[i] == k) for k in set(klass.values())})
print()


def hand_score(mode):
    """The marking ladder, reimplemented from its prose description."""
    total = 0.0
    said = {}
    for i in order:
        p = pts[i]
        if mode == "null":
            said[i] = None
            continue
        if mode == "bluffer":
            s = "unsolvable"
        elif mode == "contrarian":
            s = "solvable"
        else:
            s = claims[i]
        said[i] = s
        if s != claims[i]:
            continue
        if mode in ("bluffer", "contrarian", "claim_only"):
            total += p * 0.5                       # right claim, no reason
        else:                                      # oracle
            if s == "unsolvable":
                total += p if cert[i] is not None else p * 0.5
            else:
                total += p if wit[i] is not None else p * 0.5
    return total, said


def hand_conf(said, subset=None):
    tp = fp = tn = fn = ab_p = ab_n = 0
    for i in (subset or order):
        pos = claims[i] == "unsolvable"
        s = said[i]
        if s is None:
            ab_p += pos
            ab_n += not pos
            continue
        sp = (s == "unsolvable")
        if pos and sp:
            tp += 1
        elif pos:
            fn += 1
        elif sp:
            fp += 1
        else:
            tn += 1
    sens = round(tp / (tp + fn), 6) if (tp + fn) else None
    spec = round(tn / (tn + fp), 6) if (tn + fp) else None
    return dict(tp=tp, fp=fp, tn=tn, fn=fn, sensitivity=sens, specificity=spec)


print("%-12s %-24s %-24s %s" % ("mode", "hand", "DRILL.json", "match"))
print("-" * 86)
mismatch = 0
for mode in ("oracle", "null", "bluffer", "contrarian", "claim_only"):
    total, said = hand_score(mode)
    frac = round(total / sum(pts.values()), 6)
    rep = drill["calibration"][mode]
    got = rep["fraction"]
    hc = hand_conf(said)
    gc = rep["confusion"]["overall"]
    same = (abs(frac - got) < 1e-9
            and hc["sensitivity"] == gc["sensitivity"]
            and hc["specificity"] == gc["specificity"]
            and all(hc[k] == gc[k] for k in ("tp", "fp", "tn", "fn")))
    if not same:
        mismatch += 1
    print("%-12s %-24s %-24s %s"
          % (mode,
             "%.4f s=%s p=%s" % (frac, hc["sensitivity"], hc["specificity"]),
             "%.4f s=%s p=%s" % (got, gc["sensitivity"], gc["specificity"]),
             "OK" if same else "MISMATCH"))
    for k in sorted(set(klass.values())):
        sub = [i for i in order if klass[i] == k]
        h = hand_conf(said, sub)
        g = rep["confusion"]["by_class"][k]
        ok = (h["sensitivity"] == g["sensitivity"] and h["specificity"] == g["specificity"]
              and all(h[x] == g[x] for x in ("tp", "fp", "tn", "fn")))
        if not ok:
            mismatch += 1
        print("      %-18s hand tp/fp/tn/fn=%d/%d/%d/%d s=%s p=%s   drill s=%s p=%s  %s"
              % (k, h["tp"], h["fp"], h["tn"], h["fn"], h["sensitivity"],
                 h["specificity"], g["sensitivity"], g["specificity"],
                 "OK" if ok else "MISMATCH"))
print("-" * 86)
print("%d mismatches" % mismatch)

print()
print("=" * 72)
print("A6-B  reason_ceiling")
print("=" * 72)
rc = drill["reason_ceiling"]
hand = 0.0
capped = []
for i in order:
    if claims[i] == "unsolvable" and cert[i] is None:
        hand += pts[i] * 0.5
        capped.append(i)
    elif claims[i] == "solvable" and wit[i] is None:
        hand += pts[i] * 0.5
        capped.append(i)
    else:
        hand += pts[i]
print("  hand: %.1f / %.1f = %.4f, capped=%s" % (hand, sum(pts.values()),
                                                 hand / sum(pts.values()), capped))
print("  drill: %s / %s = %s, capped=%s"
      % (rc["awarded"], rc["possible"], rc["fraction"],
         [c["item_id"] for c in rc["capped_items"]]))
print("  arithmetic matches: %s" % (abs(hand / sum(pts.values()) - rc["fraction"]) < 1e-9))
print()
print("  the CLAIM attached to the number, verbatim:")
for c in rc["capped_items"]:
    print("    %s" % c["why"])
print()
print("  -> refuted by a5_sheet_cheater.py A5-B: a cut_set certificate that has")
print("     nothing to do with that variant's operators is accepted, so the")
print("     'reason half' IS payable and the run scores 1.0000, above the")
print("     ceiling the gate at exam/tools/sealed_drill.py:665 tests against.")

print()
print("=" * 72)
print("A6-C  is the claim 'invariant/counting cannot express it' true?")
print("=" * 72)
from exam import drill_certificates as certs
from worldgen.core.world import GridWorld
from worldgen.generate import BY_ID
target = [i for i in order if claims[i] == "unsolvable" and cert[i] is None][0]
t = by_item[target]["truth"]
world = GridWorld(BY_ID[t["world_id"]])
for probe in (
    {"kind": "invariant", "invariant": "agent_row", "initial_value": 1, "goal_value": 5},
    {"kind": "invariant", "invariant": "agent_col", "initial_value": 1, "goal_value": 7},
    {"kind": "counting", "bound": 10, "limit": 9},
    {"kind": "cut_set", "cells": [[4, 1], [4, 7]]},
):
    r = certs.check(world.spec, t["operators"], probe)
    print("  %-58s -> ok=%s %s" % (json.dumps(probe)[:58], r["ok"], r["why"][:60]))

print()
print("=" * 72)
print("A6-D  the excuse for not using exam/leakage.check_paper")
print("=" * 72)
from exam import leakage
try:
    import exam.papers as papers
    print("  BUILDERS keys:", sorted(papers.BUILDERS))
    print("  'heldout_worldgen' in BUILDERS:", "heldout_worldgen" in papers.BUILDERS)
except Exception as exc:
    print("  ", exc)
print("  drill's own probe count:", drill["leakage"]["probes"],
      "failures:", drill["leakage"]["failures"])

print()
print("=" * 72)
print("A6-E  what PLAN.md promised vs what the run directory holds")
print("=" * 72)
for want in ("MANIFEST.json", "RUN_STATE.md", "SEALED_DRILL.md"):
    p = os.path.join(RUN, want)
    print("  %-18s in run dir: %s" % (want, os.path.exists(p)))
print("  %-18s in exam/:   %s" % ("SEALED_DRILL.md",
                                  os.path.exists(os.path.join(REPO, "exam", "SEALED_DRILL.md"))))
print("  run dir holds:", sorted(os.listdir(RUN)))
