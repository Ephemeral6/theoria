"""E15 -- the reason a solver went quiet has to survive to the caller.

`lp_potential` is sound but incomplete and `zero_space`'s subset enumeration is
capped; neither of those is a defect and nothing here treats them as one.  What
these tests pin is narrower: **silence must arrive with its cause attached.**

The two negative controls live in `tools/check_status_bit.py` and are run here
as a *subprocess*, judged on the process exit code and on the artifact the
engines wrote -- not on the return value of an internal function.  A control that
can only be observed from inside the interpreter that produced it is a weaker
witness than one a shell can check, and this repository has twice had to learn
that a green in-process assertion and a working command are different facts.

P4's two standalone controls sit beside the run they belong to --
`runs/20260729T044500Z-E15-solver-status-bit/controls/n1_iteration_limit.py` and
`.../n2_over_eight_colours.py`, the shape E7 and E16 use for an attack script --
and are invoked here the same way.  They are one process each, so a reader can
tell from the exit codes alone *which* property broke, and each writes its own
verdict artifact listing every check by name.  Their non-vacuity is measured,
not asserted: `runs/20260729T044500Z-E15-solver-status-bit/NONVACUITY.md` records
the exit codes observed under the engine as committed and under the pre-E15
collapse, from a scratch copy built out of git HEAD.

Both sets are kept.  They differ in the world they attack N1 on -- the standing
check picks one that *does* certify at the default budget, these pick one whose
honest answer is `no_linear_pagoda`, i.e. the very answer an iteration limit used
to counterfeit -- and a control family whose members all choose the same fixture
is a family with one member.
"""

import json
import os
import subprocess
import sys

import pytest

from engines import lp_potential, zero_space
from engines.lp_potential import potential
from engines.zero_space import zerospace

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run_controls(*extra):
    return subprocess.run(
        [sys.executable, "-m", "tools.check_status_bit", *extra],
        cwd=HERE, capture_output=True, text=True,
    )


def test_the_negative_controls_exit_zero_as_a_process():
    """N1 and N2, through the real entry points, judged on the exit code."""
    done = _run_controls()
    assert done.returncode == 0, done.stdout + done.stderr
    assert "FAILED" not in done.stdout


def test_the_controls_report_which_entry_points_they_went_through():
    """A control that never reached a public entry proves nothing about one."""
    done = _run_controls("--json")
    assert done.returncode == 0, done.stdout + done.stderr
    report = json.loads(done.stdout)
    assert report["held"] is True
    entries = {e for c in report["controls"] for e in c["entry_points"]}
    assert entries == {"engines.lp_potential.decide", "engines.lp_potential.run",
                       "engines.zero_space.run"}
    n1 = report["controls"][0]
    assert n1["baseline_status"] == potential.CERTIFIED, (
        "N1 is only sharp on a world that does admit a pagoda at the default "
        "budget -- otherwise 'no pagoda' would have been the right answer"
    )
    assert n1["starved_status"] == potential.BUDGET
    assert n1["starved_solver_status"] == 1


# ------------------------------------------- P4: the two standalone controls

CONTROLS = os.path.join(HERE, "runs", "20260729T044500Z-E15-solver-status-bit",
                        "controls")
N1 = os.path.join(CONTROLS, "n1_iteration_limit.py")
N2 = os.path.join(CONTROLS, "n2_over_eight_colours.py")


def _run_control(script, out_dir):
    """One control, one process, its verdict artifact read back off disk.

    `--out-dir` points at pytest's `tmp_path` rather than the control's own
    `artifacts/`: the checked-in copies there are the run's evidence and a test
    that overwrites its own evidence has destroyed the thing it was proving.
    """
    done = subprocess.run(
        [sys.executable, script, "--out-dir", str(out_dir)],
        cwd=HERE, capture_output=True, text=True,
    )
    return done


def _artifact(out_dir, name):
    with open(os.path.join(str(out_dir), name), "r", encoding="utf-8") as handle:
        return json.load(handle)


