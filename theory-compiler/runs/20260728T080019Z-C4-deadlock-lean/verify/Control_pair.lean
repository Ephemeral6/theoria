/-
  Auto-generated from a grounded STRIPS task — DO NOT EDIT.

  A **conditional** unsolvability theorem for sokoban / sokoban-open4far:

      at(b1,c22) AND at(b2,c23)  AND  not-goal  =>  dead

  Conditional is the operative word. Nothing below is a claim about
  the level's start state; `dead` quantifies over every well-formed
  state the pattern accepts, reachable or not.

  The pattern — and *only* the pattern — comes from
      control
  produced by control. Its two obligations were
  recomputed here before emission over the whole well-formed state
  space; the producer's own mutex bookkeeping was read for
  cross-checking and believed for nothing.

  Everything else is read off the grounded task: 16 cell(s), 112
  ground action(s), the problem's own goal.

  `wf` — no two things share a cell — is carried as a hypothesis
  rather than assumed away. It is the content of the producer's h²
  fixpoint, and it is load-bearing: closure genuinely fails on
  states that put the player inside a box. Every reachable state is
  well-formed, checked by exhaustion on the Python side.

  Proof mode `computational`: the split is over the 1 slot(s) the
  pattern leaves free (of 3) and then over moves — 1792 leaf goals,
  every one closed by `decide`. Axiom set **empty**. No `sorry`,
  no `native_decide`.
-/

inductive Cell where
  | c11
  | c12
  | c13
  | c14
  | c21
  | c22
  | c23
  | c24
  | c31
  | c32
  | c33
  | c34
  | c41
  | c42
  | c43
  | c44
  deriving DecidableEq, Repr

/-- One cell per moving thing. `clear` is a reading of this tuple,
    not an independent atom, which is what makes "a cell holds at
    most one thing" true by construction rather than by lemma. -/
structure St where
  player : Cell
  b1 : Cell
  b2 : Cell
  deriving DecidableEq, Repr

/-- `clear c` of the STRIPS task. -/
def St.clear (s : St) (c : Cell) : Bool :=
  s.player != c && s.b1 != c && s.b2 != c

/-- Well-formed: no two things in one cell. -/
def wf (s : St) : Bool :=
  s.player != s.b1 && s.player != s.b2 && s.b1 != s.b2

