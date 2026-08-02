"""How many states does a verdict item actually have?

Class (ii) of the verdict paper is "large-space unsolvable", and until this
module existed the number that made it large was a **lower bound derived from a
construction** -- `subset_lower_bound`'s 2^m -- never a count.  That bound is
sound and it is checked (D-EX-021, D-EX-028, D-EX-029), but a bound is not a
census, and the sentence a reader takes away from the class name is a census
sentence: *this many states exist, so the naive method cannot walk them.*

Three questions get three different instruments here, and the point of the
module is that they are not the same question:

1. **How many states are there?**  `exact_count` answers it exactly, by symbolic
   reachability -- positions enumerated explicitly, latch masks carried as a
   binary decision diagram -- for any level whose latch state is the only thing
   that explodes and whose play is unbudgeted.  No enumeration, no
   extrapolation, no closed form fitted to a family: the count is computed on
   the shipped board.
2. **When the budget binds, what can still be said?**  `budgeted_bracket`
   returns a two-sided bracket, both sides computed: the lower side counts an
   explicitly constructed family of reachable states, the upper side counts the
   supersets admitted by a necessary condition on the step budget.  A bracket is
   weaker than a count and is labelled as one.
3. **Can an exhaustive computation settle the item anyway?**  A different
   question, and the answer for every shipped class (ii) item is *yes* -- see
   `positional_states` and D-EX-028.  Nothing here revises that.  A state space
   of 10^38 says the *naive* method cannot run; it says nothing about a method
   that quotients, and this module deliberately does not let the first number be
   read as an answer to the second.

Every method here is checked against `enumerate_states` -- the naive enumerator
the class is defined against -- on boards small enough for it to finish, across
every constructor and every wrapper operator the shipped items use.  A counter
that agrees with brute force nowhere is a counter with an opinion.
"""

from __future__ import annotations

import json
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

from exam.grading.rubrics_verdict import (
    ACTIONS, Level, _latched_at, enumerate_states,
)

Cell = Tuple[int, int]

#: A ceiling on the mask diagram, so that a level this method cannot handle
#: becomes a refusal with a reason rather than a MemoryError three hours in.
MAX_BDD_NODES = 2_000_000


# ============================================================ the BDD

