"""
theory.lean generator — produces Lean 4 proof framework from TheoryAST.

Strategy: BFS-based proof for finite state spaces.
Enumerate the complete reachable set offline, emit it as a Lean list,
then use native_decide/decide to verify closure and goal-absence.
No Mathlib dependency.
"""

from ..parser.ast_nodes import TheoryAST
from collections import deque


def generate_lean(ast: TheoryAST, board_size: int, initial_config: list[bool],
                  pagoda_weights: list[int], goal_count: int = 1) -> str:
    """Generate Lean 4 source proving unsolvability via BFS reachable-set closure."""
    n = board_size
    init = tuple(initial_config)

    # BFS to find all reachable states
    reachable = _bfs_reachable(n, init)

    # Check no goal state is reachable
    goal_states = [s for s in reachable if sum(s) == goal_count]
    assert len(goal_states) == 0, f"Configuration is solvable! Goal states reachable: {goal_states}"

    lines = _build_lean_source(n, init, reachable, goal_count)
    return "\n".join(lines) + "\n"


def _bfs_reachable(n: int, init: tuple[bool, ...]) -> list[tuple[bool, ...]]:
    """BFS over 1D peg solitaire states."""
    visited = {init}
    queue = deque([init])
    while queue:
        s = queue.popleft()
        for ns in _jumps(n, s):
            if ns not in visited:
                visited.add(ns)
                queue.append(ns)
    return sorted(visited, key=lambda s: s[::-1])  # deterministic order


def _jumps(n: int, state: tuple[bool, ...]):
    """Generate all successor states from a 1D peg solitaire state."""
    for i in range(n - 2):
        # forward jump: i over i+1 to i+2
        if state[i] and state[i+1] and not state[i+2]:
            s = list(state)
            s[i], s[i+1], s[i+2] = False, False, True
            yield tuple(s)
        # backward jump: i+2 over i+1 to i
        if state[i+2] and state[i+1] and not state[i]:
            s = list(state)
            s[i], s[i+1], s[i+2] = True, False, False
            yield tuple(s)


def _state_to_lean(s: tuple[bool, ...]) -> str:
    """Convert a state tuple to Lean PegState constructor."""
    bools = ", ".join("true" if b else "false" for b in s)
    return f"⟨{bools}⟩"


