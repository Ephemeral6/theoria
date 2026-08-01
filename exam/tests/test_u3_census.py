# -*- coding: utf-8 -*-
"""Properties of the U3 census, and the negative controls that give it teeth.

A check that has never been seen to say no has not been shown to check
anything.  Roughly half this file is therefore controls: manuals that MUST NOT
attain, and discovery regressions that MUST fire.  The positive cases are here
to prove the controls are not passing by refusing everything.

Lean is required for the live cases.  Where it is absent they skip -- and the
skip is loud, because "the checker could not run" and "the checker said no"
are the two things a U3 evaluator must never confuse.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from exam import u3_census                      # noqa: E402
from freeze import u3                           # noqa: E402

LEAN = u3.find_lean()
needs_lean = pytest.mark.skipif(
    LEAN is None,
    reason="no lean on PATH — (a) cannot be discharged, so a verdict here "
           "would be undischarged, not negative")


# --------------------------------------------------------------- fixtures

#: A manual whose only theorem is trivially true.  `I` is the literal `true`,
#: so `inv_all` says "every reachable state satisfies the invariant that
#: everything satisfies".  It compiles, its axiom set is empty, and it proves
#: nothing -- the D-A3-007 class §1.2.1 names as the blocker.
TAUTOLOGY_MANUAL = """\
inductive Cell where
  | a
  | b
  deriving DecidableEq, Repr

structure St where
  pos : Cell
  deriving DecidableEq, Repr

def step (s : St) : St := { s with pos := .b }

def I (s : St) : Bool := true

def Goal (s : St) : Bool := s.pos == .b

inductive Reachable : St -> Prop where
  | init : Reachable { pos := .a }
  | step : ∀ s, Reachable s -> Reachable (step s)

theorem inv_init : I { pos := .a } = true := by decide

theorem inv_closed (s : St) : I s = true -> I (step s) = true := by
  intro _; cases s with | mk p => cases p <;> decide

theorem inv_all (s : St) (h : Reachable s) : I s = true := by
  induction h with
  | init => decide
  | step t _ ih => exact inv_closed t ih
"""

#: The same shape with a REAL discharged obligation: `I` genuinely rules a
#: state out, so the invariant carries content and `inv_all` is a claim about
#: the world rather than about `true`.
REAL_MANUAL = """\
inductive Cell where
  | a
  | b
  | c
  deriving DecidableEq, Repr

structure St where
  pos : Cell
  deriving DecidableEq, Repr

def step (s : St) : St :=
  match s.pos with
  | .a => { s with pos := .b }
  | .b => { s with pos := .a }
  | .c => { s with pos := .c }

def I (s : St) : Bool := s.pos != .c

def Goal (s : St) : Bool := s.pos == .c

inductive Reachable : St -> Prop where
  | init : Reachable { pos := .a }
  | step : ∀ s, Reachable s -> Reachable (step s)

theorem inv_init : I { pos := .a } = true := by decide

theorem inv_closed (s : St) : I s = true -> I (step s) = true := by
  intro h
  cases s with
  | mk p => cases p <;> simp_all [I, step]

theorem inv_all (s : St) (h : Reachable s) : I s = true := by
  induction h with
  | init => decide
  | step t _ ih => exact inv_closed t ih
"""

def _rename_theorems(src: str) -> str:
    """`inv_*` -> `frobnicate_*`.  Nothing else moves: same definitions, same
    proofs, same axiom sets, same content."""
    return (src.replace("inv_init", "frobnicate_init")
               .replace("inv_closed", "frobnicate_closed")
               .replace("inv_all", "frobnicate_all"))


#: `real` with every theorem renamed so `u3.classify_theorem`'s prefix matcher
#: recognises nothing.  It used to be the proof that the (c) gate keyed on
#: names -- this manual was `vacuous` and `REAL_MANUAL` was `discharged`.  It
#: is now the proof that the gate does NOT: it still attains, with every
#: `name_hint` reading `None`.
ODDLY_NAMED_MANUAL = _rename_theorems(REAL_MANUAL)

#: The renamed TAUTOLOGY, and the reason the regression above has teeth.
#: "renaming does not move the verdict" is trivially satisfied by an
#: adjudicator that attains everything; this manual must stay `vacuous` under
#: exactly the rename that stopped mattering for the real one.
ODDLY_NAMED_TAUTOLOGY = _rename_theorems(TAUTOLOGY_MANUAL)

#: A development whose only theorem is a real, useful, fully proved lemma about
#: the transition function -- and whose SHAPE is outside every clause §1.2.1
#: writes a non-vacuity requirement for.  Not an equality between two closed
#: numbers (that would be a straw man); an idempotence law of the kind a manual
#: genuinely contains.  E1 must call this `unclassified`: a confession that no
#: check ran, never `vacuous`, which is an accusation that one ran and refused.
UNCLASSIFIABLE_MANUAL = """\
inductive Cell where
  | a
  | b
  deriving DecidableEq, Repr

