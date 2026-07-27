"""Deterministic PRNG.

Rationale: `random.Random` is stable in practice but its guarantees are tied to
CPython implementation details of `_randbelow`/`choice`.  The fixtures must be
byte-identical for the same seed on any interpreter, so we carry our own
splitmix64 generator: 30 lines, fully specified, no library dependency.
"""

_MASK64 = (1 << 64) - 1


class SplitMix64:
    """splitmix64 (Steele et al. 2014). Same seed -> same byte stream, forever."""

    def __init__(self, seed: int):
        self._s = seed & _MASK64

    def next_u64(self) -> int:
        self._s = (self._s + 0x9E3779B97F4A7C15) & _MASK64
        z = self._s
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK64
        return z ^ (z >> 31)

    def below(self, n: int) -> int:
        """Uniform integer in [0, n) via rejection sampling (no modulo bias)."""
        if n <= 0:
            raise ValueError("n must be positive")
        limit = _MASK64 - (_MASK64 % n)
        while True:
            r = self.next_u64()
            if r <= limit:
                return r % n

    def choice(self, seq):
        return seq[self.below(len(seq))]
