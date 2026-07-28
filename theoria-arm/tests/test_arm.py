"""Offline tests. No key, no network, no model call, no quota.

Everything here runs against `proxy/mock` or against hand-built frames. The
point is that every property the live run depends on is checked *before* an
action is spent, because a live action cannot be taken back.
"""

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from harness import arc, budget as budget_mod, modelcall    # noqa: E402
from inner import certify, commit, plan as plan_beat, probe as probe_beat  # noqa: E402
from inner import surprise, theorize                        # noqa: E402
from inner.books import Books, problem_from_frames          # noqa: E402
from inner.grammar_card import WORKED_EXAMPLE               # noqa: E402
from world import adapt                                     # noqa: E402
from world.frames import FrameStore, Step, describe_diff    # noqa: E402


# ------------------------------------------------------------------ sealing
def test_the_arm_refuses_a_short_game_id():
    """INC-005: a short-id 200 carries the pristine initial frame whatever the
    session has done. A counterfeit 200 is worse than a 400."""
    with pytest.raises(arc.ShortIdRefused):
        arc.ArcThroughProxy("http://127.0.0.1:1", "g50t", budget_mod.Budget())
    arc.ArcThroughProxy("http://127.0.0.1:1", "g50t-5849a774", budget_mod.Budget())


def test_the_400_wave_is_retryable_and_a_deterministic_500_is_not():
    assert arc._retryable(400, {"message": "game g50t-5849a774 not found"})
    assert arc._retryable(429, {})
    assert arc._retryable(-1, {})
    # tn36's ACTION6 answered 500 on all 88 attempts. Retrying a certainty
    # burns the envelope and the wall clock for nothing.
    assert not arc._retryable(500, {"message": "SERVER_ERROR"})
    assert not arc._retryable(400, {"message": "game_id not provided"})
    assert not arc._retryable(200, {})


def test_the_arm_has_no_path_to_the_game_credential():
    """Sealing, checked at the source rather than asserted in prose: the arm's
    environment client must have no way to read a key and no way to send one."""
    source = open(os.path.join(ARM, "harness", "arc.py"), encoding="utf-8").read()
    code = "\n".join(line for line in source.splitlines()
                     if not line.strip().startswith(("#", '"', "*")))
    for forbidden in ("os.environ", "read_secret", "getenv", "load_api_key",
                      "X-API-Key", "x-api-key", "Authorization"):
        assert forbidden not in code, forbidden
    # And it never builds a request to anything but its own proxy base.
    assert "self.env_base +" in code
    assert "three.arcprize.org" not in source


def test_the_desk_env_drops_the_game_credential():
    source = open(os.path.join(ARM, "harness", "modelcall.py"),
                  encoding="utf-8").read()
    assert 'env.pop("ARC_API_KEY", None)' in source


# ------------------------------------------------------------------- budget
def test_the_action_ceiling_is_hard_and_counts_successes():
    b = budget_mod.Budget(actions=3)
    for _ in range(3):
        b.check()
        b.command()
        b.succeeded()
    with pytest.raises(budget_mod.BudgetExhausted):
        b.check()


def test_a_reset_is_not_billed_as_an_action():
    b = budget_mod.Budget(actions=1)
    b.check(is_reset=True); b.command(); b.succeeded(is_reset=True)
    b.check()                                          # still allowed
    assert b.actions_ok == 0 and b.resets == 1


def test_a_spent_budget_can_still_open_a_session():
    """A run with no actions left must still be able to RESET -- otherwise a
    pre-flight that spends nothing cannot connect, and a resumed run cannot
    re-enter the game it already paid for."""
    b = budget_mod.Budget(actions=0)
    b.check(is_reset=True)                             # allowed
    with pytest.raises(budget_mod.BudgetExhausted):
        b.check()                                      # an action is not


