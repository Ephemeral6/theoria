"""Re-check a serialised certificate document as if a stranger had posted it.

This module is the *independent* half of requirement E6(B).  Three properties
make it independent, and all three are deliberate:

1. **It imports nothing from this rig.**  Not `engines.ic3_pdr`, not
   `engines.lp_potential`, not `interop.peg1d`, not `interop.certificate_export`.
   Standard library only.  `engines/ic3_pdr/check.py` already refuses to import
   `pdr` so that the search cannot certify itself; this goes one step further --
   the *producer's whole package* is out of scope, so a shared helper cannot
   quietly carry a shared bug across the boundary.  `tests/` asserts this by
   reading the import statements of this file.

2. **It reads a document, not an object.**  The input is whatever
   `json.loads` produced.  Nothing in memory survives the crossing: not the
   `System`, not the `Invariant`, not the `Certificate`, not the producer's
   `holds` flags.

3. **It re-derives the transition relation from `n_pos` alone.**  A certificate
   asserts that an invariant is inductive, and induction is only defined against
   a transition relation, so taking the relation from the same document would
   let a certificate be closed under a move set it chose for itself.
   `CONTRACTS/ic3_certificate_v0.1.md` names this and omits a `moves` field for
   exactly that reason.  The pagoda schema *does* carry its move witnesses --
   and `certificate_export.verify` reads them, which is a hole this module does
   not have; see `interop/README.md` and the E6 run's RUN_STATE.md.

The three obligations are the Lean skeleton of Theoria 1.10(a):

    inv_init    I(s0)
    inv_closed  forall s a, I s -> I (step s a)      over the FULL state space
    goal_break  forall g, Goal g -> not (I g)

`inv_closed` is checked over every state satisfying the invariant, not over the
reachable set.  Restricting to the reachable part would make the closure check
circular, which is the call both engines' READMEs already make.

The obligations were cross-read against the theory-compiler track's
`ic3_certificate.recheck`, which is a genuinely separate implementation of the
same contract.  Nothing is imported from it and it is not edited; the agreement
is on what is checked, not on code.
"""

import itertools
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

IC3_SCHEMA = "ic3_pdr/inductive_invariant_certificate@1"
PAGODA_SCHEMA = "lp_potential/pagoda_certificate@1"

# This checker is exhaustive by construction (2**n states).  A document naming a
# board it cannot enumerate is refused with a reason rather than accepted on the
# strength of a partial sweep -- a partial closure check is not a closure check.
MAX_POS = 16

Move = Tuple[int, int, int]


# --------------------------------------------------------------- the outcome

@dataclass(frozen=True)
class Refusal:
    """One reason the document was not accepted, with a witness where one exists."""

    obligation: str          # schema | shape | inv_init | inv_closed | goal_break
    reason: str
    witness: str = ""

    def as_json(self) -> Dict[str, str]:
        return {"obligation": self.obligation, "reason": self.reason,
                "witness": self.witness}


@dataclass
class RecheckResult:
    schema: str
    refusals: List[Refusal] = field(default_factory=list)
    n_states: int = 0
    n_satisfying: int = 0
    n_move_instances: int = 0
    n_transitions_checked: int = 0
    producer_claimed_ok: Optional[bool] = None   # recorded, never believed

    @property
    def ok(self) -> bool:
        return not self.refusals

    def refuse(self, obligation: str, reason: str, witness: str = "") -> None:
        self.refusals.append(Refusal(obligation, reason, witness))

    def obligations_refused(self) -> List[str]:
        seen: List[str] = []
        for refusal in self.refusals:
            if refusal.obligation not in seen:
                seen.append(refusal.obligation)
        return seen

    def as_json(self) -> Dict[str, Any]:
        return {
            "schema": self.schema,
            "ok": self.ok,
            "refusals": [r.as_json() for r in self.refusals],
            "obligations_refused": self.obligations_refused(),
            "n_states": self.n_states,
            "n_satisfying": self.n_satisfying,
            "n_move_instances": self.n_move_instances,
            "n_transitions_checked": self.n_transitions_checked,
            "producer_claimed_ok": self.producer_claimed_ok,
            "method": "exhaustive enumeration over the full state space, "
                      "geometry re-derived from n_pos",
        }


