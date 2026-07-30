"""Does one invariant ever file >1 skip on one world?  If so the coverage
column and the unavailable column are both computed from a wrong denominator."""
import os, sys, json
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, ROOT)
from collections import Counter
from fuzzlab import campaign
import fuzzlab.props.cegis_miner as cm

cm.COMBINATION_BUDGET = 1          # force the budget skip to fire on every rule
r = campaign.run_engine("cegis_miner", campaign.DEFAULT_SEED, 12, quiet=True)
rep = r["report"]
print("invariant_worlds_evaluated:", json.dumps(rep["invariant_worlds_evaluated"], sort_keys=True))
print("skips_by_cause          :", json.dumps(rep["skips_by_cause"], sort_keys=True))
print("skipped total           :", rep["skipped"])

per = Counter()
for f in r["findings"]:
    if f.kind == "skipped":
        per[(f.invariant, f.seed)] += 1
worst = per.most_common(3)
print("max skips for one (invariant, world):", worst)
print("NOTE: worlds =", 12,
      "-> 'evaluated' for frontier_is_complete_to_size =",
      rep["invariant_worlds_evaluated"]["frontier_is_complete_to_size"])
