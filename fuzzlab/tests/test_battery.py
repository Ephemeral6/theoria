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
