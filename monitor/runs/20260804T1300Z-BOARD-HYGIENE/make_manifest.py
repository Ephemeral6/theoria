# -*- coding: utf-8 -*-
"""MANIFEST.json for the board-hygiene run, derived from the tree.

Convention is CLAUDE.md's: required `prompt_id`, `branch`, `base_commit`,
`utc`; optional `files[].sha256`. Every delivered artefact is hashed, including
the board items this run wrote or amended -- a reconciliation whose text can
drift after the fact is a reconciliation nobody can check.

    python monitor/runs/20260804T1300Z-BOARD-HYGIENE/make_manifest.py
    python monitor/runs/20260804T1300Z-BOARD-HYGIENE/make_manifest.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import subprocess
import sys

RUN = "monitor/runs/20260804T1300Z-BOARD-HYGIENE"

#: Everything this run delivered. Listed by hand rather than globbed: a glob
#: would silently absorb a file some other session dropped into the directory,
#: and the manifest's whole job is to say what *this* run put there.
DELIVERED = [
    RUN + "/RUN_STATE.md",
    RUN + "/inbox_recon.txt",
    RUN + "/inbox_recon.json",
    RUN + "/gate-pytest.txt",
    RUN + "/gate-board-list.txt",
    RUN + "/recon_append.py",
    RUN + "/make_manifest.py",
    "monitor/inbox_recon.py",
    "monitor/tests/test_inbox_recon.py",
    "monitor/board/items/A35-the-only-record-of-a-win-is-written-once-at-the-end-of-the-leg.md",
    "monitor/board/items/A36-half-the-desk-bill-buys-nothing-and-the-measurement-that-says-so-has-no-owner.md",
    "monitor/board/items/S51-the-ceiling-moved-to-700-and-the-freeze-manifest-still-publishes-a-negative-balance.md",
    "monitor/board/items/S52-the-inbox-is-a-drop-box-nine-of-ten-addressed-asks-were-never-seen.md",
    "monitor/board/items/A29-theoria-arm-suite-red.md",
    "monitor/board/items/A30-the-arm-spends-its-actions-on-probes-not-on-the-level.md",
    "monitor/board/items/A31-the-win-detector-has-never-fired-and-the-round-total-turns-absence-into-zero.md",
    "monitor/board/items/A32-the-sk48-leg-pays-more-per-desk-call-and-moves-less.md",
    "monitor/board/items/A33-forty-six-baseline-runs-scored-zero-is-wrong-three-times-over.md",
    "monitor/board/items/V31-class-ii-cannot-be-built-and-the-request-to-build-it-was-never-boarded.md",
]


def root() -> str:
    return subprocess.run(["git", "rev-parse", "--show-toplevel"],
                          cwd=os.path.dirname(os.path.abspath(__file__)),
                          capture_output=True, text=True,
                          check=True).stdout.strip()


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def build(top: str) -> dict:
    files = []
    for rel in DELIVERED:
        full = os.path.join(top, rel)
        if not os.path.exists(full):
            raise SystemExit("declared but absent: %s" % rel)
        files.append({"path": rel, "sha256": sha256(full)})
    return {
        "prompt_id": "board-hygiene-2026-08-04",
        "cell": "board-hygiene",
        "territory": "monitor",
        "branch": "q/board-hygiene",
        "base_commit": "4846e66dee64940b3bb457b408db13775728915c",
        "utc": "2026-08-04T13:00:00Z",
        "api_calls": 0,
        "model_calls": 0,
        "usd": 0.0,
        "network": False,
        "sealed_pile_contact": False,
        "what": ("Reconciled the open board against master, filed four items "
                 "from measurements already on disk, and built the inbox "
                 "reconciler. Six items narrowed, none closed -- no open "
                 "item's acceptance clause is met on 4846e66d."),
        "files": sorted(files, key=lambda f: f["path"]),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="re-hash and diff against the committed manifest")
    args = ap.parse_args(argv)
    top = root()
    out = os.path.join(top, RUN, "MANIFEST.json")
    fresh = build(top)
    if args.check:
        with io.open(out, encoding="utf-8") as fh:
            old = json.load(fh)
        bad = [f["path"] for f, g in zip(old["files"], fresh["files"])
               if f != g] or (["<file list differs>"]
                              if len(old["files"]) != len(fresh["files"])
                              else [])
        if bad:
            for path in bad:
                print("MISMATCH %s" % path)
            return 1
        print("MANIFEST reproduces: %d files" % len(fresh["files"]))
        return 0
    with io.open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(fresh, fh, indent=1, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print("wrote %s (%d files)" % (out, len(fresh["files"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