class _Bdd:
    """A reduced ordered binary decision diagram over the latch mask.

    Small on purpose.  Three operations are needed and only three are here:
    disjunction (a position's mask family grows), "force this bit on" (the cart
    steps onto a switch), and model counting (the answer).

    Variables are switch indices in a fixed order, so two runs of the same level
    build the same diagram and the count is deterministic.
    """

    FALSE = 0
    TRUE = 1

    def __init__(self, nvars: int):
        self.nvars = nvars
        self._nodes: List[Optional[Tuple[int, int, int]]] = [None, None]
        self._unique: Dict[Tuple[int, int, int], int] = {}
        self._or_memo: Dict[Tuple[int, int], int] = {}
        self._exists_memo: Dict[Tuple[int, int], int] = {}
        self._and_memo: Dict[Tuple[int, int], int] = {}
        self._count_memo: Dict[int, int] = {}

    # -- construction -----------------------------------------------------
    def _var(self, node: int) -> int:
        """The variable a node tests; `nvars` for either terminal, so that the
        ordering comparisons below need no special cases."""
        return self.nvars if node < 2 else self._nodes[node][0]  # type: ignore[index]

    def _mk(self, var: int, low: int, high: int) -> int:
        if low == high:
            return low
        key = (var, low, high)
        node = self._unique.get(key)
        if node is None:
            node = len(self._nodes)
            self._nodes.append(key)
            self._unique[key] = node
        return node

    def empty_set(self) -> int:
        """The family {the empty mask}: every variable false."""
        node = self.TRUE
        for var in reversed(range(self.nvars)):
            node = self._mk(var, node, self.FALSE)
        return node

    def literal(self, var: int) -> int:
        """The family of masks containing `var`."""
        return self._mk(var, self.FALSE, self.TRUE)

    # -- operations -------------------------------------------------------
    def or_(self, a: int, b: int) -> int:
        if a == self.TRUE or b == self.TRUE:
            return self.TRUE
        if a == self.FALSE:
            return b
        if b == self.FALSE:
            return a
        if a == b:
            return a
        key = (a, b) if a <= b else (b, a)
        hit = self._or_memo.get(key)
        if hit is not None:
            return hit
        top = min(self._var(a), self._var(b))
        lo = self.or_(self._cofactor(a, top, False), self._cofactor(b, top, False))
        hi = self.or_(self._cofactor(a, top, True), self._cofactor(b, top, True))
        out = self._mk(top, lo, hi)
        self._or_memo[key] = out
        return out

    def and_(self, a: int, b: int) -> int:
        if a == self.FALSE or b == self.FALSE:
            return self.FALSE
        if a == self.TRUE:
            return b
        if b == self.TRUE:
            return a
        if a == b:
            return a
        key = (a, b) if a <= b else (b, a)
        hit = self._and_memo.get(key)
        if hit is not None:
            return hit
        top = min(self._var(a), self._var(b))
        lo = self.and_(self._cofactor(a, top, False), self._cofactor(b, top, False))
        hi = self.and_(self._cofactor(a, top, True), self._cofactor(b, top, True))
        out = self._mk(top, lo, hi)
        self._and_memo[key] = out
        return out

    def _cofactor(self, node: int, var: int, value: bool) -> int:
        if self._var(node) != var:
            return node
        _v, low, high = self._nodes[node]  # type: ignore[misc]
        return high if value else low

    def exists(self, node: int, var: int) -> int:
        """Existentially quantify `var` away: {T \\ {var} and T | {var} : T}."""
        if node < 2:
            return node
        key = (node, var)
        hit = self._exists_memo.get(key)
        if hit is not None:
            return hit
        top, low, high = self._nodes[node]  # type: ignore[misc]
        if top > var:
            out = node
        elif top == var:
            out = self.or_(low, high)
        else:
            out = self._mk(top, self.exists(low, var), self.exists(high, var))
        self._exists_memo[key] = out
        return out

    def force_on(self, node: int, var: int) -> int:
        """{T | {var} : T in `node`} -- the cart stepped onto switch `var`.

        As a Boolean function that is `x_var and (exists x_var . f)`: forget what
        the mask said about this switch, then insist it is latched.
        """
        return self.and_(self.exists(node, var), self.literal(var))

    def relax(self, node: int, var: int) -> int:
        """{T, T | {var} : T in `node`} -- `var` may be latched or not, freely.

        `exists` alone, which is the same thing said the other way round: a
        switch the cart can dip into and step back off carries no constraint.
        """
        return self.exists(node, var)

    # -- counting ---------------------------------------------------------
    def count(self, node: int) -> int:
        """Exact number of masks in the family, over all `nvars` variables."""
        if node == self.FALSE:
            return 0
        return (2 ** self._var(node)) * self._count_below(node)

    def _count_below(self, node: int) -> int:
        """Models of `node` over the variables from `_var(node)` onward."""
        if node == self.FALSE:
            return 0
        if node == self.TRUE:
            return 1
        hit = self._count_memo.get(node)
        if hit is not None:
            return hit
        var, low, high = self._nodes[node]  # type: ignore[misc]
        total = 0
        for child in (low, high):
            skipped = self._var(child) - var - 1
            total += (2 ** skipped) * self._count_below(child)
        self._count_memo[node] = total
        return total

    def size(self) -> int:
        return len(self._nodes) - 2


# ================================================== exact symbolic census

