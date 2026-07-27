"""Tests for the four follow-ups: `semantics:`, concept accounts, A0-prime, FD.

Kept separate from `test_a0.py` so that the original spike's suite stays exactly
what it was when `cold-start-a0-m6-report` was tagged.
"""

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import _bootstrap  # noqa: F401,E402

from certify import lean_check  # noqa: E402
from world.ground_truth import read_trace  # noqa: E402

ARTIFACTS = os.path.join(ROOT, "artifacts")
GENERATED = os.path.join(ROOT, "theory", "generated")
PRIME = os.path.join(ROOT, "prime")
PRIME_ARTIFACTS = os.path.join(PRIME, "artifacts")

needs_generated = pytest.mark.skipif(
    not os.path.exists(os.path.join(GENERATED, "theory.py")),
    reason="run `python run_all.py` first",
)
needs_artifacts = pytest.mark.skipif(
    not os.path.exists(os.path.join(ARTIFACTS, "candidates.jsonl")),
    reason="run `python run_all.py` first",
)
needs_prime = pytest.mark.skipif(
    not os.path.exists(os.path.join(PRIME_ARTIFACTS, "prime_report.json")),
    reason="run `python -m prime.run_prime` first",
)


# ------------------------------------------------ 1 · the semantics dialect

def test_every_manual_declares_its_semantics():
    from compile.dialect import parse_semantics
    for path in (os.path.join(ROOT, "theory", "theory.dsl"),
                 os.path.join(ROOT, "theory", "theory_no_button.dsl"),
                 os.path.join(PRIME, "theory", "theory_prime.dsl")):
        semantics = parse_semantics(open(path, encoding="utf-8").read())
        assert semantics.frame == "persist"
        assert semantics.conflict == "exclusive"
        assert semantics.cascade == "single_frame"
        assert len(semantics.rendering()) == 3


def test_a_manual_without_semantics_is_rejected_not_defaulted():
    """The whole point of E-03: silence must be an error, not an assumption."""
    from compile.dialect import SemanticsError, parse_semantics
    text = open(os.path.join(ROOT, "theory", "theory.dsl"), encoding="utf-8").read()
    stripped = "\n".join(
        line for line in text.splitlines()
        if not line.startswith("semantics:")
        and not line.strip().startswith(("frame ", "conflict ", "cascade "))
    )
    with pytest.raises(SemanticsError):
        parse_semantics(stripped)


@pytest.mark.parametrize("bad", [
    "semantics:\n  frame sideways\n  conflict exclusive\n  cascade single_frame\n",
    "semantics:\n  frame persist\n  conflict maybe\n  cascade single_frame\n",
    "semantics:\n  frame persist\n  conflict exclusive\n  cascade eventually\n",
    "semantics:\n  frame persist\n  cascade single_frame\n",
    "semantics:\n  frame persist\n  conflict priority: only_one\n"
    "  cascade single_frame\n",
])
def test_semantics_values_are_a_closed_set(bad):
    from compile.dialect import SemanticsError, parse_semantics
    with pytest.raises(SemanticsError):
        parse_semantics(bad)


def test_backend_refuses_what_it_does_not_implement():
    from compile.dialect import Semantics, SemanticsError, check_backend_support
    check_backend_support(Semantics("persist", "exclusive", "single_frame"))
    for bad in (Semantics("reset", "exclusive", "single_frame"),
                Semantics("persist", "exclusive", "multi_frame"),
                Semantics("persist", "priority", "single_frame", ["a", "b"])):
        with pytest.raises(SemanticsError):
            check_backend_support(bad)


@needs_generated
def test_generated_forms_carry_the_declared_semantics():
    py = open(os.path.join(GENERATED, "theory.py"), encoding="utf-8").read()
    assert "'frame': 'persist'" in py
    lean = open(os.path.join(GENERATED, "theory.lean"), encoding="utf-8").read()
    assert "Declared semantics: frame persist" in lean
    md = open(os.path.join(GENERATED, "theory.md"), encoding="utf-8").read()
    assert "How a Turn Works" in md


# -------------------------------------- 3 · responsibility-complete accounts

