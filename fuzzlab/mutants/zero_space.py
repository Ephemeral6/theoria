"""`zero_space` mutants — five defects, one per thing the engine promises.

The seam is `props/zero_space.py:_analyse`, the single place the property module
calls `engines.zero_space.analyse`. Each mutant below is the answer the engine
*would* have given if it had a particular bug, and `expect_kill` was written
before the driver was ever run.

Two structural facts about `ZeroSpaceResult` shape what a mutant can be, and
both are worth stating because they change what a kill means:

* `dimension` is a **property**, `len(self.basis)`. So no mutant can make
  `dimension` and `len(basis)` disagree, and `rank_nullity`'s third check
  (`len(result.basis) != result.dimension`) is **unfalsifiable by construction**
  — not weak, impossible. That is a finding about the invariant, not about any
  mutant, and it is recorded here rather than discovered later.
* `laws` and `basis` are separate fields. `zs-flip-law-value` therefore touches
  exactly one invariant, which is the point: a mutant that trips everything
  proves nothing about which invariant is load-bearing.
"""

from typing import Any, Dict, Tuple

from fuzzlab import mutants as mut
from fuzzlab.oracles import gf2

ENGINE = "zero_space"
SEAM = "_analyse"


def _drop_basis_vector(result: Any, args: Tuple[Any, ...],
                       kwargs: Dict[str, Any]) -> Any:
    if not result.basis:
        raise mut.inert("world has no conserved laws; nothing to withhold")
    result.basis = result.basis[:-1]
    return result


def _add_bogus_basis_vector(result: Any, args: Tuple[Any, ...],
                            kwargs: Dict[str, Any]) -> Any:
    n_cols = len(result.features)
    for i in range(n_cols):
        probe = 1 << i
        if not gf2.in_span(probe, result.basis, n_cols):
            result.basis = sorted(result.basis + [probe])
            return result
    raise mut.inert("law space is already everything; no vector lies outside it")


def _flip_law_value(result: Any, args: Tuple[Any, ...],
                    kwargs: Dict[str, Any]) -> Any:
    if not result.laws:
        raise mut.inert("world has no laws to misreport")
    result.laws[0].value ^= 1
    return result


def _drop_law(result: Any, args: Tuple[Any, ...],
              kwargs: Dict[str, Any]) -> Any:
    if not result.laws:
        raise mut.inert("world has no laws to withhold")
    result.laws = result.laws[:-1]
    return result


def _bump_difference_rank(result: Any, args: Tuple[Any, ...],
                          kwargs: Dict[str, Any]) -> Any:
    result.difference_rank += 1
    return result


def _contains_always_true(result: Any, args: Tuple[Any, ...],
                          kwargs: Dict[str, Any]) -> Any:
    if len(result.basis) >= len(result.features):
        raise mut.inert("space is everything; contains() is already always true")
    result.contains = lambda vector: True
    return mut.touched(result)


mut.register(
    mut.Mutant(
        id="zs-drop-basis-vector",
        engine=ENGINE, seam=SEAM, kind=mut.INCOMPLETE,
        claim="the basis spans *exactly* the space of conserved laws -- "
              "engines/zero_space/zerospace.py:analyse returns gf2.null_space "
              "of the difference matrix; props/zero_space.py names completeness "
              "as a separate claim from soundness.",
        description="drop the last vector from result.basis, leaving a strict "
                    "subspace: every law returned is still true, one true law "
                    "is withheld.",
        corrupt=_drop_basis_vector,
        expect_kill=("law_space_is_complete", "rank_nullity"),
    ),
    mut.Mutant(
        id="zs-add-bogus-basis-vector",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="every vector in the basis really is conserved along the "
              "trajectory (soundness half of the same claim).",
        description="append a single-feature vector known by the oracle to lie "
                    "outside the true null space: the engine now asserts a law "
                    "that is false of the world.",
        corrupt=_add_bogus_basis_vector,
        expect_kill=("law_space_is_complete", "rank_nullity"),
    ),
    mut.Mutant(
        id="zs-flip-law-value",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="Law.value is the parity the law actually holds at -- "
              "zerospace.py:Law documents it as the conserved value, and "
              "rendering() prints it as `mod 2 = <value>` into the manual.",
        description="flip the reported value of the first law. The law is still "
                    "conserved; the constant it is conserved *at* is now wrong. "
                    "A manual inheriting this states a false fact with the right "
                    "shape.",
        corrupt=_flip_law_value,
        expect_kill=("laws_hold_on_trajectory",),
    ),
    mut.Mutant(
        id="zs-drop-law",
        engine=ENGINE, seam=SEAM, kind=mut.INCOMPLETE,
        claim="`result.laws` is the set of conservation laws the evidence "
              "supports, and it is what `candidates()` publishes -- "
              "engines/zero_space/__init__.py builds the payload from the laws, "
              "not from the raw basis. A law silently dropped is a true fact "
              "about the world that never reaches the manual.",
        description="drop the last Law, leaving `basis` untouched. NOTE: this "
                    "prediction is POST-HOC. The mutant was written by the "
                    "adversarial reviewer after the first five had already run "
                    "and zero_space had been reported as '0 survivors'. It is "
                    "recorded as post-hoc rather than folded in among the "
                    "pre-registered five, because the whole value of "
                    "pre-registration is lost the moment a result is quietly "
                    "relabelled as a prediction.",
        corrupt=_drop_law,
        predicted_survivor=True,
    ),
    mut.Mutant(
        id="zs-bump-difference-rank",
        engine=ENGINE, seam=SEAM, kind=mut.INCONSISTENT,
        claim="difference_rank is the rank of the difference matrix, and "
              "dimension == n_features - difference_rank (rank-nullity).",
        description="report a difference rank one higher than the truth, so the "
                    "engine's own two numbers no longer add up.",
        corrupt=_bump_difference_rank,
        expect_kill=("rank_nullity",),
    ),
    mut.Mutant(
        id="zs-contains-always-true",
        engine=ENGINE, seam=SEAM, kind=mut.UNSOUND,
        claim="contains(v) is true iff v is in the span of the basis -- "
              "zerospace.py:ZeroSpaceResult.contains delegates to gf2.in_span.",
        description="shadow contains() with a function that says yes to "
                    "everything: the query interface now agrees the world "
                    "conserves quantities it does not.",
        corrupt=_contains_always_true,
        expect_kill=("membership_agrees",),
    ),
)
