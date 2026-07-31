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
from bench import report as bench_report
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


def test_a_pair_theorem_naming_one_box_twice_is_refused(tmp_path):
    """The regression an adversarial review of this run found.

    The pair guard reads `at(?ob,?oc)` in the **pre-state**, where the pushed
    box still holds its old position. For a pattern naming one box twice that
    blocks transitions which *leave* the pattern rather than enter it -- stronger
    than the theorem, and stronger is the unsound direction. Measured on the real
    planner before this check existed, a vacuous same-box pattern took `far4`'s
    optimal length from 11 to 25.

    `carve()` cannot emit one (two positions of a box are mutex), but that is a
    property of another module and `guardable()` exists not to take such things
    on trust. `tools/p13_fd_dividend.py` had this check; this module had dropped it.
    """
    domain, _, _, _, theorems = sokoban_theorems(tmp_path)
    same_box = dc.Theorem(
        pattern=(("at", "b1", "c22"), ("at", "b1", "c32")),
        blocked=(), goal_conflict=(("at", "b1", "c22"), ("at", "b1", "c42")),
        n_deleting_actions=0,
    )
    with pytest.raises(compile_theorems.NotGuardable) as caught:
        compile_theorems.guardable(domain, list(theorems) + [same_box])
    assert "twice" in str(caught.value)


def test_the_guarded_domain_still_matches_the_fixture_it_copies(tmp_path):
    """`_MOVE` and `_EFFECT` are hand-copied from the committed sokoban domain.

    Nothing else pins them, so a fixture edit would silently change the task
    every dividend number is measured on. Compared on tokens rather than text
    because the guarded copy is re-indented.
    """
    with open(sokoban.DOMAIN_PATH, encoding="utf-8") as fh:
        fixture = fh.read()

    def tokens(text, start):
        chunk = text[text.index(start):]
        depth, out = 0, []
        for index, char in enumerate(chunk):
            depth += (char == "(") - (char == ")")
            if depth == 0:
                out = chunk[:index + 1].split()
                break
        return [t for t in out if t]

    assert tokens(compile_theorems._MOVE, "(:action move") == \
        tokens(fixture, "(:action move")
    # push's effect, which the guards leave untouched -- only its precondition moves.
    assert tokens(compile_theorems._EFFECT.strip()[: -2], ":effect")[:6] == \
        tokens(fixture[fixture.index("(:action push"):], ":effect")[:6]


def test_the_indexed_guard_carries_every_pair_theorem(tmp_path):
    _, problem, _, _, theorems = sokoban_theorems(tmp_path, side=5)
    partners = compile_theorems.indexed_partners(theorems)
    for theorem in theorems:
        if theorem.size != 2:
            continue
        (_, b1, c1), (_, b2, c2) = theorem.pattern
        assert (b2, c2) in partners[(b1, c1)]
        assert (b1, c1) in partners[(b2, c2)]


def test_every_box_cell_gets_exactly_one_npair_fact(tmp_path):
    """Omitting `npair0` does not weaken the guard, it blocks the push entirely:
    no schema would apply to a (box, cell) with no dead partners."""
    _, problem, _, _, theorems = sokoban_theorems(tmp_path, side=5)
    boxes = [n for n, k in problem.objects if k == "box"]
    cells = [n for n, k in problem.objects if k == "cell"]
    facts = compile_theorems.indexed_facts(theorems, boxes, cells)
    for box in boxes:
        for cell in cells:
            matching = [f for f in facts
                        if f.startswith("(npair") and f.endswith(" %s %s)" % (box, cell))]
            assert len(matching) == 1, (box, cell, matching)


def test_the_indexed_guard_needs_no_adl(tmp_path):
    _, problem, _, _, theorems = sokoban_theorems(tmp_path, side=5)
    text = compile_theorems.indexed_domain(compile_theorems.indexed_arity(theorems))
    assert ":adl" not in text and "forall" not in text
    assert ":negative-preconditions" in text


def test_indexed_plan_steps_map_back_to_the_original_vocabulary():
    """`push-pair<k>` is not an action the original domain has."""
    mapped = compile_theorems.to_original_plan(
        ["(move c11 c12 right)", "(push-pair2 c43 c33 c23 b2 up b1 c11 b1 c12)"],
        "indexed",
    )
    assert mapped == ["(move c11 c12 right)", "(push c43 c33 c23 b2 up)"]
    # Identity for the guards that do not rename anything.
    assert compile_theorems.to_original_plan(["(push a b c d e)"], "singleton") == \
        ["(push a b c d e)"]


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


