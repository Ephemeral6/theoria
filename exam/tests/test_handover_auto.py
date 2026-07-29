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
from exam.model import (Item, LeakageError, Submission, canonical,  # noqa: E402
                        sha256)
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


def test_the_sheet_is_clean_under_the_full_leak_check():
    """No pin, no xfail: every finding is a failure.

    V25 could not assert this. It had just found, with the pooled single-holder
    cut on the day that cut was switched on, that this sheet leaked `solvable`
    8 of 8 through level-name multiplicity at an exact false-positive rate of
    0.0357 -- in a paper whose first build was already VOIDED for a *different*
    leak in the same family (`VOIDED.md` in
    `runs/20260728T202101Z-V11-handover-auto`) and re-run as `-r2` on the belief
    it was clean. So V25 pinned the finding by identity instead, deliberately not
    as an xfail, because an xfail switches the check off for the paper and the
    whole family of defects V19-V25 chased is checks that stopped looking while
    still printing.

    V26 repaired `_OPTIMAL_CASES` and ruled on `-r2`
    (`runs/20260729T2215Z-V26-handover-leak-ruling/RULING.md`), so the pin is
    deleted rather than left as folklore -- which is what V25's own comment
    instructed whoever repaired it to do.
    """
    report = leakage.check_paper(PAPER, SHEET, key_doc=KEY,
                                 answer_of=HA.answer_labels(PAPER, KEY))
    assert report["probe_hits"] == 0
    assert report["structural_hits"] == 0
    # The metadata half is asserted as "the check ran and could have spoken",
    # not as a count. V25's draft of this test asserted
    # `report.get("metadata_hits", 0) == 0`, and an adversarial review of V26
    # showed that key does not exist in `check_paper`'s return value at all
    # (`check_paper` *raises* on a metadata hit, so reaching this line already
    # means none fired). The assertion therefore passed on every paper ever
    # written, including a paper with the leak this file exists to keep out --
    # which is verbatim the "checks that stopped looking while still printing"
    # family V19-V25 chased, committed inside the fix for one of them.
    assert "metadata_hits" not in report, (
        "`check_paper` grew a `metadata_hits` key; assert on it directly now "
        "instead of on the fact that it did not raise")
    assert "solvable" in report["label_sets_checked"], (
        "the `solvable` label set was not derived, so the metadata check never "
        "looked at the family that carried V25's leak: %s"
        % report["label_sets_checked"])
    assert "tags" in report["metadata_fields_checked"]
    # V25 measured that 6 of 10 shipped (paper, label set) groups cannot fire at
    # all, so green is not evidence unless the group could have gone red. This
    # pins that at least one group under `solvable` -- the label set the leak
    # travelled on -- is genuinely testable here.
    power = report["metadata_multiplicity"]["solvable"]["group_power"]
    assert any(g["can_fire_at_all"] for g in power), (
        "every `solvable` group is untestable, so this test's green means the "
        "check could not have spoken: %s" % power)


def test_level_multiplicity_is_uniform():
    """The repair, stated as the property rather than as the two states.

    Pinning the states would pass for a paper that added a ninth case on
    `warren` and reopened the channel from the other side. What has to hold is
    that how often a level name occurs on the sheet carries no information, so
    that is what is asserted -- and separately that both dead boards are still
    dead, since the repair would also "work" by making everything solvable, which
    would delete the question the family exists to ask.
    """
    from collections import Counter
    counts = Counter(level for level, _p, _b in HA._OPTIMAL_CASES)
    assert len(set(counts.values())) == 1, (
        "level-name multiplicity is not uniform, which is the channel V25 found: "
        "%s" % dict(counts))
    solvable = Counter()
    for level, player, box in HA._OPTIMAL_CASES:
        length = H._plan_length(HA.LEVEL_OF[level], player, box)
        solvable["dead" if length is None else "solvable"] += 1
    assert solvable["dead"] == 2, (
        "the family needs both dead boards to keep asking `solvable`: %s"
        % dict(solvable))


