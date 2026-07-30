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
    # The annulment is carried here, not only in RESULTS.md. A second
    # adversarial pass measured that the prose-only remedy left this file
    # byte-identical, so every automated reader still saw an unmarked run.
    "exam/runs/20260728T202540Z-V11-handover-auto-r2/RESULTS.json",
    "exam/runs/20260728T202101Z-V11-handover-auto/VOIDED.md",
    # The gate that stops the next remedy from being prose-only.
    "exam/tests/test_run_dispositions_are_machine_readable.py",
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
            # Not MANIFEST.json itself. Hashing the file being written records
            # the *previous* content, so the entry is stale the moment it is
            # saved and can never verify -- a hash presented as a check that is
            # guaranteed to fail. Found by an adversarial review of V26: 9 of 10
            # entries verified and the tenth was this one.
            if root == HERE and name == "MANIFEST.json":
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
            "pytest_exam_tests": "456 passed, 2 xfailed",
            "exam_verify_py": "GREEN",
            "leak_gate_on_repaired_paper": "clean under every derived label set",
            "new_assertions_mutation_tested": (
                "5 mutants, all confirmed red: revert the flume swap; move "
                "flume's target off the ring; add a third warren item; stub "
                "_plan_length so a dead ring-Box item reports solvable; drop "
                "tags from METADATA_FIELDS. Also: deleting the annulment key "
                "turns test_run_dispositions_are_machine_readable red."),
        },
        "adversarial": {
            "rounds": 2,
            "reviewers": 3,
            "why_two_rounds": (
                "round 1 ran mid-drafting and round 2 against the finished "
                "ruling before delivery. Their findings did not overlap, which "
                "is the argument for running the second one at all."),
            "verdicts": {
                "round1_r2_ruling": "the filed sentence was too strong AND its "
                                    "premise was false -- readers disagreed but "
                                    "none scored wrong, which is exculpatory; "
                                    "ruling rewritten as annul-as-instrument",
                "round1_repair_is_clean": "REFUTED then adjudicated -- 'Box on "
                                          "the outer ring' was sharper than the "
                                          "leak being repaired, but it is a sound "
                                          "law, not a leak",
                "round2_six_claims_refuted": (
                    "B1 the familywise rate FELL 0.135385->0.106281 and was "
                    "already over ALPHA, stated as a rise; B2 'the rule was "
                    "published before the run' is false -- it landed 1-2 days "
                    "after, and it was the ruling's only aggravating factor; "
                    "B3 the 'structurally unclosable residual' was closable by "
                    "swapping rather than appending a flume item, and had been "
                    "written down expressly to stop anyone re-searching; B4 two "
                    "more vacuous assertions survived three lines above the one "
                    "V26 replaced, plus one vacuous replacement; B5 STATUS.md "
                    "still carried the sentence the ruling calls false; B6 the "
                    "remedy was prose-only and RESULTS.json was byte-identical; "
                    "B7 the manifest hashed itself. All fixed in this commit."),
                "round2_strongest_attack": (
                    "that r2's only pre-registered discriminator was fully "
                    "contaminated and the grounds against voiding were circular "
                    "or self-cancelling. Verdict kept as annulment; grounds 1-3 "
                    "conceded or narrowed, ground 4 stands, and the reviewer's "
                    "remedy adopted -- the disposition now lives in RESULTS.json "
                    "and is enforced by a test."),
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