@needs_fd
def test_the_indexed_guard_gets_the_pair_deadlocks_through_the_optimal_rung(tmp_path):
    """The refutation of this run's first framing, pinned.

    The `:adl` guard is refused for axioms (test above), and this run originally
    concluded pair deadlocks "cannot reach" the admissible rungs. They can: drop
    the `forall` for indexed static selectors and `astar(lmcut())` accepts the
    task, returns the same optimal length -- and expands *more* states than
    without it. That last part is why the encoding had to be built rather than
    predicted.
    """
    domain, problem, level, path, theorems = sokoban_theorems(tmp_path, side=5)
    guard_domain, guard_problem = compile_theorems.write_guarded(
        str(tmp_path), level.name, level.problem_text(), theorems,
        guard="indexed", problem=problem)

    base = fdrun.measure(FD, sokoban.DOMAIN_PATH, path, backends.FD_OPTIMAL, "lmcut")
    guarded = fdrun.measure(FD, guard_domain, guard_problem,
                            backends.FD_OPTIMAL, "lmcut")

    assert guarded.error is None, guarded.error
    assert guarded.plan_length == base.plan_length          # optimality preserved
    fd_adapter.validate_plan(
        domain, problem, compile_theorems.to_original_plan(guarded.plan, "indexed"))
    assert guarded.translator["task_size"] > base.translator["task_size"]


# ------------------------------------------------- the batch, and the zero row
#
# `open4` -- sixteen true theorems, 47 expansions before and 47 after -- is the
# row DECISIONS D-020 argues the dividend table must contain, and for one whole
# milestone it existed only in two hand-written documents (D-020 itself and
# `engines/deadlock_carver/README.md`) and in no artifact anybody regenerates.
# These tests are the guarantee that it cannot go missing again quietly: one that
# it is measured, one that it is measured *first*, and one that it survives all
# the way into the rendered Markdown.

def test_the_batch_leads_with_the_committed_fixtures_and_open4_is_row_one(tmp_path):
    rows = bench_dividend.batch(str(tmp_path / "instances"))
    families = [family for family, _, _, _ in rows]
    names = [level.name for _, level, _, _ in rows]

    assert names[0] == "open4", names
    assert names[1] == "open4far", names
    assert families[:2] == ["committed", "committed"]
    # The generated ladders still follow, in their own order.
    assert names[2:] == ["far%d" % side for side in bench_dividend.FAR_SIDES] + \
        ["ringstuck%d" % side for side in bench_dividend.RING_SIDES]


def test_the_committed_rows_are_the_bytes_on_disk_not_a_re_render(tmp_path):
    """`Level.problem_text()` would almost certainly agree. "Almost certainly" is
    not a property this rig accepts about the input to a measurement."""
    rows = bench_dividend.batch(str(tmp_path / "instances"))
    for family, level, path, text in rows:
        if family != "committed":
            continue
        assert path == level.path
        with open(path, "r", encoding="utf-8") as fh:
            assert text == fh.read()


def test_the_batch_writes_nothing_into_the_committed_fixture_directory(tmp_path):
    """The committed half of the batch is read; only the generated half is written."""
    before = sorted(os.listdir(sokoban.DATA_DIR))
    instance_dir = str(tmp_path / "instances")
    bench_dividend.batch(instance_dir)
    assert sorted(os.listdir(sokoban.DATA_DIR)) == before
    written = sorted(os.listdir(instance_dir))
    assert "sokoban_open4.pddl" not in written and "open4.pddl" not in written
    assert "far4.pddl" in written


def test_no_absolute_path_reaches_the_artifact(tmp_path):
    """A published path must resolve on a machine that is not this one."""
    out_dir = str(tmp_path / "run")
    committed = bench_dividend._artifact_path(sokoban.OPEN4_PATH, out_dir)
    assert committed == "fixtures/data/sokoban_open4.pddl"

    generated = bench_dividend._artifact_path(
        os.path.join(out_dir, "instances", "far4.pddl"), out_dir)
    assert generated == "instances/far4.pddl"

    for value in (committed, generated):
        assert not os.path.isabs(value)
        assert "\\" not in value and ":" not in value


