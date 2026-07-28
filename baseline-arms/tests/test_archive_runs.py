"""The provenance archive over the real tree.

These run against `runs/` as built, not a fixture, because the properties worth
guarding are about *this* archive being complete -- a fixture would let the real
one drift out from under them.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness import archive_runs, summarise_pilot, run_campaign as rc   # noqa: E402

MANIFEST = archive_runs.MANIFEST_PATH


@pytest.fixture(scope="module")
def manifest():
    if not os.path.exists(MANIFEST):
        pytest.skip("runs/ has not been built yet")
    with open(MANIFEST, encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def entries(manifest):
    out = []
    for item in manifest["entries"]:
        with open(os.path.join(archive_runs.TRACK,
                               item["path"].replace("/", os.sep)),
                  encoding="utf-8") as fh:
            out.append(json.load(fh))
    return out


# --------------------------------------------------------------- completeness
def test_every_pilot_cell_is_archived(entries):
    kept, superseded = summarise_pilot.load_cells()
    expected = {c["run_id"] for c in kept + superseded}
    archived = {e["id"] for e in entries if e.get("campaign") == "m4-pilot"}
    assert expected == archived


def test_every_envelope_cell_is_archived(entries):
    expected = {c["run_id"] for c in rc.load_cells()}
    archived = {e["id"] for e in entries if e["kind"] == "run"}
    assert expected <= archived


def test_failed_runs_are_archived_on_the_same_terms(entries):
    """METHOD.md row 9. A dead run must carry the same fields as a live one."""
    dead = [e for e in entries if e["kind"] == "run"
            and e["outcome"] in ("api_unusable", "model_error",
                                 "no_reset_window", "harness_error")]
    assert dead, "no dead runs archived, but the pilot and envelope both had some"
    live = [e for e in entries if e["kind"] == "run" and e not in dead]
    for e in dead:
        assert set(e) >= set(live[0]) - {"error", "repeat", "superseded_by_rerun"}
        assert e["evidence"]
        assert e["spend"]["cost_usd"] is not None


def test_superseded_cells_are_archived_not_dropped(entries):
    _, superseded = summarise_pilot.load_cells()
    flagged = {e["id"] for e in entries if e.get("superseded_by_rerun")}
    assert flagged == {c["run_id"] for c in superseded}
    assert flagged, "the pilot had superseded attempts; none are flagged"


def test_the_archived_total_matches_the_pilot_and_envelope_bills(manifest):
    kept, superseded = summarise_pilot.load_cells()
    pilot = sum(c.get("cost_usd") or 0.0 for c in kept + superseded)
    envelope = sum(c.get("cost_usd") or 0.0 for c in rc.load_cells())
    assert manifest["totals"]["cost_usd"] == pytest.approx(pilot + envelope, abs=1e-4)


# ---------------------------------------------------------------- provenance
def test_every_entry_carries_a_prompt_id(entries):
    for e in entries:
        if e["kind"] == "excluded":
            continue
        assert e["prompt_id"], e["id"]


def test_pre_p12_work_is_back_annotated(entries):
    """METHOD.md row 8 wants the commissioning ticket on the artifact. Work that
    predates the archive gets `retro:P-7`, not a plausible-looking current id."""
    retro = [e for e in entries if e.get("prompt_id") == archive_runs.RETRO_PROMPT]
    assert len(retro) >= 15
    assert archive_runs.RETRO_PROMPT.startswith("retro:")


def test_the_manifest_records_branch_and_commit(manifest):
    prov = manifest["provenance"]
    assert prov["branch"]
    assert prov["base_commit"] and len(prov["base_commit"]) == 40


def test_seed_is_null_and_explains_itself(entries):
    """Row 9 asks for a seed. There is not one; the archive says so rather than
    writing a number that would not reproduce anything."""
    for e in entries:
        if e["kind"] == "excluded":
            continue
        assert e["seed"] is None
        assert e["seed_note"]


# ------------------------------------------------------------------ evidence
def test_every_run_points_at_evidence_that_exists(entries):
    for e in entries:
        if e["kind"] == "excluded":
            continue
        assert e["evidence"], e["id"]
        for ev in e["evidence"]:
            assert not ev.get("missing"), (e["id"], ev)
            assert ev["sha256"].startswith("sha256:")
            assert os.path.exists(os.path.join(archive_runs.REPO,
                                               ev["path"].replace("/", os.sep)))


def test_evidence_says_whether_git_carries_it(entries):
    """A gitignored pointer promises less than a tracked one, and the archive
    has to say which it is."""
    seen = {ev.get("tracked") for e in entries for ev in e.get("evidence") or []}
    assert True in seen and False in seen


def test_verify_passes_on_the_archive_as_built():
    result = archive_runs.verify()
    assert result["ok"], result["problems"]
    assert result["evidence_checked"] > 0


# ------------------------------------------------------------- what is absent
def test_the_concurrent_s1_run_is_recorded_as_deliberately_excluded(entries):
    """Not archiving something has to be a statement, not a silence."""
    excluded = [e for e in entries if e["kind"] == "excluded"]
    assert len(excluded) == 1
    assert "INC-BA-003" in excluded[0]["reason"]
    assert excluded[0]["checkpoints"]


def test_the_schema_traces_fetch_is_archived_without_its_payload(entries):
    fetch = [e for e in entries if e["kind"] == "fetch"]
    assert len(fetch) == 1
    assert fetch[0]["spend"]["cost_usd"] == 0.0
    assert "D-013" in fetch[0]["note"]


def test_no_sealed_game_appears_anywhere_in_the_archive(entries):
    """G7's discipline, applied to the archive: a sealed id here would mean the
    track touched one."""
    from harness import arc_client
    sealed = {g.split("-")[0] for g in arc_client.sealed_pile()}
    for e in entries:
        blob = json.dumps(e)
        for prefix in sealed:
            assert prefix not in blob, (e["id"], prefix)


# ---------------------------------------------------------------- determinism
def test_rebuilding_produces_the_same_digest(manifest):
    again = archive_runs.build(manifest["prompt_id"])
    assert again["entries_sha256"] == manifest["entries_sha256"]
