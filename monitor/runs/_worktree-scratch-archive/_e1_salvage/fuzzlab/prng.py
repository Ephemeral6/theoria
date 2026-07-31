"""Deterministic randomness for world generation.

Wraps engine-rig's splitmix64 (`common.rng.SplitMix64`) rather than carrying a
second generator: the repo already committed to one fully-specified byte stream
per seed, and a fuzz campaign whose seed table must replay years from now is the
last place to introduce a second one.

Every helper here is a pure function of the generator state, so a `Rng(seed)`
reproduces its whole draw sequence exactly.  `derive` is how one campaign seed
fans out into per-world, per-family seeds without correlating them: the family
name is folded in through a fixed 64-bit hash, so world 17 of the `grid_solo`
family and world 17 of `jump_graph` share a campaign seed and nothing else.
"""

from typing import Any, Dict, List, Sequence, Tuple

from fuzzlab import rig  # noqa: F401  (path bootstrap)
from common.rng import SplitMix64

MASK64 = (1 << 64) - 1


def fold(name: str) -> int:
    """FNV-1a over the family name -- stable across interpreters and releases."""
    h = 0xCBF29CE484222325
    for byte in name.encode("utf-8"):
        h = ((h ^ byte) * 0x100000001B3) & MASK64
    return h


def derive(campaign_seed: int, family: str, index: int) -> int:
    """The seed for world `index` of `family` under `campaign_seed`."""
    mixer = SplitMix64((campaign_seed ^ fold(family)) & MASK64)
    for _ in range(index + 1):
        value = mixer.next_u64()
    return value


class Rng:
    """SplitMix64 plus the draws world generators actually need."""

    def __init__(self, seed: int):
        self.seed = seed & MASK64
        self._core = SplitMix64(self.seed)

    # ------------------------------------------------------------- primitives

    def u64(self) -> int:
        return self._core.next_u64()

    def below(self, n: int) -> int:
        return self._core.below(n)

    def between(self, lo: int, hi: int) -> int:
        """Uniform integer in [lo, hi] inclusive."""
        if hi < lo:
            raise ValueError("empty range [%d, %d]" % (lo, hi))
        return lo + self.below(hi - lo + 1)

    def chance(self, numerator: int, denominator: int) -> bool:
        return self.below(denominator) < numerator

    def choice(self, seq: Sequence[Any]) -> Any:
        return seq[self.below(len(seq))]

    # ------------------------------------------------------------ collections

    def shuffled(self, seq: Sequence[Any]) -> List[Any]:
        """Fisher-Yates; returns a new list, leaves the input alone."""
        out = list(seq)
        for i in range(len(out) - 1, 0, -1):
            j = self.below(i + 1)
            out[i], out[j] = out[j], out[i]
        return out

    def sample(self, seq: Sequence[Any], k: int) -> List[Any]:
        """`k` distinct elements, in the order the shuffle produced them."""
        if k > len(seq):
            raise ValueError("cannot sample %d of %d" % (k, len(seq)))
        return self.shuffled(seq)[:k]

    def subset(self, seq: Sequence[Any], min_size: int = 0,
               max_size: int = None) -> List[Any]:
        """A random subset in the input's own order, size in [min_size, max_size].

        Indices are sampled rather than values, so a sequence with repeats or
        with unhashable elements subsets correctly.
        """
        top = len(seq) if max_size is None else min(max_size, len(seq))
        size = self.between(min(min_size, top), top)
        picked = sorted(self.sample(list(range(len(seq))), size))
        return [seq[i] for i in picked]

    def weighted(self, options: Sequence[Tuple[Any, int]]) -> Any:
        """Pick from (value, weight) pairs; weights are positive integers."""
        total = sum(weight for _, weight in options)
        if total <= 0:
            raise ValueError("no positive weight")
        roll = self.below(total)
        for value, weight in options:
            if roll < weight:
                return value
            roll -= weight
        return options[-1][0]                            # pragma: no cover

    # ------------------------------------------------------------- provenance

    def state(self) -> Dict[str, Any]:
        return {"generator": "splitmix64", "seed": self.seed}