# ------------------------------------------------- the board, rebuilt from n

def states_of(n_pos: int) -> List[str]:
    """Every occupancy string, ascending.  Built here, not read from anywhere."""
    return ["".join(bits) for bits in itertools.product("01", repeat=n_pos)]


def moves_of(n_pos: int) -> List[Move]:
    """The 1D peg jump geometry: over a neighbour, into the cell beyond it."""
    out: List[Move] = []
    for src in range(n_pos):
        for step in (1, -1):
            over, dst = src + step, src + 2 * step
            if 0 <= dst < n_pos:
                out.append((src, over, dst))
    return sorted(out)


def legal(state: str, move: Move) -> bool:
    src, over, dst = move
    return state[src] == "1" and state[over] == "1" and state[dst] == "0"


def apply_move(state: str, move: Move) -> str:
    src, over, dst = move
    cells = list(state)
    cells[src] = cells[over] = "0"
    cells[dst] = "1"
    return "".join(cells)


def render_move(move: Move) -> str:
    return "jump(%d,%d,%d)" % move


# ------------------------------------------------------------ shared checks

def _check_board(document: Dict[str, Any], result: RecheckResult) -> Optional[int]:
    """`n_pos` and every bitstring in the document.  None means: stop here."""
    raw = document.get("n_pos")
    if not isinstance(raw, int) or isinstance(raw, bool):
        result.refuse("shape", "n_pos is %r, which is not an integer" % (raw,))
        return None
    if raw < 1 or raw > MAX_POS:
        result.refuse(
            "shape",
            "n_pos is %d; this checker enumerates 2**n_pos states and refuses "
            "anything above %d rather than certify on a partial sweep"
            % (raw, MAX_POS))
        return None

    ok = True
    labelled: List[Tuple[str, Any]] = [("initial_state", document.get("initial_state"))]
    goals = document.get("goal_states")
    if not isinstance(goals, list) or not goals:
        result.refuse(
            "shape",
            "goal_states is %r; a certificate with no goal states asserts "
            "nothing, and 'no goal is reachable' is vacuous over an empty set"
            % (goals,))
        ok = False
    else:
        labelled += [("goal_state", g) for g in goals]

    for label, value in labelled:
        if not isinstance(value, str):
            result.refuse("shape", "%s is %r, which is not a string" % (label, value))
            ok = False
            continue
        if len(value) != raw:
            result.refuse("shape", "%s %r is not %d positions long" % (label, value, raw))
            ok = False
        elif set(value) - {"0", "1"}:
            result.refuse("shape", "%s %r is not a bitstring" % (label, value))
            ok = False
    return raw if ok else None


def _claimed(document: Dict[str, Any]) -> Optional[bool]:
    """What the producer said about itself.  Recorded for contrast; never used."""
    if isinstance(document.get("verified"), bool):
        return bool(document["verified"])
    obligations = document.get("obligations")
    if isinstance(obligations, dict) and obligations:
        flags = [section.get("holds") for section in obligations.values()
                 if isinstance(section, dict)]
        if flags and all(isinstance(f, bool) for f in flags):
            return all(flags)
    return None


# ------------------------------------------------------------------- IC3

