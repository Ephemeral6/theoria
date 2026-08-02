"""Write this run's MANIFEST.json.

This run delivered a merge whose tree is byte-identical to master, so there are
no changed deliverables to hash.  What the manifest therefore records instead is
the *evidence of the adjudication*: the two branch tips, the four p18 commits and
their reachability, and the blob SHAs that made the ruling decidable rather than
a matter of taste.

Run from the repo root.
"""

import hashlib
import json
import os
import subprocess

RUN = "papers/runs/20260802T111536Z-V30-p18-hand-merge"
P18 = "origin/agent/p18-audits-cover-half-onmaster"
RUNDIR = "papers/phase1-workshop/runs/20260730T000000Z-P18-audits-cover-half"


def git(*args):
    return subprocess.run(("git",) + args, capture_output=True,
                          text=True).stdout.strip()


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def blob(ref, path):
    return git("rev-parse", "%s:%s" % (ref, path))


CONFLICTS = [
    "papers/phase1-workshop/REVIEW-2026-07-30.md",
    "papers/phase1-workshop/verify_paper.py",
    RUNDIR + "/MANIFEST.json",
    RUNDIR + "/RUN_STATE.md",
    RUNDIR + "/citecheck-A-abstract-to-s3.md",
    RUNDIR + "/citecheck-C-s7-to-s8.md",
    RUNDIR + "/delta-old-vs-new.md",
]

IDENTICAL = [
    RUNDIR + "/citecheck-B-s4-to-s6.md",
    RUNDIR + "/citecheck-D1-s9-to-s10.md",
    RUNDIR + "/citecheck-D2-s11-to-s12.md",
    RUNDIR + "/COVERAGE.md",
]


def main():
    own = sorted(
        os.path.join(RUN, n) for n in os.listdir(RUN)
        if os.path.isfile(os.path.join(RUN, n)) and n != "MANIFEST.json")

    doc = {
        "prompt_id": "V30-p18-hand-merge",
        "branch": "agent/v30-p18-hand-merge",
        "base_commit": git("rev-parse", "origin/master"),
        "merged_branch": P18,
        "merged_tip": git("rev-parse", P18),
        "merge_commit": git("rev-parse", "HEAD"),
        "utc": "2026-08-02T11:15:36Z",
        "worker": "W-9201",
        "territory": "papers",
        "verdict": (
            "All seven conflicts resolved to master's side. The merged tree is "
            "BYTE-IDENTICAL to origin/master: this branch's content was already "
            "absorbed by master (commit fe0d9357 says so in its own message). "
            "The merge commit exists to join the history so ci_merge stops "
            "retrying, not to move any bytes."),
        "tree_identical_to_master": git("diff", "origin/master", "--stat") == "",
        "p18_commits": [
            {"sha": "0eb876f7", "reachable_from_head": True,
             "what": "the three never-audited sections -- citecheck B/D1/D2"},
            {"sha": "5f11953b", "reachable_from_head": True,
             "what": "check G AUDITSTAMP + audit_stamp.py"},
            {"sha": "bc910d8d", "reachable_from_head": True,
             "what": "referee pass + 45 gate tests -- already on master per git cherry"},
            {"sha": "4f7e300d", "reachable_from_head": True,
             "what": "referee axis refresh -- already on master per git cherry"},
        ],
        "conflicts_resolved_to_master": CONFLICTS,
        "byte_identical_across_branches": [
            {"path": p, "sha256_blob": blob("origin/master", p),
             "same_on_p18": blob("origin/master", p) == blob(P18, p)}
            for p in IDENTICAL
        ],
        "gates": {
            "before": "pytest papers: 2 failed / 272 passed / 1 xfailed; "
                      "verify_paper: FAIL (3/7) -- C FIGDATA, E UNCITED, F BARE",
            "after": "identical, necessarily -- the tree did not change",
            "acceptance_line_met": False,
            "why_not": "The ticket's line is 'all paper gates green'. They were "
                       "already red on master before this ticket started. The "
                       "three red checks are unrelated to p18 and clearing them "
                       "means editing paper body text, which monitor/CHARTER.md "
                       "reserves to RES-2. Recorded as a gap, not worked around.",
        },
        "findings_recount": {
            "commit_message_claims": "21 (B) + 32 (D1) + 32 (D2) = 85",
            "recomputed_from_the_files_own_summary_tables":
                "B 23 (22 net of one B/C overlap), D1 32, D2 22",
            "note": "The bases differ -- D1 totals by severity, B and D2 by "
                    "pass -- so they are not addable. The three files are "
                    "byte-identical on both branches, so this discrepancy is "
                    "neither caused nor fixable by this merge; it predates it. "
                    "Master's own MANIFEST uses a third basis again (332 rows, "
                    "'not asserted').",
        },
        "spend_usd": 0.0,
        "spend_note": "offline; no API call, no sealed-pile contact",
        "files": [
            {"path": p.replace(os.sep, "/"), "bytes": os.path.getsize(p),
             "sha256": sha256(p)} for p in own
        ],
    }
    with open(os.path.join(RUN, "MANIFEST.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    print("wrote %s/MANIFEST.json" % RUN)


if __name__ == "__main__":
    main()
