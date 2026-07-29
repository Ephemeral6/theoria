/-
  Auto-generated from theory.dsl by compile/gen_lean_a0.py — DO NOT EDIT.
  Problem: a3-l2-oneway.  Arena: 35 cells.  Axes: Door_present, Switch_colour.  States: 140.
  Proofs use `decide` only, so `#print axioms` must come back empty.
  Declared semantics: frame persist, conflict exclusive, cascade single_frame.
  `step` below is total because the manual says `frame persist`; it is
  single-valued because the manual says `conflict exclusive`.
-/

/-- Arena cells, in row-major order:
    c0   = (1, 1)
    c1   = (1, 2)
    c2   = (1, 3)
    c3   = (1, 5)
    c4   = (1, 7)
    c5   = (2, 1)
    c6   = (2, 5)
    c7   = (2, 6)
    c8   = (2, 7)
    c9   = (3, 1)
    c10  = (3, 3)
    c11  = (3, 5)
    c12  = (3, 6)
    c13  = (3, 7)
    c14  = (4, 1)
    c15  = (4, 2)
    c16  = (4, 3)
    c17  = (4, 5)
    c18  = (4, 6)
    c19  = (4, 7)
    c20  = (5, 2)
    c21  = (5, 3)
    c22  = (5, 5)
    c23  = (5, 6)
    c24  = (5, 7)
    c25  = (6, 1)
    c26  = (6, 2)
    c27  = (6, 3)
    c28  = (6, 5)
    c29  = (6, 6)
    c30  = (6, 7)
    c31  = (7, 1)
    c32  = (7, 2)
    c33  = (7, 3)
    c34  = (7, 6)
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
  deriving DecidableEq, Repr

inductive Dir where
  | up
  | down
  | left
  | right
  deriving DecidableEq, Repr

/-- `Door_present`, as observed: False, True -/
inductive DoorPresent where
  | no
  | yes
  deriving DecidableEq, Repr

/-- `Switch_colour`, as observed: 7, 8 -/
inductive SwitchColour where
  | v7
  | v8
  deriving DecidableEq, Repr

structure St where
  cart : Cell
  doorPresent : DoorPresent
  switchColour : SwitchColour
  deriving DecidableEq, Repr

def s0 : St := ⟨Cell.c30, DoorPresent.yes, SwitchColour.v7⟩

