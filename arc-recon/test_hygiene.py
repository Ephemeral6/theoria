"""Offline tests for the canary and the contamination fold. No API, no network.

Every check here has a negative control. A check that has never been seen to
fail is not evidence that anything passed -- INC-003 is exactly the case where a
comparison that could not fail reported PASS for two runs that had both died, so
the tests that matter most below are the ones asserting the instruments go red.

    cd arc-recon && python -m pytest test_hygiene.py
"""

import json
import os

import pytest

import canary
import client
import contamination
from precheck import SealedGameError, assert_playable


# -- fixtures ---------------------------------------------------------------

EXPECTED = [
    {"index": 0, "action": "RESET", "hash": "aaaa", "n_frames": 1},
    {"index": 1, "action": "ACTION1", "hash": "bbbb", "n_frames": 1},
    {"index": 2, "action": "ACTION2", "hash": "cccc", "n_frames": 7},
]


def observed(*hashes):
    return [{"index": i, "action": EXPECTED[i]["action"], "hash": h,
             "n_frames": EXPECTED[i]["n_frames"]}
            for i, h in enumerate(hashes) if h is not None]


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Point every writer at a temp directory; nothing here touches data/."""
    monkeypatch.setattr(canary, "CANARY_PATH", str(tmp_path / "canary.json"))
    monkeypatch.setattr(canary, "RUNS_PATH", str(tmp_path / "runs.jsonl"))
    monkeypatch.setattr(canary, "FREEZE_PATH", str(tmp_path / "freeze.json"))
    monkeypatch.setattr(canary, "INCIDENTS_PATH", str(tmp_path / "incidents.jsonl"))
    return tmp_path


# -- compare: the three verdicts --------------------------------------------

def test_matching_hashes_pass():
    assert canary.compare(EXPECTED, observed("aaaa", "bbbb", "cccc"))["verdict"] \
        == "PASS"


def test_a_changed_hash_is_drift():
    verdict = canary.compare(EXPECTED, observed("aaaa", "ZZZZ", "cccc"))
    assert verdict["verdict"] == "DRIFT"
    assert verdict["first_divergence"] == 1
    assert verdict["mismatches"][0]["expected"] == "bbbb"
    assert verdict["mismatches"][0]["observed"] == "ZZZZ"


def test_a_step_that_never_ran_is_incomplete_not_pass():
    """INC-003's exact shape: absence must not read as agreement."""
    verdict = canary.compare(EXPECTED, observed("aaaa", "bbbb"))
    assert verdict["verdict"] == "INCOMPLETE"
    assert verdict["steps_agreed"] == 2
    assert verdict["unusable_steps"] == [{"index": 2, "action": "ACTION2"}]


def test_a_hashless_step_is_never_agreement():
    verdict = canary.compare(EXPECTED, [{"index": 1, "action": "ACTION1",
                                         "hash": None}])
    assert verdict["steps_agreed"] == 0
    assert verdict["verdict"] == "INCOMPLETE"


def test_drift_outranks_incompleteness():
    """A truncated run that also disagrees is drift, not merely incomplete."""
    verdict = canary.compare(EXPECTED, observed("aaaa", "ZZZZ"))
    assert verdict["verdict"] == "DRIFT"


# -- the freeze -------------------------------------------------------------

def test_freeze_blocks_and_says_why(sandbox):
    assert canary.freeze_state()["frozen"] is False
    canary.assert_campaigns_unfrozen()          # negative control: no raise
    canary.freeze_campaigns("INC-999", ["ar25-0c556536"], "test drift", {})
    with pytest.raises(canary.CampaignFrozen) as excinfo:
        canary.assert_campaigns_unfrozen()
    assert "INC-999" in str(excinfo.value)
    assert "ar25-0c556536" in str(excinfo.value)


def test_check_freeze_exit_code_flips(sandbox):
    assert canary.main(["check-freeze"]) == 0
    canary.freeze_campaigns("INC-999", ["ar25-0c556536"], "test drift", {})
    assert canary.main(["check-freeze"]) == 1


def test_refreezing_keeps_the_previous_freeze(sandbox):
    canary.freeze_campaigns("INC-998", ["ar25-0c556536"], "first", {})
    canary.freeze_campaigns("INC-999", ["sk48-d8078629"], "second", {})
    state = canary.freeze_state()
    assert state["incident"] == "INC-999"
    assert [h["incident"] for h in state["history"]] == ["INC-998"]


# -- incident numbering -----------------------------------------------------

