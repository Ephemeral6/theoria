"""The negative sample for `papers/verify.py`.

`monitor/gates.py` counts a territory as `decorative` until its gate declares a
file that shows the gate can go red, and 22 of the 24 gated territories are
decorative -- gates installed and never exercised, indistinguishable from
working ones for exactly as long as nothing is broken. This is `papers` leaving
that list.

Every test here is a *mutation*: it builds a synthetic `papers/` tree, breaks
one thing, and asserts the gate refuses it. The two that matter most are the
two S34 found:

* `test_provenance_directory_is_not_a_defect` -- `runs/` used to make the gate
  red, so obeying CLAUDE.md's provenance rule blocked merges;
* `test_a_vanished_suite_is_red` -- the gate displaced the territory's own
  tests when it landed, and a displaced suite has to be louder than silence.

The tests drive `main()` in-process rather than through a subprocess so that
they run in a second, and they pin `INNER` explicitly: whether stage 3 is
skipped must not depend on whether pytest was started by a human or by stage 3
itself.
"""

import importlib.util
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))

#: A gate that passes the way a real one does: it says so.
OK_GATE = "print('fake_paper: PASS (1/1)')"


def _load():
    """Load `papers/verify.py` by path -- `import verify` would resolve to
    whichever of the repository's many `verify.py` files is on sys.path first."""
    spec = importlib.util.spec_from_file_location(
        "papers_verify", os.path.join(HERE, "verify.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


V = _load()


def make_paper(root, name, gate_body=OK_GATE,
               gate_name="verify_paper.py", marker=True):
    d = os.path.join(root, name)
    os.makedirs(d, exist_ok=True)
    if marker:
        with open(os.path.join(d, V.PAPER_MARKER), "w", encoding="utf-8") as fh:
            fh.write("# a paper\n")
    if gate_body is not None:
        with open(os.path.join(d, gate_name), "w", encoding="utf-8") as fh:
            fh.write(gate_body + "\n")
    return d


def run(root, monkeypatch, skip_suite=True, timeout=None):
    """`main()` against a synthetic tree. Stage 3 is skipped unless a test is
    specifically about stage 3, because a synthetic tree has no suite."""
    monkeypatch.setenv(V.INNER, "1") if skip_suite \
        else monkeypatch.delenv(V.INNER, raising=False)
    argv = ["--root", str(root)]
    if timeout is not None:
        argv += ["--timeout", str(timeout)]
    return V.main(argv)


# ------------------------------------------------------------ classification

def test_a_paper_is_a_directory_holding_a_paper_md(tmp_path):
    make_paper(tmp_path, "phase1")
    papers, skipped, strays = V.classify(str(tmp_path))
    assert papers == ["phase1"] and skipped == [] and strays == []


def test_provenance_directory_is_not_a_defect(tmp_path, monkeypatch):
    """S34's trap, in one assertion.

    CLAUDE.md: 'every experiment writes runs/<id>/MANIFEST.json'. `runs/` is
    not gitignored, so it reaches the worktree ci_merge checks out. Before S34
    the gate demanded a gate file from it and went red -- the territory blocked
    for having followed the repository's own rule."""
    make_paper(tmp_path, "phase1")
    os.makedirs(os.path.join(tmp_path, "runs", "20260729T000000Z-X"))
    papers, skipped, strays = V.classify(str(tmp_path))
    assert papers == ["phase1"] and skipped == ["runs"] and strays == []
    assert run(tmp_path, monkeypatch) == 0


def test_an_unrecognised_directory_is_still_red(tmp_path, monkeypatch):
    """Disarming the trap must not disarm the gate: anything that is neither a
    paper nor declared provenance is red, and is named."""
    make_paper(tmp_path, "phase1")
    os.makedirs(os.path.join(tmp_path, "scratch"))
    assert V.classify(str(tmp_path))[2] == ["scratch"]
    assert run(tmp_path, monkeypatch) == 1


def test_a_directory_without_the_marker_is_not_silently_dropped(tmp_path,
                                                               monkeypatch):
    """A paper directory that loses its PAPER.md becomes a stray, not a
    non-entity. Dropping it would be the original silence in a new place."""
    make_paper(tmp_path, "phase1")
    make_paper(tmp_path, "phase2", marker=False)
    assert run(tmp_path, monkeypatch) == 1


def test_dot_and_dunder_directories_are_ignored(tmp_path, monkeypatch):
    make_paper(tmp_path, "phase1")
    os.makedirs(os.path.join(tmp_path, "__pycache__"))
    os.makedirs(os.path.join(tmp_path, ".pytest_cache"))
    assert V.classify(str(tmp_path)) == (["phase1"], [], [])
    assert run(tmp_path, monkeypatch) == 0


def test_a_file_named_like_a_paper_is_not_a_paper(tmp_path, monkeypatch):
    make_paper(tmp_path, "phase1")
    with open(os.path.join(tmp_path, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("x\n")
    assert V.classify(str(tmp_path)) == (["phase1"], [], [])


# -------------------------------------------------------------- empty floor

def test_no_paper_at_all_is_red_not_a_vacuous_pass(tmp_path, monkeypatch):
    assert run(tmp_path, monkeypatch) == 1


def test_provenance_alone_does_not_satisfy_the_floor(tmp_path, monkeypatch):
    """The failure mode the floor exists for, now reachable a second way: a
    tree holding only `runs/` walks over zero papers and would otherwise pass
    every check written below it."""
    os.makedirs(os.path.join(tmp_path, "runs"))
    assert run(tmp_path, monkeypatch) == 1


# ------------------------------------------------------------ running gates

def test_a_paper_shipping_no_gate_is_red(tmp_path, monkeypatch):
    make_paper(tmp_path, "phase1", gate_body=None)
    assert run(tmp_path, monkeypatch) == 1


def test_a_failing_gate_is_red(tmp_path, monkeypatch):
    make_paper(tmp_path, "phase1", gate_body="raise SystemExit(1)")
    assert run(tmp_path, monkeypatch) == 1


def test_a_gate_that_crashes_on_import_is_red(tmp_path, monkeypatch):
    """A gate that cannot start reports as its paper failing, which is a lie in
    the direction that looks like a verdict -- but it must still be red."""
    make_paper(tmp_path, "phase1", gate_body="import nonexistent_module_xyz")
    assert run(tmp_path, monkeypatch) == 1


def test_a_gate_that_says_nothing_is_red(tmp_path, monkeypatch):
    """The third silence, after 'no paper' and 'no gate'. A zero-byte
    verify_paper.py used to print '(no output)' on the ok line and take the
    territory green."""
    make_paper(tmp_path, "phase1", gate_body="pass")
    assert run(tmp_path, monkeypatch) == 1


def test_a_gate_that_prints_and_exits_zero_is_green(tmp_path, monkeypatch):
    """The delegated trust that remains, documented rather than pretended
    away: this file reads exit codes and refuses silence. It does not know
    what a passing paper looks like, so a gate that prints its own FAIL and
    exits 0 still passes here. Requiring a verdict token would be a contract
    on every future paper's gate, and this file is not the place to impose
    one unilaterally -- it is filed instead."""
    make_paper(tmp_path, "phase1",
               gate_body="print('verify_paper: FAIL'); raise SystemExit(0)")
    assert run(tmp_path, monkeypatch) == 0


def test_the_repository_root_is_importable_from_a_gate(tmp_path, monkeypatch):
    """`monitor/gates.py: gate_env()` states this as the contract every gate is
    entitled to assume. Two territories' gates died on it in one night."""
    make_paper(tmp_path, "phase1",
               gate_body="import monitor.gates; print('imported the root ok')")
    assert run(tmp_path, monkeypatch) == 0


def test_verify_py_is_accepted_as_a_gate_name(tmp_path, monkeypatch):
    make_paper(tmp_path, "phase1", gate_body=OK_GATE,
               gate_name="verify.py")
    assert V.gate_of(str(tmp_path), "phase1") == "verify.py"
    assert run(tmp_path, monkeypatch) == 0


def test_verify_paper_wins_over_verify(tmp_path, monkeypatch):
    make_paper(tmp_path, "phase1", gate_body=OK_GATE)
    make_paper(tmp_path, "phase1", gate_body="raise SystemExit(1)",
               gate_name="verify.py")
    assert V.gate_of(str(tmp_path), "phase1") == "verify_paper.py"
    assert run(tmp_path, monkeypatch) == 0


def test_a_hanging_gate_is_red_not_a_hung_merge_rig(tmp_path, monkeypatch):
    """`--timeout` was parsed and then never passed to anything until S34. A
    gate that never returns used to take the merge rig down with it."""
    make_paper(tmp_path, "phase1", gate_body="import time; time.sleep(30)")
    assert run(tmp_path, monkeypatch, timeout=2) == 1


# -------------------------------------------------------------- stage 3

def test_a_vanished_suite_is_red(tmp_path, monkeypatch):
    """pytest exits 5 for 'collected nothing'. Without this, a deleted suite
    and a green suite report the same green -- which is precisely how this
    territory lost its tests when the gate arrived."""
    monkeypatch.delenv(V.INNER, raising=False)
    ok, detail, ran = V.run_suite(str(tmp_path))
    assert not ok and "collected nothing" in detail and ran


def test_a_red_suite_is_red(tmp_path, monkeypatch):
    monkeypatch.delenv(V.INNER, raising=False)
    with open(os.path.join(tmp_path, "test_x.py"), "w", encoding="utf-8") as fh:
        fh.write("def test_x():\n    assert False\n")
    ok, detail, ran = V.run_suite(str(tmp_path))
    assert not ok and "exited" in detail and ran


def test_a_green_suite_is_green(tmp_path, monkeypatch):
    monkeypatch.delenv(V.INNER, raising=False)
    with open(os.path.join(tmp_path, "test_x.py"), "w", encoding="utf-8") as fh:
        fh.write("def test_x():\n    assert True\n")
    ok, _, ran = V.run_suite(str(tmp_path))
    assert ok and ran


def test_the_guard_refuses_an_unexplained_environment(tmp_path, monkeypatch):
    """The guard's failure mode is skipping stage 3 and still exiting 0 --
    the fixed defect, restored by an environment variable. A legitimate nested
    run is always inside pytest; this simulates one that is not."""
    monkeypatch.setenv(V.INNER, "1")
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delitem(sys.modules, "pytest", raising=False)
    ok, detail, ran = V.run_suite(str(tmp_path))
    assert not ok and "unexplained environment" in detail
    assert not ran


def test_the_recursion_guard_holds(tmp_path, monkeypatch):
    """This test is itself inside the suite stage 3 runs. Without the guard,
    stage 3 would start a pytest that reaches this line and starts another."""
    monkeypatch.setenv(V.INNER, "1")
    ok, detail, ran = V.run_suite(str(tmp_path))
    assert ok and "already running inside" in detail
    # green, and `ran` says it did not check anything. See the new test below.
    assert not ran


def test_stage_three_actually_runs_when_not_guarded(tmp_path, monkeypatch):
    """The guard must not be reachable by accident: with INNER cleared, a tree
    whose suite is red must take the whole gate red."""
    make_paper(tmp_path, "phase1")
    with open(os.path.join(tmp_path, "test_x.py"), "w", encoding="utf-8") as fh:
        fh.write("def test_x():\n    assert False\n")
    assert run(tmp_path, monkeypatch, skip_suite=False) == 1


def test_the_skipped_summary_does_not_claim_the_suite_ran(tmp_path,
                                                          monkeypatch,
                                                          capsys):
    """S34's own delivery shipped this defect and an adversarial pass in the
    next cycle caught it: on the nested path stage 3 is skipped, and the final
    line still read `... and the checks' own suite run`. Exit 0 is correct
    there -- the alternative is a fork bomb -- so the exit code cannot carry
    the distinction and the sentence has to.

    A green summary that asserts a check which did not execute is the same
    silence the three stages refuse; a gate is not allowed to commit it about
    itself."""
    make_paper(tmp_path, "phase1")
    monkeypatch.setenv(V.INNER, "1")
    assert V.main(["--root", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "papers: green" in out
    assert "NOT run (stage 3 skipped)" in out
    assert "own suite run" not in out, (
        "the summary claims the suite ran on a path where it was skipped: %s"
        % out)


# ------------------------------------------------- the real tree, end to end

def test_the_live_papers_tree_classifies_cleanly():
    """Not a mutation -- the positive control. If this ever reports a stray,
    somebody added a directory under papers/ that is neither a paper nor
    provenance, and the right response is to name it in NOT_PAPERS or give it
    a PAPER.md, not to widen the classifier."""
    papers, skipped, strays = V.classify(HERE)
    assert "phase1-workshop" in papers
    assert strays == [], "unclassified directory under papers/: %s" % strays


def test_this_gate_declares_a_negative_sample_that_exists():
    """`monitor/gates.py` reads the declaration out of the gate's source. A
    declaration pointing at a file that never landed is worse than none."""
    sys.path.insert(0, os.path.dirname(HERE))
    try:
        from monitor import gates
    except ImportError:
        pytest.skip("monitor package not importable from here")
    ns = gates.negative_sample_of(os.path.dirname(HERE),
                                  os.path.join(HERE, "verify.py"))
    assert ns is not None, "papers/verify.py declares no negative sample"
    assert ns["exists"], "declared negative sample does not exist: %s" % ns
    assert ns["declared"] == "papers/test_verify_delegator.py"
