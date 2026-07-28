"""Rewrite this run's MANIFEST.json with the sha256 of every file it names.

Kept next to the manifest rather than in `tools/` because it is about this run:
re-running it after editing an artefact is how the digests stay true.
"""

import hashlib
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE_RIG = os.path.dirname(os.path.dirname(HERE))

TRACKED = [
    "recheck/__init__.py",
    "recheck/expr.py",
    "recheck/ruleset.py",
    "recheck/certificate.py",
    "recheck/verify.py",
    "recheck/anchors.py",
    "recheck/forgeries.py",
    "recheck/build_cases.py",
    "recheck/verify_all.py",
    "recheck/__main__.py",
    "recheck/README.md",
    "tests/test_recheck.py",
]


def digest(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def main() -> int:
    files = []
    for relative in TRACKED:
        path = os.path.join(ENGINE_RIG, relative)
        files.append({"path": "engine-rig/" + relative, "sha256": digest(path)})
    cases = os.path.join(ENGINE_RIG, "recheck", "cases")
    for name in sorted(os.listdir(cases)):
        if name.endswith(".json"):
            files.append({"path": "engine-rig/recheck/cases/" + name,
                          "sha256": digest(os.path.join(cases, name))})
    for name in ("recheck_report.json", "RUN_STATE.md"):
        path = os.path.join(HERE, name)
        if os.path.exists(path):
            files.append({"path": "engine-rig/runs/%s/%s"
                                  % (os.path.basename(HERE), name),
                          "sha256": digest(path)})

    with open(os.path.join(HERE, "MANIFEST.json"), "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    manifest["files"] = files
    manifest["status"] = "complete"
    manifest["head_commit"] = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ENGINE_RIG,
        capture_output=True, text=True).stdout.strip()
    with open(os.path.join(HERE, "MANIFEST.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print("%d files hashed" % len(files))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
