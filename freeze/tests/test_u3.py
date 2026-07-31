# -*- coding: utf-8 -*-
"""Tests for freeze/u3.py — E1 / U3 attainment (STATS_RULES.md §1.2, §1.2.1, §9.2, §9.14).

The negative controls are the point of this file:
  * the frozen §9.2 control — cold-start-a3/theory/generated_l1_vacuous
    (D-A3-007's `I := true`) MUST read not-attained/vacuous;
  * a failing obligation MUST read not-attained;
  * a `sorry` MUST fail (b) via sorryAx;
  * Classical.choice MUST fail (b) and be flagged for the §1.2 sensitivity listing.
Positive material: a0-spike and cold-start-a0 carry discharged Lean proofs and
MUST read attained.
"""

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "freeze"))

import u3  # noqa: E402

LEAN = u3.find_lean()
needs_lean = pytest.mark.skipif(LEAN is None, reason="no Lean binary on this machine")

VACUOUS_DIR = REPO / "cold-start-a3" / "theory" / "generated_l1_vacuous"
REAL_L1_DIR = REPO / "cold-start-a3" / "theory" / "generated_l1"
A0_SPIKE = REPO / "a0-spike"
COLD_A0 = REPO / "cold-start-a0"


# ------------------------------------------------------------------ (b) axioms

def test_whitelist_passes_propext_quot_sound():
    j = u3.judge_axioms(["propext", "Quot.sound"])
    assert j["ok"] and not j["classical_choice_needed"]


def test_empty_axiom_set_passes():
    assert u3.judge_axioms([])["ok"]


def test_classical_choice_fails_b_and_is_flagged():
    j = u3.judge_axioms(["propext", "Classical.choice", "Quot.sound"])
    assert not j["ok"]
    assert j["classical_choice_needed"]
    assert "Classical.choice" in j["outside_whitelist"]


def test_sorry_ax_and_of_reduce_bool_never_allowed():
    for ax in ("sorryAx", "Lean.ofReduceBool"):
        j = u3.judge_axioms([ax])
        assert not j["ok"]
        assert ax in j["never_allowed"]


def test_parse_axiom_lines_both_shapes():
    text = ("'unsolvable' depends on axioms: [propext, Quot.sound]\n"
            "'inv_init' does not depend on any axioms\n")
    parsed = u3.parse_axiom_lines(text)
    assert parsed == {"unsolvable": ["propext", "Quot.sound"], "inv_init": []}


# ------------------------------------------------------------- (c) static scan

def test_static_scan_catches_the_frozen_vacuous_control():
    src = (VACUOUS_DIR / "theory.lean").read_text(encoding="utf-8")
    defs = u3.scan_defs(src)
    assert defs["I"]["constant"] == "true"


def test_static_scan_passes_the_real_l1_invariant():
    src = (REAL_L1_DIR / "theory.lean").read_text(encoding="utf-8")
    defs = u3.scan_defs(src)
    assert defs["I"]["constant"] is None
    assert defs["I"]["ret_type"] == "Bool"


def test_static_scan_prop_style_a0():
    src = (A0_SPIKE / "artifacts" / "A0.lean").read_text(encoding="utf-8")
    defs = u3.scan_defs(src)
    assert defs["I"]["constant"] is None
    assert defs["I"]["ret_type"] == "Prop"
    assert defs["Goal"]["constant"] is None


# ---------------------------------------------- negative control: vacuous (c)

def test_vacuous_development_reads_not_attained_without_lean():
    """The §9.2 control must be caught even lean-free (static path):
    a synthesized green compile + empty axioms over the real vacuous source."""
    src = (VACUOUS_DIR / "theory.lean").read_text(encoding="utf-8")
    v = u3.judge_development(
        compiles=True, axiom_report={"inv_all": []}, lean_src=src,
        probe_result=None, recorded={"theorems_present": ["inv_all"]},
        evidence={"source": "test"})
    assert v["verdict"] == "not_attained"
    assert v["label"] == "vacuous"


@needs_lean
def test_vacuous_dir_live_reads_vacuous():
    v = u3.evaluate(VACUOUS_DIR)
    assert v["verdict"] == "not_attained"
    assert v["label"] == "vacuous"