structure St where
  pos : Cell
  deriving DecidableEq, Repr

def step (s : St) : St := { s with pos := .b }

theorem step_idem (s : St) : step (step s) = step s := by
  cases s with | mk p => cases p <;> rfl
"""

#: `real` with EVERY proof replaced by `sorry`.  Sorrying only one theorem is
#: not a control for (b): §1.2 asks for *at least one* machine-checkable
#: theorem, so a development with one hole and two clean proofs still attains,
#: correctly.  To see the axiom whitelist say no, every theorem has to be
#: holed.
SORRIED_MANUAL = """\
inductive Cell where
  | a
  | b
  | c
  deriving DecidableEq, Repr

structure St where
  pos : Cell
  deriving DecidableEq, Repr

def step (s : St) : St :=
  match s.pos with
  | .a => { s with pos := .b }
  | .b => { s with pos := .a }
  | .c => { s with pos := .c }

def I (s : St) : Bool := s.pos != .c

def Goal (s : St) : Bool := s.pos == .c

inductive Reachable : St -> Prop where
  | init : Reachable { pos := .a }
  | step : ∀ s, Reachable s -> Reachable (step s)

theorem inv_init : I { pos := .a } = true := by sorry

theorem inv_closed (s : St) : I s = true -> I (step s) = true := by sorry

