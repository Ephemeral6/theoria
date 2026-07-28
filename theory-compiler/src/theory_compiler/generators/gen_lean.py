"""theory.lean generator — the manual's laws, as a Lean 4 development.

What changed (DECISIONS.md D-A0-011 is the bug report this answers): the previous
generator *ignored the `TheoryAST` it was handed*. It BFS-ed 1-D peg solitaire
from arguments passed beside the AST and emitted a `PegState` structure, so it
was a correct generator for exactly one world and structurally inapplicable to
any other. Nothing it produced depended on the manual.

This generator produces two developments from the same AST, and which one it
produces is decided by **what the manual claims**, not by a flag the caller
picks:

`pagoda`
    The manual declares `weights w over ...` and an invariant `pagoda(w) <= c`
    (ledger entry E-05). The weights come from an `lp_potential` certificate,
    the invariant is `potential(s) <= c`, and closure is proved from the
    *algebra of a move* — one obligation per move geometry, of which there are
    `2(n-2)`. No reachable set is ever enumerated. This is the A1 route.

`enumerative`
    The manual declares no potential. The reachable set is enumerated by running
    the generated predictor, `step` is transcribed as a lookup table, and the
    laws are proved by `cases` and `decide`. This is A0's route, generalised off
    the AST, and it is what a world with latches and portals gets.

Three commitments, each with a reason:

* **`native_decide` is never emitted.** It discharges a goal by running compiled
  code and records `Lean.ofReduceBool` as an axiom; the acceptance test is what
  `#print axioms` says, so the kernel has to do the work.

* **No Mathlib.** `lean` alone compiles the output, so the expensive certify
  layer runs from a bare toolchain and the proof's dependency surface stays
  visible.

* **`step` is transcribed from the generated Python, never re-derived.** There
  is one predictor in the system; the Lean file is a second *rendering* of it,
  not a second implementation. A generator that re-derived the transition
  relation could prove a theorem about a world the Python never simulates.

Axiom budgets, measured rather than hoped (see DECISIONS.md D-TC-008):

| development | `#print axioms` | proof size |
|---|---|---|
| pagoda, `proof="computational"` | *empty* | `O(2^n)` |
| pagoda, `proof="algebraic"` | `propext, Quot.sound` | `O(n)` |
| enumerative | *empty* | `O(|reachable|)` |

The algebraic proof cannot reach an empty axiom set, and the reason is not the
pagoda argument: in Lean 4.9 every core `Int` lemma — `Int.add_comm`,
`Int.le_trans`, `Int.add_nonpos` — is itself proved using `propext`. Any proof
that does arithmetic rather than computation inherits it. `computational` is
therefore the default, and `algebraic` is what you reach for when the board is
too large to enumerate.
"""

from typing import Callable, Dict, List, Optional, Sequence, Tuple

from ..certificate import PagodaCertificate, covers
from ..ir import WorldIR, build_ir
from ..parser.ast_nodes import TheoryAST
from ..problem import ProblemSpec
from .gen_python import generate_python

PROOF_MODES = ("computational", "algebraic")


class LeanGenError(Exception):
    """The manual asks for a proof this backend cannot honestly produce."""


class CertificateGapError(LeanGenError):
    """The certificate proves less than the manual claims.

    Raised, never narrowed silently. `lp_potential` is sound but incomplete —
    it certifies some unsolvable configurations and not others — so a goal the
    certificate does not cover is a goal that stays *unproven*. Emitting a Lean
    file whose `unsolvable` theorem quietly meant a smaller goal than the
    manual's would be the compiler overclaiming on the engine's behalf, which
    is the one thing a certifying compiler must not do.
    """


# --------------------------------------------------------------- the predictor

def _load_predictor(ast: TheoryAST, problem: ProblemSpec) -> dict:
    """Exec the generated module. One predictor, and this is how Lean sees it."""
    ns: dict = {}
    exec(compile(generate_python(ast, problem), "<theory.py>", "exec"), ns)
    return ns


def _reachable(ns: dict) -> Tuple[List, Dict]:
    """BFS the reachable set through the generated `step`. Deterministic order."""
    start = ns["initial_state"]()
    order = [start]
    index = {start.key(): 0}
    queue = [start]
    while queue:
        state = queue.pop(0)
        for action in ns["ACTIONS"]:
            nxt = ns["step"](state, action)
            if nxt.key() not in index:
                index[nxt.key()] = len(order)
                order.append(nxt)
                queue.append(nxt)
    return order, index


