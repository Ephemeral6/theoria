"""Random hypothesis frontiers -- the fuzz input for `probe_frontier`.

`probe_frontier`'s core is combinatorial and world-agnostic: it takes hypotheses
that each predict one observation per action, partitions them, and scores the
partition's entropy per unit cost.  Nothing about that needs a grid, so the
generator hands it the general object -- a prediction *table* -- rather than a
grid world that would only reach a thin slice of the table space.

Flavours exist so the interesting corners are hit on purpose rather than waited
for:

* `random`     -- an arbitrary table.
* `agreeing`   -- every hypothesis predicts the same thing everywhere; the honest
                  answer is "no experiment here is worth anything" and
                  `best_probe` must say so.
* `singleton`  -- one hypothesis, so every partition is a single class.
* `splitting`  -- at least one action splits the frontier into `k` classes with a
                  known entropy, computed by hand from the table.

Costs are drawn to include the awkward values as well as the ordinary ones:
fractional costs, large costs, and **zero**.  Zero is not a hypothetical -- the
ranking divides by it -- so it is generated deliberately and its consequences
recorded rather than being kept out of the sample.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple

from fuzzlab.prng import Rng
from fuzzlab.worlds.common import World

OBSERVATIONS = ("fires", "silent", "bounces", "vanishes")
ACTION_NAMES = ("UP", "DOWN", "LEFT", "RIGHT", "WAIT", "POKE", "PULL", "SHOVE")


@dataclass(frozen=True)
class HypSpec:
    seed: int
    flavour: str
    hypothesis_ids: Tuple[str, ...]
    actions: Tuple[str, ...]
    observations: Tuple[str, ...]
    table: Tuple[Tuple[str, ...], ...]        # table[h][a]
    weights: Tuple[float, ...]
    costs: Tuple[float, ...]
    state_token: str

    def json(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "flavour": self.flavour,
            "hypothesis_ids": list(self.hypothesis_ids),
            "actions": list(self.actions),
            "observations": list(self.observations),
            "table": [list(row) for row in self.table],
            "weights": list(self.weights),
            "costs": list(self.costs),
            "state_token": self.state_token,
        }


@dataclass
class HypWorld(World):
    spec: HypSpec

    family = "hypset"

    @property
    def seed(self) -> int:
        return self.spec.seed

    def spec_json(self) -> Dict[str, Any]:
        return self.spec.json()

    # ------------------------------------------------------- engine-facing form

    def predictions(self) -> Dict[Tuple[str, str], str]:
        """{(hypothesis id, action): observation} -- the ground truth table."""
        out = {}
        for i, hid in enumerate(self.spec.hypothesis_ids):
            for j, action in enumerate(self.spec.actions):
                out[(hid, action)] = self.spec.table[i][j]
        return out

    def hypotheses(self) -> List[Any]:
        """`probe_frontier.Hypothesis` objects backed by the table.

        Built here rather than in the property module so that every property
        sees the same objects, and so that the closure over `row` is captured
        correctly per hypothesis -- the classic late-binding trap, and one that
        would make every entropy come out wrong in the same direction.
        """
        from engines.probe_frontier import Hypothesis

        actions = self.spec.actions
        out = []
        for i, hid in enumerate(self.spec.hypothesis_ids):
            row = self.spec.table[i]
            lookup = {action: row[j] for j, action in enumerate(actions)}

            def predict(state, action, lookup=lookup):
                return lookup.get(action, "unknown")

            out.append(
                Hypothesis(
                    id=hid,
                    predict=predict,
                    weight=self.spec.weights[i],
                    description="fuzz hypothesis %s" % hid,
                )
            )
        return out

    def cost_map(self) -> Dict[str, float]:
        return {a: c for a, c in zip(self.spec.actions, self.spec.costs)}

    @property
    def state(self) -> str:
        return self.spec.state_token

    @property
    def actions(self) -> List[str]:
        return list(self.spec.actions)


def generate(seed: int) -> HypWorld:
    """A hypothesis frontier, a pure function of `seed`."""
    rng = Rng(seed)

    flavour = rng.weighted(
        [("random", 5), ("agreeing", 2), ("singleton", 1), ("splitting", 3)]
    )

    n_hyp = 1 if flavour == "singleton" else rng.between(2, 8)
    n_actions = rng.between(1, 6)
    n_obs = rng.between(2, 4)

    hypothesis_ids = tuple("h%d" % i for i in range(n_hyp))
    actions = tuple(ACTION_NAMES[:n_actions])
    observations = tuple(OBSERVATIONS[:n_obs])

    if flavour == "agreeing":
        row = tuple(rng.choice(observations) for _ in actions)
        table = tuple(row for _ in range(n_hyp))
    elif flavour == "splitting":
        table_rows = []
        for i in range(n_hyp):
            table_rows.append(
                tuple(rng.choice(observations) for _ in actions)
            )
        # Force the first action to separate: hypothesis i gets observation
        # i mod n_obs, so the class count is known before the engine runs.
        table = tuple(
            (observations[i % n_obs],) + row[1:]
            for i, row in enumerate(table_rows)
        )
    else:
        table = tuple(
            tuple(rng.choice(observations) for _ in actions)
            for _ in range(n_hyp)
        )

    weights = tuple(
        1.0 if rng.chance(2, 3) else float(rng.between(1, 5))
        for _ in range(n_hyp)
    )

    costs = []
    for _ in actions:
        pick = rng.weighted([("unit", 5), ("int", 3), ("frac", 2), ("zero", 1)])
        if pick == "unit":
            costs.append(1.0)
        elif pick == "int":
            costs.append(float(rng.between(2, 12)))
        elif pick == "frac":
            costs.append(rng.between(1, 8) / 4.0)
        else:
            costs.append(0.0)

    spec = HypSpec(
        seed=seed, flavour=flavour, hypothesis_ids=hypothesis_ids,
        actions=actions, observations=observations, table=table,
        weights=weights, costs=tuple(costs),
        state_token="s%016x" % (seed & ((1 << 64) - 1)),
    )
    return HypWorld(spec=spec)
