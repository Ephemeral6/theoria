"""Tests for the E8 measurement harness.

Offline, and cheap on purpose: the ladder's whole point is that its top rungs
cost minutes, so no test goes above n=6.  n=4 is the M9 anchor and n=6 is the
first rung that is genuinely a different size; between them they exercise every
branch of the taxonomy without spending a budget.

The two things these tests exist to stop are both mistakes that would leave the
table looking fine:

* the ladder drifting off its own anchor (the `goal_states=None` trap), and
* a deterministic field quietly turning into a timing one.
"""

import dataclasses
import json
import os

import pytest

from engines.ic3_pdr import pdr
from engines.ic3_pdr.system import System, cube_of, negate
from ic3bounds import axis_size, harness
from ic3bounds.harness import StepSpec

# Enough for a subprocess launch plus the engine at n=6 (~0.1s here), with a
# wide margin so a loaded machine does not turn a passing test red.
FAST_BUDGET = 60.0


def _run(n, timeout=FAST_BUDGET, **kwargs):
    return harness.run_step(axis_size.spec_for(n, **kwargs), timeout_seconds=timeout)


# ----------------------------------------------------------------- the anchor

def test_anchor_row_is_the_m9_invariant_character_for_character():
    record = _run(4)
    det = record["deterministic"]
    assert det["verdict"] == harness.INVARIANT
    assert det["cnf_text"] == "(!pos1 | pos2) & (pos1 | !pos2)"
    assert det["n_clauses"] == 2
    assert det["n_literals"] == 4
    assert det["converged_at_frame"] == 2
    assert det["coverage"] == "8/16"
    assert det["checker_conditions"] == {
        "goal_break": True, "inv_closed": True, "inv_init": True,
    }
    axis_size.check_anchor(record)          # must not raise


def test_the_anchor_trap_default_goal_states_is_a_different_question():
    """`build_graph(goal_states=None)` means ALL single-peg finals.

    At n=4 that is not the M9 question and does not have the M9 answer, so a
    ladder that took the default would start one rung to the side of the point
    it claims to extend.  Pinned here so the trap cannot be re-entered quietly.
    """
    trap = StepSpec(axis="size", label="n=4-trap", n=4, initial="0111",
                    goal_states=("1000", "0100", "0010", "0001"))
    det = harness.run_step(trap, timeout_seconds=FAST_BUDGET)["deterministic"]
    assert det["verdict"] == harness.INVARIANT
    assert det["cnf_text"] != "(!pos1 | pos2) & (pos1 | !pos2)"
    assert det["n_clauses"] == 4
    assert det["coverage"] == "3/16"


def test_check_anchor_raises_rather_than_warns_on_drift():
    record = _run(4)
    record["deterministic"]["cnf_text"] = "(pos0)"
    with pytest.raises(harness.AnchorDrift):
        axis_size.check_anchor(record)


def test_the_ladder_asks_for_the_anchor_goal_explicitly():
    assert axis_size.spec_for(4).goal_states == ("0100",)
    assert axis_size.spec_for(4).initial == "0111"
    assert axis_size.spec_for(6).goal_states == ("010000",)


# -------------------------------------------------------------- the taxonomy

def test_a_tiny_budget_produces_a_timeout_flagged_as_a_machine_statement():
    record = harness.run_step(axis_size.spec_for(6), timeout_seconds=0.01)
    det = record["deterministic"]
    assert det["verdict"] == harness.TIMEOUT
    # The one place a "deterministic" field is not: a faster machine finishes
    # what this one did not, and the record has to say so or a verify pass will
    # report the good news as a defect.
    assert det["machine_dependent"] is True
    assert det["escalate"] is False
    assert "this machine" in det["detail"]
    assert record["budget_seconds"] == 0.01
    assert record["timing"]["wall_seconds"] > 0
    # Nothing was measured, so nothing is claimed -- except what the spec alone
    # already fixes.
    assert det["n_clauses"] is None and det["converged_at_frame"] is None
    assert det["n_states"] == 64 and det["cube_limit"] == 6


def test_level_cap_is_not_the_same_word_as_timeout():
    """A cap we set is not a limit of the engine, and they get different rows."""
    record = _run(6, max_levels=2)
    det = record["deterministic"]
    assert det["verdict"] == harness.LEVEL_CAP
    assert det["verdict"] != harness.TIMEOUT
    assert det["escalate"] is False
    assert det["machine_dependent"] is False
    assert "no verdict within 2 levels" in det["detail"]
    assert "raising max_levels" in det["detail"]
    # n=6 really does converge, given the levels: the cap is the only reason.
    assert _run(6)["deterministic"]["converged_at_frame"] == 7


def test_a_solvable_configuration_comes_back_as_a_replayed_counterexample():
    spec = StepSpec(axis="size", label="n=4-solvable", n=4, initial="0111",
                    goal_states=("1001",))
    det = harness.run_step(spec, timeout_seconds=FAST_BUDGET)["deterministic"]
    assert det["verdict"] == harness.COUNTEREXAMPLE
    assert det["counterexample_length"] == 1
    assert det["checker_conditions"] == {"replayed": True}
    assert det["n_clauses"] is None


