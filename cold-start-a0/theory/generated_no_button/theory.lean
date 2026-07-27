/-
  Auto-generated from theory.dsl by compile/gen_lean_a0.py — DO NOT EDIT.
  Problem: a0-no-button.  Arena: 37 cells.  Axes: none.  States: 37.
  Proofs use `decide` only, so `#print axioms` must come back empty.
  Declared semantics: frame persist, conflict exclusive, cascade single_frame.
  `step` below is total because the manual says `frame persist`; it is
  single-valued because the manual says `conflict exclusive`.
-/

/-- Arena cells, in row-major order:
    c0   = (1, 1)
    c1   = (1, 2)
    c2   = (1, 3)
    c3   = (1, 4)
    c4   = (1, 6)
    c5   = (1, 7)
    c6   = (2, 1)
    c7   = (2, 2)
    c8   = (2, 3)
    c9   = (2, 4)
    c10  = (2, 6)
    c11  = (2, 7)
    c12  = (3, 1)
    c13  = (3, 2)
    c14  = (3, 3)
    c15  = (3, 4)
    c16  = (3, 6)
    c17  = (3, 7)
    c18  = (4, 1)
    c19  = (4, 2)
    c20  = (4, 3)
    c21  = (4, 4)
    c22  = (4, 6)
    c23  = (4, 7)
    c24  = (5, 1)
    c25  = (5, 2)
    c26  = (5, 3)
    c27  = (5, 4)
    c28  = (5, 6)
    c29  = (5, 7)
    c30  = (6, 1)
    c31  = (6, 2)
    c32  = (6, 3)
    c33  = (6, 6)
    c34  = (6, 7)
    c35  = (7, 6)
    c36  = (7, 7)
-/
inductive Cell where
  | c0
  | c1
  | c2
  | c3
  | c4
  | c5
  | c6
  | c7
  | c8
  | c9
  | c10
  | c11
  | c12
  | c13
  | c14
  | c15
  | c16
  | c17
  | c18
  | c19
  | c20
  | c21
  | c22
  | c23
  | c24
  | c25
  | c26
  | c27
  | c28
  | c29
  | c30
  | c31
  | c32
  | c33
  | c34
  | c35
  | c36
  deriving DecidableEq, Repr

inductive Dir where
  | up
  | down
  | left
  | right
  deriving DecidableEq, Repr

structure St where
  cart : Cell
  deriving DecidableEq, Repr

def s0 : St := ⟨Cell.c24⟩

