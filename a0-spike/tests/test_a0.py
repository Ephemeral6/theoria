"""A0 acceptance: the cold-start loop closes, and its verdicts match ground truth."""

import os
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "engine-rig"))

from pipeline import explore, run_a0, stages          # noqa: E402
from world import levels, sokoban2                    # noqa: E402


@pytest.fixture(scope="module")
def report():
    return run_a0.run()


# ------------------------------------------------------------------ the world

def test_the_conservation_law_actually_holds():
    """A push moves the box two cells, so each coordinate's parity survives."""
    for name, level in levels.LEVELS.items():
        cells = sokoban2.reachable_box_cells(level)
        assert len({(r + c) % 2 for r, c in cells}) == 1, name
        assert len({r % 2 for r, c in cells}) == 1, name
        assert len({c % 2 for r, c in cells}) == 1, name


def test_the_two_levels_differ_only_in_the_target():
    assert levels.MATCH.box == levels.MISMATCH.box
    assert levels.MATCH.player == levels.MISMATCH.player
    assert levels.MATCH.walls == levels.MISMATCH.walls
    assert levels.MATCH.target != levels.MISMATCH.target


def test_ground_truth_solvability_is_what_the_design_intended():
    truth = levels.ground_truth()
    assert truth["match"]["solvable"] is True
    assert truth["match"]["optimal_plan_length"] == 2
    assert truth["mismatch"]["solvable"] is False
    assert truth["match"]["parity_matches"] is True
    assert truth["mismatch"]["parity_matches"] is False


# --------------------------------------------------------------- the pipeline

def test_perception_finds_two_movers_and_a_board(report):
    assert report["perceive"]["movers"] == 2
    assert report["perceive"]["board"] >= 3


def test_the_edit_script_beats_the_pixel_baseline(report):
    assert report["perceive"]["script_bits"] < report["perceive"]["baseline_bits"]


def test_push_rules_require_the_box_to_have_somewhere_to_go(report):
    """The under-guarded first pass is the bug; this is the fix (THEORIZE_LOG T-4)."""
    pushes = [r for r in report["mine"]["rules"] if r["name"].startswith("push2")]
    assert len(pushes) == 4
    for rule in pushes:
        direction = rule["name"].split("_")[1]
        assert "ahead_is_box(%s)" % direction in rule["guard"]
        assert "box_beyond_free(%s)" % direction in rule["guard"]
        assert int(rule["coverage"].split("/")[0]) >= 8


def test_walk_rules_are_the_simple_thing(report):
    walks = [r for r in report["mine"]["rules"] if r["name"].startswith("walk")]
    assert len(walks) == 4
    for rule in walks:
        direction = rule["name"].split("_")[1]
        assert sorted(rule["guard"]) == ["act==%s" % direction, "ahead_free(%s)" % direction]


def test_the_blocked_class_needed_more_than_one_conjunction(report):
    """It is genuinely disjunctive; sequential covering is why it is expressible."""
    blocked = [r for r in report["mine"]["rules"] if r["name"].startswith("blocked")]
    assert len(blocked) > 4, "a single rule per direction would mean the split failed"


def test_certify_replays_every_transition_exactly(report):
    certificate = report["certify"]
    assert certificate["transitions"] >= 300
    assert certificate["replay_exact"] is True
    assert certificate["replay_failures"] == []


def test_every_transition_has_exactly_one_successor(report):
    """Constraint 9, on the induced rules."""
    assert report["certify"]["exactly_one_successor"] is True
    assert report["certify"]["ambiguities"] == []


def test_the_conservation_law_is_recovered_from_the_trajectory(report):
    law = report["prove"]
    assert law["row_plus_col_is_conserved"] is True
    assert law["null_space_dimension"] == 2, "both coordinate parities are conserved"


# ------------------------------------------------------------- the two verdicts

def test_the_solvable_level_is_planned_and_won(report):
    entry = report["levels"]["match"]
    assert entry["planner_consulted"] is True
    assert entry["won"] is True
    assert entry["plan_length"] == levels.ground_truth()["match"]["optimal_plan_length"]


