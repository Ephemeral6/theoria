"""判决题 -- the verdict rubric, and the certificate checker that gives it teeth.

Theoria.md 1.11 splits the verdict question into three classes and says what
each one is for:

  (i)   small-space unsolvable -- exhaustive search is feasible, so a complete
        searcher stops correctly too, and may even stop correctly *for the wrong
        reason* (a missing edge).  What is being examined here is therefore the
        reason, not the verdict: a certificate, or "I searched and found
        nothing".
  (ii)  large-space unsolvable -- exhaustive search is out of reach and only
        invariant reasoning answers.  Our home ground.
  (iii) solvable but hard -- the false-positive trap.  A framework with a taste
        for unsolvability proofs has to shut up here.

The rubric therefore scores two things per item and reports them separately:
the **verdict** (half the points) and the **justification** (the other half).

    certificate that this module mechanically verifies   -> full justification
    "I enumerated the whole space and found nothing"     -> partial (0.4)
    a wrong, unverifiable or absent reason               -> verdict only
    a solvable claim backed by a witness plan we replay  -> full justification

**A checker that accepts free text is not a checker.**  The whole point of
class (i) is that a right verdict with a hand-waved reason must be scored below
a right verdict with a machine-checked one, and that ordering is only real if
the machine actually refuses things.  So the certificate grammar below is
*closed*: three kinds, an exact key set per kind, and anything else -- an extra
field, a prose "explanation", a fourth kind -- is refused outright rather than
interpreted charitably.  `check_certificate` re-derives every number it is
handed from the level itself; the examinee's arithmetic is checked, never
believed.

**Why the world engine lives here rather than in the paper builder.**  A rubric
must be a pure function of (answer, truth, item) -- `exam.model.Rubric` says so,
and a rubric that could reach the builder could be tuned to the answers.  So the
level travels inside `truth` as a JSON *string* (`level_blob`), this module
parses it, and everything the marker needs -- passability, the transition
function, replay, connectivity -- is re-derived from that string.  The string
rather than a nested dict is not fussiness: `exam.leakage`'s structural check
compares key *names* across `Item.paper` and `Item.truth` at every depth, and a
level dict on both sides would collide on every field.  A blob has no keys.

The digest that freezes this file therefore covers the checker, which is
correct: the checker is the marking rule.


The certificate grammar (closed; anything outside it is refused)
---------------------------------------------------------------

    {"kind": "invariant", "invariant": NAME,
     "initial_value": V, "goal_value": W}

        NAME is one of "cart_row", "cart_col", "cart_region".  The checker
        recomputes the named quantity at the start cell and at the goal cell,
        demands V and W match, demands the invariant is *closed* under every
        command the variant leaves available, and demands the goal's value is
        on the unreachable side.  Closure is checked locally -- over the action
        alphabet and the board, never over the state space -- which is exactly
        why this certificate scales to class (ii).

        For "cart_row"/"cart_col" the value is the row/column number and
        closure means every available command has a row/column delta of one
        sign (teleport jumps included).
        For "cart_region" the value is the component's canonical representative
        cell `[row, col]` -- the lexicographically smallest cell of the
        connected component, so the naming is derivable rather than ours.

    {"kind": "cut_set", "cells": [[r, c], ...]}

        Every listed cell must be declared a hazard by the variant, and
        deleting them must disconnect start from goal in the over-approximating
        graph.  Then every path to the goal occupies a hazard, and dies.

    {"kind": "counting", "bound": N, "limit": M}

        M must be the variant's step limit, N must be no larger than a lower
        bound this module computes itself (shortest path in a relaxation that
        can only over-connect), and M must be strictly less than N.

Every graph the checker builds is an **over-approximation** of what the cart can
actually do: doors are treated as open, the button as walkable, switch state is
ignored.  Over-approximating is the only safe direction -- it can make a truly
unsolvable level look solvable (the certificate is then refused, which is a
false negative and costs the examinee points) but it can never make a solvable
level look unsolvable, which would hand out points for a false theorem.

**That paragraph was false when it was written, and the reason is worth keeping.**
The graph was built by a *second* implementation of the transition function, and
the two disagreed in three places -- an absent `portal_dest`, a `portal_dest`
inside a wall, and a cell that is both the door and the portal.  In each,
`Level.step` moved the cart and `_neighbours` dropped the edge, so the graph was
an under-approximation exactly where it mattered and `cart_region` and `cut_set`
certificates for **solvable** levels were accepted and paid in full.  A
docstring claiming soundness is not soundness.  There is now one transition
function; `_neighbours` asks it; and `Level.wellformed_problems` catches at build
time the field combinations that made the disagreement reachable.  D-EX-020.
"""

from __future__ import annotations

import json
from collections import deque
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from ..model import Item, ItemScore, Rubric

Cell = Tuple[int, int]

