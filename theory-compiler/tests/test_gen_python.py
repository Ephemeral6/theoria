"""
Test for theory.py generator — Cart world.
Full-frame responsibility: 10-step trajectory with hand-computed expected positions.

Cart world: 3 wide × 2 tall grid (cols 0-2, rows 0-1).
Cart starts at (1, 0), color=6. Board background=0.
"""

import sys
import types
from pathlib import Path

from theory_compiler.parser.theory_parser import parse_theory
from theory_compiler.generators.gen_python import generate_python

FIXTURES = Path(__file__).parent / "fixtures"


def _load_generated_module(source: str) -> types.ModuleType:
    """Compile generated Python source into a module."""
    mod = types.ModuleType("gen_cart")
    exec(compile(source, "<gen_cart>", "exec"), mod.__dict__)
    return mod


class TestCartSimulation:
    """10-step Cart trajectory with full-frame verification."""

    def setup_method(self):
        text = (FIXTURES / "cart_theory.dsl").read_text(encoding="utf-8")
        ast = parse_theory(text)
        source = generate_python(ast, grid_width=3, grid_height=2)
        self.mod = _load_generated_module(source)
        self.source = source

    def _make_initial(self):
        """Cart at (1, 0), color 6."""
        state = self.mod.State()
        state.cart.pos = (1, 0)
        state.cart.color = 6
        return state

    def test_generated_code_compiles(self):
        """Generated code should compile and define expected symbols."""
        assert hasattr(self.mod, "State")
        assert hasattr(self.mod, "Cart")
        assert hasattr(self.mod, "step")
        assert hasattr(self.mod, "simulate")

    def test_initial_render(self):
        """Initial state renders correctly."""
        state = self._make_initial()
        grid = state.render()
        # 2 rows × 3 cols; Cart at (1,0) → row 0, col 1
        assert grid == [
            [0, 6, 0],
            [0, 0, 0],
        ]

    def test_full_frame_every_cell_accounted(self):
        """Every cell must be either 0 (board) or 6 (Cart). No undefined."""
        state = self._make_initial()
        grid = state.render()
        for row in grid:
            for cell in row:
                assert cell in (0, 6), f"Unexpected cell value: {cell}"

    def test_10_step_trajectory(self):
        """Hand-computed 10-step trajectory.

        Grid: 3×2 (cols 0-2, rows 0-1). Cart starts at (1,0).
        Actions and expected positions:
          0. initial: (1, 0)
          1. push(Cart, right)  → (2, 0)
          2. push(Cart, down)   → (2, 1)
          3. push(Cart, left)   → (1, 1)
          4. push(Cart, left)   → (0, 1)
          5. push(Cart, up)     → (0, 0)
          6. push(Cart, right)  → (1, 0)
          7. push(Cart, right)  → (2, 0)
          8. push(Cart, right)  → (2, 0)  # blocked! right is out of bounds
          9. push(Cart, down)   → (2, 1)
         10. push(Cart, up)     → (2, 0)
        """
        actions = [
            "push(Cart, right)",
            "push(Cart, down)",
            "push(Cart, left)",
            "push(Cart, left)",
            "push(Cart, up)",
            "push(Cart, right)",
            "push(Cart, right)",
            "push(Cart, right)",   # blocked
            "push(Cart, down)",
            "push(Cart, up)",
        ]

        expected_positions = [
            (1, 0),  # initial
            (2, 0),  # right
            (2, 1),  # down
            (1, 1),  # left
            (0, 1),  # left
            (0, 0),  # up
            (1, 0),  # right
            (2, 0),  # right
            (2, 0),  # blocked (right edge)
            (2, 1),  # down
            (2, 0),  # up
        ]

        initial = self._make_initial()
        states = self.mod.simulate(initial, actions)

        assert len(states) == 11  # initial + 10 steps

        for i, (state, expected_pos) in enumerate(zip(states, expected_positions)):
            actual_pos = state.cart.pos
            assert actual_pos == expected_pos, (
                f"Step {i}: expected pos {expected_pos}, got {actual_pos}"
            )
            # Full-frame check: render and verify
            grid = state.render()
            ex, ey = expected_pos
            for r in range(2):
                for c in range(3):
                    if (c, r) == expected_pos:
                        assert grid[r][c] == 6, f"Step {i}: Cart not at ({c},{r})"
                    else:
                        assert grid[r][c] == 0, f"Step {i}: non-zero at ({c},{r})={grid[r][c]}"

    def test_teleport_rule(self):
        """Cart at (1, 0) pushes up → hits wall → teleports to origin (0,0).

        In our 3x2 grid, row 0 is the top row.
        push(Cart, up) when Cart is at row 0 → above is out of bounds (wall).
        """
        state = self._make_initial()  # (1, 0)
        # Push up from top row — above is out of bounds → teleport
        new_state = self.mod.step(state, "push(Cart, up)")
        # The teleport rule fires when above(Cart) = wall
        # In our implementation, free(above(Cart)) is False when at top row
        # So push_up won't fire; teleport should fire
        assert new_state.cart.pos == (0, 0), f"Expected teleport to (0,0), got {new_state.cart.pos}"