/-- The manual's rules, transcribed from the executable form. -/
def step : St → Dir → St
  | ⟨Cell.c0⟩, .up => ⟨Cell.c0⟩
  | ⟨Cell.c0⟩, .down => ⟨Cell.c6⟩
  | ⟨Cell.c0⟩, .left => ⟨Cell.c0⟩
  | ⟨Cell.c0⟩, .right => ⟨Cell.c1⟩
  | ⟨Cell.c1⟩, .up => ⟨Cell.c1⟩
  | ⟨Cell.c1⟩, .down => ⟨Cell.c7⟩
  | ⟨Cell.c1⟩, .left => ⟨Cell.c0⟩
  | ⟨Cell.c1⟩, .right => ⟨Cell.c2⟩
  | ⟨Cell.c2⟩, .up => ⟨Cell.c2⟩
  | ⟨Cell.c2⟩, .down => ⟨Cell.c8⟩
  | ⟨Cell.c2⟩, .left => ⟨Cell.c1⟩
  | ⟨Cell.c2⟩, .right => ⟨Cell.c3⟩
  | ⟨Cell.c3⟩, .up => ⟨Cell.c3⟩
  | ⟨Cell.c3⟩, .down => ⟨Cell.c9⟩
  | ⟨Cell.c3⟩, .left => ⟨Cell.c2⟩
  | ⟨Cell.c3⟩, .right => ⟨Cell.c3⟩
  | ⟨Cell.c4⟩, .up => ⟨Cell.c4⟩
  | ⟨Cell.c4⟩, .down => ⟨Cell.c10⟩
  | ⟨Cell.c4⟩, .left => ⟨Cell.c4⟩
  | ⟨Cell.c4⟩, .right => ⟨Cell.c5⟩
  | ⟨Cell.c5⟩, .up => ⟨Cell.c5⟩
  | ⟨Cell.c5⟩, .down => ⟨Cell.c11⟩
  | ⟨Cell.c5⟩, .left => ⟨Cell.c4⟩
  | ⟨Cell.c5⟩, .right => ⟨Cell.c5⟩
  | ⟨Cell.c6⟩, .up => ⟨Cell.c0⟩
  | ⟨Cell.c6⟩, .down => ⟨Cell.c12⟩
  | ⟨Cell.c6⟩, .left => ⟨Cell.c6⟩
  | ⟨Cell.c6⟩, .right => ⟨Cell.c7⟩
  | ⟨Cell.c7⟩, .up => ⟨Cell.c1⟩
  | ⟨Cell.c7⟩, .down => ⟨Cell.c13⟩
  | ⟨Cell.c7⟩, .left => ⟨Cell.c6⟩
  | ⟨Cell.c7⟩, .right => ⟨Cell.c8⟩
  | ⟨Cell.c8⟩, .up => ⟨Cell.c2⟩
  | ⟨Cell.c8⟩, .down => ⟨Cell.c14⟩
  | ⟨Cell.c8⟩, .left => ⟨Cell.c7⟩
  | ⟨Cell.c8⟩, .right => ⟨Cell.c9⟩
  | ⟨Cell.c9⟩, .up => ⟨Cell.c3⟩
  | ⟨Cell.c9⟩, .down => ⟨Cell.c15⟩
  | ⟨Cell.c9⟩, .left => ⟨Cell.c8⟩
  | ⟨Cell.c9⟩, .right => ⟨Cell.c9⟩
  | ⟨Cell.c10⟩, .up => ⟨Cell.c4⟩
  | ⟨Cell.c10⟩, .down => ⟨Cell.c16⟩
  | ⟨Cell.c10⟩, .left => ⟨Cell.c10⟩
  | ⟨Cell.c10⟩, .right => ⟨Cell.c11⟩
  | ⟨Cell.c11⟩, .up => ⟨Cell.c5⟩
  | ⟨Cell.c11⟩, .down => ⟨Cell.c17⟩
  | ⟨Cell.c11⟩, .left => ⟨Cell.c10⟩
  | ⟨Cell.c11⟩, .right => ⟨Cell.c11⟩
  | ⟨Cell.c12⟩, .up => ⟨Cell.c6⟩
  | ⟨Cell.c12⟩, .down => ⟨Cell.c18⟩
  | ⟨Cell.c12⟩, .left => ⟨Cell.c12⟩
  | ⟨Cell.c12⟩, .right => ⟨Cell.c13⟩
  | ⟨Cell.c13⟩, .up => ⟨Cell.c7⟩
  | ⟨Cell.c13⟩, .down => ⟨Cell.c19⟩
  | ⟨Cell.c13⟩, .left => ⟨Cell.c12⟩
  | ⟨Cell.c13⟩, .right => ⟨Cell.c14⟩
  | ⟨Cell.c14⟩, .up => ⟨Cell.c8⟩
  | ⟨Cell.c14⟩, .down => ⟨Cell.c20⟩
  | ⟨Cell.c14⟩, .left => ⟨Cell.c13⟩
  | ⟨Cell.c14⟩, .right => ⟨Cell.c15⟩
  | ⟨Cell.c15⟩, .up => ⟨Cell.c9⟩
  | ⟨Cell.c15⟩, .down => ⟨Cell.c21⟩
  | ⟨Cell.c15⟩, .left => ⟨Cell.c14⟩
  | ⟨Cell.c15⟩, .right => ⟨Cell.c15⟩
  | ⟨Cell.c16⟩, .up => ⟨Cell.c10⟩
  | ⟨Cell.c16⟩, .down => ⟨Cell.c22⟩
  | ⟨Cell.c16⟩, .left => ⟨Cell.c16⟩
  | ⟨Cell.c16⟩, .right => ⟨Cell.c17⟩
  | ⟨Cell.c17⟩, .up => ⟨Cell.c11⟩
  | ⟨Cell.c17⟩, .down => ⟨Cell.c23⟩
  | ⟨Cell.c17⟩, .left => ⟨Cell.c16⟩
  | ⟨Cell.c17⟩, .right => ⟨Cell.c17⟩
  | ⟨Cell.c18⟩, .up => ⟨Cell.c12⟩
  | ⟨Cell.c18⟩, .down => ⟨Cell.c24⟩
  | ⟨Cell.c18⟩, .left => ⟨Cell.c18⟩
  | ⟨Cell.c18⟩, .right => ⟨Cell.c19⟩
  | ⟨Cell.c19⟩, .up => ⟨Cell.c13⟩
  | ⟨Cell.c19⟩, .down => ⟨Cell.c25⟩
  | ⟨Cell.c19⟩, .left => ⟨Cell.c18⟩
  | ⟨Cell.c19⟩, .right => ⟨Cell.c20⟩
  | ⟨Cell.c20⟩, .up => ⟨Cell.c14⟩
  | ⟨Cell.c20⟩, .down => ⟨Cell.c26⟩
  | ⟨Cell.c20⟩, .left => ⟨Cell.c19⟩
  | ⟨Cell.c20⟩, .right => ⟨Cell.c21⟩
  | ⟨Cell.c21⟩, .up => ⟨Cell.c15⟩
  | ⟨Cell.c21⟩, .down => ⟨Cell.c27⟩
  | ⟨Cell.c21⟩, .left => ⟨Cell.c20⟩
  | ⟨Cell.c21⟩, .right => ⟨Cell.c21⟩
  | ⟨Cell.c22⟩, .up => ⟨Cell.c16⟩
  | ⟨Cell.c22⟩, .down => ⟨Cell.c28⟩
  | ⟨Cell.c22⟩, .left => ⟨Cell.c22⟩
  | ⟨Cell.c22⟩, .right => ⟨Cell.c23⟩
  | ⟨Cell.c23⟩, .up => ⟨Cell.c17⟩
  | ⟨Cell.c23⟩, .down => ⟨Cell.c29⟩
  | ⟨Cell.c23⟩, .left => ⟨Cell.c22⟩
  | ⟨Cell.c23⟩, .right => ⟨Cell.c23⟩
  | ⟨Cell.c24⟩, .up => ⟨Cell.c18⟩
  | ⟨Cell.c24⟩, .down => ⟨Cell.c30⟩
  | ⟨Cell.c24⟩, .left => ⟨Cell.c24⟩
  | ⟨Cell.c24⟩, .right => ⟨Cell.c25⟩
  | ⟨Cell.c25⟩, .up => ⟨Cell.c19⟩
  | ⟨Cell.c25⟩, .down => ⟨Cell.c31⟩
  | ⟨Cell.c25⟩, .left => ⟨Cell.c24⟩
  | ⟨Cell.c25⟩, .right => ⟨Cell.c26⟩
  | ⟨Cell.c26⟩, .up => ⟨Cell.c20⟩
  | ⟨Cell.c26⟩, .down => ⟨Cell.c32⟩
  | ⟨Cell.c26⟩, .left => ⟨Cell.c25⟩
  | ⟨Cell.c26⟩, .right => ⟨Cell.c27⟩
  | ⟨Cell.c27⟩, .up => ⟨Cell.c21⟩
  | ⟨Cell.c27⟩, .down => ⟨Cell.c27⟩
  | ⟨Cell.c27⟩, .left => ⟨Cell.c26⟩
  | ⟨Cell.c27⟩, .right => ⟨Cell.c27⟩
  | ⟨Cell.c28⟩, .up => ⟨Cell.c22⟩
  | ⟨Cell.c28⟩, .down => ⟨Cell.c33⟩
  | ⟨Cell.c28⟩, .left => ⟨Cell.c28⟩
  | ⟨Cell.c28⟩, .right => ⟨Cell.c29⟩
  | ⟨Cell.c29⟩, .up => ⟨Cell.c23⟩
  | ⟨Cell.c29⟩, .down => ⟨Cell.c34⟩
  | ⟨Cell.c29⟩, .left => ⟨Cell.c28⟩
  | ⟨Cell.c29⟩, .right => ⟨Cell.c29⟩
  | ⟨Cell.c30⟩, .up => ⟨Cell.c24⟩
  | ⟨Cell.c30⟩, .down => ⟨Cell.c30⟩
  | ⟨Cell.c30⟩, .left => ⟨Cell.c30⟩
  | ⟨Cell.c30⟩, .right => ⟨Cell.c31⟩
  | ⟨Cell.c31⟩, .up => ⟨Cell.c25⟩
  | ⟨Cell.c31⟩, .down => ⟨Cell.c31⟩
  | ⟨Cell.c31⟩, .left => ⟨Cell.c30⟩
  | ⟨Cell.c31⟩, .right => ⟨Cell.c32⟩
  | ⟨Cell.c32⟩, .up => ⟨Cell.c26⟩
  | ⟨Cell.c32⟩, .down => ⟨Cell.c0⟩
  | ⟨Cell.c32⟩, .left => ⟨Cell.c31⟩
  | ⟨Cell.c32⟩, .right => ⟨Cell.c32⟩
  | ⟨Cell.c33⟩, .up => ⟨Cell.c28⟩
  | ⟨Cell.c33⟩, .down => ⟨Cell.c35⟩
  | ⟨Cell.c33⟩, .left => ⟨Cell.c33⟩
  | ⟨Cell.c33⟩, .right => ⟨Cell.c34⟩
  | ⟨Cell.c34⟩, .up => ⟨Cell.c29⟩
  | ⟨Cell.c34⟩, .down => ⟨Cell.c36⟩
  | ⟨Cell.c34⟩, .left => ⟨Cell.c33⟩
  | ⟨Cell.c34⟩, .right => ⟨Cell.c34⟩
  | ⟨Cell.c35⟩, .up => ⟨Cell.c33⟩
  | ⟨Cell.c35⟩, .down => ⟨Cell.c35⟩
  | ⟨Cell.c35⟩, .left => ⟨Cell.c35⟩
  | ⟨Cell.c35⟩, .right => ⟨Cell.c36⟩
  | ⟨Cell.c36⟩, .up => ⟨Cell.c34⟩
  | ⟨Cell.c36⟩, .down => ⟨Cell.c36⟩
  | ⟨Cell.c36⟩, .left => ⟨Cell.c35⟩
  | ⟨Cell.c36⟩, .right => ⟨Cell.c36⟩