theorem inv_all (s : St) (h : Reachable s) : I s = true := by sorry
"""


def _write_book(tmp_path: Path, name: str, filename: str, src: str) -> Path:
    d = tmp_path / name
    d.mkdir(parents=True)
    (d / filename).write_text(src, encoding="utf-8")
    return d


# ------------------------------------------------- NEGATIVE CONTROL: verdict

@needs_lean
def test_negative_control_tautology_manual_does_not_attain(tmp_path):
    """A manual whose only theorem is trivially true MUST NOT attain U3.

    This is §1.2.1's blocker in one test.  The manual compiles and its axiom
    set is empty, so (a) and (b) both pass -- if (c) were not doing work this
    would come back `discharged`, and the endpoint would be forgeable by
    writing `def I _ := true`.
    """
    d = _write_book(tmp_path, "tautology", "theory.lean", TAUTOLOGY_MANUAL)
    site, = u3_census.discover_books(tmp_path)
    row = u3_census.adjudicate_site(site, probe=False, lean_bin=LEAN)

    assert row["criteria"]["a_compiles"] is True, (
        "the control is only meaningful if it COMPILES; a compile failure "
        "would make it a test of (a), not of (c): %r" % row.get("evidence"))
    assert row["verdict"] != "attained"
    assert row["label"] == "vacuous", row
    assert "constant" in json.dumps(row["criteria"], ensure_ascii=False)


@needs_lean
def test_positive_control_real_obligation_attains(tmp_path):
    """A manual with a real discharged obligation MUST attain.

    Without this, `test_negative_control_tautology_manual_does_not_attain`
    would pass just as well against a (c) check that rejects everything.
    """
    d = _write_book(tmp_path, "real", "theory.lean", REAL_MANUAL)
    site, = u3_census.discover_books(tmp_path)
    row = u3_census.adjudicate_site(site, probe=False, lean_bin=LEAN)

    assert row["criteria"]["a_compiles"] is True, row.get("evidence")
    assert row["verdict"] == "attained", row
    assert row["label"] == "discharged"


@needs_lean
def test_the_two_controls_differ_only_in_the_invariant(tmp_path):
    """The pair is a control only if (a) and (b) are held constant.

    Both manuals compile and both report an empty axiom set; the ONLY thing
    that moves the verdict is whether `I` has content.  Stated as a test so a
    future edit that accidentally breaks the tautology manual's compilation
    turns this red instead of quietly making the negative control vacuous.
    """
    _write_book(tmp_path, "tautology", "theory.lean", TAUTOLOGY_MANUAL)
    _write_book(tmp_path, "real", "theory.lean", REAL_MANUAL)
    rows = {s.directory.name: u3_census.adjudicate_site(s, lean_bin=LEAN)
            for s in u3_census.discover_books(tmp_path)}

    for name, row in rows.items():
        assert row["criteria"]["a_compiles"] is True, (name, row.get("evidence"))
        axioms = row["criteria"]["b_axioms"]
        assert axioms and all(axioms.values()), (name, axioms)

    assert rows["tautology"]["verdict"] != "attained"
    assert rows["real"]["verdict"] == "attained"


@needs_lean
def test_frozen_negative_control_on_disk_still_fails(tmp_path):
    """`cold-start-a3/theory/generated_l1_vacuous` — the freeze list's own
    named blocker (§9.2: "必须能抓住"). Adjudicated through the census's
    discovery rather than a hand-typed path, which is the point: the 2026-07-31
    sweep only caught it because someone remembered to type it."""
    vac = REPO / "cold-start-a3" / "theory" / "generated_l1_vacuous"
    if not vac.is_dir():
        pytest.skip("generated_l1_vacuous not present in this checkout")
    site, = u3_census.discover_books(vac)
    row = u3_census.adjudicate_site(site, probe=False, lean_bin=LEAN)
    assert row["verdict"] != "attained"
    assert row["label"] == "vacuous", row


@needs_lean
def test_sorried_manual_does_not_attain(tmp_path):
    """`sorryAx` is never whitelisted: an unfinished proof is not a proof.

    A second, independent way for (b) to say no -- the tautology control only
    exercises (c), so without this the axiom whitelist has never been seen to
    reject anything either.
    """
    _write_book(tmp_path, "sorried", "theory.lean", SORRIED_MANUAL)
    site, = u3_census.discover_books(tmp_path)
    row = u3_census.adjudicate_site(site, probe=False, lean_bin=LEAN)
    assert row["verdict"] != "attained", row
    assert row["label"] in ("axiom_violation", "failing_obligation"), row


# ------------------------------------------- NEGATIVE CONTROL: discovery (D1)

def test_level_lean_book_is_discovered(tmp_path):
    """REGRESSION for discovery defect D1 -- repaired in freeze 2026-08-01.

    `u3.evaluate()` used to look only for `<dir>/theory.lean`, so a development
    named `Level.lean` read as `no_evidence` -- indistinguishable from "there
    was no proof layer".  Four such books live in
    `theory-compiler/handover_packages/` and none of them were in the
    2026-07-31 sweep.  `u3.find_books` now takes any `.lean` that states a
    theorem, so the second half of this test flipped; the FIRST half is
    unchanged and is the standing regression, because the census must keep
    finding the book by its own enumeration.
    """
    _write_book(tmp_path, "pkg", "Level.lean", REAL_MANUAL)
    sites = u3_census.discover_books(tmp_path)
    assert len(sites) == 1
    assert sites[0].lean_files[0].name == "Level.lean"
    assert sites[0].route == "non-standard-name"

    # `u3.evaluate` alone can now see it too — D1 is closed at the source.
    # This assertion is the inverse of the one it replaces, and it is kept
    # rather than deleted so a regression IN FREEZE reads here as a failure
    # and not as a census that silently went back to carrying the fix alone.
    bare = u3.evaluate(sites[0].directory)
    assert bare["label"] != "no_evidence", (
        "freeze/u3.py stopped seeing non-standard book names — D1 has "
        "regressed; the census still finds it, which is why the first half "
        "of this test is still green and this half is not")


@needs_lean
def test_level_lean_book_is_adjudicated_not_reported_as_no_evidence(tmp_path):
    """The other half of D1: finding it must change the verdict.

    A census that discovered the book and still returned `no_evidence` would
    have moved the defect, not fixed it.  The *route* is no longer pinned to
    `eval_lean_source`: since the repair, `u3.evaluate` reaches the proof layer
    on its own and the census's fallback is correctly not taken.  What is
    pinned is the answer.
    """
    _write_book(tmp_path, "pkg", "Level.lean", REAL_MANUAL)
    site, = u3_census.discover_books(tmp_path)
    row = u3_census.adjudicate_site(site, lean_bin=LEAN)
    assert row["label"] != "no_evidence"
    assert row["verdict"] == "attained", row
    assert row["census_route"] in ("u3.evaluate",
                                   "u3.eval_lean_source:Level.lean"), row


@needs_lean
def test_direct_source_fallback_still_fires_when_the_adjudicator_goes_blind(
        tmp_path, monkeypatch):
    """The census's belt-and-braces route must stay ALIVE, not merely present.

    Since freeze's repair, `u3.evaluate` finds a `Level.lean` by itself, so the
    census's `eval_lean_source` fallback is never exercised by the happy path
    and could rot to an exception without any test noticing.  This restores the
    pre-repair adjudicator by blinding `u3.find_books`, and asserts the census
    still reaches `attained` — which is the whole reason exam enumerates books
    independently of the thing it is checking.
    """
    _write_book(tmp_path, "pkg", "Level.lean", REAL_MANUAL)
    monkeypatch.setattr(u3, "find_books", lambda *a, **k: [])

    site, = u3_census.discover_books(tmp_path)
    blinded = u3.evaluate(site.directory, lean_bin=LEAN)
    assert blinded["label"] == "no_evidence", (
        "the blinding did not take — this control proves nothing")

    row = u3_census.adjudicate_site(site, lean_bin=LEAN)
    assert row["verdict"] == "attained", row
    assert row["census_route"] == "u3.eval_lean_source:Level.lean", row


# ------------------------------------------- NEGATIVE CONTROL: discovery (D2)

def test_deeply_nested_book_is_discovered(tmp_path):
    """REGRESSION for discovery defect D2 -- repaired in freeze 2026-08-01.

    `u3.expand_targets` used to descend exactly one level, so the three books
    at `cold-start-a3/runs/<run>/generated/<variant>/` were never adjudicated.
    It walks to depth 12 now.  The census's own walk is the standing
    regression; the second assertion flipped and is kept inverted so a
    regression in freeze is visible from here.
    """
    deep = tmp_path / "runs" / "20260101T0000Z-x" / "generated" / "variant"
    deep.mkdir(parents=True)
    (deep / "theory.lean").write_text(REAL_MANUAL, encoding="utf-8")

    sites = u3_census.discover_books(tmp_path)
    assert [s.directory for s in sites] == [deep]

    reached = u3.expand_targets([tmp_path])
    assert deep in reached, (
        "freeze/u3.py stopped walking to this depth — D2 has regressed")


# --------------------------------------------------- exclusions are declared

def test_exclusions_are_recorded_with_a_reason(tmp_path):
    """A census whose exclusions are invisible cannot be audited.

    The archive under `monitor/runs/_worktree-scratch-archive/` holds
    byte-copies of other territories' books; counting them would inflate the
    denominator with duplicates.  Excluding it is right -- excluding it
    silently is not.
    """
    arch = tmp_path / "monitor" / "runs" / "_worktree-scratch-archive" / "x"
    arch.mkdir(parents=True)
    (arch / "theory.lean").write_text(REAL_MANUAL, encoding="utf-8")
    live = _write_book(tmp_path, "live", "theory.lean", REAL_MANUAL)

    recorded: list = []
    sites = u3_census.discover_books(tmp_path, record_exclusions=recorded)
    assert [s.directory for s in sites] == [live]
    paths = {e["path"] for e in recorded}
    assert "monitor/runs/_worktree-scratch-archive" in paths
    assert all(e["reason"] for e in recorded)


def test_lakefile_is_not_mistaken_for_a_book(tmp_path):
    """`lakefile.lean` is build scaffolding. Adjudicating it would manufacture
    a failing row out of a file that states no theorem."""
    d = tmp_path / "proj"
    d.mkdir()
    (d / "lakefile.lean").write_text("import Lake\nopen Lake DSL\n",
                                     encoding="utf-8")
    assert u3_census.discover_books(tmp_path) == []


# ------------------------------------------------------- census does not judge

@needs_lean
def test_census_delegates_every_verdict_to_freeze_u3(tmp_path, monkeypatch):
    """The census must contain no second opinion.

    If `freeze.u3` is the frozen adjudicator, then stubbing its judgment must
    change the census's answer completely.  A census that kept judging when
    the adjudicator was replaced would be a fork of a frozen endpoint.
    """
    _write_book(tmp_path, "real", "theory.lean", REAL_MANUAL)
    sentinel = {"verdict": "not_attained", "label": "unreadable",
                "criteria": {}, "evidence": {"source": "stub"}}
    monkeypatch.setattr(u3, "evaluate", lambda *a, **k: dict(sentinel))
    monkeypatch.setattr(u3, "eval_lean_source", lambda *a, **k: dict(sentinel))

    site, = u3_census.discover_books(tmp_path)
    row = u3_census.adjudicate_site(site, lean_bin=LEAN)
    assert row["label"] == "unreadable"
    assert row["evidence"]["source"] == "stub"


# ------------------------------------------------------------- summary shape

@needs_lean
def test_attainment_rate_carries_its_denominator_meaning(tmp_path):
    """`3/22` with no denominator attached is an invitation to quote it as
    STATS_RULES §1.2's endpoint. The two share a name and nothing else."""
    _write_book(tmp_path, "real", "theory.lean", REAL_MANUAL)
    _write_book(tmp_path, "taut", "theory.lean", TAUTOLOGY_MANUAL)
    result = u3_census.census(tmp_path, lean_bin=LEAN)
    s = result["summary"]
    assert (s["numerator"], s["denominator"]) == (1, 2)
    assert s["rate"] == 0.5
    assert "19" in s["not_the_frozen_endpoint"]
    assert "NOT" in s["denominator_meaning"]


