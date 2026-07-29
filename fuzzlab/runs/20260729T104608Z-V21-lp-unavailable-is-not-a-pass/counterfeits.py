"""Seventeen ways to break V-21's machinery, and which tests notice.

C-11's lesson is that N mutants matching N tests measures nothing: a catalogue
built by reading the test file back is a catalogue of the tests, not of the code.
So this table is written against the **code paths**, not against the assertions,
and several entries below have no dedicated test on purpose. Survivors are
reported as survivors.

Each counterfeit is applied in a **fresh subprocess** — a botched restore cannot
poison a later row — and the V-21 gate set is then run under it. A counterfeit is
`killed` if at least one gate test fails, `SURVIVED` if the whole gate stays
green with the defect in place.

    python counterfeits.py                 # the whole table
    python counterfeits.py --only c-relabel-as-no-certificate
    python counterfeits.py --apply <id> -- <pytest args>    # internal: the child

The five targets, and why each is a place a defect could hide:

* `props/lp_potential.py`  -- the catch itself, and what it files;
* `props/finding.py`       -- the taxonomy, the required `cause`, `failures()`;
* `campaign.py`            -- the three coverage columns;
* `verify.py`              -- the one command a human actually reads;
* the *classification*, as opposed to the catching -- a skip filed under the
  wrong cause is caught by nothing that only checks a world was skipped.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from typing import Callable, Dict, List, NamedTuple

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

#: The gate: every test written for V-21, and the two it strengthened. Node ids
#: rather than whole files, so a counterfeit killed by an *unrelated* pre-existing
#: test is not miscredited to this item's work.
GATE = [
    "fuzzlab/tests/test_solver_unavailable.py",
    "fuzzlab/tests/test_finding_contract.py",
    "fuzzlab/tests/test_battery.py::test_nothing_went_unjudged_because_a_tool_could_not_compute",
    "fuzzlab/tests/test_battery.py::test_the_skip_breakdown_reconciles_with_the_skip_count",
    "fuzzlab/tests/test_battery.py::test_many_skips_on_one_world_do_not_send_the_coverage_column_negative",
    "fuzzlab/tests/test_battery.py::test_short_campaign_passes_the_gate_the_docstring_describes",
    "fuzzlab/tests/test_battery.py::test_a_dead_lp_potential_shows_up_as_lost_coverage",
]


class Counterfeit(NamedTuple):
    id: str
    target: str
    description: str
    #: What a reader would wrongly conclude if this defect were live and unnoticed.
    misreading: str
    apply: Callable[[], None]
    has_dedicated_test: bool


# ------------------------------------------------------------------ the patches

def _props():
    import fuzzlab.props.lp_potential as props
    return props


def _finding():
    from fuzzlab.props import finding
    return finding


def _campaign():
    from fuzzlab import campaign
    return campaign


# --- target: the catch in props/lp_potential.py

def _drop_the_catch() -> None:
    props = _props()

    def rethrow(world, invariant, exc):
        raise exc
    props._skip_solver_unavailable = rethrow


def _catch_only_one_invariant() -> None:
    """Three of four invariants revert to pre-V-21; one keeps the catch.

    The partial fix. A gate that checks "some solver_unavailable was filed"
    rather than "every invariant filed one" passes this.
    """
    props = _props()
    original_helper = props._skip_solver_unavailable

    def rethrow(world, invariant, exc):
        raise exc

    def wrap(fn):
        def inner(world):
            props._skip_solver_unavailable = rethrow
            try:
                return fn(world)
            finally:
                props._skip_solver_unavailable = original_helper
        return inner

    props.INVARIANTS = {
        name: (fn if name == "certificate_implies_unreachable" else wrap(fn))
        for name, fn in props.INVARIANTS.items()
    }


def _swallow_return_empty() -> None:
    """The V-13 defect shape, one entrance over: catch it and report nothing."""
    props = _props()
    props._skip_solver_unavailable = lambda world, invariant, exc: []


def _file_as_violated() -> None:
    """Over-strict rather than lax: blame the engine for HiGHS's iteration limit."""
    props = _props()
    finding = _finding()

    def blame(world, invariant, exc):
        return [finding.violated(props.ENGINE, invariant, world, str(exc))]
    props._skip_solver_unavailable = blame


