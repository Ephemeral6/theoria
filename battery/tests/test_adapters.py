"""Adapters, including the guardrail firing at the point of entry."""

import pytest

from battery.adapters.a0 import load_a0_runs, parse_dsl, parse_playbook
from battery.adapters.ledger_jsonl import _canonical_action, parse_rows
from battery.guard import SealedPileError, load_piles


@pytest.fixture(scope="module")
def piles():
    return load_piles()


def _env(game_id, run_id="r", **kw):
    row = {"run_id": run_id, "game_id": game_id, "arm": "bare_cc",
           "model": "m", "step_idx": 0, "action": "RESET",
           "frame": [[[1, 2], [3, 4]]]}
    row.update(kw)
    return row


def test_a_sealed_game_is_refused_before_a_frame_is_read(piles):
    with pytest.raises(SealedPileError):
        parse_rows([_env("bp35-0a0ad940")], source="t", piles=piles)
    with pytest.raises(SealedPileError):
        parse_rows([_env("bp35")], source="t", piles=piles)


def test_dev_games_load(piles):
    runs = parse_rows([_env("ar25-0c556536")], source="t", piles=piles)
    assert len(runs) == 1
    assert runs[0].pile == "dev"
    assert runs[0].intent == "solve"


def test_actions_keep_their_coordinates(piles):
    """Clicking two different cells is two different actions."""
    assert _canonical_action("RESET") == "RESET"
    assert _canonical_action({"id": 6, "data": None}) == "ACTION6"
    a = _canonical_action({"id": 6, "data": {"x": 1, "y": 2}})
    b = _canonical_action({"id": 6, "data": {"x": 9, "y": 2}})
    assert a != b


def test_state_identity_comes_from_the_last_frame_of_a_cascade(piles):
    """One action can return several frames; the arm sees the last one."""
    same_end = [_env("ar25-0c556536", run_id="a", step_idx=0,
                     frame=[[[1]], [[9]]]),
                _env("ar25-0c556536", run_id="a", step_idx=1,
                     frame=[[[5]], [[9]]])]
    run = parse_rows(same_end, source="t", piles=piles)[0]
    assert run.steps[0].state_key == run.steps[1].state_key
    assert run.steps[0].n_frames == 2


def test_failed_steps_survive_with_no_observation(piles):
    rows = [_env("ar25-0c556536", step_idx=0),
            _env("ar25-0c556536", step_idx=1, frame=None, failed=True)]
    run = parse_rows(rows, source="t", piles=piles)[0]
    assert len(run.steps) == 2
    assert run.steps[1].failed and run.steps[1].state_key is None
    assert len(run.ok_steps) == 1


def test_model_calls_group_by_run_id(piles):
    rows = [_env("ar25-0c556536", run_id="a"),
            {"run_id": "a", "model": "m", "provider": "p",
             "total_cost_usd": 0.5,
             "usage": {"input_tokens": 10, "output_tokens": 20,
                       "cache_read_input_tokens": 5}}]
    run = parse_rows(rows, source="t", piles=piles)[0]
    assert len(run.calls) == 1
    assert run.calls[0].context_tokens == 15
    assert run.calls[0].cost_usd == 0.5


# ------------------------------------------------------------------------ A0

def test_a0_loads_both_instances():
    runs = {r.run_id: r for r in load_a0_runs()}
    assert set(runs) == {"a0-base", "a0-no-button"}
    base = runs["a0-base"]
    assert base.game_id is None and base.pile == "synthetic"
    assert base.intent == "explore"
    assert base.calls == []          # A0 ran no model in the loop


def test_a0_state_count_matches_the_worlds_own_record():
    """An independent check that the state digest is right.

    `trace_summary.json` records 59 reachable states, computed by the A0
    pipeline. The battery never reads that field for X5 — it digests frames.
    The two agreeing means the digest is identifying states correctly.
    """
    base = {r.run_id: r for r in load_a0_runs()}["a0-base"]
    distinct = len({s.state_key for s in base.steps})
    assert distinct == base.notes["reachable_states"] == 59


def test_a0_step_lands_on_the_state_its_action_produced():
    """Row t holds the state *before* its action, so step i takes frame i+1."""
    base = {r.run_id: r for r in load_a0_runs()}["a0-base"]
    assert len(base.steps) == 275       # 276 frames, 275 transitions
    assert base.steps[-1].action != "None"


def test_dsl_reader_separates_unannotated_from_unsupported(tmp_path):
    path = tmp_path / "t.dsl"
    path.write_text(
        "# manual revision 7\n"
        "rules:\n"
        "  rule push_up [ev: t6,t16,t21 cov: 52/52]\n"
        "laws:\n"
        "  invariant cart_unique count(Cart) = 1 [status: proven]\n"
        "  theorem maybe \"...\" [depends: push_up probe: pending]\n",
        encoding="utf-8")
    clauses, revision = parse_dsl(str(path))
    assert revision == 7
    by_name = {c.name: c for c in clauses}
    assert by_name["push_up"].evidence_transitions == 3
    assert by_name["push_up"].coverage_num == 52
    assert by_name["cart_unique"].evidence_transitions is None   # not zero
    assert by_name["cart_unique"].proven is True
    assert by_name["maybe"].probe_pending is True


def test_dsl_reader_survives_a_grammar_it_does_not_know(tmp_path):
    """If the DSL moves, degrade to zero counts rather than crash."""
    path = tmp_path / "t.dsl"
    path.write_text("(((not a dsl at all)))\n", encoding="utf-8")
    clauses, revision = parse_dsl(str(path))
    assert clauses == [] and revision == 1
    assert parse_dsl(str(tmp_path / "missing.dsl")) == ([], 0)


def test_playbook_counts_deadlocks_as_a_subset_of_entries(tmp_path):
    path = tmp_path / "p.dsl"
    path.write_text(
        "# comment\n"
        "order press_before_door [proof: lean]\n"
        "prune w_room(Cart) > 0 and no_button => dead [proof: lean]\n"
        "heuristic w_room(Cart) [admissible: none]\n",
        encoding="utf-8")
    entries, deadlocks = parse_playbook(str(path))
    assert entries == 3 and deadlocks == 1


def test_a0_mechanism_delay_is_measured_from_the_unlock(tmp_path):
    """The door is not a passage until the button opens it."""
    base = {r.run_id: r for r in load_a0_runs()}["a0-base"]
    mechanisms = base.truth.mechanisms
    assert mechanisms["button"]["first_used"] == 99
    # first_seen for the door is the button press, not frame 0
    assert mechanisms["door_passage"]["first_seen"] == 99
    assert mechanisms["door_passage"]["first_used"] == 157