def test_the_plan_actually_moves_the_box_onto_the_target(report):
    """Executed in the world, not merely returned by the planner."""
    entry = report["levels"]["match"]
    assert tuple(entry["executed_box_at"]) == levels.MATCH.target


def test_the_unsolvable_level_is_refused_without_search(report):
    """The point of the theorem: no planner is consulted at all."""
    entry = report["levels"]["mismatch"]
    assert entry["theorem"]["unsolvable"] is True
    assert entry["planner_consulted"] is False
    assert entry["theorem"]["goal_breaks_invariant"] is True


def test_both_verdicts_agree_with_ground_truth(report):
    for name, grade in report["grading"].items():
        assert grade["agrees"], name


def test_the_theorem_explains_itself_in_the_manuals_vocabulary(report):
    explanation = report["levels"]["mismatch"]["theorem"]["explanation"]
    assert "奇偶" in explanation
    assert report["levels"]["mismatch"]["theorem"]["invariant"] == "(box.row + box.col) mod 2"


# ------------------------------------------------------------- determinism

def test_the_evidence_set_is_deterministic():
    a = explore.evidence_set(levels.MATCH, per_class=4)
    b = explore.evidence_set(levels.MATCH, per_class=4)
    assert [e["actions"] for e in a["episodes"]] == [e["actions"] for e in b["episodes"]]


def test_mining_is_deterministic():
    evidence = explore.evidence_set(levels.MATCH, per_class=4)
    transitions = stages.transitions_from_episodes(evidence["episodes"])
    first = [r.as_json() for r in stages.mine(transitions)]
    second = [r.as_json() for r in stages.mine(transitions)]
    assert first == second


# ----------------------------- certify through the generated executable form

def test_the_manual_compiles_to_an_executable_form(report):
    assert "theory_exec.py" in report["certify_generated"]["source"]
    assert len(report["certify_generated"]["per_level"]) == 5


def test_history_replays_through_the_compiled_manual(report):
    """The only predictor is the code compiled from theory.dsl."""
    generated = report["certify_generated"]
    assert generated["frames_checked"] >= 300
    assert generated["replay_exact"] is True
    assert generated["n_render_mismatches"] == 0
    assert generated["errors"] == []


def test_replay_compares_rendered_frames_not_internal_state():
    """Full-frame responsibility: a wrong picture must fail even if state is right."""
    from pipeline import gen_exec

    module = _compiled_module()
    state = module["State"](player=levels.MATCH.player, box=levels.MATCH.box)
    frame = state.render()
    assert sum(1 for row in frame for v in row if v) == len(levels.MATCH.walls) + 2


def _compiled_module():
    from pipeline import gen_exec

    level = levels.MATCH
    dsl = open(os.path.join(HERE, "theory", "theory.dsl"), encoding="utf-8").read()
    return gen_exec.compile_module(dsl, level.height, level.width, level.walls)


def test_the_compiled_manual_blocks_at_the_board_edge():
    """The bug the manual had until certify caught it (THEORIZE_LOG T-8)."""
    module = _compiled_module()
    State, step = module["State"], module["step"]
    assert step(State(player=(0, 0), box=(3, 3)), "UP").player == (0, 0)


def test_the_compiled_manual_pushes_the_box_two_cells():
    module = _compiled_module()
    State, step = module["State"], module["step"]
    result = step(State(player=(3, 4), box=(3, 3)), "LEFT")
    assert result.box == (3, 1)
    assert result.player == (3, 3)


def test_the_generator_refuses_what_it_cannot_compile():
    """Never `True`, never `pass` -- an uncompilable theory is a finding."""
    from pipeline.gen_exec import UncompilableTheory, generate

    broken = open(os.path.join(HERE, "theory", "theory.dsl"), encoding="utf-8").read()
    broken = broken.replace("free(ahead(Player, dir))", "sparkles(Player, dir)")
    with pytest.raises(UncompilableTheory):
        generate(broken, 7, 7, levels.MATCH.walls)


