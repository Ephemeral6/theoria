"""Put each fixed defect back, in a scratch copy, and check a test goes red.

A test suite that passes proves the code passes the suite. It does not prove
the suite would have caught the bug, and for a state machine that froze the
fleet for most of a day that is the only question worth asking. So every
defect this suite claims to catch is re-introduced here into a throwaway copy
of `monitor/`, and the suite is run against it. A mutant that survives means
the test covering it is decorative.

The two OPS-M cycle 5 defects are the first two entries; the rest are the ways
the same state machine could go wrong next.

    cd monitor && python tests/mutants.py

Never writes to `monitor/` itself -- every mutation happens in a temp copy, and
the live `quota_state.json` and `dispatch-logs/` are not even copied.
"""

import os
import shutil
import subprocess
import sys
import tempfile

MONITOR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: name -> (file, the code as it is, the code as the defect had it)
MUTANTS = {
    "resume-empty-queue-never-clears-the-mode": (
        "quota.py",
        '''        if st.get("mode") != "normal" and ping() == 0:
            st["mode"] = "normal"
            st["resumed_at"] = now_utc()
            save_state(st)
            print("queue empty and window open -> mode=normal")
            return 0
        print("nothing to resume.")''',
        '''        print("nothing to resume.")'''),

    "check-never-lifts-the-hold-on-its-deadline": (
        "quota.py",
        '''        if due and now >= due:''',
        '''        if False:'''),

    "ci-merge-blocked-by-the-quota-hold": (
        "reflex.py",
        '''        if True:
            r = run([sys.executable, os.path.join(HERE, "ci_merge.py")],''',
        '''        if not hold:
            r = run([sys.executable, os.path.join(HERE, "ci_merge.py")],'''),

    "resume-relaunches-into-a-closed-window": (
        "quota.py",
        '''    if ping() != 0:''',
        '''    if False:'''),

    "hold-fires-on-any-dead-session-not-just-a-quota-one": (
        "quota.py",
        '''        line = quota_line(entry.get("log", ""))
        if line:''',
        '''        line = quota_line(entry.get("log", "")) or "assumed quota"
        if line:'''),
}


def run_one(name, fname, original, defective):
    with tempfile.TemporaryDirectory() as tmp:
        dst = os.path.join(tmp, "monitor")
        shutil.copytree(MONITOR, dst, ignore=shutil.ignore_patterns(
            "__pycache__", "dispatch-logs", "*.lock", "runs", "*.json"))
        path = os.path.join(dst, fname)
        text = open(path, encoding="utf-8").read()
        if original not in text:
            return name, "PATCH-DID-NOT-APPLY", (
                "the code moved; this mutant no longer describes anything")
        open(path, "w", encoding="utf-8", newline="\n").write(
            text.replace(original, defective, 1))
        proc = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q"],
                              cwd=dst, capture_output=True, text=True)
        caught = "; ".join(
            line.split("::")[-1].split(" ")[0]
            for line in proc.stdout.splitlines() if line.startswith("FAILED"))
        return name, ("RED" if proc.returncode else "SURVIVED"), caught


def main():
    rows = [run_one(name, *spec) for name, spec in MUTANTS.items()]
    width = max(len(r[0]) for r in rows)
    for name, verdict, caught in rows:
        print("%-*s  %-8s  %s" % (width, name, verdict, caught))
    survivors = [r for r in rows if r[1] != "RED"]
    print()
    if survivors:
        print("SURVIVED: %s" % ", ".join(r[0] for r in survivors))
        print("a mutant that survives means the test covering it is decorative")
        return 1
    print("all %d mutants caught" % len(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
