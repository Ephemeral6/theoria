"""Core tests: the paper/truth split, the guards, and the marking driver.

These are the tests that do not belong to any one question type.  They are
deliberately hostile to the machinery rather than to the question types -- a
leak checker that cannot be made to fire is not a leak checker, and a guard
nobody has watched refuse is a guard nobody has tested.
"""

from __future__ import annotations

import os
import socket
import sys

import pytest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
for path in (REPO,):
    if path not in sys.path:
        sys.path.insert(0, path)

from exam import guard, leakage                                     # noqa: E402
from exam.grading import mark as mark_mod                           # noqa: E402
from exam.model import (ExamError, Item, ItemScore, LeakageError, Paper,  # noqa: E402
                        Report, Rubric, Submission, canonical, sha256)


# ------------------------------------------------------------------ fixtures

def _item(item_id="i1", truth=None, probes=("the-secret-answer",), paper=None,
          points=1.0, tags=("t",)):
    return Item(item_id=item_id, rubric_id="r-test", points=points,
                paper=paper if paper is not None else {"kind": "demo",
                                                       "question": "what?"},
                truth=truth if truth is not None else {"answer": "the-secret-answer"},
                leak_probes=probes, tags=tags)


def _paper(items=None, qtype="heldout"):
    return Paper(paper_id="p-test", question_type=qtype,
                 instructions="answer the question",
                 items=list(items or [_item()]))


# ---------------------------------------------------------- the split itself

def test_sheet_cannot_carry_a_truth():
    """`Paper.sheet` is built from `Item.sheet_side`, which never receives the
    truth -- so the split is a property of the type, not of anyone's care."""
    paper = _paper()
    sheet = paper.sheet("digest")
    text = canonical(sheet)
    assert "the-secret-answer" not in text
    assert all("truth" not in entry for entry in sheet["items"])


def test_key_carries_the_truth_and_the_rubric_id():
    key = _paper().key("digest")
    assert key["items"][0]["truth"]["answer"] == "the-secret-answer"
    assert key["items"][0]["rubric_id"] == "r-test"


def test_duplicate_item_ids_are_refused():
    with pytest.raises(ExamError):
        _paper(items=[_item("dup"), _item("dup")])


def test_unknown_question_type_is_refused():
    with pytest.raises(ExamError):
        _paper(qtype="vibes")


# ------------------------------------------------------------- leak checking

def test_leak_probe_fires_on_a_planted_answer():
    """The checker must be capable of failing, or its passes mean nothing."""
    leaky = _item(paper={"kind": "demo", "hint": "the-secret-answer"})
    paper = _paper(items=[leaky])
    with pytest.raises(LeakageError) as excinfo:
        leakage.check_paper(paper, paper.sheet("d"))
    assert "leaks its own answers" in str(excinfo.value)


def test_structural_check_catches_an_unprobed_leak():
    """The interesting half: a key the builder never thought to probe for."""
    item = Item(item_id="i1", rubric_id="r-test", points=1.0,
                paper={"kind": "demo", "next_frame": [[0]]},
                truth={"next_frame": [[9]]},
                leak_probes=("a-probe-that-does-not-fire",))
    with pytest.raises(LeakageError) as excinfo:
        leakage.check_paper(_paper(items=[item]), _paper(items=[item]).sheet("d"))
    assert "structural" in str(excinfo.value)


def test_short_probes_are_refused_rather_than_checked():
    with pytest.raises(LeakageError):
        leakage.probe_hits('{"a": 1}', ["1"])


def test_an_item_with_no_probe_is_not_assumed_innocent():
    item = Item(item_id="i1", rubric_id="r-test", points=1.0,
                paper={"kind": "demo"}, truth={"answer": "x"}, leak_probes=())
    paper = _paper(items=[item])
    with pytest.raises(LeakageError) as excinfo:
        leakage.check_paper(paper, paper.sheet("d"))
    assert "declare no leak probe" in str(excinfo.value)


