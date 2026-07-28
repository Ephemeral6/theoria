"""Recompute a run's `MANIFEST.json` `files[]` from what is actually on disk.

    python -m tools.refresh_manifest runs/<id>            # rewrite
    python -m tools.refresh_manifest runs/<id> --check     # exit 1 on drift

A manifest written half way through a run goes stale the moment anything it
lists is edited again, and a stale hash is worse than no hash: it reads as
provenance and is not. This tool exists so refreshing it before the final commit
is one command rather than a habit, and `--check` makes the drift visible.

Every file in the run directory is listed (except the manifest itself, which
cannot contain its own hash), plus whatever `extra_paths` the manifest already
names outside it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from typing import Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(ROOT)


def digest(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def entries(run_dir: str, extra: List[str]) -> List[Dict[str, str]]:
    out = []
    for path in extra:
        full = os.path.join(REPO, path)
        if not os.path.exists(full):
            raise SystemExit("manifest names a file that does not exist: %s" % path)
        out.append({"path": path, "sha256": digest(full)})
    for base, _, names in os.walk(run_dir):
        for name in sorted(names):
            if name == "MANIFEST.json":
                continue
            full = os.path.join(base, name)
            rel = os.path.relpath(full, REPO).replace("\\", "/")
            out.append({"path": rel, "sha256": digest(full)})
    return sorted(out, key=lambda e: e["path"])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    run_dir = os.path.abspath(args.run_dir)
    manifest_path = os.path.join(run_dir, "MANIFEST.json")
    with open(manifest_path, encoding="utf-8") as handle:
        manifest = json.load(handle)

    inside = os.path.relpath(run_dir, REPO).replace("\\", "/")
    extra = [e["path"] for e in manifest.get("files", [])
             if not e["path"].startswith(inside)]
    fresh = entries(run_dir, extra)

    if args.check:
        if manifest.get("files") == fresh:
            return 0
        was = {e["path"]: e["sha256"] for e in manifest.get("files", [])}
        for entry in fresh:
            if was.get(entry["path"]) != entry["sha256"]:
                print("drifted or new: %s" % entry["path"], file=sys.stderr)
        for path in sorted(set(was) - {e["path"] for e in fresh}):
            print("listed but gone: %s" % path, file=sys.stderr)
        return 1

    manifest["files"] = fresh
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("%s: %d file(s)" % (os.path.basename(manifest_path), len(fresh)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
