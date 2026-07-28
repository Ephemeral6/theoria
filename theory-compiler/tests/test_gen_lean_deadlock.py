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
from theory_compiler import strips, strips_encoding
from theory_compiler.certificate import CertificateError
from theory_compiler.generators import gen_lean_deadlock
from theory_compiler.generators.gen_lean_deadlock import (
    DeadlockLeanError, generate_deadlock_lean,
)
from theory_compiler.strips import Atom
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


_WORLD = {}


def world():
    """One grounded task and one verified encoding for the whole module.

    `verify` is a 376,320-pair sweep and its answer never changes, so it is done
    once; `generate_deadlock_lean` refuses to emit against an unverified
    encoding, which is what makes "done once" safe rather than convenient.
    """
    if not _WORLD:
        task = strips.load_task(str(STRIPS_DIR / "sokoban_domain.pddl"),
                                str(STRIPS_DIR / "sokoban_open4far.pddl"))
        encoding = PositionalEncoding(task)
        strips_encoding.verify(encoding)
        _WORLD.update(task=task, encoding=encoding)
    return _WORLD["task"], _WORLD["encoding"]


def build(certificate: Path, exhibits: bool = True) -> str:
    task, encoding = world()
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

    def test_the_output_is_byte_reproducible(self, pair_source):
        """With a floor, so a generator that returned "" could not pass this."""
        assert build(PAIR) == pair_source
        assert pair_source.count("\n") > 400
        assert "theorem dead :" in pair_source

    def test_the_provenance_names_the_row_the_pattern_came_from(self, pair_source):
        assert "engine-rig/artifacts/candidates.jsonl" in pair_source
        assert "engine-rig/engines/deadlock_carver" in pair_source


class TestEmissionIsRead:
    """The link an adversarial review found unguarded.

    Everything upstream — `strips_encoding.verify`, `cross_check`, `recheck` —
    checks the *encoding*. The rendering of that encoding into Lean text was
    checked by nothing, and a rendering bug there survives every one of them:
    the demonstration was a one-line patch making every `push` arm emit
    `applyMove ... => s`, after which `dead` compiled with an empty axiom set
    about a world in which no box ever moves. These tests are that mutation,
    kept.
    """

    def _mutate(self, monkeypatch, mutation):
        task, encoding = world()
        cert = dc.load_deadlock_certificate(str(PAIR), task, encoding)
        real = gen_lean_deadlock._world

        def patched(L, *args, **kwargs):
            real(L, *args, **kwargs)
            mutation(L)

        monkeypatch.setattr(gen_lean_deadlock, "_world", patched)
        with pytest.raises(DeadlockLeanError) as exc:
            generate_deadlock_lean(task, encoding, cert)
        return str(exc.value)

    def test_a_push_that_moves_nothing_is_caught(self, monkeypatch):
        def neuter(L):
            for i, line in enumerate(L):
                if line.startswith("  | .push_") and " => { s with " in line:
                    L[i] = line.split(" => ")[0] + " => s"

        message = self._mutate(monkeypatch, neuter)
        assert "applyMove" in message and "compiles and proves nothing" in message

    def test_a_dropped_guard_is_caught(self, monkeypatch):
        def weaken(L):
            for i, line in enumerate(L):
                if line.startswith("  | .push_") and " && " in line:
                    head, body = line.split(" => ", 1)
                    L[i] = head + " => " + body.split(" && ")[0]

        message = self._mutate(monkeypatch, weaken)
        assert "emitted `legal` arm" in message

    def test_a_dropped_move_constructor_is_caught(self, monkeypatch):
        def drop(L):
            for i, line in enumerate(L):
                if line == "  | push_c11_c12_c13_b1_right":
                    del L[i]
                    return

        message = self._mutate(monkeypatch, drop)
        assert "not the task's ground action set" in message

    def test_a_clear_that_forgets_a_slot_is_caught(self, monkeypatch):
        def forget(L):
            for i, line in enumerate(L):
                if line.startswith("  s.player != c && "):
                    L[i] = "  s.player != c && s.b1 != c"

        message = self._mutate(monkeypatch, forget)
        assert "St.clear" in message

    def test_the_generator_refuses_an_unverified_encoding(self):
        """Otherwise the encoding-to-task link could simply be skipped."""
        task = strips.load_task(str(STRIPS_DIR / "sokoban_domain.pddl"),
                                str(STRIPS_DIR / "sokoban_open4far.pddl"))
        fresh = PositionalEncoding(task)
        cert = dc.load_deadlock_certificate(str(PAIR), task, fresh)
        assert fresh.verified_stats is None
        with pytest.raises(DeadlockLeanError) as exc:
            generate_deadlock_lean(task, fresh, cert)
        assert "has not been checked against the task" in str(exc.value)


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
    task, encoding = world()
    cert = dc.load_deadlock_certificate(str(PAIR), task, encoding)
    return generate_deadlock_lean(task, encoding, cert, **kwargs)


def moved_pattern_cert(source_cert: Path, cells):
    """The fixture's certificate with its pattern atoms moved to `cells`.

    Built by hand rather than loaded, because `load_deadlock_certificate` would
    (correctly) refuse it — and that refusal is asserted here, so the control is
    known to be a control before Lean is asked anything.
    """
    task, encoding = world()
    real = dc.load_deadlock_certificate(str(source_cert), task, encoding)
    assert len(cells) == len(real.pattern)
    probe = dc.DeadlockCertificate(
        claim="negative control", domain=real.domain, problem=real.problem,
        pattern=[Atom(a.name, a.args[:-1] + (c,)) for a, c in zip(real.pattern, cells)],
        closure=real.closure, n_deleting_actions=-1, blocked_actions=[],
        goal_conflict=None, coverage="", produced_by="control",
        provenance="negative control")
    with pytest.raises(CertificateError) as exc:
        dc.recheck(probe, encoding)
    assert "closure fails" in str(exc.value)
    return task, encoding, probe


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
    def test_a_pattern_that_is_not_a_dead_region_fails_in_lean(self, tmp_path):
        """Without this, "lean exits 0" would be a fact about string assembly.

        The whole development is **regenerated** for `at(b1,c22) AND at(b2,c23)`
        — the same shape one square in from the wall, where the boxes can be
        separated. Patching `Pat` in a finished file instead would leave
        `pat_pins` and `closed_pinned` still pinned to the old cells, and the
        file would go red from that desynchronisation rather than from the
        pattern being escapable: a control that fails for the wrong reason.
        """
        task, encoding, probe = moved_pattern_cert(PAIR, ["c22", "c23"])
        source = generate_deadlock_lean(task, encoding, probe)
        output = run_lean(source, tmp_path, expect_success=False)
        assert "sorryAx" in output, output[:4000]
        assert "closed_pinned" in output, output[:4000]