def test_n1_the_iteration_limit_control_exits_zero_as_a_process(tmp_path):
    """A real HiGHS status 1, on a world whose honest answer is status 2.

    The two used to be the same value at the caller.  The control is judged
    here on what the process did and on the artifact it left behind -- if it
    were judged on a return value, the return value being ambiguous is exactly
    the defect under test.
    """
    done = _run_control(N1, tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr

    report = _artifact(tmp_path, "n1-iteration-limit.json")
    assert report["verdict"] == "hold"
    assert report["exit_code"] == 0
    assert report["failures"] == []
    assert report["checks"] and all(c["passed"] for c in report["checks"])

    observed = report["observed"]
    assert observed["solver_status"] == 1, "the control must reach a real budget"
    assert observed["status"] == potential.BUDGET
    assert observed["no_linear_pagoda"] is False
    assert observed["decided"] is False
    assert observed["run_raised_status"] == potential.BUDGET, (
        "the public entry has to refuse, and the refusal has to say which "
        "status fired"
    )
    # ...while the same configuration, unbudgeted, still gives the real answer:
    # without this the control is satisfied by an engine that refuses everything.
    assert observed["baseline_status"] == potential.NO_LINEAR_PAGODA
    assert observed["baseline_run_returned"] == "(None, None)"
    assert report["solver_options"] == {"maxiter": 0}
    assert report["solver_is_real"].startswith("scipy.optimize"), (
        "a control that stubs the solver proves the branch is reachable, not "
        "that HiGHS ever reaches it"
    )


def test_n2_the_over_eight_colour_control_exits_zero_as_a_process(tmp_path):
    """A ten-colour palette through the real `zero_space.run`."""
    done = _run_control(N2, tmp_path)
    assert done.returncode == 0, done.stdout + done.stderr

    report = _artifact(tmp_path, "n2-over-eight-colours.json")
    assert report["verdict"] == "hold"
    assert report["exit_code"] == 0
    assert report["failures"] == []
    assert report["checks"] and all(c["passed"] for c in report["checks"])

    observed = report["observed"]
    assert observed["truncated_cells"], "the fixture has to cross the limit"
    assert observed["scope_counts"].get(zerospace.GLOBAL, 0) == 0
    assert observed["n_degraded"] > 0, (
        "a run that downgraded nothing published nothing that could have been "
        "wrong"
    )
    example = observed["degraded_example"]
    assert example["scope"] == zerospace.UNDETERMINED
    assert example["scope_proved"] is False
    assert example["subset_enumeration_limit"] == zerospace.SUBSET_ENUMERATION_LIMIT
    assert example["truncated_cells"]
    # the contrast: `global` still means something where it was earned
    assert observed["small_scope_counts"].get(zerospace.GLOBAL, 0) > 0
    assert observed["small_truncated_cells"] == []


def test_both_controls_fail_loudly_rather_than_silently(tmp_path):
    """Exit 1 has to be reachable, or exit 0 is not a measurement.

    Neither control can be driven red without changing the engine -- that is
    what makes them controls -- so what is checked here is the machinery that
    would report it: a failing check must set a non-zero `exit_code` in the
    artifact and name itself in `failures`.  The measured red runs are in
    `NONVACUITY.md`; this only pins that the reporting path exists.
    """
    for script, name in ((N1, "n1-iteration-limit.json"),
                         (N2, "n2-over-eight-colours.json")):
        out = tmp_path / os.path.basename(script)
        done = _run_control(script, out)
        assert done.returncode == 0
        report = _artifact(out, name)
        assert report["exit_code"] == (1 if report["failures"] else 0)
        assert report["verdict"] == ("violated" if report["failures"] else "hold")
        assert [c["name"] for c in report["checks"] if not c["passed"]] \
            == report["failures"]


# ------------------------------------------------------- the status bit itself

class _Stopped:
    """What `linprog` returns when it stopped without deciding."""

    def __init__(self, status):
        self.success = False
        self.status = status
        self.message = "synthetic"
        self.x = None


GRAPH = {"n_pos": 4, "goal_states": ["1000"],
         "edges": [], "triples": [[0, 1, 2], [2, 1, 0]]}


@pytest.mark.parametrize("status, word", [
    (1, potential.BUDGET),
    (2, potential.NO_LINEAR_PAGODA),
    (3, potential.UNBOUNDED),
    (4, potential.NUMERICAL),
    (99, potential.UNDECIDED),
])
def test_every_way_the_solver_can_stop_gets_its_own_word(monkeypatch, status, word):
    """Including a status the table does not know -- which must not become 2.

    An unrecognised code is the case no test was written for before, and the
    conservative reading is the only safe one: an engine that has never seen a
    status cannot have proved anything with it.
    """
    monkeypatch.setattr(potential, "linprog", lambda **kw: _Stopped(status))
    outcome = potential.solve(GRAPH, "0011")
    assert outcome.status == word
    assert outcome.solver_status == status
    assert outcome.no_linear_pagoda is (status == 2)
    assert outcome.decided is (status == 2)


class _Contradictory:
    """A `linprog` result whose `success` flag and `status` code disagree.

    Not a shape scipy is expected to produce -- which is the point.  If it ever
    does, one of the two fields is being read wrong, and neither reading is a
    fact about the configuration.
    """

    def __init__(self, status, success, x=None):
        self.success = success
        self.status = status
        self.message = "synthetic contradiction"
        self.x = x


@pytest.mark.parametrize("status, success", [
    (0, False),   # the direction E15's mutation battery found unguarded (M30)
    (2, True),
    (1, True),
])
def test_a_solver_contradicting_itself_is_refused_not_classified(
        monkeypatch, status, success):
    """Neither field wins when they disagree -- the engine declines instead.

    The `status == 0, success == False` case is the one that mattered and the
    one no assertion covered: it used to fall through to `result.x` and mint a
    Certificate from whatever a failed solve left behind.  The exact re-check
    would then have failed it as a `CertificateError` -- *weights that did not
    survive re-checking* -- which reads as *the engine tried and the geometry
    refused*, when in truth no solve ever succeeded.  A wrong story about the
    world, told confidently, is precisely what this item exists to prevent.
    """
    monkeypatch.setattr(
        potential, "linprog",
        lambda **kw: _Contradictory(status, success, x=[0.0] * 8))
    with pytest.raises(potential.LpUnavailable) as caught:
        potential.solve(GRAPH, "0011")
    assert "disagree" in str(caught.value)
    # The refusal carries a structured outcome so the contradiction stays
    # diagnosable -- but an `undecided` one.  A refusal that carried
    # `decided is True` (which statuses 0 and 2 would otherwise produce) would
    # put the collapse back on the error path after this item removed it from
    # the return path.
    assert caught.value.outcome is not None
    assert caught.value.outcome.solver_status == status
    assert caught.value.outcome.status == potential.UNDECIDED
    assert caught.value.outcome.decided is False
    assert caught.value.outcome.no_linear_pagoda is False


def test_no_linear_pagoda_is_not_reconstructible_from_a_missing_certificate():
    """`certificate is None` is true for four different reasons; the word is not.

    This is the whole item in one assertion.  Both outcomes below have no
    certificate; only one of them says anything about the configuration.
    """
    budget = potential.LpOutcome(status=potential.BUDGET, solver_status=1,
                                 solver_message="", bound=10, margin=1)
    proved = potential.LpOutcome(status=potential.NO_LINEAR_PAGODA,
                                 solver_status=2, solver_message="",
                                 bound=10, margin=1)
    assert budget.certificate is None and proved.certificate is None
    assert budget.no_linear_pagoda is False and proved.no_linear_pagoda is True
    assert budget.as_json()["decided"] is False
    assert proved.as_json()["decided"] is True
    # The claim is boxed and says so, on every row, not only where it bit.
    assert "|w_i| <= 10" in proved.as_json()["scope_of_claim"]


@pytest.mark.parametrize("status", [1, 3, 4, 99])
def test_the_public_pair_entry_refuses_rather_than_answering(monkeypatch, status):
    """`run` must not hand back `(None, None)` for a solver that gave up."""
    monkeypatch.setattr(potential, "linprog", lambda **kw: _Stopped(status))
    with pytest.raises(lp_potential.LpUnavailable) as caught:
        lp_potential.run(GRAPH, "0011")
    assert caught.value.outcome.solver_status == status
    assert caught.value.outcome.no_linear_pagoda is False


@pytest.mark.parametrize("bound", [10, 100, 10 ** 4])
def test_the_box_travels_with_the_verdict(bound):
    """`no_linear_pagoda` is boxed, so the box has to be on the outcome.

    Added after a mutant that hard-coded `bound=10` into `LpOutcome` survived the
    first draft of this file: the census probes the same worlds at 1e2/1e4/1e6
    and every row would have gone out claiming the default. The box is not part
    of the pagoda definition (E11 §6 found one world in 3000 that is infeasible
    at 10 and feasible at 100), which is exactly why a claim that misreports it
    is not a cosmetic defect.
    """
    from tools.check_status_bit import (
        N1_GOALS, N1_INITIAL, N1_N_POS, N1_TRIPLES, jump_graph)

    graph = jump_graph(N1_N_POS, N1_TRIPLES, N1_GOALS, N1_INITIAL)
    outcome = potential.solve(graph, N1_INITIAL, bound=bound)
    assert outcome.status == potential.CERTIFIED
    assert outcome.bound == bound
    assert outcome.as_json()["bound"] == bound
    assert ("|w_i| <= %d" % bound) in outcome.as_json()["scope_of_claim"]


@pytest.mark.parametrize("bound", [10, 100, 10 ** 4])
def test_the_box_travels_with_a_refusal_too(bound):
    """And especially with a refusal, which is where the box is load-bearing.

    A first draft asserted this only on a world that certifies, and the two
    construction sites in `solve` are different lines -- a mutant that hard-coded
    `bound=10` on the declining one survived (P5, `M14`). That is the site the
    census reads: it re-probes the 639 at 1e2/1e4/1e6, and every one of those
    rows is a `no_linear_pagoda`. A misreported box there would turn "infeasible
    at 10^6" into "infeasible at 10" in the artifact, silently.
    """
    from fixtures import peg4

    with open(peg4.GRAPH_PATH, encoding="utf-8") as handle:
        graph = json.load(handle)
    outcome = potential.solve(graph, "0111", bound=bound)
    assert outcome.status == potential.NO_LINEAR_PAGODA
    assert outcome.bound == bound
    assert outcome.as_json()["bound"] == bound
    assert ("|w_i| <= %d" % bound) in outcome.as_json()["scope_of_claim"]


def test_the_status_table_covers_every_scipy_code_and_maps_only_two_to_a_verdict():
    """A table a reader can check, rather than control flow they must simulate."""
    assert set(potential.STATUS_WORDS) == {0, 1, 2, 3, 4}
    verdicts = [code for code, word in potential.STATUS_WORDS.items()
                if word == potential.NO_LINEAR_PAGODA]
    assert verdicts == [potential.HIGHS_INFEASIBLE]
    assert set(potential.DECIDED_STATUSES) == {potential.CERTIFIED,
                                               potential.NO_LINEAR_PAGODA}


# ------------------------------------------------------------ the scope label

def test_a_truncated_enumeration_publishes_undetermined_not_global():
    colors = [chr(ord("a") + i) for i in range(zerospace.SUBSET_ENUMERATION_LIMIT + 2)]
    states = [[colors[i % len(colors)], colors[(i + 1) % len(colors)]]
              for i in range(len(colors))]
    result = zerospace.analyse(states, colors)

    assert result.truncated_cells, "this fixture is meant to hit the limit"
    assert result.global_laws() == []
    assert result.undetermined_laws(), "the quotient reps have to go somewhere"
    for law in result.undetermined_laws():
        payload = law.as_json()
        assert payload["scope"] == zerospace.UNDETERMINED
        assert payload["scope_proved"] is False
        assert payload["truncated_cells"] == list(result.truncated_cells)
        assert "over budget" in payload["error"]
    assert "over budget" in result.as_json()["error"]
    # A consumer filtering on the old word must lose laws, never gain one.
    assert not any("global" == law.scope for law in result.laws)
    assert zerospace.GLOBAL not in zerospace.UNDETERMINED, (
        "the downgraded word must not contain the promoted one, or "
        "`'global' in scope` resurrects the claim"
    )


def test_an_exhaustive_run_is_byte_identical_to_before_the_downgrade():
    """The degradation keys are gated, and the gate is what keeps a pin valid.

    `engine-rig/artifacts/candidates.jsonl` is sha256-pinned in
    `release/MANIFEST.jsonl` and the candidate ids are content-addressed, so a
    key added to every payload re-hashes every zero_space row.  The keys are
    therefore emitted only where the budget actually bit.
    """
    result = zerospace.analyse([["r", "b"], ["b", "r"], ["r", "b"]], ["r", "b"])
    assert result.truncated_cells == []
    for law in result.laws:
        assert set(law.as_json()) == {
            "form", "modulus", "features", "coefficients", "support", "value",
            "scope", "rendering",
        }
    assert result.as_json()["error"] is None


def test_a_downgraded_law_still_holds_on_the_trajectory():
    """The label weakened; the law did not.

    `undetermined` says the *classification* was not searched for, not that the
    conservation law is in doubt -- `verify` re-checks every reported law against
    the trajectory and must still pass.  Without this, the downgrade could be
    read as the engine hedging on its own algebra.
    """
    colors = [chr(ord("a") + i) for i in range(zerospace.SUBSET_ENUMERATION_LIMIT + 2)]
    states = [[colors[i % len(colors)], colors[(i + 1) % len(colors)]]
              for i in range(len(colors))]
    result = zero_space.run(states, colors)
    assert zerospace.verify(result, states)