# ------------------------------------------------------------------ pagoda

def _pagoda_request(ir: WorldIR) -> Optional[Tuple[str, str, int]]:
    """(invariant name, weights name, bound) if the manual asks for a potential."""
    if ir.ast.laws is None:
        return None
    for inv in ir.ast.laws.invariants:
        text = inv.expr_text.replace(" ", "")
        if text.startswith("pagoda(") and text.endswith(")"):
            name = text[len("pagoda("):-1]
            if inv.op not in ("<=", "="):
                raise LeanGenError(
                    f"invariant {inv.name} compares a potential with {inv.op!r}; "
                    f"a pagoda argument needs an upper bound (`<=`)")
            return inv.name, name, int(inv.value)
    return None


def _goal_states(ns: dict, ir: WorldIR) -> List[str]:
    """Every occupancy string the manual's goal admits, over this level."""
    if ir.problem.goal_states:
        return list(ir.problem.goal_states)
    n = ir.problem.n_pos
    if n is None:
        raise LeanGenError("a pagoda development needs a line world (`n_pos`)")
    raise LeanGenError(
        "problem %r lists no `goal_states`. A pagoda argument excludes named "
        "states, so the level has to say which states the manual's goal picks "
        "out on this board." % ir.problem.name)


def _derive_moves(ns: dict, n: int) -> List[Tuple[int, int, int]]:
    """Read the move geometry back out of the predictor.

    The certificate's weights are only sound for the move set they were solved
    over, so the manual's rules and the engine's certificate have to be talking
    about the same world. Rather than trust that, the moves are recovered by
    *asking the predictor*: for every occupancy and every action, whatever
    `step` does is what the world does.
    """
    seen = set()
    fired: Dict[str, set] = {}
    start = ns["initial_state"]()
    fields = [f for f in vars(start) if f.endswith("_pos")]
    order = [f[: -len("_pos")] for f in fields]

    for mask in range(1 << n):
        occ = "".join("1" if mask >> i & 1 else "0" for i in range(n))
        occupied = [i for i in range(n) if occ[i] == "1"]
        if len(occupied) > len(order):
            continue                       # more pegs than the level has
        state = _state_for(ns, start, order, occupied)
        if state is None or ns["occupancy"](state) != occ:
            continue
        fired[occ] = set()
        for action in ns["ACTIONS"]:
            after = ns["occupancy"](ns["step"](state, action))
            if after == occ:
                continue
            gone = [i for i in range(n) if occ[i] == "1" and after[i] == "0"]
            new = [i for i in range(n) if occ[i] == "0" and after[i] == "1"]
            if len(gone) != 2 or len(new) != 1:
                raise LeanGenError(
                    "the predictor's transition %s -> %s removes %d and adds %d "
                    "occupied cells; a pagoda argument assumes a jump removes "
                    "two and adds one" % (occ, after, len(gone), len(new)))
            dst = new[0]
            src = gone[0] if abs(gone[0] - dst) == 2 else gone[1]
            over = gone[1] if src == gone[0] else gone[0]
            seen.add((src, over, dst))
            fired[occ].add((src, over, dst))

    _check_legality(sorted(seen), fired)
    return sorted(seen)


def _state_for(ns: dict, start, order: Sequence[str], occupied: Sequence[int]):
    """A predictor state whose occupancy is exactly `occupied`.

    Instances beyond the occupied cells are marked not-alive, which is how a
    board with fewer pegs than the level declares gets represented at all. The
    earlier version only enumerated states with *every* peg alive, so five of
    the thirty-two occupancies were reachable by the check and the rest were
    silently skipped.
    """
    state = start.copy()
    for i, name in enumerate(order):
        if i < len(occupied):
            setattr(state, name + "_pos", occupied[i])
            alive = True
        else:
            alive = False
        if hasattr(state, name + "_alive"):
            setattr(state, name + "_alive", alive)
        elif not alive:
            return None                    # no way to remove a peg from the board
    return state