ACTIONS: Tuple[str, ...] = ("UP", "DOWN", "LEFT", "RIGHT")
DELTA: Dict[str, Cell] = {"UP": (-1, 0), "DOWN": (1, 0),
                          "LEFT": (0, -1), "RIGHT": (0, 1)}
OPPOSITE = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}

#: A witness longer than this is refused unread.  A rubric is handed untrusted
#: input; "replay whatever they sent" is a denial-of-service surface, and no
#: level in this family needs anything close to the cap.
MAX_WITNESS = 5000

#: Enumerating a state space inside the marker is refused past this.  Nothing in
#: the rubric needs it -- it is a guard on `enumerate_states`, which the builder
#: uses and which a future rubric might be tempted to.
MAX_ENUMERATION = 200_000

INVARIANT_NAMES = ("cart_row", "cart_col", "cart_region")
CERT_KINDS = ("invariant", "cut_set", "counting")

#: Exact key sets.  Extra keys are refused, not ignored: a certificate carrying
#: a prose "explanation" alongside the arithmetic is the free-text checker this
#: module exists to not be.
_CERT_KEYS: Dict[str, frozenset] = {
    "invariant": frozenset({"kind", "invariant", "initial_value", "goal_value"}),
    "cut_set": frozenset({"kind", "cells"}),
    "counting": frozenset({"kind", "bound", "limit"}),
}


# --------------------------------------------------------------- the level

