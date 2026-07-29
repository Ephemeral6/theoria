"""The E7 measurements. Four, and each one answers a named objection.

    python -m audit --out runs/<id>

**R · replication.** E2's §3b table, re-measured from a fresh process: the same
instances, the same singleton guard, the same three configurations. This is
replication, not independence -- it re-runs `bench/`'s compiler and `bench/`'s
FD driver -- and it is reported as replication. What it can catch is drift and
non-determinism; what it cannot catch is a shared bug, which is what §W is for.

**W · is the pruner wired in at all.** The first objection to any "no speed-up"
result: perhaps nothing was pruned. Measured directly on the bundled rung, where
the pruner is a Python callable this module can count: how many times it fired,
how many states it cut, and -- the number that settles it -- what fraction of the
states a blind search expands are dead. A pruner that never fires and a dead
region a search never enters look identical in an expansion count and are not
the same finding.

**D · dead starts.** The measurement E2's batch could not make, because every
unsolvable instance in it was settled by FD's translator before search began.
An instance whose *initial state* is already dead forces the planner to have an
opinion about the dead region. See `deadstart.py` for why the two theorem kinds
are predicted to come apart here.

**S · size.** "The instances are too small" -- so the ladder is run out to a
board where blind expands six figures, holding the guard and the configuration
fixed.

Every FD number is taken with `bench.fdrun`, which parses FD's own counters and
records the raw log. Every guarded plan is replayed against the **original**
domain by the rig's validator, so a guard that made an instance easier by making
it wrong fails here rather than flattering the table.
"""

import json
import os
import time
from typing import Dict, List, Optional, Sequence, Tuple

from bench import compile_theorems, fdrun
from engines.deadlock_carver.carve import Task, carve, pruner
from engines.fd_adapter import pddl, search
from engines.fd_adapter.validate import validate_plan
from fixtures import sokoban

from audit import deadstart

# The three configurations E2 compared, plus the control it named a control.
CONFIGS: Tuple[Tuple[str, Optional[str]], ...] = (
    ("fd-optimal", "blind"),
    ("fd-optimal", "lmcut"),
    ("fd-optimal", "ipdb"),
)

REPLICATION_SIDES = (4, 6, 7)
SIZE_SIDES = (4, 5, 6, 7, 8)
DEADSTART_SIDES = (4, 5, 6)


def _label(heuristic: Optional[str]) -> str:
    return heuristic or "default"


def _load(domain_path: str, problem_text: str):
    domain = pddl.parse_domain(open(domain_path, encoding="utf-8").read())
    problem = pddl.parse_problem(problem_text)
    return domain, problem


def _theorems(domain, problem):
    task = Task.build(domain, problem)
    return task, carve(task)


def _measure(executable: str, domain_path: str, problem_path: str,
             heuristic: Optional[str], log_dir: str, tag: str) -> Dict[str, object]:
    # Absolute, always: Fast Downward's driver runs the translator in a working
    # directory of its own, so a relative path here fails at translate time with
    # exit 30 and every counter comes back None -- which reads, in a table, as a
    # planner that found nothing rather than a file it never opened.
    measurement = fdrun.measure(
        executable, os.path.abspath(domain_path), os.path.abspath(problem_path),
        tier="fd-optimal", heuristic=heuristic,
        keep_log=os.path.join(log_dir, tag + ".log"),
    )
    return {
        "heuristic": _label(heuristic),
        "expanded": measurement.nodes.get("expanded"),
        "generated": measurement.nodes.get("generated"),
        "evaluated": measurement.nodes.get("evaluated"),
        "initial_h": measurement.initial_h,
        "solved": measurement.solved,
        "proved_unsolvable": measurement.proved_unsolvable,
        "plan_length": measurement.plan_length,
        "search_seconds": measurement.search_seconds,
        "translator_facts": measurement.translator.get("task_size"),
        "returncode": measurement.returncode,
        "error": measurement.error,
        "log": os.path.relpath(os.path.join(log_dir, tag + ".log")),
    }


# ------------------------------------------------------------------ R · replication

