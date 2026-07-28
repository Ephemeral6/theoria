"""Acceptance tests for the layered handover paper.

The suite is written against the two things that can go wrong quietly.

**The paper stops being frozen.**  Determinism is checked on bytes, not on
shapes: two builds are serialised and compared, and so are two bundle emissions.
A paper that drifts between builds cannot carry a rubric digest that means
anything.

**The paper starts answering itself.**  `exam.leakage.check_paper` runs the
declared probes over the sheet, and the same probes are then run over every byte
of both bundles -- a bundle is handed to the examinee exactly as the sheet is,
and a leak does not care which file it travelled in.  On top of that, the
optimal-action truths are re-derived by brute force from the world, because a
truth that has narrowed to one tie-break marks a correct reader wrong and
nothing else in the suite would notice.

`exam.grading.registry` is deliberately not imported at module scope.  It loads
all four question types' rubric modules and the other three are being written
concurrently; a handover suite that could not run until every sibling landed
would be reporting on its neighbours.  The one test that wants the registry
skips itself when a sibling is missing, and says which.
"""

from __future__ import annotations

import importlib
import json
import os
import re

import pytest

from exam import leakage
from exam.guard import SYNTHETIC_WORLDS, no_network
from exam.model import Submission, canonical, sha256_text
from exam.grading import rubrics_handover as R
from exam.papers import handover as H

FIXED_DIGEST = "0" * 64


# --------------------------------------------------------------- fixtures

@pytest.fixture(scope="module")
def paper():
    with no_network():
        return H.build()


@pytest.fixture(scope="module")
def key(paper):
    return paper.key(FIXED_DIGEST)


@pytest.fixture(scope="module")
def bundles(tmp_path_factory):
    with no_network():
        return H.emit_bundles(str(tmp_path_factory.mktemp("bundles")))


# ------------------------------------------------------------ determinism

def test_build_is_byte_identical():
    with no_network():
        one, two = H.build(), H.build()
    assert canonical(one.sheet(FIXED_DIGEST)) == canonical(two.sheet(FIXED_DIGEST))
    assert canonical(one.key(FIXED_DIGEST)) == canonical(two.key(FIXED_DIGEST))


def test_emit_bundles_is_byte_identical(tmp_path):
    with no_network():
        one = H.emit_bundles(str(tmp_path / "a"))
        two = H.emit_bundles(str(tmp_path / "b"))
    for tier in H.TIERS:
        # the destination path is the only thing allowed to differ
        assert one[tier]["digest"] == two[tier]["digest"]
        assert one[tier]["files"] == two[tier]["files"]
    for tier in H.TIERS:
        for name in one[tier]["files"]:
            left = (tmp_path / "a" / tier / name).read_bytes()
            right = (tmp_path / "b" / tier / name).read_bytes()
            assert left == right, "%s/%s differs between emissions" % (tier, name)


def test_build_opens_no_socket():
    """`no_network` is a tripwire, and this is the trip.

    The exam is the active instrument and therefore the one most likely to reach
    for the live game; a builder that quietly fetched something would still
    produce a plausible paper.
    """
    with no_network():
        H.build()
        H.bundle_files(H.TIER1)
        H.bundle_files(H.TIER2)


# -------------------------------------------------------------- the world

def test_world_is_synthetic(paper):
    assert paper.world["world_id"] == H.WORLD_ID
    assert H.WORLD_ID in SYNTHETIC_WORLDS
    assert "piles_sha256" in paper.world, "no cut digest on the paper"


def test_no_pile_game_is_named_anywhere(paper, bundles):
    """The dev pile ids travel in `provenance()`; nothing else may name a game.

    Checked over the bundles rather than the sheet, because the sheet's world
    block legitimately carries the cut's provenance and the bundles have no
    business mentioning a game at all.
    """
    for tier in H.TIERS:
        text = H.bundle_text(tier)
        for game_id in paper.world.get("dev_pile", []):
            assert game_id not in text
            assert game_id.split("-")[0] not in text


# ---------------------------------------------------------------- leakage

def test_sheet_is_leakage_clean(paper):
    report = leakage.check_paper(paper, paper.sheet(FIXED_DIGEST))
    assert report["probe_hits"] == 0
    assert report["structural_hits"] == 0
    assert report["probes_declared"] == 2 * len(paper.items)


