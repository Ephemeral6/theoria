/-
  Auto-generated from theory.dsl by compile/gen_lean_a0.py — DO NOT EDIT.
  Problem: a2-repaired.  Arena: 37 cells.  Axes: Button_colour, Door_present.  States: 148.
  Proofs use `decide` only, so `#print axioms` must come back empty.
  Declared semantics: frame persist, conflict exclusive, cascade single_frame.
  `step` below is total because the manual says `frame persist`; it is
  single-valued because the manual says `conflict exclusive`.
-/

/-- Arena cells, in row-major order:
    c0   = (1, 1)
    c1   = (1, 3)
    c2   = (1, 4)
    c3   = (1, 6)
    c4   = (1, 7)
    c5   = (2, 1)
    c6   = (2, 2)
    c7   = (2, 3)
    c8   = (2, 4)
    c9   = (2, 6)
    c10  = (2, 7)
    c11  = (3, 1)
    c12  = (3, 2)
    c13  = (3, 3)
    c14  = (3, 4)
    c15  = (3, 6)
    c16  = (3, 7)
    c17  = (4, 1)
    c18  = (4, 2)
    c19  = (4, 3)
    c20  = (4, 4)
    c21  = (4, 6)
    c22  = (4, 7)
    c23  = (5, 1)
    c24  = (5, 2)
    c25  = (5, 3)
    c26  = (5, 4)
    c27  = (5, 6)
    c28  = (5, 7)
    c29  = (6, 2)
    c30  = (6, 3)
    c31  = (6, 4)
    c32  = (6, 6)
    c33  = (6, 7)
    c34  = (7, 1)
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

/-- `Button_colour`, as observed: 7, 8 -/
inductive ButtonColour where
  | v7
  | v8
  deriving DecidableEq, Repr

/-- `Door_present`, as observed: False, True -/
inductive DoorPresent where
  | no
  | yes
  deriving DecidableEq, Repr

structure St where
  cart : Cell
  buttonColour : ButtonColour
  doorPresent : DoorPresent
  deriving DecidableEq, Repr

def s0 : St := ⟨Cell.c23, ButtonColour.v7, DoorPresent.yes⟩

