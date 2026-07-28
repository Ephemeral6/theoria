"""plan -- the manual, handed to a search. And what to do when it will not go.

`Theoria.md` 1.10(b) gives planning a three-rung ladder and says explicitly
that the framework does not build its own planner: object-state BFS while the
reachable set is small, then A* with an admissible heuristic, then landmark
decomposition. 1.10(d) adds the discipline: SAT goes to commit, and **UNSAT is
not an answer** -- constraint 6 forbids a bare UNSAT, so an unreachable goal
owes a certificate before anyone may call the level unsolvable.

Three tiers are tried in order and every refusal is recorded:

1. **PDDL -> fd_adapter.** The designed route. `gen_pddl` is the weakest of the
   four generators (it takes no level instance, hardcodes objects to cell 0,0,
   and does not expand `forall`), so this tier is expected to refuse on a real
   manual. It is tried anyway, and its refusal is evidence about the generator
   rather than about the world.
2. **BFS over the manual's own predictor.** The ladder's first rung, done
   exactly: breadth-first over `State.key()` using the generated `step`, goal
   test `is_goal`, node cap declared. Length-optimal for unit costs.
3. **Nothing to plan for.** If the manual declares no winning condition,
   `is_goal` compiles to `return False` and search cannot succeed. That is
   NOT unsolvability: it is a manual that has not yet said what winning is,
   and it is reported as `no_goal_declared` so it can never be mistaken for a
   proof.
"""

import collections
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

import _bootstrap                                     # noqa: F401  (sys.path)

#: The reachable set the first rung is allowed to expand before it gives up and
#: reports a computational surprise. 1.10(b) puts exact BFS's ceiling at 10^6
#: states; a live run with a wall-clock budget uses less.
BFS_NODE_CAP = 120_000

#: And a deadline, because the node cap alone is not a bound on *time*.
#: `gen_python`'s `_cell_colour` calls `render(state)`, which rebuilds the whole
#: frame; on a 64x64 board that is 4096 cells per guard evaluation, so a node
#: cap that is harmless on a 5x5 fixture is hours on a real level. A search that
#: runs out of clock is exactly the `search_timeout` surprise -- a computational
#: one, which Theoria.md 1.10(d) sends to the playbook rather than the manual --
#: so the framework already has the right response to this; it just has to be
#: given the chance to fire.
BFS_DEADLINE_S = 120.0


def plan(books, namespace: Dict[str, Any], compile_result: Dict[str, Any], *,
         node_cap: int = BFS_NODE_CAP) -> Dict[str, Any]:
    report: Dict[str, Any] = {"tiers": [], "plan": None, "backend": None,
                              "status": "not_attempted"}

    if namespace is None:
        report["status"] = "no_predictor"
        return report

    if not _has_goal(books.theory):
        report["status"] = "no_goal_declared"
        report["detail"] = (
            "the manual states no winning condition, so `is_goal` is `False` "
            "everywhere and no search can succeed. This is a gap in the "
            "manual, NOT a proof that the level is unsolvable -- constraint 6 "
            "forbids reading a failed search as an unsolvability claim.")
        return report

    report["tiers"].append(_tier_pddl(compile_result))
    if report["tiers"][-1].get("ok"):
        found = report["tiers"][-1]
        report.update({"status": "sat", "plan": found.get("actions"),
                       "backend": found.get("backend")})
        return report

    bfs = _tier_bfs(namespace, node_cap)
    report["tiers"].append(bfs)
    if bfs.get("ok"):
        report.update({"status": "sat", "plan": bfs.get("actions"),
                       "backend": "object-state-bfs",
                       "optimal": True, "expansions": bfs.get("expansions")})
        return report

    report["status"] = bfs.get("status", "unsat")
    report["detail"] = bfs.get("detail")
    report["expansions"] = bfs.get("expansions")
    return report


def _has_goal(theory_text: str) -> bool:
    for line in (theory_text or "").splitlines():
        if line.strip().startswith("goal "):
            return True
    return False


