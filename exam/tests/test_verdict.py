"""Tests for the verdict paper (Theoria.md 1.11, question type 4).

Two of these tests deliberately do not use the builder's own machinery.

`_independent_step` is a second implementation of the A2-family transition
function, written from `cold-start-a2/a2world/a2_world.py`'s prose rather than
from `exam.grading.rubrics_verdict`, and `test_independent_stepper_matches_a2world`
anchors it to the real A2 world over every (state, action) pair of the base
board.  Every class (iii) witness is then replayed through *that*, and every
class (i) verdict is re-derived by a BFS over *that*.  The reason is narrow: the
builder computes the witness plans and the state counts, so a test that replays
them with the builder's own replay tests that the builder agrees with itself.
The truth of an exam's answer key is the one thing that cannot be established
that way.

The other tests are ordinary: determinism, leakage, spec validity against
`proxy.variants.Variant`, the four calibration examinees, and a set of
plausible-but-invalid certificates that the checker has to refuse.
"""

from __future__ import annotations

import json
import os
import sys
from collections import deque
from typing import Any, Dict, Sequence

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam import leakage                                    # noqa: E402
from exam.grading import rubrics_verdict as RV              # noqa: E402
from exam.guard import no_network                           # noqa: E402
from exam.model import Report, Submission, canonical, unanswered  # noqa: E402
from exam.papers import verdict as V                        # noqa: E402

RUBRIC = RV.RUBRICS[0]
DIGEST_STUB = "0" * 64


# --------------------------------------------------------------- fixtures

@pytest.fixture(scope="module")
def paper():
    with no_network():
        return V.build()


@pytest.fixture(scope="module")
def key(paper):
    return paper.key(DIGEST_STUB)


def mark_locally(paper, key_doc, mode: str) -> Report:
    """Mark without `exam.grading.registry`.

    The registry imports all four question types' rubric modules and hashes
    them, so it is hostage to three sibling files this agent does not own and
    must not create. Importing our rubric directly is the documented fallback;
    `test_registry_if_available` exercises the real path when it happens to be
    importable.
    """
    answers = V.reference_answers(paper, key_doc, mode)
    scores = []
    for item in paper.items:
        if item.item_id not in answers:
            scores.append(unanswered(item))
            continue
        scores.append(RUBRIC.grade(answers[item.item_id], item.truth, item))
    report = Report(paper.paper_id, mode, "verdict", DIGEST_STUB, scores)
    submission = Submission(mode, paper.paper_id, answers)
    report.axes = V.axes(report, key_doc, submission)
    return report


# ------------------------------------- an independent copy of the dynamics

ACTIONS = ("UP", "DOWN", "LEFT", "RIGHT")
DELTA = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}


def _independent_step(level: Dict[str, Any], cart, pressed, action):
    """A2's transition function, rewritten from GROUND_TRUTH.md's rule table.

    push / blocked / press / teleport, in that reading order. Deliberately not
    imported from the module under test.
    """
    rows = level["rows"]
    dr, dc = DELTA[action]
    target = (cart[0] + dr, cart[1] + dc)
    if not (0 <= target[0] < len(rows) and 0 <= target[1] < len(rows[0])):
        return cart, pressed
    if rows[target[0]][target[1]] == "#":
        return cart, pressed
    button = level.get("button")
    if button is not None and list(target) == list(button):
        return cart, True
    door = level.get("door")
    if door is not None and list(target) == list(door):
        return (target, pressed) if pressed else (cart, pressed)
    portal = level.get("portal")
    if portal is not None and list(target) == list(portal):
        dest = level["portal_dest"]
        return (dest[0], dest[1]), pressed
    return target, pressed


def _independent_replay(level: Dict[str, Any], plan: Sequence[str]) -> bool:
    """Does this command sequence win, under the wrapper the level declares?"""
    forbidden = set(level.get("forbidden", ()))
    remap = dict(level.get("remap", {}))
    limit = level.get("step_limit")
    lost = {tuple(c) for c in level.get("lost_cells", ())}
    switches = [tuple(c) for c in level.get("switches", ())]
    index = {c: i for i, c in enumerate(switches)}
    need_all = bool(level.get("require_all_switches")) and bool(switches)
    goal = tuple(level["goal"])

    cart = tuple(level["start"])
    pressed = False
    latched = set()
    if cart in index:
        latched.add(index[cart])
    if cart in lost:
        return False
    for step, command in enumerate(plan, start=1):
        assert command in ACTIONS, "witness contains a non-command %r" % (command,)
        if command in forbidden:
            return False
        if limit is not None and step > limit:
            return False
        cart, pressed = _independent_step(level, cart, pressed,
                                          remap.get(command, command))
        if cart in index:
            latched.add(index[cart])
        if cart in lost:
            return False
        if cart == goal and (not need_all or len(latched) == len(switches)):
            return True
    return False


