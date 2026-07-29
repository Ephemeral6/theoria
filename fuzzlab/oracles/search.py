"""Brute-force search oracles: exact distances, plan validation, split entropy.

None of this calls an engine. `lp_potential` is judged by a BFS that computes the
true distance-to-goal it claims never to overestimate; `fd_adapter` by a plan
validator that applies the plan to the initial state and checks the goal; and
`probe_frontier` by recomputing the splitting entropy from the world's own
observation table.

Everything here is exponential-in-principle and bounded-in-practice. Where a
world is too large the function returns `None` and the caller records a
`skipped` finding with the reason — a battery that quietly narrows to the worlds
its oracle can handle reports a coverage number it did not earn.
"""

import math
from collections import deque
from typing import Any, Callable, Dict, Hashable, Iterable, List, Optional, Sequence, Set, Tuple

# Above this many states an exhaustive walk stops being worth the wall clock in
# a 500-world campaign.  Stated here rather than inline so the report can quote
# the number that produced its `skipped` count.
STATE_BUDGET = 200_000


def bfs_distances(start: Hashable,
                  successors: Callable[[Any], Iterable[Any]],
                  budget: int = STATE_BUDGET) -> Optional[Dict[Hashable, int]]:
    """Exact distance from `start` to every reachable state, or None if too big."""
    dist: Dict[Hashable, int] = {start: 0}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        for nxt in successors(state):
            if nxt in dist:
                continue
            if len(dist) >= budget:
                return None
            dist[nxt] = dist[state] + 1
            queue.append(nxt)
    return dist


def distance_to_any(start: Hashable,
                    successors: Callable[[Any], Iterable[Any]],
                    goals: Set[Hashable],
                    budget: int = STATE_BUDGET) -> Tuple[Optional[int], bool]:
    """`(true distance to the nearest goal, exhausted)`.

    `exhausted` is True when the whole reachable set was enumerated without
    hitting the budget, which is what makes "unreachable" a *proof* rather than a
    timeout — the distinction `lp_potential`'s soundness claim turns on.
    """
    dist: Dict[Hashable, int] = {start: 0}
    queue = deque([start])
    if start in goals:
        return 0, True
    while queue:
        state = queue.popleft()
        for nxt in successors(state):
            if nxt in dist:
                continue
            if len(dist) >= budget:
                return None, False
            dist[nxt] = dist[state] + 1
            if nxt in goals:
                return dist[nxt], True
            queue.append(nxt)
    return None, True


# ------------------------------------------------------------ plan validation

def validate_plan(initial: Set[str], goal: Tuple[Set[str], Set[str]],
                  actions: Dict[str, Dict[str, Set[str]]],
                  plan: Sequence[str]) -> Tuple[bool, str]:
    """Apply a STRIPS plan step by step; `(ok, why not)`.

    Written out rather than delegated because this is the whole judgement of
    `fd_adapter`: a planner that returns a plan the world cannot execute is the
    defect this exists to catch, and a validator that shares code with the
    planner cannot catch it.

    `actions` maps name -> `{"pre_pos", "pre_neg", "add", "del"}`, and `goal` is
    `(positive, negative)`. Negative preconditions and negative goal literals are
    carried explicitly because the PDDL subset in use declares
    `:negative-preconditions` and the generator emits both — dropping them would
    make the validator accept plans the world rejects, which is the one direction
    a validator must never be wrong in.
    """
    goal_pos, goal_neg = goal
    state = set(initial)
    for i, step in enumerate(plan):
        action = actions.get(step)
        if action is None:
            return False, "step %d: no such action %r" % (i, step)
        missing = action["pre_pos"] - state
        if missing:
            return False, ("step %d (%s): preconditions unmet: %s"
                           % (i, step, ", ".join(sorted(missing))))
        present = action["pre_neg"] & state
        if present:
            return False, ("step %d (%s): negative preconditions violated: %s"
                           % (i, step, ", ".join(sorted(present))))
        state = (state - action["del"]) | action["add"]
    unmet = goal_pos - state
    if unmet:
        return False, "goal unmet after %d steps: %s" % (len(plan),
                                                         ", ".join(sorted(unmet)))
    forbidden = goal_neg & state
    if forbidden:
        return False, ("negative goal violated after %d steps: %s"
                       % (len(plan), ", ".join(sorted(forbidden))))
    return True, ""


