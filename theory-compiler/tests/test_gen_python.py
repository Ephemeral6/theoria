"""theory.py generator — the world's one predictor.

Two worlds, one generator. That is the point: the predecessor hard-coded the
`moved` and `teleported` events and assumed one instance per declared type, so
the peg world's two rules compiled to `pass` and the "generated simulation"
simulated nothing (DECISIONS.md D-A0-011). These tests run both a grid world
with a portal and a line world with four pegs on it, through the same code path.
"""

import types
from pathlib import Path

import pytest

from theory_compiler.generators.gen_python import UnsupportedClause, generate_python
from theory_compiler.parser.theory_parser import parse_theory
from theory_compiler.problem import ProblemError, load_problem

FIXTURES = Path(__file__).parent / "fixtures"


def build(dsl: str, problem: str) -> types.ModuleType:
    ast = parse_theory((FIXTURES / dsl).read_text(encoding="utf-8"))
    source = generate_python(ast, load_problem(str(FIXTURES / problem)))
    mod = types.ModuleType("generated")
    mod.__dict__["__source__"] = source
    exec(compile(source, "<generated>", "exec"), mod.__dict__)
    return mod


# ------------------------------------------------------------------ grid world

class TestCartWorld:
    def setup_method(self):
        self.mod = build("cart_theory.dsl", "cart_problem.json")

    def test_declared_semantics_reach_the_generated_module(self):
        """E-03. The frame axiom is a fact about the world, so it travels with
        the world rather than being re-assumed by each backend."""
        assert self.mod.SEMANTICS == {"frame": "persist",
                                      "conflict": "exclusive",
                                      "cascade": "single_frame"}

    def test_lifted_rule_expands_to_the_hand_written_names(self):
        """E-02. `rule push forall ?d in dir` replaces four hand-written rules
        and regenerates them under exactly the names they had."""
        names = [r[0] for r in self.mod.RULES]
        assert names == ["push_up", "push_down", "push_left", "push_right",
                         "teleport"]

    def test_trajectory(self):
        state = self.mod.initial_state()
        assert state.Cart_pos == (1, 1)
        for action, expected in [
            (("push", "Cart", "up"), (0, 1)),
            (("push", "Cart", "left"), (0, 0)),
            (("push", "Cart", "left"), (0, 0)),   # blocked by the wall
            (("push", "Cart", "down"), (1, 0)),
            (("push", "Cart", "right"), (1, 1)),
        ]:
            state = self.mod.step(state, action)
            assert state.Cart_pos == expected, action

    def test_frame_persists_when_no_rule_fires(self):
        state = self.mod.initial_state()
        before = state.key()
        after = self.mod.step(state, ("push", "Cart", "nowhere"))
        assert after.key() == before

    def test_full_frame_every_cell_accounted(self):
        grid = self.mod.render(self.mod.initial_state())
        assert len(grid) == 2 and all(len(row) == 3 for row in grid)
        assert grid[1][1] == 6
        assert sum(v == 6 for row in grid for v in row) == 1

    def test_teleport_fires_at_the_wall(self):
        """The rule guarded by `above(Cart) = wall`; `origin` is a landmark."""
        state = self.mod.initial_state()
        state.Cart_pos = (0, 2)
        assert "teleport" in self.mod.fired(state, ("push", "Cart", "up"))
        assert self.mod.step(state, ("push", "Cart", "up")).Cart_pos == (0, 0)


# ------------------------------------------------------------------ line world

class TestPegWorld:
    def setup_method(self):
        self.mod = build("peg_theory.dsl", "peg5_problem.json")

    def test_many_instances_of_one_declared_type(self):
        """The restriction that made the peg world uncompilable."""
        state = self.mod.initial_state()
        positions = sorted(getattr(state, f"Peg_{i}_pos") for i in (0, 1, 3, 4))
        assert positions == [0, 1, 3, 4]

    def test_rules_ground_over_instance_pairs(self):
        """E-02 over object types: two variables, four pegs, no self-jumps."""
        names = [r[0] for r in self.mod.RULES]
        assert len(names) == 24
        assert not any(name.endswith(f"Peg_{i}_Peg_{i}")
                       for name in names for i in (0, 1, 3, 4))

    def test_the_jump_actually_happens(self):
        """v0.1 emitted `pass  # Implemented in specific game code` here."""
        state = self.mod.initial_state()
        assert self.mod.occupancy(state) == "11011"
        moved = {self.mod.occupancy(self.mod.step(state, a))
                 for a in self.mod.ACTIONS}
        moved.discard("11011")
        assert moved == {"00111", "11100"}

    def test_goal_is_a_count_over_instances(self):
        state = self.mod.initial_state()
        assert not self.mod.is_goal(state)
        for i in (1, 3, 4):
            setattr(state, f"Peg_{i}_alive", False)
        assert self.mod.is_goal(state)

    def test_reachable_set_matches_the_engine(self):
        """Independent of any certificate: BFS through the generated predictor
        reproduces the four states engine-rig's own README records."""
        seen, queue = {self.mod.occupancy(self.mod.initial_state())}, \
            [self.mod.initial_state()]
        while queue:
            state = queue.pop()
            for action in self.mod.ACTIONS:
                nxt = self.mod.step(state, action)
                if self.mod.occupancy(nxt) not in seen:
                    seen.add(self.mod.occupancy(nxt))
                    queue.append(nxt)
        assert seen == {"11011", "00111", "11100", "01001", "10010"}
        assert all(occ.count("1") >= 2 for occ in seen)


# ---------------------------------------------------------------- refusals

def test_unknown_event_is_refused_not_approximated():
    src = (FIXTURES / "peg_theory.dsl").read_text(encoding="utf-8")
    src = src.replace("then jumped(?a, ?b, right)", "then dissolved(?a, ?b, right)")
    with pytest.raises(UnsupportedClause) as exc:
        generate_python(parse_theory(src),
                        load_problem(str(FIXTURES / "peg5_problem.json")))
    assert "dissolved/3" in str(exc.value)


def test_declared_weights_need_not_be_repeated_by_the_level():
    """E-05. The manual names the potential; an engine certificate supplies the
    numbers. Requiring the level to repeat them would put a hand-transcription
    step back in the middle of the very data flow A1 exists to remove, so a
    missing vector is a warning here and `gen_lean` is what insists on it."""
    from theory_compiler.ir import build_ir
    ast = parse_theory((FIXTURES / "peg_theory.dsl").read_text(encoding="utf-8"))
    problem = load_problem(str(FIXTURES / "peg5_problem.json"))
    assert "w" not in problem.weights
    generate_python(ast, problem)                      # compiles regardless
    assert any("supplies no vector" in w for w in build_ir(ast, problem).warnings)
