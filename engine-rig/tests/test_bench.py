"""The bench, checked the way the bench checks the rig.

Everything here runs on a machine with no planner installed.  The log parser is
tested against Fast Downward output that is **committed** --
`runs/p13-fd-real/work/lmcut/run.log`, written by P-13 -- so the one part of this
package that depends on FD's exact wording has a regression test that does not
depend on FD being present.  The handful of checks that genuinely need a planner
skip, as the rest of this suite's FD tests do.
"""

import os

import pytest

from bench import compile_theorems, fdrun, instances as bench_instances, ladder
from bench import dividend as bench_dividend
from bench import toolchain
from engines import deadlock_carver as dc
from engines import fd_adapter
from engines.fd_adapter import backends
from fixtures import sokoban

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P13_LOG = os.path.join(HERE, "runs", "p13-fd-real", "work", "lmcut", "run.log")

FD = backends.find_fast_downward()
needs_fd = pytest.mark.skipif(FD is None, reason="no Fast Downward reachable")


# ---------------------------------------------------------------- the parser

def read_log():
    with open(P13_LOG, "r", encoding="utf-8") as fh:
        return fh.read()


def test_the_committed_p13_log_is_still_there():
    """The parser's only offline fixture. If this moves, the test below is blind."""
    assert os.path.isfile(P13_LOG), P13_LOG


def test_counters_parse_out_of_a_real_fd_log():
    """The numbers P-13's manifest quotes, recovered from the log it quoted them from.

    The manifest says "A* expands 8 states". That is the assertion below, and it
    is the one that fails if FD ever changes the wording of its statistics block.
    """
    log = read_log()
    assert fdrun._sum(fdrun._COUNTERS["expanded"], log) == 8
    assert fdrun._sum(fdrun._COUNTERS["generated"], log) == 22
    assert fdrun._sum(fdrun._COUNTERS["evaluated"], log) == 16
    assert fdrun._sum(fdrun._COUNTERS["reopened"], log) == 0
    assert fdrun._sum(fdrun._COUNTERS["dead_ends"], log) == 0


def test_the_progress_stamp_does_not_hide_the_counters():
    """FD stamps every search line with `[t=..., ... KB]`; the regexes allow it.

    This is the bug the first draft of this module had: with a bare `^` anchor
    every counter came back None and the table would have been full of blanks
    that looked like "the planner did not report", not "the parser missed".
    """
    log = read_log()
    assert "[t=" in log and "] Expanded" in log
    assert fdrun._sum(fdrun._COUNTERS["expanded"], log) is not None


def test_translator_lines_do_not_pollute_the_search_counters():
    """`Generated 17 rules.` is the translator's; the search's says `state(s)`."""
    log = read_log()
    assert "Generated 17 rules." in log
    # 22, the search's number -- not 39, which is what a loose regex would give.
    assert fdrun._sum(fdrun._COUNTERS["generated"], log) == 22


def test_until_last_jump_lines_are_not_counted_twice():
    """`Expanded until last jump: 0 state(s).` must not join the `Expanded` sum."""
    log = read_log()
    assert "Expanded until last jump:" in log
    assert fdrun._sum(fdrun._COUNTERS["expanded"], log) == 8


def test_translator_task_shape_parses():
    log = read_log()
    assert fdrun._sum(fdrun._TRANSLATOR["variables"], log) == 5
    assert fdrun._sum(fdrun._TRANSLATOR["facts"], log) == 14
    assert fdrun._sum(fdrun._TRANSLATOR["operators"], log) == 18


def test_times_parse_and_are_ordered():
    log = read_log()
    search = fdrun._last(fdrun._SEARCH_TIME, log)
    total = fdrun._last(fdrun._TOTAL_TIME, log)
    assert search is not None and total is not None
    assert 0 < search <= total


# ------------------------------------------------------- the instance ladders

def test_far_level_4_is_the_committed_open4far_fixture():
    """The generated ladder's bottom rung must *be* the fixture, not resemble it.

    `open4far` has an argued place in this rig -- the deadlock carver's README
    reasons about it. If the generalisation drifted, every dividend number above
    it would be measured on a board nobody had ever looked at.
    """
    generated = bench_instances.far_level(4)
    assert generated.grid == sokoban.OPEN4FAR.grid
    assert generated.player == sokoban.OPEN4FAR.player
    assert generated.boxes == sokoban.OPEN4FAR.boxes
    assert generated.goals == sokoban.OPEN4FAR.goals


