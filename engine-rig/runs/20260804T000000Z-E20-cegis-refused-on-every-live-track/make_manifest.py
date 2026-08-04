"""Derive this run's MANIFEST.json. Re-run to re-verify the published hashes."""

import hashlib
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

DELIVERED = [
    "engine-rig/engines/cegis_miner/atoms.py",
    "engine-rig/engines/cegis_miner/miner.py",
    "engine-rig/engines/cegis_miner/__init__.py",
    "engine-rig/engines/cegis_miner/README.md",
    "engine-rig/fixtures/ring_world.py",
    "engine-rig/tests/test_cegis_ring_world.py",
    "engine-rig/runs/20260804T000000Z-E20-cegis-refused-on-every-live-track/verify_e20.py",
    "engine-rig/runs/20260804T000000Z-E20-cegis-refused-on-every-live-track/findings.json",
    "engine-rig/runs/20260804T000000Z-E20-cegis-refused-on-every-live-track/RUN_STATE.md",
]


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", REPO, *args], text=True).strip()


def main():
    manifest = {
        "prompt_id": "E20-cegis-miner-refused-on-every-live-track",
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        # the commit this branch was cut from, not wherever master has since
        # moved -- other sessions commit to master while this one runs.
        "base_commit": git("merge-base", "HEAD", "master"),
        "master_at_write_time": git("rev-parse", "master"),
        "utc": "2026-08-04T00:00:00Z",
        "territory": "engine-rig",
        "lane": "generic",
        "method": (
            "replay both mdl_segmenter operators and cegis_miner over the recorded "
            "frames of theoria-arm/runs/20260731T1430Z-A3-level2-carried-r3 "
            "(g50t-5849a774, development pile), reproduce the recorded refusal "
            "exactly, and separate its three causes; regression-test the fix on a "
            "synthetic fixture of the same world class"
        ),
        "api_calls": 0,
        "network": False,
        "model_calls": 0,
        "cost_usd": 0.0,
        "sealed_pile_contact": "none",
        "inputs": {
            "recorded_ledger": (
                "theoria-arm/runs/20260731T1430Z-A3-level2-carried-r3/ledger.jsonl"),
            "read_only": True,
            "games": ["g50t-5849a774"],
            "pile": "development",
            "frames_with_pixels": 34,
            "note": ("read for its frames; no pixel data is written into engine-rig. "
                     "verify_e20.py refuses any game outside the development pile."),
        },
        "gates": {
            "pytest": "engine-rig: python -m pytest",
            "recheck": "engine-rig: python -m recheck.verify_all",
        },
        "seed": None,
        "determinism": (
            "no RNG; build_vocabulary sorts the alphabet, enumerate_frontier sorts "
            "its atoms, so output does not depend on input order"
        ),
        "status": "delivered",
        "files": [],
    }
    for rel in DELIVERED:
        path = os.path.join(REPO, rel)
        manifest["files"].append({
            "path": rel,
            "sha256": sha256(path),
            "bytes": os.path.getsize(path),
        })
    out = os.path.join(HERE, "MANIFEST.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