def _independent_search(level: Dict[str, Any], cap: int = 200_000):
    """Complete forward search over the declared state space, capped.

    Only ever called on class (i) levels -- which is the point of class (i)
    being class (i). Returns (solvable, states_seen, hit_cap).
    """
    forbidden = set(level.get("forbidden", ()))
    remap = dict(level.get("remap", {}))
    limit = level.get("step_limit")
    lost = {tuple(c) for c in level.get("lost_cells", ())}
    switches = [tuple(c) for c in level.get("switches", ())]
    index = {c: i for i, c in enumerate(switches)}
    need_all = bool(level.get("require_all_switches")) and bool(switches)
    goal = tuple(level["goal"])
    commands = [a for a in ACTIONS if a not in forbidden]

    start_mask = frozenset({index[tuple(level["start"])]} if tuple(level["start"]) in index else ())
    start = (tuple(level["start"]), False, start_mask, 0)
    seen = {start[:3]}
    queue = deque([start])
    while queue:
        cart, pressed, mask, depth = queue.popleft()
        if limit is not None and depth >= limit:
            continue
        for command in commands:
            nxt, nxt_pressed = _independent_step(level, cart, pressed,
                                                 remap.get(command, command))
            if nxt in lost:
                continue
            nxt_mask = mask | ({index[nxt]} if nxt in index else set())
            nxt_mask = frozenset(nxt_mask)
            if nxt == goal and (not need_all or len(nxt_mask) == len(switches)):
                return True, len(seen), False
            if (nxt, nxt_pressed, nxt_mask) in seen:
                continue
            if len(seen) >= cap:
                return False, len(seen), True
            seen.add((nxt, nxt_pressed, nxt_mask))
            queue.append((nxt, nxt_pressed, nxt_mask, depth + 1))
    return False, len(seen), False


def test_independent_stepper_matches_a2world():
    """Anchor the test's own stepper to `cold-start-a2`'s A2 world.

    Read-only import of the reference world over every (cart, pressed, action)
    triple of the base board. If this passes, the independent replay and the
    independent search below are checking the real A2 semantics rather than a
    private reinvention of them.
    """
    a2_dir = os.path.join(REPO, "cold-start-a2")
    if not os.path.isdir(a2_dir):
        pytest.skip("cold-start-a2 is not present in this checkout")
    if a2_dir not in sys.path:
        sys.path.insert(0, a2_dir)
    from a2world.a2_world import BASE, A2World, State   # noqa: E402

    world = A2World(BASE)
    level = V.a2_echo()
    compared = 0
    for r in range(len(level["rows"])):
        for c in range(len(level["rows"][0])):
            if level["rows"][r][c] == "#":
                continue
            for pressed in (False, True):
                for action in ACTIONS:
                    theirs = world.step(State(cart=(r, c), pressed=pressed), action)
                    mine = _independent_step(level, (r, c), pressed, action)
                    assert mine == (theirs.cart, theirs.pressed), (
                        "divergence at %s %s %s" % ((r, c), pressed, action))
                    compared += 1
    assert compared == 304, compared     # 38 floor cells x 2 button states x 4 actions


# ------------------------------------------------------------ determinism

def test_build_is_deterministic(paper):
    with no_network():
        again = V.build()
    assert canonical(paper.sheet(DIGEST_STUB)) == canonical(again.sheet(DIGEST_STUB))
    assert canonical(paper.key(DIGEST_STUB)) == canonical(again.key(DIGEST_STUB))
    assert [i.item_id for i in paper.items] == [i.item_id for i in again.items]


def test_spec_files_are_byte_identical_across_builds(paper):
    before = _spec_bytes(paper)
    with no_network():
        V.build()
    after = _spec_bytes(paper)
    assert before == after
    assert len(before) == len(paper.items)


