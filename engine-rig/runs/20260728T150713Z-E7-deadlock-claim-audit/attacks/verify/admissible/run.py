"""Independent verification driver for the E7 admissible-heuristic counterexamples.

Drives Fast Downward directly with an arbitrary --search string so the pattern
generator can be pinned, and parses FD's own counters out of the log.  Writes
nothing outside this directory.
"""

import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(HERE, "logs")
ATTACKS = os.path.abspath(os.path.join(HERE, "..", ".."))
RIG = os.path.abspath(os.path.join(ATTACKS, "..", "..", ".."))
DOMAIN = os.path.join(RIG, "fixtures", "data", "sokoban_domain.pddl")
FD = os.environ.get(
    "FAST_DOWNWARD",
    "C:/Users/user/Desktop/theoria/.worktrees/p13/engine-rig/.toolchain/downward/fast-downward.py",
)

_STAMP = r"^(?:\[t=[^\]]*\]\s*)?"
COUNTERS = {
    "expanded": re.compile(_STAMP + r"Expanded (\d+) state\(s\)\.", re.M),
    "generated": re.compile(_STAMP + r"Generated (\d+) state\(s\)\.", re.M),
    "evaluated": re.compile(_STAMP + r"Evaluated (\d+) state\(s\)\.", re.M),
    "reopened": re.compile(_STAMP + r"Reopened (\d+) state\(s\)\.", re.M),
    "dead_ends": re.compile(_STAMP + r"Dead ends: (\d+) state\(s\)\.", re.M),
    "expanded_until_last_jump": re.compile(
        _STAMP + r"Expanded until last jump: (\d+) state\(s\)\.", re.M),
    "reopened_until_last_jump": re.compile(
        _STAMP + r"Reopened until last jump: (\d+) state\(s\)\.", re.M),
    "evaluated_until_last_jump": re.compile(
        _STAMP + r"Evaluated until last jump: (\d+) state\(s\)\.", re.M),
}
RE_H = re.compile(_STAMP + r"Initial heuristic value for (\S+): (\S+)", re.M)
RE_PLAN = re.compile(_STAMP + r"Plan length: (\d+) step\(s\)\.", re.M)
RE_OPS = re.compile(r"^Translator operators: (\d+)", re.M)
RE_VARS = re.compile(r"^Translator variables: (\d+)", re.M)
RE_HC_ITER = re.compile(r"Hill climbing iterations: (\d+)")
RE_HC_PAT = re.compile(r"hill climbing pattern collection generator number of patterns: (\d+)")
RE_HC_SIZE = re.compile(r"hill climbing pattern collection generator total PDB size: (\d+)")
RE_CPDBS_PAT = re.compile(r"Canonical PDB heuristic number of patterns: (\d+)")
RE_CPDBS_SIZE = re.compile(r"Canonical PDB heuristic total PDB size: (\d+)")
RE_SYS_PAT = re.compile(r"systematic pattern collection generator number of patterns: (\d+)")


def run(domain, problem, search, log_name):
    os.makedirs(LOGS, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="e7verify")
    plan = os.path.join(tmp, "sas_plan")
    cmd = [sys.executable, FD, "--plan-file", plan, domain, problem, "--search", search]
    proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                          cwd=tmp, timeout=1800)
    log = proc.stdout + "\n" + proc.stderr
    path = os.path.join(LOGS, log_name + ".log")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("$ " + " ".join(cmd) + "\n\n" + log)
    h = RE_H.findall(log)
    out = {
        "search": search,
        "domain": os.path.relpath(domain, RIG),
        "problem": os.path.relpath(problem, RIG),
        "returncode": proc.returncode,
        "log": os.path.relpath(path, HERE),
        "initial_h": h[-1][1] if h else None,
        "plan_length": int(RE_PLAN.findall(log)[-1]) if RE_PLAN.findall(log) else None,
        "operators": int(RE_OPS.findall(log)[-1]) if RE_OPS.findall(log) else None,
        "variables": int(RE_VARS.findall(log)[-1]) if RE_VARS.findall(log) else None,
        "unsolvable_msg": "Completely explored state space" in log,
        "translate_unsolvable": "No relaxed solution" in log,
    }
    for key, pattern in COUNTERS.items():
        found = pattern.findall(log)
        out[key] = sum(int(x) for x in found) if found else None
    for key, pattern in (("hc_iterations", RE_HC_ITER), ("hc_patterns", RE_HC_PAT),
                         ("hc_pdb_size", RE_HC_SIZE), ("cpdbs_patterns", RE_CPDBS_PAT),
                         ("cpdbs_pdb_size", RE_CPDBS_SIZE), ("sys_patterns", RE_SYS_PAT)):
        found = pattern.findall(log)
        out[key] = int(found[-1]) if found else None
    return out


def pair(name, base_problem, guarded_domain, guarded_problem, search, tag):
    b = run(DOMAIN, base_problem, search, "%s.%s.base" % (name, tag))
    g = run(guarded_domain, guarded_problem, search, "%s.%s.guarded" % (name, tag))
    rec = {"instance": name, "config_tag": tag, "search": search,
           "base": b, "guarded": g,
           "delta": (None if b["expanded"] is None or g["expanded"] is None
                     else g["expanded"] - b["expanded"])}
    print("  %-14s %-46s exp %6s -> %-6s (d=%s)  h %s -> %s  ops %s -> %s  de %s -> %s"
          % (name, tag, b["expanded"], g["expanded"], rec["delta"],
             b["initial_h"], g["initial_h"], b["operators"], g["operators"],
             b["dead_ends"], g["dead_ends"]))
    return rec