def test_bundles_are_leakage_clean(paper, bundles):
    """The same probes, over the other half of what the examinee receives."""
    for tier in H.TIERS:
        text = H.bundle_text(tier)
        for item in paper.items:
            hits = leakage.probe_hits(text, item.leak_probes)
            assert not hits, "%s leaks %s of %s" % (tier, hits, item.item_id)


def test_bundle_content_never_names_a_class(bundles):
    """`level_data` and `world_law` appear in the brief and nowhere else.

    The brief is the answer alphabet, which every examinee must be given.  The
    manual and the playbook are the evidence, and evidence that classified a
    name for the reader would turn eleven items into a lookup.
    """
    forbidden = ("level_data", "world_law", "varies per level",
                 "fixed across levels", "level data", "world law")
    for tier in H.TIERS:
        evidence = H.bundle_text(tier, content_only=True)
        for token in forbidden:
            assert token not in evidence, "%s: %r in the evidence files" % (
                tier, token)
        assert "level_data" in H.bundle_files(tier)["READER_BRIEF.md"]


def test_bundle_contains_no_worked_example(bundles):
    """No concrete cell anywhere in a bundle's evidence files.

    A single worked push on a concrete board would answer four step-semantics
    items outright.  The check is crude on purpose -- any `(n,m)` at all -- so it
    cannot be satisfied by a cleverly worded example.
    """
    cell = re.compile(r"\(\s*\d+\s*,\s*\d+\s*\)")
    for tier in H.TIERS:
        for name, text in H.bundle_files(tier).items():
            if name not in H.CONTENT_FILES:
                continue
            if name == "MANUAL.md":
                # `(row, col)` is the coordinate convention, not a position.
                text = text.replace("(row, col)", "")
            found = cell.findall(text)
            assert not found, "%s/%s contains %s" % (tier, name, found[:4])


def test_item_ids_do_not_predict_the_answer(paper):
    """A bluffer who never reads the question should score at chance.

    Neither the natural order of the vocabulary (which groups the answers) nor a
    strict alternation (which makes the index predict them) survives this; the
    build orders items by a hash of a key that does not mention the answer.
    """
    names = [i for i in paper.items if i.paper["kind"] == "name_class"]

    class _View:
        paper_id = "name-family"
        items = names

    report = leakage.positional_report(
        _View(), {i.item_id: i.truth["class"] for i in names})
    assert report["clustered_by_answer"] is False
    assert report["order_runs"] >= 4

    means = report["sheet_length_mean_by_answer"]
    spread = abs(means["level_data"] - means["world_law"])
    assert spread / max(means.values()) < 0.05, (
        "the two classes' items differ in length by %.1f%%; an examinee could "
        "answer 'the long ones are laws'" % (100 * spread / max(means.values())))

    index_of = {item.item_id: n for n, item in enumerate(names)}
    parity = {(index_of[i.item_id] % 2, i.truth["class"]) for i in names}
    assert len(parity) > 2, "item index parity predicts the class"


# ----------------------------------------------------------- the questions

def test_every_rule_of_the_manual_is_exercised(paper):
    coverage = paper.notes["rule_coverage"]
    assert set(coverage) == set(R.RULE_NAMES)
    for name, count in coverage.items():
        assert count >= 2, "%s has %d witness(es); one is an anecdote" % (
            name, count)


def test_step_truths_agree_with_the_world(paper):
    """The truth is the world's, recomputed here from the world's own `step`."""
    sk = H.world()
    for item in paper.items:
        if item.paper["kind"] != "step_semantics":
            continue
        spec = H.LEVEL_OF[item.paper["level"]["level_id"]]
        player = tuple(item.paper["state"]["player"])
        box = tuple(item.paper["state"]["box"])
        level = sk.Level(name=spec.level_id, height=spec.height,
                         width=spec.width, walls=spec.walls, player=player,
                         box=box, target=spec.target)
        nxt, _ = sk.step(level, sk.State(player=player, box=box),
                         item.paper["action"])
        assert list(nxt.player) == item.truth["next_player"]
        assert list(nxt.box) == item.truth["next_box"]


