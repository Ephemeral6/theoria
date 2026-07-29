"""Is the guarded task's h(init)=infinity a budget effect or an information effect?

If hill climbing on the *base* task reaches infinity too when given far more
room, the guard only bought a cheaper route to the same abstraction.  If the
base task refuses at 30x the collection budget while the guarded task still
says infinity at 1/20th of the default, the asymmetry is not about budget.
"""
import json, os
import run as R

A = R.ATTACKS
BASE_D, BASE_P = R.DOMAIN, os.path.join(A, "work", "a5", "swap", "swap-passage.pddl")
G_D = os.path.join(A, "work", "a5", "swap", "singleton", "sokoban_guarded_singleton_domain.pddl")
G_P = os.path.join(A, "work", "a5", "swap", "singleton", "swap-passage_guarded_singleton.pddl")

LADDER = [
    ("tiny", "pdb_max_size=50000,collection_max_size=200000,max_time=30"),
    ("small", "pdb_max_size=200000,collection_max_size=1000000,max_time=30"),
    ("default", "max_time=30"),
    ("big", "pdb_max_size=8000000,collection_max_size=40000000,max_time=120"),
    ("huge", "pdb_max_size=20000000,collection_max_size=60000000,max_time=300"),
]
recs = []
for tag, opts in LADDER:
    for seed in (0, 1, 42):
        s = "astar(ipdb(%s,random_seed=%d))" % (opts, seed)
        r = R.pair("swap-passage", BASE_P, G_D, G_P, s, "budget-%s-s%d" % (tag, seed))
        r["budget"] = tag
        r["seed"] = seed
        print("      pdb sizes  base %s (%s pats)  guarded %s (%s pats)"
              % (r["base"]["hc_pdb_size"], r["base"]["hc_patterns"],
                 r["guarded"]["hc_pdb_size"], r["guarded"]["hc_patterns"]), flush=True)
        recs.append(r)
json.dump(recs, open("swap_budget.json", "w"), indent=2)
print("WROTE swap_budget.json")
