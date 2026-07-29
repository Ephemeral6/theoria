"""One shape for everything a property run can report.

A property module returns *findings*, never assertions, so that the campaign can
run 500 worlds to completion and rank what it saw rather than stopping at the
first one.  The pytest wrappers turn a non-empty list into a failure; the
campaign writes it to disk.  Same data either way.

Three kinds, and keeping them apart matters:

* `violated` -- the invariant is false.  The engine did something it says it
  does not do.
* `raised`   -- an exception escaped the property.  Every *documented* outcome
  is caught at its property and turned into a `skipped` with a cause, so what
  reaches `raised` is by construction an exception nobody wrote a policy for.
  It is a failure (see `failures`).
* `skipped`  -- the property could not be evaluated on this world, with the
  reason **and a declared `cause`** recorded.  A campaign that silently drops
  the worlds its oracle cannot handle reports a coverage number it did not earn.

## Why `skipped` is not one bucket (V-21)

`skipped` used to be a single integer covering two questions that have opposite
answers, and `lp_potential` is where that bit.  "The engine looked and correctly
has nothing to say about this configuration" is the battery working.  "HiGHS ran
out of iterations, so nobody knows" is the battery *not* working, on a world it
will then go on to describe as covered.  Reported as one number they cancel.

So every `skipped` carries a `cause`, every cause is declared in `CAUSE_CLASS`,
and the classes are three rather than two:

* `declined`    -- a fact about the configuration or the evidence.  The property
  had nothing to judge and that is the correct state of the world.  Expected to
  be large; `lp_potential` declines on ~47% of `jumpgraph` worlds by design.
* `budget`      -- *this battery* declined, on a cost threshold it chose in
  advance and can quote.  Expected to be non-zero.  The world is judgeable; we
  chose not to pay for it.
* `unavailable` -- a tool did not compute: a solver limit, an unbounded
  relaxation, numerical difficulties.  Nobody knows what the answer was.
  Expected to be **zero**, and `tests/test_battery.py` fails the suite when it is
  not, because a run with a non-zero `unavailable` did not measure what it says
  it measured.

`budget` and `unavailable` are kept apart on purpose.  Both are facts about the
tooling rather than the world, and lumping them would put a designed, routine,
priced decline into the same column as a solver failure -- which would make the
`unavailable` gate red on a green tree, and a gate whose failures are mostly
false is a gate people learn to ignore (`tests/test_finding_contract.py`).
"""

import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

VIOLATED = "violated"
RAISED = "raised"
SKIPPED = "skipped"

# ------------------------------------------------------------ skip taxonomy

DECLINED = "declined"
BUDGET = "budget"
UNAVAILABLE = "unavailable"

CAUSE_CLASSES = (DECLINED, BUDGET, UNAVAILABLE)

#: Every cause any property may file, and which of the three it is.  The table
#: is the classification; nothing re-derives it from the reason string.  A cause
#: not listed here is a `ValueError` at the call site rather than a new silent
#: bucket -- adding a way for a world to go unjudged is exactly the change that
#: has to be visible in a diff.
CAUSE_CLASS: Dict[str, str] = {
    # --- cegis_miner
    "unminable": DECLINED,
    "no_separating_guard": DECLINED,
    "no_transitions": DECLINED,
    "mover_path_not_fixed_by_pixels": DECLINED,
    "mined_track_is_not_the_mover": DECLINED,
    "evidence_not_alignable": DECLINED,
    "effects_not_readable_as_translation": DECLINED,
    "frontier_size_over_budget": BUDGET,
    # --- fd_adapter
    "pddl_error": DECLINED,
    "ground_bfs_budget": BUDGET,
    # --- zero_space
    "no_states": DECLINED,
    "feature_sweep_over_budget": BUDGET,
    # --- lp_potential
    "no_certificate": DECLINED,
    "certificate_error": DECLINED,
    "no_state_list": DECLINED,
    "sweep_budget": BUDGET,
    "bfs_budget": BUDGET,
    # The one this taxonomy was built for.  `engines.lp_potential` raises
    # `LpUnavailable` for HiGHS status 1/3/4 (E-15) -- an iteration limit, an
    # unbounded relaxation, numerical difficulties.  None of the three says
    # anything about the configuration, so the property has not judged the world;
    # and unlike `no_certificate` it is not the engine correctly declining, so it
    # must not be counted beside it.
    "solver_unavailable": UNAVAILABLE,
}