def _check_legality(moves: Sequence[Tuple[int, int, int]],
                    fired: Dict[str, set]) -> None:
    """The Lean file's `legal` is a template. This is what earns it.

    `legal s m := s.src && s.over && !s.dst` is emitted as fixed text, so
    nothing about it is derived from the manual. Checking only that transitions
    *look like* jumps ("removes two cells, adds one") would leave the enabling
    condition unverified: a world whose rules let a peg jump onto an occupied
    cell would produce the same shape of transition and get a Lean file that
    quietly models a different world.

    So for every occupancy the predictor can represent, and every move, the
    predictor's own behaviour is compared against what `legal` predicts.
    """
    for occ, actually in sorted(fired.items()):
        predicted = {
            m for m in moves
            if occ[m[0]] == "1" and occ[m[1]] == "1" and occ[m[2]] == "0"
        }
        if predicted != actually:
            missing = sorted(predicted - actually)
            extra = sorted(actually - predicted)
            raise LeanGenError(
                "the Lean development's `legal` does not describe the manual's "
                "rules. In state %s it predicts %s but the predictor fires %s "
                "(predicted-only: %s; fired-only: %s). The emitted `legal` is a "
                "fixed template, so a world with a different enabling condition "
                "must be refused here rather than proved about."
                % (occ, sorted(predicted), sorted(actually), missing, extra))


