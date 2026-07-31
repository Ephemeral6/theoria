# -*- coding: utf-8 -*-
"""E1 keys (c) on what a theorem PROVES, not on what it is called.

exam → freeze, 2026-08-01, finding F1.  Roughly half of this file is negative
controls, because the repair is a LOOSENING: `prune` and `unclassified` kinds
used to fail closed, and anything that turns a "no" into a "yes" has to be shown
saying no in the cases where no is the right answer.  The controls here are:

  * a manual whose invariant is `true`            → must NOT attain (`vacuous`)
  * a deadlock theorem with no pattern witness    → must NOT attain (`vacuous`)
  * a deadlock theorem on an unwinnable level     → must NOT attain (`vacuous`)
  * a pattern predicate that is constant          → must NOT attain (`vacuous`)
  * a statement E1 cannot read                    → must NOT attain, and must
                                                    say `unclassified`, which is
                                                    a different word on purpose

and the positive controls prove the negatives are not passing by refusing
everything.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from freeze import theorem_shape as ts     # noqa: E402
from freeze import u3                      # noqa: E402

LEAN = u3.find_lean()
needs_lean = pytest.mark.skipif(
    LEAN is None,
    reason="no lean on PATH — (a) cannot be discharged, so a verdict here "
           "would be `undischarged`, not a negative")

C4_LEAN = (REPO / "theory-compiler" / "runs" / "20260728T080019Z-C4-deadlock-lean"
           / "verify" / "Deadlock_corner.lean")
C4_THEOREMS = ["pat_pins", "closed_pinned", "dead_closed", "no_goal_pinned",
               "pat_no_goal", "dead_persists", "dead", "pat_witness",
               "level_is_winnable"]


# ------------------------------------------------------------------ fixtures

#: A real invariant: `I` genuinely rules a state out.
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

#: The same manual with `I := true`.  Compiles, empty axiom set, proves nothing.
TAUTOLOGY_MANUAL = REAL_MANUAL.replace(
    "def I (s : St) : Bool := s.pos != .c",
    "def I (s : St) : Bool := true").replace(
    """theorem inv_closed (s : St) : I s = true -> I (step s) = true := by
  intro h
  cases s with
  | mk p => cases p <;> simp_all [I, step]""",
    """theorem inv_closed (s : St) : I s = true -> I (step s) = true := by
  intro _; cases s with | mk p => cases p <;> decide""")

#: exam's reduction of F1: the real manual, renamed.  Same definitions, same
#: proofs, same axioms, same content -- only the labels moved.
ODDLY_NAMED_MANUAL = (REAL_MANUAL
                      .replace("inv_init", "frobnicate_init")
                      .replace("inv_closed", "frobnicate_closed")
                      .replace("inv_all", "frobnicate_all"))

#: A minimal conditional-unsolvability (deadlock) development, the C4 shape at
#: four cells: `a` starts, `a→b→g` wins, `a→d` is a sink the goal is not in.
PRUNE_MANUAL = """\
inductive Cell where
  | a
  | b
  | g
  | d
  deriving DecidableEq, Repr

structure St where
  pos : Cell
  deriving DecidableEq, Repr

inductive Mv where
  | ab
  | ad
  | bg
  | dd
  deriving DecidableEq, Repr

def legal (s : St) (m : Mv) : Bool :=
  match s.pos, m with
  | .a, .ab => true
  | .a, .ad => true
  | .b, .bg => true
  | .d, .dd => true
  | _, _ => false

def applyMv (s : St) (m : Mv) : St :=
  match m with
  | .ab => { s with pos := .b }
  | .ad => { s with pos := .d }
  | .bg => { s with pos := .g }
  | .dd => { s with pos := .d }

def s0 : St := ⟨.a⟩

def Goal (s : St) : Bool := s.pos == .g

def Pat (s : St) : Bool := s.pos == .d