def _spec_bytes(paper) -> Dict[str, bytes]:
    out = {}
    for item in paper.items:
        path = os.path.join(REPO, item.truth["spec"]["spec_file"])
        with open(path, "rb") as handle:
            out[item.truth["spec"]["variant_id"]] = handle.read()
    return out


def test_build_opens_no_socket():
    with no_network():
        V.build()


# ------------------------------------------------- the specs are specs

def test_every_spec_is_accepted_by_proxy_variants(paper):
    """The other track's validator is the only opinion that counts here.

    A spec our own code accepts proves our code agrees with itself. `Variant`
    is the frozen contract, and a spec it refuses is not a question.
    """
    from proxy.variants import LEGAL_OPERATORS, Variant

    seen = set()
    for item in paper.items:
        record = item.truth["spec"]
        path = os.path.join(REPO, record["spec_file"])
        variant = Variant.load(path)
        assert variant.variant_id == record["variant_id"]
        assert variant.sha256 == record["spec_sha256"]
        assert variant.base_game == "a2"
        assert variant.claim in ("solvable", "unsolvable", "unchanged")
        assert len(variant.justification) >= 40
        assert variant.operators
        for op in variant.operators:
            assert op["op"] in LEGAL_OPERATORS
        seen.add(variant.variant_id)
    assert len(seen) == len(paper.items)


def test_spec_claim_matches_the_truth(paper):
    for item in paper.items:
        path = os.path.join(REPO, item.truth["spec"]["spec_file"])
        spec = json.load(open(path, encoding="utf-8"))
        assert spec["claim"] == item.truth["claim"], item.item_id


def test_all_five_wrapper_operators_are_exercised(paper):
    from proxy.variants import LEGAL_OPERATORS

    used = set()
    for item in paper.items:
        path = os.path.join(REPO, item.truth["spec"]["spec_file"])
        for op in json.load(open(path, encoding="utf-8"))["operators"]:
            used.add(op["op"])
    assert used == set(LEGAL_OPERATORS), (
        "the frozen library is the deliverable; an operator never exercised in "
        "the rehearsal is one whose first use is on a sealed game. missing: %s"
        % sorted(set(LEGAL_OPERATORS) - used))


# ---------------------------------------------------------------- leakage

def test_leakage_is_clean(paper):
    sheet = paper.sheet(DIGEST_STUB)
    answer_of = {i.item_id: i.truth["claim"] for i in paper.items}
    report = leakage.check_paper(paper, sheet, answer_of=answer_of)
    assert report["probe_hits"] == 0
    assert report["structural_hits"] == 0
    assert report["probes_declared"] >= 4 * len(paper.items)
    positional = report["positional"]
    assert not positional["clustered_by_answer"]
    assert positional["order_runs"] >= len(paper.items) // 2


def test_the_sheet_never_names_a_class_or_a_spec(paper):
    """The class name *is* the answer for two of the three classes."""
    text = canonical(paper.sheet(DIGEST_STUB))
    for forbidden in ("small_unsolvable", "large_unsolvable", "solvable_hard",
                      "variant_spec", "a2var-", "certificate_blob", "level_blob"):
        assert forbidden not in text, forbidden
    for item in paper.items:
        assert item.truth["spec"]["variant_id"] not in text
        assert item.truth["class"] not in " ".join(item.tags)
        assert item.truth["class"] not in item.item_id


def test_item_ids_are_opaque(paper):
    for item in paper.items:
        assert item.item_id.startswith("vq-")
        assert len(item.item_id) == 13
        assert json.loads(item.truth["level_blob"])["level_id"] not in item.item_id


# ------------------------------------------------- the three classes hold

def test_class_i_is_actually_small_and_actually_unsolvable(paper):
    """Re-derive the verdict with a search this file wrote.

    Class (i)'s premise is that a complete searcher answers correctly here. If
    that were false the class would not exist, and if we only checked it with
    the builder's own enumerator we would not know.
    """
    items = [i for i in paper.items if i.truth["class"] == "small_unsolvable"]
    assert len(items) >= 4
    for item in items:
        level = json.loads(item.truth["level_blob"])
        solvable, states, capped = _independent_search(level)
        assert not capped, item.item_id
        assert not solvable, "%s is claimed unsolvable and is not" % item.item_id
        assert states < 5000, item.item_id
        assert item.truth["state_space"]["exhaustive_feasible"] is True
        assert item.truth["search_credible"] is True


