"""The recheck column: the third thing E8 asks for, per gradient step.

`test_ic3bounds_harness.py` pins the solve time and the invariant size;
`test_ic3bounds_emit.py` pins the translation and its count cross-check.  This
file pins the join -- that every rung of axis A carries an independent checker's
verdict, and that the two ways a column like this goes quietly wrong are both
closed:

* **A row with nothing to check must not read as a pass.**  The top of the
  ladder is a timeout.  There is no invariant on that row, so `status` is
  `n/a -- no invariant` and `is_pass` is False; a column that scored it green
  would be reporting a pass on an object that does not exist.
* **ACCEPT alone must not read as a pass either.**  The count cross-check is
  what makes the column non-vacuous, so it is asserted to be *evaluated* on
  every row -- both numbers present, both compared -- and a row whose recount
  disagrees with what the run recorded is shown turning red even while the
  rechecker still says ACCEPT.

Cheap on purpose, like the harness tests: nothing here goes above n=6.  The
sizes that cost minutes are covered by `recheck.verify_all`'s matrix and by
`test_ic3bounds_emit.py`, which re-run the engine once each.
"""

import copy
import json
import os

import pytest

from ic3bounds import axis_size, harness
from ic3bounds import recheck_column as column
from recheck import build_cases

FAST_BUDGET = 60.0


def _row(n, timeout=FAST_BUDGET, **kwargs):
    return harness.run_step(axis_size.spec_for(n, **kwargs),
                            timeout_seconds=timeout)


def _column(n, **kwargs):
    return column.column_for(_row(n, **kwargs))


# ------------------------------------------------------------------ the anchor

def test_the_m9_anchor_row_rechecks_accept_with_eight_of_eight():
    """M9's row, rechecked by something that never saw the engine.

    8 = 8 is the whole column in one line: the engine counted its invariant
    over 16 boolean tuples, `recheck/` counted the emitted predicate over the
    product of `peg4-0111`'s declared domains, and the two are the same set.
    """
    got = _column(4)
    assert got["status"] == "ACCEPT"
    assert got["exit_code"] == column.EXIT_ACCEPT == 0
    assert got["ruleset"] == "peg4-0111"
    assert got["ruleset_source"] == "recheck/cases/peg4-0111.rules.json"
    assert got["certificate"] == "peg4-0111-ic3-invariant"
    assert (got["engine_n_satisfying"], got["engine_n_states"]) == (8, 16)
    assert (got["recheck_n_satisfying"], got["recheck_n_states"]) == (8, 16)
    assert got["counts_agree"] is True
    assert got["agrees_with_recorded_row"] is True
    assert got["conditions"] == {
        "goal_break": True, "inv_closed": True, "inv_init": True,
        "predicate_wellformed": True, "ruleset_binding": True,
    }
    assert got["finding"] is False
    assert column.is_pass(got)


def test_the_column_reads_the_invariant_off_the_row_rather_than_re_running_ic3():
    """The row's own `cnf_text`, read back and re-rendered to prove it.

    The parent cannot afford a second `ic3()` -- 310s at n=12 and n=13 alone --
    so the invariant crosses as text.  Text is only as good as its round trip.
    """
    record = _row(4)
    system = harness.build_system(axis_size.spec_for(4))
    clauses = column.clauses_of(system, record["deterministic"])
    assert system.render_cnf(clauses) == record["deterministic"]["cnf_text"]
    assert len(clauses) == 2 and sum(len(c) for c in clauses) == 4


def test_a_reading_that_does_not_round_trip_is_refused():
    record = _row(4)
    record["deterministic"]["cnf_text"] = "(pos1 | !pos2) & (!pos1 | pos2)"
    system = harness.build_system(axis_size.spec_for(4))
    with pytest.raises(column.ColumnError):
        column.clauses_of(system, record["deterministic"])


def test_a_reading_that_loses_a_literal_is_refused_by_the_recorded_counts():
    record = _row(4)
    record["deterministic"]["cnf_text"] = "(!pos1) & (pos1 | !pos2)"
    system = harness.build_system(axis_size.spec_for(4))
    with pytest.raises(column.ColumnError) as raised:
        column.clauses_of(system, record["deterministic"])
    assert "literal" in str(raised.value)