@needs_artifacts
def test_concept_accounts_price_the_right_alternative():
    from pipeline.concept_account import NAME_BY_COLOUR, accounts
    rows = accounts(os.path.join(ARTIFACTS, "candidates.jsonl"),
                    os.path.join(ROOT, "theory", "theory.dsl"), NAME_BY_COLOUR)
    by_name = {a.name: a for a in rows}
    assert set(by_name) == {"Cart", "Button", "Door"}
    assert by_name["Cart"].script_delta > 0
    assert by_name["Button"].script_delta < 0        # still does not pay
    for account in rows:
        assert account.verdict == "mandatory", account.reason
        assert account.laws_naming_it or account.rules_targeting_it


@needs_artifacts
def test_responsibility_baseline_is_kinder_than_the_old_one():
    """The old baseline charged the object a declaration and its alternative
    none.  Correcting that has to move both accounts up."""
    from pipeline.concept_account import NAME_BY_COLOUR, accounts
    rows = accounts(os.path.join(ARTIFACTS, "candidates.jsonl"),
                    os.path.join(ROOT, "theory", "theory.dsl"), NAME_BY_COLOUR)
    by_name = {a.name: a for a in rows}
    assert by_name["Button"].script_delta > -17
    assert by_name["Door"].script_delta > -13


# ---------------------------------------------------------- 2 · A0-prime

def test_prime_toggle_is_reversible_from_every_direction():
    from prime.world import a0p_world as P
    world = P.A0PWorld(P.BASE)
    toggles = 0
    for state in world.reachable():
        for action in P.ACTIONS:
            nxt = world.step(state, action)
            if nxt.switch_on != state.switch_on:
                toggles += 1
                assert world.step(nxt, action).switch_on == state.switch_on
    assert toggles >= 8, "every direction should toggle, both ways"


def test_prime_explorer_leaves_holes_by_budget_not_by_tuning():
    from prime.world import a0p_world as P
    from prime.world.explorer import (BUDGET_FRACTION, budget_for,
                                      coverage_report, explore)
    assert BUDGET_FRACTION == 0.40
    states, actions = explore(P.BASE)
    report = coverage_report(P.BASE, states, actions)
    assert report["budget"] == budget_for(P.BASE)
    assert report["covered_pairs"] < report["state_action_pairs"]
    witnessed = report["mechanisms_witnessed"]
    assert witnessed.get("step") and witnessed.get("teleport")
    for direction in ("UP", "DOWN", "LEFT", "RIGHT"):
        assert witnessed.get("toggle_on_%s" % direction), direction
        assert witnessed.get("toggle_off_%s" % direction), direction
    # and the holes the budget did leave, which nothing was tuned for
    assert report["mechanisms_never_witnessed"].get("blocked_by_crate")


@needs_prime
def test_reidentification_merges_a_returning_object():
    from engines.mdl_segmenter.costs import CostModel
    from pipeline import segment_operators as so
    from pipeline.board import extract_board, object_layer
    from pipeline.engines_stage import background_color
    from pipeline.reidentify import reidentify

    frames, _a, _w = read_trace(os.path.join(PRIME_ARTIFACTS, "raw_trace.jsonl"))
    board = extract_board(frames)
    background = background_color(board, frames)
    layer = object_layer(frames, board, background=background)
    raw = so.segment_with("connected_components(4)+uniform_color", layer, background)
    assert len(raw.tracks) > 3, "the Door fragments before re-identification"
    merged, report = reidentify(raw, CostModel(9, 9, max_objects=len(raw.tracks)))
    assert report.applied
    assert len(merged.tracks) == 3
    assert report.script_bits_after < report.script_bits_before


@needs_prime
def test_prime_run_a_is_perfect_on_half_the_coverage():
    report = json.load(open(os.path.join(PRIME_ARTIFACTS, "prime_report.json"),
                            encoding="utf-8"))
    trace = report["trace"]["a0p-base"]
    assert trace["covered_pairs"] < trace["state_action_pairs"] * 0.6
    run_a = report["run_a"]
    assert run_a["certify_cheap"]["green"]
    assert run_a["score_vs_truth"]["accuracy"] == 1.0
    assert run_a["coverage_probes"]["untested_rules"] == []
    assert run_a["plan"]["status"] == "SAT" and run_a["plan"]["world_reaches_goal"]
    assert report["engines"]["executable_probes"] >= 10


