"""Hostile reading of the 'theory-free' prior: ablations and controls."""
import copy, json, sys, collections
from exam.grading.mark import mark
from exam.grading.registry import digest
from exam.guard import no_network
from exam.model import Submission
from exam.papers import heldout_worldgen as hw, worldgen_port as port

sys.path.insert(0, "exam/runs/20260728T151000Z-V7-exam-stress-fanout")
import importlib.util
spec = importlib.util.spec_from_file_location(
    "prior_sweep", "exam/runs/20260728T151000Z-V7-exam-stress-fanout/prior_sweep.py")
ps = importlib.util.module_from_spec(spec); spec.loader.exec_module(ps)


def score(mutate_sheet=None, delta=None):
    """Score the prior over all worlds; optionally mutate the sheet side first."""
    D = delta or ps.DELTA
    old = ps.DELTA
    ps.DELTA = D
    perfect = 0; tot_awarded = 0.0; tot_possible = 0.0
    per_rule = collections.Counter(); per_rule_ok = collections.Counter()
    beats = 0
    try:
        with no_network():
            d = digest()
            for w in port.world_ids():
                paper = hw.build_for(w, 2)
                key_doc = paper.key(d)
                answers = {}
                for it in paper.items:
                    side = copy.deepcopy(it.paper)
                    if mutate_sheet:
                        mutate_sheet(side)
                    answers[it.item_id] = ps.answer(side)
                rep = mark(key_doc, Submission("fake", paper.paper_id, answers,
                                               ("answers",)), axes_fn=hw.axes)
                got = {s.item_id: s.verdict == "correct" for s in rep.scores}
                for it in paper.items:
                    per_rule[it.truth["rule"]] += 1
                    per_rule_ok[it.truth["rule"]] += got[it.item_id]
                tot_awarded += rep.awarded; tot_possible += rep.possible
                if rep.fraction == 1.0: perfect += 1
                floor = sum(1 for it in paper.items
                            if it.truth["frame_after"] == it.paper["frame_before"])
                if rep.fraction > floor/len(paper.items) + 1e-9: beats += 1
    finally:
        ps.DELTA = old
    return {"overall": round(tot_awarded/tot_possible, 4), "perfect_worlds": perfect,
            "beats_floor": beats, "per_rule": {r: "%d/%d" % (per_rule_ok[r], per_rule[r])
                                               for r in sorted(per_rule)}}


base = score()
print("BASELINE                 ", json.dumps({k: v for k, v in base.items() if k != "per_rule"}))
print("  per rule:", json.dumps(base["per_rule"]))

def drop(key):
    def f(side):
        if isinstance(side.get("legend"), dict):
            side["legend"] = {k: v for k, v in side["legend"].items() if k != key}
    return f

for k in ("agent", "wall", "floor"):
    r = score(mutate_sheet=drop(k))
    print("legend WITHOUT %-8s  " % k, json.dumps({x: y for x, y in r.items() if x != "per_rule"}))

r = score(mutate_sheet=lambda s: s.pop("legend", None))
print("no legend at all         ", json.dumps({x: y for x, y in r.items() if x != "per_rule"}))

# controls: the direction convention is itself brought-in knowledge.
FLIP = {"UP": (1, 0), "DOWN": (-1, 0), "LEFT": (0, 1), "RIGHT": (0, -1)}
TRANS = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
print("DELTA reversed           ", json.dumps({x: y for x, y in score(delta=FLIP).items() if x != "per_rule"}))
print("DELTA transposed         ", json.dumps({x: y for x, y in score(delta=TRANS).items() if x != "per_rule"}))
