"""Reading the LP pagoda certificate that `engine-rig` exports.

The two tracks meet at `engine-rig/interop/certificates/*.json` and nowhere
else. Nothing here imports `engine-rig`; the file is the contract, and this
module is its consumer-side executable form.

**The producer's `verified: true` is not taken on trust.** That flag is computed
by the producer at build time, and the producer's own `verify()` re-derives the
arithmetic but does not check that the witness list is *complete* — a document
with witnesses deleted passes it. Since a missing witness is exactly a move
whose potential might rise, believing the flag would let an unsound weight
vector become a Lean theorem. So `load_certificate` re-derives the move set from
the geometry and checks every triple itself, and `recheck` is what the Lean
backend calls before it will emit a proof.

Schema (`lp_potential/pagoda_certificate@1`), the fields this module uses:

| field | meaning |
|---|---|
| `n_pos` | board size; positions are `0 .. n_pos-1` |
| `initial_state` | bitstring, `"1"` = peg present |
| `goal_states` | list of bitstrings; the claim is that **none** is reachable |
| `weights_integer` | `w[i]`, the pagoda weight of position `i` |
| `initial_potential` | `sum(w[i] for occupied i)` in the initial state |
| `obligations.inv_closed.witnesses` | one per move triple, `positions = [src, over, dst]` |

Move geometry, confirmed against the producer: `jump(src, over, dst)` needs a
peg at `src` and at `over` and a hole at `dst`, and leaves holes at `src` and
`over` and a peg at `dst`. So the potential changes by `w[dst] - w[src] -
w[over]`, which depends on the three weights **and not on the state** — that is
the whole reason the argument is algebraic and never needs a reachable set.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

SCHEMA = "lp_potential/pagoda_certificate@1"

Move = Tuple[int, int, int]  # (src, over, dst)


class CertificateError(Exception):
    """The certificate is malformed, or its own arithmetic does not hold."""


@dataclass
class PagodaCertificate:
    claim: str
    n_pos: int
    initial_state: str
    goal_states: List[str]
    weights: List[int]
    initial_potential: int
    produced_by: str
    path: str = ""
    declared_witnesses: List[Move] = field(default_factory=list)

    def potential(self, state: str) -> int:
        return sum(self.weights[i] for i, c in enumerate(state) if c == "1")

    def moves(self) -> List[Move]:
        """Every geometric triple, re-derived here rather than read from the file.

        `src = i`, `over = i + step`, `dst = i + 2*step` for `step` in `{+1, -1}`,
        keeping only triples inside the board.
        """
        out: List[Move] = []
        for src in range(self.n_pos):
            for step in (1, -1):
                over, dst = src + step, src + 2 * step
                if 0 <= dst < self.n_pos:
                    out.append((src, over, dst))
        return sorted(out)

    def delta(self, move: Move) -> int:
        src, over, dst = move
        return self.weights[dst] - self.weights[src] - self.weights[over]


def load_certificate(path: str) -> PagodaCertificate:
    with open(path, encoding="utf-8") as handle:
        doc = json.load(handle)

    if doc.get("schema") != SCHEMA:
        raise CertificateError(
            "expected schema %r, got %r — this reader implements one schema and "
            "will not guess at another" % (SCHEMA, doc.get("schema")))

    for key in ("n_pos", "initial_state", "goal_states", "weights_integer",
                "initial_potential"):
        if key not in doc:
            raise CertificateError("certificate is missing %r" % key)

    witnesses = []
    obligations = doc.get("obligations", {})
    for w in obligations.get("inv_closed", {}).get("witnesses", []):
        if "positions" in w and len(w["positions"]) == 3:
            witnesses.append(tuple(int(p) for p in w["positions"]))

    cert = PagodaCertificate(
        claim=doc.get("claim", "unsolvable"),
        n_pos=int(doc["n_pos"]),
        initial_state=doc["initial_state"],
        goal_states=list(doc["goal_states"]),
        weights=[int(x) for x in doc["weights_integer"]],
        initial_potential=int(doc["initial_potential"]),
        produced_by=doc.get("produced_by", "unknown"),
        path=path,
        declared_witnesses=witnesses,
    )
    recheck(cert)
    return cert


def recheck(cert: PagodaCertificate) -> None:
    """Re-derive every obligation from `weights` alone. Raises on any failure.

    This is the adjudication step. The engine proposed a weight vector; nothing
    downstream may treat it as proven until the three obligations have been
    recomputed here, over the *complete* move set, in integer arithmetic.
    """
    if len(cert.weights) != cert.n_pos:
        raise CertificateError(
            "n_pos is %d but %d weights were supplied"
            % (cert.n_pos, len(cert.weights)))

    for label, state in ([("initial_state", cert.initial_state)]
                         + [("goal_state", g) for g in cert.goal_states]):
        if len(state) != cert.n_pos:
            raise CertificateError(
                "%s %r is not %d positions long" % (label, state, cert.n_pos))
        if set(state) - {"0", "1"}:
            raise CertificateError("%s %r is not a bitstring" % (label, state))

    # inv_init — the bound is the initial potential, so this pins the arithmetic
    # rather than testing an inequality.
    actual = cert.potential(cert.initial_state)
    if actual != cert.initial_potential:
        raise CertificateError(
            "initial_potential says %d, but the weights give %d"
            % (cert.initial_potential, actual))

    # inv_closed — over every geometric triple, not only the listed witnesses.
    bad = [(m, cert.delta(m)) for m in cert.moves() if cert.delta(m) > 0]
    if bad:
        raise CertificateError(
            "the potential rises on %d move(s), so this is not a pagoda "
            "function: %s" % (len(bad), ", ".join(
                "jump(%d,%d,%d) delta=%+d" % (m[0], m[1], m[2], d)
                for m, d in bad)))

    derived = set(cert.moves())
    declared = set(cert.declared_witnesses)
    if declared - derived:
        raise CertificateError(
            "certificate lists move(s) that are not legal geometry on a "
            "%d-position board: %s" % (cert.n_pos, sorted(declared - derived)))
    if derived - declared:
        # Not fatal — we checked the full set ourselves — but a certificate that
        # skipped a move is one whose producer proved less than it claims, and
        # that is worth failing on rather than quietly covering for.
        raise CertificateError(
            "certificate omits %d move(s) from inv_closed: %s. The producer's "
            "own verifier does not check witness completeness, so this reader "
            "does." % (len(derived - declared), sorted(derived - declared)))

    # goal_break — strict, or the goal could sit exactly on the bound.
    for goal in cert.goal_states:
        p = cert.potential(goal)
        if p <= cert.initial_potential:
            raise CertificateError(
                "goal state %r has potential %d, which does not exceed the "
                "initial %d — the invariant does not exclude it"
                % (goal, p, cert.initial_potential))


def covers(cert: PagodaCertificate, goal_states: Sequence[str]) -> List[str]:
    """Which of `goal_states` this certificate does **not** exclude.

    An empty result means the certificate licenses the full claim. A non-empty
    one is not a bug to route around: it is `lp_potential`'s documented
    incompleteness showing through, and the caller must either narrow the claim
    or say plainly that it is unproven.
    """
    return [g for g in goal_states if g not in set(cert.goal_states)]