/-- The manual's rules, transcribed from the executable form. -/
def step : St → Dir → St
  | ⟨Cell.c0, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c0, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c0, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c5, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c0, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c0, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c0, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c0, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c1, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c1, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c1, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c7, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c1, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c1, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c1, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c2, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c2, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c2, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c2, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c8, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c2, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c1, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c2, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c2, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c3, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c3, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c3, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c9, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c3, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c3, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c3, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c4, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c4, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c4, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c4, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c10, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c4, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c3, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c4, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c4, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c5, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c5, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c5, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c11, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c5, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c5, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c5, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c6, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c6, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c6, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c6, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c12, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c6, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c5, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c6, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c7, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c7, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c1, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c7, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c13, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c7, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c6, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c7, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c8, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c8, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c2, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c8, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c14, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c8, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c7, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c8, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c8, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c9, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c3, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c9, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c15, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c9, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c9, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c9, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c10, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c10, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c4, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c10, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c16, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c10, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c9, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c10, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c10, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c11, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c5, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c11, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c17, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c11, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c11, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c11, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c12, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c12, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c6, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c12, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c18, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c12, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c11, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c12, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c13, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c13, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c7, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c13, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c19, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c13, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c12, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c13, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c14, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c14, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c8, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c14, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c20, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c14, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c13, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c14, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c14, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c15, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c9, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c15, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c21, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c15, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c15, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c15, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c16, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c16, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c10, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c16, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c22, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c16, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c15, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c16, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c16, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c17, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c11, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c17, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c23, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c17, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c17, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c17, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c18, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c18, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c12, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c18, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c24, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c18, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c17, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c18, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c19, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c19, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c13, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c19, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c25, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c19, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c18, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c19, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c20, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c20, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c14, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c20, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c26, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c20, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c19, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c20, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c20, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c21, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c15, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c21, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c27, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c21, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c21, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c21, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c22, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c22, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c16, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c22, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c28, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c22, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c21, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c22, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c22, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c23, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c17, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c23, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c23, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c23, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c23, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c23, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c24, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c24, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c18, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c24, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c29, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c24, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c23, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c24, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c25, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c25, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c19, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c25, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c30, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c25, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c24, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c25, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c26, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c26, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c20, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c26, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c31, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c26, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c25, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c26, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c26, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c27, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c21, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c27, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c32, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c27, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c27, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c27, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c28, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c28, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c22, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c28, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c33, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c28, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c27, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c28, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c28, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c29, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c24, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c29, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c29, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c29, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c29, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c29, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c30, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c30, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c25, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c30, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c30, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c30, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c29, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c30, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c31, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c31, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c26, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c31, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c35, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c31, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c30, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c31, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c31, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c32, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c27, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c32, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c35, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c32, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c32, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c32, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c33, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c33, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c28, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c33, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c36, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c33, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c32, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c33, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c33, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c34, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c34, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c34, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c34, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c34, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c34, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c34, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c34, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c35, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c32, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c35, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c35, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c35, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c35, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c35, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c36, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c36, ButtonColour.v7, DoorPresent.no⟩, .up => ⟨Cell.c33, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c36, ButtonColour.v7, DoorPresent.no⟩, .down => ⟨Cell.c36, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c36, ButtonColour.v7, DoorPresent.no⟩, .left => ⟨Cell.c35, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c36, ButtonColour.v7, DoorPresent.no⟩, .right => ⟨Cell.c36, ButtonColour.v7, DoorPresent.no⟩
  | ⟨Cell.c0, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c0, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c0, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c5, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c0, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c0, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c0, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c0, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c1, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c1, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c1, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c7, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c1, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c1, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c1, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c2, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c2, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c2, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c2, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c8, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c2, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c1, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c2, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c2, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c3, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c3, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c3, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c9, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c3, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c3, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c3, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c4, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c4, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c4, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c4, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c10, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c4, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c3, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c4, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c4, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c5, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c5, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c5, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c11, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c5, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c5, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c5, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c6, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c6, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c6, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c6, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c12, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c6, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c5, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c6, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c7, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c7, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c1, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c7, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c13, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c7, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c6, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c7, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c8, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c8, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c2, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c8, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c14, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c8, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c7, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c8, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c8, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c9, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c3, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c9, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c15, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c9, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c9, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c9, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c10, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c10, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c4, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c10, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c16, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c10, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c9, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c10, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c10, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c11, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c5, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c11, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c17, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c11, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c11, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c11, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c12, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c12, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c6, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c12, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c18, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c12, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c11, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c12, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c13, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c13, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c7, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c13, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c19, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c13, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c12, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c13, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c14, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c14, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c8, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c14, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c20, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c14, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c13, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c14, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c14, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c15, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c9, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c15, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c21, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c15, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c15, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c15, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c16, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c16, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c10, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c16, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c22, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c16, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c15, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c16, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c16, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c17, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c11, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c17, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c23, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c17, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c17, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c17, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c18, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c18, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c12, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c18, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c24, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c18, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c17, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c18, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c19, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c19, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c13, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c19, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c25, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c19, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c18, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c19, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c20, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c20, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c14, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c20, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c26, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c20, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c19, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c20, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c20, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c21, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c15, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c21, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c27, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c21, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c21, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c21, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c22, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c22, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c16, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c22, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c28, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c22, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c21, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c22, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c22, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c23, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c17, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c23, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c23, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c23, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c23, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c23, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c24, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c24, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c18, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c24, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c29, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c24, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c23, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c24, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c25, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c25, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c19, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c25, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c30, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c25, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c24, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c25, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c26, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c26, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c20, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c26, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c26, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c26, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c25, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c26, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c26, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c27, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c21, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c27, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c32, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c27, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c27, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c27, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c28, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c28, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c22, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c28, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c33, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c28, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c27, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c28, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c28, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c29, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c24, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c29, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c29, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c29, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c29, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c29, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c30, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c30, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c25, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c30, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c30, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c30, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c29, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c30, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c30, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c31, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c26, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c31, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c35, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c31, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c30, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c31, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c31, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c32, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c27, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c32, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c35, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c32, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c32, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c32, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c33, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c33, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c28, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c33, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c36, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c33, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c32, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c33, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c33, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c34, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c34, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c34, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c34, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c34, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c34, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c34, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c34, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c35, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c32, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c35, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c35, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c35, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c35, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c35, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c36, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c36, ButtonColour.v7, DoorPresent.yes⟩, .up => ⟨Cell.c33, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c36, ButtonColour.v7, DoorPresent.yes⟩, .down => ⟨Cell.c36, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c36, ButtonColour.v7, DoorPresent.yes⟩, .left => ⟨Cell.c35, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c36, ButtonColour.v7, DoorPresent.yes⟩, .right => ⟨Cell.c36, ButtonColour.v7, DoorPresent.yes⟩
  | ⟨Cell.c0, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c0, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c0, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c5, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c0, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c0, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c0, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c0, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c1, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c1, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c1, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c7, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c1, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c1, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c1, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c2, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c2, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c2, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c2, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c8, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c2, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c1, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c2, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c2, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c3, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c3, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c3, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c9, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c3, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c3, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c3, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c4, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c4, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c4, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c4, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c10, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c4, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c3, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c4, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c4, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c5, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c5, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c5, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c11, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c5, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c5, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c5, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c6, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c6, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c6, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c6, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c12, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c6, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c5, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c6, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c7, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c7, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c1, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c7, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c13, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c7, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c6, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c7, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c8, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c8, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c2, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c8, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c14, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c8, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c7, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c8, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c8, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c9, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c3, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c9, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c15, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c9, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c9, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c9, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c10, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c10, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c4, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c10, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c16, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c10, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c9, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c10, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c10, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c11, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c5, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c11, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c17, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c11, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c11, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c11, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c12, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c12, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c6, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c12, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c18, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c12, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c11, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c12, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c13, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c13, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c7, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c13, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c19, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c13, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c12, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c13, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c14, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c14, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c8, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c14, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c20, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c14, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c13, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c14, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c14, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c15, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c9, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c15, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c21, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c15, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c15, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c15, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c16, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c16, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c10, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c16, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c22, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c16, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c15, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c16, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c16, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c17, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c11, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c17, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c23, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c17, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c17, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c17, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c18, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c18, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c12, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c18, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c24, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c18, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c17, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c18, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c19, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c19, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c13, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c19, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c25, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c19, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c18, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c19, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c20, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c20, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c14, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c20, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c26, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c20, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c19, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c20, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c20, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c21, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c15, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c21, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c27, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c21, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c21, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c21, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c22, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c22, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c16, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c22, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c28, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c22, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c21, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c22, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c22, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c23, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c17, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c23, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c23, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c23, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c23, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c23, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c24, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c24, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c18, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c24, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c29, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c24, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c23, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c24, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c25, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c25, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c19, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c25, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c30, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c25, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c24, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c25, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c26, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c26, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c20, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c26, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c31, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c26, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c25, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c26, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c26, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c27, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c21, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c27, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c32, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c27, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c27, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c27, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c28, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c28, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c22, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c28, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c33, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c28, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c27, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c28, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c28, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c29, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c24, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c29, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c29, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c29, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c29, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c29, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c30, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c30, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c25, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c30, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c30, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c30, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c29, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c30, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c31, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c31, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c26, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c31, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c35, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c31, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c30, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c31, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c31, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c32, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c27, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c32, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c35, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c32, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c32, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c32, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c33, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c33, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c28, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c33, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c36, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c33, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c32, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c33, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c33, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c34, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c34, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c34, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c34, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c34, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c34, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c34, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c34, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c35, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c32, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c35, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c35, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c35, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c35, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c35, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c36, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c36, ButtonColour.v8, DoorPresent.no⟩, .up => ⟨Cell.c33, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c36, ButtonColour.v8, DoorPresent.no⟩, .down => ⟨Cell.c36, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c36, ButtonColour.v8, DoorPresent.no⟩, .left => ⟨Cell.c35, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c36, ButtonColour.v8, DoorPresent.no⟩, .right => ⟨Cell.c36, ButtonColour.v8, DoorPresent.no⟩
  | ⟨Cell.c0, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c0, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c0, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c5, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c0, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c0, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c0, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c0, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c1, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c1, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c1, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c7, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c1, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c1, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c1, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c2, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c2, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c2, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c2, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c8, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c2, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c1, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c2, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c2, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c3, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c3, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c3, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c9, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c3, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c3, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c3, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c4, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c4, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c4, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c4, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c10, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c4, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c3, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c4, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c4, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c5, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c5, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c5, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c11, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c5, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c5, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c5, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c6, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c6, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c6, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c6, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c12, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c6, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c5, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c6, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c7, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c7, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c1, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c7, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c13, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c7, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c6, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c7, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c8, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c8, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c2, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c8, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c14, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c8, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c7, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c8, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c8, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c9, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c3, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c9, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c15, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c9, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c9, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c9, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c10, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c10, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c4, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c10, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c16, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c10, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c9, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c10, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c10, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c11, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c5, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c11, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c17, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c11, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c11, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c11, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c12, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c12, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c6, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c12, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c18, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c12, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c11, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c12, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c13, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c13, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c7, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c13, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c19, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c13, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c12, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c13, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c14, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c14, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c8, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c14, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c20, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c14, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c13, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c14, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c14, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c15, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c9, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c15, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c21, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c15, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c15, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c15, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c16, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c16, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c10, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c16, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c22, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c16, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c15, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c16, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c16, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c17, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c11, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c17, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c23, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c17, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c17, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c17, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c18, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c18, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c12, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c18, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c24, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c18, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c17, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c18, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c19, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c19, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c13, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c19, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c25, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c19, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c18, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c19, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c20, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c20, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c14, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c20, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c26, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c20, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c19, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c20, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c20, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c21, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c15, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c21, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c27, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c21, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c21, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c21, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c22, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c22, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c16, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c22, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c28, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c22, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c21, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c22, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c22, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c23, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c17, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c23, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c23, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c23, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c23, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c23, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c24, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c24, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c18, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c24, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c29, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c24, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c23, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c24, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c25, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c25, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c19, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c25, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c30, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c25, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c24, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c25, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c26, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c26, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c20, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c26, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c26, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c26, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c25, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c26, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c26, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c27, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c21, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c27, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c32, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c27, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c27, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c27, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c28, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c28, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c22, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c28, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c33, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c28, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c27, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c28, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c28, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c29, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c24, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c29, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c29, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c29, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c29, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c29, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c30, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c30, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c25, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c30, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c30, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c30, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c29, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c30, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c30, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c31, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c26, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c31, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c35, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c31, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c30, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c31, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c31, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c32, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c27, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c32, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c35, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c32, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c32, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c32, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c33, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c33, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c28, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c33, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c36, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c33, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c32, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c33, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c33, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c34, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c34, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c34, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c34, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c34, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c34, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c34, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c34, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c35, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c32, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c35, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c35, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c35, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c35, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c35, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c36, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c36, ButtonColour.v8, DoorPresent.yes⟩, .up => ⟨Cell.c33, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c36, ButtonColour.v8, DoorPresent.yes⟩, .down => ⟨Cell.c36, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c36, ButtonColour.v8, DoorPresent.yes⟩, .left => ⟨Cell.c35, ButtonColour.v8, DoorPresent.yes⟩
  | ⟨Cell.c36, ButtonColour.v8, DoorPresent.yes⟩, .right => ⟨Cell.c36, ButtonColour.v8, DoorPresent.yes⟩