def _drop_the_outcome_payload() -> None:
    """Skip filed, but without status / solver_status / bound / margin.

    No test was written for this. The world is still correctly unjudged and
    correctly attributed to the solver, so every count is right — what is lost is
    the ability to say *which* of status 1/3/4 fired, i.e. whether to raise a
    budget or to go and look at the arithmetic.
    """
    props = _props()
    finding = _finding()

    def bare(world, invariant, exc):
        return [finding.skipped(props.ENGINE, invariant, world, str(exc),
                                cause="solver_unavailable")]
    props._skip_solver_unavailable = bare


# --- target: the classification, as opposed to the catching

def _relabel_as_no_certificate() -> None:
    """The hard one, pre-registered as such: file it as the engine's own decline.

    Every count except `skips_by_cause` is identical between the two, because
    both are skips. This is the counterfeit that decides whether the `cause`
    column is load-bearing or decorative.
    """
    props = _props()
    finding = _finding()

    def relabel(world, invariant, exc):
        return [finding.skipped(props.ENGINE, invariant, world, str(exc),
                                cause="no_certificate")]
    props._skip_solver_unavailable = relabel


def _relabel_as_budget() -> None:
    """Right that it is about tooling, wrong that we chose it.

    `budget` says *this battery declined to pay*; `unavailable` says *nobody
    knows*. A defect that swaps them keeps the skip out of the `declined` column
    and still evades the gate on `unavailable`.
    """
    props = _props()
    finding = _finding()

    def relabel(world, invariant, exc):
        return [finding.skipped(props.ENGINE, invariant, world, str(exc),
                                cause="sweep_budget")]
    props._skip_solver_unavailable = relabel


def _unavailable_is_declined() -> None:
    """One character in the taxonomy: reclassify the class itself."""
    finding = _finding()
    finding.CAUSE_CLASS = dict(finding.CAUSE_CLASS,
                               solver_unavailable=finding.DECLINED)


# --- target: props/finding.py

def _failures_narrow_again() -> None:
    """Undo V-21's second half: `failures()` stops seeing `raised`."""
    finding = _finding()
    finding.failures = lambda fs: [f for f in fs if f.kind == finding.VIOLATED]


def _cause_validation_off() -> None:
    """An undeclared cause silently becomes `declined` instead of raising."""
    finding = _finding()
    finding.cause_class = lambda cause: finding.CAUSE_CLASS.get(
        cause, finding.DECLINED)


def _skipped_cause_defaults() -> None:
    """`cause` stops being required and defaults to the commonest value.

    The shape the old convention would have decayed into. No test was written
    against the *default* specifically.
    """
    finding = _finding()
    original = finding.skipped

    def lax(engine, invariant, world, reason, *, cause="no_certificate", **data):
        return original(engine, invariant, world, reason, cause=cause, **data)
    finding.skipped = lax


def _raised_loses_its_cause() -> None:
    """`raised` findings stop recording which exception it was. No test for this."""
    finding = _finding()
    original = finding.raised

    def blank(engine, invariant, world, exc):
        f = original(engine, invariant, world, exc)
        f.cause = ""
        return f
    finding.raised = blank


def _cause_class_blank_for_skips() -> None:
    """`Finding.cause_class` returns "" for skips, so every roll-up loses its axis."""
    finding = _finding()
    finding.Finding.cause_class = property(lambda self: "")


# --- target: campaign.py

def _unavailable_always_zero() -> None:
    campaign = _campaign()
    original = campaign.run_engine

    def zeroed(*a, **k):
        result = original(*a, **k)
        report = result["report"]
        report["unavailable"] = 0
        report["invariant_worlds_unavailable"] = {
            k2: 0 for k2 in report["invariant_worlds_unavailable"]}
        return result
    campaign.run_engine = zeroed


def _skips_by_cause_empty() -> None:
    campaign = _campaign()
    original = campaign.run_engine

    def emptied(*a, **k):
        result = original(*a, **k)
        result["report"]["skips_by_cause"] = {
            k2: {} for k2 in result["report"]["skips_by_cause"]}
        return result
    campaign.run_engine = emptied


def _evaluated_ignores_skips() -> None:
    """The pre-V-13 column, restored: every world counted as evaluated."""
    campaign = _campaign()
    original = campaign.run_engine

    def inflated(*a, **k):
        result = original(*a, **k)
        report = result["report"]
        report["invariant_worlds_evaluated"] = {
            k2: report["worlds_requested"]
            for k2 in report["invariant_worlds_evaluated"]}
        return result
    campaign.run_engine = inflated


