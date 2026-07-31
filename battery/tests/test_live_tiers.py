"""The live-tier companion is true, reproducible — and seen to refuse.

Same shape as `test_freeze.py`: the positive checks first (the committed
artefact matches an in-process recompute, byte for byte, twice), then negative
controls that break the arrangement in one specific way each and assert that
`verify.rung_live_tiers` names it.  A rung that has never been seen red is a
comment.
"""

import json
import os
import re
import shutil

import pytest

from battery import freeze, verify
from battery.audit import live_tiers


@pytest.fixture(scope="module")
def fresh():
    """One in-process recompute, shared: the v9 attack suite behind it is
    memoised but still costs seconds the first time."""
    return live_tiers.build()


# --- the artefact itself --------------------------------------------------

def test_build_is_deterministic(fresh):
    assert live_tiers.build() == fresh
    assert live_tiers.serialise(live_tiers.build()) == live_tiers.serialise(fresh)


def test_no_timestamp_no_machine_path(fresh):
    """Byte-reproducible for a fixed tree: no clock, no checkout location."""
    text = live_tiers.serialise(fresh)
    assert not re.search(r"20\d\d-\d\d-\d\dT", text), "an ISO timestamp got in"
    assert "utc" not in fresh
    assert "Users" not in text and ":\\" not in text, "an absolute path got in"


def test_committed_artifact_matches_the_recompute(fresh):
    with open(live_tiers.DEFAULT_OUT, encoding="utf-8") as fh:
        committed = fh.read()
    assert committed == live_tiers.serialise(fresh), (
        "battery/artifacts_live/gaming_audit.live.json is stale; regenerate "
        "with `python -m battery.audit.live_tiers` and commit it")


def test_frozen_pin_matches_the_frozen_file_on_disk(fresh):
    assert fresh["frozen_sha256"] == freeze.sha256_file(live_tiers.FROZEN)


def test_the_diff_names_exactly_the_frozen_main_table(fresh):
    """Live `main` is empty, so the divergence is precisely the frozen nine —
    the number STATUS.md discloses and W-1671 recorded misleading a reviewer."""
    with open(live_tiers.FROZEN, encoding="utf-8") as fh:
        frozen = json.load(fh)
    diverged = sorted(r["metric"] for r in fresh["diff_vs_frozen"])
    assert diverged == sorted(frozen["main"])
    assert fresh["n_diverging"] == len(diverged)
    for row in fresh["diff_vs_frozen"]:
        assert row["frozen"] == "main" and row["live"] == "reference"


def test_every_demotion_names_a_run_and_a_number(fresh):
    """PREREG_V9 R3, carried into the artefact: the evidence rides with the
    tier, except for the R4 'withheld, not survived' rows, whose whole point
    is that the metric answered nothing."""
    for metric_id, row in fresh["metrics"].items():
        if row["tier"] != "reference" or "v9_demotion" not in row:
            continue
        evidence = row["v9_demotion"]
        assert set(evidence) == {"attack", "value", "target", "claim"}
        if evidence["attack"] != "—":
            assert evidence["value"] is not None, metric_id


# --- the refusal ----------------------------------------------------------

def test_writing_into_the_frozen_directory_is_refused(tmp_path):
    frozen_dir = os.path.join(os.path.dirname(live_tiers.FROZEN))
    with pytest.raises(ValueError, match="frozen baseline"):
        live_tiers.refuse_frozen_destination(
            os.path.join(frozen_dir, "gaming_audit.live.json"))
    # a dressed-up relative path resolves to the same place and is refused too
    with pytest.raises(ValueError, match="frozen baseline"):
        live_tiers.refuse_frozen_destination(
            os.path.join(frozen_dir, "..", "artifacts", "x.json"))
    # the sibling directory is not refused
    assert live_tiers.refuse_frozen_destination(str(tmp_path / "ok.json"))


def test_the_cli_refuses_with_exit_2(capsys):
    rc = live_tiers.main(["--out", os.path.join(
        os.path.dirname(live_tiers.FROZEN), "evil.json")])
    assert rc == 2
    assert "REFUSED" in capsys.readouterr().out
    assert not os.path.exists(
        os.path.join(os.path.dirname(live_tiers.FROZEN), "evil.json"))


# --- the rung, green ------------------------------------------------------

def test_rung_green_on_the_real_tree(capsys):
    problems = []
    verify.rung_live_tiers(problems)
    assert problems == [], problems
    out = capsys.readouterr().out
    # the divergence is REPORTED even when everything is green: exit-neutral
    assert "frozen-vs-live tier divergence" in out
    assert "P3" in out and "E2" in out


# --- the rung, red: negative controls ------------------------------------

def test_rung_red_on_a_tampered_companion(tmp_path, capsys):
    """The companion going stale is the failure class this rung exists for."""
    doc = json.load(open(live_tiers.DEFAULT_OUT, encoding="utf-8"))
    doc["metrics"]["P3"]["tier"] = "main"       # quietly resurrect a metric
    doc["main"] = ["P3"]
    bad = tmp_path / "gaming_audit.live.json"
    bad.write_text(live_tiers.serialise(doc), encoding="utf-8", newline="\n")
    problems = []
    verify.rung_live_tiers(problems, live_path=str(bad))
    assert any("recompute" in p for p in problems), problems


def test_rung_red_on_a_rewritten_baseline(tmp_path):
    """PREREG_V9 §5: the baseline is frozen; a moved pin needs a human."""
    rewritten = tmp_path / "gaming_audit.json"
    shutil.copy(live_tiers.FROZEN, rewritten)
    with open(rewritten, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n")
    problems = []
    verify.rung_live_tiers(problems, frozen_path=str(rewritten))
    assert any("PREREG" in p and "baseline" in p for p in problems), problems


def test_rung_red_when_the_disclosure_leaves_status_md(tmp_path):
    """The sentence is derived (count read from the frozen file), so it must
    track the artefact — this control deletes it and requires red."""
    status = open(os.path.join(verify.HERE, "STATUS.md"),
                  encoding="utf-8").read()
    with open(live_tiers.FROZEN, encoding="utf-8") as fh:
        claim = live_tiers.STALE_CLAIM % len(json.load(fh)["main"])
    assert claim in status, "the control must delete something real"
    stripped = tmp_path / "STATUS.md"
    stripped.write_text(status.replace(claim, "（此处曾有披露）"),
                        encoding="utf-8", newline="\n")
    problems = []
    verify.rung_live_tiers(problems, status_path=str(stripped))
    assert any("disclosure" in p for p in problems), problems


def test_rung_red_when_the_companion_is_absent(tmp_path):
    problems = []
    verify.rung_live_tiers(problems,
                           live_path=str(tmp_path / "nowhere.json"))
    assert any("absent" in p for p in problems), problems


def test_rung_red_on_unparseable_companion(tmp_path):
    bad = tmp_path / "gaming_audit.live.json"
    bad.write_text("{not json", encoding="utf-8")
    problems = []
    verify.rung_live_tiers(problems, live_path=str(bad))
    assert any("not JSON" in p for p in problems), problems
