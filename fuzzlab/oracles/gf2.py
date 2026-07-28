"""Exact GF(2) linear algebra, written here so it can judge `zero_space`.

The house rule in `oracles/__init__.py` is that an oracle may not call the engine
it judges, and this is the file where that rule costs something: `zero_space`
already contains a perfectly good null-space routine, and using it would prove
only that the module agrees with itself.

So this is an independent implementation — bitset Gaussian elimination, reduced
row echelon form, null space by back-substitution over the free columns. It is
deliberately the textbook algorithm and deliberately not clever: an oracle that
needs its own debugging is not an oracle.

Convention throughout: a vector over GF(2) of length `n` is a Python `int`, bit
`i` being coordinate `i`. Bitsets rather than lists because the whole point is to
be obviously right and incidentally fast enough to run 500 times.
"""

from typing import Dict, Iterable, List, Sequence, Tuple


def row_echelon(rows: Sequence[int], n_cols: int) -> Tuple[List[int], List[int]]:
    """Reduced row echelon form.  Returns `(rows, pivot_column_per_row)`."""
    out: List[int] = [r for r in rows if r]
    pivots: List[int] = []
    rank = 0
    for col in range(n_cols):
        bit = 1 << col
        pivot = next((i for i in range(rank, len(out)) if out[i] & bit), None)
        if pivot is None:
            continue
        out[rank], out[pivot] = out[pivot], out[rank]
        for i in range(len(out)):
            if i != rank and (out[i] & bit):
                out[i] ^= out[rank]
        pivots.append(col)
        rank += 1
    return out[:rank], pivots


def null_space(rows: Sequence[int], n_cols: int) -> List[int]:
    """A basis for `{x : R x = 0}`, as bitset vectors of length `n_cols`.

    Standard construction: put `R` in RREF, take the non-pivot columns as free
    variables, and read each basis vector off the pivot rows. The basis is
    returned in increasing free-column order, which makes it deterministic — an
    oracle whose answer depends on dict order cannot be compared against
    anything.
    """
    reduced, pivots = row_echelon(rows, n_cols)
    pivot_set = set(pivots)
    free = [c for c in range(n_cols) if c not in pivot_set]
    basis: List[int] = []
    for f in free:
        vector = 1 << f
        for row_index, pivot_col in enumerate(pivots):
            if reduced[row_index] & (1 << f):
                vector |= 1 << pivot_col
        basis.append(vector)
    return basis


def in_span(vector: int, basis: Sequence[int], n_cols: int) -> bool:
    """Is `vector` a GF(2) combination of `basis`?"""
    reduced, pivots = row_echelon(list(basis), n_cols)
    residue = vector
    for row, col in zip(reduced, pivots):
        if residue & (1 << col):
            residue ^= row
    return residue == 0


def same_span(a: Sequence[int], b: Sequence[int], n_cols: int) -> bool:
    """Do two sets of vectors span the same subspace?

    Compared by RREF rather than by rank alone: two subspaces of equal dimension
    are routinely different, and an oracle that only checked dimension would pass
    a `zero_space` that returned the right *number* of wrong laws.
    """
    ra, _pa = row_echelon(list(a), n_cols)
    rb, _pb = row_echelon(list(b), n_cols)
    return ra == rb


# ------------------------------------------------------------------ features

def feature_index(cells: int, colors: Sequence[str]) -> Dict[Tuple[int, str], int]:
    """`(cell, colour) -> coordinate`, in a fixed order.

    The indicator encoding `zero_space` works in: one GF(2) coordinate per
    (cell, colour) pair, set iff that cell shows that colour. A "law" is a subset
    of those coordinates whose parity never changes along the trajectory.
    """
    return {(cell, color): cell * len(colors) + c
            for cell in range(cells)
            for c, color in enumerate(colors)}


def encode(state: Sequence[str], index: Dict[Tuple[int, str], int]) -> int:
    vector = 0
    for cell, color in enumerate(state):
        bit = index.get((cell, color))
        if bit is not None:
            vector |= 1 << bit
    return vector


def conserved_laws(states: Sequence[Sequence[str]],
                   colors: Sequence[str]) -> Tuple[List[int], int]:
    """Every GF(2) law conserved across the whole trajectory, and the dimension.

    A law is a coefficient vector `a` with `<a, x_t>` equal for all `t`, which
    over GF(2) is `<a, x_t - x_0> = 0` for every `t` — so the law space is
    exactly the null space of the matrix of *difference* vectors. Computing it
    from differences rather than from consecutive transitions is the same
    subspace and one fewer place to get an off-by-one wrong.
    """
    if not states:
        return [], 0
    n_cols = len(states[0]) * len(colors)
    index = feature_index(len(states[0]), colors)
    base = encode(states[0], index)
    differences = [encode(s, index) ^ base for s in states[1:]]
    basis = null_space(differences, n_cols)
    return basis, n_cols


def holds_on(law: int, states: Sequence[Sequence[str]],
             colors: Sequence[str]) -> bool:
    """Does this law really have constant parity along the trajectory?

    The direct check, kept separate from `conserved_laws` on purpose: one
    computes a subspace by elimination, the other evaluates a single vector state
    by state. When they disagree the oracle is wrong, and that is worth being
    able to find out.
    """
    index = feature_index(len(states[0]), colors)
    values = {bin(encode(s, index) & law).count("1") % 2 for s in states}
    return len(values) <= 1