def _tier_pddl(compile_result: Dict[str, Any]) -> Dict[str, Any]:
    """The designed route, tried and reported whatever it does."""
    entry: Dict[str, Any] = {"tier": "pddl+fd_adapter", "ok": False}
    forms = compile_result.get("forms") or {}
    pddl = forms.get("pddl")
    if not pddl:
        entry["detail"] = ((compile_result.get("errors") or {}).get("pddl")
                           or "no PDDL form was generated")
        return entry
    domain_path, problem_path = pddl
    try:
        from engines import fd_adapter                 # noqa: PLC0415
        from engines.fd_adapter.pddl import parse_domain, parse_problem  # noqa: PLC0415
        with open(domain_path, encoding="utf-8") as fh:
            domain = parse_domain(fh.read())
        with open(problem_path, encoding="utf-8") as fh:
            problem = parse_problem(fh.read())
        found, search = fd_adapter.solve_parsed(domain, problem,
                                                domain_path=domain_path,
                                                problem_path=problem_path)
    except Exception as exc:                           # noqa: BLE001
        entry["detail"] = "%s: %s" % (type(exc).__name__, exc)
        entry["refused_by"] = "pddl"
        return entry
    if found is None:
        entry["detail"] = "the grounded task has no plan (%d expansions)" % (
            getattr(search, "expansions", 0))
        return entry
    entry.update({"ok": True, "actions": list(found.actions),
                  "backend": found.backend, "optimal": found.optimal,
                  "length": found.length})
    return entry


def _tier_bfs(namespace: Dict[str, Any], node_cap: int,
              deadline_s: float = BFS_DEADLINE_S) -> Dict[str, Any]:
    """Object-state BFS over the manual's own step. Length-optimal, unit costs."""
    entry: Dict[str, Any] = {"tier": "object-state-bfs", "ok": False}
    started = time.time()
    step = namespace["step"]
    is_goal = namespace["is_goal"]
    initial_state = namespace["initial_state"]
    actions = list(namespace.get("ACTIONS") or [])
    if not actions:
        entry["detail"] = "the manual declares no actions, so nothing can be planned"
        entry["status"] = "no_actions"
        return entry

    start = initial_state()
    if is_goal(start):
        entry.update({"ok": True, "actions": [], "expansions": 0,
                      "detail": "already at the goal"})
        return entry

    seen = {start.key()}
    queue = collections.deque([(start, [])])
    expansions = 0
    while queue:
        state, path = queue.popleft()
        expansions += 1
        elapsed = time.time() - started
        if expansions > node_cap or elapsed > deadline_s:
            entry.update({
                "status": "search_timeout", "expansions": expansions,
                "elapsed_s": round(elapsed, 1),
                "reached": "node cap" if expansions > node_cap else "deadline",
                "frontier": len(queue), "seen": len(seen),
                "detail": "expanded %d states in %.0fs without reaching the "
                          "goal (%s reached first); the ladder's first rung is "
                          "exhausted and the next one needs an admissible "
                          "heuristic the playbook does not yet carry"
                          % (expansions, elapsed,
                             "node cap" if expansions > node_cap else "deadline")})
            return entry
        for action in actions:
            try:
                nxt = step(state, action)
            except Exception:                          # noqa: BLE001
                continue
            key = nxt.key()
            if key in seen:
                continue
            seen.add(key)
            if is_goal(nxt):
                entry.update({"ok": True, "actions": path + [list(action)],
                              "expansions": expansions,
                              "length": len(path) + 1})
                return entry
            queue.append((nxt, path + [list(action)]))

    entry.update({"status": "unsat", "expansions": expansions,
                  "reachable_states": len(seen),
                  "detail": "the whole reachable set (%d states) was enumerated "
                            "and none satisfies the goal. Constraint 6: this is "
                            "a search result, not a theorem -- an unsolvability "
                            "claim needs a certificate and a probe of the "
                            "clauses it depends on." % len(seen)})
    return entry


def surprises_from(report: Dict[str, Any], register) -> List[Any]:
    fired = []
    if report.get("status") == "search_timeout":
        fired.append(register.fire(
            "search_timeout",
            report.get("detail", "the planner ran out of nodes"),
            payload={"expansions": report.get("expansions")}))
    return fired
