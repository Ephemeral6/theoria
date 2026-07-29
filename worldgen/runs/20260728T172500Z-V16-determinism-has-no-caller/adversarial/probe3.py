"""Attack: is mechanism_order's red an artefact of PARENT_SEED=1?"""
import os, subprocess, sys, tempfile
sys.path.insert(0, os.path.abspath("."))
from worldgen.tests import determinism_sandbox as ds

tmp = tempfile.mkdtemp(prefix="v16-adv3-")
SEEDS = ["1", "4", "0", "2", "6", "999", "13", "271827"]
for seed in SEEDS:
    root = ds.make_sandbox(os.path.join(tmp, "mo-%s" % seed), "mechanism_order")
    env = ds._env(root, seed)
    p = subprocess.run([sys.executable, "-m", "worldgen.build", "--check", "t3-latch-maze"],
                       cwd=root, env=env, capture_output=True)
    out = ds.text(p)
    # what set order did the parent see?
    q = subprocess.run([sys.executable, "-c",
        "d={'switch_door':1,'count_lock':2,'consumable':3};print('|'.join(set(d)))"],
        cwd=root, env=env, capture_output=True)
    print("seed=%-8s order=%-45s rc=%d red=%-5s green=%s"
          % (seed, q.stdout.decode().strip(), p.returncode,
             ds.RED_BANNER in out, ds.GREEN_BANNER in out))
