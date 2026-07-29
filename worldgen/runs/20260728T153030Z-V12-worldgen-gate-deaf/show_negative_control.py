"""Print the negative control's actual transcripts, so the red is on the record.

`python worldgen/runs/20260728T153030Z-V12-worldgen-gate-deaf/show_negative_control.py`

The pytest suite asserts these exit codes; this prints what the asserts saw, for
a reader who wants the evidence rather than a green dot. Writes nothing outside
a temporary directory.
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, ROOT)

from worldgen.tests import test_verify_qc_gate as nc  # noqa: E402

CASES = (
    ("POSITIVE CONTROL — the pinned miss (stub exits 1, as run_qc does)",
     lambda a: nc._writer(a, nc.PINNED_VERDICT, 1), None, 0),
    ("a world that used to pass L1 starts raising",
     lambda a: nc._writer(a, _worse(), 1), None, 1),
    ("the stage reports success and writes a different verdict",
     lambda a: nc._writer(a, _lying(), 0), None, 1),
    ("the red quietly went green — the pin is now a lie",
     lambda a: nc._writer(a, _better(), 0), None, 1),
    ("the failing world was dropped from the sample",
     lambda a: nc._writer(a, _shrunk(), 0), None, 1),
    ("the stage died before writing (the pre-V12 blind spot)",
     lambda a: nc._dead("ImportError: no module named pipeline\n"), None, 1),
    ("the stage died, and a CORRECT artifact from an earlier run is on disk",
     lambda a: nc._dead("death after reading\n"), nc.PINNED_VERDICT, 1),
)


def _copy():
    return json.loads(json.dumps(nc.PINNED_VERDICT))


def _worse():
    d = _copy()
    d["worlds"]["w-good"]["verdict"]["L1_liveness"] = False
    return d


def _lying():
    d = _copy()
    d["family_verdict"]["pass"] = True
    d["family_verdict"]["all_L1"] = True
    return d


def _better():
    d = _copy()
    d["worlds"]["w-raises"]["verdict"] = {"L1_liveness": True, "L3a_replay": True}
    return d


def _shrunk():
    d = _copy()
    del d["worlds"]["w-raises"]
    return d


def main():
    bad = 0
    for title, command, on_disk, expected in CASES:
        with tempfile.TemporaryDirectory() as tmp:
            from pathlib import Path
            proc = nc._run(Path(tmp), command, payload_on_disk=on_disk)
        print("=" * 78)
        print("CASE: %s" % title)
        print("expected exit %d" % expected)
        print("-" * 78)
        print(proc.stdout.rstrip())
        if proc.stderr.strip():
            print("--- stderr ---")
            print(proc.stderr.rstrip())
        print("-" * 78)
        verdict = "OK" if proc.returncode == expected else "NEGATIVE CONTROL FAILED"
        if proc.returncode != expected:
            bad += 1
        print("ACTUAL EXIT: %d   [%s]" % (proc.returncode, verdict))
        print()
    print("=" * 78)
    print("%d case(s) behaved as required, %d did not." % (len(CASES) - bad, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
