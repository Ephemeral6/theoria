"""The gate, including the thing a gate must be able to do: refuse.

`verify.py` reads artefacts and turns them into a verdict, so its failure mode
is the quiet one — a gate that says GREEN because it looked at the wrong field,
or because a missing field defaulted to the value it wanted. Both are tested by
doctoring the artefacts rather than by reading the code.
"""

from __future__ import annotations

import copy
import json
import os

import pytest

from _armimport import arm_module

ARM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Loaded by path, not by name. A plain ``import verify`` resolves to
#: ``cold-start-a2/verify.py``: ``_bootstrap`` puts the upstream roots ahead of
#: this arm on ``sys.path``, and S14 (127edab) gave eleven territories a
#: top-level ``verify.py`` seventy-five minutes after these tests were written.
#: ``tests/test_no_shadow.py`` is the guard that fails when that set grows.
verify = arm_module("verify")


@pytest.fixture(scope="module")
def artefacts():
    """The three files the gate reads. Loaded once; each test copies."""
    def load(*parts):
        with open(os.path.join(ARM, *parts), encoding="utf-8") as handle:
            return json.load(handle)
    return (load("artifacts", "run_all.json"),
            load("artifacts", "exhibits.json"),
            load("theory", "DOWNGRADE_REPORT.json"))


def _claims(artefacts):
    return {c["name"]: c for c in verify._assertions(*artefacts)}


def test_the_gate_is_green_on_what_the_arm_actually_produced(artefacts):
    claims = _claims(artefacts)
    failed = [name for name, c in claims.items() if not c["holds"]]
    assert failed == [], failed
    assert set(claims) == {"P-3", "P-5(correct)", "P-6", "P-7",
                           "shadow-1", "shadow-2", "shadow-3", "shadow-4",
                           "read-only", "P-1(counts)"}


def test_every_claim_states_itself_and_shows_its_evidence(artefacts):
    """A gate whose assertions cannot be read is a gate nobody will trust when
    it goes red."""
    for name, claim in _claims(artefacts).items():
        assert len(claim["claim"]) > 40, name
        assert claim["evidence"], name


@pytest.mark.parametrize("path,value,expected_red", [
    (("surprise_kinds_available_to_this_arm",), 7, ["P-3", "shadow-4"]),
    (("loop_turned_on",), ["a2-holed"], ["P-7"]),
    (("upstream_unchanged",), False, ["read-only"]),
    (("pre_registered_holds",), False, ["P-1(counts)"]),
])
def test_the_gate_refuses_when_the_run_says_otherwise(artefacts, path, value,
                                                      expected_red):
    run_all, exhibits, cut = artefacts
    doctored = copy.deepcopy(run_all)
    node = doctored
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    claims = {c["name"]: c for c in verify._assertions(doctored, exhibits, cut)}
    red = sorted(name for name, c in claims.items() if not c["holds"])
    assert red == sorted(expected_red), (path, red)


def test_a_missing_field_is_not_read_as_the_value_the_gate_wants(artefacts):
    """The bug the gate shipped with for one run.

    `directed_probes_scheduled` is absent on a SAT world -- there is no
    impossibility claim to certify -- and the first version read that absence as
    a failure. The repair was *not* to default it to 0, because then a run in
    which the field vanished from an UNSAT world would pass.
    """
    run_all, exhibits, cut = artefacts
    doctored = copy.deepcopy(run_all)
    unsat = [k for k, w in doctored["worlds"].items()
             if w["beats"]["plan"]["status"] == "UNSAT"]
    assert unsat, "no UNSAT world; this test has nothing to remove a field from"
    del doctored["worlds"][unsat[0]]["beats"]["plan"]["directed_probes_scheduled"]
    claims = {c["name"]: c for c in verify._assertions(doctored, exhibits, cut)}
    assert claims["shadow-1"]["holds"] is False
    assert claims["P-7"]["holds"] is False


def test_a_recorded_number_can_never_turn_the_gate_red(artefacts):
    """The split A4a depends on. If a recorded prediction could fail the gate,
    the next person to run it would be under pressure to invent the second
    arm's numbers."""
    run_all, exhibits, cut = artefacts
    recorded = verify._recorded(run_all, exhibits)
    assert set(recorded) == {"P-1", "P-2", "P-4", "P-5(identical)", "E3"}
    asserted = {c["name"] for c in verify._assertions(run_all, exhibits, cut)}
    for name in ("P-1", "P-2", "P-4", "P-5(identical)"):
        assert name not in asserted, (
            "%s is both recorded and asserted; one of them is wrong" % name)
    for name, entry in recorded.items():
        assert entry["status"].startswith(("RECORDED", "NOT CONSTRUCTIBLE"))
        assert entry["what"]


def test_the_recorded_half_names_the_instruments_that_do_not_exist(artefacts):
    """P-2 and P-4 are not merely uncompared -- nothing in this arm measures
    them at all. A4b reading `RECORDED` and expecting numbers would lose a day
    finding that out."""
    recorded = verify._recorded(*artefacts[:2])
    assert recorded["P-2"]["numbers"] is None
    assert "nothing in this arm computes" in recorded["P-2"]["status"]
    assert "no cost instrument" in recorded["P-4"]["status"]


def test_the_gate_reports_e3_without_failing_on_it(artefacts):
    run_all, exhibits, cut = artefacts
    recorded = verify._recorded(run_all, exhibits)
    assert recorded["E3"]["status"].startswith("NOT CONSTRUCTIBLE")
    claims = {c["name"] for c in verify._assertions(run_all, exhibits, cut)}
    assert not any(name.startswith("E3") for name in claims)
