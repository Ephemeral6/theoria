"""Tests for the A0 cold-start spike.

Two kinds, and the second kind is the one that matters:

* **positive** — the loop does what the milestones claim;
* **mutation** — a deliberately broken manual is *caught*. A green certify is
  worth nothing unless a red one is reachable, and the cheap layer went green on
  the very first run of the real manual, which is exactly when a checker most
  needs to prove it is not vacuous.
"""

import importlib.util
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import _bootstrap  # noqa: F401,E402

from certify import lean_check, replay  # noqa: E402
from compile import problem as problem_mod  # noqa: E402
from pipeline import multi_miner, segment_operators  # noqa: E402
from pipeline.board import extract_board, object_layer  # noqa: E402
from pipeline.engines_stage import background_color  # noqa: E402
from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402
from world import a0_world  # noqa: E402
from world.explorer import coverage_report, explore  # noqa: E402
from world.ground_truth import read_trace  # noqa: E402

ARTIFACTS = os.path.join(ROOT, "artifacts")
GENERATED = os.path.join(ROOT, "theory", "generated")
GENERATED_NB = os.path.join(ROOT, "theory", "generated_no_button")
TRACE = os.path.join(ARTIFACTS, "raw_trace.jsonl")
TRACE_NB = os.path.join(ARTIFACTS, "raw_trace_no_button.jsonl")

needs_artifacts = pytest.mark.skipif(
    not os.path.exists(TRACE), reason="run `python run_all.py` first"
)
needs_generated = pytest.mark.skipif(
    not os.path.exists(os.path.join(GENERATED, "theory.py")),
    reason="run `python run_all.py` first",
)


# ------------------------------------------------------------------ M1 world

def test_world_is_deterministic():
    world = a0_world.A0World(a0_world.BASE)
    state = world.initial()
    first = [world.step(state, a).key() for a in a0_world.ACTIONS]
    second = [world.step(state, a).key() for a in a0_world.ACTIONS]
    assert first == second


def test_step_is_total_and_single_valued():
    world = a0_world.A0World(a0_world.BASE)
    for state in world.reachable():
        successors = {a: world.step(state, a) for a in a0_world.ACTIONS}
        assert len(successors) == len(a0_world.ACTIONS)
        for nxt in successors.values():
            assert world.in_bounds(nxt.cart)
            assert nxt.cart not in world.walls


def test_render_is_full_frame():
    """Every pixel is board or exactly one object — no cell is contested."""
    world = a0_world.A0World(a0_world.BASE)
    for state in world.reachable():
        frame = world.render(state)
        assert len(frame) == a0_world.HEIGHT
        assert all(len(row) == a0_world.WIDTH for row in frame)
        occupied = [state.cart, world.spec.button_cell]
        if not state.pressed:
            occupied.append(world.spec.door_cell)
        assert len(set(occupied)) == len(occupied)


def test_explorer_is_reproducible_and_covers_the_mechanisms():
    states_a, actions_a = explore(a0_world.BASE)
    states_b, actions_b = explore(a0_world.BASE)
    assert [s.key() for s in states_a] == [s.key() for s in states_b]
    assert actions_a == actions_b

    report = coverage_report(a0_world.BASE, states_a, actions_a)
    assert report["button_press_transitions"], "the latch was never exercised"
    assert report["portal_transitions"], "the portal was never exercised"
    assert report["door_entry_transitions"], "the Door was never walked through"
    assert report["win_frames"], "the goal was never reached"
    # 233/236: the three uncoverable pairs are the alternative Button approaches,
    # unreachable once the latch is set.  D-A0-003.
    assert report["covered_pairs"] == 233
    assert len(report["uncovered_pairs"]) == 3


@needs_artifacts
def test_trace_is_byte_stable():
    before = open(TRACE, "rb").read()
    from world.ground_truth import write_trace
    world = a0_world.A0World(a0_world.BASE)
    states, actions = explore(a0_world.BASE)
    tmp = os.path.join(ARTIFACTS, "_tmp_trace.jsonl")
    write_trace(tmp, world, states, actions)
    after = open(tmp, "rb").read()
    os.remove(tmp)
    assert before == after


# --------------------------------------------------------------- M2 engines

@needs_artifacts
def test_board_extraction_finds_the_hole_in_the_wall():
    frames, _actions, _wins = read_trace(TRACE)
    board = extract_board(frames)
    background = background_color(board, frames)
    assert background == 0, "the walls must not be mistaken for background"
    dynamic = set(board.dynamic_cells)
    assert (4, 5) in dynamic, "the Door cell is the wall's one unexplained cell"
    assert (3, 2) in dynamic, "the Button cell changes colour"
    assert (0, 0) not in dynamic