def cause_class(cause: str) -> str:
    """Which of the three a cause is.  Unknown causes are an error, not a class."""
    try:
        return CAUSE_CLASS[cause]
    except KeyError:
        raise ValueError(
            "undeclared skip cause %r -- add it to finding.CAUSE_CLASS with the "
            "class it belongs to (%s). A cause that classifies itself is a "
            "bucket nobody reviewed." % (cause, ", ".join(CAUSE_CLASSES))
        ) from None


@dataclass
class Finding:
    engine: str
    invariant: str
    kind: str                                  # violated | raised | skipped
    family: str
    seed: int
    detail: str
    data: Dict[str, Any] = field(default_factory=dict)
    #: For `skipped`, a cause declared in `CAUSE_CLASS`.  For `raised`, the
    #: exception's type name -- useful for triage, and deliberately *not* run
    #: through `CAUSE_CLASS`, because the whole point of `raised` is that it is
    #: the bucket nobody has classified yet.  Empty for `violated`, where the
    #: invariant name is the cause.
    cause: str = ""

    @property
    def cause_class(self) -> str:
        """`declined` / `budget` / `unavailable`, or "" where a cause is not a skip."""
        return cause_class(self.cause) if self.kind == SKIPPED else ""

    def json(self) -> Dict[str, Any]:
        return {
            "engine": self.engine,
            "invariant": self.invariant,
            "kind": self.kind,
            "family": self.family,
            "seed": self.seed,
            "seed_hex": "0x%016x" % self.seed,
            "detail": self.detail,
            "cause": self.cause,
            "cause_class": self.cause_class,
            "data": self.data,
        }

    def __str__(self) -> str:
        tag = "%s/%s" % (self.kind, self.cause) if self.cause else self.kind
        return "[%s] %s.%s seed=0x%016x -- %s" % (
            tag, self.engine, self.invariant, self.seed, self.detail
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
        cause=type(exc).__name__,
    )


def skipped(engine: str, invariant: str, world: Any, reason: str,
            *, cause: str, **data: Any) -> Finding:
    """A world this invariant did not judge, with the reason and a declared cause.

    `cause` is keyword-only and **required**.  It was a convention before V-21 --
    6 of 20 call sites carried one -- and a convention adhered to 30% of the time
    is not a column anyone can read.  Making it a parameter means a new skip
    cannot be added without deciding, in the same edit, which of the three
    classes it is; making it keyword-only means it can never be swallowed by
    `**data` the way it used to be.
    """
    cause_class(cause)              # raises on an undeclared cause
    return Finding(
        engine=engine, invariant=invariant, kind=SKIPPED,
        family=world.family, seed=world.seed, detail=reason, data=data,
        cause=cause,
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
    """The findings that make a test fail: violations **and** unexpected raises.

    Until V-21 this sentence was the docstring and the body returned `VIOLATED`
    alone.  The prose was the wider of the two, which is the dangerous direction:
    a reader -- or the first person to import this -- would conclude that a
    property crashing fails the suite, and it did not.  The two are now the same
    claim, and the code moved rather than the prose.  Both directions were live
    and the argument for each is in
    `runs/20260729T104608Z-V21-lp-unavailable-is-not-a-pass/PREREGISTRATION.md` §2;
    the short form:

    * **`raised` is `unexpected` by construction.**  Every documented outcome in
      this battery is caught at its property and converted to a `skipped` with a
      cause -- `NoSeparatingGuard`, `CertificateError`, `PddlError`, an unminable
      segmentation, and since V-21 `LpUnavailable`.  So an exception that reaches
      `raised` is one nobody wrote a policy for.  That is what "unexpected"
      meant, and the body was ignoring the word.
    * **`raised` is measured at zero on a green tree**, across all six engines,
      before this widened.  Widening a gate whose input is already zero cannot
      turn a green tree red for a documented outcome.
    * **Narrowing the prose instead would have ratified the bug.**
      `tests/test_finding_contract.py` records an incident in which a dead
      reporting path turned every violation into a `raised` while the headline
      "0 violations" stayed true.  Editing this docstring down to "violations
      only" would write *a crashing property is not a failure* into the contract
      on purpose, in the same battery.

    `skipped` is deliberately still not a failure: a world nobody judged is not a
    world the engine got wrong.  It is accounted for instead in the coverage
    column, by cause and cause-class (`campaign.py`), and the `unavailable` class
    has its own gate in `tests/test_battery.py`.  Those are different questions
    and this function answers only one of them.
    """
    return [f for f in findings if f.kind in (VIOLATED, RAISED)]
