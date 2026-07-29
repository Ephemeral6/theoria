"""Adversarial tripwire pytest plugin: raise if the REAL check_determinism is entered in-process."""
import os
import worldgen.build as _b
_LOG = os.environ.get("V16_TRIP_LOG", "v16_trip.log")
_orig = _b.check_determinism
def _tripped(*a, **k):
    with open(_LOG, "a", encoding="utf-8") as h:
        h.write("TRIPPED args=%r\n" % (a,))
    raise AssertionError("V16 ADVERSARIAL TRIPWIRE: build.check_determinism was called in-process")
_b.check_determinism = _tripped
