"""The metric registry.

A metric is a `Card` — an id, a family, a one-line definition, the run
capabilities it needs, and which direction counts as "more capable" — plus a
function from a `Run` to a `Value`.

Three rules the whole battery leans on:

* **A metric that cannot be computed says so.**  `Value.status` is
  `not-applicable` (the run structurally lacks the input — an arm with no
  books cannot have a theorem count) or `insufficient-data` (the input exists
  but is too thin — a two-step run has no trend), each with a reason string.
  Neither is ever a zero.  A battery that reports zero for "no data" is a
  battery that will eventually be believed.
* **Direction is declared, not inferred.**  Every card says whether higher or
  lower is the more capable reading, so the discrimination pass can check an
  ordering without a human re-deriving it, and a reader cannot quietly flip it
  after seeing the numbers.
* **`neutral` direction means diagnostic.**  Some numbers describe a run
  without ranking it (how much it cost, how many concepts it named).  They are
  kept because they explain the ranked ones, and excluded from any ordering
  claim.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from battery.model import Run

FAMILIES = ("exploration", "planning", "economy", "mechanism", "epistemic")

# Rounding is part of determinism: a float that differs in the last bit between
# two runs would break byte-identical artefacts.  Nine digits is far more
# precision than any of these metrics can support and is well inside the range
# where repr() is stable.
PRECISION = 9


@dataclass(frozen=True)
class Value:
    """One metric on one run."""

    metric_id: str
    value: Optional[float]
    status: str          # ok | not-applicable | insufficient-data
    reason: str = ""
    support: Optional[Dict[str, object]] = None

    @property
    def ok(self) -> bool:
        return self.status == "ok"

    def as_dict(self) -> Dict[str, object]:
        out: Dict[str, object] = {"status": self.status, "value": self.value}
        if self.reason:
            out["reason"] = self.reason
        if self.support:
            out["support"] = self.support
        return out


@dataclass(frozen=True)
class Card:
    """A registered metric."""

    metric_id: str
    family: str
    definition: str
    needs: Tuple[str, ...]
    direction: str            # higher | lower | neutral
    fn: Callable[[Run], Value]
    unit: str = ""

    def as_dict(self) -> Dict[str, object]:
        return {
            "id": self.metric_id,
            "family": self.family,
            "definition": self.definition,
            "needs": list(self.needs),
            "direction": self.direction,
            "unit": self.unit,
        }


REGISTRY: Dict[str, Card] = {}


def ok(metric_id: str, value: float, **support) -> Value:
    return Value(metric_id, round(float(value), PRECISION), "ok",
                 support=support or None)


def na(metric_id: str, reason: str) -> Value:
    """Structurally inapplicable — the run cannot have this input at all."""
    return Value(metric_id, None, "not-applicable", reason)


def thin(metric_id: str, reason: str) -> Value:
    """The input exists but is too thin to support the number."""
    return Value(metric_id, None, "insufficient-data", reason)


_NEED_REASONS = {
    "steps": "the run records no environment steps",
    "observations": "no step carries an observation to identify a state by",
    "model_calls": "the run records no model calls",
    "cost": "no model call carries a cost",
    "theory": "this arm keeps no explicit theory",
    "truth": "no ground truth is available for this run",
    "optimal": "no optimal plan length is known",
    "mechanisms": "this run carries no mechanism annotation",
    "solve_attempt": "this trace is a coverage walk, not an attempt to win; "
                     "scoring it for path efficiency would measure the "
                     "trace's purpose rather than the arm",
    "won": "this run never reached the goal, and path efficiency has no floor "
           "-- a run that gives up on step one scores better than any solve, "
           "so scoring a loss would rank failure as excellence",
    "repairs": "this arm records no repair episode; an arm with no manual "
               "cannot be refuted by one, so the absence is structural",
    "prompt_chars": "no model call records the size of the prompt it was sent",
    "http_tries": "the source records no HTTP attempt count per step",
    "failed_steps": "no step in this run failed, so there is no failure to "
                    "respond to",
}


def metric(metric_id: str, family: str, definition: str, *,
           needs: Sequence[str] = (), direction: str = "higher",
           unit: str = "") -> Callable:
    """Register a metric.  The wrapper enforces `needs` before the body runs."""
    if family not in FAMILIES:
        raise ValueError("unknown family %r" % family)
    if direction not in ("higher", "lower", "neutral"):
        raise ValueError("unknown direction %r" % direction)

    def decorate(fn: Callable[[Run], Value]) -> Callable[[Run], Value]:
        def guarded(run: Run) -> Value:
            caps = run.capabilities()
            for need in needs:
                if not caps.get(need):
                    return na(metric_id, _NEED_REASONS.get(
                        need, "missing input %r" % need))
            return fn(run)

        REGISTRY[metric_id] = Card(
            metric_id=metric_id, family=family, definition=definition,
            needs=tuple(needs), direction=direction, fn=guarded, unit=unit)
        return guarded

    return decorate


def evaluate(run: Run) -> Dict[str, Value]:
    """Every registered metric, on one run."""
    return {mid: REGISTRY[mid].fn(run) for mid in sorted(REGISTRY)}


def r2(ys: Sequence[float], fitted: Sequence[float]) -> float:
    """Coefficient of determination, guarded against a constant series."""
    mean = sum(ys) / len(ys)
    ss_tot = sum((y - mean) ** 2 for y in ys)
    ss_res = sum((y - f) ** 2 for y, f in zip(ys, fitted))
    if ss_tot <= 0:
        # A perfectly flat series is explained exactly by any model with an
        # intercept; reporting 1.0 would make "no growth" look like a great
        # quadratic fit, so it is reported as no explanatory power instead.
        return 0.0
    return 1.0 - ss_res / ss_tot


def polyfit_r2(xs: Sequence[float], ys: Sequence[float], degree: int) -> float:
    """R^2 of a least-squares polynomial fit, via normal equations.

    Hand-rolled rather than numpy so the arithmetic is identical on every
    machine; determinism outranks convenience here, and these are tiny fits.
    """
    n = len(xs)
    if n <= degree + 1:
        return 0.0
    # Normal equations for the Vandermonde system, solved by Gaussian
    # elimination with partial pivoting.
    size = degree + 1
    a = [[sum(x ** (i + j) for x in xs) for j in range(size)]
         for i in range(size)]
    b = [sum(y * (x ** i) for x, y in zip(xs, ys)) for i in range(size)]
    for col in range(size):
        pivot = max(range(col, size), key=lambda r_: abs(a[r_][col]))
        if abs(a[pivot][col]) < 1e-12:
            return 0.0
        a[col], a[pivot] = a[pivot], a[col]
        b[col], b[pivot] = b[pivot], b[col]
        for row in range(col + 1, size):
            factor = a[row][col] / a[col][col]
            for k in range(col, size):
                a[row][k] -= factor * a[col][k]
            b[row] -= factor * b[col]
    coeffs = [0.0] * size
    for row in range(size - 1, -1, -1):
        acc = b[row] - sum(a[row][k] * coeffs[k] for k in range(row + 1, size))
        coeffs[row] = acc / a[row][row]
    fitted = [sum(c * (x ** i) for i, c in enumerate(coeffs)) for x in xs]
    value = r2(ys, fitted)
    return value if math.isfinite(value) else 0.0


# Importing the family modules is what populates REGISTRY.
from battery.metrics import (  # noqa: E402,F401  (import for side effect)
    economy, epistemic, exploration, mechanism, planning,
)


def cards_by_family() -> Dict[str, List[Card]]:
    out: Dict[str, List[Card]] = {f: [] for f in FAMILIES}
    for mid in sorted(REGISTRY):
        card = REGISTRY[mid]
        out[card.family].append(card)
    return out
