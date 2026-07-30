"""What a red is worth, and what the single-holder guard actually costs.

V25. Two debts V21 measured and deliberately left: tokens carried by exactly one
item are never scored, and small groups clear the tolerance by luck. They pull in
opposite directions, so the item required both be treated together.

They were treated differently, and both rulings are pinned here rather than
asserted in a status file:

* The single-holder gap is **not closable** by any rule of this kind. A token on
  one item has statistics that depend only on which item it sits on, so a real
  leak and a bookkeeping identifier on the same item are numerically identical.
  Pinned by `test_a_single_holder_leak_is_arithmetically_identical_to_an_id`.
* The multiplicity correction is real, exact, and **published rather than
  applied**. Applying it silences a leak V21 planted at n=6. Pinned by
  `test_the_correction_is_reported_and_never_suppresses_a_finding` together with
  `test_applying_the_correction_as_a_gate_would_silence_a_planted_leak`, which
  keeps the reason on the record instead of in a commit message.
"""

import itertools
import os
import sys
import time
from collections import Counter
from math import comb

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam import leakage
from exam.model import Item, LeakageError, Paper


def _paper(tag_of, answer_of, n=12):
    items = [
        Item(item_id="q%02d" % i, rubric_id="r", points=2.0,
             paper=({"kind": "probe", "body": "board %d" % i}),
             truth={"claim": answer_of(i)},
             leak_probes=[answer_of(i)],
             tags=tuple(tag_of(i)))
        for i in range(n)
    ]
    return Paper(paper_id="v25test", question_type="verdict",
                 instructions="", items=items)


def _labels(paper):
    return {i.item_id: i.truth["claim"] for i in paper.items}


def _dirty():
    """V21's negative control 1: `dead` is the answer, hidden by unique markers."""
    return _paper(lambda i: ("verdict", "level:%02d" % i,
                             "dead" if i < 6 else "live"),
                  lambda i: "dead" if i < 6 else "live")


# -- the exact null ---------------------------------------------------------

def test_the_fire_probability_is_exact_not_sampled():
    """Checked against hand arithmetic, because a wrong null is invisible.

    n=8 split 6/2. The gate needs rate > 0.90, and the only rate above it is
    8/8 -- 7/8 = 0.875 does not clear. A token on k=2 reaches 1.0 only when its
    two carriers are exactly the two minority items: one subset of C(8,2) = 28.
    """
    counts = {"yes": 6, "no": 2}
    assert leakage.token_fire_probability(counts, 2) == pytest.approx(1 / 28)

    # n=12 balanced, k=6: the carriers must be exactly one class or exactly the
    # other -- two subsets of C(12,6) = 924.
    assert leakage.token_fire_probability({"a": 6, "b": 6}, 6) == pytest.approx(
        2 / comb(12, 6))

    # k=0 and k=n are not tests and cannot fire.
    assert leakage.token_fire_probability(counts, 0) == 0.0
    assert leakage.token_fire_probability(counts, 8) == 0.0


def test_the_fast_count_agrees_with_the_oracle_everywhere():
    """The count was rewritten for cost; this is the proof it kept the answer.

    The obvious way to count is to enumerate every split of the carriers across
    answer classes, and that is exponential in the number of *answer classes* --
    the one dimension an exam does not control, since an exam whose answers are
    integers has as many classes as it has distinct answers. Measured before the
    rewrite: 0.46s at six classes, 14.7s at eight, unfinished at twelve.

    So `_fire_count` collapses states instead, and `_fire_count_bruteforce` stays
    in the module as the oracle it is checked against. Here over every class-size
    multiset with n <= 8, every k, and six tolerances -- including 0.875, which is
    exactly 7/8 and so an exact float tie at n=8, and 0.50, which puts the
    majority floor rather than the tolerance in charge. The wider sweep (2130
    configurations) is
    `runs/20260729T1820Z-V25-leakage-loo-and-multiplicity/b4_fast_count_vs_oracle.py`.
    """
    checked = 0
    for m in range(1, 4):
        for sizes in itertools.combinations_with_replacement(range(1, 7), m):
            if sum(sizes) > 8:
                continue
            for k in range(1, sum(sizes)):
                for tol in (0.90, 0.875, 0.75, 0.50, 0.99, 1.0):
                    fast = leakage._fire_count(sizes, k, tol)
                    slow = leakage._fire_count_bruteforce(sizes, k, tol)
                    checked += 1
                    assert fast == slow, (sizes, k, tol, fast, slow)
    assert checked > 500, "the sweep silently stopped covering anything"

    # Agreement on zero is free; these have large nonzero counts. The last is the
    # shape that makes the pruning bound work hardest: one dominant class plus
    # singletons, so only carriers landing entirely off the dominant class fire.
    for sizes, k, tol in (((40, 30, 4, 3, 2, 1), 35, 0.60),
                          ((75, 1, 1, 1, 1, 1), 3, 0.90)):
        assert (leakage._fire_count(sizes, k, tol)
                == leakage._fire_count_bruteforce(sizes, k, tol) > 0)


