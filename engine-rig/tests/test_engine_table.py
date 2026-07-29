"""`ENGINE_TABLE.md` must agree with the runs it was built from.

A table nobody re-checks goes stale silently, and a stale table is worse than
none: it reads exactly as convincing as a current one. So the check is wired to
the suite rather than left to whoever remembers.

The three outcomes are kept apart, which is the whole discipline here:

* a fact disagreeing with its artifact **fails** — the table is wrong;
* the table being out of date **fails** — regenerate it;
* an artifact being *absent* **skips**, with the reason. Two of the twenty-one
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
    assert rc != 2, (
        "a placeholder survived substitution -- that is a defect in "
        "tools/engine_table.py, reproducible on every checkout, and must never "
        "take the skip branch above"
    )
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


def test_the_standing_rule_on_verified_is_published_and_names_the_held_out_rows():
    """The rule must be a gate, not a paragraph.

    E17's adversarial review (F17) found the rule stated in the file with no
    test behind it, and — worse — forbidding a word no cell used, which makes it
    unfalsifiable in both directions. So this binds it to something checkable:
    the rule is present, and the only two rows permitted to quote a held-out
    figure are the two that have one.
    """
    if not engine_table.TABLE.exists():
        pytest.skip("ENGINE_TABLE.md has not been generated on this machine")
    text = engine_table.TABLE.read_text(encoding="utf-8")

    assert engine_table.SELF_CONSISTENT in text, (
        "the standing rule's permitted wording is not published"
    )
    assert f"may not say 「{engine_table.VERIFIED}」" in text, (
        "the standing rule itself is missing from the table"
    )

    held_out_rows = {"`zero_space`", "`lp_potential`"}
    for row in engine_table.ROWS:
        claims_held_out = "Held out (E17)" in row["boundary"]
        assert claims_held_out == (row["engine"] in held_out_rows), (
            f"{row['engine']} disagrees with the standing rule: a row may claim a "
            "held-out figure only if E17 measured one for it, and both rows that "
            "have one must say so"
        )


def test_every_number_in_the_table_is_backed_by_a_probe():
    """No bare numeral may appear in the row prose.

    A digit written directly into the prose is a number no artifact verifies,
    and it would survive every drift check in this file. Identifiers and code
    constants are exempt by name, not by pattern, so adding one is a visible
    decision rather than a widened regex.
    """
    import re

    # The generator's own matcher, not a second copy of it. E13 found that the
    # copy here and the original in tools/engine_table.py had drifted into
    # agreeing on the same mistake -- both were `[a-z0-9_.]+`, so both were blind
    # to the three keys carrying a capital letter.
    placeholder = engine_table._PLACEHOLDER
    numeral = re.compile(r"(?<![\w.])\d[\d,. ]*")
    # Identifiers, code constants and combinatorics -- not measurements.
    exempt = {
        "0", "1", "2", "3", "4", "12", "16", "64", "0.0", "1.0", "1.9",
        "002", "003", "008", "014", "024", "0111",
        "2,3",      # the (2,3) object shape in probe_frontier's enumerated space
        "2, 3",     # a cross-reference to rows 2, 3 and 4
        # E17's smallest false-certificate witness. These are labels, not
        # measurements: two peg4 states and one jump geometry, each of which a
        # reader can look up in Fixture C. The weight vector that goes with them
        # is deliberately *not* in the prose -- it lives in the run's
        # `witnesses.false_certificates` block, because it is a measurement.
        "0100", "0011", "3,2,1",
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


def test_no_placeholder_survives_into_the_published_table():
    """The failure E13 found, pinned where it happened.

    Three keys -- `cegis.fixtureA_transitions`, `zs.fixtureB_features`,
    `zs.fixtureB_transitions` -- carry a capital letter, and `_PLACEHOLDER` was
    `[a-z0-9_.]+`, so the substituter never saw them. They were published into
    the table verbatim, braces and all, for two rows of the paper's engine
    section. Nothing caught it: `sub`'s unknown-key guard is only reachable by
    keys the pattern already matches, `--check` compared one unsubstituted table
    against another and reported "is current", and the numeral test above blanked
    lowercase placeholders only, so an unexpanded key contributed no digits and
    therefore no offender.

    This test reads the *published bytes* rather than the templates, because the
    templates were never wrong -- rendering was.
    """
    if not engine_table.TABLE.exists():
        pytest.skip("ENGINE_TABLE.md has not been generated on this machine")
    left = []
    for ln in engine_table.TABLE.read_text(encoding="utf-8").splitlines():
        if ln.startswith("|---"):
            continue
        # The provenance table at the end publishes probe regexes, which
        # legitimately contain braces. Those rows, and only those, are keyed by
        # `` `fact.key` `` in column 1; the eight engine rows are keyed by a
        # numeral, so this cannot hide a placeholder in the table proper.
        if ln.startswith("| "):
            key = ln.split("|")[1].strip()
            if key.startswith("`") and "." in key:
                continue
        left += [(ln[:40], p) for p in engine_table._unresolved(ln)]
    assert not left, (
        f"placeholder(s) published as text in the table: {left}. A number that is "
        "still a placeholder is worse than a missing one -- it reads as prose."
    )


def test_the_render_check_does_not_need_a_single_artifact():
    """The rendering guard has to be reachable on a partial checkout.

    E13's first version of this fix routed the failure through `ProbeError`, and
    `main` probes before it renders -- so on a checkout missing any of the 21
    artifacts, `verify()` raised first and the rendering fault came back as exit
    3, which this file's own first test *skips* on. The negative control turned
    the suite yellow rather than red, on exactly the checkouts where a rendering
    fault would go unnoticed longest.

    `render_selfcheck()` asks the artifact-free half of the question: does every
    template render at all? It must stay artifact-free, so this test asserts the
    result rather than the mechanism -- it passes on any checkout, including one
    with no `runs/` directory whatsoever.
    """
    assert engine_table.render_selfcheck() == []


def test_sub_refuses_a_key_its_own_matcher_cannot_see():
    """The guard that does not depend on `_PLACEHOLDER` being right.

    Widening the character class fixes today's three keys. It does not fix the
    next key that falls outside whatever the class is then, which is why `sub`
    now re-reads its own output with a deliberately dumber matcher. Feed it a key
    no plausible pattern would accept and it must still refuse to return text
    with a brace in it.
    """
    # PlaceholderError, not its parent: the two carry different exit codes and
    # therefore different suite outcomes (2 fails, 3 skips), so a test that
    # accepted either would pass again the day somebody collapsed them back.
    with pytest.raises(engine_table.PlaceholderError) as exc:
        engine_table.sub("the answer is {zs.fixtureÄ_features}", {"zs.ok": "1"})
    assert "survived substitution" in str(exc.value)
    assert issubclass(engine_table.PlaceholderError, engine_table.ProbeError)

    # And the ordinary path is untouched: a known key still substitutes.
    assert engine_table.sub("{a.b}", {"a.b": "7"}) == "7"


def test_the_ladder_derived_statistics_are_checked_by_something_other_than_themselves():
    """Six probes compute statistics; the tripwire only pins what they printed.

    `fd.wall_median`, `fd.search_share_median`, `fd.startup_band`,
    `fd.search_outlier`, `fd.wall_outlier` and `fd.crossover` are derivations,
    not transcriptions. A wrong `key=` in a `max()` or an off-by-one in the rung
    filter would be pinned as correct by the expectation beside it forever, which
    is the failure mode E13 was opened to fix one level up.

    So this checks the properties the derivations must have, from the artifact
    directly -- not the values, which the expectations already carry.
    """
    import json

    path = engine_table.REPO / "engine-rig/runs/20260728T072633Z-E2-fd-ladder-bench/ladder.json"
    if not path.exists():
        pytest.skip("the E2 bench artifact is not on this machine")
    rows = engine_table._fd_timed_rows(json.loads(path.read_text(encoding="utf-8")))

    # Every fd-* rung must be present, not silently dropped by the filter.
    raw = sum(1 for _, g in engine_table._ladder_rungs(
        json.loads(path.read_text(encoding="utf-8")))
        if str(g.get("tier", "")).startswith("fd-"))
    assert len(rows) == raw, (
        f"the rung filter dropped {raw - len(rows)} fd-* rows; every published "
        "median is then over a population nobody declared"
    )

    # The three clocks nest. If they ever stop nesting, "startup = wall -
    # fd_total" is not startup and the whole cell is wrong.
    for name, cfg, wall, fd_total, search in rows:
        assert search <= fd_total <= wall, (name, cfg, wall, fd_total, search)

    # The two outliers answer different questions and must be free to differ.
    by_share = max(rows, key=lambda r: r[4] / r[2])
    by_wall = max(rows, key=lambda r: r[2])
    assert by_share[2] <= by_wall[2]
    assert all(r[2] <= by_wall[2] for r in rows)
    assert all(r[4] / r[2] <= by_share[4] / by_share[2] for r in rows)
