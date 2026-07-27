"""theory.lean generator for A0.

`theory_compiler.generators.gen_lean` cannot be used: it ignores the AST it is
handed and emits a 1D peg-solitaire development (DECISIONS.md D-A0-011).  This
backend emits the canonical skeleton of Theoria 1.10a instead —

```lean
structure St                     -- word table
def step : St → Dir → St         -- rules
def Goal : St → Bool
inductive Reachable : St → Prop
def I : St → Bool                -- invariant
theorem inv_init   : I s₀
theorem inv_closed : ∀ s d, I s → I (step s d)
theorem goal_break : ∀ s, Goal s → ¬ I s
theorem unsolvable : ¬ ∃ s, Reachable s ∧ Goal s
```

Three commitments, each for a stated reason:

* **`decide`, never `native_decide`.** `native_decide` discharges a goal by
  running compiled code and records `Lean.ofReduceBool` as an axiom. Theoria's
  acceptance test is that `#print axioms` comes back empty, so the kernel has to
  do the work.

* **No Mathlib.** `lean` alone compiles this file — the expensive certify layer
  stays runnable from a bare toolchain, and the proof's dependency surface stays
  visible.

* **`step` is transcribed from `theory.py`, not re-derived.** The transition
  table is produced by executing the generated executable form over the finite
  state space. There is one predictor in the system (constraint 4); the Lean file
  is a second *rendering* of it, not a second implementation.

**Every state component is its own inductive type**, including the Button's
colour. That is not cosmetic: `cases` on an inductive turns `inv_closed` into a
few hundred goals with no free variables left, each of which `decide` closes by
computation. A `Nat`-valued field would leave a variable behind and no amount of
`decide` would help.
"""

import importlib.util
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from theory_compiler.parser.ast_nodes import TheoryAST

from compile.problem import Problem

DIRS = ("up", "down", "left", "right")


@dataclass
class Axis:
    """One component of the state, as a Lean inductive."""

    field: str                     # the theory.py attribute, e.g. "Button_colour"
    type_name: str                 # "ButtonColour"
    accessor: str                  # "buttonColour"
    values: List                   # the observed values, in order
    labels: List[str]              # constructor names, aligned with `values`

    def ctor(self, value) -> str:
        return "%s.%s" % (self.type_name, self.labels[self.values.index(value)])