def test_the_exact_count_survives_many_answer_classes():
    """A gate slow enough to be switched off is a gate that is not there.

    Twenty answer classes over 200 items is not exotic -- it is one numeric-answer
    exam. The oracle would need 21**20 splits for it. Two seconds is a loose
    bound on purpose: the claim being pinned is "not exponential", not a
    benchmark, and a tight bound would fail on a loaded machine for no reason.
    """
    counts = {"c%d" % j: 10 for j in range(20)}
    start = time.perf_counter()
    p = leakage.token_fire_probability(counts, 5)
    assert time.perf_counter() - start < 2.0
    assert p == 0.0        # no class holds a majority anywhere near 0.90

    # ... and still exact where firing is possible at that scale: with one class
    # of 75 and five singletons, a token on 3 items clears 0.90 exactly when all
    # three carriers are singletons -- C(5,3) of C(80,3).
    counts = {"big": 75}
    counts.update({"s%d" % j: 1 for j in range(5)})
    assert leakage.token_fire_probability(counts, 3) == pytest.approx(
        comb(5, 3) / comb(80, 3), rel=1e-12)


def test_the_published_rate_and_the_gate_agree_on_the_exact_tie():
    """`_fires` and the gate are the same comparison, or the published rate lies.

    `_fires`' docstring claims the counter and the gate cannot drift because they
    share the predicate. Until V25's adversarial pass that was a copy rather than a
    call -- `_token_hits_within` wrote `rate > tolerance and rate > floor + 1e-9`
    out inline -- and two mutations of `_fires` survived all 66 tests in this area,
    because the counter and its oracle both route through `_fires` and move
    together, so the agreement test is structurally blind to it.

    The surviving `>=` mutant is not academic: 9/10, 18/20, 36/40 and 72/80 are all
    *exactly* the double 0.90, so the shipped tolerance sits on a reachable tie on
    any group whose size is a multiple of ten -- including n=80, the largest real
    group. Under that mutant this p_fire moves from 0.0 to 10/210 while the gate
    still does not fire: a false-positive rate published for a threshold that is
    not the one that fires, which `_fires`' own docstring calls worse than no rate.
    """
    assert 9 / 10 == 0.90 and 72 / 80 == 0.90, "the tie must be a real double tie"

    counts = {"dead": 5, "live": 5}
    # k=4 on [5,5] reaches best = 9 (four carriers in one class, five non-carriers
    # in the other) and no further, so at tolerance 0.90 nothing may fire.
    assert leakage.token_fire_probability(counts, 4, 0.90) == 0.0
    assert leakage._fire_count((5, 5), 4, 0.90) == 0
    # ... and the tie is genuinely populated: one hair below, those subsets fire.
    assert leakage._fire_count((5, 5), 4, 0.8999999999999999) == 2 * comb(5, 4)

    # The gate, on a paper whose token really does sit on the tie: `aaa` holds four
    # `dead` items, so correct = 4 + 5 = 9 of 10 against a floor of 0.5.
    paper = _paper(lambda i: ("aaa",) if i < 4 else ("zzz",),
                   lambda i: "dead" if i < 5 else "live", n=10)
    assert leakage.metadata_hits(paper, _labels(paper)) == [], (
        "rate is exactly 0.900000 and the tolerance is 0.90: the gate must not "
        "fire, so the null it publishes must not count the tie either")


