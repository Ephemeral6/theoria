"""Derive this run's MANIFEST.json. Never hand-write the hashes.

The monitor territory has no shared manifest generator (P1PUSH4's manifest was
produced ad hoc), so this run carries its own, in the shape
`theoria-arm/runs/20260801T0900Z-R2-frontier-by-generation/make_manifest.py`
established: declare the artefacts, hash them from disk, read branch and
base_commit from git rather than from memory.

    python make_manifest.py            # write MANIFEST.json
    python make_manifest.py --check    # re-hash and diff against the file

`--check` is the half that makes the other half worth anything: a manifest that
has never been re-derived is a list of numbers nobody has looked at twice.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

# The delivered surface of this run, repo-relative. Board items first.
BOARD_ITEMS = [
    "A22-r3-generated-frontier-round",
    "A23-anchor-drift-on-the-default-leg",
    "A24-round-scoreboard-columns-are-null",
    "A25-change-sentence-not-bound-to-the-knob",
    "A26-frontier-width-and-probe-yield-as-scoreboard",
    "A27-freeze-gate-reads-the-rewritable-half",
    "A28-desk-through-the-model-proxy-behind-a-flag",
    "C15-the-unnameable-cell-has-no-home-in-the-dsl",
    "S45-launch-blockers-915-916-and-the-reason-floor",
    "S46-turn-costs-mixes-two-axes",
    "S47-refusal-wave-retry-predicate",
    "S48-schema-column-withdrawal-claims-text",
    "V28-exam-four-tests-must-flip",
    "V29-one-proxy-validated-not-two",
]
RUN_DIR = "monitor/runs/2026-08-01T035719Z-BOARDREFILL"
ARTIFACTS = ["monitor/board/items/%s.md" % i for i in BOARD_ITEMS] + [
    "%s/INBOX_RECONCILE.md" % RUN_DIR,
    "%s/RUN_STATE.md" % RUN_DIR,
    "%s/make_manifest.py" % RUN_DIR,
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args):
    return subprocess.check_output(["git"] + list(args), cwd=REPO).decode().strip()


def artifacts():
    out = {}
    for rel in sorted(ARTIFACTS):
        p = os.path.join(REPO, rel)
        if not os.path.exists(p):
            # Absence is recorded as absence, never as an empty hash.
            out[rel] = {"absent": True}
            continue
        out[rel] = {"bytes": os.path.getsize(p), "sha256": sha256(p)}
    return out


def build():
    return {
        "artifacts": artifacts(),
        "base_commit": git("rev-parse", "HEAD"),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "determinism": (
            "No stochastic step; seed is null. Hashes are over files on disk; "
            "`--check` re-derives them."
        ),
        "prompt_id": "BOARDREFILL",
        "results": {
            "board_items_written": len(BOARD_ITEMS),
            "items_with_api_spend": ["A22-r3-generated-frontier-round"],
            "inbox_asks_unclaimed": 8,
            "inbox_asks_claimed": 1,
            "spend_this_run_usd": 0.0,
        },
        "utc": "2026-08-01T035719Z",
        "utc_source": (
            "machine clock at run time, unedited. It reads earlier than artefacts "
            "this run cites (R2 at 0900Z, freeze->exam at 0700Z); the skew is "
            "recorded in RUN_STATE.md rather than hand-corrected."
        ),
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
        bad = [k for k in fresh["artifacts"]
               if old.get("artifacts", {}).get(k) != fresh["artifacts"][k]]
        missing = [k for k in old.get("artifacts", {}) if k not in fresh["artifacts"]]
        if bad or missing:
            print("MANIFEST MISMATCH")
            for k in bad:
                print("  changed/absent:", k)
            for k in missing:
                print("  dropped from declaration:", k)
            return 1
        print("MANIFEST OK: %d artifacts re-hashed and identical" % len(fresh["artifacts"]))
        return 0
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(fresh, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    print("wrote %s (%d artifacts)" % (path, len(fresh["artifacts"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
