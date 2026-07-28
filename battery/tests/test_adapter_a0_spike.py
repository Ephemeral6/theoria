"""The a0-spike adapter, and the refusals that are the point of it.

Most of what this adapter does is decline to produce a number: no trace, no
model calls, no probes, no per-concept compression account, no revision
marker.  The tests below check the declines as hard as the values, because an
adapter that quietly invented any of them would still pass a test suite that
only looked at what it emitted.
"""

import pytest

from battery.adapters.a0_spike import load_a0_spike_runs
from battery.metrics import evaluate


@pytest.fixture(scope="module")
def run():
    runs = load_a0_spike_runs()
    assert len(runs) == 1, "a0-spike is one arm building one manual"
    return runs[0]


@pytest.fixture(scope="module")
def values(run):
    return evaluate(run)


@pytest.fixture(scope="module")
def repairs(run):
    return {r.episode_id: r for r in run.repairs}


# ------------------------------------------------------------------ identity

def test_the_run_is_a_pileless_self_built_world(run):
    assert run.run_id == "a0-spike"
    assert run.arm == "theoria_a0_spike"
    assert run.source == "a0-spike"
    assert run.game_id is None and run.pile == "synthetic"
    assert run.intent == "explore"
    assert run.model is None


def test_no_trace_and_no_model_calls_are_carried_as_absences(run):
    """The two big holes, asserted rather than assumed.

    a0-spike persists no frames — its trace is regenerable in-memory data in
    `pipeline/explore.py`, which the battery does not execute — and it ran no
    LLM at all.
    """
    assert run.steps == []
    assert run.calls == []
    caps = run.capabilities()
    assert caps["steps"] is False
    assert caps["observations"] is False
    assert caps["model_calls"] is False
    assert caps["theory"] is True and caps["repairs"] is True
    assert "regenerable in-memory" in run.notes["trace_persistence"]


def test_the_missing_trace_is_reported_not_scored(values):
    """Exploration and P1/P2/P3 have no input, so they must refuse."""
    for mid, value in sorted(values.items()):
        if mid.startswith("X") or mid in ("P1", "P2", "P3"):
            assert value.status == "not-applicable", mid
            assert value.value is None, mid
            assert value.reason, mid


def test_the_economy_family_refuses_a_run_with_no_model(values):
    for mid, value in sorted(values.items()):
        if mid.startswith("E"):
            assert value.status == "not-applicable", mid
            assert value.value is None, mid


def test_an_exploration_sweep_is_not_scored_for_path_efficiency(run, values):
    """1966 coverage actions against a 2-step optimal plan is 983x.

    The ratio would be the trace's purpose, not the arm's planning, so P4 has
    to decline it even though the optimal length is known.
    """
    assert run.truth.optimal_steps == 2
    assert run.capabilities()["optimal"] is True
    assert run.capabilities()["solve_attempt"] is False
    assert values["P4"].status == "not-applicable"


def test_the_mechanism_family_refuses_an_unannotated_world(run, values):
    assert run.truth.mechanisms == {}
    for mid in ("M1", "M2", "M3"):
        assert values[mid].status == "not-applicable", mid


# -------------------------------------------------------------------- theory

def test_the_manual_is_read_whole(run):
    clauses = run.theory.clauses
    assert len(clauses) == 9
    kinds = sorted(c.kind for c in clauses)
    assert kinds.count("rule") == 5
    assert kinds.count("invariant") == 3
    assert kinds.count("theorem") == 1
    # every rule carries a full-coverage annotation
    rules = [c for c in clauses if c.kind == "rule"]
    assert all(c.coverage_num == c.coverage_den is not None for c in rules)
    assert run.theory.deadlock_theorems == 1


def test_replay_and_held_out_come_from_the_report(run):
    t = run.theory
    assert t.replay_pairs == 1966 and t.replay_agree == 1966
    assert t.held_out_pairs == 39960 and t.held_out_agree == 39960


def test_the_held_out_frame_is_stated_so_the_two_arms_are_not_compared(run):
    """39960 exhaustive cases and A0's 3 uncovered pairs are not one number."""
    frame = run.theory.held_out_frame
    assert frame and frame.strip()
    assert "exhaustive" in frame
    assert "39960" in frame


def test_concepts_exist_but_carry_no_compression_account(run, values):
    """The trap: one global number annotated twice, with the sign inverted.

    `compress: -39` is 373-412, the whole-script delta, written on both
    word-table entries and stale against `perceive`'s 602/712.  Passing it
    through would give K6 a mean over one measurement and make K7 count two
    fabricated negative-gain concepts.
    """
    concepts = run.theory.concepts
    assert [c.name for c in concepts] == ["Box", "Player"]
    assert all(c.compression_bits is None for c in concepts)
    assert values["K5"].value == 2          # the concepts are counted
    assert values["K6"].status == "insufficient-data"
    assert values["K7"].status == "insufficient-data"
    assert "373-412" in run.notes["compression_accounts"]


