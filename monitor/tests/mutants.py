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

    # ---- S30: the three ways the failure exit can quietly stop existing ----

    # 1. The exit itself. Put back the unguarded call and a crash goes back to
    #    leaving the previous page in place, which is the whole defect.
    "a-crashed-scan-writes-nothing-and-the-page-just-gets-older": (
        "scan.py",
        '''        try:
            state = build(args.tests, out_dir=args.out_dir)
        except Exception as exc:                    # noqa: BLE001 -- reported''',
        '''        try:
            state = build(args.tests, out_dir=args.out_dir)
        except ZeroDivisionError as exc:            # noqa: BLE001 -- reported'''),

    # 2. The failure page rendering the last good numbers instead of refusing
    #    to. This is the tempting "helpful" version: keep showing data, add a
    #    banner. It is the defect with a badge on.
    "the-failure-page-carries-the-previous-run-forward": (
        "scan.py",
        '''    last_at, last_epoch = _prior_success(out_dir)
    state = dict(_stamps(now))''',
        '''    last_at, last_epoch = _prior_success(out_dir)
    state = dict(_stamps(now))
    state["metrics"] = {"marker": "旧的数字-91"}'''),

    # 3. The judgement behind the 55 tracebacks: git that could not answer
    #    being read as git that found nothing.
    "git-that-did-not-answer-reads-as-a-clean-tree": (
        "scan.py",
        '''    if out.returncode != 0 or out.stdout is None:''',
        '''    if False:'''),
}


def _copy(tmp):
    dst = os.path.join(tmp, "monitor")
    shutil.copytree(MONITOR, dst, ignore=shutil.ignore_patterns(
        "__pycache__", "dispatch-logs", "*.lock", "runs", "*.json"))
    return dst


def _suite(dst):
    """Run the suite in `dst`; return (returncode, set of failing test names)."""
    proc = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q"],
                          cwd=dst, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    failed = {line.split("::")[-1].split(" ")[0]
              for line in (proc.stdout or "").splitlines()
              if line.startswith("FAILED")}
    return proc.returncode, failed


def baseline():
    """What already fails in an **unmutated** copy.

    Without this the harness was unfalsifiable. `_copy` excludes `*.json` and
    `runs/`, and the temp directory is not a git repository, so several tests
    fail there for reasons that have nothing to do with any mutation -- which
    made `proc.returncode != 0` true for every patch that applied, and "RED"
    the answer the harness gave to everything. A mutation report that cannot
    print SURVIVED is decorative in exactly the way it accuses its subjects of
    being.
    """
    with tempfile.TemporaryDirectory() as tmp:
        return _suite(_copy(tmp))[1]


def run_one(name, fname, original, defective, base=frozenset()):
    with tempfile.TemporaryDirectory() as tmp:
        dst = _copy(tmp)
        path = os.path.join(dst, fname)
        text = open(path, encoding="utf-8").read()
        if original not in text:
            return name, "PATCH-DID-NOT-APPLY", (
                "the code moved; this mutant no longer describes anything")
        open(path, "w", encoding="utf-8", newline="\n").write(
            text.replace(original, defective, 1))
        _, failed = _suite(dst)
        # Only failures the unmutated copy did not already have count as
        # having caught anything.
        caught = sorted(failed - set(base))
        return name, ("RED" if caught else "SURVIVED"), "; ".join(caught)


def main():
    base = baseline()
    if base:
        print("baseline: %d test(s) already fail in an unmutated copy and are "
              "discounted below --" % len(base))
        for t in sorted(base):
            print("    %s" % t)
        print("  (these depend on the real repository; the copy is not a git "
              "checkout. They are noise here, and worth removing at the source.)")
        print()

    rows = [run_one(name, *spec, base=base) for name, spec in MUTANTS.items()]
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
