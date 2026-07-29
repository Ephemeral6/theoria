"""Put `release/` on the path so the tests import the scripts, not a copy."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