def test_a_cut_and_its_complement_have_the_same_null():
    """An invariant the published rate silently rides on.

    `_partition_key` maps a token on k items and one on the complementary n-k to
    the same key, and the family-wise product keeps whichever token sorted first.
    That is only order-independent because `p_fire(k) == p_fire(n-k)` exactly --
    otherwise the published rate becomes a function of token *spelling*, which is
    the one thing the exact count was introduced to remove. It also justifies
    `group_power` sweeping only to n//2.
    """
    for counts in ({"a": 6, "b": 2}, {"a": 6, "b": 6}, {"a": 5, "b": 3, "c": 2},
                   {"a": 9, "b": 1}, {"a": 4, "b": 4, "c": 4}):
        n = sum(counts.values())
        for k in range(1, n):
            assert (leakage.token_fire_probability(counts, k)
                    == leakage.token_fire_probability(counts, n - k)), (counts, k)


def test_group_power_includes_a_single_carrier_cut():
    """The pooled cut can hold one item, so the power sweep must start at k=1.

    The first version swept k = 2..n-1 on the grounds that single-holder tokens are
    never scored. True of tokens, false of the check: the pooled private-marker cut
    holds one item on the M5 fixture and fires there. Starting at 2 understated the
    power of exactly the groups this function describes.
    """
    counts = {"dead": 1, "live": 11}
    assert leakage.token_fire_probability(counts, 1) > 0.0, (
        "fixture no longer has a firing k=1")
    power = leakage.group_power(counts)
    assert power["best_k"] == 1, power
    assert power["can_fire_at_all"] is True

    # And a vanishingly small best case must not print as the impossible one.
    tiny = leakage.group_power({"a": 46, "b": 46, **{"s%d" % i: 1 for i in range(8)}})
    if tiny["can_fire_at_all"]:
        assert tiny["best_p_fire"] != 0.0, (
            "a nonzero probability rounded to 0.0 reads as `cannot fire`, which is "
            "reported as None -- the two must stay distinguishable")


def test_group_power_stays_affordable_on_a_large_group():
    """It runs once per group per label set, so its cost is multiplied by four.

    Unmemoised and sweeping the full k range it took seconds on groups of a few
    hundred; the shipped `heldout` group is n=80 and the loose bound here is about
    the shape of the cost, not a benchmark.
    """
    counts = {"c%d" % j: 13 for j in range(6)}          # the real heldout shape
    start = time.perf_counter()
    leakage.group_power(counts)
    assert time.perf_counter() - start < 2.0

    counts = {"a": 100, "b": 100, **{"s%d" % j: 1 for j in range(20)}}
    start = time.perf_counter()
    leakage.group_power(counts)
    assert time.perf_counter() - start < 5.0


def test_a_multi_class_group_cannot_fire_and_the_report_says_so():
    """The green on two of the four shipped papers is mute, not clean.

    The token rule scores `(largest carrier class + largest non-carrier class) / n`
    against a 0.90 tolerance. That statistic is two-class-shaped: with m answer
    classes its ceiling is `2 * largest_class / n`, which for anything like balanced
    classes is about 2/m and therefore below 0.90 as soon as m >= 3. No token of any
    size can fire, whatever the paper does.

    Measured over the shipped set, 6 of the 10 (paper, label set) groups are in that
    state -- including **both** label sets of `p15-heldout-a0`, the 80-item paper,
    and the only label set of `p15-handover-a0`. V21's result that "all four papers
    derive label sets and all four come back clean" is, for two of them, clean
    because the check cannot speak.

    That is V21's own defect at the level of the statistic rather than the
    traversal, and the reason `group_power` exists. Pinned here so that nobody can
    quote those greens as evidence again without this failing first.
    """
    # Three balanced classes over nine items: ceiling 6/9 = 0.667, tolerance 0.90.
    counts = {"a": 3, "b": 3, "c": 3}
    assert all(leakage.token_fire_probability(counts, k) == 0.0
               for k in range(1, 9))
    power = leakage.group_power(counts)
    assert power["can_fire_at_all"] is False
    assert power["untestable_at_alpha"] is True
    assert power["best_p_fire"] is None

    # Two classes over the same nine items can fire, so it is the class count that
    # does this and not the group size.
    assert leakage.group_power({"a": 5, "b": 4})["can_fire_at_all"] is True

    # And the shipped artefact carries the verdict per label set, on papers with no
    # findings at all -- which is the only place it matters.
    from exam.grading.registry import digest
    from exam.papers import module_for
    paper = module_for("heldout").build()
    report = leakage.check_paper(paper, paper.sheet(digest()),
                                 key_doc=paper.key(digest()))
    multiplicity = report["metadata_multiplicity"]
    assert multiplicity, "a clean paper published nothing about its own power"
    for source, entry in multiplicity.items():
        assert entry["group_power"], source
        assert all(g["can_fire_at_all"] is False for g in entry["group_power"]), (
            "%s can now fire; if the statistic was fixed, delete this pin and say "
            "so in STATUS.md" % source)


