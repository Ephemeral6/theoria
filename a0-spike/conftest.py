"""Put a0-spike and engine-rig on sys.path for the tests."""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ENGINES = os.path.join(os.path.dirname(_HERE), "engine-rig")
for path in (_HERE, _ENGINES):
    if path not in sys.path:
        sys.path.insert(0, path)
