"""S20: a gate nobody has ever made fail is indistinguishable from one that works.

Adopted from the audit's advice on S13. A completion gate that has never been
shown to go red is not evidence about the territory -- it is evidence that
nothing has broken *yet*, and those look identical until the day they do not.

The mechanism is a declaration, not a sniff: the gate script names the test that
manufactures its red, on a line of its own. Guessing from filenames would let a
gate acquire a negative sample by someone naming a file well, and would miss
every real one named something else.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import gates                                                    # noqa: E402


def _territory(tmp_path, gate_body, sample=None):
    root = tmp_path / "repo"
    terr = root / "terr"
    terr.mkdir(parents=True)
    (terr / "verify.sh").write_text(gate_body, encoding="utf-8")
    if sample:
        p = root / sample
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("def test_x():\n    assert True\n", encoding="utf-8")
    return str(root)


def test_a_gate_declaring_a_sample_that_exists_is_not_decorative(tmp_path):
    root = _territory(tmp_path,
                      "#!/bin/sh\n# negative-sample: t/test_red.py\nexit 0\n",
                      sample="t/test_red.py")
    row = gates.gate_for(root, "terr")
    assert row["kind"] == "verify"
    assert row["decorative"] is False, row
    assert row["negative_sample"]["declared"] == "t/test_red.py"


def test_a_gate_declaring_nothing_is_decorative(tmp_path):
    root = _territory(tmp_path, "#!/bin/sh\nexit 0\n")
    row = gates.gate_for(root, "terr")
    assert row["decorative"] is True, row
    assert row["negative_sample"] is None
    assert "negative sample" in row["why"]


def test_a_declaration_pointing_at_nothing_does_not_count(tmp_path):
    """The claim has to be to a file that landed.

    Otherwise the cheapest way to clear the check is to declare a path and never
    write it -- which is the same shape as the defect being fixed.
    """
    root = _territory(tmp_path,
                      "#!/bin/sh\n# negative-sample: t/never_written.py\nexit 0\n")
    row = gates.gate_for(root, "terr")
    assert row["decorative"] is True, row
    assert row["negative_sample"]["exists"] is False


def test_a_nodeid_suffix_is_accepted(tmp_path):
    root = _territory(
        tmp_path,
        "#!/bin/sh\n# negative-sample: t/test_red.py::test_the_red\nexit 0\n",
        sample="t/test_red.py")
    assert gates.gate_for(root, "terr")["decorative"] is False


def test_an_ungated_territory_is_decorative_too(tmp_path):
    """`none` and `pytest` are not gates that have been exercised either.

    Reported through the same field so a caller cannot read "not decorative" off
    a territory that has no gate at all.
    """
    root = tmp_path / "repo"
    (root / "terr").mkdir(parents=True)
    assert gates.gate_for(str(root), "terr")["decorative"] is True


def test_the_survey_reports_decorative_beside_gated(tmp_path):
    root = _territory(tmp_path,
                      "#!/bin/sh\n# negative-sample: t/test_red.py\nexit 0\n",
                      sample="t/test_red.py")
    (tmp_path / "repo" / "other").mkdir()
    (tmp_path / "repo" / "other" / "verify.sh").write_text("exit 0\n",
                                                           encoding="utf-8")
    s = gates.survey(root)
    assert "terr" in s["gated"] and "other" in s["gated"]
    assert s["decorative"] == ["other"], s["decorative"]


def test_monitors_own_gate_declares_one():
    """The rig that demands this of everyone else goes first.

    S13's whole finding was that a self-discipline clause is not a mechanism;
    the enforcer exempting itself would be the same mistake one level up.
    """
    row = gates.gate_for(gates.ROOT, "monitor")
    assert row["negative_sample"] is not None, row
    assert row["negative_sample"]["exists"] is True, row
    assert row["decorative"] is False, row
