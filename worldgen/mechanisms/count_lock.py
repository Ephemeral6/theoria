"""Count-lock — tokens are collected, and a lock opens once enough of them are.

Two kinds sharing one number.  A `token` is picked up by walking into it; a
`lock` is a tile that is solid until the number of tokens collected so far
reaches its own `k`, and passable from then on.

**The count is global to the world, not per lock.**  Several locks may read the
same total with different `k`, so one collection run opens them in `k` order and
a reader who has induced the counter has induced every lock at once.  That is
the whole reason the family is a counter and not a key-per-door: it is the
cheapest world in the catalogue whose state is a *quantity* rather than a set of
independent bits.

Semantics:

* the agent moves into an uncollected token — the token's state goes 0 → 1 and
  the agent takes its cell (`collect_token`).  A collected token is floor, so a
  later crossing of the same cell is an ordinary `walk` and not a rule of this
  family at all;
* the agent moves into a lock whose `k` is met — the agent walks onto it
  (`walk_through_lock`);
* the agent moves into a lock whose `k` is not met — nothing happens at all
  (`blocked_by_lock`).

**This family is irreversible by construction, and that is what it is for.**
Collection is monotone — nothing anywhere decreases a token's state — so
`collect_token` for a given token has exactly one witness in the whole reachable
graph and a lock that has opened never closes.  A0′
(`cold-start-a0/prime/A0P_REPORT.md` §1) is the measurement of what that costs:
its latched Button gave `press_left` one witness and no way to obtain a second,
capping what any amount of exploration could establish, while the toggle it was
compared against shipped a perfect manual on 47 % coverage.  This module supplies
that cost deliberately, as the counterweight to `color_cycle` and to a toggle
switch, so the generator can vary reversibility instead of assuming it.
"""

from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from ..core.spec import Entity, WorldSpec
from ..core.types import Cell, State
from .base import Ctx, Mechanism, Outcome, View, register


