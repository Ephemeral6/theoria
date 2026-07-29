"""What an attacker submits.

One `Attack` is one claim: *this `Run` reaches the metric's pre-registered
threshold while the thing that built it did no work at all.*  Both halves are
recomputed by the harness — `value` comes from `battery.metrics.evaluate`, and
the poverty certificate comes from `battery/audit/v9/check.py` reading the
builder's own source — so neither can be asserted by the author.

That is the one lesson `battery/audit/exploits/` had to learn twice: a
`succeeded` flag an author can type is not a finding.  Here the author types
only `claim`, `accidental` and `rationale`; every field a verdict depends on is
derived.

`build_low` exists for the diagnostics.  A metric that declares no direction
has no "better", so the attack on it is *controllability*: two poverty-certified
runs whose value differs by an order of magnitude at the attacker's whim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from battery.model import Run


@dataclass(frozen=True)
class Attack:
    """One blind attack on one metric."""

    metric_id: str
    # Short slug, unique within a module.  Appears in the artefact.
    name: str
    # Zero-argument, deterministic, poverty-certified.  See check.py.
    build: Callable[[], Run]
    # One line: what score this reaches, and what capability it lacks.
    claim: str
    # Could a real arm land here *without trying*?  Must be argued from
    # something concrete; the argument goes in `rationale`.
    accidental: bool
    rationale: str
    # Diagnostics only: the second run, for the controllability test.
    build_low: Optional[Callable[[], Run]] = None
    # Diagnostics used as another metric's defence: what reading the attacker
    # declares "benign", fixed at submission time.
    benign_window: str = ""
    # Free notes from the attacker, carried into the artefact verbatim.
    notes: dict = field(default_factory=dict)