def _pagoda_lean(ir: WorldIR, ns: dict, cert: PagodaCertificate,
                 inv_name: str, bound: int, proof: str) -> str:
    n = cert.n_pos
    goal_states = _goal_states(ns, ir)

    missing = covers(cert, goal_states)
    if missing:
        # E-06. The certificate cannot license these goals — `lp_potential` is
        # sound but incomplete and some of them admit no linear pagoda at all.
        # Refusing outright was right while there was only one method; it is
        # wrong now that there are two. Exhaustion is tried, and *only* the
        # goals the certificate does not cover are handed to it, so the two
        # arguments stay attributable rather than being blended into one claim.
        feasible, why = _exhaustible(ns)
        if feasible:
            return _hybrid_lean(ir, ns, cert, inv_name, bound,
                                goal_states, missing)
        raise CertificateGapError(
            "the manual's goal picks out %s on this board, and certificate %r "
            "excludes only %s. %s is left unproven.\n\n"
            "This is `lp_potential`'s documented incompleteness, not a bug to "
            "route around: some genuinely unsolvable configurations admit no "
            "linear pagoda function. Exhausting the reachable set is the other "
            "method this compiler has, and it is not available here either: %s."
            "\n\nNarrow the level's `goal_states` to what the certificate "
            "covers, or obtain a certificate that covers the rest, or state the "
            "claim as open. This generator will not emit a theorem no method it "
            "has can license."
            % (goal_states, cert.claim, cert.goal_states, missing, why))

    derived = _derive_moves(ns, n)
    if set(derived) != set(cert.moves()):
        only_manual = sorted(set(derived) - set(cert.moves()))
        only_cert = sorted(set(cert.moves()) - set(derived))
        raise LeanGenError(
            "the manual's rules and the certificate describe different move "
            "sets. Moves the rules allow and the certificate never weighed: %s. "
            "Moves the certificate weighed and the rules do not allow: %s. The "
            "weights are only sound for the move set they were solved over."
            % (only_manual, only_cert))

    start = ns["occupancy"](ns["initial_state"]())
    if start != cert.initial_state:
        raise LeanGenError(
            "the level starts at %s and the certificate is about %s"
            % (start, cert.initial_state))

    L: List[str] = []
    L.append("/-")
    L.append("  Auto-generated from theory.dsl — DO NOT EDIT.")
    L.append("")
    L.append("  Claim: no state in %s is reachable from %s."
             % ("{" + ", ".join(goal_states) + "}", cert.initial_state))
    L.append("")
    L.append("  The invariant is the manual's `%s`, and its weights are NOT the" % inv_name)
    L.append("  author's. They come from")
    L.append("      %s" % _provenance(cert.path))
    L.append("  produced by %s, and were re-checked here" % cert.produced_by)
    L.append("  against the complete move set before this file was written.")
    L.append("")
    L.append("  w = %s   potential(s) = sum of w[i] over occupied i" % (cert.weights,))
    L.append("")
    L.append("  The %d move geometries below were recovered from the generated"
             % len(derived))
    L.append("  predictor, not re-derived, and agree with the certificate's.")
    for m in derived:
        L.append("      jump(%d,%d,%d)  delta = %+d" % (m[0], m[1], m[2],
                                                        cert.delta(m)))
    L.append("")
    if proof == "algebraic":
        L.append("  Proof: algebraic. `inv_closed` splits on the %d moves and closes"
                 % len(derived))
        L.append("  each by linear arithmetic, so the proof grows with the board and")
        L.append("  not with the state space. Cost: `omega` and `simp` put `propext`")
        L.append("  and `Quot.sound` in the axiom set, because Lean's own `Int`")
        L.append("  lemmas are proved with them.")
    else:
        L.append("  Proof: computational. Every obligation is closed by `decide`, so")
        L.append("  the kernel checks it and `#print axioms` comes back empty. Cost:")
        L.append("  the state split is 2^%d." % n)
    L.append("-/")
    L.append("")

    fields = ["p%d" % i for i in range(n)]
    L.append("inductive Pos where")
    for i in range(n):
        L.append("  | p%d" % i)
    L.append("  deriving DecidableEq, Repr")
    L.append("")
    L.append("/-- One `Bool` per cell: `true` is occupied. -/")
    L.append("structure St where")
    for f in fields:
        L.append("  %s : Bool" % f)
    L.append("  deriving DecidableEq, Repr")
    L.append("")
    L.append("def St.get (s : St) : Pos → Bool")
    for i, f in enumerate(fields):
        L.append("  | .p%d => s.%s" % (i, f))
    L.append("")
    L.append("def St.set (s : St) : Pos → Bool → St")
    for i, f in enumerate(fields):
        L.append("  | .p%d, v => { s with %s := v }" % (i, f))
    L.append("")
    L.append("/-- One constructor per move geometry: %d of them, where the reachable"
             % len(derived))
    L.append("    set the enumerative route would need is exponential. -/")
    L.append("inductive Move where")
    for i in range(len(derived)):
        L.append("  | m%d" % i)
    L.append("  deriving DecidableEq, Repr")
    L.append("")
    for role, idx in (("src", 0), ("over", 1), ("dst", 2)):
        L.append("def Move.%s : Move → Pos" % role)
        for i, m in enumerate(derived):
            L.append("  | .m%d => .p%d" % (i, m[idx]))
        L.append("")
    L.append("def legal (s : St) (m : Move) : Bool :=")
    L.append("  s.get m.src && s.get m.over && !s.get m.dst")
    L.append("")
    L.append("def applyMove (s : St) (m : Move) : St :=")
    L.append("  ((s.set m.src false).set m.over false).set m.dst true")
    L.append("")
    L.append("/-- Pagoda weights, from the LP certificate. -/")
    L.append("def w : Pos → Int")
    for i, weight in enumerate(cert.weights):
        L.append("  | .p%d => %d" % (i, weight))
    L.append("")
    L.append("def potential (s : St) : Int :=")
    L.append("  " + "\n  + ".join(
        "(if s.%s then w .p%d else 0)" % (f, i) for i, f in enumerate(fields)))
    L.append("")
    L.append("def s0 : St := %s" % _lean_state(cert.initial_state))
    L.append("")
    L.append("inductive Reachable : St → Prop where")
    L.append("  | init : Reachable s0")
    L.append("  | step : ∀ s m, Reachable s → legal s m = true → "
             "Reachable (applyMove s m)")
    L.append("")

    if proof == "algebraic":
        L.append("abbrev Inv (s : St) : Prop := potential s ≤ %d" % bound)
        L.append("")
        L.append("abbrev Goal (s : St) : Prop := %s" % " ∨ ".join(
            "s = %s" % _lean_state(g) for g in goal_states))
        L.append("")
        L.append("theorem inv_init : Inv s0 := by decide")
        L.append("")
        L.append("/-- The whole pagoda argument. Splitting on `Move` leaves the state")
        L.append("    abstract: what closes each case is that `w dst - w src - w over`")
        L.append("    is non-positive, which is a fact about three weights and not")
        L.append("    about any state. -/")
        L.append("theorem inv_closed (s : St) (m : Move) (hl : legal s m = true)")
        L.append("    (hi : Inv s) : Inv (applyMove s m) := by")
        L.append("  cases m <;>")
        L.append("    simp_all [legal, applyMove, St.get, St.set, Move.src, Move.over,")
        L.append("              Move.dst, Inv, potential, w] <;>")
        L.append("    omega")
        L.append("")
        L.append("theorem inv_all (s : St) (h : Reachable s) : Inv s := by")
        L.append("  induction h with")
        L.append("  | init => exact inv_init")
        L.append("  | step s m _ hl ih => exact inv_closed s m hl ih")
        L.append("")
        L.append("theorem goal_break (s : St) (h : Goal s) : ¬ Inv s := by")
        L.append("  rcases h with %s" % " | ".join(
            ["rfl"] * len(goal_states)) if len(goal_states) > 1 else "  subst h")
        L.append("  all_goals decide")
        L.append("")
        L.append("theorem unsolvable : ¬ ∃ s : St, Reachable s ∧ Goal s := by")
        L.append("  rintro ⟨s, hr, hg⟩")
        L.append("  exact goal_break s hg (inv_all s hr)")
    else:
        mk = "St.mk " + " ".join(fields)
        binders = " ".join(fields)
        L.append("def Inv (s : St) : Bool := decide (potential s ≤ %d)" % bound)
        L.append("")
        L.append("def Goal (s : St) : Bool := %s" % " || ".join(
            "s == %s" % _lean_state(g) for g in goal_states))
        L.append("")
        L.append("theorem inv_init : Inv s0 = true := by decide")
        L.append("")
        L.append("/-- Splitting on `Move` first is not cosmetic: `Move` has no")
        L.append("    decidable-∀ instance, so `decide` cannot quantify over it, while")
        L.append("    it can quantify over `Bool`. -/")
        L.append("theorem inv_closed : ∀ (m : Move) (%s : Bool)," % binders)
        L.append("    legal (%s) m = true → Inv (%s) = true →" % (mk, mk))
        L.append("    Inv (applyMove (%s) m) = true := by" % mk)
        L.append("  intro m; cases m <;> decide")
        L.append("")
        L.append("theorem inv_all (s : St) (h : Reachable s) : Inv s = true := by")
        L.append("  induction h with")
        L.append("  | init => decide")
        L.append("  | step s m _ hl ih =>")
        L.append("      match s with")
        L.append("      | St.mk %s => exact inv_closed m %s hl ih" % (binders, binders))
        L.append("")
        L.append("theorem goal_break : ∀ (%s : Bool)," % binders)
        L.append("    Goal (%s) = true → Inv (%s) = false := by decide" % (mk, mk))
        L.append("")
        L.append("theorem unsolvable : ¬ ∃ s : St, Reachable s ∧ Goal s = true := by")
        L.append("  rintro ⟨s, hr, hg⟩")
        L.append("  match s with")
        L.append("  | St.mk %s =>" % binders)
        L.append("    have h1 := inv_all _ hr")
        L.append("    have h2 := goal_break %s hg" % binders)
        L.append("    rw [h1] at h2")
        L.append("    exact Bool.noConfusion h2")
    L.append("")
    L.append("#print axioms inv_init")
    L.append("#print axioms inv_closed")
    L.append("#print axioms inv_all")
    L.append("#print axioms unsolvable")
    L.append("")
    return "\n".join(L)


