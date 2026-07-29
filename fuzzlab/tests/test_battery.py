"""The battery as a test: a short campaign per engine, plus the seed-table contract.

`props/__init__.py` splits the two front ends on purpose — the campaign needs
findings it can count and rank, pytest needs assertions, and neither should be
reimplemented in terms of the other. So this module runs the *same* `check()`
functions on a small, fixed number of worlds and asserts the result, which makes
a regression fail the suite rather than only lowering a number in a report.

The world count is deliberately small. The standing 500-world campaign is
`python -m fuzzlab.campaign`; this is the gate that has to stay fast enough that
people run it.
"""

import json
import subprocess
import sys

import pytest

from fuzzlab import campaign, prng
from fuzzlab.props import ENGINES, finding, load
from fuzzlab.worlds import FAMILIES, GENERATORS

WORLDS = 25
SEED = campaign.DEFAULT_SEED


@pytest.mark.parametrize("engine", ENGINES)
def test_engine_has_at_least_three_invariants(engine):
    """The item's floor. Three per engine is the specification, not a target."""
    module = load(engine)
    assert len(module.INVARIANTS) >= 3, sorted(module.INVARIANTS)
    assert module.FAMILY in FAMILIES


@pytest.mark.parametrize("engine", ENGINES)
def test_short_campaign_finds_no_violation(engine):
    result = campaign.run_engine(engine, SEED, WORLDS, quiet=True)
    violations = [f for f in result["findings"] if f.kind == finding.VIOLATED]
    assert not violations, "\n".join(str(v) for v in violations[:5])
    assert result["report"]["worlds_checked"] == WORLDS
    assert not result["report"]["generator_errors"]


@pytest.mark.parametrize("engine", ENGINES)
def test_short_campaign_passes_the_gate_the_docstring_describes(engine):
    """`finding.failures()` wired up, which until V-21 it never was.

    It had **zero callers** — a function whose docstring claimed "violations and
    unexpected raises" and whose body returned violations, imported by nobody, so
    the discrepancy could not be observed from any test. Widening the body fixes
    the sentence; calling it is what makes the sentence load-bearing.

    This is strictly stronger than the test above: a property that *crashes* has
    established nothing, and `test_finding_contract.py` records an incident where
    a dead reporting path turned every violation into a `raised` while the
    headline "0 violations" stayed true. That headline would not survive this.
    """
    result = campaign.run_engine(engine, SEED, WORLDS, quiet=True)
    bad = finding.failures(result["findings"])
    assert not bad, "\n".join(str(f) for f in bad[:5])


@pytest.mark.parametrize("engine", ENGINES)
def test_nothing_went_unjudged_because_a_tool_could_not_compute(engine):
    """A clean tree must have zero `unavailable`, and this is where it is gated.

    The answer to "did you just move the problem into another bucket". Filing
    `LpUnavailable` as `skipped` is only honest if somebody reads the skips, and
    a number in an artifact that nothing asserts on is a number nobody reads. So
    the `unavailable` class — a tool did not compute, nobody knows the answer —
    is required to be empty here.

    **Pre-registered as able to fail for a non-defect.** If HiGHS hits numerical
    difficulties on some future world, this goes red and no engine change will
    clear it. That is intended: the run did not measure what it claims to have
    measured, and the correct response is to look at the toolchain, not to relax
    the assertion. It is deliberately *not* a `violated` — the engine is accused
    of nothing — which is why it is a separate test with its own message.

    `declined` and `budget` skips are untouched by this: the engine correctly
    having nothing to say, and this battery declining to pay for a sweep, are
    both expected to be non-zero and neither is a gap in what was measured.
    """
    result = campaign.run_engine(engine, SEED, WORLDS, quiet=True)
    report = result["report"]
    unavailable = report["invariant_worlds_unavailable"]
    assert not any(unavailable.values()), (
        "%s: %r world(s) went unjudged because a tool could not compute -- "
        "%s. The coverage this run reports was not earned."
        % (engine, {k: v for k, v in unavailable.items() if v},
           [str(f) for f in result["findings"]
            if f.kind == finding.SKIPPED
            and f.cause_class == finding.UNAVAILABLE][:3]))
    assert report["unavailable"] == 0


