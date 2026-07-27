/-
  Auto-generated from theory.dsl — DO NOT EDIT.

  Claim: no state in {00010} is reachable from 11011.

  The invariant is the manual's `pagoda_potential`, and its weights are NOT the
  author's. They come from
      engine-rig/interop/certificates/pagoda_5_11011_to_00010.json
  produced by engine-rig/engines/lp_potential, and were re-checked here
  against the complete move set before this file was written.

  w = [-1, 1, 0, 1, -1]   potential(s) = sum of w[i] over occupied i

  The 6 move geometries below were recovered from the generated
  predictor, not re-derived, and agree with the certificate's.
      jump(0,1,2)  delta = +0
      jump(1,2,3)  delta = +0
      jump(2,1,0)  delta = -2
      jump(2,3,4)  delta = -2
      jump(3,2,1)  delta = +0
      jump(4,3,2)  delta = +0

  Proof: computational. Every obligation is closed by `decide`, so
  the kernel checks it and `#print axioms` comes back empty. Cost:
  the state split is 2^5.
-/

inductive Pos where
  | p0
  | p1
  | p2
  | p3
  | p4
  deriving DecidableEq, Repr

/-- One `Bool` per cell: `true` is occupied. -/
structure St where
  p0 : Bool
  p1 : Bool
  p2 : Bool
  p3 : Bool
  p4 : Bool
  deriving DecidableEq, Repr

def St.get (s : St) : Pos → Bool
  | .p0 => s.p0
  | .p1 => s.p1
  | .p2 => s.p2
  | .p3 => s.p3
  | .p4 => s.p4

def St.set (s : St) : Pos → Bool → St
  | .p0, v => { s with p0 := v }
  | .p1, v => { s with p1 := v }
  | .p2, v => { s with p2 := v }
  | .p3, v => { s with p3 := v }
  | .p4, v => { s with p4 := v }

/-- One constructor per move geometry: 6 of them, where the reachable
    set the enumerative route would need is exponential. -/
inductive Move where
  | m0
  | m1
  | m2
  | m3
  | m4
  | m5
  deriving DecidableEq, Repr

def Move.src : Move → Pos
  | .m0 => .p0
  | .m1 => .p1
  | .m2 => .p2
  | .m3 => .p2
  | .m4 => .p3
  | .m5 => .p4

def Move.over : Move → Pos
  | .m0 => .p1
  | .m1 => .p2
  | .m2 => .p1
  | .m3 => .p3
  | .m4 => .p2
  | .m5 => .p3

def Move.dst : Move → Pos
  | .m0 => .p2
  | .m1 => .p3
  | .m2 => .p0
  | .m3 => .p4
  | .m4 => .p1
  | .m5 => .p2

def legal (s : St) (m : Move) : Bool :=
  s.get m.src && s.get m.over && !s.get m.dst

def applyMove (s : St) (m : Move) : St :=
  ((s.set m.src false).set m.over false).set m.dst true

/-- Pagoda weights, from the LP certificate. -/
def w : Pos → Int
  | .p0 => -1
  | .p1 => 1
  | .p2 => 0
  | .p3 => 1
  | .p4 => -1

def potential (s : St) : Int :=
  (if s.p0 then w .p0 else 0)
  + (if s.p1 then w .p1 else 0)
  + (if s.p2 then w .p2 else 0)
  + (if s.p3 then w .p3 else 0)
  + (if s.p4 then w .p4 else 0)

def s0 : St := ⟨true, true, false, true, true⟩

inductive Reachable : St → Prop where
  | init : Reachable s0
  | step : ∀ s m, Reachable s → legal s m = true → Reachable (applyMove s m)

def Inv (s : St) : Bool := decide (potential s ≤ 0)

def Goal (s : St) : Bool := s == ⟨false, false, false, true, false⟩

theorem inv_init : Inv s0 = true := by decide

/-- Splitting on `Move` first is not cosmetic: `Move` has no
    decidable-∀ instance, so `decide` cannot quantify over it, while
    it can quantify over `Bool`. -/
theorem inv_closed : ∀ (m : Move) (p0 p1 p2 p3 p4 : Bool),
    legal (St.mk p0 p1 p2 p3 p4) m = true → Inv (St.mk p0 p1 p2 p3 p4) = true →
    Inv (applyMove (St.mk p0 p1 p2 p3 p4) m) = true := by
  intro m; cases m <;> decide

theorem inv_all (s : St) (h : Reachable s) : Inv s = true := by
  induction h with
  | init => decide
  | step s m _ hl ih =>
      match s with
      | St.mk p0 p1 p2 p3 p4 => exact inv_closed m p0 p1 p2 p3 p4 hl ih

theorem goal_break : ∀ (p0 p1 p2 p3 p4 : Bool),
    Goal (St.mk p0 p1 p2 p3 p4) = true → Inv (St.mk p0 p1 p2 p3 p4) = false := by decide

theorem unsolvable : ¬ ∃ s : St, Reachable s ∧ Goal s = true := by
  rintro ⟨s, hr, hg⟩
  match s with
  | St.mk p0 p1 p2 p3 p4 =>
    have h1 := inv_all _ hr
    have h2 := goal_break p0 p1 p2 p3 p4 hg
    rw [h1] at h2
    exact Bool.noConfusion h2

#print axioms inv_init
#print axioms inv_closed
#print axioms inv_all
#print axioms unsolvable
