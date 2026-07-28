"""The deadlock certificate compiled to Lean, and actually checked by Lean.

The acceptance for this path is not "a file was produced". It is that `lean`
exits 0 and `#print axioms` reports an empty set for every theorem in it — no
`sorry`, no `native_decide`, no `Classical.choice` sneaking in through a
tactic. `TestNegativeControl` is what makes that check mean something: it moves
the pattern one cell, and the same file that was green goes red with `sorryAx`.

Two developments, one per closure form. The pair pattern pins both boxes and
costs 1792 leaf goals (~4s); the corner pattern pins one and costs 28672 (~60s),
so it runs only under `THEORIA_REQUIRE_LEAN=1` — the flag whose whole meaning is
"this run is supposed to have proved something".
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from theory_compiler import deadlock_certificate as dc
from theory_compiler import strips
from theory_compiler.generators import gen_lean_deadlock
from theory_compiler.generators.gen_lean_deadlock import (
    DeadlockLeanError, generate_deadlock_lean,
)
from theory_compiler.strips_encoding import PositionalEncoding, shortest_plan

FIXTURES = Path(__file__).parent / "fixtures"
STRIPS_DIR = FIXTURES / "strips"
PAIR = FIXTURES / "deadlock_open4far_b1c12_b2c13.json"
CORNER = FIXTURES / "deadlock_open4far_b1c11.json"
REPO = Path(__file__).resolve().parents[2]

LEAN = shutil.which("lean")
needs_lean = pytest.mark.skipif(LEAN is None, reason="lean is not on PATH")
slow = pytest.mark.skipif(
    os.environ.get("THEORIA_REQUIRE_LEAN") != "1",
    reason="the 28672-leaf development runs under THEORIA_REQUIRE_LEAN=1")


def build(certificate: Path, exhibits: bool = True) -> str:
    task = strips.load_task(str(STRIPS_DIR / "sokoban_domain.pddl"),
                            str(STRIPS_DIR / "sokoban_open4far.pddl"))
    encoding = PositionalEncoding(task)
    cert = dc.load_deadlock_certificate(str(certificate), task, encoding)
    plan = witness = None
    if exhibits:
        plan = shortest_plan(encoding)
        witness = min(s for s in encoding.states()
                      if encoding.holds(s, list(cert.pattern)))
    return generate_deadlock_lean(task, encoding, cert, plan=plan, witness=witness)


@pytest.fixture(scope="module")
def pair_source():
    return build(PAIR)


def run_lean(source: str, tmp_path: Path, expect_success: bool = True) -> str:
    target = tmp_path / "Theory.lean"
    target.write_text(source, encoding="utf-8", newline="\n")
    shutil.copy(REPO / "theory-compiler" / "lean" / "lean-toolchain", tmp_path)
    result = subprocess.run([LEAN, str(target)], cwd=str(tmp_path),
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=900)
    output = result.stdout.decode("utf-8", errors="replace")
    if expect_success:
        assert result.returncode == 0, f"lean failed:\n{output[:4000]}"
    else:
        assert result.returncode != 0, f"lean was expected to fail:\n{output[:4000]}"
    return output


THEOREMS = ("pat_pins", "closed_pinned", "dead_closed", "no_goal_pinned",
            "pat_no_goal", "dead_persists", "dead", "pat_witness",
            "level_is_winnable")


# ---------------------------------------------------------------- the source

class TestSource:
    def test_the_world_is_read_off_the_task_not_the_certificate(self, pair_source):
        assert "inductive Move where" in pair_source
        assert pair_source.count("  | push_") == 64
        assert pair_source.count("  | move_") == 48
        assert "def s0 : St := ⟨.c44, .c22, .c33⟩" in pair_source

    def test_the_certificate_contributes_the_pattern_and_nothing_else(self, pair_source):
        assert "def Pat (s : St) : Bool :=\n  s.b1 == .c12 && s.b2 == .c13" in pair_source
        assert "def Goal (s : St) : Bool :=\n  s.b1 == .c42 && s.b2 == .c13" in pair_source

    def test_the_theorem_is_conditional_not_a_claim_about_s0(self, pair_source):
        assert ("theorem dead : ∀ (r s : St), wf r = true → Pat r = true → "
                "ReachFrom r s →") in pair_source
        assert "ReachFrom (r : St) : St → Prop" in pair_source

    def test_no_sorry_and_no_native_decide(self, pair_source):
        """Checked on the code, not on the header — the header says the words."""
        body = pair_source.split("-/", 1)[1]
        assert "sorry" not in body
        assert "native_decide" not in body
        assert "Classical" not in body

    def test_every_theorem_has_its_axiom_set_printed(self, pair_source):
        for name in THEOREMS:
            assert "#print axioms %s" % name in pair_source

    def test_the_output_is_byte_reproducible(self):
        assert build(PAIR) == build(PAIR)

    def test_the_provenance_names_the_row_the_pattern_came_from(self, pair_source):
        assert "engine-rig/artifacts/candidates.jsonl" in pair_source
        assert "engine-rig/engines/deadlock_carver" in pair_source


class TestRefusals:
    def test_there_is_no_algebraic_fallback(self):
        with pytest.raises(DeadlockLeanError) as exc:
            build_with(proof="algebraic")
        assert "one proof mode" in str(exc.value)

    def test_a_split_over_budget_is_refused_rather_than_emitted(self, monkeypatch):
        """A file that will not elaborate is not a proof, and pretending
        otherwise would be discovered by whoever ran it, not here."""
        monkeypatch.setattr(gen_lean_deadlock, "MAX_LEAN_CASES", 100)
        with pytest.raises(DeadlockLeanError) as exc:
            build(PAIR)
        assert "over the budget" in str(exc.value)
        assert "pins 2 of 3 slots" in str(exc.value)


def build_with(**kwargs) -> str:
    task = strips.load_task(str(STRIPS_DIR / "sokoban_domain.pddl"),
                            str(STRIPS_DIR / "sokoban_open4far.pddl"))
    encoding = PositionalEncoding(task)
    cert = dc.load_deadlock_certificate(str(PAIR), task, encoding)
    return generate_deadlock_lean(task, encoding, cert, **kwargs)


# ------------------------------------------------------------------- and Lean

@needs_lean
class TestLean:
    def test_the_pair_pattern_compiles_with_an_empty_axiom_set(self, pair_source, tmp_path):
        output = run_lean(pair_source, tmp_path)
        for name in THEOREMS:
            assert "'%s' does not depend on any axioms" % name in output, output
        assert "sorryAx" not in output
        assert "ofReduceBool" not in output
        assert "Classical.choice" not in output

    @slow
    def test_the_corner_pattern_compiles_with_an_empty_axiom_set(self, tmp_path):
        """The other closure form: no ground action deletes a pattern atom at
        all, because grounding already discarded the pushes the wall makes
        impossible. It pins one slot instead of two, so it costs 16x more."""
        output = run_lean(build(CORNER), tmp_path)
        for name in THEOREMS:
            assert "'%s' does not depend on any axioms" % name in output, output
        assert "sorryAx" not in output


@needs_lean
class TestNegativeControl:
    def test_moving_the_pattern_one_cell_turns_the_file_red(self, pair_source, tmp_path):
        """Without this, "lean exits 0" would be a fact about string assembly.

        `at(b1,c22) AND at(b2,c23)` is the same shape one square in from the
        wall, and it is not a dead region: the boxes can be separated.
        """
        tampered = pair_source.replace(
            "def Pat (s : St) : Bool :=\n  s.b1 == .c12 && s.b2 == .c13",
            "def Pat (s : St) : Bool :=\n  s.b1 == .c22 && s.b2 == .c23")
        assert tampered != pair_source
        output = run_lean(tampered, tmp_path, expect_success=False)
        assert "sorryAx" in output, output[:4000]