class Level:
    """One A2-family level plus the wrapper operators applied to it.

    Parsed from the JSON blob in `truth["level_blob"]`.  Nothing here reads a
    file or reaches the builder.
    """

    def __init__(self, doc: Dict[str, Any]):
        self.doc = doc
        self.level_id: str = doc["level_id"]
        self.rows: List[str] = list(doc["rows"])
        self.height = len(self.rows)
        self.width = len(self.rows[0]) if self.rows else 0
        self.start: Cell = _cell(doc["start"])
        self.goal: Cell = _cell(doc["goal"])
        self.button: Optional[Cell] = _opt_cell(doc.get("button"))
        self.door: Optional[Cell] = _opt_cell(doc.get("door"))
        self.portal: Optional[Cell] = _opt_cell(doc.get("portal"))
        self.portal_dest: Optional[Cell] = _opt_cell(doc.get("portal_dest"))
        self.switches: Tuple[Cell, ...] = tuple(_cell(c) for c in doc.get("switches", ()))
        self.switch_index: Dict[Cell, int] = {c: i for i, c in enumerate(self.switches)}
        self.require_all_switches: bool = bool(doc.get("require_all_switches", False))
        self.forbidden: frozenset = frozenset(doc.get("forbidden", ()))
        self.remap: Dict[str, str] = dict(doc.get("remap", {}))
        self.step_limit: Optional[int] = doc.get("step_limit")
        self.lost_cells: frozenset = frozenset(_cell(c) for c in doc.get("lost_cells", ()))
        self.win_score_required: int = int(doc.get("win_score_required", 1))

    # -- geometry ---------------------------------------------------------
    def in_bounds(self, cell: Cell) -> bool:
        return 0 <= cell[0] < self.height and 0 <= cell[1] < self.width

    def is_wall(self, cell: Cell) -> bool:
        return self.rows[cell[0]][cell[1]] == "#"

    def commands(self) -> Tuple[str, ...]:
        """The arm's alphabet after `forbid_action`."""
        return tuple(a for a in ACTIONS if a not in self.forbidden)

    def world_action(self, command: str) -> str:
        """`remap_action` is applied at the proxy, so the arm's command and the
        world's action are not the same string."""
        return self.remap.get(command, command)

    def effective_actions(self) -> Set[str]:
        """World actions some surviving command can still produce."""
        return {self.world_action(c) for c in self.commands()}

    def passable(self, cell: Cell) -> bool:
        """Cells the cart could conceivably occupy, generously.

        Door open, hazards ignored.  Two cells are excluded, and neither
        exclusion is generosity -- both are cells `step` will never return, so
        admitting them would let a cut set claim a cell no path ever stands on:

        * the **portal entry**, because a teleport moves the cart *through* it;
        * the **button**, because stepping into B latches the button and leaves
          the cart where it was.  `step` says so at line 205 and always has.

        The button used to be admitted, which cost nothing while `_neighbours`
        was a separate implementation that yielded it as a neighbour.  Once
        `_neighbours` began asking `step`, the button became a node with no
        edges -- its own singleton component -- and since `components` names a
        component by its lexicographically smallest cell, the atrium's start
        representative moved from the button at [1,1] to [1,3] and the shipped
        `a2var-i1` certificate was refused.  The separation was never in doubt;
        the *name* of the component changed.  Excluding the button is what makes
        the node set mean "cells the cart can rest on", which is what both
        `cut_set` and `cart_region` have always assumed it meant.
        """
        if not self.in_bounds(cell) or self.is_wall(cell):
            return False
        if self.portal is not None and cell == self.portal:
            return False
        if self.button is not None and cell == self.button:
            return False
        return True

    def can_stand(self, cell: Cell) -> bool:
        """Cells the cart could be standing on **when it issues a command**.

        Not the same question as `passable`, which asks where the cart can come
        to *rest*, and the difference is load bearing. `passable` excludes the
        button because `step` never returns it -- but the cart can *start* there,
        and a `portal_dest` can put it there, and from there it can issue a
        command like any other.

        This distinction was learned the expensive way. When `passable` began
        excluding the button, `row_col_deltas` -- which had been using it to ask
        this question -- stopped counting the teleport jump out of a button cell.
        On a board where the cart starts on the button and the button is the
        portal's only entry, the jump's row delta vanished, `cart_row` looked
        monotone, and a certificate for a level solvable in ONE command was paid
        2.0 of 2.0. An adversarial review of this run's own fix found it.
        Deliberately generous: extra entry cells can only add displacements, and
        more displacements make monotonicity harder to prove, so erring wide
        refuses certificates rather than accepting false ones. D-EX-027.
        """
        return self.in_bounds(cell) and not self.is_wall(cell)

    def cells(self) -> Iterable[Cell]:
        for r in range(self.height):
            for c in range(self.width):
                yield (r, c)

    # -- dynamics ---------------------------------------------------------
    def step(self, cart: Cell, pressed: bool, action: str) -> Tuple[Cell, bool]:
        """One world action, one successor.  A2's semantics, verbatim:
        the button press and the door opening happen in the same transition and
        the cart does not move; the teleport fires on entry."""
        dr, dc = DELTA[action]
        target = (cart[0] + dr, cart[1] + dc)
        if not self.in_bounds(target) or self.is_wall(target):
            return cart, pressed
        if self.button is not None and target == self.button:
            return cart, True
        if self.door is not None and target == self.door:
            if not pressed:
                return cart, pressed
            return target, pressed
        if self.portal is not None and target == self.portal:
            return (self.portal_dest or target), pressed
        return target, pressed

    def is_win(self, cart: Cell, latched: int) -> bool:
        if cart != self.goal:
            return False
        if self.require_all_switches and self.switches:
            full = (1 << len(self.switches)) - 1
            if latched != full:
                return False
        # The level awards one point on victory; `win_tighten` raises the bar.
        return 1 >= self.win_score_required

    # -- well-formedness --------------------------------------------------
    def wellformed_problems(self) -> List[str]:
        """Ways this level's fields describe a world `step` will model wrongly.

        Not called from the marker: a rubric must mark whatever it is handed,
        and refusing to mark a malformed level would turn a builder's mistake
        into an examinee's zero.  It is called from the *builder*'s self-check,
        where a malformed level is caught before anyone sits the paper.

        Every entry here is a shape that produced an accepted-but-false
        certificate before `_neighbours` was made to delegate to `step`.  The
        delegation is what makes the checker sound; this is the second line, and
        it is the one that will matter in Phase 4, when a level is transcribed
        from a sealed game rather than written here.  `_level()` in the paper
        builder defaults `portal_dest` to `None`, so "portal set, destination
        forgotten" is inside the level shape rather than outside it.
        """
        problems: List[str] = []
        if self.portal is not None:
            if self.portal_dest is None:
                problems.append(
                    "portal is set at %s but portal_dest is None; `step` then "
                    "returns the portal cell itself, so the cart rests on P -- "
                    "which the board's legend says never happens"
                    % (list(self.portal),))
            else:
                if not self.in_bounds(self.portal_dest):
                    problems.append("portal_dest %s is off the board"
                                    % (list(self.portal_dest),))
                elif self.is_wall(self.portal_dest):
                    problems.append(
                        "portal_dest %s is a wall cell; `step` parks the cart "
                        "inside the wall and lets it walk out again"
                        % (list(self.portal_dest),))
                if self.portal_dest == self.portal:
                    problems.append("portal_dest is the portal cell itself")
            if self.door is not None and self.door == self.portal:
                problems.append(
                    "door and portal are the same cell %s; `step` tests the "
                    "door first and the portal never fires, so any reader of "
                    "the two fields models a different world"
                    % (list(self.portal),))
            if self.portal == self.start:
                problems.append("the cart starts on the portal cell")
            if self.button is not None and self.portal_dest == self.button:
                problems.append(
                    "portal_dest is the button cell; the teleport parks the "
                    "cart somewhere `step` will never return it to, so where "
                    "the cart can rest and where it can stand come apart")
        if self.button is not None and self.button == self.door:
            problems.append("button and door are the same cell; the button "
                            "branch of `step` wins and the door never opens")
        if self.button is not None and self.button == self.start:
            # Found by an adversarial review of this run's own fix: the cart can
            # be standing on the button even though `step` never returns it
            # there, and one caller was reading `passable` as though it could
            # not. Legal in the world; refused here because every argument in
            # this module about where the cart can be gets harder to state.
            problems.append(
                "the cart starts on the button cell %s; `step` never returns "
                "the cart there, so the level's own start is a cell the "
                "movement graph does not contain" % (list(self.button),))
        if len(set(self.switches)) != len(self.switches):
            # `switch_index` is a dict, so duplicates collapse to one bit, while
            # anything counting `switches` as a list over-counts. It makes the
            # 2^m bound claim more states than the level has.
            problems.append(
                "the switch list repeats a cell; `switch_index` collapses "
                "duplicates to one latch bit, so any count taken over the list "
                "is larger than the number of distinct latch states")
        if not self.in_bounds(self.start) or self.is_wall(self.start):
            problems.append("the start cell %s is not a floor cell"
                            % (list(self.start),))
        if not self.in_bounds(self.goal) or self.is_wall(self.goal):
            problems.append("the goal cell %s is not a floor cell"
                            % (list(self.goal),))
        return problems


