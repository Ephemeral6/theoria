"""papers' completion gate — the one that existed but was in the wrong place.

    cd papers && python verify.py

`papers/phase1-workshop/verify_paper.py` has been a real gate for some time,
checking four properties of the draft. `gates.py` never found it, because
discovery looks at the *territory root* and this lived one directory down. So
the survey reported `papers` as UNGATED for days while a working gate sat
inside it.

Worth naming rather than quietly fixing, because it is a variety of the failure
this repository keeps meeting: the check existed, ran, and passed, and the thing
that was supposed to notice it was looking somewhere else. A gate nobody can
find is, to every automated reader, a gate that does not exist.

## What this file is and is not

It is a **delegator**. It does not re-check anything and it does not modify
`verify_paper.py`, which belongs to the paper's author. It finds every paper
directory under `papers/` and runs whichever gate each one ships, so a second
paper is covered on the day it arrives without anyone editing this file.

Its own contribution is refusing two silences:

* **no paper directory found** is RED, not a vacuous pass -- an empty walk
  satisfies every loop, and "there was nothing to check" must never be
  reported the same way as "everything checked out";
* **a paper directory with no gate** is RED and names the directory, because
  the entire reason this file exists is that an unfound gate reads as no gate.
"""

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

#: Gate filenames a paper directory may ship, in preference order.
GATE_NAMES = ("verify_paper.py", "verify.py")

#: At least one paper must exist. The floor is the point: a walk over nothing
#: returns success from every check written above it.
MIN_PAPERS = 1


def sh(argv, cwd):
    """UTF-8, not the host locale -- cp936 here, and a gate printing UTF-8
    would otherwise raise inside subprocess.run and count as 'did not check'."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env)


def paper_dirs():
    return sorted(d for d in os.listdir(HERE)
                  if os.path.isdir(os.path.join(HERE, d))
                  and not d.startswith((".", "__")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=1800)
    ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    problems = []
    papers = paper_dirs()
    print("[1/2] find the papers and their gates")
    if len(papers) < MIN_PAPERS:
        print("   FAIL  no paper directory under papers/ -- an empty walk "
              "passes every check written below it, so it is refused here")
        print("\npapers: RED (1 problem)")
        return 1

    ran = []
    for name in papers:
        d = os.path.join(HERE, name)
        gate = next((g for g in GATE_NAMES
                     if os.path.isfile(os.path.join(d, g))), None)
        if gate is None:
            problems.append("%s ships no gate (%s)"
                            % (name, " / ".join(GATE_NAMES)))
            print("   FAIL  %s ships no gate" % name)
            continue
        ran.append((name, gate))
        print("   ok    %s -> %s" % (name, gate))

    print("[2/2] run each one")
    for name, gate in ran:
        r = sh([sys.executable, gate], cwd=os.path.join(HERE, name))
        if r.returncode != 0:
            problems.append("%s/%s exited %d" % (name, gate, r.returncode))
            print("   FAIL  %s/%s exited %d\n%s"
                  % (name, gate, r.returncode, (r.stdout + r.stderr)[-2500:]))
            continue
        tail = [l for l in r.stdout.strip().splitlines() if l.strip()]
        print("   ok    %s: %s" % (name, tail[-1] if tail else "(no output)"))

    print()
    if problems:
        print("papers: RED (%d problem(s))" % len(problems))
        return 1
    print("papers: green -- %d paper(s), each gated by its own check" % len(ran))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