@needs_prime
def test_prime_run_b_repairs_a_replay_invisible_error():
    """The controlled answer to A0_REPORT §6.1."""
    report = json.load(open(os.path.join(PRIME_ARTIFACTS, "prime_report.json"),
                            encoding="utf-8"))
    run_b = report["run_b"]
    assert run_b["certify_cheap"] is True, "the seed must be invisible to replay"
    assert "ArenaEscape" in run_b["certify_lean"]
    assert run_b["coverage_probes"]["refuted"] == ["push_onto_crate"]
    assert run_b["score_vs_truth_before"]["accuracy"] < 1.0
    assert run_b["score_vs_truth_after"]["accuracy"] == 1.0
    assert run_b["revisions"] == 1


@needs_prime
def test_prime_lean_is_axiom_free():
    lean = os.path.join(PRIME, "theory", "generated", "theory.lean")
    if lean_check.find_lean() is None or not os.path.exists(lean):
        pytest.skip("no Lean toolchain")
    result = lean_check.check(lean)
    assert result["green"], result
    assert all(not r["axioms"] for r in result["axiom_reports"])


# ------------------------------------------- 4 · the Fast Downward code path

@needs_generated
def test_fd_code_path_needs_no_caller_changes():
    """Discovery, invocation, `sas_plan` parsing and validation, via a stand-in.

    Says nothing about Fast Downward's search — see `certify/fd_conformance.py`
    and STATUS.md's Fast Downward blocker.
    """
    from certify import fd_conformance
    result = fd_conformance.check(os.path.join(GENERATED, "domain.pddl"),
                                  os.path.join(GENERATED, "problem.pddl"))
    assert result["discovery"]["ok"]
    assert result["backend_reported"], "solve() must pick FD with no prefer= hint"
    assert result["same_length"] and result["same_plan"]
    assert result["green"]


# ----------------------------------------- 4b · the REAL Fast Downward path

def test_fd_unsat_tells_a_proof_apart_from_a_crash():
    """The distinction constraint 6 turns on, and the one fd_adapter loses."""
    from certify.fd_unsat import classify, is_unsat
    assert is_unsat(RuntimeError("no plan exists for gripper"))          # stub
    assert is_unsat(RuntimeError(
        "Fast Downward produced no plan file (exit 12): ..."))           # FD
    # 13 is "my search was incomplete and found nothing" -- not a proof.
    assert not is_unsat(RuntimeError(
        "Fast Downward produced no plan file (exit 13): ..."))
    assert not is_unsat(RuntimeError("Fast Downward produced no plan file (exit 1)"))
    assert not is_unsat(RuntimeError("segmentation fault"))
    assert classify(RuntimeError("no plan exists")) == "unsat"
    assert classify(RuntimeError(
        "produced no plan file (exit 13)")) == "error(exit 13)"


def test_generated_pddl_declares_every_type_it_uses():
    """FD's translator dies on a supertype that is never introduced (D-A0-019)."""
    import re
    for directory in (GENERATED,
                      os.path.join(ROOT, "theory", "generated_no_button"),
                      os.path.join(PRIME, "theory", "generated")):
        path = os.path.join(directory, "domain.pddl")
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        block = re.search(r"\(:types(.*?)\)", text, re.S).group(1)
        declared, used = set(), set()
        for line in block.splitlines():
            if "-" not in line:
                continue
            names, _, parent = line.partition("-")
            declared.update(names.split())
            used.add(parent.strip())
        assert used <= declared | {"object"}, (
            "%s uses %r as a supertype without declaring it"
            % (path, used - declared - {"object"}))


@pytest.mark.skipif(
    not os.path.exists(os.path.join(ROOT, "artifacts", "fd_real.json")),
    reason="no real Fast Downward run recorded; see BLOCKER_FAST_DOWNWARD.md",
)
def test_real_fast_downward_agrees_with_the_stub():
    report = json.load(open(os.path.join(ROOT, "artifacts", "fd_real.json"),
                            encoding="utf-8"))
    checked = [i for i in report["instances"] if "skipped" not in i]
    assert len(checked) == 3
    by_name = {i["instance"]: i for i in checked}
    assert by_name["a0-base"]["fast_downward"]["length"] == 12
    assert by_name["a0p-base"]["fast_downward"]["length"] == 10
    # The one that matters: FD must PROVE the variant unsolvable, or the
    # impossibility theorem is arguing with the planner.
    assert by_name["a0-no-button"]["fast_downward"]["status"] == "UNSAT"
    for instance in checked:
        assert instance["same_status"] and instance["same_length"], instance
        assert instance["green"], instance
