"""P3: heldout.split.random_transition_split leaks -- train and test overlap."""
from heldout import split as S
def _bad(n_transitions, world_seed):
    order = S.shuffled(range(n_transitions), world_seed ^ S.SPLIT_SALT)
    cut = (n_transitions * 7) // 10
    return sorted(order[:cut]), sorted(order[cut - 12:])
S.random_transition_split = _bad
