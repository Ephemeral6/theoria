"""Tests for the automated layered handover (V11).

Three things are checked here that the P-15 handover tests do not check, because
P-15 did not have them: the fourth question family, the marking of a board with
no solution, and the *blinding* of the prompt an examinee actually receives.

The last one is the reason this file is longer than it looks like it should be.
Two runs earlier tonight lost their result to a leak that was not in the thing
being guarded: V15 shipped a tracked file that named the answer, V17 put the
answer in the criteria document.  A leak moves when you block it.  So the prompt
is tested as a *string* -- what is in it, and what is not -- rather than trusted
because it was assembled carefully.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam import guard, leakage                                     # noqa: E402
from exam.grading import registry                                   # noqa: E402
from exam.grading import rubrics_handover_auto as R                 # noqa: E402
from exam.grading.mark import mark                                  # noqa: E402
from exam.model import Item, Submission, canonical, sha256          # noqa: E402
from exam.papers import handover_auto as HA                         # noqa: E402
from exam.papers import handover as H                               # noqa: E402
from exam.tools import run_handover_auto as DRIVER                  # noqa: E402


def _paper():
    return HA.build()


def _sheet_key(paper):
    d = registry.digest()
    return (paper.sheet(d, registry.module_digests().get(
        "exam.grading.rubrics_handover_auto")), paper.key(d))


PAPER = _paper()
SHEET, KEY = _sheet_key(PAPER)


# ------------------------------------------------------------ the paper builds

def test_the_build_is_deterministic_and_offline():
    with guard.no_network():
        one = HA.build()
        two = HA.build()
    a, _ = _sheet_key(one)
    b, _ = _sheet_key(two)
    assert sha256(a) == sha256(b)


def test_the_sheet_does_not_carry_its_own_answers():
    report = leakage.check_paper(PAPER, SHEET, key_doc=KEY,
                                 answer_of=HA.answer_labels(PAPER, KEY))
    assert report["probe_hits"] == 0
    assert report["structural_hits"] == 0


def test_every_family_of_1_11_is_on_the_sheet():
    kinds = {i.paper["kind"] for i in PAPER.items}
    assert kinds == {"step_semantics", "name_class", "optimal_action",
                     "rule_justification", "counterexample"}


def test_all_five_rules_are_exercised():
    coverage = PAPER.notes["rule_coverage"]
    assert all(count > 0 for count in coverage.values()), coverage


def test_the_sheet_has_room_to_fail():
    """P-15's open weakness 1: a saturated sheet cannot show a tier difference.

    The check is not that the sheet is hard -- that is what the run measures --
    but that it *could* be: at least two items whose answer needs a search of a
    dozen moves or more, and at least one board with no solution that the
    manual's own arithmetic does not settle.
    """
    long_plans = [e for e in KEY["items"]
                  if e["truth"].get("plan_len") and e["truth"]["plan_len"] >= 14]
    assert len(long_plans) >= 2, "no item needs a real search"

    dead = [e for e in KEY["items"] if e["truth"].get("solvable") is False]
    assert len(dead) >= 2
    levels = PAPER.notes["levels"]
    unsettled = []
    for entry in dead:
        level_id = [t.split(":", 1)[1] for t in entry["tags"]
                    if t.startswith("level:")][0]
        spec = levels[level_id]
        item = [i for i in PAPER.items if i.item_id == entry["item_id"]][0]
        box = tuple(item.paper["state"]["box"])
        target = tuple(spec["target"])
        parity_settles = (box[0] % 2 != target[0] % 2
                          or box[1] % 2 != target[1] % 2)
        if not parity_settles:
            unsettled.append(level_id)
    assert unsettled, ("every dead board is settled by the manual's parity "
                       "laws, so the playbook's deadlock prune has nowhere to "
                       "pay off and the tier difference cannot land anywhere")


# --------------------------------------------------------- the truth is right

def test_the_optimal_sets_are_re_derived_by_brute_force():
    """The key's accepted set, recomputed here without the builder's help."""
    world = H.world()
    for entry in KEY["items"]:
        truth = entry["truth"]
        if "optimal_actions" not in truth:
            continue
        item = [i for i in PAPER.items if i.item_id == entry["item_id"]][0]
        level_id = item.paper["level"]["level_id"]
        spec = HA.LEVEL_OF[level_id]
        player = tuple(item.paper["state"]["player"])
        box = tuple(item.paper["state"]["box"])
        plan = world.solve_bfs(H._level(spec, player, box))
        if not truth["solvable"]:
            assert plan is None, "%s is marked dead and is not" % entry["item_id"]
            assert truth["optimal_actions"] == []
            continue
        assert plan is not None and len(plan) == truth["plan_len"]
        accepted = set()
        for action in world.DIRECTIONS:
            nxt, event = world.step(H._level(spec, player, box),
                                    world.State(player=player, box=box), action)
            if event == world.BLOCKED:
                continue
            onward = world.solve_bfs(H._level(spec, nxt.player, nxt.box))
            if onward is not None and len(onward) == len(plan) - 1:
                accepted.add(action)
        assert accepted == set(truth["optimal_actions"])


def test_the_step_truths_are_the_world_and_not_the_theory():
    world = H.world()
    for entry in KEY["items"]:
        if entry["rubric_id"] != "handover_auto.step_semantics":
            continue
        item = [i for i in PAPER.items if i.item_id == entry["item_id"]][0]
        spec = HA.LEVEL_OF[item.paper["level"]["level_id"]]
        player = tuple(item.paper["state"]["player"])
        box = tuple(item.paper["state"]["box"])
        nxt, _ = world.step(H._level(spec, player, box),
                            world.State(player=player, box=box),
                            item.paper["action"])
        assert list(nxt.player) == entry["truth"]["next_player"]
        assert list(nxt.box) == entry["truth"]["next_box"]


def test_every_justification_key_says_why_it_is_the_key():
    for entry in KEY["items"]:
        if entry["rubric_id"] != "handover_auto.rule_justification":
            continue
        assert entry["truth"]["why"].strip(), entry["item_id"]
        assert set(entry["truth"]["rests_on"]) <= set(R.CITABLE)


def test_the_counterexample_item_is_answerable():
    entry = [e for e in KEY["items"]
             if e["rubric_id"] == "handover_auto.counterexample"][0]
    boards = entry["truth"]["legal_boards"]
    assert boards
    ok = False
    for board in boards:
        walls = {tuple(w) for w in board["blocked"]}
        for r in range(board["rows"]):
            for c in range(board["cols"]):
                if (r, c) not in walls and r % 2 == 0:
                    ok = True
    assert ok, "no legal situation refutes the claim, so the item is unfair"


# ------------------------------------------------------------- the calibration

def _mark_fake(mode):
    fake = HA.reference_answers(PAPER, KEY, mode)
    return mark(KEY, Submission("calib-" + mode, HA.PAPER_ID, fake))


def test_the_oracle_scores_full_marks():
    """A known-full-marks answer, scored before any real answer is marked.

    If this ever falls below 1.0 the rubric is stricter than the truth, and
    every score the run reports is depressed by an unknown amount.
    """
    assert _mark_fake("oracle").fraction == 1.0


def test_the_null_examinee_scores_zero_and_is_unanswered_not_wrong():
    report = _mark_fake("null")
    assert report.fraction == 0.0
    assert report.to_json()["counts"]["unanswered"] == len(PAPER.items)
    assert report.to_json()["counts"]["wrong"] == 0


def test_neither_fake_that_lacks_understanding_beats_the_oracle():
    oracle = _mark_fake("oracle").fraction
    for mode in ("memoriser", "bluffer"):
        assert _mark_fake(mode).fraction < oracle


def test_citing_everything_is_not_a_strategy():
    """The bluffer cites every clause on every justification item.

    It must not do better than half of that family, or the penalty term is not
    doing its job and the family rewards saying more.
    """
    report = _mark_fake("bluffer")
    tag_of = {e["item_id"]: e["tags"] for e in KEY["items"]}
    got = sum(s.awarded for s in report.scores
              if HA.FAMILY_WHY in tag_of[s.item_id])
    can = sum(s.possible for s in report.scores
              if HA.FAMILY_WHY in tag_of[s.item_id])
    assert got / can <= 0.5, "shotgunning citations pays"


# ------------------------------------------------------------------ the rubrics

def _item(rubric_id, points=2.0, truth=None):
    return Item("t1", rubric_id, points, {}, truth or {})


def test_optimal_action_pays_the_two_halves_separately():
    truth = {"solvable": True, "optimal_actions": ["UP", "LEFT"], "plan_len": 20}
    item = _item("handover_auto.optimal_action", 2.0, truth)
    both = R.grade_optimal_action("action=UP; plan_len=20", truth, item)
    move = R.grade_optimal_action("action=LEFT; plan_len=9", truth, item)
    length = R.grade_optimal_action("action=DOWN; plan_len=20", truth, item)
    neither = R.grade_optimal_action("action=DOWN; plan_len=3", truth, item)
    assert (both.awarded, both.verdict) == (2.0, "correct")
    assert (move.awarded, move.verdict) == (1.0, "wrong")
    assert length.awarded == 1.0
    assert neither.awarded == 0.0


def test_none_and_abstain_are_different_claims():
    dead = {"solvable": False, "optimal_actions": [], "plan_len": None}
    item = _item("handover_auto.optimal_action", 2.0, dead)
    said_none = R.grade_optimal_action("action=none; plan_len=none", dead, item)
    said_abstain = R.grade_optimal_action("abstain", dead, item)
    said_move = R.grade_optimal_action("action=UP; plan_len=4", dead, item)
    assert said_none.awarded == 2.0 and said_none.verdict == "correct"
    assert said_abstain.awarded == 0.0 and said_abstain.verdict == "abstained"
    assert said_move.awarded == 0.0 and said_move.verdict == "wrong"

    live = {"solvable": True, "optimal_actions": ["UP"], "plan_len": 5}
    live_item = _item("handover_auto.optimal_action", 2.0, live)
    assert R.grade_optimal_action("action=none; plan_len=none", live,
                                  live_item).awarded == 0.0


def test_a_justification_hit_pays_and_a_spurious_one_costs_the_same():
    truth = {"rests_on": ["goal_box_on_target", "push2"]}
    item = _item("handover_auto.rule_justification", 3.0, truth)
    exact = R.grade_rule_justification("rests_on=push2+goal_box_on_target",
                                       truth, item)
    half = R.grade_rule_justification("rests_on=push2", truth, item)
    padded = R.grade_rule_justification(
        "rests_on=push2+goal_box_on_target+walk", truth, item)
    shotgun = R.grade_rule_justification(
        "rests_on=" + "+".join(sorted(R.CITABLE)), truth, item)
    assert exact.awarded == 3.0 and exact.verdict == "correct"
    assert half.awarded == 1.5 and half.verdict == "wrong"
    assert padded.awarded == 1.5, "a spurious citation must cost a hit"
    assert shotgun.awarded == 0.0, "citing everything must pay nothing"


def test_a_repeated_citation_is_counted_once():
    truth = {"rests_on": ["push2"]}
    item = _item("handover_auto.rule_justification", 3.0, truth)
    assert R.grade_rule_justification("rests_on=push2+push2", truth,
                                      item).awarded == 3.0


def test_a_citation_outside_the_published_list_is_a_parse_failure():
    truth = {"rests_on": ["push2"]}
    item = _item("handover_auto.rule_justification", 3.0, truth)
    score = R.grade_rule_justification("rests_on=push3", truth, item)
    assert score.awarded == 0.0 and "parse_error" in score.detail


def test_the_counterexample_is_checked_by_recomputing_the_claim():
    truth = {"claim": "box_row_mod2_eq_1",
             "legal_boards": [{"id": "b", "rows": 4, "cols": 4,
                               "blocked": [[1, 1]]}]}
    item = _item("handover_auto.counterexample", 3.0, truth)
    good = R.grade_counterexample("level=b; player=(0,1); box=(2,2)", truth, item)
    claim_holds = R.grade_counterexample("level=b; player=(0,1); box=(3,2)",
                                         truth, item)
    on_a_wall = R.grade_counterexample("level=b; player=(0,1); box=(1,1)",
                                       truth, item)
    off_board = R.grade_counterexample("level=b; player=(0,1); box=(9,9)",
                                       truth, item)
    same_cell = R.grade_counterexample("level=b; player=(2,2); box=(2,2)",
                                       truth, item)
    wrong_board = R.grade_counterexample("level=zzz; player=(0,1); box=(2,2)",
                                         truth, item)
    assert good.awarded == 3.0 and good.verdict == "correct"
    for bad in (claim_holds, on_a_wall, off_board, same_cell, wrong_board):
        assert bad.awarded == 0.0 and bad.verdict == "wrong"


def test_the_registry_covers_this_module():
    assert "handover_auto.rule_justification" in registry.all_rubrics()
    assert registry.module_digests()["exam.grading.rubrics_handover_auto"]


# ------------------------------------------------------------------- blinding

#: Substrings that must not reach an examinee.  Each one is a way the reader
#: could stop being fresh: a path it could open, a name it could search for, or
#: a statement of what is being measured (which tells it what to say).
FORBIDDEN = (
    "a0-spike", "exam/", "artifacts", "worktree", "Theoria.md", "PARTNER_SYNC",
    "rubrics_handover", "run_handover_auto", "V11-handover", "tier1_manual",
    "tier2_manual_playbook", "playbook is worth", "STATUS.md", "DECISIONS.md",
    "handover_auto", "p15-", "v11-handover-a0",
)


@pytest.mark.parametrize("tier", HA.TIERS)
def test_the_prompt_names_no_place_the_reader_could_go(tier):
    text = HA.prompt_text(tier, SHEET)
    for token in FORBIDDEN:
        assert token not in text, "%s leaks %r" % (tier, token)


@pytest.mark.parametrize("tier", HA.TIERS)
def test_the_prompt_carries_no_answer(tier):
    """Every probe the paper declared, run against the prompt and not just the
    sheet.  The sheet is checked at build time; the prompt is what is actually
    handed over, and it is a superset."""
    text = HA.prompt_text(tier, SHEET)
    for item in PAPER.items:
        assert not leakage.probe_hits(text, item.leak_probes), item.item_id


def test_the_prompt_does_not_say_which_tier_the_reader_is_in_relative_terms():
    """A reader told it is the *deprived* arm may try harder or give up.

    Each brief describes what it has; neither mentions the other tier's
    existence as a comparison, and neither says a difference is being measured.

    Checked on the brief alone.  The bundle is the deliverable and its words are
    not ours to police -- the playbook says "compare the Box's row parity with
    the target's", which is the document doing its job, not the examiner
    steering.  Policing the whole prompt would have forced an edit to the
    deliverable, and an exam that edits the thing it examines measures the edit.
    """
    for tier in HA.TIERS:
        brief = HA.reader_brief(tier).lower()
        for token in ("tier 1", "tier 2", "compare", "the other", "measur",
                      "hopeless", "unsolvable", "impossible", "playbook adds"):
            assert token not in brief, "%s brief steers with %r" % (tier, token)


def test_tier2_differs_from_tier1_by_the_playbook_and_nothing_else():
    one = HA.prompt_text(HA.TIER1, SHEET)
    two = HA.prompt_text(HA.TIER2, SHEET)
    assert "PLAYBOOK.dsl" in two and "PLAYBOOK.dsl" not in one
    assert len(two) > len(one)
    # the sheet half is byte-identical
    marker = "# The question sheet"
    assert one[one.index(marker):] == two[two.index(marker):]


def test_the_prompt_asks_for_a_tool_report():
    for tier in HA.TIERS:
        assert "TOOLS:" in HA.prompt_text(tier, SHEET)


# --------------------------------------------------------------- the driver

def test_the_driver_freezes_the_key_without_writing_it(tmp_path):
    run_dir = str(tmp_path / "run")
    out = DRIVER.build(run_dir)
    prereg = out["prereg"]
    assert prereg["key_written_to_disk"] is False
    on_disk = []
    for root, _dirs, files in os.walk(run_dir):
        on_disk.extend(os.path.join(root, f) for f in files)
    blob = ""
    for path in on_disk:
        with open(path, encoding="utf-8") as fh:
            blob += fh.read()
    for item in PAPER.items:
        assert not leakage.probe_hits(blob, item.leak_probes), item.item_id
    assert prereg["key_sha256"] == sha256(KEY)


def test_scoring_refuses_a_key_that_no_longer_matches(tmp_path, monkeypatch):
    run_dir = str(tmp_path / "run")
    DRIVER.build(run_dir)
    prereg_path = os.path.join(run_dir, "PREREGISTRATION.json")
    with open(prereg_path, encoding="utf-8") as fh:
        prereg = json.load(fh)
    prereg["key_sha256"] = "0" * 64
    with open(prereg_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(prereg, fh)
    with pytest.raises(RuntimeError, match="pre-registration"):
        DRIVER.score(run_dir)


def test_the_grader_has_no_noise_of_its_own(tmp_path):
    """Cosmetic rewriting must not move a single point.

    This is the number every delta in the run is compared against. It is
    expected to be zero and it is measured anyway: an instrument whose error is
    assumed rather than measured cannot rule anything out.
    """
    subs = []
    for mode in ("oracle", "memoriser", "bluffer"):
        fake = HA.reference_answers(PAPER, KEY, mode)
        subs.append(HA.submission(mode, HA.TIER1, fake))
    noise = DRIVER.grader_noise(KEY, subs)
    assert noise["repeat_max_abs_delta_points"] == 0.0
    assert noise["cosmetic_max_abs_delta_points"] == 0.0


def test_a_delta_inside_the_error_bars_is_not_reported_as_a_finding():
    """The V17 failure, pinned: a point estimate whose interval crosses zero."""
    out = DRIVER.bootstrap_over_examinees([0.80, 0.84, 0.76], [0.82, 0.86, 0.78])
    assert out["point"] > 0
    assert out["excludes_zero"] is False


def test_a_real_separation_does_clear_them():
    out = DRIVER.bootstrap_over_examinees([0.10, 0.12, 0.11], [0.90, 0.92, 0.91])
    assert out["excludes_zero"] is True
