"""A solver that could not compute must not be recorded as a world that passed.

`engines.lp_potential.run` raises `LpUnavailable` for HiGHS status 1, 3 and 4
(E-15) — an iteration limit, an unbounded relaxation, numerical difficulties.
None of the three says anything about the configuration, which is why E-15 stopped
the engine from returning the `(None, None)` that downstream reads as *no linear
pagoda exists*.

`props/lp_potential.py` caught `CertificateError` in four places and
`LpUnavailable` in none, so the refusal escaped to `finding.run_invariants`,
became a `raised`, and `campaign.json`'s `invariant_worlds_evaluated` — which
subtracts `skipped` and only `skipped` — counted the world as **evaluated**.
`finding.failures()` returned `VIOLATED` alone, so nothing failed either.

The measured shape of that, before the fix, on the 12 worlds used here:

| run | raised | `invariant_worlds_evaluated` |
|---|---|---|
| normal | 0 | 5 |
| HiGHS starved to `maxiter=0` | 44 | **11** |

Blinding the solver *raised* the coverage the battery claimed, because honest
declines are subtracted and blind spots are not. That is the coverage column
running backwards, and it is the thing these tests pin.

## The lever is a real solver limit, not a stub

`solver_options={"maxiter": 0}` goes to the real `scipy.optimize.linprog` and
produces a genuine HiGHS status 1. Nothing is mocked; `engine-rig` is untouched.
The injection point is `props/lp_potential._solve` — **fuzzlab's own seam**, the
one the mutation battery uses, per the house rule in `README.md`. A test that
substitutes a fake result object proves the branch is reachable, not that HiGHS
ever reaches it.
"""

import pytest

from fuzzlab import campaign
from fuzzlab.props import finding
import fuzzlab.props.lp_potential as props

WORLDS = 12
SEED = campaign.DEFAULT_SEED
STARVED = {"maxiter": 0}


def _starved(world):
    """The real engine on the real graph, with a real zero-iteration budget."""
    from engines import lp_potential as engine
    return engine.run(world.graph, world.initial,
                      goal_states=list(world.goal_states),
                      solver_options=STARVED)


#: Captured at import, before any fixture can rebind it.  The first cut of this
#: file patched inside a `yield` fixture, so a test asking for both `starved_run`
#: and `live_run` got two starved runs and the comparison passed vacuously in one
#: direction and failed in the other.  The patch is now scoped to the call.
_PRISTINE_SOLVE = props._solve


def _run_with(solve) -> dict:
    original = props._solve
    props._solve = solve
    try:
        return campaign.run_engine("lp_potential", SEED, WORLDS, quiet=True)
    finally:
        props._solve = original


@pytest.fixture
def starved_run():
    return _run_with(_starved)


@pytest.fixture
def live_run():
    return _run_with(_PRISTINE_SOLVE)


# --------------------------------------------------------- the negative sample

def test_a_starved_solver_judges_nothing(starved_run):
    """Not one world may be recorded as evaluated when no LP was solved."""
    report = starved_run["report"]
    evaluated = report["invariant_worlds_evaluated"]
    assert set(evaluated) == set(props.INVARIANTS)
    for name in sorted(props.INVARIANTS):
        assert evaluated[name] == 0, (
            "%s claims %d worlds evaluated with HiGHS given zero iterations; a "
            "world no LP was solved for is a world nothing was judged on"
            % (name, evaluated[name]))


def test_a_starved_solver_is_attributable_not_merely_absent(starved_run):
    """`campaign.json` must say *why*, and say it in a machine-readable field."""
    report = starved_run["report"]
    for name in sorted(props.INVARIANTS):
        causes = report["skips_by_cause"][name]
        assert causes.get("solver_unavailable", 0) > 0, (
            "%s recorded no solver_unavailable skip; the skips it did record "
            "are %r" % (name, causes))
        assert report["invariant_worlds_unavailable"][name] > 0
    assert report["unavailable"] > 0


def test_unavailable_is_not_the_same_field_as_a_clean_decline(starved_run, live_run):
    """The V-13 rule: two different reasons may not produce one number.

    The live run's skips are `no_certificate` — the engine looking and correctly
    declining, cause-class `declined`. The starved run's are overwhelmingly
    `solver_unavailable`, class `unavailable`. Same `kind`, different columns,
    and the columns are what a reader audits.

    **Not all of them, and the exception is the point.** On 1 of these 12 worlds
    HiGHS settles infeasibility in presolve and never reaches its iteration
    budget, so even starved it returns a genuine `no_linear_pagoda` and the skip
    is a correct `no_certificate`. The first version of this test asserted the
    starved run files *no* `no_certificate` and failed on exactly that world. The
    assertion was wrong, not the engine: a taxonomy that could not represent "the
    solver was starved and answered anyway" would be sorting by which run it was
    rather than by what happened. So what is pinned is that the two causes are
    counted apart and move independently — which is the V-13 rule — and not that
    each run has only one of them.
    """
    live = live_run["report"]
    starved = starved_run["report"]
    for name in sorted(props.INVARIANTS):
        live_causes = live["skips_by_cause"][name]
        starved_causes = starved["skips_by_cause"][name]
        assert live_causes.get("solver_unavailable", 0) == 0
        assert live["invariant_worlds_unavailable"][name] == 0
        assert live_causes.get("no_certificate", 0) > 0
        assert starved_causes.get("solver_unavailable", 0) > 0
        # The two reasons do not collapse into one number in either direction.
        assert (starved_causes.get("no_certificate", 0)
                < live_causes["no_certificate"])
        assert (starved["skips_by_cause_class"][name].get("unavailable", 0)
                > live["skips_by_cause_class"][name].get("unavailable", 0))


