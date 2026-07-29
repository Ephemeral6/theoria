"""E7's measurements, pinned so the conclusion cannot rot without a red test.

`DEADLOCK_CLAIM.md` argues from four numbers. Each of them is asserted here, at
the smallest size that carries it, so that a change to the carver, the fixture
or the relaxation shows up as a failing test rather than as a document that
quietly stopped being true.

The FD-dependent tests skip without a real planner and start running the moment
`FAST_DOWNWARD` points at one -- same convention as `test_fd_ladder.py`, same
reason: they are about a real planner by definition.
"""

import os

import pytest

from audit import claim, deadstart
from engines.fd_adapter import backends

pytestmark = pytest.mark.filterwarnings("ignore")


@pytest.fixture(scope="module")
def far4():
    return claim.coverage(4)


# ---------------------------------------------------------------- the mechanism

def test_the_delete_relaxation_is_exactly_the_true_dead_set(far4):
    """The finding. Not a subset -- equal, on every size measured."""
    assert far4["n_reachable"] == 3342
    assert far4["n_truly_dead"] == far4["n_relaxation_dead"] == 2904
    assert far4["relaxation_dead_within_truly_dead"]
    assert far4["n_truly_dead_neither_detects"] == 0


def test_the_theorems_are_a_strict_subset_of_what_the_relaxation_gets_free(far4):
    """Zero states detected by a theorem that the relaxation misses.

    This is the number `DEADLOCK_CLAIM.md` conditions its suggested wording on.
    A geometry where it stops being zero is the boundary case that document
    says to look for, and it should be found by this test failing, not by
    someone rereading the prose.
    """
    assert far4["n_theorem_dead"] == 1624
    assert far4["theorem_dead_within_relaxation_dead"]
    assert far4["n_theorem_dead_outside_relaxation"] == 0
    assert far4["n_relaxation_dead_outside_theorems"] == 1280


def test_the_theorems_are_sound(far4):
    """Whatever else is true, no theorem may condemn a state that could win."""
    assert far4["theorem_dead_within_truly_dead"]


# ------------------------------------------------------------- the pruner works

def test_the_pruner_is_connected_and_the_plan_survives():
    """'No speed-up' would mean nothing if nothing had been pruned."""
    rows = {row["instance"]: row for row in claim.wiring(sides=(4,))}
    far = rows["far4"]
    assert far["pruner_fired"] == 69
    assert far["states_cut"] == 237
    assert far["blind_expansions"] == 808
    assert far["pruned_expansions"] == 571
    assert far["plan_unchanged"]


def test_the_prize_is_not_small():
    """Between a sixth and a half of the reachable space is dead."""
    far = claim.wiring(sides=(4,))[0]
    assert far["dead_fraction_of_reachable"] > 0.45


# ------------------------------------------------------------- the instances

def test_the_dead_start_instances_really_start_dead():
    """A control that is not dead, and two that are -- one per theorem kind."""
    from engines.deadlock_carver.carve import Task, carve
    from engines.fd_adapter import pddl
    from fixtures import sokoban

    domain = pddl.parse_domain(open(sokoban.DOMAIN_PATH, encoding="utf-8").read())
    kinds = {}
    for level in deadstart.levels((4,)):
        problem = pddl.parse_problem(level.problem_text())
        task = Task.build(domain, problem)
        covering = [t for t in carve(task) if t.covers(task.initial)]
        kinds[level.name] = sorted({t.kind for t in covering})

    assert kinds["deadstart-corner4"] == ["no_deleting_action"]
    assert kinds["deadstart-pair4"] == ["deleting_actions_blocked"]
    assert kinds["alive-pair4"] == [], "the control must not start dead"


def test_the_two_theorem_kinds_do_not_split_on_the_relaxation():
    """The prediction `deadstart.py` was built on, and the result that refuted it.

    Both kinds are relaxation-dead. Asserted so that the docstring's reasoning
    and its refutation stay attached to each other.
    """
    from engines.fd_adapter import pddl, search
    from fixtures import sokoban

    domain = pddl.parse_domain(open(sokoban.DOMAIN_PATH, encoding="utf-8").read())
    static = pddl.static_predicates(domain)
    for name in ("deadstart-corner4", "deadstart-pair4"):
        level = next(l for l in deadstart.levels((4,)) if l.name == name)
        problem = pddl.parse_problem(level.problem_text())
        grounded = pddl.ground_actions(domain, problem)
        actions, initial, _ok = search.strip_static(domain, problem, grounded)
        assert not claim.relaxed_reachable_goal(actions, initial, problem, static), name

    live = next(l for l in deadstart.levels((4,)) if l.name == "alive-pair4")
    problem = pddl.parse_problem(live.problem_text())
    grounded = pddl.ground_actions(domain, problem)
    actions, initial, _ok = search.strip_static(domain, problem, grounded)
    assert claim.relaxed_reachable_goal(actions, initial, problem, static)


# --------------------------------------------------------- needs a real planner

@pytest.mark.skipif(
    backends.find_fast_downward() is None, reason="Fast Downward is not installed"
)
def test_the_python_relaxation_agrees_with_fast_downwards(tmp_path):
    """An independent reimplementation nobody compared is a second guess."""
    work = str(tmp_path / "instances")
    logs = str(tmp_path / "logs")
    os.makedirs(work, exist_ok=True)
    os.makedirs(logs, exist_ok=True)
    report = claim.relaxation_agrees_with_fd(
        backends.find_fast_downward(), work, logs, side=4, sample=8)
    assert report["n_agree"] == report["n_checked"] == 8


@pytest.mark.skipif(
    backends.find_fast_downward() is None, reason="Fast Downward is not installed"
)
def test_fast_downward_settles_a_dead_start_without_being_told(tmp_path):
    """The confirmation: both kinds, unguarded, zero expansions, h = infinity."""
    work = str(tmp_path / "instances")
    logs = str(tmp_path / "logs")
    os.makedirs(work, exist_ok=True)
    os.makedirs(logs, exist_ok=True)
    rows = {row["instance"]: row
            for row in claim.dead_starts(
                backends.find_fast_downward(), work, logs, sides=(4,))}

    for name in ("deadstart-corner4", "deadstart-pair4"):
        for measured in rows[name]["unguarded"]:
            assert measured["expanded"] == 0, (name, measured)
            assert "infinity" in (measured["initial_h"] or ""), (name, measured)
            assert measured["proved_unsolvable"], (name, measured)

    # And the control is genuinely searched, so the instrument can tell them apart.
    control = {m["heuristic"]: m for m in rows["alive-pair4"]["unguarded"]}
    assert control["lmcut"]["solved"]
    assert control["lmcut"]["expanded"] > 0