def test_class_ii_bound_is_recorded_and_enormous(paper):
    items = [i for i in paper.items if i.truth["class"] == "large_unsolvable"]
    assert len(items) >= 4
    for item in items:
        space = item.truth["state_space"]
        assert space["exhaustive_feasible"] is False
        assert space["enumerated"] is None
        assert space["lower_bound"] > V.LARGE_SPACE_THRESHOLD
        assert space["lower_bound"] > 10 ** 12
        assert space["lower_bound"] == 2 ** space["m"]
        assert "2^%d" % space["m"] in space["arithmetic"]
        assert item.truth["search_credible"] is False


def test_class_ii_bound_is_constructive_not_asserted(paper):
    """Spot-check the 2^m argument by building two of the subsets.

    The bound says distinct subsets of the dippable switches give distinct
    reachable states. Take two subsets, drive them with the independent
    stepper, and check the latch sets really differ and the cart really ends in
    the same place -- which is the whole argument, at m = 2.
    """
    item = next(i for i in paper.items if i.truth["class"] == "large_unsolvable"
                and json.loads(i.truth["level_blob"])["level_id"] == "gantry")
    level = json.loads(item.truth["level_blob"])
    outcomes = []
    for dips in (["UP", "DOWN"], ["DOWN", "UP"]):
        cart, pressed = tuple(level["start"]), False
        latched = set()
        switches = {tuple(c): n for n, c in enumerate(level["switches"])}
        for command in dips:
            cart, pressed = _independent_step(level, cart, pressed, command)
            if cart in switches:
                latched.add(switches[cart])
        outcomes.append((cart, frozenset(latched)))
    assert outcomes[0][0] == outcomes[1][0] == tuple(level["start"])
    assert outcomes[0][1] != outcomes[1][1]
    assert len(outcomes[0][1]) == len(outcomes[1][1]) == 1


def test_class_iii_witnesses_actually_win(paper):
    """Replay every witness with the independently written stepper."""
    items = [i for i in paper.items if i.truth["class"] == "solvable_hard"]
    assert len(items) >= 6
    for item in items:
        level = json.loads(item.truth["level_blob"])
        plan = item.truth["witness"]
        assert plan, item.item_id
        assert len(plan) == item.truth["witness_length"]
        assert _independent_replay(level, plan), (
            "%s (%s) claims solvable and its witness does not win"
            % (item.item_id, level["level_id"]))


def test_class_iii_is_long_enough_to_trap_a_shallow_searcher(paper):
    plans = [i.truth["witness_length"] for i in paper.items
             if i.truth["class"] == "solvable_hard"]
    assert max(plans) > 250, "no witness is long enough to be a trap"
    assert sum(1 for n in plans if n > 90) >= 4


def test_solvable_and_unsolvable_boards_overlap(paper):
    """The board must carry no signal about the answer."""
    by_level: Dict[str, set] = {}
    for item in paper.items:
        level_id = json.loads(item.truth["level_blob"])["level_id"]
        by_level.setdefault(level_id, set()).add(item.truth["claim"])
    both = [k for k, v in by_level.items() if len(v) == 2]
    assert len(both) >= 2, ("at least two boards must appear with both answers, "
                            "or board identity is a free answer: %s" % by_level)
    sizes = {}
    for item in paper.items:
        sizes.setdefault(item.truth["board_size_class"], set()).add(item.truth["claim"])
    assert sizes["small"] == {"solvable", "unsolvable"}
    assert sizes["large"] == {"solvable", "unsolvable"}


# ------------------------------------------------------ the calibrations

def test_oracle_scores_everything(paper, key):
    report = mark_locally(paper, key, "oracle")
    assert report.fraction == 1.0
    assert report.axes["confusion"]["sensitivity"] == 1.0
    assert report.axes["confusion"]["specificity"] == 1.0
    counts = report.axes["reason_quality"]["counts"]
    assert counts.get("certificate") == 9
    assert counts.get("witness") == 8
    assert "search_exhaustion" not in counts


def test_null_scores_nothing(paper, key):
    report = mark_locally(paper, key, "null")
    assert report.awarded == 0.0
    assert report.fraction == 0.0
    assert all(s.verdict == "unanswered" for s in report.scores)