@needs_lean
def test_kind_coverage_splits_permanent_non_attainers_from_gaps(tmp_path):
    """The census's most load-bearing output, and its own worst failure mode.

    The table answers: if the sealed campaign emits theorems of kind K, can E1
    ever award U3 for them?  It used to answer it by sniffing for the substring
    `"no executable"` in E1's `why` text.  freeze's 2026-08-01 repair stopped
    writing that sentence, and the table did not go red -- it went EMPTY.
    `kinds_that_can_never_attain: []`, a clean bill of health manufactured by a
    lookup miss, on the one output whose job is to report gaps.  It keys on
    `theorem_shape.KINDS_WITH_A_C_CHECK` now, so the next such change is an
    ImportError.

    `REAL_MANUAL` carries both sides of the split: `inv_all`/`inv_closed` are
    `invariant` (checked, and they pass), `inv_init` is a `point_claim` (no
    check, and there should not be one -- it is a supporting obligation, not a
    claim about the world).  A `point_claim` in the same list as a real gap
    would make the real gap unfindable, which is why the lists are separate.
    """
    _write_book(tmp_path, "oddly_named", "theory.lean", ODDLY_NAMED_MANUAL)
    result = u3_census.census(tmp_path, lean_bin=LEAN)

    kc = result["kind_coverage"]
    # The table is populated at all — the lookup-miss failure, asserted
    # directly rather than inferred from the absence of problems.
    assert kc["kinds"], kc
    assert "unknown" not in kc["kinds"], (
        "E1 emitted the retired kind `unknown`; the vocabulary moved back")

    assert kc["kinds_with_a_c_check"] == ["invariant", "prune", "unsolvable"]

    inv = kc["kinds"]["invariant"]
    assert inv["no_check_implemented"] is False
    assert inv["c_ok"] == 2, inv

    pc = kc["kinds"]["point_claim"]
    assert pc["no_check_implemented"] is True
    assert pc["permanent"] is True
    assert pc["c_ok"] == 0 and pc["c_unchecked"] == 1, pc

    # The split itself: a permanent non-attainer is not a defect and must not
    # be reported as one, while the union stays available for readers of the
    # older field.
    assert kc["permanent_non_attainers"] == ["point_claim"]
    assert kc["coverage_gaps"] == [], kc["coverage_gaps"]
    assert set(kc["kinds_that_can_never_attain"]) == (
        set(kc["coverage_gaps"]) | set(kc["permanent_non_attainers"]))

    # ... and the development attains anyway, through the invariant, despite
    # every theorem name being unrecognisable.  This is the repair.
    row, = result["rows"]
    assert row["label"] == "discharged", row


