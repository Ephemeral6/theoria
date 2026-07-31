"""battery — the territory gate. `python -m battery.verify`

`monitor/gates.py` treats `verify.py` as a territory's canonical gate and falls
back to a bare pytest run when there is none. The battery had no gate, so its
freeze would have been checked by nothing: S13's finding was that a skipped gate
and a passing gate look identical from the outside.

Three gates, in order of what they protect:

  1. **the freeze** — `BATTERY_V1.md` still describes the tree it was written
     against (`battery/freeze.py`).
  2. **the suite** — `battery/tests`, which is what the freeze's determinism and
     anti-gaming claims rest on. A deselected or uncollected test is reported as
     loudly as a failing one: the cheapest way to disarm this gate is an
     `addopts` line, not a broken assertion.
  3. **the readings** — the seven artefacts. Drift here is *reported and
     tolerated*: Phase 4 exists to recompute against inputs the battery has
     never read, so a gate that failed on new numbers would fail by
     construction. Silence would be the wrong answer too, hence the report.

Exit 0 = the instrument matches its record. Exit 1 = something to read before
merging.
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _say(text):
    """Print without dying on a console that cannot encode the bytes.

    A gate that raises UnicodeEncodeError while reporting a failure shows the
    operator a traceback instead of the reason, on a Windows console whose code
    page is not UTF-8. It failed closed, but it failed illegibly.
    """
    enc = sys.stdout.encoding or "utf-8"
    sys.stdout.write(text.encode(enc, "replace").decode(enc, "replace") + "\n")


def gate_freeze():
    from battery import freeze
    fails = freeze.check()
    if fails:
        _say("FAIL  freeze: the tree no longer matches BATTERY_V1.md")
        for f in fails:
            _say("      - " + f.replace("\n", "\n        "))
        return False
    _say("ok    freeze: %d code + %d docs + %d suite + %d freeze files, the "
         "pre-registration and the pile cut all match BATTERY_V1.md"
         % (len(freeze.CODE), len(freeze.DOCS), len(freeze.SUITE),
            len(freeze.FREEZE)))
    return True


def gate_tests():
    out = subprocess.run([sys.executable, "-m", "pytest", "battery/tests", "-q"],
                         cwd=ROOT, capture_output=True)
    text = (out.stdout + out.stderr).decode("utf-8", "replace")
    tail = text.strip().splitlines()[-1] if text.strip() else "(no output)"
    if out.returncode != 0:
        _say("FAIL  tests: battery/tests")
        for ln in text.strip().splitlines()[-15:]:
            _say("      " + ln)
        return False
    # A green run that quietly skipped the objecting tests is not a green run.
    muted = [w for w in ("deselected", "error") if w in tail]
    if muted:
        _say("FAIL  tests: %s — tests were %s rather than run. The suite is "
             "half this gate; silencing part of it is not passing it."
             % (tail, " and ".join(muted)))
        return False
    passed = re.search(r"(\d+) passed", tail)
    if not passed or int(passed.group(1)) < 200:
        _say("FAIL  tests: %s — far fewer tests ran than this suite has. "
             "Collection was cut short somewhere." % tail)
        return False
    _say("ok    tests: " + tail)
    return True


def gate_readings():
    from battery import freeze
    drift = freeze.readings_drift()
    if drift:
        _say("note  readings: %d of %d artefacts differ from BATTERY_V1.md — "
             "%s" % (len(drift), len(freeze.READINGS), ", ".join(drift)))
        _say("      Not a failure: artefacts are readings, and a recompute is "
             "supposed to change them. Record the new values in a new freeze "
             "version before publishing them.")
    else:
        _say("ok    readings: %d artefacts match the values recorded at freeze "
             "time" % len(freeze.READINGS))
    return True


def main():
    ok = True
    for gate in (gate_freeze, gate_tests, gate_readings):
        ok = gate() and ok
    _say("VERIFY " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