/-- The manual's rules, transcribed from the executable form. -/
def step : St → Dir → St
  | ⟨Cell.c0, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c0, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c0, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c5, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c0, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c0, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c0, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c1, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c1, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c1, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c1, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c1, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c1, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c0, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c1, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c2, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c2, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c2, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c2, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c2, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c2, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c1, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c2, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c2, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c3, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c3, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c3, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c6, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c3, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c3, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c3, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c14, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c4, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c4, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c4, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c8, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c4, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c14, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c4, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c4, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c5, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c0, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c5, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c9, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c5, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c5, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c5, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c5, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c6, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c3, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c6, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c11, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c6, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c6, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c6, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c7, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c7, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c14, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c7, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c12, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c7, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c6, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c7, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c8, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c8, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c4, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c8, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c13, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c8, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c7, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c8, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c8, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c9, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c5, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c9, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c14, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c9, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c9, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c9, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c9, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c10, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c10, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c10, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c16, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c10, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c10, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c10, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c10, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c11, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c6, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c11, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c17, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c11, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c11, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c11, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c12, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c12, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c7, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c12, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c18, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c12, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c11, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c12, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c13, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c13, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c8, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c13, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c19, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c13, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c12, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c13, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c13, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c14, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c9, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c14, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c3, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c14, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c14, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c14, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c15, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c15, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c15, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c15, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c20, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c15, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c14, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c15, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c16, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c16, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c10, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c16, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c21, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c16, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c15, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c16, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c16, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c17, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c11, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c17, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c22, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c17, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c17, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c17, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c18, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c18, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c12, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c18, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c23, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c18, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c17, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c18, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c19, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c19, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c13, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c19, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c24, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c19, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c18, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c19, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c19, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c20, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c15, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c20, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c26, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c20, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c3, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c20, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c21, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c21, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c16, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c21, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c27, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c21, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c20, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c21, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c21, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c22, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c17, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c22, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c28, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c22, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c22, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c22, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c23, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c23, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c18, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c23, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c29, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c23, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c22, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c23, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c24, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c24, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c19, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c24, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c30, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c24, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c23, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c24, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c24, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c25, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c3, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c25, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c31, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c25, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c25, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c25, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c26, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c26, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c20, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c26, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c32, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c26, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c25, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c26, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c27, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c27, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c21, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c27, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c33, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c27, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c26, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c27, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c27, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c28, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c22, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c28, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c28, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c28, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c28, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c28, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c29, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c29, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c23, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c29, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c29, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c29, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c28, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c29, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c30, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c30, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c24, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c30, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c30, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c30, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c29, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c30, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c30, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c31, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c25, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c31, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c31, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c31, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c31, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c31, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c32, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c32, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c26, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c32, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c32, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c32, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c31, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c32, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c33, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c33, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c27, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c33, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c33, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c33, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c32, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c33, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c33, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c34, DoorPresent.no, SwitchColour.v7⟩, .up => ⟨Cell.c29, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c34, DoorPresent.no, SwitchColour.v7⟩, .down => ⟨Cell.c34, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c34, DoorPresent.no, SwitchColour.v7⟩, .left => ⟨Cell.c34, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c34, DoorPresent.no, SwitchColour.v7⟩, .right => ⟨Cell.c34, DoorPresent.no, SwitchColour.v7⟩
  | ⟨Cell.c0, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c0, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c0, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c5, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c0, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c0, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c0, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c1, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c1, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c1, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c1, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c1, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c1, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c0, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c1, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c2, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c2, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c2, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c2, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c2, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c2, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c1, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c2, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c2, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c3, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c3, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c3, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c6, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c3, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c3, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c3, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c14, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c4, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c4, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c4, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c8, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c4, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c14, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c4, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c4, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c5, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c0, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c5, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c9, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c5, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c5, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c5, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c5, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c6, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c3, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c6, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c11, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c6, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c6, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c6, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c7, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c7, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c14, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c7, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c12, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c7, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c6, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c7, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c8, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c8, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c4, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c8, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c13, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c8, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c7, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c8, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c8, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c9, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c5, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c9, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c14, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c9, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c9, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c9, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c9, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c10, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c10, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c10, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c16, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c10, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c10, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c10, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c10, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c11, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c6, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c11, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c17, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c11, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c11, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c11, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c12, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c12, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c7, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c12, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c18, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c12, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c11, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c12, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c13, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c13, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c8, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c13, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c19, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c13, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c12, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c13, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c13, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c14, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c9, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c14, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c3, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c14, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c14, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c14, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c15, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c15, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c15, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c15, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c20, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c15, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c14, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c15, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c16, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c16, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c10, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c16, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c21, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c16, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c15, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c16, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c16, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c17, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c11, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c17, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c22, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c17, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c17, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c17, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c18, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c18, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c12, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c18, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c23, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c18, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c17, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c18, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c19, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c19, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c13, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c19, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c24, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c19, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c18, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c19, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c19, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c20, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c15, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c20, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c26, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c20, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c3, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c20, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c21, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c21, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c16, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c21, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c27, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c21, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c20, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c21, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c21, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c22, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c17, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c22, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c28, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c22, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c22, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c22, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c23, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c23, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c18, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c23, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c29, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c23, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c22, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c23, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c24, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c24, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c19, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c24, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c30, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c24, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c23, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c24, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c24, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c25, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c3, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c25, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c31, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c25, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c25, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c25, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c26, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c26, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c20, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c26, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c32, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c26, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c25, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c26, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c27, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c27, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c21, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c27, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c33, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c27, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c26, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c27, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c27, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c28, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c22, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c28, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c28, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c28, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c28, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c28, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c29, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c29, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c23, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c29, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c29, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c29, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c28, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c29, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c30, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c30, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c24, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c30, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c30, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c30, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c29, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c30, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c30, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c31, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c25, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c31, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c31, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c31, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c31, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c31, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c32, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c32, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c26, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c32, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c32, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c32, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c31, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c32, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c33, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c33, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c27, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c33, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c33, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c33, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c32, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c33, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c33, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c34, DoorPresent.no, SwitchColour.v8⟩, .up => ⟨Cell.c29, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c34, DoorPresent.no, SwitchColour.v8⟩, .down => ⟨Cell.c34, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c34, DoorPresent.no, SwitchColour.v8⟩, .left => ⟨Cell.c34, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c34, DoorPresent.no, SwitchColour.v8⟩, .right => ⟨Cell.c34, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c0, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c0, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c0, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c5, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c0, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c0, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c0, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c1, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c1, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c1, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c1, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c1, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c1, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c0, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c1, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c2, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c2, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c2, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c2, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c2, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c2, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c1, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c2, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c2, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c3, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c3, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c3, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c6, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c3, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c3, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c3, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c14, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c4, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c4, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c4, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c8, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c4, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c14, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c4, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c4, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c5, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c0, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c5, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c5, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c5, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c5, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c5, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c5, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c6, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c3, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c6, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c11, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c6, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c6, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c6, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c7, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c7, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c14, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c7, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c12, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c7, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c6, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c7, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c8, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c8, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c4, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c8, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c13, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c8, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c7, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c8, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c8, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c9, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c5, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c9, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c14, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c9, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c9, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c9, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c9, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c10, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c10, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c10, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c16, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c10, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c10, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c10, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c10, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c11, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c6, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c11, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c17, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c11, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c11, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c11, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c12, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c12, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c7, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c12, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c18, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c12, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c11, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c12, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c13, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c13, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c8, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c13, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c19, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c13, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c12, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c13, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c13, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c14, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c14, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c14, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c3, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c14, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c14, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c14, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c15, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c15, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c15, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c15, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c20, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c15, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c14, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c15, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c16, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c16, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c10, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c16, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c21, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c16, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c15, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c16, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c16, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c17, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c11, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c17, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c22, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c17, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c17, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c17, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c18, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c18, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c12, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c18, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c23, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c18, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c17, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c18, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c19, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c19, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c13, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c19, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c24, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c19, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c18, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c19, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c19, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c20, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c15, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c20, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c26, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c20, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c3, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c20, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c21, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c21, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c16, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c21, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c27, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c21, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c20, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c21, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c21, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c22, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c17, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c22, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c28, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c22, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c22, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c22, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c23, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c23, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c18, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c23, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c29, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c23, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c22, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c23, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c24, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c24, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c19, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c24, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c30, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c24, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c23, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c24, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c24, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c25, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c3, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c25, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c31, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c25, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c25, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c25, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c26, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c26, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c20, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c26, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c32, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c26, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c25, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c26, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c27, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c27, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c21, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c27, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c33, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c27, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c26, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c27, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c27, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c28, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c22, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c28, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c28, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c28, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c28, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c28, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c29, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c29, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c23, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c29, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c29, DoorPresent.no, SwitchColour.v8⟩
  | ⟨Cell.c29, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c28, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c29, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c30, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c30, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c24, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c30, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c30, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c30, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c29, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c30, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c30, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c31, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c25, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c31, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c31, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c31, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c31, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c31, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c32, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c32, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c26, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c32, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c32, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c32, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c31, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c32, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c33, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c33, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c27, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c33, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c33, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c33, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c32, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c33, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c33, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c34, DoorPresent.yes, SwitchColour.v7⟩, .up => ⟨Cell.c29, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c34, DoorPresent.yes, SwitchColour.v7⟩, .down => ⟨Cell.c34, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c34, DoorPresent.yes, SwitchColour.v7⟩, .left => ⟨Cell.c34, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c34, DoorPresent.yes, SwitchColour.v7⟩, .right => ⟨Cell.c34, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c0, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c0, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c0, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c5, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c0, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c0, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c0, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c1, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c1, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c1, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c1, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c1, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c1, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c0, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c1, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c2, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c2, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c2, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c2, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c2, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c2, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c1, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c2, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c2, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c3, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c3, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c3, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c6, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c3, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c3, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c3, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c14, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c4, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c4, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c4, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c8, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c4, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c14, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c4, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c4, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c5, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c0, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c5, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c5, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c5, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c5, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c5, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c5, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c6, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c3, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c6, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c11, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c6, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c6, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c6, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c7, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c7, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c14, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c7, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c12, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c7, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c6, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c7, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c8, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c8, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c4, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c8, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c13, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c8, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c7, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c8, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c8, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c9, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c5, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c9, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c14, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c9, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c9, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c9, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c9, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c10, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c10, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c10, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c16, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c10, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c10, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c10, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c10, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c11, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c6, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c11, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c17, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c11, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c11, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c11, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c12, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c12, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c7, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c12, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c18, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c12, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c11, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c12, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c13, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c13, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c8, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c13, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c19, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c13, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c12, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c13, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c13, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c14, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c14, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c14, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c3, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c14, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c14, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c14, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c15, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c15, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c15, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c15, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c20, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c15, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c14, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c15, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c16, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c16, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c10, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c16, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c21, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c16, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c15, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c16, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c16, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c17, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c11, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c17, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c22, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c17, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c17, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c17, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c18, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c18, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c12, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c18, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c23, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c18, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c17, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c18, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c19, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c19, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c13, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c19, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c24, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c19, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c18, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c19, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c19, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c20, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c15, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c20, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c26, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c20, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c3, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c20, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c21, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c21, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c16, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c21, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c27, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c21, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c20, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c21, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c21, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c22, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c17, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c22, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c28, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c22, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c22, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c22, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c23, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c23, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c18, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c23, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c29, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c23, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c22, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c23, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c24, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c24, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c19, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c24, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c30, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c24, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c23, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c24, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c24, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c25, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c3, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c25, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c31, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c25, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c25, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c25, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c26, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c26, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c20, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c26, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c32, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c26, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c25, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c26, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c27, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c27, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c21, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c27, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c33, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c27, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c26, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c27, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c27, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c28, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c22, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c28, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c28, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c28, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c28, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c28, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c29, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c29, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c23, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c29, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c29, DoorPresent.yes, SwitchColour.v7⟩
  | ⟨Cell.c29, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c28, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c29, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c30, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c30, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c24, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c30, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c30, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c30, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c29, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c30, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c30, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c31, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c25, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c31, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c31, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c31, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c31, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c31, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c32, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c32, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c26, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c32, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c32, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c32, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c31, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c32, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c33, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c33, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c27, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c33, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c33, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c33, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c32, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c33, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c33, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c34, DoorPresent.yes, SwitchColour.v8⟩, .up => ⟨Cell.c29, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c34, DoorPresent.yes, SwitchColour.v8⟩, .down => ⟨Cell.c34, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c34, DoorPresent.yes, SwitchColour.v8⟩, .left => ⟨Cell.c34, DoorPresent.yes, SwitchColour.v8⟩
  | ⟨Cell.c34, DoorPresent.yes, SwitchColour.v8⟩, .right => ⟨Cell.c34, DoorPresent.yes, SwitchColour.v8⟩

