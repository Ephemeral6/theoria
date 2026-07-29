"""Import roots for the ablation arm.  Nothing here is ever written to.

This arm imports from four trees it does not own — `engine-rig` (the engines and
the candidates contract), `theory-compiler/src` (the frozen v0.1 parser),
`cold-start-a0` (the generators and the cheap certify layer) and `cold-start-a2`
(the second offline world).  The pattern is `cold-start-a2/_bootstrap.py`'s,
copied deliberately, together with the three rules that make it safe:

* **package names never shadow.** Everything this arm owns is under `ablcore`,
  `arms` or `tests`.  Nothing here is called `world`, `pipeline`, `compile`,
  `certify`, `a2world` or `a2pipeline`, whatever order the roots end up in.
* **library functions only, never a `main()`.** Every staged module upstream
  computes its output path from its own `__file__` and writes into its own
  `artifacts/`; `cold-start-a0/pipeline/plan_stage.py::run_plan` writes
  unconditionally on both the SAT and the UNSAT branch.  Those drivers are
  rewritten here, not called.
* **`a2pipeline` is never imported.** Its modules pin `ROOT` to their own
  directory, so calling one writes into `cold-start-a2/artifacts/`.  Only
  `a2world` — the world and its trace reader — is imported from that tree.
  The two functions this arm needs out of `a2pipeline/compile_a2.py` are
  copied into `ablcore/compile_abl.py` with the credit stated there, which is
  exactly what A2 itself did to A0's `recovered_region` and for the same reason.

`tests/test_readonly.py` checks all three by hashing the upstream trees around a
full run, so none of the above is on the honour system.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

ENGINE_RIG = os.path.join(REPO, "engine-rig")
THEORY_COMPILER = os.path.join(REPO, "theory-compiler", "src")
COLD_START_A0 = os.path.join(REPO, "cold-start-a0")
COLD_START_A2 = os.path.join(REPO, "cold-start-a2")

UPSTREAM_ROOTS = (ENGINE_RIG, THEORY_COMPILER, COLD_START_A0, COLD_START_A2)

# The repo root, so that `proxy.ledger` and `proxy.canon` are importable for the
# ledger-format alignment.  `proxy/` is imported and never modified, like the
# rest; its writer is used exactly as `theoria-arm` uses it, against a path
# inside this arm's own run directory.
for _path in UPSTREAM_ROOTS + (REPO, HERE):
    if _path not in sys.path:
        sys.path.insert(0, _path)


def artifact(name: str) -> str:
    """A path under this arm's own `artifacts/`.  The directory is not created."""
    return os.path.join(HERE, "artifacts", name)


def run_dir(slug: str) -> str:
    return os.path.join(HERE, "runs", slug)
