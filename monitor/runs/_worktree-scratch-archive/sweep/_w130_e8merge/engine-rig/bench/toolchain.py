"""Which planner produced these numbers, and why you cannot check that from git.

`.toolchain/` is gitignored by design -- roughly 1.6 GB of compiler, planner and
build tree, machine-local, and P-13 argued the case for keeping it out.  The
consequence is a real hole in this repo's provenance story and it is this run's
job to write it down rather than to work around it:

> **Every Fast Downward number in this run was produced by a binary that is not
> in the repository and cannot be reconstructed from it.**  The repo's
> determinism requirement -- fixtures and artifacts byte-reproducible for a fixed
> seed -- does not reach these numbers.  What stands in for it is this record:
> the binary's sha256, the planner's git commit, the compiler, and the exact
> build command, so that a reader on another machine can rebuild *a* binary and
> check whether it hashes the same.

That is weaker than a committed artifact and it is not pretending otherwise.
What it buys is falsifiability: a rebuild that produces a different hash is a
question someone can then ask, where an unrecorded toolchain leaves nothing to
ask about.

The build recipe itself is not restated here.  It lives in
`runs/p13-fd-real/TOOLCHAIN_MANIFEST.md`, which this module points at and whose
key facts it re-derives from the live binary at run time -- so a manifest that
has drifted from the binary shows up as a mismatch instead of being quoted as
though it were still true.
"""

import hashlib
import os
import re
import subprocess
import sys
from typing import Dict, Optional

# The provenance document P-13 wrote.  Repo-relative; this module checks it is
# there rather than duplicating what it says.
TOOLCHAIN_MANIFEST = "engine-rig/runs/p13-fd-real/TOOLCHAIN_MANIFEST.md"

# What that manifest recorded, so this run can say whether the binary in front of
# it is the one the manifest describes.  Copied here as an *expectation to be
# checked*, never as a substitute for measuring.
EXPECTED = {
    "binary_sha256": "645671ae40d825478a043a9f94c856dc6130a11c166b3393837c153c5020aee1",
    "fd_commit": "7120aa01704bfe8e3b9b92c062a4f775bc89c7bd",
    "fd_version": "Fast Downward 24.06+",
    "compiler": "winlibs mingw-w64 GCC 16.1.0 (UCRT, posix threads, SEH, r3)",
}

# The build, in one line, so the manifest is self-contained for a reader who
# never opens TOOLCHAIN_MANIFEST.md.  `-static` is load-bearing -- P-13 spent a
# debugging session on the crash it prevents.
BUILD_COMMAND = (
    'cmake -G Ninja -S src -B builds/release -DCMAKE_BUILD_TYPE=Release '
    '-DCMAKE_C_COMPILER=<mingw64>/bin/gcc.exe '
    '-DCMAKE_CXX_COMPILER=<mingw64>/bin/g++.exe '
    '-DCMAKE_EXE_LINKER_FLAGS="-static" && cmake --build builds/release'
)

_VERSION = re.compile(r"^(Fast Downward .+)$", re.M)
_REVISION = re.compile(r"git revision \[[^\]]*\]:\s*(\S+)")


def sha256(path: str) -> Optional[str]:
    if not os.path.isfile(path):
        return None
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def binary_path(driver: str) -> str:
    """Where the driver's own `util.py` looks for the search binary."""
    return os.path.join(
        os.path.dirname(os.path.abspath(driver)),
        "builds", "release", "bin", "downward.exe",
    )


def probe(driver: Optional[str], repo_root: str) -> Dict[str, object]:
    """Everything about the planner this run can establish by looking at it.

    Returns a record that is honest when the planner is absent: `available` goes
    False and every FD-derived field is None, which is the state a machine
    without `.toolchain/` is in and the state the artifacts must be readable in.
    """
    record: Dict[str, object] = {
        "available": driver is not None,
        "driver": driver,
        "why_not_in_the_repository": (
            ".toolchain/ is gitignored by design (~1.6 GB of compiler, planner "
            "and build tree). See P-13."
        ),
        "reproducibility_gap": (
            "Every Fast Downward number in this run came from a binary that is "
            "not tracked by git and cannot be rebuilt from the repository alone. "
            "The repo's byte-reproducibility requirement does not cover them. "
            "What replaces it is the hash, commit and build command below: a "
            "rebuild that hashes differently is a question a reader can raise."
        ),
        "toolchain_manifest": TOOLCHAIN_MANIFEST,
        "toolchain_manifest_present": os.path.isfile(
            os.path.join(repo_root, TOOLCHAIN_MANIFEST)
        ),
        "build_command": BUILD_COMMAND,
        "expected": dict(EXPECTED),
        "reported_version": None,
        "reported_revision": None,
        "binary": None,
        "binary_sha256": None,
        "binary_bytes": None,
        "matches_p13_manifest": None,
        "notes": [],
    }
    if driver is None:
        record["notes"].append(
            "No Fast Downward reachable: FD rungs are absent from this run, the "
            "bundled rung answers alone, and every FD column reads null."
        )
        return record

    try:
        completed = subprocess.run(
            [sys.executable, driver, "--version"],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=120,
        )
        text = (completed.stdout or "") + (completed.stderr or "")
        version = _VERSION.search(text)
        revision = _REVISION.search(text)
        record["reported_version"] = version.group(1).strip() if version else None
        record["reported_revision"] = revision.group(1) if revision else None
    except (OSError, subprocess.SubprocessError) as exc:
        record["notes"].append("could not run --version: %s" % exc)

    binary = binary_path(driver)
    record["binary"] = binary
    record["binary_sha256"] = sha256(binary)
    record["binary_bytes"] = os.path.getsize(binary) if os.path.isfile(binary) else None

    # The check that makes the expectation above worth writing down.
    checks = {
        "binary_sha256": record["binary_sha256"] == EXPECTED["binary_sha256"],
        "fd_commit": (
            record["reported_revision"] is not None
            and EXPECTED["fd_commit"].startswith(record["reported_revision"])
        ),
        "fd_version": record["reported_version"] == EXPECTED["fd_version"],
    }
    record["checks_against_p13"] = checks
    record["matches_p13_manifest"] = all(checks.values())
    if not record["matches_p13_manifest"]:
        record["notes"].append(
            "This binary is NOT the one runs/p13-fd-real/TOOLCHAIN_MANIFEST.md "
            "describes (%s). The numbers in this run are still measurements, but "
            "they are not comparable to P-13's." % checks
        )
    return record