# ------------------------------------------------------------------ semantics

def _manual() -> str:
    return open(os.path.join(HERE, "theory", "theory.dsl"), encoding="utf-8").read()


def test_the_manual_declares_all_three_semantic_facts():
    """dsl_grammar v0.2 §semantics: mandatory, and these are the adjudicated values.

    Pinned as literals on purpose. They are claims about *this world*, measured in
    `probes/semantics_probe.py` over 47040 representable state-action pairs, and a
    silent edit to any of them compiles a different world. See THEORIZE_LOG T-11.
    """
    from theory_compiler.parser.theory_parser import parse_theory

    semantics = parse_theory(_manual()).semantics
    assert semantics is not None
    assert semantics.frame == "persist"
    assert semantics.conflict == "exclusive"
    assert semantics.cascade == "single_frame"


@pytest.mark.parametrize("statement, unimplemented", [
    ("frame     persist", "frame     reset"),
    ("conflict  exclusive", "conflict  priority: walk > push2"),
    ("cascade   single_frame", "cascade   multi_frame"),
])
def test_the_generator_refuses_a_semantics_value_it_does_not_implement(
        statement, unimplemented):
    """v0.2 revision item 10, which `gen_pddl` learned the hard way.

    Declaring the fact buys nothing if the backend reads it and encodes a
    different world anyway. Each of these three parses; none is implemented here;
    all three must stop the build rather than compile to `persist` / `exclusive`
    / `single_frame` by default.
    """
    from pipeline.gen_exec import UncompilableTheory, generate

    mutated = _manual().replace(statement, unimplemented)
    assert mutated != _manual(), "the mutation did not apply -- test is vacuous"
    with pytest.raises(UncompilableTheory) as caught:
        generate(mutated, 7, 7, levels.MATCH.walls)
    # `priority: r1 > r2` is normalised to the bare value `priority` by the
    # parser, so the order is not part of what the message has to name.
    value = unimplemented.split()[1].rstrip(":")
    assert value in str(caught.value), "the refusal must name the value it refused"


def test_the_compiled_step_enforces_exclusive_even_when_rules_agree():
    """Two rules firing is a violation whether or not they agree on the answer.

    The earlier `step` compared *successors* and let duplicates through when they
    matched. That passes every test while the guards really are disjoint, which
    is exactly what makes it worth pinning: it reads like enforcement and is not.
    """
    from pipeline import gen_exec

    module = gen_exec.compile_module(
        _manual(), levels.MATCH.height, levels.MATCH.width, levels.MATCH.walls)
    State, step = module["State"], module["step"]
    start = State(player=levels.MATCH.player, box=levels.MATCH.box)

    duplicated = module["RULES"] + [module["RULES"][0]]
    original = list(module["RULES"])
    module["RULES"][:] = duplicated
    try:
        with pytest.raises(RuntimeError, match="conflict exclusive violated"):
            for direction in ("UP", "DOWN", "LEFT", "RIGHT"):
                step(start, direction)
    finally:
        module["RULES"][:] = original


# ----------------------------------------------- held-out and the proof form

def test_the_theory_holds_on_states_it_never_observed(report):
    """Replay-exactness does not imply this. That is the whole point of A0."""
    held = report["held_out"]
    assert held["total_cases"] > 30000
    assert held["total_mismatches"] == 0
    assert held["exact"] is True


def test_push_needs_both_the_crossed_and_the_landing_cell(report):
    """The bug held-out testing found, and replay never could (THEORIZE_LOG T-9)."""
    for rule in report["mine"]["rules"]:
        if not rule["name"].startswith("push2"):
            continue
        direction = rule["name"].split("_")[1]
        assert "box_ahead_free(%s)" % direction in rule["guard"]
        assert "box_beyond_free(%s)" % direction in rule["guard"]


def test_evidence_is_pooled_across_levels(report):
    """One level cannot force every domain rule."""
    assert len(report["explore"]["levels"]) == 5
    assert report["explore"]["transitions"] > 1500


