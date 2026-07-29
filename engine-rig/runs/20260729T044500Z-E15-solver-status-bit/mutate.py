"""E15 -- does anything actually go red when the fix is undone?

    python runs/20260729T044500Z-E15-solver-status-bit/mutate.py [--dry-run]

Two questions, and the second is the one C11 says gets skipped.

1. **The one the ticket names.**  Collapse the structured result back into a bare
   `None` and show the two negative controls are let through -- i.e. that they
   are testing the fix and not the weather.  M01 and M02 below are that
   experiment.
2. **Whether the mutation surface is wider than the test surface.**  C11's
   finding was 18 mutants that corresponded one-to-one with 18 tests, which
   measures nothing but the author's imagination.  So this battery deliberately
   contains mutants nobody wrote a test for, including ones expected to
   **survive**.  Survivors are reported, not deleted, and the ones here are real
   gaps in the assertions.

Each mutant is a textual substitution with a unique anchor.  A mutant whose
anchor does not appear is reported as `not_applied` and never counted as killed:
a patch that silently failed to apply is the most flattering possible result and
the easiest to miss.
"""

import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE_RIG = os.path.dirname(os.path.dirname(HERE))

POTENTIAL = os.path.join(ENGINE_RIG, "engines", "lp_potential", "potential.py")
LP_INIT = os.path.join(ENGINE_RIG, "engines", "lp_potential", "__init__.py")
ZEROSPACE = os.path.join(ENGINE_RIG, "engines", "zero_space", "zerospace.py")