@needs_lean
def test_real_l1_dir_live_reads_attained_with_probe():
    v = u3.evaluate(REAL_L1_DIR, probe=True, lean_bin=LEAN)
    assert v["verdict"] == "attained"
    assert v["label"] == "discharged"


@needs_lean
def test_probe_detects_definitional_constancy():
    r = u3.probe_constancy(LEAN, VACUOUS_DIR / "theory.lean")
    assert r["probed"] and r["constant"] == "true"
    r2 = u3.probe_constancy(LEAN, REAL_L1_DIR / "theory.lean")
    assert r2["probed"] and r2["constant"] is None


# ------------------------------------- negative control: failing obligation (a)

def _arm_run(tmp_path, records):
    (tmp_path / "certify.json").write_text(
        json.dumps(records), encoding="utf-8")
    return tmp_path


def test_failing_obligation_reads_not_attained(tmp_path):
    run = _arm_run(tmp_path, [{
        "cheap_green": True, "proof_layer_available": True,
        "expensive": {"available": True, "ok": False, "returncode": 1,
                      "stdout": "", "stderr": "type mismatch",
                      "detail": "lean rejected the file"},
    }])
    v = u3.evaluate(run)
    assert v["verdict"] == "not_attained"
    assert v["label"] == "failing_obligation"
    assert v["criteria"]["a_compiles"] is False


@needs_lean
def test_live_failing_proof_reads_failing_obligation(tmp_path):
    bad = tmp_path / "theory.lean"
    bad.write_text("theorem bad : 1 = 2 := rfl\n", encoding="utf-8")
    v = u3.evaluate(tmp_path, lean_bin=LEAN)
    assert v["verdict"] == "not_attained"
    assert v["label"] == "failing_obligation"


@needs_lean
def test_live_sorry_fails_b_via_sorry_ax(tmp_path):
    f = tmp_path / "theory.lean"
    f.write_text("theorem holed : 1 = 1 := by sorry\n", encoding="utf-8")
    v = u3.evaluate(tmp_path, lean_bin=LEAN)
    assert v["verdict"] == "not_attained"
    # sorry may surface as a compile warning (rc 0) with sorryAx in the axiom
    # report, or as a rejection, depending on the toolchain; both are refusals.
    assert v["label"] in ("axiom_violation", "failing_obligation")
    if v["label"] == "axiom_violation":
        per = v["criteria"]["per_theorem"]["holed"]
        assert "sorryAx" in per["b"]["never_allowed"]


@needs_lean
def test_live_classical_tautology_fails_b_and_flags(tmp_path):
    """The G1 counterexample from STATS_RULES §1.2: a true, compiling,
    contentless classical tautology must fail (b) after the 2026-07-29
    narrowing, and set the sensitivity flag."""
    f = tmp_path / "theory.lean"
    f.write_text("theorem inv_all (p : Prop) : p ∨ ¬ p := Classical.em p\n",
                 encoding="utf-8")
    v = u3.evaluate(tmp_path, lean_bin=LEAN)
    assert v["verdict"] == "not_attained"
    assert v["label"] == "axiom_violation"
    assert v["flags"]["classical_choice_needed"]


# ---------------------------------------------- declared refusal (strict read)

def test_declared_refusal_reads_not_attained_with_gap_flag(tmp_path):
    """A run whose Lean form was refused ('not attempted: … too big') produced
    no theorem: NOT-attained under the strict §1.2 reading, with the 缺格
    ambiguity surfaced as flags.gap_candidate_g (never as arithmetic)."""
    run = _arm_run(tmp_path, [{
        "cheap_green": False, "proof_layer_available": False,
        "expensive": {"available": False, "ok": False,
                      "detail": "not attempted: the enumerative development "
                                "decides every state in the kernel and this "
                                "level has about an unknown number of them "
                                "(ceiling 200000)."},
    }])
    v = u3.evaluate(run)
    assert v["verdict"] == "not_attained"
    assert v["label"] == "declared_refusal"
    assert v["flags"]["gap_candidate_g"] is True