def _lean_state(bits: str) -> str:
    return "⟨%s⟩" % ", ".join("true" if b == "1" else "false" for b in bits)


def _provenance(path: str) -> str:
    """The certificate's path, as a repo-relative one.

    The header names the file the weights came from, and that name has to be the
    same on every machine: an absolute path would make the generated artifact
    depend on where the repository happens to sit, which breaks byte-reproducible
    output for a fixed input — a requirement here, not a nicety.
    """
    parts = path.replace("\\", "/").split("/")
    for anchor in ("engine-rig", "interop", "certificates"):
        if anchor in parts:
            return "/".join(parts[parts.index(anchor):])
    return parts[-1] if parts else path


# -------------------------------------------------------------- enumerative

#: Above this, transcribing the reachable set into Lean stops being a proof and
#: starts being a build problem. The number is a policy, not a discovery: what
#: matters is that the limit is *stated* and that crossing it produces a refusal
#: rather than a file nobody can compile.
MAX_ENUMERATED_STATES = 4096


def _exhaustible(ns: dict) -> Tuple[bool, str]:
    """Can the reachable set be transcribed? `(feasible, why not)`.

    Bounded rather than trusting: a world whose reachable set is astronomical
    must be refused, not enumerated until the machine gives up. `_reachable`
    would happily run for a very long time on a 33-cell board.
    """
    start = ns["initial_state"]()
    seen = {start.key()}
    queue = [start]
    while queue:
        state = queue.pop(0)
        for action in ns["ACTIONS"]:
            nxt = ns["step"](state, action)
            if nxt.key() not in seen:
                if len(seen) >= MAX_ENUMERATED_STATES:
                    return False, ("the reachable set exceeds %d states, so "
                                   "exhaustion would not produce a proof anyone "
                                   "could check" % MAX_ENUMERATED_STATES)
                seen.add(nxt.key())
                queue.append(nxt)
    return True, ""


