"""`probe_frontier` — four invariants against a brute-force recomputation.

`hypset` worlds carry an explicit observation table — hypothesis × action ->
observation — so every quantity this engine computes can be recomputed directly
from the world rather than inferred. That makes the comparison exact instead of
approximate, which matters for entropy: a tolerance wide enough to absorb a
different summation order is also wide enough to hide a wrong partition.

Three details of the engine's definition, each of which manufactures a
confident false bug report if the oracle gets it wrong. The third one did:

* the engine's `entropy_of` is **bits** (`math.log2`), and so is the oracle's
  `partition_entropy`;
* `ProbeValue.value` is `entropy / cost`, *not* entropy. The ranking is by
  `value` first. A property that recomputed entropy and compared it against
  `value` would fire on every world with a non-unit cost;
* the entropy is over **summed `Hypothesis.weight` per class**, not over class
  *sizes*. `hypset` draws non-uniform weights, so the first version of this
  module — which counted hypotheses — reported 120 violations across 60 worlds
  against an engine that was right every time. The engine's own line is
  `class_weights = [sum(weights_by_id[i] for i in ids) for ids in
  partition.values()]`, and the oracle now sums the same weights from the
  world's own hypothesis list. Left recorded here rather than quietly fixed:
  a fuzz battery's most likely output is a false accusation, and the only
  defence is checking the oracle before filing.

| invariant | claim under test |
|---|---|
| `partition_matches_truth` | the partition an action induces is exactly the grouping of hypotheses by predicted observation |
| `entropy_matches_bruteforce` | the reported entropy is the Shannon entropy in bits of that partition's block sizes |
| `ranking_is_sound` | `rank_probes` returns every action exactly once, ordered by the total order its docstring states |
| `splits_flag_is_honest` | `splits` is true exactly when the action actually separates at least two hypotheses |
"""

from typing import Any, Dict, List, Sequence

from fuzzlab import rig  # noqa: F401  (path bootstrap)
from fuzzlab.oracles import search
from fuzzlab.props import finding

from engines import probe_frontier as engine  # noqa: E402

FAMILY = "hypset"
ENGINE = "probe_frontier"

# Entropies are compared exactly up to floating-point summation noise.  This is
# a float-equality tolerance, not a "close enough" band: any real disagreement
# is a whole block moving and is orders of magnitude larger.
EPS = 1e-9


def _truth_partition(world: Any, action: str) -> Dict[Any, List[str]]:
    """The grouping the world's own observation table dictates.

    Read off `world.predictions()` — a plain `{(hypothesis_id, action):
    observation}` dict — and not off the `Hypothesis` objects the world hands the
    engine. Those objects carry `predict` callables, and calling them to build
    the expected answer would be asking the input to grade the output.
    """
    table = world.predictions()
    out: Dict[Any, List[str]] = {}
    for hid in world.spec_json()["hypothesis_ids"]:
        out.setdefault(table[(hid, action)], []).append(hid)
    return out


def _class_weights(world: Any, blocks: Dict[Any, List[str]]) -> List[float]:
    """Summed hypothesis weight per class — the quantity the engine takes entropy of.

    Not class *sizes*. See the module docstring: `hypset` draws non-uniform
    weights and counting instead of weighting is what produced this module's one
    false accusation.
    """
    weights = {h.id: h.weight for h in world.hypotheses()}
    return [sum(weights[i] for i in ids) for ids in blocks.values()]


# --------------------------------------------------------------- invariants

