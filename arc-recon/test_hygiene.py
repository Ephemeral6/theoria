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
    """Point every writer at a temp directory; nothing here touches data/.

    FREEZE_LOG_PATH was missing from this list from the day it was added to
    `canary.py` until 2026-07-31, so every run of this suite appended six
    freeze events to the tracked append-only log. `conftest.py` now enforces
    the sentence above instead of asserting it.
    """
    monkeypatch.setattr(canary, "CANARY_PATH", str(tmp_path / "canary.json"))
    monkeypatch.setattr(canary, "RUNS_PATH", str(tmp_path / "runs.jsonl"))
    monkeypatch.setattr(canary, "FREEZE_PATH", str(tmp_path / "freeze.json"))
    monkeypatch.setattr(canary, "FREEZE_LOG_PATH",
                        str(tmp_path / "freeze_log.jsonl"))
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


def test_a_comma_inside_a_cookie_value_does_not_become_a_name():
    """The regression that made the redactor leak through itself.

    The first version split the header on "," on the theory that one header can
    carry several cookies. A value containing a comma then produced a fragment
    of the VALUE dressed up as a name -- so the function whose whole job was to
    drop values emitted one.
    """
    leaky = "GAMESESSION=v1,eyJndWlkIjoiOTk3ZDYzZmYifQ==; Path=/; HttpOnly"
    assert client.cookie_names(leaky) == ["GAMESESSION"]
    # The classic Set-Cookie trap: Expires carries a comma of its own.
    assert client.cookie_names(
        "AWSALBAPP-0=SECRET; Expires=Tue, 04 Aug 2026 00:00:00 GMT; Path=/"
    ) == ["AWSALBAPP-0"]
    # Nothing that is not a cookie token gets through.
    assert client.cookie_names("no-equals-sign; Path=/") == []
    assert client.cookie_names("") == []


def test_cookie_values_never_survive_name_extraction():
    """Negative control for INC-008: no value fragment, from any header shape."""
    import email.message
    message = email.message.Message()
    for raw in ("AWSALBAPP-0=SECRETVALUE; Expires=Tue, 04 Aug 2026 00:00:00 GMT",
                "GAMESESSION=TOKEN,WITH,COMMAS; Path=/; HttpOnly"):
        message.add_header("Set-Cookie", raw)
    names = client._issued_cookie_names(message)
    assert names == ["AWSALBAPP-0", "GAMESESSION"]
    blob = json.dumps(names)
    for secret in ("SECRETVALUE", "TOKEN", "WITH", "COMMAS", "GMT", "00:00:00"):
        assert secret not in blob, secret


def test_every_set_cookie_header_is_counted_not_just_the_first():
    import email.message
    message = email.message.Message()
    for raw in ("AWSALBAPP-0=A; Path=/", "AWSALBAPP-1=B; Path=/",
                "GAMESESSION=C; HttpOnly"):
        message.add_header("Set-Cookie", raw)
    assert client._issued_cookie_names(message) == \
        ["AWSALBAPP-0", "AWSALBAPP-1", "GAMESESSION"]
    # A plain mapping with lowercase keys must still be read (headers are
    # case-insensitive; the previous version missed this).
    assert client._issued_cookie_names({"set-cookie": "GAMESESSION=C"}) \
        == ["GAMESESSION"]


def _cookie_value_offenders(rows):
    """Anything in a cookie field that is not a bare cookie token is suspect."""
    offenders = []
    for number, entry in rows:
        for field in ("set_cookie_names", "cookies_held", "cookies_sent",
                      "cookies_held_after"):
            for name in entry.get(field) or []:
                if not client._COOKIE_TOKEN.match(str(name)):
                    offenders.append((number, field, "not-a-token"))
        raw = entry.get("set_cookie")
        if isinstance(raw, str) and raw and not raw.startswith("<redacted"):
            offenders.append((number, "set_cookie", "raw header retained"))
    return offenders


def test_the_cookie_value_detector_can_actually_fail():
    """Positive control. The first version tested `"=" in text`, which the name
    fields can never contain -- so for two of the three fields it checked, the
    assertion was incapable of failing and proved nothing."""
    planted = [(1, {"set_cookie_names": ["GAMESESSION=TOKENVALUE"]}),
               (2, {"cookies_sent": ["AWSALBAPP-0=SECRET"]}),
               (3, {"set_cookie": "GAMESESSION=raw; Path=/"})]
    found = _cookie_value_offenders(planted)
    assert len(found) == 3, found
    assert _cookie_value_offenders([(4, {"set_cookie_names": ["GAMESESSION"],
                                         "set_cookie": "<redacted INC-008>"})]) == []


