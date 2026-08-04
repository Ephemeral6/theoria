"""Derive a work-run `MANIFEST.json` instead of typing one.

`CLAUDE.md` requires every experiment to write `runs/<id>/MANIFEST.json` with
`prompt_id`, `branch`, `base_commit`, `utc`, and says the manifest is derived by
the territory's own tool. This territory did not have one: the three work runs
already on disk carry three slightly different key sets, each typed by hand, and
`runs/20260801T0600Z-schema-column/MANIFEST.json` and
`runs/20260802T2040Z-A28-baseline-zero-examined/MANIFEST.json` disagree about
whether the hashed block is called `files` or `artifacts`.

So: one function, one key set, hashes read off disk.

    python -m harness.run_manifest runs/<dir> --prompt-id A28b --note "..."
    python -m harness.run_manifest runs/<dir> --verify

`--verify` re-hashes every listed file and reports the mismatches, which is the
only thing that makes the hashes worth writing down.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from typing import Any, Dict, List

TRACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(TRACK)
TERRITORY = os.path.basename(TRACK)
MANIFEST_NAME = "MANIFEST.json"

# Keys every manifest in this territory carries, in this order.
REQUIRED = ("prompt_id", "branch", "base_commit", "utc")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(*args: str) -> str:
    # cwd is the territory, not `REPO`: `REPO` is the root that repo-relative
    # paths are computed against and a test may point it at a scratch tree, but
    # branch and base_commit must always come from the real checkout.
    try:
        return subprocess.check_output(("git",) + args, cwd=TRACK,
                                       stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return ""


def hashed_files(run_dir: str, extra: List[str]) -> Dict[str, Dict[str, Any]]:
    """Every file in the run directory except the manifest, plus named extras.

    Paths are repo-relative so a manifest can be checked from the repo root.
    """
    out: Dict[str, Dict[str, Any]] = {}
    paths: List[str] = []
    for root, _dirs, names in os.walk(run_dir):
        for n in sorted(names):
            if n == MANIFEST_NAME:
                continue
            paths.append(os.path.join(root, n))
    paths.extend(os.path.join(REPO, p) if not os.path.isabs(p) else p for p in extra)
    for p in sorted(set(paths)):
        if not os.path.exists(p):
            raise SystemExit("manifest input does not exist: %s" % p)
        rel = os.path.relpath(p, REPO).replace(os.sep, "/")
        out[rel] = {"bytes": os.path.getsize(p), "sha256": sha256(p)}
    return out


def build(run_dir: str, prompt_id: str, utc: str, note: str,
          extra: List[str], seed: Any = None, spend: str = "none",
          network: str = "none", results: Any = None,
          tests: str = "", references: List[str] = ()) -> Dict[str, Any]:
    """`references` are delivered paths that are deliberately **not** hashed.

    A hash is only worth writing down if it reproduces on someone else's
    checkout. `core.autocrlf` is true on this machine and `monitor/inbox/` is
    covered by no `eol=lf` attribute, so a file written there with LF is checked
    out with CRLF and any sha256 taken here would be true of nothing anywhere
    else. Naming those paths without hashing them is honest; hashing them is a
    guarantee that fails on the first reader.
    """
    doc: Dict[str, Any] = {
        "prompt_id": prompt_id,
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": _git("rev-parse", "HEAD"),
        "utc": utc,
        "territory": TERRITORY,
        "run_dir": os.path.relpath(run_dir, REPO).replace(os.sep, "/"),
        "note": note,
        "seed": seed,
        "spend": spend,
        "network": network,
        "tests": tests,
        "files": hashed_files(run_dir, extra),
        "references_not_hashed": sorted(references),
    }
    if results is not None:
        doc["results"] = results
    for k in REQUIRED:
        if not doc.get(k):
            raise SystemExit("manifest is missing a required key: %s" % k)
    return doc


def write(run_dir: str, doc: Dict[str, Any]) -> str:
    path = os.path.join(run_dir, MANIFEST_NAME)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def verify(run_dir: str) -> Dict[str, Any]:
    path = os.path.join(run_dir, MANIFEST_NAME)
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    problems: List[str] = []
    for k in REQUIRED:
        if not doc.get(k):
            problems.append("missing required key: %s" % k)
    for rel, rec in sorted((doc.get("files") or {}).items()):
        p = os.path.join(REPO, rel)
        if not os.path.exists(p):
            problems.append("listed file is gone: %s" % rel)
            continue
        if os.path.getsize(p) != rec.get("bytes"):
            problems.append("size changed: %s" % rel)
        if sha256(p) != rec.get("sha256"):
            problems.append("sha256 changed: %s" % rel)
    return {"ok": not problems, "problems": problems,
            "files": len(doc.get("files") or {})}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_dir")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--prompt-id", default="")
    ap.add_argument("--utc", default="")
    ap.add_argument("--note", default="")
    ap.add_argument("--tests", default="")
    ap.add_argument("--extra", action="append", default=[],
                    help="repo-relative file to hash alongside the run dir")
    ap.add_argument("--reference", action="append", default=[],
                    help="repo-relative delivered path to name but not hash")
    ap.add_argument("--results-json", default="",
                    help="path to a JSON file to embed under results")
    args = ap.parse_args(argv)

    run_dir = os.path.abspath(args.run_dir)
    if args.verify:
        res = verify(run_dir)
        print(json.dumps(res, indent=2, sort_keys=True))
        return 0 if res["ok"] else 1

    results = None
    if args.results_json:
        with open(args.results_json, encoding="utf-8") as fh:
            results = json.load(fh)
    doc = build(run_dir, args.prompt_id, args.utc, args.note, args.extra,
                results=results, tests=args.tests, references=args.reference)
    print(write(run_dir, doc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
