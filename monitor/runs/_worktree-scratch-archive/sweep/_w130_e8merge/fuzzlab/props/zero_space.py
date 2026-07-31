"""`zero_space` — four invariants, judged by an independent GF(2) implementation.

`zero_space` ships its own `verify(result, states)`, and this module does not use
it. Verifying a null-space routine with the null-space routine's own checker
establishes that the module agrees with itself, which is not the question. So
every number here is recomputed in `fuzzlab/oracles/gf2.py` — a separate bitset
elimination written for this purpose — and compared.

What the engine claims, and what each invariant tests:

| invariant | claim under test |
|---|---|
| `laws_hold_on_trajectory` | **soundness.** Every law returned really does have constant parity along the trajectory, and equal to the `value` reported. |
| `law_space_is_complete` | **completeness.** The basis spans *exactly* the space of conserved laws — no law invented, none missed. |
| `rank_nullity` | the reported `difference_rank` and `dimension` are consistent with each other and with the true rank of the difference matrix. |
| `membership_agrees` | `contains()` answers correctly on vectors known (by the oracle) to be inside and outside the space. |

Soundness and completeness are separated deliberately. They fail differently and
they matter differently: an unsound law is a false statement about the world that
a manual could inherit, and an incomplete basis is a true statement the LLM never
gets offered. Only the first is a correctness bug; the second is a capability
gap. A single "does it match" property would report them as the same thing.

One coordinate convention, stated because getting it wrong would manufacture a
bug report: the oracle indexes features by the engine's own `Feature(cell,
color)` **objects**, not by position. Reading the engine's feature list is not
calling its algorithm — the two implementations have to share a coordinate
system to be comparable at all — but assuming its ordering would be an
unstated dependency, and a reordering upstream would then look like an
engine defect.
"""

from typing import Any, Dict, List, Sequence

from fuzzlab import rig  # noqa: F401  (path bootstrap)
from fuzzlab.oracles import gf2
from fuzzlab.props import finding

from engines import zero_space as engine  # noqa: E402

FAMILY = "parityworld"
ENGINE = "zero_space"

# Above this the exhaustive membership sweep stops being worth the wall clock;
# stated so the report can quote the number that produced its `skipped` count.
MEMBERSHIP_BUDGET = 14


def _index(features: Sequence[Any]) -> Dict[Any, int]:
    """`(cell, color) -> bit position`, read off the engine's own feature list."""
    return {(f.cell, f.color): i for i, f in enumerate(features)}


def _encode(state: Sequence[str], index: Dict[Any, int]) -> int:
    vector = 0
    for cell, color in enumerate(state):
        bit = index.get((cell, color))
        if bit is not None:
            vector |= 1 << bit
    return vector


def _analyse(world: Any):
    return engine.analyse(world.states, world.colors)


# --------------------------------------------------------------- invariants

def laws_hold_on_trajectory(world: Any) -> List[finding.Finding]:
    """Every returned law has constant parity along the trajectory, = `value`."""
    result = _analyse(world)
    index = _index(result.features)
    encoded = [_encode(s, index) for s in world.states]
    out: List[finding.Finding] = []
    for law in result.laws:
        values = [bin(law.vector & x).count("1") % 2 for x in encoded]
        if len(set(values)) > 1:
            first = next(i for i, v in enumerate(values) if v != values[0])
            out.append(finding.violated(
                ENGINE, "laws_hold_on_trajectory", world,
                "law %s changes parity at state %d (%d -> %d)"
                % (law.rendering(), first, values[0], values[first]),
                law=law.rendering(), scope=law.scope, at_state=first,
                support=[f.name() for f in law.support()]))
        elif values and values[0] != (law.value & 1):
            out.append(finding.violated(
                ENGINE, "laws_hold_on_trajectory", world,
                "law %s is constant at %d but reports value %d"
                % (law.rendering(), values[0], law.value),
                law=law.rendering(), scope=law.scope,
                observed=values[0], reported=law.value))
    return out


