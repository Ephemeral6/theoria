"""The factory check A0′ asks for: can each rule be witnessed *again*?

`cold-start-a0/prime/A0P_REPORT.md` §1 is the reason this file exists.  A0 saw
99 % of its state-action pairs and shipped a manual wrong in three places; A0′
saw 47 % and shipped a perfect one.  The variable was not how much was seen but
whether what was seen could be seen a second time — A0's Button was a latch, so
`press_left` had exactly one witness and no way to obtain another, and a
generalisation over one witness has to be rejected on evidence grounds.

So every world this library ships is stamped with, per ground-truth rule, **the
maximum number of times a single trajectory can witness it**.  That is a
property of the reachable graph, not of any particular walk, and it is computed
rather than asserted:

* build the reachable state graph and condense it into strongly connected
  components — inside an SCC everything is mutually reachable, which is exactly
  "you can come back and do it again";
* a rule's firing transitions become nodes; `t1 → t2` when `t2`'s source is
  reachable from `t1`'s target;
* if any firing transition can reach its own source again the count is
  **unbounded**; otherwise it is the longest chain in that DAG.

`max_witnesses == 1` is the A0 failure mode, stated in advance instead of
discovered in a post-mortem.  A mechanism module's `truth_rules` carries the
designer's `reversible` claim; `audit` compares the claim against the number and
reports disagreements, so a mechanism cannot quietly ship a wrong one.
"""

import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .types import ACTIONS, State
from .world import GridWorld

UNBOUNDED = -1          # JSON-friendly sentinel for "as often as you like"


# --------------------------------------------------------------------- SCCs

def _scc(nodes: Sequence[int], succ: Sequence[Sequence[int]]) -> List[int]:
    """Iterative Tarjan.  Returns component id per node, ids in reverse
    topological order of the condensation (so `comp[u] >= comp[v]` whenever
    `u` reaches `v`... only within Tarjan's own numbering, which is why the
    reachability closure below does not rely on it)."""
    n = len(nodes)
    index = [-1] * n
    low = [0] * n
    on_stack = [False] * n
    comp = [-1] * n
    stack: List[int] = []
    counter = 0
    ncomp = 0

    for root in range(n):
        if index[root] != -1:
            continue
        work: List[Tuple[int, int]] = [(root, 0)]
        while work:
            v, pi = work.pop()
            if pi == 0:
                index[v] = low[v] = counter
                counter += 1
                stack.append(v)
                on_stack[v] = True
            recurse = False
            for i in range(pi, len(succ[v])):
                w = succ[v][i]
                if index[w] == -1:
                    work.append((v, i + 1))
                    work.append((w, 0))
                    recurse = True
                    break
                if on_stack[w]:
                    low[v] = min(low[v], index[w])
            if recurse:
                continue
            if low[v] == index[v]:
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    comp[w] = ncomp
                    if w == v:
                        break
                ncomp += 1
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[v])
    return comp


def _condensation_reach(comp: Sequence[int], succ: Sequence[Sequence[int]]) -> List[int]:
    """Bitset per component: which components it can reach, itself included."""
    ncomp = max(comp) + 1 if comp else 0
    edges: List[set] = [set() for _ in range(ncomp)]
    for v, outs in enumerate(succ):
        cv = comp[v]
        for w in outs:
            cw = comp[w]
            if cw != cv:
                edges[cv].add(cw)

    # Tarjan numbers components so that every edge goes from a higher id to a
    # lower one; processing in increasing id order therefore sees successors
    # already finished, and one linear pass suffices.
    reach = [0] * ncomp
    for c in range(ncomp):
        bits = 1 << c
        for d in sorted(edges[c]):
            bits |= reach[d]
        reach[c] = bits
    return reach


# ------------------------------------------------------------------- audit

