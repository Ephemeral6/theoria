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

**A crash is not a finding (E14).** BFS calls the generated `step`, and
`gen_python` documents that predictor as *total*: "every object the rules do
not mention is carried over unchanged, **which is what makes this total**".
Its one declared exception, `AmbiguousTransition`, is itself a constraint-9
defect signal. So an exception out of `step` is never "that action does not
apply here" -- it is either a declared violation or a bug in the compiled
manual. Swallowing it prunes a successor, which shrinks the search tree, which
makes the queue drain sooner, which makes `status: "unsat"` and its "the whole
reachable set was enumerated" arrive *faster and more often*. Every crash made
the health certificate look better. So the crashes are now counted into the
report, and the exhaustiveness claim is gated on that count being zero: a run
with crashes reports `status: "unsat_unsound"` and `exhaustive: False`, never
`unsat`. The shape is copied from `engine-rig/bench/ladder.py:74-82`, which on
a budget overrun writes `proved_unsolvable: False` *plus* `error: "over
budget: ..."` and records the ceiling positively in the artifact.
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

#: How many distinct crash sites to keep verbatim in the artifact. The *count*
#: is never capped -- only the sample of messages is -- so a truncated sample
#: can never make the count look smaller than it was.
CRASH_SAMPLE_CAP = 8


class StepCrashLog:
    """Every exception the generated `step` threw, counted, typed and located.

    The account exists so that no field claiming exhaustiveness can be written
    without it. `as_json()` is emitted on *every* exit of `_tier_bfs`, including
    the ones where the count is zero -- a zero that is printed is evidence, a
    zero that is absent is indistinguishable from a report that never looked.
    """

    def __init__(self, site: str) -> None:
        self.site = site
        self.count = 0
        self.successors_pruned = 0
        self.by_type: Dict[str, int] = {}
        self.samples: List[Dict[str, Any]] = []

    def record(self, exc: BaseException, *, action: Any,
               expansion: int, pruned: int = 1) -> None:
        self.count += 1
        self.successors_pruned += pruned
        kind = type(exc).__name__
        self.by_type[kind] = self.by_type.get(kind, 0) + 1
        if len(self.samples) < CRASH_SAMPLE_CAP:
            self.samples.append({
                "type": kind,
                "message": str(exc)[:400],
                "action": list(action) if isinstance(action, (tuple, list)) else action,
                "at_expansion": expansion,
            })

    def as_json(self) -> Dict[str, Any]:
        return {
            "site": self.site,
            "count": self.count,
            "successors_pruned": self.successors_pruned,
            "by_type": dict(sorted(self.by_type.items())),
            "samples": self.samples,
            "sample_cap": CRASH_SAMPLE_CAP,
            "note": ("`step` is documented total and its only declared "
                     "exception, AmbiguousTransition, is itself a constraint-9 "
                     "defect. So none of these is 'the action does not apply' "
                     "-- each is a violation or a bug, and each one silently "
                     "shrank the reachable set this search enumerated."),
        }


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
    # E14: the crash account travels with every verdict, not only the one it
    # invalidates -- a reader must never have to infer "no crashes" from silence.
    for key in ("step_crashes", "search_ceiling"):
        if key in bfs:
            report[key] = bfs[key]
    if bfs.get("ok"):
        crashed = (bfs.get("step_crashes") or {}).get("count") or 0
        # E14 (adversarial review, correction 2): `optimal` is an
        # exhaustiveness claim, not a description of the plan. BFS is
        # length-optimal only if no successor was dropped, and a crash on the
        # shorter route makes a longer plan look optimal. So it is gated on the
        # same count everything else is.
        report.update({"status": "sat", "plan": bfs.get("actions"),
                       "backend": "object-state-bfs",
                       "optimal": not crashed,
                       "expansions": bfs.get("expansions")})
        if crashed:
            report["error"] = bfs.get("error")
            report["detail"] = bfs.get("detail")
        return report

    report["status"] = bfs.get("status", "unsat")
    report["detail"] = bfs.get("detail")
    report["expansions"] = bfs.get("expansions")
    if "exhaustive" in bfs:
        report["exhaustive"] = bfs["exhaustive"]
    if bfs.get("error"):
        report["error"] = bfs["error"]
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
    """Object-state BFS over the manual's own step. Length-optimal, unit costs.

    The account is stamped onto the entry **here**, after `_bfs_search` has
    returned, whichever of its five exits it took. The first version of this
    change stamped a snapshot at each exit and missed one -- the `ok: True`
    return -- so a search that crashed and then found the goal published
    `count: 0`. A false printed zero is worse than an absent one, and it was
    exactly this ticket's disease surviving inside this ticket's fix. Doing it
    once, structurally, is what makes that class of miss impossible rather than
    merely fixed. (Adversarial review, correction 1.)
    """
    crashes = StepCrashLog("plan._tier_bfs: step(state, action)")
    entry = _bfs_search(namespace, node_cap, deadline_s, crashes)
    entry["step_crashes"] = crashes.as_json()
    # The ceiling, written down positively rather than left implicit -- the
    # `ladder.py:226` shape: a reader must be able to check "N < cap" from the
    # artifact alone instead of trusting that the search would have said so.
    entry["search_ceiling"] = {"node_cap": node_cap, "deadline_s": deadline_s}
    if crashes.count and entry.get("ok"):
        # A plan was found, and successors were dropped getting to it. The plan
        # itself still replays -- it is a positive certificate -- but nothing
        # about minimality survives, so say so on the entry the caller reads.
        entry["error"] = _crash_error(crashes)
        entry["detail"] = (
            "a plan of length %s was found, but %d call(s) to `step` raised "
            "and each removed a successor. The plan is still a plan -- it can "
            "be replayed -- but it is NOT known to be shortest, because a "
            "shorter route through a pruned successor would never have been "
            "seen." % (entry.get("length"), crashes.count))
    return entry