inductive ReachFrom (r : St) : St → Prop where
  | refl : ReachFrom r r
  | step : ∀ s m, ReachFrom r s → legal s m = true → ReachFrom r (applyMv s m)

theorem pat_no_goal : ∀ (s : St), Pat s = true → Goal s = false := by
  intro s hp
  cases s with
  | mk p => cases p <;> simp_all [Pat, Goal]

theorem dead : ∀ (r s : St), Pat r = true → ReachFrom r s → Goal s = false := by
  intro r s hp h
  have key : Pat s = true := by
    induction h with
    | refl => exact hp
    | step t m _ hl ih =>
        cases t with
        | mk p => cases p <;> cases m <;> simp_all [Pat, legal, applyMv]
  exact pat_no_goal s key

theorem pat_witness : Pat ⟨.d⟩ = true := by decide

theorem level_is_winnable : ∃ s : St, ReachFrom s0 s ∧ Goal s = true := by
  have h0 : ReachFrom s0 ⟨.b⟩ :=
    ReachFrom.step _ .ab ReachFrom.refl (by decide)
  have h1 : ReachFrom s0 ⟨.g⟩ :=
    ReachFrom.step _ .bg h0 (by decide)
  exact ⟨_, h1, by decide⟩
"""

_WITNESS_BLOCK = "theorem pat_witness : Pat ⟨.d⟩ = true := by decide\n\n"
_SOLVABLE_BLOCK = PRUNE_MANUAL[PRUNE_MANUAL.index("theorem level_is_winnable"):]

#: The same deadlock proof with no state shown to satisfy the pattern.  The
#: contract calls this out by name: 「模式无人满足的证书一律拒 ... 两条义务会空空
#: 地全过, `#print axioms` 会打印空集, 而它什么也没说」.
PRUNE_NO_PATTERN_WITNESS = PRUNE_MANUAL.replace(_WITNESS_BLOCK, "")

#: The same deadlock proof with no evidence the level is winnable at all.  A
#: dead-zone theorem on a level that was lost from the start is true and empty.
PRUNE_NO_SOLVABLE_WITNESS = PRUNE_MANUAL.replace(_SOLVABLE_BLOCK, "")

#: Every theorem renamed.  Nothing else changed.
PRUNE_RENAMED = (PRUNE_MANUAL
                 .replace("pat_no_goal", "frobnicate_one")
                 .replace("level_is_winnable", "frobnicate_two")
                 .replace("pat_witness", "frobnicate_three")
                 .replace("theorem dead", "theorem frobnicate_four"))

#: Compiles, empty axiom set, and states something E1 has no §1.2.1 clause for.
#: The theorem is deliberately NAMED as if it were an invariant.
UNREADABLE_MANUAL = """\
inductive Colour where
  | red
  | blue
  deriving DecidableEq, Repr

