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
import re
import sys
from collections import deque
from unittest import mock
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
        assert item.truth["state_space"]["naive_enumeration_feasible"] is True
        assert item.truth["search_credible"] is True


def test_class_ii_bound_is_recorded_and_enormous(paper):
    items = [i for i in paper.items if i.truth["class"] == "large_unsolvable"]
    assert len(items) >= 4
    for item in items:
        space = item.truth["state_space"]
        assert space["naive_enumeration_feasible"] is False
        assert space["enumerated"] is None
        assert space["lower_bound"] > V.LARGE_SPACE_THRESHOLD
        assert space["lower_bound"] > 10 ** 12
        assert space["lower_bound"] == 2 ** space["m"]
        assert "2^%d" % space["m"] in space["arithmetic"]
        # This assertion was briefly removed by D-EX-022, on the argument that
        # the `(cart, button)` quotient decides these levels so a searcher's
        # claim is true. The argument is false -- the quotient ignores
        # `step_limit` and carries no latch state -- and the decision was
        # withdrawn. The assertion is back, and the quotient is kept as a
        # recorded measurement that is explicitly not a search space. D-EX-027.
        assert item.truth["search_credible"] is False
        assert space["positional_states"] < 10 ** 4
        assert "NOT a sound abstraction" in space["quotient_note"]
        # The record must not be readable as an enumeration that ran and came
        # back clean. It used to say `"truncated": False` beside
        # `"enumerated": None`. D-EX-028.
        assert space["enumeration_attempted"] is False
        assert space["truncated"] is None


def test_class_ii_levels_actually_truncate_the_enumerator(paper):
    """The premise `_large_space` derives its refusal from, measured.

    `_large_space` does not time an enumeration -- a timeout would not carry the
    claim (engine-rig D-024) and running one on every build costs seconds for a
    result the constructive bound already fixes. So it *derives* "a forward
    enumeration under this cap cannot terminate" from 2^m exceeding the cap.
    That derivation has a premise -- that the bound is sound on this level --
    and this test checks it against the enumerator itself rather than trusting
    it. Without this, the honest-looking record would rest on exactly the kind
    of unmeasured assertion the field rename was about. D-EX-028.

    Scoped by the *record*, not by the class. `_large_space` is called by seven
    items, not the four class (ii) ones -- the three `solvable_hard` items carry
    the same claim, and scoping this test to `large_unsolvable` would have left
    three unmeasured records behind exactly the check written to catch them.
    Measured: all seven truncate, none finds a solution inside the cap, ~5 s.
    """
    items = [i for i in paper.items
             if i.truth["state_space"]["naive_enumeration_feasible"] is False]
    assert len(items) == 7, "expected 4 class (ii) + 3 solvable_hard"
    assert {i.truth["class"] for i in items} == {"large_unsolvable",
                                                 "solvable_hard"}
    for item in items:
        level = RV.Level(json.loads(item.truth["level_blob"]))
        result = RV.enumerate_states(level, cap=RV.MAX_ENUMERATION)
        assert result["truncated"] is True, (
            "%s: the enumerator terminated under the cap, so the record's "
            "refusal to enumerate is unfounded and its lower bound is wrong"
            % item.item_id)
        assert result["states"] >= RV.MAX_ENUMERATION
        # It must run out of room, not run into the answer. A solvable_hard
        # item whose plan turned up inside the cap would mean the naive method
        # does work here, which is the opposite of what the record claims.
        assert result["solution"] is None, item.item_id
        # And the counterweight, so the two numbers stay on the record together:
        # what the naive method cannot finish, a quotient walk settles at once.
        assert item.truth["state_space"]["positional_states"] < 10 ** 4