def _worlds_columns_count_findings() -> None:
    """The BLOCKER an adversarial pass found, restored.

    `invariant_worlds_evaluated` / `invariant_worlds_unavailable` counted skip
    *findings* rather than distinct seeds. Equal only while no property files two
    skips for one world; `cegis_miner.frontier_is_complete_to_size` files one per
    rule, and forcing its budget low enough produced `evaluated: -56` over 12
    worlds. Added after the review, so it is a counterfeit for a defect that was
    real rather than hypothetical.
    """
    campaign = _campaign()
    finding = _finding()
    original = campaign.run_engine

    def by_findings(*a, **k):
        result = original(*a, **k)
        report = result["report"]
        counts = {}
        for f in result["findings"]:
            if f.kind == finding.SKIPPED:
                counts[f.invariant] = counts.get(f.invariant, 0) + 1
        report["invariant_worlds_evaluated"] = {
            name: report["worlds_requested"] - counts.get(name, 0)
            for name in report["invariant_worlds_evaluated"]}
        return result
    campaign.run_engine = by_findings


def _campaign_exit_ignores_unavailable() -> None:
    """`campaign.main` stops exiting non-zero on `unavailable` — finding 5's half."""
    campaign = _campaign()
    original = campaign.main

    def lenient(argv=None):
        code = original(argv)
        return 0 if code == 1 else code
    campaign.main = lenient


def _unavailable_counted_as_evaluated() -> None:
    """The exact V-21 defect, moved from the property into the report.

    The skip is filed correctly and attributed correctly; the coverage column
    then adds it back. Identical net effect, one file away.
    """
    campaign = _campaign()
    original = campaign.run_engine

    def added_back(*a, **k):
        result = original(*a, **k)
        report = result["report"]
        report["invariant_worlds_evaluated"] = {
            name: value + report["invariant_worlds_unavailable"].get(name, 0)
            for name, value in report["invariant_worlds_evaluated"].items()}
        return result
    campaign.run_engine = added_back


TABLE: List[Counterfeit] = [
    Counterfeit("c-drop-the-catch", "props/lp_potential.py",
                "the LpUnavailable catch re-raises: exactly the pre-V-21 code",
                "the solver's silence is coverage",
                _drop_the_catch, True),
    Counterfeit("c-catch-only-one-invariant", "props/lp_potential.py",
                "one of four invariants keeps the catch, three revert",
                "three quarters of the fix, reported as all of it",
                _catch_only_one_invariant, True),
    Counterfeit("c-swallow-return-empty", "props/lp_potential.py",
                "the catch returns [] -- caught and unreported",
                "the V-13 defect through a new entrance",
                _swallow_return_empty, True),
    Counterfeit("c-file-as-violated", "props/lp_potential.py",
                "an iteration limit is filed as an engine violation",
                "the engine is blamed for HiGHS; a false accusation",
                _file_as_violated, True),
    Counterfeit("c-drop-the-outcome-payload", "props/lp_potential.py",
                "the skip carries no status / solver_status / bound / margin",
                "unjudged, attributable to the solver, but not diagnosable",
                _drop_the_outcome_payload, False),
    Counterfeit("c-relabel-as-no-certificate", "the classification",
                "solver_unavailable is filed as no_certificate",
                "a starved solver reads as the engine's documented incompleteness",
                _relabel_as_no_certificate, True),
    Counterfeit("c-relabel-as-budget", "the classification",
                "solver_unavailable is filed as sweep_budget",
                "a solver failure reads as a cost we chose to decline",
                _relabel_as_budget, False),
    Counterfeit("c-unavailable-is-declined", "props/finding.py",
                "CAUSE_CLASS moves solver_unavailable into `declined`",
                "the gate on `unavailable` can never fire",
                _unavailable_is_declined, False),
    Counterfeit("c-failures-narrow-again", "props/finding.py",
                "failures() returns VIOLATED only, as it did before V-21",
                "a crashing property is not a failure",
                _failures_narrow_again, True),
    Counterfeit("c-cause-validation-off", "props/finding.py",
                "an undeclared cause defaults to `declined` instead of raising",
                "a new bucket can be added without anyone classifying it",
                _cause_validation_off, True),
    Counterfeit("c-skipped-cause-defaults", "props/finding.py",
                "cause stops being required; it defaults to no_certificate",
                "the convention decays back to what it was, silently",
                _skipped_cause_defaults, False),
    Counterfeit("c-raised-loses-its-cause", "props/finding.py",
                "raised findings no longer record the exception type",
                "triage cannot group crashes without reading tracebacks",
                _raised_loses_its_cause, False),
    Counterfeit("c-cause-class-blank", "props/finding.py",
                "Finding.cause_class returns \"\" for every skip",
                "the second axis disappears from every roll-up",
                _cause_class_blank_for_skips, False),
    Counterfeit("c-unavailable-always-zero", "campaign.py",
                "invariant_worlds_unavailable is reported as 0",
                "the gate reads green because the number was blanked",
                _unavailable_always_zero, False),
    Counterfeit("c-skips-by-cause-empty", "campaign.py",
                "skips_by_cause is reported empty",
                "the breakdown that makes the skip auditable is gone",
                _skips_by_cause_empty, False),
    Counterfeit("c-evaluated-ignores-skips", "campaign.py",
                "invariant_worlds_evaluated is the world count again",
                "the pre-V-13 coverage column, restored",
                _evaluated_ignores_skips, True),
    Counterfeit("c-worlds-columns-count-findings", "campaign.py",
                "the world columns subtract skip findings instead of seeds",
                "a coverage column that has been observed at -56 out of 12",
                _worlds_columns_count_findings, True),
    Counterfeit("c-campaign-exit-ignores-unavailable", "campaign.py",
                "campaign.main stops exiting non-zero on unavailable",
                "'gated' is true of a 25-world test and false of the artifact",
                _campaign_exit_ignores_unavailable, False),
    Counterfeit("c-unavailable-counted-as-evaluated", "campaign.py",
                "the coverage column adds the unavailable skips back",
                "V-21's defect, relocated from the property into the report",
                _unavailable_counted_as_evaluated, False),
]