def naive_reach(level: Level, cap: int) -> Dict[str, Any]:
    """The naive enumeration, counted rather than recorded.

    Same semantics as `enumerate_states` and the same transition function --
    `Level.step`, asked directly, because D-EX-020 is what happens when a second
    implementation of it appears.  What is dropped is the bookkeeping:
    `enumerate_states` keeps a shortest command sequence for every state it
    meets, which is what makes it useful for witnesses and what makes it cost
    around 473 bytes a state.  At a ceiling of 200,000 states that is enough to
    exhaust this machine when several boards are walked in one process, and the
    census walks seventeen.

    The step budget is honoured by expanding in layers, so a state's depth is
    its shortest length exactly as `paths` made it -- the budget is respected
    without storing the path that proves it.

    `test_the_counting_probe_matches_the_recording_one` requires the two to
    return the same count and the same truncation flag on every board small
    enough for both, which is the only thing that makes dropping the bookkeeping
    safe rather than convenient.
    """
    start = (level.start, False, _latched_at(level, 0, level.start))
    seen = {start}
    frontier = [start]
    depth = 0
    truncated = False
    while frontier and not truncated:
        if level.step_limit is not None and depth >= level.step_limit:
            break
        nxt: List[Any] = []
        for cart, pressed, latched in frontier:
            for command in level.commands():
                moved, moved_pressed = level.step(
                    cart, pressed, level.world_action(command))
                if moved in level.lost_cells:
                    continue
                state = (moved, moved_pressed, _latched_at(level, latched, moved))
                if state in seen:
                    continue
                if len(seen) >= cap:
                    truncated = True
                    break
                seen.add(state)
                nxt.append(state)
            if truncated:
                break
        frontier = nxt
        depth += 1
    return {"states": len(seen), "cap": cap, "truncated": truncated}


class UncountableHere(Exception):
    """This module refuses to count this level, and says which premise failed.

    A refusal, never a fallback.  The whole value of the number is that the
    method was applicable; a counter that guesses when it is out of its depth is
    worse than no counter, because the guess is indistinguishable from a count.
    """


def reachable_positions(level: Level) -> Dict[Cell, None]:
    """Cells the cart can occupy, latches ignored, hazards and budget honoured
    only where they are unconditional.

    Latches gate nothing about geometry on any level this module accepts (that
    is `_require_latch_free_geometry`), so the position set is exactly the
    projection of the reachable state set.
    """
    start = level.start
    seen: Dict[Cell, None] = {start: None}
    frontier = [start]
    while frontier:
        nxt: List[Cell] = []
        for cell in frontier:
            for command in level.commands():
                moved, _pressed = level.step(cell, False, level.world_action(command))
                if moved in level.lost_cells or moved in seen:
                    continue
                seen[moved] = None
                nxt.append(moved)
        frontier = nxt
    return seen


def _require_latch_free_geometry(level: Level) -> None:
    """The premise the whole module rests on, checked rather than assumed.

    If the level has a button, a door or a portal then the cart's *position*
    graph depends on state the position enumeration above does not carry, and
    every count here would be over a graph the level does not have.  Refuse.
    """
    problems = []
    if level.button is not None:
        problems.append("a button, so `pressed` is part of the state")
    if level.door is not None:
        problems.append("a door, so an edge exists only once the button is pressed")
    if level.portal is not None or level.portal_dest is not None:
        problems.append("a teleport, so `step` is not a unit displacement")
    if problems:
        raise UncountableHere(
            "%s has %s; this module counts levels whose only state beyond the "
            "cart's cell is the latch mask" % (level.level_id, " and ".join(problems)))


def column_major(cell: Cell) -> Tuple[int, int]:
    """The variable order the census uses.  Named so a test can pass the other
    one and show that the count does not move -- see `exact_count`'s note on why
    the order is load bearing for size and inert for the answer."""
    return (cell[1], cell[0])


def row_major(cell: Cell) -> Tuple[int, int]:
    """The order that exhausted this machine's memory on the shipped boards."""
    return (cell[0], cell[1])


