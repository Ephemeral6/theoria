"""The campaign-freeze loop's writing half, offline. No API, no network.

ACCESS_CHECK §2's qualification was that the canary could *detect* drift but
nothing downstream could *see* the verdict: `campaign_freeze.json` did not
exist and no runner read it. These tests pin the writing half of the closed
loop (the reading half is `theoria-arm/tests/test_freeze_preflight.py`, in the
arm's own territory):

* drift writes `{frozen: true, reason, ...}` and appends to the log;
* a green sweep writes/refreshes `{frozen: false, checked_utc}`;
* a green sweep NEVER clears a standing freeze -- the INC-003 rule, one level
  up: an instrument that can heal its own red state measures nothing;
* the file is never deleted; history is in the adjacent append-only log;
* `init-freeze` builds the initial file offline from the last recorded replay
  and refuses everything else (an existing file, an empty record).

    cd arc-recon && python -m pytest test_campaign_freeze.py
"""

import json
import os

import pytest

import canary


# -- fixtures ---------------------------------------------------------------

@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Every file canary.py's freeze paths touch, pointed into tmp."""
    paths = {
        "FREEZE_PATH": tmp_path / "campaign_freeze.json",
        "FREEZE_LOG_PATH": tmp_path / "campaign_freeze_log.jsonl",
        "RUNS_PATH": tmp_path / "canary_runs.jsonl",
        "INCIDENTS_PATH": tmp_path / "incidents.jsonl",
    }
    for name, path in paths.items():
        monkeypatch.setattr(canary, name, str(path))
    return paths


def green_run(t="2026-07-30T03:49:08Z"):
    return {"t": t, "card_id": "card-test",
            "verdicts": {"g50t-5849a774": "PASS", "ar25-0c556536": "PASS"},
            "note": "test sweep"}


def read_log(paths):
    log = paths["FREEZE_LOG_PATH"]
    if not log.exists():
        return []
    return [json.loads(line) for line in
            log.read_text(encoding="utf-8").splitlines() if line.strip()]


# -- drift freezes, and the log records it ----------------------------------

def test_drift_writes_a_frozen_file_and_logs_the_transition(sandbox):
    canary.freeze_campaigns("INC-900", ["g50t-5849a774"], "canary drift",
                            {"mismatches": 1})
    state = json.loads(sandbox["FREEZE_PATH"].read_text(encoding="utf-8"))
    assert state["frozen"] is True
    assert state["reason"] == "canary drift"
    assert state["incident"] == "INC-900"
    assert "how_to_clear" in state
    events = read_log(sandbox)
    assert [e["event"] for e in events] == ["frozen"]
    assert events[0]["incident"] == "INC-900"

    with pytest.raises(canary.CampaignFrozen) as caught:
        canary.assert_campaigns_unfrozen()
    assert "INC-900" in str(caught.value)
    assert "canary drift" in str(caught.value)


def test_a_second_freeze_keeps_the_first_in_history_never_deleting(sandbox):
    canary.freeze_campaigns("INC-900", ["g50t-5849a774"], "first drift", {})
    canary.freeze_campaigns("INC-901", ["ar25-0c556536"], "second drift", {})
    state = json.loads(sandbox["FREEZE_PATH"].read_text(encoding="utf-8"))
    assert state["frozen"] is True
    assert state["incident"] == "INC-901"
    assert [h["incident"] for h in state["history"]] == ["INC-900"]
    assert [e["event"] for e in read_log(sandbox)] == ["frozen", "frozen"]


# -- green writes/refreshes -------------------------------------------------

def test_a_green_sweep_creates_the_file_with_checked_utc(sandbox):
    state = canary.refresh_freeze(green_run())
    assert state["frozen"] is False
    assert state["checked_utc"] == "2026-07-30T03:49:08Z"
    assert state["canary_run"]["card_id"] == "card-test"
    on_disk = json.loads(sandbox["FREEZE_PATH"].read_text(encoding="utf-8"))
    assert on_disk == state
    assert [e["event"] for e in read_log(sandbox)] == ["green"]
    canary.assert_campaigns_unfrozen()               # must not raise