def _load(theory_py_path: str):
    spec = importlib.util.spec_from_file_location("a0_theory_tmp", theory_py_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _label(value) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    return "v%s" % value


def _accessor(field: str) -> str:
    obj, _, kind = field.partition("_")
    return obj[0].lower() + obj[1:] + kind.capitalize()


def _type_name(field: str) -> str:
    obj, _, kind = field.partition("_")
    return obj + kind.capitalize()


def build_axes(module, problem: Problem) -> Tuple[List[Tuple[int, int]], List[Axis]]:
    """The arena, plus one axis per non-mover observation that ever varies.

    An observation with a single observed value is a constant, not a state
    component, and is dropped: carrying it would multiply the case split by one
    and prove nothing.
    """
    arena = [tuple(c) for c in problem.arena]
    base = module.initial_state()
    candidates = [
        f for f in vars(base)
        if not f.startswith("Cart") and f.endswith(("_colour", "_present"))
    ]

    seen: Dict[str, set] = {f: {getattr(base, f)} for f in candidates}
    for cell in arena:
        probe = base.copy()
        probe.Cart_pos = cell
        for direction in DIRS:
            nxt = module.step(probe, ("push", "Cart", direction))
            for f in candidates:
                seen[f].add(getattr(nxt, f))

    axes: List[Axis] = []
    for field in candidates:
        values = sorted(seen[field], key=lambda v: (isinstance(v, bool), v))
        if len(values) < 2:
            continue
        axes.append(Axis(
            field=field,
            type_name=_type_name(field),
            accessor=_accessor(field),
            values=values,
            labels=[_label(v) for v in values],
        ))
    return arena, axes


def _states(module, arena, axes: Sequence[Axis]):
    base = module.initial_state()
    out = []

    def build(index: int, assignment: Dict[str, object]):
        if index == len(axes):
            for cell in arena:
                state = base.copy()
                state.Cart_pos = cell
                for key, value in assignment.items():
                    setattr(state, key, value)
                out.append(state)
            return
        axis = axes[index]
        for value in axis.values:
            build(index + 1, dict(assignment, **{axis.field: value}))

    build(0, {})
    return out


def _term(state, cart_index, axes: Sequence[Axis]) -> str:
    parts = ["Cell.c%d" % cart_index[tuple(state.Cart_pos)]]
    parts += [axis.ctor(getattr(state, axis.field)) for axis in axes]
    return "⟨%s⟩" % ", ".join(parts)


def door_latch_invariant(axes: Sequence[Axis]) -> Optional[Tuple[str, str]]:
    """`door_latch` (THEORIZE_LOG L-02) in terms of whatever axes exist."""
    button = next((a for a in axes if a.field == "Button_colour"), None)
    door = next((a for a in axes if a.field == "Door_present"), None)
    if button is None or door is None or 8 not in button.values:
        return None
    return (
        "(s.%s == %s) != (s.%s == %s)"
        % (button.accessor, button.ctor(8), door.accessor, door.ctor(True)),
        "door_latch (THEORIZE_LOG L-02): exactly one of 'the Button shows 8'\n"
        "and 'the Door exists' holds, in every reachable state.\n"
        "cart_unique (L-01) is NOT proved here: representing the state as the\n"
        "Cart's cell already assumes there is exactly one Cart, so a Lean proof\n"
        "would be discharged by the representation. It is checked where it can\n"
        "actually fail — per frame, by the cheap layer's responsibility pass.",
    )


def weight_invariant(safe_cells: Sequence[Tuple[int, int]], arena,
                     comment: str):
    """A 0/1 pagoda weight: `w(cell) = 0` on `safe_cells`, `1` elsewhere.

    Written as a weight rather than as a membership test on purpose — this is the
    invariant language Theoria 1.9 names (counts, parity, finite weights), and it
    is the same object the certificate and an admissible heuristic would share.
    `I(s) := w(cart) = 0` is then literally "the potential never rises above its
    initial value".
    """
    safe = {tuple(c) for c in safe_cells}
    table = [(i, 0 if cell in safe else 1) for i, cell in enumerate(arena)]

    def build(_axes):
        lines = ["\n/-- Pagoda weight: 0 on the room the Cart starts in, 1 outside. -/",
                 "def w : Cell → Nat"]
        for i, value in table:
            lines.append("  | .c%d => %d" % (i, value))
        return ("w s.cart == 0", comment, "\n".join(lines))

    return build


def generate_lean(ast: TheoryAST, problem: Problem, theory_py_path: str,
                  invariant_builder: Optional[Callable] = None,
                  goal_cell: Optional[Tuple[int, int]] = None,
                  unsolvable: bool = False) -> str:
    module = _load(theory_py_path)
    arena, axes = build_axes(module, problem)
    cart_index = {cell: i for i, cell in enumerate(arena)}
    states = _states(module, arena, axes)
    initial = module.initial_state()
    goal = tuple(goal_cell) if goal_cell else _goal_cell(module, arena)

    if invariant_builder is None:
        built = door_latch_invariant(axes)
        if built is None:
            built = ("true", "this instance has no latch; the invariant is vacuous")
    else:
        built = invariant_builder(axes)
    invariant, comment = built[0], built[1]
    preamble = built[2] if len(built) > 2 else ""

    L: List[str] = []
    L.append("/-")
    L.append("  Auto-generated from theory.dsl by compile/gen_lean_a0.py — DO NOT EDIT.")
    L.append("  Problem: %s.  Arena: %d cells.  Axes: %s.  States: %d."
             % (problem.name, len(arena),
                ", ".join(a.field for a in axes) or "none", len(states)))
    L.append("  Proofs use `decide` only, so `#print axioms` must come back empty.")
    L.append("-/")
    L.append("")

    L.append("/-- Arena cells, in row-major order:")
    for i, cell in enumerate(arena):
        L.append("    c%-3d = (%d, %d)" % (i, cell[0], cell[1]))
    L.append("-/")
    L.append("inductive Cell where")
    for i in range(len(arena)):
        L.append("  | c%d" % i)
    L.append("  deriving DecidableEq, Repr")
    L.append("")

    L.append("inductive Dir where")
    for d in DIRS:
        L.append("  | %s" % d)
    L.append("  deriving DecidableEq, Repr")
    L.append("")

    for axis in axes:
        L.append("/-- `%s`, as observed: %s -/"
                 % (axis.field, ", ".join(str(v) for v in axis.values)))
        L.append("inductive %s where" % axis.type_name)
        for label in axis.labels:
            L.append("  | %s" % label)
        L.append("  deriving DecidableEq, Repr")
        L.append("")

    L.append("structure St where")
    L.append("  cart : Cell")
    for axis in axes:
        L.append("  %s : %s" % (axis.accessor, axis.type_name))
    L.append("  deriving DecidableEq, Repr")
    L.append("")

    L.append("def s0 : St := %s" % _term(initial, cart_index, axes))
    L.append("")

    L.append("/-- The manual's rules, transcribed from the executable form. -/")
    L.append("def step : St → Dir → St")
    for state in states:
        term = _term(state, cart_index, axes)
        for d in DIRS:
            nxt = module.step(state, ("push", "Cart", d))
            L.append("  | %s, .%s => %s" % (term, d, _term(nxt, cart_index, axes)))
    L.append("")

    L.append("def Goal (s : St) : Bool := s.cart == Cell.c%d" % cart_index[goal])
    L.append("")

    L.append("inductive Reachable : St → Prop where")
    L.append("  | init : Reachable s0")
    L.append("  | step : ∀ (s : St) (d : Dir), Reachable s → Reachable (step s d)")
    L.append("")

    if preamble:
        L.append(preamble)
        L.append("")
    for line in comment.splitlines():
        L.append("-- %s" % line)
    L.append("def I (s : St) : Bool := %s" % invariant)
    L.append("")

    destructure = "  obtain ⟨c%s⟩ := s" % "".join(", " + a.accessor for a in axes)
    split = "  cases c <;> %scases d <;> decide" % "".join(
        "cases %s <;> " % a.accessor for a in axes
    )
    split_no_dir = "  cases c <;> %sdecide" % "".join(
        "cases %s <;> " % a.accessor for a in axes
    )

    L.append("theorem inv_init : I s0 = true := by decide")
    L.append("")
    L.append("theorem inv_closed (s : St) (d : Dir) : I s = true → I (step s d) = true := by")
    L.append(destructure)
    L.append(split)
    L.append("")
    L.append("theorem inv_all (s : St) (h : Reachable s) : I s = true := by")
    L.append("  induction h with")
    L.append("  | init => decide")
    L.append("  | step s d _ ih => exact inv_closed s d ih")
    L.append("")

    if unsolvable:
        L.append("theorem goal_break (s : St) : Goal s = true → I s = false := by")
        L.append(destructure)
        L.append(split_no_dir)
        L.append("")
        L.append("theorem unsolvable : ¬ ∃ s : St, Reachable s ∧ Goal s = true := by")
        L.append("  rintro ⟨s, hr, hg⟩")
        L.append("  have hi : I s = true := inv_all s hr")
        L.append("  have hb : I s = false := goal_break s hg")
        L.append("  rw [hi] at hb")
        L.append("  exact absurd hb (by decide)")
        L.append("")
        L.append("#print axioms unsolvable")
    else:
        L.append("#print axioms inv_all")
    L.append("")
    return "\n".join(L)


def _goal_cell(module, arena):
    for cell in arena:
        state = module.initial_state()
        state.Cart_pos = cell
        if module.is_goal(state):
            return cell
    raise ValueError("no arena cell satisfies the manual's goal")
