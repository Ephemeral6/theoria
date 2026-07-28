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


def _longest_chain(links: Sequence[Sequence[int]]) -> int:
    """Longest path, in nodes, through a DAG given as adjacency lists.

    Iterative on purpose.  Rules in the catalogue run to hundreds of firing
    transitions (`t3-latch-maze` / `walk`: 858), and a recursive descent that
    raises `sys.setrecursionlimit` to match is not buying a catchable
    `RecursionError` — it is buying the C stack running out under the
    interpreter, which no `except` can see.

    The relation is acyclic by construction once the unbounded test above is
    right: no firing transition reaches its own source, so no chain of them can
    close.  A cycle here would therefore mean the two tests disagree about the
    same `reach` bitset, and a wrong number is worse than a stop, so it raises.
    """
    n = len(links)
    depth = [0] * n
    UNSEEN, OPEN, DONE = 0, 1, 2
    mark = [UNSEEN] * n

    for root in range(n):
        if mark[root] != UNSEEN:
            continue
        mark[root] = OPEN
        stack: List[Tuple[int, int]] = [(root, 0)]
        while stack:
            i, k = stack.pop()
            if k == len(links[i]):
                # Every successor is finished by now, so its depth is final.
                depth[i] = 1 + max((depth[j] for j in links[i]), default=0)
                mark[i] = DONE
                continue
            stack.append((i, k + 1))
            j = links[i][k]
            if mark[j] == OPEN:
                raise AssertionError(
                    "cycle among firing transitions of a rule measured bounded; "
                    "the reachability closure contradicts the unbounded test"
                )
            if mark[j] == UNSEEN:
                mark[j] = OPEN
                stack.append((j, 0))
    return max(depth, default=0)


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

        # Unbounded exactly when some firing transition can get back to the
        # state it fired from — *its own* source, not another firing's.  Firing
        # A and then reaching B's source is a second witness, not a repeat of
        # the first, and counting it as one collapsed every graded rule in the
        # catalogue onto the UNBOUNDED sentinel.
        unbounded = any(can_reach(t, s) for s, _a, t in transitions)
        if unbounded:
            max_witnesses: int = UNBOUNDED
        else:
            # `can_reach` reads nothing but `comp`, so two firing transitions
            # sharing a (source component, target component) pair have identical
            # neighbourhoods and can never chain to each other — that link would
            # be the self-loop just ruled out.  Collapsing onto the pairs is
            # therefore exact, and it takes the biggest rule in the catalogue
            # from ~736k reachability probes to a few dozen.
            pairs = sorted({(comp[s], comp[t]) for s, _a, t in transitions})
            links = [[j for j, (src, _tgt) in enumerate(pairs)
                      if reach[tgt_i] >> src & 1]
                     for _src_i, tgt_i in pairs]
            max_witnesses = _longest_chain(links)

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
    """`analyse`, plus a comparison against each mechanism's own claim.

    **Which claim, on which axis.**  What `analyse` measures is A0′'s property —
    how many times one trajectory can witness a rule — and that is *not* whether
    the rule's effect can be undone.  A collected token never comes back, so
    `collect_token` is irreversible; a world with three tokens still witnesses
    the rule three times, because each token is a fresh witness of the same rule.
    Conversely `advance_cycler` has order k and destroys nothing, yet measures a
    single witness in two catalogue worlds, because nothing routes the agent back
    to a shut phase.  Reversible effect, one witness — and one-way effect,
    several witnesses — are both real and the library had one word for both.

    So mechanisms declare `re_witnessable` where the two axes come apart, and
    that is what is checked; `reversible` is the fallback for the rules where
    they coincide, and stays in the table as prose either way.  Seven of twenty
    worlds used to ship a `DISAGREES` that was only this conflation, which is the
    worst possible state for a check to be in: a constant false alarm is
    indistinguishable from the real one it exists to raise.

    A claim of `True` or `False` is checked; `"conditional — ..."` is not a claim
    about a particular world and is recorded as `deferred`, with the measured
    number filling it in.
    """
    result = analyse(world)
    checked: List[Dict[str, Any]] = []
    for claim in claims:
        name = claim.get("name")
        measured = result["rules"].get(name)
        # The re-witnessability axis if the mechanism separated it, else the
        # reversibility claim, which is the same statement wherever they coincide.
        axis = "re_witnessable" if "re_witnessable" in claim else "reversible"
        stated = claim.get(axis)
        if measured is None:
            verdict = "unreachable"          # the rule can never fire in this world
        elif isinstance(stated, bool):
            verdict = "agrees" if stated == measured["re_witnessable"] else "DISAGREES"
        else:
            verdict = "deferred"
        checked.append({
            "rule": name,
            "axis": axis,
            "claimed": stated,
            "reversible": claim.get("reversible"),
            "measured": None if measured is None else measured["max_witnesses"],
            "re_witnessable": None if measured is None else measured["re_witnessable"],
            "verdict": verdict,
        })
    result["claims"] = checked
    result["claim_disagreements"] = [c["rule"] for c in checked if c["verdict"] == "DISAGREES"]
    return result