@needs_lean
def test_kind_coverage_reports_a_real_gap_as_a_gap(tmp_path):
    """NEGATIVE CONTROL for the test above.

    A split that has only ever been shown to put things in the harmless bin
    has not been shown to sort anything.  This manual's sole theorem is an
    equality between two closed terms under no relation hypothesis and with a
    hypothesis E1 cannot read -- outside every shape §1.2.1 writes a
    requirement for.  It must land `unclassified`, and `unclassified` must
    appear in `coverage_gaps` and NOT in `permanent_non_attainers`.
    """
    _write_book(tmp_path, "odd_shape", "theory.lean", UNCLASSIFIABLE_MANUAL)
    result = u3_census.census(tmp_path, lean_bin=LEAN)
    row, = result["rows"]
    assert row["verdict"] != "attained", row
    assert row["label"] == "unclassified", (
        "an unreadable shape must be a CONFESSION (`unclassified`), never an "
        "accusation (`vacuous`): %s" % row)

    kc = result["kind_coverage"]
    assert "unclassified" in kc["coverage_gaps"], kc
    assert "unclassified" not in kc["permanent_non_attainers"], kc
    assert kc["kinds"]["unclassified"]["c_unchecked"] >= 1, kc["kinds"]

    md = u3_census.to_markdown(result)
    assert "Coverage gaps (a defect): `unclassified`" in md, md