/-- The 112 ground actions of the task, one constructor each. -/
inductive Move where
  | move_c11_c12_right
  | move_c11_c21_down
  | move_c12_c11_left
  | move_c12_c13_right
  | move_c12_c22_down
  | move_c13_c12_left
  | move_c13_c14_right
  | move_c13_c23_down
  | move_c14_c13_left
  | move_c14_c24_down
  | move_c21_c11_up
  | move_c21_c22_right
  | move_c21_c31_down
  | move_c22_c12_up
  | move_c22_c21_left
  | move_c22_c23_right
  | move_c22_c32_down
  | move_c23_c13_up
  | move_c23_c22_left
  | move_c23_c24_right
  | move_c23_c33_down
  | move_c24_c14_up
  | move_c24_c23_left
  | move_c24_c34_down
  | move_c31_c21_up
  | move_c31_c32_right
  | move_c31_c41_down
  | move_c32_c22_up
  | move_c32_c31_left
  | move_c32_c33_right
  | move_c32_c42_down
  | move_c33_c23_up
  | move_c33_c32_left
  | move_c33_c34_right
  | move_c33_c43_down
  | move_c34_c24_up
  | move_c34_c33_left
  | move_c34_c44_down
  | move_c41_c31_up
  | move_c41_c42_right
  | move_c42_c32_up
  | move_c42_c41_left
  | move_c42_c43_right
  | move_c43_c33_up
  | move_c43_c42_left
  | move_c43_c44_right
  | move_c44_c34_up
  | move_c44_c43_left
  | push_c11_c12_c13_b1_right
  | push_c11_c12_c13_b2_right
  | push_c11_c21_c31_b1_down
  | push_c11_c21_c31_b2_down
  | push_c12_c13_c14_b1_right
  | push_c12_c13_c14_b2_right
  | push_c12_c22_c32_b1_down
  | push_c12_c22_c32_b2_down
  | push_c13_c12_c11_b1_left
  | push_c13_c12_c11_b2_left
  | push_c13_c23_c33_b1_down
  | push_c13_c23_c33_b2_down
  | push_c14_c13_c12_b1_left
  | push_c14_c13_c12_b2_left
  | push_c14_c24_c34_b1_down
  | push_c14_c24_c34_b2_down
  | push_c21_c22_c23_b1_right
  | push_c21_c22_c23_b2_right
  | push_c21_c31_c41_b1_down
  | push_c21_c31_c41_b2_down
  | push_c22_c23_c24_b1_right
  | push_c22_c23_c24_b2_right
  | push_c22_c32_c42_b1_down
  | push_c22_c32_c42_b2_down
  | push_c23_c22_c21_b1_left
  | push_c23_c22_c21_b2_left
  | push_c23_c33_c43_b1_down
  | push_c23_c33_c43_b2_down
  | push_c24_c23_c22_b1_left
  | push_c24_c23_c22_b2_left
  | push_c24_c34_c44_b1_down
  | push_c24_c34_c44_b2_down
  | push_c31_c21_c11_b1_up
  | push_c31_c21_c11_b2_up
  | push_c31_c32_c33_b1_right
  | push_c31_c32_c33_b2_right
  | push_c32_c22_c12_b1_up
  | push_c32_c22_c12_b2_up
  | push_c32_c33_c34_b1_right
  | push_c32_c33_c34_b2_right
  | push_c33_c23_c13_b1_up
  | push_c33_c23_c13_b2_up
  | push_c33_c32_c31_b1_left
  | push_c33_c32_c31_b2_left
  | push_c34_c24_c14_b1_up
  | push_c34_c24_c14_b2_up
  | push_c34_c33_c32_b1_left
  | push_c34_c33_c32_b2_left
  | push_c41_c31_c21_b1_up
  | push_c41_c31_c21_b2_up
  | push_c41_c42_c43_b1_right
  | push_c41_c42_c43_b2_right
  | push_c42_c32_c22_b1_up
  | push_c42_c32_c22_b2_up
  | push_c42_c43_c44_b1_right
  | push_c42_c43_c44_b2_right
  | push_c43_c33_c23_b1_up
  | push_c43_c33_c23_b2_up
  | push_c43_c42_c41_b1_left
  | push_c43_c42_c41_b2_left
  | push_c44_c34_c24_b1_up
  | push_c44_c34_c24_b2_up
  | push_c44_c43_c42_b1_left
  | push_c44_c43_c42_b2_left
  deriving DecidableEq, Repr

