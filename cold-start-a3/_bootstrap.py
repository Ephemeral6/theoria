"""Path bootstrap for A3.

Four roots go on `sys.path` and nothing else:

  `engine-rig`          the engines and `common.candidates`
  `theory-compiler/src` the frozen v0.2 parser
  `cold-start-a0`       the A0 track's compile backends and certify layer
  here                  A3's own `a3world` / `a3pipeline` packages

**A3 writes no generator and no engine.**  The four backends and the cheap
certify layer are `cold-start-a0`'s, imported unmodified; the engines are
`engine-rig`'s; the parser is the frozen contract's.  A3 supplies a world, a
cost meter, a problem builder and the drivers that join them — nothing that
could flatter the instrument it is measuring with.

**`cold-start-a2` is deliberately *not* on this path.**  A2 is a sibling
experiment, not a library, and importing it would mean a third module named
`_bootstrap` racing the two that already exist plus a live coupling to another
run's `artifacts/`.  Where A2 wrote a workaround A3 also needs — the PDDL
addressability patch (A2's D-A2-006) and the UTF-8 Lean reader (D-A2-007) —
A3 re-derives it in its own tree and says so, which is the same call A2 made
about A0's `plan_stage` and for the same reason.

**A3 imports from `cold-start-a0` and never writes to it.**  That directory
belongs to the theory-compiler track (CLAUDE.md).  Two consequences are
designed for rather than hoped for:

* every A3 package is named distinctly (`a3world`, `a3pipeline`) so nothing
  here can shadow `world` / `pipeline` / `compile` / `certify` upstream,
  whatever order the roots end up in;
* every upstream `main()` and several upstream stage drivers write their
  reports into *their own* `artifacts/`, so A3 calls none of them.  It calls
  the pure functions and drives them from here.  Reuse stops exactly where it
  would mean writing into another track's territory, and
  `tools/verify_readonly.py` checks that by hashing the trees before and after
  a full run.

The upstream files A3 depends on are hashed into `artifacts/upstream_pin.json`
on every run: two other sessions work this repo concurrently, and a silent
change upstream would otherwise silently change A3's numbers.
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


def theory_dir() -> str:
    return os.path.join(HERE, "theory")