# ------------------------------------------------- the row with nothing to check

def test_a_timed_out_row_reads_no_invariant_and_never_passed():
    """The boundary rung.  There is no invariant, so there is no verdict.

    This is the assertion the whole column exists to make honestly: n=14 is the
    result E8 was asked to find, and it must not arrive wearing a green tick.
    """
    got = column.column_for(_row(6, timeout=0.01))
    assert got["status"] == column.NO_INVARIANT == "n/a \u2014 no invariant"
    assert got["exit_code"] is None
    assert got["counts_agree"] is None
    assert got["engine_n_satisfying"] is None
    assert got["recheck_n_satisfying"] is None
    assert got["finding"] is False          # a boundary, not a defect
    assert column.is_pass(got) is False
    assert "pass" not in got["status"]
    assert "not a pass" in got["detail"]
    assert column.cell(got) == column.NO_INVARIANT


def test_every_verdict_without_an_invariant_gets_the_same_word():
    """`level-cap` is not a timeout, but it has no invariant either."""
    capped = column.column_for(_row(6, max_levels=2))
    assert capped["status"] == column.NO_INVARIANT
    assert column.is_pass(capped) is False

    for verdict in (harness.TIMEOUT, harness.LEVEL_CAP, harness.ENGINE_REFUSED,
                    harness.ADAPTER_MISMATCH, harness.COUNTEREXAMPLE):
        got = column.column_for(
            {"spec": axis_size.spec_for(4).as_json(),
             "deterministic": {"verdict": verdict}})
        assert got["status"] == column.NO_INVARIANT, verdict
        assert column.is_pass(got) is False, verdict


# ------------------------------------------------------- the count cross-check

def test_the_cross_check_is_evaluated_on_every_row_that_answered():
    """Not "was it configured" -- both numbers are on every row, and compared."""
    payload = axis_size.run(ns=(4, 6), timeout_seconds=FAST_BUDGET,
                            command="test")
    assert [step["spec"]["n"] for step in payload["steps"]] == [4, 6]
    for step in payload["steps"]:
        got = step["recheck"]
        assert got["status"] == "ACCEPT"
        # Both counts present, and the comparison actually made -- a `None`
        # here would mean the column was reporting a verdict nobody checked.
        assert isinstance(got["engine_n_satisfying"], int)
        assert isinstance(got["recheck_n_satisfying"], int)
        assert got["counts_agree"] is True
        assert got["agrees_with_recorded_row"] is True
        assert column.is_pass(got)
    assert [step["recheck"]["engine_n_satisfying"]
            for step in payload["steps"]] == [8, 30]
    assert payload["recheck_findings"] == []
    assert payload["recheck"]["taxonomy"]["2"].startswith("would-not-load")
    assert column.NO_INVARIANT in payload["recheck"]["no_invariant"]


def test_a_recount_that_disagrees_with_the_row_is_a_finding_not_a_pass():
    """The comparison is made, not copied.

    If the column simply echoed `n_satisfying` back at itself the assertion
    below would be unfalsifiable.  Move the recorded number and the row goes
    red while the independent verdict stays ACCEPT -- which is exactly the
    shape of failure a verdict-only column cannot see.
    """
    record = _row(4)
    record["deterministic"]["n_satisfying"] = 9
    got = column.column_for(record)
    assert got["status"] == "ACCEPT"                  # the verdict is unmoved
    assert got["agrees_with_recorded_row"] is False
    assert got["finding"] is True
    assert column.is_pass(got) is False
    assert "re-counting" in got["detail"]