def optimal_plan_length(initial: Set[str], goal: Tuple[Set[str], Set[str]],
                        actions: Dict[str, Dict[str, Set[str]]],
                        budget: int = STATE_BUDGET) -> Tuple[Optional[int], bool]:
    """Shortest plan length by BFS over ground states; `(length, exhausted)`.

    Ground STRIPS BFS is exponential and that is fine here: the worlds are drawn
    small on purpose, and where one is not, this returns `(None, False)` and the
    property records a `skipped` rather than pretending to have checked
    optimality. `exhausted` is the difference between "no plan exists" and "I ran
    out of budget", which is the whole of the unsolvability judgement.
    """
    goal_pos, goal_neg = frozenset(goal[0]), frozenset(goal[1])
    start = frozenset(initial)

    def satisfied(state) -> bool:
        return goal_pos <= state and not (goal_neg & state)

    def successors(state):
        for action in actions.values():
            if action["pre_pos"] <= state and not (action["pre_neg"] & state):
                yield frozenset((state - action["del"]) | action["add"])

    if satisfied(start):
        return 0, True
    seen = {start}
    queue = deque([(start, 0)])
    while queue:
        state, depth = queue.popleft()
        for nxt in successors(state):
            if nxt in seen:
                continue
            if len(seen) >= budget:
                return None, False
            seen.add(nxt)
            if satisfied(nxt):
                return depth + 1, True
            queue.append((nxt, depth + 1))
    return None, True


# ------------------------------------------------------------------- entropy

def partition_entropy(groups: Sequence[float]) -> float:
    """Shannon entropy in **bits** of a partition with these class *weights*.

    Two things are stated rather than assumed, because each is a whole
    comparison: the unit is **bits** (an oracle recomputing in nats produces a
    confident, wrong bug report), and the argument is class **weight**, not class
    size. Where hypotheses carry non-uniform weights those differ, and passing
    sizes here is exactly the mistake this battery made once. Non-positive
    weights contribute nothing.
    """
    total = sum(groups)
    if total <= 0:
        return 0.0
    out = 0.0
    for size in groups:
        if size <= 0:
            continue
        p = size / total
        out -= p * math.log2(p)
    return out


def split_partition(hypotheses: Sequence[Any], action: str,
                    predict: Callable[[Any, str], Any]) -> Dict[Any, List[Any]]:
    """Group hypotheses by the observation each predicts for `action`.

    This *is* the split a probe induces: run the action, see which block the
    world falls into, and every hypothesis outside that block is refuted.
    """
    out: Dict[Any, List[Any]] = {}
    for h in hypotheses:
        out.setdefault(predict(h, action), []).append(h)
    return out


def best_split(hypotheses: Sequence[Any], actions: Sequence[str],
               predict: Callable[[Any, str], Any]) -> Tuple[Optional[str], float]:
    """The action with the highest split entropy; ties broken by action order.

    The tie-break is stated because it has to match whatever the engine does for
    a comparison of *which action* to be meaningful. Where it does not, the
    property compares entropies and not names, and says so.
    """
    best_action: Optional[str] = None
    best_entropy = -1.0
    for action in actions:
        blocks = split_partition(hypotheses, action, predict)
        entropy = partition_entropy([len(b) for b in blocks.values()])
        if entropy > best_entropy + 1e-12:
            best_action, best_entropy = action, entropy
    return best_action, (best_entropy if best_entropy >= 0 else 0.0)