def test_clean_paper_passes_and_reports_its_evidence():
    paper = _paper()
    report = leakage.check_paper(paper, paper.sheet("d"))
    assert report["probe_hits"] == 0 and report["structural_hits"] == 0
    assert report["probes_declared"] == 1


def test_positional_report_sees_a_clustered_paper():
    """A paper sorted by answer is guessable without reading it."""
    items = [_item("a%d" % i, truth={"answer": "x"}, probes=("aaa",)) for i in range(4)]
    items += [_item("b%d" % i, truth={"answer": "y"}, probes=("bbb",)) for i in range(4)]
    paper = _paper(items=items)
    labels = {i.item_id: ("unsolvable" if i.item_id.startswith("a") else "solvable")
              for i in items}
    report = leakage.positional_report(paper, labels)
    assert report["clustered_by_answer"] is True
    assert report["chance_baseline"] == 0.5


# ------------------------------------------- 4. metadata independence
#
# These four exist because the verdict paper shipped with `points` = 3.0 on
# every solvable item and 2.0 on every unsolvable one. A cheater subagent read
# the whole claim half of the paper off that field without looking at a single
# board. Checks 1-3 all passed it.

def _labelled(points_by_label, n_each=5):
    """Ids are `q-NN`, deliberately carrying no trace of the label.

    They used to read `solvable-0` / `unsolvable-0`, and V21 adding `item_id` to
    the checked fields turned both tests below red -- correctly. These two are
    about `points`; an answer key printed into the id as well would have masked
    whatever `points` was doing. That the leak was sitting in exam's own fixtures,
    unnoticed until the field was checked, is the argument for checking it.
    """
    items, labels = [], {}
    for label, points in points_by_label.items():
        for i in range(n_each):
            iid = "q-%02d" % len(items)
            items.append(Item(iid, "r-test", points, {"kind": "verdict",
                                                      "q": "board %d" % i},
                              {"claim": label}, ("probe-%s" % label,)))
            labels[iid] = label
    return _paper(items=items), labels


def test_the_old_labelled_fixture_was_itself_an_item_id_leak():
    """Kept as evidence, because a fixture repaired in silence teaches nothing.

    The ids the two tests above used until V21 spelled out the answer. Whole-value
    bucketing could never have seen it -- every id is distinct, so every bucket is
    a singleton -- and it took the token check to find it.
    """
    items, labels = [], {}
    for label in ("solvable", "unsolvable"):
        for i in range(5):
            iid = "%s-%d" % (label, i)
            items.append(Item(iid, "r-test", 2.0, {"kind": "verdict",
                                                   "q": "board %d" % i},
                              {"claim": label}, ("probe-%s" % label,)))
            labels[iid] = label
    hits = [h for h in leakage.metadata_hits(_paper(items=items), labels)
            if h["field"] == "item_id"]
    assert {h["token"] for h in hits} == {"solvable", "unsolvable"}


def test_a_point_value_that_encodes_the_answer_is_a_leak():
    paper, labels = _labelled({"solvable": 3.0, "unsolvable": 2.0})
    hits = leakage.metadata_hits(paper, labels)
    assert [h["field"] for h in hits] == ["points"]
    assert hits[0]["predicts"] == 1.0


def test_uniform_points_are_clean():
    paper, labels = _labelled({"solvable": 2.0, "unsolvable": 2.0})
    assert leakage.metadata_hits(paper, labels) == []


def test_an_identifier_is_not_treated_as_a_key():
    """A field with a distinct value per item fits perfectly and predicts
    nothing; counting it would bury the one real leak in noise."""
    items, labels = [], {}
    for i in range(6):
        iid = "i%d" % i
        items.append(Item(iid, "r-test", 1.0, {"kind": "k"},
                          {"claim": "solvable" if i % 2 else "unsolvable"},
                          ("probe-%d" % i,), tags=("variant-%d" % i,)))
        labels[iid] = "solvable" if i % 2 else "unsolvable"
    assert leakage.metadata_hits(_paper(items=items), labels) == []


