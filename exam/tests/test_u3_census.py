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

#: The `real` manual with every theorem renamed so `u3.classify_theorem`'s
#: prefix matcher no longer recognises it.  Identical proof, identical axioms,
#: identical content -- only the names moved.  Used to show that the (c) gate
#: keys on names.
ODDLY_NAMED_MANUAL = (REAL_MANUAL
                      .replace("inv_init", "frobnicate_init")
                      .replace("inv_closed", "frobnicate_closed")
                      .replace("inv_all", "frobnicate_all"))

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
    """REGRESSION for discovery defect D1.

    `u3.evaluate()` looks only for `<dir>/theory.lean`, so a development named
    `Level.lean` reads as `no_evidence` -- indistinguishable from "there was
    no proof layer".  Four such books live in
    `theory-compiler/handover_packages/` and none of them were in the
    2026-07-31 sweep.  The census must find the book AND route it to the
    adjudicator's source path.
    """
    _write_book(tmp_path, "pkg", "Level.lean", REAL_MANUAL)
    sites = u3_census.discover_books(tmp_path)
    assert len(sites) == 1
    assert sites[0].lean_files[0].name == "Level.lean"
    assert sites[0].route == "non-standard-name"

    # And u3.evaluate alone genuinely cannot see it — the defect is real, not
    # a straw man.  If this ever starts failing, freeze/u3.py grew a walker
    # and this census's D1 justification should be revisited.
    bare = u3.evaluate(sites[0].directory)
    assert bare["label"] == "no_evidence", (
        "freeze/u3.py now sees non-standard book names; re-check D1")


@needs_lean
def test_level_lean_book_is_adjudicated_not_reported_as_no_evidence(tmp_path):
    """The other half of D1: finding it must change the verdict.

    A census that discovered the book and still returned `no_evidence` would
    have moved the defect, not fixed it.
    """
    _write_book(tmp_path, "pkg", "Level.lean", REAL_MANUAL)
    site, = u3_census.discover_books(tmp_path)
    row = u3_census.adjudicate_site(site, lean_bin=LEAN)
    assert row["label"] != "no_evidence"
    assert row["verdict"] == "attained", row
    assert row["census_route"] == "u3.eval_lean_source:Level.lean"


# ------------------------------------------- NEGATIVE CONTROL: discovery (D2)

def test_deeply_nested_book_is_discovered(tmp_path):
    """REGRESSION for discovery defect D2: `u3.expand_targets` descends one
    level.  Three books live at `cold-start-a3/runs/<run>/generated/<variant>/`
    and were never adjudicated."""
    deep = tmp_path / "runs" / "20260101T0000Z-x" / "generated" / "variant"
    deep.mkdir(parents=True)
    (deep / "theory.lean").write_text(REAL_MANUAL, encoding="utf-8")

    sites = u3_census.discover_books(tmp_path)
    assert [s.directory for s in sites] == [deep]

    reached = u3.expand_targets([tmp_path])
    assert deep not in reached, (
        "freeze/u3.py now walks; re-check D2's justification")


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
def test_kind_coverage_names_the_kinds_that_can_never_attain(tmp_path):
    """The census's most load-bearing output.

    A theorem of kind `unknown` fails closed and its development is labelled
    `vacuous` however good the proof is. That must be visible as a coverage
    gap, not buried as an attainment number -- otherwise a sealed campaign
    whose theorems are named unluckily reports U3 = 0/19 and the paper says
    the manuals were vacuous.
    """
    _write_book(tmp_path, "oddly_named", "theory.lean", ODDLY_NAMED_MANUAL)
    result = u3_census.census(tmp_path, lean_bin=LEAN)

    kc = result["kind_coverage"]
    assert "unknown" in kc["kinds"]
    assert kc["kinds"]["unknown"]["no_check_implemented"] is True
    assert "unknown" in kc["kinds_that_can_never_attain"]
    # ... and the development it belongs to reads `vacuous` despite proving
    # exactly what the `real` control proves.  This is the finding.
    row, = result["rows"]
    assert row["label"] == "vacuous", row


@needs_lean
def test_FINDING_renaming_the_theorems_alone_flips_the_verdict(tmp_path):
    """FINDING F1, as a test: E1's (c) gate keys on THEOREM NAMES.

    `ODDLY_NAMED_MANUAL` is `REAL_MANUAL` with `inv_` renamed to
    `frobnicate_`.  Same definitions, same proofs, same axiom sets, same
    content.  One attains U3; the other is labelled `vacuous` -- the word
    §1.2.1 reserves for a manual that proved a tautology.

    This is why the sokoban deadlock development at
    `theory-compiler/runs/20260728T080019Z-C4-deadlock-lean/verify/` reads
    `vacuous` in the census: its theorems are named `dead`, `pat_no_goal`,
    `closed_pinned`.  STATS_RULES.md:123 names that development as the
    paradigm of "the kind of non-trivial theorem U3 means".

    Failing closed is the correct safety direction and this test does not ask
    for it to be reversed.  What it pins is that the *label* is wrong: an
    unclassified theorem is not a vacuous one, and a Phase 4 paper cannot tell
    the difference from the output as it stands.

    If freeze/ fixes this (a distinct `unclassified` label, or a (c) check for
    the prune/deadlock kind), this test should go red and be rewritten to
    match — it is a record of a defect, not a specification of it.
    """
    _write_book(tmp_path, "named_inv", "theory.lean", REAL_MANUAL)
    _write_book(tmp_path, "named_frobnicate", "theory.lean", ODDLY_NAMED_MANUAL)
    rows = {s.directory.name: u3_census.adjudicate_site(s, lean_bin=LEAN)
            for s in u3_census.discover_books(tmp_path)}

    # (a) and (b) are identical across the pair — only the name moved.
    for name, row in rows.items():
        assert row["criteria"]["a_compiles"] is True, (name, row.get("evidence"))
        assert all(row["criteria"]["b_axioms"].values()), (name, row)

    assert rows["named_inv"]["verdict"] == "attained"
    assert rows["named_frobnicate"]["verdict"] != "attained"
    assert rows["named_frobnicate"]["label"] == "vacuous"

    why = json.dumps(rows["named_frobnicate"]["criteria"], ensure_ascii=False)
    assert "no executable" in why and "unknown" in why, why


@needs_lean
def test_FINDING_deadlock_paradigm_on_disk_is_labelled_vacuous(tmp_path):
    """FINDING F1 against the real artefact rather than a fixture.

    Guards the claim in the report: this development compiles, every theorem
    reports an empty axiom set, it carries `pat_witness` (a well-formed state
    the pattern accepts) and `level_is_winnable` (a plan from s0 to a goal) --
    and E1 still calls it vacuous.  If someone fixes freeze/u3.py this test
    goes red, which is the correct signal.
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
    assert row["label"] == "vacuous", (
        "freeze/u3.py may have grown a prune/deadlock (c) check — "
        "re-verify the report's finding F1")
    assert row["verdict"] != "attained"


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