@needs_artifacts
def test_uniform_colour_operator_wins_on_script_bits():
    frames, _actions, _wins = read_trace(TRACE)
    board = extract_board(frames)
    background = background_color(board, frames)
    layer = object_layer(frames, board, background=background)
    name, seg, report = segment_operators.choose_operator(layer, background)
    assert name.endswith("uniform_color")
    assert len(seg.tracks) == 3
    chosen = next(r for r in report if r["chosen"])
    other = next(r for r in report if not r["chosen"])
    assert chosen["script_bits"] < other["script_bits"]
    assert other["tracks"] > 10, "the colour-agnostic operator should fragment"


@needs_artifacts
def test_mined_rules_cover_every_transition_exclusively():
    frames, actions, _wins = read_trace(TRACE)
    board = extract_board(frames)
    background = background_color(board, frames)
    layer = object_layer(frames, board, background=background)
    _name, seg, _r = segment_operators.choose_operator(layer, background)
    track_ids = [t.track_id for t in seg.tracks]
    transitions = multi_miner.build_transitions(frames, layer, actions, seg,
                                                background=background)
    result = multi_miner.mine(transitions, track_ids)
    for tid in track_ids:
        assert result.guards_are_mutually_exclusive(tid), tid
        assert result.explains_every_transition(tid), tid


@needs_artifacts
def test_candidates_match_the_frozen_schema():
    from tools.validate_candidates import main as validate  # engine-rig
    for name in ("candidates.jsonl", "candidates_no_button.jsonl"):
        path = os.path.join(ARTIFACTS, name)
        assert os.path.exists(path)
        assert validate([path]) == 0


@needs_artifacts
def test_zero_space_found_the_latch_law():
    report = json.load(open(os.path.join(ARTIFACTS, "engines_report.json"),
                            encoding="utf-8"))
    supports = [set(law["support"]) for law in report["zero_space"]["global_laws"]]
    assert {"8@(3,2)", "5@(4,5)"} in supports, (
        "the Button<->Door dependency should come out as a conservation law"
    )


# ---------------------------------------------------------------- M3 theory

def test_theory_dsl_parses_and_says_what_the_log_claims():
    for name in ("theory.dsl", "theory_no_button.dsl"):
        ast = parse_theory(open(os.path.join(ROOT, "theory", name),
                                encoding="utf-8").read())
        assert ast.word_table and ast.rules and ast.goal and ast.laws
        for rule in ast.rules.rules:
            assert rule.meta is not None and rule.meta.coverage, rule.name

    ast = parse_theory(open(os.path.join(ROOT, "theory", "theory.dsl"),
                            encoding="utf-8").read())
    names = {r.name for r in ast.rules.rules}
    assert names == {"push_up", "push_down", "push_left", "push_right",
                     "teleport_down", "press_left", "door_opens_left"}
    # R-05: the direction generalisation of the press was rejected, on purpose.
    assert "press_up" not in names
    assert {t.name for t in ast.laws.theorems} == {"press_is_direction_free"}
    assert ast.laws.theorems[0].probe == "pending"


def test_playbook_is_legal_and_every_entry_carries_its_warrant():
    """Constraint 10's anti-cheat, plus constraint 5 applied to the playbook."""
    from theory_compiler.parser.ast_nodes import (
        HeuristicStmt, OrderStmt, PreferStmt, PruneStmt)
    from theory_compiler.parser.playbook_parser import parse_playbook

    playbook = os.path.join(ROOT, "theory", "playbook.dsl")
    ast = parse_playbook(open(playbook, encoding="utf-8").read())
    assert ast.statements
    for statement in ast.statements:
        if isinstance(statement, (OrderStmt, PruneStmt)):
            assert statement.proof, statement
        elif isinstance(statement, HeuristicStmt):
            assert statement.admissible is not None, statement
        elif isinstance(statement, PreferStmt):
            assert statement.evidence, "an empirical entry with no k/n"


# --------------------------------------------------------------- M4 certify

@needs_generated
def test_cheap_certify_is_green():
    report = replay.certify(os.path.join(GENERATED, "theory.py"), TRACE)
    assert report["green"], report["anomalies"][:5]
    assert report["pixels_checked"] == 276 * 81


@needs_generated
def test_cheap_certify_is_green_on_the_variant():
    report = replay.certify(os.path.join(GENERATED_NB, "theory.py"), TRACE_NB)
    assert report["green"], report["anomalies"][:5]