def exact_count(level: Level, order_key=column_major) -> Dict[str, Any]:
    """The exact number of reachable `(cart, pressed, latch mask)` states.

    Symbolic in the mask and explicit in the position: the reachable set is
    stored as one BDD per cell, the transition relation is `Level.step` itself
    (not a second implementation of it -- D-EX-020 is what happens when there
    are two), and the fixpoint is the same least fixpoint `enumerate_states`
    computes, taken over sets instead of over elements.

    Refuses a level with a step budget: with a budget the reachable set is not
    the least fixpoint of the transition relation, it is the union of the first
    `step_limit` images, and the mask families stop being cheap.  `budgeted_
    bracket` is that case, and it returns a bracket rather than a count because
    a bracket is what it can honestly return.
    """
    _require_latch_free_geometry(level)
    if level.step_limit is not None:
        raise UncountableHere(
            "%s carries a step budget of %d; the exact count is not the least "
            "fixpoint of the transition relation and this method does not apply"
            % (level.level_id, level.step_limit))

    positions = reachable_positions(level)
    switches = [cell for cell in level.switches if cell in positions]
    # A switch the cart can never stand on can never be latched, so it is not a
    # variable.  Including it would multiply the count by 2 per phantom switch.
    #
    # Column-major, and the order is load bearing rather than cosmetic. Under
    # the natural (row, column) order the two alcoves of one column sit 60
    # variables apart, and every intermediate family the fixpoint passes through
    # -- "the masks reachable in at most t commands", which is a knapsack -- needs
    # a diagram quadratic in that separation. Row-major exhausted this machine's
    # memory on the shipped k=60 boards; column-major finishes them in under a
    # second. Neither order changes the answer, only whether there is one.
    order = {cell: i for i, cell in enumerate(sorted(set(switches), key=order_key))}
    bdd = _Bdd(len(order))

    # The dip closure, and it is what makes the fixpoint affordable.
    #
    # A switch the cart can step onto and step straight back off, returning to
    # the cell it left, is a switch whose latch bit is free at that cell: every
    # mask reachable there is reachable with the bit either way. Applying that
    # up front lands on the saturated family directly, instead of climbing to it
    # through every "reachable within t commands" family in between -- which is
    # the sequence that blows the diagram up, and which contributes nothing,
    # since this level has no step budget for those families to mean anything
    # against. Sound because a dip is a real pair of commands: relaxation only
    # ever adds states the level actually has.
    dips: Dict[Cell, List[int]] = {}
    for cell in positions:
        free: List[int] = []
        for command in level.commands():
            moved, _pressed = level.step(cell, False, level.world_action(command))
            if moved == cell or moved not in order or moved in level.lost_cells:
                continue
            for back in level.commands():
                returned, _p = level.step(moved, False, level.world_action(back))
                if returned == cell:
                    free.append(order[moved])
                    break
        dips[cell] = sorted(set(free))

    def saturate(cell: Cell, family: int) -> int:
        for var in dips[cell]:
            family = bdd.relax(family, var)
        return family

    families: Dict[Cell, int] = {cell: _Bdd.FALSE for cell in positions}
    start_family = bdd.empty_set()
    if level.start in order:
        start_family = bdd.force_on(start_family, order[level.start])
    families[level.start] = saturate(level.start, start_family)

    worklist = deque([level.start])
    queued = {level.start}
    while worklist:
        cell = worklist.popleft()
        queued.discard(cell)
        family = families[cell]
        for command in level.commands():
            moved, _pressed = level.step(cell, False, level.world_action(command))
            if moved in level.lost_cells:
                continue
            image = family
            if moved in order:
                image = bdd.force_on(image, order[moved])
            merged = saturate(moved, bdd.or_(families[moved], image))
            if merged != families[moved]:
                families[moved] = merged
                if moved not in queued:
                    queued.add(moved)
                    worklist.append(moved)
        if bdd.size() > MAX_BDD_NODES:
            raise UncountableHere(
                "%s: the mask diagram passed %d nodes before the fixpoint "
                "closed; this method refuses rather than swap"
                % (level.level_id, MAX_BDD_NODES))

    total = sum(bdd.count(node) for node in families.values())
    return {
        "states": total,
        "positions": len(positions),
        "latch_variables": len(order),
        "bdd_nodes": bdd.size(),
        "method": "symbolic-reachability",
        "method_note": (
            "exact. Positions enumerated explicitly (%d of them), latch masks "
            "carried as a reduced ordered BDD over the %d switches the cart can "
            "reach, transition relation taken from `Level.step` itself. The "
            "fixpoint is the one `enumerate_states` computes, over sets instead "
            "of elements, so the two agree wherever the enumerator can finish "
            "-- which is what `test_symbolic_census_agrees_with_brute_force` "
            "measures." % (len(positions), len(order))),
    }