def law_space_is_complete(world: Any) -> List[finding.Finding]:
    """The basis spans exactly the conserved-law space the oracle computes.

    Both directions are reported separately. An engine that returns a strict
    subspace is *incomplete* — every law it did return is true, and it withheld
    some — which is a different fact about the engine than returning a vector
    that is not conserved at all.
    """
    result = _analyse(world)
    index = _index(result.features)
    n_cols = len(result.features)
    encoded = [_encode(s, index) for s in world.states]
    if not encoded:
        return [finding.skipped(ENGINE, "law_space_is_complete", world,
                                "world has no states", cause="no_states")]

    differences = [x ^ encoded[0] for x in encoded[1:]]
    expected = gf2.null_space(differences, n_cols)

    out: List[finding.Finding] = []
    for vector in result.basis:
        if not gf2.in_span(vector, expected, n_cols):
            out.append(finding.violated(
                ENGINE, "law_space_is_complete", world,
                "engine returned a basis vector that is not a conserved law "
                "(support %s)" % [i for i in range(n_cols) if vector >> i & 1],
                direction="unsound", n_features=n_cols))
            break
    for vector in expected:
        if not gf2.in_span(vector, result.basis, n_cols):
            out.append(finding.violated(
                ENGINE, "law_space_is_complete", world,
                "a conserved law is missing from the engine's basis: engine "
                "dimension %d, true dimension %d"
                % (len(result.basis), len(expected)),
                direction="incomplete", engine_dimension=len(result.basis),
                true_dimension=len(expected), n_features=n_cols))
            break
    return out


def rank_nullity(world: Any) -> List[finding.Finding]:
    """`dimension == n_features - difference_rank == len(basis)`, and the rank is right."""
    result = _analyse(world)
    index = _index(result.features)
    n_cols = len(result.features)
    encoded = [_encode(s, index) for s in world.states]
    differences = [x ^ encoded[0] for x in encoded[1:]]
    true_rank = len(gf2.row_echelon(differences, n_cols)[0])

    out: List[finding.Finding] = []
    if result.difference_rank != true_rank:
        out.append(finding.violated(
            ENGINE, "rank_nullity", world,
            "difference_rank is %d, the true rank of the difference matrix is %d"
            % (result.difference_rank, true_rank),
            reported=result.difference_rank, expected=true_rank))
    if result.dimension != n_cols - result.difference_rank:
        out.append(finding.violated(
            ENGINE, "rank_nullity", world,
            "dimension %d != n_features %d - difference_rank %d"
            % (result.dimension, n_cols, result.difference_rank),
            dimension=result.dimension, n_features=n_cols,
            difference_rank=result.difference_rank))
    if len(result.basis) != result.dimension:
        out.append(finding.violated(
            ENGINE, "rank_nullity", world,
            "basis has %d vectors but dimension reports %d"
            % (len(result.basis), result.dimension),
            basis=len(result.basis), dimension=result.dimension))
    return out


def membership_agrees(world: Any) -> List[finding.Finding]:
    """`contains()` is right on vectors the oracle knows are in and out.

    Skipped rather than sampled when the feature count is large: the sweep below
    enumerates combinations of the basis, and a partial sweep that reported a
    pass would be claiming coverage it did not have.
    """
    result = _analyse(world)
    n_cols = len(result.features)
    if n_cols > MEMBERSHIP_BUDGET * 4:
        return [finding.skipped(ENGINE, "membership_agrees", world,
                                "%d features exceeds the sweep budget" % n_cols,
                                cause="feature_sweep_over_budget",
                                n_features=n_cols)]
    out: List[finding.Finding] = []
    for vector in result.basis:
        if not result.contains(vector):
            out.append(finding.violated(
                ENGINE, "membership_agrees", world,
                "contains() is False for one of the engine's own basis vectors",
                direction="false_negative"))
            break

    # A vector outside the space, if one exists: any single feature not in the
    # span. `dimension == n_features` means the space is everything and there is
    # nothing outside to test, which is a legitimate world, not a skip.
    if len(result.basis) < n_cols:
        for i in range(n_cols):
            probe = 1 << i
            if not gf2.in_span(probe, result.basis, n_cols):
                if result.contains(probe):
                    out.append(finding.violated(
                        ENGINE, "membership_agrees", world,
                        "contains() is True for feature %d, which is outside "
                        "the span of the engine's own basis" % i,
                        direction="false_positive", feature=i))
                break
    return out


INVARIANTS = {
    "laws_hold_on_trajectory": laws_hold_on_trajectory,
    "law_space_is_complete": law_space_is_complete,
    "rank_nullity": rank_nullity,
    "membership_agrees": membership_agrees,
}


def check(world: Any) -> List[finding.Finding]:
    return finding.run_invariants(ENGINE, world, INVARIANTS)
