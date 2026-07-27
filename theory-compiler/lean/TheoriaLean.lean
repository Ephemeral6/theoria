/-
  Auto-generated Lean 4 proof: 1D Peg Solitaire unsolvability
  Board: 5 positions, pegs at [0, 1, 3, 4]
  Reachable states: 5 (computed by BFS)
  No state with exactly 1 peg(s) is reachable.
  Strategy: enumerate reachable set, prove closure, check no goal member.
-/

structure PegState where
  s0 : Bool
  s1 : Bool
  s2 : Bool
  s3 : Bool
  s4 : Bool
  deriving DecidableEq, Repr

inductive Pos where
  | p0
  | p1
  | p2
  | p3
  | p4
  deriving DecidableEq, Repr

def initState : PegState := ⟨true, true, false, true, true⟩

def pegCount (s : PegState) : Nat :=
  (if s.s0 then 1 else 0) + (if s.s1 then 1 else 0) + (if s.s2 then 1 else 0) + (if s.s3 then 1 else 0) + (if s.s4 then 1 else 0)

def isGoalB (s : PegState) : Bool := pegCount s == 1

def PegState.get (s : PegState) : Pos → Bool
  | .p0 => s.s0
  | .p1 => s.s1
  | .p2 => s.s2
  | .p3 => s.s3
  | .p4 => s.s4

def PegState.set (s : PegState) (p : Pos) (v : Bool) : PegState :=
  match p with
  | .p0 => { s with s0 := v }
  | .p1 => { s with s1 := v }
  | .p2 => { s with s2 := v }
  | .p3 => { s with s3 := v }
  | .p4 => { s with s4 := v }

def applyJump (s : PegState) (a b c : Pos) : PegState :=
  ((s.set a false).set b false).set c true

def isValidGeom (a b c : Pos) : Bool :=
  match a, b, c with
  | .p0, .p1, .p2 => true
  | .p2, .p1, .p0 => true
  | .p1, .p2, .p3 => true
  | .p3, .p2, .p1 => true
  | .p2, .p3, .p4 => true
  | .p4, .p3, .p2 => true
  | _, _, _ => false

inductive Step : PegState → PegState → Prop where
  | jump (s : PegState) (a b c : Pos)
    (hg : isValidGeom a b c = true)
    (ha : s.get a = true) (hb : s.get b = true) (hc : s.get c = false) :
    Step s (applyJump s a b c)

inductive Reachable : PegState → PegState → Prop where
  | refl : ∀ s, Reachable s s
  | step : ∀ s t u, Step s t → Reachable t u → Reachable s u

def allReachable : List PegState := [
  ⟨true, true, true, false, false⟩,
  ⟨true, false, false, true, false⟩,
  ⟨false, true, false, false, true⟩,
  ⟨true, true, false, true, true⟩,
  ⟨false, false, true, true, true⟩
]

def allPos : List Pos := [.p0, .p1, .p2, .p3, .p4]

def checkNoGoal : Bool := allReachable.all (fun s => !isGoalB s)
def checkInitMember : Bool := allReachable.contains initState
def checkClosed : Bool :=
  allReachable.all fun s =>
    allPos.all fun a => allPos.all fun b => allPos.all fun c =>
      !(isValidGeom a b c && s.get a && s.get b && !s.get c) ||
      allReachable.contains (applyJump s a b c)

theorem checkNoGoal_true : checkNoGoal = true := by native_decide
theorem checkInitMember_true : checkInitMember = true := by native_decide
theorem checkClosed_true : checkClosed = true := by native_decide

theorem init_in_reachable : initState ∈ allReachable := by decide

theorem no_goal_in_reachable (s : PegState) (h : s ∈ allReachable) :
    isGoalB s = false := by
  cases h with
  | head => native_decide
  | tail _ h1 =>
    cases h1 with
    | head => native_decide
    | tail _ h2 =>
      cases h2 with
      | head => native_decide
      | tail _ h3 =>
        cases h3 with
        | head => native_decide
        | tail _ h4 =>
          cases h4 with
          | head => native_decide
          | tail _ hlast => exact absurd hlast (List.not_mem_nil _)

theorem closed_under_jump (s : PegState) (a b c : Pos)
    (hs : s ∈ allReachable)
    (hg : isValidGeom a b c = true)
    (ha : s.get a = true) (hb : s.get b = true) (hc : s.get c = false) :
    applyJump s a b c ∈ allReachable := by
  cases hs with
  | head =>
    cases a <;> cases b <;> cases c <;> simp [isValidGeom] at hg <;>
      simp_all [PegState.get, applyJump, PegState.set, allReachable] <;> decide
  | tail _ h1 =>
    cases h1 with
    | head =>
      cases a <;> cases b <;> cases c <;> simp [isValidGeom] at hg <;>
      simp_all [PegState.get, applyJump, PegState.set, allReachable] <;> decide
    | tail _ h2 =>
      cases h2 with
      | head =>
        cases a <;> cases b <;> cases c <;> simp [isValidGeom] at hg <;>
      simp_all [PegState.get, applyJump, PegState.set, allReachable] <;> decide
      | tail _ h3 =>
        cases h3 with
        | head =>
          cases a <;> cases b <;> cases c <;> simp [isValidGeom] at hg <;>
      simp_all [PegState.get, applyJump, PegState.set, allReachable] <;> decide
        | tail _ h4 =>
          cases h4 with
          | head =>
            cases a <;> cases b <;> cases c <;> simp [isValidGeom] at hg <;>
      simp_all [PegState.get, applyJump, PegState.set, allReachable] <;> decide
          | tail _ hlast => exact absurd hlast (List.not_mem_nil _)

theorem reachable_subset (s t : PegState) (hs : s ∈ allReachable)
    (hr : Reachable s t) : t ∈ allReachable := by
  induction hr with
  | refl _ => exact hs
  | step s₁ t₁ u₁ hstep _ ih =>
    apply ih
    cases hstep with
    | jump a b c hg ha hb hc =>
      exact closed_under_jump s₁ a b c hs hg ha hb hc

theorem unsolvable : ¬ ∃ t : PegState, Reachable initState t ∧ isGoalB t = true := by
  intro ⟨t, hreach, hgoal⟩
  have hmem : t ∈ allReachable := reachable_subset _ _ init_in_reachable hreach
  have hno : isGoalB t = false := no_goal_in_reachable t hmem
  rw [hno] at hgoal
  exact absurd hgoal (by decide)

#print axioms unsolvable
