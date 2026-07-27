"""zero_space -- public entry points."""

from typing import Any, Dict, List, Optional, Sequence

from common.candidates import emit, make_candidate
from engines.zero_space import gf2  # noqa: F401
from engines.zero_space.zerospace import (  # noqa: F401
    Feature,
    Law,
    ZeroSpaceResult,
    analyse,
    build_features,
    cell_local_subspace,
    encode,
    equivalent_modulo_encoding,
    red_parity_vector,
    verify,
)

ENGINE = "zero_space"


def to_payload(law: Law, result: ZeroSpaceResult) -> Dict[str, Any]:
    """The invariant payload shape; frozen in this engine's README."""
    payload = law.as_json()
    payload["space_dimension"] = result.dimension
    payload["difference_rank"] = result.difference_rank
    return payload


def candidates(result: ZeroSpaceResult, timestamp: Optional[str] = None
               ) -> List[Dict[str, Any]]:
    transitions = list(range(result.n_transitions))
    coverage = "%d/%d" % (result.n_transitions, result.n_transitions)
    return [
        make_candidate(
            engine=ENGINE,
            kind="invariant",
            payload=to_payload(law, result),
            transitions=transitions,
            coverage=coverage,
            timestamp=timestamp,
        )
        for law in result.laws
    ]


def run(states: Sequence[Sequence[str]], colors: Sequence[str],
        out_path: Optional[str] = None,
        timestamp: Optional[str] = None) -> ZeroSpaceResult:
    result = analyse(states, colors)
    if not verify(result, states):
        raise AssertionError("a recovered law does not hold on the trajectory")
    if out_path:
        emit(out_path, candidates(result, timestamp=timestamp))
    return result