theorem inv_everything : Colour.red ≠ Colour.blue := by decide
"""


def _book(tmp_path: Path, name: str, src: str, filename: str = "theory.lean") -> Path:
    d = tmp_path / name
    d.mkdir(parents=True, exist_ok=True)
    (d / filename).write_text(src, encoding="utf-8")
    return d


def _offline(src: str, theorems, recorded=None):
    """Judge a development without Lean: synthesise a green compile and an
    empty axiom set, exactly as `test_u3.py`'s §9.2 control does.  This isolates
    (c): (a) and (b) are held at pass by construction."""
    return u3.judge_development(
        compiles=True, axiom_report={t: [] for t in theorems}, lean_src=src,
        probe_result=None, recorded=recorded or {}, evidence={"source": "test"})


# ================================================== F1: the paradigm case (C4)

def test_c4_deadlock_development_attains_through_the_deadlock_theorem():
    """`STATS_RULES.md:123` names this development as the paradigm of what U3
    means: 「它产出的、跨 28,672 个状态的死锁定理正是 U3 所指的那类非平凡定理」.
    Under the prefix matcher all nine theorems read `kind=unknown`, failed (c)
    closed, and the development was labelled `vacuous`."""
    assert C4_LEAN.exists(), C4_LEAN
    v = _offline(C4_LEAN.read_text(encoding="utf-8"), C4_THEOREMS)

    assert v["verdict"] == "attained"
    assert v["label"] == "discharged"
    dead = v["criteria"]["per_theorem"]["dead"]
    assert dead["kind"] == u3.PRUNE_KIND, dead["kind_basis"]
    assert dead["c"]["ok"] is True, dead["c"]
    subs = dead["c"]["sub_checks"]
    assert subs["pattern_preds"] == ["Pat", "wf"]
    assert subs["a_pattern_satisfiable"] and subs["b_pattern_excludes_goal"]
    assert subs["c_level_solvable"]
    # every sub-check names where it got its evidence
    assert "pat_witness" in subs["a_provenance"]
    assert "level_is_winnable" in subs["c_provenance"]


def test_c4_deadlock_theorem_is_recognised_after_renaming():
    """F1 as a property: the verdict may not move when only the labels move."""
    src = C4_LEAN.read_text(encoding="utf-8")
    renamed = src
    mapping = {t: "frobnicate_%d" % i for i, t in enumerate(C4_THEOREMS)}
    for old, new in mapping.items():
        renamed = renamed.replace(old, new)
    v = _offline(renamed, list(mapping.values()))

    assert v["verdict"] == "attained", v["criteria"]["kind_coverage"]
    assert v["criteria"]["per_theorem"][mapping["dead"]]["kind"] == u3.PRUNE_KIND


# ============================================ F1: exam's reduced fixture pair

@needs_lean
def test_renaming_the_theorems_no_longer_flips_the_verdict(tmp_path):
    """exam's one-line reduction of F1.  `ODDLY_NAMED_MANUAL` is `REAL_MANUAL`
    with `inv_` renamed to `frobnicate_`: same definitions, same proofs, same
    axiom sets, same content.  Before this repair one attained and the other
    was `vacuous`."""
    real = u3.evaluate(_book(tmp_path, "real", REAL_MANUAL), lean_bin=LEAN)
    odd = u3.evaluate(_book(tmp_path, "odd", ODDLY_NAMED_MANUAL), lean_bin=LEAN)

    for row in (real, odd):
        assert row["criteria"]["a_compiles"] is True, row.get("evidence")
    assert real["verdict"] == odd["verdict"] == "attained"
    assert real["label"] == odd["label"] == "discharged"


def test_the_name_hint_is_recorded_and_inert():
    """A name may still be a hint.  It may not be the decision.

    `inv_everything` proves that two colours differ — the old matcher would
    have read `invariant` off the prefix and run the invariant check on `def I`,
    which this manual does not even have."""
    v = _offline(UNREADABLE_MANUAL, ["inv_everything"])
    entry = v["criteria"]["per_theorem"]["inv_everything"]
    assert entry["name_hint"] == u3.INVARIANT_KIND
    assert entry["kind"] == u3.UNCLASSIFIED_KIND
    assert entry["c"]["ok"] is None


# ================================= the two verdicts one word used to conflate

def test_unclassified_is_not_vacuous():
    """exam's ask 1.  `vacuous` accuses a manual of proving a tautology;
    `unclassified` confesses that E1 does not know what kind this is.  A reader
    of the Phase 4 table must be able to tell them apart."""
    unreadable = _offline(UNREADABLE_MANUAL, ["inv_everything"])
    taut = _offline(TAUTOLOGY_MANUAL, ["inv_all"])

    assert unreadable["label"] == "unclassified"
    assert taut["label"] == "vacuous"
    # both are still not attained: the arithmetic did not move
    assert unreadable["verdict"] == taut["verdict"] == "not_attained"
    assert unreadable["flags"]["unclassified_theorems"] == ["inv_everything"]


def test_a_vacuous_label_names_which_theorems_it_accuses():
    """`vacuous` wins the label when a check ran and refused, but a development
    also holding unclassified theorems must say which ones the word covers —
    otherwise the conflation moves from the label to the reader."""
    v = _offline(TAUTOLOGY_MANUAL, ["inv_all", "inv_init"])
    assert v["label"] == "vacuous"
    assert v["criteria"]["refuted"] == ["inv_all"]
    assert v["criteria"]["unclassified"] == ["inv_init"]
    joined = " ".join(v["criteria"]["c_residuals"])
    assert "is NOT a finding about" in joined and "inv_init" in joined


def test_unclassified_ranks_above_vacuous_but_below_discharged():
    assert u3.STAGES[-1] == "discharged"
    assert (u3._STAGE_RANK["vacuous"] < u3._STAGE_RANK["unclassified"]
            < u3._STAGE_RANK["discharged"])
    assert len(set(u3.STAGES)) == len(u3.STAGES)


# =============================== NEGATIVE CONTROLS for the new `prune` check

@needs_lean
def test_positive_control_minimal_deadlock_development_attains(tmp_path):
    """Without this, the three negative controls below would pass just as well
    against a `prune` check that rejects everything."""
    v = u3.evaluate(_book(tmp_path, "prune", PRUNE_MANUAL), lean_bin=LEAN)
    assert v["criteria"]["a_compiles"] is True, v.get("evidence")
    assert v["verdict"] == "attained", v
    assert v["criteria"]["per_theorem"]["dead"]["kind"] == u3.PRUNE_KIND


@needs_lean
def test_negative_control_deadlock_without_a_pattern_witness(tmp_path):
    """§1.2.1-prune (a): 「存在至少一个良构状态满足该模式」.

    `CONTRACTS/deadlock_certificate_v0.1.md`: 模式无人满足的证书一律拒 — the two
    obligations pass vacuously, `#print axioms` prints the empty set, and the
    theorem says nothing.  This manual is byte-identical to the positive
    control except that `pat_witness` is gone."""
    v = u3.evaluate(_book(tmp_path, "nowit", PRUNE_NO_PATTERN_WITNESS),
                    lean_bin=LEAN)
    assert v["criteria"]["a_compiles"] is True, v.get("evidence")
    axioms = v["criteria"]["b_axioms"]
    assert axioms and all(axioms.values()), axioms
    assert v["verdict"] != "attained", v
    assert v["label"] == "vacuous", v
    subs = v["criteria"]["per_theorem"]["dead"]["c"]["sub_checks"]
    assert subs["a_pattern_satisfiable"] is False
    assert subs["b_pattern_excludes_goal"] and subs["c_level_solvable"]


@needs_lean
def test_negative_control_deadlock_on_a_level_never_shown_winnable(tmp_path):
    """§1.2.1-prune (c): 「该局本身可解，或另有独立见证」.

    Byte-identical to the positive control except that `level_is_winnable` is
    gone.  「在一局本来就输定的关卡上证一条死区定理，句句为真，什么也没证明。」"""
    v = u3.evaluate(_book(tmp_path, "nosolve", PRUNE_NO_SOLVABLE_WITNESS),
                    lean_bin=LEAN)
    assert v["criteria"]["a_compiles"] is True, v.get("evidence")
    assert v["verdict"] != "attained", v
    assert v["label"] == "vacuous", v
    subs = v["criteria"]["per_theorem"]["dead"]["c"]["sub_checks"]
    assert subs["c_level_solvable"] is False
    assert subs["a_pattern_satisfiable"] and subs["b_pattern_excludes_goal"]


def test_negative_control_a_constant_pattern_is_vacuous():
    """A pattern that every state satisfies is not a dead zone."""
    src = PRUNE_MANUAL.replace("def Pat (s : St) : Bool := s.pos == .d",
                               "def Pat (s : St) : Bool := true")
    v = _offline(src, ["pat_no_goal", "dead", "pat_witness", "level_is_winnable"])
    assert v["label"] == "vacuous", v
    c = v["criteria"]["per_theorem"]["dead"]["c"]
    assert c["ok"] is False
    assert "constant" in c["why"]


def test_negative_control_a_witness_resting_on_sorry_does_not_count():
    """A supporting obligation only supports if it passed (b) itself.  Here
    `pat_witness` compiled but reports `sorryAx`, so §1.2.1-prune (a) has no
    witness — the deadlock theorem's own axiom set is still clean."""
    v = u3.judge_development(
        compiles=True,
        axiom_report={"pat_no_goal": [], "dead": [], "level_is_winnable": [],
                      "pat_witness": ["sorryAx"]},
        lean_src=PRUNE_MANUAL, probe_result=None, recorded={},
        evidence={"source": "test"})
    assert v["verdict"] != "attained", v
    subs = v["criteria"]["per_theorem"]["dead"]["c"]["sub_checks"]
    assert subs["a_pattern_satisfiable"] is False


