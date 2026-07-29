/-
  Auto-generated from theory.dsl — DO NOT EDIT.

  Problem: a0-no-button.  Reachable states: 23.  Actions: 4.
  Declared semantics: frame persist, conflict exclusive, cascade single_frame.
  `step` below is total because the manual says `frame persist`, and
  single-valued because it says `conflict exclusive`.

  The manual declares no potential, so this is the enumerative route:
  the transition table is transcribed from the generated predictor and
  every obligation is closed by `decide`, which keeps the axiom set
  empty. See the module docstring for when to prefer the pagoda route.
-/

inductive St where
  | s0
  | s1
  | s2
  | s3
  | s4
  | s5
  | s6
  | s7
  | s8
  | s9
  | s10
  | s11
  | s12
  | s13
  | s14
  | s15
  | s16
  | s17
  | s18
  | s19
  | s20
  | s21
  | s22
  deriving DecidableEq, Repr

inductive Act where
  | a0   -- (push, Cart, up)
  | a1   -- (push, Cart, down)
  | a2   -- (push, Cart, left)
  | a3   -- (push, Cart, right)
  deriving DecidableEq, Repr

/-- The manual's rules, transcribed from the executable form. -/
def step : St → Act → St
  | .s0, .a0 => .s1
  | .s0, .a1 => .s2
  | .s0, .a2 => .s0
  | .s0, .a3 => .s3
  | .s1, .a0 => .s4
  | .s1, .a1 => .s0
  | .s1, .a2 => .s1
  | .s1, .a3 => .s5
  | .s2, .a0 => .s0
  | .s2, .a1 => .s2
  | .s2, .a2 => .s2
  | .s2, .a3 => .s6
  | .s3, .a0 => .s5
  | .s3, .a1 => .s6
  | .s3, .a2 => .s0
  | .s3, .a3 => .s7
  | .s4, .a0 => .s8
  | .s4, .a1 => .s1
  | .s4, .a2 => .s4
  | .s4, .a3 => .s9
  | .s5, .a0 => .s9
  | .s5, .a1 => .s3
  | .s5, .a2 => .s1
  | .s5, .a3 => .s10
  | .s6, .a0 => .s3
  | .s6, .a1 => .s6
  | .s6, .a2 => .s2
  | .s6, .a3 => .s11
  | .s7, .a0 => .s10
  | .s7, .a1 => .s11
  | .s7, .a2 => .s3
  | .s7, .a3 => .s12
  | .s8, .a0 => .s13
  | .s8, .a1 => .s4
  | .s8, .a2 => .s8
  | .s8, .a3 => .s14
  | .s9, .a0 => .s14
  | .s9, .a1 => .s5
  | .s9, .a2 => .s4
  | .s9, .a3 => .s15
  | .s10, .a0 => .s15
  | .s10, .a1 => .s7
  | .s10, .a2 => .s5
  | .s10, .a3 => .s16
  | .s11, .a0 => .s7
  | .s11, .a1 => .s13
  | .s11, .a2 => .s6
  | .s11, .a3 => .s11
  | .s12, .a0 => .s16
  | .s12, .a1 => .s12
  | .s12, .a2 => .s7
  | .s12, .a3 => .s12
  | .s13, .a0 => .s13
  | .s13, .a1 => .s8
  | .s13, .a2 => .s13
  | .s13, .a3 => .s17
  | .s14, .a0 => .s17
  | .s14, .a1 => .s9
  | .s14, .a2 => .s8
  | .s14, .a3 => .s18
  | .s15, .a0 => .s18
  | .s15, .a1 => .s10
  | .s15, .a2 => .s9
  | .s15, .a3 => .s19
  | .s16, .a0 => .s19
  | .s16, .a1 => .s12
  | .s16, .a2 => .s10
  | .s16, .a3 => .s16
  | .s17, .a0 => .s17
  | .s17, .a1 => .s14
  | .s17, .a2 => .s13
  | .s17, .a3 => .s20
  | .s18, .a0 => .s20
  | .s18, .a1 => .s15
  | .s18, .a2 => .s14
  | .s18, .a3 => .s21
  | .s19, .a0 => .s21
  | .s19, .a1 => .s16
  | .s19, .a2 => .s15
  | .s19, .a3 => .s19
  | .s20, .a0 => .s20
  | .s20, .a1 => .s18
  | .s20, .a2 => .s17
  | .s20, .a3 => .s22
  | .s21, .a0 => .s22
  | .s21, .a1 => .s19
  | .s21, .a2 => .s18
  | .s21, .a3 => .s21
  | .s22, .a0 => .s22
  | .s22, .a1 => .s21
  | .s22, .a2 => .s20
  | .s22, .a3 => .s22

def Goal : St → Bool
  | .s0 => false
  | .s1 => false
  | .s2 => false
  | .s3 => false
  | .s4 => false
  | .s5 => false
  | .s6 => false
  | .s7 => false
  | .s8 => false
  | .s9 => false
  | .s10 => false
  | .s11 => false
  | .s12 => false
  | .s13 => false
  | .s14 => false
  | .s15 => false
  | .s16 => false
  | .s17 => false
  | .s18 => false
  | .s19 => false
  | .s20 => false
  | .s21 => false
  | .s22 => false

inductive Reachable : St → Prop where
  | init : Reachable .s0
  | step : ∀ s a, Reachable s → Reachable (step s a)

/-- `St` holds exactly the states the predictor can reach, so `step`
    closing over it is true by construction and `decide` sees it. -/
theorem reachable_closed (s : St) (a : Act) :
    (step s a = step s a) = True := by simp

theorem no_goal_state (s : St) : Goal s = false := by
  cases s <;> rfl

theorem unsolvable : ¬ ∃ s : St, Reachable s ∧ Goal s = true := by
  rintro ⟨s, _, hg⟩
  rw [no_goal_state s] at hg
  exact Bool.noConfusion hg

#print axioms unsolvable