#: (id, path, anchor, replacement, note)
MUTANTS = [
    # ---- the collapse the ticket asks to be demonstrated ------------------
    ("M01-run-collapses-to-none", LP_INIT,
     """    if outcome.status == NO_LINEAR_PAGODA:
        return None, None
    if outcome.status != CERTIFIED:""",
     """    if outcome.certificate is None:
        return None, None
    if False:""",
     "the public pair entry stops branching by name and reads "
     "`certificate is None` instead -- the original defect, in new field names"),

    ("M02-solve_certificate-collapses-to-none", POTENTIAL,
     """    raise LpUnavailable(
        "linprog stopped without deciding feasibility: %s -- status %r (%s). \"""",
     """    return None
    raise LpUnavailable(
        "linprog stopped without deciding feasibility: %s -- status %r (%s). \"""",
     "the narrow wrapper folds every undecided outcome back into None"),

    # ---- the status table -------------------------------------------------
    ("M03-status-1-reads-as-infeasible", POTENTIAL,
     "    1: BUDGET,", "    1: NO_LINEAR_PAGODA,",
     "an iteration limit is classified as a geometric fact"),
    ("M04-status-3-reads-as-infeasible", POTENTIAL,
     "    3: UNBOUNDED,", "    3: NO_LINEAR_PAGODA,",
     "an unbounded relaxation is classified as a geometric fact"),
    ("M05-status-4-reads-as-infeasible", POTENTIAL,
     "    4: NUMERICAL,", "    4: NO_LINEAR_PAGODA,",
     "numerical difficulties are classified as a geometric fact"),
    ("M06-unknown-status-defaults-to-infeasible", POTENTIAL,
     "STATUS_WORDS.get(int(result.status), UNDECIDED)",
     "STATUS_WORDS.get(int(result.status), NO_LINEAR_PAGODA)",
     "a status nobody has seen is read as a proof"),

    # ---- the predicate ----------------------------------------------------
    ("M07-no_linear_pagoda-reconstructed-from-none", POTENTIAL,
     "        return self.status == NO_LINEAR_PAGODA",
     "        return self.certificate is None",
     "the predicate is re-derived from the absent certificate"),
    ("M08-everything-is-decided", POTENTIAL,
     "        return self.status in DECIDED_STATUSES", "        return True",
     "`decided` stops discriminating"),
    ("M09-artifact-always-decided", POTENTIAL,
     '            "decided": self.decided,', '            "decided": True,',
     "the published artifact overstates what the run decided"),
    ("M10-artifact-always-claims-no-pagoda", POTENTIAL,
     '            "no_linear_pagoda": self.no_linear_pagoda,',
     '            "no_linear_pagoda": True,',
     "the published artifact asserts the verdict unconditionally"),
    ("M11-solver-options-dropped", POTENTIAL,
     "        options=dict(solver_options) if solver_options else None,",
     "        options=None,",
     "the caller cannot reach the real solver's budget -- N1's premise"),
    ("M12-outcome-sidecar-not-written", LP_INIT,
     "    if outcome_path:", "    if False:",
     "the status exists in memory and nowhere a reader can see it"),
    ("M13-scope_of_claim-drops-the-box", POTENTIAL,
     '"linear pagodas with |w_i| <= %d and goal margin >= %d; weights "',
     '"linear pagodas; weights "',
     "the boxed claim stops saying it is boxed"),
    ("M14-outcome-hardcodes-the-default-bound", POTENTIAL,
     """        status=word,
        solver_status=int(result.status),
        solver_message=message,
        bound=bound,""",
     """        status=word,
        solver_status=int(result.status),
        solver_message=message,
        bound=10,""",
     "the bound travelling with the verdict stops being the bound used"),
    ("M15-exception-loses-the-outcome", POTENTIAL,
     "        self.outcome = outcome", "        self.outcome = None",
     "a caller catching the refusal cannot learn which status fired"),

    # ---- zero_space -------------------------------------------------------
    ("M16-quotient-always-global", ZEROSPACE,
     "    quotient_scope = GLOBAL if not truncated_cells else UNDETERMINED",
     "    quotient_scope = GLOBAL",
     "the truncated enumeration goes back to claiming the world"),
    ("M17-downgraded-word-contains-global", ZEROSPACE,
     'UNDETERMINED = "undetermined"', 'UNDETERMINED = "global_undetermined"',
     "a consumer testing `'global' in scope` resurrects the claim"),
    ("M18-degradation-keys-never-emitted", ZEROSPACE,
     "        if self.scope == UNDETERMINED:\n            payload[\"scope_proved\"] = False",
     "        if False:\n            payload[\"scope_proved\"] = False",
     "the downgrade happens but never reaches the product"),
    ("M19-scope_proved-true-on-a-downgrade", ZEROSPACE,
     '            payload["scope_proved"] = False',
     '            payload["scope_proved"] = True',
     "the payload contradicts its own label"),
    ("M20-error-text-stops-naming-the-budget", ZEROSPACE,
     '                "over budget: cell-local enumeration capped at %s colours per "',
     '                "cell-local enumeration capped at %s colours per "',
     "the ladder-shaped `over budget` marker disappears"),
    ("M21-truncation-not-recorded", ZEROSPACE,
     "            truncated.append(cell)", "            pass",
     "the cap fires and leaves no trace -- the original silent degradation"),
    ("M22-limit-raised-out-of-reach", ZEROSPACE,
     "SUBSET_ENUMERATION_LIMIT = 8", "SUBSET_ENUMERATION_LIMIT = 100",
     "N2's premise: no palette crosses the cap any more"),
    ("M23-run-record-never-errors", ZEROSPACE,
     '            "error": None if self.scope_exhaustive else (',
     '            "error": None if True else (',
     "the run-level degradation record goes quiet"),
    ("M24-global_laws-includes-the-undetermined", ZEROSPACE,
     "        return [law for law in self.laws if law.scope == GLOBAL]",
     "        return [law for law in self.laws if law.scope != CELL_LOCAL]",
     "the accessor re-promotes what the label demoted"),
    # ---- five nobody wrote a test for, added so the mutation surface is not
    # ---- a mirror of the assertion surface (C11's finding, stated as a rule
    # ---- in PREREGISTRATION.md P5)
    ("M26-budget-counted-as-decided", POTENTIAL,
     "DECIDED_STATUSES = (CERTIFIED, NO_LINEAR_PAGODA)",
     "DECIDED_STATUSES = (CERTIFIED, NO_LINEAR_PAGODA, BUDGET)",
     "the set of outcomes that say something about the configuration quietly "
     "grows to include a resource limit"),
    ("M27-budget-meaning-reads-as-a-verdict", POTENTIAL,
     'BUDGET: "HiGHS hit its iteration limit; feasibility was not decided",',
     'BUDGET: "no weight function of this shape exists",',
     "the prose a human reads contradicts the status word beside it"),
    ("M28-artifact-hardcodes-the-infeasible-code", POTENTIAL,
     '            "solver_status": self.solver_status,',
     '            "solver_status": 2,',
     "the integer a reader would check the word against is faked"),
    ("M29-cell-local-word-renamed", ZEROSPACE,
     'CELL_LOCAL = "cell_local"', 'CELL_LOCAL = "local"',
     "the other scope word changes under consumers that filter on it"),
    ("M30-success-status-disagreement-ignored", POTENTIAL,
     "    if bool(result.success) != (word == CERTIFIED):",
     "    if False:",
     "a linprog result whose `success` and `status` disagree is classified "
     "anyway instead of refusing"),
    ("M31-disagreement-guard-only-one-way", POTENTIAL,
     "    if bool(result.success) != (word == CERTIFIED):",
     "    if bool(result.success) and word != CERTIFIED:",
     "the guard is narrowed back to the direction that was noticed first: "
     "`status == 0` with `success` false would then mint a Certificate out of "
     "whatever the failed solve left in `result.x`"),

    ("M25-degradation-keys-gated-on-the-run-not-the-label", ZEROSPACE,
     "        if self.scope == UNDETERMINED:", "        if not self.scope_exhaustive:",
     "cell-local rows in a truncated run also carry the degradation -- the "
     "design alternative, expected to survive"),
]

CONTROLS = [sys.executable, "-m", "tools.check_status_bit"]
SUITE = [sys.executable, "-m", "pytest", "tests/test_solver_status_bit.py",
         "-x", "--no-header", "-p", "no:cacheprovider"]