def _read_cnf(document: Dict[str, Any], variables: Sequence[str],
              result: RecheckResult) -> Optional[List[List[Tuple[int, bool]]]]:
    raw = document.get("cnf")
    if not isinstance(raw, list):
        result.refuse("shape", "cnf is %r, which is not a list of clauses" % (raw,))
        return None
    if not raw:
        result.refuse(
            "shape",
            "the certificate carries no clauses, so its invariant is `true`; "
            "true accepts every goal state and separates nothing")
        return None

    index_of = {name: i for i, name in enumerate(variables)}
    clauses: List[List[Tuple[int, bool]]] = []
    ok = True
    for position, clause in enumerate(raw):
        if not isinstance(clause, list):
            result.refuse("shape", "clause %d is %r, not a list" % (position, clause))
            ok = False
            continue
        if not clause:
            result.refuse(
                "shape",
                "clause %d is empty. An empty clause is false in every state, so "
                "the invariant accepts nothing and cannot hold at the initial "
                "state" % position)
            ok = False
            continue
        literals: List[Tuple[int, bool]] = []
        for literal in clause:
            if not isinstance(literal, (list, tuple)) or len(literal) != 2:
                result.refuse("shape", "clause %d holds %r, not a [variable, value] "
                                       "pair" % (position, literal))
                ok = False
                continue
            name, value = literal
            if name not in index_of:
                result.refuse(
                    "shape",
                    "a clause mentions %r, which is not one of the certificate's "
                    "declared variables %r -- an undeclared name is an error, not "
                    "something to guess at" % (name, list(variables)))
                ok = False
                continue
            if not isinstance(value, bool):
                result.refuse("shape", "literal %r carries %r, not a boolean"
                              % (name, value))
                ok = False
                continue
            literals.append((index_of[name], value))
        clauses.append(literals)
    return clauses if ok else None


def _holds(state: str, clauses: Sequence[Sequence[Tuple[int, bool]]]) -> bool:
    return all(
        any((state[index] == "1") == value for index, value in clause)
        for clause in clauses
    )


def recheck_ic3(document: Dict[str, Any]) -> RecheckResult:
    """Recompute inv_init / inv_closed / goal_break for an IC3 certificate."""
    result = RecheckResult(schema=IC3_SCHEMA)
    result.producer_claimed_ok = _claimed(document)

    if document.get("schema") != IC3_SCHEMA:
        result.refuse("schema", "expected schema %r, got %r; this reader "
                                "implements one schema and will not guess at "
                                "another" % (IC3_SCHEMA, document.get("schema")))
        return result

    n_pos = _check_board(document, result)

    variables = document.get("variables")
    if not isinstance(variables, list) or not all(isinstance(v, str) for v in variables):
        result.refuse("shape", "variables is %r, which is not a list of names"
                      % (variables,))
        return result
    if n_pos is not None and len(variables) != n_pos:
        result.refuse("shape", "n_pos is %d but %d variables were declared"
                      % (n_pos, len(variables)))
        n_pos = None
    if len(set(variables)) != len(variables):
        result.refuse("shape", "the certificate declares a variable twice: %r"
                      % (variables,))
        return result

    clauses = _read_cnf(document, variables, result)
    if n_pos is None or clauses is None:
        return result

    states = states_of(n_pos)
    moves = moves_of(n_pos)
    result.n_states = len(states)
    result.n_move_instances = len(moves)

    inside = [s for s in states if _holds(s, clauses)]
    result.n_satisfying = len(inside)
    accepted = set(inside)

    initial = document["initial_state"]
    if initial not in accepted:
        result.refuse(
            "inv_init",
            "the invariant does not hold at the initial state %s, so it "
            "separates nothing" % initial,
            witness=initial)

    escapes: List[str] = []
    for state in inside:
        for move in moves:
            if not legal(state, move):
                continue
            result.n_transitions_checked += 1
            after = apply_move(state, move)
            if after not in accepted:
                escapes.append("%s -%s-> %s" % (state, render_move(move), after))
    if escapes:
        result.refuse(
            "inv_closed",
            "the invariant is not inductive: %d transition(s) leave it over the "
            "full state space" % len(escapes),
            witness=escapes[0])

    admitted = [g for g in document["goal_states"] if g in accepted]
    if admitted:
        result.refuse(
            "goal_break",
            "the invariant admits goal state(s) %s, so it does not exclude them"
            % ", ".join(admitted),
            witness=admitted[0])
    return result


# ---------------------------------------------------------------- pagoda

def _potential(weights: Sequence[int], state: str) -> int:
    return sum(weights[i] for i, cell in enumerate(state) if cell == "1")