def _cell(value: Any) -> Cell:
    return (int(value[0]), int(value[1]))


def _opt_cell(value: Any) -> Optional[Cell]:
    return None if value is None else _cell(value)


def load_level(truth: Dict[str, Any]) -> Level:
    return Level(json.loads(truth["level_blob"]))


# ------------------------------------------------------------------ replay

def replay(level: Level, commands: Sequence[Any]) -> Dict[str, Any]:
    """Drive the level with an arm's command sequence.

    Every wrapper operator is honoured in the order the proxy honours it
    (`proxy.variants.VariantRuntime`): a forbidden command is never forwarded,
    the step limit is counted over forwarded commands, the hazard fires on the
    frame the arm observes after a command.  A witness that only works because
    the replay is laxer than the proxy is not a witness.
    """
    if not isinstance(commands, (list, tuple)):
        return {"win": False, "status": "witness_is_not_a_list", "used": 0}
    if len(commands) > MAX_WITNESS:
        return {"win": False, "status": "witness_over_cap", "used": len(commands)}

    cart = level.start
    pressed = False
    latched = 0
    if cart in level.switch_index:
        latched |= 1 << level.switch_index[cart]
    if cart in level.lost_cells:
        return {"win": False, "status": "hazard_at_start", "used": 0}

    used = 0
    for command in commands:
        if not isinstance(command, str) or command not in ACTIONS:
            return {"win": False, "status": "unknown_command", "used": used}
        if command in level.forbidden:
            return {"win": False, "status": "forbidden_command", "used": used}
        used += 1
        if level.step_limit is not None and used > level.step_limit:
            return {"win": False, "status": "over_step_limit", "used": used}
        cart, pressed = level.step(cart, pressed, level.world_action(command))
        if cart in level.switch_index:
            latched |= 1 << level.switch_index[cart]
        if cart in level.lost_cells:
            return {"win": False, "status": "hazard", "used": used}
        if level.is_win(cart, latched):
            return {"win": True, "status": "win", "used": used}
    return {"win": level.is_win(cart, latched),
            "status": "exhausted" if not level.is_win(cart, latched) else "win",
            "used": used}


# --------------------------------------------------- the relaxed graph

def _neighbours(level: Level, cell: Cell, actions: Iterable[str]) -> Iterable[Cell]:
    """Where one command can put the cart, **asked of `Level.step` itself**.

    This used to be a second implementation of the transition function, and the
    two drifted in the way second implementations do.  `step` sends the cart to
    ``portal_dest or target`` with no check that the destination exists or is
    passable; this function dropped the edge whenever `portal_dest` was absent
    or unwalkable.  `step` tests the door *before* the portal; this function had
    no door branch at all.  Wherever they disagreed, `step` moved the cart and
    the graph did not -- so `relaxed_edges` was not an over-approximation, and a
    `cart_region` or `cut_set` certificate for a **solvable** level was accepted
    and paid in full.  Three reproductions are in this run's
    `verify_checker_claims.py`; the cheapest needs no malformed field at all,
    only a cell that is both the door and the portal.

    An over-approximating graph that fails *closed* is not an over-approximation.
    So there is now one transition function and this asks it.  `pressed=True` is
    the only relaxation left, and it is the intended one: the door is treated as
    already open, which can only add edges.
    """
    for action in actions:
        target, _ = level.step(cell, True, action)
        if target == cell:
            continue                    # blocked move, or a button press
        yield target