def legal (s : St) (m : Move) : Bool :=
  match m with
  | .move_c11_c12_right => s.player == .c11 && s.clear .c12
  | .move_c11_c21_down => s.player == .c11 && s.clear .c21
  | .move_c12_c11_left => s.player == .c12 && s.clear .c11
  | .move_c12_c13_right => s.player == .c12 && s.clear .c13
  | .move_c12_c22_down => s.player == .c12 && s.clear .c22
  | .move_c13_c12_left => s.player == .c13 && s.clear .c12
  | .move_c13_c14_right => s.player == .c13 && s.clear .c14
  | .move_c13_c23_down => s.player == .c13 && s.clear .c23
  | .move_c14_c13_left => s.player == .c14 && s.clear .c13
  | .move_c14_c24_down => s.player == .c14 && s.clear .c24
  | .move_c21_c11_up => s.player == .c21 && s.clear .c11
  | .move_c21_c22_right => s.player == .c21 && s.clear .c22
  | .move_c21_c31_down => s.player == .c21 && s.clear .c31
  | .move_c22_c12_up => s.player == .c22 && s.clear .c12
  | .move_c22_c21_left => s.player == .c22 && s.clear .c21
  | .move_c22_c23_right => s.player == .c22 && s.clear .c23
  | .move_c22_c32_down => s.player == .c22 && s.clear .c32
  | .move_c23_c13_up => s.player == .c23 && s.clear .c13
  | .move_c23_c22_left => s.player == .c23 && s.clear .c22
  | .move_c23_c24_right => s.player == .c23 && s.clear .c24
  | .move_c23_c33_down => s.player == .c23 && s.clear .c33
  | .move_c24_c14_up => s.player == .c24 && s.clear .c14
  | .move_c24_c23_left => s.player == .c24 && s.clear .c23
  | .move_c24_c34_down => s.player == .c24 && s.clear .c34
  | .move_c31_c21_up => s.player == .c31 && s.clear .c21
  | .move_c31_c32_right => s.player == .c31 && s.clear .c32
  | .move_c31_c41_down => s.player == .c31 && s.clear .c41
  | .move_c32_c22_up => s.player == .c32 && s.clear .c22
  | .move_c32_c31_left => s.player == .c32 && s.clear .c31
  | .move_c32_c33_right => s.player == .c32 && s.clear .c33
  | .move_c32_c42_down => s.player == .c32 && s.clear .c42
  | .move_c33_c23_up => s.player == .c33 && s.clear .c23
  | .move_c33_c32_left => s.player == .c33 && s.clear .c32
  | .move_c33_c34_right => s.player == .c33 && s.clear .c34
  | .move_c33_c43_down => s.player == .c33 && s.clear .c43
  | .move_c34_c24_up => s.player == .c34 && s.clear .c24
  | .move_c34_c33_left => s.player == .c34 && s.clear .c33
  | .move_c34_c44_down => s.player == .c34 && s.clear .c44
  | .move_c41_c31_up => s.player == .c41 && s.clear .c31
  | .move_c41_c42_right => s.player == .c41 && s.clear .c42
  | .move_c42_c32_up => s.player == .c42 && s.clear .c32
  | .move_c42_c41_left => s.player == .c42 && s.clear .c41
  | .move_c42_c43_right => s.player == .c42 && s.clear .c43
  | .move_c43_c33_up => s.player == .c43 && s.clear .c33
  | .move_c43_c42_left => s.player == .c43 && s.clear .c42
  | .move_c43_c44_right => s.player == .c43 && s.clear .c44
  | .move_c44_c34_up => s.player == .c44 && s.clear .c34
  | .move_c44_c43_left => s.player == .c44 && s.clear .c43
  | .push_c11_c12_c13_b1_right => s.player == .c11 && s.b1 == .c12 && s.clear .c13
  | .push_c11_c12_c13_b2_right => s.player == .c11 && s.b2 == .c12 && s.clear .c13
  | .push_c11_c21_c31_b1_down => s.player == .c11 && s.b1 == .c21 && s.clear .c31
  | .push_c11_c21_c31_b2_down => s.player == .c11 && s.b2 == .c21 && s.clear .c31
  | .push_c12_c13_c14_b1_right => s.player == .c12 && s.b1 == .c13 && s.clear .c14
  | .push_c12_c13_c14_b2_right => s.player == .c12 && s.b2 == .c13 && s.clear .c14
  | .push_c12_c22_c32_b1_down => s.player == .c12 && s.b1 == .c22 && s.clear .c32
  | .push_c12_c22_c32_b2_down => s.player == .c12 && s.b2 == .c22 && s.clear .c32
  | .push_c13_c12_c11_b1_left => s.player == .c13 && s.b1 == .c12 && s.clear .c11
  | .push_c13_c12_c11_b2_left => s.player == .c13 && s.b2 == .c12 && s.clear .c11
  | .push_c13_c23_c33_b1_down => s.player == .c13 && s.b1 == .c23 && s.clear .c33
  | .push_c13_c23_c33_b2_down => s.player == .c13 && s.b2 == .c23 && s.clear .c33
  | .push_c14_c13_c12_b1_left => s.player == .c14 && s.b1 == .c13 && s.clear .c12
  | .push_c14_c13_c12_b2_left => s.player == .c14 && s.b2 == .c13 && s.clear .c12
  | .push_c14_c24_c34_b1_down => s.player == .c14 && s.b1 == .c24 && s.clear .c34
  | .push_c14_c24_c34_b2_down => s.player == .c14 && s.b2 == .c24 && s.clear .c34
  | .push_c21_c22_c23_b1_right => s.player == .c21 && s.b1 == .c22 && s.clear .c23
  | .push_c21_c22_c23_b2_right => s.player == .c21 && s.b2 == .c22 && s.clear .c23
  | .push_c21_c31_c41_b1_down => s.player == .c21 && s.b1 == .c31 && s.clear .c41
  | .push_c21_c31_c41_b2_down => s.player == .c21 && s.b2 == .c31 && s.clear .c41
  | .push_c22_c23_c24_b1_right => s.player == .c22 && s.b1 == .c23 && s.clear .c24
  | .push_c22_c23_c24_b2_right => s.player == .c22 && s.b2 == .c23 && s.clear .c24
  | .push_c22_c32_c42_b1_down => s.player == .c22 && s.b1 == .c32 && s.clear .c42
  | .push_c22_c32_c42_b2_down => s.player == .c22 && s.b2 == .c32 && s.clear .c42
  | .push_c23_c22_c21_b1_left => s.player == .c23 && s.b1 == .c22 && s.clear .c21
  | .push_c23_c22_c21_b2_left => s.player == .c23 && s.b2 == .c22 && s.clear .c21
  | .push_c23_c33_c43_b1_down => s.player == .c23 && s.b1 == .c33 && s.clear .c43
  | .push_c23_c33_c43_b2_down => s.player == .c23 && s.b2 == .c33 && s.clear .c43
  | .push_c24_c23_c22_b1_left => s.player == .c24 && s.b1 == .c23 && s.clear .c22
  | .push_c24_c23_c22_b2_left => s.player == .c24 && s.b2 == .c23 && s.clear .c22
  | .push_c24_c34_c44_b1_down => s.player == .c24 && s.b1 == .c34 && s.clear .c44
  | .push_c24_c34_c44_b2_down => s.player == .c24 && s.b2 == .c34 && s.clear .c44
  | .push_c31_c21_c11_b1_up => s.player == .c31 && s.b1 == .c21 && s.clear .c11
  | .push_c31_c21_c11_b2_up => s.player == .c31 && s.b2 == .c21 && s.clear .c11
  | .push_c31_c32_c33_b1_right => s.player == .c31 && s.b1 == .c32 && s.clear .c33
  | .push_c31_c32_c33_b2_right => s.player == .c31 && s.b2 == .c32 && s.clear .c33
  | .push_c32_c22_c12_b1_up => s.player == .c32 && s.b1 == .c22 && s.clear .c12
  | .push_c32_c22_c12_b2_up => s.player == .c32 && s.b2 == .c22 && s.clear .c12
  | .push_c32_c33_c34_b1_right => s.player == .c32 && s.b1 == .c33 && s.clear .c34
  | .push_c32_c33_c34_b2_right => s.player == .c32 && s.b2 == .c33 && s.clear .c34
  | .push_c33_c23_c13_b1_up => s.player == .c33 && s.b1 == .c23 && s.clear .c13
  | .push_c33_c23_c13_b2_up => s.player == .c33 && s.b2 == .c23 && s.clear .c13
  | .push_c33_c32_c31_b1_left => s.player == .c33 && s.b1 == .c32 && s.clear .c31
  | .push_c33_c32_c31_b2_left => s.player == .c33 && s.b2 == .c32 && s.clear .c31
  | .push_c34_c24_c14_b1_up => s.player == .c34 && s.b1 == .c24 && s.clear .c14
  | .push_c34_c24_c14_b2_up => s.player == .c34 && s.b2 == .c24 && s.clear .c14
  | .push_c34_c33_c32_b1_left => s.player == .c34 && s.b1 == .c33 && s.clear .c32
  | .push_c34_c33_c32_b2_left => s.player == .c34 && s.b2 == .c33 && s.clear .c32
  | .push_c41_c31_c21_b1_up => s.player == .c41 && s.b1 == .c31 && s.clear .c21
  | .push_c41_c31_c21_b2_up => s.player == .c41 && s.b2 == .c31 && s.clear .c21
  | .push_c41_c42_c43_b1_right => s.player == .c41 && s.b1 == .c42 && s.clear .c43
  | .push_c41_c42_c43_b2_right => s.player == .c41 && s.b2 == .c42 && s.clear .c43
  | .push_c42_c32_c22_b1_up => s.player == .c42 && s.b1 == .c32 && s.clear .c22
  | .push_c42_c32_c22_b2_up => s.player == .c42 && s.b2 == .c32 && s.clear .c22
  | .push_c42_c43_c44_b1_right => s.player == .c42 && s.b1 == .c43 && s.clear .c44
  | .push_c42_c43_c44_b2_right => s.player == .c42 && s.b2 == .c43 && s.clear .c44
  | .push_c43_c33_c23_b1_up => s.player == .c43 && s.b1 == .c33 && s.clear .c23
  | .push_c43_c33_c23_b2_up => s.player == .c43 && s.b2 == .c33 && s.clear .c23
  | .push_c43_c42_c41_b1_left => s.player == .c43 && s.b1 == .c42 && s.clear .c41
  | .push_c43_c42_c41_b2_left => s.player == .c43 && s.b2 == .c42 && s.clear .c41
  | .push_c44_c34_c24_b1_up => s.player == .c44 && s.b1 == .c34 && s.clear .c24
  | .push_c44_c34_c24_b2_up => s.player == .c44 && s.b2 == .c34 && s.clear .c24
  | .push_c44_c43_c42_b1_left => s.player == .c44 && s.b1 == .c43 && s.clear .c42
  | .push_c44_c43_c42_b2_left => s.player == .c44 && s.b2 == .c43 && s.clear .c42

