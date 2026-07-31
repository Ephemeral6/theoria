"""The campaign-freeze gate, on the paths that actually spend. Both ways.

`arc-recon/canary.py` writes `data/campaign_freeze.json`; until this gate the
arm never read it, so the freeze circuit was detection-only (ACCESS_CHECK §2's
qualification). These tests pin the reading half, and they pin it in both
directions on purpose -- a suite that only ever observes refusals cannot tell
a working wire from one that refuses unconditionally, which is the same
three-state problem `test_launch_gate_wired.py` documents:

1. **REFUSE** -- a frozen file stops a live `Run` and a live `Campaign`
   before anything touches the shared pool, naming the incident and reason.
2. **LAUNCH** -- a clear file lets the same constructions past the gate.
3. **UNAFFECTED** -- mock and offline paths never consult the gate at all:
   drift in the real ARC cannot invalidate a rehearsal against proxy/mock.

The pool-ordering proof uses a sentinel: `spend_mod.plan_caps` is replaced
with something that raises a distinctive error, so "the gate fired first"
and "construction proceeded past the gate" are observable as *which*
exception comes out, without ever constructing a real claim on the pool.

Zero network, zero spend, zero sealed-pile contact.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

from harness import campaign as camp
from harness import freeze_gate
from harness import run as run_mod
from harness import spend as spend_mod


# -- fixtures ---------------------------------------------------------------

class PoolTouched(Exception):
    """Sentinel: construction reached the spend machinery."""


@pytest.fixture
def no_pool(monkeypatch):
    """Make any step toward the shared pool loudly visible."""
    def boom(*args, **kwargs):
        raise PoolTouched("plan_caps was reached")
    monkeypatch.setattr(spend_mod, "plan_caps", boom)


def frozen_file(tmp_path, monkeypatch, **over):
    state = {"frozen": True, "since": "2026-07-31T00:00:00Z",
             "incident": "INC-901", "games": ["g50t-5849a774"],
             "reason": "canary drift on g50t-5849a774",
             "how_to_clear": "owner decision", "history": []}
    state.update(over)
    path = tmp_path / "campaign_freeze.json"
    path.write_text(json.dumps(state), encoding="utf-8")
    monkeypatch.setattr(freeze_gate, "FREEZE_PATH", str(path))
    return path


def clear_file(tmp_path, monkeypatch):
    path = tmp_path / "campaign_freeze.json"
    path.write_text(json.dumps({"frozen": False,
                                "checked_utc": "2026-07-30T03:49:08Z"}),
                    encoding="utf-8")
    monkeypatch.setattr(freeze_gate, "FREEZE_PATH", str(path))
    return path


# -- the address is canary's address ----------------------------------------

def test_the_path_is_the_one_canary_writes():
    """Two territories, one file. If either side moves it, this goes red
    before a live launch reads a gate that nothing writes."""
    arc_recon = os.path.join(freeze_gate.REPO, "arc-recon")
    sys.path.insert(0, arc_recon)
    try:
        import canary                                   # noqa: PLC0415
        assert (os.path.normcase(os.path.normpath(freeze_gate.FREEZE_PATH))
                == os.path.normcase(os.path.normpath(canary.FREEZE_PATH)))
    finally:
        sys.path.remove(arc_recon)


def test_the_tracked_initial_file_exists_and_is_readable():
    """Item (3) of the closeout: the file was initialised offline from the
    last recorded canary verdict and committed. A checkout where it is gone
    is the `missing` case, which is warned about, not silently normal."""
    state = freeze_gate.freeze_state()
    assert state is not None, freeze_gate.FREEZE_PATH
    assert "frozen" in state
    assert state["frozen"] is False or "reason" in state


# -- the gate function, both ways -------------------------------------------

def test_frozen_refuses_and_names_the_reason(tmp_path, monkeypatch):
    frozen_file(tmp_path, monkeypatch)
    with pytest.raises(freeze_gate.CampaignFrozen) as caught:
        freeze_gate.assert_unfrozen()
    message = str(caught.value)
    assert "FROZEN" in message
    assert "INC-901" in message
    assert "canary drift on g50t-5849a774" in message


def test_clear_proceeds_with_the_checked_timestamp(tmp_path, monkeypatch):
    clear_file(tmp_path, monkeypatch)
    reading = freeze_gate.assert_unfrozen()
    assert reading["state"] == "clear"
    assert reading["checked_utc"] == "2026-07-30T03:49:08Z"


def test_missing_warns_and_proceeds(tmp_path, monkeypatch):
    """Missing is not frozen -- the instrument is new, and a hard stop on
    absence would brick every checkout that predates it. But it is a warning
    that names the path, never silence."""
    monkeypatch.setattr(freeze_gate, "FREEZE_PATH",
                        str(tmp_path / "not-created.json"))
    warnings = []
    reading = freeze_gate.assert_unfrozen(warn=warnings.append)
    assert reading["state"] == "missing"
    assert len(warnings) == 1
    assert "not-created.json" in warnings[0]
    assert "init-freeze" in warnings[0]


def test_missing_is_one_flag_away_from_fatal(tmp_path, monkeypatch):
    """The hardening path exists and works; flipping it is a decision, not a
    rewrite."""
    monkeypatch.setattr(freeze_gate, "FREEZE_PATH",
                        str(tmp_path / "not-created.json"))
    monkeypatch.setattr(freeze_gate, "MISSING_IS_FATAL", True)
    with pytest.raises(freeze_gate.CampaignFrozen):
        freeze_gate.assert_unfrozen()


def test_an_unreadable_file_refuses(tmp_path, monkeypatch):
    """A corrupt freeze file is not a missing one. Collapsing the two would
    let truncation thaw a freeze."""
    path = tmp_path / "campaign_freeze.json"
    path.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(freeze_gate, "FREEZE_PATH", str(path))
    with pytest.raises(freeze_gate.CampaignFrozen) as caught:
        freeze_gate.assert_unfrozen()
    assert "could not be read" in str(caught.value)


def test_valid_json_that_is_not_an_object_refuses(tmp_path, monkeypatch):
    path = tmp_path / "campaign_freeze.json"
    path.write_text("null", encoding="utf-8")
    monkeypatch.setattr(freeze_gate, "FREEZE_PATH", str(path))
    with pytest.raises(freeze_gate.CampaignFrozen):
        freeze_gate.assert_unfrozen()


def test_a_truthy_frozen_string_still_refuses(tmp_path, monkeypatch):
    """`frozen: "false"` is a string and a string is truthy; the one value
    that must never be read loosely is the one that authorises spending."""
    frozen_file(tmp_path, monkeypatch, frozen="false")
    with pytest.raises(freeze_gate.CampaignFrozen):
        freeze_gate.assert_unfrozen()


# -- 1. REFUSE: through the real constructors --------------------------------

def test_a_frozen_file_stops_a_live_campaign(tmp_path, monkeypatch, no_pool):
    frozen_file(tmp_path, monkeypatch)
    with pytest.raises(camp.CampaignStopped) as caught:
        camp.Campaign(prompt_id="freeze-test", out_dir=str(tmp_path / "out"),
                      games=list(camp.DEV_PILE), offline=False)
    stop = caught.value
    assert "campaign-freeze gate" in str(stop)
    assert "INC-901" in str(stop)
    assert stop.detail["freeze_path"] == str(tmp_path / "campaign_freeze.json")


def test_a_frozen_file_stops_a_live_run_before_the_pool(tmp_path, monkeypatch,
                                                        no_pool):
    """`CampaignFrozen`, not `PoolTouched`: the refusal lands before a single
    step toward the shared pool, so a frozen environment cannot even hold a
    reservation open."""
    frozen_file(tmp_path, monkeypatch)
    with pytest.raises(freeze_gate.CampaignFrozen):
        run_mod.Run("g50t-5849a774", "freeze-test",
                    runs_root=str(tmp_path / "runs"))
    assert not (tmp_path / "runs").exists(), \
        "a refused run must leave no run directory behind"


# -- 2. LAUNCH: the same constructors, gate clear ----------------------------

def test_a_clear_file_lets_a_live_campaign_construct(tmp_path, monkeypatch,
                                                     no_pool):
    clear_file(tmp_path, monkeypatch)
    campaign = camp.Campaign(prompt_id="freeze-test",
                             out_dir=str(tmp_path / "out"),
                             games=list(camp.DEV_PILE), offline=False)
    assert campaign.games == list(camp.DEV_PILE)


def test_a_clear_file_lets_a_live_run_past_the_gate(tmp_path, monkeypatch,
                                                    no_pool):
    """`PoolTouched`, not `CampaignFrozen`: with the gate clear, construction
    proceeds to the spend machinery -- which the sentinel stops, so nothing
    real is reserved. The exception's *identity* is the proof the gate said
    yes."""
    clear_file(tmp_path, monkeypatch)
    with pytest.raises(PoolTouched):
        run_mod.Run("g50t-5849a774", "freeze-test",
                    runs_root=str(tmp_path / "runs"))


def test_a_missing_file_lets_a_live_run_past_the_gate_with_a_warning(
        tmp_path, monkeypatch, no_pool, capsys):
    monkeypatch.setattr(freeze_gate, "FREEZE_PATH",
                        str(tmp_path / "not-created.json"))
    with pytest.raises(PoolTouched):
        run_mod.Run("g50t-5849a774", "freeze-test",
                    runs_root=str(tmp_path / "runs"))
    assert "WARNING" in capsys.readouterr().err


# -- 3. UNAFFECTED: mock and offline paths ----------------------------------

def test_a_frozen_file_does_not_stop_an_offline_campaign(tmp_path,
                                                         monkeypatch):
    """A rehearsal never plays the world the canary watches; drift there
    cannot invalidate it."""
    frozen_file(tmp_path, monkeypatch)
    campaign = camp.Campaign(prompt_id="freeze-test",
                             out_dir=str(tmp_path / "out"),
                             games=list(camp.DEV_PILE), offline=True)
    assert campaign.games == list(camp.DEV_PILE)


def test_a_frozen_file_does_not_stop_a_mock_upstream_campaign(tmp_path,
                                                              monkeypatch):
    frozen_file(tmp_path, monkeypatch)
    campaign = camp.Campaign(prompt_id="freeze-test",
                             out_dir=str(tmp_path / "out"),
                             games=list(camp.DEV_PILE), offline=False,
                             env_upstream="http://127.0.0.1:1",
                             env_key="stub", require_key=False)
    assert campaign.env_upstream == "http://127.0.0.1:1"


def test_a_frozen_file_does_not_stop_a_mock_upstream_run(tmp_path,
                                                         monkeypatch, no_pool):
    """`PoolTouched` again: a mock-upstream `Run` sails past a frozen gate,
    because the gate is judged by the upstream it will actually contact."""
    frozen_file(tmp_path, monkeypatch)
    with pytest.raises(PoolTouched):
        run_mod.Run("g50t-5849a774", "freeze-test",
                    env_upstream="http://127.0.0.1:1", env_key="stub",
                    require_key=False, runs_root=str(tmp_path / "runs"))


def test_the_gate_is_not_consulted_at_all_on_a_mock_upstream(tmp_path,
                                                             monkeypatch,
                                                             no_pool):
    """Not "consulted and ignored" -- never consulted. An unreadable freeze
    file refuses everything it is shown, so a mock run surviving one proves
    the file was never opened."""
    path = tmp_path / "campaign_freeze.json"
    path.write_text("{corrupt", encoding="utf-8")
    monkeypatch.setattr(freeze_gate, "FREEZE_PATH", str(path))
    with pytest.raises(PoolTouched):
        run_mod.Run("g50t-5849a774", "freeze-test",
                    env_upstream="http://127.0.0.1:1", env_key="stub",
                    require_key=False, runs_root=str(tmp_path / "runs"))
