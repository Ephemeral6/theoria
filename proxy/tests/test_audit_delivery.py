"""The corrected delivery audit, and the confusions it must not repeat.

The check this replaces failed A10 by counting `arm` values in
`proxy/var/ledger.jsonl`. Every test here is a way that count can be right and
mean nothing. The first one is the defect itself: a missing file and a file
that was read and answered zero used to produce the same red.
"""
import json
import os

import pytest

from tools import audit_delivery
from tools.audit_delivery import census


def write(path, records):
    """A raw stream, on purpose.

    `test_reconcile.py` builds fixtures through the real `Ledger` because
    reconciliation reads the envelope RED-40 taught it to require. The census
    reads four fields and counts them, so a literal stream states each case in
    one place and keeps what is being asserted visible.
    """
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for record in records:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
    return path


def step(arm, seq, event="env_step"):
    return {"v": "1.0", "seq": seq, "arm": arm, "event": event,
            "run_id": "r-test", "ts": "2026-07-30T00:00:00.000Z"}


def start(arm, env_upstream, model_upstream=None, run_id="r-test"):
    return {"v": "1.0", "seq": 1, "arm": arm, "event": "run_start",
            "run_id": run_id, "ts": "2026-07-30T00:00:00.000Z",
            "env_upstream": env_upstream, "model_upstream": model_upstream}


# -- the defect this module exists for -------------------------------------

def test_an_absent_ledger_and_an_empty_answer_are_different_words(tmp_path):
    """The 2026-07-29 check could print the same red for both.

    `proxy/var/` is gitignored, so on a clean checkout the file is simply not
    there. "I could not look" and "I looked and the answer is zero" are
    different claims about the world and only one of them is about A10.
    """
    missing = census(str(tmp_path / "nope.jsonl"))
    present = census(write(str(tmp_path / "there.jsonl"),
                           [start("mock_arm", "http://127.0.0.1:1"),
                            step("mock_arm", 2)]))

    assert missing["state"] == "ABSENT"
    assert present["state"] == "PRESENT"
    assert missing["state"] != present["state"]
    # And the absent one carries no count at all, so a caller cannot reach for
    # a zero that was never measured.
    assert "axis1_real_arm_records" not in missing
    assert present["axis1_real_arm_records"] == 0


def test_the_two_senses_of_a_real_arm_are_counted_separately(tmp_path):
    """`--mock --arm bare_cc` is the forgery the ticket's literal wording invites.

    It costs nothing and writes records that satisfy axis 1 while nothing
    leaves the machine. A census that reports one number cannot tell it from a
    live run, so it reports two.
    """
    forged = census(write(str(tmp_path / "forged.jsonl"), [
        start("bare_cc", "http://127.0.0.1:61554", "http://127.0.0.1:61555"),
        step("bare_cc", 2), step("bare_cc", 3)]))

    assert forged["axis1_real_arm_records"] == 3, "the arm identity is real"
    assert forged["axis2_live_runs"] == 0, "and nothing left the machine"


def test_a_live_upstream_is_what_axis_two_counts(tmp_path):
    live = census(write(str(tmp_path / "live.jsonl"), [
        start("theoria", "https://three.arcprize.org", None),
        step("theoria", 2)]))

    assert live["axis1_real_arm_records"] == 2
    assert live["axis2_live_runs"] == 1


def test_incidents_are_not_counted_as_the_arm_they_complain_about(tmp_path):
    """`reconcile.py:521` stamps an incident with `steps[0]["arm"]`.

    So running reconciliation against the shared ledger appends records that
    wear a real arm's name without a real arm having run. An auditor who counts
    `arm` values counts its own footprints -- and this is not hypothetical: six
    such records are in the live ledger, from the previous pass at this item.
    """
    result = census(write(str(tmp_path / "incidents.jsonl"), [
        start("theoria", "https://three.arcprize.org"),
        step("theoria", 2),
        dict(step("theoria", 3, event="incident"), kind="score_mismatch"),
        dict(step("theoria", 4, event="incident"), kind="score_mismatch")]))

    assert result["records"] == 4
    assert result["activity_records"] == 2
    assert result["incident_records"] == 2
    assert result["by_arm_excluding_incidents"] == {"theoria": 2}
    assert result["axis1_real_arm_records"] == 2, (
        "the two incidents must not inflate the arm's own count")