def test_the_probe_reserve_is_only_reachable_by_a_probe():
    b = budget_mod.Budget(actions=5, reserve_for_probes=2)
    for _ in range(3):
        b.check(); b.command(); b.succeeded()
    with pytest.raises(budget_mod.BudgetExhausted):
        b.check()                                      # ordinary play is done
    b.check(probe=True)                                # the reserve is not


def test_a_budget_resumes_across_stages():
    b = budget_mod.Budget(actions=120)
    for _ in range(7):
        b.command(); b.succeeded()
    again = budget_mod.resume(b.as_json(), actions=120)
    assert again.actions_ok == 7 and again.actions_left == 113


# ------------------------------------------------------------- constraint 8
def test_certify_and_commit_may_not_spend_a_model_call():
    desk = modelcall.ModelDesk(run=None)
    for beat in ("certify", "commit", "plan", "observe"):
        with pytest.raises(modelcall.ModelError):
            desk.call("x", beat=beat)


def test_the_seven_surprises_are_seven_and_split_five_two():
    assert len(surprise.KINDS) == 7
    assert len(surprise.EMPIRICAL) == 5
    assert len(surprise.COMPUTATIONAL) == 2
    with pytest.raises(ValueError):
        surprise.Surprise("eighth_kind", "no")


def test_every_surprise_names_the_book_it_changes():
    register = surprise.Register()
    assert register.fire("replay_mismatch", "x").book == "theory.dsl"
    assert register.fire("search_timeout", "x").book == "playbook.dsl"


def test_the_audit_catches_a_call_at_a_forbidden_beat():
    register = surprise.Register()
    register.fire("replay_mismatch", "x")
    clean = [{"event": "model_call", "run_id": "r", "beat": "theorize"}]
    dirty = clean + [{"event": "model_call", "run_id": "r", "beat": "commit"}]
    assert register.audit(clean, "r")["constraint_8_holds"]
    assert not register.audit(dirty, "r")["constraint_8_holds"]


def test_a_model_call_with_no_surprise_at_all_is_a_violation():
    register = surprise.Register()
    calls = [{"event": "model_call", "run_id": "r", "beat": "theorize"}]
    assert not register.audit(calls, "r")["constraint_8_holds"]


# -------------------------------------------------------------------- world
def _store(grids, actions):
    store = FrameStore()
    store.add(Step(0, "RESET", [grids[0]]))
    for i, (g, a) in enumerate(zip(grids[1:], actions), start=1):
        store.add(Step(i, a, [g]))
    return store


def test_the_cascade_is_never_collapsed_at_intake():
    store = FrameStore()
    store.add(Step(0, "RESET", [[[0]]]))
    store.add(Step(1, "ACTION2", [[[1]], [[2]], [[3]]]))
    assert store.steps[1].n_frames == 3
    assert store.steps[1].grid == [[3]]                # the state after
    assert store.summary()["max_frames_in_one_command"] == 3


def test_board_and_dynamic_cells_partition_the_frame():
    grids = [[[0, 0], [0, 6]], [[0, 6], [0, 0]]]
    store = _store(grids, ["ACTION1"])
    assert set(store.constant_cells()) | set(store.dynamic_cells()) == {
        (0, 0), (0, 1), (1, 0), (1, 1)}
    assert not set(store.constant_cells()) & set(store.dynamic_cells())
    assert sorted(store.dynamic_cells()) == [(0, 1), (1, 1)]


def test_the_action_list_ends_in_none_as_the_miner_requires():
    grids = [[[0]], [[1]], [[2]]]
    store = _store(grids, ["ACTION1", "ACTION2"])
    assert store.actions == ["ACTION1", "ACTION2", None]


def test_the_arena_crop_is_only_taken_on_a_big_frame_and_is_declared():
    small = _store([[[0, 0], [0, 6]], [[0, 6], [0, 0]]], ["ACTION1"])
    assert adapt.choose_window(small)["full_frame"] is True

    big_a = [[0] * 64 for _ in range(64)]
    big_b = [row[:] for row in big_a]
    big_b[10][10] = 6
    window = adapt.choose_window(_store([big_a, big_b], ["ACTION1"]))
    assert window["full_frame"] is False
    assert window["covered"] == 1.0                    # no dynamic cell dropped
    assert "4096" in window["reason"]


