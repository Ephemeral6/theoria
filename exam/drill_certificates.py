"""Machine-checkable certificates for wrapped worldgen worlds.

Theoria.md §1.11 says the answer to a verdict question is "一张机器可查的证书" --
a certificate a machine can check -- and that what class (i) really tests is the
*reason*: a certificate, or "I searched and found nothing".  So the drill has to
be able to check one mechanically, or it is rehearsing the wrong thing.

The grammar is deliberately the one `exam/grading/rubrics_verdict.py:120-124`
already froze, key-for-key:

    invariant : {kind, invariant, initial_value, goal_value}
    cut_set   : {kind, cells}
    counting  : {kind, bound, limit}

and it is closed the same way -- an unexpected or missing key is a refusal, not
a warning.  Two implementations of one grammar would drift, and the copy that
drifts is the one that accepts something it should not, so the key sets are
imported from that module rather than restated here.

**What these checks are worth, stated once and plainly.**  `invariant` and
`counting` are checked with *no state enumeration at all*: they read the
operator spec, the action-delta table and two cell coordinates.  `cut_set` is
checked on the grid graph, which is the board, not the state space.  That is the
whole point -- on a sealed game the state space is not enumerable and a reason
that needs it is not available.  But each carries a **side condition** on the
world it is used against, and the checker refuses rather than assumes:

* `invariant` and `counting` need "the agent moves at most one cell per command,
  along a `DELTA` axis".  A portal breaks it (the agent teleports) and so does
  gravity (the agent is moved by settle, not by the command), so worlds carrying
  either family are refused.
* `cut_set` needs two things, and the second is easy to miss. The agent must
  traverse the grid cell by cell -- portals break that -- **and it must be
  observed on every cell it traverses**, because an `observation_loss` is decided
  on a rendered frame, not on a position. `proxy/variants.py:_cells_hit` reads
  only `frames[-1]`, deliberately: "intermediate cascade frames are transient and
  declaring a loss on them would make the variant depend on animation timing".
  In worldgen the same thing happens inside `GridWorld.step`, which runs `settle`
  to a fixpoint before anything is rendered. So on a world with gravity the agent
  can be carried *through* a lethal cell during settle and come to rest beyond
  it, never having been rendered on it -- the loss never fires and a board-level
  cut is not a cut. Gravity is refused here too, for a different reason than it
  is refused above.

  This generalises past the drill, and §4 of `exam/SEALED_DRILL.md` records it:
  on any hosted game with cascades, `observation_loss` cuts where the arm comes
  to *rest*, not where it passes.

A certificate that passes here is a claim about *this* wrapped world that was
established without searching it.  The drill then checks that claim against the
exhaustive oracle, which is the one thing Phase 4 will never be able to do.
"""

from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Set, Tuple

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from exam.grading.rubrics_verdict import _CERT_KEYS  # noqa: E402
from worldgen.core.spec import WorldSpec  # noqa: E402
from worldgen.core.types import ACTIONS, AGENT, DELTA, Cell  # noqa: E402
from worldgen.mechanisms.base import for_kind  # noqa: E402

#: Families that break the "one cell per command, along an axis" premise.
TELEPORTING = ("portal",)
#: Families that move the agent outside the command it issued.
NON_COMMANDED = ("gravity",)

AXIS = {"agent_row": 0, "agent_col": 1}


def effective_families(spec: WorldSpec) -> FrozenSet[str]:
    """Every mechanism this world actually binds, not just the ones it declares.

    `WorldSpec.families` is a *declaration*. `GridWorld.__init__` binds
    mechanisms from the entity kinds present as well, so a spec carrying portal
    entities without naming `portal` in `families` is a world that teleports and
    does not say so. Across the twenty shipped worlds the two agree exactly --
    but that is a property of the catalogue, not an invariant of the type, and a
    side condition that can be evaded by omitting a word is not a side
    condition. So the union is what gets checked.
    """
    bound = set(spec.families)
    for entity in spec.entities:
        mechanism = for_kind(entity.kind)
        if mechanism is not None:
            bound.add(mechanism.name)
    return frozenset(bound)


class CertificateRefused(ValueError):
    """The certificate does not check out, and the message says why."""


def effective_actions(operators: Sequence[Dict[str, Any]]) -> Dict[str, Optional[str]]:
    """Command name -> the action actually performed, or `None` if refused.

    Reproduces `proxy/variants.py:VariantRuntime.before` ordering exactly:
    `forbid_action` is consulted **before** `remap_action`, so a command that is
    forbidden is never remapped, and a command that remaps *onto* a forbidden
    action is still forwarded.  That asymmetry is easy to get backwards and it
    changes which invariants hold, so it is derived from the frozen order rather
    than restated.
    """
    forbidden = {op["action"] for op in operators if op["op"] == "forbid_action"}
    remap = {op["from"]: op["to"] for op in operators if op["op"] == "remap_action"}
    out: Dict[str, Optional[str]] = {}
    for command in ACTIONS:
        if command in forbidden:
            out[command] = None
        else:
            out[command] = remap.get(command, command)
    return out