def partition_matches_truth(world: Any) -> List[finding.Finding]:
    """The engine's partition is the world's own grouping by predicted observation."""
    hypotheses = world.hypotheses()
    costs = world.cost_map()
    out: List[finding.Finding] = []
    for action in world.actions:
        got = engine.partition_for(hypotheses, world.state, action)
        want = _truth_partition(world, action)
        normalised = {k: sorted(v) for k, v in got.items()}
        expected = {k: sorted(v) for k, v in want.items()}
        if normalised != expected:
            out.append(finding.violated(
                ENGINE, "partition_matches_truth", world,
                "action %r partitions as %s, the observation table says %s"
                % (action, normalised, expected),
                # `engine=` here collided with `finding.violated`'s own first
                # parameter, so the only path that reports this invariant raised
                # TypeError instead of returning a finding -- for as long as the
                # invariant has existed. It never showed up because the engine
                # never partitioned wrongly, so the line never ran. Renamed, and
                # `test_battery.py` now refuses the collision by parsing.
                action=action, engine_partition=normalised, truth=expected))
    return out


def entropy_matches_bruteforce(world: Any) -> List[finding.Finding]:
    """Reported entropy equals the block-size entropy of the true partition, in bits."""
    hypotheses = world.hypotheses()
    costs = world.cost_map()
    out: List[finding.Finding] = []
    for value in engine.rank_probes(hypotheses, world.state, world.actions, costs):
        blocks = _truth_partition(world, value.action)
        weights = _class_weights(world, blocks)
        expected = search.partition_entropy(weights)
        if abs(value.entropy - expected) > EPS:
            out.append(finding.violated(
                ENGINE, "entropy_matches_bruteforce", world,
                "action %r reports %.12f bits, brute force says %.12f"
                % (value.action, value.entropy, expected),
                action=value.action, reported=value.entropy, expected=expected,
                class_weights=sorted(weights)))
    return out


def ranking_is_sound(world: Any) -> List[finding.Finding]:
    """Every action ranked exactly once, in the total order the docstring states.

    The order is `(-value, -entropy, cost, str(action))`. Checking the stated
    order rather than merely "descending by something" is the point: a ranking
    that is *nearly* sorted still hands the caller the wrong probe first, and
    that is the engine's entire output.
    """
    hypotheses = world.hypotheses()
    costs = world.cost_map()
    ranked = engine.rank_probes(hypotheses, world.state, world.actions, costs)
    out: List[finding.Finding] = []

    got = sorted(str(v.action) for v in ranked)
    want = sorted(str(a) for a in world.actions)
    if got != want:
        out.append(finding.violated(
            ENGINE, "ranking_is_sound", world,
            "rank_probes returned %d entries for %d actions (%s vs %s)"
            % (len(ranked), len(world.actions), got, want),
            returned=got, actions=want))
        return out

    keys = [(-v.value, -v.entropy, v.cost, str(v.action)) for v in ranked]
    if keys != sorted(keys):
        first = next(i for i in range(1, len(keys)) if keys[i] < keys[i - 1])
        out.append(finding.violated(
            ENGINE, "ranking_is_sound", world,
            "ranking is out of order at position %d: %r then %r"
            % (first, ranked[first - 1].action, ranked[first].action),
            at=first, keys=[list(map(str, k)) for k in keys]))
    return out


def splits_flag_is_honest(world: Any) -> List[finding.Finding]:
    """`splits` is true exactly when the action really separates two hypotheses."""
    hypotheses = world.hypotheses()
    costs = world.cost_map()
    out: List[finding.Finding] = []
    for value in engine.rank_probes(hypotheses, world.state, world.actions, costs):
        blocks = _truth_partition(world, value.action)
        really = len(blocks) > 1
        if value.splits != really:
            out.append(finding.violated(
                ENGINE, "splits_flag_is_honest", world,
                "action %r reports splits=%s but induces %d observation class(es)"
                % (value.action, value.splits, len(blocks)),
                action=value.action, reported=value.splits,
                n_classes=len(blocks)))
    return out


INVARIANTS = {
    "partition_matches_truth": partition_matches_truth,
    "entropy_matches_bruteforce": entropy_matches_bruteforce,
    "ranking_is_sound": ranking_is_sound,
    "splits_flag_is_honest": splits_flag_is_honest,
}


def check(world: Any) -> List[finding.Finding]:
    return finding.run_invariants(ENGINE, world, INVARIANTS)
