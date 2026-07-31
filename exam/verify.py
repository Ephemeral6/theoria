"""One command that decides whether this territory is green.

```bash
python -m exam.verify
```

Stages, and each answers a different question:

| stage | question |
|---|---|
| `build_papers` | do the four papers still build, split sheet from key, and pass every leak check? |
| `pytest` | do the exam's own properties hold, including the regressions for the defects that shipped? |
| `run_exam --calibrate` | does the marker still reproduce four known scores before it marks anything? |
| `run_selftest` | does the marker behave correctly *between* its endpoints, and does every injected fault still get caught? |
| `build_prereg` | does endpoint 2's pre-registration still describe the paper that builds, and is every negative control still judged as pre-registered? |
| `withdrawn_claims` | has a claim withdrawn by D-EX-028 grown back anywhere this territory writes? |
| `artefact_locations` | does any tracked artefact record where its builder stood? |
| `artifacts_match_committed` | is what is committed under `exam/artifacts/` what this code produces? |
| `determinism` | do two builds in fresh interpreters produce byte-identical sheets? |

**The producers write to a shadow tree, not to `exam/artifacts/`.**  For weeks
this file printed GREEN without ever comparing a build against a committed
artefact, and the reason was structural rather than an oversight: `build_papers`
overwrote the tracked artefacts in place as stage one, so by the time any later
stage could have asked the question, the evidence was gone.  Verify now seeds a
temporary copy of `exam/artifacts`, points every producer at it through
`EXAM_ARTIFACTS_DIR`, and leaves the tracked tree untouched for the whole run;
`artifacts_match_committed` then compares the two.  A mismatch is red and stays
red -- adopting a rebuild means running `python -m exam.tools.build_papers`
yourself and committing the diff with the reason, because a gate that quietly
adopted what it found would erase the finding, which is how this went unseen.

`artefact_locations` covers a dimension `determinism` cannot see by
construction. The determinism stage compares two in-process builds' sheet
digests and never opens `exam/artifacts/build_manifest.json` -- so it was not
falsely green, it was answering a narrower question, and the marked sheets
really are location-independent. What went unmeasured was the build manifest,
which recorded twelve absolute paths naming whichever worktree ran last. V27.

**The self-test's uncaught faults are reported and do not gate.** A run that
discovers a fault no check catches has done its job; turning that into a red
exit code would make the honest response to a discovery indistinguishable from
a broken build, and would create a reason not to add a fault. What *does* gate
is a dirty baseline — a check firing before anything was injected means the
matrix underneath it means nothing — and any failed mutant, because a mutant's
expectation is arithmetic rather than judgement.

Same shape as `worldgen/verify.py`, and for the same reason stated there: the
verifier fails on defects in this library and prints measurements as
measurements.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from typing import Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if REPO not in sys.path:            # `python exam/verify.py`, not just `-m`
    sys.path.insert(0, REPO)


def _run(label: str, argv: Sequence[str], *, gates: bool = True,
         env: Optional[Dict[str, str]] = None) -> Tuple[str, int, bool]:
    print("\n" + "=" * 78)
    print("== %s%s" % (label, "" if gates else "   (reported, does not gate)"))
    print("=" * 78, flush=True)
    result = subprocess.run(list(argv), cwd=REPO, env=env)
    return label, result.returncode, gates


def _determinism() -> Tuple[str, int, bool]:
    """Two builds, two fresh interpreters, byte-identical sheets.

    In-process rebuilding proves less than it looks like it proves: a cached
    module, a memoised digest or a dict iteration order carried over from the
    first build would go unnoticed. Separate processes, and a different
    PYTHONHASHSEED in each, is what the determinism claim actually means.
    """
    print("\n" + "=" * 78)
    print("== determinism: two builds, fresh interpreters, PYTHONHASHSEED 7 vs 99")
    print("=" * 78, flush=True)
    script = (
        "import sys; sys.path.insert(0, %r);"
        "from exam.papers import BUILDERS, module_for;"
        "from exam.grading.registry import digest;"
        "from exam.model import canonical, sha256;"
        "print(' '.join(sha256(module_for(t).build().sheet(digest()))"
        "                for t in sorted(BUILDERS)))" % REPO
    )
    digests = []
    for seed in ("7", "99"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        out = subprocess.run([sys.executable, "-c", script], cwd=REPO, env=env,
                             capture_output=True, text=True)
        if out.returncode != 0:
            print(out.stderr[-2000:])
            return "determinism", out.returncode, True
        digests.append(out.stdout.strip())
        print("  PYTHONHASHSEED=%-3s %s" % (seed, out.stdout.strip()))
    same = digests[0] == digests[1]
    print("  identical: %s" % same)
    return "determinism", 0 if same else 1, True


def main(argv: List[str] | None = None) -> int:
    py = sys.executable
    from exam.tools import check_artifacts_match as match

    tmp = tempfile.mkdtemp(prefix="exam-verify-")
    shadow = os.path.join(tmp, "artifacts")
    match.seed_shadow(shadow)
    # Seeded as a copy rather than empty: the producers read as well as write
    # -- `run_exam` marks the submissions under `answers/` against the keys
    # under `truth/` -- so an empty tree would be a different run, not a
    # cleaner one.
    build_env = dict(os.environ, EXAM_ARTIFACTS_DIR=shadow)
    print("producers write to a shadow tree; exam/artifacts is not touched")
    print("  EXAM_ARTIFACTS_DIR=%s" % shadow)

    try:
        stages = [
            _run("build_papers", [py, "-m", "exam.tools.build_papers"],
                 env=build_env),
            _run("pytest", [py, "-m", "pytest", "exam/tests", "-q"]),
            _run("run_exam --calibrate", [py, "-m", "exam.tools.run_exam",
                                          "--calibrate"], env=build_env),
            _run("run_selftest", [py, "-m", "exam.tools.run_selftest"],
                 env=build_env),
            # Endpoint 2. Gates on two things at once: the pre-registration
            # still describes the paper that builds (class mix, points, rubric
            # weights, certificate grammar), and every negative control is
            # still judged as pre-registered -- `bluffer` 不成立, `memoriser`
            # 不可结论, `denier` and `overclaimer` each refused by the one floor
            # that catches them alone.
            _run("build_prereg", [py, "-m", "exam.tools.build_prereg"],
                 env=build_env),
            # A claim withdrawn by D-EX-028 must not survive anywhere this
            # territory writes -- least of all in a generated artefact, which
            # is where it last did.
            _run("withdrawn_claims",
                 [py, "-m", "exam.tools.check_withdrawn_claims"]),
            _run("artefact_locations",
                 [py, "-m", "exam.tools.check_artefact_locations"]),
            _run("artifacts_match_committed",
                 [py, "-m", "exam.tools.check_artifacts_match",
                  "--built", shadow]),
            _determinism(),
        ]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n" + "=" * 78)
    print("== summary")
    print("=" * 78)
    failed = []
    for label, code, gates in stages:
        state = "ok" if code == 0 else "FAILED(%d)" % code
        print("  %-26s %s%s" % (label, state, "" if gates else "  [reported]"))
        if code != 0 and gates:
            failed.append(label)
    if failed:
        print("\nRED: %s" % ", ".join(failed))
        return 1
    print("\nGREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