class CountLock(Mechanism):
    name = "count_lock"
    kinds = ("token", "lock")
    priority = 50

    # `mine` arrives as both kinds in spec order; the state slice covers the
    # tokens only, and a token's local index is its position among the tokens.
    @staticmethod
    def _tokens(mine: Tuple[Entity, ...]) -> Tuple[Entity, ...]:
        return tuple(e for e in mine if e.kind == "token")

    @staticmethod
    def _locks(mine: Tuple[Entity, ...]) -> Tuple[Entity, ...]:
        return tuple(e for e in mine if e.kind == "lock")

    @staticmethod
    def _threshold(lock: Entity) -> int:
        # A lock with no `k` is a lock that wants one token; a default of 0 would
        # make a mis-specified lock silently open, which is the worse failure.
        return int(lock.prop("k", 1))

    # ----------------------------------------------------------------- state
    def n_vars(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> int:
        return len(self._tokens(mine))

    def initial_vars(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> Tuple[int, ...]:
        return (0,) * len(self._tokens(mine))

    def _collected(self, view: View) -> int:
        return sum(1 for v in view.all() if v)

    def _uncollected_cells(self, mine: Tuple[Entity, ...], view: View) -> Tuple[Cell, ...]:
        return tuple(e.cell for i, e in enumerate(self._tokens(mine)) if not view.get(i))

    def _closed_cells(self, mine: Tuple[Entity, ...], view: View) -> Tuple[Cell, ...]:
        count = self._collected(view)
        return tuple(e.cell for e in self._locks(mine) if count < self._threshold(e))

    # --------------------------------------------------------------- queries
    def occupied(self, spec: WorldSpec, mine: Tuple[Entity, ...],
                 view: View) -> FrozenSet[Cell]:
        # Tokens are walked into, not around, so only closed locks are solid.
        return frozenset(self._closed_cells(mine, view))

    def reserved(self, spec: WorldSpec, mine: Tuple[Entity, ...],
                 view: View) -> FrozenSet[Cell]:
        """Uncollected tokens only.

        An agent deposited on an uncollected token by a fall or a teleport would
        stand on it without collecting it, so the count would disagree with the
        grid and the lock would stay shut with a token apparently already taken.
        Once collected the cell is plain floor and there is nothing left to skip,
        which is why this is computed from the view rather than inherited as the
        static default.  Open locks are floor too; closed ones are in `occupied`.
        """
        return frozenset(self._uncollected_cells(mine, view))

    # ------------------------------------------------------------- behaviour
    def interact(self, ctx: Ctx) -> Optional[Outcome]:
        tokens = self._tokens(ctx.mine)
        for index, token in enumerate(tokens):
            if token.cell != ctx.target:
                continue
            if ctx.view.get(index):
                return None            # already collected: floor, let it walk
            return Outcome(
                agent=ctx.target,
                writes=((ctx.view.abs(index), 1),),
                rule="collect_token",
            )

        count = self._collected(ctx.view)
        for lock in self._locks(ctx.mine):
            if lock.cell != ctx.target:
                continue
            if count < self._threshold(lock):
                return Outcome(agent=None, rule="blocked_by_lock")
            return Outcome(agent=ctx.target, rule="walk_through_lock")
        return None

    # --------------------------------------------------------------- drawing
    def render(self, spec: WorldSpec, mine: Tuple[Entity, ...], view: View,
               frame: List[List[int]]) -> None:
        uncollected = self._uncollected_cells(mine, view)
        if uncollected:
            color = spec.color("token")
            for r, c in uncollected:
                frame[r][c] = color
        # An open lock is not drawn at all — it renders as floor, exactly as the
        # A0′ Door does.  Its disappearance is the observable event, and the only
        # one: nothing else in the frame announces that the count reached `k`.
        closed = self._closed_cells(mine, view)
        if closed:
            color = spec.color("lock")
            for r, c in closed:
                frame[r][c] = color

    # -------------------------------------------------------------- the truth
    def truth_rules(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> List[Dict[str, Any]]:
        rules: List[Dict[str, Any]] = []
        if self._tokens(mine):
            rules.append(
                {"name": "collect_token",
                 "when": "act=D and the target cell holds an uncollected token",
                 "then": "that token becomes collected — it stops being drawn and "
                         "the global collected count rises by one — and the agent "
                         "takes its cell",
                 # Two axes, and conflating them is what made seven worlds ship
                 # a "disagreement" that was not one.  The *effect* is one-way: a
                 # collected token never comes back.  The *rule* is nonetheless
                 # re-witnessable whenever the world has more than one token,
                 # because each token is a fresh witness of the same rule — which
                 # is A0′'s criterion, and it is about evidence, not about undo.
                 # A0's Button was unwitnessable-again because there was exactly
                 # one of it; three tokens are three witnesses.
                 "reversible": False,
                 "re_witnessable": len(self._tokens(mine)) >= 2,
                 "why": "one witness per token, so the count is the number of "
                        "tokens — %d here" % len(self._tokens(mine))})
        if self._locks(mine):
            rules.extend([
                {"name": "walk_through_lock",
                 "when": "act=D and the target cell holds a lock whose k is at most "
                         "the global number of tokens collected so far — the count "
                         "is shared by every lock, not kept per lock",
                 "then": "the agent moves onto the lock's cell",
                 "reversible": True},
                {"name": "blocked_by_lock",
                 "when": "act=D and the target cell holds a lock whose k exceeds the "
                         "global number of tokens collected so far",
                 "then": "nothing changes",
                 "reversible": True},
            ])
        return rules

    def invariants(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> List[Dict[str, Any]]:
        tokens = self._tokens(mine)
        if not tokens:
            return []
        color = spec.color("token")

        def check(world, state, _color=color) -> bool:
            view = world.view(self, state)
            expected = sum(1 for v in view.all() if not v)
            frame = world.render(state)
            return sum(row.count(_color) for row in frame) == expected

        def collection_monotone(world, prev, _action, nxt) -> bool:
            before = world.view(self, prev)
            after = world.view(self, nxt)
            if self._collected(after) < self._collected(before):
                return False
            # Second clause of the same sentence: "so a lock that has opened
            # never closes again".  It follows from the first only if a lock's
            # threshold is fixed, which is a separate assumption; checking it
            # directly costs nothing and does not rely on that.
            was_closed = set(self._closed_cells(world.mine(self), before))
            now_closed = set(self._closed_cells(world.mine(self), after))
            return now_closed <= was_closed

        return [
            {"name": "token_count",
             "statement": "the number of cells showing colour %d equals the number "
                          "of tokens not yet collected" % color,
             "check": check},
            {"name": "collection_is_monotone",
             "statement": "the number of collected tokens never decreases, so a lock "
                          "that has opened never closes again",
             # A property of a *transition*, so `check` — handed one state at a
             # time — could not express it and was `None`.  That was honest; what
             # was not honest was `invariants_all_hold` reporting `true` anyway.
             # `edge_check` sees both endpoints, so the claim is now exercised
             # over the whole reachable graph instead of asserted.
             "edge_check": collection_monotone},
        ]

    def reversibility(self, spec: WorldSpec, mine: Tuple[Entity, ...]) -> List[Dict[str, Any]]:
        if not self._tokens(mine) and not self._locks(mine):
            return []
        return [
            {"note": "the reachable graph is a DAG in the token count: every "
                     "transition either holds it or raises it by one, so the world "
                     "has %d irreversible frontiers and an explorer that crosses "
                     "one cannot get back to sample the other side again"
                     % len(self._tokens(mine))},
            {"note": "blocked_by_lock is a no-op and so trivially re-witnessable "
                     "while it lasts, but its witnesses stop existing once the "
                     "count passes k — a rule can be reversible and still be lost"},
        ]


register(CountLock())