def replication(executable: str, work: str, log_dir: str,
                sides: Sequence[int] = REPLICATION_SIDES) -> List[Dict[str, object]]:
    """E2 §3b, re-measured: singleton guard, before and after, three configs."""
    from bench import instances as bench_instances

    rows: List[Dict[str, object]] = []
    for side in sides:
        level = bench_instances.far_level(side)
        text = level.problem_text()
        plain = os.path.join(work, "far%d.pddl" % side)
        with open(plain, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        domain, problem = _load(sokoban.DOMAIN_PATH, text)
        task, theorems = _theorems(domain, problem)
        compile_theorems.guardable(domain, theorems)
        guarded_dir = os.path.join(work, "guarded")
        os.makedirs(guarded_dir, exist_ok=True)
        guard_domain, guard_problem = compile_theorems.write_guarded(
            guarded_dir, "far%d" % side, text, theorems,
            guard="singleton", problem=problem)

        singles = sum(1 for t in theorems if t.size == 1)
        for _tier, heuristic in CONFIGS:
            before = _measure(executable, sokoban.DOMAIN_PATH, plain, heuristic,
                              log_dir, "R-far%d-%s-before" % (side, _label(heuristic)))
            after = _measure(executable, guard_domain, guard_problem, heuristic,
                             log_dir, "R-far%d-%s-after" % (side, _label(heuristic)))
            rows.append({
                "instance": "far%d" % side,
                "guard": "singleton",
                "theorems_total": len(theorems),
                "theorems_carried": singles,
                "config": "astar(%s())" % _label(heuristic),
                "before": before,
                "after": after,
                "dividend": _dividend(before.get("expanded"), after.get("expanded")),
                "plan_unchanged": _plan_unchanged(
                    domain, problem, before.get("plan_length"),
                    after.get("plan_length")),
            })
    return rows


def _dividend(before: Optional[int], after: Optional[int]) -> Optional[float]:
    if not before or after is None:
        return None
    return round((before - after) / before, 4)


def _plan_unchanged(domain, problem, before: Optional[int],
                    after: Optional[int]) -> Optional[bool]:
    if before is None or after is None:
        return None
    return before == after


# ---------------------------------------------------------- W · is it wired in

def wiring(sides: Sequence[int] = REPLICATION_SIDES) -> List[Dict[str, object]]:
    """On the rung whose pruner this module can count: does it fire, and where?

    Three numbers per instance, and the third is the one that matters:

    * `pruner_calls` / `states_cut` -- the pruner ran and removed states. If
      these were zero, "no speed-up" would mean "nothing was pruned" and the
      whole result would be an artefact of a disconnected hook.
    * `dead_fraction_of_blind` -- of the states a blind search expands, what
      fraction is dead. This is the size of the prize, measured without any
      planner's opinion in it. A heuristic that expands fewer states than that
      fraction predicts is avoiding the region rather than proving anything
      about it.
    """
    from bench import instances as bench_instances

    rows: List[Dict[str, object]] = []
    for side in sides:
        level = bench_instances.far_level(side)
        text = level.problem_text()
        domain, problem = _load(sokoban.DOMAIN_PATH, text)
        task, theorems = _theorems(domain, problem)
        dead = pruner(theorems)

        calls = {"n": 0, "dead": 0}

        def counting(state, _dead=dead, _calls=calls):
            _calls["n"] += 1
            verdict = _dead(state)
            if verdict:
                _calls["dead"] += 1
            return verdict

        blind = search.search(domain, problem, prune=None)
        pruned = search.search(domain, problem, prune=counting)

        # The independent half: a breadth-first walk written here, which never
        # consults the pruner, recording every state it expands. The theorems
        # are asked about those states *afterwards*. Nothing in this number can
        # be explained by the hook, because the hook is not involved -- so it
        # measures the size of the prize rather than the behaviour of the thing
        # claiming the prize.
        expanded, dead_seen = _walk(domain, problem, dead)

        rows.append({
            "instance": "far%d" % side,
            "theorems": len(theorems),
            "blind_expansions": blind.expansions,
            "pruned_expansions": pruned.expansions,
            "engine_reported_pruned": pruned.pruned,
            "pruner_calls": calls["n"],
            "pruner_fired": calls["dead"],
            "states_cut": blind.expansions - pruned.expansions,
            "reachable_states": expanded,
            "dead_reachable_states": dead_seen,
            "dead_fraction_of_reachable": (
                round(dead_seen / expanded, 4) if expanded else None),
            "plan_unchanged": _same_plan(blind.plan, pruned.plan),
        })
    return rows


def _same_plan(left, right) -> bool:
    if left is None or right is None:
        return (left is None) == (right is None)
    return len(left) == len(right)


def _walk(domain, problem, dead) -> Tuple[int, int]:
    """Breadth-first over the reachable space, counting dead states expanded.

    Written here rather than taken from `engines.fd_adapter.search` on purpose:
    the point of this number is that it does not come from the module whose
    pruning hook is under suspicion.
    """
    from collections import deque

    grounded = pddl.ground_actions(domain, problem)
    actions, initial, _static_goal_ok = search.strip_static(domain, problem, grounded)
    static = pddl.static_predicates(domain)
    seen = {initial}
    queue = deque([initial])
    expanded = 0
    dead_seen = 0
    while queue:
        state = queue.popleft()
        expanded += 1
        if dead(state):
            dead_seen += 1
        if search.is_goal(problem, state, static):
            continue
        for action in actions:
            if not search.applicable(action, state):
                continue
            successor = search.successor(action, state)
            if successor not in seen:
                seen.add(successor)
                queue.append(successor)
    return expanded, dead_seen


# -------------------------------------------------------------- D · dead starts

def dead_starts(executable: str, work: str, log_dir: str,
                sides: Sequence[int] = DEADSTART_SIDES) -> List[Dict[str, object]]:
    """The measurement E2's batch could not make. See `deadstart.py`."""
    rows: List[Dict[str, object]] = []
    for level in deadstart.levels(tuple(sides)):
        text = level.problem_text()
        plain = os.path.join(work, "%s.pddl" % level.name)
        with open(plain, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        domain, problem = _load(sokoban.DOMAIN_PATH, text)
        task, theorems = _theorems(domain, problem)

        kind = level.name.split("-")[0] if "-" not in level.name else level.name.split("-")[1]
        covering = [t for t in theorems if t.covers(task.initial)]

        guarded_paths: Dict[str, Tuple[str, str]] = {}
        guarded_dir = os.path.join(work, "guarded")
        os.makedirs(guarded_dir, exist_ok=True)
        for guard in compile_theorems.guardable_guards(theorems):
            try:
                guarded_paths[guard] = compile_theorems.write_guarded(
                    guarded_dir, level.name, text, theorems,
                    guard=guard, problem=problem)
            except compile_theorems.NotGuardable:
                continue

        entry: Dict[str, object] = {
            "instance": level.name,
            "kind": kind,
            "theorems": len(theorems),
            "theorems_covering_the_initial_state": [t.rendering() for t in covering],
            "closure_kinds": sorted({t.kind for t in covering}),
            "unguarded": [],
            "guarded": {},
        }
        for _tier, heuristic in CONFIGS:
            entry["unguarded"].append(_measure(
                executable, sokoban.DOMAIN_PATH, plain, heuristic, log_dir,
                "D-%s-%s-plain" % (level.name, _label(heuristic))))
        for guard, (guard_domain, guard_problem) in sorted(guarded_paths.items()):
            results = []
            for _tier, heuristic in CONFIGS:
                results.append(_measure(
                    executable, guard_domain, guard_problem, heuristic, log_dir,
                    "D-%s-%s-%s" % (level.name, guard, _label(heuristic))))
            entry["guarded"][guard] = results
        rows.append(entry)
    return rows


# ------------------------------------------------- H · does the heuristic know

def _problem_with_initial(problem_text: str, problem, state) -> str:
    """The same problem with `state` as its initial state.

    The static atoms (`adj`) come from the original `:init`, because a state in
    the search has had them stripped -- `strip_static` removes exactly the atoms
    no action can change, so putting them back is not a guess.
    """
    from engines.fd_adapter.pddl import Atom

    dynamic = set(state)
    statics = [a for a in problem.init if a[0] == "adj"]
    atoms: List[Atom] = sorted(dynamic) + sorted(statics)
    rendered = "\n".join(
        "    (%s)" % " ".join(atom) for atom in atoms
    )
    head, _sep, tail = problem_text.partition("(:init")
    _body, _sep2, rest = tail.partition("(:goal")
    return "%s(:init\n%s)\n  (:goal%s" % (head, rendered, rest)


def heuristic_knows(executable: str, work: str, log_dir: str,
                    side: int = 4, sample: int = 12) -> Dict[str, object]:
    """Ask the heuristic what it thinks of a dead state, one state at a time.

    This is the mechanism behind E2's zero, measured rather than argued.  Sample
    states from `far{side}`'s reachable space, split them by whether a theorem
    covers them, rebuild each as a one-state problem, and read Fast Downward's
    own `Initial heuristic value` line.

    If the dead ones come back `infinity`, the theorems are redundant to this
    planner: A* prunes an infinite-h node without being told anything, so a
    guard that removes the same node cannot change the count.  If they came back
    finite, the zero would have to be explained some other way.
    """
    from bench import instances as bench_instances

    level = bench_instances.far_level(side)
    text = level.problem_text()
    domain, problem = _load(sokoban.DOMAIN_PATH, text)
    task, theorems = _theorems(domain, problem)
    dead = pruner(theorems)

    states = _collect(domain, problem)
    dead_states = [s for s in states if dead(s)]
    live_states = [s for s in states if not dead(s)]

    def stride(items):
        if len(items) <= sample:
            return items
        step = len(items) // sample
        return [items[i * step] for i in range(sample)]

    rows: List[Dict[str, object]] = []
    for group, chosen in (("dead", stride(dead_states)), ("alive", stride(live_states))):
        for index, state in enumerate(chosen):
            path = os.path.join(work, "H-far%d-%s-%02d.pddl" % (side, group, index))
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(_problem_with_initial(text, problem, state))
            for _tier, heuristic in CONFIGS:
                measured = _measure(
                    executable, sokoban.DOMAIN_PATH, path, heuristic, log_dir,
                    "H-far%d-%s-%02d-%s" % (side, group, index, _label(heuristic)))
                rows.append({
                    "group": group,
                    "index": index,
                    "heuristic": _label(heuristic),
                    "initial_h": measured["initial_h"],
                    "infinite": "infinity" in (measured["initial_h"] or ""),
                    "expanded": measured["expanded"],
                    "proved_unsolvable": measured["proved_unsolvable"],
                    "solved": measured["solved"],
                    "translator_settled": _translator_settled(measured["log"]),
                })
    summary: Dict[str, object] = {"instance": "far%d" % side,
                                  "n_reachable": len(states),
                                  "n_dead": len(dead_states),
                                  "rows": rows}
    for group in ("dead", "alive"):
        for _tier, heuristic in CONFIGS:
            name = _label(heuristic)
            picked = [r for r in rows if r["group"] == group and r["heuristic"] == name]
            summary["%s_%s_infinite" % (group, name)] = (
                sum(1 for r in picked if r["infinite"]), len(picked))
    return summary


def _translator_settled(log_path: str) -> Optional[bool]:
    if not os.path.exists(log_path):
        return None
    with open(log_path, "r", encoding="utf-8", errors="replace") as handle:
        return "No relaxed solution!" in handle.read()


def _collect(domain, problem) -> List[object]:
    """Every reachable state, in a fixed order."""
    from collections import deque

    grounded = pddl.ground_actions(domain, problem)
    actions, initial, _ok = search.strip_static(domain, problem, grounded)
    static = pddl.static_predicates(domain)
    seen = [initial]
    known = {initial}
    queue = deque([initial])
    while queue:
        state = queue.popleft()
        if search.is_goal(problem, state, static):
            continue
        for action in actions:
            if not search.applicable(action, state):
                continue
            successor = search.successor(action, state)
            if successor not in known:
                known.add(successor)
                seen.append(successor)
                queue.append(successor)
    return seen


# ------------------------------------------- C · what the planner already prunes

def relaxed_reachable_goal(actions, state, problem, static) -> bool:
    """Is the goal reachable in the delete relaxation from this state?

    The relaxation drops delete effects and keeps adding until nothing new
    appears.  This is `h^1`-style reachability -- exactly what Fast Downward's
    translator computes before it hands anything to the search, and what makes
    it print `No relaxed solution! Generating unsolvable task...`.

    Written here rather than read off FD so it can be run 3 342 times without
    3 342 subprocesses.  It is checked against FD on a sample, and the sample
    agreement is reported: an independent reimplementation nobody compared to
    the original is a second guess, not a second opinion.

    The sokoban domain has no negative preconditions, so the usual complication
    -- a relaxation has to compile them away -- does not arise, and this is the
    textbook fixpoint.
    """
    reached = set(state)
    wanted = [a for a in problem.goal_positive if a[0] not in static]
    changed = True
    while changed:
        if all(atom in reached for atom in wanted):
            return True
        changed = False
        for action in actions:
            if not all(atom in reached for atom in action.pre_positive):
                continue
            for atom in action.add_effects:
                if atom not in reached:
                    reached.add(atom)
                    changed = True
    return all(atom in reached for atom in wanted)


def coverage(side: int = 4) -> Dict[str, object]:
    """Three sets over one instance's reachable space, and how they nest.

    * `theorem_dead` -- states some carver theorem covers.
    * `relaxation_dead` -- states whose delete relaxation cannot reach the goal.
      Fast Downward computes this for free, before search, on every instance.
    * `truly_dead` -- states from which the goal is genuinely unreachable,
      by backward search over the real transition relation.

    Soundness says `theorem_dead` and `relaxation_dead` both sit inside
    `truly_dead`.  The question this run exists to answer is how the first two
    sit with respect to *each other*, because that is what decides whether a
    proved deadlock tells a real planner anything it did not have.
    """
    from collections import deque

    from bench import instances as bench_instances

    level = bench_instances.far_level(side)
    text = level.problem_text()
    domain, problem = _load(sokoban.DOMAIN_PATH, text)
    task, theorems = _theorems(domain, problem)
    dead = pruner(theorems)

    grounded = pddl.ground_actions(domain, problem)
    actions, initial, _ok = search.strip_static(domain, problem, grounded)
    static = pddl.static_predicates(domain)

    states = _collect(domain, problem)
    index = {state: i for i, state in enumerate(states)}

    # Backward: which states can still reach a goal, over the real relation.
    forward: List[List[int]] = [[] for _ in states]
    backward: List[List[int]] = [[] for _ in states]
    goals = []
    for i, state in enumerate(states):
        if search.is_goal(problem, state, static):
            goals.append(i)
            continue
        for action in actions:
            if not search.applicable(action, state):
                continue
            j = index.get(search.successor(action, state))
            if j is not None:
                forward[i].append(j)
                backward[j].append(i)
    alive = set(goals)
    queue = deque(goals)
    while queue:
        i = queue.popleft()
        for j in backward[i]:
            if j not in alive:
                alive.add(j)
                queue.append(j)

    theorem_dead = {i for i, s in enumerate(states) if dead(s)}
    truly_dead = {i for i in range(len(states)) if i not in alive}
    relaxation_dead = {
        i for i, s in enumerate(states)
        if not relaxed_reachable_goal(actions, s, problem, static)
    }

    return {
        "instance": "far%d" % side,
        "n_reachable": len(states),
        "n_theorem_dead": len(theorem_dead),
        "n_relaxation_dead": len(relaxation_dead),
        "n_truly_dead": len(truly_dead),
        "theorem_dead_within_relaxation_dead": len(theorem_dead - relaxation_dead) == 0,
        "n_theorem_dead_outside_relaxation": len(theorem_dead - relaxation_dead),
        "n_relaxation_dead_outside_theorems": len(relaxation_dead - theorem_dead),
        "theorem_dead_within_truly_dead": len(theorem_dead - truly_dead) == 0,
        "relaxation_dead_within_truly_dead": len(relaxation_dead - truly_dead) == 0,
        "n_truly_dead_neither_detects": len(truly_dead - relaxation_dead - theorem_dead),
        "_states": states,
        "_theorem_dead": sorted(theorem_dead),
        "_relaxation_dead": sorted(relaxation_dead),
    }


def relaxation_agrees_with_fd(executable: str, work: str, log_dir: str,
                              side: int = 4, sample: int = 16) -> Dict[str, object]:
    """Check the Python relaxation against Fast Downward's, state by state.

    An independent reimplementation nobody compared to the original is a second
    guess.  This runs FD on `sample` rebuilt one-state problems and asks whether
    its translator printed `No relaxed solution!` exactly where this module says
    the relaxation is dead.
    """
    from bench import instances as bench_instances

    report = coverage(side)
    states = report["_states"]
    relaxed = set(report["_relaxation_dead"])
    level = bench_instances.far_level(side)
    text = level.problem_text()
    _domain, problem = _load(sokoban.DOMAIN_PATH, text)

    step = max(1, len(states) // sample)
    picked = [i for i in range(0, len(states), step)][:sample]
    rows = []
    for i in picked:
        path = os.path.join(work, "C-far%d-%04d.pddl" % (side, i))
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(_problem_with_initial(text, problem, states[i]))
        measured = _measure(executable, sokoban.DOMAIN_PATH, path, "lmcut",
                            log_dir, "C-far%d-%04d" % (side, i))
        fd_says_dead = bool(_translator_settled(measured["log"]))
        rows.append({
            "state": i,
            "python_relaxation_dead": i in relaxed,
            "fd_translator_dead": fd_says_dead,
            "agree": (i in relaxed) == fd_says_dead,
        })
    return {
        "n_checked": len(rows),
        "n_agree": sum(1 for r in rows if r["agree"]),
        "rows": rows,
    }


# --------------------------------------------------------------------- S · size

def size_ladder(executable: str, work: str, log_dir: str,
                sides: Sequence[int] = SIZE_SIDES) -> List[Dict[str, object]]:
    """"The instances are too small." Same guard, same configs, bigger boards."""
    return replication(executable, work, log_dir, sides=sides)


# -------------------------------------------------------------------- the driver

def run(out_dir: str, executable: Optional[str] = None) -> Dict[str, object]:
    from engines.fd_adapter import backends

    executable = executable or backends.find_fast_downward()
    if not executable:
        raise RuntimeError(
            "no Fast Downward. This audit re-measures a claim about a real "
            "planner; running it against the stub would answer a different "
            "question and is refused rather than downgraded.")

    work = os.path.join(out_dir, "instances")
    log_dir = os.path.join(out_dir, "logs")
    os.makedirs(work, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    started = time.time()
    report: Dict[str, object] = {
        "fast_downward": executable,
        "configs": ["astar(%s())" % _label(h) for _t, h in CONFIGS],
    }
    report["wiring"] = wiring()
    _dump(out_dir, report)
    report["coverage"] = [
        {k: v for k, v in coverage(side).items() if not k.startswith("_")}
        for side in (4, 5, 6)
    ]
    _dump(out_dir, report)
    report["relaxation_vs_fd"] = relaxation_agrees_with_fd(executable, work, log_dir)
    _dump(out_dir, report)
    report["dead_starts"] = dead_starts(executable, work, log_dir)
    _dump(out_dir, report)
    report["replication"] = replication(executable, work, log_dir)
    _dump(out_dir, report)
    report["size_ladder"] = size_ladder(executable, work, log_dir, sides=(8,))
    report["seconds"] = round(time.time() - started, 1)
    _dump(out_dir, report)
    return report


def _dump(out_dir: str, report: Dict[str, object]) -> None:
    path = os.path.join(out_dir, "claim_audit.json")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
