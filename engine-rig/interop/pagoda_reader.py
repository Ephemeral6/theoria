"""A reader for `lp_potential/pagoda_certificate@1` that does not know the producer.

`certificate_export.verify()` is the producer grading its own homework twice: it
redoes the arithmetic, which catches a wrong sum, but it iterates the move list
the same document supplied, so a document that quietly omits an inconvenient
move instance passes it with an empty finding list. `DECISIONS.md` D-035 says so
in the table, and `interop/README.md` says so in prose. Neither of them was a
checker.

This is that checker, and it is deliberately built the awkward way:

* **stdlib only.** It imports `json`, `fractions`, `os`, `sys` and nothing else.
  Not `engines`, not `interop`, not `recheck`, not `common`. Copy this one file
  to an empty directory with a certificate and it runs — `tests/test_interop.py`
  does exactly that, in a subprocess with an empty `PYTHONPATH`, because a claim
  of independence that only a comment makes is not a claim anybody checked.
* **the move relation is grounded here, not read.** `jump_moves()` re-derives
  the peg1d geometry from `n_pos` alone. It duplicates the six lines of
  `peg1d.move_instances`, on purpose: a reader that imported the producer's
  geometry would be re-checking the producer's premise against itself. The
  duplication is the guarantee. `CONTRACTS/pagoda_certificate_v0.1.md` is what
  both copies are written from.
* **the producer's own verdict is not read.** `obligations`, `verified` and
  `conclusion` are never opened. They are the producer's opinion, and this file
  exists precisely because an opinion in the same document is not evidence. The
  same discipline the theory-compiler track wrote down for its ic3 reader
  (`CONTRACTS/ic3_certificate_v0.1.md`: 「没有 `moves` 字段，这是有意的」) —
  an invariant is only inductive *with respect to a transition relation*, so the
  relation must not come from the document asserting the invariant.

What a clean run entitles a reader to: **the three pagoda obligations hold for
the stated weights, over the whole state space, under the peg1d jump relation on
`n_pos` cells.** That is the full pagoda argument, so it entitles the reader to
the conclusion as well — unlike `certificate_export.verify()`, which entitles
you only to "the stated obligations hold over the stated moves".

What it does *not* establish: that peg1d is the right rule set for whatever
world the caller cares about. This reader takes the geometry as its own
assumption, declared in `GEOMETRY`, and says so rather than pretending the
document settled it. A different rule family needs a different reader and a
different schema id — which is why the schema string is pinned exactly.
"""

import json
import os
import sys
from fractions import Fraction

SCHEMA = "lp_potential/pagoda_certificate@1"

#: The rule family this reader grounds. `@1` documents carry no rule set (see
#: the module docstring for why that is deliberate), so the family is the
#: reader's assumption and is named here rather than inferred.
GEOMETRY = "peg1d_jump"

#: Fields written by the producer about its own conclusions. Reading any of them
#: would defeat the point of this file, so they are listed rather than merely
#: not-used: a future edit that starts reading one has to delete a name here
#: first, and `tests/test_interop.py` asserts none of them is read.
PRODUCER_OPINION = ("obligations", "verified", "conclusion", "checked_over")


def jump_moves(n_pos):
    """Every `(src, over, dst)` jump on a 1-D board of `n_pos` cells.

    Both directions, over the *whole* state space rather than the reachable
    part: an invariant that is only closed on the states you happened to reach
    is closed by assuming what it is meant to prove.
    """
    moves = []
    for src in range(n_pos):
        for step in (1, -1):
            over, dst = src + step, src + 2 * step
            if 0 <= dst < n_pos:
                moves.append((src, over, dst))
    return sorted(moves)


def potential(weights, state):
    return sum(w for w, cell in zip(weights, state) if cell == "1")


def _is_state(value, n_pos):
    return (isinstance(value, str) and len(value) == n_pos
            and set(value) <= {"0", "1"})


