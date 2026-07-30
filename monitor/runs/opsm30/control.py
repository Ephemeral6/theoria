"""OPS-M cycle 30 adversarial control.

Unlike cycle 29's control.py, this does not *reimplement* ci_merge's invocation
conditions -- it imports ci_merge and calls its own `gate_for` and `sh`.  A
reimplementation is a claim about the runner that nothing checks against the
runner, which is the exact failure `gates.py` was written to end.  If ci_merge
changes, this control changes with it.

The only thing not reproduced is the worktree *location*: ci_merge uses
`tempfile.mkdtemp()` in %TEMP%, and OPS-M cycle 30's rules require experiment
worktrees inside the repo.  Location-sensitivity is therefore tested separately
rather than assumed absent (cycle 29 proved freeze *is* location-sensitive).

Usage: python control.py <label> <worktree> <territory> [<territory> ...]
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", ".."))
import ci_merge  # noqa: E402  -- the runner itself, not a copy of it
import gates     # noqa: E402


def main():
    label = sys.argv[1]
    wt = os.path.abspath(sys.argv[2])
    out = {"label": label, "worktree": wt,
           "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "head": ci_merge.sh(["git", "rev-parse", "HEAD"], cwd=wt).stdout.strip(),
           "via": "ci_merge.gate_for + ci_merge.sh + gates.gate_env",
           "territories": {}}
    for d in sys.argv[3:]:
        row = ci_merge.gate_for(wt, d)
        rec = {"kind": row["kind"], "name": row["name"], "why": row["why"],
               "cmd": row["cmd"]}
        if row["kind"] == "none":
            rec["verdict"] = "UNGATED-or-ABSENT"
            rec["dir_exists"] = os.path.isdir(os.path.join(wt, d))
        else:
            t0 = time.time()
            r = ci_merge.sh(row["cmd"], cwd=os.path.join(wt, d), timeout=1800,
                            extra_env=gates.gate_env(wt))
            rec["secs"] = round(time.time() - t0, 1)
            rec["returncode"] = r.returncode
            # ci_merge's own verdict mapping, line-for-line (ci_merge.py:544-563)
            if row["kind"] == "verify" and r.returncode != 0:
                rec["verdict"] = "RED (verify gate red in %s)" % d
            elif r.returncode == ci_merge.NO_TESTS_COLLECTED:
                rec["verdict"] = "BROKEN (collects nothing)"
            elif r.returncode != 0:
                rec["verdict"] = "RED (tests red in %s)" % d
            else:
                rec["verdict"] = "GREEN"
            rec["tail"] = (r.stdout + r.stderr)[-8000:]
        out["territories"][d] = rec
        print("%-10s %-40s rc=%s  %ss"
              % (d, rec["verdict"], rec.get("returncode"), rec.get("secs")))
    here = os.path.dirname(os.path.abspath(__file__))
    name = "control-%s.json" % label
    with open(os.path.join(here, name), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    print("written: %s" % name)


if __name__ == "__main__":
    main()
