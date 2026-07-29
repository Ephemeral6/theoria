"""Held-out validation for `zero_space`.

`zerospace.analyse` computes the null space of the differences of *consecutive*
states, so a subset of transitions cannot be expressed as a sub-trajectory.  The
fit below therefore selects difference vectors explicitly and then hands them to
the engine's own code: `gf2.null_space`, `zerospace.local_laws`,
`gf2.quotient_basis`, `gf2.reduce_modulo` and `zerospace.Law`.  Selection is the
only thing this module does that the engine does not.

`fit_matches_engine` is the gate on that claim: with train = every transition the
basis produced here must equal `analyse(...).basis` exactly.  It is checked on
every world of the corpus, not sampled.
"""

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from engines.zero_space import gf2, zerospace
from engines.zero_space.zerospace import Feature, Law
from heldout import split
from heldout.parityworld import COLORS, ParityWorld


@dataclass
class LawOutcome:
    scope: str
    support: List[str]
    value: int
    delta_hit: bool
    value_hit: bool
    first_delta_witness: Dict[str, object]     # {} when delta_hit
    first_value_witness: Dict[str, object]     # {} when value_hit


@dataclass
class SplitOutcome:
    world_id: str
    split_name: str
    variant: str                    # "" for Z-S1; "op<j>" for Z-S2
    n_train: int
    n_heldout: int
    train_rank: int
    full_rank: int
    dimension: int
    laws: List[LawOutcome]


def _features(world: ParityWorld) -> List[Feature]:
    return zerospace.build_features(world.n_cells, sorted(COLORS))


def fit(encoded: Sequence[int], features: Sequence[Feature],
        train: Sequence[int]) -> Tuple[List[Law], List[int]]:
    """The engine's presentation, over an explicitly chosen set of transitions.

    `train` holds transition indices `t`, meaning the difference between state
    `t` and state `t+1`.
    """
    differences = [encoded[t] ^ encoded[t + 1] for t in train]
    basis = gf2.null_space(differences, len(features))
    locals_, truncated = zerospace.local_laws(basis, features)
    globals_ = [
        gf2.reduce_modulo(vector, locals_)
        for vector in gf2.quotient_basis(sorted(basis), locals_)
    ]
    laws: List[Law] = []
    for scope, vectors in (("cell_local", locals_), ("global", globals_)):
        for vector in vectors:
            laws.append(
                Law(vector=vector, features=list(features),
                    value=gf2.dot(vector, encoded[0]), scope=scope,
                    scope_exhaustive=not truncated)
            )
    return laws, sorted(locals_ + globals_)


def fit_matches_engine(world: ParityWorld) -> bool:
    """Sanity gate: train = everything must reproduce `analyse` exactly."""
    features = _features(world)
    encoded = [zerospace.encode(s, features) for s in world.states]
    _, basis = fit(encoded, features, range(len(world.states) - 1))
    reference = zerospace.analyse(world.states, COLORS)
    return sorted(basis) == sorted(reference.basis)


def score(world: ParityWorld, train: Sequence[int], heldout: Sequence[int],
          split_name: str, variant: str = "") -> SplitOutcome:
    features = _features(world)
    encoded = [zerospace.encode(s, features) for s in world.states]
    laws, basis = fit(encoded, features, train)

    outcomes: List[LawOutcome] = []
    for law in laws:
        delta_witness: Dict[str, object] = {}
        value_witness: Dict[str, object] = {}
        for t in heldout:
            if gf2.dot(law.vector, encoded[t] ^ encoded[t + 1]) != 0:
                delta_witness = {
                    "transition": t,
                    "operation": world.actions[t],
                    "cells": list(world.operations[world.actions[t]]),
                }
                break
        for t in heldout:
            for endpoint in (t, t + 1):
                got = gf2.dot(law.vector, encoded[endpoint])
                if got != law.value:
                    value_witness = {"state_index": endpoint,
                                     "expected": law.value, "got": got}
                    break
            if value_witness:
                break
        outcomes.append(
            LawOutcome(
                scope=law.scope,
                support=[f.name() for f in law.support()],
                value=law.value,
                delta_hit=not delta_witness,
                value_hit=not value_witness,
                first_delta_witness=delta_witness,
                first_value_witness=value_witness,
            )
        )

    full = [encoded[t] ^ encoded[t + 1] for t in range(len(encoded) - 1)]
    return SplitOutcome(
        world_id=world.world_id,
        split_name=split_name,
        variant=variant,
        n_train=len(train),
        n_heldout=len(heldout),
        train_rank=gf2.rank([encoded[t] ^ encoded[t + 1] for t in train]),
        full_rank=gf2.rank(full),
        dimension=len(basis),
        laws=outcomes,
    )


def run_s1(world: ParityWorld) -> SplitOutcome:
    train, heldout = split.random_transition_split(len(world.actions), world.seed)
    return score(world, train, heldout, "Z-S1")


def run_s2(world: ParityWorld) -> List[SplitOutcome]:
    out = []
    for j in range(len(world.operations)):
        train, heldout = split.leave_one_operation_out(world.actions, j)
        if not train or not heldout:
            continue
        out.append(score(world, train, heldout, "Z-S2", variant="op%d" % j))
    return out