#: C11's file, run as a separate judge.  Kept apart from `SUITE` so the report
#: can say *which* defence caught a mutant: a mutant only the older file kills is
#: one this item added no coverage for, and that is worth seeing rather than
#: averaging away.
LEGACY = [sys.executable, "-m", "pytest", "tests/test_tool_failure_is_not_truth.py",
          "-x", "--no-header", "-p", "no:cacheprovider"]


def _stamp():
    """The tree this battery was actually run against.

    An adversarial review of E15 caught `MUTATION.json` reporting a survivor
    (`M30`) of an engine that had since been fixed: the artifact was three
    minutes older than `potential.py` and nothing on its face said so, so a
    reader trusting the machine-readable file over the prose got a wrong answer
    about the code they were about to merge.  A mutation report is a statement
    about a specific tree; if it does not name the tree it cannot be checked for
    staleness, which is this item's own complaint wearing a different hat.
    """
    def _git(*args):
        try:
            done = subprocess.run(["git", *args], cwd=ENGINE_RIG,
                                  capture_output=True, text=True)
            return done.stdout.strip() if done.returncode == 0 else None
        except OSError:                                  # pragma: no cover
            return None

    dirty = _git("status", "--porcelain", "engines", "tools", "tests")
    return {
        "head": _git("rev-parse", "HEAD"),
        "head_subject": _git("log", "-1", "--format=%s"),
        "engines_tools_tests_dirty": bool(dirty),
        "dirty_paths": [line[2:].strip()
                        for line in (dirty or "").splitlines()],
        "note": "if `head` is not the commit you are reviewing, or "
                "`engines_tools_tests_dirty` is true, these counts describe a "
                "different tree than the one you are about to merge",
    }


def _run(command):
    done = subprocess.run(command, cwd=ENGINE_RIG, capture_output=True, text=True)
    return done.returncode, (done.stdout + done.stderr)[-1200:]


def main():
    dry = "--dry-run" in sys.argv[1:]
    started = time.time()

    base_controls, _ = _run(CONTROLS)
    base_suite, _ = _run(SUITE)
    base_legacy, _ = _run(LEGACY)
    if (base_controls, base_suite, base_legacy) != (0, 0, 0):
        print("the unmutated tree is not green; nothing below would mean "
              "anything (controls=%d suite=%d legacy=%d)"
              % (base_controls, base_suite, base_legacy))
        return 2

    results = []
    for mutant_id, path, anchor, replacement, note in MUTANTS:
        with open(path, encoding="utf-8") as handle:
            original = handle.read()
        occurrences = original.count(anchor)
        if occurrences != 1:
            results.append({"id": mutant_id, "outcome": "not_applied",
                            "occurrences": occurrences, "note": note})
            continue
        if dry:
            results.append({"id": mutant_id, "outcome": "anchor_ok",
                            "note": note})
            continue
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(original.replace(anchor, replacement))
            controls_rc, controls_tail = _run(CONTROLS)
            suite_rc, suite_tail = _run(SUITE)
            legacy_rc, _ = _run(LEGACY)
        finally:
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(original)

        killed_by = []
        if controls_rc != 0:
            killed_by.append("tools.check_status_bit")
        if suite_rc != 0:
            killed_by.append("tests/test_solver_status_bit.py")
        if legacy_rc != 0:
            killed_by.append("tests/test_tool_failure_is_not_truth.py")
        results.append({
            "id": mutant_id,
            "file": os.path.relpath(path, ENGINE_RIG).replace(os.sep, "/"),
            "note": note,
            "controls_exit": controls_rc,
            "suite_exit": suite_rc,
            "legacy_exit": legacy_rc,
            "killed_by": killed_by,
            "outcome": "killed" if killed_by else "survived",
            "controls_tail": controls_tail if controls_rc else "",
        })

    killed = [r for r in results if r["outcome"] == "killed"]
    survived = [r for r in results if r["outcome"] == "survived"]
    stray = [r for r in results if r["outcome"] not in ("killed", "survived")]
    report = {
        "tree": _stamp(),
        "mutants": len(MUTANTS),
        "killed": len(killed),
        "survived": len(survived),
        "not_applied": len(stray),
        "killed_only_by_controls": [
            r["id"] for r in killed
            if r["killed_by"] == ["tools.check_status_bit"]],
        "killed_only_by_suite": [
            r["id"] for r in killed
            if r["killed_by"] == ["tests/test_solver_status_bit.py"]],
        "killed_only_by_the_older_c11_file": [
            r["id"] for r in killed
            if r["killed_by"] == ["tests/test_tool_failure_is_not_truth.py"]],
        "survivors": [{"id": r["id"], "note": r["note"]} for r in survived],
        "not_applied_ids": [r["id"] for r in stray],
        "wall_seconds": round(time.time() - started, 1),
        "results": results,
    }
    if not dry:
        with open(os.path.join(HERE, "MUTATION.json"), "w",
                  encoding="utf-8", newline="\n") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
    print(json.dumps({k: v for k, v in report.items() if k != "results"},
                     indent=2, sort_keys=True))
    return 0 if not stray else 1


if __name__ == "__main__":
    sys.exit(main())
