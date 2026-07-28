"""The three-rung ladder: who is chosen, what they are asked, what they answer.

Fast Downward is installed here now, but this file is written so that none of it
depends on that -- the suite must stay green on a machine without one.  Three
techniques, in order of how much they can prove:

* the selection rule is tested by injecting the discovery function, so every
  clause of `choose_tier` is covered on a machine with no planner at all;
* the driver protocol -- the command line, the plan file, a proof of
  unsolvability versus a search that gave up -- is tested against a conformance
  script that speaks it.  A fake planner cannot show that Fast Downward is
  correct, but the defect being fixed here is in *this* code's reading of the
  protocol, and that is exactly what a fake can pin down.  What the fake says is
  not invented: its exit codes and log lines were read off the real planner's
  behaviour, which is the only reason they are worth asserting on;
* the cross-rung agreement tests are skipped until a real planner is reachable
  and start running the moment `FAST_DOWNWARD` points at one.
"""

import json
import os
import textwrap

import pytest

from engines import fd_adapter
from engines.fd_adapter import backends, fuzz
from engines.fd_adapter.pddl import parse_domain, parse_problem
from engines.fd_adapter.validate import validate_plan

HAND_VERIFIED_OPTIMUM = 5

FIXTURE_PLAN = (
    "(pick ball1 rooma left)\n"
    "(pick ball2 rooma right)\n"
    "(move rooma roomb)\n"
    "(drop ball1 roomb left)\n"
    "(drop ball2 roomb right)\n"
    "; cost = 5 (unit cost)\n"
)

# A valid but wasteful plan: one ball at a time, four extra actions.  Good
# enough for the satisficing rung, and wrong for an optimal one.
FIXTURE_PLAN_LONG = (
    "(pick ball1 rooma left)\n"
    "(move rooma roomb)\n"
    "(drop ball1 roomb left)\n"
    "(move roomb rooma)\n"
    "(pick ball2 rooma left)\n"
    "(move rooma roomb)\n"
    "(drop ball2 roomb left)\n"
)

# A Fast Downward stand-in.  It implements the part of the driver's contract
# this adapter depends on and nothing else: write the plan file and exit 0, or
# exit with one of the codes that mean "no plan file, and here is why".  Every
# invocation records its argv next to the script, so the tests can assert on the
# command line that was built rather than only on the result.
FAKE_FAST_DOWNWARD = textwrap.dedent(
    '''\
    import json
    import os
    import sys

    HERE = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(HERE, "argv.json"), "w", encoding="utf-8") as fh:
        json.dump(sys.argv[1:], fh)

    mode = os.environ.get("FAKE_FD_MODE", "plan")
    plan_path = sys.argv[sys.argv.index("--plan-file") + 1]

    if mode in ("plan", "long", "numbered"):
        source = "plan.txt" if mode != "long" else "plan-long.txt"
        with open(os.path.join(HERE, source), encoding="utf-8") as fh:
            text = fh.read()
        target = plan_path + ".1" if mode == "numbered" else plan_path
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(text)
        sys.exit(0)
    if mode == "exhausted":
        # What the real planner does on a provably unsolvable instance: the
        # generic "no plan" exit code, and the verdict only in the log.
        sys.stdout.write("Completely explored state space -- no solution!\\n")
        sys.exit(12)
    if mode == "structurally_unsat":
        sys.exit(11)
    if mode == "translate_unsat":
        sys.exit(10)
    if mode == "incomplete":
        sys.stdout.write("Search stopped without finding a solution.\\n")
        sys.exit(12)
    sys.stderr.write("fake Fast Downward fell over\\n")
    sys.exit(1)
    '''
)


@pytest.fixture(scope="module")
def instance():
    domain = parse_domain(fd_adapter.read(fd_adapter.DOMAIN_PATH))
    problem = parse_problem(fd_adapter.read(fd_adapter.PROBLEM_PATH))
    return domain, problem


@pytest.fixture
def fake_fd(tmp_path, monkeypatch):
    """A `fast-downward.py` the discovery function will find, and this rig can run."""
    home = tmp_path / "fake-fd"
    home.mkdir()
    (home / "fast-downward.py").write_text(FAKE_FAST_DOWNWARD, encoding="utf-8")
    (home / "plan.txt").write_text(FIXTURE_PLAN, encoding="utf-8")
    (home / "plan-long.txt").write_text(FIXTURE_PLAN_LONG, encoding="utf-8")
    for variable in backends.FD_ENV_VARS:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("FAST_DOWNWARD", str(home))
    monkeypatch.setenv("FAKE_FD_MODE", "plan")
    return home


