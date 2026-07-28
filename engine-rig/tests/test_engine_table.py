"""`ENGINE_TABLE.md` must agree with the runs it was built from.

A table nobody re-checks goes stale silently, and a stale table is worse than
none: it reads exactly as convincing as a current one. So the check is wired to
the suite rather than left to whoever remembers.

The three outcomes are kept apart, which is the whole discipline here:

* a fact disagreeing with its artifact **fails** — the table is wrong;
* the table being out of date **fails** — regenerate it;
* an artifact being *absent* **skips**, with the reason. Two of the nineteen
  artifacts live outside `engine-rig/` (`fuzzlab/`, `theoria-arm/`), and a
  checkout without them cannot run this check. Reporting that as a pass would be
  the mistake D-030 names: a missing cross-check is a missing check, not a
  green one.
"""

from __future__ import annotations

import pytest

from tools import engine_table


def test_the_table_is_current_and_every_fact_still_matches_its_artifact():
    rc = engine_table.main(["--check"])
    if rc == 3:
        pytest.skip("an artifact ENGINE_TABLE.md is built from is not on this machine")
    assert rc == 0, (
        "ENGINE_TABLE.md disagrees with the runs under it. Either a run was "
        "edited (re-read it, then update the expectation in tools/engine_table.py) "
        "or the table was not regenerated (`python -m tools.engine_table`)."
    )


def test_no_row_may_leave_its_boundary_cell_blank():
    """The one rule the work order named, enforced rather than trusted.

    A row with nothing in the boundary column reads as "no boundary", which is
    the opposite of what an empty cell means.
    """
    for row in engine_table.ROWS:
        assert row["boundary"].strip(), f"{row['engine']} has an empty boundary cell"


def test_a_boundary_that_was_never_measured_says_so_in_those_words():
    """`ic3_pdr` is the row this table exists to be honest about.

    If somebody later fills that cell in with a boundary, this test should be
    deleted in the same commit as the run that measured it -- and not before.
    """
    ic3 = next(r for r in engine_table.ROWS if "ic3_pdr" in r["engine"])
    # `{unmeasured}` is the placeholder the renderer expands to the literal.
    assert "{unmeasured}" in ic3["boundary"] or engine_table.UNMEASURED in ic3["boundary"], (
        "ic3_pdr's boundary is unmeasured (one certificate, one configuration, "
        "one 16-state fixture, no property module). If that has changed, the "
        "run that changed it goes in runs/ and this test goes with it."
    )

    # And the published file must actually carry the word, not just the source.
    if not engine_table.TABLE.exists():
        pytest.skip("ENGINE_TABLE.md has not been generated on this machine")
    row = next(
        (ln for ln in engine_table.TABLE.read_text(encoding="utf-8").splitlines()
         if ln.startswith("| 8 |") and "ic3_pdr" in ln),
        None,
    )
    assert row is not None, "ic3_pdr's row is missing from the published table"
    assert engine_table.UNMEASURED in row, (
        "the published ic3_pdr row does not say 边界未测 -- an unmeasured "
        "boundary has been written as a measured one, which is the one way "
        "this table can do real damage."
    )


def test_every_number_in_the_table_is_backed_by_a_probe():
    """No bare numeral may appear in the row prose.

    A digit written directly into the prose is a number no artifact verifies,
    and it would survive every drift check in this file. Identifiers and code
    constants are exempt by name, not by pattern, so adding one is a visible
    decision rather than a widened regex.
    """
    import re

    placeholder = re.compile(r"\{[a-z0-9_.]+\}")
    numeral = re.compile(r"(?<![\w.])\d[\d,. ]*")
    # Identifiers, code constants and combinatorics -- not measurements.
    exempt = {
        "0", "1", "2", "3", "4", "12", "16", "64", "0.0", "1.0", "1.9",
        "002", "003", "008", "024", "0111",
        "2,3",      # the (2,3) object shape in probe_frontier's enumerated space
        "2, 3",     # a cross-reference to rows 2, 3 and 4
    }
    offenders = []
    for row in engine_table.ROWS:
        for col in ("solves", "fixture", "recheck", "boundary"):
            blanked = placeholder.sub("\x00", row[col])
            for m in numeral.finditer(blanked):
                token = m.group(0).strip().rstrip(",.")
                if token in exempt:
                    continue
                offenders.append((row["engine"], col, token))
    assert not offenders, f"unbacked numerals in the table prose: {offenders}"
