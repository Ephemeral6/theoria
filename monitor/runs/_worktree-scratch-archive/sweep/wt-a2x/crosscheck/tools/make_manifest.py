"""Write `runs/<stamp>/MANIFEST.json` -- what ran, on what, hashed.

Same shape the other arms in this repository use (`cold-start-a3/runs/p-17/`):
`prompt_id`, `branch`, `base_commit`, `head_commit`, the determinism pins, and a
sha256 per artefact and per book. The point is that a reader can check any claim
in FINDINGS.md against the bytes that produced it without trusting the prose.

    python -m crosscheck.tools.make_manifest runs/2026-07-28T00-00-00Z-a2x

The timestamp is passed in rather than read from the clock: a manifest that
changes when nothing changed is not evidence.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from typing import Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Everything the run is accountable for, relative to the repo root.
BOOKS = [
    "crosscheck/s_on_c/manual.dsl",
    "crosscheck/c_on_s/manual.dsl",
]
GENERATED = [
    "crosscheck/s_on_c/predictor.py",
    "crosscheck/c_on_s/predictor.py",
]


def sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=HERE, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return ""


def hash_tree(root: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            out[os.path.relpath(full, root).replace(os.sep, "/")] = sha256(full)
    return out


def build(run_dir: str, prompt_id: str, status: str, note: str) -> Dict[str, object]:
    absolute = run_dir if os.path.isabs(run_dir) else os.path.join(HERE, run_dir)
    manifest: Dict[str, object] = {
        "prompt_id": prompt_id,
        "status": status,
        "note": note,
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "head_commit": _git("rev-parse", "HEAD"),
        "base_commit": _git("merge-base", "HEAD", "master"),
        "dirty": bool(_git("status", "--porcelain")),
        "python": "%d.%d.%d" % sys.version_info[:3],
        "seed": {
            "rng": "none -- every stage here is structural; no random numbers "
                   "are drawn and no clock is read",
            "timestamp": os.path.basename(absolute.rstrip("/\\")),
        },
        "artifacts": hash_tree(absolute),
    }
    for label, paths in (("books", BOOKS), ("generated_forms", GENERATED)):
        entries = {}
        for rel in paths:
            full = os.path.join(HERE, rel)
            if os.path.isfile(full):
                entries[rel] = sha256(full)
        manifest[label] = entries
    return manifest


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir")
    parser.add_argument("--prompt-id", default="A2-crosscheck")
    parser.add_argument("--status", default="complete")
    parser.add_argument("--note", default="")
    args = parser.parse_args(argv)

    absolute = args.run_dir if os.path.isabs(args.run_dir) \
        else os.path.join(HERE, args.run_dir)
    manifest = build(absolute, args.prompt_id, args.status, args.note)
    out = os.path.join(absolute, "MANIFEST.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
    print("%s  (%d artefacts)" % (out, len(manifest["artifacts"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