def test_a_box_on_the_outer_ring_is_dead_for_a_reason_and_not_by_accident():
    """The sharpest predictor on this family is a sound law. Pinned as such.

    An adversarial review of V26's repair found that "the Box is drawn on the
    outermost ring" predicts `solvable` 10 of 10 here -- and that V26's repair
    *sharpened* it, from 8 of 8 at p_fire 0.0357 to 10 of 10 at 0.0222, because
    both dead cases put the Box at the literal same cell `(0, 5)` (both `stile`
    and `cairn` are authored with `start_box=(0, 5)`) while both appended states
    put it in the interior.

    It was nearly filed as a second leak. It is not one, and the difference is
    measured rather than argued: a Box on an edge can only ever be pushed along
    that edge, so if the target is *not* on the ring the Box can never reach it.
    Every ring cell on `warren`, `kiln`, `stile` and `cairn` is therefore dead
    from every player position -- 26, 22, 21 and 17 cells, all checked -- and
    `flume`, the one level whose target *is* on the ring at `(7, 5)`, has 2 ring
    cells that are solvable, exactly as the law says it must. A rule whose truth
    tracks the target's position is world reasoning, which is what the paper is
    for; `leakage.METADATA_FIELDS` excludes `state` and `board` on precisely that
    doctrine.

    What this test pins is the *reason*, because the reason is what makes it
    legitimate. The dangerous edit is not "the rule stops being pure" -- an
    impure rule is a broken channel, which is fine. It is "the rule stays pure
    while ceasing to be derivable": a ring Box that is dead on a board where ring
    Boxes *can* be pushed to the target is dead for some other reason, so a reader
    scoring it with ring-implies-dead is being rewarded for a Sokoban reflex
    instead of a derivation, and that is a leak. So the invariant asserted is the
    conditional one -- any level contributing a ring-Box item must have its target
    off the ring -- with `flume` standing as the law's positive control.

    The residual defect that cannot be tested from here is recorded in the run's
    RULING.md: this paper cannot distinguish a reader applying the sound rule from
    one applying the unsound "edge Box is dead, full stop" prior, because four of
    the five targets happen to sit off the ring.
    """
    def on_ring(spec, cell):
        row, col = cell
        return (row == 0 or col == 0
                or row == spec.height - 1 or col == spec.width - 1)

    def solvable_ring_boxes(spec):
        walls = set(map(tuple, spec.walls))
        free = [(r, c) for r in range(spec.height) for c in range(spec.width)
                if (r, c) not in walls]
        return [b for b in free
                if on_ring(spec, b) and tuple(b) != tuple(spec.target)
                and any(H._plan_length(spec, p, b) for p in free if p != b)]

    # The invariant that keeps the family honest.
    for level, _player, box in HA._OPTIMAL_CASES:
        spec = HA.LEVEL_OF[level]
        if not on_ring(spec, box):
            continue
        assert H._plan_length(spec, _player, box) is None, (
            "%s %s/%s has its Box on the ring and is solvable, which is fine in "
            "itself -- but check the ring cut's purity before assuming so"
            % (level, _player, box))
        assert not on_ring(spec, spec.target), (
            "%s contributes a ring-Box item while its own target %s is on the "
            "ring, so ring-implies-dead is pure here but not derivable -- that "
            "item now rewards a Sokoban reflex rather than a deduction"
            % (level, spec.target))
        assert not solvable_ring_boxes(spec), (
            "%s has a dead ring-Box item and also solvable ring Boxes, so the "
            "rule the item leans on is unsound on this very board: %s"
            % (level, solvable_ring_boxes(spec)))

    # Positive control: the law must also *fail to forbid* the solvable case, or
    # it is not a law, just a description of how these boards were authored.
    flume = HA.LEVEL_OF["flume"]
    assert on_ring(flume, flume.target), "flume's target moved off the ring"
    assert solvable_ring_boxes(flume), (
        "flume's target is on the ring, so some ring Box must be pushable to it; "
        "if this fails, ring-implies-dead is not a law of this world and every "
        "argument built on it above is void")


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