def test_ring_level_4_is_the_committed_ringstuck_fixture():
    generated = bench_dividend.ring_level(4)
    assert generated.grid == sokoban.RING_STUCK.grid
    assert generated.player == sokoban.RING_STUCK.player
    assert generated.boxes == sokoban.RING_STUCK.boxes
    assert generated.goals == sokoban.RING_STUCK.goals


def test_the_three_board_is_refused_rather_than_silently_dead():
    """At side 3 the construction puts a box on a corner; the ladder must say so."""
    with pytest.raises(ValueError):
        bench_instances.far_level(3)


def test_bench_writes_nothing_into_the_committed_fixture_directory(tmp_path):
    """A benchmark that regenerates its inputs into `fixtures/data/` would be one
    `git status` away from being blamed for a fixture drift it did not cause."""
    before = sorted(os.listdir(sokoban.DATA_DIR))
    bench_instances.all_instances(str(tmp_path / "instances"))
    bench_dividend.ring_level(5)
    assert sorted(os.listdir(sokoban.DATA_DIR)) == before


def test_generated_instances_do_not_claim_a_solvability_nobody_proved(tmp_path):
    generated = [
        entry for entry in bench_instances.sokoban_ladder(str(tmp_path))
        if "generated" in entry.note
    ]
    assert generated
    assert all(entry.solvable is None for entry in generated)


# ----------------------------------------------------------- the compilation

def sokoban_theorems(tmp_path, side=4):
    level = bench_instances.far_level(side)
    path = str(tmp_path / ("%s.pddl" % level.name))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(level.problem_text())
    domain = fd_adapter.parse_domain(fd_adapter.read(sokoban.DOMAIN_PATH))
    problem = fd_adapter.parse_problem(fd_adapter.read(path))
    task = dc.Task.build(domain, problem)
    return domain, problem, level, path, dc.carve(task)


def test_the_guard_assumptions_hold_on_the_fixture(tmp_path):
    domain, _, _, _, theorems = sokoban_theorems(tmp_path)
    assert theorems
    compile_theorems.guardable(domain, theorems)      # must not raise


def test_a_theorem_about_another_predicate_is_refused_not_skipped(tmp_path):
    """A guard that quietly covers less than the theorems do would report a
    dividend for evidence it never gave the planner."""
    domain, _, _, _, theorems = sokoban_theorems(tmp_path)
    impostor = dc.Theorem(
        pattern=(("clear", "c11"),), blocked=(),
        goal_conflict=(("clear", "c11"), ("at", "b1", "c11")),
        n_deleting_actions=0,
    )
    with pytest.raises(compile_theorems.NotGuardable):
        compile_theorems.guardable(domain, list(theorems) + [impostor])


def test_pairs_are_emitted_in_both_orders(tmp_path):
    """Either box of a dead pair can be the one that completes it."""
    _, _, _, _, theorems = sokoban_theorems(tmp_path)
    pairs = [t for t in theorems if t.size == 2]
    assert pairs, "the fixture is supposed to produce pair deadlocks"
    _, emitted = compile_theorems.guard_facts(theorems, "full")
    for theorem in pairs:
        (_, b1, c1), (_, b2, c2) = theorem.pattern
        assert "(deadpair %s %s %s %s)" % (b1, c1, b2, c2) in emitted
        assert "(deadpair %s %s %s %s)" % (b2, c2, b1, c1) in emitted


def test_the_singleton_guard_does_not_pay_for_facts_it_cannot_read(tmp_path):
    """`push` has no `deadpair` precondition under that guard, so the facts would
    inflate the reported task size for nothing."""
    _, _, _, _, theorems = sokoban_theorems(tmp_path)
    singles, pairs = compile_theorems.guard_facts(theorems, "singleton")
    assert singles and pairs == []
    size = compile_theorems.guard_size(theorems, "singleton")
    assert size["theorems_expressed"] == len(singles) < size["theorems_total"]


def test_the_original_init_reaches_the_planner_byte_for_byte(tmp_path):
    """The guarded problem is a splice, not a re-serialisation: a difference in
    the measurement must not be able to come from this module reformatting."""
    _, _, level, _, theorems = sokoban_theorems(tmp_path)
    original = level.problem_text()
    guarded = compile_theorems.guarded_problem_text(original, theorems, "full")
    for line in original.splitlines():
        if line.strip().startswith("(at") or line.strip().startswith("(clear"):
            assert line in guarded
    assert "(:domain sokoban-guarded)" in guarded
    assert "(:domain sokoban)" not in guarded


def test_every_carved_theorem_reaches_the_full_guard(tmp_path):
    _, _, _, _, theorems = sokoban_theorems(tmp_path)
    size = compile_theorems.guard_size(theorems, "full")
    assert size["theorems_expressed"] == size["theorems_total"] == len(theorems)


