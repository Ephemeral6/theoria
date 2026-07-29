"""Attack (e): `same_answer` is not a sufficient refutation test.

Build a Theorem whose pattern covers a state that is (i) reachable and (ii)
ALIVE -- the goal is reachable from it -- but that lies on no optimal plan.  The
theorem's own `claim` ("every reachable state containing P is dead") is FALSE.
Pruning with it changes neither `solved` nor `length`, so `same_answer` is True,
`refutation()` returns None, and `candidates()` publishes the false theorem with
no `refuted` marker.
"""
import os
import sys
from collections import deque

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from engines import deadlock_carver as dc
from engines.deadlock_carver.carve import Theorem
from engines.fd_adapter import search as fd_search
from engines.fd_adapter.pddl import parse_domain, parse_problem
from fixtures import sokoban

domain = parse_domain(open(sokoban.DOMAIN_PATH, encoding="utf-8").read())
problem = parse_problem(open(sokoban.OPEN4FAR.path, encoding="utf-8").read())
task = dc.Task.build(domain, problem)

actions, initial, _ = task.actions, task.initial, None
static = set()


def goal_hit(state):
    return (all(a in state for a in task.goal_positive)
            and not any(a in state for a in task.goal_negative))


# forward BFS from the initial state
d_init = {initial: 0}
q = deque([initial])
succ = {}
while q:
    s = q.popleft()
    outs = []
    for a in actions:
        if fd_search.applicable(a, s):
            t = fd_search.successor(a, s)
            outs.append(t)
            if t not in d_init:
                d_init[t] = d_init[s] + 1
                q.append(t)
    succ[s] = outs

goals = [s for s in d_init if goal_hit(s)]
optimal = min(d_init[g] for g in goals)
print("reachable states:", len(d_init), " optimal plan length:", optimal)

# backward BFS: distance to a goal within the reachable set
pred = {}
for s, outs in succ.items():
    for t in outs:
        pred.setdefault(t, []).append(s)
d_goal = {g: 0 for g in goals}
q = deque(goals)
while q:
    s = q.popleft()
    for p in pred.get(s, ()):
        if p not in d_goal:
            d_goal[p] = d_goal[s] + 1
            q.append(p)

alive_offpath = [
    s for s in d_init
    if s in d_goal and d_init[s] + d_goal[s] > optimal and d_init[s] > 0
]
print("reachable+ALIVE states on no optimal plan:", len(alive_offpath))
victim = sorted(alive_offpath, key=lambda s: (d_init[s], sorted(s)))[0]
print("victim: d_init=%d d_goal=%d (goal IS reachable from it)"
      % (d_init[victim], d_goal[victim]))

# A pattern that is exactly this state's atom set -- so the pruner deletes this
# state (and any superset) and nothing else.
pattern = tuple(sorted(victim))
fake = Theorem(pattern=pattern, blocked=(), goal_conflict=(pattern[0], pattern[0]),
               n_deleting_actions=0)
print("\nfake theorem claim:", fake.as_json()["claim"][:90], "...")
print("is that claim true?  goal reachable from the covered state in %d moves -> FALSE"
      % d_goal[victim])

report = dc.pruning_report(domain, problem, [fake])
print("\npruning_report: baseline solved=%s len=%s | pruned solved=%s len=%s"
      % (report.baseline.solved, report.baseline.length,
         report.pruned.solved, report.pruned.length))
print("states pruned:", report.pruned.pruned)
print("same_answer  :", report.same_answer)
print("refutation() :", dc.refutation(report))

rows = dc.candidates([fake], task, report=report, timestamp="2026-07-27T00:00:00Z")
inv = [r for r in rows if r["kind"] == "invariant"]
print("\ninvariant rows emitted:", len(inv))
print("row carries 'refuted'? ", "refuted" in inv[0]["payload"])
print("plan row 'plan_length_unchanged':",
      [r for r in rows if r["kind"] == "plan"][0]["payload"]["plan_length_unchanged"])
print("\n=> a demonstrably false theorem passed the gate.")