@needs_lean
def test_the_deadlock_pair_differs_only_in_the_witness(tmp_path):
    """The controls above are controls only if (a) and (b) are held constant.
    Both manuals compile and both report whitelisted axioms; the only thing
    that moves the verdict is whether the pattern was shown to be inhabited."""
    good = u3.evaluate(_book(tmp_path, "good", PRUNE_MANUAL), lean_bin=LEAN)
    bad = u3.evaluate(_book(tmp_path, "bad", PRUNE_NO_PATTERN_WITNESS),
                      lean_bin=LEAN)
    for name, row in (("good", good), ("bad", bad)):
        assert row["criteria"]["a_compiles"] is True, (name, row.get("evidence"))
        axioms = row["criteria"]["b_axioms"]
        assert axioms and all(axioms.values()), (name, axioms)
    assert good["verdict"] == "attained"
    assert bad["verdict"] != "attained"


@needs_lean
def test_the_deadlock_development_survives_renaming(tmp_path):
    v = u3.evaluate(_book(tmp_path, "renamed", PRUNE_RENAMED), lean_bin=LEAN)
    assert v["verdict"] == "attained", v
    assert v["criteria"]["per_theorem"]["frobnicate_four"]["kind"] == u3.PRUNE_KIND


# ============================ the frozen §9.2 control is still caught, by shape

