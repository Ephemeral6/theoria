"""Reading the `ic3_pdr` inductive-invariant certificate.

The second certificate schema this compiler consumes, and the reason it exists:
`lp_potential` is sound but incomplete. On the peg boards some genuinely
unsolvable configurations admit no linear pagoda function at all, and `ic3_pdr`
is the engine whose whole reason for being is that gap — the same three
obligations (`inv_init` / `inv_closed` / `goal_break`), a different class of
invariant.

**Why it is worth consuming even though E-06 is already discharged.** E-06 was
closed by exhausting the reachable set, which works because that set has five
states. A proof by exhaustion is `O(reachable set)` and does not survive a
larger board. A CNF invariant does: two clauses stay two clauses, and the Lean
development that follows from it splits on **moves**, not on states. That is
the same trade the pagoda route buys, extended to configurations the pagoda
route cannot reach.

**The producer's own verdict is not evidence.** The candidate payload carries a
`conditions` block and a `check` block, both computed by the producer — and its
`checked_by` note says the checker shares no code with the search, which is a
real and valuable discipline on *their* side of the boundary. It is still their
opinion arriving in a file. Exactly as `certificate.py` refuses to believe
`verified: true`, this module recomputes all three obligations over the full
state space before anything downstream may use them, and it imports nothing
from `engine-rig`.

Schema (`ic3_pdr/inductive_invariant_certificate@1`), the fields used here:

| field | meaning |
|---|---|
| `n_pos` | board size; positions are `0 .. n_pos-1` |
| `variables` | one name per position, **positionally** — `variables[i]` is cell `i` |
| `initial_state` | bitstring, `"1"` = occupied |
| `goal_states` | list of bitstrings; the claim is that **none** is reachable |
| `cnf` | list of clauses, each a list of `[variable, required_value]` literals |
"""

import json
from typing import List, Sequence, Tuple

from .certificate import CertificateError, Move

SCHEMA = "ic3_pdr/inductive_invariant_certificate@1"

Literal = Tuple[str, bool]      # (variable, the value that satisfies the clause)
Clause = List[Literal]


class InductiveInvariantCertificate:
    """A CNF invariant separating the initial state from every goal state."""

    def __init__(self, claim: str, n_pos: int, variables: Sequence[str],
                 initial_state: str, goal_states: Sequence[str],
                 cnf: Sequence[Clause], produced_by: str, path: str = ""):
        self.claim = claim
        self.n_pos = n_pos
        self.variables = list(variables)
        self.initial_state = initial_state
        self.goal_states = list(goal_states)
        self.cnf = [list(c) for c in cnf]
        self.produced_by = produced_by
        self.path = path

    def index_of(self, variable: str) -> int:
        """`variables` is positional; the index carries the meaning.

        The producer spells them `pos0..posN`, but nothing here depends on that:
        a certificate naming them `a, b, c` would work identically, and one that
        mentions a name it never declared is refused rather than guessed at.
        """
        try:
            return self.variables.index(variable)
        except ValueError:
            raise CertificateError(
                "a clause mentions %r, which is not one of the certificate's "
                "declared variables %r" % (variable, self.variables))

    def holds(self, state: str) -> bool:
        """Does the invariant accept this occupancy string?"""
        return all(
            any((state[self.index_of(v)] == "1") == value for v, value in clause)
            for clause in self.cnf)

    def moves(self) -> List[Move]:
        """The move geometry, re-derived here rather than read from the file.

        An invariant is inductive only *with respect to a transition relation*,
        so the relation cannot come from the same document that asserts the
        induction — that would let a certificate be closed under a move set it
        chose for itself. This is the identical derivation `certificate.py`
        performs, and `gen_lean` cross-checks both against the predictor.
        """
        out: List[Move] = []
        for src in range(self.n_pos):
            for step in (1, -1):
                over, dst = src + step, src + 2 * step
                if 0 <= dst < self.n_pos:
                    out.append((src, over, dst))
        return sorted(out)

    def states(self) -> List[str]:
        return ["".join("1" if i >> k & 1 else "0" for k in range(self.n_pos))
                for i in range(1 << self.n_pos)]

    def clause_text(self) -> str:
        return " & ".join(
            "(" + " | ".join(("" if value else "!") + v for v, value in clause) + ")"
            for clause in self.cnf)


def legal(state: str, move: Move) -> bool:
    src, over, dst = move
    return state[src] == "1" and state[over] == "1" and state[dst] == "0"


