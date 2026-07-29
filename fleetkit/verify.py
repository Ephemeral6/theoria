"""fleetkit's completion gate — the kit that ships a board owes one itself.

    cd fleetkit && python verify.py

Three rungs, and the territory is finished only if all three are green:

  1. the suite passes;
  2. a fleet is stood up in a **brand-new empty repository** and two workers
     claim and deliver two items through the real CLI;
  3. the artefacts that run produced carry the fields they claim -- the
     generated `fleet.json`, the board's directory layout, and the log lines
     that record the claims and the deliveries.

Rung 2 is the whole point. A coordination kit that has only ever been exercised
inside the repository that grew it has not been shown to be repository-agnostic
at all -- and being repository-agnostic is its entire claim. So the gate builds
a fresh `git init` somewhere in a tempdir, writes a config for it, and drives
the real `python -m fleetkit.board` CLI as subprocesses.

## The substitution, stated rather than glossed

The two workers are **processes, not language models**. Everything the kit owns
is exercised for real -- atomic claiming, territory exclusivity, delivery, the
log -- and what is simulated is the judgement inside a worker, which is the one
thing fleetkit does not supply. S18 recorded that as an open acceptance gap and
this gate does not quietly close it; it prints it.

## The other gap it prints

`dispatch`, `reflex`, `quota`, `assign` and `ci_merge` -- about 1,400 lines,
the launching and merging half -- are not ported. A gap named once in a README
becomes invisible in a week, so the gate says it on every run. An unported half
that nobody is reminded of reads, eventually, as a finished kit.

## It does not write into the working tree

Everything lands in a `mkdtemp` removed in a `finally`. The kit's own state
root is chosen by `FLEET_HOME`, so the fresh fleet cannot reach into this one.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

#: Floors. Not decoration: the number below which "it ran" stops being true.
#: Two items and two workers is the smallest arrangement in which territory
#: exclusivity can be observed at all -- with one of either, the property is
#: vacuous and the gate would pass on a board that does not enforce anything.
MIN_ITEMS = 2
MIN_WORKERS = 2
#: CLAIM and DONE for each of the two items.
MIN_LOG_LINES = 4

#: Every key `config.write_default` must produce. Checked with `not in`, never
#: `get(k, <hoped-for value>)`: a gate that defaults a missing field to the
#: value it wants passes a run in which the field silently disappeared.
REQUIRED_CONFIG = ("task_prefix", "territories", "protected_root", "lanes",
                   "plain_item", "progress_hook")

#: Named so the gate can say what is still missing rather than implying a whole
#: kernel was ported.
UNPORTED = ("dispatch", "reflex", "quota", "assign", "ci_merge")


def sh(argv, cwd, env=None):
    """Run a child, decoding UTF-8 rather than the host locale.

    `text=True` alone uses cp936 here, and a child printing UTF-8 then either
    mojibakes or raises inside `subprocess.run` -- a checker that dies decoding
    its child is a checker that did not check. `KNOWN_TRAPS.md` entry 2.
    """
    e = dict(os.environ)
    e["PYTHONIOENCODING"] = "utf-8"
    if env:
        e.update(env)
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=e)


def fail(problems, message):
    print("   FAIL  %s" % message)
    problems.append(message)


def rung_tests(problems):
    print("[1/3] suite")
    r = sh([sys.executable, "-m", "pytest", "-q"], cwd=HERE)
    if r.returncode == 5:
        # test_*.py exist and pytest collected nothing, so its configuration
        # points elsewhere. Read as green this would be one more instance of
        # this repository mistaking a check that could not run for one that
        # passed.
        fail(problems, "pytest collected nothing -- testpaths misconfigured, "
                       "which is a broken gate, not a passing one")
        return
    if r.returncode != 0:
        fail(problems, "suite red (exit %d)\n%s"
             % (r.returncode, (r.stdout + r.stderr)[-3000:]))
        return
    print("   ok    %s" % (r.stdout.strip().splitlines() or ["(no output)"])[-1])


def rung_fresh_fleet(problems, scratch):
    """Stand a fleet up in a repository that has never seen fleetkit."""
    print("[2/3] a fleet in a brand-new empty repository")
    root = os.path.join(scratch, "newproject")
    os.makedirs(os.path.join(root, "src"))
    os.makedirs(os.path.join(root, "docs"))
    r = sh(["git", "init", "-q"], cwd=root)
    if r.returncode != 0:
        fail(problems, "git init failed in the scratch repo: %s" % r.stderr)
        return None

    sys.path.insert(0, HERE)
    from fleetkit import config
    config.write_default(root, task_prefix="GateProbe-",
                         territories=["src", "docs"])

    home = os.path.join(root, ".fleet")
    items = os.path.join(home, "board", "items")
    os.makedirs(items)
    for iid, terr in (("T1-first", "src"), ("T2-second", "docs")):
        with open(os.path.join(items, "%s.md" % iid), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write("priority: 2\ncell: T\nterritory: %s\ndeps: none\n\n# %s\n"
                     % (terr, iid))

    env = {"FLEET_HOME": home, "PYTHONPATH": HERE}
    taken = []
    for worker in ("W-1", "W-2"):
        r = sh([sys.executable, "-m", "fleetkit.board", "claim", worker],
               cwd=home, env=env)
        if r.returncode != 0 or "CLAIM" not in r.stdout:
            fail(problems, "%s could not claim anything (exit %d): %s"
                 % (worker, r.returncode, (r.stdout + r.stderr)[-800:]))
            return None
        taken.append((r.stdout.splitlines()[0].split()[1], worker))

    for iid, worker in taken:
        r = sh([sys.executable, "-m", "fleetkit.board", "done", iid, worker],
               cwd=home, env=env)
        if r.returncode != 0:
            fail(problems, "%s could not deliver %s: %s"
                 % (worker, iid, (r.stdout + r.stderr)[-500:]))
            return None

    print("   ok    two workers claimed and delivered %d item(s)" % len(taken))
    print("   note  the workers are PROCESSES, not language models. Everything "
          "the kit owns ran for real; what is simulated is the judgement "
          "inside a worker, which fleetkit does not supply.")
    return {"root": root, "home": home, "taken": taken}


def rung_artefacts(problems, fleet):
    print("[3/3] artefact self-check")
    from fleetkit import config

    cfg_path = os.path.join(fleet["root"], config.CONFIG_NAME)
    if not os.path.exists(cfg_path):
        fail(problems, "no %s was generated at all" % config.CONFIG_NAME)
        return
    data = json.load(open(cfg_path, encoding="utf-8"))
    missing = [k for k in REQUIRED_CONFIG if k not in data]
    if missing:
        fail(problems, "the generated config is missing %s" % ", ".join(missing))
        return
    if not data.get("task_prefix"):
        fail(problems, "task_prefix is empty -- liveness is decided by matching "
                       "process names against it, so an empty prefix reports "
                       "every worker dead")
        return

    board = os.path.join(fleet["home"], "board")
    done = os.listdir(os.path.join(board, "done"))
    claimed = os.listdir(os.path.join(board, "claimed"))
    if len(done) < MIN_ITEMS:
        fail(problems, "only %d item(s) delivered, floor is %d -- with fewer "
                       "than two the exclusivity property is vacuous"
             % (len(done), MIN_ITEMS))
        return
    if claimed:
        fail(problems, "%d claim(s) still held after delivery: %s"
             % (len(claimed), ", ".join(claimed[:4])))
        return

    log_path = os.path.join(board, "board.log")
    if not os.path.exists(log_path):
        fail(problems, "the board kept no log at all")
        return
    lines = [l for l in open(log_path, encoding="utf-8").read().splitlines()
             if l.strip()]
    claims = [l for l in lines if "CLAIM" in l]
    dones = [l for l in lines if "DONE" in l]
    if len(lines) < MIN_LOG_LINES or len(claims) < MIN_WORKERS \
            or len(dones) < MIN_ITEMS:
        fail(problems, "the log records %d line(s) (%d CLAIM, %d DONE); floors "
                       "are %d/%d/%d -- a board that does its work and records "
                       "nothing is a board nobody can audit"
             % (len(lines), len(claims), len(dones),
                MIN_LOG_LINES, MIN_WORKERS, MIN_ITEMS))
        return

    print("   ok    config carries all %d required keys; %d delivered, 0 still "
          "claimed; log has %d CLAIM and %d DONE"
          % (len(REQUIRED_CONFIG), len(done), len(claims), len(dones)))


def unported_note():
    present = [m for m in UNPORTED
               if os.path.exists(os.path.join(HERE, "fleetkit", "%s.py" % m))]
    missing = [m for m in UNPORTED if m not in present]
    if missing:
        print("   note  NOT ported, ~1400 lines: %s. The kit coordinates; it "
              "does not yet launch or merge. Printed every run because a gap "
              "named once in a README is invisible in a week."
              % ", ".join(missing))
    else:
        print("   note  every module S18 listed as unported is now present -- "
              "update UNPORTED and the README rather than leaving this stale.")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    problems = []
    scratch = tempfile.mkdtemp(prefix="fleetkit-verify-")
    try:
        rung_tests(problems)
        fleet = rung_fresh_fleet(problems, scratch)
        if fleet:
            rung_artefacts(problems, fleet)
        unported_note()
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    print()
    if problems:
        print("fleetkit: RED (%d problem(s))" % len(problems))
        return 1
    print("fleetkit: green -- suite, a fleet stood up from nothing, artefacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
