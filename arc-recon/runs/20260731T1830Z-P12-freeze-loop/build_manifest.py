"""Write MANIFEST.json for this run: per-file sha256 over the delivered bytes.

    python build_manifest.py
"""

import hashlib
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))

ARTEFACTS = ["freeze_audit.json", "RUN_STATE.md"]

#: Read to produce the audit. `campaign_freeze_log.jsonl` is append-only and
#: was NOT rewritten by this run, including the six unadjudicable entries the
#: audit reports: making one's own audit green by editing the record is the
#: disease, not the cure.
INPUTS = [
    "arc-recon/data/campaign_freeze.json",
    "arc-recon/data/campaign_freeze_log.jsonl",
    "arc-recon/data/incidents.jsonl",
]


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def git(*args):
    return subprocess.check_output(["git"] + list(args), cwd=REPO,
                                   text=True).strip()


def main():
    manifest = {
        "prompt_id": "P-12",
        "prompt": "Phase 1 acceptance gaps: campaign_freeze wiring",
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        # merge-base, not `rev-parse master`: master moved under this
        # branch while the work was in flight (21a724ed landed in
        # theoria-arm mid-session), and naming the moving tip would
        # record a base this run was never built on.
        "base_commit": git("merge-base", "master", "HEAD"),
        "utc": "2026-07-31T18:30:00Z",
        "_seed_note": "no randomness: freeze-audit is a deterministic read.",
        "cost": {"api_calls": 0, "model_calls": 0, "usd": 0.0,
                 "_note": "offline. No canary sweep was run; clear-freeze and "
                          "freeze-audit never touch the network."},
        "pile_discipline": {
            "_note": "no game was played. Development-pile ids appear only as "
                     "data inside the freeze log; no sealed-pile id appears in "
                     "any file of this run.",
        },
        "files": [{"path": name, "sha256": sha256(os.path.join(HERE, name))}
                  for name in ARTEFACTS
                  if os.path.exists(os.path.join(HERE, name))],
        "inputs": [{"path": name, "read_only": True,
                    "sha256": sha256(os.path.join(REPO, name))}
                   for name in INPUTS if os.path.exists(os.path.join(REPO, name))],
    }
    out = os.path.join(HERE, "MANIFEST.json")
    with open(out, "w", encoding="utf-8", newline="") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    for entry in manifest["files"] + manifest["inputs"]:
        print("  %s  %s" % (entry["sha256"], entry["path"]))
    print("  -> %s" % out)


if __name__ == "__main__":
    main()