def Goal (s : St) : Bool := s.cart == Cell.c11

inductive Reachable : St → Prop where
  | init : Reachable s0
  | step : ∀ (s : St) (d : Dir), Reachable s → Reachable (step s d)


/-- Pagoda weight: 0 on the room the Cart starts in, 1 outside. -/
def w : Cell → Nat
  | .c0 => 0
  | .c1 => 0
  | .c2 => 0
  | .c3 => 0
  | .c4 => 1
  | .c5 => 1
  | .c6 => 0
  | .c7 => 0
  | .c8 => 0
  | .c9 => 0
  | .c10 => 1
  | .c11 => 1
  | .c12 => 0
  | .c13 => 0
  | .c14 => 0
  | .c15 => 0
  | .c16 => 1
  | .c17 => 1
  | .c18 => 0
  | .c19 => 0
  | .c20 => 0
  | .c21 => 0
  | .c22 => 1
  | .c23 => 1
  | .c24 => 0
  | .c25 => 0
  | .c26 => 0
  | .c27 => 0
  | .c28 => 1
  | .c29 => 1
  | .c30 => 0
  | .c31 => 0
  | .c32 => 0
  | .c33 => 1
  | .c34 => 1
  | .c35 => 1
  | .c36 => 1

-- right_room_locked (THEORIZE_LOG L-04), proposed by zero_space as a GF(2)
-- occupancy law over 37 arena cells and adjudicated into this form.
-- w = 0 exactly on the 23 cells the Cart was ever observed on; the goal cell
-- carries w = 1.  I(s) := w(cart) = 0 is 'the potential never rises'.
def I (s : St) : Bool := w s.cart == 0

theorem inv_init : I s0 = true := by decide

theorem inv_closed (s : St) (d : Dir) : I s = true → I (step s d) = true := by
  obtain ⟨c⟩ := s
  cases c <;> cases d <;> decide

theorem inv_all (s : St) (h : Reachable s) : I s = true := by
  induction h with
  | init => decide
  | step s d _ ih => exact inv_closed s d ih

theorem goal_break (s : St) : Goal s = true → I s = false := by
  obtain ⟨c⟩ := s
  cases c <;> decide

theorem unsolvable : ¬ ∃ s : St, Reachable s ∧ Goal s = true := by
  rintro ⟨s, hr, hg⟩
  have hi : I s = true := inv_all s hr
  have hb : I s = false := goal_break s hg
  rw [hi] at hb
  exact absurd hb (by decide)

#print axioms unsolvable