@pytest.mark.parametrize("engine", ENGINES)
def test_the_skip_breakdown_reconciles_with_the_skip_count(engine):
    """`skips_by_cause` must account for every skip, not most of them.

    Without this the breakdown could drift from the total and the `unavailable`
    row could read 0 because a cause stopped being counted rather than because
    nothing was unavailable — which is the same silence one level up.

    The first version of this test had a second assertion,
    `sum(row.values()) == WORLDS - invariant_worlds_evaluated[name]`, which an
    adversarial pass showed was `x == x`: `invariant_worlds_evaluated` was
    *defined* as `WORLDS - skip_count`, so both sides were the same count
    re-derived from the same findings. It passed on a report whose coverage
    column read **−56**. What replaces it below compares the two against each
    other only where they are genuinely computed differently — findings against
    distinct seeds.
    """
    result = campaign.run_engine(engine, SEED, WORLDS, quiet=True)
    report = result["report"]

    # `report["skipped"]` comes from a separate Counter pass in `run_engine`, so
    # this one is a real cross-check of the breakdown against the total.
    by_cause = sum(n for row in report["skips_by_cause"].values()
                   for n in row.values())
    by_class = sum(n for row in report["skips_by_cause_class"].values()
                   for n in row.values())
    assert by_cause == report["skipped"] == by_class

    # Findings and worlds are different quantities and the artifact publishes
    # both. A world column may never exceed the world count, and may never
    # exceed the finding count for the same slice.
    for name in report["invariants"]:
        worlds_skipped = report["invariant_worlds_skipped"][name]
        findings_skipped = sum(report["skips_by_cause"].get(name, {}).values())
        assert 0 <= worlds_skipped <= WORLDS, (name, worlds_skipped)
        assert worlds_skipped <= findings_skipped, (
            "%s: %d worlds skipped from %d skip findings -- a world cannot be "
            "skipped more times than it was reported"
            % (name, worlds_skipped, findings_skipped))
        assert (report["invariant_worlds_evaluated"][name]
                == WORLDS - worlds_skipped)
        assert 0 <= report["invariant_worlds_evaluated"][name] <= WORLDS
        assert (report["invariant_worlds_unavailable"][name]
                <= worlds_skipped)


def test_many_skips_on_one_world_do_not_send_the_coverage_column_negative():
    """The BLOCKER an adversarial pass found, kept as a regression.

    `invariant_worlds_evaluated` used to subtract the skip **finding** count from
    the world count, and the two are equal only if no property ever files two
    skips for one world. `cegis_miner.frontier_is_complete_to_size` files one per
    rule inside a loop; forcing its budget low enough to fire produced
    `invariant_worlds_evaluated: -56` over 12 worlds — and the reconciliation
    test of the day passed on that report, because its second assertion was
    `x == x`.

    Eight skips per world per invariant, driven through the real
    `campaign.run_engine`, is the same shape without needing to bend a budget.
    Both world columns must stay inside `[0, WORLDS]` and the finding columns
    must show the eight.
    """
    from fuzzlab.props import load

    module = load("zero_space")
    original = module.check
    names = sorted(module.INVARIANTS)

    def eight_skips(world):
        return [finding.skipped("zero_space", names[0], world,
                                "synthetic multi-skip", cause="no_states")
                for _ in range(8)]

    module.check = eight_skips
    try:
        result = campaign.run_engine("zero_space", SEED, WORLDS, quiet=True)
    finally:
        module.check = original

    report = result["report"]
    assert report["skipped"] == 8 * WORLDS
    assert report["skips_by_cause"][names[0]] == {"no_states": 8 * WORLDS}
    # ...and the world columns count worlds.
    assert report["invariant_worlds_skipped"][names[0]] == WORLDS
    assert report["invariant_worlds_evaluated"][names[0]] == 0
    for name in names:
        assert 0 <= report["invariant_worlds_evaluated"][name] <= WORLDS, (
            "%s: %d, outside [0, %d] -- the column is counting findings again"
            % (name, report["invariant_worlds_evaluated"][name], WORLDS))
        assert 0 <= report["invariant_worlds_unavailable"][name] <= WORLDS


# ------------------------------------------------------------- the seed table

@pytest.mark.parametrize("family", FAMILIES)
def test_worlds_are_pure_functions_of_their_seed(family):
    """Two generations from one seed are the same world, fingerprint included."""
    generate = GENERATORS[family]
    for index in (0, 7, 41):
        seed = prng.derive(SEED, family, index)
        a, b = generate(seed), generate(seed)
        assert a.fingerprint() == b.fingerprint()
        assert a.spec_json() == b.spec_json()


