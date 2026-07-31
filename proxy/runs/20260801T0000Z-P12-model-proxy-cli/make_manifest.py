"""Re-derive this run's MANIFEST.json.

Byte-stable: the file list is sorted, hashes are over the bytes on disk, and
nothing that varies between machines (paths, timestamps of the run itself)
enters a hashed field. Run it again after editing a delivered file and diff.

    python proxy/runs/20260801T0000Z-P12-model-proxy-cli/make_manifest.py
"""

import hashlib
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

DELIVERED = [
    "proxy/cli_transport.py",
    "proxy/model_proxy.py",
    "proxy/tests/test_cli_transport.py",
    "proxy/STATUS.md",
    "proxy/DECISIONS.md",
    "proxy/CONTRACT_CHANGES.md",
    "proxy/LEDGER_FORMAT.md",
    "proxy/runs/20260801T0000Z-P12-model-proxy-cli/FINDING.md",
    "proxy/runs/20260801T0000Z-P12-model-proxy-cli/RUN_STATE.md",
    "monitor/inbox/2026-08-01T0000Z-P12-proxy-to-theoria-arm-"
    "the-cli-can-go-through-the-model-proxy.md",
]


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def main():
    manifest = {
        "prompt_id": "P-12-model-proxy",
        "prompt": "close Phase 1 acceptance item 模型代理: implement every step "
                  "of verify-lab/DUAL_PROXY.md §4's checklist that does not "
                  "require a paid credential",
        "branch": "p12/model-proxy",
        # merge-base, not `rev-parse master`: master moves under a fleet, and a
        # manifest that re-derives to a different commit tomorrow is not a
        # provenance record.
        "base_commit": subprocess.run(
            ["git", "-C", REPO, "merge-base", "HEAD", "master"],
            capture_output=True, text=True, check=True).stdout.strip(),
        "utc": "2026-08-01T00:00:00Z",
        "territory": "proxy",
        "seed": None,
        "spend_usd": 0.0,
        "api_calls": 0,
        "network": "none - every far end is a loopback fixture",
        "sealed_pile_contact": "none",
        "gate": {"command": "cd proxy && python -m pytest",
                 "result": "442 passed", "exit": 0},
        "contract_fingerprint": subprocess.run(
            ["python", "-m", "proxy.tools.contract", "--fingerprint"],
            cwd=REPO, capture_output=True, text=True).stdout.strip().splitlines()[-1],
        "files": [{"path": p, "sha256": sha256_of(os.path.join(REPO, p))}
                  for p in sorted(DELIVERED)],
    }
    out = os.path.join(HERE, "MANIFEST.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print(out)


if __name__ == "__main__":
    main()
