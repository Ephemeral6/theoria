"""Seed sweep for mechanism_order: how often does the gate MISS, and does it ever
go non-zero for a reason other than the determinism diff?"""
import os, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.abspath("."))
from worldgen.tests import determinism_sandbox as ds
tally = {"RED-diff": 0, "MISSED": 0, "other-nonzero": 0}
root = ds.make_sandbox(tempfile.mkdtemp(prefix="v16-adv6-"), "mechanism_order")
for s in range(1, 31):
    env = ds._env(root, str(s))
    p = subprocess.run([sys.executable, "-m", "worldgen.build", "--check", "t3-latch-maze"],
                       cwd=root, env=env, capture_output=True)
    out = ds.text(p)
    named = [l for l in out.splitlines() if "differs between runs" in l]
    if p.returncode == 0:
        k = "MISSED"
    elif ds.RED_BANNER in out and named:
        k = "RED-diff"
    else:
        k = "other-nonzero"
    tally[k] += 1
    print("seed=%-4d %s" % (s, k), flush=True)
print(tally)
