"""Re-verification of every corrected integer, run by the corrector, not relayed.

1. per-rule table of the prior, the identity of the `walk` miss, the zero set.
2. the `[]` / "unsolvable" / 0 scores on the adaptation paper.
"""
import copy, json, collections, importlib.util
from exam.grading.mark import mark
from exam.grading.registry import digest
from exam.guard import no_network
from exam.model import Submission
from exam.papers import heldout_worldgen as hw, worldgen_port as port
from exam.papers import module_for

RUN = "exam/runs/20260728T151000Z-V7-exam-stress-fanout"
spec = importlib.util.spec_from_file_location("prior_sweep", RUN + "/prior_sweep.py")
ps = importlib.util.module_from_spec(spec); spec.loader.exec_module(ps)

per_rule = collections.Counter(); per_rule_ok = collections.Counter()
misses = []
n_items = 0
with no_network():
    d = digest()
    for w in port.world_ids():
        paper = hw.build_for(w, 2)
        answers = {it.item_id: ps.answer(it.paper) for it in paper.items}
        rep = mark(d and paper.key(d), Submission("p", paper.paper_id, answers,
                                                  ("answers",)), axes_fn=hw.axes)
        got = {s.item_id: s.verdict == "correct" for s in rep.scores}
        for it in paper.items:
            n_items += 1
            r = it.truth["rule"]
            per_rule[r] += 1; per_rule_ok[r] += got[it.item_id]
            if not got[it.item_id]:
                misses.append((it.item_id, r))

print("items:", n_items, " misses:", len(misses))
zero = sorted(r for r in per_rule if per_rule_ok[r] == 0)
print("zero-set rules:", len(zero), {r: per_rule[r] for r in zero},
      "sum =", sum(per_rule[r] for r in zero))
for r in sorted(per_rule):
    print("   %-28s %d/%d" % (r, per_rule_ok[r], per_rule[r]))
print("walk misses      :", [m for m in misses if m[1] == "walk"])
print("collect_token    : %d/%d, misses %s"
      % (per_rule_ok["collect_token"], per_rule["collect_token"],
         [m for m in misses if m[1] == "collect_token"]))

# ------------------------------------------------------------------ item 3
print()
mod = module_for("adaptation")
with no_network():
    d = digest()
    paper = mod.build()
    key_doc = paper.key(d)
    ax = getattr(mod, "axes", None)
    print("adaptation items:", len(paper.items))
    for label, ans in (("[]", []), ('"unsolvable"', "unsolvable"), ("0", 0),
                       ("GARBAGE", "__V4_GARBAGE__"), ('""', ""), ("{}", {}),
                       ("None", None)):
        sub = Submission("n", paper.paper_id,
                         {i.item_id: copy.deepcopy(ans) for i in paper.items},
                         ("answers",))
        rep = mark(key_doc, sub, axes_fn=ax)
        by_rub = collections.Counter()
        for s in rep.scores:
            if s.awarded:
                by_rub[s.rubric_id] += s.awarded
        print("  %-12s -> %.3f / %.3f   %s"
              % (label, rep.awarded, rep.possible,
                 {k: round(v, 3) for k, v in sorted(by_rub.items())}))
