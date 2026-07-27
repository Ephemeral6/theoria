"""deadlock_carver: the theorems are true, minimal, and worth nodes.

Three things need separate evidence and get it:

  * the mutexes the proofs rest on are the ones the world really has;
  * every theorem is **sound** -- checked by exhausting the state space and
    confirming that no state matching a dead pattern can reach a goal, which
    shares nothing with the proof that produced the theorem;
  * pruning changes the node count and nothing else.
"""

from collections import deque

import pytest

from common.jsonio import read_jsonl
from engines import deadlock_carver as dc
from engines.fd_adapter import search as fd_search
from engines.fd_adapter.pddl import ground_actions, parse_domain, parse_problem
from fixtures import sokoban
from tools.validate_candidates import validate_file


@pytest.fixture(scope="module")
def domain():
    with open(sokoban.DOMAIN_PATH, "r", encoding="utf-8") as fh:
        return parse_domain(fh.read())


def problem_of(level):
    with open(level.path, "r", encoding="utf-8") as fh:
        return parse_problem(fh.read())


@pytest.fixture(scope="module")
def open4(domain):
    problem = problem_of(sokoban.OPEN4)
    task = dc.Task.build(domain, problem)
    return task, dc.carve(task)


@pytest.fixture(scope="module")
def ring(domain):
    problem = problem_of(sokoban.RING)
    task = dc.Task.build(domain, problem)
    return task, dc.carve(task)


# ----------------------------------------------------------------- mutexes

def test_the_derived_mutexes_are_the_ones_the_world_has(open4):
    task, _ = open4
    mutexes = task.mutexes
    # A cell holds at most one thing...
    assert mutexes.mutex(("at", "b1", "c22"), ("clear", "c22"))
    assert mutexes.mutex(("at", "b1", "c22"), ("at-player", "c22"))
    assert mutexes.mutex(("at", "b1", "c22"), ("at", "b2", "c22"))
    # ... and a box is in at most one place.
    assert mutexes.mutex(("at", "b1", "c22"), ("at", "b1", "c23"))
    # None of which makes everything mutex with everything.
    assert mutexes.co_possible(("at", "b1", "c22"), ("at", "b2", "c33"))
    assert mutexes.co_possible(("at", "b1", "c22"), ("clear", "c23"))


def test_a_pattern_that_describes_no_state_proves_nothing(open4):
    """Two boxes on one cell is `dead` only vacuously; the carver refuses it."""
    task, _ = open4
    pattern = (("at", "b1", "c22"), ("at", "b2", "c22"))
    assert not task.mutexes.consistent(pattern)
    assert dc.prove(task, pattern) is None


# ---------------------------------------------------------------- theorems

def test_the_box_in_a_dead_corner_theorem_is_actually_produced(open4):
    """Theoria 1.9's own example, in the engine's own words."""
    _, theorems = open4
    renderings = {t.rendering() for t in theorems}
    for corner in ("c11", "c14", "c41", "c44"):
        for box in ("b1", "b2"):
            assert "at(%s,%s) AND not-goal => dead" % (box, corner) in renderings


def test_corner_theorems_need_no_mutex_reasoning_at_all(open4):
    """Grounding already deleted every push out of a corner (D-016)."""
    _, theorems = open4
    corners = [t for t in theorems if t.size == 1]
    assert corners and all(t.kind == "no_deleting_action" for t in corners)
    assert all(t.n_deleting_actions == 0 for t in corners)


def test_the_pair_theorems_are_the_wall_line_deadlocks(open4):
    """Two boxes side by side against a wall: pushes exist and every one is blocked."""
    _, theorems = open4
    pairs = [t for t in theorems if t.size == 2]
    assert pairs
    assert all(t.kind == "deleting_actions_blocked" for t in pairs)
    assert all(t.n_deleting_actions == len(t.blocked) > 0 for t in pairs)
    assert {t.rendering() for t in pairs} >= {
        "at(b1,c12) AND at(b2,c13) AND not-goal => dead",
        "at(b1,c42) AND at(b2,c43) AND not-goal => dead",
    }


def test_every_theorem_is_minimal(open4):
    """A pair whose half is already dead would double-count in the node account."""
    _, theorems = open4
    singletons = {t.pattern[0] for t in theorems if t.size == 1}
    for theorem in theorems:
        if theorem.size == 2:
            assert not set(theorem.pattern) & singletons


def test_the_carver_stays_inside_its_documented_pattern_width(open4):
    _, theorems = open4
    assert all(t.size <= dc.MAX_PATTERN for t in theorems)


# ------------------------------------------------------------- soundness