def test_memoriser_is_competent_on_small_and_collapses_on_large(paper, key):
    report = mark_locally(paper, key, "memoriser")
    by_board = report.axes["by_board_size"]
    assert by_board["small"]["fraction"] == 1.0
    assert by_board["large"]["fraction"] == 0.0
    assert by_board["large"]["n"] >= 6
    by_class = report.axes["by_class"]
    assert by_class["small_unsolvable"]["fraction"] == 1.0
    assert by_class["large_unsolvable"]["fraction"] == 0.0
    assert 0.4 < report.fraction < 0.8


#: The number the paper exists to produce. A bluffer that answers "unsolvable"
#: to everything has perfect recall on the unsolvable items and is worthless;
#: if this threshold ever has to be raised, the rubric started paying for
#: confidence and the paper is broken.
BLUFFER_CEILING = 0.30


def test_bluffer_has_perfect_sensitivity_no_specificity_and_a_bad_score(paper, key):
    report = mark_locally(paper, key, "bluffer")
    matrix = report.axes["confusion"]
    assert matrix["sensitivity"] == 1.0
    assert matrix["specificity"] == 0.0
    assert matrix["fp"] == 8 and matrix["tn"] == 0
    assert report.fraction < BLUFFER_CEILING
    # 9 of 34, not 9 of 42: the solvable items used to be worth 3 against 2, and
    # a cheater subagent read the whole claim half off `points` because of it.
    # The weights are uniform now. The anti-bluffer property did not depend on
    # them -- there are 9 unsolvable items to 8 solvable, and half of every
    # item's marks are the reason, which a bluffer never earns.
    assert report.fraction == pytest.approx(9.0 / 34.0, abs=1e-5)
    # every point it got is a verdict point; it justified nothing.
    assert report.axes["reason_quality"]["counts"] == {"none": 17}
    assert report.axes["reason_quality"]["certified_share_of_correct_unsolvable"] == 0.0


def test_confusion_is_always_reported(paper, key):
    for mode in ("oracle", "null", "memoriser", "bluffer"):
        axes = mark_locally(paper, key, mode).axes
        assert "confusion" in axes
        assert "sensitivity" in axes["confusion"]
        assert "specificity" in axes["confusion"]
        assert "reason_quality" in axes


def test_said_is_set_on_every_answered_item(paper, key):
    """`confusion` reads `detail["said"]`; without it every item looks abstained."""
    report = mark_locally(paper, key, "oracle")
    for score in report.scores:
        assert score.detail["said"] in ("solvable", "unsolvable")


# ------------------------------------------------- the certificate checker

def _find(paper, **want):
    """The one item matching every field, by variant id suffix.

    Looked up by the spec's variant id rather than by board and claim: the same
    board carries several items and the sheet order is a shuffle, so "the first
    atrium item that is unsolvable" is two different items on two different
    runs. A test that depends on shuffle order is a test that will lie later.
    """
    suffix = want["spec"]
    matches = [i for i in paper.items
               if i.truth["spec"]["variant_id"].startswith("a2var-%s-" % suffix)]
    assert len(matches) == 1, "%s matched %d items" % (suffix, len(matches))
    return matches[0]


def _level_of(paper, spec: str) -> RV.Level:
    return RV.Level(json.loads(_find(paper, spec=spec).truth["level_blob"]))


def test_checker_refuses_free_text(paper):
    level = _level_of(paper, "i2")
    for junk in ("the cart can never go up, so the goal is unreachable",
                 ["cart_row", 5, 1], 42, None,
                 {"kind": "prose", "text": "I proved it"},
                 {"kind": "invariant", "invariant": "vibes",
                  "initial_value": 5, "goal_value": 1}):
        result = RV.check_certificate(junk, level)
        assert not result["ok"], junk


def test_checker_refuses_an_extra_field(paper):
    """A certificate carrying its own prose alongside the arithmetic is the
    free-text checker this grammar exists to not be."""
    level = _level_of(paper, "i2")
    good = {"kind": "invariant", "invariant": "cart_row",
            "initial_value": 5, "goal_value": 1}
    assert RV.check_certificate(good, level)["ok"]
    padded = dict(good, explanation="every move is downward or sideways")
    result = RV.check_certificate(padded, level)
    assert not result["ok"]
    assert "key set" in result["why"]


