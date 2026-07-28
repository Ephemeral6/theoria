"""Two builds of the same spec produce the same bytes.

Determinism is the property that makes a shipped artefact reviewable: a world
whose trace or ground truth moves between runs turns every future diff into
noise and hides the real change.  The usual culprit is a `set` or a dict
iteration order reaching an output, which is why `GridWorld` orders mechanisms by
`(priority, name)`, keeps entities in spec order, and sorts the reachable set by
`State.key()`.

This is the in-process half of the check.  `worldgen.build.check_determinism`
does the other half — a rebuild in a *fresh interpreter* at a different
`PYTHONHASHSEED`, which is the only way to catch hash-order leakage — and it is
not repeated here because spawning twenty subprocess builds would dominate the
suite's runtime for a strictly weaker version of a gate the build already runs.

The trace half runs on a **ten-world subset**, one per family and both gravity
worlds included: `explorer.explore` measures the exhaustive walk before it
truncates, and that walk costs ten seconds on `t3-full-house` alone.  The ground
truth half is cheap and sweeps all twenty.
"""

import json

import pytest

from worldgen.core import explorer, trace, truth
from worldgen.core.world import GridWorld
from worldgen.generate import BY_ID
from worldgen.tests import support

# One world per mechanism family plus both variant styles, chosen for a cheap
# exhaustive walk; `t3-full-house`'s walk alone is ~10 s and buys nothing here
# that a small world with the same three families does not.
TRACE_SAMPLE = (
    "t1-walk-maze",          # no mechanism at all
    "t1-push-open",          # push
    "t1-switch-toggle",      # switch_door
    "t1-cycler-gate",        # color_cycle
    "t1-tokens-lock",        # count_lock
    "t1-fragile-bridge",     # consumable
    "t2-portal-pair",        # portal, twoway
    "t2-portal-paired",      # portal, paired
    "t2-gravity-push",       # gravity + push
    "t2-unsolvable-nodoor",  # the unsolvable certificate
)


def _trace_bytes(world_id: str) -> str:
    grid = GridWorld(BY_ID[world_id])
    states, actions = explorer.explore(grid)
    return "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
                   for row in trace.rows(grid, states, actions))


@pytest.mark.parametrize("world_id", TRACE_SAMPLE)
def test_trace_is_identical_across_two_builds(world_id):
    assert _trace_bytes(world_id) == _trace_bytes(world_id)


@pytest.mark.parametrize("world_id", support.WORLD_IDS)
def test_ground_truth_json_is_identical_across_two_builds(world_id):
    def once() -> str:
        blob = truth.ground_truth(GridWorld(BY_ID[world_id]), diagnose=True)
        return json.dumps(blob, indent=2, sort_keys=True) + "\n"

    assert once() == once()
