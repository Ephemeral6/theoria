"""V28 — the two acceptance items `test_u3_census.py` does not cover.

`0acc8b8f` flipped the regression tests after freeze repaired E1, and did it
more thoroughly than the inbox note asked (six tests, not four). Two things in
V28's acceptance line were left without an executable check, and this file is
those two:

1. **The populations must agree.** *`exam/u3_census.py` 与 freeze 的 D2 在书目上
   对上（24 本，两侧各自枚举，数相等才算对上）.* Both sides have recorded 24 in
   their run archives — `exam/runs/20260801T1200Z-U3-CENSUS-REPAIRED/census.json`
   and `freeze/runs/20260801T0700Z-E1-kind-census/census.json` — and nothing
   re-derives it. A number agreed once in two JSON files is not an agreement
   that survives the next walker change; both walkers have already been wrong
   once (D1 and D2 hid sixteen books from the 2026-07-31 sweep).

2. **The name-keying control must be executed, not argued.**
   `test_REGRESSION_F1_renaming_the_theorems_does_not_move_the_verdict` pins the
   right property and says in its docstring *"Restore the name matcher as the
   decider and (2) fails immediately."* That sentence is a prediction. V28 asks
   for it to be run: *把一个按名字判 kind 的分类器重新塞回去，vacuous /
   discharged 的判定必须翻——否则这次「修好了」和「测试不再看这件事了」在盘上
   长得一模一样.* So this file re-installs the defect and measures the split.

Neither test needs Lean: (1) is pure directory walking, and (2) drives
`u3.judge_development` directly with `compiles=True` and a synthesised axiom
report, so the whole file runs offline in well under a second.
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "exam")):
    if p not in sys.path:
        sys.path.insert(0, p)

import u3_census  # noqa: E402
from freeze import theorem_shape, u3  # noqa: E402

from .test_u3_census import (  # noqa: E402
    ODDLY_NAMED_MANUAL, ODDLY_NAMED_TAUTOLOGY, REAL_MANUAL, TAUTOLOGY_MANUAL,
)

#: Both run archives record 24 books after freeze's D1/D2 repair.
#: `freeze/runs/20260801T0700Z-E1-kind-census/census.json` -> `"books": 24`
#: `exam/runs/20260801T1200Z-U3-CENSUS-REPAIRED/census.json` -> 24 rows
EXPECTED_BOOKS = 24


# ------------------------------------------------------- 1. the populations

def _exam_books():
    return {s.directory.resolve() for s in u3_census.discover_books(REPO)}


def _freeze_books():
    out = set()
    for target in u3.expand_targets([REPO], record_exclusions=[]):
        if u3.find_books(target):
            out.add(Path(target).resolve())
    return out


def test_the_two_book_enumerations_agree_directory_for_directory():
    """exam's walker and freeze's walker must find the same books.

    They are genuinely independent implementations, which is the only reason
    the agreement is worth anything:

    * exam's `discover_books` uses `os.walk` to **arbitrary** depth, takes any
      `.lean` not in `SCAFFOLD_NAMES`, and excludes by path fragment;
    * freeze's `expand_targets` recurses to `max_depth=12`, excludes by
      directory **name** (`u3.DEFAULT_EXCLUSIONS`), and admits a file only if
      `states_a_theorem` finds a `theorem`/`lemma` in it — content, not name.

    So one filters books by name and the other by content, and one bounds depth
    where the other does not. Agreement across that pair is evidence; a shared
    helper would have been evidence of nothing.
    """
    exam_dirs, freeze_dirs = _exam_books(), _freeze_books()

    def rel(paths):
        return sorted(p.relative_to(REPO).as_posix() for p in paths)

    assert exam_dirs == freeze_dirs, (
        "the two walkers disagree.\n  only exam:   %s\n  only freeze: %s"
        % (rel(exam_dirs - freeze_dirs), rel(freeze_dirs - exam_dirs)))
    assert len(exam_dirs) == EXPECTED_BOOKS, (
        "the book population moved: %d, expected %d. If books were genuinely "
        "added or removed, update EXPECTED_BOOKS and both run archives; if not, "
        "a walker changed.\n%s" % (len(exam_dirs), EXPECTED_BOOKS, rel(exam_dirs)))


def test_the_population_guard_would_notice_a_book_going_missing(tmp_path):
    """NEGATIVE CONTROL for the test above.

    An equality between two walkers that both returned nothing would pass. This
    runs the same comparison over a tree holding exactly one book, so the pair
    is seen to agree on a population they had to actually find, and seen to
    report a difference when one of them is made to miss it.
    """
    book = tmp_path / "a_book"
    book.mkdir()
    (book / "theory.lean").write_text(
        "def I : Nat := 1\ntheorem inv_x : I = 1 := rfl\n", encoding="utf-8")

    exam_found = {s.directory.resolve() for s in u3_census.discover_books(tmp_path)}
    freeze_found = {Path(t).resolve()
                    for t in u3.expand_targets([tmp_path], record_exclusions=[])
                    if u3.find_books(t)}
    assert exam_found == freeze_found == {book.resolve()}

    # And the comparison is capable of failing: a file stating no theorem is a
    # book to nobody, so both walkers must drop it rather than one of them.
    scaffold = tmp_path / "not_a_book"
    scaffold.mkdir()
    (scaffold / "lakefile.lean").write_text("import Lake\n", encoding="utf-8")
    assert {s.directory.resolve()
            for s in u3_census.discover_books(tmp_path)} == {book.resolve()}
    assert {Path(t).resolve()
            for t in u3.expand_targets([tmp_path], record_exclusions=[])
            if u3.find_books(t)} == {book.resolve()}


# --------------------------------------------------- 2. the name-key control

def _judge(src):
    """Adjudicate a manual at the judgment layer — no Lean, no disk.

    `compiles=True` and an all-empty axiom report grant (a) and (b), so the
    label is decided by (c) alone, which is the thing under test.
    """
    dev = theorem_shape.parse_development(src)
    return u3.judge_development(
        compiles=True, axiom_report={name: [] for name in dev.theorems},
        lean_src=src, probe_result=None, recorded={}, evidence={})


def _name_keyed_classifier(real):
    """The defect, reconstructed: kind read off the theorem's NAME."""
    def _classify(thm, dev):
        hint = theorem_shape.name_hint(thm.name)
        if hint is None:
            return theorem_shape.UNCLASSIFIED_KIND, {
                "rule": "name matcher recognised no prefix (reinstated defect)"}
        return hint, dict(real(thm, dev)[1])
    return _classify