def recorded_argv(home) -> list:
    with open(os.path.join(str(home), "argv.json"), encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------- the tier rule

def present(path="/nowhere/fast-downward.py"):
    return lambda: path


def absent():
    return None


def test_prefer_stub_wins_even_when_a_planner_is_installed():
    """Every committed artifact rides on this clause; it comes first for a reason."""
    assert backends.choose_tier(prefer="stub", discover=present()) == (backends.STUB, None)
    assert backends.choose_tier(prefer="stub-bfs", discover=present()) == (backends.STUB, None)


def test_the_optimal_rung_is_the_default_when_fast_downward_is_reachable():
    assert backends.choose_tier(discover=present()) == (
        backends.FD_OPTIMAL, "/nowhere/fast-downward.py"
    )


def test_no_planner_means_the_stub_answers():
    assert backends.choose_tier(discover=absent) == (backends.STUB, None)


def test_a_pruner_forces_the_stub():
    """Not a preference: Fast Downward has no pruning hook at all."""
    assert backends.choose_tier(prune=lambda state: False, discover=present()) == (
        backends.STUB, None
    )


def test_an_in_memory_instance_forces_the_stub():
    assert backends.choose_tier(on_disk=False, discover=present()) == (backends.STUB, None)


def test_a_named_rung_is_honoured():
    for tier in (backends.FD_OPTIMAL, backends.FD_SATISFICING):
        assert backends.choose_tier(prefer=tier, discover=present()) == (
            tier, "/nowhere/fast-downward.py"
        )


def test_a_named_rung_raises_rather_than_quietly_dropping_to_another():
    with pytest.raises(backends.FastDownwardMissing):
        backends.choose_tier(prefer=backends.FD_OPTIMAL, discover=absent)


def test_a_named_fd_rung_with_a_pruner_is_a_contradiction():
    with pytest.raises(ValueError):
        backends.choose_tier(
            prefer=backends.FD_OPTIMAL, prune=lambda state: False, discover=present()
        )


def test_a_named_fd_rung_needs_files_on_disk():
    with pytest.raises(ValueError):
        backends.choose_tier(prefer=backends.FD_SATISFICING, on_disk=False,
                             discover=present())


def test_an_unknown_backend_name_is_refused():
    with pytest.raises(ValueError):
        backends.choose_tier(prefer="pyperplan", discover=present())


# --------------------------------------------------------- the search configs

def test_each_rung_names_the_configuration_it_runs():
    assert backends.fd_search_config(backends.STUB) == "bfs"
    assert backends.fd_search_config(backends.FD_OPTIMAL) == "astar(lmcut())"
    assert backends.fd_search_config(backends.FD_OPTIMAL, "ipdb") == "astar(ipdb())"
    assert backends.fd_search_config(backends.FD_SATISFICING) == "--alias lama-first"


def test_an_unknown_heuristic_is_refused():
    with pytest.raises(ValueError):
        backends.fd_search_config(backends.FD_OPTIMAL, "hff")


def test_the_optimal_rung_is_asked_with_a_search_string():
    command, config = backends.fd_command(
        "/fd/fast-downward.py", "d.pddl", "p.pddl", "out", backends.FD_OPTIMAL, "ipdb"
    )
    assert config == "astar(ipdb())"
    assert command[-2:] == ["--search", "astar(ipdb())"]
    assert command[command.index("--plan-file") + 1] == "out"
    assert "--alias" not in command


def test_the_satisficing_rung_is_asked_by_alias_before_the_files():
    command, config = backends.fd_command(
        "/fd/fast-downward.py", "d.pddl", "p.pddl", "out", backends.FD_SATISFICING
    )
    assert config == "--alias lama-first"
    assert command[command.index("--alias") + 1] == "lama-first"
    assert command.index("--alias") < command.index("d.pddl")
    assert "--search" not in command


def test_a_bare_search_binary_gets_an_explicit_configuration_and_says_so():
    """No driver means no aliases; the payload must not claim LAMA it did not run."""
    command, config = backends.fd_command(
        "/fd/downward", "d.pddl", "p.pddl", "out", backends.FD_SATISFICING
    )
    assert config == backends.FD_SATISFICING_SEARCH
    assert "--alias" not in command
    assert command[-2:] == ["--search", backends.FD_SATISFICING_SEARCH]


# ------------------------------------------------- the driver protocol, faked

def test_a_faked_planner_answers_on_the_optimal_rung(fake_fd, instance):
    domain, problem = instance
    plan = fd_adapter.solve()
    assert plan.backend == backends.FD_OPTIMAL
    assert plan.search == "astar(lmcut())"
    assert plan.optimal is True
    assert plan.length == HAND_VERIFIED_OPTIMUM
    assert validate_plan(domain, problem, plan.actions)
    assert plan.as_json()["backend"] == backends.FD_OPTIMAL
    assert plan.as_json()["search"] == "astar(lmcut())"


def test_the_satisficing_rung_reports_itself_as_not_optimal(fake_fd, instance, monkeypatch):
    domain, problem = instance
    monkeypatch.setenv("FAKE_FD_MODE", "long")
    plan = fd_adapter.solve(prefer=backends.FD_SATISFICING)
    assert plan.backend == backends.FD_SATISFICING
    assert plan.optimal is False
    assert plan.length > HAND_VERIFIED_OPTIMUM
    assert validate_plan(domain, problem, plan.actions)   # still a plan
    assert recorded_argv(fake_fd)[:2] == ["--alias", "lama-first"]


def test_the_heuristic_reaches_the_command_line(fake_fd):
    fd_adapter.solve(heuristic="ipdb")
    assert recorded_argv(fake_fd)[-2:] == ["--search", "astar(ipdb())"]


@pytest.mark.parametrize("mode", ["exhausted", "structurally_unsat", "translate_unsat"])
def test_a_proved_unsolvable_instance_says_so_by_type(fake_fd, monkeypatch, mode):
    """The defect the cold-start track reported: a proof read as a crash."""
    monkeypatch.setenv("FAKE_FD_MODE", mode)
    with pytest.raises(fd_adapter.NoPlanExists):
        fd_adapter.solve()


def test_a_proof_is_a_result_not_an_exception_for_solve_parsed(fake_fd, instance,
                                                               monkeypatch):
    domain, problem = instance
    monkeypatch.setenv("FAKE_FD_MODE", "exhausted")
    plan, result = fd_adapter.solve_parsed(
        domain, problem,
        domain_path=fd_adapter.DOMAIN_PATH, problem_path=fd_adapter.PROBLEM_PATH,
    )
    assert plan is None
    assert result.plan is None


def test_giving_up_is_not_a_proof_and_stays_a_hard_error(fake_fd, monkeypatch):
    """An incomplete search giving up says nothing about whether a plan exists.

    Same exit code as the proof above -- 12 either way, which is why this is
    decided on what the planner said and not on how it exited.
    """
    monkeypatch.setenv("FAKE_FD_MODE", "incomplete")
    with pytest.raises(RuntimeError) as raised:
        fd_adapter.solve()
    assert not isinstance(raised.value, fd_adapter.NoPlanExists)


def test_the_satisficing_rung_is_never_allowed_to_prove_unsolvability(fake_fd,
                                                                     monkeypatch):
    """Exhaustion under a portfolio's cost bound is not a proof of no plan.

    The same log that counts as a proof on the optimal rung is refused here.
    Conservative on purpose: the cost is one re-ask, and the alternative is this
    rig publishing an unsolvability claim no planner made.
    """
    monkeypatch.setenv("FAKE_FD_MODE", "exhausted")
    assert backends.proves_unsolvable(
        backends.FD_OPTIMAL, 12, "Completely explored state space -- no solution!")
    assert not backends.proves_unsolvable(
        backends.FD_SATISFICING, 12, "Completely explored state space -- no solution!")
    with pytest.raises(RuntimeError) as raised:
        fd_adapter.solve(prefer="fd-satisficing")
    assert not isinstance(raised.value, fd_adapter.NoPlanExists)


def test_a_crashed_planner_stays_a_hard_error(fake_fd, monkeypatch):
    monkeypatch.setenv("FAKE_FD_MODE", "crash")
    with pytest.raises(RuntimeError) as raised:
        fd_adapter.solve()
    assert not isinstance(raised.value, fd_adapter.NoPlanExists)
    assert "fell over" in str(raised.value)


def test_a_numbered_plan_file_is_found(fake_fd, monkeypatch):
    """Anytime configurations write `sas_plan.1`, not `sas_plan`."""
    monkeypatch.setenv("FAKE_FD_MODE", "numbered")
    plan = fd_adapter.solve()
    assert plan.length == HAND_VERIFIED_OPTIMUM


def test_unsat_on_the_bundled_rung_raises_the_same_type(tmp_path):
    """Both rungs agree on what unsolvable looks like from outside.

    A ball cannot be in two rooms at once -- `pick` deletes `at`, and `drop`
    adds exactly one -- so this goal is unreachable, and the bundled search
    exhausts the space and says so.
    """
    problem_path = tmp_path / "impossible.pddl"
    problem_path.write_text(
        "(define (problem impossible) (:domain gripper)\n"
        "  (:objects rooma roomb - room ball1 - ball left right - gripper)\n"
        "  (:init (at-robby rooma) (free left) (free right) (at ball1 rooma))\n"
        "  (:goal (and (at ball1 rooma) (at ball1 roomb))))\n",
        encoding="utf-8",
    )
    with pytest.raises(fd_adapter.NoPlanExists):
        fd_adapter.solve(fd_adapter.DOMAIN_PATH, str(problem_path), prefer="stub")


# -------------------------------------------------------- determinism guards

def test_the_artifact_path_stays_on_the_bundled_rung(fake_fd):
    """`run()` writes candidates.jsonl; a planner on PATH must not change bytes."""
    plan = fd_adapter.run()
    assert plan.backend == backends.STUB
    assert plan.as_json()["search"] == "bfs"


def test_the_stub_payload_is_unchanged_by_the_ladder():
    """The `search`/`backend` fields the committed artifact already carries."""
    payload = fd_adapter.solve(prefer="stub").as_json()
    assert payload["backend"] == "stub-bfs"
    assert payload["search"] == "bfs"
    assert list(payload) == [
        "domain", "problem", "backend", "search", "optimal", "length", "actions",
    ]


# ------------------------------------------------------- the differential fuzz

def test_the_closed_form_reproduces_the_hand_verified_optimum():
    """The oracle is checked against the one number that was derived by hand."""
    assert fuzz.optimum(2) == HAND_VERIFIED_OPTIMUM
    assert [fuzz.optimum(n) for n in range(5)] == [0, 3, 5, 9, 11]


def test_random_instances_are_a_function_of_the_seed():
    first = fuzz.random_instances(rounds=6, seed=7)
    second = fuzz.random_instances(rounds=6, seed=7)
    assert [(i.movers, i.settled) for i in first] == [(i.movers, i.settled) for i in second]
    assert fuzz.random_instances(rounds=6, seed=8) != first


def test_every_rung_agrees_with_the_closed_form_optimum(tmp_path):
    """The differential itself.

    Without a planner this compares the bundled search against arithmetic, one
    instance at a time; with one it compares three planners as well, and does
    more rounds because it can afford fewer of them per second.
    """
    executable = backends.find_fast_downward()
    rounds = 12 if executable is not None else 6
    comparisons = fuzz.differential(str(tmp_path), rounds=rounds)
    assert len(comparisons) == rounds
    for comparison in comparisons:
        assert comparison.disagreements() == [], comparison
        assert backends.STUB in comparison.lengths


def test_every_fuzzed_plan_passes_the_independent_validator(tmp_path):
    """A satisficing plan is still a plan; nothing is exempt from replay."""
    domain = parse_domain(fd_adapter.read(fd_adapter.DOMAIN_PATH))
    for instance in fuzz.random_instances(rounds=4):
        _, problem_path = fuzz.write(instance, str(tmp_path))
        problem = parse_problem(fd_adapter.read(problem_path))
        plan = fd_adapter.solve(fd_adapter.DOMAIN_PATH, problem_path, prefer="stub")
        assert validate_plan(domain, problem, plan.actions)
        assert plan.length == instance.optimum


# --------------------------------------------- the rungs, against a real planner

@pytest.mark.skipif(
    backends.find_fast_downward() is None, reason="Fast Downward is not installed"
)
def test_the_optimal_rungs_and_the_stub_return_the_same_length(instance):
    """Same optimum, not necessarily the same actions -- optimality is not uniqueness."""
    domain, problem = instance
    lengths = {}
    for tier, heuristic in (
        (backends.STUB, None),
        (backends.FD_OPTIMAL, "lmcut"),
        (backends.FD_OPTIMAL, "ipdb"),
    ):
        plan = fd_adapter.solve(prefer=tier, heuristic=heuristic)
        assert validate_plan(domain, problem, plan.actions)
        assert plan.optimal is True
        lengths[(tier, heuristic)] = plan.length
    assert set(lengths.values()) == {HAND_VERIFIED_OPTIMUM}


@pytest.mark.skipif(
    backends.find_fast_downward() is None, reason="Fast Downward is not installed"
)
def test_the_satisficing_rung_returns_a_valid_plan_no_shorter_than_the_optimum(instance):
    domain, problem = instance
    plan = fd_adapter.solve(prefer=backends.FD_SATISFICING)
    assert plan.backend == backends.FD_SATISFICING
    assert plan.optimal is False
    assert validate_plan(domain, problem, plan.actions)
    assert plan.length >= HAND_VERIFIED_OPTIMUM