def _structure(document):
    """Rejections that make the arithmetic questions meaningless.

    Returned separately because a malformed document must not be handed to
    `potential()` — a `weights_integer` one element short would silently score
    the last cell as zero and could turn a forgery into a pass.
    """
    bad = []
    if not isinstance(document, dict):
        # A JSON file is whatever somebody put in it. `check` used to raise
        # `AttributeError` on a top-level array, which is a traceback where a
        # refusal belongs -- and a traceback is the one output a caller cannot
        # tell apart from a rejection.
        return ["the document is a %s, not an object"
                % type(document).__name__]
    if document.get("schema") != SCHEMA:
        bad.append("schema is %r, not %r" % (document.get("schema"), SCHEMA))
        return bad

    n_pos = document.get("n_pos")
    if not isinstance(n_pos, int) or isinstance(n_pos, bool) or n_pos < 3:
        bad.append("n_pos is %r; a jump needs at least 3 cells" % (n_pos,))
        return bad

    weights = document.get("weights_integer")
    if not isinstance(weights, list):
        # Said separately from the length complaint on purpose: a tuple used to
        # be reported as "has no entries", which is a correct refusal with a
        # wrong reason, and the reason is what a human acts on.
        bad.append("weights_integer is a %s, not a list"
                   % type(weights).__name__)
    elif len(weights) != n_pos:
        bad.append("weights_integer has %d entries, n_pos is %d"
                   % (len(weights), n_pos))
    elif any(not isinstance(w, int) or isinstance(w, bool) for w in weights):
        bad.append("weights_integer holds a non-integer: %r" % (weights,))

    if not _is_state(document.get("initial_state"), n_pos):
        bad.append("initial_state %r is not a %d-bit string"
                   % (document.get("initial_state"), n_pos))

    goals = document.get("goal_states")
    if not isinstance(goals, list):
        bad.append("goal_states is a %s, not a list" % type(goals).__name__)
    elif not goals:
        # A certificate against no goal states discharges `goal_break`
        # vacuously and concludes nothing. Refusing it is the same call the ic3
        # contract makes about an empty clause set.
        bad.append("goal_states is empty; a certificate against nothing "
                   "proves nothing")
    elif any(not _is_state(g, n_pos) for g in goals):
        bad.append("goal_states holds an entry that is not a %d-bit string: %r"
                   % (n_pos, goals))

    if not isinstance(document.get("initial_potential"), int) or \
            isinstance(document.get("initial_potential"), bool):
        bad.append("initial_potential is %r, not an integer bound"
                   % (document.get("initial_potential"),))
    return bad


def _rationals_agree(document):
    """`weights_rational`, if present, must be the integers up to one positive scale.

    Both fields are the producer's, so this is an internal-consistency check,
    not an independent one — but a forger who edits the integers and forgets the
    rationals has left the document disagreeing with itself, and a document that
    disagrees with itself is not a certificate.
    """
    rationals = document.get("weights_rational")
    if rationals is None:
        return []
    weights = document["weights_integer"]
    if not isinstance(rationals, list) or len(rationals) != len(weights):
        return ["weights_rational has %s entries, weights_integer has %d"
                % (len(rationals) if isinstance(rationals, list) else "no",
                   len(weights))]
    try:
        exact = [Fraction(str(r)) for r in rationals]
    except (ValueError, ZeroDivisionError, TypeError):
        return ["weights_rational is not parseable as exact rationals: %r"
                % (rationals,)]
    ratios = {Fraction(w, 1) / r for w, r in zip(weights, exact) if r != 0}
    zeros_agree = all((w == 0) == (r == 0) for w, r in zip(weights, exact))
    if not zeros_agree:
        return ["weights_rational and weights_integer disagree about which "
                "cells carry zero weight"]
    if not ratios:
        return ["weights_rational is all zeros; it scales to nothing"]
    if len(ratios) != 1 or ratios.pop() <= 0:
        return ["weights_integer is not a single positive multiple of "
                "weights_rational"]
    return []


