/-
  Auto-generated from theory.dsl — DO NOT EDIT.

  Unsolvability of {0100} from 0111, by a **separating invariant**.

  The invariant is the manual's `separating`, and its clauses are NOT
  written here by hand. They come from
      ic3_peg4_0111_to_0100.json
  produced by engine-rig/engines/ic3_pdr, and were re-checked here
  before emission: all three obligations recomputed over the full
  state space, the producer's own `conditions` block not believed.

      I(s) = (!pos1 | pos2) & (pos1 | !pos2)

  `proof="computational"`: `inv_closed` is closed by `decide`
  over every state, which keeps the axiom set **empty** and
  costs a 2^4 split. The same trade D-TC-008 records for the
  pagoda route: empty axioms xor a proof that does not grow
  with the board. Both are honest; neither is both.
-/

inductive Pos where
  | p0
  | p1
  | p2
  | p3
  deriving DecidableEq, Repr

/-- One `Bool` per cell: `true` is occupied. -/
structure St where
  p0 : Bool
  p1 : Bool
  p2 : Bool
  p3 : Bool
  deriving DecidableEq, Repr

def St.get (s : St) : Pos → Bool
  | .p0 => s.p0
  | .p1 => s.p1
  | .p2 => s.p2
  | .p3 => s.p3

def St.set (s : St) : Pos → Bool → St
  | .p0, v => { s with p0 := v }
  | .p1, v => { s with p1 := v }
  | .p2, v => { s with p2 := v }
  | .p3, v => { s with p3 := v }

inductive Move where
  | m0   -- jump(0,1,2)
  | m1   -- jump(1,2,3)
  | m2   -- jump(2,1,0)
  | m3   -- jump(3,2,1)
  deriving DecidableEq, Repr

def Move.src : Move → Pos
  | .m0 => .p0
  | .m1 => .p1
  | .m2 => .p2
  | .m3 => .p3

def Move.over : Move → Pos
  | .m0 => .p1
  | .m1 => .p2
  | .m2 => .p1
  | .m3 => .p2

def Move.dst : Move → Pos
  | .m0 => .p2
  | .m1 => .p3
  | .m2 => .p0
  | .m3 => .p1

def legal (s : St) (m : Move) : Bool :=
  s.get m.src && s.get m.over && !s.get m.dst

def applyMove (s : St) (m : Move) : St :=
  ((s.set m.src false).set m.over false).set m.dst true

/-- The engine's separating invariant, clause by clause. -/
def Inv (s : St) : Bool :=
  (!s.p1 || s.p2) && (s.p1 || !s.p2)

def s0 : St := ⟨false, true, true, true⟩

inductive Reachable : St → Prop where
  | init : Reachable s0
  | step : ∀ s m, Reachable s → legal s m = true → Reachable (applyMove s m)

theorem inv_init : Inv s0 = true := by decide

/-- Every state, every move, by `decide`: empty axiom set, 2^4.
    The algebraic form of this proof is the same statement with
    the board left abstract. -/
theorem inv_closed (s : St) (m : Move) (hl : legal s m = true)
    (hi : Inv s = true) : Inv (applyMove s m) = true := by
  revert hl hi
  cases s with
  | mk p0 p1 p2 p3 =>
    cases p0 <;> cases p1 <;> cases p2 <;> cases p3 <;> cases m <;> decide

theorem inv_all (s : St) (h : Reachable s) : Inv s = true := by
  induction h with
  | init => exact inv_init
  | step s m _ hl ih => exact inv_closed s m hl ih

theorem goal_break_0 : Inv ⟨false, true, false, false⟩ = false := by decide

theorem unsolvable : ¬ ∃ s : St, Reachable s ∧ (s = ⟨false, true, false, false⟩) := by
  rintro ⟨s, hr, hg⟩
  have hi := inv_all s hr
  rcases hg with rfl
  · rw [goal_break_0] at hi; exact Bool.noConfusion hi

#print axioms inv_init
#print axioms inv_closed
#print axioms inv_all
#print axioms unsolvable
