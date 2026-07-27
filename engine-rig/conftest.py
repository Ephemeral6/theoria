"""Make `common/`, `engines/`, `fixtures/`, `tools/` importable from the tests.

The engine-rig directory itself is not an importable package name (it contains a
hyphen), so tests import `common.*` / `engines.*` / `fixtures.*` with this
directory on sys.path.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
