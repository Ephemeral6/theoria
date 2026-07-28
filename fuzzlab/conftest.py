"""Test-time setup: import path, and how hard hypothesis is allowed to try.

Three profiles, because the same battery is run at three different budgets and
the number of examples is the only thing that changes between them:

    fast   25 examples   -- the edit/run loop
    ci    100 examples   -- the default, what `verify.sh` runs
    deep 1000 examples   -- an overnight sweep

`FUZZLAB_PROFILE` selects one.  `derandomize=True` everywhere: a property suite
whose failures depend on the wall clock cannot be replayed from a seed table,
and a seed table nobody can replay is a decoration.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from hypothesis import HealthCheck, Verbosity, settings  # noqa: E402

import fuzzlab.rig  # noqa: F401,E402  (puts engine-rig on sys.path)

_COMMON = dict(
    derandomize=True,
    deadline=None,                      # world generation dominates; wall-clock
                                        # deadlines would flake on a loaded box
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

settings.register_profile("fast", max_examples=25, **_COMMON)
settings.register_profile("ci", max_examples=100, **_COMMON)
settings.register_profile("deep", max_examples=1000, verbosity=Verbosity.normal,
                          **_COMMON)

settings.load_profile(os.environ.get("FUZZLAB_PROFILE", "ci"))
