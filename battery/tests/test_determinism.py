"""Determinism: same inputs, byte-identical artefacts.

This is what makes a recompute auditable — a reviewer re-runs the battery and
diffs. If the output wobbled, "the numbers changed" would stop being evidence
of anything.

The test runs against the frozen fixture, not the live ledger, because
`baseline-arms/ledger.jsonl` is append-only and another session may be writing
to it between the two runs.
"""

import hashlib
import json
import os

import pytest

from battery.run_battery import main
from battery.tests import make_fixture

ARTEFACTS = ("capability_spectrum.json", "discrimination.json",
             "redundancy.json", "gaming_audit.json")


def _digests(directory):
    out = {}
    for name in ARTEFACTS:
        path = os.path.join(directory, name)
        assert os.path.exists(path), "%s was not written" % name
        with open(path, "rb") as fh:
            out[name] = hashlib.sha256(fh.read()).hexdigest()
    return out


@pytest.fixture(scope="module")
def fixture_path(tmp_path_factory):
    path = os.path.join(str(tmp_path_factory.mktemp("fixture")),
                        "ledger.jsonl")
    make_fixture.write(path)
    return path


def _run(fixture_path, out):
    code = main(["--ledger", fixture_path, "--a0", "none", "--out", out])
    assert code == 0
    return out


def test_two_recomputes_are_byte_identical(fixture_path, tmp_path):
    first = _run(fixture_path, str(tmp_path / "a"))
    second = _run(fixture_path, str(tmp_path / "b"))
    assert _digests(first) == _digests(second)


def test_the_fixture_generator_is_byte_stable(tmp_path):
    a = make_fixture.write(str(tmp_path / "a.jsonl"))
    b = make_fixture.write(str(tmp_path / "b.jsonl"))
    assert open(a, "rb").read() == open(b, "rb").read()


def test_artefacts_carry_no_wall_clock(fixture_path, tmp_path):
    """A timestamp in the output would break byte-identity by construction."""
    out = _run(fixture_path, str(tmp_path / "a"))
    for name in ARTEFACTS:
        with open(os.path.join(out, name), "r", encoding="utf-8") as fh:
            body = fh.read()
        for marker in ("2026-07-2", "generated_at", "timestamp"):
            assert marker not in body, \
                "%s leaks a wall clock via %r" % (name, marker)


def test_artefacts_record_which_inputs_produced_them(fixture_path, tmp_path):
    """Byte-identity is only meaningful if the inputs are identified."""
    out = _run(fixture_path, str(tmp_path / "a"))
    with open(os.path.join(out, "capability_spectrum.json"),
              encoding="utf-8") as fh:
        payload = json.load(fh)
    provenance = payload["provenance"]
    assert provenance["cut"]["piles_sha256"].startswith("3feca53e")
    digests = provenance["input_digests"]
    assert any(v and len(v) == 64 for v in digests.values())


def test_the_fixture_gradient_is_recovered(fixture_path, tmp_path):
    """The fixture encodes a known ordering; the battery should find it.

    A weaker rung revisits states more often by construction, so X1 ("lower is
    better") must separate the ladder in the declared direction. This is the
    discrimination machinery being tested against an answer we planted, which
    is the only way to know it would notice a real one.
    """
    out = _run(fixture_path, str(tmp_path / "a"))
    with open(os.path.join(out, "discrimination.json"), encoding="utf-8") as fh:
        discrimination = json.load(fh)
    x1 = discrimination["metrics"]["X1"]
    assert x1["n_paired_games"] == 4
    assert x1["agrees_with_declared_direction"] is True
    assert x1["magnitude"] in ("medium", "large")
    # ...and the verdict is still `underpowered`, because four paired games
    # cannot reach p<0.05 however cleanly a metric separates.
    assert x1["verdict"] == "underpowered"
    assert x1["sign_test"]["min_attainable_p"] > 0.05
