"""Path bootstrap for A2.

Four roots go on `sys.path` and nothing else:

  `engine-rig`         the six engines and `common.candidates`
  `theory-compiler/src` the frozen v0.1 parser
  `cold-start-a0`      the A0 track's compile backends and certify layer, which
                       INC-004's ruling lets A2 reuse rather than re-derive
  here                 A2's own `a2world` / `a2pipeline` packages

**A2 imports from `cold-start-a0` and never writes to it.**  That directory
belongs to the theory-compiler track (CLAUDE.md) and this track is read-only
there.  Two consequences are designed for rather than hoped for:

* every A2 package is named distinctly (`a2world`, `a2pipeline`) so that nothing
  here can shadow `world` / `pipeline` / `compile` / `certify` upstream, whatever
  order the two roots end up in;
* `cold-start-a0`'s own `plan_stage.run_plan` writes its report into
  *its* `artifacts/`, so A2 does not call it — `a2pipeline.plan` drives
  `fd_adapter` directly.  Reuse stops exactly where it would mean writing into
  another track's territory.

The upstream files A2 depends on are hashed into `artifacts/upstream_pin.json`
on every run, because that directory has work in flight from another session and
a silent change there would otherwise silently change A2's results.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

ENGINE_RIG = os.path.join(REPO, "engine-rig")
THEORY_COMPILER = os.path.join(REPO, "theory-compiler", "src")
COLD_START_A0 = os.path.join(REPO, "cold-start-a0")

for path in (ENGINE_RIG, THEORY_COMPILER, COLD_START_A0, HERE):
    if path not in sys.path:
        sys.path.insert(0, path)


def artifacts_dir() -> str:
    path = os.path.join(HERE, "artifacts")
    os.makedirs(path, exist_ok=True)
    return path


def artifact(name: str) -> str:
    return os.path.join(artifacts_dir(), name)
