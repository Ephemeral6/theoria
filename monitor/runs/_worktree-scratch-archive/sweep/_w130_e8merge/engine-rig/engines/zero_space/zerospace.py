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

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from engines.zero_space import gf2


@dataclass(frozen=True)
class Feature:
    cell: int
    color: str

    def name(self) -> str:
        return "%s@%d" % (self.color, self.cell)


#: The three things `scope` can say.  `undetermined` is not a third *kind* of
#: law -- it is the same quotient representative `global` names, reported under a
#: different word because the search that would have justified `global` was cut
#: short.  A distinct word rather than a flag beside `global`, so that a consumer
#: filtering `scope == "global"` gets fewer laws instead of an unproved one, and
#: so the weakening cannot be lost by a reader who does not know to look for the
#: flag (E15).  No substring of `global`, deliberately: `"global" in scope` must
#: not resurrect it either.
CELL_LOCAL = "cell_local"
GLOBAL = "global"
UNDETERMINED = "undetermined"


@dataclass
class Law:
    """One linear conservation law: sum of the selected features, mod 2."""

    vector: int
    features: List[Feature]
    value: int
    scope: str                      # cell_local | global | undetermined
    # Cells whose colour subsets were not enumerated exhaustively.  Non-empty
    # means a cell-local explanation may exist and was never searched for, which
    # is why such a law is published as `undetermined` rather than `global` --
    # the difference between a law about the world and a law about the encoding.
    truncated_cells: Tuple[int, ...] = ()
    subset_enumeration_limit: Optional[int] = None

    @property
    def scope_exhaustive(self) -> bool:
        return not self.truncated_cells

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
        # The degradation keys below are emitted **only** on a truncated row, and
        # that restriction is load-bearing rather than tidy: `artifacts/
        # candidates.jsonl` is sha256-pinned in `release/MANIFEST.jsonl` and the
        # candidate ids are content-addressed, so a key added to every row
        # re-hashes every zero_space candidate and invalidates a manifest this
        # track does not own.  An exhaustively-enumerated row is byte-identical
        # to what it was before E15; a truncated one -- which no checked-in
        # artifact contains, all of them being 2-colour -- carries the budget on
        # its face.  Shape borrowed from `bench/ladder.py`'s over-budget rung,
        # which writes `proved_unsolvable: False` *and* an `error` naming the
        # limit rather than dropping the row: the cap is recorded positively, in
        # the product, where a reader who never opens this file will meet it.
        payload: Dict[str, object] = {
            "form": "gf2_linear",
            "modulus": 2,
            "features": [{"cell": f.cell, "color": f.color} for f in self.features],
            "coefficients": self.coefficients(),
            "support": [f.name() for f in self.support()],
            "value": self.value,
            "scope": self.scope,
            "rendering": self.rendering(),
        }
        #
        # Gated on the *label*, not on `scope_exhaustive`.  Every law of a
        # truncated run carries `scope_exhaustive is False` -- that is C11's
        # reading and it is kept -- but a `cell_local` law was **found** in the
        # span, and the budget cut short the searching, not the finding.  Its
        # claim is unweakened, so its payload is unchanged; only the quotient
        # representatives, whose classification is exactly what went unsearched,
        # carry the degradation.
        if self.scope == UNDETERMINED:
            payload["scope_proved"] = False
            payload["subset_enumeration_limit"] = self.subset_enumeration_limit
            payload["truncated_cells"] = list(self.truncated_cells)
            payload["error"] = (
                "over budget: cell-local enumeration capped at %s colours per "
                "cell; cells %s were searched only for singletons and their full "
                "set" % (self.subset_enumeration_limit, list(self.truncated_cells))
            )
            payload["scope_note"] = (
                "scope is %r, not %r: a cell-local explanation for this law may "
                "exist in cells %s and was not searched for. The law itself is "
                "unaffected -- it holds on the trajectory either way -- but "
                "whether it is a fact about the world or about the encoding is "
                "undecided here."
                % (UNDETERMINED, GLOBAL, list(self.truncated_cells))
            )
        return payload