def _load(path):
    spec = importlib.util.spec_from_file_location("a0_mut", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@needs_generated
@pytest.mark.parametrize("mutation,expect", [
    ("drop_door_rule", "render_mismatch"),
    ("drop_press_rule", "render_mismatch"),
    ("break_teleport", "render_mismatch"),
    ("drop_door_object", "unowned_pixel"),
])
def test_mutants_are_caught(tmp_path, mutation, expect):
    """A green certify only means something if a red one is reachable."""
    source = open(os.path.join(GENERATED, "theory.py"), encoding="utf-8").read()
    if mutation == "drop_door_rule":
        source = source.replace("('door_opens_left', _guard_door_opens_left,"
                                " _effect_door_opens_left, 'Door'),", "")
    elif mutation == "drop_press_rule":
        source = source.replace("('press_left', _guard_press_left,"
                                " _effect_press_left, 'Button'),", "")
    elif mutation == "break_teleport":
        source = source.replace("LANDMARKS['portal_exit']", "(1, 2)")
    elif mutation == "drop_door_object":
        # As if the Door had never been admitted to the word table at all: it
        # neither renders nor owns a pixel, so (4,5) belongs to nobody.
        source = source.replace("    if state.Door_present:\n"
                                "        r, c = state.Door_pos\n"
                                "        grid[r][c] = state.Door_colour\n",
                                "", 1)
        source = source.replace("    if state.Door_present:\n"
                                "        r, c = state.Door_pos\n"
                                "        if owner[r][c] is not None:\n"
                                "            contested.append(((r, c), "
                                "owner[r][c], 'Door'))\n"
                                "        owner[r][c] = 'Door'\n",
                                "", 1)
    mutant = tmp_path / "theory_mutant.py"
    mutant.write_text(source, encoding="utf-8")

    report = replay.certify(str(mutant), TRACE)
    assert not report["green"], "mutation %r went undetected" % mutation
    assert expect in report["anomaly_kinds"], report["anomaly_kinds"]


@needs_generated
def test_simultaneous_rule_semantics():
    """press_left and door_opens_left must both fire on the same transition.

    They share a guard, and `press_left` invalidates it.  Reading guards against
    the updated state would silently leave the Door shut — the bug this test
    exists to keep fixed.
    """
    theory = _load(os.path.join(GENERATED, "theory.py"))
    state = theory.initial_state()
    state.Cart_pos = (3, 3)
    assert set(theory.fired(state, ("push", "Cart", "left"))) == {
        "press_left", "door_opens_left"}
    nxt = theory.step(state, ("push", "Cart", "left"))
    assert nxt.Button_colour == 8
    assert nxt.Door_present is False
    assert nxt.Cart_pos == (3, 3), "the Cart does not move when it presses"


@needs_generated
def test_no_two_rules_claim_one_object_anywhere():
    """Constraint 9, checked over the manual's whole state space."""
    theory = _load(os.path.join(GENERATED, "theory.py"))
    problem = problem_mod.derive(TRACE, "a0-base")
    base = theory.initial_state()
    for cell in problem.arena:
        for colour in (7, 8):
            for present in (True, False):
                state = base.copy()
                state.Cart_pos = tuple(cell)
                state.Button_colour = colour
                state.Door_present = present
                for direction in ("up", "down", "left", "right"):
                    theory.step(state, ("push", "Cart", direction))  # raises if not


# ------------------------------------------------------------------ M4 plan

@needs_generated
def test_plan_is_sat_and_the_world_agrees():
    report = json.load(open(os.path.join(ARTIFACTS, "plan_generated.json"),
                            encoding="utf-8"))
    assert report["status"] == "SAT"
    assert report["manual_reaches_goal"] and report["world_reaches_goal"]
    assert report["execution_mismatches"] == []
    assert report["length"] == 12


# ------------------------------------------------------------- M5 unsolvable

@needs_generated
def test_variant_is_unsat_with_a_certificate():
    report = json.load(open(os.path.join(ARTIFACTS, "unsolvable_report.json"),
                            encoding="utf-8"))
    assert report["plan"]["status"] == "UNSAT"
    assert report["zero_space"]["in_recovered_space"]
    assert report["zero_space"]["region_size"] == 23
    assert report["theorem"]["explanation"].strip()
    assert report["theorem"]["probe"] == "passed"


def test_the_variant_really_is_unsolvable():
    """Independent of the manual: enumerate the world itself."""
    world = a0_world.A0World(a0_world.NO_BUTTON)
    assert not any(world.is_win(s) for s in world.reachable())
    solvable = a0_world.A0World(a0_world.BASE)
    assert any(solvable.is_win(s) for s in solvable.reachable())


# --------------------------------------------------------------- Lean layer

@pytest.mark.skipif(lean_check.find_lean() is None,
                    reason="no Lean toolchain (see DECISIONS.md D-A0-012)")
@pytest.mark.parametrize("directory,target", [
    (GENERATED, "inv_all"),
    (GENERATED_NB, "unsolvable"),
])
def test_lean_proofs_are_axiom_free(directory, target):
    path = os.path.join(directory, "theory.lean")
    if not os.path.exists(path):
        pytest.skip("run `python run_all.py` first")
    report = lean_check.check(path)
    assert report["green"], report
    names = {r["name"]: r["axioms"] for r in report["axiom_reports"]}
    assert target in names
    assert names[target] == [], "native_decide would show up right here"


@needs_generated
def test_lean_uses_decide_not_native_decide():
    for directory in (GENERATED, GENERATED_NB):
        path = os.path.join(directory, "theory.lean")
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        assert "native_decide" not in text
        assert "sorry" not in text