def analyse(world: GridWorld) -> Dict[str, Any]:
    states = world.reachable()
    order = {s.key(): i for i, s in enumerate(states)}
    n = len(states)

    succ: List[List[int]] = [[] for _ in range(n)]
    firings: Dict[str, List[Tuple[int, str, int]]] = {}
    for i, state in enumerate(states):
        for action in ACTIONS:
            nxt, rule = world.explain(state, action)
            j = order[nxt.key()]
            if j not in succ[i]:
                succ[i].append(j)
            firings.setdefault(rule, []).append((i, action, j))

    comp = _scc(range(n), succ)
    reach = _condensation_reach(comp, succ)

    def can_reach(src: int, dst: int) -> bool:
        return bool(reach[comp[src]] >> comp[dst] & 1)

    rules: Dict[str, Dict[str, Any]] = {}
    for rule, transitions in sorted(firings.items()):
        sources = sorted({s for s, _a, _t in transitions})
        targets = sorted({t for _s, _a, t in transitions})

        # Unbounded exactly when firing the rule can lead back to a firing state.
        unbounded = any(can_reach(t, s) for t in targets for s in sources)
        if unbounded:
            max_witnesses: int = UNBOUNDED
        else:
            # A DAG over firing transitions; longest chain by memoised descent.
            edges = {i: [j for j in range(len(transitions))
                         if can_reach(transitions[i][2], transitions[j][0])]
                     for i in range(len(transitions))}
            depth: Dict[int, int] = {}

            def longest(i: int) -> int:
                if i in depth:
                    return depth[i]
                depth[i] = 1
                best = 1
                for j in edges[i]:
                    best = max(best, 1 + longest(j))
                depth[i] = best
                return best

            limit = sys.getrecursionlimit()
            sys.setrecursionlimit(max(limit, len(transitions) * 4 + 1000))
            try:
                max_witnesses = max((longest(i) for i in range(len(transitions))),
                                    default=0)
            finally:
                sys.setrecursionlimit(limit)

        rules[rule] = {
            "firing_transitions": len(transitions),
            "firing_states": len(sources),
            "max_witnesses": max_witnesses,
            "re_witnessable": unbounded or max_witnesses >= 2,
            "single_witness": (not unbounded) and max_witnesses == 1,
        }

    bounded = [r for r, v in rules.items() if not v["re_witnessable"]]
    return {
        "reachable_states": n,
        "components": max(comp) + 1 if comp else 0,
        "rules": rules,
        "rules_total": len(rules),
        "rules_re_witnessable": sum(1 for v in rules.values() if v["re_witnessable"]),
        "rules_single_witness": sorted(bounded),
        "reversibility_score": round(
            sum(1 for v in rules.values() if v["re_witnessable"]) / max(1, len(rules)), 4
        ),
    }


def audit(world: GridWorld, claims: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """`analyse`, plus a comparison against each mechanism's own `reversible` claim.

    A claim of `True` or `False` is checked; `"conditional — ..."` is not a claim
    about a particular world and is recorded as `deferred`, with the measured
    number filling it in.  A `False` claim that measures re-witnessable is a real
    disagreement and is reported as one — that is the case where a mechanism
    thinks it is supplying an irreversible rule and the geometry has quietly
    given the agent a way back.
    """
    result = analyse(world)
    checked: List[Dict[str, Any]] = []
    for claim in claims:
        name = claim.get("name")
        measured = result["rules"].get(name)
        stated = claim.get("reversible")
        if measured is None:
            verdict = "unreachable"          # the rule can never fire in this world
        elif isinstance(stated, bool):
            verdict = "agrees" if stated == measured["re_witnessable"] else "DISAGREES"
        else:
            verdict = "deferred"
        checked.append({
            "rule": name,
            "claimed": stated,
            "measured": None if measured is None else measured["max_witnesses"],
            "re_witnessable": None if measured is None else measured["re_witnessable"],
            "verdict": verdict,
        })
    result["claims"] = checked
    result["claim_disagreements"] = [c["rule"] for c in checked if c["verdict"] == "DISAGREES"]
    return result
