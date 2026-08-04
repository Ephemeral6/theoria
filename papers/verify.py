"""papers' completion gate — the one that existed but was in the wrong place.

    cd papers && python verify.py

`papers/phase1-workshop/verify_paper.py` has been a real gate for some time,
checking six properties of the draft. `gates.py` never found it, because
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

## S34 (2026-07-29, RES-2): what closing the hole cost

S34 was filed as "papers has a suite but no canonical verify gate". By the time
it was claimed that was already false -- this file had landed, `survey()`
already counted `papers` among the gated, and S33 had already retired the
`tests_only` allowance the item asked to remove. The debt the item named was
paid before it was claimed. Two it did not name were open, and both are
side effects of paying it.

**The suite this gate displaced.** `monitor/gates.py:192 gate_for()` returns
inside its `find_gate` branch and never reaches `has_tests()` on line 213: a
territory that ships a gate is gated *by that gate alone*. The consequence is
visible in `monitor/ci/merge.log`. Line 1856, 2026-07-29T15:02:51Z: P16 lands
the territory's first `test_*.py` and the merge runs `pytest:papers`. Line
1872, 53 minutes later at 15:55:51Z: S32 lands this file and the same merge
runs `verify:papers(verify.py)`. Every papers merge since -- 1894, 1938, 1948
-- reads `verify:papers(verify.py)` and nothing else.

So `pytest:papers` ran **once, ever**: the 62 tests of `test_uncited_gate.py`,
which was all the territory had in that 53-minute window.
`test_bare_gate.py`'s 20 tests arrived with p17 at 18:02:35Z (merge.log:1894),
after the switch, and have **never been run by CI at all**. Stage 3 below
exists because of that.

Two corrections an adversarial pass forced, because the tidier story was the
wrong one. First, this was not a gate walking in on a suite: S32 authored this
file at 11:03Z, when `papers` held no test at all (merge.log:1838 still calls
it `NO GATE, MERGED UNCHECKED`), and P16's suite arrived in between. Nobody
displaced anything on purpose; the two commits were correct separately and the
loss happened in the order they merged, which is the only place it was ever
visible. Second, the precedent already existed and was in writing:
`monitor/tests/test_gates.py:163-166` records the same event for `proxy` --
a canonical `verify.py` superseding `verify_spend.sh` -- and says in as many
words that the only reason it was acceptable is that `proxy/verify.py:260`
re-invokes the superseded gate as one of its own stages, "否则这就是加了一道闸门、
悄悄关掉另一道". This file did not do that. The lesson had been learned, written
down, and then not applied one commit later, which is the more useful finding
than the outage would have been.

**And declaring the sample is not running it.** `negative_sample_of()` checks
`os.path.isfile` (`gates.py:177`) and stops. The declaration at the foot of
this docstring clears `papers` out of `survey()["decorative"]` while executing
none of the tests it points at -- a green earned by an existence check. That
is why the declaration comes with stage 3 and not instead of it.

A smaller thing found by writing that declaration, reported to the monitor
rather than fixed here because `gates.py` is not this territory's to change:
`NEGATIVE_SAMPLE.search()` takes the **first** match anywhere in the file, so
this paragraph -- which merely talks about the mechanism -- shadowed the real
declaration below it, and `survey()` read the sample as the single backtick
that followed the phrase. It failed safe here (a path that does not exist
leaves the gate `decorative`). It would not have failed safe if the prose had
happened to name a file that does exist.

**The trap this gate armed.** `paper_dirs()` used to return *every*
subdirectory and demand a gate from each. `CLAUDE.md` tells every agent in the
repository to write provenance to `<territory>/runs/<id>/`, and `runs/` is
gitignored nowhere -- at this branch's base commit `c54954d6`,
`git ls-tree -r --name-only c54954d6 | grep -cE '(^|/)runs/'` is **3870** across
22 top-level directories. A committed `papers/runs/` would therefore have taken
this gate red for the crime of following the convention.

The count carries its command and its commit because the first draft of this
paragraph said 3706 and no definition reproduced it two hours later: the tree
gains provenance files continuously, so a bare live count in a docstring is a
number that rots on its own. The order of magnitude is the argument; the digits
are only worth writing down if a reader can re-derive them.

Stated at its true size, which is smaller than it first looked: it has never
fired. `grep "red in papers" monitor/ci/merge.log` is empty. The reason is that
this territory's provenance has always gone one level deeper, into
`papers/phase1-workshop/runs/`, where `paper_dirs()` never looked -- so the
convention and the trap have been missing each other by one directory for as
long as both existed. On the ordinary branch path it would also have failed the
offending *branch* rather than master. It is latent fragility, not an incident,
and it is not specific to `runs/`: any committed top-level directory under
`papers/` -- shared figures, templates, an archive, a second paper's assets --
did the same thing.

It stops being latent with this commit: S34's own provenance is at
`papers/runs/20260729T224939Z-S34/`, the territory-root location `CLAUDE.md`
specifies, which is a deliberate move off phase1-workshop's local habit and
onto the repository's rule. The fix and its first user land together.

So the classification below is explicit rather than residual: a directory is a
paper if it holds a `PAPER.md`, `runs/` is provenance and is skipped by name,
and anything that is neither is still RED and named. Fail-closed survives; the
trap does not.

# negative-sample: papers/test_verify_delegator.py
"""

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

