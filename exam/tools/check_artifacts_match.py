"""Is what is committed under `exam/artifacts/` what this code produces?

    python -m exam.tools.check_artifacts_match            # build fresh, compare
    python -m exam.tools.check_artifacts_match --built D  # compare an existing D

`exam/verify.py` printed GREEN for weeks without ever answering that question.
Three of its stages -- `build_papers`, `run_exam --calibrate`, `run_selftest` --
**overwrote the tracked artefacts in place**, and no stage looked at what had
been there first.  The determinism stage compares two *fresh* builds against
each other in memory (`PYTHONHASHSEED` 7 vs 99) and never opens a committed
file.  So the four sheets, four keys, `calibration.json`, `exam_summary.json`,
`selftest.json`, `matrix/` and `build_manifest.json` could have been generated
by a rubric that no longer exists, and every gate would still have been green --
which is what happened on the branches lagging `18a39417`, where the committed
`rubric_digest` read `e06bdf52` and a rebuild produced `63ce1eab`.

This is the same defect one level up from V21: a check ran, went green, and was
used as evidence, while measuring something other than what its name claims.
Every number the papers quote out of `exam/artifacts/` rested on it.

**Comparison, never silent adoption.**  The build under test goes to a shadow
tree; the tracked tree is not written to at any point.  A mismatch is reported
as a mismatch and the caller decides -- adoption is running `build_papers` on
purpose, with the diff and the reason in a commit message.  A gate that fixed
the drift it found would erase its own finding, which is exactly how the
original defect stayed invisible.

Two questions, both of which must hold:

1. **the working tree still holds what was committed** -- `git diff` over
   `exam/artifacts` is empty.  A hand-edited byte, or an in-place build by some
   earlier command, fails here.
2. **a fresh build reproduces it** -- every tracked artefact a producer rewrote
   in the shadow tree is byte-identical to its committed twin.

The shadow tree is seeded as a *copy* of `exam/artifacts` rather than starting
empty, because the producers read as well as write -- `run_exam` marks the
submissions under `answers/` against the keys under `truth/` -- and a producer
run against an empty tree would be a different run.  Files no producer touches
therefore compare equal trivially, and the report says how many were actually
rebuilt so the coverage is visible rather than assumed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Dict, List, Optional, Sequence, Tuple

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

TRACKED_ROOT = "exam/artifacts"

#: The producers `exam/verify.py` runs, in its order.  Each writes into
#: whatever `EXAM_ARTIFACTS_DIR` names, so pointing them at the shadow tree is
#: the whole of the redirect.
PRODUCERS: Sequence[Tuple[str, Sequence[str]]] = (
    ("build_papers", ("-m", "exam.tools.build_papers")),
    ("run_exam --calibrate", ("-m", "exam.tools.run_exam", "--calibrate")),
    # Not `--quick`: the committed `selftest.json` carries a `fault_matrix`,
    # and a quick run writes the file without one, so the cheap variant would
    # report drift that is only its own missing half.
    ("run_selftest", ("-m", "exam.tools.run_selftest")),
    # Endpoint 2's pre-registration and its control transcripts. It reads the
    # key and the answers directory and writes `prereg/` and
    # `endpoint_controls/`, so it belongs on the same redirect as the rest: a
    # pre-registration that could be rebuilt into a different document without
    # the gate noticing would be a pre-registration in name only.
    ("build_prereg", ("-m", "exam.tools.build_prereg")),
)


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tracked_artefacts() -> List[str]:
    out = subprocess.run(["git", "ls-files", TRACKED_ROOT], cwd=REPO,
                         capture_output=True, text=True, check=True).stdout
    return [p for p in out.splitlines() if p.strip()]


def working_tree_is_committed() -> Tuple[bool, str]:
    """Question 1: does `exam/artifacts` on disk still hold what git has?

    `--exit-code` against HEAD, so a staged-but-uncommitted edit counts as a
    difference too: the gate's subject is what is *committed*, not what is
    staged.
    """
    diff = subprocess.run(["git", "diff", "--exit-code", "--stat", "HEAD", "--",
                           TRACKED_ROOT], cwd=REPO, capture_output=True, text=True)
    return diff.returncode == 0, (diff.stdout + diff.stderr).strip()


def seed_shadow(dest: str) -> Dict[str, Tuple[str, int]]:
    """Copy `exam/artifacts` to `dest`; return `{relpath: (sha256, mtime_ns)}`.

    The mtime is what makes the coverage line honest.  A producer that rewrites
    a file with identical bytes is doing its job, and counting only the files
    whose *contents* changed would report "0 rebuilt" on a perfectly green run,
    which reads like the gate compared nothing.  Touched-vs-differing are two
    numbers and the report prints both.
    """
    src = os.path.join(REPO, "exam", "artifacts")
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    seed: Dict[str, Tuple[str, int]] = {}
    for rel in tracked_artefacts():
        path = os.path.join(dest, os.path.relpath(rel, TRACKED_ROOT))
        if os.path.exists(path):
            seed[rel] = (_sha256_file(path), os.stat(path).st_mtime_ns)
    # Beside the shadow tree, never inside it: a file inside would be an
    # artefact the comparison then had to special-case.  `--built` reads it so
    # a caller that seeded and built the tree itself (exam/verify.py) still
    # gets the coverage numbers.
    with open(_seed_sidecar(dest), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({k: list(v) for k, v in seed.items()}, fh,
                  indent=2, sort_keys=True)
    return seed


def _seed_sidecar(shadow: str) -> str:
    return os.path.join(os.path.dirname(os.path.abspath(shadow)),
                        "seed_digests.json")


def load_seed(shadow: str) -> Optional[Dict[str, Tuple[str, int]]]:
    path = _seed_sidecar(shadow)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return {k: (v[0], int(v[1])) for k, v in json.load(fh).items()}


def run_producers(shadow: str, *, verbose: bool = True) -> List[Tuple[str, int]]:
    env = dict(os.environ, EXAM_ARTIFACTS_DIR=shadow)
    results = []
    for label, args in PRODUCERS:
        proc = subprocess.run([sys.executable, *args], cwd=REPO, env=env,
                              capture_output=not verbose, text=True)
        results.append((label, proc.returncode))
    return results


def compare(shadow: str, seed: Optional[Dict[str, Tuple[str, int]]] = None
            ) -> Tuple[List[str], List[str], List[str], List[str]]:
    """-> (mismatched, touched, changed, missing) for every tracked artefact.

    `touched` is what a producer wrote at all, `changed` what it wrote
    differently from the seed, `mismatched` what does not equal the committed
    file.  Only the last one gates; the first two are the gate stating its own
    coverage, so "green" cannot mean "compared nothing".
    """
    mismatched: List[str] = []
    touched: List[str] = []
    changed: List[str] = []
    missing: List[str] = []
    for rel in tracked_artefacts():
        committed = os.path.join(REPO, rel)
        built = os.path.join(shadow, os.path.relpath(rel, TRACKED_ROOT))
        if not os.path.exists(built):
            missing.append(rel)
            continue
        built_digest = _sha256_file(built)
        if seed is not None and rel in seed:
            seed_digest, seed_mtime = seed[rel]
            if os.stat(built).st_mtime_ns != seed_mtime:
                touched.append(rel)
            if seed_digest != built_digest:
                changed.append(rel)
        if not os.path.exists(committed):
            missing.append(rel)
            continue
        if built_digest != _sha256_file(committed):
            mismatched.append(rel)
    return mismatched, touched, changed, missing


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--built", metavar="DIR",
                        help="compare an already-built shadow tree instead of "
                             "building one (exam/verify.py passes the tree its "
                             "own stages wrote)")
    parser.add_argument("--keep", action="store_true",
                        help="do not delete the shadow tree this run built")
    args = parser.parse_args(list(argv) if argv is not None else None)

    clean, detail = working_tree_is_committed()
    print("working tree vs HEAD under %s: %s"
          % (TRACKED_ROOT, "clean" if clean else "DIFFERS"))
    if not clean:
        print(detail)

    tmp = None
    seed: Optional[Dict[str, Tuple[str, int]]] = None
    if args.built:
        shadow = os.path.abspath(args.built)
        seed = load_seed(shadow)
        print("comparing an existing build: %s" % shadow)
    else:
        tmp = tempfile.mkdtemp(prefix="exam-shadow-")
        shadow = os.path.join(tmp, "artifacts")
        seed = seed_shadow(shadow)
        print("building into a shadow tree (the tracked tree is not written to)")
        for label, code in run_producers(shadow, verbose=False):
            print("  %-22s exit %d" % (label, code))
            if code != 0:
                print("a producer failed; the comparison below would be "
                      "meaningless, so this is red on its own")
                return 1

    mismatched, touched, changed, missing = compare(shadow, seed)
    n = len(tracked_artefacts())
    if seed is not None:
        print("producers rewrote %d of %d tracked artefacts; %d of those differ "
              "from the seed" % (len(touched), n, len(changed)))
    if tmp and not args.keep:
        shutil.rmtree(tmp, ignore_errors=True)
    elif tmp:
        print("shadow tree kept at %s" % shadow)

    if not mismatched and not missing and clean:
        print("artifacts match committed: %d tracked files, all reproduced" % n)
        return 0

    for rel in mismatched:
        print("  MISMATCH  %s" % rel)
    for rel in missing:
        print("  MISSING   %s" % rel)
    print("\nWhat is committed under %s is not what this code produces. Two "
          "dispositions and they are not interchangeable: if the artefacts are "
          "stale, rebuild them (`python -m exam.tools.build_papers`, "
          "`run_exam --calibrate`, `run_selftest`) and commit the diff with the "
          "reason; if the generator changed by mistake, revert the generator. "
          "Deciding which is a judgement, so this gate reports and does not "
          "adopt." % TRACKED_ROOT)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