@pytest.mark.parametrize("family,build_level,states_of,m_of", [
    # Constructor AND operator, because the operator is part of the family:
    # orchard's forbidden LEFT is exactly what takes m from 2k to 2(k-1).
    # measured == closed form, at every k, with nothing fitted.
    ("gantry",
     lambda k: V.variant_of(V.comb_room("gantry", k, None), "gantry",
                            remap={"LEFT": "RIGHT", "RIGHT": "LEFT"}),
     lambda k: 2 * k * 4 ** k, lambda k: 2 * k),
    ("lattice",
     lambda k: V.variant_of(V.comb_room("lattice", k, 2), "lattice",
                            lost_cells=[[4, 2]]),
     lambda k: 2 * k * 4 ** k, lambda k: 2 * k),
    ("spindle",  # unbudgeted: ii3 ships a step_limit, which binds instead of k
     lambda k: V.comb_open("spindle", k, 1, k),
     lambda k: 2 * k * 4 ** k, lambda k: 2 * k),
    ("orchard",
     lambda k: V.variant_of(V.comb_open("orchard", k, 2, 1), "orchard",
                            forbidden=["LEFT"]),
     lambda k: (2 * 4 ** k - 8) // 3, lambda k: 2 * (k - 1)),
])
def test_the_comb_families_grow_exactly_as_the_bound_extrapolates(
        family, build_level, states_of, m_of):
    """The measurement that licenses extrapolating 2^m to the shipped k=60.

    The shipped bound is arithmetic, never a count: no class (ii) board has ever
    had its states enumerated, and none ever can -- the affordable ceiling on
    this hardware is ~5e6 states against ii1's 2^120 = 1.33e36, and the
    enumerator costs ~473 bytes per state, so 10^12 alone would want ~473 TB.
    What *is* affordable is enumerating the same families at small k and
    checking the growth law they follow.

    Enumerated to completion, `measured == 2k*4^k` for the three comb_room-shaped
    families and `(2*4^k - 8)/3` for orchard, exactly, at every k, with no
    fitting. So 2^m is a true lower bound and a loose one -- by a factor of 2k,
    growing, or 8/3, constant. Extrapolation to k=60 is licensed by the closed
    form being exact wherever it can be checked, not by any count reaching k=60,
    and this test is the check.

    k stops at 6 because that is where the largest family still fits under the
    shipped cap: gantry at k=7 is 229,376 states, past MAX_ENUMERATION. Running
    the ladder to k=9 costs ~128 s and adds one order of magnitude; k<=6 costs
    ~3 s. D-EX-028.

    orchard's m is 2(k-1), not 2k: with LEFT forbidden the two column-1 alcoves
    sit behind the start and are not dippable. That is why shipped ii4 reports
    m=118 rather than 120, and getting it wrong is what makes the ratio look
    like it drifts rather than converging to 8/3.
    """
    kmin = 2 if family in ("lattice", "orchard") else 1
    ratios = []
    for k in range(kmin, 7):
        level = RV.Level(build_level(k))
        bound = V.subset_lower_bound(level)
        assert bound["m"] == m_of(k), "%s k=%d" % (family, k)

        result = RV.enumerate_states(level, cap=RV.MAX_ENUMERATION)
        assert not result["truncated"], (
            "%s k=%d hit the cap; the ladder must stay under it" % (family, k))
        assert result["states"] == states_of(k), (
            "%s k=%d: measured %d, closed form %d"
            % (family, k, result["states"], states_of(k)))
        # The bound is sound at every rung, which is the property that matters.
        assert result["states"] >= bound["lower_bound"]
        ratios.append(result["states"] / bound["lower_bound"])

    if family == "orchard":
        # (8/3)(2^m - 1) / 2^m, converging to 8/3 from below.
        assert ratios[-1] == pytest.approx(8 / 3, abs=0.01)
        assert all(a < b for a, b in zip(ratios, ratios[1:]))
    else:
        # 2k*2^m / 2^m == 2k exactly: the looseness grows without bound.
        assert ratios == [float(2 * k) for k in range(kmin, 7)]


def test_a_board_that_looks_large_but_enumerates_is_not_class_ii():
    """The negative control: big by every surface measure, and enumerable.

    A classifier tried only on true positives has not been tried. This board is
    the widest in the file -- 400 switches on a 200-cell corridor, more of both
    than any shipped class (ii) item -- and a tight step budget means the whole
    reachable set is 6,480 states, enumerated to completion in 0.01 s. It must
    not be classed as class (ii), and the reason it is refused must be the
    constructive bound rather than anything about its size. D-EX-028.
    """
    doc = V.variant_of(V.comb_open("negctl-looks-large", 200, 1, 200),
                       "negctl-looks-large", step_limit=10)
    level = RV.Level(doc)
    assert len(level.switches) == 400
    assert len(level.switches) > 120, "must out-switch every shipped class (ii)"

    result = RV.enumerate_states(level, cap=RV.MAX_ENUMERATION)
    assert result["truncated"] is False
    assert result["states"] == 6480

    bound = V.subset_lower_bound(level)
    assert bound["dippable_switches"] == 400, "it really does look large"
    assert bound["m"] == 4, "the budget, not the switch count, sets m"
    assert bound["lower_bound"] == 16
    assert result["states"] >= bound["lower_bound"]

    with pytest.raises(AssertionError, match="under the"):
        V._large_space(doc)


def test_a_truncating_board_is_still_refused_without_a_bound():
    """The criterion is a conjunction, and this is the half that proves it.

    Criterion (b) -- our own enumerator failing to finish -- is not sufficient
    on its own, and this board shows why it must not be: at a budget of 20 the
    reachable set passes the 200,000 cap and the enumerator truncates, exactly
    as it does on ii1..ii4, yet the constructive bound is only 2^8 = 256 and the
    item is refused. If truncation alone earned the label, a board 30 orders of
    magnitude smaller than ii1 would ship as class (ii) on the strength of a cap
    we chose ourselves. D-EX-028.
    """
    doc = V.variant_of(V.comb_open("negctl-truncates", 200, 1, 200),
                       "negctl-truncates", step_limit=20)
    level = RV.Level(doc)

    result = RV.enumerate_states(level, cap=RV.MAX_ENUMERATION)
    assert result["truncated"] is True, "this board must truncate, like ii1..ii4"

    bound = V.subset_lower_bound(level)
    assert bound["lower_bound"] == 2 ** 8
    assert bound["lower_bound"] < V.LARGE_SPACE_THRESHOLD
    with pytest.raises(AssertionError, match="under the"):
        V._large_space(doc)


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
    """A search claim is paid where it could be true and refused where it cannot.

    D-EX-022 briefly rewrote this test on the argument that the class (ii)
    boards are searchable after all, via their `(cart, button)` quotient. The
    original assertion is restored (D-EX-027), but it does *not* rest on the
    quotient being useless: D-EX-028 measured that the quotient settles every
    shipped class (ii) item, and its unsoundness is one-sided -- an
    over-approximation yields false `solvable`, never false `unsolvable`, so a
    goal in a different component is a sound unsolvability proof, and the key
    itself is computed that way.

    What the refusal rests on is narrower and is the only thing this test
    asserts: `reason: "exhaustive_search"` claims the *naive* method, forward
    enumeration over the full (cart, button, latch mask) state, and that method
    cannot terminate on a class (ii) board -- so the claim is a false statement
    about what the examinee did, whatever cheaper complete method exists. The
    ordering the test also pins -- a certificate always beats a search -- was
    the part of D-EX-022's rewrite worth keeping. D-EX-027, amended by D-EX-028.
    """
    small = next(i for i in paper.items if i.truth["class"] == "small_unsolvable")
    large = next(i for i in paper.items if i.truth["class"] == "large_unsolvable")
    answer = {"claim": "unsolvable", "reason": "exhaustive_search"}

    got = RUBRIC.grade(answer, small.truth, small)
    assert got.detail["reason"] == "search_exhaustion"
    assert got.awarded == pytest.approx(small.points * (0.5 + 0.5 * RV.SEARCH_CREDIT))
    assert got.awarded < small.points

    got_large = RUBRIC.grade(answer, large.truth, large)
    assert got_large.detail["reason"] == "search_not_credible"
    assert got_large.awarded == pytest.approx(large.points * 0.5)

    # A certificate beats a search on both classes, which is the whole of the
    # class (i) ordering and does not depend on board size.
    for item, searched in ((small, got), (large, got_large)):
        certified = RUBRIC.grade(
            {"claim": "unsolvable",
             "certificate": json.loads(item.truth["certificate_blob"])},
            item.truth, item)
        assert certified.awarded > searched.awarded
        assert certified.awarded == item.points


def test_the_quotient_is_recorded_and_is_not_a_search_space(paper):
    """D-EX-022's withdrawal, pinned so it is not re-derived from scratch.

    `positional_states` is a real measurement and a tempting one: 177 to 600
    where `lower_bound` says 2^60 to 2^120. It is not a sound abstraction, and
    the truth file has to say so, because the next reader will otherwise make
    the same inference this run did. D-EX-027.
    """
    for item in paper.items:
        space = item.truth["state_space"]
        assert isinstance(space["positional_states"], int)
        if not space["naive_enumeration_feasible"]:
            assert "NOT a sound abstraction" in space["quotient_note"]
            assert item.truth["search_credible"] is False

    # And the two mechanisms that make it unsound, on levels built from shipped
    # constructors and shipped operators.
    budgeted = RV.Level(V.variant_of(V.comb_open("probe", 6, 1, 6), "probe",
                                     step_limit=12))
    assert V.positional_states(budgeted) == 18
    assert RV.enumerate_states(budgeted, cap=RV.MAX_ENUMERATION)["solution"] is None

    latched = RV.Level(V.variant_of(V.comb_room("probe", 5, 2), "probe",
                                    lost_cells=[[1, 3]]))
    assert latched.require_all_switches is True
    assert V.positional_states(latched) == 25
    assert RV.enumerate_states(latched, cap=RV.MAX_ENUMERATION)["solution"] is None


def test_every_solvable_item_says_where_its_witness_came_from(paper):
    """由构造即知答案 is a claim about the key, so the key has to be checkable.

    `README` said "a computed witness plan" and the module said "computed and
    replayed, not asserted". Neither separates a breadth-first search from a
    construction, and five of the eight solvable witnesses are the former. That
    is not a defect -- a plan that replays and wins proves solvability however
    it was found -- but leaving it unsaid on a paper whose premise is that the
    answer follows from the construction is. D-EX-023.
    """
    solvable = [i for i in paper.items if i.truth["claim"] == "solvable"]
    assert len(solvable) == 8
    sources = [i.truth["witness_source"] for i in solvable]
    assert set(sources) <= {"search", "construction"}
    assert None not in sources
    assert sources.count("search") == 5
    assert sources.count("construction") == 3
    # The three constructed ones are exactly the large-board items, which is the
    # part that matters: where a search was not available, the key did not use
    # one either.
    constructed = {json.loads(i.truth["level_blob"])["level_id"]
                   for i in solvable if i.truth["witness_source"] == "construction"}
    assert constructed == {"lattice"}
    for item in solvable:
        if item.truth["witness_source"] == "construction":
            assert item.truth["state_space"]["naive_enumeration_feasible"] is False


# ------------------------------------------------------------------------
# V5 regressions. Each of these pins a defect that shipped, in the form it
# shipped in, so that a future edit reintroducing it fails the suite rather
# than being found by the next auditor. D-EX-011's precedent.
# ------------------------------------------------------------------------

def _bare_level(level_id, rows, start, goal, **extra):
    doc = {"level_id": level_id, "rows": list(rows), "start": list(start),
           "goal": list(goal), "button": None, "door": None, "portal": None,
           "portal_dest": None, "switches": [], "require_all_switches": False,
           "forbidden": [], "remap": {}, "step_limit": None, "lost_cells": [],
           "win_score_required": 1}
    doc.update(extra)
    return doc


@pytest.mark.parametrize("name,extra,cert", [
    # `_level()` defaults portal_dest to None, so "portal set, destination
    # forgotten" is inside the level shape rather than outside it. `step`
    # returned `portal_dest or target` -- the portal cell itself -- and walked
    # the cart on through; the graph dropped the edge and reported two
    # components. Full marks for a proof that the level is unsolvable, on a
    # level solvable in three commands.
    ("portal_dest_is_none",
     {"portal": [2, 3], "portal_dest": None},
     {"kind": "invariant", "invariant": "cart_region",
      "initial_value": [1, 1], "goal_value": [1, 4]}),
    # Same disagreement, reached without any degenerate value: `step` tests the
    # door before the portal and the graph had no door branch at all.
    ("portal_dest_in_a_wall",
     {"portal": [2, 3], "portal_dest": [1, 3]},
     {"kind": "invariant", "invariant": "cart_region",
      "initial_value": [1, 1], "goal_value": [1, 4]}),
])
def test_a_certificate_is_refused_on_a_level_that_is_actually_solvable(
        name, extra, cert):
    """The over-approximation claim, tested rather than asserted.

    `relaxed_edges`' docstring said it "can never make a solvable level look
    unsolvable, which would hand out points for a false theorem". It could, in
    three ways, because the graph was a second implementation of `Level.step`
    and the two disagreed about the teleport and the door. D-EX-020.
    """
    doc = _bare_level("regression-" + name,
                      ["#######", "#..#..#", "#.SP.G#", "#..#..#", "#######"],
                      (2, 2), (2, 5), **extra)
    level = RV.Level(doc)
    found = RV.enumerate_states(level, cap=RV.MAX_ENUMERATION)
    assert found["solution"] is not None, "the probe level must be solvable"
    assert RV.replay(level, found["solution"])["win"] is True
    result = RV.check_certificate(cert, level)
    assert result["ok"] is False, (
        "a certificate for a false theorem was accepted: %s" % result["why"])


def test_a_cut_set_is_refused_when_the_door_and_the_portal_collide():
    """The third disagreement, and the vacuous-acceptance bug behind it.

    `_check_cut_set` read "the goal is not a node of the graph" as success, so
    once the door/portal collision hid the goal, *any* declared hazard bought a
    full-marks cut set that cut nothing. Both halves are fixed; this pins both.
    """
    doc = _bare_level(
        "regression-door-portal",
        ["########", "#..#.#.#", "#....###", "#.#....#", "#.#...##", "########"],
        (3, 4), (3, 3), button=[1, 4], door=[3, 3], portal=[3, 3],
        portal_dest=[2, 4], lost_cells=[[2, 3], [3, 6]])
    level = RV.Level(doc)
    found = RV.enumerate_states(level, cap=RV.MAX_ENUMERATION)
    assert found["solution"] is not None
    result = RV.check_certificate({"kind": "cut_set", "cells": [[2, 3]]}, level)
    assert result["ok"] is False
    # And the builder would have refused to ship the level in the first place.
    assert any("door and portal" in p for p in level.wellformed_problems())


def test_every_shipped_level_is_wellformed(paper):
    """The second line of defence, on the levels that actually ship."""
    for item in paper.items:
        level = RV.Level(json.loads(item.truth["level_blob"]))
        assert level.wellformed_problems() == []


def test_a_cart_standing_on_the_button_still_counts_the_teleport_jump():
    """The defect this run introduced and an adversarial review of it found.

    Excluding the button from `passable` was right for the movement graph and
    wrong for `row_col_deltas`, which was using `passable` to ask a different
    question: not "where can the cart rest" but "where can the cart be standing
    when it issues a command". The cart can start on the button. On a board
    where the button is the teleport's only entry, the jump's row delta vanished,
    `cart_row` looked monotone, and a level solvable in ONE command was paid
    2.0 of 2.0 for a certificate saying it is unsolvable. D-EX-027.
    """
    doc = _bare_level("regression-button-start",
                      ["####", "#..#", "##.#", "####"], (1, 1), (2, 2),
                      button=[1, 1], portal=[1, 2], portal_dest=[2, 2],
                      forbidden=["UP", "DOWN"])
    level = RV.Level(doc)
    assert RV.replay(level, ["RIGHT"])["win"] is True
    rows, _cols = RV.row_col_deltas(level)
    assert rows == {0, 1}, "the teleport's row delta is missing from the closure"
    result = RV.check_certificate(
        {"kind": "invariant", "invariant": "cart_row",
         "initial_value": 1, "goal_value": 2}, level)
    assert result["ok"] is False
    # And the builder refuses the level, so it cannot reach a sheet at all.
    assert any("starts on the button" in p for p in level.wellformed_problems())


def test_a_duplicated_switch_is_refused_by_the_builder():
    """`switch_index` collapses duplicates; anything counting the list does not.

    Not reachable from `comb_open`/`comb_room`, so nothing shipped is affected,
    but it makes `subset_lower_bound` claim more states than the level has and
    it is exactly the hand-transcription hazard Phase 4 will meet. D-EX-027.
    """
    doc = _bare_level("regression-dup-switch",
                      ["######", "#..#.#", "#.##.#", "######"], (2, 4), (2, 1),
                      switches=[[1, 2], [1, 4], [1, 4]])
    level = RV.Level(doc)
    assert len(level.switch_index) < len(level.switches)
    assert any("repeats a cell" in p for p in level.wellformed_problems())


def test_the_bound_itself_refuses_a_duplicated_switch():
    """The test above asserts what `wellformed_problems` says, not what the
    bound does -- and its own docstring names the consequence it does not check.

    Measured before the fix, on a shipped constructor: `comb_open` with its
    switch list replaced by 60 copies of one cell gave `m=60` and a lower bound
    of 2^60 = 1.15e18 on a board with **359** reachable states, an overstatement
    of 3.2e15. Neither the lane premise nor `LARGE_SPACE_THRESHOLD` refused it.
    The only guard that did was `wellformed_problems`, reached from
    `_self_check` at the end of `build()` -- after all seven `_large_space`
    calls had already written their records. A bound that survives only because
    a caller three frames away happens to check is not a bound. D-EX-028.
    """
    doc = V.comb_open("regression-dup-bound", 60, 1, 60)
    doc["switches"] = [[1, 1] for _ in range(60)]
    level = RV.Level(doc)
    # The premise that fails is distinctness of latch bits, not the lane.
    assert len(level.switch_index) == 1 and len(level.switches) == 60
    with pytest.raises(AssertionError, match="distinct cells"):
        V.subset_lower_bound(level)
    with pytest.raises(AssertionError, match="distinct cells"):
        V._large_space(doc)


def test_a_duplicate_outside_the_bounded_prefix_still_yields_a_bound():
    """The guard is gated on `candidates[:m]`, and this is why.

    A repeated entry naming an impassable cell never becomes a dip candidate,
    so it never enters the 2^m family and the bound over the real alcoves stays
    sound. A coarser guard keyed on `level.switches` would refuse this board,
    which would be a false refusal: the arithmetic it rejects is correct.
    """
    doc = V.comb_open("regression-dup-offprefix", 20, 1, 20)
    clean = V.subset_lower_bound(RV.Level(doc))
    doc["switches"] = list(doc["switches"]) + [[0, 0], [0, 0]]
    level = RV.Level(doc)
    assert len(level.switch_index) < len(level.switches)
    assert not level.passable((0, 0)), "the added entries must be off-board wall"
    noisy = V.subset_lower_bound(level)
    assert noisy["m"] == clean["m"]
    assert noisy["lower_bound"] == clean["lower_bound"]


def _straddle_board(corridor=24, start_col=12, step_limit=25):
    """`comb_open` plus two shipped operators, with the start INSIDE the span of
    the dip sources. Every shipped item starts at the corridor end instead."""
    haz = ([[1, c] for c in range(2, corridor + 1, 2)]
           + [[3, c] for c in range(2, corridor + 1, 2)])
    return V.variant_of(V.comb_open("straddle", corridor, start_col, 1),
                        "straddle", lost_cells=haz, step_limit=step_limit)


def test_an_interior_start_does_not_buy_the_straight_line_cost():
    """The third premise, and the one two guards did not cover (D-EX-029).

    `dist(c_m) + 2m` is the true cost of the walk only when the start lies
    *outside* the span of the dip sources -- true of every shipped item
    (`start_col=1`) and assumed of all boards. With an interior start the m
    nearest sources straddle it, no single walk to c_m touches the ones behind,
    and the shorthand omits the backtrack.

    Measured before the fix, on this board: m=10, a published 2^10, and **758** of
    those 1024 latch masks actually reachable -- with `wellformed_problems()`
    empty, the lane guard passing, the duplicate guard passing, `_large_space`
    accepting, and the published `arithmetic` describing a walk costing 137
    commands against a budget of 99. The number stayed a true lower bound; the
    justification did not, on the class graded on justification.

    So this pins the discrimination rather than the number: the sweep affords 8,
    the shorthand would have claimed 10, and the two must not agree here.
    """
    level = RV.Level(_straddle_board())
    bound = V.subset_lower_bound(level)
    assert bound["m"] == 8, "the sweep affords 8 dips on this board"

    # What the withdrawn shorthand would have allowed, computed the way the old
    # loop did. If this ever equals the sweep's m, the board has stopped
    # straddling and the test has stopped testing anything.
    reach = V.position_paths(level, level.start)
    dists = sorted(len(reach[s]) for s in
                   (V._dip_source(level, reach, sw) for sw in level.switches)
                   if s is not None and s in reach)
    shorthand = 0
    for index, distance in enumerate(dists, start=1):
        if distance + 2 * index > level.step_limit:
            break
        shorthand = index
    assert shorthand > bound["m"], (
        "this board must be one where the shorthand over-charges the budget "
        "less than the real sweep does, or it is not the regression board")


def test_the_straddle_board_is_refused_rather_than_shipped():
    """The same shape at the scale that used to clear the threshold.

    Before D-EX-029 this board reached m=40, `lower_bound` 2^40 = 1.0995e12 --
    over `LARGE_SPACE_THRESHOLD` -- so `_large_space` accepted it and wrote a
    class (ii) record whose justification described a walk the budget could not
    buy. It must now fall under the threshold and be refused.
    """
    doc = _straddle_board(corridor=60, start_col=30, step_limit=99)
    bound = V.subset_lower_bound(RV.Level(doc))
    assert bound["m"] == 29
    assert bound["lower_bound"] < V.LARGE_SPACE_THRESHOLD
    with pytest.raises(AssertionError, match="under the"):
        V._large_space(doc)


def test_the_published_arithmetic_names_a_cost_the_budget_affords():
    """The `arithmetic` string is published in the shipped truth key, so a false
    cost clause in it is a false claim in an artefact, not a stale comment. It
    used to read "at a cost of dist + 2m commands" -- a formula, unevaluated, and
    the wrong one. It now carries the measured sweep, which must fit the budget.
    """
    doc = V.variant_of(V.comb_open("spindle-cost", 200, 1, 200),
                       "spindle-cost", step_limit=150)
    bound = V.subset_lower_bound(RV.Level(doc))
    assert "dist + 2m" not in bound["arithmetic"]
    assert "sweep to the far end" in bound["arithmetic"]
    match = re.search(r"at a cost of (\d+) commands", bound["arithmetic"])
    assert match, "the cost clause must publish a number, not a formula"
    assert int(match.group(1)) <= 150, "and the budget must afford it"


def test_a_bound_under_the_enumeration_cap_may_not_claim_the_cap():
    """`enumeration_refused_because` asserts the bound is "past the cap", and
    nothing checked it: it held only because `MAX_ENUMERATION` (200,000) happens
    to sit below `LARGE_SPACE_THRESHOLD` (10^12). Neither constant's docstring
    stated the ordering as a requirement, so raising the cap above the threshold
    left the record still publishing "past the cap of ..." -- a false sentence
    about the arithmetic printed directly beside it.
    """
    doc = V.variant_of(V.comb_open("spindle-cap", 200, 1, 200),
                       "spindle-cap", step_limit=150)
    assert V._large_space(doc)["naive_enumeration_feasible"] is False

    with mock.patch.object(V, "MAX_ENUMERATION", 10 ** 40):
        with pytest.raises(AssertionError, match="does not exceed the enumeration cap"):
            V._large_space(doc)


def test_the_subset_bound_refuses_a_board_it_does_not_fit():
    """`subset_lower_bound` was unsound off the strict comb, and said nothing.

    A shipped constructor (`comb_open`) plus a shipped operator
    (`observation_loss` on the corridor) produced m=60, a claimed 2^60, and
    `exhaustive_feasible: False` (the old name of the field, D-EX-028) on a
    level with 29,791 reachable states. The
    bound counted each dip in isolation and never checked the lane walked
    between dips. D-EX-021.
    """
    base = V.comb_open("regression-comb", 30, 1, 30)
    lvl = V.variant_of(base, "regression-comb",
                       lost_cells=[[2, c] for c in range(2, 31)])
    with pytest.raises(AssertionError, match="not demonstrated"):
        V.subset_lower_bound(RV.Level(lvl))


def test_the_subset_bound_refuses_a_corridor_made_of_switches():
    """The other falsifier: every corridor cell is itself a latching switch.

    Walking between two dips then latches switches the subset did not choose,
    so the reachable masks are the m prefixes rather than the 2^m subsets.
    """
    width = 12
    rows = ["#" * width,
            "#" + "s" * (width - 2) + "#",
            "#" + "s" * (width - 2) + "#",
            "#" + "s" * (width - 2) + "#",
            "#" * width]
    switches = [[r, c] for r in (1, 2, 3) for c in range(1, width - 1)]
    lvl = _bare_level("regression-chainlink", rows, (1, 1), (3, width - 2),
                      switches=switches, require_all_switches=True)
    with pytest.raises(AssertionError, match="not demonstrated"):
        V.subset_lower_bound(RV.Level(lvl))


def test_the_shipped_class_ii_levels_still_pass_the_lane_precondition(paper):
    """The precondition must refuse the falsifiers and accept the paper."""
    for item in paper.items:
        space = item.truth["state_space"]
        if space["naive_enumeration_feasible"]:
            continue
        bound = V.subset_lower_bound(RV.Level(json.loads(item.truth["level_blob"])))
        assert bound["lower_bound"] == space["lower_bound"]
        assert bound["m"] >= 60


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


# ------- negative control: an UNFIXED concurrency defect, pinned so it cannot
# ------- change quietly.  See RUN_STATE.md and ADVERSARIAL.md (claim 5) in
# ------- exam/runs/20260728T151000Z-V7-exam-stress-fanout/.

@pytest.mark.xfail(strict=True, reason=(
    "UNFIXED DEFECT, pinned deliberately: verdict._emit_spec writes 17 spec "
    "files into the shared, tracked, non-temporary exam/artifacts/variant_specs/ "
    "with model.write_json, whose open(path, 'w') truncates on open, and then "
    "reads each one straight back with Variant.load(path) at verdict.py:479. "
    "Two concurrent verdict.build() calls race: 6 workers x 12 builds produced "
    "2 JSONDecodeErrors, and pytest exam/tests/test_selftest.py under 4 "
    "concurrent builders failed 1 of 34. NOT fixed here: the fix has to decide "
    "whether SPEC_DIR should be per-process at all, and that is its own item. "
    "strict=True on purpose: whichever way it is fixed -- validating the spec "
    "text in memory, or writing and reading a private path -- this XPASSes, the "
    "suite goes red, and the writeup has to be re-derived."))
def test_a_concurrent_builder_cannot_hand_emit_spec_an_empty_spec(tmp_path,
                                                                 monkeypatch):
    """The race, reproduced without a race.

    A real concurrency test would be flaky, and a flaky strict-xfail is worse
    than no test.  So the interleaving is injected instead of waited for: the
    shared spec path is truncated at the exact moment `Variant.load` opens it,
    which is what a competing `verdict.build()` does when it reaches
    `open(path, "w")` a few microseconds earlier.  Everything happens under
    `tmp_path`; the tracked specs under `exam/artifacts/variant_specs/` are
    never touched, because leaving a committed artefact zero bytes long is the
    damage this test exists to describe.
    """
    from proxy.variants import Variant

    source = os.path.join(V.SPEC_DIR, "a2var-i1-atrium-nodown.json")
    with open(source, "r", encoding="utf-8") as handle:
        spec = json.load(handle)

    monkeypatch.setattr(V, "SPEC_DIR", str(tmp_path))
    shared = os.path.join(str(tmp_path), "%s.json" % spec["variant_id"])

    original_load = Variant.load

    def load_while_a_competitor_truncates(path):
        if os.path.exists(shared):
            with open(shared, "w", encoding="utf-8"):
                pass                       # the competing builder's open(..., "w")
        return original_load(path)

    monkeypatch.setattr(Variant, "load",
                        staticmethod(load_while_a_competitor_truncates))

    emitted = V._emit_spec(spec)
    assert emitted["variant_id"] == spec["variant_id"]
