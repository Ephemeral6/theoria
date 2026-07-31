"""Write this run's MANIFEST.json, hashing every delivered file.

Kept in the run directory rather than in `tools/`: it hashes a fixed list that
belongs to this run, and a general version would need the list passed in anyway.

    python make_manifest.py
"""
import hashlib
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RUN = "proxy/runs/20260731T104757Z-S31"

#: Delivered outside this directory. Hashed too, because "the manifest covers
#: the run directory" is how an edit to the thing the run actually changed goes
#: unrecorded.
ELSEWHERE = [
    "proxy/tests/test_ledger_format_sync.py",
    "proxy/LEDGER_FORMAT.md",
    "proxy/DELIVERY_RULING.md",
]


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def main():
    paths = []
    for root, _dirs, names in os.walk(HERE):
        for name in sorted(names):
            if name == "MANIFEST.json" or name.endswith(".pyc"):
                continue
            full = os.path.join(root, name)
            paths.append(os.path.relpath(full, REPO).replace(os.sep, "/"))
    paths = sorted(paths) + ELSEWHERE

    doc = {
        "prompt_id": "S31-a10-said-done-prove-it",
        "prompt": "monitor/board/claimed/S31-a10-said-done-prove-it.W-1800.md",
        "cell": "S3",
        "territory": "proxy",
        "worker": "W-1800",
        "branch": subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                 cwd=REPO, capture_output=True, text=True
                                 ).stdout.strip(),
        "base_commit": subprocess.run(["git", "rev-parse", "master"], cwd=REPO,
                                      capture_output=True, text=True
                                      ).stdout.strip(),
        "utc": "2026-07-31T10:47:57Z",
        "status": "done",
        "goal": "Fourth pickup of S31. Establish what A10 and S31's own branch "
                "actually delivered against master; turn the reconciliation "
                "ruling from a restated paragraph into a gate; demonstrate the "
                "amount-mismatch negative sample; and prepare the live real-arm "
                "probe fully without firing it.",
        "api_calls": 0,
        "usd_spent": 0.0,
        "network_egress": "none -- the live probe was prepared and not fired; "
                          "the shared spend pool is unchanged at $36.1423 "
                          "spent, 0 held, 0 live reservations",
        "sealed_pile_contact": "none -- the dev-pile whitelist is read from "
                               "arc-recon/data/piles.json's `dev_pile` key and "
                               "the sealed list is never loaded; a refused id "
                               "is not echoed",
        "credentials": "none read, none written; presence-only checks",
        "relay": {
            "chain": ["W-1691 (died mid-sentence)",
                      "W-1702 (8 commits, unpushed)",
                      "W-1710 (pushed and verified)",
                      "W-1800 (this run)"],
            "prior_run": "proxy/runs/20260730T125718Z-S31-a10-said-done-prove-it",
            "finding": "requirements 1, 3 and 4 were already on master and were "
                       "re-verified rather than inherited; "
                       "agent/s31-a10-said-done-prove-it is stale, not "
                       "unmerged, and must not be merged",
        },
        "gates": {
            "cd proxy && python -m pytest": "421 passed in 66.77s "
                                            "(414 baseline + 7 new)",
            "cd proxy && python verify.py": "proxy: green -- 5/5 stages",
        },
        "files": [{"path": p, "sha256": sha256(os.path.join(REPO, p))}
                  for p in paths],
    }
    out = os.path.join(HERE, "MANIFEST.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print("wrote %s -- %d file(s)" % (out, len(doc["files"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
