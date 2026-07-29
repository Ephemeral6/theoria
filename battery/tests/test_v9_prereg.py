"""The pre-registration and the poverty certificate are themselves testable.

Two things are checked here and they are different in kind:

* the pre-registration is **frozen** — every registered metric has a band, the
  band decides the number, and no metric carries a hand-picked threshold.  This
  is what makes "the threshold was chosen to fit the attack" unavailable as an
  explanation.
* the certificate **rejects work** — a builder that searches, reads a file or
  varies between calls must fail.  A checker nobody tries to fool is a checker
  that passes everything.
"""

from __future__ import annotations

import pytest

from battery.audit.v9 import prereg
from battery.audit.v9.check import certificate
from battery.metrics import REGISTRY
from battery.model import Run, Step


# --- the pre-registration is frozen ---------------------------------------

def test_every_registered_metric_has_a_band():
    assert set(prereg.BAND) == set(REGISTRY)


def test_every_threshold_comes_from_its_band():
    for metric_id, band in prereg.BAND.items():
        assert prereg.TARGETS[metric_id] == prereg.BAND_TARGET[band], metric_id


def test_neutral_metrics_carry_no_threshold():
    for metric_id, card in REGISTRY.items():
        if card.direction == "neutral":
            assert prereg.TARGETS[metric_id] is None, metric_id
        else:
            assert prereg.TARGETS[metric_id] is not None, metric_id


def test_meets_respects_direction():
    assert prereg.meets("X2", "higher", 0.96)
    assert not prereg.meets("X2", "higher", 0.94)
    assert prereg.meets("X1", "lower", 0.04)
    assert not prereg.meets("X1", "lower", 0.06)
    assert not prereg.meets("X1", "lower", None)


def test_controllability_needs_an_order_of_magnitude():
    assert prereg.controllable(1.0, 10.0)
    assert not prereg.controllable(1.0, 9.0)
    assert prereg.controllable(100.0, 111.0)      # absolute limb
    assert not prereg.controllable(None, 10.0)


# --- the certificate rejects work -----------------------------------------

def _trivial() -> Run:
    return Run(run_id="t", arm="a", source="v9",
               steps=[Step(idx=i, action="a", state_key="s%d" % i)
                      for i in range(4)])


def test_a_laid_out_run_certifies():
    cert = certificate(_trivial)
    assert cert["ok"], cert["violations"]


def test_a_searching_builder_is_refused():
    def searching() -> Run:
        i = 0
        while i < 4:
            i += 1
        return Run(run_id="t", arm="a", source="v9")

    cert = certificate(searching)
    assert not cert["ok"]
    assert any(v.startswith("C3") for v in cert["violations"])


def test_a_builder_that_reads_a_file_is_refused():
    def reads() -> Run:
        handle = open(__file__)          # noqa: SIM115
        handle.close()
        return Run(run_id="t", arm="a", source="v9")

    cert = certificate(reads)
    assert not cert["ok"]
    assert any(v.startswith("C2") for v in cert["violations"])


def test_a_nondeterministic_builder_is_refused():
    counter = {"n": 0}

    def drifting() -> Run:
        counter["n"] += 1
        return Run(run_id="t%d" % counter["n"], arm="a", source="v9")

    cert = certificate(drifting)
    assert not cert["ok"]
    assert any(v.startswith("C1") for v in cert["violations"])


def test_a_builder_calling_an_unlisted_helper_is_refused():
    def helper() -> int:
        return 3

    def leaning() -> Run:
        return Run(run_id="t", arm="a", source="v9",
                   steps=[Step(idx=helper(), action="a", state_key="s")])

    cert = certificate(leaning)
    assert not cert["ok"]
    assert any("helper" in v for v in cert["violations"])


def test_smuggled_ground_truth_in_notes_is_refused():
    def smuggler() -> Run:
        return Run(run_id="t", arm="a", source="v9",
                   notes={"optimal_plan": [1, 2, 3]})

    cert = certificate(smuggler)
    assert not cert["ok"]
    assert any(v.startswith("C4") for v in cert["violations"])


@pytest.mark.parametrize("prediction", prereg.PREDICTIONS)
def test_predictions_are_recorded_with_an_id(prediction):
    identifier, text = prediction
    assert identifier.startswith("V9-P")
    assert len(text) > 30