def test_incident_ids_continue_and_ignore_revisions(sandbox):
    with open(canary.INCIDENTS_PATH, "w", encoding="utf-8") as fh:
        for ident in ("INC-001", "INC-001a", "INC-002a", "INC-006"):
            fh.write(json.dumps({"id": ident}) + "\n")
    assert canary.next_incident_id() == "INC-007"


def test_first_incident_when_the_file_is_empty(sandbox):
    assert canary.next_incident_id() == "INC-001"


# -- the guard --------------------------------------------------------------

def test_sealed_games_are_refused():
    with pytest.raises(SealedGameError):
        assert_playable("ls20-9607627b")
    with pytest.raises(SealedGameError):
        assert_playable("ft09-0d8bbf25")
    assert_playable("ar25-0c556536")            # negative control


def test_replay_refuses_a_sealed_target_before_spending(sandbox):
    canary._write_json(canary.CANARY_PATH,
                       {"version": "v1", "games": {"ls20-9607627b": {
                           "sequence": [1], "expected": EXPECTED[:2]}}})
    with pytest.raises(SealedGameError):
        canary.replay(["ls20-9607627b"])


def test_the_invocation_cap_is_checked_before_any_call(sandbox):
    canary._write_json(canary.CANARY_PATH, {"version": "v1", "games": {
        "ar25-0c556536": {"sequence": [1] * 6, "expected": EXPECTED},
        "g50t-5849a774": {"sequence": [1] * 6, "expected": EXPECTED},
        "sk48-d8078629": {"sequence": [1] * 6, "expected": EXPECTED},
        "tn36-ef4dde99": {"sequence": [1] * 6, "expected": EXPECTED}}})
    monkey = canary.INVOCATION_CAP
    canary.INVOCATION_CAP = 20
    try:
        with pytest.raises(canary.BudgetExceeded):
            canary.replay()                     # 24 planned > 20
    finally:
        canary.INVOCATION_CAP = monkey


# -- seeding ----------------------------------------------------------------

def test_seed_only_trusts_steps_both_replays_agreed_on(tmp_path, monkeypatch):
    report = {"results": {"ar25-0c556536": {
        "verdict": {"verdict": "PASS"},
        "run_a": [{"action": "RESET", "hash": "aaaa", "n_frames": 1},
                  {"action": "ACTION1", "hash": "bbbb", "n_frames": 1},
                  {"action": "ACTION2", "hash": "DIFF", "n_frames": 1},
                  {"action": "ACTION3", "hash": "dddd", "n_frames": 1}],
        "run_b": [{"action": "RESET", "hash": "aaaa", "n_frames": 1},
                  {"action": "ACTION1", "hash": "bbbb", "n_frames": 1},
                  {"action": "ACTION2", "hash": "OTHER", "n_frames": 1},
                  {"action": "ACTION3", "hash": "dddd", "n_frames": 1}]}}}
    path = tmp_path / "precheck.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    monkeypatch.setattr(canary, "PRECHECK_PATH", str(path))
    spec = canary.seed_from_precheck()
    # Truncated at the disagreement -- ACTION3 agreed, but it is downstream of a
    # step that did not, so its agreement means nothing.
    assert spec["games"]["ar25-0c556536"]["sequence"] == [1]
    assert len(spec["games"]["ar25-0c556536"]["expected"]) == 2


def test_seed_skips_games_without_a_pass(tmp_path, monkeypatch):
    report = {"results": {"ar25-0c556536": {
        "verdict": {"verdict": "UNPLAYABLE"}, "run_a": [], "run_b": []}}}
    path = tmp_path / "precheck.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    monkeypatch.setattr(canary, "PRECHECK_PATH", str(path))
    assert canary.seed_from_precheck()["games"] == {}


# -- the shipped spec -------------------------------------------------------

def test_the_shipped_spec_is_within_budget():
    spec = json.load(open(os.path.join(contamination.DATA_DIR, "canary.json"),
                          encoding="utf-8"))
    total = 0
    for game_id, game in spec["games"].items():
        assert_playable(game_id)                # nothing sealed in the spec
        assert len(game["sequence"]) <= canary.ACTIONS_PER_GAME
        assert len(game["expected"]) == len(game["sequence"]) + 1
        total += len(game["sequence"])
    assert total <= canary.INVOCATION_CAP


# -- contamination fold -----------------------------------------------------

def test_the_cut_file_still_matches_its_published_hash():
    assert contamination.verify_piles_hash()["matches"]