def test_escalating_verdicts_are_defects_and_never_the_boundary():
    assert set(harness.ESCALATING) == {harness.ENGINE_REFUSED,
                                       harness.ADAPTER_MISMATCH}
    fake = [
        {"spec": {"n": 4, "label": "n=4"},
         "budget_seconds": 1.0,
         "deterministic": {"verdict": harness.ENGINE_REFUSED, "escalate": True,
                           "machine_dependent": False, "n_states": 16,
                           "detail": "checker refused"}},
        {"spec": {"n": 6, "label": "n=6"},
         "budget_seconds": 1.0,
         "deterministic": {"verdict": harness.TIMEOUT, "escalate": False,
                           "machine_dependent": True, "n_states": 64,
                           "detail": "budget"}},
    ]
    boundary = axis_size.boundary_of(fake)
    assert boundary["verdict"] == harness.TIMEOUT     # not the refusal
    assert boundary["n"] == 6
    assert axis_size.escalations(fake) == [
        "n=4: engine-refused -- checker refused"
    ]


def test_there_is_no_generalisation_failure_category_because_it_cannot_happen():
    """`generalise` always terminates and always returns a clause.

    Worst case it drops nothing and hands back the full negated cube.  So the
    failure mode does not exist in this implementation, no verdict names it, and
    the drift toward the cube limit is recorded as a continuous quantity instead.
    """
    assert not any("generalis" in verdict for verdict in harness.VERDICTS)

    system = harness.build_system(axis_size.spec_for(4))
    run = pdr._Run(system=system, frames=[set(), set()])
    for state in system.states:
        clause = negate(cube_of(state))
        result = run.generalise(clause, 1)
        assert isinstance(result, frozenset)
        assert 1 <= len(result) <= len(clause)
        assert result <= clause

    det = _run(4)["deterministic"]
    assert det["literal_saturation"] == pytest.approx(4 / (2 * 4))
    assert det["widest_clause"] == 2 and det["cube_limit"] == 4


# --------------------------------------------------------- literals and vacuity

def test_n_literals_is_computed_here_because_the_engine_does_not_report_it():
    fields = {f.name for f in dataclasses.fields(pdr.Invariant)}
    assert "n_literals" not in fields
    assert not hasattr(pdr.Invariant, "n_literals")
    assert hasattr(pdr.Invariant, "n_clauses")          # the one it does report

    spec = axis_size.spec_for(6)
    system = harness.build_system(spec)
    verdict = pdr.ic3(system, max_levels=spec.max_levels)
    expected = sum(len(clause) for clause in verdict.clauses)

    det = harness.run_step(spec, timeout_seconds=FAST_BUDGET)["deterministic"]
    assert det["n_literals"] == expected
    assert det["n_clauses"] == verdict.n_clauses
    assert det["n_literals"] != det["n_clauses"]


def test_every_row_carries_the_vacuity_fraction():
    for n, coverage, ratio in ((4, "8/16", 0.5), (6, "30/64", 30 / 64)):
        det = _run(n)["deterministic"]
        assert det["coverage"] == coverage
        assert det["coverage_ratio"] == pytest.approx(ratio)
        assert det["near_vacuous"] is False
        assert det["n_satisfying"] * det["n_states"] > 0


def test_near_vacuous_is_a_stated_threshold_not_a_hidden_one():
    assert 0.5 < harness.NEAR_VACUOUS_RATIO < 1.0


# ------------------------------------------------ the deterministic/timing split

def test_two_runs_agree_on_every_deterministic_field():
    first = _run(6)
    second = _run(6)
    assert harness.deterministic_differences(first, second) == []
    left = dict(first["deterministic"])
    right = dict(second["deterministic"])
    left.pop("detail")
    right.pop("detail")
    assert left == right


def test_timings_are_checked_for_presence_and_ordering_never_equality():
    first = _run(6)
    second = _run(6)
    for record in (first, second):
        assert harness.timing_problems(record) == []
        timing = record["timing"]
        assert timing["wall_seconds"] > 0
        assert timing["ic3_seconds"] is not None
        # The engine's own clocks live inside the subprocess wall clock; that
        # ordering is the only thing anybody may assert about them.
        assert timing["ic3_seconds"] <= timing["wall_seconds"]
        assert timing["build_seconds"] <= timing["wall_seconds"]
    # And equality is emphatically NOT asserted: the split exists because these
    # two numbers are allowed to differ, and a verify pass must ignore them.
    assert "wall_seconds" not in harness.DETERMINISTIC_FIELDS
    assert "ic3_seconds" not in harness.DETERMINISTIC_FIELDS


