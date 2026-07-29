"""Resource 2 of the OPS-R proposal: physical memory and the concurrency budget.

**A proposal, not a shipped check** — same standing as
`board_log_invariants.py`, and for the same reason: the resource is `monitor`'s.
Reads and never writes.

    python concurrency_invariants.py

## Why counting the registry is not counting the resource

`monitor/reflex.py` gates spawning on two numbers: free RAM must be at least
`MIN_FREE_GB`, and live workers must be under `WORKER_MAX`. The second number
comes from walking `registry.json` for `W-`-prefixed entries and asking
`schtasks` about each. A worker started by `monitor/worker.cmd` is in neither —
it is a `start`ed console running `claude -p`, with no registry entry and no
scheduled task — so it consumes RAM and a concurrency slot while being invisible
to the thing that decides whether there is room for another. The machine has
already died once under about twenty concurrent sessions.

That is not "the gate was bypassed". `worker.cmd` was introduced *deliberately*,
after that crash, to add capacity. The accurate statement is the reviewer's:
**nobody is guarding the total.** A gate whose count does not cover every
consumer of the resource is a decoration, and the repair is to make the count
read the resource — actual processes — rather than a registry of intentions.

## The invariant

    every process that consumes an agent's worth of RAM is inside the count
    the admission gate uses

Operationalised as: the number of live agent processes must not exceed
`WORKER_MAX`, and free RAM must not be below `MIN_FREE_GB` — both measured from
the operating system, neither from a file the spawner maintains.

## The negative control

`_planted_overrun()` feeds a synthetic process table over the cap and a synthetic
free-RAM figure under the floor, and asserts both fire. A checker that read a
healthy machine and printed "ok" would otherwise be indistinguishable from one
that always prints "ok" — which is the whole subject of this proposal.
"""

import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, os.pardir, os.pardir))
REFLEX = os.path.join(REPO, "monitor", "reflex.py")

#: Read out of reflex.py rather than duplicated, so the invariant cannot drift
#: away from the gate it is checking. The proposal quoted WORKER_MAX=2; the tree
#: now says 7, and a second hard-coded copy here would have gone stale the same
#: way and been believed.
DEFAULTS = {"WORKER_MAX": 7, "MIN_FREE_GB": 8.0}


def gate_constants(path: str = REFLEX) -> Dict[str, Any]:
    out = dict(DEFAULTS)
    out["source"] = "defaults (reflex.py unreadable)"
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return out
    for name in ("WORKER_MAX", "MIN_FREE_GB"):
        match = re.search(r"^%s\s*=\s*([0-9.]+)" % name, text, re.MULTILINE)
        if match:
            out[name] = float(match.group(1)) if "." in match.group(1) \
                else int(match.group(1))
    out["source"] = os.path.relpath(path, REPO).replace(os.sep, "/")
    return out


def agent_processes() -> Dict[str, Any]:
    """Count what is actually running, not what a registry says should be.

    Best effort by construction, and it says so: process discovery differs by
    platform and by how a session was started. `counted: false` is reported when
    the probe could not run, because a count that did not happen must not read
    as a count of zero — that is the same failure mode as the gate this proposal
    is about.
    """
    if os.name == "nt":
        command = ["tasklist", "/FO", "CSV", "/NH"]
    else:
        command = ["ps", "-eo", "comm="]
    try:
        proc = subprocess.run(command, capture_output=True, timeout=30)
    except Exception as exc:                                   # noqa: BLE001
        return {"counted": False, "why": "%s" % type(exc).__name__, "names": []}
    if proc.returncode != 0:
        return {"counted": False, "why": "exit %d" % proc.returncode, "names": []}

    text = proc.stdout.decode("utf-8", "replace")
    names: List[str] = []
    for line in text.splitlines():
        line = line.strip().strip('"')
        if not line:
            continue
        name = line.split('","')[0] if os.name == "nt" else line
        if re.search(r"\bclaude", name, re.IGNORECASE):
            names.append(name)
    return {"counted": True, "names": names, "live": len(names)}


