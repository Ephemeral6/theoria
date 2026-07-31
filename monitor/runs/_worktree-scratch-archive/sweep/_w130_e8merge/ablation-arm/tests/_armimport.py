"""Load a module this arm owns, by path, whatever else is on `sys.path`.

`_bootstrap` prepends four upstream roots and only then this arm, so for any
top-level module name the arm shares with an upstream tree, a plain
``import <name>`` silently returns the *upstream* one. That is not hypothetical:
S14 (127edab, 2026-07-28T23:38) added a top-level ``verify.py`` to eleven
territories, and from that moment ``ablation-arm/tests/test_verify.py`` was
exercising ``cold-start-a2``'s gate instead of this arm's. It had passed 75
minutes earlier.

Reordering `sys.path` would fix it too, and would be worse: the arm imports the
upstream trees precisely to run against *their* modules, and `_bootstrap`'s order
is the order the program itself runs under. So the narrow thing is done here —
the test says which tree it means — and `test_no_shadow.py` fails when a new
collision appears rather than letting the next one go unnoticed for 75 minutes.
"""

from __future__ import annotations

import importlib.util
import os
import sys

ARM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def arm_module(name: str):
    """Import ``<ARM>/<name>.py`` under the alias ``ablation_arm.<name>``.

    The alias keeps `sys.modules` honest: nothing else in the process gets a
    ``verify`` that is this arm's, and nothing here gets one that is not.
    """
    path = os.path.join(ARM, name + ".py")
    if not os.path.isfile(path):
        raise ImportError(f"{name}: this arm has no top-level {name}.py at {path}")
    alias = "ablation_arm." + name
    cached = sys.modules.get(alias)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(alias, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"{name}: no loader for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        del sys.modules[alias]
        raise
    return module