# ============================================ the budgeted comb, bracketed

def _comb_shape(level: Level) -> Dict[str, Any]:
    """Is this the open comb -- one corridor, a latching alcove above and below
    every column -- and nothing else?

    A positive whitelist.  The bracket below reasons about *this* board and no
    other: three rows, the middle one switch-free, the outer two entirely
    switches, walls around, all four actions live, no hazards.  Anything else
    raises, because the necessary condition the upper bound is built from is a
    statement about this geometry.
    """
    if level.height != 5:
        raise UncountableHere("%s is %d rows; the comb bracket wants 5"
                              % (level.level_id, level.height))
    if level.lost_cells:
        raise UncountableHere("%s declares hazards; the bracket does not model them"
                              % level.level_id)
    if set(level.commands()) != set(ACTIONS) or level.remap:
        raise UncountableHere(
            "%s does not offer all four unremapped actions (commands=%s remap=%s); "
            "the bracket's walk costs assume it"
            % (level.level_id, list(level.commands()), level.remap))
    corridor_len = level.width - 2
    for row in (0, 4):
        if level.rows[row] != "#" * level.width:
            raise UncountableHere("%s row %d is not solid border" % (level.level_id, row))
    for row in (1, 3):
        expected = set(range(1, corridor_len + 1))
        got = {c for c in range(level.width) if (row, c) in level.switch_index}
        if got != expected:
            raise UncountableHere(
                "%s row %d does not carry a switch in every corridor column"
                % (level.level_id, row))
        if level.rows[row][0] != "#" or level.rows[row][-1] != "#":
            raise UncountableHere("%s row %d is not walled at both ends"
                                  % (level.level_id, row))
    for col in range(1, corridor_len + 1):
        if (2, col) in level.switch_index:
            raise UncountableHere(
                "%s corridor cell (2,%d) is itself a switch; the bracket's walk "
                "costs assume the corridor latches nothing" % (level.level_id, col))
        if level.is_wall((2, col)):
            raise UncountableHere("%s corridor cell (2,%d) is wall"
                                  % (level.level_id, col))
    if level.start[0] != 2:
        raise UncountableHere("%s does not start in the corridor" % level.level_id)
    if len(level.switches) != 2 * corridor_len:
        raise UncountableHere(
            "%s carries %d switches against %d corridor columns; the bracket "
            "counts two per column"
            % (level.level_id, len(level.switches), corridor_len))
    return {"corridor_len": corridor_len, "start_col": level.start[1]}


