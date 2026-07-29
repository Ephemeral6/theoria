"""The split rules, as executable code.

One module, so that "how was it cut" is answerable by reading twenty lines rather
than by trusting a sentence.  Each function is a literal transcription of a rule
in PREREGISTRATION.md section 2 and must not be edited after a hit rate has been
seen -- the pre-registration commit is the ancestor that proves it was not.
"""

from typing import List, Sequence, Tuple

from common.rng import SplitMix64

TRAIN_FRACTION_NUMERATOR = 7          # Z-S1: 70 / 30
TRAIN_FRACTION_DENOMINATOR = 10
SPLIT_SALT = 0x5115                   # Z-S1: world_seed ^ SPLIT_SALT drives the shuffle


def shuffled(items: Sequence[int], seed: int) -> List[int]:
    """Fisher-Yates over `items`, driven by SplitMix64 -- interpreter-independent."""
    out = list(items)
    rng = SplitMix64(seed)
    for i in range(len(out) - 1, 0, -1):
        j = rng.below(i + 1)
        out[i], out[j] = out[j], out[i]
    return out


def random_transition_split(n_transitions: int, world_seed: int
                            ) -> Tuple[List[int], List[int]]:
    """Z-S1.  Returns (train_indices, heldout_indices), both sorted, disjoint.

    Every transition lands on exactly one side; the assertion is here rather than
    in a test because a split that leaked would silently turn this whole run into
    the thing it is measuring.
    """
    order = shuffled(range(n_transitions), world_seed ^ SPLIT_SALT)
    cut = (n_transitions * TRAIN_FRACTION_NUMERATOR) // TRAIN_FRACTION_DENOMINATOR
    train = sorted(order[:cut])
    heldout = sorted(order[cut:])
    assert set(train).isdisjoint(heldout), "Z-S1 split leaked"
    assert len(train) + len(heldout) == n_transitions, "Z-S1 split lost a transition"
    return train, heldout


def leave_one_operation_out(actions: Sequence[int], operation: int
                            ) -> Tuple[List[int], List[int]]:
    """Z-S2.  Held out = every transition whose action is `operation`."""
    train = [t for t, a in enumerate(actions) if a != operation]
    heldout = [t for t, a in enumerate(actions) if a == operation]
    assert set(train).isdisjoint(heldout), "Z-S2 split leaked"
    assert len(train) + len(heldout) == len(actions), "Z-S2 split lost a transition"
    return train, heldout