def relaxed_edges(level: Level, *, blocked: frozenset = frozenset()) -> Dict[Cell, Set[Cell]]:
    """Undirected over-approximation of the cart's movement.

    Undirected on purpose.  The real move relation is directed once an action is
    forbidden, and directed reachability is the thing we would have to compute
    to be exact -- but exactness is not what a soundness argument needs.  Taking
    the undirected closure only adds edges, so a separation in this graph is a
    separation in the real one.  The converse fails, and that asymmetry is the
    price of a certificate that costs O(cells x actions) instead of O(states).

    The node set is a **closure**, not a filter.  Seeding from the passable cells
    and then following `step` means a cell the transition function can actually
    reach is in the graph even when `passable()` would have refused it -- a
    teleport destination inside a wall, say.  Filtering the successors instead
    was the shape of the unsoundness described on `_neighbours`: a cell the cart
    can stand on but the graph does not know about is a cell no certificate can
    be refused on account of.
    """
    actions = level.effective_actions()
    graph: Dict[Cell, Set[Cell]] = {}
    stack: List[Cell] = []
    for cell in level.cells():
        if level.passable(cell) and cell not in blocked:
            graph[cell] = set()
            stack.append(cell)
    while stack:
        cell = stack.pop()
        for nxt in _neighbours(level, cell, actions):
            if nxt in blocked:
                continue
            if nxt not in graph:
                graph[nxt] = set()
                stack.append(nxt)
            graph[cell].add(nxt)
            graph[nxt].add(cell)
    return graph


def components(graph: Dict[Cell, Set[Cell]]) -> Dict[Cell, Cell]:
    """cell -> its component's canonical representative (the smallest cell).

    Row-major smallest, so the naming is a fact about the board rather than a
    convention only we know.  An examinee can name the same component we do.
    """
    rep: Dict[Cell, Cell] = {}
    for cell in sorted(graph):
        if cell in rep:
            continue
        seen = {cell}
        queue = deque([cell])
        while queue:
            here = queue.popleft()
            for nxt in graph.get(here, ()):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        canonical_rep = min(seen)
        for member in seen:
            rep[member] = canonical_rep
    return rep


def relaxed_distance(level: Level, src: Cell, dst: Cell) -> Optional[int]:
    """Shortest path in the over-approximating graph = a lower bound on
    commands, because one command moves the cart at most one edge (a teleport
    jump is one edge; a blocked move and a button press are zero)."""
    graph = relaxed_edges(level)
    if src not in graph:
        return None
    if src == dst:
        return 0
    seen = {src}
    queue = deque([(src, 0)])
    while queue:
        here, d = queue.popleft()
        for nxt in graph.get(here, ()):
            if nxt in seen:
                continue
            if nxt == dst:
                return d + 1
            seen.add(nxt)
            queue.append((nxt, d + 1))
    return None


def row_col_deltas(level: Level) -> Tuple[Set[int], Set[int]]:
    """Every (row, col) displacement a single command can produce.

    Blocked moves and the button press contribute 0.  A teleport contributes the
    jump from each cell that can enter it.  This is the whole closure argument
    for `cart_row` / `cart_col`, and it is O(actions + board) -- which is what
    makes the certificate usable on a level with 2^120 states.
    """
    rows: Set[int] = {0}
    cols: Set[int] = {0}
    actions = level.effective_actions()
    for action in actions:
        dr, dc = DELTA[action]
        rows.add(dr)
        cols.add(dc)
    if level.portal is not None and level.portal_dest is not None:
        for action in actions:
            dr, dc = DELTA[action]
            entry = (level.portal[0] - dr, level.portal[1] - dc)
            # `can_stand`, not `passable`: the question is where the cart can be
            # when it issues the command, which includes the button. D-EX-027.
            if level.can_stand(entry):
                rows.add(level.portal_dest[0] - entry[0])
                cols.add(level.portal_dest[1] - entry[1])
    return rows, cols


# ------------------------------------------------------- the certificate

def check_certificate(cert: Any, level: Level) -> Dict[str, Any]:
    """Verify a submitted certificate against the level.  Refuse everything else.

    Returns `{"ok": bool, "why": str, "kind": str|None}`.  `ok` is only ever
    True when this function has re-derived the claim from the board; nothing the
    examinee wrote is taken on trust, including the numbers it wrote about its
    own invariant.
    """
    if not isinstance(cert, dict):
        return _no(None, "a certificate must be a JSON object, got %s"
                   % type(cert).__name__)
    kind = cert.get("kind")
    if kind not in CERT_KINDS:
        return _no(None, "kind %r is outside the closed grammar %s"
                   % (kind, list(CERT_KINDS)))
    keys = frozenset(cert)
    if keys != _CERT_KEYS[kind]:
        missing = sorted(_CERT_KEYS[kind] - keys)
        extra = sorted(keys - _CERT_KEYS[kind])
        return _no(kind, "key set is wrong: missing %s, unexpected %s. The "
                         "grammar is closed; a field we do not check is a field "
                         "that could say anything." % (missing, extra))
    if kind == "invariant":
        return _check_invariant(cert, level)
    if kind == "cut_set":
        return _check_cut_set(cert, level)
    return _check_counting(cert, level)


