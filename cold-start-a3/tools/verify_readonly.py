"""Hash the other tracks' trees, run everything, hash again.

`cold-start-a3` imports `cold-start-a0`'s generators and certify layer,
`engine-rig`'s engines and `theory-compiler`'s parser, and writes to none of
them.  That is a claim about behaviour, so it is measured rather than asserted:
this script takes a sha256 of every file under the four trees, runs A3's whole
pipeline, and takes them again.

It is a **script and not a pytest case**, for the same reason A2's is: two
other sessions work this repository concurrently, so files in those trees
legitimately change while A3 runs, and a test would go red for a reason that
has nothing to do with A3.  Run it when you want the answer; read its report
when you want to know which files moved and whether A3 could have been the
cause.

    python -m tools.verify_readonly
"""

import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)

WATCHED = ("cold-start-a0", "engine-rig", "theory-compiler", "CONTRACTS")
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git", ".toolchain", ".lake",
             "node_modules", ".venv"}


def snapshot():
    digests = {}
    for tree in WATCHED:
        root_dir = os.path.join(REPO, tree)
        if not os.path.isdir(root_dir):
            continue
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
            for name in sorted(files):
                path = os.path.join(root, name)
                rel = os.path.relpath(path, REPO).replace("\\", "/")
                try:
                    with open(path, "rb") as handle:
                        digests[rel] = hashlib.sha256(handle.read()).hexdigest()
                except OSError:
                    digests[rel] = "unreadable"
    return digests


def main() -> int:
    before = snapshot()
    print("hashed %d files under %s" % (len(before), ", ".join(WATCHED)))

    run = subprocess.run([sys.executable, "run_all.py"], cwd=HERE,
                         capture_output=True, text=True, timeout=3600)
    print("run_all.py exit=%d" % run.returncode)
    if run.returncode != 0:
        sys.stdout.write(run.stdout[-4000:])
        sys.stderr.write(run.stderr[-4000:])

    after = snapshot()

    changed = sorted(k for k in before if k in after and before[k] != after[k])
    vanished = sorted(set(before) - set(after))
    appeared = sorted(set(after) - set(before))

    report = {
        "files_hashed": len(before),
        "run_all_exit": run.returncode,
        "changed": changed,
        "vanished": vanished,
        "appeared": appeared,
        "clean": not (changed or vanished or appeared),
    }
    out = os.path.join(HERE, "artifacts", "readonly_report.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")

    print("%d files hashed, %d changed, %d vanished, %d appeared"
          % (len(before), len(changed), len(vanished), len(appeared)))
    for path in (changed + vanished + appeared)[:20]:
        print("   ", path)
    if changed or vanished or appeared:
        print("NOTE: another session works this repo concurrently. A change "
              "here is not proof A3 caused it — check whether A3 has any "
              "reason to touch the listed paths.")
    return 0 if report["clean"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
