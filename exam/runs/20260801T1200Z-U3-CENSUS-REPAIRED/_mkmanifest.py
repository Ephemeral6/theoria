# -*- coding: utf-8 -*-
"""One-shot MANIFEST writer for this run record (kept for provenance).

Derived from `exam/runs/20260801T0400Z-U3-CENSUS/_mkmanifest.py`, the same
territory's own writer, so the two run records' manifests are comparable field
for field.  Hashes are taken over the working copy, which is why the LF note at
the bottom is load-bearing rather than style.
"""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RD = Path(__file__).resolve().parent

files = [
    ROOT / "exam" / "u3_census.py",
    ROOT / "exam" / "tests" / "test_u3_census.py",
    RD / "census.json",
    RD / "census.md",
    RD / "prereg_acceptance.py",
    RD / "prereg_acceptance.json",
    RD / "prereg_acceptance_selftest.py",
    RD / "prereg_acceptance_selftest.json",
    RD / "break_the_guarantees.py",
    RD / "RUN_STATE.md",
]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


man = {
    "prompt_id": "z/exam-u3-followthrough",
    "prompt": ("Two follow-throughs from 2026-08-01: (1) flip exam's U3 "
               "regression tests now that freeze repaired the adjudicator to "
               "key on theorem CONTENT rather than NAME, keeping a test that "
               "would catch a regression to name-keying; (2) re-run "
               "exam/u3_census.py over everything on disk and report the new "
               "numbers against the old, with the denominator caveat still "
               "travelling inside the JSON; (3) verify the verdict-question "
               "pre-registration against its own acceptance."),
    "branch": "z/exam-u3-followthrough",
    "base_commit": subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        capture_output=True, text=True).stdout.strip()[:8],
    "base_note": ("master e8345aff with the unmerged branch ep/u3-exam-audit "
                  "merged in: exam/u3_census.py and its tests are NOT on "
                  "master, so a worktree cut from master alone cannot run "
                  "this ticket at all."),
    "utc": "2026-08-01T12:00:00Z",
    "seed": None,
    "territory": "exam",
    "spend": {"usd": 0.0, "api_calls": 0, "model_calls": 0, "network": False,
              "note": ("offline throughout: Lean 4.9.0 locally, the exam "
                       "suite, and synthetic control transcripts already on "
                       "disk. Nothing here required a live run.")},
    "adjudicator": {
        "module": "freeze/u3.py",
        "sha256": _sha(ROOT / "freeze" / "u3.py"),
        "shape_module": "freeze/theorem_shape.py",
        "shape_sha256": _sha(ROOT / "freeze" / "theorem_shape.py"),
        "repair_commit": "1c063290",
        "note": ("every verdict in census.json is this module's return value; "
                 "the census contains no second opinion"),
    },
    "toolchain": {"lean": "4.9.0 x86_64-w64-windows-gnu 8f9843a4a5fe"},
    "census": {
        "books": "17/24 attained (was 14/24 at 04:00Z)",
        "books_by_label": {"discharged": 17, "vacuous": 2,
                           "unclassified": 4, "failing_obligation": 1},
        "books_by_label_prior": {"discharged": 14, "vacuous": 9,
                                 "failing_obligation": 1},
        "rows_moved": 7,
        "rows_moved_note": ("all seven are in theory-compiler and every move "
                            "is OUT of `vacuous`: the repair only ever "
                            "withdraws an accusation. theory-compiler 0/7 -> "
                            "3/7; no other territory moves."),
        "bookless_claimants": "20 runs, 0 attained (was 15 runs, 0 attained)",
        "bookless_claimants_note": (
            "the +5 is NOT the adjudicator: five run directories appeared on "
            "disk between 04:00Z and now (four R1/R1b live legs, all "
            "declared_refusal, plus theoria-arm/runs/audit-smoke). Nothing "
            "left the set and no label changed. Two causes in one diff, "
            "separated deliberately."),
        "coverage_gaps": ["unclassified"],
        "permanent_non_attainers": ["point_claim", "witness"],
        "probe": False,
        "byte_reproducible": True,
        "cross_check": (
            "agrees row for row with freeze's independent census, "
            "freeze/runs/20260801T0700Z-E1-kind-census/: 14->17 discharged, "
            "9->2 vacuous, 0->4 unclassified, 1->1 failing_obligation, "
            "theory-compiler 0/7->3/7. Two enumerations built by different "
            "territories agree on all 24 rows."),
        "denominator_warning": (
            "NOT STATS_RULES.md 1.2's rate. 1.2's denominator is 19 sealed "
            "games (12 clean); nothing on disk today is a sealed game. The "
            "caveat travels inside census.json under summary."
            "denominator_meaning and summary.not_the_frozen_endpoint."),
    },
    "prereg_audit": {
        "document": "exam/PREREG_VERDICT.md",
        "conditions": 10,
        "passed": 10,
        "verdict": "ACCEPTED",
        "negative_controls": {
            "bluffer": {"sensitivity": 1.0, "specificity": 0.0,
                        "balanced_accuracy": 0.5, "verdict": "REFUTED",
                        "killed_by": "specificity floor (independent of BA)"},
            "denier": {"sensitivity": 0.0, "specificity": 1.0,
                       "balanced_accuracy": 0.5, "verdict": "REFUTED",
                       "killed_by": "BA floor"},
        },
        "auditor_selftest": ("four deliberate breakages, four caught, none "
                             "missed; the two floor breakages are caught but "
                             "not cleanly attributed -- see RUN_STATE.md 4"),
    },
    "tests_flipped": [
        "test_FINDING_renaming_the_theorems_alone_flips_the_verdict -> "
        "test_REGRESSION_F1_renaming_the_theorems_does_not_move_the_verdict",
        "test_FINDING_deadlock_paradigm_on_disk_is_labelled_vacuous -> "
        "test_REGRESSION_F1_deadlock_paradigm_on_disk_attains",
        "test_kind_coverage_names_the_kinds_that_can_never_attain -> "
        "test_kind_coverage_splits_permanent_non_attainers_from_gaps",
        "test_level_lean_book_is_discovered (second half inverted)",
        "test_deeply_nested_book_is_discovered (second half inverted)",
        "test_level_lean_book_is_adjudicated_not_reported_as_no_evidence "
        "(route no longer pinned; verdict is)",
    ],
    "tests_added": [
        "test_direct_source_fallback_still_fires_when_the_adjudicator_goes_blind",
        "test_kind_coverage_reports_a_real_gap_as_a_gap",
    ],
    "breakage_matrix": {
        "kind taken from name_hint again": "7 failed",
        "permanent non-attainers folded into coverage_gaps": "1 failed",
        "gap detector restored to the dead substring sniff": "2 failed",
        "census direct-source fallback deleted": "1 failed",
    },
    "findings": [
        "E1 (2026-08-01, freeze 1c063290) reads the STATEMENT: F1, D1 and D2 "
        "are closed at the source. exam's six red regression tests were the "
        "intended signal; freeze's note named four of them.",
        "NEW, in exam's own code: kind_coverage() detected 'no (c) check' by "
        "sniffing for the substring 'no executable' in E1's `why` text. The "
        "repair stopped writing that sentence, so the table did not go red -- "
        "it went EMPTY, a clean bill of health manufactured by a lookup miss "
        "on the one output whose job is reporting gaps. Now keys on "
        "freeze.theorem_shape.KINDS_WITH_A_C_CHECK, an exported name.",
        "point_claim and witness are PERMANENT non-attainers (supporting "
        "obligations; 1.2.1 writes no requirement and never will). Listing "
        "them beside a real gap makes the real gap unfindable, so the field "
        "is split; kinds_that_can_never_attain is retained as the union.",
        "The `unsolvable` (c) check has STILL never been observed to say yes: "
        "0/1 now, 0/14 before. The 13 that left were reclassified by shape, "
        "not discharged. freeze's c_init_has_action residual is the cause.",
        "16 unclassified theorems across 4 handover_packages books are a live "
        "coverage gap: they fail closed and now say the honest word, but "
        "those books cannot attain through any theorem they contain.",
        "exam/u3_census.py and its tests are on the UNMERGED branch "
        "ep/u3-exam-audit. A Phase 4 reader working from master sees freeze's "
        "census and not exam's, so the two-territory cross-check above is "
        "invisible from the mainline.",
    ],
    "sealed_pile_contact": "none",
    "files": [{"path": str(f.relative_to(ROOT)).replace("\\", "/"),
               "sha256": _sha(f)}
              for f in files],
}
# LF explicitly. `exam/.gitattributes` pins `* text eol=lf`, so git stores LF;
# Python's text mode on Windows writes CRLF, and a sha256 taken over that
# working copy would fail to reproduce after a fresh checkout — the hashes
# below would be wrong about the very files they certify.
with open(RD / "MANIFEST.json", "w", encoding="utf-8", newline="\n") as fh:
    fh.write(json.dumps(man, indent=1, ensure_ascii=False) + "\n")
print("wrote", RD / "MANIFEST.json")
