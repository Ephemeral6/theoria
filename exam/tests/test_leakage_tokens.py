"""The leakage gate must catch a token-level leak, and must not cry wolf.

V21. `metadata_hits` bucketed by whole value and dropped every singleton bucket,
so one unique token anywhere in a field -- a `level:` marker, a per-item id --
made every bucket a singleton and a genuine leak sharing the rest of the value
became structurally invisible. The gate ran, went green, and was used as
evidence.

Both directions are tested here, and the second matters as much as the first: a
checker fixed by refusing everything is a checker that gets switched off.
"""

import sys
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam import leakage
from exam.model import Item, LeakageError, Paper, canonical


def _paper(tag_of, answer_of, n=12):
    """A minimal two-answer paper whose only variable is its tags."""
    items = [
        Item(item_id="q%02d" % i, rubric_id="r", points=2.0,
             paper=({"kind": "probe", "body": "board %d" % i}),
             truth={"claim": answer_of(i)},
             leak_probes=[answer_of(i)],
             tags=tuple(tag_of(i)))
        for i in range(n)
    ]
    return Paper(paper_id="tokentest", question_type="verdict",
                 instructions="", items=items)


def _labels(paper):
    return {i.item_id: i.truth["claim"] for i in paper.items}


# -- negative control 1: a real token leak must go red ---------------------

def test_a_token_leak_hidden_by_a_unique_marker_is_caught():
    """The `tags: dead` case, exactly as the item describes it.

    Every item's tag *list* is unique, because each carries its own `level:NN`.
    So every whole-value bucket is a singleton and the old check scored nothing
    at all. But `dead` sits on precisely the items whose answer is `dead`, which
    is an answer key printed on the sheet.
    """
    answer_of = lambda i: "dead" if i < 6 else "live"          # noqa: E731
    paper = _paper(lambda i: ("verdict", "level:%02d" % i,
                              "dead" if i < 6 else "live"),
                   answer_of)
    hits = leakage.metadata_hits(paper, _labels(paper))
    tokens = [h for h in hits if "token" in h]
    assert tokens, "the token check missed a token that is the answer"
    assert {h["token"] for h in tokens} >= {"dead", "live"}
    for hit in tokens:
        assert hit["predicts"] == pytest.approx(1.0)

    with pytest.raises(LeakageError):
        leakage.check_paper(paper, paper.sheet("d"), answer_of=_labels(paper))


def test_the_old_whole_value_check_alone_would_have_missed_it():
    """The regression this test exists for, demonstrated rather than asserted.

    Bucketing by whole value on the same paper produces twelve singleton
    buckets and therefore scores nothing. If a future change makes the token
    check redundant, this will still be here saying why it was added.
    """
    answer_of = lambda i: "dead" if i < 6 else "live"          # noqa: E731
    paper = _paper(lambda i: ("verdict", "level:%02d" % i,
                              "dead" if i < 6 else "live"),
                   answer_of)
    buckets = {}
    for item in paper.items:
        buckets.setdefault(canonical(item.sheet_side().get("tags")), []).append(item)
    assert len(buckets) == len(paper.items), "expected every bucket to be a singleton"
    assert all(len(v) == 1 for v in buckets.values())


# -- negative control 2: a clean paper must stay green ---------------------

def test_a_clean_paper_is_not_flagged():
    """Tags that carry no answer must not trip the check.

    Same shape, same unique `level:` markers, but the informative token is
    uncorrelated with the answer -- half of each tag group answers each way.
    """
    answer_of = lambda i: "dead" if i % 2 == 0 else "live"     # noqa: E731
    paper = _paper(lambda i: ("verdict", "level:%02d" % i,
                              "north" if i < 6 else "south"),
                   answer_of)
    assert leakage.metadata_hits(paper, _labels(paper)) == []
    report = leakage.check_paper(paper, paper.sheet("d"), answer_of=_labels(paper))
    assert report["paper_id"] == "tokentest"


def test_a_constant_token_predicts_nothing_and_is_skipped():
    """`verdict` is on every item. A token everyone carries is not a rule."""
    answer_of = lambda i: "dead" if i % 2 == 0 else "live"     # noqa: E731
    paper = _paper(lambda i: ("verdict", "level:%02d" % i), answer_of)
    assert leakage.metadata_hits(paper, _labels(paper)) == []


