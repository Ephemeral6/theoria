"""Sequential covering: learn a disjunctive effect class as several conjunctive rules.

`cegis_miner.synthesize` looks for ONE conjunction true of every positive and no
negative. On the A0 world that fails outright, and correctly so -- with enough
evidence the `blocked` class is genuinely disjunctive:

    nothing moves  <=  a wall or the board edge is ahead
                    OR the box is ahead but the cell it would cross is occupied
                    OR the box is ahead but the cell it would land on is occupied

No conjunction covers those three together, so `synthesize` raises
NoSeparatingGuard. The answer is not to weaken the guard language -- the frozen
grammar says guards are conjunctions -- but to learn a *set* of rules whose
guards are conjunctions and whose disjunction is the class. That is ordinary
sequential covering, and it keeps every individual rule inside the contract.

Each learned conjunct excludes every negative, so each rule is sound on its own;
together they cover all positives. Mutual exclusivity is then checked separately,
because "exactly one successor" is an obligation, not an assumption.
"""

from typing import Dict, List, Sequence, Tuple


def _mask_of(guard: Sequence, masks: Dict, universe: int) -> int:
    mask = universe
    for atom in guard:
        mask &= masks[atom]
    return mask


def _generalise(seed: int, atoms: Sequence, masks: Dict, universe: int,
                negatives: int, order_key, keep: Sequence = ()) -> List:
    """Most general conjunction containing `seed` that admits no negative.

    Start from every literal true at the seed -- the maximally specific rule,
    describing exactly that transition -- then drop literals while no negative
    creeps in.

    Which literal to drop next is not arbitrary: at each step drop the one whose
    removal *covers the most positives*. Dropping in a fixed order instead (by
    cost, say) leaves accidental correlates standing -- a first cut of this
    produced `act==DOWN and ahead_free(RIGHT) and ahead_is_box(LEFT)`, which is
    true of its witnesses and means nothing. An accidental literal is exactly the
    one whose removal widens coverage, so maximising coverage strips it.

    `keep` literals are never dropped, so a rule always names its own action and
    can be read without knowing which bucket it came from.
    """
    guard = [a for a in atoms if (masks[a] >> seed) & 1]
    keep_set = set(keep)
    positives = universe & ~negatives
    while True:
        best, best_cover = None, -1
        for atom in guard:
            if atom in keep_set:
                continue
            reduced = [a for a in guard if a is not atom]
            covered = _mask_of(reduced, masks, universe)
            if covered & negatives:
                continue
            score = bin(covered & positives).count("1")
            if score > best_cover:
                best, best_cover = atom, score
        if best is None:
            break
        guard = [a for a in guard if a is not best]
    return sorted(guard, key=order_key)


def learn_dnf(positives: int, universe: int, masks: Dict, order_key,
              max_rules: int = 8, keep: Sequence = ()) -> List[List]:
    """Cover every positive with conjunctions, none of which admits a negative."""
    negatives = universe & ~positives
    atoms = list(masks)
    uncovered = positives
    rules: List[List] = []

    while uncovered:
        if len(rules) >= max_rules:
            raise RuntimeError(
                "could not cover the class in %d conjunctions; %d positives left"
                % (max_rules, bin(uncovered).count("1"))
            )
        seed = (uncovered & -uncovered).bit_length() - 1
        guard = _generalise(seed, atoms, masks, universe, negatives, order_key, keep=keep)
        covered = _mask_of(guard, masks, universe)
        if not covered & uncovered:                     # pragma: no cover - defensive
            raise RuntimeError("generalisation failed to cover its own seed")
        rules.append(guard)
        uncovered &= ~covered
    return rules


def mutually_exclusive(rules: Sequence[Sequence], masks: Dict, universe: int
                       ) -> Tuple[bool, List[Tuple[int, int]]]:
    """Do any two guards fire on the same transition? Constraint 9, checked."""
    overlaps = []
    covers = [_mask_of(rule, masks, universe) for rule in rules]
    for i in range(len(covers)):
        for j in range(i + 1, len(covers)):
            if covers[i] & covers[j]:
                overlaps.append((i, j))
    return not overlaps, overlaps
