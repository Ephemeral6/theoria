"""A worldgen world, presented through the protocol the environment proxy speaks.

Why this file exists, in one sentence: so the sealed drill can drive the **real**
`proxy.variants.VariantRuntime` instead of a second implementation of it.

Theoria.md Phase 1's 变体注入层 says the variant layer must not rewrite the game --
it rewrites commands and observations on the proxy, and the operator library is
therefore limited to the wrapper-legal set (`proxy.variants.LEGAL_OPERATORS`).
Phase 4 then freezes that library *before* any sealed game is opened.  A rehearsal
that reimplements the wrapper rehearses the reimplementation; the frozen artefact
goes untested and the first real use is still the first use.  So here the world is
adapted **up** to the proxy's body protocol -- ``{"state", "frame", "score"}`` --
and the frozen runtime is driven over it unmodified.

Two consequences follow, and both are load-bearing for what the drill can claim:

* every semantic decision (a forbidden command costs no step; `after` never runs
  on a refusal; `win_tighten` compares against `body["score"]`) comes from
  `proxy/variants.py` and `proxy/env_proxy.py:374-402`, not from this file;
* a worldgen world has **no score**.  `worldgen`'s recorded trace carries
  ``{t, frame, action, win}`` and nothing else, so `score` is `None` here.  That
  is faithful, not lazy, and the drill reports what the frozen `win_tighten` does
  with it rather than papering over it.

`RESET` is deliberately **not** in the command alphabet the oracle searches, and
the reason is narrower than it first looks.  The runtime treats RESET as "zero
the counters and clear `dead`" (`proxy/variants.py:190-193`), which does refill a
`step_limit` -- but `WorldSession.command` restarts the episode with it, so the
agent is returned to the start as well.  A budget shorter than the distance to
the goal is therefore *not* escapable by resetting, and the test that tries it is
in `exam/tests/test_sealed_drill.py`.  RESET is excluded because solvability here
is defined **within one episode**, which is the quantity a verdict question is
asking about; admitting it would silently change the question to "can the arm
ever win, given unlimited retries", which every solvable-at-all world answers
yes to.  The distinction is recorded because the first draft of this file argued
the wrong one.
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from proxy.variants import Refusal, Variant, VariantRuntime, _Remap  # noqa: E402
from worldgen.core.types import ACTIONS, State  # noqa: E402
from worldgen.core.world import GridWorld  # noqa: E402

#: The oracle refuses to answer rather than truncate.  A worldgen world has at
#: most 2654 reachable states (`t3-full-house`), and the composed space is that
#: times (step budget + 1) times the two values of `dead`, so this is roomy for
#: the catalogue and still small enough to fail fast on a mistake.
NODE_LIMIT = 400_000


class OracleTruncated(RuntimeError):
    """The composed search hit `NODE_LIMIT`.

    Raised rather than returned: a truncated exhaustive search that reports
    "unsolvable" is the exact failure `engine-rig`'s D-024 exists to forbid --
    "I did not find one" is not "there is none".
    """


class WorldSession:
    """One episode of one world, spoken as proxy response bodies.

    The body shape is the subset of the upstream schema the variant runtime
    actually reads: `state` (`NOT_FINISHED` / `WIN`), `frame` (a list of grids,
    last one live -- see `proxy/variants.py:_cells_hit`), and `score`.
    """

    def __init__(self, world: GridWorld):
        self.world = world
        self.state: State = world.initial()

    def body(self) -> Dict[str, Any]:
        return {
            "state": "WIN" if self.world.is_win(self.state) else "NOT_FINISHED",
            "frame": [self.world.render(self.state)],
            "score": None,          # worldgen keeps no score; see the module docstring
        }

    def command(self, action: str) -> Dict[str, Any]:
        # RESET restarts the episode rather than being an action of it. The
        # runtime already treats it as "zero the counters, clear dead"
        # (`proxy/variants.py:190-193`), so the world must match: a new episode
        # from the initial state. It is faithful, and it is *not* an escape
        # hatch from a `step_limit` -- the budget resets, but so does the
        # agent's position, so a goal further away than the budget stays out of
        # reach. `exam/tests/test_sealed_drill.py` pins that.
        if action == "RESET":
            self.state = self.world.initial()
        else:
            self.state = self.world.step(self.state, action)
        return self.body()


def _runtime_at(variant: Optional[Variant], commands: int, dead: bool,
                last_body: Optional[Dict[str, Any]]) -> VariantRuntime:
    """A runtime resumed at a known point of an episode.

    `VariantRuntime`'s own docstring states it "holds nothing but counters and
    the last observed body, both of which follow from the recorded action
    sequence -- so replaying the actions reproduces the variant's behaviour
    exactly".  Resuming from `(commands, dead, last_body)` is that sentence used
    forwards, and it is what lets the oracle search a graph instead of a tree.
    """
    runtime = VariantRuntime(variant)
    runtime.commands = commands
    runtime.dead = dead
    runtime.last_body = last_body
    return runtime


def apply_command(runtime: VariantRuntime, session: WorldSession,
                  command: str) -> Tuple[Dict[str, Any], bool, Any]:
    """One command through the wrapper, composed exactly as the proxy composes it.

    Mirrors `proxy/env_proxy.py:380-402`: `before` decides; a `Refusal` is
    answered from the wrapper and **never reaches the world**, so `after` does
    not run on it; a `_Remap` forwards a different action; everything else
    forwards unchanged and the response goes through `after`.

    Returns `(body, forwarded, applied)`.
    """
    decision = runtime.before(command)
    if isinstance(decision, Refusal):
        return decision.body, False, decision.applied
    applied = None
    action = decision
    if isinstance(decision, _Remap):
        applied = decision.applied
        action = decision.action_name
    body = session.command(action)
    body, after_applied = runtime.after(body)
    if after_applied is not None:
        applied = after_applied if applied is None else {
            "op": "multiple", "applied": [applied, after_applied]}
    return body, True, applied


def _step_budget(variant: Optional[Variant]) -> Optional[int]:
    if variant is None:
        return None
    limits = [op["limit"] for op in variant.operators if op["op"] == "step_limit"]
    return min(limits) if limits else None


def solve(world: GridWorld, variant: Optional[Variant],
          commands: Sequence[str] = ACTIONS,
          node_limit: int = NODE_LIMIT) -> Dict[str, Any]:
    """Exhaustively decide the wrapped world, and return a witness or a proof.

    A node is `(world state, commands charged, dead)`.  `dead` is absorbing --
    once a `step_limit` or an `observation_loss` has fired the runtime refuses
    everything (`proxy/variants.py:195-198`) -- so it is carried rather than
    recomputed.  The counter is part of the node because `step_limit` makes
    otherwise-identical world states genuinely different: reaching a cell with
    two commands left is not the same position as reaching it with none.

    Returns a dict with `solvable`, `witness` (the shortest winning command
    sequence, or `None`), `reachable_nodes`, `world_states_seen`, and `budget`.

    The counter is folded before it enters the node key, and it has to be or the
    graph never closes.  `VariantRuntime.commands` increments on every forwarded
    command whether or not a `step_limit` was declared, so carrying it raw makes
    every revisit of a world state a fresh node and the search runs forever on a
    world with four reachable cells.  Two foldings, both exact rather than
    approximate:

    * no `step_limit` declared -> the counter is never read, so it is folded to
      zero and world states merge as they should;
    * a budget of `n` -> anything past `n + 1` is folded to `n + 1`, because the
      runtime sets `dead` the moment the count exceeds the budget and `dead` is
      absorbing, so every larger count behaves identically.
    """
    budget = _step_budget(variant)

    def fold(commands: int) -> int:
        if budget is None:
            return 0
        return min(commands, budget + 1)
    start_session = WorldSession(world)
    start_body = start_session.body()

    # The initial observation goes through `after` too: an observation_loss on
    # the starting cell must fire before the first command, and a variant that
    # kills the arm at t=0 is a legitimate -- if brutal -- construction.
    boot = _runtime_at(variant, 0, False, None)
    start_body, _ = boot.after(start_body) if variant is not None else (start_body, None)
    if variant is not None and boot.dead:
        return {"solvable": False, "witness": None, "reachable_nodes": 1,
                "world_states_seen": 1, "budget": budget,
                "note": "a loss condition fired on the initial observation, "
                        "before any command was issued"}
    if start_body.get("state") == "WIN":
        return {"solvable": True, "witness": [], "reachable_nodes": 1,
                "world_states_seen": 1, "budget": budget,
                "note": "the initial state already satisfies the win condition"}

    start_key = (start_session.state.key(), 0, False)
    seen = {start_key: None}                       # node -> (prev_node, command)
    order: List[Tuple[Any, State, Dict[str, Any]]] = [
        (start_key, start_session.state, start_body)]
    cursor = 0
    world_states = {start_session.state.key()}

    while cursor < len(order):
        node_key, node_state, node_body = order[cursor]
        cursor += 1
        _, node_commands, node_dead = node_key
        for command in commands:
            session = WorldSession(world)
            session.state = node_state
            runtime = _runtime_at(variant, node_commands, node_dead, node_body)
            body, _forwarded, _applied = apply_command(runtime, session, command)
            nxt = (session.state.key(), fold(runtime.commands), runtime.dead)
            if nxt in seen:
                continue
            if len(seen) >= node_limit:
                raise OracleTruncated(
                    "%s: composed search exceeded %d nodes"
                    % (world.spec.world_id, node_limit))
            seen[nxt] = (node_key, command)
            world_states.add(session.state.key())
            if body.get("state") == "WIN":
                witness = _path(seen, nxt)
                return {"solvable": True, "witness": witness,
                        "reachable_nodes": len(seen),
                        "world_states_seen": len(world_states),
                        "budget": budget}
            # The runtime's own `last_body`, not the body `apply_command`
            # returned. They differ on a refusal: `after()` never runs, so a
            # live runtime still holds the pre-refusal body while the caller
            # sees a synthetic GAME_OVER. Storing the caller's view made 40 of
            # 380 nodes resume from a state no replay ever reaches -- harmless
            # for verdicts (every such node has `dead=True`, which is
            # absorbing) but flatly contrary to what `_runtime_at` claims.
            # Found by the V6 adversarial pass.
            order.append((nxt, session.state, runtime.last_body))

    return {"solvable": False, "witness": None, "reachable_nodes": len(seen),
            "world_states_seen": len(world_states), "budget": budget}


def _path(seen: Dict[Any, Any], node: Any) -> List[str]:
    out: List[str] = []
    while seen.get(node) is not None:
        prev, command = seen[node]
        out.append(command)
        node = prev
    out.reverse()
    return out


def replay(world: GridWorld, variant: Optional[Variant],
           commands: Sequence[str]) -> Dict[str, Any]:
    """Run a command sequence through the wrapper and report where it ends.

    The drill uses this to re-check a witness independently of the search that
    produced it: a witness that the searcher believes but a straight replay does
    not is a bug in the searcher, and that is worth catching here rather than on
    a sealed game.
    """
    session = WorldSession(world)
    runtime = VariantRuntime(variant)
    body = session.body()
    if variant is not None:
        body, _ = runtime.after(body)
    trace: List[Dict[str, Any]] = []
    for command in commands:
        body, forwarded, applied = apply_command(runtime, session, command)
        trace.append({"command": command, "forwarded": forwarded,
                      "state": body.get("state"), "applied": applied})
        if body.get("state") == "WIN":
            return {"win": True, "used": len(trace), "trace": trace,
                    "dead": runtime.dead}
    return {"win": body.get("state") == "WIN", "used": len(trace),
            "trace": trace, "dead": runtime.dead}