def test_open4_is_the_zero_row_47_expansions_before_and_after(tmp_path):
    """D-020's number, re-derived rather than quoted.

    The bundled rung is a deterministic breadth-first search, so this is an exact
    equality and not a timing. If the carver, the encoding or the search changes
    what `open4` costs, this fails and D-020 needs rewriting -- which is the point
    of pinning it here rather than trusting the prose.
    """
    domain = fd_adapter.parse_domain(fd_adapter.read(sokoban.DOMAIN_PATH))
    problem = fd_adapter.parse_problem(fd_adapter.read(sokoban.OPEN4_PATH))
    theorems = dc.carve(dc.Task.build(domain, problem))
    assert len(theorems) == 16

    stub = bench_dividend.stub_dividend(domain, problem, theorems, repeats=1,
                                        carve_seconds=0.5)
    assert stub["expansions_before"] == 47
    assert stub["expansions_after"] == 47
    assert stub["states_pruned"] == 0
    assert stub["plan_length_unchanged"] is True
    assert stub["dividend_is_honest"] is True


def test_the_zero_row_reaches_the_markdown_and_is_not_silently_dropped(tmp_path):
    """The hole this run was opened to close: the number landed in the JSON and
    never rendered. A zero row that no reader sees is a zero row nobody has."""
    domain = fd_adapter.parse_domain(fd_adapter.read(sokoban.DOMAIN_PATH))
    problem = fd_adapter.parse_problem(fd_adapter.read(sokoban.OPEN4_PATH))
    theorems = dc.carve(dc.Task.build(domain, problem))
    report = {
        "form": "deadlock_dividend",
        "claim_under_test": "x",
        "repeats": 1,
        "fast_downward": None,
        "prior_audit": bench_dividend.E7_RECONCILIATION,
        "results": [{
            "instance": "open4", "family": "committed",
            "cells": len(sokoban.OPEN4.floors()), "boxes": 2,
            "n_theorems": len(theorems),
            "n_singleton_theorems": sum(1 for t in theorems if t.size == 1),
            "n_pair_theorems": sum(1 for t in theorems if t.size == 2),
            "carve_seconds": 0.5,
            "problem_path": "fixtures/data/sokoban_open4.pddl",
            "stub": bench_dividend.stub_dividend(domain, problem, theorems,
                                                 repeats=1, carve_seconds=0.5),
            # The measured shape of `open4` on FD's blind control: a second
            # witness to the same zero, from a search that is not this repo's.
            "fd": [{
                "instance": "open4", "guard": "singleton",
                "rung": "fd-optimal/blind", "guard_size": {
                    "theorems_expressed": 8, "theorems_total": 16},
                "expansions_before": 49, "expansions_after": 49,
                "task_size_before": 1029, "task_size_after": 869,
                "plan_length_delta": 0, "dividend_is_honest": True,
                "guard_refused": None,
            }],
        }],
        "tiebreak_sensitivity": {"summary": [{
            "instance": "open4", "tiebreaks": ["astar", "single", "goalcount"],
            "baseline_min": 45, "baseline_max": 82, "baseline_spread_pct": 82.2,
            "guards": {"singleton": {"ratio_min": 1.0, "ratio_max": 1.0,
                                     "dividend_min_pct": 0.0,
                                     "dividend_max_pct": 0.0,
                                     "ratio_spread_points": 0.0}},
        }]},
    }
    markdown = bench_report.dividend_markdown(report)

    assert "### The zero row" in markdown
    assert "**`open4`: 47 → 47 expansions**" in markdown
    assert "D-020" in markdown
    # The second witness and the tie-break survival, both from the JSON.
    assert "`open4` under `singleton`, 49 → 49" in markdown
    assert "the zero is not one ordering's accident" in markdown
    # And the row itself is in the table above the callout, with both counts.
    table = [line for line in markdown.splitlines()
             if line.startswith("| `open4` | committed |")]
    assert len(table) == 1, table
    assert table[0].split("|")[6].strip() == "47"       # exp before
    assert table[0].split("|")[7].strip() == "47"       # exp after


