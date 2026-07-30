"""Regenerate this run's MANIFEST.json from what is actually on disk.

Generated rather than hand-written, for the reason V21's generator gives: a
manifest that has to be remembered is a manifest that will be wrong. The `files`
list is walked, so a probe added later cannot go unrecorded.

    MANIFEST_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ) \
      python exam/runs/20260729T1820Z-V25-leakage-loo-and-multiplicity/write_manifest.py
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
    "exam/leakage.py",
    "exam/tests/test_leakage_multiplicity.py",
    "exam/tests/test_leakage_tokens.py",
    "exam/tests/test_handover_auto.py",
    "exam/STATUS.md",
    "exam/artifacts/leakage.json",
]
WALKED = [REL]


def sha256(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def git(*args):
    return subprocess.run(("git",) + args, cwd=REPO, capture_output=True,
                          text=True).stdout.strip()


def main():
    paths = list(TRACKED)
    for root_rel in WALKED:
        for dirpath, dirnames, filenames in os.walk(
                os.path.join(REPO, root_rel)):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for name in sorted(filenames):
                if name == "MANIFEST.json":
                    continue        # cannot hash the file being written
                full = os.path.join(dirpath, name)
                paths.append(os.path.relpath(full, REPO).replace(os.sep, "/"))

    files = [{"path": p, "sha256": sha256(os.path.join(REPO, p))}
             for p in sorted(set(paths))
             if os.path.isfile(os.path.join(REPO, p))]

    manifest = {
        "prompt_id": "V2-V25-leakage-loo-and-multiplicity",
        "run_id": RUN_ID,
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": git("rev-parse", "HEAD"),
        "utc": os.environ.get("MANIFEST_UTC") or sys.exit(
            "set MANIFEST_UTC from `date -u +%Y-%m-%dT%H:%M:%SZ` -- a "
            "self-reported clock drifted an hour on this branch already"),
        "python": "%d.%d.%d" % sys.version_info[:3],
        "worktree_dirty": bool(git("status", "--porcelain")),
        "tests": ("pytest exam/tests -q (381 passed, 2 xfailed); "
                  "python exam/verify.py (GREEN); "
                  "b4_fast_count_vs_oracle.py (2130 differential configurations, "
                  "0 mismatches); "
                  "b5_pooled_private_cut.py (3/3 fixtures as expected)"),
        "passive": {"api_calls": 0, "game_spend_usd": 0.0, "network": 0,
                    "sealed_pile_reads": 0},
        "result": {
            "multiplicity_correction": {
                "status": "exact, published, not applied",
                "exact_vs_v21_sampled": {"exact": 0.1034, "v21_sampled": 0.117},
                "scopes_published": ["in_field", "in_label_set"],
                "why_not_applied": ("at n=6 with three cuts tried the family-wise "
                                    "rate is 0.187, so alpha 0.05 silences a leak "
                                    "V21 planted on purpose and a human sees by "
                                    "eye; firing means 'a human adjudicates', so a "
                                    "false alarm costs one look and a miss costs a "
                                    "published paper"),
            },
            "exact_count_cost": {
                "bruteforce_seconds": {"6_classes_n80": 0.46,
                                       "8_classes_n80": 14.67,
                                       "12_classes_n120": None},
                "pruned_seconds": {"20_classes_n200": 0.0},
                "differential_configurations": 2130,
                "mismatches": 0,
            },
            "single_holder_ruling": {
                "first_pass": "not closable (withdrawn)",
                "after_adversarial_review": ("closable by one pooled cut over the "
                                             "field's private markers; the "
                                             "impossibility proof only covers "
                                             "per-token rules"),
                "found_immediately": ("a real leak in v11-handover-a0: level-name "
                                      "uniqueness predicts `solvable` 8/8 at "
                                      "p_fire 0.0357"),
                "coverage_four_shipped_distinct": [97, 106],
                "withdrawn_numbers": {"237_of_261": "scan slots over five papers",
                                      "219_of_230": "scan slots over four",
                                      "cry_wolf_cost": 0},
                "known_evasion": ("a decoy private marker on every item pushes the "
                                  "cut to k=n; the rule that survives it is "
                                  "measured in b5 and not shipped"),
            },
            "groups_that_cannot_fire": {
                "count": [6, 10],
                "cause": ("the statistic is two-class-shaped: ceiling is "
                          "2*largest/n, about 2/m for m balanced answer classes, "
                          "so below the 0.90 tolerance once m >= 3"),
                "includes": ["p15-heldout-a0/event", "p15-heldout-a0/level_name",
                             "p15-handover-a0/rule", "p15-verdict-a2/class"],
                "consequence": ("two of the four shipped papers were green under a "
                                "check that could not have reported anything"),
            },
            "papers": {"p15-adaptation-a0": "GREEN", "p15-handover-a0": "GREEN",
                       "p15-heldout-a0": "GREEN", "p15-verdict-a2": "GREEN",
                       "v11-handover-a0": "RED (pinned, not repaired)"},
        },
        "adversarial": {
            "reviewers": 3,
            "verdicts": {
                "single_holder_theorem": "REFUTED -- accepted and reworked",
                # Was "see ADVERSARIAL.md" -- a file this run never wrote. The
                # record lives in RUN_STATE.md instead, so the pointer names that.
                # A manifest citing a file that does not exist is the same defect
                # this lane files against papers, and it does not get an exemption
                # for being ours.
                "fast_exact_count": "1170339 configurations across three implementations,"
                                    " zero disagreements; three real defects found and"
                                    " fixed -- see RUN_STATE.md section"
                                    " '打快速计数器的那个'",
                "reader_visibility": ("group_power was dead code and clean papers "
                                      "published no multiplicity at all -- both "
                                      "fixed"),
            },
            "note": ("the refutation of this item's own central ruling arrived with "
                     "a counterexample carrying a real leak, which is the "
                     "difference between a review and a re-read"),
        },
        "files": files,
    }
    out = os.path.join(HERE, "MANIFEST.json")
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True,
                  ensure_ascii=False)
        handle.write("\n")
    print("%s: %d files" % (out, len(files)))


if __name__ == "__main__":
    main()