def test_optimal_items_accept_every_optimal_action(paper):
    """Brute force, independently of `optimal_actions`.

    Enumerate every action, ask the oracle for the distance it leaves behind,
    and demand the truth's accepted set be exactly the actions that shorten it.
    A rubric that demanded the one plan BFS happened to return would mark a
    correct reader wrong, and this is the only test that would catch it.
    """
    sk = H.world()
    multi = 0
    for item in paper.items:
        if item.paper["kind"] != "optimal_action":
            continue
        spec = H.LEVEL_OF[item.paper["level"]["level_id"]]
        player = tuple(item.paper["state"]["player"])
        box = tuple(item.paper["state"]["box"])

        def _level(p, b):
            return sk.Level(name=spec.level_id, height=spec.height,
                            width=spec.width, walls=spec.walls, player=p,
                            box=b, target=spec.target)

        here = sk.solve_bfs(_level(player, box))
        assert here is not None and len(here) > 0
        expected = set()
        for action in sk.DIRECTIONS:
            nxt, event = sk.step(_level(player, box),
                                 sk.State(player=player, box=box), action)
            if event == sk.BLOCKED:
                continue
            there = sk.solve_bfs(_level(nxt.player, nxt.box))
            if there is not None and len(there) == len(here) - 1:
                expected.add(action)
        assert set(item.truth["optimal_actions"]) == expected
        assert item.truth["distance"] == len(here)
        if len(expected) > 1:
            multi += 1
        # every accepted action must actually be marked correct
        for action in expected:
            score = R.grade_optimal_action(action, item.truth, item)
            assert score.verdict == "correct", "%s rejects %s" % (
                item.item_id, action)
    assert multi >= 2, ("no item has more than one optimal action, so "
                        "'accept the whole set' is untested")


def test_no_single_action_answers_most_optimal_items(paper):
    """A reader who always says the same direction should not look competent."""
    items = [i for i in paper.items if i.paper["kind"] == "optimal_action"]
    for action in R.ACTIONS:
        hits = sum(1 for i in items if action in i.truth["optimal_actions"])
        assert hits <= len(items) / 2.0, (
            "%s is optimal in %d of %d items" % (action, hits, len(items)))


# ------------------------------------------------------- the four examinees

def test_oracle_scores_full_marks(paper, key):
    result = H.score_locally(paper, H.reference_answers(paper, key, "oracle"))
    assert result["fraction"] == 1.0
    assert result["awarded"] == result["possible"]


def test_null_scores_zero(paper, key):
    answers = H.reference_answers(paper, key, "null")
    assert answers == {}
    result = H.score_locally(paper, answers)
    assert result["awarded"] == 0.0


def test_no_deliverable_is_a_code_path_not_a_constant(paper, key):
    """「CC 无物可交记零」, derived rather than written down.

    A real submission with no capability and no answers goes through the same
    marker as everyone else, scores zero because there is nothing in it, and
    `axes` reports *why* -- which is the part that makes the zero a finding
    instead of a blank.
    """
    submission = H.no_deliverable_submission()
    assert submission.capabilities == ()
    assert submission.answers == {}

    report = _mark(paper, key, submission)
    assert report.awarded == 0.0
    assert report.possible > 0.0
    assert all(s.verdict == "unanswered" for s in report.scores)

    axes = H.axes(report, key, submission)
    assert axes["no_deliverable"] is True
    assert axes["tier"] is None
    assert "无物可交" in axes["no_deliverable_reason"]
    assert axes["reader_minus_author"] == -axes["author_baseline_fraction"]
    assert "capability_unclaimed" not in axes


def test_answering_without_declaring_a_bundle_is_flagged_not_zeroed(paper, key):
    """Answers are evidence of a deliverable; a declaration is a claim about one.

    Reporting such an examinee as "nothing to hand over" would be a false
    finding, and it would land on every calibration fake, none of which is an
    arm.  It is flagged instead, and its mark stands on its answers.
    """
    undeclared = Submission(examinee_id="undeclared", paper_id=H.PAPER_ID,
                            answers=H.reference_answers(paper, key, "oracle"),
                            capabilities=("answers",), meta={"tier": None})
    axes = H.axes(_mark(paper, key, undeclared), key, undeclared)
    assert axes["no_deliverable"] is False
    assert "capability_unclaimed" in axes
    assert axes["fraction"] == 1.0