def test_a_batch_with_no_zero_row_says_so_rather_than_saying_nothing():
    """The failure mode is silence, so silence is what the renderer must not do."""
    lines = bench_report._zero_row_section({"results": [{
        "instance": "far4", "n_theorems": 16,
        "stub": {"expansions_before": 808, "expansions_after": 571,
                 "plan_length_unchanged": True},
    }]})
    assert any("No zero row in this batch" in line for line in lines)


def _twin_entry(name, expansions_after=571, n_theorems=16):
    return {
        "instance": name, "family": "committed", "cells": 16, "boxes": 2,
        "n_theorems": n_theorems, "n_singleton_theorems": 8,
        "n_pair_theorems": n_theorems - 8, "carve_seconds": 0.07,
        "stub": {"expansions_before": 808, "expansions_after": expansions_after,
                 "states_pruned": 69, "plan_length_unchanged": True},
        "fd": [{"guard": "singleton", "rung": "fd-optimal/blind",
                "expansions_before": 837, "expansions_after": 610,
                "task_size_before": 1029, "task_size_after": 869,
                "plan_length_delta": 0, "guard_refused": None,
                "replayed_on_original_domain": True,
                "guarded": {"solved": True}}],
    }


def test_the_committed_fixture_and_its_generated_copy_must_measure_the_same():
    """`far4` is *supposed* to be `open4far`. The dataclass test above asserts it
    about two objects; this asserts it about two measurements."""
    agreeing = {"results": [_twin_entry("open4far"), _twin_entry("far4")]}
    assert bench_dividend.twin_failures(agreeing) == []

    drifted = {"results": [_twin_entry("open4far"),
                           _twin_entry("far4", expansions_after=570)]}
    problems = bench_dividend.twin_failures(drifted)
    assert len(problems) == 1
    assert "same board" in problems[0] and "expansions_after" in problems[0]


def test_a_drifted_generator_is_a_failure_of_the_run_not_a_footnote():
    """It reaches `failures()`, which is what sets the run's exit code."""
    drifted = {
        "results": [_twin_entry("open4far"), _twin_entry("far4", n_theorems=15)],
        "tiebreak_sensitivity": {"rows": []},
    }
    problems = bench_dividend.failures(drifted)
    assert any("drifted from the committed fixture" in line for line in problems)


def test_the_twin_verdict_renders_even_when_it_finds_nothing():
    """A check reported only on failure cannot be told from a check nobody ran."""
    markdown = bench_report.dividend_markdown({
        "claim_under_test": "x", "results": [],
        "structural_twins": {"pairs": [["open4far", "far4"]], "why": "w",
                             "compared": "c", "agree": True, "problems": []},
    })
    assert "`open4far` ≡ `far4`" in markdown
    assert "**Every structural column agrees.**" in markdown

    broken = bench_report.dividend_markdown({
        "claim_under_test": "x", "results": [],
        "structural_twins": {"pairs": [["open4far", "far4"]], "why": "w",
                             "compared": "c", "agree": False,
                             "problems": ["open4far vs far4: boom"]},
    })
    assert "They do not agree" in broken
    assert "* open4far vs far4: boom" in broken


# ----------------------------------------------- the wall clock, with the carve

def _measurement(search_seconds, wall_seconds, **kwargs):
    return fdrun.FdMeasurement(
        tier=backends.FD_OPTIMAL, config="astar(blind())", heuristic="blind",
        search_seconds=search_seconds, wall_seconds=wall_seconds, **kwargs)


def test_the_carve_is_charged_against_the_search_clock_not_the_driver():
    """The end-to-end clock on this batch is ~150 ms of Python driver startup that
    no theorem can touch. Charging a dividend against it would measure the driver.
    """
    base = _measurement(0.500, 1.000)
    guarded = _measurement(0.400, 0.950)
    clock = bench_dividend._wall_clock(base, guarded, carve_seconds=1.0)

    assert clock["charged_against"] == "search_seconds"
    assert clock["search_seconds_saved"] == pytest.approx(0.100)
    assert clock["net_seconds_with_carving"] == pytest.approx(0.900)
    assert clock["carving_is_repaid"] is False
    # Both clocks are recorded; only one is the invoice. The end-to-end saving is
    # half the search saving here, and if `net` were computed from it the answer
    # would be 0.95 rather than 0.9 -- which is the confusion this test pins out.
    assert clock["end_to_end_seconds_saved"] == pytest.approx(0.050)
    assert clock["net_seconds_with_carving"] != pytest.approx(0.950)