def apply_move(state: str, move: Move) -> str:
    src, over, dst = move
    cells = list(state)
    cells[src] = cells[over] = "0"
    cells[dst] = "1"
    return "".join(cells)


def load_ic3_certificate(path: str) -> InductiveInvariantCertificate:
    with open(path, encoding="utf-8") as handle:
        doc = json.load(handle)

    if doc.get("schema") != SCHEMA:
        raise CertificateError(
            "expected schema %r, got %r — this reader implements one schema and "
            "will not guess at another" % (SCHEMA, doc.get("schema")))

    for key in ("n_pos", "variables", "initial_state", "goal_states", "cnf"):
        if key not in doc:
            raise CertificateError("certificate is missing %r" % key)

    cnf: List[Clause] = []
    for clause in doc["cnf"]:
        if not clause:
            raise CertificateError(
                "the certificate contains an empty clause. An empty clause is "
                "false in every state, so the invariant accepts nothing and "
                "cannot hold at the initial state — this would be caught below "
                "anyway, but the shape is worth naming.")
        cnf.append([(str(v), bool(value)) for v, value in clause])

    cert = InductiveInvariantCertificate(
        claim=doc.get("claim", "unsolvable"),
        n_pos=int(doc["n_pos"]),
        variables=doc["variables"],
        initial_state=doc["initial_state"],
        goal_states=doc["goal_states"],
        cnf=cnf,
        produced_by=doc.get("produced_by", "unknown"),
        path=path,
    )
    recheck(cert)
    return cert


def recheck(cert: InductiveInvariantCertificate) -> None:
    """Re-derive all three obligations from the CNF alone. Raises on failure.

    This is the adjudication step. The engine proposed a separating invariant;
    nothing downstream may treat it as proven until the three obligations have
    been recomputed here, over the **whole** state space rather than the
    reachable part. That is the call `ic3_pdr` documents making and it is the
    right one: an inductive invariant must be closed under moves from every
    state satisfying it, and restricting the relation to the reachable part
    would make the closure check quietly circular.
    """
    if len(cert.variables) != cert.n_pos:
        raise CertificateError(
            "n_pos is %d but %d variables were declared"
            % (cert.n_pos, len(cert.variables)))
    if len(set(cert.variables)) != len(cert.variables):
        raise CertificateError(
            "the certificate declares a variable twice: %r" % (cert.variables,))
    if not cert.cnf:
        raise CertificateError(
            "the certificate carries no clauses, so its invariant is `true`, "
            "which admits every goal state and separates nothing")

    for label, state in ([("initial_state", cert.initial_state)]
                         + [("goal_state", g) for g in cert.goal_states]):
        if len(state) != cert.n_pos:
            raise CertificateError(
                "%s %r is not %d positions long" % (label, state, cert.n_pos))
        if set(state) - {"0", "1"}:
            raise CertificateError("%s %r is not a bitstring" % (label, state))

    for clause in cert.cnf:                    # resolves every name, or raises
        for variable, _ in clause:
            cert.index_of(variable)

    if not cert.holds(cert.initial_state):
        raise CertificateError(
            "inv_init fails: the invariant does not hold at the initial state "
            "%s, so it separates nothing." % cert.initial_state)

    escapes = [(s, m, apply_move(s, m))
               for s in cert.states() for m in cert.moves()
               if cert.holds(s) and legal(s, m) and not cert.holds(apply_move(s, m))]
    if escapes:
        state, move, after = escapes[0]
        raise CertificateError(
            "inv_closed fails: the invariant is not inductive. From %s, which "
            "satisfies it, jump(%d,%d,%d) reaches %s, which does not — %d such "
            "escape(s) over the full state space. A non-inductive invariant "
            "proves nothing about reachability."
            % (state, move[0], move[1], move[2], after, len(escapes)))

    admitted = [g for g in cert.goal_states if cert.holds(g)]
    if admitted:
        raise CertificateError(
            "goal_break fails: the invariant admits goal state(s) %s, so it "
            "does not exclude them." % admitted)


def covers(cert: InductiveInvariantCertificate,
           goal_states: Sequence[str]) -> List[str]:
    """Which of `goal_states` this certificate does **not** exclude.

    Same shape and same contract as the pagoda reader's `covers`: an empty
    result means the certificate licenses the full claim, and a non-empty one is
    the method's incompleteness showing through rather than a bug to route
    around.
    """
    return [g for g in goal_states if g not in set(cert.goal_states)]