def check(document, geometry=jump_moves):
    """Re-derive all three pagoda obligations. Empty list means accepted.

    `geometry` is a parameter so a caller with a different rule family can
    supply it; it is never taken from `document`.
    """
    bad = _structure(document)
    if bad:
        return bad

    weights = document["weights_integer"]
    bound = document["initial_potential"]
    bad.extend(_rationals_agree(document))

    # inv_init -- the declared bound must actually bound the start. Reading the
    # bound from the document rather than recomputing it from `initial_state` is
    # what makes this a check at all: `certificate_export` writes the bound *as*
    # potential(initial), so the producer's own copy of this obligation reads
    # "x <= x" and its docstring admits as much.
    start = potential(weights, document["initial_state"])
    if start > bound:
        bad.append("inv_init: potential(%s) = %d exceeds the declared bound %d"
                   % (document["initial_state"], start, bound))

    # inv_closed -- over every move this reader derived, not every move the
    # document listed. This is the obligation `certificate_export.verify()`
    # cannot discharge, and the only reason this file exists.
    for src, over, dst in geometry(document["n_pos"]):
        delta = weights[dst] - weights[src] - weights[over]
        if delta > 0:
            bad.append("inv_closed: jump(%d,%d,%d) raises the potential by %d"
                       % (src, over, dst, delta))

    # goal_break -- every goal state must fail the invariant.
    for goal in document["goal_states"]:
        value = potential(weights, goal)
        if value <= bound:
            bad.append("goal_break: goal %s has potential %d, which the "
                       "invariant (<= %d) admits" % (goal, value, bound))
    return bad


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def second_opinion(document, limit=20):
    """Exhaustive reachability, for boards small enough to enumerate.

    Not part of the verdict, and deliberately so: a valid pagoda *implies*
    unreachability, so a search can never strengthen an accepted certificate. It
    can only catch a bug in this reader — if `check` accepts a document whose
    claim enumeration refutes, one of the two is wrong and both are mine. It is
    reported beside the verdict, never folded into it.

    Returns `None` when the board is too large to enumerate, which is the case
    the certificate exists for in the first place.
    """
    n_pos = document.get("n_pos")
    if not isinstance(n_pos, int) or n_pos > limit:
        return None
    moves = jump_moves(n_pos)
    start = document["initial_state"]
    seen, frontier = {start}, [start]
    while frontier:
        state = frontier.pop()
        for src, over, dst in moves:
            if state[src] == "1" and state[over] == "1" and state[dst] == "0":
                cells = list(state)
                cells[src] = cells[over] = "0"
                cells[dst] = "1"
                nxt = "".join(cells)
                if nxt not in seen:
                    seen.add(nxt)
                    frontier.append(nxt)
    return {"n_reachable": len(seen),
            "goal_reachable": bool(seen & set(document["goal_states"]))}


def main(argv):
    """Exit 0 accepted, 1 refused, 2 the file could not be adjudicated.

    The three are kept apart deliberately. `REJECTED` is a statement about the
    certificate; a traceback is a statement about this program, and both used to
    leave status 1 -- so a wrapper reading the exit code would have reported a
    malformed file as a refuted claim. `recheck/__main__.py` separates the same
    two for the same reason.
    """
    if len(argv) != 2:
        sys.stderr.write("usage: %s <certificate.json>\n"
                         % os.path.basename(argv[0] or "pagoda_reader.py"))
        return 2
    try:
        document = load(argv[1])
    except (OSError, ValueError, RecursionError) as exc:
        sys.stderr.write("MALFORMED %s\n  %s: %s\n"
                         % (argv[1], type(exc).__name__, exc))
        return 2
    if not isinstance(document, dict):
        # `check` refuses this too, and returns rather than raising, which is
        # what the library owes a caller. The CLI grades it differently: a JSON
        # array is not a certificate this program declined to believe, it is a
        # file that was never a certificate, and exit 1 would say the first.
        sys.stderr.write("MALFORMED %s\n  the document is a %s, not an object\n"
                         % (argv[1], type(document).__name__))
        return 2
    rejections = check(document)
    if rejections:
        sys.stdout.write("REJECTED %s\n" % argv[1])
        for line in rejections:
            sys.stdout.write("  %s\n" % line)
        return 1
    # Only now, and only on a document `check` has already found well-formed:
    # `second_opinion` indexes fields that a refused document need not have, so
    # running it first turned some refusals into tracebacks.
    opinion = second_opinion(document)
    n_moves = len(jump_moves(document["n_pos"]))
    sys.stdout.write(
        "ACCEPTED %s\n  the pagoda obligations hold for the stated weights "
        "over all %d jump instances on %d cells, under %s\n"
        % (argv[1], n_moves, document["n_pos"], GEOMETRY))
    if opinion is not None:
        sys.stdout.write(
            "  second opinion (not part of the verdict): %d states reachable, "
            "goal reachable: %s\n"
            % (opinion["n_reachable"], opinion["goal_reachable"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