@dataclass
class ZeroSpaceResult:
    features: List[Feature]
    laws: List[Law]
    basis: List[int]
    difference_rank: int
    n_transitions: int
    # Cells whose colour-subset enumeration hit `SUBSET_ENUMERATION_LIMIT`.
    # Empty is the ordinary case and means every `scope` label is a proof.
    truncated_cells: List[int] = field(default_factory=list)

    @property
    def scope_exhaustive(self) -> bool:
        return not self.truncated_cells

    @property
    def n_features(self) -> int:
        return len(self.features)

    @property
    def dimension(self) -> int:
        return len(self.basis)

    def global_laws(self) -> List[Law]:
        """Laws proved to span cells.  Empty when the enumeration was truncated.

        Not "every law that is not cell-local": where a cell went unenumerated,
        the quotient representatives come back as `undetermined` and are found
        through `undetermined_laws`.  A caller that wants both should say so.
        """
        return [law for law in self.laws if law.scope == GLOBAL]

    def cell_local_laws(self) -> List[Law]:
        return [law for law in self.laws if law.scope == CELL_LOCAL]

    def undetermined_laws(self) -> List[Law]:
        """Quotient representatives whose classification the budget cut short."""
        return [law for law in self.laws if law.scope == UNDETERMINED]

    def as_json(self) -> Dict[str, object]:
        """The run's own degradation record, independent of any single law."""
        return {
            "form": "zero_space_run",
            "n_features": self.n_features,
            "dimension": self.dimension,
            "difference_rank": self.difference_rank,
            "n_transitions": self.n_transitions,
            "subset_enumeration_limit": SUBSET_ENUMERATION_LIMIT,
            "truncated_cells": list(self.truncated_cells),
            "scope_exhaustive": self.scope_exhaustive,
            "scope_counts": {
                CELL_LOCAL: len(self.cell_local_laws()),
                GLOBAL: len(self.global_laws()),
                UNDETERMINED: len(self.undetermined_laws()),
            },
            "error": None if self.scope_exhaustive else (
                "over budget: cell-local enumeration capped at %d colours per "
                "cell; cells %s not enumerated exhaustively, so %d law(s) are "
                "reported as %r rather than %r"
                % (SUBSET_ENUMERATION_LIMIT, list(self.truncated_cells),
                   len(self.undetermined_laws()), UNDETERMINED, GLOBAL)
            ),
        }

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

SUBSET_ENUMERATION_LIMIT = 8


def local_laws(basis: Sequence[int], features: Sequence[Feature]
               ) -> Tuple[List[int], List[int]]:
    """Laws whose support lies inside a single cell -- laws about the encoding.

    These are extracted first so that what remains is the part of the recovered
    space that says something about the *world*.  The null space basis that falls
    out of the elimination is arbitrary (it depends on which columns end up
    free), and left alone it mixes the two kinds together.

    Returns `(found, truncated_cells)`.  A cell with more than
    `SUBSET_ENUMERATION_LIMIT` colours is not enumerated exhaustively -- only its
    singletons and its full set are tried -- so a cell-local law over, say, three
    of eleven colours is missed there.  A missed cell-local law does not vanish:
    it stays in the quotient, and until E15 it was published with
    `scope: "global"`, i.e. as a law **about the world** rather than about the
    encoding.  That was a budget deciding a classification.  The budget is
    returned rather than absorbed, `analyse` carries it into the result, and the
    affected representatives are now labelled `undetermined` and carry the cap
    in their own payload.  It is live, not hypothetical: a ten-colour palette
    crosses the limit.
    """
    groups: Dict[int, List[int]] = {}
    for i, feature in enumerate(features):
        groups.setdefault(feature.cell, []).append(i)

    found: List[int] = []
    truncated: List[int] = []
    for cell in sorted(groups):
        indices = groups[cell]
        if len(indices) > SUBSET_ENUMERATION_LIMIT:   # keep the enumeration bounded
            subsets = [[i] for i in indices] + [indices]
            truncated.append(cell)
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
    return found, truncated


def analyse(states: Sequence[Sequence[str]], colors: Sequence[str]) -> ZeroSpaceResult:
    n_cells = len(states[0])
    features = build_features(n_cells, sorted(colors))
    encoded = [encode(state, features) for state in states]
    differences = [encoded[t] ^ encoded[t + 1] for t in range(len(encoded) - 1)]

    basis = gf2.null_space(differences, len(features))

    # Canonical presentation: the encoding's own laws first, then a
    # representative of each remaining dimension, reduced modulo them.
    locals_, truncated_cells = local_laws(basis, features)
    globals_ = [
        gf2.reduce_modulo(vector, locals_)
        for vector in gf2.quotient_basis(sorted(basis), locals_)
    ]

    # `global` is only a proved classification when every cell was enumerated
    # exhaustively.  Where it was not, the quotient representatives are not
    # promoted to a claim about the world at all -- they go out as
    # `undetermined`, carrying the cells and the cap that put them there.  The
    # cell-local ones are unaffected: those were *found* in the span, and
    # finding is not what the budget cut short.
    quotient_scope = GLOBAL if not truncated_cells else UNDETERMINED

    laws: List[Law] = []
    for scope, vectors in ((CELL_LOCAL, locals_), (quotient_scope, globals_)):
        for vector in vectors:
            laws.append(
                Law(
                    vector=vector,
                    features=features,
                    value=gf2.dot(vector, encoded[0]),
                    scope=scope,
                    truncated_cells=tuple(truncated_cells),
                    subset_enumeration_limit=SUBSET_ENUMERATION_LIMIT,
                )
            )

    return ZeroSpaceResult(
        features=features,
        laws=laws,
        basis=sorted(locals_ + globals_),
        difference_rank=gf2.rank(differences),
        n_transitions=len(differences),
        truncated_cells=truncated_cells,
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