#: Gate filenames a paper directory may ship, in preference order.
GATE_NAMES = ("verify_paper.py", "verify.py")

#: What makes a directory a paper. Positive and single: keying off the gate
#: file would be circular -- a paper without a gate would become invisible,
#: which is the silence this file was written to refuse -- and a blocklist of
#: everything that is not a paper cannot be written in advance.
PAPER_MARKER = "PAPER.md"

#: Directories under `papers/` that are not papers and are not defects.
#: `runs/` is CLAUDE.md's provenance convention, mandatory repository-wide.
#:
#: The other two are the use the docstring above anticipated -- "any committed
#: top-level directory under `papers/` -- shared figures, templates, an archive,
#: a second paper's assets -- did the same thing". Both arrived together on
#: 2026-07-31 in `b8a7d6bc`, "salvage: paid P11 transport shards and two
#: never-committed paper corpora", which committed the complete contents of two
#: abandoned worktrees that "existed on no ref at all". Each entry carries its
#: reason, in the form `monitor/gates.py:59` uses for `NOT_TERRITORIES`: a
#: registration whose reason is not written down is a line added, not a ruling.
#:
#: Registering is the right half of the choice rather than the cheap half.
#: `GATE_NAMES` below makes a paper directory that ships no gate RED, so a
#: skeleton `PAPER.md` does not turn either of these green -- it turns "neither
#: a paper nor declared provenance" into "ships no gate", and buys the cost of a
#: whole gate implementation for a directory that is not a paper anyway.
NOT_PAPERS = frozenset({
    "runs",
    # 2026-07-31, registered 2026-08-04 (V31): P-23's citation library for
    # `Theoria.md` §3.2 item 7 and its downstream section, not a paper. Its own
    # `related-work/README.md:7` opens "This directory is **not** a paper. It is
    # the evidence base a paper draws on", and it was superseded before it was
    # committed: 16 of its 48 BibTeX keys are already in
    # `papers/phase1-workshop/references.bib`, phase1-workshop's own P-7 search
    # traces cover all seven literature lines including the two `lines/` never
    # wrote, and the `[bib: TODO]` markers it existed to fill are gone.
    "related-work",
    # 2026-07-31, registered 2026-08-04 (V31): P3's chart data and prose bodies
    # for figures 5 and 6, not a paper. `case-studies/README.md:20-22` says so
    # itself -- "Figures themselves are the P21-figures ticket's territory; this
    # directory ships the numbers and the words, not the plots" -- and
    # `README.md:40-47` records that the 死锁定理集 half of the Phase 3 unit it
    # was drafted against "is not here", it is `engine-rig`'s. `README.md:28-38`
    # calls its three cases "pre-campaign case studies standing in for the ones
    # the clause asks for", to be re-cut on live material. Nothing in the tree
    # cites it. The nearest thing to a counter-argument is `Theoria.md:381`,
    # which books the Phase 3 boundary as a 最小可发表单元; a unit that ships one
    # of its two named halves, on self-built worlds, is not that unit yet.
    "case-studies",
})

#: At least one paper must exist. The floor is the point: a walk over nothing
#: returns success from every check written above it.
MIN_PAPERS = 1

#: Set while stage 3 runs the suite, so a test that drives this gate end to end
#: does not re-enter stage 3 and fork-bomb the merge rig.
INNER = "THEORIA_PAPERS_VERIFY_INNER"

