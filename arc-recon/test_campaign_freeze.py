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


# -- clearing: the owner decision how_to_clear names -------------------------
#
# `freeze_campaigns` wrote a `how_to_clear` paragraph from the first commit,
# and nothing implemented it: the only available clearing was hand-editing the
# tracked JSON, which records no reason, names no owner, and reads in a diff
# exactly like vandalism. These pin the command that replaced that.

def _file_incident(paths, ident):
    with open(paths["INCIDENTS_PATH"], "a", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps({"id": ident, "title": "t"}, sort_keys=True) + "\n")


def test_clear_freeze_records_reason_owner_and_its_own_incident(sandbox):
    canary.freeze_campaigns("INC-900", ["g50t-5849a774"], "canary drift", {})
    state = canary.clear_freeze("re-baselined after the operators confirmed a "
                                "content update", by="A-3 owner")
    assert state["frozen"] is False
    assert state["cleared"]["by"] == "A-3 owner"
    assert "operators confirmed" in state["cleared"]["reason"]
    assert state["history"][-1]["incident"] == "INC-900"
    canary.assert_campaigns_unfrozen()               # must not raise

    incident_id = state["cleared"]["clearing_incident"]
    assert incident_id in canary.incident_ids()
    assert [e["event"] for e in read_log(sandbox)] == ["frozen", "cleared"]
    assert read_log(sandbox)[-1]["clearing_incident"] == incident_id


def test_clear_freeze_does_not_restore_checked_utc(sandbox):
    """An owner adjudicates a past observation; they do not make a new one.

    If clearing restored `checked_utc`, the file would claim the canary had
    vouched for an environment nobody had looked at since the drift.
    """
    canary.refresh_freeze(green_run())
    canary.freeze_campaigns("INC-900", ["g50t-5849a774"], "canary drift", {})
    state = canary.clear_freeze("adjudicated", by="owner")
    assert state["checked_utc"] is None
    assert "no replay has vouched" in state["note"]


def test_clear_freeze_refuses_without_a_reason_or_an_owner(sandbox):
    canary.freeze_campaigns("INC-900", ["g50t-5849a774"], "canary drift", {})
    with pytest.raises(RuntimeError, match="requires a reason"):
        canary.clear_freeze("   ", by="owner")
    with pytest.raises(RuntimeError, match="requires --by"):
        canary.clear_freeze("a reason", by="")
    # neither refusal may have moved the state or the log
    assert json.loads(sandbox["FREEZE_PATH"].read_text(encoding="utf-8"))["frozen"]
    assert [e["event"] for e in read_log(sandbox)] == ["frozen"]


def test_clear_freeze_refuses_an_adjudication_that_was_never_filed(sandbox):
    canary.freeze_campaigns("INC-900", ["g50t-5849a774"], "canary drift", {})
    with pytest.raises(RuntimeError, match="not in"):
        canary.clear_freeze("adjudicated", by="owner", adjudication="INC-404")
    _file_incident(sandbox, "INC-404")
    state = canary.clear_freeze("adjudicated", by="owner",
                                adjudication="INC-404")
    assert state["cleared"]["adjudication"] == "INC-404"


def test_clear_freeze_refuses_when_nothing_is_frozen(sandbox):
    canary.refresh_freeze(green_run())
    with pytest.raises(RuntimeError, match="not frozen"):
        canary.clear_freeze("nothing to do", by="owner")


# -- the state file vs the log that cannot be rewritten ----------------------

def test_deleting_the_state_file_does_not_thaw_a_filed_freeze(sandbox):
    """The hole `freeze-audit` exists to close, exercised end to end.

    `init_freeze_from_runs` refuses to *overwrite*; it did not refuse to
    *create*. So `rm campaign_freeze.json && canary.py init-freeze` rebuilt an
    unfrozen file from `canary_runs.jsonl` with no memory of the freeze -- a
    thaw costing one deletion and one offline command, in an instrument whose
    whole design forbids self-healing.
    """
    _file_incident(sandbox, "INC-900")
    _write_runs(sandbox, green_run())
    canary.freeze_campaigns("INC-900", ["g50t-5849a774"], "canary drift", {})
    os.remove(sandbox["FREEZE_PATH"])

    with pytest.raises(RuntimeError, match="thaw by"):
        canary.init_freeze_from_runs()
    assert not sandbox["FREEZE_PATH"].exists()

    audit = canary.freeze_audit()
    assert audit["verdict"] == "DIVERGED"
    with pytest.raises(canary.CampaignFrozen, match="DIVERGED"):
        canary.assert_campaigns_unfrozen()

    # and the documented way out works even with the state file gone
    state = canary.clear_freeze("adjudicated: operators confirmed the update",
                                by="owner")
    assert state["frozen"] is False
    assert state["history"][-1]["incident"] == "INC-900"
    assert canary.freeze_audit()["verdict"] == "OK"
    canary.assert_campaigns_unfrozen()