def test_a_token_on_one_item_is_an_identifier_not_a_rule():
    """A token carried by exactly one item states no rule there is a second
    item to test, so it must not be scored -- otherwise every id is a leak and
    the real one drowns.

    The fixture has to make the guard load-bearing, and the first version of this
    test did not: its single-holder tokens sat on a 6/6 answer split and scored
    0.583 against a 0.900 tolerance, so deleting the guard left the test green.
    It asserted the outcome of the tolerance, not of the guard. Here 11 items
    answer `live` and the one `dead` item is the sole carrier of `ridge`, so the
    token would score a perfect 1.000 against a 0.917 floor -- the guard is the
    only thing standing between this fixture and a hit.

    **Amended by V25, and the amendment is the point.** This test used to assert
    `metadata_hits(...) == []` on this fixture, and that assertion was wrong -- its
    own docstring calls `ridge` a real leak two paragraphs up. The guard is right
    about *tokens* and V21 read it as a licence to report nothing at all, so the
    test froze a miss. V25's pooled cut asks the question once per field instead of
    once per token ("does carrying a private marker here predict the answer?") and
    that question this fixture answers 12 of 12. So: no *token* finding for
    `ridge`, and a `<private-marker>` finding that catches it.
    """
    answer_of = lambda i: "dead" if i == 0 else "live"         # noqa: E731
    paper = _paper(lambda i: ("verdict", "level:%02d" % i)
                   + (("ridge",) if i == 0 else ()), answer_of, n=12)
    labels = _labels(paper)

    # What the guard is suppressing, computed here so the fixture cannot rot into
    # a tautology again: leave-one-out on a sole carrier is perfect by arithmetic.
    n = len(paper.items)
    floor = 11 / n
    rate = (1 + (n - 1)) / n
    assert rate == pytest.approx(1.0) and rate > floor > 0.9, (
        "fixture no longer makes the single-holder guard load-bearing")

    hits = leakage.metadata_hits(paper, labels)
    assert [h for h in hits if h.get("token") == "ridge"] == [], (
        "a token on one item was scored as a token; then every id is a leak")
    pooled = [h for h in hits if h.get("token") == leakage.PRIVATE_MARKER_CUT]
    assert len(pooled) == 1, (
        "the leak this fixture plants went unreported, which is what V21 froze")
    assert pooled[0]["carrier_ids"] == ["q00"]
    assert pooled[0]["predicts"] == pytest.approx(1.0)


def test_an_identifier_family_is_a_constant_not_a_leak():
    """The other side of the pooled cut, which is what makes it safe.

    Same shape, but every item carries its own private marker (`mark000`..) rather
    than one item carrying `ridge`. Pooling then holds all twelve items, and a cut
    that holds everything predicts nothing -- dropped by the same constant guard
    the individual tokens use. So an exam that numbers its items does not go red,
    and that is arithmetic rather than a special case.

    `level:%02d` will not do here: `%02d` is two characters and `MIN_TOKEN` drops
    it, so those markers never reach the carrier map at all. A guard that is never
    exercised by the fixture meant to exercise it is V21's defect over again.
    """
    answer_of = lambda i: "dead" if i == 0 else "live"          # noqa: E731
    paper = _paper(lambda i: ("verdict", "mark%03d" % i), answer_of, n=12)
    assert leakage.metadata_hits(paper, _labels(paper)) == []


# -- the singleton half ----------------------------------------------------

def test_unscored_singleton_values_are_counted_not_discarded():
    """"No hits" and "nothing was scored" print the same and mean opposites.

    The whole-value check still declines to score a singleton bucket -- rightly,
    there is no second item to test the rule against -- but the count is now
    reportable, so a green gate can be read.
    """
    answer_of = lambda i: "dead" if i < 6 else "live"          # noqa: E731
    paper = _paper(lambda i: ("verdict", "level:%02d" % i), answer_of)
    coverage = leakage.metadata_coverage(paper, _labels(paper))
    tags = [c for c in coverage if c["field"] == "tags"]
    assert tags, "the singleton buckets vanished instead of being counted"
    assert tags[0]["singleton_values"] == len(paper.items)
    assert tags[0]["scored_values"] == 0


def test_the_report_carries_the_coverage_not_just_the_function():
    """A count nobody prints is a count nobody can read.

    The first pass added `metadata_coverage` and left it uncalled outside the
    tests, so `exam/artifacts/leakage.json` still said only "no hits" -- which is
    exactly what a check that scored nothing also says. That is the V21 defect
    itself, one level up: the fix ran, went green, and did not reach the artefact
    the gate is read from.
    """
    answer_of = lambda i: "dead" if i < 6 else "live"          # noqa: E731
    paper = _paper(lambda i: ("verdict", "level:%02d" % i), answer_of)
    report = leakage.check_paper(paper, paper.sheet("d"),
                                 answer_of=_labels(paper))
    tags = [c for c in report["metadata_unscored"]["<declared>"]
            if c["field"] == "tags"]
    assert tags, "the report went green without saying it scored nothing"
    assert tags[0]["scored_values"] == 0


