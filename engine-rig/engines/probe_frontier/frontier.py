"""probe_frontier -- pick the action that splits the hypothesis frontier hardest.

Under determinism this is a computation, not an estimate.  Each surviving
hypothesis predicts exactly one observation for a candidate action; the action
partitions the frontier into classes that agree; the entropy of that partition is
how many bits the observation is worth.  Greedy argmax over candidate actions.

Nothing here is bandit-shaped: there is no noise to average out, no exploration
bonus, no regret.  An action that splits the frontier in half removes exactly one
bit of uncertainty, and an action every hypothesis agrees on removes none --
which is why a rule with a single witness is the thing to probe, and why probing
where the theory is confident is worthless.
"""

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Hashable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class Hypothesis:
    """One surviving explanation, able to predict an observation for any action."""

    id: str
    predict: Callable[[Any, Any], Hashable]
    weight: float = 1.0
    description: str = ""


@dataclass
class ProbeValue:
    action: Any
    partition: Dict[Hashable, List[str]]
    entropy: float
    cost: float

    @property
    def n_classes(self) -> int:
        return len(self.partition)

    @property
    def value(self) -> float:
        """Bits per unit of path cost -- reaching a state is itself a plan."""
        return self.entropy / self.cost if self.cost else float("inf")

    @property
    def splits(self) -> bool:
        return self.n_classes > 1

    def as_json(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "entropy_bits": round(self.entropy, 12),
            "cost": self.cost,
            "value_bits_per_cost": round(self.value, 12),
            "n_classes": self.n_classes,
            "partition": {
                str(observation): sorted(ids)
                for observation, ids in sorted(
                    self.partition.items(), key=lambda kv: str(kv[0])
                )
            },
        }


def entropy_of(weights: Sequence[float]) -> float:
    """Shannon entropy in bits of a partition given by class weights."""
    total = float(sum(weights))
    if total <= 0:
        return 0.0
    out = 0.0
    for weight in weights:
        if weight <= 0:
            continue
        share = weight / total
        out -= share * math.log2(share)
    return out


def partition_for(hypotheses: Sequence[Hypothesis], state: Any, action: Any
                  ) -> Dict[Hashable, List[str]]:
    partition: Dict[Hashable, List[str]] = {}
    for hypothesis in hypotheses:
        observation = hypothesis.predict(state, action)
        partition.setdefault(observation, []).append(hypothesis.id)
    return partition


def probe_value(hypotheses: Sequence[Hypothesis], state: Any, action: Any,
                cost: float = 1.0) -> ProbeValue:
    partition = partition_for(hypotheses, state, action)
    weights_by_id = {h.id: h.weight for h in hypotheses}
    class_weights = [
        sum(weights_by_id[i] for i in ids) for ids in partition.values()
    ]
    return ProbeValue(
        action=action,
        partition=partition,
        entropy=entropy_of(class_weights),
        cost=cost,
    )


def rank_probes(hypotheses: Sequence[Hypothesis], state: Any,
                actions: Sequence[Any],
                costs: Optional[Dict[Any, float]] = None) -> List[ProbeValue]:
    """Every candidate action, best splitter first.

    Ordering is total and deterministic: most bits per unit cost, then most bits,
    then cheapest, then the action's own name -- so a tie never depends on
    dictionary order.
    """
    costs = costs or {}
    values = [
        probe_value(hypotheses, state, action, cost=costs.get(action, 1.0))
        for action in actions
    ]
    values.sort(key=lambda v: (-v.value, -v.entropy, v.cost, str(v.action)))
    return values


def best_probe(hypotheses: Sequence[Hypothesis], state: Any,
               actions: Sequence[Any],
               costs: Optional[Dict[Any, float]] = None) -> Optional[ProbeValue]:
    """The most discriminating action, or None if no action separates anything."""
    ranked = rank_probes(hypotheses, state, actions, costs=costs)
    if not ranked or not ranked[0].splits:
        return None
    return ranked[0]


def surviving(hypotheses: Sequence[Hypothesis], state: Any, action: Any,
              observation: Hashable) -> List[Hypothesis]:
    """The hypotheses still standing after the probe returns `observation`."""
    return [h for h in hypotheses if h.predict(state, action) == observation]