# ------------------------------------------------------------- the verdicts

def _row(config, length, solved=True, unsolvable=False):
    return {"config": config, "plan_length": length, "solved": solved,
            "proved_unsolvable": unsolvable}


def test_an_optimal_rung_off_the_closed_form_is_a_failure():
    instance = bench_instances.BenchInstance(
        name="x", family="gripper", domain_path="", problem_path="", optimum=5)
    verdict = ladder.verdicts(instance, [
        _row("stub-bfs", 5), _row("fd-optimal/lmcut", 6)])
    assert verdict["optimum_ok"] is False


def test_a_longer_satisficing_plan_is_allowed_and_a_shorter_one_is_not():
    instance = bench_instances.BenchInstance(
        name="x", family="gripper", domain_path="", problem_path="", optimum=5)
    assert ladder.verdicts(instance, [
        _row("stub-bfs", 5), _row("fd-satisficing", 7)])["satisficing_ok"] is True
    assert ladder.verdicts(instance, [
        _row("stub-bfs", 5), _row("fd-satisficing", 4)])["satisficing_ok"] is False


def test_rungs_disagreeing_about_solvability_is_a_failure():
    instance = bench_instances.BenchInstance(
        name="x", family="sokoban", domain_path="", problem_path="")
    verdict = ladder.verdicts(instance, [
        _row("stub-bfs", None, solved=False, unsolvable=True),
        _row("fd-optimal/lmcut", 4)])
    assert verdict["solvability_consistent"] is False


# ------------------------------------------------------------- the toolchain

def test_the_p13_manifest_is_still_where_the_gap_note_points(tmp_path):
    record = toolchain.probe(None, os.path.dirname(HERE))
    assert record["toolchain_manifest_present"] is True
    assert record["available"] is False
    assert record["reproducibility_gap"]


@needs_fd
def test_the_binary_in_front_of_us_is_the_one_p13_described():
    """The check that gives the recorded hash its point: it is compared, not quoted."""
    record = toolchain.probe(FD, os.path.dirname(HERE))
    assert record["binary_sha256"] == toolchain.EXPECTED["binary_sha256"]
    assert record["matches_p13_manifest"] is True


# ------------------------------------------------------- end to end, with FD

@needs_fd
def test_a_guarded_plan_replays_on_the_original_domain(tmp_path):
    """The safety net. A guard that removed a transition it had no right to
    remove shows up here and nowhere else."""
    domain, problem, level, _, theorems = sokoban_theorems(tmp_path, side=5)
    guard_domain, guard_problem = compile_theorems.write_guarded(
        str(tmp_path), level.name, level.problem_text(), theorems, guard="singleton")
    record = fdrun.measure(FD, guard_domain, guard_problem,
                           backends.FD_OPTIMAL, "lmcut")
    assert record.plan, record.error
    fd_adapter.validate_plan(domain, problem, record.plan)


@needs_fd
def test_the_singleton_guard_preserves_the_optimal_length(tmp_path):
    """The compilation's whole claim, on one instance, on the rung where length
    is an optimum rather than a result."""
    _, _, level, path, theorems = sokoban_theorems(tmp_path, side=5)
    base = fdrun.measure(FD, sokoban.DOMAIN_PATH, path, backends.FD_OPTIMAL, "lmcut")
    guard_domain, guard_problem = compile_theorems.write_guarded(
        str(tmp_path), level.name, level.problem_text(), theorems, guard="singleton")
    guarded = fdrun.measure(FD, guard_domain, guard_problem,
                            backends.FD_OPTIMAL, "lmcut")
    assert base.plan_length == guarded.plan_length


@needs_fd
def test_the_full_guard_is_refused_by_the_optimal_rung_for_the_reason_recorded(tmp_path):
    """A finding of this run, pinned so it cannot quietly stop being true.

    FD's translator compiles the universal precondition into axioms and
    `astar(lmcut())` refuses a task with axioms. If a later FD build accepts it,
    this test fails and the run's conclusion needs revisiting -- which is the
    point of pinning it.
    """
    _, _, level, _, theorems = sokoban_theorems(tmp_path, side=5)
    guard_domain, guard_problem = compile_theorems.write_guarded(
        str(tmp_path), level.name, level.problem_text(), theorems, guard="full")
    record = fdrun.measure(FD, guard_domain, guard_problem,
                           backends.FD_OPTIMAL, "lmcut")
    assert record.plan is None
    assert record.error is not None
    assert "axiom" in record.error.lower()