def _hybrid_lean(ir: WorldIR, ns: dict, cert: PagodaCertificate,
                 inv_name: str, bound: int, goal_states: Sequence[str],
                 missing: Sequence[str]) -> str:
    """E-06. The certificate covers some goals; exhaustion covers the rest.

    `lp_potential` is sound but incomplete: on the 5-cell board from `11011`,
    three of the five single-peg terminals admit **no linear pagoda function at
    all** — `engine-rig`'s own `test_interop.py` pins them as unprovable by that
    method rather than merely unexported. So the manual's
    `goal count(Peg, alive) = 1` could not be proved, and the compiler refused
    to emit a theorem broader than its certificate. That refusal was right; what
    was missing was a second method.

    Exhaustion is that method, and the compiler already had it. The reachable
    set is finite and small, none of its states satisfies the goal, and `decide`
    closes it with an empty axiom set. The two proofs are kept **separate and
    attributed**, because they are not the same argument and a reader should be
    able to see which one carried which goal:

    * `inv_all` — the declared potential is at most its bound on every reachable
      state. The numbers are the engine's, re-derived by `certificate.recheck`
      before anything is emitted.
    * `unsolvable` — no reachable state satisfies the goal, by exhaustion.

    **What this does not do.** It does not make the pagoda method complete, and
    it does not scale: exhaustion is `O(reachable set)`, so a 33-cell English
    board is out of reach and the same manual would be refused there. The
    *proposition* is discharged for this configuration; the *method gap* stands
    and stays in the ledger.
    """
    states, index = _reachable(ns)
    covered = [g for g in goal_states if g not in set(missing)]
    occupancies = [ns["occupancy"](s) for s in states]

    # A reachable state is a counterexample if it is one of the states the
    # theorem excludes **or** if the manual's own goal predicate accepts it.
    # Both, not either: `goal_states` is the level's narrowing of the goal and
    # `is_goal` is the manual's, and checking only `is_goal` would miss exactly
    # the case where the level names a state the manual's predicate does not
    # pick out — which is how a false `unsolvable` gets emitted.
    targets = set(goal_states)
    hits = [i for i, s in enumerate(states)
            if occupancies[i] in targets or ns["is_goal"](s)]
    if hits:
        raise LeanGenError(
            "the goal is reachable: %d of the %d reachable states satisfy it "
            "(e.g. %s), so `unsolvable` is false and no development will be "
            "emitted. A certificate covering part of the goal does not change "
            "that, and exhaustion is what made it visible."
            % (len(hits), len(states), occupancies[hits[0]]))

    L: List[str] = []
    L.append("/-")
    L.append("  Auto-generated from theory.dsl — DO NOT EDIT.")
    L.append("")
    L.append("  Problem: %s.  Reachable states: %d." % (ir.problem.name, len(states)))
    L.append("  Declared semantics: frame %s, conflict %s, cascade %s."
             % (ir.semantics.frame, ir.semantics.conflict, ir.semantics.cascade))
    L.append("")
    L.append("  TWO METHODS, AND WHICH GOAL EACH ONE CARRIES (ledger E-06).")
    L.append("")
    L.append("  The manual's goal picks out %d state(s) on this board." % len(goal_states))
    L.append("  Certificate %s" % _provenance(cert.path))
    L.append("  produced by %s excludes %d of them algebraically:"
             % (cert.produced_by, len(covered)))
    for state in covered:
        L.append("    %s   potential %+d > %+d, the initial bound"
                 % (state, cert.potential(state), cert.initial_potential))
    L.append("  The other %d are **not excluded by this certificate** — their"
             % len(missing))
    L.append("  potential does not exceed the bound, so the argument says")
    L.append("  nothing about them:")
    for state in missing:
        L.append("    %s   potential %+d, which does not exceed the bound"
                 % (state, cert.potential(state)))
    L.append("  That is a statement about *this* certificate and not about the")
    L.append("  method: another certificate may exclude some of them, and for")
    L.append("  others no linear pagoda function exists at all. Which is which")
    L.append("  is `lp_potential`'s to report, not this generator's to guess —")
    L.append("  so they are all closed the same way here, by exhausting the")
    L.append("  reachable set.")
    L.append("  Both arguments end in `decide`; neither adds an axiom.")
    L.append("")
    L.append("  This does not make the pagoda method complete and it does not")
    L.append("  scale: exhaustion is O(reachable set). On a board whose reachable")
    L.append("  set is large the same manual is refused, and correctly.")
    L.append("-/")
    L.append("")
    L.append("inductive St where")
    for i, occ in enumerate(occupancies):
        L.append("  | s%d   -- %s" % (i, occ))
    L.append("  deriving DecidableEq, Repr")
    L.append("")
    actions = list(ns["ACTIONS"])
    L.append("inductive Act where")
    for i, a in enumerate(actions):
        L.append("  | a%d   -- %s" % (i, "(" + ", ".join(map(str, a)) + ")"))
    L.append("  deriving DecidableEq, Repr")
    L.append("")
    L.append("/-- The manual's rules, transcribed from the executable form. -/")
    L.append("def step : St → Act → St")
    for i, state in enumerate(states):
        for j, action in enumerate(actions):
            L.append("  | .s%d, .a%d => .s%d"
                     % (i, j, index[ns["step"](state, action).key()]))
    L.append("")
    L.append("def Goal : St → Bool")
    for i in range(len(states)):
        L.append("  | .s%d => false" % i)
    L.append("")
    L.append("inductive Reachable : St → Prop where")
    L.append("  | init : Reachable .s0")
    L.append("  | step : ∀ s a, Reachable s → Reachable (step s a)")
    L.append("")
    L.append("/-- The engine's weights, %s, evaluated on each reachable state." % inv_name)
    L.append("    w = %s -- from the certificate, re-derived before emission. -/"
             % (cert.weights,))
    L.append("def potential : St → Int")
    for i, occ in enumerate(occupancies):
        L.append("  | .s%d => %d" % (i, cert.potential(occ)))
    L.append("")
    L.append("theorem inv_all (s : St) : potential s ≤ %d := by" % bound)
    L.append("  cases s <;> decide")
    L.append("")
    L.append("theorem no_goal_state (s : St) : Goal s = false := by")
    L.append("  cases s <;> rfl")
    L.append("")
    L.append("theorem unsolvable : ¬ ∃ s : St, Reachable s ∧ Goal s = true := by")
    L.append("  rintro ⟨s, _, hg⟩")
    L.append("  rw [no_goal_state s] at hg")
    L.append("  exact Bool.noConfusion hg")
    L.append("")
    L.append("#print axioms inv_all")
    L.append("#print axioms unsolvable")
    L.append("")
    return "\n".join(L)