def test_the_ledger_never_holds_a_cookie_value():
    """Over the real ledger -- the INC-008 redaction must hold."""
    path = os.path.join(contamination.DATA_DIR, "recon_ledger.jsonl")
    rows = []
    for number, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.strip()
        if line:
            rows.append((number, json.loads(line)))
    assert _cookie_value_offenders(rows) == [], _cookie_value_offenders(rows)[:5]


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


def test_a_transport_failure_still_leaves_exactly_one_ledger_row(tmp_path):
    """The module promises the ledger is complete by construction, and
    contamination.py's sealed-pile audit can only see what the ledger holds. A
    request that left the process and then timed out used to leave no row at
    all -- so a call carrying a sealed game_id could have been made and the
    audit would still report clean."""
    import urllib.error
    ledger = tmp_path / "ledger.jsonl"
    api = client.ArcClient(api_key="x", ledger_path=str(ledger))

    class Exploding:
        def open(self, *args, **kwargs):
            raise OSError("simulated connection reset")

    api._opener = Exploding()
    with pytest.raises(urllib.error.URLError):
        api.request("POST", "/api/cmd/RESET",
                    body={"game_id": "ar25-0c556536", "card_id": "c"}, note="t")

    rows = [json.loads(line) for line in open(ledger, encoding="utf-8")]
    assert len(rows) == 1 and api.calls == 1
    assert rows[0]["status"] == -1
    assert "simulated connection reset" in rows[0]["transport_error"]
    # The whole point: the audit can see what we sent.
    assert rows[0]["request_body"]["game_id"] == "ar25-0c556536"
    assert contamination.sealed_api_contacts(str(ledger))["clean"] is True


def test_the_sealed_audit_sees_a_failed_call_too(tmp_path):
    """Negative control for the test above: a sealed id in a failed request is
    still a contact."""
    import urllib.error
    ledger = tmp_path / "ledger.jsonl"
    api = client.ArcClient(api_key="x", ledger_path=str(ledger))

    class Exploding:
        def open(self, *args, **kwargs):
            raise OSError("boom")

    api._opener = Exploding()
    with pytest.raises(urllib.error.URLError):
        api.request("POST", "/api/cmd/RESET",
                    body={"game_id": "ls20-9607627b"}, note="t")
    audit = contamination.sealed_api_contacts(str(ledger))
    assert audit["clean"] is False
    assert audit["sealed_games_contacted"] == ["ls20-9607627b"]


def test_cookies_sent_is_the_jar_before_the_call_not_after(tmp_path):
    """`cookies_held` was snapshotted inside _record, which runs after the
    response was absorbed -- so the first call of a session, which provably
    sent nothing, was logged as though it held the server's cookies."""
    import http.cookiejar
    ledger = tmp_path / "ledger.jsonl"
    api = client.ArcClient(api_key="x", ledger_path=str(ledger))

    class Seeding:
        """Stands in for HTTPCookieProcessor: fills the jar during open()."""

        def open(self, request, timeout=None):
            cookie = http.cookiejar.Cookie(
                0, "GAMESESSION", "TOKEN", None, False,
                "three.arcprize.org", False, False, "/", True,
                False, None, False, None, None, {})
            api.jar.set_cookie(cookie)
            return _FakeResponse()

    class _FakeResponse:
        status = 200
        headers = {"set-cookie": "GAMESESSION=TOKEN; Path=/"}

        def read(self):
            return b'{"ok": true}'

        def geturl(self):
            return client.BASE_URL + "/api/cmd/RESET"

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    api._opener = Seeding()
    api.request("POST", "/api/cmd/RESET", body={"game_id": "ar25-0c556536"},
                note="first call of the session")
    row = json.loads(open(ledger, encoding="utf-8").read().strip())
    assert row["cookies_sent"] == []                  # nothing was echoed
    assert row["cookies_held_after"] == ["GAMESESSION"]