def test_hits_and_coverage_come_from_one_traversal():
    """The verdict and the coverage must not be obtainable from two walks.

    Two traversals can disagree, and then a report says "nothing was declined"
    beside a hit list built under different accounting. `metadata_scan` is the
    single pass; the other two are projections of it.
    """
    answers = {0: "yes", 1: "yes", 2: "yes", 3: "yes", 4: "no", 5: "no"}
    paper = _paper(lambda i: ("verdict", "pair%d" % (i // 2) if i < 4
                              else "solo%d" % i),
                   lambda i: answers[i], n=6)
    labels = _labels(paper)
    hits, unscored = leakage.metadata_scan(paper, labels)
    assert hits == leakage.metadata_hits(paper, labels)
    assert unscored == leakage.metadata_coverage(paper, labels)


# -- the papers this gate is actually guarding -----------------------------

def test_every_shipped_paper_derives_at_least_one_label_set():
    """The audit was vacuous on two of four papers, and said so by saying nothing.

    `derive_label_sets` required a field on 60% of items to treat it as the
    paper's class. A paper built from several item families has no such field,
    so `p15-adaptation-a0` and `p15-handover-a0` derived nothing and the
    metadata check ran on zero of their 89 items. A check that examines nothing
    reports the same green as a check that examined everything.
    """
    from exam.grading.registry import digest
    from exam.papers import BUILDERS, module_for
    for question_type in sorted(BUILDERS):
        paper = module_for(question_type).build()
        label_sets = leakage.derive_label_sets(paper, paper.key(digest()))
        assert label_sets, (
            "%s derives no label set, so its metadata check examines nothing"
            % paper.paper_id)


def test_a_subset_with_one_answer_left_is_not_a_prediction():
    """Dropping singletons can leave a scored subset with only one answer.

    Then the "prediction rate" is 1.0 by arithmetic — every bucket's majority is
    its whole content — while the floor still reflects the full group, so a
    field gets flagged for predicting the only answer available. `metadata_hits`
    already refuses to score a group with one answer in it; that rule simply was
    not applied to the subset it ends up scoring. `v11-handover-a0` was the live
    case, flagged at 1.000 against a 0.750 floor by V21's wider net.
    """
    # Six items: four `yes` in pairs (scored), two `no` alone (singletons,
    # dropped). Before the fix the two surviving buckets were all-`yes` and the
    # field scored 1.000 against a 4/6 floor.
    answers = {0: "yes", 1: "yes", 2: "yes", 3: "yes", 4: "no", 5: "no"}
    paper = _paper(lambda i: ("verdict", "pair%d" % (i // 2) if i < 4 else "solo%d" % i),
                   lambda i: answers[i], n=6)
    hits = leakage.metadata_hits(paper, _labels(paper))
    assert [h for h in hits if "token" not in h] == [], hits


def test_a_degenerate_whole_value_subset_does_not_disable_the_token_check():
    """The two checks must not be able to switch each other off.

    The degenerate-subset guard was written as a `continue`, which skipped the
    rest of the field's processing -- including the token check, the one thing
    this function was changed to add. A whole-value subset collapsing to one
    answer says nothing about whether a token leaks.
    """
    # `tags` whole-values: three pairs (scored) all answering "yes", plus two
    # singletons answering "no" -- the degenerate subset. And a token, `red`,
    # that is exactly the "no" items. The token leak must still be reported.
    answers = {0: "yes", 1: "yes", 2: "yes", 3: "yes", 4: "no", 5: "no"}
    tags = {0: ("pair0",), 1: ("pair0",), 2: ("pair1",), 3: ("pair1",),
            4: ("solo4", "red"), 5: ("solo5", "red")}
    paper = _paper(lambda i: tags[i], lambda i: answers[i], n=6)
    hits = leakage.metadata_hits(paper, _labels(paper))
    assert [h for h in hits if h.get("token") == "red"], hits


def test_a_subset_correction_does_not_desensitise_the_token_check():
    """The per-subset floor must stay local.

    Raising the group floor to satisfy one field's degenerate subset would make
    every later field, and the token check itself, harder to trip -- a
    correction leaking out of the thing it corrects.
    """
    import inspect
    src = inspect.getsource(leakage._metadata_hits_within)
    assert "floor = max(" not in src, (
        "the subset floor is being assigned back to the group floor")


def test_a_subset_floor_from_an_earlier_field_cannot_suppress_a_later_leak():
    """The behavioural half of the test above, which a source grep cannot be.

    Four of six respellings of the identical regression slip past that grep
    (`floor = floor_here = max(...)`, `floor += max(0.0, ...)`, and so on), so the
    grep pins a spelling and this pins the behaviour. `points` is scored first and
    its surviving subset is lopsided enough to compute a 0.950 subset floor; the
    `ridge` token in `tags` predicts 0.940 over the whole group against the real
    0.500 floor. If the first field's floor escapes, the second field's genuine
    leak is compared against 0.950 and silently suppressed.
    """
    n = 50
    answers = ["dead"] * 25 + ["live"] * 25
    # points: two multi-item buckets covering 20 items, 19 of them `dead`, so
    # `points` itself is correctly not flagged while computing a 0.950 subset
    # floor. Everyone else gets a distinct value whose tokens are all shorter
    # than MIN_TOKEN, so `points` contributes no tokens of its own.
    points = {i: 2.0 for i in range(10)}
    points.update({i: 3.0 for i in range(10, 19)})
    points[49] = 3.0
    for k, i in enumerate([i for i in range(n) if i not in points]):
        points[i] = round(4.0 + (k + 1) / 100.0, 2)
    ridge = set(range(23)) | {25}          # 23 `dead` + 1 `live`

    items = [Item(item_id="q%02d" % i, rubric_id="r", points=points[i],
                  paper={"kind": "probe", "body": "board %d" % i},
                  truth={"claim": answers[i]}, leak_probes=["v-%d" % i],
                  tags=("verdict", "level:%02d" % i)
                       + (("ridge",) if i in ridge else ()))
             for i in range(n)]
    paper = Paper(paper_id="floorleak", question_type="verdict",
                  instructions="", items=items)
    hits = leakage.metadata_hits(paper, _labels(paper))
    ridge_hits = [h for h in hits if h.get("token") == "ridge"]
    assert ridge_hits, (
        "a 0.940 token leak was suppressed by a floor another field computed")
    assert ridge_hits[0]["majority_floor"] == pytest.approx(0.5)


def test_a_token_rate_equal_to_the_floor_is_not_a_hit():
    """The floor comparison must stay strict.

    A token that predicts at exactly the majority-class rate has told us nothing
    -- guessing the majority does that well for free. Weakening `>` to `>=` there
    is invisible to every other test here, because they all use tokens that either
    beat the floor outright or fall under the tolerance.
    """
    n = 20
    answers = {i: ("dead" if i == 19 else "live") for i in range(n)}
    # floor = 19/20 = 0.950. `ridge` sits on ten `live` items, so with-token
    # majority 10 plus without-token majority 9 is 19/20 = 0.950 exactly: over
    # the 0.900 tolerance, level with the floor, and therefore not a finding.
    paper = _paper(lambda i: ("verdict", "level:%02d" % i)
                   + (("ridge",) if i < 10 else ()),
                   lambda i: answers[i], n=n)
    labels = _labels(paper)
    carriers = [i for i in paper.items if "ridge" in i.tags]
    rate = (len(carriers) + (n - len(carriers) - 1)) / n
    assert rate == pytest.approx(0.95) and rate > 0.90, "fixture drifted"
    assert [h for h in leakage.metadata_hits(paper, labels)
            if h.get("token") == "ridge"] == []


def test_short_tokens_are_dropped_as_punctuation_noise():
    """`MIN_TOKEN` is why the tokeniser does not return every stray character.

    Nothing else here pins it: lowering it to 1 leaves every test green while
    quietly multiplying the number of tokens scored, and each token scored is
    another independent chance to fire. The cost of that is measured in
    `exam/STATUS.md` under V21.
    """
    assert leakage.field_tokens(["a", "bc", "abc"]) == {"abc"}
    assert leakage.field_tokens("x-y-zzz") == {"zzz"}
    assert leakage.field_tokens(None) == set()


def test_no_label_set_is_derived_that_cannot_then_be_scored():
    """`MIN_LABELLED` must not fall below the floor the scorer itself applies.

    Lowering it buys label sets that `_metadata_hits_within` immediately declines
    for having fewer than four items -- more entries in `label_sets_checked`, not
    more checking. That is the V21 defect wearing the fix's clothes, so the
    coupling is asserted rather than left as a comment.
    """
    assert leakage.MIN_LABELLED >= 4
    from exam.grading.registry import digest
    from exam.papers import BUILDERS, module_for
    for question_type in sorted(BUILDERS):
        paper = module_for(question_type).build()
        for source, labels in leakage.derive_label_sets(
                paper, paper.key(digest())).items():
            assert len(labels) >= leakage.MIN_LABELLED, (
                "%s derives %s on %d items, below its own scoring floor"
                % (paper.paper_id, source, len(labels)))


def test_a_group_too_small_to_score_is_recorded_rather_than_skipped():
    """The unscorable case one level up from a field: a whole answer-alphabet group.

    `_metadata_hits_within` refuses a group of fewer than four items, and refuses a
    group with one answer in it. Both are right, and both used to return an empty
    pair -- indistinguishable from "scored everything, found nothing". A paper
    whose families are all small is then reported green having examined none of
    them. Mutation testing found nothing pinning this, which is how it got written.
    """
    # Two `kind` groups of three: every group is under the four-item floor, so the
    # whole paper is unscorable and must say so rather than report a bare green.
    items = [
        Item(item_id="q%02d" % i, rubric_id="r", points=2.0,
             paper={"kind": "fam%d" % (i // 3), "body": "board %d" % i},
             truth={"claim": "dead" if i % 2 else "live"},
             leak_probes=["dead" if i % 2 else "live"], tags=("verdict",))
        for i in range(6)
    ]
    paper = Paper(paper_id="smallgroups", question_type="verdict",
                  instructions="", items=items)
    hits, declined = leakage.metadata_scan(paper, _labels(paper))
    assert hits == []
    reasons = {d["declined"] for d in declined if d["field"] is None}
    assert reasons == {"fewer than 4 labelled items"}, declined
    assert len(declined) == 2, "one record per unscorable group"


def test_an_answer_key_printed_into_the_item_id_is_caught():
    """An adversarial probe walked a `q-dead-NN` paper straight past the gate.

    `item_id` is bookkeeping rather than content, so nobody was looking at it, and
    whole-value bucketing could never have scored it anyway -- it is distinct on
    every item by construction, which makes every bucket a singleton. The token
    check is what makes the field checkable at all, which is why it is added now
    and not before.
    """
    answer_of = lambda i: "dead" if i < 6 else "live"          # noqa: E731
    items = [
        Item(item_id="q-%s-%02d" % (answer_of(i), i), rubric_id="r", points=2.0,
             paper={"kind": "probe", "body": "board %d" % i},
             truth={"claim": answer_of(i)}, leak_probes=[answer_of(i)],
             tags=("verdict",))
        for i in range(12)
    ]
    paper = Paper(paper_id="idleak", question_type="verdict", instructions="",
                  items=items)
    hits = [h for h in leakage.metadata_hits(paper, _labels(paper))
            if h["field"] == "item_id"]
    assert hits, "the answer was printed in the item id and the gate passed it"
    assert {h["token"] for h in hits} >= {"dead", "live"}


def test_the_shipped_papers_stay_green_with_item_id_checked():
    """Widening the allowlist must not be paid for in false alarms.

    A gate that reddens on the papers it is meant to certify gets switched off, so
    the new field is only worth having if the four real papers stay clean under it.
    """
    from exam.grading.registry import digest
    from exam.papers import BUILDERS, module_for
    assert "item_id" in leakage.METADATA_FIELDS
    for question_type in sorted(BUILDERS):
        paper = module_for(question_type).build()
        for source, labels in sorted(leakage.derive_label_sets(
                paper, paper.key(digest())).items()):
            hits, _declined = leakage.metadata_scan(paper, labels)
            assert [h for h in hits if h["field"] == "item_id"] == [], (
                "%s/%s reddens on item_id" % (paper.paper_id, source))


def test_a_field_that_was_never_scored_says_so_in_the_report():
    """A constant field is correctly unscorable, and must still be printed.

    On `p15-verdict-a2` all three metadata fields are constant, so the check
    scores nothing on any of its four label sets. That green is honest -- there is
    nothing there to leak -- but it was indistinguishable from the green of a
    paper that was fully examined, which is the whole complaint V21 was opened
    about. Every field must appear either as scored or as declined-with-a-reason.
    """
    from exam.grading.registry import digest
    from exam.papers import module_for
    paper = module_for("verdict").build()
    labels = leakage.derive_label_sets(paper, paper.key(digest()))
    assert labels, "the verdict paper derives no label set"
    for source, answer_of in sorted(labels.items()):
        hits, declined = leakage.metadata_scan(paper, answer_of)
        accounted = {h["field"] for h in hits} | {d["field"] for d in declined}
        assert set(leakage.METADATA_FIELDS) <= accounted, (
            "%s/%s: fields %s were neither scored nor explained"
            % (paper.paper_id, source,
               set(leakage.METADATA_FIELDS) - accounted))
