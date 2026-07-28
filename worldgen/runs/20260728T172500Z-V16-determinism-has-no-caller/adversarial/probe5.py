"""(1) which artefacts does mechanism_order actually move?
   (2) a crash-only defect: does it produce banner-without-named-artefact?"""
import os, shutil, sys, tempfile
sys.path.insert(0, os.path.abspath("."))
from worldgen.tests import determinism_sandbox as ds

tmp = tempfile.mkdtemp(prefix="v16-adv5-")

# (1)
root = ds.make_sandbox(os.path.join(tmp, "mo"), "mechanism_order")
d = ds.divergent_artefacts(root, "t3-latch-maze",
                           os.path.join(tmp, "a"), os.path.join(tmp, "b"))
print("mechanism_order differing artefacts:", d)
print("  -> raw_trace.jsonl moved?", "raw_trace.jsonl" in d)

# (2) crash-only defect: comparison build (at 271828) dies, parent (at 1) is fine.
CRASH = ds.Injection(
    "crash_at_271828", "t1-walk-maze", "adversarial: only the child build dies",
    [("core/explorer.py", ds._COVERAGE_ANCHOR,
      ds._COVERAGE_ANCHOR +
      '        "v16_crash": (_ for _ in ()).throw(RuntimeError("boom"))'
      ' if __import__("os").environ.get("PYTHONHASHSEED") == "271828" else 0,\n')],
    guaranteed=True)
ds.BY_NAME["crash_at_271828"] = CRASH
root2 = ds.make_sandbox(os.path.join(tmp, "crash"), "crash_at_271828")
p = ds.run_gate(root2, "t1-walk-maze")
out = ds.text(p)
named = [l.strip() for l in out.splitlines() if "differs between runs" in l]
print("crash-only: rc=%d banner=%s named=%r" % (p.returncode, ds.RED_BANNER in out, named))
print("tail:", out.strip().splitlines()[-6:])