def test_memoriser_splits_by_family(paper, key):
    """Perfect on transitions, at chance on the vocabulary.

    This is the reader Theoria 1.11 warns about -- the one who pattern-matched a
    single board -- and a handover paper that could not separate it from `oracle`
    would be scoring recall.
    """
    result = H.score_locally(paper, H.reference_answers(paper, key, "memoriser"))
    families = result["by_family"]
    assert families[H.FAMILY_STEP]["fraction"] == 1.0
    assert families[H.FAMILY_NAMES]["fraction"] < 1.0
    assert result["fraction"] < 1.0

    # It answers `world_law` to everything, so it scores exactly the world_law
    # share of the vocabulary family -- not a number that happens to be low.
    names = [i for i in paper.items if i.paper["kind"] == "name_class"]
    laws = sum(1 for i in names if i.truth["class"] == "world_law")
    assert families[H.FAMILY_NAMES]["awarded"] == pytest.approx(float(laws))


def test_bluffer_is_beaten_by_the_paper(paper, key):
    """The constant-answer arm is the floor any reader has to clear."""
    result = H.score_locally(paper, H.reference_answers(paper, key, "bluffer"))
    assert result["fraction"] < 0.5
    assert result["by_family"][H.FAMILY_STEP]["fraction"] < 0.2


# ------------------------------------------------------- the author baseline

def test_author_baseline_is_computed_and_high(paper):
    baseline = paper.notes["author_baseline"]
    assert baseline["form"] in ("compiled", "checked-in")
    assert baseline["fraction"] >= 0.95, (
        "the deliverable cannot answer its own handover sheet: %s"
        % baseline["wrong"])
    for family in H.FAMILIES:
        assert baseline["by_family"][family]["fraction"] >= 0.9, family


def test_author_baseline_is_in_the_truth_and_not_on_the_sheet(paper):
    sheet_text = canonical(paper.sheet(FIXED_DIGEST))
    assert "author_baseline" not in sheet_text
    assert "author_baseline" in canonical(paper.key(FIXED_DIGEST))
    for item in paper.items:
        assert item.item_id + " =>" not in sheet_text


def test_author_answers_never_read_the_answer_key():
    """Poison every truth and demand the same answers.

    「新读者打平作者」 is worthless if the author peeked.  The check is not a
    reading of `author_answers` but an experiment on it: a paper whose truths
    have been replaced with nonsense must produce byte-identical author answers,
    which it can only do by having read the deliverable instead.  Built fresh
    rather than mutating the shared fixture -- a test that poisons state its
    neighbours depend on is a test that fails somebody else.
    """
    with no_network():
        clean, poisoned = H.build(), H.build()
    for item in poisoned.items:
        object.__setattr__(item, "truth", {"poisoned": True})
    assert H.author_answers(clean) == H.author_answers(poisoned)


def test_author_rule_names_agree_with_the_world(paper):
    """Two independent derivations of the same fact.

    `_which_rule` reads the world; the author baseline runs the compiled manual
    and reports which rule fired.  They agree, which is the a0-spike `certify`
    check in miniature -- and if they ever stop agreeing, the manual and the
    world have parted company.
    """
    answers = H.author_answers(paper)
    for item in paper.items:
        if item.paper["kind"] != "step_semantics":
            continue
        assert answers[item.item_id] == H.step_answer_text(item.truth)


# --------------------------------------------------------------- the tiers

def test_both_tiers_exist_and_differ_only_by_the_playbook(bundles):
    one = H.bundle_files(H.TIER1)
    two = H.bundle_files(H.TIER2)
    assert set(two) - set(one) == {"PLAYBOOK.dsl", "PLAYBOOK.md"}
    assert one["MANUAL.dsl"] == two["MANUAL.dsl"]
    assert one["MANUAL.md"] == two["MANUAL.md"]
    assert bundles[H.TIER1]["digest"] != bundles[H.TIER2]["digest"]


def test_tier1_has_no_strategy(bundles):
    """The manual-only tier must really be manual-only.

    Not a spelling check: these are the words the playbook's whole content is
    made of, and any of them appearing in tier 1 means the tiers are not two
    tiers.
    """
    text = H.bundle_text(H.TIER1, content_only=True).lower()
    for word in ("deadlock", "heuristic", "prune", "playbook", "search",
                 "strategy"):
        assert word not in text, "tier 1 mentions %r" % word


