"""Regenerate this run's MANIFEST.json from what is actually on disk.

The first pass hand-wrote it and it went stale twice over: the `files` list named
five of the twelve adversarial probes, and `tests` recorded "8 passed / 349 passed"
after the counts had moved to 19 / 361. A manifest that has to be remembered is a
manifest that will be wrong, which is the same complaint E18 makes about the
survey's ratios. So it is generated, and the generator ships beside it.

    python exam/runs/20260729T1130Z-V21-leakage-gate-token-level/write_manifest.py
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

#: Everything this item touched, plus everything it produced. Directories are
#: walked, so a probe added later cannot go unrecorded.
TRACKED = [
    "exam/leakage.py",
    "exam/tests/test_leakage_tokens.py",
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
        for dirpath, _dirnames, filenames in os.walk(
                os.path.join(REPO, root_rel)):
            for name in sorted(filenames):
                if name == "MANIFEST.json":
                    continue        # cannot hash the file being written
                full = os.path.join(dirpath, name)
                paths.append(os.path.relpath(full, REPO).replace(os.sep, "/"))

    files = [{"path": p, "sha256": sha256(os.path.join(REPO, p))}
             for p in sorted(set(paths))
             if os.path.isfile(os.path.join(REPO, p))]

    manifest = {
        "prompt_id": "V21-leakage-gate-token-level",
        "run_id": RUN_ID,
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": git("rev-parse", "HEAD"),
        "utc": os.environ.get("MANIFEST_UTC") or sys.exit(
            "set MANIFEST_UTC from `date -u +%Y-%m-%dT%H:%M:%SZ` -- a "
            "self-reported clock drifted an hour on this branch already"),
        "python": "%d.%d.%d" % sys.version_info[:3],
        "worktree_dirty": bool(git("status", "--porcelain")),
        "tests": ("pytest exam/tests/test_leakage_tokens.py -q (20 passed); "
                  "pytest exam/tests -q (363 passed, 2 xfailed); "
                  "python -m exam.verify (GREEN); "
                  "adversarial/a10_mutation_test.py "
                  "(23 mutations x 20 tests, every mutation caught by >=1 test)"),
        "passive": {"api_calls": 0, "game_spend_usd": 0.0, "network": 0,
                    "sealed_pile_reads": 0},
        "audit_result": {
            "papers_audited": 4,
            "hits": 0,
            "label_sets_before": {"p15-adaptation-a0": 0, "p15-handover-a0": 0,
                                  "p15-heldout-a0": 2, "p15-verdict-a2": 3},
            "label_sets_after": {"p15-adaptation-a0": 3, "p15-handover-a0": 1,
                                 "p15-heldout-a0": 2, "p15-verdict-a2": 4},
            "note": ("All four clean under both nets. Two derived no label set "
                     "at all before, so their metadata check ran on zero of "
                     "their 89 items. p15-verdict-a2 derives four and scores "
                     "none of them -- all three original metadata fields are "
                     "constant on it -- which the report now states outright "
                     "instead of printing as an ordinary green."),
        },
        "adversarial": {
            "probes_rerun": 12,
            "report": REL + "/adversarial/ADVERSARIAL.md",
            "raw_output": REL + "/adversarial/PROBE_OUTPUT.txt",
            "mutation_table": REL + "/adversarial/MUTATION_TABLE.txt",
            "note": ("The subagent died before writing a report, leaving twelve "
                     "scripts and no conclusions; all twelve were re-run and "
                     "adjudicated. It overturned two of the first pass's own "
                     "tests and one of its fixes."),
            "false_positive_rate": {
                "exhaustive_balanced": {"n4": 0.20, "n5": 0.08, "n6": 0.0357,
                                        "n8": 0.0081, "n12": 0.0064},
                "permutation_null": {"v11-handover-a0/solvable": 0.117,
                                     "p15-adaptation-a0/exact_on_heldout": 0.013,
                                     "other_11_label_fields": 0.0},
            },
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
