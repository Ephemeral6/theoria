/- Auto-generated from theory.dsl. Canonical skeleton of Theoria 1.10a:
     inv_init / inv_closed / goal_break  =>  unsolvable
   Core Lean 4 only -- no Mathlib. -/

inductive Dir where
  | up | down | left | right
  deriving DecidableEq, Repr

structure S where
  pr : Int
  pc : Int
  br : Int
  bc : Int
  deriving DecidableEq, Repr

def drow : Dir → Int
  | .up => -1 | .down => 1 | .left => 0 | .right => 0

def dcol : Dir → Int
  | .up => 0 | .down => 0 | .left => -1 | .right => 1

-- problem data (the level; domain/problem split)
def H : Int := 7
def W : Int := 7

def isWall (r c : Int) : Bool :=
  (r == 1 && c == 5) || (r == 4 && c == 4) || (r == 5 && c == 5)

def onBoard (r c : Int) : Bool := 0 <= r && r < H && 0 <= c && c < W

def freeCell (s : S) (r c : Int) : Bool :=
  onBoard r c && !isWall r c && !(r == s.br && c == s.bc)

/- step, compiled from the rules of theory.dsl:
     walk   : free(ahead(Player,dir))                      -> player moves 1
     push2  : Box.pos = ahead(Player,dir), free(ahead(Box)), free(beyond(Box))
                                                            -> box moves 2, player 1
     stayed : otherwise                                     -> nothing -/
-- written without `let`: the bindings would block `split` in inv_closed
def step (s : S) (d : Dir) : S :=
  if freeCell s (s.pr + drow d) (s.pc + dcol d) then
    { s with pr := s.pr + drow d, pc := s.pc + dcol d }
  else if ((s.pr + drow d == s.br) && (s.pc + dcol d == s.bc)) &&
          freeCell s (s.br + drow d) (s.bc + dcol d) &&
          freeCell s (s.br + 2 * drow d) (s.bc + 2 * dcol d) then
    { pr := s.br, pc := s.bc,
      br := s.br + 2 * drow d, bc := s.bc + 2 * dcol d }
  else
    s

/- The invariant, in the manual's own vocabulary:
   the box never changes checkerboard colour. -/
def I (s : S) : Prop := (s.br + s.bc) % 2 = 0

instance (s : S) : Decidable (I s) := by unfold I; infer_instance

def s0 : S := { pr := 3, pc := 5, br := 3, bc := 3 }

-- the unsolvable level's target
def Goal (s : S) : Prop := s.br = 3 ∧ s.bc = 2

theorem inv_init : I s0 := by decide

theorem drow_dcol_cases (d : Dir) :
    (drow d = -1 ∧ dcol d = 0) ∨ (drow d = 1 ∧ dcol d = 0) ∨
    (drow d = 0 ∧ dcol d = -1) ∨ (drow d = 0 ∧ dcol d = 1) := by
  cases d <;> simp [drow, dcol]

theorem inv_closed (s : S) (d : Dir) (h : I s) : I (step s d) := by
  unfold I step
  split
  · exact h                       -- walk: the box does not move
  · split
    · -- push: the box moves two cells along one axis, so the sum shifts by ±2
      simp only
      rcases drow_dcol_cases d with ⟨hr, hc⟩ | ⟨hr, hc⟩ | ⟨hr, hc⟩ | ⟨hr, hc⟩ <;>
        rw [hr, hc] <;> unfold I at h <;> omega
    · exact h                     -- stayed: the box does not move

theorem goal_break (s : S) (hg : Goal s) : ¬ I s := by
  unfold Goal at hg
  unfold I
  obtain ⟨h1, h2⟩ := hg
  rw [h1, h2]
  decide

inductive Reachable : S → Prop where
  | init : Reachable s0
  | step : ∀ s d, Reachable s → Reachable (step s d)

/- The whole point: no search, three lemmas. -/
theorem unsolvable : ∀ s, Reachable s → ¬ Goal s := by
  intro s hr
  have hi : I s := by
    induction hr with
    | init => exact inv_init
    | step s d _ ih => exact inv_closed s d ih
  intro hg
  exact goal_break s hg hi
