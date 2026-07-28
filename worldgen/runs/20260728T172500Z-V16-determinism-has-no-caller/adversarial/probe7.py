"""Is the 'independent oracle' measuring nondeterminism, or seed-dependence?
Rerun it with the SAME seed on both sides."""
import os, sys, tempfile
sys.path.insert(0, os.path.abspath("."))
from worldgen.tests import determinism_sandbox as ds
tmp = tempfile.mkdtemp(prefix="v16-adv7-")
for inj in ds.INJECTIONS:
    root = ds.make_sandbox(os.path.join(tmp, inj.name), inj.name)
    same = ds.divergent_artefacts(root, inj.world,
                                  os.path.join(tmp, inj.name + "-s1"),
                                  os.path.join(tmp, inj.name + "-s2"),
                                  seeds=("1", "1"))
    print("%-16s guaranteed=%-5s  same-seed(1,1) differing=%s"
          % (inj.name, inj.guaranteed, same), flush=True)