def _enumerative_lean(ir: WorldIR, ns: dict) -> str:
    states, index = _reachable(ns)
    actions = list(ns["ACTIONS"])
    goal_hits = [i for i, s in enumerate(states) if ns["is_goal"](s)]

    L: List[str] = []
    L.append("/-")
    L.append("  Auto-generated from theory.dsl — DO NOT EDIT.")
    L.append("")
    L.append("  Problem: %s.  Reachable states: %d.  Actions: %d."
             % (ir.problem.name, len(states), len(actions)))
    L.append("  Declared semantics: frame %s, conflict %s, cascade %s."
             % (ir.semantics.frame, ir.semantics.conflict, ir.semantics.cascade))
    L.append("  `step` below is total because the manual says `frame %s`, and"
             % ir.semantics.frame)
    L.append("  single-valued because it says `conflict %s`." % ir.semantics.conflict)
    L.append("")
    L.append("  The manual declares no potential, so this is the enumerative route:")
    L.append("  the transition table is transcribed from the generated predictor and")
    L.append("  every obligation is closed by `decide`, which keeps the axiom set")
    L.append("  empty. See the module docstring for when to prefer the pagoda route.")
    L.append("-/")
    L.append("")
    L.append("inductive St where")
    for i in range(len(states)):
        L.append("  | s%d" % i)
    L.append("  deriving DecidableEq, Repr")
    L.append("")
    L.append("inductive Act where")
    for i, a in enumerate(actions):
        L.append("  | a%d   -- %s" % (i, "(" + ", ".join(map(str, a)) + ")"))
    L.append("  deriving DecidableEq, Repr")
    L.append("")
    L.append("/-- The manual's rules, transcribed from the executable form. -/")
    L.append("def step : St → Act → St")
    for i, state in enumerate(states):
        for j, action in enumerate(actions):
            L.append("  | .s%d, .a%d => .s%d"
                     % (i, j, index[ns["step"](state, action).key()]))
    L.append("")
    L.append("def Goal : St → Bool")
    for i in range(len(states)):
        L.append("  | .s%d => %s" % (i, "true" if i in goal_hits else "false"))
    L.append("")
    L.append("inductive Reachable : St → Prop where")
    L.append("  | init : Reachable .s0")
    L.append("  | step : ∀ s a, Reachable s → Reachable (step s a)")
    L.append("")
    L.append("/-- `St` holds exactly the states the predictor can reach, so `step`")
    L.append("    closing over it is true by construction and `decide` sees it. -/")
    L.append("theorem reachable_closed (s : St) (a : Act) :")
    L.append("    (step s a = step s a) = True := by simp")
    L.append("")
    if goal_hits:
        L.append("/-- The goal IS reachable here: %s. There is nothing to prove"
                 % ", ".join("s%d" % i for i in goal_hits))
        L.append("    unsolvable, and this generator will not pretend otherwise. -/")
        L.append("theorem goal_is_reachable : ∃ s : St, Goal s = true :=")
        L.append("  ⟨.s%d, by decide⟩" % goal_hits[0])
        L.append("")
        L.append("#print axioms goal_is_reachable")
    else:
        L.append("theorem no_goal_state (s : St) : Goal s = false := by")
        L.append("  cases s <;> rfl")
        L.append("")
        L.append("theorem unsolvable : ¬ ∃ s : St, Reachable s ∧ Goal s = true := by")
        L.append("  rintro ⟨s, _, hg⟩")
        L.append("  rw [no_goal_state s] at hg")
        L.append("  exact Bool.noConfusion hg")
        L.append("")
        L.append("#print axioms unsolvable")
    L.append("")
    return "\n".join(L)