def test_the_invoice_is_repaid_when_the_search_saved_more_than_the_carve():
    clock = bench_dividend._wall_clock(
        _measurement(2.0, 3.0), _measurement(0.5, 1.5), carve_seconds=1.0)
    assert clock["search_seconds_saved"] == pytest.approx(1.5)
    assert clock["carving_is_repaid"] is True
    assert clock["net_seconds_with_carving"] == pytest.approx(-0.5)
    assert clock["solves_to_repay_carving"] == 1


def test_solves_to_repay_rounds_up_because_a_partial_solve_repays_nothing():
    clock = bench_dividend._wall_clock(
        _measurement(1.000, 2.0), _measurement(0.997, 2.0), carve_seconds=1.0)
    assert clock["search_seconds_saved"] == pytest.approx(0.003)
    # 1.0 / 0.003 = 333.33 -- and 333 solves leave the carve unpaid.
    assert clock["solves_to_repay_carving"] == 334


def test_no_number_of_repeats_repays_a_carve_out_of_a_saving_that_is_not_positive():
    """Zero and negative are different findings and neither is a repayment."""
    flat = bench_dividend._wall_clock(
        _measurement(0.5, 1.0), _measurement(0.5, 1.0), carve_seconds=1.0)
    assert flat["search_seconds_saved"] == 0.0
    assert flat["solves_to_repay_carving"] is None
    assert flat["carving_is_repaid"] is False

    slower = bench_dividend._wall_clock(
        _measurement(0.5, 1.0), _measurement(0.7, 1.2), carve_seconds=1.0)
    assert slower["search_seconds_saved"] == pytest.approx(-0.2)
    assert slower["solves_to_repay_carving"] is None
    assert slower["carving_is_repaid"] is False


def test_a_refused_guard_has_no_clock_and_no_invented_dividend():
    """FD refuses the `full` guard on the admissible rungs, so there is no search
    time on the guarded side. A missing clock must stay missing."""
    clock = bench_dividend._wall_clock(
        _measurement(0.5, 1.0),
        _measurement(None, 0.2, error="This configuration does not support axioms!"),
        carve_seconds=1.0,
    )
    assert clock["search_seconds_after"] is None
    assert clock["search_seconds_saved"] is None
    assert clock["net_seconds_with_carving"] is None
    assert clock["carving_is_repaid"] is None
    assert clock["solves_to_repay_carving"] is None
    # The end-to-end clock exists either way -- the process still ran.
    assert clock["end_to_end_seconds_after"] == pytest.approx(0.2)


def test_the_wall_clock_columns_all_reach_the_markdown():
    row = {
        "instance": "far4", "guard": "singleton", "rung": "fd-optimal/blind",
        "guard_refused": None,
        "wall_clock": bench_dividend._wall_clock(
            _measurement(0.500, 1.000), _measurement(0.400, 0.950),
            carve_seconds=1.0),
    }
    lines = bench_report._wall_clock_section({"results": [{"fd": [row]}]})
    text = "\n".join(lines)
    assert "search_seconds" in text                      # what it is charged against
    assert "| `far4` | singleton | fd-optimal/blind |" in text
    assert "+0.900" in text                              # net, sign kept
    assert "| 10 |" in text                              # solves to repay
    assert "No row repaid the carve" in text


def test_the_bundled_rung_carries_the_same_invoice_as_the_fd_rows(tmp_path):
    """Two engines' wall-clock verdicts must be readable side by side, not one in
    a table and the other in a paragraph of narrative."""
    domain, problem, _, _, theorems = sokoban_theorems(tmp_path)
    stub = bench_dividend.stub_dividend(domain, problem, theorems, repeats=1,
                                        carve_seconds=1.5)
    timing = stub["timing"]
    assert timing["carve_seconds"] == 1.5
    assert set(timing) >= {"seconds_saved", "carve_seconds",
                           "net_seconds_with_carving", "carving_is_repaid"}
    # Arithmetic, not a clock comparison: the invoice must add up whatever the
    # machine was doing at the time.
    assert timing["net_seconds_with_carving"] == pytest.approx(
        timing["carve_seconds"] - timing["seconds_saved"], abs=1e-6)
    assert timing["carving_is_repaid"] == (
        timing["seconds_saved"] >= timing["carve_seconds"])


# ------------------------------------------------ tie-break sensitivity (G7/E7)

