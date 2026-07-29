"""Are the states the guard removes ones lmcut was already refusing to expand?

If any theorem-dead state is *not* relaxation-dead, then A* with lmcut would have
expanded it and the guard's expansion saving is ordinary pruning.  If none is,
the saving has to come from the heuristic changing value on live states.  This
re-uses the audit's own `relaxation_sweep.analyse`, on the instances the lmcut
counterexamples actually live on.
"""
import json, os, random, sys

ATT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, ATT)
import relaxation_sweep as RS                     # noqa: E402
from a7_hunt import random_level                  # noqa: E402
from a3_family import HAND, parse                 # noqa: E402

WANT = {"hunt0021", "hunt0037", "hunt0070"}
levels = []
rng = random.Random(7)
for index in range(400):
    lvl = random_level(rng, index)
    if lvl is not None and lvl.name in WANT:
        levels.append(lvl)
    if len(levels) == len(WANT):
        break
levels.append(parse("three-far8", HAND["three-far8"]))
levels.append(parse("swap-passage", HAND["swap-passage"]))

out = []
for lvl in levels:
    entry = RS.analyse(lvl, cap=400000)
    out.append(RS.public(entry) if "skipped" not in entry else entry)
    print(json.dumps(out[-1], sort_keys=True)[:400], flush=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "deadsets.json"), "w"), indent=2, sort_keys=True)
