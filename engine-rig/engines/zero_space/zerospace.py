"""zero_space -- every linear conservation law over GF(2), in one elimination.

The state is encoded as one indicator feature per (cell, colour) pair.  The
engine is *not* handed the notion "red count": it sees 16 anonymous bits, takes
the difference of consecutive states, and computes the null space of the observed
difference matrix.  Every vector `a` in that null space satisfies
`a . x(t) = a . x(0)` for all t -- i.e. one linear conservation law, exactly, with
no search and no tolerance.

Two kinds of law come out of Fixture B and the engine labels them apart:

  cell-local -- support inside a single cell's feature group, e.g.
                "cell 3 holds exactly one of {R, B}", a law about the encoding;
  global     -- support spanning cells; here exactly one dimension's worth, and
                every representative of it is `(#Red) mod 2 = const`.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from engines.zero_space import gf2


@dataclass(frozen=True)
class Feature:
    cell: int
    color: str

    def name(self) -> str:
        return "%s@%d" % (self.color, self.cell)


@dataclass
class Law:
    """One linear conservation law: sum of the selected features, mod 2."""

    vector: int
    features: List[Feature]
    value: int
    scope: str                      # cell_local | global

    @property
    def n_features(self) -> int:
        return len(self.features)

    def coefficients(self) -> List[int]:
        return gf2.to_bits(self.vector, self.n_features)

    def support(self) -> List[Feature]:
        return [self.features[i] for i in gf2.support(self.vector, self.n_features)]

    def rendering(self) -> str:
        chosen = self.support()
        cells = {f.cell for f in chosen}
        colors = {f.color for f in chosen}
        if len(colors) == 1 and len(cells) == self.n_cells:
            return "(#%s) mod 2 = %d" % (chosen[0].color, self.value)
        if len(cells) == 1:
            names = "+".join(f.color for f in sorted(chosen, key=lambda f: f.color))
            return "cell %d: %s mod 2 = %d" % (chosen[0].cell, names, self.value)
        return "(%s) mod 2 = %d" % (
            " + ".join(f.name() for f in chosen),
            self.value,
        )

    @property
    def n_cells(self) -> int:
        return len({f.cell for f in self.features})

    def as_json(self) -> Dict[str, object]:
        return {
            "form": "gf2_linear",
            "modulus": 2,
            "features": [{"cell": f.cell, "color": f.color} for f in self.features],
            "coefficients": self.coefficients(),
            "support": [f.name() for f in self.support()],
            "value": self.value,
            "scope": self.scope,
            "rendering": self.rendering(),
        }


@dataclass
class ZeroSpaceResult:
    features: List[Feature]
    laws: List[Law]
    basis: List[int]
    difference_rank: int
    n_transitions: int

    @property
    def n_features(self) -> int:
        return len(self.features)

    @property
    def dimension(self) -> int:
        return len(self.basis)

    def global_laws(self) -> List[Law]:
        return [law for law in self.laws if law.scope == "global"]

    def cell_local_laws(self) -> List[Law]:
        return [law for law in self.laws if law.scope == "cell_local"]

    def contains(self, vector: int) -> bool:
        """Is this vector one of the conservation laws the evidence supports?"""
        return gf2.in_span(vector, self.basis)


# ------------------------------------------------------------------ encoding

def build_features(n_cells: int, colors: Sequence[str]) -> List[Feature]:
    return [Feature(cell, color) for cell in range(n_cells) for color in colors]


def encode(state: Sequence[str], features: Sequence[Feature]) -> int:
    vector = 0
    for i, feature in enumerate(features):
        if state[feature.cell] == feature.color:
            vector |= 1 << i
    return vector


# -------------------------------------------------------------------- driver

def local_laws(basis: Sequence[int], features: Sequence[Feature]) -> List[int]:
    """Laws whose support lies inside a single cell -- laws about the encoding.

    These are extracted first so that what remains is the part of the recovered
    space that says something about the *world*.  The null space basis that falls
    out of the elimination is arbitrary (it depends on which columns end up
    free), and left alone it mixes the two kinds together.
    """
    groups: Dict[int, List[int]] = {}
    for i, feature in enumerate(features):
        groups.setdefault(feature.cell, []).append(i)

    found: List[int] = []
    for cell in sorted(groups):
        indices = groups[cell]
        if len(indices) > 8:                       # keep the enumeration bounded
            subsets = [[i] for i in indices] + [indices]
        else:
            subsets = [
                [indices[k] for k in range(len(indices)) if (mask >> k) & 1]
                for mask in range(1, 1 << len(indices))
            ]
        for subset in subsets:
            vector = 0
            for i in subset:
                vector |= 1 << i
            if gf2.in_span(vector, basis) and not gf2.in_span(vector, found):
                found.append(vector)
    return found


def analyse(states: Sequence[Sequence[str]], colors: Sequence[str]) -> ZeroSpaceResult:
    n_cells = len(states[0])
    features = build_features(n_cells, sorted(colors))
    encoded = [encode(state, features) for state in states]
    differences = [encoded[t] ^ encoded[t + 1] for t in range(len(encoded) - 1)]

    basis = gf2.null_space(differences, len(features))

    # Canonical presentation: the encoding's own laws first, then a
    # representative of each remaining dimension, reduced modulo them.
    locals_ = local_laws(basis, features)
    globals_ = [
        gf2.reduce_modulo(vector, locals_)
        for vector in gf2.quotient_basis(sorted(basis), locals_)
    ]

    laws: List[Law] = []
    for scope, vectors in (("cell_local", locals_), ("global", globals_)):
        for vector in vectors:
            laws.append(
                Law(
                    vector=vector,
                    features=features,
                    value=gf2.dot(vector, encoded[0]),
                    scope=scope,
                )
            )

    return ZeroSpaceResult(
        features=features,
        laws=laws,
        basis=sorted(locals_ + globals_),
        difference_rank=gf2.rank(differences),
        n_transitions=len(differences),
    )


def verify(result: ZeroSpaceResult, states: Sequence[Sequence[str]]) -> bool:
    """Re-check every reported law directly against the trajectory."""
    encoded = [encode(state, result.features) for state in states]
    for law in result.laws:
        values = {gf2.dot(law.vector, x) for x in encoded}
        if values != {law.value}:
            return False
    return True


def red_parity_vector(features: Sequence[Feature], color: str) -> int:
    """The ground-truth law, for equivalence checking: (#color) mod 2."""
    vector = 0
    for i, feature in enumerate(features):
        if feature.color == color:
            vector |= 1 << i
    return vector


def cell_local_subspace(features: Sequence[Feature]) -> List[int]:
    """Span of the per-cell "exactly one colour" laws."""
    by_cell: Dict[int, int] = {}
    for i, feature in enumerate(features):
        by_cell[feature.cell] = by_cell.get(feature.cell, 0) | (1 << i)
    return [by_cell[cell] for cell in sorted(by_cell)]


def equivalent_modulo_encoding(result: ZeroSpaceResult, target: int) -> bool:
    """Is the recovered space exactly `target` plus the encoding's own laws?

    This is the equivalence check the acceptance criterion asks for: not string
    matching, and not merely "the law is in there" -- the recovered space must be
    spanned by the target together with the cell-occupancy laws, so nothing is
    missing and nothing extra has been claimed.
    """
    structural = cell_local_subspace(result.features)
    return gf2.span_equal(result.basis, structural + [target])