def test_a_later_green_sweep_refreshes_checked_utc(sandbox):
    canary.refresh_freeze(green_run(t="2026-07-30T00:00:00Z"))
    state = canary.refresh_freeze(green_run(t="2026-07-31T00:00:00Z"))
    assert state["checked_utc"] == "2026-07-31T00:00:00Z"
    assert [e["event"] for e in read_log(sandbox)] == ["green", "green"]


def test_a_green_sweep_never_clears_a_standing_freeze(sandbox):
    """The negative control this whole file exists for.

    Drift can be intermittent: the sweep that catches the environment back on
    its old behaviour proves nothing about the runs made while it was off it.
    If a green replay could thaw the file, the freeze would be a self-healing
    instrument -- the INC-003 failure shape, one level up.
    """
    canary.freeze_campaigns("INC-900", ["g50t-5849a774"], "canary drift", {})
    state = canary.refresh_freeze(green_run())
    assert state["frozen"] is True, "a green sweep must not thaw a freeze"
    on_disk = json.loads(sandbox["FREEZE_PATH"].read_text(encoding="utf-8"))
    assert on_disk["frozen"] is True
    assert on_disk["incident"] == "INC-900"
    events = read_log(sandbox)
    assert [e["event"] for e in events] == ["frozen", "green-while-frozen"]
    with pytest.raises(canary.CampaignFrozen):
        canary.assert_campaigns_unfrozen()


# -- offline initialisation -------------------------------------------------

def _write_runs(paths, *runs):
    with open(paths["RUNS_PATH"], "w", encoding="utf-8", newline="") as fh:
        for run in runs:
            fh.write(json.dumps(run, sort_keys=True) + "\n")


def test_init_freeze_builds_the_file_from_the_last_recorded_pass(sandbox):
    _write_runs(sandbox,
                {"t": "2026-07-29T00:00:00Z", "card_id": "c1",
                 "verdicts": {"g50t-5849a774": "INCOMPLETE"}},
                green_run(t="2026-07-30T03:49:08Z"))
    state = canary.init_freeze_from_runs()
    assert state["frozen"] is False
    assert state["checked_utc"] == "2026-07-30T03:49:08Z"
    assert "OFFLINE" in state["note"]
    assert [e["event"] for e in read_log(sandbox)] == ["initialized"]


def test_init_freeze_refuses_to_overwrite_an_existing_file(sandbox):
    _write_runs(sandbox, green_run())
    canary.init_freeze_from_runs()
    with pytest.raises(RuntimeError, match="already exists"):
        canary.init_freeze_from_runs()


def test_init_freeze_refuses_with_no_recorded_replay(sandbox):
    with pytest.raises(RuntimeError, match="no recorded replay"):
        canary.init_freeze_from_runs()
    assert not sandbox["FREEZE_PATH"].exists()


def test_init_freeze_from_a_drifted_record_starts_frozen(sandbox):
    """The record outranks the wish: if the last observation was drift, the
    file the runners will read must open saying so."""
    _write_runs(sandbox, {"t": "2026-07-30T03:49:08Z", "card_id": "c2",
                          "verdicts": {"g50t-5849a774": "DRIFT"},
                          "froze_campaigns": True, "incident": "INC-777"})
    state = canary.init_freeze_from_runs()
    assert state["frozen"] is True
    assert state["incident"] == "INC-777"
    with pytest.raises(canary.CampaignFrozen):
        canary.assert_campaigns_unfrozen()


# -- the CLI surface --------------------------------------------------------

def test_the_parser_accepts_write_freeze_and_init_freeze():
    parser = canary.build_parser()
    args = parser.parse_args(["replay", "--write-freeze"])
    assert args.write_freeze is True
    assert parser.parse_args(["replay"]).write_freeze is False
    assert parser.parse_args(["init-freeze"]).func is canary._cmd_init_freeze


def test_cmd_init_freeze_exit_codes(sandbox, capsys):
    _write_runs(sandbox, green_run())
    assert canary._cmd_init_freeze(None) == 0
    assert "frozen=False" in capsys.readouterr().out