@needs_lean
def test_frozen_negative_control_still_reads_vacuous():
    """`cold-start-a3/theory/generated_l1_vacuous` — 抓不住它就不许冻结.
    The repair loosened (c); this is the check that it did not loosen here."""
    v = u3.evaluate(REPO / "cold-start-a3" / "theory" / "generated_l1_vacuous",
                    probe=True, lean_bin=LEAN)
    assert v["verdict"] == "not_attained"
    assert v["label"] == "vacuous", v
    assert "constant" in json.dumps(v["criteria"], ensure_ascii=False)


# ================================================== D1: books are not named

def test_D1_a_book_called_Level_lean_is_adjudicated(tmp_path):
    """`u3.evaluate` used to look only for `<dir>/theory.lean`, so four handover
    packages whose book is `Level.lean` read `no_evidence` — indistinguishable
    from "there was no proof layer"."""
    d = _book(tmp_path, "pkg", REAL_MANUAL, filename="Level.lean")
    assert [p.name for p in u3.find_books(d)] == ["Level.lean"]
    v = u3.evaluate(d, lean_bin=LEAN)
    assert v["label"] != "no_evidence", v


def test_D1_a_lakefile_is_not_mistaken_for_a_book(tmp_path):
    """Build scaffolding states no theorem.  Adjudicating it would manufacture
    a failing row out of a file that claims nothing — and the test is the
    theorem, not the file name."""
    d = tmp_path / "proj"
    d.mkdir()
    (d / "lakefile.lean").write_text("import Lake\nopen Lake DSL\n", encoding="utf-8")
    assert u3.find_books(d) == []
    assert u3.evaluate(d)["label"] == "no_evidence"


