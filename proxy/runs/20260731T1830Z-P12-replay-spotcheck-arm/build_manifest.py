"""Write MANIFEST.json for this run: per-file sha256 over the delivered bytes.

Deliberately hashes the file as written, not a re-serialisation. A verifier
that re-canonicalises before hashing is checking that today's serialiser
agrees with itself, not that the bytes on disk are the bytes that were
published — the same argument `proxy/ledger.py:line_hash` makes.

    python build_manifest.py
"""

import hashlib
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))

ARTEFACTS = [
    "replay_spotcheck_g50t_arm.json",
    "replay_spotcheck_g50t_arm_strict.json",
    "replay_spotcheck_sk48_arm.json",
    "crosscheck_arm_vs_baseline.json",
    "crosscheck_baseline.py",
    "RUN_STATE.md",
]

#: Read, never written. Another territory's output.
INPUTS = [
    "theoria-arm/runs/20260731T1240Z-A3-level2-carried/ledger.jsonl",
    "theoria-arm/runs/20260731T1310Z-A3-level2-carried-r2/ledger.jsonl",
    "theoria-arm/runs/20260731T1430Z-A3-level2-carried-r3/ledger.jsonl",
    "theoria-arm/runs/20260731T1500Z-A3-sk48-carried-l1/ledger.jsonl",
    "proxy/runs/20260731T154336Z-P1-replay-spotcheck-2/replay_spotcheck_g50t.json",
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
        "prompt": "Phase 1 acceptance gaps: 复放抽检 ⟨2⟩ 局 + campaign_freeze",
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": git("rev-parse", "master"),
        "utc": "2026-07-31T18:30:00Z",
        "_seed_note": "no randomness: the spot check and the cross-check are "
                      "deterministic reads over fixed inputs.",
        "cost": {"api_calls": 0, "model_calls": 0, "usd": 0.0,
                 "_note": "zero network. Every frame hash compared here was "
                          "already on disk before this run started."},
        "pile_discipline": {
            "games": ["g50t-5849a774", "sk48-d8078629"],
            "_note": "both development pile (arc-recon/data/piles.json). No "
                     "sealed-pile id appears in any file of this run.",
        },
        "files": [{"path": name, "sha256": sha256(os.path.join(HERE, name))}
                  for name in ARTEFACTS if os.path.exists(os.path.join(HERE, name))],
        "inputs": [{"path": name, "read_only": True,
                    "sha256": sha256(os.path.join(REPO, name))}
                   for name in INPUTS if os.path.exists(os.path.join(REPO, name))],
    }
    out = os.path.join(HERE, "MANIFEST.json")
    with open(out, "w", encoding="utf-8", newline="") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    # ASCII on stdout: this repository's Windows consoles are GBK, and a
    # manifest builder that crashes on its own summary line after writing the
    # file is a builder that looks like it failed when it did not.
    for entry in manifest["files"] + manifest["inputs"]:
        print("  %s  %s" % (entry["sha256"], entry["path"]))
    print("  -> %s" % out)


if __name__ == "__main__":
    main()
