"""Exact linear algebra over GF(2), with vectors as integer bitmasks.

Bit j of a vector is coefficient j.  Everything here is exact by construction --
no tolerances, no floating point -- which is the whole reason the framework puts
conservation laws on this engine rather than on a statistical one.
"""

from typing import Dict, Iterable, List, Sequence, Tuple


def from_bits(bits: Sequence[int]) -> int:
    value = 0
    for i, bit in enumerate(bits):
        if bit % 2:
            value |= 1 << i
    return value


def to_bits(vector: int, n: int) -> List[int]:
    return [(vector >> i) & 1 for i in range(n)]


def support(vector: int, n: int) -> List[int]:
    return [i for i in range(n) if (vector >> i) & 1]


def dot(a: int, b: int) -> int:
    """Bilinear form over GF(2): parity of the overlap."""
    return bin(a & b).count("1") % 2


def rref(rows: Iterable[int]) -> Dict[int, int]:
    """Reduced row echelon form; returns {pivot column: row}."""
    pivots: Dict[int, int] = {}
    for row in rows:
        current = row
        for col in sorted(pivots):
            if (current >> col) & 1:
                current ^= pivots[col]
        if not current:
            continue
        col = (current & -current).bit_length() - 1     # lowest set bit
        for other_col in list(pivots):                  # back-substitute
            if (pivots[other_col] >> col) & 1:
                pivots[other_col] ^= current
        pivots[col] = current
    return pivots


def rank(rows: Iterable[int]) -> int:
    return len(rref(rows))


def in_span(vector: int, basis: Iterable[int]) -> bool:
    pivots = rref(basis)
    current = vector
    for col in sorted(pivots):
        if (current >> col) & 1:
            current ^= pivots[col]
    return current == 0


def span_equal(a: Sequence[int], b: Sequence[int]) -> bool:
    """Do two sets of vectors span the same subspace?"""
    return (
        rank(a) == rank(b) == rank(list(a) + list(b))
    )


def null_space(rows: Sequence[int], n_cols: int) -> List[int]:
    """Basis of {x : row . x = 0 for every row}."""
    pivots = rref(rows)
    pivot_cols = sorted(pivots)
    free_cols = [c for c in range(n_cols) if c not in pivots]
    basis: List[int] = []
    for free in free_cols:
        vector = 1 << free
        for col in pivot_cols:
            if (pivots[col] >> free) & 1:
                vector |= 1 << col
        basis.append(vector)
    return basis


def reduce_modulo(vector: int, subspace: Sequence[int]) -> int:
    """Canonical representative of `vector` in the quotient by `subspace`."""
    pivots = rref(subspace)
    current = vector
    for col in sorted(pivots):
        if (current >> col) & 1:
            current ^= pivots[col]
    return current


def quotient_basis(space: Sequence[int], subspace: Sequence[int]) -> List[int]:
    """Vectors of `space` that extend `subspace` to all of it, one per dimension."""
    growing: List[int] = list(subspace)
    out: List[int] = []
    for vector in space:
        if not in_span(vector, growing):
            growing.append(vector)
            out.append(vector)
    return out
