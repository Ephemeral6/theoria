"""Regenerate this run's MANIFEST.json from what is actually on disk.

Generated rather than hand-written, for the reason V21's generator gives: a
manifest that has to be remembered is a manifest that will be wrong. The `files`
list is walked, so anything added later cannot go unrecorded.

V26 adds one rule of its own, learned the hard way at V25's delivery: **do not
write a pointer to a file this run did not produce.** V25's manifest cited an
`ADVERSARIAL.md` that was never written, which is the same dangling-citation
defect this lane files against papers. Every path named in `adversarial` below is
asserted to exist before the manifest is written.

    MANIFEST_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ) \
      python exam/runs/20260729T2215Z-V26-handover-leak-ruling/write_manifest.py
"""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
RUN_ID = os.path.basename(HERE)
REL = os.path.relpath(HERE, REPO).replace(os.sep, "/")

TRACKED = [
    "exam/papers/handover_auto.py",
    "exam/tests/test_handover_auto.py",
    "exam/leakage.py",
    "exam/STATUS.md",
    "exam/runs/20260728T202540Z-V11-handover-auto-r2/RESULTS.md",
    "exam/runs/20260728T202101Z-V11-handover-auto/VOIDED.md",
]

#: Paths cited in the `adversarial` block. Checked, not trusted.
CITED = [
    REL + "/RULING.md",
    REL + "/RUN_STATE.md",
]


def sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def git(*args):
    return subprocess.run(("git",) + args, cwd=REPO, capture_output=True,
                          text=True).stdout.strip()


def main():
    utc = os.environ.get("MANIFEST_UTC")
    if not utc:
        sys.exit("MANIFEST_UTC must be set; this script takes no clock of its "
                 "own so that reruns are byte-stable")

    missing = [p for p in CITED if not os.path.exists(os.path.join(REPO, p))]
    if missing:
        sys.exit("manifest cites files that do not exist: %s" % missing)

    files = []
    for rel in TRACKED:
        path = os.path.join(REPO, rel)
        if os.path.exists(path):
            files.append({"path": rel, "sha256": sha256(path)})
    for root, _dirs, names in os.walk(HERE):
        for name in sorted(names):
            if name.endswith(".pyc") or "__pycache__" in root:
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, REPO).replace(os.sep, "/")
            files.append({"path": rel, "sha256": sha256(path)})
    files.sort(key=lambda entry: entry["path"])

    manifest = {
        "prompt_id": "V-V26-handover-leak-ruling",
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": git("rev-parse", "HEAD"),
        "utc": utc,
        "run_id": RUN_ID,
        "lane": "verify",
        "author": "RES-3",
        "territory": "exam",
        "based_on": {
            "branch": "agent/v25-leakage-loo-and-multiplicity",
            "why": "the leak is only visible to V25's pooled private-marker cut, "
                   "which is not on master yet; from master the repair could not "
                   "be verified because nothing would detect what it repairs",
        },
        "what": "repaired the level-multiplicity leak in v11-handover-a0 and ruled "
                "on the -r2 run that sat the leaking sheet",
        "cost": {"api_calls": 0, "usd": 0.0, "network": False,
                 "sealed_pile_contact": False},
        "verification": {
            "pytest_exam_tests": "385 passed, 2 xfailed",
            "exam_verify_py": "GREEN",
            "leak_gate_on_repaired_paper": "clean under every derived label set",
        },
        "adversarial": {
            "reviewers": 2,
            "verdicts": {
                "r2_ruling": "the filed sentence was too strong AND its premise "
                             "was false -- readers disagreed but none scored "
                             "wrong, which is exculpatory; ruling rewritten as "
                             "annul-as-instrument, see RULING.md",
                "repair_is_clean": "REFUTED then adjudicated -- 'Box on the outer "
                                   "ring' predicts 10/10 at p_fire 0.022222 and "
                                   "the repair sharpened it from 0.035714, but it "
                                   "is a sound law (its truth tracks whether the "
                                   "target is on the ring), not a leak; residual "
                                   "recorded and filed, see RULING.md",
                "found_in_v26_own_work": "a vacuous assertion "
                                         "(report.get('metadata_hits', 0) == 0 -- "
                                         "no such key) and a stale module "
                                         "docstring; both fixed",
            },
            "record": CITED,
        },
        "files": files,
    }

    out = os.path.join(HERE, "MANIFEST.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
    print("%s: %d files" % (out, len(files)))


if __name__ == "__main__":
    main()