def test_the_differ_ignores_timings_but_catches_a_changed_counter():
    first = _run(4)
    second = _run(4)
    second["timing"]["wall_seconds"] = first["timing"]["wall_seconds"] * 17 + 1
    assert harness.deterministic_differences(first, second) == []
    second["deterministic"]["n_literals"] = 999
    problems = harness.deterministic_differences(first, second)
    assert len(problems) == 1 and "n_literals" in problems[0]


def test_a_machine_dependent_row_is_compared_only_on_verdict_and_budget():
    slow = harness.run_step(axis_size.spec_for(6), timeout_seconds=0.01)
    other = json.loads(json.dumps(slow))
    other["timing"]["wall_seconds"] = 99.0
    assert harness.deterministic_differences(slow, other) == []
    other["budget_seconds"] = 300.0
    assert any("budget_seconds" in line
               for line in harness.deterministic_differences(slow, other))


def test_the_timing_checker_catches_an_impossible_ordering():
    record = _run(4)
    record["timing"]["ic3_seconds"] = record["timing"]["wall_seconds"] + 10.0
    assert harness.timing_problems(record) != []


def test_no_absolute_path_or_wall_clock_leaks_into_the_deterministic_half():
    blob = json.dumps(_run(4)["deterministic"])
    assert "C:\\" not in blob and "/home/" not in blob and "/tmp/" not in blob
    assert "engine-rig" not in blob


# ------------------------------------------------------- the transcription gate

def test_the_transcription_gate_passes_on_the_system_ic3_actually_searches():
    spec = axis_size.spec_for(6)
    system = harness.build_system(spec)
    assert harness.transcription_mismatches(
        system, spec.n, spec.initial, spec.goal_states) == []


def test_the_transcription_gate_catches_a_corrupted_transition_relation():
    spec = axis_size.spec_for(4)
    system = harness.build_system(spec)
    corrupt = dict(system.transitions)
    corrupt[(False, True, True, True)] = (("jump(0,0,0)", (True, True, True, True)),)
    broken = dataclasses.replace(system, transitions=corrupt)
    problems = harness.transcription_mismatches(
        broken, spec.n, spec.initial, spec.goal_states)
    assert problems and "transitions from 0111" in problems[0]


def test_a_mismatched_adapter_escalates_instead_of_being_tabulated():
    fake = [{"spec": {"n": 4, "label": "n=4"}, "budget_seconds": 1.0,
             "deterministic": {"verdict": harness.ADAPTER_MISMATCH,
                               "escalate": True, "machine_dependent": False,
                               "n_states": 16, "detail": "not the peg world"}}]
    assert axis_size.boundary_of(fake) is None
    assert axis_size.escalations(fake)


# ------------------------------------------------------------- the axis runner

def test_the_axis_writes_after_every_rung_so_an_interrupt_keeps_its_work(tmp_path):
    seen = []

    def on_step(payload):
        path = os.path.join(str(tmp_path), "axis_size.json")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(payload, fh, indent=2)
        seen.append(len(payload["steps"]))

    payload = axis_size.run(ns=(4, 6), timeout_seconds=FAST_BUDGET,
                            on_step=on_step, command="test")
    assert seen == [1, 2]                     # written twice, not once at the end
    assert payload["complete"] is True
    assert [s["spec"]["n"] for s in payload["steps"]] == [4, 6]
    assert payload["boundary"] is None
    assert payload["escalations"] == []
    assert payload["provenance"]["prompt_id"] == "E8-ic3-bounds"
    with open(os.path.join(str(tmp_path), "axis_size.json"), encoding="utf-8") as fh:
        assert len(json.load(fh)["steps"]) == 2


def test_the_axis_refuses_to_run_off_its_anchor(monkeypatch):
    def wrong_goal(n, max_levels=64):
        return StepSpec(axis="size", label="n=%d" % n, n=n,
                        initial="0" + "1" * (n - 1),
                        goal_states=("1000",), max_levels=max_levels)

    monkeypatch.setattr(axis_size, "spec_for", wrong_goal)
    with pytest.raises(harness.AnchorDrift):
        axis_size.run(ns=(4,), timeout_seconds=FAST_BUDGET)


def test_the_markdown_table_computes_nothing_the_json_lacks():
    payload = axis_size.run(ns=(4,), timeout_seconds=FAST_BUDGET, command="test")
    table = axis_size.markdown(payload)
    assert "| 4 | 16 | invariant | 2 | 4 |" in table
    assert "8/16" in table


def test_the_ladder_reaches_a_size_the_budget_cannot_buy():
    """The declared ladder must actually contain the boundary.

    Not run here -- n=14 is a five-minute rung -- but the constants are pinned so
    a later edit cannot quietly trim the ladder back to the sizes that are
    comfortable and then report "no boundary reached".
    """
    assert axis_size.LADDER == (4, 6, 8, 10, 12, 13, 14)
    assert axis_size.LADDER[0] == axis_size.ANCHOR_N
    assert axis_size.DEFAULT_TIMEOUT_SECONDS == 300.0
    assert 2 ** axis_size.LADDER[-1] == 16384