BY_ID = {c.id: c for c in TABLE}


# ------------------------------------------------------------------ the driver

def _child(counterfeit_id: str, pytest_args: List[str]) -> int:
    import pytest
    if counterfeit_id != "__none__":
        BY_ID[counterfeit_id].apply()
    return pytest.main(["-q", "--no-header", "-p", "no:cacheprovider",
                        *pytest_args])


def _run(counterfeit_id: str) -> Dict[str, object]:
    started = time.time()
    proc = subprocess.run(
        [sys.executable, os.path.abspath(__file__), "--apply", counterfeit_id,
         "--", *GATE],
        cwd=ROOT, capture_output=True)
    text = (proc.stdout + proc.stderr).decode("utf-8", "replace")
    failed = [line.split(" ")[1] for line in text.splitlines()
              if line.startswith("FAILED ")]
    return {
        "id": counterfeit_id,
        "returncode": proc.returncode,
        "killed": proc.returncode != 0,
        "failing_tests": sorted({f for f in failed}),
        "n_failing": len(set(failed)),
        "elapsed_s": round(time.time() - started, 1),
        "tail": text.strip().splitlines()[-1:],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", default=None, help="internal: the child mode")
    parser.add_argument("--only", default=None)
    parser.add_argument("--out", default=os.path.join(HERE, "COUNTERFEITS.json"))
    parser.add_argument("rest", nargs="*")
    args = parser.parse_args()

    if args.apply:
        return _child(args.apply, args.rest)

    print("baseline (no counterfeit): ", end="", flush=True)
    base = _run("__none__")
    print("rc=%d %s  %.0fs" % (base["returncode"], base["tail"], base["elapsed_s"]))
    if base["killed"]:
        print("BASELINE NOT GREEN -- every row below would be uninterpretable")
        return 1

    table = [c for c in TABLE if args.only in (None, c.id)]
    rows = []
    for counterfeit in table:
        row = _run(counterfeit.id)
        row.update(target=counterfeit.target,
                   description=counterfeit.description,
                   misreading=counterfeit.misreading,
                   has_dedicated_test=counterfeit.has_dedicated_test)
        rows.append(row)
        print("  %-38s %-22s %s  (%d failing, %.0fs)"
              % (counterfeit.id, counterfeit.target,
                 "killed  " if row["killed"] else "SURVIVED",
                 row["n_failing"], row["elapsed_s"]), flush=True)

    survivors = [r for r in rows if not r["killed"]]
    report = {
        "gate": GATE,
        "baseline": base,
        "counterfeits": rows,
        "n_counterfeits": len(rows),
        "n_survivors": len(survivors),
        "survivors": [r["id"] for r in survivors],
        "n_without_a_dedicated_test": sum(
            1 for r in rows if not r["has_dedicated_test"]),
    }
    with open(args.out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("\n%d counterfeits, %d survivors (%s)"
          % (len(rows), len(survivors), ", ".join(report["survivors"]) or "none"))
    print("%d of %d had no dedicated test written for them"
          % (report["n_without_a_dedicated_test"], len(rows)))
    print("-> %s" % args.out)
    # Survivors are the finding, not a failure of this script.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