def test_an_empty_answer_class_changes_nothing():
    """A label with no items is not a class. Counting it as one would move the
    published false-positive rate depending on which labels a paper happens to
    declare but never use."""
    assert (leakage.token_fire_probability({"yes": 6, "no": 2}, 2)
            == leakage.token_fire_probability({"yes": 6, "no": 2, "maybe": 0}, 2))


def test_the_exact_null_reproduces_v21s_sampled_permutation_number():
    """V21 got 0.117 from 2000 shuffles under `random.Random(20260729)`.

    The same quantity enumerated exactly, with no RNG at all, must land inside
    the Monte-Carlo error of that. `v11-handover-a0`/`solvable` is n=8 split 6/2
    with three tokens on disjoint pairs, so the family-wise rate is
    1 - (1 - 1/28)^3.

    This is the check that makes the exactness worth having: it agrees with an
    independently written, independently seeded estimate, so neither is a
    transcription of the other.
    """
    p = leakage.token_fire_probability({"true": 6, "false": 2}, 2)
    familywise = 1.0 - (1.0 - p) ** 3
    assert familywise == pytest.approx(0.1034, abs=5e-4)
    assert abs(familywise - 0.117) < 0.03, (
        "exact enumeration disagrees with V21's sampled null by more than "
        "Monte-Carlo error; one of them is wrong")


# -- the single-holder ruling ----------------------------------------------

def test_a_single_holder_leak_is_arithmetically_identical_to_an_id():
    """The reason the guard stays, stated as a computation rather than a claim.

    Left: 12 items, exactly one answering `dead`, and the token `ridge` sits on
    precisely that item -- a real leak, and the M5 blind spot V25 was opened to
    close. Right: the same paper, but the token is `tag07`, a per-item
    identifier that happens to land on the same item and must NOT be flagged.

    Every statistic available to the gate is identical between them, because
    both are functions of the carrier set alone and the carrier sets are equal.
    So no rule reading only (carriers, answers) can fire on one and not the
    other, and since the identifier must stay silent, so must the leak.
    """
    leak = _paper(lambda i: (("verdict", "level:%02d" % i, "ridge") if i == 7
                             else ("verdict", "level:%02d" % i)),
                  lambda i: "dead" if i == 7 else "live")
    ident = _paper(lambda i: ("verdict", "level:%02d" % i, "tag%02d" % i),
                   lambda i: "dead" if i == 7 else "live")

    def stats(paper, token):
        answer_of = _labels(paper)
        group = list(paper.items)
        n = len(group)
        holders = [i for i in group
                   if token in leakage.field_tokens(i.sheet_side().get("tags"))]
        assert len(holders) == 1, "fixture is not a single-holder case"
        held = {i.item_id for i in holders}
        counts = Counter(answer_of[i.item_id] for i in group)
        with_t = Counter(answer_of[i.item_id] for i in holders)
        without = Counter(answer_of[i.item_id] for i in group
                          if i.item_id not in held)
        in_sample = (with_t.most_common(1)[0][1]
                     + without.most_common(1)[0][1]) / n
        return (in_sample,
                leakage.token_fire_probability(counts, len(holders)),
                sorted(held) == sorted(
                    i.item_id for i in group
                    if answer_of[i.item_id] == "dead"))

    assert stats(leak, "ridge") == stats(ident, "tag07")

    # And neither is reported, which is the only consistent outcome.
    for paper, token in ((leak, "ridge"), (ident, "tag07")):
        hits = leakage.metadata_hits(paper, _labels(paper))
        assert not [h for h in hits if h.get("token") == token]