def test_checker_refuses_a_plausible_but_wrong_invariant(paper):
    """The one a careless examinee actually writes.

    On the atrium with DOWN forbidden the cart's row IS monotone -- it can only
    decrease -- so `cart_row` looks like the right instrument and the stated
    values are the true ones. It is still not a proof: the goal is *above* the
    start, which is the direction the invariant permits. The real argument is
    the partition, and the checker has to tell the two apart.
    """
    level = _level_of(paper, "i1")
    assert "DOWN" in level.forbidden
    bogus = {"kind": "invariant", "invariant": "cart_row",
             "initial_value": 5, "goal_value": 2}
    result = RV.check_certificate(bogus, level)
    assert not result["ok"]
    assert "non-increasing" in result["why"]
    honest = {"kind": "invariant", "invariant": "cart_region",
              "initial_value": V._region_rep(level.doc, "start"),
              "goal_value": V._region_rep(level.doc, "goal")}
    assert RV.check_certificate(honest, level)["ok"]


def test_checker_refuses_a_cut_set_that_does_not_cut(paper):
    """The near-twin of the cistern item: same operator, cells that miss.

    Every cell named here IS a declared hazard, so the cheap half of the check
    passes. The level is nevertheless solvable, and the checker only finds that
    out by recomputing connectivity without them -- which is the difference
    between a checker and a plausibility filter.
    """
    level = _level_of(paper, "iii3")
    hazards = sorted(level.lost_cells)
    assert len(hazards) == 3
    result = RV.check_certificate(
        {"kind": "cut_set", "cells": [list(c) for c in hazards]}, level)
    assert not result["ok"]
    assert "does not separate" in result["why"]


def test_checker_refuses_a_cut_set_of_non_hazards(paper):
    level = _level_of(paper, "i3")
    assert RV.check_certificate({"kind": "cut_set", "cells": [[3, 5]]}, level)["ok"]
    result = RV.check_certificate({"kind": "cut_set", "cells": [[3, 5], [1, 1]]},
                                  level)
    assert not result["ok"]
    assert "not declared hazards" in result["why"]


def test_checker_refuses_an_inflated_counting_bound(paper):
    item = _find(paper, spec="i4")
    level = RV.Level(json.loads(item.truth["level_blob"]))
    honest = json.loads(item.truth["certificate_blob"])
    assert honest["kind"] == "counting"
    assert RV.check_certificate(honest, level)["ok"]
    inflated = dict(honest, bound=honest["bound"] + 1)
    result = RV.check_certificate(inflated, level)
    assert not result["ok"]
    assert "not a lower bound" in result["why"]
    wrong_limit = dict(honest, limit=honest["limit"] + 1)
    assert not RV.check_certificate(wrong_limit, level)["ok"]


def test_a_certificate_does_not_transplant(paper):
    """A certificate that is valid somewhere is not valid everywhere."""
    source = _find(paper, spec="i3")
    cert = json.loads(source.truth["certificate_blob"])
    assert cert["kind"] == "cut_set"
    others = [i for i in paper.items if i.item_id != source.item_id
              and i.truth["claim"] == "unsolvable"]
    refused = 0
    for item in others:
        level = RV.Level(json.loads(item.truth["level_blob"]))
        if not RV.check_certificate(cert, level)["ok"]:
            refused += 1
    assert refused == len(others)


# --------------------------------------------------------- rubric behaviour

def test_a_right_verdict_with_no_reason_scores_only_the_verdict(paper):
    item = next(i for i in paper.items if i.truth["claim"] == "unsolvable")
    score = RUBRIC.grade({"claim": "unsolvable"}, item.truth, item)
    assert score.verdict == "correct"
    assert score.awarded == pytest.approx(item.points * 0.5)
    assert score.detail["reason"] == "none"


def test_search_exhaustion_is_partial_on_small_and_worthless_on_large(paper):
    small = next(i for i in paper.items if i.truth["class"] == "small_unsolvable")
    large = next(i for i in paper.items if i.truth["class"] == "large_unsolvable")
    answer = {"claim": "unsolvable", "reason": "exhaustive_search"}

    got = RUBRIC.grade(answer, small.truth, small)
    assert got.detail["reason"] == "search_exhaustion"
    assert got.awarded == pytest.approx(small.points * (0.5 + 0.5 * RV.SEARCH_CREDIT))
    assert got.awarded < small.points

    got = RUBRIC.grade(answer, large.truth, large)
    assert got.detail["reason"] == "search_not_credible"
    assert got.awarded == pytest.approx(large.points * 0.5)