def applyMove (s : St) (m : Move) : St :=
  match m with
  | .move_c11_c12_right => { s with player := .c12 }
  | .move_c11_c21_down => { s with player := .c21 }
  | .move_c12_c11_left => { s with player := .c11 }
  | .move_c12_c13_right => { s with player := .c13 }
  | .move_c12_c22_down => { s with player := .c22 }
  | .move_c13_c12_left => { s with player := .c12 }
  | .move_c13_c14_right => { s with player := .c14 }
  | .move_c13_c23_down => { s with player := .c23 }
  | .move_c14_c13_left => { s with player := .c13 }
  | .move_c14_c24_down => { s with player := .c24 }
  | .move_c21_c11_up => { s with player := .c11 }
  | .move_c21_c22_right => { s with player := .c22 }
  | .move_c21_c31_down => { s with player := .c31 }
  | .move_c22_c12_up => { s with player := .c12 }
  | .move_c22_c21_left => { s with player := .c21 }
  | .move_c22_c23_right => { s with player := .c23 }
  | .move_c22_c32_down => { s with player := .c32 }
  | .move_c23_c13_up => { s with player := .c13 }
  | .move_c23_c22_left => { s with player := .c22 }
  | .move_c23_c24_right => { s with player := .c24 }
  | .move_c23_c33_down => { s with player := .c33 }
  | .move_c24_c14_up => { s with player := .c14 }
  | .move_c24_c23_left => { s with player := .c23 }
  | .move_c24_c34_down => { s with player := .c34 }
  | .move_c31_c21_up => { s with player := .c21 }
  | .move_c31_c32_right => { s with player := .c32 }
  | .move_c31_c41_down => { s with player := .c41 }
  | .move_c32_c22_up => { s with player := .c22 }
  | .move_c32_c31_left => { s with player := .c31 }
  | .move_c32_c33_right => { s with player := .c33 }
  | .move_c32_c42_down => { s with player := .c42 }
  | .move_c33_c23_up => { s with player := .c23 }
  | .move_c33_c32_left => { s with player := .c32 }
  | .move_c33_c34_right => { s with player := .c34 }
  | .move_c33_c43_down => { s with player := .c43 }
  | .move_c34_c24_up => { s with player := .c24 }
  | .move_c34_c33_left => { s with player := .c33 }
  | .move_c34_c44_down => { s with player := .c44 }
  | .move_c41_c31_up => { s with player := .c31 }
  | .move_c41_c42_right => { s with player := .c42 }
  | .move_c42_c32_up => { s with player := .c32 }
  | .move_c42_c41_left => { s with player := .c41 }
  | .move_c42_c43_right => { s with player := .c43 }
  | .move_c43_c33_up => { s with player := .c33 }
  | .move_c43_c42_left => { s with player := .c42 }
  | .move_c43_c44_right => { s with player := .c44 }
  | .move_c44_c34_up => { s with player := .c34 }
  | .move_c44_c43_left => { s with player := .c43 }
  | .push_c11_c12_c13_b1_right => { s with player := .c12, b1 := .c13 }
  | .push_c11_c12_c13_b2_right => { s with player := .c12, b2 := .c13 }
  | .push_c11_c21_c31_b1_down => { s with player := .c21, b1 := .c31 }
  | .push_c11_c21_c31_b2_down => { s with player := .c21, b2 := .c31 }
  | .push_c12_c13_c14_b1_right => { s with player := .c13, b1 := .c14 }
  | .push_c12_c13_c14_b2_right => { s with player := .c13, b2 := .c14 }
  | .push_c12_c22_c32_b1_down => { s with player := .c22, b1 := .c32 }
  | .push_c12_c22_c32_b2_down => { s with player := .c22, b2 := .c32 }
  | .push_c13_c12_c11_b1_left => { s with player := .c12, b1 := .c11 }
  | .push_c13_c12_c11_b2_left => { s with player := .c12, b2 := .c11 }
  | .push_c13_c23_c33_b1_down => { s with player := .c23, b1 := .c33 }
  | .push_c13_c23_c33_b2_down => { s with player := .c23, b2 := .c33 }
  | .push_c14_c13_c12_b1_left => { s with player := .c13, b1 := .c12 }
  | .push_c14_c13_c12_b2_left => { s with player := .c13, b2 := .c12 }
  | .push_c14_c24_c34_b1_down => { s with player := .c24, b1 := .c34 }
  | .push_c14_c24_c34_b2_down => { s with player := .c24, b2 := .c34 }
  | .push_c21_c22_c23_b1_right => { s with player := .c22, b1 := .c23 }
  | .push_c21_c22_c23_b2_right => { s with player := .c22, b2 := .c23 }
  | .push_c21_c31_c41_b1_down => { s with player := .c31, b1 := .c41 }
  | .push_c21_c31_c41_b2_down => { s with player := .c31, b2 := .c41 }
  | .push_c22_c23_c24_b1_right => { s with player := .c23, b1 := .c24 }
  | .push_c22_c23_c24_b2_right => { s with player := .c23, b2 := .c24 }
  | .push_c22_c32_c42_b1_down => { s with player := .c32, b1 := .c42 }
  | .push_c22_c32_c42_b2_down => { s with player := .c32, b2 := .c42 }
  | .push_c23_c22_c21_b1_left => { s with player := .c22, b1 := .c21 }
  | .push_c23_c22_c21_b2_left => { s with player := .c22, b2 := .c21 }
  | .push_c23_c33_c43_b1_down => { s with player := .c33, b1 := .c43 }
  | .push_c23_c33_c43_b2_down => { s with player := .c33, b2 := .c43 }
  | .push_c24_c23_c22_b1_left => { s with player := .c23, b1 := .c22 }
  | .push_c24_c23_c22_b2_left => { s with player := .c23, b2 := .c22 }
  | .push_c24_c34_c44_b1_down => { s with player := .c34, b1 := .c44 }
  | .push_c24_c34_c44_b2_down => { s with player := .c34, b2 := .c44 }
  | .push_c31_c21_c11_b1_up => { s with player := .c21, b1 := .c11 }
  | .push_c31_c21_c11_b2_up => { s with player := .c21, b2 := .c11 }
  | .push_c31_c32_c33_b1_right => { s with player := .c32, b1 := .c33 }
  | .push_c31_c32_c33_b2_right => { s with player := .c32, b2 := .c33 }
  | .push_c32_c22_c12_b1_up => { s with player := .c22, b1 := .c12 }
  | .push_c32_c22_c12_b2_up => { s with player := .c22, b2 := .c12 }
  | .push_c32_c33_c34_b1_right => { s with player := .c33, b1 := .c34 }
  | .push_c32_c33_c34_b2_right => { s with player := .c33, b2 := .c34 }
  | .push_c33_c23_c13_b1_up => { s with player := .c23, b1 := .c13 }
  | .push_c33_c23_c13_b2_up => { s with player := .c23, b2 := .c13 }
  | .push_c33_c32_c31_b1_left => { s with player := .c32, b1 := .c31 }
  | .push_c33_c32_c31_b2_left => { s with player := .c32, b2 := .c31 }
  | .push_c34_c24_c14_b1_up => { s with player := .c24, b1 := .c14 }
  | .push_c34_c24_c14_b2_up => { s with player := .c24, b2 := .c14 }
  | .push_c34_c33_c32_b1_left => { s with player := .c33, b1 := .c32 }
  | .push_c34_c33_c32_b2_left => { s with player := .c33, b2 := .c32 }
  | .push_c41_c31_c21_b1_up => { s with player := .c31, b1 := .c21 }
  | .push_c41_c31_c21_b2_up => { s with player := .c31, b2 := .c21 }
  | .push_c41_c42_c43_b1_right => { s with player := .c42, b1 := .c43 }
  | .push_c41_c42_c43_b2_right => { s with player := .c42, b2 := .c43 }
  | .push_c42_c32_c22_b1_up => { s with player := .c32, b1 := .c22 }
  | .push_c42_c32_c22_b2_up => { s with player := .c32, b2 := .c22 }
  | .push_c42_c43_c44_b1_right => { s with player := .c43, b1 := .c44 }
  | .push_c42_c43_c44_b2_right => { s with player := .c43, b2 := .c44 }
  | .push_c43_c33_c23_b1_up => { s with player := .c33, b1 := .c23 }
  | .push_c43_c33_c23_b2_up => { s with player := .c33, b2 := .c23 }
  | .push_c43_c42_c41_b1_left => { s with player := .c42, b1 := .c41 }
  | .push_c43_c42_c41_b2_left => { s with player := .c42, b2 := .c41 }
  | .push_c44_c34_c24_b1_up => { s with player := .c34, b1 := .c24 }
  | .push_c44_c34_c24_b2_up => { s with player := .c34, b2 := .c24 }
  | .push_c44_c43_c42_b1_left => { s with player := .c43, b1 := .c42 }
  | .push_c44_c43_c42_b2_left => { s with player := .c43, b2 := .c42 }