def _explore(domain, problem):
    """The reachable states, and which of them can still reach a goal.

    A forward BFS then a backward closure -- deliberately not the carver's
    argument, and not the planner's either.  This is the referee.
    """
    actions, start, _ = fd_search.strip_static(
        domain, problem, ground_actions(domain, problem)
    )
    static = fd_search.static_predicates(domain)
    edges = {}
    seen = {start}
    queue = deque([start])
    while queue:
        state = queue.popleft()
        targets = []
        for action in actions:
            if not fd_search.applicable(action, state):
                continue
            nxt = fd_search.successor(action, state)
            targets.append(nxt)
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
        edges[state] = targets

    winning = {s for s in seen if fd_search.is_goal(problem, s, static)}
    changed = True
    while changed:
        changed = False
        for state, targets in edges.items():
            if state in winning:
                continue
            if any(t in winning for t in targets):
                winning.add(state)
                changed = True
    return seen, winning


@pytest.mark.parametrize("level", [sokoban.OPEN4, sokoban.RING])
def test_no_theorem_ever_condemns_a_state_that_could_still_win(domain, level):
    problem = problem_of(level)
    task = dc.Task.build(domain, problem)
    theorems = dc.carve(task)
    reachable, winning = _explore(domain, problem)
    dead = dc.pruner(theorems)

    condemned = [s for s in reachable if dead(s)]
    assert condemned, "the theorems match no reachable state -- nothing was tested"
    assert not [s for s in condemned if s in winning]


def test_the_pruner_matches_exactly_the_states_the_patterns_describe(ring):
    task, theorems = ring
    dead = dc.pruner(theorems)
    corner = ("at", "b1", "c11")
    assert dead(frozenset({corner, ("at-player", "c12")}))
    assert not dead(frozenset({("at", "b1", "c12"), ("at-player", "c11")}))


# ----------------------------------------------------------- the node account

def test_pruning_pays_on_a_solvable_instance_and_changes_nothing_else(domain):
    problem = problem_of(sokoban.OPEN4FAR)
    task = dc.Task.build(domain, problem)
    report = dc.pruning_report(domain, problem, dc.carve(task))

    assert report.baseline.length == report.pruned.length == 11
    assert report.same_answer
    assert report.baseline.expansions == 808
    assert report.pruned.expansions == 571
    assert report.saved == 237
    assert report.ratio < 0.75


def test_pruning_pays_most_where_the_search_has_to_exhaust(domain):
    """Proving `no plan` means visiting everything -- unless half of it is dead."""
    problem = problem_of(sokoban.RING_STUCK)
    task = dc.Task.build(domain, problem)
    report = dc.pruning_report(domain, problem, dc.carve(task))

    assert report.baseline.plan is None and report.pruned.plan is None
    assert (report.baseline.expansions, report.pruned.expansions) == (44, 22)
    assert report.pruned.pruned > 0


def test_pruning_is_a_no_op_when_the_answer_lies_shallower_than_any_deadlock(domain):
    """Honest negative result: on `open4` the theorems are true and buy nothing."""
    problem = problem_of(sokoban.OPEN4)
    task = dc.Task.build(domain, problem)
    report = dc.pruning_report(domain, problem, dc.carve(task))
    assert report.saved == 0
    assert report.baseline.length == report.pruned.length == 6


# ---------------------------------------------------------------- emission

def test_the_emitted_stream_satisfies_the_frozen_schema(domain, tmp_path):
    out = str(tmp_path / "candidates.jsonl")
    problem = problem_of(sokoban.OPEN4FAR)
    task, theorems, report = dc.run(domain, problem, out_path=out,
                                    timestamp="2026-07-27T00:00:00Z")
    assert validate_file(out) == []
    rows = read_jsonl(out)
    assert len(rows) == len(theorems) + 1

    assert all(row["engine"] == "fd_adapter" for row in rows)
    assert all(row["payload"]["producer"] == "deadlock_carver" for row in rows)
    assert all(row["status"] == "candidate" for row in rows)

    invariants = [r for r in rows if r["kind"] == "invariant"]
    assert len(invariants) == len(theorems)
    assert all(r["payload"]["form"] == "conditional_unsolvability" for r in invariants)

    account = [r for r in rows if r["kind"] == "plan"][0]
    assert account["payload"]["expansions_before"] == 808
    assert account["payload"]["expansions_after"] == 571
    assert account["payload"]["plan_length_unchanged"] is True


def test_the_carver_is_deterministic(domain):
    problem = problem_of(sokoban.OPEN4)
    first = [t.rendering() for t in dc.carve(dc.Task.build(domain, problem))]
    second = [t.rendering() for t in dc.carve(dc.Task.build(domain, problem))]
    assert first == second == sorted(first, key=lambda r: (r.count("AND"), r))
