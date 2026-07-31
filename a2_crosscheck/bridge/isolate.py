"""Import two tracks' code into one process without letting them collide.

Both A0 tracks call their world package `world`, both call their pipeline
`pipeline`, and both expect their own directory on `sys.path`. Import them
naively in one process and the second `import world.…` silently resolves inside
the first track's package -- or, if the module names happen to differ, fails
outright, which is the luckier half of the same bug.

So a track is loaded inside a window in which only that track's roots are on the
path and the shadowed top-level names are absent from `sys.modules`. Whatever the
load creates is then re-registered under a private alias and the window closes,
leaving `sys.modules` exactly as it was found. The returned module object keeps
its siblings alive through its own globals, so it goes on working afterwards.

This is bookkeeping, not cleverness, and it is confined to this file on purpose:
everything else in `crosscheck/` should be able to say `import` and mean it.
"""

import importlib
import sys
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Sequence

# Top-level names both tracks define. Anything here is purged for the duration
# of a load and restored afterwards.
SHADOWED = ("world", "pipeline", "theory", "compile", "certify", "prime",
            "engines", "tests", "conftest")


def _snapshot(names: Iterable[str]) -> Dict[str, Any]:
    out = {}
    for key in list(sys.modules):
        for name in names:
            if key == name or key.startswith(name + "."):
                out[key] = sys.modules.pop(key)
                break
    return out


@contextmanager
def only(roots: Sequence[str], shadowed: Sequence[str] = SHADOWED):
    """A window in which `roots` lead the path and `shadowed` names are unbound."""
    saved_modules = _snapshot(shadowed)
    saved_path = list(sys.path)
    for root in reversed(list(roots)):
        sys.path.insert(0, root)
    created: Dict[str, Any] = {}
    try:
        yield created
    finally:
        for key in list(sys.modules):
            for name in shadowed:
                if key == name or key.startswith(name + "."):
                    created[key] = sys.modules.pop(key)
                    break
        sys.path[:] = saved_path
        sys.modules.update(saved_modules)


def load(roots: Sequence[str], dotted: str, alias_prefix: str) -> Any:
    """Import `dotted` with `roots` in front, then hide it under `alias_prefix`.

    The alias keeps the loaded tree reachable for debugging and stops a second
    load of the same track from paying the cost twice, without ever occupying the
    bare name that the other track also wants.
    """
    alias = alias_prefix + dotted
    if alias in sys.modules:
        return sys.modules[alias]
    with only(roots) as created:
        module = importlib.import_module(dotted)
    for key, value in created.items():
        sys.modules.setdefault(alias_prefix + key, value)
    sys.modules[alias] = module
    return module


def loaded_aliases(alias_prefix: str) -> List[str]:
    return sorted(k for k in sys.modules if k.startswith(alias_prefix))