def test_every_tiebreak_configuration_is_a_blind_search():
    """The reconciliation with E7 that keeps this block from overclaiming.

    E7 §7b withdrew the whole `astar(ipdb())` column as an artefact of iPDB's
    pattern generation. If a tie-break configuration here ever grew a heuristic,
    the spread it produced could be read as an admissible-heuristic dividend --
    exactly the reading E7 forbids. So the block is blind, by test.
    """
    for _, search, _ in bench_dividend.TIEBREAKS:
        assert "blind()" in search
        assert "ipdb" not in search and "lmcut" not in search and "ff(" not in search
    # ...and all three order primarily on the same admissible f.
    assert bench_dividend.TIEBREAKS[0][1] == backends.FD_HEURISTICS["blind"]
    for _, search, _ in bench_dividend.TIEBREAKS[1:]:
        assert "sum([g(),blind()])" in search
        assert "reopen_closed=true" in search


def test_the_prior_audit_findings_are_data_and_all_of_them_render():
    """A caveat that lives only in the Markdown is a caveat a reader of the JSON
    never sees, and a caveat only in the JSON is one no reader sees at all."""
    ids = {item["id"] for item in bench_dividend.E7_RECONCILIATION["findings"]}
    assert ids == {"E7-ipdb-withdrawn", "E7-blind-band", "E7-lmcut-range",
                   "E7-tiebreak-invariant"}

    markdown = bench_report.dividend_markdown({
        "claim_under_test": "x",
        "prior_audit": bench_dividend.E7_RECONCILIATION,
        "results": [],
    })
    for item in bench_dividend.E7_RECONCILIATION["findings"]:
        assert item["id"] in markdown
        assert item["finding"] in markdown
    assert "DEADLOCK_CLAIM.md" in markdown
    # The two numbers E7 corrected, in the file that would otherwise repeat E2's.
    assert "-8.7% to -27.1%" in markdown
    assert "0 to -153 expansions" in markdown


def _tiebreak_rows():
    """`far5`'s measured shape: the baseline moves by half, the ratio by little."""
    return [
        {"instance": "far5", "tiebreak": "astar", "search": "astar(blind())",
         "note": "n", "expansions_before": 958, "plan_length_before": 13,
         "error": None,
         "guards": {"singleton": {"expansions_after": 872, "plan_length_after": 13,
                                  "expansions_ratio": 0.9102, "error": None}}},
        {"instance": "far5", "tiebreak": "single", "search": "eager(single(...))",
         "note": "n", "expansions_before": 1479, "plan_length_before": 13,
         "error": None,
         "guards": {"singleton": {"expansions_after": 1287, "plan_length_after": 13,
                                  "expansions_ratio": 0.8702, "error": None}}},
    ]


def test_tiebreak_summary_separates_the_baseline_spread_from_the_ratio_spread():
    summary = bench_dividend.tiebreak_summary(_tiebreak_rows())
    assert len(summary) == 1
    entry = summary[0]
    assert entry["baseline_min"] == 958 and entry["baseline_max"] == 1479
    assert entry["baseline_spread_pct"] == pytest.approx(54.4, abs=0.1)

    guard = entry["guards"]["singleton"]
    assert guard["dividend_min_pct"] == pytest.approx(9.0, abs=0.1)
    assert guard["dividend_max_pct"] == pytest.approx(13.0, abs=0.1)
    # The whole point: the absolute count moved by 54 points and the dividend by 4.
    assert guard["ratio_spread_points"] == pytest.approx(4.0, abs=0.1)
    assert guard["ratio_spread_points"] < entry["baseline_spread_pct"]


def test_a_tiebreak_that_moved_an_optimal_length_is_a_soundness_failure():
    """All three configurations order on the same admissible f, so a length that
    moves means either the `--search` string is not the search it claims or the
    guard is unsound in a way only one node ordering exposes."""
    rows = _tiebreak_rows()
    rows[1]["guards"]["singleton"]["plan_length_after"] = 12
    problems = bench_dividend.failures({
        "results": [],
        "tiebreak_sensitivity": {"rows": rows},
    })
    assert len(problems) == 1
    assert "optimal length" in problems[0]
    assert "far5/single/singleton" in problems[0]