def test_the_cost_of_the_single_holder_guard_is_reported():
    """Not scoring them is defensible; not saying so is not.

    91% of the tokens on the shipped papers are single-holder. A green gate that
    never mentions this reads as "checked and clean" when it means "looked at
    9% of the tokens" -- which is V21's defect exactly, one level down.
    """
    # The marker has to be >= MIN_TOKEN characters to survive tokenising at all:
    # `level:07` splits into `level` and `07`, and `07` is dropped as punctuation
    # noise before any of this. That is worth knowing -- the per-item markers on
    # V21's own fixtures are invisible to the tokeniser rather than skipped by
    # the guard, which are two different reasons for the same silence.
    paper = _paper(lambda i: ("verdict", "mark%03d" % i,
                              "dead" if i < 6 else "live"),
                   lambda i: "dead" if i < 6 else "live")
    group = list(paper.items)
    cov = leakage.single_holder_coverage(group, _labels(paper), "tags")
    assert cov["single_holder"] == 12, cov      # one `markNNN` per item
    assert cov["scored"] == 2, cov              # `dead` and `live`
    assert cov["constant"] == 1, cov            # `verdict`
    assert cov["tokens"] == cov["single_holder"] + cov["scored"] + cov["constant"]

    _hits, declined = leakage.metadata_scan(paper, _labels(paper))  # noqa: E501
    assert [d for d in declined
            if d.get("declined") == "single-holder tokens are not scorable"], \
        "the coverage gap is not in the report a reader actually gets"


# -- the multiplicity correction -------------------------------------------

def test_every_red_carries_what_it_is_worth():
    paper = _dirty()
    hits = [h for h in leakage.metadata_hits(paper, _labels(paper))
            if h.get("token") == "dead"]
    assert hits
    hit = hits[0]
    for key in ("p_fire", "p_fire_familywise_in_field", "cuts_tried_in_field",
                "p_fire_familywise_in_label_set", "cuts_tried_in_label_set",
                "weak_evidence"):
        assert key in hit, "a red without %s cannot be discounted by a reader" % key
    # 2/924, and `dead`/`live` are complements -- one cut, not two.
    assert hit["p_fire"] == pytest.approx(2 / comb(12, 6), abs=1e-6)
    assert hit["cuts_tried_in_field"] == 1
    assert hit["weak_evidence"] is False


def test_the_correction_is_charged_at_the_wider_scope_too():
    """A familywise rate over one field, called familywise, would be a lie.

    The token check runs per (answer-alphabet group, metadata field), so a rate
    that pays only for the cuts tried on one field understates the search that
    actually ran. Here `tags` and `item_id` each carry the same `dead`/`live` cut
    -- one cut per field, two under the answer key -- and the label-set number has
    to be the larger one.

    Measured on the shipped papers, the widening is small (2, 3, 2 and 0 cuts per
    paper against 1-3 per field), which is worth knowing and is not a reason to
    leave it out: the number is what makes "small" checkable.
    """
    paper = _paper(lambda i: ("verdict", "dead" if i < 6 else "live"),
                   lambda i: "dead" if i < 6 else "live")
    # `item_id` carries the answer too, so the same cut is reached twice through
    # two different fields -- which really is two chances to fire.
    paper = Paper(paper_id=paper.paper_id, question_type=paper.question_type,
                  instructions=paper.instructions,
                  items=[Item(item_id="%s-%s" % (i.item_id, i.truth["claim"]),
                              rubric_id=i.rubric_id, points=i.points,
                              paper=i.paper, truth=i.truth,
                              leak_probes=i.leak_probes, tags=i.tags)
                         for i in paper.items])
    answer_of = {i.item_id: i.truth["claim"] for i in paper.items}
    hits = [h for h in leakage.metadata_hits(paper, answer_of) if "token" in h]
    assert hits
    fields = {h["field"] for h in hits}
    assert fields == {"tags", "item_id"}, fields
    for hit in hits:
        assert hit["cuts_tried_in_field"] == 1
        assert hit["cuts_tried_in_label_set"] == 2, (
            "the label-set scope must count the cut tried through each field")
        assert (hit["p_fire_familywise_in_label_set"]
                >= hit["p_fire_familywise_in_field"])
        # Two chances at 2/924 each, not one.
        assert hit["p_fire_familywise_in_label_set"] == pytest.approx(
            1 - (1 - 2 / comb(12, 6)) ** 2, abs=1e-6)