@pytest.mark.skipif(
    __import__("pipeline.cross_form", fromlist=["find_lean"]).find_lean() is None,
    reason="no lean toolchain available",
)
def test_the_lean_proof_checks_and_rests_on_nothing_exotic(report):
    lean = report["lean"]
    assert lean["compiles"] is True
    assert lean["uses_sorry"] is False
    assert lean["sorry_in_source"] is False
    assert lean["non_vacuous"] is True
    assert any("unsolvable" in line and "propext" in line for line in lean["axioms"])


@pytest.mark.skipif(
    __import__("pipeline.cross_form", fromlist=["find_lean"]).find_lean() is None,
    reason="no lean toolchain available",
)
def test_the_lean_and_python_forms_are_the_same_world(report):
    """Same theory, several forms -- checked, not asserted."""
    cross = report["lean_cross_form"]
    assert cross["forms_agree"] is True
    assert cross["n_mismatches"] == 0
    assert cross["cases"] > 9000


# ------------------------------------------- variant injection and adaptation

@pytest.fixture(scope="module")
def adaptation():
    from pipeline import adapt
    return {entry["variant"]: entry for entry in adapt.run_all()["variants"]}


def test_every_variant_changes_exactly_one_rule():
    from pipeline import adapt
    from world.sokoban2 import BASE_RULES
    for variant in adapt.VARIANTS:
        differing = [
            field for field in ("push_distance", "require_crossing_free",
                                "walls_block_player")
            if getattr(variant.rules, field) != getattr(BASE_RULES, field)
        ]
        assert len(differing) == 1, (variant.name, differing)


def test_a_frequently_fired_rule_is_caught_almost_immediately(adaptation):
    """`ghost` weakens walk, which fires constantly."""
    assert adaptation["ghost"]["detection"]["actions_until_surprise"] <= 10


def test_a_rare_guard_change_hides_completely_in_the_base_level(adaptation):
    """`nocross` differs only where the crossed cell is blocked -- unreachable in `match`."""
    assert adaptation["nocross"]["detection"]["detected"] is False


def test_but_the_right_level_finds_it_quickly(adaptation):
    """Detection latency is a property of where you look, not only of the change."""
    across = adaptation["nocross"]["detection_across_levels"]
    assert across["detected_anywhere"] is True
    assert across["earliest"] <= 10
    assert "match" in across["levels_that_never_notice"]


def test_changing_the_push_rule_invalidates_the_theorem_that_depends_on_it(adaptation):
    for name in ("push1", "push3", "nocross"):
        assert adaptation[name]["invalidated_theorems"] == ["unsolvable_mismatch"]
    assert adaptation["ghost"]["invalidated_theorems"] == []


def test_one_variant_actually_flips_the_verdict(adaptation):
    """push1 kills the conservation law and `mismatch` becomes solvable."""
    entry = adaptation["push1"]
    assert entry["conservation_law_still_true"] is False
    assert entry["mismatch_still_unsolvable"] is False
    assert entry["old_verdict_still_correct"] is False
    assert entry["silently_wrong_without_dependency_tracking"] is True


def test_dependency_tracking_is_what_catches_it(adaptation):
    """Without [depends: push2] nothing would force the theorem to be re-examined."""
    entry = adaptation["push1"]
    assert entry["changed_rule"] == "push2"
    assert "unsolvable_mismatch" in entry["invalidated_theorems"]


def test_every_variant_repairs_to_an_exact_theory(adaptation):
    for name, entry in adaptation.items():
        assert entry["repair"]["replay_exact"] is True, name
        assert entry["repair"]["exactly_one_successor"] is True, name


def test_the_repaired_push_effect_matches_the_injected_change(adaptation):
    assert set(adaptation["push1"]["repair"]["push_effects"]) == {
        "(-1, 0)", "(1, 0)", "(0, -1)", "(0, 1)"}
    assert set(adaptation["push3"]["repair"]["push_effects"]) == {
        "(-3, 0)", "(3, 0)", "(0, -3)", "(0, 3)"}