def _crash_error(crashes: StepCrashLog) -> str:
    return ("step raised %d time(s) (%s); %d successor(s) were pruned without "
            "adjudication"
            % (crashes.count,
               ", ".join("%s x%d" % (k, v)
                         for k, v in sorted(crashes.by_type.items())),
               crashes.successors_pruned))


def _bfs_search(namespace: Dict[str, Any], node_cap: int, deadline_s: float,
                crashes: StepCrashLog) -> Dict[str, Any]:
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
            except Exception as exc:                   # noqa: BLE001
                # E14: was a bare `continue`. Dropping the successor here is
                # what let a crashing predictor pass for a small world.
                crashes.record(exc, action=action, expansion=expansions)
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

    # The queue drained. Whether that means "the whole reachable set" depends
    # entirely on whether any successor was thrown away on the way, so the two
    # facts are written together and the claim is gated on the count.
    entry.update({"expansions": expansions, "reachable_states": len(seen)})
    if crashes.count:
        entry.update({
            "status": "unsat_unsound",
            "exhaustive": False,
            "error": _crash_error(crashes),
            "detail": "the queue drained after %d expansions over %d distinct "
                      "states, but %d call(s) to the manual's own `step` raised "
                      "and each one silently removed a successor. `step` is "
                      "documented total, so those are defects, not "
                      "inapplicable actions -- the set enumerated here is a "
                      "SUBSET of the reachable set of the manual as written, "
                      "and this run is not entitled to say the goal is "
                      "unreachable. Fix the predictor and re-run."
                      % (expansions, len(seen), crashes.count),
        })
        return entry
    entry.update({"status": "unsat", "exhaustive": True,
                  "detail": "the whole reachable set (%d states) was enumerated "
                            "and none satisfies the goal -- no call to `step` "
                            "raised, so no successor was dropped and the set is "
                            "the manual's own. Constraint 6: this is "
                            "a search result, not a theorem -- an unsolvability "
                            "claim needs a certificate and a probe of the "
                            "clauses it depends on." % len(seen)})
    return entry


def surprises_from(report: Dict[str, Any], register, *,
                   reported: Optional[set] = None,
                   token: Optional[str] = None) -> List[Any]:
    """Turn a plan verdict into the surprises that should reach the desk.

    **`no_goal_declared` was silent, and that is why nothing was ever won.**
    Across all four live legs of 2026-07-31 the planner returned
    `no_goal_declared` on *every* turn -- 29/29 on
    `20260731T1430Z-A3-level2-carried-r3` -- so `plan(...)["status"]` was never
    `"sat"`, `_commit` was never entered, and not one of the 33 actions that leg
    spent was an attempt to win. The arm probed, theorized, probed, theorized,
    and never played. Meanwhile this function fired nothing, so across eight
    desk calls costing $13.44 the model was never once told that its playbook
    declares no goal and that planning is therefore dead on arrival.

    It is a `heuristic_miss`: computational family, and the computational family
    is the one whose book is the **playbook**, which is exactly where the goal
    is missing. No eighth surprise is invented -- `Theoria.md` 1.10(d) fixes the
    seven and `inner/surprise.py` refuses any other name.

    **Fired once per playbook revision, not once per turn.** A surprise is the
    only thing that calls the desk; a gap that fires every turn would call the
    desk every turn to be told the same thing. `reported` is a set the caller
    owns and `token` identifies the playbook the gap was found in, so the
    second turn with an unchanged playbook is silent and the first turn after a
    rewrite that still has no goal speaks up again.
    """
    fired = []
    if report.get("status") == "search_timeout":
        fired.append(register.fire(
            "search_timeout",
            report.get("detail", "the planner ran out of nodes"),
            payload={"expansions": report.get("expansions")}))

    if report.get("status") == "no_goal_declared":
        key = ("no_goal_declared", token)
        if reported is None or key not in reported:
            if reported is not None:
                reported.add(key)
            fired.append(register.fire(
                "heuristic_miss",
                report.get("detail", "no goal is declared")
                + " Until a `goal` is stated the plan tier cannot return "
                  "`sat`, `commit` never runs, and every action this arm "
                  "spends is a probe rather than an attempt to win. Declaring "
                  "the winning condition is the highest-value edit available "
                  "to the playbook.",
                payload={"status": "no_goal_declared",
                         "consequence": "plan never returns sat; commit never "
                                        "runs; no level can be completed",
                         "book_to_edit": "playbook.dsl",
                         "playbook_token": token}))
    return fired
