"""Regression: the build's acceptance conditions used to be decorations.

Every gate below was already *computed* and printed by the previous version of
`worldgen/build.py`, which then returned 0 regardless.  Seven of twenty worlds
shipped with `claim_disagreements` and one with a violated invariant, and because
the noise was constant nobody could have distinguished a real disagreement from
it — a measurement nothing can fail is worse than no measurement, because it
looks like one.

So the gate is exercised in both directions.  The synthetic manifests below
violate each gate in turn and must be *reported*; and the real
`INDEX.json`, if the catalogue has been built, must come back green.  The second
half is not redundant: `gate_failures` reads `manifest["totals"]` by key name, so
a gate keyed on a string the real manifest never emits would pass every synthetic
test in this file and still gate nothing.
"""

import json
import os

import pytest

from worldgen import build
from worldgen.tests import support

GATE_KEYS = tuple(key for key, _why in build.GATES)


def _manifest(**totals):
    base = {key: [] for key in GATE_KEYS}
    base.update(totals)
    return {"prompt_id": "test", "worlds": [], "totals": base}


def test_the_named_gates_are_all_present():
    """Named individually rather than compared as a set: a gate added later is a
    tightening and should not fail this, but a gate *dropped* is exactly the
    regression, and a set comparison could not tell the two apart."""
    for key in ("solvability_intent_failures", "rule_correspondence_failures",
                "invariant_failures", "claim_disagreements", "frame_collisions"):
        assert key in GATE_KEYS, "the build no longer gates on %r" % key


def test_a_clean_manifest_reports_nothing():
    assert build.gate_failures(_manifest()) == []


@pytest.mark.parametrize("key", GATE_KEYS)
def test_each_gate_can_fail_on_its_own(key):
    failures = build.gate_failures(_manifest(**{key: ["w-bad"]}))
    assert len(failures) == 1, failures
    assert "w-bad" in failures[0]
    assert key in failures[0], (
        "the failure line does not name the gate that produced it: %r" % failures[0])


def test_every_gate_fails_together():
    failures = build.gate_failures(
        _manifest(**{key: ["w-%d" % i] for i, key in enumerate(GATE_KEYS)}))
    assert len(failures) == len(GATE_KEYS), failures
    for key in GATE_KEYS:
        assert any(key in line for line in failures), key


def test_a_gate_reports_every_offending_world():
    failures = build.gate_failures(_manifest(invariant_failures=["w-a", "w-b", "w-c"]))
    assert len(failures) == 3, failures


def test_the_shipped_catalogue_passes_its_own_gate():
    """The keys the synthetic manifests use are the keys `build_all` really emits."""
    path = os.path.join(support.OUT, "INDEX.json")
    if not os.path.exists(path):
        pytest.skip("no shipped INDEX.json — run `python -m worldgen.build`")
    with open(path, encoding="utf-8") as handle:
        manifest = json.load(handle)
    for key in GATE_KEYS:
        assert key in manifest["totals"], (
            "gate %r reads a key the real manifest does not emit" % key)
    assert build.gate_failures(manifest) == []