def test_thin_evidence_for_a_conservation_law_is_labelled_thin():
    """6 states over hundreds of features leaves a null space in which nearly
    every vector is a 'law'. The engine is right and the evidence is not, and
    the report has to say which."""
    grids = [[[0] * 20 for _ in range(20)] for _ in range(3)]
    for t, g in enumerate(grids):
        g[t][t] = 3                                    # a little motion, few states
    report = adapt.laws(_store(grids, ["ACTION1", "ACTION2"]))
    adequacy = report["evidence_adequacy"]
    assert adequacy["transitions"] == 2
    assert adequacy["verdict"].startswith("THIN")
    assert "unfalsified rather than confirmed" in adequacy["verdict"]


def test_the_law_cell_cap_narrows_loudly_or_not_at_all():
    grids = [[[0] * 64 for _ in range(64)]]
    grids.append([row[:] for row in grids[0]])
    for i in range(300):
        grids[1][i // 64][i % 64] = 3
    report = adapt.laws(_store(grids, ["ACTION1"]), cap=240)
    assert report["cells_dynamic"] == 300
    assert report["cells_used"] == 240
    assert report["narrowed"] is True


# ----------------------------------------------------------------- the books
def test_the_grammar_card_example_actually_compiles(tmp_path):
    """The card is handed to the desk as a constraint statement. If it stops
    being true the desk is being lied to."""
    books = Books(str(tmp_path))
    books.write(theory=WORKED_EXAMPLE, playbook="# none\n")
    books.write_problem({"name": "l", "grid": [5, 5], "background": 0,
                         "board": [[0] * 5 for _ in range(5)],
                         "objects": [{"name": "Cart", "type": "Cart",
                                      "pos": [2, 2], "color": 6}]})
    result = books.compile_all()
    assert result["ok"], result["errors"]
    namespace, error = books.load_predictor()
    assert namespace is not None, error
    assert namespace["ACTIONS"] == [("key", 1)]
    assert namespace["GEOMETRY"] == "grid"


def test_the_problem_instance_is_computed_not_written(tmp_path):
    grids = [[[0, 0], [0, 6]], [[0, 6], [0, 0]]]
    store = _store(grids, ["ACTION1"])
    problem = problem_from_frames(store, [{"name": "Cart", "type": "Cart",
                                           "color": 6}])
    assert problem["objects"][0]["pos"] == [1, 1]      # read off the frame
    assert problem["grid"] == [2, 2]
    # A cell that has ever changed cannot be board (constraint 2).
    assert problem["board"][0][1] == problem["background"]


def test_an_object_the_frame_cannot_locate_is_recorded_not_crashed(tmp_path):
    store = _store([[[0, 0], [0, 6]], [[0, 6], [0, 0]]], ["ACTION1"])
    problem = problem_from_frames(store, [{"name": "Ghost", "type": "Ghost",
                                           "color": 9}])
    assert problem["unlocated"] == ["Ghost"]
    assert problem["objects"][0]["present"] is False
    assert problem["objects"][0]["pos"] == [0, 0]


def test_snapshots_keep_every_revision(tmp_path):
    books = Books(str(tmp_path))
    books.write(theory="a\n", playbook="b\n")
    first = books.snapshot("before")
    books.write(theory="c\n")
    second = books.snapshot("after")
    assert first["revision"] == 1 and second["revision"] == 2
    assert open(os.path.join(first["dir"], "theory.dsl")).read() == "a\n"
    assert open(os.path.join(second["dir"], "theory.dsl")).read() == "c\n"


# ---------------------------------------------------------------- the beats
def _compiled_books(tmp_path, theory=WORKED_EXAMPLE):
    books = Books(str(tmp_path))
    books.write(theory=theory, playbook="# none\n")
    books.write_problem({"name": "l", "grid": [3, 3], "background": 0,
                         "board": [[0] * 3 for _ in range(3)],
                         "objects": [{"name": "Cart", "type": "Cart",
                                      "pos": [2, 1], "color": 6}]})
    return books, books.compile_all()


def test_certify_reports_a_manual_that_cannot_draw_its_own_frame(tmp_path):
    books, compiled = _compiled_books(tmp_path)
    observed = [[0, 0, 0], [0, 0, 0], [0, 6, 0]]
    wrong = [row[:] for row in observed]
    wrong[0][0] = 4                                    # a pixel nobody claims
    store = _store([wrong], [])
    report = certify.cheap(books, store, commit.action_to_manual)
    responsibility = report["checks"]["responsibility"]
    assert responsibility["ok"] is False
    assert responsibility["cells_unexplained"] == 1


def test_certify_turns_a_raising_predictor_into_a_finding_not_a_traceback(tmp_path):
    books = Books(str(tmp_path))
    books.write(theory=WORKED_EXAMPLE)
    books.write_problem({"name": "l", "grid": [3, 3], "background": 0,
                         "board": [[0] * 3 for _ in range(3)],
                         "objects": [{"name": "Cart", "type": "Cart",
                                      "color": 6}]})     # no pos at all
    books.compile_all()
    store = _store([[[0, 0, 0], [0, 0, 0], [0, 6, 0]]], [])
    report = certify.cheap(books, store, commit.action_to_manual)
    assert report["ok"] is False
    assert "raised" in report["checks"]["responsibility"]


def test_certify_failures_become_the_right_surprises(tmp_path):
    register = surprise.Register()
    report = {"cheap": {"checks": {
        "responsibility": {"ok": False, "detail": "d", "cells_unexplained": 3},
        "replay": {"ok": False, "first_divergence": {"t": 2, "kind": "x"}},
        "unambiguous": {"ok": False, "detail": "two rules"},
    }}, "expensive": {"available": False}}
    certify.surprises_from(report, register)
    counts = register.counts()
    assert counts["render_mismatch"] == 1
    assert counts["replay_mismatch"] == 1
    assert counts["proof_failure"] == 1


def test_a_manual_with_no_goal_is_not_an_unsolvability_claim(tmp_path):
    books, compiled = _compiled_books(tmp_path, theory=WORKED_EXAMPLE.replace(
        "goal:\n  goal count(Cart) = 1\n", ""))
    namespace, _ = books.load_predictor()
    report = plan_beat.plan(books, namespace, compiled)
    assert report["status"] == "no_goal_declared"
    assert "not a proof" in report["detail"].lower()


def test_bfs_finds_a_plan_over_the_manuals_own_predictor(tmp_path):
    theory = WORKED_EXAMPLE.replace("goal count(Cart) = 1",
                                    "goal Cart.pos = (0, 1)")
    books, compiled = _compiled_books(tmp_path, theory=theory)
    namespace, error = books.load_predictor()
    assert namespace is not None, error
    report = plan_beat.plan(books, namespace, compiled)
    assert report["status"] == "sat"
    assert report["plan"] == [["key", 1], ["key", 1]]
    assert report["backend"] == "object-state-bfs"


def test_the_planner_gives_up_on_the_clock_not_only_on_the_node_count(tmp_path):
    """`render` rebuilds the whole frame per guard evaluation, so a node cap
    that is harmless on a fixture is hours on a 64x64 level. Running out of
    clock must surface as `search_timeout` -- a computational surprise -- and
    not as a hung run."""
    theory = WORKED_EXAMPLE.replace("goal count(Cart) = 1",
                                    "goal Cart.pos = (0, 0)")
    books, compiled = _compiled_books(tmp_path, theory=theory)
    namespace, error = books.load_predictor()
    assert namespace is not None, error
    report = plan_beat._tier_bfs(namespace, node_cap=10 ** 9, deadline_s=0.0)
    assert report["status"] == "search_timeout"
    assert report["reached"] == "deadline"

    register = surprise.Register()
    plan_beat.surprises_from({"status": "search_timeout", "detail": "d"}, register)
    assert register.counts()["search_timeout"] == 1
    assert register.items[0].family == "computational"
    assert register.items[0].book == "playbook.dsl"


def test_the_action_mapping_round_trips_and_refuses_anything_else():
    assert commit.action_to_manual("ACTION3") == ("key", 3)
    assert commit.action_to_arc(("key", 3)) == 3
    with pytest.raises(ValueError):
        commit.action_to_arc(("click", 3, 4))


def test_a_probe_prediction_is_written_before_the_result(tmp_path):
    log = probe_beat.ProbeLog(str(tmp_path / "probes.jsonl"))
    probe_id = log.record_design(action=2, design_report={},
                                 predictions={"manual": "aaa", "inert": "bbb"},
                                 step_idx=4)
    rows = [json.loads(l) for l in open(log.path, encoding="utf-8")]
    assert rows[0]["phase"] == "design"                # design is on disk first
    result = log.record_result(probe_id, observed="bbb", status=200, n_frames=1)
    assert result["manual_survived"] is False
    assert result["refuted"] == ["manual"]
    rows = [json.loads(l) for l in open(log.path, encoding="utf-8")]
    assert [r["phase"] for r in rows] == ["design", "result"]


def test_an_unrunnable_probe_is_recorded_rather_than_dropped(tmp_path):
    log = probe_beat.ProbeLog(str(tmp_path / "probes.jsonl"))
    log.record_unrunnable(reason="nothing separates", design_report={},
                          step_idx=3)
    rows = [json.loads(l) for l in open(log.path, encoding="utf-8")]
    assert rows[0]["phase"] == "unrunnable"


def test_probe_hypotheses_include_one_ablation_per_rule(tmp_path):
    books, _ = _compiled_books(tmp_path)
    namespace, _ = books.load_predictor()
    ids = {h.id for h in probe_beat.build_hypotheses(namespace)}
    assert {"manual", "inert"} <= ids
    assert any(i.startswith("without_") for i in ids)


# ----------------------------------------------------------------- the reply
def test_the_cost_cross_check_prices_a_real_usage_block():
    """Two independent cost figures per run: the CLI's own `total_cost_usd` and
    `proxy/cost.py` over the recorded usage. A cross-check that can only fail in
    one direction is not a cross-check -- an earlier version of this coerced
    `PriceTable.cost`'s dict return to a float, put every call in the exception
    path, and announced that the table could not price `claude-opus-5`."""
    from armtools.archive import costs                    # noqa: PLC0415
    usage = {"input_tokens": 2, "output_tokens": 43066,
             "cache_read_input_tokens": 24264,
             "cache_creation_input_tokens": 20736,
             "cache_creation": {"ephemeral_1h_input_tokens": 20736,
                                "ephemeral_5m_input_tokens": 0}}
    records = [{"event": "model_call", "model": "claude-opus-5", "usage": usage,
                "response": {"total_cost_usd": 1.307727}}]
    report = costs(records)
    assert report["from_price_table"]["unpriced_models"] is None
    assert report["from_price_table"]["usd_total"] > 1.0
    assert report["cli_reported_usd"] == 1.307727
    assert "verdict" in report


def test_the_cache_ttl_gap_is_diagnosed_rather_than_left_as_a_delta():
    """`pricing_v1.json` carries a 2.0x multiplier for 1-hour cache writes and
    `proxy/cost.py` never applies it, because the TTL is in a nested usage
    object it does not read. The report must name that, not just print a delta."""
    from armtools.archive import _cache_ttl_diagnosis     # noqa: PLC0415
    calls = [{"model": "claude-opus-5",
              "usage": {"cache_creation_input_tokens": 20736,
                        "cache_creation": {"ephemeral_1h_input_tokens": 20736,
                                           "ephemeral_5m_input_tokens": 0}}}]
    report = _cache_ttl_diagnosis(calls, None)
    assert report["cache_creation_1h_tokens"] == 20736
    assert report["under_billed_usd"] > 0
    assert "cache_creation_input_tokens_1h" in report["verdict"]

    none = _cache_ttl_diagnosis([{"model": "claude-opus-5", "usage": {}}], None)
    assert "not a source of disagreement" in none["verdict"]


def test_the_bootstrap_theorize_is_named_not_smuggled(tmp_path):
    """The first theorize answers no surprise because no manual exists yet.
    Exactly one such call is allowed; a second uncovered call is a violation."""
    from armtools.archive import constraint_8             # noqa: PLC0415
    run_dir = str(tmp_path)
    call = {"event": "model_call", "run_id": "r", "beat": "theorize"}
    one = constraint_8([call], run_dir)
    assert one["holds"] and one["bootstrap_calls_allowed"] == 1
    two = constraint_8([call, dict(call)], run_dir)
    assert not two["holds"]
    assert two["calls_not_covered_by_a_surprise"] == 1

    with open(os.path.join(run_dir, "surprises.jsonl"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"kind": "replay_mismatch"}) + "\n")
    assert constraint_8([call, dict(call)], run_dir)["holds"]