def _require_grammar(cert: Dict[str, Any]) -> str:
    kind = cert.get("kind")
    if kind not in _CERT_KEYS:
        raise CertificateRefused(
            "unknown certificate kind %r; the frozen grammar is %s"
            % (kind, ", ".join(sorted(_CERT_KEYS))))
    expected = _CERT_KEYS[kind]
    got = frozenset(cert)
    if got != expected:
        raise CertificateRefused(
            "%s certificate has the wrong keys: missing %s, unexpected %s"
            % (kind, sorted(expected - got) or "none", sorted(got - expected) or "none"))
    return kind


def _require_local_motion(spec: WorldSpec, why: str) -> None:
    bad = sorted(f for f in effective_families(spec) if f in TELEPORTING + NON_COMMANDED)
    if bad:
        raise CertificateRefused(
            "%s needs the agent to move one cell per command along an axis, and "
            "%s carries %s, which breaks that premise. Refused rather than "
            "assumed." % (why, spec.world_id, ", ".join(sorted(bad))))


def _open_cells(spec: WorldSpec) -> Set[Cell]:
    return {(r, c)
            for r in range(spec.height)
            for c in range(spec.width)
            if spec.layout[r][c] != "#"}


def check_invariant(spec: WorldSpec, operators: Sequence[Dict[str, Any]],
                    cert: Dict[str, Any]) -> Dict[str, Any]:
    """A monotone coordinate the goal sits on the wrong side of.

    Checked from the command alphabet alone: if no command the wrapper still
    forwards has a delta that moves the coordinate toward the goal, the
    coordinate is monotone, and a goal strictly on the unreachable side is
    unreachable.  No state is enumerated.
    """
    _require_local_motion(spec, "an axis invariant")
    name = cert["invariant"]
    if name not in AXIS:
        raise CertificateRefused(
            "unknown invariant %r; this checker knows %s"
            % (name, ", ".join(sorted(AXIS))))
    axis = AXIS[name]
    start = spec.agent_start[axis]
    goal = spec.goal[axis]
    if cert["initial_value"] != start:
        raise CertificateRefused(
            "initial_value %r but %s starts at %r"
            % (cert["initial_value"], name, start))
    if cert["goal_value"] != goal:
        raise CertificateRefused(
            "goal_value %r but the goal sits at %r" % (cert["goal_value"], goal))
    if goal == start:
        raise CertificateRefused(
            "%s is already the goal value; an invariant on it separates nothing"
            % name)
    needed = 1 if goal > start else -1
    live = effective_actions(operators)
    offenders = sorted(
        command for command, action in live.items()
        if action is not None and _sign(DELTA[action][axis]) == needed)
    if offenders:
        raise CertificateRefused(
            "%s is not monotone: %s still %s it"
            % (name, ", ".join(offenders),
               "increases" if needed > 0 else "decreases"))
    return {
        "ok": True, "kind": "invariant",
        "why": "no forwarded command changes %s in the direction of the goal "
               "(%d -> %d), so %s is monotone and the goal is on the unreachable "
               "side" % (name, start, goal, name),
        "checked_without_enumerating_states": True,
        "alphabet": {k: v for k, v in sorted(live.items())},
    }


def _sign(value: int) -> int:
    return (value > 0) - (value < 0)


