"""E18 (D-036) — the linkage between a paper number and a script that makes it.

These tests are deliberately **fast**: they check that the path from artefact to
script exists and is unbroken, not that the numbers are right.  Recomputing them
means thousands of worlds and belongs in `verify.py`'s rung 4, which runs
`tools.survey_numbers.run_all --check`.

The distinction matters and is the reason this file is short.  A suite that
recomputed everything would be too slow to run, would therefore be skipped, and
a skipped check is exactly the failure E18 was filed about.  So: the suite
guards the wiring, the gate guards the values.
"""

import importlib
import json
import re
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ENGINE_RIG = HERE.parent
REPO = ENGINE_RIG.parent
COUNTS = ENGINE_RIG / "runs" / "20260730T120000Z-E18" / "counts"
PKG_DIR = ENGINE_RIG / "tools" / "survey_numbers"

# The run directory whose numbers were prose-only.  Any ENGINE_TABLE registry
# entry still sourced from here is a number with no script behind it.
E11 = "runs/20260729T000000Z-E11-engine-crosscheck-deep"


def committed_counts():
    if not COUNTS.is_dir():
        return []
    return sorted(p for p in COUNTS.glob("*.json") if p.name != "SUMMARY.json")


def test_package_is_discoverable_and_non_empty():
    """An empty sweep is not a pass — verify.py's own rule, one level down."""
    from tools.survey_numbers.run_all import discover

    names = discover()
    assert names, (
        "tools/survey_numbers has no recomputation modules. Rung 4 would then "
        "check nothing and print green, which is the shape of defect E18 was "
        "filed about."
    )


def test_every_module_exposes_compute():
    from tools.survey_numbers.run_all import discover

    for name in discover():
        mod = importlib.import_module(f"tools.survey_numbers.{name}")
        assert callable(getattr(mod, "compute", None)), (
            f"tools/survey_numbers/{name}.py has no compute(); run_all cannot "
            f"run it, so whatever number it was written for is unscripted again."
        )


def test_committed_counts_name_a_module_that_still_exists():
    """A counts file whose producer was renamed away is prose with a .json suffix."""
    counts = committed_counts()
    assert counts, f"no committed counts under {COUNTS.relative_to(REPO)}"
    for path in counts:
        rec = json.loads(path.read_text(encoding="utf-8"))
        module = rec.get("module")
        assert module, f"{path.name} does not record which module produced it"
        importlib.import_module(module)  # raises if it is gone


def test_every_counts_file_records_its_inputs_with_digests():
    """A recomputation whose inputs are not pinned can move without anyone noticing."""
    for path in committed_counts():
        rec = json.loads(path.read_text(encoding="utf-8"))
        inputs = rec.get("inputs")
        assert inputs, f"{path.name} names no inputs"
        missing = [i["path"] for i in inputs if i.get("sha256") is None]
        assert not missing, (
            f"{path.name} claims inputs that were absent when it ran: {missing}"
        )


@pytest.mark.parametrize("path", committed_counts(), ids=lambda p: p.stem)
def test_disagreement_with_e11_is_recorded_not_hidden(path):
    """Where the recomputation differs from the 2026-07-29 prose, both are on disk.

    The rule from the work order: the recomputed value is the number of record,
    and the difference is written down rather than smoothed over.  This test
    enforces the second half — a module may disagree with E11, but it may not
    disagree silently.
    """
    rec = json.loads(path.read_text(encoding="utf-8"))
    assert "e11_prose" in rec, f"{path.name} does not record what E11 claimed"
    if rec.get("agrees_with_e11") is False:
        assert rec.get("caveats"), (
            f"{path.name} disagrees with the E11 report and says nothing about "
            f"why. A bare replacement number is the same kind of evidence the "
            f"old one was."
        )


def test_no_registry_entry_still_resolves_only_to_e11_prose():
    """The structural fix: `ENGINE_TABLE.md`'s numbers point at scripts, not at reports.

    `tools/engine_table.py` probes each published number out of an artefact. For
    the cross-check's numbers that artefact was a *Markdown report*, so the probe
    proved the table's digits matched the report's digits and proved nothing
    about whether the report's digits matched a computation.  Every such probe
    that this ticket rescripted is re-pointed at `runs/.../counts/*.json`.

    Entries still pointing into the E11 run directory are listed in
    `UNSCRIPTED` below with a reason, so the exception is visible rather than
    implied by absence.
    """
    from tools import engine_table

    from tools.survey_numbers.unscripted import UNSCRIPTED

    still_prose = {
        key: getattr(probe, "where", "?")
        for key, (_expect, probe) in engine_table.FACTS.items()
        if E11 in getattr(probe, "where", "")
    }
    undeclared = sorted(set(still_prose) - set(UNSCRIPTED))
    assert not undeclared, (
        "these ENGINE_TABLE numbers are still probed out of E11 prose and are "
        "not declared in tools/survey_numbers/unscripted.py:\n  "
        + "\n  ".join(f"{k}  <-  {still_prose[k]}" for k in undeclared)
        + "\n\nEither give the number a script (tools/survey_numbers/) and "
          "re-point the probe at its counts JSON, or declare it unscripted "
          "with a reason. A number nobody can recompute may not be quietly "
          "inherited."
    )
    stale = sorted(set(UNSCRIPTED) - set(still_prose))
    assert not stale, (
        f"declared unscripted but no longer probed from E11 prose: {stale}. "
        f"Delete the declaration; a stale exemption reads like coverage."
    )