def test_a_tiebreak_run_that_did_not_answer_is_reported_not_skipped():
    rows = _tiebreak_rows()
    rows[0]["error"] = "no plan file and no proof (exit 34, rung fd-optimal)"
    problems = bench_dividend.failures({
        "results": [], "tiebreak_sensitivity": {"rows": rows}})
    assert any("did not answer under this tie-break" in line for line in problems)


def test_the_tiebreak_tables_reach_the_markdown_with_the_e7_qualifier():
    rows = _tiebreak_rows()
    markdown = bench_report.dividend_markdown({
        "claim_under_test": "x",
        "prior_audit": bench_dividend.E7_RECONCILIATION,
        "results": [],
        "tiebreak_sensitivity": {
            "gap_closed": "E2 G7", "question": "instance or open list?",
            "blind_only": "All three configurations are f = g + blind().",
            "not_a_tiebreak_invariant": "needs f < C*",
            "excluded": "the unsolvable family",
            "timings_not_measured": "structural only",
            "configurations": [{"tiebreak": k, "search": s, "note": n}
                               for k, s, n in bench_dividend.TIEBREAKS],
            "guards": ["singleton"],
            "rows": rows,
            "summary": bench_dividend.tiebreak_summary(rows),
        },
    })
    assert "## Tie-break sensitivity" in markdown
    assert "| `far5` | astar | 958 | 13 | 872 | 0.9102 |" in markdown
    assert "| `far5` | single | 1479 | 13 | 1287 | 0.8702 |" in markdown
    assert "54.4%" in markdown                     # the baseline spread
    assert "| 4.0 |" in markdown                   # the ratio spread, in points
    # E7's stronger instrument, named where the weaker one is reported.
    assert "f < C*" in markdown
    assert "weaker of the two instruments" in markdown


@needs_fd
def test_measure_search_and_measure_agree_on_the_configuration_they_share(tmp_path):
    """`measure_search` builds its own argv, which is the one deliberate exception
    to this package's "never measure what the adapter would not run" rule. The
    exception is only safe while the two paths agree where they overlap, and
    `astar(blind())` is where they overlap."""
    _, _, _, path, _ = sokoban_theorems(tmp_path, side=4)
    through_adapter = fdrun.measure(FD, sokoban.DOMAIN_PATH, path,
                                    backends.FD_OPTIMAL, "blind")
    verbatim = fdrun.measure_search(FD, sokoban.DOMAIN_PATH, path,
                                    backends.FD_HEURISTICS["blind"])
    assert verbatim.error is None, verbatim.error
    assert verbatim.nodes["expanded"] == through_adapter.nodes["expanded"]
    assert verbatim.plan_length == through_adapter.plan_length
    assert verbatim.solved is through_adapter.solved


@needs_fd
def test_the_tiebreak_dependence_g7_reported_is_real_and_the_length_is_not(tmp_path):
    """E2's G7, on the instance G7 quoted. The absolute count moves; the optimal
    length does not, under any of the three. If FD ever made these three agree,
    the tie-break block would be measuring nothing and this test says so."""
    _, _, _, path, _ = sokoban_theorems(tmp_path, side=5)
    counts, lengths = {}, set()
    for key, search, _ in bench_dividend.TIEBREAKS:
        record = fdrun.measure_search(FD, sokoban.DOMAIN_PATH, path, search)
        assert record.error is None, (key, record.error)
        counts[key] = record.nodes["expanded"]
        lengths.add(record.plan_length)
    assert len(lengths) == 1, lengths            # same optimum under every rule
    assert len(set(counts.values())) > 1, counts  # different work to get there


@needs_fd
def test_indexed_and_adl_guards_agree_on_a_blind_search(tmp_path):
    """Two encodings of the same theorems must remove the same transitions.

    Blind A* because it is the one configuration that accepts both, so the
    comparison is possible at all.
    """
    _, problem, level, _, theorems = sokoban_theorems(tmp_path, side=4)
    results = {}
    for guard in ("full", "indexed"):
        guard_domain, guard_problem = compile_theorems.write_guarded(
            str(tmp_path), level.name, level.problem_text(), theorems,
            guard=guard, problem=problem)
        record = fdrun.measure(FD, guard_domain, guard_problem,
                               backends.FD_OPTIMAL, "blind")
        assert record.error is None, (guard, record.error)
        results[guard] = (record.nodes["expanded"], record.plan_length)
    assert results["full"] == results["indexed"], results
