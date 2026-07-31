import os, sys, tempfile
sys.path.insert(0, os.path.abspath("."))
from worldgen.tests import determinism_sandbox as ds
tmp = tempfile.mkdtemp(prefix="v16-adv2-")
for inj in ds.INJECTIONS:
    root = ds.make_sandbox(os.path.join(tmp, inj.name), inj.name)
    p = ds.run_gate(root, inj.world)
    out = ds.text(p)
    print("="*70)
    print("INJECTION", inj.name, "world", inj.world, "rc", p.returncode)
    print(out[-1800:])
