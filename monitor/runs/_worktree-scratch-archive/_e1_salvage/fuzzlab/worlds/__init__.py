"""Parametric random worlds.

Five families, one generator each, all pure functions of a 64-bit seed:

| family        | `generate(seed)` returns | feeds                          |
|---------------|--------------------------|--------------------------------|
| `gridworld`   | frames + actions + truth | mdl_segmenter, cegis_miner     |
| `parityworld` | coloured cell states     | zero_space                     |
| `jumpgraph`   | a peg-jump state graph   | lp_potential                   |
| `blockworld`  | STRIPS PDDL text         | fd_adapter                     |
| `hypset`      | hypotheses + actions     | probe_frontier                 |

Every world carries `spec` (the drawn parameters, JSON-serialisable) and
`fingerprint()` (a sha256 over the canonical form).  The seed table records both,
so a replay that regenerates a different world is caught by the fingerprint
rather than by a property mysteriously flipping.
"""

from fuzzlab.worlds import blockworld, gridworld, hypset, jumpgraph, parityworld  # noqa: F401

FAMILIES = ("gridworld", "parityworld", "jumpgraph", "blockworld", "hypset")

GENERATORS = {
    "gridworld": gridworld.generate,
    "parityworld": parityworld.generate,
    "jumpgraph": jumpgraph.generate,
    "blockworld": blockworld.generate,
    "hypset": hypset.generate,
}