def _no(kind: Optional[str], why: str) -> Dict[str, Any]:
    return {"ok": False, "kind": kind, "why": why}


def _yes(kind: str, why: str) -> Dict[str, Any]:
    return {"ok": True, "kind": kind, "why": why}


def _check_invariant(cert: Dict[str, Any], level: Level) -> Dict[str, Any]:
    name = cert.get("invariant")
    if name not in INVARIANT_NAMES:
        return _no("invariant", "no invariant named %r; the closed set is %s"
                   % (name, list(INVARIANT_NAMES)))

    if name in ("cart_row", "cart_col"):
        axis = 0 if name == "cart_row" else 1
        rows, cols = row_col_deltas(level)
        deltas = rows if axis == 0 else cols
        init = level.start[axis]
        goal = level.goal[axis]
        if not (isinstance(cert["initial_value"], int)
                and isinstance(cert["goal_value"], int)):
            return _no("invariant", "cart_row/cart_col values must be integers")
        if cert["initial_value"] != init or cert["goal_value"] != goal:
            return _no("invariant",
                       "the stated values do not match the board: start %s=%d, "
                       "goal %s=%d" % (name, init, name, goal))
        if max(deltas) <= 0:
            if goal > init:
                return _yes("invariant",
                            "every available command has %s delta <= 0 "
                            "(deltas %s), so %s never increases; the goal needs "
                            "%d > %d" % (name, sorted(deltas), name, goal, init))
            return _no("invariant",
                       "%s is non-increasing but the goal is not above the "
                       "start, so the invariant does not exclude it" % name)
        if min(deltas) >= 0:
            if goal < init:
                return _yes("invariant",
                            "every available command has %s delta >= 0 "
                            "(deltas %s), so %s never decreases; the goal needs "
                            "%d < %d" % (name, sorted(deltas), name, goal, init))
            return _no("invariant",
                       "%s is non-decreasing but the goal is not below the "
                       "start, so the invariant does not exclude it" % name)
        return _no("invariant",
                   "%s is not monotone under the available commands (deltas %s); "
                   "the quantity is not an invariant of this variant at all"
                   % (name, sorted(deltas)))

    # cart_region
    graph = relaxed_edges(level)
    rep = components(graph)
    start_rep = rep.get(level.start)
    goal_rep = rep.get(level.goal)
    if start_rep is None or goal_rep is None:
        return _no("invariant", "start or goal is not a passable cell of this "
                                "board; the certificate does not describe it")
    said_start = _maybe_cell(cert["initial_value"])
    said_goal = _maybe_cell(cert["goal_value"])
    if said_start is None or said_goal is None:
        return _no("invariant", "cart_region values are component "
                                "representatives, written [row, col]")
    if said_start != start_rep or said_goal != goal_rep:
        return _no("invariant",
                   "the stated representatives are wrong: start's component is "
                   "%s, goal's is %s" % (list(start_rep), list(goal_rep)))
    if start_rep == goal_rep:
        return _no("invariant",
                   "start and goal are in the same component (%s), so this "
                   "invariant does not separate them" % list(start_rep))
    return _yes("invariant",
                "the cart's component is closed under every available command, "
                "start sits in %s and the goal in %s"
                % (list(start_rep), list(goal_rep)))


def _maybe_cell(value: Any) -> Optional[Cell]:
    if (isinstance(value, (list, tuple)) and len(value) == 2
            and all(isinstance(v, int) for v in value)):
        return (int(value[0]), int(value[1]))
    return None


def _check_cut_set(cert: Dict[str, Any], level: Level) -> Dict[str, Any]:
    cells = cert.get("cells")
    if not isinstance(cells, list) or not cells:
        return _no("cut_set", "cells must be a non-empty list of [row, col]")
    parsed: List[Cell] = []
    for entry in cells:
        cell = _maybe_cell(entry)
        if cell is None:
            return _no("cut_set", "every cut cell must be [row, col], got %r" % (entry,))
        parsed.append(cell)
    outside = [list(c) for c in parsed if c not in level.lost_cells]
    if outside:
        return _no("cut_set",
                   "%s are not declared hazards by this variant, so cutting "
                   "them is a claim about a different level" % outside)
    # The goal has to be a cell of this board *before* anything is cut, or the
    # separation is vacuous: `rep` would simply not contain it and the old code
    # read that absence as success. Any hazard at all then bought a full-marks
    # "cut set" that cut nothing -- which is how the door/portal reproduction in
    # this run's `verify_checker_claims.py` was paid 2.0 of 2.0.
    if level.goal in parsed:
        return _no("cut_set", "the goal cell is itself named as a cut cell; that "
                              "is a claim about the goal, not a separation")
    if level.goal not in components(relaxed_edges(level)):
        return _no("cut_set",
                   "the goal is not a cell this board's transition function "
                   "reaches at all, so removing %s is not the reason the level "
                   "is unsolvable -- the certificate names the wrong argument"
                   % [list(c) for c in parsed])

    graph = relaxed_edges(level, blocked=frozenset(parsed))
    rep = components(graph)
    if level.start not in rep:
        return _no("cut_set", "the start cell is itself cut; the argument is "
                              "degenerate rather than a separation")
    if level.goal in rep and rep[level.goal] == rep[level.start]:
        return _no("cut_set",
                   "removing %s does not separate the goal from the start"
                   % [list(c) for c in parsed])
    return _yes("cut_set",
                "every path from the start to the goal occupies one of %s, and "
                "each of those is a declared hazard"
                % [list(c) for c in parsed])