def check_cut_set(spec: WorldSpec, operators: Sequence[Dict[str, Any]],
                  cert: Dict[str, Any]) -> Dict[str, Any]:
    """A set of cells every path from start to goal must cross.

    Checked on the board graph: delete the cells, then flood-fill from the start
    over 4-adjacency and confirm the goal is not reached.  The board is the
    thing a reader of the sheet can see, so this is a reason a marker can check
    against the same information the examinee had.
    """
    bad = sorted(f for f in effective_families(spec) if f in TELEPORTING + NON_COMMANDED)
    if bad:
        raise CertificateRefused(
            "a cut set on the board is only a cut if the agent walks the board "
            "and is *observed* on every cell it walks, and %s carries %s. "
            "Refused rather than assumed."
            % (spec.world_id, ", ".join(sorted(bad))))
    cells = cert["cells"]
    if not isinstance(cells, list) or not cells:
        raise CertificateRefused("cut_set needs a non-empty list of cells")
    cut: Set[Cell] = set()
    for cell in cells:
        if (not isinstance(cell, (list, tuple)) or len(cell) != 2
                or not all(isinstance(v, int) for v in cell)):
            raise CertificateRefused("cut cell %r is not an [int, int]" % (cell,))
        cut.add((cell[0], cell[1]))
    # The cells must be cells *this variant* makes lethal. Without this the
    # certificate is a statement about the board being accepted as a proof about
    # the variant, and a cut drawn on a world with no `observation_loss` at all
    # would be accepted. `exam/grading/rubrics_verdict.py:521-525` has exactly
    # this check against `level.lost_cells`; the first version of this file
    # imported the frozen grammar's key sets and then rewrote its checks, and the
    # rewrite dropped it -- which is precisely the drift the module docstring
    # warns about, arriving as predicted. Found by the V6 adversarial pass.
    #
    # The colour matters as much as the coordinates: `_cells_hit` fires only when
    # the named cell renders `value`, and only the agent renders `AGENT`
    # (`worldgen/core/types.py:42`). A loss keyed on any other colour does not cut
    # the agent's path, so it does not support this argument.
    hazards: Set[Cell] = set()
    for op in operators:
        if op.get("op") != "observation_loss" or op.get("value") != AGENT:
            continue
        for entry in op.get("cells", ()):
            hazards.add((entry[0], entry[1]))
    outside = sorted(c for c in cut if c not in hazards)
    if outside:
        raise CertificateRefused(
            "%s are not cells this variant makes lethal to the agent, so cutting "
            "them is a claim about a different world. This variant declares %s "
            "lethal at the agent's colour (%d)."
            % (outside, sorted(hazards) or "no cells", AGENT))

    start, goal = spec.agent_start, spec.goal
    if start in cut or goal in cut:
        raise CertificateRefused(
            "the cut contains the start or the goal; that is not a separation, "
            "it is a deletion of the endpoints")
    open_cells = _open_cells(spec) - cut
    seen = {start}
    frontier = [start]
    while frontier:
        cell = frontier.pop()
        for action in ACTIONS:
            dr, dc = DELTA[action]
            nxt = (cell[0] + dr, cell[1] + dc)
            if nxt in open_cells and nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
    if goal in seen:
        raise CertificateRefused(
            "removing %s leaves the goal reachable on the board, so it is not a "
            "cut" % (sorted(cut),))
    return {
        "ok": True, "kind": "cut_set",
        "why": "deleting %s disconnects the goal from the start on the board, "
               "so every route crosses one of them" % (sorted(cut),),
        "checked_without_enumerating_states": True,
        "component_size_without_cut": len(seen),
    }


def check_counting(spec: WorldSpec, operators: Sequence[Dict[str, Any]],
                   cert: Dict[str, Any]) -> Dict[str, Any]:
    """More commands are needed than the budget allows.

    The bound is the Manhattan distance from start to goal, which is a genuine
    lower bound exactly when one command moves the agent at most one cell along
    one axis -- the side condition `_require_local_motion` enforces.  Nothing is
    enumerated; two coordinates and a subtraction settle it.
    """
    _require_local_motion(spec, "a Manhattan counting bound")
    bound, limit = cert["bound"], cert["limit"]
    if not isinstance(bound, int) or not isinstance(limit, int):
        raise CertificateRefused("bound and limit must both be ints")
    real = (abs(spec.goal[0] - spec.agent_start[0])
            + abs(spec.goal[1] - spec.agent_start[1]))
    if bound != real:
        raise CertificateRefused(
            "bound %d is not the Manhattan distance from %s to %s, which is %d"
            % (bound, spec.agent_start, spec.goal, real))
    budgets = sorted(op["limit"] for op in operators if op["op"] == "step_limit")
    if not budgets:
        raise CertificateRefused(
            "a counting certificate argues against a budget, and this variant "
            "declares no step_limit")
    if limit != budgets[0]:
        raise CertificateRefused(
            "limit %d does not match the variant's tightest step_limit %d"
            % (limit, budgets[0]))
    if bound <= limit:
        raise CertificateRefused(
            "%d commands are needed and %d are allowed, so the budget does not "
            "bite -- this certificate proves nothing" % (bound, limit))
    return {
        "ok": True, "kind": "counting",
        "why": "the goal is %d cells away in Manhattan distance and one command "
               "moves the agent at most one cell, so at least %d commands are "
               "needed; the variant allows %d" % (bound, bound, limit),
        "checked_without_enumerating_states": True,
    }


CHECKERS = {
    "invariant": check_invariant,
    "cut_set": check_cut_set,
    "counting": check_counting,
}


def check(spec: WorldSpec, operators: Sequence[Dict[str, Any]],
          cert: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Check one certificate, or report that none was offered."""
    if cert is None:
        return {"ok": False, "kind": None,
                "why": "no certificate was offered for this claim"}
    try:
        kind = _require_grammar(cert)
        return CHECKERS[kind](spec, operators, cert)
    except CertificateRefused as exc:
        return {"ok": False, "kind": cert.get("kind"), "why": str(exc)}