def Goal (s : St) : Bool := s.cart == Cell.c0

inductive Reachable : St → Prop where
  | init : Reachable s0
  | step : ∀ (s : St) (d : Dir), Reachable s → Reachable (step s d)

-- switch_door_latch (THEORIZE_LOG L-02, zero_space): exactly one of
-- 'the Switch shows 8' and 'the Door exists' holds, in every reachable
-- state.  A0's Button was a latch and could only witness one polarity;
-- A3's Switch toggles, so both directions of this law have witnesses in
-- the level-1 sweep and neither half is an analogy from the other.
-- cart_unique (L-01) is NOT proved here: representing the state as the
-- Cart's cell already assumes there is exactly one Cart, so a Lean proof
-- would be discharged by the representation.  It is checked where it can
-- actually fail — per frame, by the cheap layer's responsibility pass.
def I (s : St) : Bool := (s.switchColour == SwitchColour.v8) != (s.doorPresent == DoorPresent.yes)

theorem inv_init : I s0 = true := by decide

theorem inv_closed (s : St) (d : Dir) : I s = true → I (step s d) = true := by
  obtain ⟨c, doorPresent, switchColour⟩ := s
  cases c <;> cases doorPresent <;> cases switchColour <;> cases d <;> decide

theorem inv_all (s : St) (h : Reachable s) : I s = true := by
  induction h with
  | init => decide
  | step s d _ ih => exact inv_closed s d ih

#print axioms inv_all