def test_unavailable_without_refusal_reads_no_proof_layer(tmp_path):
    run = _arm_run(tmp_path, [{
        "cheap_green": True, "proof_layer_available": False,
        "expensive": {"available": False, "ok": False,
                      "detail": "no Lean form was generated"},
    }])
    assert u3.evaluate(run)["label"] == "no_proof_layer"


def test_empty_certify_reads_no_evidence(tmp_path):
    run = _arm_run(tmp_path, [])
    v = u3.evaluate(run)
    assert v["verdict"] == "not_attained"
    assert v["label"] == "no_evidence"


def test_undischarged_when_lean_never_ran(tmp_path):
    run = _arm_run(tmp_path, [{
        "cheap_green": True, "proof_layer_available": True,
        "expensive": {"available": True, "ok": False,
                      "lean_file": str(tmp_path / "nowhere.lean"),
                      "detail": "a Lean file exists but `lean` is not on PATH, "
                                "so the proof obligations are stated and "
                                "undischarged"},
    }])
    assert u3.evaluate(run)["label"] == "undischarged"


def test_compiled_but_unreported_axioms_fails_strict(tmp_path):
    run = _arm_run(tmp_path, [{
        "cheap_green": True, "proof_layer_available": True,
        "expensive": {"available": True, "ok": True, "returncode": 0,
                      "stdout": "", "detail": "lean accepted the file"},
    }])
    v = u3.evaluate(run)
    assert v["verdict"] == "not_attained"
    assert v["label"] == "axioms_unreported"


def test_transfer_only_run_reads_no_proof_layer(tmp_path):
    (tmp_path / "transfer.json").write_text(json.dumps(
        {"certify": {"cheap_green": False, "proof_layer_available": False}}),
        encoding="utf-8")
    assert u3.evaluate(tmp_path)["label"] == "no_proof_layer"


def test_best_record_wins_across_certify_records(tmp_path):
    """至少一条: one refused record plus one discharged record → attained."""
    lean_src = REAL_L1_DIR / "theory.lean"
    run = _arm_run(tmp_path, [
        {"cheap_green": False, "proof_layer_available": False,
         "expensive": {"available": False, "ok": False,
                       "detail": "not attempted: too big"}},
        {"cheap_green": True, "proof_layer_available": True,
         "expensive": {"available": True, "ok": True, "returncode": 0,
                       "lean_file": str(lean_src),
                       "stdout": "'inv_all' does not depend on any axioms\n",
                       "detail": "lean accepted the file"}},
    ])
    v = u3.evaluate(run)
    assert v["verdict"] == "attained"
    assert v["label"] == "discharged"


# ----------------------------------------------------------- positive material

def test_a0_spike_reads_attained_from_recorded_evidence():
    v = u3.evaluate(A0_SPIKE)
    assert v["verdict"] == "attained"
    assert v["label"] == "discharged"
    per = v["criteria"]["per_theorem"]
    assert per["unsolvable"]["b"]["ok"]
    assert per["unsolvable"]["c"]["ok"]
    subs = per["unsolvable"]["c"]["sub_checks"]
    assert subs["a_inv_at_init"] and subs["b_goals_excluded"]
    assert subs["c_init_has_action"] and subs["d_goal_nonempty"]


def test_cold_start_a0_reads_attained_from_recorded_cert():
    v = u3.evaluate(COLD_A0)
    assert v["verdict"] == "attained"
    assert v["label"] == "discharged"


def test_residuals_are_reported_not_hidden():
    """The (c) check must confess its §9.2 residual instead of passing silently."""
    v = u3.evaluate(A0_SPIKE)
    assert any("residual" in r for r in v["criteria"]["c_residuals"])


@needs_lean
def test_a0_spike_live_probe_still_attains():
    v = u3.evaluate(A0_SPIKE, probe=True, lean_bin=LEAN)
    assert v["verdict"] == "attained"
    assert v["label"] == "discharged"


# ------------------------------------------------------------------- sweep bits

def test_stage_ordering_is_total_and_discharged_is_max():
    assert u3.STAGES[-1] == "discharged"
    assert len(set(u3.STAGES)) == len(u3.STAGES)


def test_markdown_table_counts_attained(tmp_path):
    rows = [u3.evaluate(A0_SPIKE)]
    md = u3.to_markdown(rows)
    assert "attained" in md and "1 / 1" in md
