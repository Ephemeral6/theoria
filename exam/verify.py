"""One command that decides whether this territory is green.

```bash
python -m exam.verify
```

Five stages, and each answers a different question:

| stage | question |
|---|---|
| `build_papers` | do the four papers still build, split sheet from key, and pass every leak check? |
| `pytest` | do the exam's own properties hold, including the regressions for the defects that shipped? |
| `run_exam --calibrate` | does the marker still reproduce four known scores before it marks anything? |
| `run_selftest` | does the marker behave correctly *between* its endpoints, and does every injected fault still get caught? |
| `determinism` | do two builds in fresh interpreters produce byte-identical sheets? |

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
import subprocess
import sys
from typing import List, Sequence, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def _run(label: str, argv: Sequence[str], *, gates: bool = True) -> Tuple[str, int, bool]:
    print("\n" + "=" * 78)
    print("== %s%s" % (label, "" if gates else "   (reported, does not gate)"))
    print("=" * 78, flush=True)
    result = subprocess.run(list(argv), cwd=REPO)
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
    stages = [
        _run("build_papers", [py, "-m", "exam.tools.build_papers"]),
        _run("pytest", [py, "-m", "pytest", "exam/tests", "-q"]),
        _run("run_exam --calibrate", [py, "-m", "exam.tools.run_exam", "--calibrate"]),
        _run("run_selftest", [py, "-m", "exam.tools.run_selftest"]),
        _determinism(),
    ]

    print("\n" + "=" * 78)
    print("== summary")
    print("=" * 78)
    failed = []
    for label, code, gates in stages:
        state = "ok" if code == 0 else "FAILED(%d)" % code
        print("  %-22s %s%s" % (label, state, "" if gates else "  [reported]"))
        if code != 0 and gates:
            failed.append(label)
    if failed:
        print("\nRED: %s" % ", ".join(failed))
        return 1
    print("\nGREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