@needs_lean
def test_REGRESSION_F1_renaming_the_theorems_does_not_move_the_verdict(tmp_path):
    """STANDING REGRESSION for finding F1, which is now repaired.

    **The defect, recorded because deleting the evidence would leave the
    regression unexplained.**  Until 2026-08-01 E1 decided §1.2.1 (c) with
    `u3.classify_theorem`, a PREFIX MATCHER OVER THEOREM NAMES.
    `ODDLY_NAMED_MANUAL` is `REAL_MANUAL` with `inv_` renamed to
    `frobnicate_` -- same definitions, same proofs, same axiom sets, same
    content, and in this exact fixture pair one attained U3 and the other was
    labelled `vacuous`, the word §1.2.1 reserves for a manual that proved a
    tautology.  That is what a naming-convention detector standing in for the
    first of three frozen primary endpoints looks like when you reduce it to
    two files.  freeze repaired it: `theorem_shape.py` reads the kind off the
    STATEMENT and `classify_theorem` is demoted to `name_hint`, reported beside
    every theorem and read by nothing that decides anything.

    **What this test now pins, and why it would catch a return to name-keying.**
    Not merely that the pair agrees -- an adjudicator that said `discharged` to
    everything would satisfy that. Three things together:

    1. the pair agrees, and both attain;
    2. on the renamed book the name matcher recognises NOTHING
       (`name_hint is None` on every theorem) and the verdict is `attained`
       anyway -- so the deciding path demonstrably did not consult the name;
    3. the tautology control renamed the same way is STILL `vacuous`, so (1)
       is not being bought with a checker that stopped refusing.

    Restore the name matcher as the decider and (2) fails immediately.
    """
    _write_book(tmp_path, "named_inv", "theory.lean", REAL_MANUAL)
    _write_book(tmp_path, "named_frobnicate", "theory.lean", ODDLY_NAMED_MANUAL)
    _write_book(tmp_path, "named_frobnicate_taut", "theory.lean",
                ODDLY_NAMED_TAUTOLOGY)
    rows = {s.directory.name: u3_census.adjudicate_site(s, lean_bin=LEAN)
            for s in u3_census.discover_books(tmp_path)}

    # (a) and (b) are identical across all three — only names and `I` moved.
    for name, row in rows.items():
        assert row["criteria"]["a_compiles"] is True, (name, row.get("evidence"))
        assert all(row["criteria"]["b_axioms"].values()), (name, row)

    # (1) the pair agrees.
    assert rows["named_inv"]["verdict"] == "attained", rows["named_inv"]
    assert rows["named_frobnicate"]["verdict"] == "attained", (
        "renaming the theorems moved the verdict — E1's (c) gate is reading "
        "theorem NAMES again (finding F1, repaired 2026-08-01)")
    assert rows["named_inv"]["label"] == rows["named_frobnicate"]["label"]

    # ... and it agrees theorem for theorem, not just in the summary label.
    def kinds_by_position(row):
        return [t["kind"] for _, t in
                sorted((row["criteria"]["per_theorem"] or {}).items())]
    assert kinds_by_position(rows["named_inv"]) == \
        kinds_by_position(rows["named_frobnicate"])

    # (2) the name matcher recognises nothing on the renamed book, and the
    #     book attains regardless.  This is the assertion that dies the moment
    #     the deciding path consults a name again.
    frob = rows["named_frobnicate"]["criteria"]["per_theorem"]
    assert frob, rows["named_frobnicate"]
    assert all(t.get("name_hint") is None for t in frob.values()), (
        "the fixture no longer defeats the name matcher, so it can no longer "
        "witness that the name is not consulted: %s"
        % {n: t.get("name_hint") for n, t in frob.items()})
    assert any(t["c"].get("ok") is True for t in frob.values()), frob

    # (3) the checker still refuses.  Renaming buys the tautology nothing.
    taut = rows["named_frobnicate_taut"]
    assert taut["verdict"] != "attained", taut
    assert taut["label"] == "vacuous", (
        "a renamed tautology stopped being refused — (1) above is now being "
        "satisfied by an adjudicator that says yes to everything")