def test_a_weakened_invariant_is_caught_although_it_still_rechecks_accept():
    """Trap 8, at the row level: the same set, or a different one?

    On peg-6 there is a one-literal weakening that satisfies all three
    conditions -- `tests/test_ic3bounds_emit.py` is where that is established.
    Written into a row it stays ACCEPT and denotes fewer states, so the counts
    are the only thing between the table and a green cell about the wrong
    object.  The assertion that some weakening survives the verdict is
    deliberate: if none does, this test has stopped demonstrating anything.
    """
    record = _row(6)
    system = harness.build_system(axis_size.spec_for(6))
    honest = column.clauses_of(system, record["deterministic"])
    recorded = record["deterministic"]["n_satisfying"]

    accepted_but_smaller = []
    for position, clause in enumerate(honest):
        for literal in sorted(clause):
            weakened = list(honest)
            weakened[position] = frozenset(x for x in clause if x != literal)
            forged = copy.deepcopy(record)
            forged["deterministic"]["cnf_text"] = system.render_cnf(weakened)
            forged["deterministic"]["n_clauses"] = len(weakened)
            forged["deterministic"]["n_literals"] = sum(len(c) for c in weakened)
            got = column.column_for(forged)
            if got["status"] != "ACCEPT":
                continue                      # refused on the merits
            if got["engine_n_satisfying"] == recorded:
                continue                      # a redundant literal: the same set
            accepted_but_smaller.append(got)

    assert accepted_but_smaller, (
        "peg-6 is here because a weakening of its invariant passes all three "
        "conditions. If none does any more the case must be re-chosen -- do not "
        "delete the assertion")
    for got in accepted_but_smaller:
        assert got["status"] == "ACCEPT"
        assert got["agrees_with_recorded_row"] is False
        assert got["finding"] is True
        assert column.is_pass(got) is False


# ----------------------------------------------------------------- the taxonomy

def test_the_taxonomy_is_rechecks_own_exit_codes_and_not_a_new_one():
    """`python -m recheck` already answers in five codes.  These are those."""
    from recheck import __main__ as recheck_cli
    from recheck.verify import ACCEPT, INCONSISTENT, REJECT

    assert recheck_cli.EXIT[ACCEPT] == column.EXIT_ACCEPT == 0
    assert recheck_cli.EXIT[REJECT] == column.EXIT_REJECT == 1
    assert recheck_cli.EXIT[INCONSISTENT] == column.EXIT_INCONSISTENT == 3
    # 2 and 4 have no verdict behind them, so they are read off the module the
    # exit codes are defined in rather than guessed at here.
    assert "2  the input would not load" in recheck_cli.__doc__
    assert "4  the recheck itself failed" in recheck_cli.__doc__
    assert column.EXIT_WOULD_NOT_LOAD == 2 and column.EXIT_CRASHED == 4
    assert set(column.STATUS_BY_EXIT) == {0, 1, 2, 3, 4}
    assert set(column.TAXONOMY) == {"0", "1", "2", "3", "4", "n/a"}


def test_a_certificate_too_big_to_load_is_uncheckable_and_not_a_pass():
    """`MAX_STATES` is the honest meaning of "uncheckable certificate".

    A 20-position board declares 2^20 = 1048576 states, above
    `recheck.ruleset.MAX_STATES`, so the rule set never becomes an object and
    there is no verdict to report -- exit 2, not a REJECT and emphatically not
    an ACCEPT.  No engine is run: the refusal happens before anything is built.
    """
    from recheck.ruleset import MAX_STATES

    n = 20
    assert 2 ** n > MAX_STATES >= 2 ** 13
    fabricated = {
        "spec": {"axis": "size", "label": "n=20", "n": n,
                 "initial": "0" + "1" * (n - 1),
                 "goal_states": ["01" + "0" * (n - 2)], "max_levels": 64},
        "deterministic": {"verdict": harness.INVARIANT,
                          "cnf_text": "(!pos1 | pos2)",
                          "n_clauses": 1, "n_literals": 2,
                          "n_satisfying": 1, "n_states": 2 ** n},
    }
    got = column.column_for(fabricated)
    assert got["exit_code"] == column.EXIT_WOULD_NOT_LOAD == 2
    assert got["status"] == "would-not-load"
    assert got["finding"] is True
    assert column.is_pass(got) is False
    assert got["recheck_n_satisfying"] is None
    assert "uncheckable" in got["detail"]


