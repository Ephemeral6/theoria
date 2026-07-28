"""Structural properties that must hold for every world in the catalogue.

These are the claims the rest of the library is entitled to assume, and each of
them has already been false once:

* the state vector's shape was checked only inside `GridWorld.__init__`, so a
  mechanism whose `n_vars` and `initial_vars` disagreed failed at world-build
  time with a message about slices rather than about itself;
* **the frame determines the state** is the load-bearing one.  A reader of a
  world gets frames and nothing else, so two reachable states that render alike
  make the world unlearnable from its own trace — and the failure would surface
  as a *miner* reporting that no guard separates two transitions, which is the
  wrong place to look.  `consumable` renders ARMED identically to INTACT and
  defends it with "the agent is standing on it", an argument that held only
  while `interact` was the sole route onto a tile;
* `rule_correspondence` exists because 12 of 20 worlds once shipped declaring
  rules that never fire, and one of those dormant rules (`teleport_twoway`) was
  a live defect wearing an `unreachable` label;
* `intended_solvable` exists because the first cut of this catalogue had the
  label inverted: `t2-unsolvable-nodoor`, whose whole purpose is to ship an
  unsolvability certificate, was winnable in five steps.

The whole catalogue is swept rather than sampled: `support` caches the reachable
set per world, and the full sweep costs well under a second even including
`t3-full-house`'s 2654 states.
"""

import pytest

from worldgen.core import reversibility as rev, solvability, truth
from worldgen.generate import BY_ID
from worldgen.tests import support

ALL = support.WORLD_IDS


@pytest.mark.parametrize("world_id", ALL)
def test_state_vector_shape_matches_declaration(world_id):
    """Every bound mechanism's `n_vars` agrees with its own `initial_vars`."""
    grid = support.world(world_id)
    for mechanism in grid.mechanisms:
        mine = grid.mine(mechanism)
        declared = mechanism.n_vars(grid.spec, mine)
        initial = mechanism.initial_vars(grid.spec, mine)
        assert declared == len(initial), (
            "%s/%s: n_vars says %d, initial_vars has %d entries"
            % (world_id, mechanism.name, declared, len(initial)))
    assert sum(length for _base, length in grid.slices.values()) \
        == len(grid.initial().vars)


@pytest.mark.parametrize("world_id", ALL)
def test_frame_determines_state(world_id):
    """`render` is injective over the reachable set — no two states look alike."""
    report = truth.frame_determines_state(support.world(world_id),
                                          support.reachable(world_id))
    assert report["injective"], (
        "%s: %d reachable states render to %d distinct frames; collisions %r"
        % (world_id, report["states"], report["distinct_frames"],
           report["collisions"]))


@pytest.mark.parametrize("world_id", ALL)
def test_settle_converges_on_every_reachable_state(world_id):
    """No reachable state trips SETTLE_LIMIT.

    Asserted in the stronger fixpoint form: a state a reader can observe came out
    of `step`, which settles, so settling it again must be the identity.  A world
    that fails this either does not converge (`RuntimeError`) or ships states
    that are still mid-cascade.
    """
    grid = support.world(world_id)
    for state in support.reachable(world_id):
        assert grid.settle(state) == state, "%s: %r is not a settle fixpoint" % (
            world_id, state.key())


@pytest.mark.parametrize("world_id", ALL)
def test_rule_table_matches_the_world(world_id):
    """Every declared primary rule fires, and every fired tag is declared."""
    corr = truth.rule_correspondence(support.world(world_id))
    assert corr["agrees"], (
        "%s: declared_never_fires=%r fired_undeclared=%r declared_duplicates=%r"
        % (world_id, corr["declared_never_fires"], corr["fired_undeclared"],
           corr["declared_duplicates"]))


@pytest.mark.parametrize("world_id", ALL)
def test_no_reversibility_claim_disagreements(world_id):
    """No mechanism's re-witnessability claim contradicts the measured stamp."""
    grid = support.world(world_id)
    stamp = rev.audit(grid, truth.rule_table(grid))
    assert stamp["claim_disagreements"] == [], (
        "%s: %s" % (world_id, stamp["claim_disagreements"]))


@pytest.mark.parametrize("world_id", ALL)
def test_measured_solvability_matches_intent(world_id):
    spec = BY_ID[world_id]
    if spec.intended_solvable is None:
        pytest.skip("%s makes no solvability claim" % world_id)
    measured = solvability.solve(support.world(world_id)) is not None
    assert measured == spec.intended_solvable, (
        "%s: intended_solvable=%r but the exhaustive search says %r"
        % (world_id, spec.intended_solvable, measured))


def test_exactly_one_world_is_unsolvable():
    """The catalogue ships one unsolvability certificate, and knows which world."""
    unsolvable = sorted(wid for wid in ALL
                        if solvability.solve(support.world(wid)) is None)
    assert unsolvable == ["t2-unsolvable-nodoor"]