def test_reader_briefs_exist_and_are_parseable(bundles, tmp_path_factory):
    """The brief must be complete enough to answer from, and machine-checkable.

    Every grammar the sheet uses has to be named in it, together with every
    token of every answer alphabet: a reader who was not told the alphabet and
    then scored zero for a parse failure was marked on the brief, not on the
    manual.
    """
    for tier in H.TIERS:
        path = os.path.join(bundles[tier]["path"], "READER_BRIEF.md")
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as fh:
            brief = fh.read()
        for kind in ("step_semantics", "name_class", "optimal_action"):
            assert kind in brief
        for token in R.RULE_NAMES + R.ACTIONS + R.NAME_CLASSES + (R.ABSTAIN,):
            assert token in brief, "%s: brief omits %r" % (tier, token)
        assert "player=(row,col); box=(row,col); rule=<name>" in brief
        for name in bundles[tier]["files"]:
            if name in H.CONTENT_FILES:
                assert "`%s`" % name in brief, "brief omits %s" % name

        # the format example must be a format example, not an answer
        examples = re.findall(r'"([^"]+)":\s*"([^"]+)"', brief)
        assert examples, "the brief shows no answer shape"
        for item_id, answer in examples:
            assert item_id not in {i.item_id for i in H.build().items}


def test_reader_brief_example_parses_under_the_real_rubric(bundles):
    """Whatever the brief shows a reader is a sentence of the published grammar.

    A brief demonstrating a shape the marker rejects is worse than no brief.
    """
    brief = H.bundle_files(H.TIER2)["READER_BRIEF.md"]
    for _item_id, answer in re.findall(r'"([^"]+)":\s*"([^"]+)"', brief):
        if answer.startswith("<"):
            continue
        for parse in (R.parse_step_answer, R.parse_class_answer,
                      R.parse_action_answer):
            try:
                parse(answer)
                break
            except R.ParseFailure:
                continue
        else:                                     # pragma: no cover
            pytest.fail("the brief shows %r, which no grammar accepts" % answer)