@pytest.mark.parametrize("family", FAMILIES)
def test_distinct_indices_give_distinct_worlds(family):
    """Not a tautology: a generator that ignored its seed would pass everything else."""
    generate = GENERATORS[family]
    prints = {generate(prng.derive(SEED, family, i)).fingerprint() for i in range(40)}
    assert len(prints) >= 30, "%d distinct worlds in 40 draws" % len(prints)


def test_seeds_are_independent_across_families():
    """World `i` of one family and world `i` of another share a campaign seed only."""
    for index in range(20):
        values = {prng.derive(SEED, family, index) for family in FAMILIES}
        assert len(values) == len(FAMILIES)


def test_the_campaign_is_reproducible_across_interpreters(tmp_path):
    """Same seed, fresh process, different PYTHONHASHSEED -> identical seed table.

    Run out of process because that is the only way to vary `PYTHONHASHSEED`, and
    a determinism check that shares an interpreter with the thing it is checking
    cannot see hash-order nondeterminism at all.
    """
    import os

    rows = []
    for hashseed in ("1", "271828"):
        out = tmp_path / hashseed
        env = dict(os.environ, PYTHONHASHSEED=hashseed)
        proc = subprocess.run(
            [sys.executable, "-m", "fuzzlab.campaign", "--engine", "zero_space",
             "--worlds", "20", "--out", str(out), "--quiet"],
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))),
            env=env, capture_output=True,
        )
        assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")[-2000:]
        rows.append((out / "seeds.jsonl").read_bytes())
    assert rows[0] == rows[1]


# --------------------------------------------------------------- minimisation

def test_replay_reproduces_the_world_a_seed_names():
    """The seed table's whole promise: a row replays to the world it describes."""
    from fuzzlab import minimize

    family = "parityworld"
    seed = prng.derive(SEED, family, 3)
    world = GENERATORS[family](seed)
    replayed = minimize.replay(family, seed, "zero_space")
    assert replayed["fingerprint"] == world.fingerprint()
    assert replayed["spec"] == world.spec_json()


@pytest.mark.parametrize("family", FAMILIES)
def test_size_metric_is_defined_for_every_family(family):
    """A family whose size is undefined would silently rank last forever."""
    from fuzzlab import minimize

    world = GENERATORS[family](prng.derive(SEED, family, 1))
    assert minimize.size_of(world) > 0


# ------------------------------------------- coverage has to mean something

def test_a_dead_lp_potential_shows_up_as_lost_coverage():
    """Disable the engine entirely; the battery must report less coverage, not the same.

    The experiment is E-11's and it is the sharpest statement of what
    `props/lp_potential.py`'s four bare `return []` openers were costing.
    Every invariant in that module is conditional on a certificate existing, so
    replacing `run` with `return None, None` — the engine deleted — used to
    produce **byte-identical findings** and an unchanged
    `invariant_worlds_evaluated: 500` for all four. A battery that cannot
    distinguish a working engine from an absent one is not measuring the engine,
    and the campaign's coverage column was the only place that could have said
    so.

    This test is the regression, and it is written to *fail* against the code as
    it stood before V-13: it asserts that the dead engine is visible as a drop in
    evaluated worlds, which is exactly what the `finding.skipped` calls buy.
    """
    import fuzzlab.props.lp_potential as props

    live = campaign.run_engine("lp_potential", SEED, WORLDS, quiet=True)

    original = props._solve
    props._solve = lambda world: (None, None)
    try:
        dead = campaign.run_engine("lp_potential", SEED, WORLDS, quiet=True)
    finally:
        props._solve = original

    live_evaluated = live["report"]["invariant_worlds_evaluated"]
    dead_evaluated = dead["report"]["invariant_worlds_evaluated"]

    for name in sorted(props.INVARIANTS):
        assert dead_evaluated[name] == 0, (
            "%s still reports %d worlds evaluated with the engine disabled; a "
            "world nothing was checked on must be `skipped`, not an empty list"
            % (name, dead_evaluated[name]))
        assert live_evaluated[name] > dead_evaluated[name], (
            "%s reports the same coverage whether the engine runs or not" % name)

    # And the live run must not be claiming the full world count either: the
    # certificate-less worlds are real and they are not judged.
    assert any(live_evaluated[name] < WORLDS for name in props.INVARIANTS), (
        "every invariant claims all %d worlds; the certificate-less ones are "
        "being counted as evaluated again" % WORLDS)
