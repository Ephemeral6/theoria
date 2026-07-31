"""Offline tests. No key, no network, no model call, no quota.

Everything here runs against `proxy/mock` or against hand-built frames. The
point is that every property the live run depends on is checked *before* an
action is spent, because a live action cannot be taken back.
"""

import importlib.util
import json
import os
import pathlib
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


def test_the_run_assembler_has_no_path_to_the_game_credential_either():
    """`harness/run.py` escaped the check above for as long as it was true of
    everything else.

    The key read did not appear in this file; it appeared two frames down, in
    `EnvProxyConfig.__init__`, which `Run.__init__` used to call. So the arm's
    assembler passed a source scan while putting the live credential in the
    arm's own interpreter for the whole run. The environment proxy is a child
    process now, so the scan is finally meaningful here -- and it is written
    down so that reverting to an in-process proxy goes red instead of going
    quiet.

    `read_secret` is the name that matters: it is the only door a secret comes
    through (`proxy/redact.py`), so a module that cannot reach it cannot hold
    one, whatever it does with environment variables.
    """
    code = _executable_source(os.path.join(ARM, "harness", "run.py"))
    for forbidden in ("read_secret", "load_api_key", "EnvProxyConfig",
                      "X-API-Key", "x-api-key", "Authorization"):
        assert forbidden not in code, forbidden

    # The supervisor is the only thing between this file and a key, and it does
    # not read one either: it names a variable for the *child* to read.
    supervisor = _executable_source(os.path.join(ARM, "harness",
                                                 "proxy_process.py"))
    for forbidden in ("read_secret", "load_api_key", "ARC_API_KEY"):
        assert forbidden not in supervisor, forbidden


def _executable_source(path: str) -> str:
    """A module's code with every comment and string literal removed.

    The older scan in this file drops lines that *start* with `#` or a quote,
    which is enough for `harness/arc.py` and not enough for a module whose
    docstring explains the very thing being forbidden: the two tests above and
    below are about `EnvProxyConfig` not being constructed, and both files say
    the words "EnvProxyConfig" and "read_secret" in prose several times.
    Tokenising asks the question the line filter was approximating.
    """
    import io                                          # noqa: PLC0415
    import tokenize                                    # noqa: PLC0415

    with open(path, "rb") as fh:
        raw = fh.read()
    kept = []
    for token in tokenize.tokenize(io.BytesIO(raw).readline):
        if token.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        kept.append(token.string)
    return "\n".join(kept)


def test_the_desk_env_drops_the_game_credential():
    """Kept as a cheap tripwire; the real assertion moved and is stronger.

    This used to grep `modelcall.py` for the literal `env.pop("ARC_API_KEY",
    None)`. A source-text assertion pins the spelling, not the behaviour: it
    stayed green through the whole period in which the line above it promised
    the desk could not "inherit a base URL that would send it somewhere
    unrecorded" while `ANTHROPIC_BASE_URL` was inherited on every call (A11's
    F3). It would equally have gone red on a rename that changed nothing.

    `tests/test_desk_sealing.py` now asserts the outcome -- what is in the
    environment dict actually handed to `subprocess.run` -- with a positive
    control that an unrelated variable survives. What is left here is the
    membership check, which is worth keeping only because it is free.
    """
    from harness.modelcall import SCRUBBED_FROM_DESK_ENV  # noqa: PLC0415
    assert "ARC_API_KEY" in SCRUBBED_FROM_DESK_ENV


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
def test_prose_in_an_invariant_is_a_parse_error_and_the_card_says_so():
    """The desk conflated `invariant` (an equation) with `theorem` (a
    sentence) on the first live run and paid a repair round for it. The card
    now states the rule; this pins both halves."""
    from theory_compiler.parser.theory_parser import ParseError, parse_theory  # noqa: PLC0415
    from inner.grammar_card import CARD                # noqa: PLC0415

    bad = WORKED_EXAMPLE.replace(
        "  invariant cart_unique count(Cart) = 1 [status: observed]",
        '  invariant cart_unique "there is only ever one cart" [status: observed]')
    with pytest.raises(ParseError):
        parse_theory(bad)

    good = WORKED_EXAMPLE.replace(
        "  invariant cart_unique count(Cart) = 1 [status: observed]",
        '  theorem cart_unique "there is only ever one cart" [probe: pending]')
    parse_theory(good)                                 # a sentence is fine here

    assert "No comparison op in invariant" in CARD
    assert "NOT INTERCHANGEABLE" in CARD


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