def test_manifest_records_provenance(bundles):
    for tier in H.TIERS:
        with open(os.path.join(bundles[tier]["path"], "MANIFEST.json"),
                  "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
        assert manifest["bundle_digest"] == bundles[tier]["digest"]
        assert manifest["provenance"]["MANUAL.dsl"]["source_sha256"] == \
            sha256_text(H.read_manual_source())
        assert manifest["provenance"]["MANUAL.md"]["model_calls"] == 0


def test_tier_delta_needs_two_readers(paper, key):
    """One report is one reader; the delta says so rather than inventing one."""
    answers = H.reference_answers(paper, key, "oracle")
    solo = H.submission("reader-t2", H.TIER2, answers)
    axes = H.axes(_mark(paper, key, solo), key, solo)
    assert axes["tier2_minus_tier1"] is None
    assert "both tiers" in axes["tier2_minus_tier1_note"]

    paired = H.submission("reader-t2", H.TIER2, answers,
                          paired_tier_fraction=0.5)
    axes = H.axes(_mark(paper, key, paired), key, paired)
    assert axes["tier2_minus_tier1"] == pytest.approx(0.5)


def test_tier_delta_reports_per_family(paper, key):
    """The value of strategic knowledge should land where strategy is used."""
    weak = H.reference_answers(paper, key, "memoriser")
    strong = H.reference_answers(paper, key, "oracle")
    report_one = _mark(paper, key, H.submission("t1", H.TIER1, weak))
    report_two = _mark(paper, key, H.submission("t2", H.TIER2, strong))
    delta = H.tier_delta(report_one, report_two, key)
    assert delta["tier2_minus_tier1"] > 0
    assert delta["by_family"][H.FAMILY_STEP] == 0.0
    assert delta["by_family"][H.FAMILY_OPTIMAL] > 0


def test_reader_minus_author_is_zero_when_the_reader_draws_level(paper, key):
    """「新读者打平作者」 is a subtraction, and this is it."""
    answers = H.reference_answers(paper, key, "oracle")
    sub = H.submission("perfect-reader", H.TIER2, answers)
    axes = H.axes(_mark(paper, key, sub), key, sub)
    assert axes["reader_minus_author"] == pytest.approx(0.0)
    assert axes["no_deliverable"] is False


# ---------------------------------------------------------------- rubrics

def test_unparseable_answers_score_zero_with_the_reason(paper):
    item = next(i for i in paper.items
                if i.paper["kind"] == "step_semantics")
    for bad in ("the player moves left", "player=(1,1); box=(2,2)",
                "player=(1,1); box=(2,2); rule=slide", "", "player=1,1"):
        score = R.grade_step(bad, item.truth, item)
        assert score.awarded == 0.0
        assert score.verdict == "wrong"
        assert score.detail["parse_error"]
        assert score.detail["said"] is None


def test_step_rubric_is_all_or_nothing(paper):
    item = next(i for i in paper.items
                if i.paper["kind"] == "step_semantics")
    truth = item.truth
    nearly = "player=(%d,%d); box=(9,9); rule=%s" % (
        truth["next_player"][0], truth["next_player"][1], truth["rule"])
    score = R.grade_step(nearly, truth, item)
    assert score.awarded == 0.0
    assert score.detail["player_ok"] is True
    assert score.detail["box_ok"] is False


def test_field_order_and_case_do_not_matter(paper):
    item = next(i for i in paper.items
                if i.paper["kind"] == "step_semantics")
    truth = item.truth
    reordered = "RULE=%s ; BOX=( %d , %d ); Player=(%d,%d)" % (
        truth["rule"], truth["next_box"][0], truth["next_box"][1],
        truth["next_player"][0], truth["next_player"][1])
    assert R.grade_step(reordered, truth, item).verdict == "correct"


def test_abstain_is_its_own_verdict(paper):
    for item in (paper.items[0], paper.items[-1]):
        rubric = {r.rubric_id: r for r in R.RUBRICS}[item.rubric_id]
        score = rubric.grade("abstain", item.truth, item)
        assert score.verdict == "abstained"
        assert score.awarded == 0.0


def test_rubrics_are_pure_in_their_three_arguments(paper):
    """A rubric that could see the examinee could flatter it.

    Cheap structural proxy for the contract in `exam.model.Rubric`: the graders
    close over nothing but module constants, so there is nothing examinee-shaped
    for them to read.
    """
    for rubric in R.RUBRICS:
        assert rubric.grade.__closure__ is None
        assert rubric.grade.__code__.co_argcount == 3


def test_rubric_ids_are_unique_and_used(paper):
    ids = [r.rubric_id for r in R.RUBRICS]
    assert len(ids) == len(set(ids))
    assert {i.rubric_id for i in paper.items} == set(ids)


def test_registry_digest_covers_this_module():
    """Skipped, not failed, while the sibling rubric modules are being written.

    `exam.grading.registry` imports all four; three of them belong to other
    agents.  Failing here would report on their absence, not on this paper.
    """
    try:
        registry = importlib.import_module("exam.grading.registry")
        digest = registry.digest()
    except ModuleNotFoundError as exc:
        pytest.skip("registry needs a sibling rubric module that does not exist "
                    "yet: %s" % exc.name)
    assert len(digest) == 64
    for rubric_id in (r.rubric_id for r in R.RUBRICS):
        assert registry.rubric(rubric_id) is not None
    assert registry.module_digests()["exam.grading.rubrics_handover"] == \
        _module_digest(R)


# ----------------------------------------------------------------- helpers

def _module_digest(module) -> str:
    import inspect
    return sha256_text(inspect.getsource(module))


def _mark(paper, key, submission):
    """Mark without `exam.grading.mark`, which needs the whole registry.

    Same contract: look each item's rubric up by id, hand it
    (answer, truth, item), collect.  The one difference is the rubric table,
    which here is this module's own.
    """
    from exam.model import Report, ItemScore

    table = {r.rubric_id: r for r in R.RUBRICS}
    scores = []
    for item in paper.items:
        if item.item_id not in submission.answers:
            scores.append(ItemScore(item.item_id, item.rubric_id, 0.0,
                                    item.points, "unanswered",
                                    {"why": "no answer submitted"}))
            continue
        scores.append(table[item.rubric_id].grade(
            submission.answers[item.item_id], item.truth, item))
    report = Report(paper_id=paper.paper_id, examinee_id=submission.examinee_id,
                    question_type=paper.question_type,
                    rubric_digest=FIXED_DIGEST, scores=scores)
    report.axes = {"by_tag": report.by_tag({i.item_id: i.tags
                                            for i in paper.items})}
    return report