@needs_lean
def test_REGRESSION_F1_deadlock_paradigm_on_disk_attains(tmp_path):
    """The same regression against the real artefact rather than a fixture.

    The sokoban deadlock development compiles, reports an empty axiom set on
    all nine theorems, and carries `pat_witness` (a well-formed state the
    pattern accepts) and `level_is_winnable` (a plan from s0 to a goal).
    `STATS_RULES.md:123` names it as the PARADIGM of the kind of non-trivial
    theorem U3 means -- and until 2026-08-01 E1 labelled it `vacuous`, because
    its theorems are called `dead`, `pat_no_goal`, `closed_pinned`.  That was
    finding F1's most damaging instance: the rule text's own worked example
    failing the rule's implementation.

    It now reads `discharged` through the `prune` kind's new (c) check.  This
    test is the standing guard on that, and it asserts the three sub-checks by
    name rather than the label alone: a label can be reached by an adjudicator
    that stopped checking, three named provenances cannot.
    """
    verify = (REPO / "theory-compiler" / "runs"
              / "20260728T080019Z-C4-deadlock-lean" / "verify")
    src = verify / "Deadlock_corner.lean"
    if not src.exists():
        pytest.skip("C4 deadlock development not present in this checkout")

    row = u3.eval_lean_source(src, probe=False, lean_bin=LEAN, recorded={})
    assert row["criteria"]["a_compiles"] is True, row.get("evidence")
    assert all(row["criteria"]["b_axioms"].values()), row["criteria"]["b_axioms"]
    assert {"pat_witness", "level_is_winnable", "dead"} <= set(
        row["criteria"]["b_axioms"]), row["criteria"]["b_axioms"]
    assert row["label"] == "discharged", (
        "the deadlock paradigm stopped attaining — F1 has regressed, or the "
        "prune (c) check has: %s" % row["criteria"].get("c_residuals"))
    assert row["verdict"] == "attained"

    # It must attain THROUGH `dead`, the deadlock theorem itself — attaining
    # through some other theorem would leave the paradigm unadjudicated while
    # the row read green.
    assert "dead" in row["criteria"]["attaining"], row["criteria"]["attaining"]
    dead = row["criteria"]["per_theorem"]["dead"]
    assert dead["kind"] == "prune", dead
    assert dead["c"]["ok"] is True, dead["c"]
    subs = dead["c"]["sub_checks"]
    assert all(subs[k] for k in ("a_pattern_satisfiable",
                                 "b_pattern_excludes_goal",
                                 "c_level_solvable")), subs

    # `dead`'s kind came off the STATEMENT: a negative conclusion about a
    # predicate, from a quantified start state carrying pattern hypotheses.
    # A name matcher cannot produce that basis; only a parse can.
    assert dead["kind_basis"]["start_anchor"] == "quantified", dead["kind_basis"]
    assert dead["kind_basis"]["pattern_preds"], dead["kind_basis"]

    # And the name is demonstrably not what decides, because on this very file
    # the two DISAGREE and the kind wins.  `dead_persists` and `dead_closed`
    # are hinted `prune` by the old prefix matcher and are read as `invariant`;
    # `no_goal_pinned` is hinted `unsolvable` and is read as `unclassified`.
    per = row["criteria"]["per_theorem"]
    disagree = {n: (t.get("name_hint"), t["kind"]) for n, t in per.items()
                if t.get("name_hint") is not None
                and t.get("name_hint") != t["kind"]}
    assert disagree, (
        "no theorem here separates the hint from the kind, so this file can "
        "no longer witness that the name is not consulted: %s"
        % {n: (t.get("name_hint"), t["kind"]) for n, t in per.items()})

    # The sharpest single fact: a theorem the old matcher did not recognise at
    # all now carries the development to `discharged`.
    unhinted_attainers = [n for n in row["criteria"]["attaining"]
                          if per[n].get("name_hint") is None]
    assert unhinted_attainers, (
        "every attaining theorem is one the old prefix matcher recognised; "
        "this file no longer demonstrates the repair")

    # This real artefact also carries a real coverage gap, and the census must
    # say so in the honest word.  `vacuous` here would be an accusation E1
    # never earned.
    assert row["criteria"]["unclassified"], row["criteria"]
    assert row["flags"]["unclassified_theorems"] == row["criteria"]["unclassified"]