def _ring_store():
    """A 6x6 world, a 4-cell ring of colour 9 that moves down, a colour-3 pip."""
    def frame(ring, pip=(0, 5)):
        grid = [[0] * 6 for _ in range(6)]
        for r, c in ring:
            grid[r][c] = 9
        grid[pip[0]][pip[1]] = 3
        return grid
    return _store([frame([(1, 1), (1, 2), (2, 1), (2, 2)]),
                   frame([(3, 1), (3, 2), (4, 1), (4, 2)])], ["ACTION2"])


RING_THEORY = """semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Ring { pos: Coord, color: Int }   # arc-colour: 9  arc-instances: all
  Ring [segment: uniform_color ev: t0-t1 compress: 0]

events:
  event moved(o, dir)

rules:
  rule shift forall ?p in Ring [ev: t1 cov: 1/1]
    when act=key(2) and free(below(?p)) then moved(?p, down)
"""


def test_one_declaration_covers_every_cell_the_board_cannot_explain(tmp_path):
    """E-08. `render` paints one cell per instance, so an object with extent
    needs one instance per cell. Before this, a 4-cell ring was drawn as a
    single pixel and the other three were unexplained forever -- which is what
    made the first live run's responsibility count oscillate instead of fall."""
    store = _ring_store()
    decls = theorize._objects_from_theory(RING_THEORY)
    assert decls[0]["instances"] == "all"

    problem = problem_from_frames(store, decls)
    assert len(problem["objects"]) == 4
    assert {o["name"] for o in problem["objects"]} == {
        "Ring_r1c1", "Ring_r1c2", "Ring_r2c1", "Ring_r2c2"}
    assert all(o["type"] == "Ring" for o in problem["objects"])
    assert problem["instances_per_declaration"] == {"Ring": 4}

    books = Books(str(tmp_path))
    books.write(theory=RING_THEORY)
    books.write_problem(problem)
    result = books.compile_all()
    assert result["ok"], result["errors"]

    namespace, error = books.load_predictor()
    assert namespace is not None, error
    # `forall ?p in Ring` grounds once per instance.
    assert len(namespace["RULES"]) == 4
    # And the responsibility check goes green, which is the whole point.
    drawn = namespace["render"](namespace["initial_state"]())
    assert describe_diff(drawn, store.grids[0]) == "no cells changed"


def test_the_level_predicts_the_responsibility_count_certify_will_report(tmp_path):
    """A number in the level file that disagreed with the check it predicts
    would be worse than no number. A dynamic cell showing the BACKGROUND colour
    at t0 needs no owner -- the board already draws it."""
    store = _ring_store()
    problem = problem_from_frames(store,
                                  theorize._objects_from_theory(RING_THEORY))
    r = problem["responsibility"]
    assert r["dynamic_cells"] == 8          # 4 vacated + 4 arrived-at
    assert r["need_an_owner_at_t0"] == 4    # only the 4 the ring occupies at t0
    assert r["n_unexplained_at_t0"] == 0

    books = Books(str(tmp_path))
    books.write(theory=RING_THEORY)
    books.write_problem(problem)
    books.compile_all()
    report = certify.cheap(books, store, commit.action_to_manual)
    assert report["checks"]["responsibility"]["ok"] is True
    assert (report["checks"]["responsibility"]["cells_unexplained"]
            == r["n_unexplained_at_t0"])