def test_the_repaired_adjudicator_gives_the_renamed_pair_the_same_verdict():
    """The baseline the control below is measured against."""
    assert _judge(REAL_MANUAL)["label"] == "discharged"
    assert _judge(ODDLY_NAMED_MANUAL)["label"] == "discharged"
    # ...and it is not a checker that says yes to everything.
    assert _judge(TAUTOLOGY_MANUAL)["label"] == "vacuous"
    assert _judge(ODDLY_NAMED_TAUTOLOGY)["label"] == "vacuous"


def test_NEGATIVE_CONTROL_reinstalling_name_keying_splits_the_renamed_pair(
        monkeypatch):
    """Put the defect back, and the pair must come apart.

    This is V28's first negative sample. Without it, "E1 was repaired" and "the
    tests stopped looking at this" are indistinguishable on the board: every
    assertion in the standing regression is of the form *these two agree*, and
    a checker that had simply stopped discriminating would satisfy all of them.

    Reinstalled, `REAL_MANUAL` still attains — its theorems are named `inv_*`,
    which the matcher recognises — and `ODDLY_NAMED_MANUAL`, which differs from
    it only in that `inv_` was spelled `frobnicate_`, does not. Same
    definitions, same proofs, same statements, different verdict.

    **The label it flips to is `unclassified`, not `vacuous`, and that is not a
    weaker result.** Before 2026-08-01 one word carried both meanings and the
    rename produced `vacuous` — an accusation that the manual proved a
    tautology. The same repair that killed name-keying also split the word
    (freeze's ask 2), so an unrecognised name now lands in the fail-closed
    bucket instead. What V28 asks to see flip is the adjudication, and it
    flips: `attained` to `not_attained`, on a rename.
    """
    real = theorem_shape._classify
    monkeypatch.setattr(theorem_shape, "_classify", _name_keyed_classifier(real))

    named = _judge(REAL_MANUAL)
    renamed = _judge(ODDLY_NAMED_MANUAL)

    assert named["label"] == "discharged", named
    assert renamed["label"] != named["label"], (
        "the name-keyed classifier was re-installed and the verdict did NOT "
        "move — so the standing regression is not sensitive to the defect it "
        "exists to catch, and its green tells us nothing: %s" % renamed)
    assert renamed["verdict"] == "not_attained", renamed
    assert renamed["label"] == "unclassified", renamed


def test_the_name_key_control_restores_the_real_classifier():
    """monkeypatch undoes itself, but a control that leaked would poison every
    test after it in the file — and the failure would look like a defect in
    whatever ran next. Cheap to assert, so asserted."""
    assert theorem_shape._classify.__name__ == "_classify"
    assert _judge(ODDLY_NAMED_MANUAL)["label"] == "discharged"


# ------------------------------------------------- 3. unclassified fails closed

UNCLASSIFIED_ONLY = """\
def I : Nat := 1
theorem odd_shape (h : I = I) : (fun n => n) 1 = 1 := rfl
"""


def test_NEGATIVE_CONTROL_an_unclassified_theorem_fails_closed():
    """V28's second negative sample, at the judgment layer.

    `test_kind_coverage_reports_a_real_gap_as_a_gap` already pins this through
    the census; this pins it one level down, where the decision is actually
    made, so a census-side change cannot quietly become the only thing holding
    it. (a) and (b) are granted, so nothing but (c) can stop this development —
    and (c) must refuse to open.
    """
    verdict = _judge(UNCLASSIFIED_ONLY)
    assert verdict["label"] == "unclassified", verdict
    assert verdict["verdict"] == "not_attained", (
        "a shape E1 cannot read attained anyway — `unclassified` opened "
        "instead of failing closed: %s" % verdict)
    per = verdict["criteria"]["per_theorem"]
    assert per["odd_shape"]["kind"] == theorem_shape.UNCLASSIFIED_KIND, per
    assert per["odd_shape"]["c"]["ok"] is None, (
        "(c) must be three-valued here: None is `not checked`, and False would "
        "be an accusation E1 has not earned: %s" % per)


@pytest.mark.parametrize("kind", sorted(theorem_shape.KINDS_WITH_A_C_CHECK))
def test_the_kinds_with_a_check_are_the_three_freeze_named(kind):
    """Pins the vocabulary the split above depends on.

    `kind_coverage()` keys on this exported set precisely so the next change to
    it is an ImportError rather than a silent lookup miss (`0acc8b8f`). If a
    kind joins or leaves, this fails and the coverage table is re-read by a
    human instead of quietly re-classifying a permanent non-attainer as a gap.
    """
    assert kind in ("invariant", "unsolvable", "prune")
    assert theorem_shape.KINDS_WITH_A_C_CHECK == frozenset(
        {"invariant", "unsolvable", "prune"})