def _check_counting(cert: Dict[str, Any], level: Level) -> Dict[str, Any]:
    bound = cert.get("bound")
    limit = cert.get("limit")
    if not isinstance(bound, int) or not isinstance(limit, int):
        return _no("counting", "bound and limit must be integers")
    if level.step_limit is None:
        return _no("counting", "this variant has no step limit, so a counting "
                               "argument has nothing to count against")
    if limit != level.step_limit:
        return _no("counting", "the variant's step limit is %d, not %d"
                   % (level.step_limit, limit))
    lower = relaxed_distance(level, level.start, level.goal)
    if lower is None:
        return _no("counting", "the goal is not even reachable in the relaxed "
                               "graph; the counting argument is not the reason")
    if bound > lower:
        return _no("counting",
                   "%d is not a lower bound: the relaxed board admits a %d-command "
                   "path, and the relaxation only over-connects" % (bound, lower))
    if limit >= bound:
        return _no("counting",
                   "a budget of %d is not smaller than the claimed requirement "
                   "of %d, so nothing follows" % (limit, bound))
    return _yes("counting",
                "at least %d commands are needed (verified against a relaxation "
                "admitting %d) and the budget is %d" % (bound, lower, limit))


# ------------------------------------------------------------- enumeration

def enumerate_states(level: Level, cap: int = MAX_ENUMERATION) -> Dict[str, Any]:
    """Full forward enumeration in command space, capped.

    Only meaningful for class (i): the cap is what makes "exhaustive search is
    feasible here" a measured fact rather than an adjective.  The cap is
    recorded in the truth file next to the count, because a count that silently
    hit its cap is not an enumeration.
    """
    start = (level.start, False, _latched_at(level, 0, level.start))
    seen = {start}
    queue = deque([start])
    solved: Optional[List[str]] = None
    paths = {start: []}
    truncated = False
    while queue:
        cart, pressed, latched = queue.popleft()
        path = paths[(cart, pressed, latched)]
        for command in level.commands():
            if level.step_limit is not None and len(path) + 1 > level.step_limit:
                continue
            nxt_cart, nxt_pressed = level.step(cart, pressed, level.world_action(command))
            if nxt_cart in level.lost_cells:
                continue
            nxt = (nxt_cart, nxt_pressed, _latched_at(level, latched, nxt_cart))
            if nxt in seen:
                continue
            if len(seen) >= cap:
                truncated = True
                queue.clear()
                break
            seen.add(nxt)
            paths[nxt] = path + [command]
            if solved is None and level.is_win(nxt_cart, nxt[2]):
                solved = paths[nxt]
            queue.append(nxt)
    return {"states": len(seen), "cap": cap, "truncated": truncated,
            "solution": solved}


def _latched_at(level: Level, latched: int, cell: Cell) -> int:
    idx = level.switch_index.get(cell)
    return latched if idx is None else latched | (1 << idx)


# ------------------------------------------------------------- the marking

#: How the points split.  Half the item is the verdict, half is the reason --
#: which is the whole content of Theoria.md 1.11's class (i): "这里考的是理由".
VERDICT_WEIGHT = 0.5
JUSTIFICATION_WEIGHT = 0.5

#: What "I searched the whole space" is worth when it is true.  Non-zero because
#: it is a correct verdict honestly obtained; well under a certificate because
#: it does not transfer to the next level, which is the thing being bought.
SEARCH_CREDIT = 0.4

_SEARCH_REASONS = frozenset({"exhaustive_search", "searched_whole_space",
                             "enumeration", "complete_search"})
_ABSTAIN = frozenset({"abstain", "unknown", "unsure", "no_verdict"})


def _claim_of(answer: Any) -> Optional[str]:
    if isinstance(answer, str):
        return answer.strip().lower()
    if isinstance(answer, dict):
        claim = answer.get("claim")
        if isinstance(claim, str):
            return claim.strip().lower()
    return None


