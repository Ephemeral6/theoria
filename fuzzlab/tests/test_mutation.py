"""The mutation harness, checked against the standard it exists to enforce.

This module measures whether the battery's invariants can be made to fire. A
harness that quietly stopped injecting anything would report every mutant as a
survivor and read as a devastating result about the battery — the failure is
loud in the direction of *more* findings, which is the worst direction for a
tool whose output is a list of accusations.

So the same rule applies to it as to everything else here: a probe that cannot
be shown failing is a green light with nothing behind it. These tests are the
harness's own negative control.

`test_flip_law_value_is_killed_and_baseline_is_clean` is the load-bearing one.
It pins a *known* engine defect against a *known* verdict: baseline clean, one
named invariant fires, and — the part that matters — the other three do not. If
injection silently stopped working the first half fails; if the seam started
leaking across invariants the second half fails.
"""

import pytest

from fuzzlab import mutation
from fuzzlab import mutants as mut
from fuzzlab.props import finding, load

WORLDS = 8          # enough for the pinned assertions; this is not a campaign


def _zero_space_worlds():
    module = load("zero_space")
    return module, mutation.build_worlds(module.FAMILY, mutation.DEFAULT_SEED, WORLDS)


def _mutant(mutant_id: str) -> mut.Mutant:
    for m in mut.catalog():
        if m.id == mutant_id:
            return m
    raise AssertionError("no mutant %r in the catalogue" % mutant_id)


# ------------------------------------------------------------------ the seam

def test_seam_is_restored_after_an_exception_inside_the_body():
    """A crash mid-campaign must not leave a patched property module behind.

    This is why the injection is a context manager over fuzzlab's own attribute
    rather than surgery on `sys.modules`: the restore has to survive the
    failure path, and the failure path is the one that gets exercised when a
    mutant is doing its job.
    """
    module = load("zero_space")
    before = module._analyse
    with pytest.raises(RuntimeError):
        with mut.applied(_mutant("zs-drop-basis-vector"), []):
            raise RuntimeError("boom")
    assert module._analyse is before


def test_an_unknown_seam_is_refused_rather_than_silently_skipped():
    bad = mut.Mutant(
        id="test-no-such-seam", engine="zero_space", seam="_no_such_helper",
        kind=mut.UNSOUND, claim="test fixture", description="test fixture",
        corrupt=lambda r, a, k: r, expect_kill=("rank_nullity",))
    with pytest.raises(AttributeError):
        with mut.applied(bad, []):
            pass


# ------------------------------------------------------- the inert detection

def test_a_mutant_that_changes_nothing_is_inert_and_not_a_survivor():
    """The whole report turns on this distinction.

    A corruption that fails to apply produces exactly the same campaign output
    as an invariant that failed to notice one that did. Counting the first as
    the second manufactures findings, so the driver must take those worlds out
    of the denominator and leave `worlds_evaluated` at zero rather than
    reporting a mutant nothing killed.
    """
    module, worlds = _zero_space_worlds()
    noop = mut.Mutant(
        id="test-noop", engine="zero_space", seam="_analyse", kind=mut.UNSOUND,
        claim="test fixture: contradicts nothing, on purpose",
        description="returns the engine's answer unchanged",
        corrupt=lambda result, args, kwargs: result,
        expect_kill=("rank_nullity",))
    row = mutation.run_mutant(noop, worlds, {})
    assert row["worlds_evaluated"] == 0
    assert row["worlds_inert"] == len(worlds)
    assert row["predicted_but_missed"] == ["rank_nullity"]
    # The assertions above are what this test originally checked, and an
    # adversarial pass pointed out that they do not check what the name says:
    # a mutant with `eval=0` was still reported `survived=True` and printed
    # SURVIVED. The test passed while the property it is named for was false.
    assert row["survived"] is False, "a mutant that never ran has not survived"
    assert row["undetermined"] is True


def test_touched_marks_a_change_repr_cannot_see():
    """Shadowing a method leaves a dataclass `repr` identical.

    Without `touched()` the `zs-contains-always-true` mutant is inert on every
    world, its row reads `eval=0`, and `membership_agrees` is left unmeasured
    while the table still shows a line for it — an absence that looks like a
    measurement.
    """
    module, worlds = _zero_space_worlds()
    row = mutation.run_mutant(_mutant("zs-contains-always-true"), worlds, {})
    assert row["worlds_evaluated"] > 0, "the marker is not reaching the driver"


# -------------------------------------------------- the load-bearing pinning

def test_flip_law_value_is_killed_and_baseline_is_clean():
    module, worlds = _zero_space_worlds()

    dirty = mutation.baseline("zero_space", worlds)
    assert dirty == {}, (
        "these worlds violate an invariant with no mutant applied, so nothing "
        "measured on them is about the mutant: %s" % dirty)

    row = mutation.run_mutant(_mutant("zs-flip-law-value"), worlds, dirty)
    assert row["worlds_evaluated"] > 0
    killers = {name for name, n in row["killed"].items() if n}
    assert killers == {"laws_hold_on_trajectory"}, (
        "a value-only defect should be seen by the soundness invariant and by "
        "nothing else; got %s" % sorted(killers))
    assert row["worlds_to_first_kill"]["laws_hold_on_trajectory"] == 1


def test_kills_are_violations_and_not_crashes():
    """`raised` is detection in the weak sense and must not enter the headline.

    A battery whose kills are mostly exceptions is one refactor away from
    silence, and an exception carries no statement of *what* was wrong into the
    report. The driver keeps the columns apart; this pins that it does.
    """
    module, worlds = _zero_space_worlds()
    row = mutation.run_mutant(_mutant("zs-bump-difference-rank"), worlds, {})
    assert row["killed"]["rank_nullity"] > 0
    assert not any(row["raised_only"].values())


# ------------------------------------------------- the catalogue's own rules

@pytest.mark.parametrize("kwargs,missing", [
    ({"claim": "  "}, "claim"),
    ({"expect_kill": ()}, "expect_kill"),
])
def test_a_mutant_without_its_paperwork_is_refused(kwargs, missing):
    """Both fields are load-bearing, not documentation.

    Without `claim` a mutant can inject behaviour no engine ever promised, and
    a surviving one then reads as a weak invariant when the invariant is right.
    Without `expect_kill` written first, "the battery caught it" cannot be told
    apart from writing mutants until one trips something.
    """
    base = dict(
        id="test-paperwork", engine="zero_space", seam="_analyse",
        kind=mut.UNSOUND, claim="a real claim", description="d",
        corrupt=lambda r, a, k: r, expect_kill=("rank_nullity",))
    base.update(kwargs)
    with pytest.raises(ValueError, match=missing):
        mut.Mutant(**base)


def test_every_registered_mutant_names_a_real_invariant():
    """`expect_kill` must reference invariants that exist.

    A typo here silently becomes a `predicted_but_missed` row: the report would
    say the battery failed to catch something it was never asked about.
    """
    for mutant in mut.catalog():
        known = set(load(mutant.engine).INVARIANTS)
        unknown = [n for n in mutant.expect_kill if n not in known]
        assert not unknown, "%s expects unknown invariants %s (known: %s)" % (
            mutant.id, unknown, sorted(known))