def test_disjoint_answer_alphabets_do_not_make_kind_a_leak():
    """Two families answering in different vocabularies: `kind` predicts the
    answer by arithmetic, not by leaking."""
    items, labels = [], {}
    for i in range(5):
        a, b = "da%d" % i, "db%d" % i
        items.append(Item(a, "r", 1.0, {"kind": "detect"},
                          {"claim": "detected"}, ("pa%d" % i,)))
        items.append(Item(b, "r", 1.0, {"kind": "collateral"},
                          {"claim": "solvable" if i else "unsolvable"},
                          ("pb%d" % i,)))
        labels[a] = "detected"
        labels[b] = "solvable" if i else "unsolvable"
    assert leakage.metadata_hits(_paper(items=items), labels) == []


def test_derive_label_sets_ignores_a_class_the_sheet_already_publishes():
    """The held-out paper prints `split` on every item on purpose, having
    matched the class quotas so the tag is safe to show. Flagging a sheet field
    for predicting something the sheet states outright is noise."""
    items = [Item("i%d" % i, "r", 1.0, {"kind": "k", "tags_note": "replay"},
                  {"split": "replay", "frame_after": [[i]]}, ("p%d" % i,),
                  tags=("replay",)) for i in range(5)]
    items += [Item("j%d" % i, "r", 1.0, {"kind": "k", "tags_note": "heldout"},
                   {"split": "heldout", "frame_after": [[9, i]]}, ("q%d" % i,),
                   tags=("heldout",)) for i in range(5)]
    paper = _paper(items=items)
    derived = leakage.derive_label_sets(paper, paper.key("d"))
    assert "split" not in derived


def test_cheater_brief_contains_the_sheet_and_no_key():
    paper = _paper()
    brief = leakage.cheater_brief(paper.sheet("d"))
    assert "CHEAT" in brief and "the-secret-answer" not in brief


# -------------------------------------------------------------------- guards

def test_no_network_makes_sockets_raise():
    with guard.no_network():
        with pytest.raises(guard.NetworkForbidden):
            socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # and it puts the real one back, or every later test would be poisoned
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.close()


def test_synthetic_worlds_are_allowed():
    for world in guard.SYNTHETIC_WORLDS:
        assert guard.assert_synthetic_world(world) == "synthetic"


def test_a_sealed_game_is_refused():
    piles = guard.load_piles()
    sealed = piles.sealed_pile[0]
    with pytest.raises(guard.SealedPileError):
        guard.assert_synthetic_world(sealed)
    # and by its short id too, which the live API accepts
    with pytest.raises(guard.SealedPileError):
        guard.assert_synthetic_world(sealed.split("-", 1)[0])


def test_a_dev_game_needs_an_explicit_decision():
    piles = guard.load_piles()
    dev = piles.dev_pile[0]
    with pytest.raises(guard.UnknownGameError):
        guard.assert_synthetic_world(dev)
    assert guard.assert_synthetic_world(dev, allow_dev=True) == "dev"


def test_a_missing_world_id_is_a_bug_not_a_synthetic_run():
    with pytest.raises(guard.UnknownGameError):
        guard.assert_synthetic_world(None)


def test_provenance_records_the_cut_digest():
    prov = guard.provenance()
    assert len(prov["piles_sha256"]) == 64
    assert prov["n_sealed"] == 21


# ------------------------------------------------------------------- marking

class _Registry:
    """A stand-in rubric, so the driver can be tested without a real paper."""

    def __init__(self, fn):
        self.fn = fn

    def __call__(self, rubric_id):
        return Rubric(rubric_id, "test rubric", self.fn)


def _key(items, digest="d"):
    return {"paper_id": "p-test", "question_type": "heldout",
            "rubric_digest": digest,
            "items": [i.key_side() for i in items]}


