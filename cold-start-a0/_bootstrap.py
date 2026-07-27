"""Path bootstrap: make the two upstream tracks importable as libraries.

`engine-rig` expects to be run with its own directory as the import root
(`from engines import ...`, `from common import ...`); `theory-compiler` ships a
`src/` layout.  Neither is installed as a package here, and neither may be
modified, so this module puts both roots on `sys.path` and nothing else.

Import it before importing anything from either track.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

ENGINE_RIG = os.path.join(REPO, "engine-rig")
THEORY_COMPILER = os.path.join(REPO, "theory-compiler", "src")

for path in (ENGINE_RIG, THEORY_COMPILER, HERE):
    if path not in sys.path:
        sys.path.insert(0, path)


def artifacts_dir() -> str:
    path = os.path.join(HERE, "artifacts")
    os.makedirs(path, exist_ok=True)
    return path


def artifact(name: str) -> str:
    return os.path.join(artifacts_dir(), name)
