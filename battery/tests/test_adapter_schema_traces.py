"""The upstream Schema adapter, on a synthetic corpus.

The real payload is gitignored — third-party data with no declared licence —
so a test that read it would pass here and fail on a reader's machine, and
would also be the one place a per-step record could leak into the tree. These
fixtures are hand-built and assert the four refusals the adapter is really
about: no invented turn axis, no synthesised cost, no `failed` derived from
`dead`, and no `Theory` assembled from source code.
"""

import json
import os

import pytest

from battery.adapters.schema_traces import (
    ARM, SCHEMA_ROOT_ENV, load_calls, load_schema_runs, load_steps,
    resolve_root,
)
from battery.guard import load_piles

DEV_GAME = "ar25-0c556536"
SEALED_GAME = "bp35-0a0ad940"


def write_jsonl(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def action(seq, step_index, act, grid, **kw):
    row = {"kind": "action_taken", "seq": seq, "turn": step_index,
           "step_index": step_index, "action": act, "x": None, "y": None,
           "grid": grid, "level": 0, "level_up": False, "win": False,
           "dead": False, "state": "NOT_FINISHED"}
    row.update(kw)
    return row


def make_corpus(root, collection="claude_fable_opus", name="m_max_ar25_100.0",
                game_id=DEV_GAME, events=None, session=None):
    run_dir = os.path.join(root, collection, name)
    os.makedirs(run_dir, exist_ok=True)
    with open(os.path.join(run_dir, "run.json"), "w", encoding="utf-8") as fh:
        json.dump({"game_id": game_id, "provider": "p", "model": "m",
                   "max_actions": 100, "win_levels": 3, "started_at": 0}, fh)
    write_jsonl(os.path.join(run_dir, "events.jsonl"), events if events
                is not None else [action(5, 0, 1, [[1]]),
                                  action(9, 1, 2, [[2]])])
    if session is not None:
        write_jsonl(os.path.join(run_dir, "sessions", "session-001.jsonl"),
                    session)
    return run_dir


# ------------------------------------------------------------------- steps

def test_seq_orders_but_step_index_indexes():
    """`seq` is not contiguous and does not start at zero upstream, so using
    it as an index would silently renumber every step."""
    rows = [action(90, 1, 2, [[2]]), action(11, 0, 1, [[1]])]
    steps, _ = load_steps_from(rows)
    assert [s.idx for s in steps] == [0, 1]
    assert steps[0].state_key != steps[1].state_key


def load_steps_from(rows, tmp=None):
    import tempfile
    tmp = tmp or tempfile.mkdtemp()
    path = os.path.join(tmp, "events.jsonl")
    write_jsonl(path, rows)
    return load_steps(path)


def test_coordinates_are_part_of_action_identity():
    """Clicking two cells is two actions; collapsing them would make a click
    grid look like one repeated action."""
    rows = [action(1, 0, 6, [[1]], x=3, y=4),
            action(2, 1, 6, [[2]], x=9, y=9),
            action(3, 2, 6, [[3]], x=3, y=4)]
    steps, _ = load_steps_from(rows)
    assert steps[0].action == steps[2].action
    assert steps[0].action != steps[1].action


def test_dead_is_not_a_failed_step():
    """`dead` means the arm lost; `failed` means the environment refused the
    action. Conflating them would hand this arm bare_cc's API failure rate."""
    rows = [action(1, 0, 1, [[1]], dead=True, state="GAME_OVER")]
    steps, _ = load_steps_from(rows)
    assert steps[0].failed is False


def test_truncated_ticks_report_unknown_rather_than_a_floor():
    rows = [action(1, 0, 1, [[1]], ticks=[{"g": []}, {"g": []}]),
            action(2, 1, 1, [[2]], ticks=[{"g": []}], ticks_truncated=True),
            action(3, 2, 1, [[3]])]
    steps, meta = load_steps_from(rows)
    assert steps[0].n_frames == 2
    assert steps[1].n_frames is None      # a floor is not a count
    assert steps[2].n_frames is None
    assert meta["truncated_ticks"] == 1


def test_mispredictions_are_counted_but_never_become_a_repair():
    """The only recorded refutation in this corpus, and it carries no located
    clause, probe, revision or re-proof. A Repair built from it would report a
    loop upstream never ran."""
    rows = [action(1, 0, 1, [[1]]),
            {"kind": "model_mispredicted", "seq": 2, "turn": 0,
             "step_index": 0, "predicted": [[1]], "actual": [[2]],
             "surprise": "s"}]
    steps, meta = load_steps_from(rows)
    assert meta["mispredictions"] == 1
    assert len(steps) == 1


# ------------------------------------------------------------------- calls

def assistant(request_id, tokens, **kw):
    row = {"type": "assistant", "sessionId": "s", "requestId": request_id,
           "message": {"id": "m", "role": "assistant", "model": "m",
                       "usage": {"input_tokens": tokens,
                                 "output_tokens": 1,
                                 "cache_read_input_tokens": 2,
                                 "cache_creation_input_tokens": 3}}}
    row.update(kw)
    return row


def test_calls_group_by_request_not_by_record(tmp_path):
    """One API request emits several assistant records in every real run dir.
    Counting records would over-count invocations and add the same usage in
    more than once."""
    path = str(tmp_path / "session-001.jsonl")
    write_jsonl(path, [assistant("req-1", 10), assistant("req-1", 10),
                       assistant("req-2", 20)])
    calls, meta = load_calls(path)
    assert len(calls) == 2
    assert meta["assistant_records"] == 3
    assert [c.input_tokens for c in calls] == [10, 20]
    assert [c.turn for c in calls] == [0, 1]


def test_a_record_without_a_request_id_is_its_own_group(tmp_path):
    path = str(tmp_path / "session-001.jsonl")
    write_jsonl(path, [assistant(None, 1), assistant(None, 2)])
    calls, _ = load_calls(path)
    assert len(calls) == 2


def test_no_cost_and_no_step_index_are_invented(tmp_path):
    """The two numbers this corpus cannot support. A guessed step index would
    carry the same type as a fact."""
    path = str(tmp_path / "session-001.jsonl")
    write_jsonl(path, [assistant("req-1", 10)])
    calls, _ = load_calls(path)
    assert calls[0].cost_usd is None
    assert calls[0].step_idx is None


def test_api_errors_are_flagged(tmp_path):
    path = str(tmp_path / "session-001.jsonl")
    write_jsonl(path, [assistant("req-1", 1, isApiErrorMessage=True)])
    calls, meta = load_calls(path)
    assert calls[0].is_error is True
    assert meta["api_errors"] == 1


# -------------------------------------------------------------------- runs

def test_the_score_in_a_directory_name_never_reaches_the_run_id(tmp_path):
    """The claude run dirs encode an upstream score in their names. A run id
    travels into every artefact; a score has no business riding along."""
    make_corpus(str(tmp_path), name="claude-fable-5_max_sk48_100.0")
    runs = load_schema_runs(str(tmp_path), piles=load_piles())
    assert len(runs) == 1
    assert runs[0].run_id == "claude_fable_opus/claude-fable-5_max_sk48"
    assert "100.0" not in runs[0].run_id


def test_a_collection_without_token_fields_gets_no_calls(tmp_path):
    """Zero tokens would be a fabrication, and a zero-token Call would make
    the economy family compute a number over material that has none."""
    make_corpus(str(tmp_path), collection="gpt_5_6_sol",
                name="gpt_5_6_sol_max_ar25",
                session=[assistant("req-1", 10)])
    runs = load_schema_runs(str(tmp_path), piles=load_piles())
    assert runs[0].calls == []
    assert runs[0].capabilities()["model_calls"] is False
    assert any("token usage" in reason
               for reason in runs[0].notes["absent_by_construction"])


def test_the_arm_has_no_theory_and_says_why(tmp_path):
    make_corpus(str(tmp_path))
    run = load_schema_runs(str(tmp_path), piles=load_piles())[0]
    assert run.theory is None
    assert run.arm == ARM
    assert any("theory" in reason
               for reason in run.notes["absent_by_construction"])


def test_the_guardrail_refuses_a_sealed_game(tmp_path):
    make_corpus(str(tmp_path), game_id=SEALED_GAME)
    from battery.guard import SealedPileError
    with pytest.raises(SealedPileError):
        load_schema_runs(str(tmp_path), piles=load_piles())


def test_an_absent_payload_is_not_an_error(tmp_path):
    """A fresh clone and every git worktree look like this. The battery
    recomputes without a Schema arm and says which arms were present."""
    assert load_schema_runs(str(tmp_path / "nope"), piles=load_piles()) == []


def test_the_root_resolves_through_the_environment(monkeypatch):
    monkeypatch.setenv(SCHEMA_ROOT_ENV, "/somewhere/else")
    assert resolve_root() == "/somewhere/else"
    assert resolve_root("/explicit") == "/explicit"


def test_loading_is_deterministic(tmp_path):
    make_corpus(str(tmp_path), name="a_max_ar25_100.0")
    make_corpus(str(tmp_path), name="b_max_ar25_94.7")
    first = load_schema_runs(str(tmp_path), piles=load_piles())
    second = load_schema_runs(str(tmp_path), piles=load_piles())
    assert [r.run_id for r in first] == [r.run_id for r in second]
    assert [r.run_id for r in first] == sorted(r.run_id for r in first)