def test_a_declaration_that_would_swallow_the_frame_is_capped_and_says_so():
    from inner.books import MAX_INSTANCES_PER_DECL     # noqa: PLC0415
    grids = [[[0] * 64 for _ in range(64)] for _ in range(2)]
    for i in range(400):                               # 400 dynamic cells of colour 7
        grids[0][i // 64][i % 64] = 7
    store = _store(grids, ["ACTION1"])
    problem = problem_from_frames(
        store, [{"name": "Blob", "type": "Blob", "color": 7, "instances": "all"}])
    assert len(problem["objects"]) == MAX_INSTANCES_PER_DECL
    assert problem["instance_caps_hit"]
    assert "capped" in problem["instance_caps_hit"][0]


def test_a_single_cell_object_is_still_a_single_instance():
    store = _ring_store()
    problem = problem_from_frames(
        store, [{"name": "Pip", "type": "Pip", "color": 3, "instances": "one"}])
    assert len(problem["objects"]) == 1
    assert "instances_per_declaration" not in problem


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


def test_a_forall_schema_is_one_hypothesis_not_one_per_instance(tmp_path):
    """`forall ?p in Ring` grounds to one rule per instance. Ablating each
    separately would be seventy near-identical hypotheses and seventy times the
    work; the manual's claim is the schema."""
    store = _ring_store()
    books = Books(str(tmp_path))
    books.write(theory=RING_THEORY)
    books.write_problem(problem_from_frames(
        store, theorize._objects_from_theory(RING_THEORY)))
    assert books.compile_all()["ok"]
    namespace, error = books.load_predictor()
    assert namespace is not None, error

    assert len(namespace["RULES"]) == 4                # four ground rules ...
    hypotheses = probe_beat.build_hypotheses(namespace)
    ablations = [h for h in hypotheses if h.id.startswith("without_")]
    assert [h.id for h in ablations] == ["without_shift"]   # ... one hypothesis
    assert "4 ground instances" in ablations[0].description

    # And suppressing the schema really does suppress every instance of it.
    state = namespace["initial_state"]()
    action = ("key", 2)
    assert ablations[0].predict(state, action) != hypotheses[0].predict(state, action)
    assert ablations[0].predict(state, action) == hypotheses[1].predict(state, action)


# ----------------------------------------------------------------- the reply
def test_the_evidence_gate_waits_for_a_batch_but_never_cancels_a_call():
    """A surprise triggers theorize; it does not make another pass over the
    same frames worth $1.30. The gate delays a call until enough new world has
    arrived -- and stands aside when the budget is nearly spent, so a run
    cannot end without theorizing on what it has."""
    from inner.loop import MIN_NEW_FRAMES_BETWEEN_THEORIZE as N   # noqa: PLC0415
    assert N >= 2

    class Fake:
        def __init__(self, steps, last, left):
            self.steps = list(range(steps))
            self._frames_at_last_theorize = last
            self.actions_left = left

        def gated(self):
            new = len(self.steps) - self._frames_at_last_theorize
            return new < N and self.actions_left > N

    assert Fake(steps=6, last=5, left=100).gated()        # 1 new: wait
    assert not Fake(steps=9, last=5, left=100).gated()    # 4 new: go
    assert not Fake(steps=6, last=5, left=2).gated()      # nearly out: go anyway


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


def test_the_sealed_pile_check_reads_the_bytes_and_fails_closed():
    """"The guard did not fire" is a statement about the guard. The manifest
    has to make a statement about what actually crossed the wire."""
    from armtools.archive import sealing                # noqa: PLC0415
    clean = [{"event": "env_step", "game_id": "g50t-5849a774", "run_id": "r"}]
    report = sealing(clean)
    assert report["cut_integrity"] is True
    assert report["sealed_pile_untouched"] is True
    assert report["game_ids_anywhere_in_the_records"] == ["g50t-5849a774"]

    # A sealed id anywhere in any record -- not only in a game_id field --
    # must show up. bp35-0a0ad940 is on the sealed pile.
    dirty = clean + [{"event": "model_call", "run_id": "r",
                      "request": {"prompt": "compare with bp35-0a0ad940"}}]
    report = sealing(dirty)
    assert report["sealed_game_ids_found"] == ["bp35-0a0ad940"]
    assert report["sealed_pile_untouched"] is False


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



def _own_pool(tmp_path):
    """A spend pool this test owns, so the fleet's does not get billed.

    `play()` defaults `spend_gate=None`, which resolves to the *real* pool --
    the one every session shares and the one whose action ceiling decides
    whether the sealed confirmation run can still afford to happen. Tests that
    forgot this wrote 2 817 of its 4 775 actions. The dollars were $0.00, which
    is why it went unnoticed for two days.
    """
    from harness import run as run_mod                 # noqa: PLC0415
    from proxy.spend_gate import SpendGate             # noqa: PLC0415

    policy = run_mod._scratch_policy(str(tmp_path / "scratch-pool.jsonl"))
    gate = SpendGate(policy)
    return gate, {"pool": policy.pool,
                  "ledger_abspath": os.path.abspath(policy.ledger_path)}

# --------------------------------------------------------- the whole shell
def test_the_shell_turns_end_to_end_against_the_mock(tmp_path):
    """No key, no network, no model call, no quota -- and a full ledger."""
    from harness.run import FIXTURE_RUNS_DIR, play     # noqa: PLC0415
    from inner.loop import TheoriaArm                  # noqa: PLC0415
    from proxy.ledger import read_ledger               # noqa: PLC0415
    from proxy.mock.arc_mock import DEFAULT_KEY, MockArc   # noqa: PLC0415

    game = "g50t-5849a774"
    slug = "pytest-" + os.path.basename(str(tmp_path))
    # The ledger goes in `tmp_path`, which this test owns, rather than in the
    # run directory, which it does not.
    #
    # It used to land in `runs/<slug>/ledger.jsonl`, and because `tmp_path`'s
    # basename is stable across pytest invocations, every run of this test on
    # this machine appended to one file forever. That was deliberate -- the old
    # comment here called cross-run accumulation "the property being relied on"
    # -- and it made the assertion below a claim about an artefact with no
    # owner, unbounded lifetime, and no exclusivity.
    #
    # It broke exactly as that description predicts. On 2026-07-28T23:39:49Z two
    # pytest processes ran this test concurrently on one checkout; `Ledger`
    # seeds `seq` once in `__init__` under an in-process lock only, so the
    # second writer resumed from a tail the first had already moved past. Seven
    # `seq` values were issued twice and the `prev` chain forked. No record was
    # lost, but `verify_chain` and `validate_ledger` both go FAIL, and the file
    # is gitignored and append-only -- so the failure was permanent and no code
    # change could clear it. The suite was green exactly once per clean checkout
    # and red on this machine forever after.
    #
    # Giving the test its own file makes the whole-file assertion true by
    # construction and removes the poison pill. It does NOT fix the writer:
    # `Ledger` still cannot be shared by two processes, which is a `proxy/`
    # defect and is filed there. Cross-run continuation on a shared file is a
    # ledger property and is tested in `proxy/tests/test_ledger.py`, over a file
    # that test owns.
    ledger_path = str(tmp_path / "ledger.jsonl")

    def factory(env_base, run):
        return TheoriaArm(env_base=env_base, run=run, game_id=game,
                          budget_actions=6, offline=True)

    # Not `runs/`: that is the archive, and this run cost nothing and proves
    # nothing about the world. See `harness.run.FIXTURE_RUNS_DIR`.
    with MockArc(api_key=DEFAULT_KEY, games=[game]) as mock:
        gate, expect = _own_pool(tmp_path)
        summary = play(game, slug, factory, env_upstream=mock.base_url,
                       env_key=DEFAULT_KEY, require_key=False,
                       spend_gate=gate, expect_pool=expect,
                       runs_root=FIXTURE_RUNS_DIR,
                       ledger_path=ledger_path)

    assert summary["budget"]["actions_ok"] == 6
    assert summary["model_calls"] == 0                 # offline: zero calls
    assert summary["scorecard"]["total_actions"] == 6

    everything = read_ledger(ledger_path)
    # LEDGER_FORMAT.md §1: one file holds many runs, `run_id` partitions it and
    # `seq` orders it.
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
    from harness.run import FIXTURE_RUNS_DIR, play     # noqa: PLC0415
    from inner.loop import TheoriaArm                  # noqa: PLC0415
    from proxy.mock.arc_mock import DEFAULT_KEY, MockArc   # noqa: PLC0415

    game = "g50t-5849a774"
    slug = "pytest-count-" + os.path.basename(str(tmp_path))

    def factory(env_base, run):
        return TheoriaArm(env_base=env_base, run=run, game_id=game,
                          budget_actions=4, offline=True)

    with MockArc(api_key=DEFAULT_KEY, games=[game]) as mock:
        gate, expect = _own_pool(tmp_path)
        summary = play(game, slug, factory, env_upstream=mock.base_url,
                       env_key=DEFAULT_KEY, require_key=False,
                       spend_gate=gate, expect_pool=expect,
                       runs_root=FIXTURE_RUNS_DIR,
                       ledger_path=str(tmp_path / "ledger.jsonl"))
    assert summary["scorecard"]["total_actions"] == summary["budget"]["actions_ok"]


# ----------------------------------------------------------- the archive
def test_armversion_reimplements_the_walk_exactly(tmp_path):
    """`armversion._counted` must agree with `_bootstrap.arm_version`'s walk.

    They are two implementations of one rule -- one over a directory, one over
    a git tree -- and the rule is stated with *substring* tests, so `runsim/`
    and `__pycache__x/` are skipped where a component-wise reading would keep
    them. An adversarial review found the reimplementation reading it
    component-wise. Nothing on disk was wrong, because no such directory has
    ever existed here; the divergence would simply have made a real run report
    that it matched no commit. This pins the four cases that separate the two
    readings.
    """
    from armtools.armversion import _counted            # noqa: PLC0415

    cases = {
        "harness/run.py": True,
        "_bootstrap.py": True,
        "runs/20260728T0Z-x/thing.py": False,           # the archive
        "world/runs/x.py": False,                       # a nested one
        "runsim/x.py": False,                           # substring, not component
        "runs_old/x.py": False,
        "__pycache__/x.py": False,
        "__pycache__x/x.py": False,                     # substring again
        "notes.md": False,                              # not a .py file
    }
    for rel, expected in cases.items():
        assert _counted(rel) is expected, rel

    # And the walk itself agrees, on a real directory built to contain them.
    arm = tmp_path / "theoria-arm"
    for rel in cases:
        target = arm / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("x = 1\n", encoding="utf-8")
    (arm / "_bootstrap.py").write_text(
        pathlib.Path(os.path.join(ARM, "_bootstrap.py")).read_text(
            encoding="utf-8"), encoding="utf-8")

    spec = importlib.util.spec_from_file_location(
        "arm_under_test_bootstrap", str(arm / "_bootstrap.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    walked = module.arm_version()
    assert walked["files"] == sum(1 for v in cases.values() if v)


def test_arm_version_does_not_depend_on_where_the_arm_is_checked_out(tmp_path):
    """A worktree named `runs-something` used to zero the hash.

    `os.sep + "runs" in root` was applied to the *absolute* path, so an
    ancestor directory decided it: under `.worktrees/runs-cleanup/` -- an
    ordinary name under CLAUDE.md's worktree rule -- every file was skipped and
    `arm_version` returned `files: 0` and the sha256 of the empty string. Any
    run made there records a version that can never be matched to a commit.
    """
    digests = []
    for parent in ("plain", "runs-cleanup", "__pycache__-ish"):
        arm = tmp_path / parent / "theoria-arm"
        (arm / "harness").mkdir(parents=True)
        (arm / "harness" / "run.py").write_text("x = 1\n", encoding="utf-8")
        (arm / "_bootstrap.py").write_text(
            pathlib.Path(os.path.join(ARM, "_bootstrap.py")).read_text(
                encoding="utf-8"), encoding="utf-8")
        spec = importlib.util.spec_from_file_location(
            "bootstrap_" + parent.replace("-", "_"), str(arm / "_bootstrap.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        digests.append(module.arm_version())

    assert digests[0]["files"] == 2
    assert len({d["sha256"] for d in digests}) == 1, digests


def test_the_archive_stays_accountable():
    """`verify_provenance`'s ten checks, run as part of the suite.

    The archive is the thing Phase 4 reads back to account for every ARC action
    this arm spent. A check that only runs when somebody remembers to run it is
    not a guarantee.

    The count is asserted so that a check cannot quietly disappear -- a suite
    that runs nine checks and a suite that runs eight both print green. It went
    from nine to ten with check 10 ("every file a manifest lists is in the clone
    or excluded by the repository's own rules"), which exists because check 8
    dispatches and therefore cannot see a stale `files[]` in an `amend`
    manifest.
    """
    from armtools import verify_provenance               # noqa: PLC0415

    checks = verify_provenance.run()
    assert not checks.failed, [
        "%s: %s" % (r["check"], r["detail"]) for r in checks.failed]
    assert len(checks.rows) == 10


# ------------------------------------------- E14: a crash is not a finding
#
# The negative sample. A `step` that is *constructed* to raise is driven
# through both sites, and the report must go RED rather than clean. Then the
# same crash is driven through with the counting removed, which is the only way
# to show these assertions are not passing for free.

class _CrashingStep:
    """A predictor that raises on demand, and counts how often it was asked.

    Construction guarantees the crash: `raise_on` is checked before anything
    else happens, and the exception type is one neither site declares, so it can
    only reach the bare `except Exception` handlers this ticket is about.
    """

    class Boom(RuntimeError):
        pass

    def __init__(self, inner, raise_on=lambda state, action: True):
        self.inner = inner
        self.raise_on = raise_on
        self.calls = 0
        self.raised = 0

    def __call__(self, state, action):
        self.calls += 1
        if self.raise_on(state, action):
            self.raised += 1
            raise self.Boom("injected: the compiled manual fell over on %r"
                            % (action,))
        return self.inner(state, action)


def _worked_example_books(tmp_path, goal="goal Cart.pos = (2, 2)"):
    theory = WORKED_EXAMPLE.replace("goal count(Cart) = 1", goal)
    books = Books(str(tmp_path))
    books.write(theory=theory, playbook="# none\n")
    books.write_problem({"name": "l", "grid": [3, 3], "background": 0,
                         "board": [[0] * 3 for _ in range(3)],
                         "objects": [{"name": "Cart", "type": "Cart",
                                      "pos": [2, 1], "color": 6}]})
    compiled = books.compile_all()
    namespace, error = books.load_predictor()
    assert namespace is not None, error
    return books, namespace, compiled


def _worked_example_namespace(tmp_path, goal="goal Cart.pos = (2, 2)"):
    return _worked_example_books(tmp_path, goal)[1]


def test_the_unpoisoned_planner_still_says_unsat_and_says_why(tmp_path):
    """The control. Without an injected crash the same instance must stay green,
    or the negative sample below would prove nothing about crashes."""
    namespace = _worked_example_namespace(tmp_path)
    report = plan_beat._tier_bfs(namespace, node_cap=plan_beat.BFS_NODE_CAP)
    assert report["status"] == "unsat"
    assert report["exhaustive"] is True
    assert report["step_crashes"]["count"] == 0
    assert report["reachable_states"] == 3
    # The ceiling is in the artifact, positively, the way ladder.py:226 puts it
    # there -- a reader can check 3 < cap without trusting this sentence.
    assert report["search_ceiling"]["node_cap"] == plan_beat.BFS_NODE_CAP


def test_a_crashing_step_turns_the_planner_red_not_clean(tmp_path):
    """E14, the whole ticket in one assertion: the exhaustiveness claim must
    NOT survive a crash. Before the fix this returned `unsat` with "the whole
    reachable set (N states) was enumerated" -- and the fewer successors
    survived, the sooner it said so."""
    namespace = _worked_example_namespace(tmp_path)
    crashing = _CrashingStep(namespace["step"])
    namespace = dict(namespace, step=crashing)

    report = plan_beat._tier_bfs(namespace, node_cap=plan_beat.BFS_NODE_CAP)

    assert crashing.raised > 0, "the injected step never actually raised"
    assert report["status"] == "unsat_unsound"
    assert report["exhaustive"] is False
    assert report["step_crashes"]["count"] == crashing.raised
    assert report["step_crashes"]["successors_pruned"] == crashing.raised
    assert report["step_crashes"]["by_type"] == {"Boom": crashing.raised}
    assert "over budget" not in (report.get("error") or "")
    assert report["error"] and "raised" in report["error"]
    # And the sentence that was the defect is gone from the artifact.
    assert "the whole reachable set" not in report["detail"]
    assert "not entitled" in report["detail"]


def test_without_the_crash_count_that_same_crash_is_waved_through(
        tmp_path, monkeypatch):
    """Non-vacuity. Remove the counting and nothing else, re-run the identical
    injected crash, and watch the report come back clean and exhaustive. This
    is what the code did before E14, and it is why the assertions above are
    load-bearing rather than decorative."""
    namespace = _worked_example_namespace(tmp_path)
    crashing = _CrashingStep(namespace["step"])
    namespace = dict(namespace, step=crashing)

    monkeypatch.setattr(plan_beat.StepCrashLog, "record",
                        lambda self, exc, **kw: None)
    report = plan_beat._tier_bfs(namespace, node_cap=plan_beat.BFS_NODE_CAP)

    assert crashing.raised > 0, "the injected step never actually raised"
    assert report["step_crashes"]["count"] == 0        # the crash left no trace
    assert report["status"] == "unsat"                 # ... and the claim stands
    assert report["exhaustive"] is True
    assert "the whole reachable set" in report["detail"]
    # 3 states without the crash (see the control above), 1 with it: the health
    # certificate got *cleaner* as the predictor got worse.
    assert report["reachable_states"] < 3


def test_a_crashing_step_cannot_certify_constraint_9(tmp_path):
    """The certify half. `ok: true` with "no (state, action) among N x M
    admitted two rules" must not be reachable while pairs are going
    unadjudicated -- the N x M was always the nominal product."""
    namespace = _worked_example_namespace(tmp_path, goal="goal count(Cart) = 1")
    store = _store([[[0, 0, 0], [0, 0, 0], [0, 6, 0]]], [])

    clean = certify._ambiguity(namespace, store, commit.action_to_manual)
    assert clean["ok"] is True
    assert clean["step_crashes"]["count"] == 0
    assert clean["pairs_checked"] == clean["pairs_nominal"]
    assert clean["sample_cap"] == certify.AMBIGUITY_SAMPLE_CAP

    crashing = _CrashingStep(namespace["step"])
    poisoned = dict(namespace, step=crashing)
    report = certify._ambiguity(poisoned, store, commit.action_to_manual)

    assert crashing.raised > 0
    assert report["ok"] is False
    assert report["step_crashes"]["count"] == crashing.raised
    assert report["pairs_checked"] < report["pairs_nominal"]
    assert "admitted two rules" not in report["detail"]
    assert "NOT certified" in report["detail"]


def test_without_the_crash_count_constraint_9_certifies_a_broken_manual(
        tmp_path, monkeypatch):
    """Non-vacuity, certify half."""
    namespace = _worked_example_namespace(tmp_path, goal="goal count(Cart) = 1")
    store = _store([[[0, 0, 0], [0, 0, 0], [0, 6, 0]]], [])
    crashing = _CrashingStep(namespace["step"])
    poisoned = dict(namespace, step=crashing)

    monkeypatch.setattr(certify.StepCrashLog, "record",
                        lambda self, exc, **kw: None)
    report = certify._ambiguity(poisoned, store, commit.action_to_manual)

    assert crashing.raised > 0
    assert report["step_crashes"]["count"] == 0
    assert report["ok"] is True                        # constraint 9 "passes"
    assert "admitted two rules" in report["detail"]


# ------------------- E14, second pass: what the adversarial review refuted

def test_a_plan_found_after_a_crash_reports_the_crash_and_drops_optimality(
        tmp_path):
    """Adversarial review, correction 1 and 2. The first version of this change
    snapshotted the crash account at four of five exits and missed the `ok:
    True` one, so a search that crashed and then found the goal published
    `count: 0` -- a false printed zero, which is worse than an absent one -- and
    `optimal: True`, which is an exhaustiveness claim: BFS is length-optimal
    only if no successor was dropped."""
    books, namespace, compiled = _worked_example_books(
        tmp_path, goal="goal Cart.pos = (0, 1)")
    real = namespace["step"]

    def crashing(state, action):
        if tuple(action) == ("key", 9):
            raise _CrashingStep.Boom("injected on the bogus action")
        return real(state, action)

    # An extra declared action that always raises, so the good route still
    # reaches the goal and the search exits via `ok: True` rather than draining.
    poisoned = dict(namespace, step=crashing,
                    ACTIONS=list(namespace["ACTIONS"]) + [("key", 9)])

    entry = plan_beat._tier_bfs(poisoned, node_cap=plan_beat.BFS_NODE_CAP)
    assert entry["ok"] is True
    assert entry["actions"] == [["key", 1], ["key", 1]]
    assert entry["step_crashes"]["count"] > 0, (
        "the sat exit published a crash count of zero on a search that crashed")
    assert entry["error"] and "raised" in entry["error"]
    assert "NOT known to be shortest" in entry["detail"]

    # Through the real entry point, not just the tier -- the adversarial review
    # showed the aggregation layer was where the false zero survived, and that
    # skipping it was how the first pass missed this.
    report = plan_beat.plan(books, poisoned, dict(compiled, forms={}))
    assert report["status"] == "sat"
    assert report["optimal"] is False
    assert report["step_crashes"]["count"] == entry["step_crashes"]["count"]


def test_every_exit_of_the_bfs_tier_carries_the_final_crash_account(tmp_path):
    """The structural half of correction 1: the account is stamped once, after
    the search returns, so no exit can be added later that forgets it. Checked
    by walking every exit rather than by reading the code."""
    namespace = _worked_example_namespace(tmp_path)

    exits = {
        "no_actions": dict(namespace, ACTIONS=[]),
        "already_at_goal": _worked_example_namespace(
            tmp_path / "goal", goal="goal Cart.pos = (2, 1)"),
        "unsat": namespace,
    }
    for name, ns in exits.items():
        entry = plan_beat._tier_bfs(ns, node_cap=plan_beat.BFS_NODE_CAP)
        assert "step_crashes" in entry, name
        assert entry["step_crashes"]["count"] == 0, name
        assert "search_ceiling" in entry, name

    timed_out = plan_beat._tier_bfs(namespace, node_cap=10 ** 9, deadline_s=0.0)
    assert timed_out["status"] == "search_timeout"
    assert "step_crashes" in timed_out and "search_ceiling" in timed_out


def test_a_manual_without_a_declared_ambiguity_type_files_crashes_as_crashes(
        tmp_path):
    """Adversarial review, correction 10. The default for a missing
    `AmbiguousTransition` was `Exception`, so `except ambiguous` swallowed every
    crash and filed it as a constraint-9 CLASH -- a positive finding about the
    world manufactured from a bug -- leaving `pairs_checked` above
    `pairs_nominal` with a crash count of zero."""
    namespace = _worked_example_namespace(tmp_path, goal="goal count(Cart) = 1")
    store = _store([[[0, 0, 0], [0, 0, 0], [0, 6, 0]]], [])
    crashing = _CrashingStep(namespace["step"])
    stripped = {k: v for k, v in namespace.items() if k != "AmbiguousTransition"}
    stripped["step"] = crashing

    report = certify._ambiguity(stripped, store, commit.action_to_manual)

    assert crashing.raised > 0
    assert report["step_crashes"]["count"] == crashing.raised
    assert report["n_clashes"] == 0, (
        "a crash was filed as an ambiguity -- a finding about the world")
    assert report["pairs_checked"] <= report["pairs_nominal"]
    assert report["ok"] is False


def test_the_arms_desk_is_armed_against_the_game_id(tmp_path):
    """The wiring, not the mechanism.

    `test_desk_gate.py` proves `ModelDesk` refuses a prompt carrying the game
    id. That is worth nothing if `inner/loop.py` builds the desk without arming
    it, which is exactly the kind of gap that let the rule hold "by omission"
    in the first place. So: build the arm the way `play()` does and look at the
    desk it actually made.

    Both spellings must be present. The stem is the half that leaks -- it is
    what a run slug embeds and therefore what an absolute path in an engine
    traceback carries into the prompt.
    """
    from inner.loop import TheoriaArm                   # noqa: PLC0415
    from proxy.ledger import Ledger, RunLedger          # noqa: PLC0415

    class _Run:
        def __init__(self, d):
            self.dir = str(d)
            self.run_id = "r-wiring"
            self.run = RunLedger(Ledger(str(d / "l.jsonl")), "r-wiring",
                                 "theoria", game_id="g50t-5849a774")
            self.spend_binding = None

    arm = TheoriaArm(env_base="http://127.0.0.1:1", run=_Run(tmp_path),
                     game_id="g50t-5849a774", budget_actions=1, offline=True)

    assert "g50t-5849a774" in arm.desk.forbid_in_prompt
    assert "g50t" in arm.desk.forbid_in_prompt


def test_a_campaign_leg_slug_carries_no_game(tmp_path):
    """The other half of the same rule, at the source.

    The guard is a backstop. The fix is that the id never enters a path, so it
    cannot be picked up by a traceback, a compiler error or a Lean diagnostic
    that this arm has not thought of.
    """
    from harness import campaign as camp                # noqa: PLC0415

    c = camp.Campaign(prompt_id="A3-campaign-devpile", out_dir=str(tmp_path),
                      games=["g50t-5849a774"])
    slug = c._leg_slug("g50t-5849a774", 1)
    assert "g50t" not in slug
    assert "5849a774" not in slug
    assert slug.endswith("-leg01")


@pytest.mark.parametrize("breach", ["AnonymityBreach", "SealedPileBreach"])
def test_an_anonymity_breach_ends_the_run_instead_of_being_filed_as_a_desk_failure(
        tmp_path, breach):
    """The defect this fix introduced, caught before it shipped.

    `_main_loop` wraps theorize in `except Exception` so a desk that times out
    or returns junk does not end the run: the manual stays, the surprises stay
    pending, and the turn falls through to gathering more evidence. That is
    right for the failures the loop can recover from by trying again.

    `AnonymityBreach` is not one of them. Swallowed by that handler it would be
    recorded as "the desk failed", the leg would keep playing, and the rest of
    the budget would be spent on a run already inadmissible under
    `Theoria.md:353`. The breach has to reach the caller, exactly as
    `CostCeilingReached` does.

    `SealedPileBreach` is the second parameter and it is not redundant. It is a
    *subclass*, so the loop's `except (AnonymityBreach, CredentialBreach):
    raise` covers it today by inheritance and nothing says so out loud -- a
    later hand that made it a sibling of `AnonymityBreach`, which is the
    obvious refactor for two things that are "different incidents", would drop
    the stricter of the two into the broad `except Exception` handler below.
    The leg would then keep playing and keep spending after a *sealed* game had
    reached model context, which is the one failure in this file that no repeat
    run undoes. Cheap to pin, expensive to discover.

    Driven through the real loop rather than asserted against the source: the
    whole point is which handler catches it, and reading the file cannot tell
    you that.
    """
    import harness.modelcall as modelcall               # noqa: PLC0415
    from harness.modelcall import AnonymityBreach       # noqa: PLC0415
    from harness.run import FIXTURE_RUNS_DIR, play      # noqa: PLC0415
    from inner.loop import TheoriaArm                   # noqa: PLC0415
    from proxy.mock.arc_mock import DEFAULT_KEY, MockArc    # noqa: PLC0415

    raised = getattr(modelcall, breach)
    assert issubclass(raised, AnonymityBreach)

    game = "g50t-5849a774"
    seen = {}

    def factory(env_base, run):
        arm = TheoriaArm(env_base=env_base, run=run, game_id=game,
                         budget_actions=8, offline=True)

        def boom(*a, **kw):
            seen["called"] = seen.get("called", 0) + 1
            raise raised("the prompt carries a game id")

        arm.desk.call = boom
        # Force theorize to be reached: offline skips it, so re-arm the flag
        # the loop consults and give it a surprise to act on.
        arm.offline = False
        arm.register.fire("replay_mismatch", "forced, so theorize is reached")
        return arm

    with MockArc(api_key=DEFAULT_KEY, games=[game]) as mock:
        with pytest.raises(raised):
            # Not `runs/`: D-S8-018. This run cost nothing and proves nothing
            # about the world, and left in the archive it trips
            # `verify_provenance`'s first check on the *next* invocation of the
            # suite -- which is how it was found. The pool is private for the
            # same reason, one ledger over: a test must not spend from the
            # fleet's shared purse either.
            gate, expect = _own_pool(tmp_path)
            play(game, "pytest-anon-" + os.path.basename(str(tmp_path)),
                 factory, env_upstream=mock.base_url, env_key=DEFAULT_KEY,
                 require_key=False, spend_gate=gate, expect_pool=expect,
                 runs_root=FIXTURE_RUNS_DIR,
                 ledger_path=str(tmp_path / "ledger.jsonl"))

    assert seen.get("called"), "the desk was never reached; the test proved nothing"
