"""Rebuild three-far8 (base + singleton guard) from the current a3_family HAND.

The stored base problem file was rewritten at 23:39:25 by a later pass, after the
23:34:58 log that reports 9202 expansions, while the stored guarded file dates
from the 23:35 pass.  So base-on-disk and guard-on-disk are not necessarily the
same vintage.  Rebuilding both from one source removes the question.
"""
import os, sys, hashlib, json

ATT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, ATT)
from lens import carve_level                       # noqa: E402
from a3_family import HAND, parse                  # noqa: E402
from bench import compile_theorems                 # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "work", "three-far8")
level = parse("three-far8", HAND["three-far8"])
_p, _d, problem, theorems, _c = carve_level(level, OUT)
gdom, gprob = compile_theorems.write_guarded(
    os.path.join(OUT, "singleton"), level.name, level.problem_text(),
    theorems, guard="singleton", problem=problem)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


old_base = os.path.join(ATT, "work", "a3", "three-far8", "three-far8.pddl")
old_guard = os.path.join(ATT, "work", "a3", "three-far8", "singleton",
                         "three-far8_guarded_singleton.pddl")
info = {
    "n_theorems": len(theorems),
    "regen_base": sha(os.path.join(OUT, "three-far8.pddl")),
    "disk_base": sha(old_base),
    "regen_guard": sha(gprob),
    "disk_guard": sha(old_guard),
}
info["base_matches_disk"] = info["regen_base"] == info["disk_base"]
info["guard_matches_disk"] = info["regen_guard"] == info["disk_guard"]
print(json.dumps(info, indent=2))
json.dump(info, open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "three-far8_provenance.json"), "w"), indent=2)
