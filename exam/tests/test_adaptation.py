"""Tests for question type 3 — rule-change adaptation.

Two of these tests are the ones worth reading.

`test_the_memoriser_is_silently_wrong_where_the_verdict_flipped` is the headline.
An arm that replays its history perfectly and has learned nothing else answers
this paper by saying, of every variant, that nothing changed and that the level
named `mismatch` is still impossible. On two of the six variants it *is* now
winnable. The examinee's total is a respectable-looking fraction; the flag is
what condemns it, and the test asserts the flag by name rather than asserting a
number that could drift.

`test_every_variant_agrees_with_a_brute_force_over_the_world` refuses to trust
the generator. Every truth the paper ships is recomputed here by a different
route -- the divergence index from the observations the *sheet* actually carries,
the parity claims from an analytic argument about the travel distance, the
verdict from breadth-first search, the falsified rules from the event labels
`sokoban2.step` returns rather than from a re-implementation of its guards. A
generator checked against itself is checked against nothing.
"""

from __future__ import annotations

import os
import sys
from dataclasses import replace
from typing import Any, Dict, List, Optional

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
EXAM = os.path.dirname(HERE)
REPO = os.path.dirname(EXAM)
for _path in (REPO, os.path.join(REPO, "a0-spike"), os.path.join(REPO, "engine-rig")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from exam import guard, leakage                                  # noqa: E402
from exam.model import (Item, Report, Submission, canonical,     # noqa: E402
                        unanswered)
from exam.papers import adaptation                               # noqa: E402

# The rubrics are taken from the module, not from the registry. The registry
# imports all four question types' rubric modules, and the other three were
# being written concurrently in sibling worktrees while this suite was: a
# suite that fails because a neighbour has not landed yet reports on the
# neighbour, not on this paper. The integration is not skipped, it is a test of
# its own (`test_the_rubrics_register_cleanly_alongside_the_other_types`), which
# skips with a reason when a sibling module is absent.
from exam.grading import rubrics_adaptation as rubrics           # noqa: E402

from world import levels, sokoban2                               # noqa: E402
from world.sokoban2 import BLOCKED, DIRECTIONS, DELTA, MOVE, PUSH, Rules, State  # noqa: E402

RUBRIC_BY_ID = {r.rubric_id: r for r in rubrics.RUBRICS}

_PAPER = None
_KEY = None


def paper():
    """One build for the whole module. `build()` is deterministic; see below."""
    global _PAPER, _KEY
    if _PAPER is None:
        _PAPER = adaptation.build()
        _KEY = _PAPER.key("test-digest")
    return _PAPER


def key_doc():
    paper()
    return _KEY


def mark_locally(examinee_id: str, answers: Dict[str, Any]) -> Report:
    """The marker of `exam.grading.mark`, minus the registry lookup.

    Same contract: an item with no answer is `unanswered` and scores zero,
    every other item is handed (answer, truth, item) and nothing else.
    """
    scores = []
    for item in paper().items:
        if item.item_id not in answers:
            scores.append(unanswered(item))
            continue
        score = RUBRIC_BY_ID[item.rubric_id].grade(
            answers[item.item_id], item.truth, item)
        assert score.verdict in ("correct", "wrong", "abstained", "unanswered")
        assert score.awarded <= score.possible + 1e-9
        scores.append(score)
    return Report(paper().paper_id, examinee_id, "adaptation", "test-digest",
                  scores)


def report_for(mode: str) -> Report:
    answers = adaptation.reference_answers(paper(), key_doc(), mode)
    return mark_locally(mode, answers)


def variant_rows() -> List[Dict[str, Any]]:
    return key_doc()["notes"]["variant_table"]


def rules_of(row: Dict[str, Any]) -> Rules:
    return replace(Rules(), **row["changed_fields"])


# ------------------------------------------------------------- the basics

def test_the_paper_is_the_right_shape():
    p = paper()
    assert p.paper_id == adaptation.PAPER_ID == "p15-adaptation-a0"
    assert p.question_type == "adaptation"
    assert len(p.items) == 60
    assert p.world["world_id"] == "a0-prime"
    assert p.world["base_world_id"] == "a0"
    families = {tag for item in p.items for tag in item.tags
                if tag in ("detect", "describe", "collateral", "repair")}
    assert families == {"detect", "describe", "collateral", "repair"}
    # Collateral carries the most weight in the paper, on purpose.
    total = sum(i.points for i in p.items)
    collateral = sum(i.points for i in p.items if "collateral" in i.tags)
    assert collateral / total > 0.4


def test_two_builds_are_byte_identical():
    first = adaptation.build()
    second = adaptation.build()
    assert canonical(first.sheet("d")) == canonical(second.sheet("d"))
    assert canonical(first.key("d")) == canonical(second.key("d"))


def test_building_the_paper_opens_no_socket():
    with guard.no_network():
        built = adaptation.build()
    assert canonical(built.sheet("d")) == canonical(paper().sheet("d"))


def test_the_world_is_synthetic_and_neither_pile_is_touched():
    assert guard.assert_synthetic_world("a0-prime") == "synthetic"
    assert guard.assert_synthetic_world("a0") == "synthetic"
    text = canonical(paper().sheet("d"))
    piles = guard.load_piles()
    assert piles.sealed_pile, "the cut must actually name a sealed pile"
    for game_id in piles.sealed_pile:
        # Not the id, and not the short id either: a sealed game is not named on
        # a sheet, and `provenance()` publishes only the count of that pile.
        assert game_id not in text
        assert game_id.split("-")[-1] not in text
    # The dev pile is named, and only in the provenance block -- that block is
    # the record of which cut this artefact was built under, and dropping it to
    # make a string search cleaner would trade a real guarantee for a cosmetic
    # one. No item mentions a dev game.
    for item in paper().items:
        for game_id in piles.dev_pile:
            assert game_id not in canonical(item.sheet_side())


# ------------------------------------------------------------------ leakage

def test_the_sheet_does_not_carry_its_own_answers():
    p = paper()
    report = leakage.check_paper(p, p.sheet("test-digest"))
    assert report["probe_hits"] == 0
    assert report["structural_hits"] == 0
    assert report["probes_declared"] > 0
    assert all(item.leak_probes for item in p.items)


def test_the_transparent_variant_names_stay_in_the_truth_file():
    text = canonical(paper().sheet("d"))
    for row in variant_rows():
        assert row["transparent_name"] not in text
        for field in row["changed_fields"]:
            assert field not in text
        assert row["variant"].startswith("v-a0-")
    # ... and they are all present in the key, which is where they belong.
    key_text = canonical(key_doc())
    for row in variant_rows():
        assert row["transparent_name"] in key_text


def test_the_answer_does_not_track_the_item_order():
    p = paper()
    answer_of = {}
    for item in p.items:
        if "collateral" in item.tags:
            answer_of[item.item_id] = item.truth["verdict"]
        elif "single_level" in item.tags:
            answer_of[item.item_id] = ("detected" if item.truth["detected"]
                                       else "never")
    report = leakage.check_paper(p, p.sheet("d"), answer_of=answer_of)
    positional = report["positional"]
    # Built in variant order the paper would be six blocks whose answers move
    # together; `clustered_by_answer` is the check that would catch it.
    assert positional["clustered_by_answer"] is False


# ------------------------------------------------------------ calibration

def test_the_oracle_scores_full_marks_by_construction():
    report = report_for("oracle")
    assert report.fraction == 1.0
    assert all(score.verdict == "correct" for score in report.scores)


def test_the_null_examinee_scores_zero():
    report = report_for("null")
    assert report.awarded == 0.0
    assert all(score.verdict == "unanswered" for score in report.scores)


def test_the_memoriser_is_silently_wrong_where_the_verdict_flipped():
    """The headline demonstration.

    The memoriser answers as if nothing had changed: it never sees a
    divergence, names no change, invalidates nothing, and keeps the old verdict
    on `mismatch`. On the variants where that verdict has flipped, keeping it
    means declaring a winnable level impossible -- exactly what
    `theorem unsolvable_mismatch [depends: push2]` exists to prevent, and
    exactly what every replay check it owns would still pass.
    """
    answers = adaptation.reference_answers(paper(), key_doc(), "memoriser")
    report = mark_locally("memoriser", answers)
    numbers = adaptation.axes(report, key_doc(),
                              Submission("memoriser", paper().paper_id, answers))

    flipped = [row["variant"] for row in variant_rows() if row["verdict_flipped"]]
    assert flipped, "the paper must contain a variant whose verdict flips"
    assert numbers["silently_wrong"] == len(flipped)
    assert numbers["silently_wrong_items"] == sorted(
        "%s.collateral" % v for v in flipped)
    for item_id in numbers["silently_wrong_items"]:
        score = next(s for s in report.scores if s.item_id == item_id)
        assert score.detail["silently_wrong"] is True
        assert score.detail["said"] == rubrics.OLD_VERDICT
        assert score.detail["verdict_flipped"] is True

    # It scores nothing on detect and describe, which is the other half of the
    # point: replay is prediction about the past.
    by_tag = report.by_tag({i.item_id: i.tags for i in paper().items})
    assert by_tag["describe"]["fraction"] == 0.0
    assert by_tag["detect"]["fraction"] < 0.05
    assert report.fraction < 0.25


def test_the_bluffer_answers_everything_and_still_scores_badly():
    answers = adaptation.reference_answers(paper(), key_doc(), "bluffer")
    assert len(answers) == len(paper().items)          # it answers every item
    report = mark_locally("bluffer", answers)
    assert report.fraction < 0.25
    numbers = adaptation.axes(report, key_doc(),
                              Submission("bluffer", paper().paper_id, answers))
    # Perfect sensitivity, no specificity: the arm Theoria.md 1.11 says a
    # verdict paper must not reward.
    assert numbers["mismatch_verdict"]["sensitivity"] == 1.0
    assert numbers["mismatch_verdict"]["specificity"] == 0.0
    # It is never *silently* wrong -- it is loudly wrong, which is a different
    # and much less dangerous failure. The two numbers have to separate them.
    assert numbers["silently_wrong"] == 0
    assert numbers["detect"]["false_alarm"] >= 1
    # Naming the whole registry buys nothing on the set that matters.
    assert numbers["collateral_parts_correct"]["rules"] == 0


def test_the_two_bad_arms_are_told_apart_by_axes_not_by_the_total():
    memoriser = report_for("memoriser")
    bluffer = report_for("bluffer")
    assert abs(memoriser.fraction - bluffer.fraction) < 0.05
    m = adaptation.axes(memoriser, key_doc(), Submission("m", paper().paper_id, {}))
    b = adaptation.axes(bluffer, key_doc(), Submission("b", paper().paper_id, {}))
    assert (m["silently_wrong"], m["detect"]["false_alarm"]) != \
           (b["silently_wrong"], b["detect"]["false_alarm"])


# ---------------------------------------------------- the undetectable one

def test_one_variant_is_undetectable_on_the_base_level():
    """`adapt.py::detection_across_levels`, as an exam item.

    A guard weakening is invisible until you stand somewhere the old and the new
    guard disagree, and `match` makes that configuration unreachable. The truth
    has to say "never here" over a *complete* stream, and has to say where it
    does show, or the item is unanswerable.
    """
    rows = [row for row in variant_rows()
            if row["first_divergence"][levels.MATCH.name] is None]
    assert len(rows) == 1, "exactly one variant should hide on the base level"
    row = rows[0]

    item = next(i for i in paper().items
                if i.item_id == "%s.detect.%s" % (row["variant"], levels.MATCH.name))
    assert item.truth["detected"] is False
    assert item.truth["index"] is None
    # "no divergence in the first 640 of 341" is a sentence with nothing in it.
    assert item.paper["stream"]["complete"] is True

    elsewhere = {k: v for k, v in row["first_divergence"].items() if v is not None}
    assert elsewhere, "undetectable everywhere would be a different finding"
    assert min(elsewhere.values()) <= 16

    # And an examinee that names a step number there earns nothing, however
    # plausible the number.
    plausible = rubrics.grade_detect({"detected": True, "index": min(elsewhere.values())},
                                     item.truth, item)
    assert plausible.awarded == 0.0
    assert plausible.detail["false_alarm"] is True
    honest = rubrics.grade_detect({"detected": False}, item.truth, item)
    assert honest.awarded == item.points


def test_the_undetectable_item_is_not_identifiable_by_the_size_of_its_stream():
    """The one positional signal this paper cannot shuffle away.

    Stream length is the length of the variant's own deterministic exploration,
    which is a genuine observable -- there is no honest way to pad it. So the
    check is not "lengths are equal", it is "length does not single the item
    out": the level where nothing is ever detected must be neither the longest
    nor the shortest stream on the sheet, or a cheater with a ruler passes.
    """
    lengths = {item.item_id: item.paper["stream"]["n_actions"]
               for item in paper().items if "single_level" in item.tags}
    hidden = [item.item_id for item in paper().items
              if "single_level" in item.tags and item.truth["index"] is None]
    assert len(hidden) == 1
    ordered = sorted(lengths.values())
    assert ordered[0] < lengths[hidden[0]] < ordered[-1]


def test_the_caps_never_hide_a_divergence():
    for item in paper().items:
        if "single_level" not in item.tags:
            continue
        stream = item.paper["stream"]
        embedded = sum(len(e["obs"]) for e in item.paper["episodes"])
        assert embedded == stream["n_actions"] <= stream["cap"]
        if item.truth["index"] is None:
            assert stream["complete"] is True
        else:
            assert item.truth["index"] <= embedded


# --------------------------------------------- independent ground truth

def _rule_of(level, state: State, action: str) -> str:
    """Which manual rule governs this transition, derived from the event label.

    Written the other way round from `adaptation._classify`: that one re-derives
    the guard cascade, this one asks `sokoban2.step` what happened and only then
    splits the one case the event label cannot distinguish. Two routes to the
    same name is the point of having it here.
    """
    _nxt, event = sokoban2.step(level, state, action)
    if event == MOVE:
        return "walk"
    if event == PUSH:
        return "push2"
    dr, dc = DELTA[action]
    ahead = (state.player[0] + dr, state.player[1] + dc)
    if ahead != state.box:
        return "blocked_wall"
    distance = level.rules.push_distance
    crossed = [(state.box[0] + dr * k, state.box[1] + dc * k)
               for k in range(1, distance)]
    blocked_crossing = level.rules.require_crossing_free and any(
        not sokoban2.in_bounds(level, c) or sokoban2.is_wall(level, c)
        for c in crossed)
    return "blocked_box_crossing" if blocked_crossing else "blocked_box_landing"


def _all_states(level):
    cells = [(r, c) for r in range(level.height) for c in range(level.width)
             if (r, c) not in level.walls]
    return [State(player=p, box=b) for p in cells for b in cells if p != b]


def _registered_levels():
    return (levels.MATCH, levels.MISMATCH) + levels.CROSSING_LEVELS


def test_every_variant_agrees_with_a_brute_force_over_the_world():
    for row in variant_rows():
        rules = rules_of(row)

        # -- falsified rules, from event labels rather than from guards -------
        hit = set()
        for base in _registered_levels():
            old = replace(base, rules=Rules())
            new = replace(base, rules=rules)
            for state in _all_states(base):
                for action in DIRECTIONS:
                    a, _ = sokoban2.step(old, state, action)
                    b, _ = sokoban2.step(new, state, action)
                    if (a.player, a.box) != (b.player, b.box):
                        hit.add(_rule_of(old, state, action))
                        hit.add(_rule_of(new, state, action))
        assert sorted(hit) == row["rules_falsified"], row["variant"]

        # -- the parity claims, analytically ---------------------------------
        # The box only ever moves `push_distance` cells along one axis, so each
        # of the three parity invariants survives exactly when that distance is
        # even. Nothing else in `Rules` can move it.
        parity_survives = (rules.push_distance % 2 == 0)
        parity_claims = {"box_row_parity", "box_col_parity", "box_parity"}
        broken = parity_claims & set(row["claims_now_false"])
        assert broken == (set() if parity_survives else parity_claims), row["variant"]

        # -- the verdict, by search ------------------------------------------
        mismatch = replace(levels.MISMATCH, rules=rules)
        winnable = sokoban2.solve_bfs(mismatch) is not None
        assert row["mismatch_verdict"] == ("solvable" if winnable else "unsolvable")
        assert ("unsolvable_mismatch" in row["claims_now_false"]) is winnable
        assert row["verdict_flipped"] is winnable

        # -- re-examination is a superset of falsehood, and not the same set --
        assert set(row["claims_now_false"]) <= set(row["claims_to_reexamine"])


def test_the_divergence_index_can_be_recomputed_from_the_sheet_alone():
    """The examinee's own route to the answer, walked here.

    Nothing in this test touches the generator's helpers: it takes the
    observations the sheet ships, predicts each step with the base rules (which
    is what the old manual predicts), and counts.
    """
    by_name = {level.name: level for level in levels.EVIDENCE_LEVELS}
    for item in paper().items:
        if "single_level" not in item.tags:
            continue
        level_name = item.truth["level"]
        base = replace(by_name[level_name], rules=Rules())

        found = None
        seen = 0
        for episode in item.paper["episodes"]:
            predicted = State(player=tuple(episode["start"][0]),
                              box=tuple(episode["start"][1]))
            for action, player, box in episode["obs"]:
                observed = State(player=tuple(player), box=tuple(box))
                predicted, _ = sokoban2.step(base, predicted, action)
                seen += 1
                if (predicted.player, predicted.box) != (observed.player,
                                                         observed.box):
                    found = seen
                    break
                predicted = observed
            if found is not None:
                break
        assert found == item.truth["index"], item.item_id


def test_the_cross_level_truth_is_the_single_level_truths():
    single = {}
    for item in paper().items:
        if "single_level" in item.tags:
            single.setdefault(item.paper["variant"], {})[
                item.truth["level"]] = item.truth["index"]
    for item in paper().items:
        if "across_levels" in item.tags:
            assert item.truth["per_level"] == single[item.paper["variant"]]


def test_the_two_field_variant_is_observationally_a_one_label_change():
    """The composition that the grid found and a hand-written list would not.

    Shortening the travel distance to one cell leaves no crossed cells, so
    dropping the crossing rule changes nothing anyone can observe. The truth for
    "what changed" is the one-label answer, and this test proves the premise the
    hard way: the full transition tables are equal.
    """
    rows = [row for row in variant_rows() if len(row["changed_fields"]) > 1]
    assert rows, "the grid must produce at least one composition"
    vacuous = [row for row in rows if len(row["change_labels"]) == 1]
    assert len(vacuous) == 1
    row = vacuous[0]

    twin = replace(Rules(), **{k: v for k, v in row["changed_fields"].items()
                               if k == "push_distance"})
    full = rules_of(row)
    for base in _registered_levels():
        one, two = replace(base, rules=twin), replace(base, rules=full)
        for state in _all_states(base):
            for action in DIRECTIONS:
                a, _ = sokoban2.step(one, state, action)
                b, _ = sokoban2.step(two, state, action)
                assert (a.player, a.box) == (b.player, b.box)

    item = next(i for i in paper().items if i.item_id == "%s.describe" % row["variant"])
    over_claim = rubrics.grade_describe(
        {"labels": sorted(set(row["change_labels"]) | {"chg-box-crosses-blocked"})},
        item.truth, item)
    assert over_claim.awarded == 0.0


def test_the_repair_budget_is_the_number_the_protocol_actually_spends():
    from pipeline import explore
    by_name = {level.name: level for level in levels.EVIDENCE_LEVELS}
    for item in paper().items:
        if "repair" not in item.tags:
            continue
        rules = rules_of(next(row for row in variant_rows()
                              if row["variant"] == item.paper["variant"]))
        spent = 0
        for name in item.paper["protocol"]["levels"]:
            level = replace(by_name[name], rules=rules)
            episodes = explore.plan_episodes(
                level, per_class=item.paper["protocol"]["per_class"])
            spent += sum(len(e.actions) for e in episodes)
        assert spent == item.truth["budget_actions"], item.item_id
        assert item.truth["exact_on_heldout"] is (
            item.truth["heldout_mispredictions"] == 0)
        cells = 7 * 7 - len(adaptation.HELDOUT_WALLS)
        assert item.truth["heldout_checks"] == cells * (cells - 1) * 4


def test_repair_is_not_uniformly_easy_or_the_item_measures_nothing():
    outcomes = {item.truth["exact_on_heldout"] for item in paper().items
                if "repair" in item.tags}
    assert outcomes == {True, False}


# ------------------------------------------- the substitution, checked

def test_the_old_theory_stand_in_matches_the_compiled_manual():
    """Close the one gap the module docstring admits to.

    `adapt.py` predicts with the executable form compiled from theory.dsl; this
    paper predicts with `sokoban2.step` under the base rules and argues they are
    the same function. When the compiler can parse the manual, that argument is
    checkable, so it is checked. When it cannot -- the theory-compiler track's
    parser now demands a `semantics:` section the v0.1 A0 manual predates, which
    is why every test in a0-spike currently errors -- the test skips with the
    reason rather than passing quietly.
    """
    from pipeline import gen_exec
    dsl_path = os.path.join(REPO, "a0-spike", "theory", "theory.dsl")
    with open(dsl_path, encoding="utf-8") as handle:
        dsl_text = handle.read()

    level = levels.MATCH
    try:
        module = gen_exec.compile_module(dsl_text, level.height, level.width,
                                         level.walls)
    except Exception as exc:                      # pragma: no cover - see above
        pytest.skip("the A0 manual does not compile in this checkout: %s"
                    % str(exc).splitlines()[0][:120])

    State_, step = module["State"], module["step"]
    base = replace(level, rules=Rules())
    for state in _all_states(level):
        for action in DIRECTIONS:
            expected, _ = sokoban2.step(base, state, action)
            got = step(State_(player=state.player, box=state.box), action)
            assert (got.player, got.box) == (expected.player, expected.box)


# ------------------------------------------------- the rubric's own edges

def test_the_detection_bands_are_what_the_module_says_they_are():
    item = next(i for i in paper().items
                if "single_level" in i.tags and i.truth["index"] is not None)
    truth, index = item.truth, item.truth["index"]
    assert rubrics.grade_detect(index, truth, item).awarded == item.points
    assert 0 < rubrics.grade_detect(index + 2, truth, item).awarded < item.points
    assert 0 < rubrics.grade_detect(index + 8, truth, item).awarded \
        < rubrics.grade_detect(index + 2, truth, item).awarded
    assert rubrics.grade_detect(index + 9, truth, item).awarded == 0.0
    # "never" where it was in fact caught out is a different failure from a bad
    # number, and axes has to be able to see it.
    missed = rubrics.grade_detect({"detected": False}, truth, item)
    assert missed.awarded == 0.0 and missed.detail["missed"] is True


def test_abstaining_is_recorded_as_abstention_and_not_as_a_wrong_answer():
    item = next(i for i in paper().items if "collateral" in i.tags)
    score = rubrics.grade_collateral("abstain", item.truth, item)
    assert score.verdict == "abstained"
    assert score.awarded == 0.0
    assert score.detail["said"] == "abstain"


def test_a_rubric_is_a_pure_function_of_its_three_arguments():
    item = next(i for i in paper().items if "collateral" in i.tags)
    answer = {"rules_falsified": list(item.truth["rules_falsified"]),
              "claims_to_reexamine": list(item.truth["claims_to_reexamine"]),
              "claims_now_false": list(item.truth["claims_now_false"]),
              "verdict": item.truth["verdict"]}
    first = rubrics.grade_collateral(answer, item.truth, item)
    second = rubrics.grade_collateral(answer, item.truth, item)
    assert first.to_json() == second.to_json()
    assert first.awarded == item.points


def test_the_rubric_ids_this_paper_uses_are_the_ones_it_ships():
    used = {item.rubric_id for item in paper().items}
    assert used == set(RUBRIC_BY_ID)
    assert used == {"adapt.detect.v1", "adapt.detect_cross.v1",
                    "adapt.describe.v1", "adapt.collateral.v1",
                    "adapt.repair.v1"}


def test_the_rubrics_register_cleanly_alongside_the_other_types():
    """The integration, once the neighbours exist.

    Two things are checked that the direct import cannot: that no other question
    type has claimed one of these rubric ids (the registry refuses duplicates,
    because a report cannot be read if an id names two marking rules), and that
    marking through the real marker gives the same numbers as marking here.
    """
    try:
        from exam.grading import registry
        from exam.grading.mark import mark
        rubric_ids = set(registry.all_rubrics())
    except Exception as exc:                      # pragma: no cover
        pytest.skip("the rubric registry is not complete yet: %s"
                    % str(exc).splitlines()[0][:120])

    assert set(RUBRIC_BY_ID) <= rubric_ids
    digest = registry.digest()
    key = paper().key(digest)
    for mode in ("oracle", "null", "memoriser", "bluffer"):
        answers = adaptation.reference_answers(paper(), key, mode)
        report = mark(key, Submission(mode, paper().paper_id, answers),
                      axes_fn=adaptation.axes)
        assert report.meta["rubric_digest_matches"] is True
        assert report.fraction == mark_locally(mode, answers).fraction
    oracle = mark(key, Submission("oracle", paper().paper_id,
                                  adaptation.reference_answers(paper(), key, "oracle")),
                  axes_fn=adaptation.axes)
    assert oracle.fraction == 1.0
    assert oracle.axes["silently_wrong"] == 0
