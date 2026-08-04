"""Regenerate this run's MANIFEST.json.

Offline and deterministic: it hashes files and shells out to `git` for the
branch and the base commit. It writes nothing except `MANIFEST.json`, so a
reader who distrusts the published hashes can re-run it and diff.

`MANIFEST.json` itself is excluded from `files` -- a manifest cannot carry its
own digest, and pretending otherwise is the kind of self-reference that looks
like provenance and checks nothing.

    cd proxy/runs/20260802T0900Z-S47-refusal-wave-retry-predicate
    python make_manifest.py
"""

import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

#: The base commit is pinned as a literal, not read from `git merge-base`.
#: Master advanced past it while this ticket was open (`1e5b3f00` -> `9e478dd8`),
#: and a manifest whose provenance moves when someone else merges is a manifest
#: that records the reader's day rather than the run's.
BASE_COMMIT = "1e5b3f00dfb40fcc73f582a5de2390d1d3466844"

#: Everything this ticket delivered, in the order a reader should meet it.
DELIVERED = [
    "proxy/forward.py",
    "proxy/env_proxy.py",
    "proxy/tests/test_forward_retry_predicate.py",
    "proxy/tools/refusal_replay.py",
    "proxy/tests/test_refusal_replay.py",
    "proxy/DECISIONS.md",
    "proxy/CONTRACT_CHANGES.md",
    "proxy/LEDGER_FORMAT.md",
    "proxy/STATUS.md",
    "proxy/README.md",
    "proxy/runs/20260802T0900Z-S47-refusal-wave-retry-predicate/RUN_STATE.md",
    "proxy/runs/20260802T0900Z-S47-refusal-wave-retry-predicate/NOTES.md",
    "proxy/runs/20260802T0900Z-S47-refusal-wave-retry-predicate/d-s47-001.md",
    "proxy/runs/20260802T0900Z-S47-refusal-wave-retry-predicate/refusal_replay.json",
    "proxy/runs/20260802T0900Z-S47-refusal-wave-retry-predicate/verify_s47.sh",
    "proxy/runs/20260802T0900Z-S47-refusal-wave-retry-predicate/make_manifest.py",
    ("monitor/inbox/20260802T0930Z-W-9203-proxy-to-theoria-arm"
     "-s47-landed-retry-is-now-nested.md"),
]

#: The evidence this run read and did not write. Hashed so that "the archive has
#: moved" is detectable rather than arguable -- `refusal_replay --verify` says
#: the same thing about the pooled numbers, and this says it about the bytes.
EVIDENCE = [
    "theoria-arm/runs/20260731T1240Z-A3-level2-carried/ledger.jsonl",
    "theoria-arm/runs/20260731T1310Z-A3-level2-carried-r2/ledger.jsonl",
    "theoria-arm/runs/20260731T1430Z-A3-level2-carried-r3/ledger.jsonl",
    "theoria-arm/runs/20260731T1500Z-A3-sk48-carried-l1/ledger.jsonl",
    "monitor/inbox/20260801T0400Z-theoria-arm-to-proxy-refusal-wave.md",
]


def digest(path):
    sha = hashlib.sha256()
    with open(os.path.join(ROOT, path), "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            sha.update(chunk)
    return "sha256:" + sha.hexdigest()


def entries(paths):
    out = []
    for path in paths:
        if os.path.exists(os.path.join(ROOT, path)):
            out.append({"path": path, "sha256": digest(path)})
        else:
            out.append({"path": path, "sha256": None, "absent": True})
    return out


def git(*args):
    return subprocess.run(("git",) + args, cwd=ROOT, capture_output=True,
                          text=True).stdout.strip()


def fingerprint():
    """`proxy.tools.contract --fingerprint`, run rather than remembered."""
    done = subprocess.run([sys.executable, "-m", "proxy.tools.contract",
                           "--fingerprint"], cwd=ROOT, capture_output=True,
                          text=True)
    return done.stdout.strip() or None


def main():
    manifest = {
        "prompt_id": "S47-refusal-wave-retry-predicate",
        "prompt": ("monitor/board: 87% of live commands are refused upstream and "
                   "the byte-identical retry succeeds -- give forward() a retry "
                   "predicate for that one response, item 1 only"),
        "territory": "proxy",
        "worker": "W-9203",
        "branch": "agent/s47-refusal-wave-retry-predicate",
        "base_commit": BASE_COMMIT,
        "head_commit": git("rev-parse", "HEAD"),
        "utc": "2026-08-02T09:00:45Z",
        "seed": None,

        "spend_usd": 0.0,
        "api_calls": 0,
        "actions_charged": 0,
        "network": "none -- every far end is a loopback fixture or a file on disk",
        "sealed_pile_contact": "none",

        # Measured, not asserted. It is byte-identical on this branch and on
        # master, which is the empirical form of C-009's claim that the contract
        # detector cannot see this change -- so the written row is the only
        # announcement there is.
        "contract_fingerprint": fingerprint(),

        "gate": {
            "suite": "536 passed, 0 failed (cd proxy && python -m pytest)",
            "baseline": "497 passed at 1e5b3f00, before anything changed",
            "new_tests": "25 for the predicate, 14 for the offline replay",
            "mutation": ("7 of the 25 predicate tests fail if forward() is made "
                         "to ignore retry_body; the rest are negative controls "
                         "that pass on master by design. Measured, not assumed."),
            "verify_py": "green on all five rungs",
            "verify_contract_sh": ("9 of 10 steps ok; the tenth runs pytest from "
                                   "the repo root, where the repo-root tools/ "
                                   "package shadows proxy/tools -- red on master "
                                   "at 1e5b3f00 for the same reason, not caused "
                                   "or fixed here"),
            "verify_s47_sh": "green",
        },

        "result": {
            "legs": 4,
            "env_steps_before": 570,
            "env_steps_after": 149,
            "wave_attempts": 494,
            "row_reduction": 0.7386,
            "outbound_attempts_before": 570,
            "outbound_attempts_after": 570,
            "sockets_unchanged": True,
            "scorecard_total_actions": 72,
            "actions_agree_before": True,
            "actions_agree_after": True,
            "max_attempts": 5,
            "note": ("149 and not 76: the replay models forward()'s bounded "
                     "loop, and 73 rows exist because the 5-attempt budget ran "
                     "out while the predicate still wanted to retry"),
        },

        "files": entries(DELIVERED),
        "evidence_read_not_written": entries(EVIDENCE),

        "reproduce": [
            "cd proxy && python -m pytest",
            "cd proxy && python verify.py",
            ("python -m proxy.tools.refusal_replay --verify "
             "--leg theoria-arm/runs/20260731T1240Z-A3-level2-carried/ledger.jsonl "
             "--leg theoria-arm/runs/20260731T1310Z-A3-level2-carried-r2/ledger.jsonl "
             "--leg theoria-arm/runs/20260731T1430Z-A3-level2-carried-r3/ledger.jsonl "
             "--leg theoria-arm/runs/20260731T1500Z-A3-sk48-carried-l1/ledger.jsonl"),
            ("bash proxy/runs/20260802T0900Z-S47-refusal-wave-retry-predicate"
             "/verify_s47.sh"),
        ],
    }

    out = os.path.join(HERE, "MANIFEST.json")
    with open(out, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print("wrote %s (%d delivered, %d evidence)"
          % (out, len(manifest["files"]), len(manifest["evidence_read_not_written"])))


if __name__ == "__main__":
    main()
