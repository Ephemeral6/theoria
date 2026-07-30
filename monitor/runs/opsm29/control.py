"""OPS-M cycle 29 control experiment.

Runs a territory's gate the way ci_merge.py runs it -- same command resolution
(gates.gate_for), same cwd (the territory inside the worktree), same
environment (gates.gate_env + the UTF-8 pin from ci_merge.sh) -- against a
worktree the caller names.  Point it at clean origin/master and it answers the
only question that makes a red flag meaningful: was the red already there
before the branch?

Usage: python control.py <worktree> <territory> [<territory> ...]
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", ".."))
import gates  # noqa: E402


def sh(args, cwd, extra_env=None, timeout=1800):
    # Identical to ci_merge.sh: the UTF-8 pin is part of the conditions, not a
    # convenience -- without it a gate that prints a non-GBK character dies of
    # UnicodeEncodeError on Windows and gets recorded as a red gate.
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    if extra_env:
        env.update(extra_env)
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          timeout=timeout, env=env)


def main():
    wt = os.path.abspath(sys.argv[1])
    out = {"worktree": wt, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                time.gmtime()),
           "head": sh(["git", "rev-parse", "HEAD"], cwd=wt).stdout.strip(),
           "territories": {}}
    for d in sys.argv[2:]:
        row = gates.gate_for(wt, d)
        rec = {"kind": row["kind"], "name": row["name"], "why": row["why"]}
        if row["kind"] == "none":
            rec["verdict"] = "UNGATED"
        else:
            r = sh(row["cmd"], cwd=os.path.join(wt, d),
                   extra_env=gates.gate_env(wt))
            rec["returncode"] = r.returncode
            rec["verdict"] = "GREEN" if r.returncode == 0 else "RED"
            rec["tail"] = (r.stdout + r.stderr)[-6000:]
        out["territories"][d] = rec
        print("%-10s %s (rc=%s)" % (d, rec["verdict"], rec.get("returncode")))
    here = os.path.dirname(os.path.abspath(__file__))
    # Named after the worktree, so a second run against a *merged* tree cannot
    # silently overwrite the clean-master baseline it is meant to be compared
    # against.  Losing the baseline would leave the comparison unfalsifiable.
    name = "control-%s.json" % os.path.basename(wt.rstrip("\\/"))
    with open(os.path.join(here, name), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print("written: %s" % name)


if __name__ == "__main__":
    main()