def recheck_pagoda(document: Dict[str, Any]) -> RecheckResult:
    """Recompute the same three obligations for an LP pagoda certificate.

    Unlike `certificate_export.verify`, the move instances come from `n_pos`,
    not from `obligations.inv_closed.witnesses`.  A document that simply omits
    an inconvenient witness passes that checker and is refused here.
    """
    result = RecheckResult(schema=PAGODA_SCHEMA)
    result.producer_claimed_ok = _claimed(document)

    if document.get("schema") != PAGODA_SCHEMA:
        result.refuse("schema", "expected schema %r, got %r"
                      % (PAGODA_SCHEMA, document.get("schema")))
        return result

    n_pos = _check_board(document, result)

    weights = document.get("weights_integer")
    if not isinstance(weights, list) or not all(
            isinstance(w, int) and not isinstance(w, bool) for w in weights):
        result.refuse("shape", "weights_integer is %r, which is not a list of "
                               "integers" % (weights,))
        return result
    if n_pos is None:
        return result
    if len(weights) != n_pos:
        result.refuse("shape", "n_pos is %d but %d weights were given"
                      % (n_pos, len(weights)))
        return result

    states = states_of(n_pos)
    moves = moves_of(n_pos)
    result.n_states = len(states)
    result.n_move_instances = len(moves)

    initial = document["initial_state"]
    bound = _potential(weights, initial)
    inside = [s for s in states if _potential(weights, s) <= bound]
    result.n_satisfying = len(inside)

    stated = document.get("initial_potential")
    if stated is not None and stated != bound:
        result.refuse(
            "shape",
            "initial_potential says %r but the weights give %d at %s"
            % (stated, bound, initial))

    # inv_init is arithmetic: potential(s0) <= potential(s0).  It cannot fail,
    # and saying so is more honest than reporting a check that is not one.

    for move in moves:
        src, over, dst = move
        delta = weights[dst] - weights[src] - weights[over]
        result.n_transitions_checked += 1
        if delta > 0:
            result.refuse(
                "inv_closed",
                "%s raises the potential by %d, so the invariant is not closed "
                "under it" % (render_move(move), delta),
                witness="%s: w[%d] - w[%d] - w[%d] = %d - %d - %d = %d"
                        % (render_move(move), dst, src, over,
                           weights[dst], weights[src], weights[over], delta))

    # The producer's own witness list is not evidence, but a list that does not
    # cover the board is a defect worth naming: it is what lets a dropped
    # witness slip past a checker that trusts it.
    witnesses = (((document.get("obligations") or {}).get("inv_closed") or {})
                 .get("witnesses"))
    if isinstance(witnesses, list):
        listed = {tuple(w.get("positions", ())) for w in witnesses
                  if isinstance(w, dict)}
        missing = [render_move(m) for m in moves if m not in listed]
        if missing:
            result.refuse(
                "inv_closed",
                "the document's own witness list omits %d of the %d move "
                "instances this board has; a witness list that does not cover "
                "the geometry cannot discharge closure"
                % (len(missing), len(moves)),
                witness=", ".join(missing[:4]))

    for goal in document["goal_states"]:
        value = _potential(weights, goal)
        if value <= bound:
            result.refuse(
                "goal_break",
                "goal %s has potential %d, which does not exceed the initial "
                "potential %d, so reaching it would not break the invariant"
                % (goal, value, bound),
                witness="%s: potential %d <= %d" % (goal, value, bound))
    return result


# ------------------------------------------------------------------ entry

def recheck(document: Dict[str, Any]) -> RecheckResult:
    """Dispatch on the document's own schema string."""
    schema = document.get("schema")
    if schema == IC3_SCHEMA:
        return recheck_ic3(document)
    if schema == PAGODA_SCHEMA:
        return recheck_pagoda(document)
    result = RecheckResult(schema=str(schema))
    result.refuse("schema", "unknown schema %r; this checker implements %r and "
                            "%r" % (schema, IC3_SCHEMA, PAGODA_SCHEMA))
    return result


def recheck_text(text: str) -> RecheckResult:
    """Re-check a certificate from its serialised bytes -- the stranger's path."""
    return recheck(json.loads(text))


def recheck_file(path: str) -> RecheckResult:
    with open(path, encoding="utf-8") as handle:
        return recheck_text(handle.read())
