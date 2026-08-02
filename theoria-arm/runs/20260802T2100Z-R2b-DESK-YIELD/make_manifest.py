"""Derive this analysis run's MANIFEST.json from the files on disk.

Offline-analysis runs under `theoria-arm/runs/` do not go through
`armtools.archive` -- that tool reconciles a score, a spend ledger and a
constraint-8 count, and this run has none of those because it made no model
call.  What CLAUDE.md requires of every run is the four provenance fields and,
optionally, a per-file digest; that is what this builds, and it is kept beside
the artefacts so the hashes can be recomputed rather than trusted.

    python make_manifest.py            # write MANIFEST.json
    python make_manifest.py --check    # re-hash and diff, exit 1 on drift
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKIP = {"MANIFEST.json", "__pycache__"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def files():
    out = []
    for name in sorted(os.listdir(HERE)):
        if name in SKIP or not os.path.isfile(os.path.join(HERE, name)):
            continue
        path = os.path.join(HERE, name)
        out.append({"path": name, "bytes": os.path.getsize(path),
                    "sha256": sha256(path)})
    return out


def git(*args):
    try:
        return subprocess.check_output(["git"] + list(args), cwd=HERE,
                                       text=True).strip()
    except Exception:
        return None


def build():
    return {
        "prompt_id": "R2b-desk-cost-forensics",
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": git("rev-parse", "HEAD"),
        "utc": "2026-08-02T21:00:00Z",
        "territory": "theoria-arm",
        "lane": "campaign",
        "what": ("Why the two R2b legs disagreed. The obvious hypothesis -- desk "
                 "cost proportional to manual size -- is refuted in both "
                 "directions: sk48 sent the SMALLER prompt (85,904 vs 128,759 "
                 "chars), carried the SMALLER manual (32,522 vs 72,299), and paid "
                 "3.5x per action. Output tokens carry 69% of the bill on both "
                 "legs, and four consecutive sk48 calls -- $14.93, 74% of the "
                 "leg's spend -- returned replies with no === THEORY === block, "
                 "so the books never moved and the leg never left step 10."),
        "leg": "offline forensics -- no model call, no API call, no spend",
        "inputs": [
            "runs/20260801T044640Z-R2b-g50t-a (desk/, desk_log.json, ledger.jsonl, books/snapshots)",
            "runs/20260801T044640Z-R2b-sk48-b (same)",
            "armtools/prompt_census.py -- the input-side census, used as given",
        ],
        "built_by": ["armtools/desk_yield.py (new)", "armtools/prompt_census.py"],
        "sealed_pile_contact": "none -- both legs are development-pile games, "
                               "and nothing under environment_files/ was opened",
        "spend": {"usd": 0.0, "model_calls": 0,
                  "note": "reads archived records only"},
        "seed": None,
        "files": files(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    path = os.path.join(HERE, "MANIFEST.json")
    fresh = build()
    if args.check:
        with open(path, encoding="utf-8") as fh:
            old = json.load(fh)
        drift = [f for f in fresh["files"]
                 if f not in old.get("files", [])]
        missing = [f["path"] for f in old.get("files", [])
                   if f["path"] not in {g["path"] for g in fresh["files"]}]
        if drift or missing:
            print("MANIFEST drift: changed=%s missing=%s"
                  % ([f["path"] for f in drift], missing))
            return 1
        print("MANIFEST re-hashes clean over %d files" % len(fresh["files"]))
        return 0
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(fresh, fh, indent=1, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print("wrote %s over %d files" % (path, len(fresh["files"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