def grade_verdict(answer: Any, truth: Dict[str, Any], item: Item) -> ItemScore:
    """Score one verdict item: the call, then the reason for it.

    Pure in (answer, truth, item).  Everything the checker needs about the world
    is re-derived from `truth["level_blob"]`.
    """
    possible = item.points
    verdict_points = possible * VERDICT_WEIGHT
    reason_points = possible * JUSTIFICATION_WEIGHT
    said = _claim_of(answer)
    detail: Dict[str, Any] = {"said": said, "expected": truth["claim"],
                              "reason": "none"}

    if said is None:
        detail["why"] = ("no parseable claim; an answer is either a claim string "
                         "or an object with a `claim` field")
        return ItemScore(item.item_id, item.rubric_id, 0.0, possible, "wrong", detail)

    if said in _ABSTAIN:
        detail["said"] = "abstain"
        detail["why"] = ("abstained. Not scored as wrong -- a framework that "
                         "will say 'unsolvable' has to be able to say nothing -- "
                         "but not paid for either.")
        return ItemScore(item.item_id, item.rubric_id, 0.0, possible, "abstained", detail)

    correct = (said == truth["claim"])
    awarded = verdict_points if correct else 0.0
    detail["verdict_points"] = round(awarded, 6)

    if correct:
        level = load_level(truth)
        if said == "unsolvable":
            awarded += _score_unsolvable_reason(answer, truth, level, reason_points, detail)
        elif said == "solvable":
            awarded += _score_solvable_reason(answer, level, reason_points, detail)

    detail["reason_points"] = round(awarded - detail["verdict_points"], 6)
    return ItemScore(item.item_id, item.rubric_id, round(awarded, 6), possible,
                     "correct" if correct else "wrong", detail)


def _score_unsolvable_reason(answer: Any, truth: Dict[str, Any], level: Level,
                             reason_points: float, detail: Dict[str, Any]) -> float:
    cert = answer.get("certificate") if isinstance(answer, dict) else None
    if cert is not None:
        result = check_certificate(cert, level)
        detail["certificate"] = result
        if result["ok"]:
            detail["reason"] = "certificate"
            return reason_points
        detail["reason"] = "invalid_certificate"
        detail["why"] = ("the verdict is right and the certificate is not; only "
                         "the verdict is paid. " + result["why"])
        return 0.0

    reason = answer.get("reason") if isinstance(answer, dict) else None
    if isinstance(reason, str) and reason.strip().lower() in _SEARCH_REASONS:
        if truth.get("search_credible"):
            detail["reason"] = "search_exhaustion"
            detail["why"] = ("a correct verdict from a complete search. Paid at "
                             "%g of the reason, because it does not transfer to "
                             "the next level." % SEARCH_CREDIT)
            return reason_points * SEARCH_CREDIT
        detail["reason"] = "search_not_credible"
        # "beyond enumeration" and "a false statement about the search" were both
        # withdrawn by D-EX-028: every class (ii) item in this exam is settled by
        # an exhaustive computation over at most 600 nodes, so the
        # marker was calling a true claim false -- the exact failure D-EX-022
        # recorded once already, re-entering through this string after the field
        # underneath it was renamed. What is measured is narrower and is all this
        # may assert: the NAIVE forward enumeration, over the full (cart, button,
        # latch mask) state that class (i) is graded on, cannot terminate here.
        # The examinee is told what the level does not support rather than what it
        # did, because this text is the only account it gets of the zero.
        detail["why"] = ("the naive forward enumeration -- over the full (cart, "
                         "button, latch mask) state -- cannot terminate on this "
                         "level (%s), so 'I searched it all' is not a claim this "
                         "level supports. A cheaper complete method may well "
                         "exist; naming one is a certificate, not a search."
                         % truth.get("state_space", {}).get("arithmetic", "large"))
        return 0.0

    detail["reason"] = "none"
    detail["why"] = ("right verdict, no reason offered. Theoria.md 1.11: a "
                     "complete searcher can be right for a reason that does not "
                     "survive the next board.")
    return 0.0


def _score_solvable_reason(answer: Any, level: Level, reason_points: float,
                           detail: Dict[str, Any]) -> float:
    witness = answer.get("witness") if isinstance(answer, dict) else None
    if witness is None:
        detail["reason"] = "none"
        detail["why"] = ("right verdict, no witness plan. On a solvable level "
                         "the constructive answer is the plan; without it the "
                         "claim is indistinguishable from a guess.")
        return 0.0
    result = replay(level, witness)
    detail["witness_replay"] = result
    if result["win"]:
        detail["reason"] = "witness"
        return reason_points
    detail["reason"] = "invalid_witness"
    detail["why"] = ("the verdict is right and the plan does not win (%s); only "
                     "the verdict is paid." % result["status"])
    return 0.0


RUBRICS: Tuple[Rubric, ...] = (
    Rubric(
        rubric_id="verdict.a2.claim_and_certificate",
        description=(
            "Half the points for the verdict, half for the reason. On an "
            "unsolvable level the reason is a certificate this rubric verifies "
            "against the board (full) or a credible exhaustive search (partial); "
            "on a solvable one it is a witness plan this rubric replays."),
        grade=grade_verdict,
    ),
)