def s0 : St := ⟨.c44, .c22, .c33⟩

/-- The problem's goal. -/
def Goal (s : St) : Bool :=
  s.b1 == .c42 && s.b2 == .c13

/-- The certificate's pattern: at(b1,c22) AND at(b2,c23) -/
def Pat (s : St) : Bool :=
  s.b1 == .c22 && s.b2 == .c23

/-- One step of the task, from an arbitrary state rather than from `s0`. -/
inductive ReachFrom (r : St) : St → Prop where
  | refl : ReachFrom r r
  | step : ∀ s m, ReachFrom r s → legal s m = true → ReachFrom r (applyMove s m)

/-- The pattern pins 2 of 3 slot(s), so a state satisfying it is
    determined by the rest. This is what keeps the split below small. -/
theorem pat_pins : ∀ (b1 b2 : Cell), Pat ⟨.c11, b1, b2⟩ = true → b1 = .c22 ∧ b2 = .c23 := by
  intro b1 b2
  cases b1 <;> cases b2 <;> decide

/-- Closure, on the states the pattern leaves open. -/
theorem closed_pinned : ∀ (player : Cell) (m : Move),
    wf ⟨player, .c22, .c23⟩ = true → legal ⟨player, .c22, .c23⟩ m = true →
    wf (applyMove ⟨player, .c22, .c23⟩ m) = true ∧ Pat (applyMove ⟨player, .c22, .c23⟩ m) = true := by
  intro player m
  cases player <;> cases m <;> decide