def _build_lean_source(n: int, init: tuple[bool, ...],
                       reachable: list[tuple[bool, ...]],
                       goal_count: int) -> list[str]:
    L = []

    L.append("/-")
    L.append(f"  Auto-generated Lean 4 proof: 1D Peg Solitaire unsolvability")
    L.append(f"  Board: {n} positions, pegs at {[i for i,p in enumerate(init) if p]}")
    L.append(f"  Reachable states: {len(reachable)} (computed by BFS)")
    L.append(f"  No state with exactly {goal_count} peg(s) is reachable.")
    L.append(f"  Strategy: enumerate reachable set, prove closure, check no goal member.")
    L.append("-/")
    L.append("")

    # Structure
    L.append("structure PegState where")
    for i in range(n):
        L.append(f"  s{i} : Bool")
    L.append("  deriving DecidableEq, Repr")
    L.append("")

    # Position
    L.append("inductive Pos where")
    for i in range(n):
        L.append(f"  | p{i}")
    L.append("  deriving DecidableEq, Repr")
    L.append("")

    # initState
    L.append(f"def initState : PegState := {_state_to_lean(init)}")
    L.append("")

    # pegCount
    L.append("def pegCount (s : PegState) : Nat :=")
    parts = [f"(if s.s{i} then 1 else 0)" for i in range(n)]
    L.append("  " + " + ".join(parts))
    L.append("")

    L.append(f"def isGoalB (s : PegState) : Bool := pegCount s == {goal_count}")
    L.append("")

    # get/set
    L.append("def PegState.get (s : PegState) : Pos → Bool")
    for i in range(n):
        L.append(f"  | .p{i} => s.s{i}")
    L.append("")

    L.append("def PegState.set (s : PegState) (p : Pos) (v : Bool) : PegState :=")
    L.append("  match p with")
    for i in range(n):
        L.append(f"  | .p{i} => {{ s with s{i} := v }}")
    L.append("")

    # applyJump
    L.append("def applyJump (s : PegState) (a b c : Pos) : PegState :=")
    L.append("  ((s.set a false).set b false).set c true")
    L.append("")

    # isValidGeom
    L.append("def isValidGeom (a b c : Pos) : Bool :=")
    L.append("  match a, b, c with")
    for i in range(n - 2):
        L.append(f"  | .p{i}, .p{i+1}, .p{i+2} => true")
        L.append(f"  | .p{i+2}, .p{i+1}, .p{i} => true")
    L.append("  | _, _, _ => false")
    L.append("")

    # Step / Reachable
    L.append("inductive Step : PegState → PegState → Prop where")
    L.append("  | jump (s : PegState) (a b c : Pos)")
    L.append("    (hg : isValidGeom a b c = true)")
    L.append("    (ha : s.get a = true) (hb : s.get b = true) (hc : s.get c = false) :")
    L.append("    Step s (applyJump s a b c)")
    L.append("")
    L.append("inductive Reachable : PegState → PegState → Prop where")
    L.append("  | refl : ∀ s, Reachable s s")
    L.append("  | step : ∀ s t u, Step s t → Reachable t u → Reachable s u")
    L.append("")

    # allReachable list
    L.append("def allReachable : List PegState := [")
    for i, s in enumerate(reachable):
        comma = "," if i < len(reachable) - 1 else ""
        L.append(f"  {_state_to_lean(s)}{comma}")
    L.append("]")
    L.append("")

    # Bool checks
    L.append("def allPos : List Pos := [" + ", ".join(f".p{i}" for i in range(n)) + "]")
    L.append("")
    L.append("def checkNoGoal : Bool := allReachable.all (fun s => !isGoalB s)")
    L.append("def checkInitMember : Bool := allReachable.contains initState")
    L.append("def checkClosed : Bool :=")
    L.append("  allReachable.all fun s =>")
    L.append("    allPos.all fun a => allPos.all fun b => allPos.all fun c =>")
    L.append("      !(isValidGeom a b c && s.get a && s.get b && !s.get c) ||")
    L.append("      allReachable.contains (applyJump s a b c)")
    L.append("")

    # native_decide checks
    L.append("theorem checkNoGoal_true : checkNoGoal = true := by native_decide")
    L.append("theorem checkInitMember_true : checkInitMember = true := by native_decide")
    L.append("theorem checkClosed_true : checkClosed = true := by native_decide")
    L.append("")

    # init_in_reachable
    L.append("theorem init_in_reachable : initState ∈ allReachable := by decide")
    L.append("")

    # no_goal_in_reachable — case-split on List.Mem
    L.append("theorem no_goal_in_reachable (s : PegState) (h : s ∈ allReachable) :")
    L.append("    isGoalB s = false := by")
    _emit_list_cases(L, len(reachable), "h", "native_decide")
    L.append("")

    # closed_under_jump — case-split on membership, then on Pos values
    L.append("theorem closed_under_jump (s : PegState) (a b c : Pos)")
    L.append("    (hs : s ∈ allReachable)")
    L.append("    (hg : isValidGeom a b c = true)")
    L.append("    (ha : s.get a = true) (hb : s.get b = true) (hc : s.get c = false) :")
    L.append("    applyJump s a b c ∈ allReachable := by")
    _emit_list_cases_jump(L, len(reachable), "hs", n)
    L.append("")

    # reachable_subset
    L.append("theorem reachable_subset (s t : PegState) (hs : s ∈ allReachable)")
    L.append("    (hr : Reachable s t) : t ∈ allReachable := by")
    L.append("  induction hr with")
    L.append("  | refl _ => exact hs")
    L.append("  | step s₁ t₁ u₁ hstep _ ih =>")
    L.append("    apply ih")
    L.append("    cases hstep with")
    L.append("    | jump a b c hg ha hb hc =>")
    L.append("      exact closed_under_jump s₁ a b c hs hg ha hb hc")
    L.append("")

    # unsolvable
    L.append("theorem unsolvable : ¬ ∃ t : PegState, Reachable initState t ∧ isGoalB t = true := by")
    L.append("  intro ⟨t, hreach, hgoal⟩")
    L.append("  have hmem : t ∈ allReachable := reachable_subset _ _ init_in_reachable hreach")
    L.append("  have hno : isGoalB t = false := no_goal_in_reachable t hmem")
    L.append("  rw [hno] at hgoal")
    L.append("  exact absurd hgoal (by decide)")
    L.append("")
    L.append("#print axioms unsolvable")

    return L


def _emit_list_cases(L: list[str], count: int, var: str, tactic: str):
    """Emit nested cases on List.Mem for `count` elements."""
    indent = "  "
    cur_var = var
    for i in range(count - 1):
        L.append(f"{indent}cases {cur_var} with")
        L.append(f"{indent}| head => {tactic}")
        next_var = f"h{i+1}"
        L.append(f"{indent}| tail _ {next_var} =>")
        indent += "  "
        cur_var = next_var
    # last element
    L.append(f"{indent}cases {cur_var} with")
    L.append(f"{indent}| head => {tactic}")
    L.append(f"{indent}| tail _ hlast => exact absurd hlast (List.not_mem_nil _)")


def _emit_list_cases_jump(L: list[str], count: int, var: str, n: int):
    """Emit nested cases for closed_under_jump proof."""
    indent = "  "
    cur_var = var
    tactic = ("cases a <;> cases b <;> cases c <;> simp [isValidGeom] at hg <;>\n"
              "      simp_all [PegState.get, applyJump, PegState.set, allReachable] <;> decide")
    for i in range(count - 1):
        L.append(f"{indent}cases {cur_var} with")
        L.append(f"{indent}| head =>")
        L.append(f"{indent}  {tactic}")
        next_var = f"h{i+1}"
        L.append(f"{indent}| tail _ {next_var} =>")
        indent += "  "
        cur_var = next_var
    L.append(f"{indent}cases {cur_var} with")
    L.append(f"{indent}| head =>")
    L.append(f"{indent}  {tactic}")
    L.append(f"{indent}| tail _ hlast => exact absurd hlast (List.not_mem_nil _)")