def test_a_crash_in_the_rechecker_is_not_reported_as_a_refusal():
    """Python's own status for an uncaught exception is 1, which is REJECT."""
    record = _row(4)
    record["deterministic"]["cnf_text"] = "pos1 & pos2"      # no parentheses
    got = column.column_for(record)
    assert got["exit_code"] == column.EXIT_CRASHED == 4
    assert got["exit_code"] != column.EXIT_REJECT
    assert got["status"] == "rechecker-crashed"
    assert got["finding"] is True
    assert column.is_pass(got) is False


def test_findings_name_the_row_and_the_run_fails_on_them():
    payload = axis_size.run(ns=(4,), timeout_seconds=FAST_BUDGET, command="test")
    assert payload["recheck_findings"] == []
    payload["steps"][0]["recheck"]["finding"] = True
    payload["steps"][0]["recheck"]["status"] = "REJECT"
    found = column.findings(payload["steps"])
    assert len(found) == 1 and found[0].startswith("n=4: REJECT")


# ------------------------------------------------------- the ladder is covered

def test_every_ladder_rung_that_answers_has_a_rule_set_available():
    """A rung whose size has no independent transcription has no column.

    Every rung but the last returned an invariant, so every rung but the last
    needs a rule set.  Two ways to have one, and the distinction is the point:
    the sizes in `build_cases.PEG_GRADIENT` have a **committed** case under
    `recheck/cases/`, and the rungs added when the ladder was made contiguous are
    **generated in memory** by `ruleset_for`, which hashes over exactly the bytes
    `build_cases` would have written.  Both are independent of the engine; only
    one is on disk.  A rung with neither would have no column at all, and this
    asserts there is no such rung.

    n=14 deliberately has no committed case: it timed out, there is no invariant,
    and a rule set nothing certifies would only be clutter.
    """
    answered = [n for n in axis_size.LADDER if n != 14]
    committed = {n for n, _, _ in build_cases.PEG_GRADIENT}
    generated = [n for n in answered if n not in committed]
    assert generated, "the ladder is contiguous, so some rungs are above the "                       "committed gradient -- if not, this test has gone stale"

    for n in answered:
        start = axis_size.initial_for(n)
        ruleset, source = column.ruleset_for(n, start, axis_size.goal_for(n))
        assert ruleset.name == build_cases.peg_name(start, n)
        if n in committed:
            assert source == "recheck/cases/%s.rules.json" % ruleset.name
            assert os.path.exists(column.case_path(n, start)), n
            certificate = os.path.join(
                build_cases.CASES_DIR,
                "%s-ic3.cert.json" % build_cases.peg_name(start, n))
            assert os.path.exists(certificate), n
        else:
            assert "no committed case" in source, n

    assert not os.path.exists(column.case_path(14, axis_size.initial_for(14)))


def test_the_committed_case_is_preferred_over_one_generated_on_the_spot():
    """The byte-checked file, where there is one: `--check` reviews that."""
    from recheck.ruleset import canonical_text

    ruleset, source = column.ruleset_for(4, "0111", "0100")
    assert source == "recheck/cases/peg4-0111.rules.json"
    with open(column.case_path(4, "0111"), "r", encoding="utf-8") as handle:
        # OPS-M cycle 32 merge note: `peg_ruleset` is now
        # `(start, goal, name, gradient)`; peg4 is an *anchored* case, so this is
        # the same call `all_cases` makes for `peg4-0111.rules.json` -- which is
        # what this assertion is about.
        assert handle.read().replace("\r\n", "\n") == canonical_text(
            build_cases.peg_ruleset("0111", goal="0100"))

    # And above the committed sizes the same generator answers, with the digest
    # it would have had as a file -- so the binding still means the file.
    ruleset, source = column.ruleset_for(9, "011111111", "010000000")
    assert "no committed case" in source
    assert ruleset.name == "peg9-011111111"


def test_the_column_carries_no_absolute_path_or_wall_clock():
    blob = json.dumps(_column(4))
    assert "C:\\" not in blob and "/home/" not in blob and "/tmp/" not in blob
    assert "engine-rig" not in blob
    assert "seconds" not in blob