def test_the_desks_reply_is_parsed_into_two_books_and_a_log():
    reply = ("noise\n=== THEORY ===\n```\nsemantics:\n  frame persist\n```\n"
             "=== PLAYBOOK ===\n```\n# none\n```\n"
             '=== LOG ===\n```json\n[{"id":"O-01","verdict":"accept"}]\n```\n')
    parsed = theorize.parse_reply(reply)
    assert parsed["theory"].startswith("semantics:")
    assert parsed["playbook"] == "# none"
    assert parsed["log"][0]["verdict"] == "accept"


def test_a_reply_without_a_theory_block_is_not_silently_accepted():
    parsed = theorize.parse_reply("I think ACTION2 is good.")
    assert parsed["theory"] == ""
    assert parsed["blocks_found"] == []


def test_a_declared_landmark_is_placed_from_its_cell_hint():
    """A landmark the level cannot place is a hard compile error, so the hint
    has to survive the round trip from the manual into the level instance."""
    text = ("word_table:\n"
            "  landmark exit_cell   # arc-cell: (7, 3)\n"
            "  landmark portal      # arc-cell: 12,40\n"
            "  landmark nowhere\n")
    found = theorize._landmarks_from_theory(text)
    assert found == {"exit_cell": (7, 3), "portal": (12, 40), "nowhere": None}

    store = _store([[[0, 0], [0, 6]], [[0, 6], [0, 0]]], ["ACTION1"])
    problem = problem_from_frames(store, [], landmarks=found)
    assert problem["landmarks"]["exit_cell"] == [7, 3]
    assert problem["landmarks"]["nowhere"] == [0, 0]
    assert problem["landmarks_defaulted"] == ["nowhere"]