def Goal (s : St) : Bool := s.cart == Cell.c10

inductive Reachable : St → Prop where
  | init : Reachable s0
  | step : ∀ (s : St) (d : Dir), Reachable s → Reachable (step s d)


/-- Pagoda weight: 0 on the room the Cart starts in, 1 outside. -/
def w : Cell → Nat
  | .c0 => 1
  | .c1 => 0
  | .c2 => 0
  | .c3 => 1
  | .c4 => 1
  | .c5 => 0
  | .c6 => 0
  | .c7 => 0
  | .c8 => 0
  | .c9 => 1
  | .c10 => 1
  | .c11 => 0
  | .c12 => 0
  | .c13 => 0
  | .c14 => 0
  | .c15 => 1
  | .c16 => 1
  | .c17 => 0
  | .c18 => 0
  | .c19 => 0
  | .c20 => 0
  | .c21 => 1
  | .c22 => 1
  | .c23 => 0
  | .c24 => 0
  | .c25 => 0
  | .c26 => 0
  | .c27 => 1
  | .c28 => 1
  | .c29 => 0
  | .c30 => 0
  | .c31 => 0
  | .c32 => 1
  | .c33 => 1
  | .c34 => 1
  | .c35 => 1
  | .c36 => 1

-- STALE ON PURPOSE.  This is the exhibit's certificate — w = 0 only on the
-- 21 cells of the left room — regenerated against the REPAIRED step.  It is
-- kept as a red artefact: `inv_closed` is now false, because teleport_down
-- carries the Cart from a w = 0 cell to a w = 1 cell in one move.  A manual
-- that dropped its refuted theorem silently would leave no trace of this.
def I (s : St) : Bool := w s.cart == 0

theorem inv_init : I s0 = true := by decide

theorem inv_closed (s : St) (d : Dir) : I s = true → I (step s d) = true := by
  obtain ⟨c, buttonColour, doorPresent⟩ := s
  cases c <;> cases buttonColour <;> cases doorPresent <;> cases d <;> decide

theorem inv_all (s : St) (h : Reachable s) : I s = true := by
  induction h with
  | init => decide
  | step s d _ ih => exact inv_closed s d ih

theorem goal_break (s : St) : Goal s = true → I s = false := by
  obtain ⟨c, buttonColour, doorPresent⟩ := s
  cases c <;> cases buttonColour <;> cases doorPresent <;> decide

theorem unsolvable : ¬ ∃ s : St, Reachable s ∧ Goal s = true := by
  rintro ⟨s, hr, hg⟩
  have hi : I s = true := inv_all s hr
  have hb : I s = false := goal_break s hg
  rw [hi] at hb
  exact absurd hb (by decide)

#print axioms unsolvable
