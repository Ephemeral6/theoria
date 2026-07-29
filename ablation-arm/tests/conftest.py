"""Put the arm on `sys.path`, once, for every test module.

`_bootstrap` does the same for the upstream trees, and importing it here rather
than in each test file keeps the import order identical to the one the arm runs
under -- a test suite that assembles a different path than the program is
testing a different program.
"""

from __future__ import annotations

import os
import sys

ARM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ARM)
for path in (ARM, REPO):
    if path not in sys.path:
        sys.path.insert(0, path)

import _bootstrap                                                  # noqa: F401,E402
