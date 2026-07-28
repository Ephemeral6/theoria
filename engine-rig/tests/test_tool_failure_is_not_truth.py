"""Negative controls for one family of bug: a tool's failure read as a fact.

C11.  A planner that stopped, a solver that ran out of iterations, an
enumeration that hit its cap and a witness list that hit its display budget are
all *facts about the tool*.  Theoria's constraint 6 says a universal claim needs
a proof and a bare UNSAT is not one -- "the search said no" does not count, a
certificate does.  Every test here is a **negative sample**: it drives a
component with a tool that failed and asserts the component declines to make a
claim.

The rule these tests are written to is that each one must be red *by
construction* if its fix is reverted, not merely red on some inputs.  Where that
needed a fake tool, the fake is in this file and its exit code and log are
literals, so nothing depends on which planner or solver is installed:

* `test_exit_12_without_the_exhaustion_line_is_not_a_proof` fails the moment
  `p13_fd_dividend.run_fd` goes back to `done.returncode == 12`;
* `test_the_satisficing_rung_may_not_prove_unsolvability` fails if the rung is
  dropped from the predicate, which is the other half of the canon;
* `test_a_double_failure_is_not_a_passing_control` fails if `same_answer` is
  recomputed without the `answered` guard;
* `test_a_zero_witness_budget_cannot_certify_anything` fails if the rechecker's
  obligations go back to reading truncated lists;
* `test_an_iteration_limit_is_not_an_infeasibility` fails if `solve_certificate`
  folds a non-infeasible solver stop back into `None`.

`test_exit_12_with_the_exhaustion_line_on_the_optimal_rung_is_a_proof` is here so
that the file cannot pass by a predicate that simply always says no: the canon is
meant to cost something and to still answer.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.fd_adapter import backends
from engines.lp_potential import LpUnavailable, potential
from engines.mdl_segmenter import segmenter
from engines.zero_space import zerospace
from recheck import forgeries
from recheck.certificate import certificate_from_spec
from recheck.ruleset import ruleset_from_spec
from recheck.verify import REJECT, recheck
from tools import p13_fd_dividend as p13

from test_recheck import cert, rules, spec


# ------------------------------------------------- a Fast Downward that failed

EXHAUSTED = backends.FD_EXHAUSTED

FAKE_FD = '''\
import sys
sys.stdout.write(%r)
sys.exit(%d)
'''


def fake_fd(tmp_path, log, exit_code):
    """A stand-in planner that prints `log` and exits `exit_code`.

    Written as a `.py` so `run_fd` launches it with `sys.executable`, which is
    the same branch a real `fast-downward.py` takes.  It never writes a plan
    file, so every run through it is a run that produced no plan -- the exact
    situation in which the exit code is all a caller has to go on.
    """
    path = tmp_path / "fake_fd.py"
    path.write_text(FAKE_FD % (log, exit_code), encoding="utf-8")
    return str(path)


def _instance(tmp_path):
    domain = tmp_path / "domain.pddl"
    problem = tmp_path / "problem.pddl"
    domain.write_text("(define (domain d))", encoding="utf-8")
    problem.write_text("(define (problem p))", encoding="utf-8")
    return str(domain), str(problem)


def test_exit_12_without_the_exhaustion_line_is_not_a_proof(tmp_path):
    """The negative control the canon exists for.

    Exit 12 is `SEARCH_UNSOLVED_INCOMPLETE`: "the search stopped without a
    plan".  FD emits it both when a complete search emptied its open list and
    when an incomplete one gave up, and only FD's own "Completely explored state
    space" separates the two.  Without that line there is no proof, and
    `unsolvable` must stay False.
    """
    domain, problem = _instance(tmp_path)
    run = p13.run_fd(
        fake_fd(tmp_path, "Search stopped without finding a solution.\n", 12),
        domain, problem,
    )
    assert run.exit_code == 12
    assert run.unsolvable is False, (
        "a bare exit 12 was read as a proof of unsolvability -- this is the "
        "defect backends.proves_unsolvable exists to prevent"
    )
    assert run.answered is False, "no plan and no proof is no answer"
    assert run.exhausted_reported is False


def test_exit_12_with_the_exhaustion_line_on_the_optimal_rung_is_a_proof(tmp_path):
    """...and the canon still answers, or refusing would be free."""
    domain, problem = _instance(tmp_path)
    run = p13.run_fd(
        fake_fd(tmp_path, "[t=0.1s] %s -- no solution!\n" % EXHAUSTED, 12),
        domain, problem,
    )
    assert run.rung == backends.FD_OPTIMAL
    assert run.unsolvable is True
    assert run.answered is True


def test_the_satisficing_rung_may_not_prove_unsolvability(tmp_path):
    """LAMA searches under a cost bound, so "exhausted" means "no cheaper plan".

    Same exit code, same log line as the test above; only the rung differs.  The
    predicate refuses, and `run_fd` picks the refusing rung for anything it
    cannot vouch for as complete and unbounded -- an alias here.
    """
    domain, problem = _instance(tmp_path)
    run = p13.run_fd(
        fake_fd(tmp_path, "[t=0.1s] %s -- no solution!\n" % EXHAUSTED, 12),
        domain, problem, alias=backends.FD_SATISFICING_ALIAS,
    )
    assert run.rung == backends.FD_SATISFICING
    assert run.exhausted_reported is True, "the log did say it explored everything"
    assert run.unsolvable is False, "and that is still not a proof on this rung"


@pytest.mark.parametrize("exit_code", [1, 22, 23, 30])
def test_a_crashed_planner_asserts_nothing(tmp_path, exit_code):
    """Out of memory, out of time, driver error: none of them is an answer."""
    domain, problem = _instance(tmp_path)
    run = p13.run_fd(fake_fd(tmp_path, "boom\n", exit_code), domain, problem)
    assert run.unsolvable is False
    assert run.answered is False


def test_a_double_failure_is_not_a_passing_control():
    """Two crashed runs used to agree, and the agreement was the gate.

    `same_answer` gates "the deadlock theorems did not change this instance's
    answer".  When both runs fail, `plan_length` is `None` on both sides and
    `unsolvable` is False on both, so the old conjunction was True and a row
    that measured nothing published itself as a passing control.
    """
    dead = p13.FdRun(config=p13.BLIND, rung=backends.FD_OPTIMAL, exit_code=30,
                     expansions=None, plan_length=None, plan=None,
                     unsolvable=False, exhausted_reported=False)
    assert dead.answered is False
    assert (dead.plan_length == dead.plan_length
            and dead.unsolvable == dead.unsolvable), (
        "the old expression really did evaluate to True on two dead runs"
    )
    assert p13.same_answer(dead, dead) is None

    solved = p13.FdRun(config=p13.BLIND, rung=backends.FD_OPTIMAL, exit_code=0,
                       expansions=9, plan_length=4, plan=["(a)"] * 4,
                       unsolvable=False, exhausted_reported=False)
    assert p13.same_answer(solved, dead) is None, "one dead run is enough"
    assert p13.same_answer(solved, solved) is True, "and real agreement survives"
    longer = p13.FdRun(config=p13.BLIND, rung=backends.FD_OPTIMAL, exit_code=0,
                       expansions=9, plan_length=5, plan=["(a)"] * 5,
                       unsolvable=False, exhausted_reported=False)
    assert p13.same_answer(solved, longer) is False, "and so does real disagreement"

    report = {
        "executable": "fake", "search": p13.BLIND,
        "deadlock_dividend": [{
            "instance": "crashed", "theorems": 3, "theorems_encoded": 3,
            "fd_expansions_before": None, "fd_expansions_after": None,
            "fd_plan_before": None, "fd_plan_after": None,
            "fd_unsolvable_before": False, "fd_unsolvable_after": False,
            "fd_answered_before": False, "fd_answered_after": False,
            "fd_exit_code_before": 30, "fd_exit_code_after": 30,
            "same_answer": None,
            "stub_expansions_before": 44, "stub_expansions_after": 22,
        }],
        "cross_check": [{
            "instance": "crashed", "status": "ran",
            "stub_plan_length": None, "stub_unsolvable": True,
            "stub_expansions": 7, "fd_plan_length": None,
            "fd_unsolvable": False, "fd_answered": False,
            "fd_rung": backends.FD_OPTIMAL, "fd_exhausted_reported": False,
            "fd_expansions": None, "fd_exit_code": 30, "agree": None,
        }],
    }
    text = p13.render(report)
    assert "yes" not in text, "a row nobody answered must not read as agreement"
    assert "**NO**" not in text, "nor as a disagreement FD never voiced"
    assert "no answer" in text
    assert "Nothing about this instance follows from it." in text


def test_a_planner_that_did_not_answer_is_not_a_planner_that_disagreed():
    """`agree` is None, not False, when FD said nothing.

    The stub proved this instance unsolvable.  Reading `fd.unsolvable is False`
    against it files a cross-backend disagreement against a backend that
    crashed.
    """
    crashed = p13.FdRun(config=p13.BLIND, rung=backends.FD_OPTIMAL, exit_code=22,
                        expansions=None, plan_length=None, plan=None,
                        unsolvable=False, exhausted_reported=False)
    assert (True == crashed.unsolvable) is False, (
        "the old expression really did call this a disagreement"
    )
    assert p13.backends_agree(True, None, crashed) is None

    proved = p13.FdRun(config=p13.BLIND, rung=backends.FD_OPTIMAL, exit_code=12,
                       expansions=0, plan_length=None, plan=None,
                       unsolvable=True, exhausted_reported=True)
    assert p13.backends_agree(True, None, proved) is True
    solved = p13.FdRun(config=p13.BLIND, rung=backends.FD_OPTIMAL, exit_code=0,
                       expansions=4, plan_length=2, plan=["(a)", "(b)"],
                       unsolvable=False, exhausted_reported=False)
    assert p13.backends_agree(True, None, solved) is False, (
        "a real disagreement -- stub proved UNSAT, FD returned a plan -- must "
        "still be reported"
    )
    assert p13.backends_agree(False, 2, solved) is True
    assert p13.backends_agree(False, 3, solved) is False


# ---------------------------------------------------------------- the LP solver

class _Stopped:
    """What `linprog` returns when it stopped without deciding."""

    def __init__(self, status):
        self.success = False
        self.status = status
        self.message = "synthetic"
        self.x = None


GRAPH = {"n_pos": 4, "goal_states": ["1000"],
         "edges": [], "triples": [[0, 1, 2], [2, 1, 0]]}


@pytest.mark.parametrize("status", [1, 3, 4])
def test_an_iteration_limit_is_not_an_infeasibility(monkeypatch, status):
    """Only HiGHS status 2 says anything about the configuration.

    Status 1 (iteration limit), 3 (unbounded) and 4 (numerical difficulties) are
    facts about the solver.  Folding them into `None` would let a resource limit
    publish itself as "no linear pagoda exists", which is what the caller's
    docstring reads `None` as.
    """
    monkeypatch.setattr(potential, "linprog", lambda **kw: _Stopped(status))
    with pytest.raises(LpUnavailable):
        potential.solve_certificate(GRAPH, "0011")


def test_a_proved_infeasibility_still_returns_none(monkeypatch):
    """The refusal has to keep the real answer reachable."""
    monkeypatch.setattr(potential, "linprog", lambda **kw: _Stopped(2))
    assert potential.solve_certificate(GRAPH, "0011") is None


# --------------------------------------------------------- the witness budget

def test_a_zero_witness_budget_cannot_certify_anything():
    """A *display* budget used to decide three certificate obligations.

    `inv_closed`, `goal_break` and `potential_nonincreasing` were each
    `not <list truncated to max_witnesses>`.  At `max_witnesses=0` the lists are
    empty whatever the world does, so a tampered certificate that this checker
    rejects at the default budget was accepted at a budget of zero.
    """
    payload = spec("peg4-1110-pagoda", "cert")
    payload.pop("ruleset")
    payload["weights"]["pos3"] = 5           # the tamper test_recheck performs
    ruleset, certificate = rules("peg4-1110"), certificate_from_spec(payload)

    at_default = recheck(ruleset, certificate)
    assert at_default.verdict == REJECT
    assert at_default.conditions["potential_nonincreasing"] is False

    starved = recheck(ruleset, certificate, max_witnesses=0)
    assert starved.conditions["potential_nonincreasing"] is False, (
        "a certificate was accepted because nobody had budget to print the "
        "counterexample"
    )
    assert starved.verdict == REJECT
    assert starved.witnesses.get("potential_nonincreasing", []) == [], (
        "the budget still governs what is shown -- only not what is decided"
    )
    assert starved.stats["n_raising_transitions"] > 0


def test_a_zero_witness_budget_cannot_close_an_open_invariant():
    """The same starvation on `inv_closed`, the inductive-invariant obligation.

    `a2-right-room-locked` is A2's false theorem: true of the manual, false of
    the world, and it escapes through the teleport.  `closed_bad` is filled
    under `len(closed_bad) < max_witnesses`, so at a budget of zero the escape
    list is empty and the invariant closes on a world it does not hold in.
    """
    ruleset, certificate = rules("a2-world"), cert("a2-right-room-locked")
    assert recheck(ruleset, certificate).conditions["inv_closed"] is False

    starved = recheck(ruleset, certificate, max_witnesses=0)
    assert starved.conditions["inv_closed"] is False, (
        "a false invariant closed because nobody had budget to print its escape"
    )
    assert starved.verdict == REJECT
    assert starved.witnesses.get("inv_closed", []) == []
    assert starved.stats["n_escaping_transitions"] > 0


@pytest.mark.parametrize(
    "forgery", forgeries.CATALOGUE, ids=lambda f: f.name)
def test_no_forgery_survives_by_starving_the_witness_budget(forgery):
    """The general form, over the whole forgery catalogue.

    The named tests above pin the three obligations that were coupled to
    `max_witnesses`; this one says the property they are instances of, on every
    forgery the rechecker is tested against: **the display budget may not change
    a verdict.**  It covers the branches a hand-written fixture keeps missing --
    `goal_break` under `inductive_invariant`, `region_closed` under
    `dead_region` -- because the catalogue already contains a forgery that
    breaks each one (`claims-everything`, `region-that-leaks`).
    """
    try:
        ruleset_spec, certificate_spec = forgery.build()
        ruleset = ruleset_from_spec(ruleset_spec)
        certificate = certificate_from_spec(certificate_spec)
    except Exception:                     # a forgery that will not even load
        pytest.skip("forgery is refused before any obligation is evaluated")

    full = recheck(ruleset, certificate)
    starved = recheck(ruleset, certificate, max_witnesses=0)
    assert starved.conditions == full.conditions, (
        "a budget of zero changed what this checker decided about %s"
        % forgery.name
    )
    assert starved.verdict == full.verdict


def test_a_zero_budget_cannot_certify_a_broken_region_either():
    """The same starvation, on the other two obligations."""
    payload = spec("peg4-1110", "rules")
    payload["goal"] = ["and",
                       ["=", ["var", "pos0"], ["lit", 1]],
                       ["=", ["var", "pos1"], ["lit", 0]],
                       ["=", ["var", "pos2"], ["lit", 0]],
                       ["=", ["var", "pos3"], ["lit", 1]]]
    unbound = spec("peg4-1110-pagoda", "cert")
    unbound.pop("ruleset")
    starved = recheck(ruleset_from_spec(payload), certificate_from_spec(unbound),
                      max_witnesses=0)
    assert starved.conditions["goal_break"] is False
    assert starved.verdict == REJECT


# -------------------------------------------------- truncated enumerations

def test_a_truncated_subset_scan_does_not_get_to_call_a_law_global():
    """`scope: "global"` is a claim about the world; the budget must show.

    Above `SUBSET_ENUMERATION_LIMIT` colours a cell's subsets are not
    enumerated, so a cell-local law can be missed and published as a law about
    the world.  Ten colours -- an ARC palette -- crosses the limit, so this is
    a live path and not a hypothetical one.
    """
    colors = [chr(ord("a") + i) for i in range(zerospace.SUBSET_ENUMERATION_LIMIT + 2)]
    states = [[colors[i % len(colors)], colors[(i + 1) % len(colors)]]
              for i in range(len(colors))]
    result = zerospace.analyse(states, colors)
    assert result.truncated_cells, "this fixture is meant to hit the limit"
    assert result.scope_exhaustive is False
    assert all(law.scope_exhaustive is False for law in result.laws)

    small = zerospace.analyse([["r", "b"], ["b", "r"], ["r", "b"]], ["r", "b"])
    assert small.truncated_cells == []
    assert small.scope_exhaustive is True
    assert all(law.scope_exhaustive for law in small.laws)


def test_an_inexplicable_transition_is_raised_not_billed_as_nothing():
    """`_match_cost`'s IMPOSSIBLE sentinel shares a `kind` with "no change".

    The driver's `if kind is not None` treats both as "nothing happened", so an
    unexplained transition would cost zero bits, emit no event, and continue the
    track in silence -- the model's failure published as a fact about the
    trajectory.  The vanish/appear lanes normally make that unreachable; this
    test prices them above IMPOSSIBLE so the optimiser is forced into the cell,
    and asserts the segmenter raises instead of billing it.
    """
    a = segmenter.Component(cells=((0, 0),), colors=(1,))
    b = segmenter.Component(cells=((0, 0), (0, 1)), colors=(2, 3))
    assert segmenter._match_cost(a, b, segmenter.CostModel(4, 4))[0] == segmenter.IMPOSSIBLE

    class Ruinous(segmenter.CostModel):
        def vanish_bits(self):
            return segmenter.IMPOSSIBLE * 10

        def appear_bits(self, n_cells, box_h, box_w):
            return segmenter.IMPOSSIBLE * 10

    with pytest.raises(segmenter.SegmentationError):
        segmenter._assign([a], [b], Ruinous(4, 4))


# ------------------------------------------------------ the budget is published

def test_a_search_result_carries_the_budget_it_ran_under():
    """`plan is None` from the stub is a proof; the artefact has to show why."""
    from engines.fd_adapter import search as stub

    empty = stub.SearchResult(None, 0, 0, 0, 0)
    assert empty.exhaustive is False, (
        "the placeholder the Fast Downward path builds must not inherit a claim "
        "about a bundled search that never ran"
    )


# ------------------------------------------- the standing check, and its own

def test_the_standing_check_is_green_on_this_territory():
    """`tools/check_solver_status` runs here, in the suite that gates merges.

    `monitor/gates.py` resolves engine-rig's gate to pytest -- there is no
    `verify.sh` in this directory -- so a check that is not a test is a check
    that does not run.
    """
    from tools import check_solver_status as check

    findings = [f for f in check.check_paths([check.HERE])
                if f.level == check.ERROR]
    assert not findings, "\n".join(f.render() for f in findings)


def test_the_standing_check_catches_the_defect_it_was_written_for():
    """Its own negative control: the pre-fix line, verbatim."""
    from tools import check_solver_status as check

    before = "unsolvable=done.returncode == 12,\n"
    findings = check.check_source("f(\n    %s)\n" % before, "<synthetic>")
    assert len(findings) == 1
    assert findings[0].target == "unsolvable"
    assert findings[0].level == check.ERROR


def test_the_standing_check_accepts_the_fix():
    """Routing the same comparison through a predicate has to silence it.

    Otherwise the only way to a green check is to stop asking the question,
    which is worse than the defect.
    """
    from tools import check_solver_status as check

    after = ("f(\n    unsolvable=backends.proves_unsolvable("
             "rung, done.returncode, log),\n)\n")
    assert check.check_source(after, "<synthetic>") == []


@pytest.mark.parametrize("source", [
    # Control flow: nobody stores the comparison as a claim.
    "if proc.returncode != 0:\n    raise RuntimeError('boom')\n",
    # A gate reporting on its own subprocess -- note level at most, never error.
    "ok = proc.returncode == 0\n",
    # The engine's own verdict field, compared to its own constant.
    "reachable = self.status == REACHABLE\n",
    # A raise is the conservative direction and is never a finding.
    "def unsolvable(r):\n    if r.status != 2:\n        raise LpUnavailable()\n"
    "    return None\n",
])
def test_the_standing_check_does_not_fire_on_correct_code(source):
    """The false positives calibration found and the vocabulary now excludes."""
    from tools import check_solver_status as check

    assert [f for f in check.check_source(source, "<synthetic>")
            if f.level == check.ERROR] == []