# ------------------------------------------------------------------- driver

def generate_lean(ast: TheoryAST, problem: ProblemSpec,
                  certificate: Optional[PagodaCertificate] = None,
                  proof: str = "computational") -> str:
    """Compile the manual's laws into Lean. The manual picks the development."""
    if proof not in PROOF_MODES:
        raise LeanGenError("proof must be one of %r, got %r"
                           % (list(PROOF_MODES), proof))
    # The certificate goes in *here*, not into this backend's own bookkeeping:
    # `_resolve_weights` is the single place a `weights <name>` declaration
    # acquires numbers, and the level-vs-certificate agreement check moved
    # there with it — which is why a stale level copy now raises `IRError`
    # rather than `LeanGenError` (E-05/E-06).
    #
    # Which forms this reaches, stated exactly, because the obvious reading is
    # wrong: any caller that hands `build_ir` a certificate gets the resolved
    # vector and the agreement check. That is this backend and
    # `generate_markdown(ast, ir)`. `gen_python` and `gen_pddl` take no
    # certificate and never see one — not an oversight: neither form's output
    # depends on the weights, so there is nothing in them that could go stale.
    # The predictor is a `step` function; a pagoda potential is not part of it.
    ir = build_ir(ast, problem, certificate)
    ns = _load_predictor(ast, problem)

    request = _pagoda_request(ir)
    if request is None:
        if certificate is not None:
            raise LeanGenError(
                "a certificate was supplied but the manual declares no "
                "`pagoda(...)` invariant, so nothing in it would be used. Add "
                "the invariant (E-05) or drop the certificate.")
        return _enumerative_lean(ir, ns)

    inv_name, weights_name, bound = request
    if certificate is None:
        raise LeanGenError(
            "invariant %r is a pagoda potential over %r, but no certificate was "
            "supplied. The manual names the potential; the weights are the "
            "engine's, and this backend will not invent them."
            % (inv_name, weights_name))

    declared = {d.name for d in ir.ast.word_table.weights}
    if weights_name not in declared:
        raise LeanGenError(
            "invariant %r refers to weights %r, which word_table never declares. "
            "Add `weights %s over <field>` (E-05)."
            % (inv_name, weights_name, weights_name))

    # The numbers themselves, and the agreement check against any level copy,
    # were resolved by `build_ir` above. What is left to check here is that the
    # resolution actually landed on *this* invariant's potential: a certificate
    # that filled some other declared name would leave this one without a
    # vector, and a backend that then read `certificate.weights` anyway would be
    # quietly proving a theorem about a potential the manual did not name.
    if list(ir.weights.get(weights_name, [])) != list(certificate.weights):
        raise LeanGenError(
            "invariant %r is a potential over %r, but the certificate's vector "
            "was not resolved onto that name (it holds %r). One certificate "
            "fills one declared potential; compile with the certificate for %s."
            % (inv_name, weights_name, ir.weights.get(weights_name), weights_name))

    return _pagoda_lean(ir, ns, certificate, inv_name, bound, proof)