def test_a_token_and_its_complement_are_one_cut_not_two():
    """The multiplicity unit is the partition, not the token.

    `p15-adaptation-a0` scores four tokens -- `narrow`/`wide` on `tags` and the
    same two on `item_id` -- that are one cut wearing four names. Counting
    tokens would charge four tests for one and over-correct fourfold; it is also
    what makes the exact number agree with V21's sampled null (0.0152 against a
    published 0.013) instead of missing it by a factor of four.
    """
    paper = _dirty()
    hits = leakage.metadata_hits(paper, _labels(paper))
    tokens = {h["token"] for h in hits if "token" in h}
    assert {"dead", "live"} <= tokens, "both halves of the cut are reported"
    assert {h["cuts_tried_in_field"] for h in hits if "token" in h} == {1}


def test_the_correction_is_reported_and_never_suppresses_a_finding():
    """A weak red is still a red. It is labelled, not withheld."""
    answers = {0: "yes", 1: "yes", 2: "yes", 3: "yes", 4: "no", 5: "no"}
    tags = {0: ("pair0",), 1: ("pair0",), 2: ("pair1",), 3: ("pair1",),
            4: ("solo4", "red"), 5: ("solo5", "red")}
    paper = _paper(lambda i: tags[i], lambda i: answers[i], n=6)
    hits = [h for h in leakage.metadata_hits(paper, _labels(paper))
            if h.get("token") == "red"]
    assert hits, "the correction swallowed a planted leak"
    assert hits[0]["weak_evidence"] is True, (
        "at n=6 with three cuts this really could be luck, and the red has to "
        "say so")
    with pytest.raises(LeakageError):
        leakage.check_paper(paper, paper.sheet("d"), answer_of=_labels(paper))


def test_applying_the_correction_as_a_gate_would_silence_a_planted_leak():
    """The measurement behind the ruling, kept executable.

    If a later change makes the correction a suppressor, this fails and says
    what it costs: `red` is a leak a human sees by eye, and at n=6 with three
    cuts tried the family-wise rate is 0.187, so an alpha of 0.05 hides it.
    """
    counts = {"yes": 4, "no": 2}
    p = leakage.token_fire_probability(counts, 2)
    assert p == pytest.approx(1 / comb(6, 2), abs=1e-9)
    familywise = 1.0 - (1.0 - p) ** 3          # pair0, pair1, red
    assert familywise > leakage.ALPHA
    assert familywise == pytest.approx(0.1866, abs=5e-4)


def test_a_clean_paper_gains_no_reds_from_any_of_this():
    """The other direction, which matters as much: no new false alarms."""
    paper = _paper(lambda i: ("verdict", "level:%02d" % i,
                              "odd" if i % 2 else "even"),
                   lambda i: "dead" if i < 6 else "live")
    assert leakage.metadata_hits(paper, _labels(paper)) == []
    leakage.check_paper(paper, paper.sheet("d"), answer_of=_labels(paper))


def test_the_shipped_papers_stay_green_and_say_how_much_went_unscored():
    from exam.grading.registry import digest
    from exam.papers import BUILDERS, module_for
    for qt in sorted(BUILDERS):
        paper = module_for(qt).build()
        report = leakage.check_paper(paper, paper.sheet(digest()),
                                     key_doc=paper.key(digest()))
        unscored = report.get("metadata_unscored", {})
        assert unscored, (
            "%s reports no coverage at all, which is the one thing a reader "
            "cannot distinguish from a check that examined everything" % qt)
