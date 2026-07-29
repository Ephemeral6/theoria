"""(f) with_report=False, (g) the MARK branch and invariants_withheld.

Uses a knowingly unsound theorem that DOES move the answer, so `refutation()`
fires, then walks all four cells of the README's table.
"""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from engines import deadlock_carver as dc
from engines.deadlock_carver.carve import Theorem
from engines.fd_adapter import search as fd_search
from engines.fd_adapter.pddl import parse_domain, parse_problem
from fixtures import sokoban

domain = parse_domain(open(sokoban.DOMAIN_PATH, encoding="utf-8").read())
problem = parse_problem(open(sokoban.OPEN4FAR.path, encoding="utf-8").read())
task = dc.Task.build(domain, problem)
real = dc.carve(task)
print("real theorems:", len(real))

# a theorem covering the initial state -> prunes everything -> answer moves
pattern = tuple(sorted(task.initial))
killer = Theorem(pattern=pattern, blocked=(), goal_conflict=(pattern[0], pattern[0]),
                 n_deleting_actions=0)
theorems = list(real) + [killer]
report = dc.pruning_report(domain, problem, theorems)
print("same_answer:", report.same_answer, "-> refuted:", dc.refutation(report) is not None)


def show(label, rows):
    inv = [r for r in rows if r["kind"] == "invariant"]
    plan = [r for r in rows if r["kind"] == "plan"]
    pp = plan[0]["payload"] if plan else {}
    print("%-34s invariants=%-3d plan=%d  refuted=%-5s withheld=%-5s on_refutation=%-9s "
          "plan_length_unchanged=%s"
          % (label, len(inv), len(plan), pp.get("refuted", "ABSENT"),
             pp.get("invariants_withheld", "ABSENT"),
             pp.get("on_refutation", "ABSENT"),
             pp.get("plan_length_unchanged", "ABSENT")))
    if inv:
        print("      invariant rows carry refuted:",
              sorted({r["payload"].get("refuted", "ABSENT") for r in inv}))


show("refuted, withhold (default)", dc.candidates(theorems, task, report=report, timestamp="T"))
show("refuted, mark", dc.candidates(theorems, task, report=report, timestamp="T",
                                    on_refutation=dc.MARK))
show("no report (with_report=False)", dc.candidates(theorems, task, report=None, timestamp="T"))

# (f) the same through run(), which is the entry point tools/ use
out = "runs/20260729T020000Z-E16-verdict-must-gate/attacks/_f_out.jsonl"
if os.path.exists(out):
    os.remove(out)


def fake_carve(t, max_pattern=None):
    return theorems


import engines.deadlock_carver as mod
orig = mod.carve
mod.carve = fake_carve
try:
    mod.run(domain, problem, out_path=out, with_report=False, timestamp="T")
finally:
    mod.carve = orig
rows = [json.loads(l) for l in open(out, encoding="utf-8")]
print("\nrun(..., with_report=False) wrote %d rows to disk:" % len(rows))
print("   invariant rows:", sum(1 for r in rows if r["kind"] == "invariant"),
      " plan rows:", sum(1 for r in rows if r["kind"] == "plan"))
print("   any 'refuted' marker anywhere?",
      any("refuted" in r["payload"] for r in rows))
print("   the killer theorem is among them:",
      any(r["payload"].get("pattern_text", "").startswith("at(") for r in rows))
print("   -> a theorem this repo's own gate refutes is on disk, with nothing "
      "in the stream saying so.")

# (g) does the plan row ever disagree with the invariant rows?
rows = dc.candidates(theorems, task, report=report, timestamp="T", on_refutation=dc.MARK)
plan = [r for r in rows if r["kind"] == "plan"][0]["payload"]
print("\nMARK branch consistency: plan.refuted=%s plan.invariants_withheld=%s "
      "plan.plan_length_unchanged=%s ; %d invariant rows all marked refuted=%s"
      % (plan["refuted"], plan["invariants_withheld"], plan["plan_length_unchanged"],
         sum(1 for r in rows if r["kind"] == "invariant"),
         all(r["payload"].get("refuted") for r in rows if r["kind"] == "invariant")))

# empty theorem list under WITHHOLD
rows = dc.candidates([], task, report=report, timestamp="T")
plan = [r for r in rows if r["kind"] == "plan"][0]["payload"]
print("carved nothing + refuted: invariants_withheld=%s (same value as a run that "
      "withheld zero)" % plan["invariants_withheld"])