def test_a_certificate_beats_a_search_on_the_same_item(paper):
    """Class (i) in one assertion: same verdict, different answer, different mark."""
    item = next(i for i in paper.items if i.truth["class"] == "small_unsolvable")
    certified = RUBRIC.grade(
        {"claim": "unsolvable",
         "certificate": json.loads(item.truth["certificate_blob"])},
        item.truth, item)
    searched = RUBRIC.grade({"claim": "unsolvable", "reason": "exhaustive_search"},
                            item.truth, item)
    bare = RUBRIC.grade({"claim": "unsolvable"}, item.truth, item)
    assert certified.awarded > searched.awarded > bare.awarded
    assert certified.awarded == item.points
    assert all(s.verdict == "correct" for s in (certified, searched, bare))


def test_a_bad_witness_scores_only_the_verdict(paper):
    item = next(i for i in paper.items if i.truth["claim"] == "solvable")
    score = RUBRIC.grade({"claim": "solvable", "witness": ["UP", "UP", "UP"]},
                         item.truth, item)
    assert score.verdict == "correct"
    assert score.detail["reason"] == "invalid_witness"
    assert score.awarded == pytest.approx(item.points * 0.5)


def test_abstention_is_neither_right_nor_wrong(paper):
    item = next(i for i in paper.items if i.truth["claim"] == "unsolvable")
    score = RUBRIC.grade({"claim": "abstain"}, item.truth, item)
    assert score.verdict == "abstained"
    assert score.awarded == 0.0
    assert score.detail["said"] == "abstain"


def test_a_bare_string_answer_is_accepted(paper):
    """The bluffer submits one, and a rubric that could not read it would
    silently score the bluffer as abstaining -- which is the calibration this
    paper is for."""
    item = next(i for i in paper.items if i.truth["claim"] == "unsolvable")
    score = RUBRIC.grade("unsolvable", item.truth, item)
    assert score.verdict == "correct"
    assert score.detail["said"] == "unsolvable"


def test_witness_length_cap_is_enforced(paper):
    item = next(i for i in paper.items if i.truth["claim"] == "solvable")
    level = RV.Level(json.loads(item.truth["level_blob"]))
    result = RV.replay(level, ["UP"] * (RV.MAX_WITNESS + 1))
    assert result["status"] == "witness_over_cap"


def test_grade_is_pure_in_its_three_arguments(paper):
    """No disk, no world, no examinee identity -- `exam.model.Rubric` says so."""
    item = next(i for i in paper.items if i.truth["claim"] == "unsolvable")
    answer = {"claim": "unsolvable",
              "certificate": json.loads(item.truth["certificate_blob"])}
    first = RUBRIC.grade(answer, item.truth, item)
    second = RUBRIC.grade(json.loads(json.dumps(answer)),
                          json.loads(json.dumps(item.truth)), item)
    assert first.awarded == second.awarded
    assert first.detail["reason"] == second.detail["reason"]


# --------------------------------------------------------------- the shell

def test_paper_declares_the_synthetic_world(paper):
    assert paper.question_type == "verdict"
    assert paper.paper_id == V.PAPER_ID
    assert paper.notes["world"] == "a2"
    assert paper.world["synthetic_worlds"] == ["a0", "a0-prime", "a2"]
    assert paper.world["piles_sha256"].startswith("3feca53e")
    text = canonical(paper.sheet(DIGEST_STUB)) + canonical(paper.key(DIGEST_STUB))
    assert "dc22" not in text.lower()


def test_registry_if_available():
    """Use the real registry when the three sibling modules exist.

    They are owned by other agents working concurrently, so their absence is not
    a failure of this paper -- but when they are present the digest path is the
    one that will actually mark, and it should work.
    """
    try:
        from exam.grading import registry
        digest = registry.digest()
    except Exception as exc:                    # pragma: no cover - timing
        pytest.skip("registry not importable yet (%s); rubrics imported directly"
                    % type(exc).__name__)
    assert len(digest) == 64
    assert registry.rubric(V.RUBRIC_ID).grade is RV.grade_verdict
    assert "exam.grading.rubrics_verdict" in registry.module_digests()