def test_no_probe_count_is_invented_from_an_annotation_string(run, values):
    """The theorem says `probe: passed`; that is not a probe record."""
    assert run.theory.probes_designed == 0
    assert run.theory.probes_executable == 0
    assert values["K8"].status == "insufficient-data"


def test_there_is_no_playbook(run, values):
    assert run.theory.playbook_entries == 0
    assert values["K9"].status == "insufficient-data"


def test_an_unmarked_manual_does_not_borrow_the_parsers_default(run):
    """`parse_dsl` defaults to revision 1; a0-spike's manual has no marker.

    Reporting 1 would be indistinguishable from the marker cold-start-a0's
    no-button manual genuinely writes, so this arm reports 0 and explains it.
    """
    assert run.theory.revisions == 0
    note = run.notes["revisions"]
    assert "no revision marker" in note
    assert "T-8" in note and "T-9" in note


# ------------------------------------------------------------------- repairs

def test_all_four_injected_variants_become_repairs(repairs):
    assert sorted(repairs) == ["ghost", "nocross", "push1", "push3"]
    assert all(r.strategy == "rebuild" for r in repairs.values())
    assert all(r.baseline_actions == 1966 for r in repairs.values())


def test_repair_costs_are_read_per_variant(repairs):
    assert repairs["push1"].repair_actions == 3661
    assert repairs["push3"].repair_actions == 1478
    assert repairs["nocross"].repair_actions == 1753
    assert repairs["ghost"].repair_actions == 1721


def test_detection_latency_where_the_change_was_noticed(repairs):
    for name, expected in (("push1", 18), ("push3", 18), ("ghost", 6)):
        r = repairs[name]
        assert r.detected is True, name
        assert r.detection_actions == expected, name
        assert r.actions_examined is None, name


def test_the_undetected_variant_takes_the_other_arm_of_the_union(repairs):
    """`nocross` has no `actions_until_surprise` field at all.

    A manual that replayed 341 actions exactly while being silently wrong is
    the interesting case, and reading the detected-shape key unconditionally
    would raise `KeyError` on it.
    """
    r = repairs["nocross"]
    assert r.detected is False
    assert r.detection_actions is None
    assert r.actions_examined == 341


def test_a_null_per_level_entry_does_not_become_a_number(repairs):
    """`per_level.match` is `null` for nocross; min()/sum() would blow up."""
    r = repairs["nocross"]
    assert r.notes["per_level_detection"]["match"] is None
    assert r.notes["levels_that_never_notice"] == ["match"]
    assert r.notes["earliest_detection"] == 6
    assert repairs["push1"].notes["levels_that_never_notice"] == []


def test_earliest_detection_across_levels(repairs):
    earliest = {k: v.notes["earliest_detection"] for k, v in repairs.items()}
    assert earliest == {"push1": 18, "push3": 18, "nocross": 6, "ghost": 6}


def test_dependency_tracking_is_credited_to_exactly_one_variant(repairs):
    """`push1` destroys the conservation law the theorem stands on."""
    assert repairs["push1"].silently_wrong_without_tracking is True
    assert repairs["push1"].notes["conservation_law_still_true"] is False
    for name in ("push3", "nocross", "ghost"):
        assert repairs[name].silently_wrong_without_tracking is False, name


def test_collateral_damage_is_counted_against_a_ceiling_of_one(repairs):
    assert all(r.theorems_before == 1 for r in repairs.values())
    assert repairs["push1"].invalidated_theorems == 1
    assert repairs["push3"].invalidated_theorems == 1
    assert repairs["nocross"].invalidated_theorems == 1
    # `ghost` changes `walk`, which the theorem does not depend on.
    assert repairs["ghost"].invalidated_theorems == 0
    assert repairs["ghost"].changed_clause == "walk"
    assert "0.0 or 1.0" in repairs["ghost"].notes["collateral_ceiling"]


def test_no_beats_are_fabricated_to_close_the_loop(repairs):
    """a0-spike detects and re-mines; it does not run the six-beat loop."""
    for name, r in sorted(repairs.items()):
        assert r.beats == [], name
        assert r.beats_closed == 0, name
        assert r.beats_required == 6, name
        assert r.env_actions == 0, name
        assert "0 of 6" in r.notes["beats"], name


# ---------------------------------------------------------------- provenance

def test_loading_twice_is_identical(run):
    a = load_a0_spike_runs()[0]
    b = load_a0_spike_runs()[0]
    assert a == b
    assert [r.episode_id for r in a.repairs] == [r.episode_id for r in b.repairs]
    assert a.notes == b.notes == run.notes


def test_a_missing_bundle_yields_no_runs_rather_than_an_error(tmp_path):
    assert load_a0_spike_runs(str(tmp_path)) == []