def test_D1_theory_lean_is_still_preferred_when_both_exist(tmp_path):
    d = _book(tmp_path, "pkg", REAL_MANUAL, filename="Level.lean")
    (d / "theory.lean").write_text(REAL_MANUAL, encoding="utf-8")
    assert [p.name for p in u3.find_books(d)] == ["theory.lean", "Level.lean"]


# ============================================ D2: the sweep walks, and says so

def test_D2_a_deeply_nested_book_is_reached(tmp_path):
    """`expand_targets` used to descend one level, so the three books under
    `cold-start-a3/runs/<run>/generated/<variant>/` were unreachable and a
    hand-typed path list stood in for a census."""
    deep = tmp_path / "runs" / "20260101T0000Z-x" / "generated" / "variant"
    deep.mkdir(parents=True)
    (deep / "theory.lean").write_text(REAL_MANUAL, encoding="utf-8")
    assert u3.expand_targets([tmp_path]) == [deep]


def test_D2_exclusions_are_declared_not_silent(tmp_path):
    """A census whose exclusions are invisible cannot be audited."""
    for skipped in (".worktrees", "__pycache__"):
        d = tmp_path / skipped / "x"
        d.mkdir(parents=True)
        (d / "theory.lean").write_text(REAL_MANUAL, encoding="utf-8")
    live = _book(tmp_path, "live", REAL_MANUAL)

    recorded: list = []
    assert u3.expand_targets([tmp_path], record_exclusions=recorded) == [live]
    reasons = {Path(e["path"]).name: e["reason"] for e in recorded}
    assert set(reasons) == {".worktrees", "__pycache__"}
    assert all(reasons.values())


def test_D2_the_walk_does_not_double_count(tmp_path):
    """A run dir that is itself adjudicable and holds an adjudicable child must
    appear once each, not once per path that reaches it."""
    outer = _book(tmp_path, "outer", REAL_MANUAL)
    inner = _book(outer, "inner", REAL_MANUAL)
    found = u3.expand_targets([tmp_path, tmp_path])
    assert sorted(found) == sorted([outer, inner])


# ================================================ the shape parser's own edges

def test_shape_parser_reads_the_four_developments_on_disk():
    """The classifier is only as good as the parse.  These are the four
    generators the repo actually has, and their kinds are asserted here so a
    parser regression shows up as a kind change rather than as a census drift."""
    expected = {
        C4_LEAN: {"dead": u3.PRUNE_KIND, "dead_closed": u3.INVARIANT_KIND,
                  "pat_witness": u3.POINT_KIND,
                  "level_is_winnable": u3.WITNESS_KIND},
        REPO / "a0-spike" / "artifacts" / "A0.lean":
            {"unsolvable": u3.UNSOLVABLE_KIND, "inv_closed": u3.INVARIANT_KIND,
             "inv_init": u3.POINT_KIND},
        REPO / "cold-start-a0" / "theory" / "generated" / "theory.lean":
            {"inv_all": u3.INVARIANT_KIND, "inv_init": u3.POINT_KIND},
        REPO / "cold-start-a3" / "theory" / "generated_l1_vacuous" / "theory.lean":
            {"inv_all": u3.INVARIANT_KIND},
    }
    for path, kinds in expected.items():
        assert path.exists(), path
        dev = ts.parse_development(path.read_text(encoding="utf-8"))
        for name, kind in kinds.items():
            assert dev.theorems[name].kind == kind, (path.name, name,
                                                     dev.theorems[name].basis)


def test_shape_parser_fails_closed_on_an_unreadable_source():
    """A source that cannot be parsed must produce no kinds at all — never a
    kind it guessed."""
    dev = ts.parse_development(None)
    assert dev.theorems == {} and dev.parsed is False
    v = u3.judge_development(True, {"whatever": []}, None, None, {},
                             {"source": "test"})
    assert v["label"] == "unclassified"
    assert v["verdict"] == "not_attained"