def test_the_claim_set_is_the_sealed_pile_minus_the_quarantined():
    summary = contamination.claim_set()
    assert summary["sealed_pile_size"] == 21
    assert summary["claim_set_size"] == 19
    assert summary["quarantined"] == ["ft09-0d8bbf25", "ls20-9607627b"]
    assert set(summary["quarantined"]) & set(summary["claim_set"]) == set()
    assert (len(summary["clean"]) + len(summary["retained_with_sensitivity_analysis"])
            == summary["claim_set_size"])


def test_the_last_log_entry_per_game_wins():
    register = contamination.current_register()
    # dc22 has two entries; the later one must not have downgraded the level
    # INC-004 established.
    assert register["dc22-fdcac232"]["level"] == "design_document_disclosed"
    assert register["ar25-0c556536"]["level"] == "trajectories_reviewed"


# -- the INC-007 transport ---------------------------------------------------

def test_the_jar_learns_cookies_from_error_responses_too():
    """The load-bearing detail of the fix, and it is not obvious.

    The first call of a retry loop is usually the 400. If the jar only learned
    routing cookies from 2xx, the retry would be routed as blindly as the first
    attempt and the fix would buy nothing inside the envelope where it matters
    most. It works because urllib sorts response processors by handler_order and
    HTTPCookieProcessor (500) runs before HTTPErrorProcessor (1000), which is the
    handler that turns a 400 into an exception. Pin it: a future reordering would
    degrade the fix silently, with no test failing and no error raised.
    """
    import urllib.request
    processors = [type(h).__name__ for h in
                  client.ArcClient(api_key="x", dry_run=True)
                  ._opener.process_response["https"]]
    assert processors.index("HTTPCookieProcessor") \
        < processors.index("HTTPErrorProcessor")
    assert urllib.request.HTTPCookieProcessor.handler_order \
        < urllib.request.HTTPErrorProcessor.handler_order


def test_cookies_can_be_turned_off_to_reproduce_the_old_transport():
    on = client.ArcClient(api_key="x", dry_run=True)
    off = client.ArcClient(api_key="x", dry_run=True, cookies=False)
    assert on.transport["cookies"] is True
    assert off.transport["cookies"] is False
    names = [type(h).__name__ for h in off._opener.process_response["https"]]
    assert "HTTPCookieProcessor" not in names


def test_cookie_values_never_survive_name_extraction():
    """Negative control for INC-008: the values must not come back out."""
    header = ("AWSALBAPP-0=SECRETVALUE; Expires=Tue, 04 Aug 2026 00:00:00 GMT; "
              "Path=/, GAMESESSION=TOKENVALUE; Path=/; HttpOnly")
    names = client.cookie_names(header)
    assert "AWSALBAPP-0" in names and "GAMESESSION" in names
    blob = json.dumps(names)
    assert "SECRETVALUE" not in blob and "TOKENVALUE" not in blob
    # The Expires attribute contains a comma, which is what makes naive
    # Set-Cookie splitting leak: the fragment after it must not become a name.
    assert not any("00:00:00" in n or "GMT" in n for n in names)


def test_every_set_cookie_header_is_counted_not_just_the_first():
    import email.message
    message = email.message.Message()
    for raw in ("AWSALBAPP-0=A; Path=/", "AWSALBAPP-1=B; Path=/",
                "GAMESESSION=C; HttpOnly"):
        message.add_header("Set-Cookie", raw)
    assert client._issued_cookie_names(message) == \
        ["AWSALBAPP-0", "AWSALBAPP-1", "GAMESESSION"]
    # A plain mapping (which collapses duplicates) must still not crash.
    assert client._issued_cookie_names({"Set-Cookie": "GAMESESSION=C"}) \
        == ["GAMESESSION"]


def test_the_ledger_never_holds_a_cookie_value():
    """Over the real, committed ledger -- the INC-008 redaction must hold."""
    path = os.path.join(contamination.DATA_DIR, "recon_ledger.jsonl")
    offenders = []
    for number, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.strip()
        if not line:
            continue
        entry = json.loads(line)
        for field in ("set_cookie", "set_cookie_names", "cookies_held"):
            value = entry.get(field)
            if value is None:
                continue
            text = value if isinstance(value, str) else " ".join(map(str, value))
            # A name list is names. Anything carrying "=" is carrying a value.
            if "=" in text:
                offenders.append((number, field))
    assert offenders == [], offenders[:5]