def _binomials(n: int) -> List[int]:
    row = [1]
    for k in range(1, n + 1):
        row.append(row[-1] * (n - k + 1) // k)
    return row


def _bracket_lower(corridor_len: int, start_col: int, budget: int) -> Dict[str, Any]:
    """A count of states this board *demonstrably* has: one explicit strategy.

    From the start, walk right to column q, dipping into any chosen subset of
    the alcoves passed on the way -- two commands each, up and back down -- and
    stop.  Every (cell, mask) that strategy produces is reachable, distinct
    pairs are distinct states, and the arithmetic is a sum of binomials.  So this
    is a lower bound with no optimality argument anywhere in it, which is the
    only kind of bound worth having about a board nothing can search.

    The strategy walks rightward only, so it says nothing about the alcoves to
    the left of the start; the bound is loose by exactly that and by every walk
    that doubles back.  Loose is fine.  Wrong is not.
    """
    total = 0
    per_column: List[Tuple[int, int]] = []
    for col in range(start_col, corridor_len + 1):
        travel = col - start_col
        available = 2 * (col - start_col + 1)
        if travel > budget:
            break
        binom = _binomials(available)
        # Stopping in the corridor at (2, col): every dipped alcove costs 2.
        room = budget - travel
        corridor_states = sum(binom[j] for j in range(available + 1) if 2 * j <= room)
        # Stopping inside an alcove: the last one costs 1, not 2, and the mask
        # necessarily contains it.  Two alcoves per column, minus that one.
        alcove_binom = _binomials(available - 1)
        alcove_states = 0
        if travel + 1 <= budget:
            room_alcove = budget - travel - 1
            alcove_states = 2 * sum(alcove_binom[j] for j in range(available)
                                    if 2 * j <= room_alcove)
        total += corridor_states + alcove_states
        per_column.append((col, corridor_states + alcove_states))
    return {"lower": total, "widest_column": per_column[-1][0] if per_column else None}


def _run_polynomial(corridor_len: int, budget: int) -> List[List[int]]:
    """`table[m][r]` = subsets of the alcoves in columns 1..m whose rightmost
    occupied column is exactly m and which form `r` maximal runs in total.

    A run is a maximal block of consecutive columns latched in the same outer
    row.  It is the quantity the upper bound needs, because a run can be walked
    end to end inside its own row but can only be *entered* from the corridor,
    so every run costs at least one vertical command.
    """
    cap = budget + 1
    # state: (row1 occupied in previous column, row3 occupied in previous column)
    cur = {(False, False): [0] * (cap + 1)}
    cur[(False, False)][0] = 1          # the empty prefix, zero runs
    table: List[List[int]] = [[0] * (cap + 1) for _ in range(corridor_len + 1)]
    table[0][0] = 1                     # the empty subset
    for col in range(1, corridor_len + 1):
        nxt: Dict[Tuple[bool, bool], List[int]] = {}
        for (prev1, prev3), vec in cur.items():
            for now1 in (False, True):
                for now3 in (False, True):
                    added = (1 if (now1 and not prev1) else 0) \
                        + (1 if (now3 and not prev3) else 0)
                    slot = nxt.setdefault((now1, now3), [0] * (cap + 1))
                    for runs, count in enumerate(vec):
                        if not count:
                            continue
                        total = runs + added
                        if total > cap:
                            continue
                        slot[total] += count
        cur = nxt
        for (now1, now3), vec in cur.items():
            if now1 or now3:
                for runs, count in enumerate(vec):
                    table[col][runs] += count
    return table


def _bracket_upper(corridor_len: int, start_col: int, budget: int) -> Dict[str, Any]:
    """A count of every state the budget *could* admit: a necessary condition.

    Fix the cart's final cell, in column q, and let M be the rightmost column
    the walk had to touch -- the larger of q and the rightmost latched alcove.
    Then the walk pays, at minimum:

      * horizontal: `(M - start_col) + (M - q)` commands.  Column changes by at
        most one per command, the walk must reach M, and it must end at q.
      * vertical: one command per maximal run.  An outer row is enterable only
        from the corridor, and a run is bounded on both sides by columns the
        walk may not enter -- entering one would latch an alcove outside the
        mask, giving a different state.

    The two are disjoint (a command moves either along a row or between rows), so
    their sum is a lower bound on the walk's length, and any (cell, mask) whose
    sum exceeds the budget is unreachable.  Counting the pairs that survive is
    the same run-polynomial DP, read once per column.

    It is an over-count -- it drops the requirement that a mask contain the
    alcove the cart is standing in, and it never checks that the runs can be
    scheduled inside one out-and-back sweep.  Over-counting is the correct
    direction for an upper bound.
    """
    table = _run_polynomial(corridor_len, budget)
    cap = budget + 1
    prefix = [[0] * (cap + 1) for _ in range(corridor_len + 1)]
    for col in range(corridor_len + 1):
        for runs in range(cap + 1):
            prefix[col][runs] = (prefix[col - 1][runs] if col else 0) + table[col][runs]
    total = 0
    for q in range(1, corridor_len + 1):
        cells_in_column = 3          # (1,q), (2,q), (3,q)
        column_total = 0
        for m in range(q, corridor_len + 1):
            travel = (m - start_col) + (m - q)
            if travel < 0 or travel > budget:
                continue
            room = budget - travel
            source = prefix[q] if m == q else table[m]
            column_total += sum(source[r] for r in range(min(room, cap) + 1))
        total += cells_in_column * column_total
    return {"upper": total}


def budgeted_bracket(level: Level) -> Dict[str, Any]:
    """Both sides of the bracket, plus the gap, for a budgeted comb."""
    _require_latch_free_geometry(level)
    if level.step_limit is None:
        raise UncountableHere("%s has no step budget; count it exactly instead"
                              % level.level_id)
    shape = _comb_shape(level)
    low = _bracket_lower(shape["corridor_len"], shape["start_col"], level.step_limit)
    high = _bracket_upper(shape["corridor_len"], shape["start_col"], level.step_limit)
    return {
        "lower": low["lower"],
        "upper": high["upper"],
        "positions": len(reachable_positions(level)),
        "method": "budgeted-bracket",
        "method_note": (
            "not a count. Lower: an explicit rightward sweep that dips into any "
            "chosen subset of the alcoves it passes, two commands each -- every "
            "pair it produces is reachable, so the sum of binomials is a floor "
            "with no optimality argument in it. Upper: the walk must pay "
            "(M-start)+(M-q) horizontal commands to reach the rightmost touched "
            "column M and come back to the cart's column q, plus one vertical "
            "command per maximal run of latched alcoves, and those two counts "
            "are disjoint -- so any (cell, mask) whose sum exceeds the budget is "
            "unreachable, and the survivors are a ceiling. The true count lies "
            "between them and is not computed here."),
    }


# ================================================================= census

#: What a naive forward enumeration can actually finish on this hardware.  Not a
#: constant with a theory behind it -- `MAX_ENUMERATION` is the cap the papers
#: enforce, and this is the same order of magnitude.  Used only to turn a count
#: into the yes/no the class boundary is drawn on.
NAIVE_CEILING = 200_000


def census(level: Level) -> Dict[str, Any]:
    """One record per level: the count if there is one, the bracket if not, and
    the verdict on whether the naive method can run.

    Three instruments, tried in the order of how much they assume:

    1. **the naive enumerator itself**, under `NAIVE_CEILING`.  If it finishes,
       the count is exact and the class boundary answers itself -- the method
       the class is defined against demonstrably ran.  This is the only branch
       that reaches an item with a button, a door or a teleport, and it needs no
       structural premise at all.
    2. **symbolic reachability**, when enumeration ran out of room.  Exact, and
       it assumes only that the latch mask is the sole state beyond the cell.
    3. **the budgeted bracket**, when a step budget puts the reachable set out
       of reach of both.  Not a count, and the record says so.

    `naive_enumeration_feasible` is derived from the number, never asserted.  On
    a bracket it is derived from the *lower* side, which is the only side that
    can rule the naive method out.
    """
    enumerated = naive_reach(level, cap=NAIVE_CEILING)
    if not enumerated["truncated"]:
        record: Dict[str, Any] = {
            "states": enumerated["states"],
            "positions": len(reachable_positions(level)),
            "method": "enumeration",
            "method_note": (
                "exact. The naive forward enumeration over (cart, button, latch "
                "mask) terminated at %d states under a ceiling of %d, so the "
                "method class (ii) is defined against demonstrably runs here."
                % (enumerated["states"], NAIVE_CEILING)),
        }
    else:
        try:
            record = exact_count(level)
        except UncountableHere as exact_refusal:
            try:
                bracket = budgeted_bracket(level)
            except UncountableHere as bracket_refusal:
                # Neither exact method applies and the board is outside the
                # bracket's geometry.  What is left is the one number the run
                # above did establish: the enumerator reached the ceiling, so the
                # level has at least that many states.  A floor and no ceiling is
                # a poor census and is labelled as one -- but it is measured, and
                # it is enough to answer the only question the class boundary
                # asks.
                return {
                    "states": None,
                    "exact": None,
                    "lower": NAIVE_CEILING,
                    "upper": None,
                    "positions": len(reachable_positions(level)),
                    "method": "enumeration-truncated",
                    "method_note": (
                        "not a count, and not a bracket: only a floor. The naive "
                        "enumeration reached its ceiling of %d states without "
                        "closing, which establishes at least that many and "
                        "nothing more. Neither exact method applies here -- %s; "
                        "%s." % (NAIVE_CEILING, exact_refusal, bracket_refusal)),
                    "exact_refused_because": str(exact_refusal),
                    "bracket_refused_because": str(bracket_refusal),
                    "naive_enumeration_feasible": False,
                    "naive_ceiling": NAIVE_CEILING,
                    "enumeration_truncated_at": NAIVE_CEILING,
                }
            bracket["exact"] = None
            bracket["exact_refused_because"] = str(exact_refusal)
            bracket["naive_enumeration_feasible"] = bracket["lower"] <= NAIVE_CEILING
            bracket["naive_ceiling"] = NAIVE_CEILING
            bracket["enumeration_truncated_at"] = NAIVE_CEILING
            return bracket
        record["enumeration_truncated_at"] = NAIVE_CEILING
    record["exact"] = record["states"]
    record["lower"] = record["states"]
    record["upper"] = record["states"]
    record["naive_enumeration_feasible"] = record["states"] <= NAIVE_CEILING
    record["naive_ceiling"] = NAIVE_CEILING
    return record


#: Census results, keyed by the level's canonical JSON.
#:
#: Not an optimisation with a shrug attached: `build_papers` and `build_prereg`
#: rebuild the verdict paper many times per process, and the census costs about
#: a second and a half per large board -- most of it the naive enumeration that
#: has to run to the ceiling before it can report that it did.  Uncached, one
#: `build_prereg` took over ten minutes.  Safe because `census` is a pure
#: function of the level document: same board, same number, and the key is the
#: board itself rather than an id that two boards could share.
_CENSUS_CACHE: Dict[str, Dict[str, Any]] = {}


def census_of_doc(level_doc: Dict[str, Any]) -> Dict[str, Any]:
    """`census`, memoised on the level document, for the build path."""
    key = json.dumps(level_doc, sort_keys=True, separators=(",", ":"))
    hit = _CENSUS_CACHE.get(key)
    if hit is None:
        hit = census(Level(level_doc))
        _CENSUS_CACHE[key] = hit
    return dict(hit)


def brute_force_count(level: Level, cap: int = 5_000_000) -> Optional[int]:
    """The naive enumerator's own answer, or `None` when it hits the cap.

    Here so that every other method in this file has something to be wrong
    against.  It is `enumerate_states`, not a copy of it.
    """
    result = enumerate_states(level, cap=cap)
    return None if result["truncated"] else result["states"]