def test_a_freeze_entry_with_no_filed_incident_is_unadjudicable_not_diverged(
        sandbox):
    """This repository's own log opens with six of these.

    `data/campaign_freeze_log.jsonl` was committed carrying INC-TEST /
    INC-998 / INC-999 entries from an unsandboxed exercise, none of which
    exist in `incidents.jsonl`. The drift path files the incident *before* it
    freezes, so a freeze with no incident never came from drift. It must not
    be reported as a lost freeze -- and it must not be swallowed either.
    """
    _write_runs(sandbox, green_run())
    canary.freeze_campaigns("INC-TEST", ["ar25-0c556536"], "test freeze", {})
    os.remove(sandbox["FREEZE_PATH"])

    state = canary.init_freeze_from_runs()           # allowed: not adjudicable
    assert state["frozen"] is False
    audit = canary.freeze_audit()
    assert audit["verdict"] == "UNADJUDICABLE_LOG"
    assert [e["incident"] for e in audit["unadjudicable_freeze_entries"]] \
        == ["INC-TEST"]
    canary.assert_campaigns_unfrozen()               # not a stop, only a note


def test_green_while_frozen_is_not_state_bearing(sandbox):
    """A sweep that changed nothing must not be able to answer "what should
    the state file say"; only the transitions may."""
    _file_incident(sandbox, "INC-900")
    canary.freeze_campaigns("INC-900", ["g50t-5849a774"], "canary drift", {})
    canary.refresh_freeze(green_run())
    assert [e["event"] for e in read_log(sandbox)] == [
        "frozen", "green-while-frozen"]
    assert canary.last_state_bearing_event()["event"] == "frozen"


def test_freeze_audit_is_ok_on_an_ordinary_green_history(sandbox):
    canary.refresh_freeze(green_run())
    audit = canary.freeze_audit()
    assert audit["verdict"] == "OK"
    assert audit["last_state_bearing_event"]["event"] == "green"


def test_freeze_audit_and_clear_freeze_are_on_the_parser():
    parser = canary.build_parser()
    assert parser.parse_args(["freeze-audit"]).func is canary._cmd_freeze_audit
    args = parser.parse_args(["clear-freeze", "--reason", "r", "--by", "o"])
    assert args.func is canary._cmd_clear_freeze
    assert (args.reason, args.by, args.adjudication) == ("r", "o", None)
    with pytest.raises(SystemExit):                  # --by is not optional
        parser.parse_args(["clear-freeze", "--reason", "r"])


def test_cmd_exit_codes_for_audit_and_clear(sandbox, capsys):
    _file_incident(sandbox, "INC-900")
    _write_runs(sandbox, green_run())
    canary.init_freeze_from_runs()
    assert canary._cmd_freeze_audit(_Args(json=False)) == 0

    canary.freeze_campaigns("INC-900", ["g50t-5849a774"], "canary drift", {})
    os.remove(sandbox["FREEZE_PATH"])
    assert canary._cmd_freeze_audit(_Args(json=True)) == 1
    assert canary._cmd_clear_freeze(
        _Args(reason="adjudicated", by="owner", adjudication=None)) == 0
    assert "checked_utc is null" in capsys.readouterr().out
    assert canary._cmd_freeze_audit(_Args(json=False)) == 0


def test_main_turns_a_refusal_into_an_exit_code_not_a_traceback(sandbox, capsys):
    canary.refresh_freeze(green_run())
    assert canary.main(["clear-freeze", "--reason", "r", "--by", "o"]) == 3
    assert "REFUSED" in capsys.readouterr().out


class _Args:
    def __init__(self, **kw):
        self.__dict__.update(kw)
