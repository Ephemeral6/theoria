"""Path bootstrap for the Theoria arm.

Four roots go on `sys.path` and nothing else:

  `engine-rig`          the eight engines and `common.candidates`
  `theory-compiler/src` the parser and the four generators
  repo root             `proxy` (the double proxy, used as a library)
  here                  this arm's own packages

**This arm imports from three other tracks and writes to none of them.** The
directories `engine-rig/`, `theory-compiler/` and `proxy/` are read-only from
here (CLAUDE.md's territory rule), and `arc-recon/` likewise. Every artefact
this arm produces lands under `theoria-arm/`.

Three consequences are designed for rather than hoped for:

* package names are distinct (`harness`, `world`, `inner`) and this directory
  goes on `sys.path` **last**, so nothing here can shadow an upstream module
  whatever order the roots end up in;
* `proxy` is imported as a package from the repo root rather than copied, so
  the ledger this arm writes is produced by the frozen writer -- the same
  bytes, the same redaction, the same append-only guarantee;
* the upstream files this arm depends on are hashed into the run manifest,
  because two other Claude Code sessions have work in flight in this repo and a
  silent change upstream would otherwise silently change this arm's results.
"""

import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

ENGINE_RIG = os.path.join(REPO, "engine-rig")
THEORY_COMPILER = os.path.join(REPO, "theory-compiler", "src")

# The arm's own root goes on last so an upstream name always wins.
for path in (HERE, THEORY_COMPILER, ENGINE_RIG, REPO):
    if path not in sys.path:
        sys.path.insert(0, path)


#: The upstream files whose behaviour this arm's results depend on. Hashed into
#: every run manifest. Adding a file here is cheap; noticing a silent change
#: after the fact is not.
UPSTREAM_PINS = (
    "proxy/ledger.py",
    "proxy/env_proxy.py",
    "proxy/model_proxy.py",
    "proxy/forward.py",
    "proxy/guard.py",
    "proxy/redact.py",
    "proxy/cost.py",
    "proxy/pricing/pricing_v1.json",
    "proxy/LEDGER_FORMAT.md",
    "arc-recon/data/piles.json",
    "engine-rig/engines/mdl_segmenter/__init__.py",
    "engine-rig/engines/cegis_miner/__init__.py",
    "engine-rig/engines/zero_space/__init__.py",
    "engine-rig/engines/probe_frontier/__init__.py",
    "engine-rig/common/candidates.py",
    "engine-rig/tools/validate_candidates.py",
    "theory-compiler/src/theory_compiler/parser/theory_parser.py",
    "theory-compiler/src/theory_compiler/generators/gen_python.py",
    "theory-compiler/src/theory_compiler/generators/gen_markdown.py",
    "theory-compiler/src/theory_compiler/generators/gen_pddl.py",
    "theory-compiler/src/theory_compiler/generators/gen_lean.py",
    "CONTRACTS/candidates_schema.md",
)


def upstream_pin() -> dict:
    """sha256 of every upstream file this arm leans on, plus this arm's own
    sources. A run that cannot be reproduced should at least say why."""
    pins = {}
    for rel in UPSTREAM_PINS:
        path = os.path.join(REPO, rel)
        try:
            with open(path, "rb") as fh:
                pins[rel] = hashlib.sha256(fh.read()).hexdigest()
        except OSError:
            pins[rel] = None
    return pins


def arm_version() -> dict:
    """A hash over this arm's own sources, in the shape proxy.runner uses.

    The two skip tests are substring tests, and they are applied to the path
    **below** `HERE` rather than to the absolute path. That is a correction:
    applied to the absolute path, an ancestor directory decides the answer.
    `.worktrees/runs-cleanup/theoria-arm` -- a perfectly ordinary worktree
    under CLAUDE.md's naming rule -- contains `\\runs`, so every file was
    skipped and the function returned `files: 0` and the sha256 of the empty
    string. A run made there would record an arm version that matches nothing
    and cannot be made to match anything.

    The tests themselves are left as substring tests, so `runsim/` and
    `__pycache__x/` are still skipped. Changing that would change the hash of
    any tree containing such a directory; no tree in this arm's history does
    (`git log --all --full-history --name-only`), and the same rule is
    reimplemented over git objects in `armtools/armversion.py`, so every hash
    ever recorded still reconstructs.
    """
    digests = {}
    for root, _dirs, names in os.walk(HERE):
        below = root[len(HERE):]
        if "__pycache__" in below or os.sep + "runs" in below:
            continue
        for name in sorted(names):
            if not name.endswith(".py"):
                continue
            path = os.path.join(root, name)
            with open(path, "rb") as fh:
                digests[os.path.relpath(path, HERE).replace(os.sep, "/")] = \
                    hashlib.sha256(fh.read()).hexdigest()
    blob = "".join("%s=%s\n" % kv for kv in sorted(digests.items()))
    return {"files": len(digests),
            "sha256": hashlib.sha256(blob.encode("utf-8")).hexdigest()}


def path(*parts: str) -> str:
    return os.path.join(HERE, *parts)
