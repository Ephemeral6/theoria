"""Build BOTH artifacts: (1) solver could not compute, (2) checked and clean."""
import json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, ROOT)
from fuzzlab import campaign
import fuzzlab.props.lp_potential as props

HERE = os.path.dirname(os.path.abspath(__file__))

def starved(world):
    from engines import lp_potential as engine
    return engine.run(world.graph, world.initial,
                      goal_states=list(world.goal_states),
                      solver_options={"maxiter": 0})

out = os.path.join(HERE, "starved")
os.makedirs(out, exist_ok=True)
pristine = props._solve
props._solve = starved
try:
    rc = campaign.main(["--engine", "lp_potential", "--worlds", "12", "--out", out])
finally:
    props._solve = pristine
print("campaign.main exit code with a blind solver:", rc)

clean = os.path.join(HERE, "clean")
os.makedirs(clean, exist_ok=True)
rc2 = campaign.main(["--engine", "lp_potential", "--worlds", "12", "--out", clean])
print("campaign.main exit code clean:", rc2)

for label, d in (("STARVED", out), ("CLEAN", clean)):
    j = json.load(open(os.path.join(d, "campaign.json"), encoding="utf-8"))
    print("\n===== %s =====" % label)
    print(json.dumps(j["totals"], indent=2, sort_keys=True))
    e = j["engines"][0]
    for k in ("invariant_worlds_evaluated", "invariant_worlds_unavailable",
              "skips_by_cause", "skips_by_cause_class", "skipped", "raised",
              "unavailable", "worlds_checked"):
        print("  %s = %s" % (k, json.dumps(e[k], sort_keys=True)))
