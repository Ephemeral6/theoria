"""Write this run's MANIFEST.json — required fields plus sha256 for every file."""

import datetime
import hashlib
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))

TRACKED = (
    "worldgen/tests/determinism_sandbox.py",
    "worldgen/tests/test_determinism_gate.py",
    "worldgen/RUN_STATE.md",
    "monitor/inbox/20260728T175900Z-V16-determinism-definition-gap.md",
)


def sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def git(*args):
    return subprocess.run(("git",) + args, cwd=ROOT, capture_output=True,
                          text=True).stdout.strip()


def main():
    files = []
    for rel in TRACKED:
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        files.append({"path": rel, "sha256": sha256(path),
                      "size": os.path.getsize(path)})
    rundir = os.path.relpath(HERE, ROOT).replace(os.sep, "/")
    for name in sorted(os.listdir(HERE)):
        if name in ("MANIFEST.json", "__pycache__"):
            continue
        path = os.path.join(HERE, name)
        if os.path.isfile(path):
            files.append({"path": "%s/%s" % (rundir, name), "sha256": sha256(path),
                          "size": os.path.getsize(path)})

    manifest = {
        "prompt_id": "V16-determinism-has-no-caller",
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": git("rev-parse", "HEAD"),
        "utc": datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "lane": "verify",
        "territory": "worldgen",
        "what": "a negative control for worldgen.build.check_determinism, which "
                "no test in this repository had ever caused to run",
        "worktree_clean_outside_this_run": git("status", "--short", "worldgen/") .splitlines(),
        "files": files,
    }
    with open(os.path.join(HERE, "MANIFEST.json"), "w",
              encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