def test_no_single_tag_token_predicts_an_answer():
    """The leak that shipped once, and the check that now stands where it was.

    `Item.tags` is printed on the sheet.  The first build tagged the two boards
    with no solution `dead`, which is the answer to those items written beside
    the question.  `leakage.metadata_hits` missed it and was right to by its own
    rule: it buckets on the whole `tags` value, every item also carries a unique
    `level:` token, so every bucket held one item and was skipped as an
    identifier rather than a key.  The rule "a field that is different on every
    item predicts nothing" is true of values and false of *tokens*.

    So: bucket on each token separately, inside one answer alphabet, and refuse
    any token that appears on more than one item and agrees with the answer
    every time.
    """
    labels = HA.answer_labels(PAPER, KEY)
    by_kind = {}
    for item in PAPER.items:
        if item.item_id in labels:
            by_kind.setdefault(item.paper["kind"], []).append(item)

    offenders = []
    for kind, items in sorted(by_kind.items()):
        if len({labels[i.item_id] for i in items}) < 2:
            continue
        buckets = {}
        for item in items:
            for token in item.tags:
                buckets.setdefault(token, set()).add(labels[item.item_id])
        for token, seen in sorted(buckets.items()):
            n = sum(1 for i in items if token in i.tags)
            if n > 1 and len(seen) == 1 and n < len(items):
                offenders.append((kind, token, sorted(seen), n))
    assert not offenders, (
        "a tag token printed on the sheet is an answer key: %s" % offenders)


#: The two cross-item leaks that shipped on the sheet six readers sat, pinned so
#: that a *third* one fails the suite instead of being discovered by an
#: adversarial reviewer after the fact.  They are not deleted: the sheet is the
#: sheet those readers answered, and editing it now would leave a run whose
#: artefacts describe a paper that no longer exists.
KNOWN_CROSS_LEAKS = {
    ("v11-why-02",
     "prune parity(Box.pos) != parity(target) => dead [proof: lean]"),
    ("v11-why-05",
     "prune no_direction_admits_a_push(Box.pos) => dead [proof: none]"),
}


def test_no_new_sheet_claim_restates_a_playbook_entry():
    """The check whose absence cost this run its result.

    The adversarial review found that two `rule_justification` claims restate,
    in English and as presupposed-true, the playbook's two `prune` entries --
    and the playbook is the *treatment*.  Tier 1 was therefore handed the thing
    tier 2 was supposed to have exclusively, on exactly the family where a
    difference had been pre-registered.  Nothing in `exam/leakage.py` looks for
    this: it compares an item's metadata against its own answer, never one
    item's prose against the other tier's bundle.

    `cross_item_leak_report` measures containment of the playbook entry rather
    than Jaccard, because an entry is six words and a claim is thirty and
    Jaccard scores a perfect restatement at 0.2. The first version of the check
    used Jaccard and found nothing, which is worth remembering: a check that
    reports clean is not evidence of clean.
    """
    found = {(f["item_id"], f["playbook_entry"])
             for f in HA.cross_item_leak_report(PAPER, KEY)}
    new = found - KNOWN_CROSS_LEAKS
    assert not new, "a sheet claim restates a tier-2-only playbook entry: %s" % (
        sorted(new),)
    assert KNOWN_CROSS_LEAKS <= found, (
        "the known leaks stopped being detected -- either the sheet changed or "
        "the detector did, and both need saying out loud: %s" % sorted(found))


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

#: V25 carried the repair states here as `BALANCED_EXTRA_CASES`, monkeypatched on
#: by a `balanced_paper` fixture, because it had measured the leak but ruling on
#: the `-r2` run that sat the leaking sheet was not its call. V26 applied them to
#: `_OPTIMAL_CASES` itself and ruled on the run, so the fixture is gone: with the
#: shipped cases already balanced, patching the extras back on would have appended
#: `stile` and `cairn` a *third* time -- a paper no one ships, quietly standing in
#: for the real one in the two driver tests below. They use the real `PAPER` now.


def test_the_driver_freezes_the_key_without_writing_it(tmp_path):
    paper, key = PAPER, KEY
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
    for item in paper.items:
        assert not leakage.probe_hits(blob, item.leak_probes), item.item_id
    assert prereg["key_sha256"] == sha256(key)


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
