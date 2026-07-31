"""Attack (d): tools/run_all.py step 9 uses carver theorems as a search pruner
to decide a published `verdict: "unreachable"` -- with no pruning_report, on a
DIFFERENT instance than the one the carver's gate ran on.

run_all.py:152  deadlock_carver.run(soko_domain, soko_problem=OPEN4FAR)  <- gated
run_all.py:191  probe_frontier.run_with_planner(..., ring_problem,
                    prune=pruner(carve(Task.build(soko_domain, ring_problem))),
                    out_path=out_path)                                   <- NOT gated

The theorems carved on RING never meet `candidates()`, never meet
`pruning_report`, and their consequence (`unreachable`) is published to
artifacts/candidates.jsonl (row 43).
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from engines import deadlock_carver as dc
from engines import probe_frontier
from engines.fd_adapter.pddl import parse_domain, parse_problem
from fixtures import sokoban
from engines.probe_frontier import sokoban_probe
build_probe = sokoban_probe.build

soko_domain = parse_domain(open(sokoban.DOMAIN_PATH, encoding="utf-8").read())
ring_problem = parse_problem(open(sokoban.RING.path, encoding="utf-8").read())

task = dc.Task.build(soko_domain, ring_problem)
theorems = dc.carve(task)
print("theorems carved on RING:", len(theorems))

# Was a verdict EVER taken on these?  run_all does not take one.
report = dc.pruning_report(soko_domain, ring_problem, theorems)
print("pruning_report(ring).same_answer =", report.same_answer)
print("refutation(report) =", dc.refutation(report))

bundle = build_probe()
for label, prune in (("with pruner", dc.pruner(theorems)), ("blind", None)):
    designed = probe_frontier.design(
        bundle["hypotheses"], bundle["configurations"], soko_domain, ring_problem,
        prune=prune,
    )
    print("\n%s:" % label)
    for p in designed:
        print("   %-20s tier=%-12s verdict=%-12s len=%s expansions=%s"
              % (p.configuration.name, p.tier, p.reach.status,
                 p.reach.length, p.reach.expansions))

# Now the same publication path with a DELIBERATELY unsound pruner: nothing
# between it and artifacts/candidates.jsonl reads any verdict.
class PruneEverythingNotInitial:
    def __init__(self, initial):
        self.initial = initial
    def __call__(self, state):
        return state != self.initial

designed = probe_frontier.design(
    bundle["hypotheses"], bundle["configurations"], soko_domain, ring_problem,
    prune=PruneEverythingNotInitial(task.initial),
)
print("\nwith a knowingly unsound pruner (no gate anywhere on this path):")
for p in designed:
    print("   %-20s tier=%-12s verdict=%s" % (p.configuration.name, p.tier, p.reach.status))