def test_a_manual_declaring_a_landmark_compiles_once_the_level_places_it(tmp_path):
    theory = WORKED_EXAMPLE.replace(
        "  object Cart { pos: Coord, color: Int }",
        "  object Cart { pos: Coord, color: Int }\n"
        "  landmark exit_cell   # arc-cell: (0, 1)").replace(
        "goal count(Cart) = 1", "goal Cart.pos = exit_cell")
    books = Books(str(tmp_path))
    books.write(theory=theory)
    store = _store([[[0, 0, 0], [0, 0, 0], [0, 6, 0]]], [])
    books.write_problem(problem_from_frames(
        store, theorize._objects_from_theory(theory),
        landmarks=theorize._landmarks_from_theory(theory)))
    result = books.compile_all()
    assert result["ok"], result["errors"]


def test_the_colour_hint_is_read_off_the_object_declaration():
    text = ("word_table:\n"
            "  object Cart { pos: Coord, color: Int }  # arc-colour: 6\n"
            "  object Door { pos: Coord, color: Int }  # arc-color = 5\n"
            "  object Ghost { pos: Coord }\n")
    found = {o["name"]: o["color"] for o in theorize._objects_from_theory(text)}
    assert found == {"Cart": 6, "Door": 5, "Ghost": None}


# --------------------------------------------------------- the whole shell
def test_the_shell_turns_end_to_end_against_the_mock(tmp_path):
    """No key, no network, no model call, no quota -- and a full ledger."""
    from harness.run import play                       # noqa: PLC0415
    from inner.loop import TheoriaArm                  # noqa: PLC0415
    from proxy.ledger import read_ledger               # noqa: PLC0415
    from proxy.mock.arc_mock import DEFAULT_KEY, MockArc   # noqa: PLC0415

    game = "g50t-5849a774"
    slug = "pytest-" + os.path.basename(str(tmp_path))

    def factory(env_base, run):
        return TheoriaArm(env_base=env_base, run=run, game_id=game,
                          budget_actions=6, offline=True)

    with MockArc(api_key=DEFAULT_KEY, games=[game]) as mock:
        summary = play(game, slug, factory, env_upstream=mock.base_url,
                       env_key=DEFAULT_KEY, require_key=False)

    assert summary["budget"]["actions_ok"] == 6
    assert summary["model_calls"] == 0                 # offline: zero calls
    assert summary["scorecard"]["total_actions"] == 6

    run_dir = os.path.join(ARM, "runs", slug)
    everything = read_ledger(os.path.join(run_dir, "ledger.jsonl"))
    # LEDGER_FORMAT.md §1: one file holds many runs, `run_id` partitions it and
    # `seq` orders it. The file is append-only, so re-running this test adds a
    # run rather than replacing one -- which is the property being relied on.
    records = [r for r in everything if r["run_id"] == summary["run_id"]]
    events = [r["event"] for r in records]
    assert events[0] == "run_start" and events[-1] == "run_end"
    assert all(r["arm"] == "theoria" for r in records)
    assert sum(1 for e in events if e == "env_step") == 7       # RESET + 6
    # §3: step_idx is dense and monotonic within a run.
    steps = [r["step_idx"] for r in records if r["event"] == "env_step"]
    assert steps == list(range(len(steps)))
    # §2: seq is dense across the whole file, whoever wrote it.
    assert [r["seq"] for r in everything] == list(range(1, len(everything) + 1))
    # No record may carry a credential.
    assert DEFAULT_KEY not in json.dumps(everything)


def test_the_scorecard_action_count_matches_the_ledgers_successes(tmp_path):
    """baseline-arms measured scorecard.total_actions == successful actions on
    four independent samples. If that ever stops holding, the budget's whole
    unit of account is wrong and this test is where it shows."""
    from harness.run import play                       # noqa: PLC0415
    from inner.loop import TheoriaArm                  # noqa: PLC0415
    from proxy.mock.arc_mock import DEFAULT_KEY, MockArc   # noqa: PLC0415

    game = "g50t-5849a774"
    slug = "pytest-count-" + os.path.basename(str(tmp_path))

    def factory(env_base, run):
        return TheoriaArm(env_base=env_base, run=run, game_id=game,
                          budget_actions=4, offline=True)

    with MockArc(api_key=DEFAULT_KEY, games=[game]) as mock:
        summary = play(game, slug, factory, env_upstream=mock.base_url,
                       env_key=DEFAULT_KEY, require_key=False)
    assert summary["scorecard"]["total_actions"] == summary["budget"]["actions_ok"]