def test_bookless_certify_run_is_not_silently_dropped(tmp_path):
    """A run that reached certify and wrote no manual must still be counted.

    This is the flattering-denominator failure: a book-only census cannot see
    a run that never produced a book, so an arm that stops emitting Lean makes
    the rate go UP.  All four live carried legs of 2026-07-31 are this shape.
    """
    run = tmp_path / "runs" / "20260731T1240Z-leg"
    run.mkdir(parents=True)
    (run / "certify.json").write_text("[]", encoding="utf-8")

    assert u3_census.discover_books(tmp_path) == []
    claimants = u3_census.discover_claimants(tmp_path)
    assert claimants == [run]

    result = u3_census.census(tmp_path, lean_bin=None)
    bc = result["bookless_claimants"]
    assert bc["count"] == 1
    assert bc["attained"] == 0
    assert bc["labels"] == {"no_evidence": 1}
    # and it must NOT have moved the book denominator
    assert result["summary"]["denominator"] == 0


def test_bookless_claimants_are_not_folded_into_the_book_rate(tmp_path):
    """Folding them in would make the two failure modes interchangeable."""
    _write_book(tmp_path, "real", "theory.lean", REAL_MANUAL)
    run = tmp_path / "runs" / "leg"
    run.mkdir(parents=True)
    (run / "certify.json").write_text("[]", encoding="utf-8")

    result = u3_census.census(tmp_path, lean_bin=None)
    assert result["summary"]["denominator"] == 1, (
        "the bookless run leaked into the book denominator")
    assert result["bookless_claimants"]["count"] == 1


def test_a_book_dir_is_not_double_counted_as_a_claimant(tmp_path):
    """A run dir that has BOTH a certify record and a book belongs to the book
    census only; counting it twice inflates both denominators at once."""
    run = tmp_path / "runs" / "leg"
    run.mkdir(parents=True)
    (run / "certify.json").write_text("[]", encoding="utf-8")
    (run / "theory.lean").write_text(REAL_MANUAL, encoding="utf-8")

    books = u3_census.discover_books(tmp_path)
    assert [b.directory for b in books] == [run]
    assert u3_census.discover_claimants(
        tmp_path, [b.directory for b in books]) == []


def test_census_json_is_serialisable_and_path_sanitised(tmp_path):
    """Artefacts must not carry absolute paths (V27: twelve of them named
    whichever worktree ran last)."""
    _write_book(tmp_path, "real", "theory.lean", REAL_MANUAL)
    result = u3_census.census(tmp_path, lean_bin=None)
    blob = json.dumps(result, ensure_ascii=False)
    json.loads(blob)
    assert str(REPO) not in blob.replace("\\\\", "/")
    for row in result["rows"]:
        assert not Path(row["run"]).is_absolute()


# -------------------------------------------------------------------- CLI

def test_cli_expect_books_is_the_only_thing_that_fails(tmp_path):
    """A low attainment rate is a measurement; discovery finding nothing is a
    broken instrument.  Only the second is red."""
    _write_book(tmp_path, "taut", "theory.lean", TAUTOLOGY_MANUAL)
    # 0 attained out of 1 — still exit 0.
    assert u3_census.main(["--root", str(tmp_path)]) == 0
    # discovery under-delivering — exit 2.
    assert u3_census.main(["--root", str(tmp_path), "--expect-books", "5"]) == 2


def test_cli_runs_as_a_module(tmp_path):
    _write_book(tmp_path, "taut", "theory.lean", TAUTOLOGY_MANUAL)
    proc = subprocess.run(
        [sys.executable, "-m", "exam.u3_census", "--root", str(tmp_path)],
        cwd=str(REPO), capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, proc.stderr
    assert "books attained U3" in proc.stdout