def test_clearing_routing_cookies_keeps_the_session_identity():
    """The retry envelope assumed each attempt was an independent routing draw.
    A pinned jar removes that, so there has to be a way to redraw without
    discarding the session we are trying to reach."""
    import http.cookiejar
    api = client.ArcClient(api_key="x", dry_run=True)
    for name in ("AWSALBAPP-0", "AWSALBAPP-1", "GAMESESSION"):
        api.jar.set_cookie(http.cookiejar.Cookie(
            0, name, "v", None, False, "three.arcprize.org", False, False,
            "/", True, False, None, False, None, None, {}))
    assert api.cookies_held() == ["AWSALBAPP-0", "AWSALBAPP-1", "GAMESESSION"]
    api.clear_routing_cookies()
    assert api.cookies_held() == ["GAMESESSION"]


def test_the_retry_envelope_redraws_a_replica_when_pinned(monkeypatch):
    """INC-007a's regression guard. Forty identical retries used to work because
    each was a fresh routing draw; a pinned jar makes them all the same draw, so
    the envelope has to be able to let go of the pin."""
    import http.cookiejar
    import precheck

    api = client.ArcClient(api_key="x", dry_run=True)
    for name in ("AWSALBAPP-0", "GAMESESSION"):
        api.jar.set_cookie(http.cookiejar.Cookie(
            0, name, "v", None, False, "three.arcprize.org", False, False,
            "/", True, False, None, False, None, None, {}))

    calls = {"n": 0}
    held_at_each_attempt = []

    def always_not_found(method, path, body=None, note=""):
        calls["n"] += 1
        held_at_each_attempt.append(api.cookies_held())
        raise client.ArcApiError(400, '{"message": "game x not found"}', path)

    monkeypatch.setattr(api, "request", always_not_found)
    monkeypatch.setattr(precheck.time, "sleep", lambda *_: None)
    status, _, stats = precheck.send_command(
        api, "/api/cmd/RESET", {"game_id": "ar25-0c556536"}, "t", attempts=12)

    assert stats["attempts"] == 12 and status == 400
    # Pin present at the start, dropped once the redraw fires, session kept.
    assert held_at_each_attempt[0] == ["AWSALBAPP-0", "GAMESESSION"]
    assert api.cookies_held() == ["GAMESESSION"]
    assert any(h == ["GAMESESSION"] for h in held_at_each_attempt), \
        "the redraw never took effect within the envelope"


# -- the INC-008 check must cover every ledger, not just the first one -------

def test_redactor_scans_the_cascade_ledgers_too(tmp_path, monkeypatch):
    """S5 salvaged P-20 into cascade/runs/, adding four more request ledgers.

    The redactor was written against a single hardcoded path, which is a check
    that would keep reporting "0 carry a cookie value" no matter what those
    four files held. Both halves are asserted here: that the real ledgers are
    discovered, and -- the negative control -- that a planted value in one of
    them is actually found.
    """
    import redact_ledger

    found = redact_ledger.all_ledgers()
    assert any("recon_ledger" in p for p in found)
    assert sum(1 for p in found if "cascade" in p) >= 4, found

    planted = tmp_path / "ledger.planted.jsonl"
    planted.write_text(
        json.dumps({"t": "2026-07-28T00:00:00Z", "note": "planted",
                    "set_cookie": "GAMESESSION=deadbeef; Path=/"}) + "\n",
        encoding="utf-8")
    report = redact_ledger.scan(str(planted))
    assert report["entries_with_values"] == 1
    assert report["offenders"][0]["names"] == ["GAMESESSION"]


def test_redactor_discovers_ledgers_under_a_nested_run(tmp_path, monkeypatch):
    """Negative control for the walk: a ledger one directory deeper is found."""
    import redact_ledger

    nest = tmp_path / "runs" / "2026-01-01T000000Z-x"
    nest.mkdir(parents=True)
    (nest / "ledger.g.jsonl").write_text("", encoding="utf-8")
    (nest / "steps.g.jsonl").write_text("", encoding="utf-8")
    monkeypatch.setattr(redact_ledger, "CASCADE_RUNS", str(tmp_path / "runs"))
    monkeypatch.setattr(redact_ledger, "LEDGER_PATH", str(tmp_path / "none"))
    found = redact_ledger.all_ledgers()
    assert [os.path.basename(p) for p in found] == ["ledger.g.jsonl"]