/-- The same, with the pinning discharged. -/
theorem dead_closed : ∀ (s : St) (m : Move), wf s = true → Pat s = true →
    legal s m = true →
    wf (applyMove s m) = true ∧ Pat (applyMove s m) = true := by
  intro s m hw hp hl
  cases s with
  | mk player b1 b2 =>
    obtain ⟨h1, h2⟩ := pat_pins b1 b2 hp
    subst h1
    subst h2
    exact closed_pinned player m hw hl

/-- The pattern excludes the goal, on the slots the two of them read. -/
theorem no_goal_pinned : ∀ (b1 b2 : Cell), Pat ⟨.c11, b1, b2⟩ = true → Goal ⟨.c11, b1, b2⟩ = false := by
  intro b1 b2
  cases b1 <;> cases b2 <;> decide

/-- The pattern excludes the goal. -/
theorem pat_no_goal : ∀ (s : St), Pat s = true → Goal s = false := by
  intro s
  cases s with
  | mk player b1 b2 => exact no_goal_pinned b1 b2

theorem dead_persists : ∀ (r s : St), wf r = true → Pat r = true →
    ReachFrom r s → wf s = true ∧ Pat s = true := by
  intro r s hw hp h
  induction h with
  | refl => exact ⟨hw, hp⟩
  | step t m _ hl ih => exact dead_closed t m ih.1 ih.2 hl

/-- The theorem. From **any** well-formed state containing the pattern,
    nothing reachable is a goal. -/
theorem dead : ∀ (r s : St), wf r = true → Pat r = true → ReachFrom r s →
    Goal s = false := by
  intro r s hw hp h
  exact pat_no_goal s (dead_persists r s hw hp h).2

#print axioms pat_pins
#print axioms closed_pinned
#print axioms dead_closed
#print axioms no_goal_pinned
#print axioms pat_no_goal
#print axioms dead_persists
#print axioms dead
