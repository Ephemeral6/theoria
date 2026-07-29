"""Attack: is the committed weakening_table cell unseeded_rng x size_only stable?"""
import os, shutil, sys, tempfile
sys.path.insert(0, os.path.abspath("."))
from worldgen.tests import determinism_sandbox as ds
results=[]
for trial in range(10):
    root = tempfile.mkdtemp(prefix="v16-adv4-")
    try:
        ds.make_sandbox(root, "unseeded_rng", "size_only")
        p = ds.run_gate(root, "t1-walk-maze")
        out = ds.text(p)
        red = p.returncode != 0 and ds.RED_BANNER in out
        results.append("RED" if red else "MISSED")
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print(trial, results[-1], flush=True)
print("summary:", {v: results.count(v) for v in set(results)})