def _log_with(tmp_path, monkeypatch, *rows):
    """Replay the real log, then append rows, then point the reader at it."""
    path = tmp_path / "log.jsonl"
    with open(path, "w", encoding="utf-8") as fh:
        for entry in contamination.entries():
            fh.write(json.dumps(entry) + "\n")
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    monkeypatch.setattr(contamination, "LOG_PATH", str(path))


def test_a_typo_in_the_claim_state_does_not_land_a_game_in_clean(tmp_path,
                                                                 monkeypatch):
    """The fail-open bug: matching two exact strings let everything else
    through into the fully-uncontaminated set."""
    _log_with(tmp_path, monkeypatch,
              {"game_id": "wa30-ee6fef47", "level": "blurb_glimpsed",
               "claims": "quarantined",          # missing _from_claims
               "pile": "sealed", "note": "typo"})
    summary = contamination.claim_set()
    assert "wa30-ee6fef47" not in summary["clean"]
    assert "wa30-ee6fef47" in summary["needs_adjudication"]
    assert summary["unrecognised_claim_state"][0]["claims"] == "quarantined"


def test_a_missing_claim_state_on_a_leaked_game_is_not_clean(tmp_path,
                                                             monkeypatch):
    _log_with(tmp_path, monkeypatch,
              {"game_id": "vc33-5430563c", "level": "mechanics_disclosed",
               "pile": "sealed", "note": "no claims field at all"})
    summary = contamination.claim_set()
    assert "vc33-5430563c" not in summary["clean"]
    assert "vc33-5430563c" in summary["needs_adjudication"]


def test_a_materially_leaked_game_cannot_sit_in_the_claim_set_quietly(
        tmp_path, monkeypatch):
    """Level and claim state are two hand-written fields; they must agree."""
    _log_with(tmp_path, monkeypatch,
              {"game_id": "sc25-635fd71a", "level": "mechanics_disclosed",
               "claims": "retained_with_sensitivity_analysis",
               "pile": "sealed", "note": "level says material, state says keep"})
    summary = contamination.claim_set()
    assert "sc25-635fd71a" in summary["needs_adjudication"]
    assert "sc25-635fd71a" not in summary["retained_with_sensitivity_analysis"]
    assert summary["retained_above_material_level"][0]["game_id"] \
        == "sc25-635fd71a"


def test_the_live_register_needs_no_adjudication():
    """Negative control for the three above: the shipped register is clean."""
    assert contamination.claim_set()["needs_adjudication"] == []


def test_the_cross_track_audit_covers_more_than_our_own_ledger():
    audit = contamination.all_ledger_audit()
    assert audit["ledgers_scanned"] >= 1
    assert audit["all_clean"] is True
    assert "arc-recon/data/recon_ledger.jsonl" in audit["ledgers"]


def test_a_sealed_id_in_a_response_is_not_a_touch(tmp_path):
    """The catalogue lists all 25. Counting that as contact would make the
    audit incapable of ever coming back clean."""
    ledger = tmp_path / "ledger.jsonl"
    with open(ledger, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "method": "GET", "url": "https://three.arcprize.org/api/games",
            "request_body": None,
            "response_body": [{"game_id": "ls20-9607627b"},
                              {"game_id": "ar25-0c556536"}]}) + "\n")
    audit = contamination.sealed_api_contacts(str(ledger))
    assert audit["clean"] is True
    assert audit["sealed_ids_seen_in_responses"] == 1


def test_a_sealed_id_in_a_request_is_a_touch(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    with open(ledger, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "method": "POST", "url": "https://three.arcprize.org/api/cmd/RESET",
            "request_body": {"game_id": "ls20-9607627b", "card_id": "x"},
            "response_body": {"guid": "y"}}) + "\n")
    audit = contamination.sealed_api_contacts(str(ledger))
    assert audit["clean"] is False
    assert audit["sealed_games_contacted"] == ["ls20-9607627b"]


def test_a_short_sealed_id_in_a_request_is_also_a_touch(tmp_path):
    """Short ids are banned (INC-005) but the audit must still catch one."""
    ledger = tmp_path / "ledger.jsonl"
    with open(ledger, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "method": "POST", "url": "https://three.arcprize.org/api/cmd/ACTION1",
            "request_body": {"game_id": "ls20", "card_id": "x"},
            "response_body": {}}) + "\n")
    assert contamination.sealed_api_contacts(str(ledger))["clean"] is False


def test_the_real_ledger_has_addressed_no_sealed_game():
    assert contamination.sealed_api_contacts()["clean"] is True
