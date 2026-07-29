"""One shape for everything a property run can report.

A property module returns *findings*, never assertions, so that the campaign can
run 500 worlds to completion and rank what it saw rather than stopping at the
first one.  The pytest wrappers turn a non-empty list into a failure; the
campaign writes it to disk.  Same data either way.

Three kinds, and keeping them apart matters:

* `violated` -- the invariant is false.  The engine did something it says it
  does not do.
* `raised`   -- the engine raised where the property expected an answer.  An
  exception is not automatically a defect (`NoSeparatingGuard` and
  `CertificateError` are documented outcomes) so these are collected and
  triaged, not asserted on.
* `skipped`  -- the property could not be evaluated on this world, with the
  reason recorded.  A campaign that silently drops the worlds its oracle cannot
  handle reports a coverage number it did not earn.
"""

import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

VIOLATED = "violated"
RAISED = "raised"
SKIPPED = "skipped"


@dataclass
class Finding:
    engine: str
    invariant: str
    kind: str                                  # violated | raised | skipped
    family: str
    seed: int
    detail: str
    data: Dict[str, Any] = field(default_factory=dict)

    def json(self) -> Dict[str, Any]:
        return {
            "engine": self.engine,
            "invariant": self.invariant,
            "kind": self.kind,
            "family": self.family,
            "seed": self.seed,
            "seed_hex": "0x%016x" % self.seed,
            "detail": self.detail,
            "data": self.data,
        }

    def __str__(self) -> str:
        return "[%s] %s.%s seed=0x%016x -- %s" % (
            self.kind, self.engine, self.invariant, self.seed, self.detail
        )


def violated(engine: str, invariant: str, world: Any, detail: str,
             **data: Any) -> Finding:
    return Finding(
        engine=engine, invariant=invariant, kind=VIOLATED,
        family=world.family, seed=world.seed, detail=detail, data=data,
    )


def raised(engine: str, invariant: str, world: Any, exc: BaseException) -> Finding:
    return Finding(
        engine=engine, invariant=invariant, kind=RAISED,
        family=world.family, seed=world.seed,
        detail="%s: %s" % (type(exc).__name__, exc),
        data={"traceback": traceback.format_exc(limit=8)},
    )


def skipped(engine: str, invariant: str, world: Any, reason: str,
            **data: Any) -> Finding:
    return Finding(
        engine=engine, invariant=invariant, kind=SKIPPED,
        family=world.family, seed=world.seed, detail=reason, data=data,
    )


def run_invariants(engine: str, world: Any,
                   invariants: Dict[str, Callable[[Any], List[Finding]]],
                   only: Optional[List[str]] = None) -> List[Finding]:
    """Run each invariant, converting an escaping exception into a `raised`.

    Every invariant runs even after an earlier one fails: on a single world the
    invariants are independent questions, and answering only the first one makes
    triage guess at the rest.
    """
    out: List[Finding] = []
    for name, fn in invariants.items():
        if only is not None and name not in only:
            continue
        try:
            out.extend(fn(world))
        except Exception as exc:                        # noqa: BLE001
            out.append(raised(engine, name, world, exc))
    return out


def failures(findings: List[Finding]) -> List[Finding]:
    """The findings that make a test fail: violations and unexpected raises."""
    return [f for f in findings if f.kind == VIOLATED]