#: pytest's exit code for "collected nothing". Not a pass: without this, a
#: suite that has been deleted and a suite that is green report the same green.
NO_TESTS_COLLECTED = 5


def sh(argv, cwd, timeout=None, env_extra=None):
    """UTF-8, not the host locale -- cp936 here, and a gate printing UTF-8
    would otherwise raise inside subprocess.run and count as 'did not check'.

    The repository root goes on PYTHONPATH because `monitor/gates.py:
    gate_env()` states that as the contract every gate is entitled to assume,
    and a sub-gate that dies on `import` gets reported as its paper failing --
    a lie in the direction that looks like a verdict."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env["PYTHONPATH"] = ROOT + (os.pathsep + env["PYTHONPATH"]
                                if env.get("PYTHONPATH") else "")
    if env_extra:
        env.update(env_extra)
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env,
                          timeout=timeout)


def classify(root):
    """`(papers, skipped, strays)` for the directories directly under `root`.

    Three names, not two, and the third is the one that matters: a directory
    that is neither a paper nor declared provenance is a *stray*, and a stray
    is red. That keeps the gate fail-closed while `runs/` -- which the
    repository orders every agent to create -- stops being an accusation."""
    papers, skipped, strays = [], [], []
    # A root that does not exist yields no papers, and the floor in `main()`
    # turns that into RED. Crashing here would be reported by the merge rig as
    # the gate failing rather than as the territory being absent -- a lie in
    # the direction that looks like a verdict.
    if not os.path.isdir(root):
        return papers, skipped, strays
    for name in sorted(os.listdir(root)):
        if not os.path.isdir(os.path.join(root, name)):
            continue
        if name.startswith((".", "__")):
            continue
        if name in NOT_PAPERS:
            skipped.append(name)
        elif _has(os.path.join(root, name), PAPER_MARKER):
            papers.append(name)
        else:
            strays.append(name)
    return papers, skipped, strays


def _has(directory, filename):
    """Case-sensitively, on a filesystem that may not be.

    `os.path.isfile` accepts `PAPER.MD` on Windows and rejects it on Linux, so
    a tree would classify differently on the two -- and determinism is a stated
    requirement of this repository, not a preference."""
    try:
        return filename in os.listdir(directory)
    except OSError:
        return False


def gate_of(root, name):
    """The gate file the directory `root/name` ships, or None."""
    d = os.path.join(root, name)
    return next((g for g in GATE_NAMES if _has(d, g)), None)


def run_suite(root, timeout=None):
    """`(ok, detail, ran)` for the territory's own test suite.

    Three outcomes collapse into two everywhere else and must not here: green,
    red, and *collected nothing*. The third is what a deleted suite looks like,
    and catching it is the whole reason this stage exists.

    `ran` is third because `ok` cannot carry it. The legitimate nested run is
    green *without having checked anything*, and S34's own summary line went out
    claiming "the checks' own suite run" on exactly that path -- a false
    sentence on the green path, which is the defect class this file was written
    to refuse. Returned as a value rather than sniffed out of `detail`'s prose,
    so the caller cannot get it wrong."""
    if os.environ.get(INNER):
        # The guard has to be un-settable by accident, because the thing it
        # can do wrong is skip stage 3 and still exit 0 -- which is the exact
        # defect stage 3 was added to fix, restored by an environment
        # variable. A legitimate nested run is always inside pytest; anything
        # else setting this name is an environment nobody can explain, and an
        # unexplained environment is not a pass.
        if "pytest" not in sys.modules and "PYTEST_CURRENT_TEST" not in os.environ:
            return False, ("%s is set but this is not a nested run -- refusing "
                           "to skip stage 3 on an unexplained environment "
                           "variable" % INNER), False
        return (True,
                "skipped: already running inside the suite (%s set)" % INNER,
                False)
    r = sh([sys.executable, "-m", "pytest", "-q", "-x"], cwd=root,
           timeout=timeout, env_extra={INNER: "1"})
    tail = [l for l in r.stdout.strip().splitlines() if l.strip()]
    last = tail[-1] if tail else "(no output)"
    if r.returncode == NO_TESTS_COLLECTED:
        return False, ("pytest collected nothing -- the suite that shows this "
                       "territory's checks can go red is gone"), True
    if r.returncode != 0:
        return False, "pytest exited %d: %s" % (r.returncode, last), True
    return True, last, True


def main(argv=None):
    ap = argparse.ArgumentParser()
    # 1500, not 1800: `monitor/ci_merge.py:543` kills a gate at 1800s, so a
    # gate whose own limit is also 1800 never gets to say anything -- the
    # runner reports an opaque kill instead of "phase1-workshop's gate hung".
    # A subordinate timeout has to be strictly shorter than its supervisor's
    # or it is decorative.
    ap.add_argument("--timeout", type=int, default=1500,
                    help="seconds allowed to any one subprocess; parsed and "
                         "then ignored until S34, so a gate that hung hung "
                         "the merge rig with it")
    ap.add_argument("--root", default=HERE,
                    help="the papers/ tree to check; overridden by the tests, "
                         "which build synthetic ones")
    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    root = os.path.abspath(args.root)

    problems = []

    print("[1/3] classify the directories under papers/")
    papers, skipped, strays = classify(root)
    for name in skipped:
        # Not "provenance": that was true while `runs/` was the only entry, and
        # stopped being true the moment the set had to carry a judgement call.
        # A line that names the register a directory is in can be checked
        # against it; a line that asserts what the directory *is* goes quietly
        # wrong when the register grows.
        print("   --    %s (declared not a paper, see NOT_PAPERS)" % name)
    for name in strays:
        problems.append("%s is neither a paper (no %s) nor declared provenance"
                        % (name, PAPER_MARKER))
        print("   FAIL  %s: no %s, and not named in NOT_PAPERS"
              % (name, PAPER_MARKER))
    if len(papers) < MIN_PAPERS:
        problems.append("no paper directory under papers/")
        print("   FAIL  no paper directory under papers/ -- an empty walk "
              "passes every check written below it, so it is refused here")
        print("\npapers: RED (%d problem(s))" % len(problems))
        return 1
    print("   ok    %d paper(s): %s" % (len(papers), ", ".join(papers)))

    print("[2/3] run the gate each paper ships")
    for name in papers:
        gate = gate_of(root, name)
        if gate is None:
            problems.append("%s ships no gate (%s)"
                            % (name, " / ".join(GATE_NAMES)))
            print("   FAIL  %s ships no gate" % name)
            continue
        try:
            r = sh([sys.executable, gate], cwd=os.path.join(root, name),
                   timeout=args.timeout)
        except subprocess.TimeoutExpired:
            problems.append("%s/%s did not finish in %ds"
                            % (name, gate, args.timeout))
            print("   FAIL  %s/%s did not finish in %ds -- a gate that hangs "
                  "is not a gate that passed" % (name, gate, args.timeout))
            continue
        if r.returncode != 0:
            problems.append("%s/%s exited %d" % (name, gate, r.returncode))
            print("   FAIL  %s/%s exited %d\n%s"
                  % (name, gate, r.returncode, (r.stdout + r.stderr)[-2500:]))
            continue
        tail = [l for l in r.stdout.strip().splitlines() if l.strip()]
        if not tail:
            # The third silence, after "no paper" and "no gate": a gate that
            # ran, said nothing, and exited 0. A zero-byte `verify_paper.py`
            # is indistinguishable from a thorough one here, and the previous
            # version of this file printed "(no output)" on its `ok` line and
            # called the territory green.
            problems.append("%s/%s exited 0 without printing anything"
                            % (name, gate))
            print("   FAIL  %s/%s exited 0 and said nothing -- a gate that "
                  "asserts nothing is not a gate that passed" % (name, gate))
            continue
        print("   ok    %s -> %s: %s" % (name, gate, tail[-1]))

    print("[3/3] run the suite that shows those gates can go red")
    try:
        ok, detail, suite_ran = run_suite(root, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        ok, detail, suite_ran = (False,
                                 "pytest did not finish in %ds" % args.timeout,
                                 True)
    if ok:
        print("   ok    %s" % detail)
    else:
        problems.append(detail)
        print("   FAIL  %s" % detail)

    print()
    if problems:
        print("papers: RED (%d problem(s))" % len(problems))
        return 1
    # The summary states only what happened. On the nested path stage 3 is
    # green without having run, and the previous wording said "the checks' own
    # suite run" anyway -- a green line asserting a check that did not execute
    # is the same silence the three stages above are built to refuse, so it is
    # not allowed on this file's own output either.
    print("papers: green -- %d paper(s), each gated by its own check, and the "
          "checks' own suite %s"
          % (len(papers), "run" if suite_ran else "NOT run (stage 3 skipped)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
