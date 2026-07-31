"""Same-tree classifier dump. Load ONE release/ package, classify ANOTHER tree.

    python dump_classes.py --release <dir>/release --tree <repo-root> --out x.jsonl

Writes one line per tracked path of --tree: {"path","class","verdict"}.
Read-only: never calls enumerate.main, never writes MANIFEST.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--release", required=True)
    ap.add_argument("--tree", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rel_dir = os.path.abspath(a.release)
    tree = os.path.abspath(a.tree)
    sys.path.insert(0, rel_dir)
    sys.path.insert(0, os.path.join(os.path.dirname(rel_dir), "arc-recon"))

    import check_redlines as redlines  # noqa
    import enumerate as en  # noqa

    # Repoint BOTH readers at the tree under test.
    en.REPO_ROOT = tree
    redlines.REPO_ROOT = tree
    en._HERE = rel_dir

    out = subprocess.run(["git", "-C", tree, "ls-files"],
                         capture_output=True, text=True, check=True).stdout
    paths = sorted(p for p in out.split("\n") if p)
    sys.stderr.write("release=%s tree=%s files=%d\n" % (rel_dir, tree, len(paths)))

    rows = en.build(paths)
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps({"path": r["path"], "class": r["class"],
                                 "verdict": r["verdict"],
                                 "ruled_by": r.get("ruled_by")},
                                sort_keys=True) + "\n")
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["class"]] = counts.get(r["class"], 0) + 1
    sys.stderr.write("counts %s  rows=%d\n" % (json.dumps(counts, sort_keys=True), len(rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