def test_blinding_the_solver_lowers_coverage_it_does_not_raise_it(
        starved_run, live_run):
    """The regression, in the exact direction the defect ran.

    Pre-fix these numbers were 11 (starved) against 5 (live): removing the
    solver's ability to answer *improved* the reported coverage. Asserting
    `starved < live` rather than `starved == 0` is deliberate — it is the
    property that was false, stated as a comparison so it stays meaningful if
    the world count or the corpus changes.
    """
    live = live_run["report"]["invariant_worlds_evaluated"]
    starved = starved_run["report"]["invariant_worlds_evaluated"]
    for name in sorted(props.INVARIANTS):
        assert live[name] > 0, (
            "the live run judged no worlds either, so this comparison would "
            "pass vacuously")
        assert starved[name] < live[name], (
            "%s: starving the solver reports %d worlds evaluated against %d "
            "with it running" % (name, starved[name], live[name]))


def test_a_starved_solver_does_not_pass_the_gate(starved_run):
    """`failures()` is the gate, and an unjudged world must not sail through it.

    Two independent things have to hold and they are asserted apart: the run
    files no `violated` (the engine did nothing wrong — a solver limit is not a
    defect and must never be reported as one), and it also files no `raised`,
    because the exception is now handled where the policy for it lives.
    """
    findings = starved_run["findings"]
    assert not [f for f in findings if f.kind == finding.VIOLATED], (
        "a solver iteration limit was filed as an engine violation; that is a "
        "false accusation, not a stricter gate")
    assert not finding.failures(findings)


# ------------------------------------------------- the control on the control

def test_removing_the_catch_lets_the_starved_solver_through(starved_run):
    """Non-vacuity: with the catch gone, the pathology comes straight back.

    A test that cannot be made to fail is a green light with nothing behind it.
    So `_skip_solver_unavailable` is rebound to re-raise — which is exactly the
    pre-V-21 control flow, since `except LpUnavailable: return <re-raises>`
    propagates — and the assertions above are shown to be false.

    What comes back is the whole defect at once: every world counted as
    evaluated, no `solver_unavailable` anywhere, and the coverage *higher* than
    the live run's. The `failures()` widening catches it a second way, which is
    asserted here too: before V-21 neither net existed.
    """
    def _rethrow(world, invariant, exc):
        raise exc

    original_helper = props._skip_solver_unavailable
    props._skip_solver_unavailable = _rethrow
    try:
        uncaught = _run_with(_starved)
    finally:
        props._skip_solver_unavailable = original_helper

    report = uncaught["report"]
    assert report["raised"] > 0, (
        "the catch was removed and nothing escaped -- the starved solver is not "
        "reaching the LP at all, so this control proves nothing")
    assert report["unavailable"] == 0
    for name in sorted(props.INVARIANTS):
        assert report["skips_by_cause"][name].get("solver_unavailable", 0) == 0
        assert report["invariant_worlds_evaluated"][name] > 0, (
            "%s: without the catch the unjudged worlds must be counted as "
            "evaluated -- that is the bug, and if it is not reproduced here "
            "these tests are passing for some other reason" % name)
    # And the second net: with the catch gone the run does not pass the gate.
    assert finding.failures(uncaught["findings"])


def test_the_starved_solver_really_is_a_real_highs_limit():
    """No stub anywhere: assert the status came from HiGHS, and is status 1.

    If `maxiter=0` ever stopped producing a genuine iteration limit -- a scipy
    upgrade, a presolve change -- every test above would go quietly vacuous,
    passing because nothing was ever starved. This is the assertion that would
    go red instead.
    """
    from engines.lp_potential.potential import LpUnavailable
    from fuzzlab import prng
    from fuzzlab.worlds import GENERATORS

    seen = []
    for index in range(WORLDS):
        world = GENERATORS["jumpgraph"](prng.derive(SEED, "jumpgraph", index))
        try:
            _starved(world)
        except LpUnavailable as exc:
            seen.append(exc.outcome)
    assert seen, "no world produced an LpUnavailable under maxiter=0"
    assert all(o is not None for o in seen), (
        "LpUnavailable arrived without its LpOutcome, so the skip cannot record "
        "which status fired")
    assert {o.status for o in seen} == {"budget"}, {o.status for o in seen}
    assert {o.solver_status for o in seen} == {1}
    assert not any(o.decided for o in seen)