def test_an_unreadable_line_is_named_rather_than_skipped(tmp_path):
    path = str(tmp_path / "torn.jsonl")
    write(path, [start("mock_arm", "http://127.0.0.1:1")])
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("{not json\n")

    result = census(path)
    assert result["unreadable_lines"] == 1
    assert result["records"] == 1


# -- the evidence half, and its failing path -------------------------------

def test_the_audit_is_green_on_the_tree_that_ships_it():
    problems = []
    audit_delivery.check_evidence(problems)
    assert problems == [], problems


def test_red_a_pinned_artefact_that_changed_makes_the_audit_fail(
        tmp_path, monkeypatch):
    """The negative sample for the evidence half.

    A check that only ever runs against a good tree has no failing path. This
    rebuilds A10's manifest over a scratch tree, corrupts one pinned file, and
    requires the audit to name it.
    """
    repo = tmp_path / "repo"
    (repo / "proxy" / "runs" / "20260729T010000Z-A10").mkdir(parents=True)
    pinned = repo / "proxy" / "runs" / "20260729T010000Z-A10" / "demo_output.txt"
    pinned.write_text("VERDICT: PASS\n", encoding="utf-8")

    import hashlib
    digest = hashlib.sha256(pinned.read_bytes()).hexdigest()
    manifest = repo / "proxy" / "runs" / "20260729T010000Z-A10" / "MANIFEST.json"
    manifest.write_text(json.dumps({
        "prompt_id": "A10-shared-ledger-real-arms",
        "files": [{"path": "proxy/runs/20260729T010000Z-A10/demo_output.txt",
                   "sha256": digest}],
    }), encoding="utf-8")

    monkeypatch.setattr(audit_delivery, "REPO", str(repo))
    monkeypatch.setattr(audit_delivery, "MANIFEST_PATH", str(manifest))

    clean = []
    audit_delivery.check_evidence(clean)
    assert clean == [], "the scratch tree starts honest"

    pinned.write_text("VERDICT: PASS\n(and a line nobody recorded)\n",
                      encoding="utf-8")
    problems = []
    audit_delivery.check_evidence(problems)
    assert len(problems) == 1, problems
    assert "demo_output.txt" in problems[0]
    assert "no longer matches" in problems[0]


def test_red_a_missing_artefact_makes_the_audit_fail(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "proxy").mkdir(parents=True)
    manifest = repo / "proxy" / "MANIFEST.json"
    manifest.write_text(json.dumps({
        "prompt_id": "A10-shared-ledger-real-arms",
        "files": [{"path": "proxy/gone.py", "sha256": "0" * 64}],
    }), encoding="utf-8")

    monkeypatch.setattr(audit_delivery, "REPO", str(repo))
    monkeypatch.setattr(audit_delivery, "MANIFEST_PATH", str(manifest))

    problems = []
    audit_delivery.check_evidence(problems)
    assert problems == ["missing: proxy/gone.py"]


def test_red_a_manifest_that_cannot_be_read_is_a_problem_not_a_pass(
        tmp_path, monkeypatch):
    """With A10's manifest gone there is nothing to check against, and the
    audit must say so rather than finding no problems and reporting green."""
    monkeypatch.setattr(audit_delivery, "MANIFEST_PATH",
                        str(tmp_path / "absent.json"))
    problems = []
    audit_delivery.check_evidence(problems)
    assert len(problems) == 1
    assert "unreadable" in problems[0]


def test_the_substance_markers_still_hold():
    """A digest cannot express "A10's fix is still in a file others edit"."""
    for relative, marker, why in audit_delivery.MARKERS:
        path = os.path.join(audit_delivery.HERE, relative)
        with open(path, encoding="utf-8") as fh:
            assert marker in fh.read(), why