def _install(monkeypatch, fn):
    monkeypatch.setattr(mark_mod, "rubric", _Registry(fn))
    monkeypatch.setattr(mark_mod, "digest", lambda: "d")


def test_missing_answers_are_unanswered_not_wrong(monkeypatch):
    _install(monkeypatch, lambda a, t, i: ItemScore(i.item_id, i.rubric_id,
                                                    i.points, i.points, "correct"))
    items = [_item("i1"), _item("i2")]
    report = mark_mod.mark(_key(items),
                           Submission("e", "p-test", {"i1": "x"}))
    verdicts = {s.item_id: s.verdict for s in report.scores}
    assert verdicts == {"i1": "correct", "i2": "unanswered"}
    assert report.fraction == 0.5


def test_a_rubric_cannot_award_more_than_the_item_is_worth(monkeypatch):
    _install(monkeypatch, lambda a, t, i: ItemScore(i.item_id, i.rubric_id,
                                                    99.0, i.points, "correct"))
    with pytest.raises(ExamError):
        mark_mod.mark(_key([_item("i1")]), Submission("e", "p-test", {"i1": "x"}))


def test_marking_across_papers_is_refused(monkeypatch):
    _install(monkeypatch, lambda a, t, i: ItemScore(i.item_id, i.rubric_id,
                                                    0.0, i.points, "wrong"))
    with pytest.raises(ExamError):
        mark_mod.mark(_key([_item("i1")]), Submission("e", "other", {"i1": "x"}))


def test_a_rubric_digest_change_is_carried_into_the_report(monkeypatch):
    _install(monkeypatch, lambda a, t, i: ItemScore(i.item_id, i.rubric_id,
                                                    i.points, i.points, "correct"))
    report = mark_mod.mark(_key([_item("i1")], digest="stale"),
                           Submission("e", "p-test", {"i1": "x"}))
    assert report.meta["rubric_digest_matches"] is False
    assert "warning" in report.meta


def test_confusion_reports_both_rates_and_keeps_abstentions_apart():
    """The bluffer's signature: sensitivity 1.0, specificity 0.0."""
    items = [Item("u%d" % i, "r", 1.0, {}, {"claim": "unsolvable"}, ("probe-u",))
             for i in range(3)]
    items += [Item("s%d" % i, "r", 1.0, {}, {"claim": "solvable"}, ("probe-s",))
              for i in range(2)]
    key = _key(items)
    scores = [ItemScore(i.item_id, "r", 0.0, 1.0, "correct",
                        {"said": "unsolvable"}) for i in items]
    report = Report("p-test", "bluffer", "verdict", "d", scores)
    conf = mark_mod.confusion(report, key, positive="unsolvable")
    assert conf["sensitivity"] == 1.0
    assert conf["specificity"] == 0.0

    abstaining = [ItemScore(i.item_id, "r", 0.0, 1.0, "abstained", {}) for i in items]
    conf2 = mark_mod.confusion(Report("p-test", "quiet", "verdict", "d", abstaining),
                               key, positive="unsolvable")
    assert conf2["sensitivity"] is None and conf2["specificity"] is None
    assert conf2["abstained_on_positive"] == 3
    assert conf2["abstained_on_negative"] == 2


def test_by_tag_breaks_a_single_percentage_apart():
    scores = [ItemScore("a", "r", 1.0, 1.0, "correct"),
              ItemScore("b", "r", 0.0, 1.0, "wrong")]
    report = Report("p", "e", "heldout", "d", scores)
    out = report.by_tag({"a": ("common",), "b": ("rare",)})
    assert out["common"]["fraction"] == 1.0
    assert out["rare"]["fraction"] == 0.0


# -------------------------------------------------------------- determinism

def test_canonical_is_stable_across_key_order():
    assert sha256({"a": 1, "b": 2}) == sha256({"b": 2, "a": 1})
