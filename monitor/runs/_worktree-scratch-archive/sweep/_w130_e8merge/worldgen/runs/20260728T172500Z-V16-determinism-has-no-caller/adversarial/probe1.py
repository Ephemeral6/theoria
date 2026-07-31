"""Probe: does the sandbox subprocess import the sandbox copy? Where does the red come from?"""
import os, subprocess, sys, tempfile
sys.path.insert(0, os.path.abspath("."))
from worldgen.tests import determinism_sandbox as ds

tmp = tempfile.mkdtemp(prefix="v16-adv-")
root = ds.make_sandbox(os.path.join(tmp, "clean"))
env = ds._env(root)
p = subprocess.run([sys.executable, "-c",
    "import worldgen.build as b, sys; print('BUILD FILE:', b.__file__); print('OUT:', b.OUT); print('sys.path[0]:', sys.path[0])"],
    cwd=root, env=env, capture_output=True)
print(ds.text(p))