def free_gb() -> Optional[float]:
    """Free physical memory, or `None` — never a guess.

    Two probes on Windows because `wmic` is **removed** on Windows 11, which is
    the machine this ran on: the first attempt reported `NOT MEASURED`, and
    `judge` correctly refused to call that a pass. Worth keeping the failure in
    the record, because "the probe silently returned nothing and the gate read
    it as room to spawn" is a smaller version of the bug this file is about.
    """
    try:
        if os.name == "nt":
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command",
                 "(Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory"],
                capture_output=True, timeout=60)
            match = re.search(r"(\d+)", proc.stdout.decode("utf-8", "replace"))
            if match:
                return round(int(match.group(1)) / 1024 / 1024, 2)
            proc = subprocess.run(
                ["wmic", "OS", "get", "FreePhysicalMemory", "/Value"],
                capture_output=True, timeout=30)
            match = re.search(r"FreePhysicalMemory=(\d+)",
                              proc.stdout.decode("utf-8", "replace"))
            return round(int(match.group(1)) / 1024 / 1024, 2) if match else None
        with open("/proc/meminfo", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("MemAvailable:"):
                    return round(int(line.split()[1]) / 1024 / 1024, 2)
    except Exception:                                          # noqa: BLE001
        return None
    return None


def judge(live: Optional[int], free: Optional[float],
          gate: Dict[str, Any]) -> Dict[str, Any]:
    """The predicate, separated from the probes so the control can drive it."""
    violations: List[str] = []
    if live is not None and live > gate["WORKER_MAX"]:
        violations.append("live agent processes %d exceed WORKER_MAX %s"
                          % (live, gate["WORKER_MAX"]))
    if free is not None and free < gate["MIN_FREE_GB"]:
        violations.append("free RAM %.1f GB is below MIN_FREE_GB %s"
                          % (free, gate["MIN_FREE_GB"]))
    unmeasured = [n for n, v in (("live", live), ("free_gb", free)) if v is None]
    return {"violations": violations, "unmeasured": unmeasured,
            # `clean` requires the measurement to have happened. An unmeasured
            # resource is not a resource within budget.
            "clean": not violations and not unmeasured}


def _planted_overrun() -> Dict[str, Any]:
    return judge(live=99, free=0.5, gate={"WORKER_MAX": 7, "MIN_FREE_GB": 8.0})


def _planted_unmeasured() -> Dict[str, Any]:
    return judge(live=None, free=None, gate={"WORKER_MAX": 7, "MIN_FREE_GB": 8.0})


def main() -> int:
    over = _planted_overrun()
    blind = _planted_unmeasured()
    ok = len(over["violations"]) == 2 and blind["clean"] is False
    print("== negative controls: %s" % ("both go red as they must" if ok
                                        else "DID NOT FIRE -- checker is broken"))
    if not ok:
        print("   over=%r blind=%r" % (over, blind))
        return 2

    gate = gate_constants()
    procs = agent_processes()
    free = free_gb()
    live = procs["live"] if procs["counted"] else None
    report = judge(live, free, gate)

    print("== live machine")
    print("   gate constants from %s: WORKER_MAX=%s MIN_FREE_GB=%s"
          % (gate["source"], gate["WORKER_MAX"], gate["MIN_FREE_GB"]))
    print("   agent processes: %s"
          % (live if procs["counted"] else "NOT COUNTED (%s)" % procs["why"]))
    print("   free RAM: %s GB" % (free if free is not None else "NOT MEASURED"))
    for line in report["violations"]:
        print("   VIOLATION: %s" % line)
    for name in report["unmeasured"]:
        print("   UNMEASURED: %s -- not a pass" % name)
    print("   %s" % ("within budget" if report["clean"] else "OVER OR UNKNOWN"))
    return 0 if report["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
