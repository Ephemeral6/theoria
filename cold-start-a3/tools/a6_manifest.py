"""Write `runs/<id>/MANIFEST.json` for A6.

Separate from `run_a6.py` on purpose.  The acceptance artefact is asserted
byte-reproducible by `tests/test_a6.py`, and a manifest carries `head_commit` —
which changes on every commit, including the commit that records the manifest.
Folding one into the other would make a determinism test that fails whenever the
work is saved.

Run after `run_a6.py` and `python -m a6carry.score`:

    python -m tools.a6_manifest
"""

import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

RUN_ID = "20260728T1800Z-A6-transfer-protocol"
RUN = os.path.join(ROOT, "runs", RUN_ID)
REPO = os.path.dirname(ROOT)

PROMPT_ID = "A6-transfer-protocol"
BRANCH = "agent/a6-transfer-protocol"
UTC = "2026-07-29T07:20:00Z"


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        digest.update(handle.read())
    return digest.hexdigest()


def git(*args):
    result = subprocess.run(("git",) + args, cwd=REPO, capture_output=True,
                            text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def tree(root, prefix):
    out = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for name in sorted(files):
            path = os.path.join(base, name)
            key = prefix + "/" + os.path.relpath(path, root).replace(os.sep, "/")
            out[key] = sha256_file(path)
    return out


def main():
    files = {}
    for name in ("a6_acceptance.json", "scoring_push_manual.json", "PLAN.md"):
        path = os.path.join(RUN, name)
        if os.path.exists(path):
            files[name] = sha256_file(path)
    for sub in ("artifacts", "generated", "packs"):
        path = os.path.join(RUN, sub)
        if os.path.isdir(path):
            files.update(tree(path, sub))

    books = {}
    for rel in ("theory/push/domain.dsl", "theory/push/playbook.dsl",
                "theory/domain.dsl", "theory/playbook.dsl"):
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        if os.path.exists(path):
            books[rel] = sha256_file(path)

    source = {}
    for name in sorted(os.listdir(os.path.join(ROOT, "a6carry"))):
        if name.endswith(".py"):
            source["a6carry/" + name] = sha256_file(
                os.path.join(ROOT, "a6carry", name))
    source["run_a6.py"] = sha256_file(os.path.join(ROOT, "run_a6.py"))

    head = git("rev-parse", "HEAD")
    base = git("merge-base", "master", "HEAD")

    manifest = {
        "prompt_id": PROMPT_ID,
        "branch": BRANCH,
        "base_commit": base,
        "head_commit": head,
        "utc": UTC,
        "status": "complete",
        "python": "%d.%d.%d" % sys.version_info[:3],
        "seed": {
            "THEORIA_DETERMINISTIC_IDS": "1",
            "THEORIA_FIXED_TIME": "2026-07-28T00:00:00Z",
            "rng": "none — A6 draws no random numbers; the planner is "
                   "`stub-bfs` and the scorer's BFS is ordered by "
                   "`State.key()`, so determinism is structural",
        },
        "note": (
            "Two lives.  W-5201 wrote `a6carry/` and `theory/push/` on "
            "2026-07-28 and died before committing a line of it or running any "
            "of it; RES-1 rescued it at 6ee8538, found four defects that stop "
            "the run on contact, and built the acceptance, the scorer and the "
            "tests.  The salvage commit is deliberately separate so the two "
            "are diffable."
        ),
        "reproduce": [
            "python run_a6.py",
            "python -m a6carry.score",
            "python -m pytest",
        ],
        "books": books,
        "source": source,
        "files": files,
    }

    out = os.path.join(RUN, "MANIFEST.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, indent=2, sort_keys=True,
                                ensure_ascii=False) + "\n")
    print("wrote %s (%d artefact hashes, %d books, %d source files)"
          % (os.path.relpath(out, ROOT).replace(os.sep, "/"),
             len(files), len(books), len(source)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
