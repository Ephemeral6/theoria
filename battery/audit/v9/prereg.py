"""The frozen pre-registration: thresholds, and the rule that made them.

Committed before any attack ran.  `battery/PREREG_V9.md` is the prose; this is
the part a program can check.  Nothing here may be edited after the attack
commits land — a later change is an amendment, appended and dated, never an
edit in place.

The table is *generated from the rule* rather than hand-picked per metric, so
"the threshold was chosen to make my attack succeed" is not available as an
explanation.  `TARGET_RULE` records which band each metric fell in.
"""

from __future__ import annotations

from typing import Dict, Optional

# Which band of §1.2's rule each metric falls in.  The band decides the number;
# the number is not chosen per metric.
BAND: Dict[str, str] = {
    # exploration
    "X1": "unit-lower", "X2": "unit-higher", "X3": "signed-unit-higher",
    "X4": "unit-lower", "X5": "neutral", "X6": "unit-higher",
    # planning
    "P1": "rate-higher", "P2": "trend-higher", "P3": "unit-lower",
    "P4": "ratio-optimal-one", "P5": "neutral",
    # economy
    "E1": "neutral", "E2": "unit-higher", "E3": "unit-lower",
    "E4": "nonneg-lower", "E5": "ratio-lower", "E6": "neutral",
    "E7": "nonneg-lower",
    # mechanism
    "M1": "ratio-lower", "M2": "unit-higher", "M3": "ratio-lower",
    "M4": "ratio-lower", "M5": "unit-higher", "M6": "neutral",
    # epistemic
    "K1": "unit-higher", "K2": "unit-higher", "K3": "count-higher",
    "K4": "unit-higher", "K5": "count-higher", "K6": "bits-higher",
    "K7": "neutral", "K8": "unit-higher", "K9": "count-higher",
    "K10": "count-higher", "K11": "neutral", "K12": "unit-higher",
    "K13": "ratio-lower", "K14": "bits-higher",
}

# §1.2 of PREREG_V9.md, verbatim as numbers.
BAND_TARGET: Dict[str, Optional[float]] = {
    "unit-higher": 0.95,
    "unit-lower": 0.05,
    "signed-unit-higher": 0.90,
    "nonneg-lower": 0.001,
    "count-higher": 100.0,
    "bits-higher": 1000.0,
    "ratio-lower": 0.001,
    "ratio-optimal-one": 1.0,
    "rate-higher": 50.0,
    "trend-higher": 10.0,
    "neutral": None,
}

TARGETS: Dict[str, Optional[float]] = {
    metric_id: BAND_TARGET[band] for metric_id, band in BAND.items()
}

# §1.1 — controllability, for the metrics that declare no direction.
NEUTRAL_RATIO = 10.0
NEUTRAL_ABSOLUTE = 10.0

# §4 — the aggregator's own directional predictions, written before results.
# Kept here as data so the report cannot quietly drop the ones that were wrong.
PREDICTIONS = [
    ("V9-P1", "at least 3 of the 9 current main-table metrics fall to a blind "
              "attack (main = E2 E3 K7 K11 K12 M3 M6 P3 P4)"),
    ("V9-P2", "the blind attacks disagree with battery/audit/exploits/ on at "
              "least 5 metrics"),
    ("V9-P3", "K12 falls: beats_required is fixed at 6 but the beat list comes "
              "from the source, so six closed beats can simply be asserted"),
    ("V9-P4", "M3 and K7 come back not-gameable for want of computability "
              "rather than for robustness"),
    ("V9-P5", "P4's `won` gate stops the old attack and not a new one: `won` "
              "is a bool on Step and can be set"),
]


def target_for(metric_id: str) -> Optional[float]:
    return TARGETS.get(metric_id)


def meets(metric_id: str, direction: str, value: Optional[float]) -> bool:
    """§1 S2 — does this value reach the pre-registered threshold?"""
    if value is None:
        return False
    target = TARGETS.get(metric_id)
    if target is None:            # neutral: handled by controllability
        return False
    if direction == "higher":
        return value >= target
    if direction == "lower":
        return value <= target
    return False


def controllable(lo: Optional[float], hi: Optional[float]) -> bool:
    """§1.1 — two poverty-certified runs whose diagnostic differs at will."""
    if lo is None or hi is None:
        return False
    low, high = (lo, hi) if lo <= hi else (hi, lo)
    if high >= NEUTRAL_RATIO * max(abs(low), 1e-9):
        return True
    return abs(high - low) >= NEUTRAL_ABSOLUTE
