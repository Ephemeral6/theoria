import json, os, subprocess, run

A = run.ATTACKS
TARGETS = [
    ("far9",
     os.path.join(A, "work", "a2", "far9", "far9.pddl"),
     os.path.join(A, "work", "a2", "far9", "singleton", "sokoban_guarded_singleton_domain.pddl"),
     os.path.join(A, "work", "a2", "far9", "singleton", "far9_guarded_singleton.pddl")),
    ("swap-passage",
     os.path.join(A, "work", "a5", "swap", "swap-passage.pddl"),
     os.path.join(A, "work", "a5", "swap", "singleton", "sokoban_guarded_singleton_domain.pddl"),
     os.path.join(A, "work", "a5", "swap", "singleton", "swap-passage_guarded_singleton.pddl")),
]
CONFIGS = [
    ("sys1", "astar(cpdbs(patterns=systematic(1)))"),
    ("sys2", "astar(cpdbs(patterns=systematic(2)))"),
    ("sys3", "astar(cpdbs(patterns=systematic(3)))"),
    ("ipdb-default", "astar(ipdb())"),
] + [("ipdb-seed%d" % n, "astar(ipdb(random_seed=%d))" % n) for n in (0, 1, 2, 3, 7, 11, 42, 1234)]

recs = []
for name, bp, gd, gp in TARGETS:
    print("===", name, flush=True)
    for tag, s in CONFIGS:
        try:
            recs.append(run.pair(name, bp, gd, gp, s, tag))
        except subprocess.TimeoutExpired:
            print("  %-14s %-20s TIMEOUT" % (name, tag), flush=True)
json.dump(recs, open("pinned_patterns.json", "w"), indent=2)
print("WROTE pinned_patterns.json")
